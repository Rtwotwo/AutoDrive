# TOAD: Test-Time Trajectory Optimization for Autonomous Driving 阅读笔记

> **论文标题**: Test-Time Trajectory Optimization for Autonomous Driving
> **arXiv**: 2606.07170v1, 2026-06-05
> **作者**: Yihong Xu\*, Éloi Zablocki\*, Yuan Yin, Elias Ramzi, Ellington Kirby, Alexandre Boulch, Matthieu Cord
> **机构**: valeo.ai, Paris, France & Sorbonne Université, CNRS, ISIR
> **关键词**: 端到端自动驾驶、测试时优化、交叉熵方法 (CEM)、轨迹评分器、即插即用

---

## 1. 核心思想

现有端到端规划器的"生成-评分-选择"范式存在根本缺陷：**评分器仅在候选轨迹生成后使用，无法反向影响候选集质量**。如果候选集本身很弱，再好的评分器也无能为力。

**TOAD 的核心创新**：将冻结的评分器重新定义为可优化的**轨迹级奖励函数**，在测试时通过交叉熵方法 (CEM) 搜索奖励最大化的轨迹，无需重新训练任何模型。

---

## 2. 方法详解

### 2.1 评分器作为奖励函数

**轨迹定义**：一个轨迹 $\tau = (p_1, \ldots, p_{n_p})$ 是 $n_p$ 个未来位姿的序列，每个位姿 $p_t = (x_t, y_t, \theta_t) \in \mathbb{R}^3$ 在自车坐标系中。

**评分器** $S$：在给定观测 $o$（传感器输入 + 自车状态）和目标 $g$（目标/路线）的条件下，将完整轨迹映射为一个标量：

$$S(\tau; o, g) \in \mathbb{R}$$

$S$ 是一个与基础规划器联合训练的神经网络。TOAD 将其视为**轨迹空间上的奖励函数**，从而可以在连续轨迹空间上搜索最优解，而非仅在固定候选集中排序。

### 2.2 控制空间优化

直接在位姿空间中采样会产生锯齿状、动力学不可行的轨迹。TOAD 通过**运动学自行车模型 (Bicycle Model, BM)** 注入动力学先验。

**控制序列定义**：

$$\mathbf{u} = (u_t)_{t=1}^{n_p}, \quad u_t = (a_t, \omega_t) \in \mathbb{R}^2 \tag{1}$$

其中 $a_t$ 是纵向加速度，$\omega_t$ 是横摆角速度 (yaw rate)。

**自行车模型是可逆的**，因此控制量和轨迹表示等价：
- 前向：$\tau = \text{BM}(\mathbf{u}, v_0)$，从控制序列 + 当前速度推出轨迹
- 逆向：$\mathbf{u} = \text{BM}^{-1}(\tau, v_0)$，从轨迹恢复控制序列

**在控制空间搜索的两大优势**：
1. 每个采样天然平滑且动力学可行
2. 舒适性（定义在加速度和 jerk 上）可直接从 $\mathbf{u}$ 计算

### 2.3 基于规划器的信任域 (Trust Region)

**核心动机**：CEM 理论上可以从任何位置初始化，但没有约束的话搜索会漂移到评分器无法可靠评估的区域（奖励黑客问题）。

**信任域构建**：假设基础规划器输出 $N$ 个候选轨迹及其选择的轨迹：

$$\text{BasePlanner}(o, g) = (\mathcal{T}, \tau_{\text{base}}), \quad \tau_{\text{base}} \in \mathcal{T} = \{\tau^{(i)}\}_{i=1}^{N} \tag{2}$$

该公式**覆盖所有现有规划器**，包括单候选规划器（$\mathcal{T} = \{\tau_{\text{base}}\}$）。

映射到控制空间：$\mathbf{U} = \{\mathbf{u}^{(i)} = \text{BM}^{-1}(\tau^{(i)}, v_0)\}_{i=1}^{N}$，选中的为 $\mathbf{u}_{\text{base}}$。

信任域以 $\mathbf{u}_{\text{base}}$ 为锚点，$\mathbf{U}$ 的分布决定其范围。

### 2.4 TOAD 目标函数：CEM + 信任域先验

CEM 最大化目标函数 $J(\mathbf{u})$，该目标结合了评分器奖励和两个闭式正则化项：

$$\boxed{J(\mathbf{u}) = S\big(\text{BM}(\mathbf{u}, v_0); o, g\big) - \lambda_a C_{\text{anchor}}(\mathbf{u}) - \lambda_c C_{\text{comf}}(\mathbf{u})} \tag{3}$$

**三项的含义**：

| 项 | 公式 | 作用 |
|-----|------|------|
| **Scorer Reward** | $S(\text{BM}(\mathbf{u}, v_0); o, g)$ | 学习到的轨迹级奖励（主优化信号） |
| **Anchor Regularizer** | $C_{\text{anchor}}(\mathbf{u}) = \|\mathbf{u} - \mathbf{u}_{\text{base}}\|^2$ | 约束搜索不远离锚点，保持在评分器可靠区域内 |
| **Comfort Regularizer** | $C_{\text{comf}}$（闭式） | 累积违反标准运动学舒适限制的平方值：纵/横向加速度、jerk、yaw rate、yaw acceleration |

$C_{\text{comf}}$ 是精确的闭式表达式而非学习估计，提供评分器仅能粗略估计的信号。评估范围涵盖未来控制以及上一次执行的控制，惩罚自车近期运动的不舒适转换。

### 2.5 CEM 搜索过程

#### 初始化

- 均值设为锚点：$\boldsymbol{\mu}_0 = \mathbf{u}_{\text{base}}$
- 标准差由基础规划器自身提议的离散度决定：
  $$\boldsymbol{\sigma}_0 = \max\big(\beta \cdot \text{std}(\mathbf{U}), \epsilon\big)$$
  其中 $\beta < 1$，$\epsilon$ 是防止探索完全崩溃的下界（$\epsilon_a = 0.1\ \text{m/s}^2$，$\epsilon_\omega = 0.025\ \text{rad/s}$）。

探索因此依赖于**规划器自身的不确定性**——这是一个优雅的设计。

#### 迭代过程

对迭代 $k = 1, \ldots, K$，在 $\mathbb{R}^{2n_p}$ 中使用高斯分布 $\mathcal{N}(\boldsymbol{\mu}_k, \text{diag}(\boldsymbol{\sigma}_k^2))$：

1. **采样**：抽取 $M$ 个控制序列
2. **推演与评分**：通过 BM 推演轨迹，计算 $J(\mathbf{u})$
3. **选择精英**：保留得分最高的 $E$ 个序列作为精英集 $\mathcal{E}_k$
4. **更新分布**：
   $$\boldsymbol{\mu}_k = \text{mean}(\mathcal{E}_k), \quad \boldsymbol{\sigma}_k = \text{std}(\mathcal{E}_k)$$

#### 最终轨迹选择

CEM 收敛后，推演最终均值轨迹 $\tau_{\text{mean}} = \text{BM}(\boldsymbol{\mu}_K, v_0)$。最终输出取 $\tau_{\text{mean}}$ 和 $\tau_{\text{base}}$ 中评分更高的：

$$\boxed{\tau^{\star} = \arg\max_{\tau \in \{\tau_{\text{mean}}, \tau_{\text{base}}\}} S(\tau; o, g) - \lambda_c \ C_{\text{comf}}\big(\text{BM}^{-1}(\tau, v_0)\big)} \tag{4}$$

注意此处**排除了 $C_{\text{anchor}}$**（CEM 均值不应因偏离锚点而受惩罚），但保留了舒适性惩罚。与 $\tau_{\text{base}}$ 的比较保证了返回轨迹的成本不会低于原始轨迹。

---

## 3. 关键设计选择总结

| 设计选择 | 说明 | 消融验证 |
|----------|------|----------|
| **控制空间搜索** | 通过 BM 保证动力学可行 + 平滑 | 优于轨迹空间搜索 (48.5 vs 36.4 EPDMS) |
| **信任域热启动** | $\boldsymbol{\mu}_0 = \mathbf{u}_{\text{base}}$ | 标准正态初始化也有竞争力 (42.7 vs 48.5) |
| **评分器奖励** | 主优化信号 | 移除后大幅下降 (48.5 → 35.7) |
| **锚点正则化** | 约束不偏离信任域 | 移除后下降 (48.5 → 44.4) |
| **舒适性正则化** | 闭式运动学舒适性惩罚 | 移除后下降 (48.5 → 46.9) |
| **评分器泛化性** | 必须能评估 proposal 之外的轨迹 | GTRS scorer → 23.9 (崩溃)；SparseDriveV2 → 34.6 |

---

## 4. 评分器选择的关键发现

**不是所有评分器都能作为奖励函数！**

| 评分器类型 | 训练方式 | TOAD 表现 |
|-----------|----------|-----------|
| **DrivoR scorer** | 与生成器联合训练但**解耦**，自由解码评估 | ✅ 成功：+43.6% (iPad) |
| GTRS scorer | 评分固定词汇表中的预计算轨迹 | ❌ 崩溃到 23.9 |
| SparseDriveV2 scorer | 评分固定词汇表 | ❌ 降至 34.6 |

**原因**：固定词汇表评分器在训练时从未见过词汇表之外的轨迹，因此在其上的预测完全不可靠。TOAD 的搜索会探索提案分布之外的轨迹，只有解耦训练的评分器才能保持准确。

---

## 5. 超参数配置

| 参数 | 值 | 说明 |
|------|-----|------|
| CEM 迭代 $K$ | 5 (on-the-fly) / 100 (vocabulary) | 后者因词汇表 >8K 需更多迭代 |
| 每次候选数 $M$ | 64 | 平衡搜索质量与推理成本 |
| 精英数 $E$ | $M/8 = 8$ | 实验最佳（候选预算 64 下） |
| 初始标准差缩放 $\beta$ | 0.5 | |
| 加速度下界 $\epsilon_a$ | 0.1 m/s² | |
| 横摆角速度下界 $\epsilon_\omega$ | 0.025 rad/s | |
| 舒适性权重 $\lambda_c$ | 0.05 | |
| 锚点权重 $\lambda_a$ | 0.5 | |

---

## 6. 计算成本

- **搜索本身**仅增加 1.9 ms (K=5) ~ 20.4 ms (K=100)，相对于总推理时间 100~780 ms。
- 当评分器共享感知主干时（如 DrivoR），搜索几乎免费（1.9 ms）。
- 若评分器外部独立，需额外 ~100 ms 的 ViT-S 感知编码器。

---

## 7. 核心公式汇总

### 控制空间搜索
$$\mathbf{u} = (a_t, \omega_t)_{t=1}^{n_p} \in \mathbb{R}^{2n_p} \tag{1}$$

### 信任域
$$\text{BasePlanner}(o, g) = (\mathcal{T}, \tau_{\text{base}}) \tag{2}$$

### CEM 目标函数
$$J(\mathbf{u}) = S\big(\text{BM}(\mathbf{u}, v_0); o, g\big) - \lambda_a\|\mathbf{u} - \mathbf{u}_{\text{base}}\|^2 - \lambda_c C_{\text{comf}}(\mathbf{u}) \tag{3}$$

### 最终输出
$$\tau^{\star} = \arg\max_{\tau \in \{\tau_{\text{mean}}, \tau_{\text{base}}\}} S(\tau; o, g) - \lambda_c C_{\text{comf}}\big(\text{BM}^{-1}(\tau, v_0)\big) \tag{4}$$

### CEM 初始化
$$\boldsymbol{\mu}_0 = \mathbf{u}_{\text{base}}, \quad \boldsymbol{\sigma}_0 = \max(\beta \cdot \text{std}(\mathbf{U}), \epsilon)$$

### CEM 更新
$$\boldsymbol{\mu}_k = \text{mean}(\mathcal{E}_k), \quad \boldsymbol{\sigma}_k = \text{std}(\mathcal{E}_k)$$

---

## 8. 主要实验结果

| Benchmark | 基础模型 | TOAD 提升 | 备注 |
|-----------|---------|-----------|------|
| NAVSIM-v1 | 6 个规划器 | +0.1% ~ +2.4% PDMS | 安全性已近饱和，主要提升进度分 |
| NAVSIM-v2 | 6 个规划器 | +2.3% ~ +43.6% EPDMS | iPad 从 34.7→49.8；越弱的提升越大 |
| NAVSIM-v2 | DrivoR + TOAD | **56.3 EPDMS** | 新 SOTA，仅差特权 PDM-Closed 0.3 |
| HUGSIM | DrivoR + TOAD | nuScenes HDS 39.7→49.9 | 安全性+舒适性均有提升 |

**关键发现**：收益来自**搜索本身**而非更强的评分器。仅用评分器重新排序原始提案甚至可能损害性能，而 TOAD 一致提升。

---

## 9. 局限性与展望

1. **依赖基础规划器热启动**：足够精确的评分器+优化器理论上应能从头搜索，是否可通过更多数据和容量取代基础规划器？
2. **依赖监督解耦评分器**：未来可通过自监督或世界模型奖励减少对昂贵轨迹级标注的依赖。
3. **奖励不完全精确**：能见度受限时可能产生失败案例。

---

## 10. 与 HDP 的对比

| 维度 | HDP | TOAD |
|------|-----|------|
| 方法类型 | 训练时改进（损失空间+表示+RL） | **测试时优化**（无需重训练） |
| 即插即用 | ❌ 需重新训练 | ✅ 可用于任意冻结规划器 |
| 核心机制 | 扩散模型生成+混合损失监督 | CEM 搜索+冻结评分器优化 |
| 数据需求 | 需大规模训练数据 (20M+ 帧) | 无需额外训练数据 |
| 推理开销 | DPM-Solver 6 步采样 | +1.9~20.4 ms CEM 搜索 |
| 互补性 | **生成侧**改进 | **评分/选择侧**改进 |

两者高度互补：HDP 改进轨迹生成质量，TOAD 在生成基础上进一步搜索优化。

---

*笔记日期: 2026-07-16*
