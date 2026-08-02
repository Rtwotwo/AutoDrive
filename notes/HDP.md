# Hyper Diffusion Planner (HDP) 阅读笔记

> **论文标题**: Unleashing the Potential of Diffusion Models for End-to-End Autonomous Driving
> **arXiv**: 2602.22801v1, 2026-02-26
> **作者**: Yinan Zheng\*, Tianyi Tan\*, Bin Huang\*, Enguang Liu, Ruiming Liang, Jianlin Zhang, Jianwei Cui, Guang Chen, Kun Ma, Hangjun Ye, Long Chen, Ya-Qin Zhang, Xianyuan Zhan†, Jingjing Liu†
> **机构**: 清华大学智能产业研究院 (AIR) + 小米汽车 (Xiaomi EV)
> **项目主页**: https://zhengyinan-air.github.io/Hyper-Diffusion-Planner/
> **关键词**: 端到端自动驾驶、扩散模型、模仿学习、强化学习、真实车辆部署

---

## 1. 核心思想

现有端到端自动驾驶中的扩散规划器过度依赖**锚点轨迹 (anchors)**、**目标条件 (goal points)** 和**规则后处理**等工程辅助设计，掩盖了扩散模型本身的能力。

**HDP 的核心哲学**：去掉这些额外设计，回归极简的 vanilla 扩散模型，并通过三个关键维度的系统性研究释放扩散模型作为 E2E AD 规划器的真正潜力。

---

## 2. 方法详解

### 2.1 扩散模型基础

扩散模型定义一个将条件轨迹数据分布 $q_{0}(\tau_{0}|C)$ 逐步转化为噪声分布的前向过程：

$$q_{t0}(\tau_t|\tau_0) = \mathcal{N}(\tau_t | \alpha_t \tau_0, \sigma_t^2 I), \quad t \in [0, 1] \tag{1}$$

- $\tau_{0} \in \mathbb{R}^{L \times 4}$：规划轨迹，$L$ 个时间步，每步含自车中心航点坐标 $(x_{l}, y_{l})$ 和航向的 cos/sin 值
- $C$：来自感知骨干的潜在表示（条件）
- $\alpha_{t}, \sigma_{t}$：预定义的噪声调度 (Variance Preserving, VP)
- $t \to 1$ 时边缘分布趋近 $\mathcal{N}(0, I)$

逆向去噪过程等价于扩散 ODE：

$$\frac{d\tau_t}{dt} = f(t)\tau_t - \frac{1}{2}g^2(t)\nabla_{\tau_t}\log q_t(\tau_t) \tag{2}$$

其中 $f(t) = \frac{d\log\alpha_{t}}{dt}$，$g^2(t) = \frac{d\sigma_{t}^2}{dt} - 2\frac{d\log\alpha_{t}}{dt}\sigma_{t}^2$。

**标准扩散训练目标**（ϵ-matching）：

$$\mathcal{L} = \mathbb{E}_{t,\tau_0,\tau_t,\epsilon}\left[\|\epsilon_\theta(\tau_t, t, C) - \epsilon\|^2_2\right] \tag{3}$$

其中 $t \sim \mathcal{U}(0,1)$，$\tau_{0} \sim q_{0}(\tau_{0}|C)$，$\tau_{t} \sim q_{t0}(\tau_{t}|\tau_{0})$，$\epsilon \sim \mathcal{N}(0, I)$。

模型通过拟合噪声 $\epsilon$ 间接学习分数函数：$s_\theta(\tau_{t}, t, C) = -\epsilon_\theta(\tau_{t}, t, C) / \sigma_{t}$。生成时使用 ODE 求解器（实践中用 DPM-Solver 6 步）。

---

### 2.2 扩散损失空间设计 (Diffusion Loss Space)

#### 问题分析

规划轨迹位于**低维流形**，与高维图像生成本质不同。扩散模型可以预测三种可互相转换的量：

| 预测目标 | 含义 | 转换关系 |
|----------|------|----------|
| $\epsilon$ | 高斯噪声 | $\epsilon = (\tau_{t} - \alpha_{t}\tau_{0})/\sigma_{t}$ |
| $v_{t}$ | 流速度 (flow velocity) | $v_{t} = \alpha_{t}\epsilon - \sigma_{t}\tau_{0}$ |
| $\tau_{0}$ | 干净数据 | $\tau_{0} = (\tau_{t} - \sigma_{t}\epsilon)/\alpha_{t}$ |

这三种量可互相转换，因此有 **9 种预测-损失组合**：

| 预测 ↓ / 损失 → | $\tau_{0}$-loss | $v$-loss | $\epsilon$-loss |
|:---:|:---:|:---:|:---:|
| **$\tau_{0}$-pred** | $E[\lVert\tau_\theta - \tau_{0}\rVert^2]$ | — | — |
| **$v$-pred** | — | $E[\lVert v_{\theta;t} - v_{t}\rVert^2]$ | — |
| **$\epsilon$-pred** | — | — | $E[\lVert\epsilon_\theta - \epsilon\rVert^2]$ |

其中各预测头与损失函数的转换关系（表 III）完整定义了模型的参数化和监督方式。例如参数化为输出 $\tau_\theta$ 但用 $\epsilon$-loss：

$$\mathcal{L} = \mathbb{E}_{\tau_0,t,\epsilon}\left\|\frac{\tau_t - \alpha_t\tau_\theta}{\sigma_t} - \epsilon\right\|^2$$

#### 核心发现

**τ₀-prediction + τ₀-loss 是最优组合**，原因有两方面：

**① 快速收敛**：轨迹 $\tau_{0}$ 本身位于低维流形，神经网络可轻松捕捉；而 $\epsilon$ 和 $v$ 目标支撑在高维空间，需求更大模型容量。

**② 高质量生成**：去噪末期（$t \to 0$，$\sigma_{t} \to 0$），$\epsilon$ 和 $v$ 预测难以估计微弱噪声信号，产生高频伪影和轨迹抖动；$\tau_{0}$ 预测直接输出干净轨迹，天然抑制噪声，生成运动学一致轨迹。

ϵ-prediction + τ₀-loss / v-loss **完全崩溃**的原因：训练目标中噪声目标被 $1/\alpha_{t}$ 缩放 → 低噪声阶段方差极大 → 训练不稳定。

---

### 2.3 轨迹表示与混合损失 (Trajectory Representation & Hybrid Loss)

#### 问题分析

| 表示方式 | 优势 | 劣势 |
|----------|------|------|
| **绝对航点** $\tau_{0}^x = \{(x_{l}, y_{l})\}_{l=1}^{L}$ | 空间建模好，ADE 低 | 速度曲线严重抖动，局部时间一致性差 |
| **速度表示** $\tau_{0}^v = \{(v_{l}^x, v_{l}^y)\}_{l=1}^{L}$ | 轨迹平滑，Comfort 高 | 全局几何建模稍弱 |

速度表示下，推理时通过积分恢复绝对轨迹，数值分布更集中，学习更稳定。

#### 混合损失 (Hybrid Loss)

模型**输出速度**，同时计算两个损失：

$$\boxed{\mathcal{L}_{\text{velocity}} = \mathbb{E}_{\tau_0^v, \epsilon, t}\left\|\tau_\theta^v - \tau_0^v\right\|^2_2} \tag{4a}$$

$$\boxed{\mathcal{L}_{\text{waypoints}} = \mathbb{E}_{\tau_0^x, \epsilon, t}\left\|M \tau_\theta^v \cdot \Delta t - \tau_0^x\right\|^2_2 = \mathbb{E}_{\tau_0^v, \epsilon, t}\left\|M \tau_\theta^v \cdot \Delta t - M \tau_0^v \cdot \Delta t\right\|^2_2} \tag{4b}$$

最终混合损失：

$$\boxed{\mathcal{L}_{\text{hybrid}} = \mathcal{L}_{\text{velocity}} + \omega \cdot \mathcal{L}_{\text{waypoints}}} \tag{5}$$

**符号含义**：

| 符号 | 含义 |
|------|------|
| $\tau_\theta^v$ | 模型输出的预测速度序列 |
| $\tau_{0}^v$ | 真实速度序列 |
| $\tau_{0}^x$ | 真实绝对航点序列 |
| $\Delta t$ | 相邻帧时间间隔 |
| $M$ | 全 1 下三角矩阵，实现速度逐元素积分 → 航点 |
| $\omega = 0.1$ | 平衡权重 |

#### Theorem IV.1（混合损失的理论保证）

**定理内容**：公式 (5) 的混合损失等价于 P-范数下的扩散分数匹配损失：

$$\boxed{\mathcal{L}_{\text{hybrid}} = \mathbb{E}_{\tau_0^v, \epsilon, t}\left[\|\tau_\theta^v - \tau_0^v\|^2_P\right]} \tag{6}$$

其中 $P = I + \Delta t^2 \cdot \omega M^T M$ **严格正定**，该损失的最小化者就是公式 (2) 中的**边缘分数函数 (marginal score function)**。

**证明概要**：

$$\mathcal{L}_{\text{hybrid}} = \mathbb{E}[(\tau_\theta^v - \tau_0^v)^T(\tau_\theta^v - \tau_0^v)] + \omega \mathbb{E}[\Delta t^2 (\tau_\theta^v - \tau_0^v)^T M^T M (\tau_\theta^v - \tau_0^v)]$$

$$= \mathbb{E}[(\tau_\theta^v - \tau_0^v)^T (I + \omega \Delta t^2 M^T M) (\tau_\theta^v - \tau_0^v)]$$

$$= \mathbb{E}[\|\tau_\theta^v - \tau_0^v\|^2_P] = \mathbb{E}[D_P(\tau_\theta^v, \tau_0^v)]$$

其中 $D_{P}(u, v) = \|u - v\|^2_{P}$ 是 Bregman Divergence（$\Phi_{P}(u) = u^T P u$ 严格凸），因此提供无偏梯度学习边缘分数函数。

**关键结论**：混合损失**不改变扩散训练的最优解**——这是区别于其他工作（如 VAD 的 L1 损失/辅助碰撞损失会引入偏差）的核心优势。

#### 实现细节：梯度截断 (Detach)

由于 $\mathcal{L}_{\text{waypoints}}$ 中积分操作使未来时间步梯度累积，导致梯度分布不平衡。实现时限制梯度回传到时间窗口 $W$：

```python
def detached_integral(v, W, dt):
    wpt_sg = torch.cumsum(v.detach()) * dt       # detach 的历史
    shift_sg = torch.roll(wpt_sg, shifts=W)
    shift_sg[:W] = 0
    wpt = torch.cumsum(v) * dt                    # 有梯度的部分
    shift = torch.roll(wpt, shifts=W)
    shift[:W] = 0
    return wpt + shift_sg - shift                 # 只对窗口内回传梯度
```

---

### 2.4 数据缩放 (Data Scaling)

#### 多模态能力涌现

**轨迹发散度 (Trajectory Divergence)** 指标：衡量多模态生成能力

$$\text{Divergence Score} = \frac{1}{N_2}\sum_{i=1}^{N_2}\left\|P_L^i - \frac{1}{N_2}\sum_{i=1}^{N_2}P_L^i\right\|_2 \tag{7}$$

其中 $P_{L}^i$ 是第 $i$ 条轨迹的终点，$N_{2}$ 为生成轨迹数。

**关键发现**：

| 数据量 | 多模态表现 | 说明 |
|--------|-----------|------|
| 100K 帧 (NAVSIM 量级) | 模式崩溃 | 所有轨迹收敛到单一模式 |
| 20M 帧 | 多模态涌现 | 发散度快速增长 |
| 70M 帧 | 持续提升 | 闭环 +20%，开环 +10% |

结论与 Zhang et al. [54] 理论一致：扩散模型需充足数据才能泛化。**无先验知识（anchor/goal）也能捕获多模态驾驶行为，关键是数据量。**

---

### 2.5 强化学习后训练 (RL Post-Training)

#### 问题形式化

将扩散规划器形式化为策略 $\pi(a|s)$：
- 动作 $a$：生成的轨迹 $\tau_{0}$
- 状态 $s$：潜在表示 $C$

**KL 正则化 RL 目标**（第 $k$ 次迭代时从 $\pi_{k-1}$ 出发优化 $\pi_{k}$）：

$$\max_{\pi_k} \mathbb{E}_{s \sim \mathcal{D}}\left[\mathbb{E}_{a \sim \pi_k}[r(s, a)] - \frac{1}{\beta}D_{KL}(\pi_k \| \pi_{k-1})\right] \tag{8}$$

- $\mathcal{D}$：replay buffer
- $\beta > 0$：温度参数
- $D_{KL}(p\|q) = \mathbb{E}_{x \sim p}[\log(p(x)/q(x))]$

该 KL 正则化目标存在闭式解 [38]：

$$\boxed{\pi_k^{\star}(a|s) \propto \pi_{k-1}(a|s) \cdot \exp(\beta \cdot r(s, a))} \tag{9}$$

#### 加权回归损失

相比于需要推理时梯度计算（classifier guidance，昂贵不适合真车）或多步 MDP 建模（DPPO，需存储所有去噪步梯度）的方法，HDP 采用**加权回归**，计算成本几乎等同于 IL：

$$\mathcal{L}_{RL} = \mathbb{E}_{t, \epsilon, (s,a) \sim \mathcal{D}}\left[\exp(\beta \cdot r(s, a)) \cdot \|\epsilon_\theta^k(a_t, t, s) - \epsilon\|^2_2\right] \tag{10}$$

其中 $a_{t} = \alpha_{t} a + \sigma_{t} \epsilon$。

**本质**：在 IL 损失前乘以一个与奖励指数成正比的权重 $\exp(\beta r)$，好样本权重高、差样本权重低。

#### RL-Hybrid Loss

与预训练保持一致，将混合损失形式推广到 RL 后训练：

$$\boxed{\mathcal{L}_{RL-hybrid} = \mathbb{E}_{v, \epsilon, t}\left[\exp(\beta r) \cdot \|v_\theta^k - v\|^2_P\right]} \tag{11}$$

#### Theorem V.1（加权扩散损失的理论保证）

**定理内容**：公式 (9) 中的最优动作 $a \sim \pi_{k}^{\star}(a|s)$ 可以通过**优化公式 (11) 的加权扩散损失**、并用学习到的 $v^{k\star}$ 求解扩散逆过程来生成。

**证明概要**：

$$\mathbb{E}_{v \sim \pi_{k-1}, \epsilon, t}\left[\exp(\beta r) \|v_\theta - v\|^2_P\right]$$

$$= \int_v \int_{\epsilon,t} \exp(\beta r) \|v_\theta - v\|^2_P \cdot \pi_{k-1}(v) p_\epsilon(\epsilon) p_t(t) d\epsilon dt dv$$

$$= \frac{1}{Z}\int_v \int_{\epsilon,t} \|v_\theta - v\|^2_P \cdot \exp(\beta r)\pi_{k-1}(v) \cdot p_\epsilon(\epsilon) p_t(t) d\epsilon dt dv$$

$$= \frac{1}{Z}\int_v \int_{\epsilon,t} \|v_\theta - v\|^2_P \cdot \pi_k^{\star}(v) \cdot p_\epsilon(\epsilon) p_t(t) d\epsilon dt dv$$

$$= \frac{1}{Z} \mathbb{E}_{v \sim \pi_k^{\star}, \epsilon, t}\left[\|v_\theta - v\|^2_P\right]$$

其中 $Z = \int_{v} \exp(\beta r)\pi_{k-1}(v)dv$ 是归一化常数。加权回归等价于在最优策略分布上的标准分数匹配——这是**加权回归有效的数学基础**。

#### 实际实现

- **安全奖励**（伪闭环仿真，SAT 碰撞检测）：

  $$r_{\text{safety}} = 1 - \max_{l=1,\ldots,L} c_l$$

  其中 $c_{l}$ 对主动碰撞罚 1.0，追尾衰减罚 0.3（减轻非反应性模拟的伪影）

- **Reward Group Normalization** [46]：稳定权重数值范围
- **样本过滤**：丢弃所有动作获得相同奖励的样本
- **EMA 策略更新**：进一步稳定训练

---

### 2.6 模型架构

HDP 采用 E2E AD 标准架构，包含两个部分：

#### 场景编码器 (Scene Encoder)

1. 图像 + LiDAR → 工业级感知骨干 → 统一 BEV 特征 [30]
2. 两组 Transformer Queries 提取感知信息：
   - **OD Tokens**（目标检测）：车辆、行人定位
   - **LD Tokens**（车道检测）：道路结构理解
3. OD + LD + **Navi Tokens**（导航信息）拼接 → 多层 Self-Attention 融合 → 潜在表示 $C$

#### 扩散解码器 (Diffusion Decoder)

基于 DiT [40] 的 vanilla Transformer：

1. 噪声轨迹 $\tau_{t}$ 分割并投影为 $L$ 个 tokens → + 位置嵌入 + 速度嵌入
2. **Self-Attention Block**：噪声 token 间信息融合
3. **Cross-Attention Block**：轨迹 token 与条件 $C$ (OD/LD/Navi) 交互
4. **adaLN Block** (Adaptive Layer Normalization) [40]：注入扩散时间步 $t$
5. 重复 $N=6$ 层
6. **MLP Final Layer** [33, 57]：输出预测（速度 $\tau_\theta^v$）

推理时 ONNX → TensorRT 编译，DPM-Solver 6 步采样，满足 **10Hz 要求**。仅需轻量平滑后处理。

---

## 3. 核心公式汇总

### 扩散基础

$$q_{t0}(\tau_t|\tau_0) = \mathcal{N}(\tau_t | \alpha_t \tau_0, \sigma_t^2 I) \tag{1}$$

$$\frac{d\tau_t}{dt} = f(t)\tau_t - \frac{1}{2}g^2(t)\nabla_{\tau_t}\log q_t(\tau_t) \tag{2}$$

$$\mathcal{L}_\epsilon = \mathbb{E}_{t,\tau_0,\tau_t,\epsilon}\left[\|\epsilon_\theta(\tau_t, t, C) - \epsilon\|^2_2\right] \tag{3}$$

### 混合损失

$$\mathcal{L}_{\text{velocity}} = \mathbb{E}\left\|\tau_\theta^v - \tau_0^v\right\|^2_2 \tag{4a}$$

$$\mathcal{L}_{\text{waypoints}} = \mathbb{E}\left\|M \tau_\theta^v \cdot \Delta t - \tau_0^x\right\|^2_2 \tag{4b}$$

$$\mathcal{L}_{\text{hybrid}} = \mathcal{L}_{\text{velocity}} + \omega \cdot \mathcal{L}_{\text{waypoints}}, \quad \omega = 0.1 \tag{5}$$

$$\mathcal{L}_{\text{hybrid}} = \mathbb{E}\left[\|\tau_\theta^v - \tau_0^v\|^2_P\right], \quad P = I + \Delta t^2 \cdot \omega M^T M \succ 0 \tag{6}$$

### 轨迹发散度

$$\text{Divergence} = \frac{1}{N_2}\sum_{i=1}^{N_2}\left\|P_L^i - \frac{1}{N_2}\sum_{i=1}^{N_2}P_L^i\right\|_2 \tag{7}$$

### RL 策略优化

$$\max_{\pi_k} \mathbb{E}_{s \sim \mathcal{D}}\left[\mathbb{E}_{a \sim \pi_k}[r(s, a)] - \frac{1}{\beta}D_{KL}(\pi_k \| \pi_{k-1})\right] \tag{8}$$

$$\pi_k^{\star}(a|s) \propto \pi_{k-1}(a|s) \cdot \exp(\beta \cdot r(s, a)) \tag{9}$$

### RL 加权回归

$$\mathcal{L}_{RL} = \mathbb{E}_{t, \epsilon, (s,a) \sim \mathcal{D}}\left[\exp(\beta r(s, a)) \cdot \|\epsilon_\theta^k(a_t, t, s) - \epsilon\|^2_2\right] \tag{10}$$

$$\mathcal{L}_{RL-hybrid} = \mathbb{E}_{v, \epsilon, t}\left[\exp(\beta r) \cdot \|v_\theta^k - v\|^2_P\right] \tag{11}$$

---

## 4. 关键设计选择总结

| 设计选择 | 说明 | 消融/对比验证 |
|----------|------|--------------|
| **τ₀-pred + τ₀-loss** | 直接预测轨迹数据，数据空间监督 | 9 种组合中唯一同时快速收敛+高质量 (75.27 vs 最差 0.66) |
| **速度输出 + 混合损失** | 速度输出保证平滑，航点监督保证空间精度 | 闭环 57.88 vs 仅速度 21.98 / 仅航点 11.42 |
| **理论保证的损失函数** | P-范数 Bregman Divergence 不改变最优解 | 区别于 VAD 等使用 L1/辅助损失引入偏差的方法 |
| **极简设计** | 无锚点、无目标条件、无规则后处理 | 反而释放扩散模型能力 |
| **大规模数据** | 20M→70M 帧持续提升 | 100K 帧出现模式崩溃 |
| **加权回归 RL** | 计算量 ≈ IL，无推理时额外梯度 | 对比 classifier guidance / DPPO 更高效 |
| **RL 安全奖励** | SAT 碰撞检测 + 追尾衰减 | 安全场景显著提升 |

---

## 5. 两种理论保证的对比

| | Theorem IV.1 | Theorem V.1 |
|---|---|---|
| **阶段** | IL 预训练 | RL 后训练 |
| **核心结论** | 混合损失 = P-范数下无偏分数匹配 | 加权回归 = 最优策略分布上的标准分数匹配 |
| **证明方法** | Bregman Divergence ($\Phi_{P}$ 严格凸) | 权重吸收 + 归一化常数 |
| **实践意义** | 混合损失不改变扩散最优解 | $\exp(\beta r)$ 权重是 RL 的有效实现 |

---

## 6. 开环评估指标公式

**minADE Score** (最小平均位移误差):

$$S_{ADE} = 100 \times \text{Clip}\left(1 - \frac{\min\text{ADE}}{\text{Thresh}_{ADE}}, 0, 1\right), \quad \text{Thresh}_{ADE} = 4$$

**minFDE Score** (最小终点位移误差):

$$S_{FDE} = 100 \times \text{Clip}\left(1 - \frac{\min\text{FDE}}{\text{Thresh}_{FDE}}, 0, 1\right), \quad \text{Thresh}_{FDE} = 8$$

**Comfort Score**:

$$\text{Cost} = \frac{1}{N_1}\sum_{i=1}^{N_1}\left(\text{Cost}_{Acc} \times \text{Acc} + \text{Cost}_{Jerk} \times \text{Jerk}\right), \quad \text{Cost}_{Acc}=1.0, \text{Cost}_{Jerk}=0.5$$

$$S_{Comfort} = 100 \times \text{Clip}\left(1 - \frac{\text{Cost}}{\text{Thresh}_{Comfort}}, 0, 1\right), \quad \text{Thresh}_{Comfort} = 200$$

**开环综合分数**:

$$S_{Open-Loop} = (1 - CR) \times \sum_{m \in M} \omega_m S_m, \quad M = \{ADE, FDE, Comfort\}$$

其中 $\omega_{ADE}=0.35, \omega_{FDE}=0.25, \omega_{Comfort}=0.40$。

---

## 7. 闭环评估指标公式

**成功率**（6 场景加权）：

$$\text{Success Rate} = w_1 s_1 + w_2 s_2 + w_3 s_3 + w_4 s_4 + w_5 s_5 + w_6 s_6$$

| 场景 | $s_{1}$ 起步 | $s_{2}$ 跟车停车 | $s_{3}$ 导航变道 | $s_{4}$ 让行 VRU | $s_{5}$ 路口让行 | $s_{6}$ 左右转弯 |
|------|-----------|---------------|---------------|---------------|---------------|---------------|
| 权重 $w$ | 0.1 | 0.25 | 0.25 | 0.1 | 0.1 | 0.2 |

**稳定性分数**:

$$S_{center} = 100 \times \text{Clip}\left(1 - \frac{k_{center}}{\text{Thresh}_{center}}, 0, 1\right), \quad \text{Thresh}_{center} = 40$$

$$S_{speed} = 100 \times \text{Clip}\left(1 - \frac{k_{speed}}{\text{Thresh}_{speed}}, 0, 1\right), \quad \text{Thresh}_{speed} = 40$$

其中 $k_{center}, k_{speed}$ 是每 100km 异常中心化和异常速度的次数。

$$\text{Closed-Loop Score} = \frac{\text{Success Rate} + \frac{S_{center} + S_{speed}}{2}}{2}$$

---

## 8. 主要实验结果

### 递进式消融 (Table II)

| 模型 | 数据量 | 开环 | 闭环 | 关键转折 |
|------|--------|------|------|----------|
| Base Model (ϵ-loss+ϵ-pred) | M | 51.07 | 7.83 | — |
| + τ₀-loss & τ₀-pred | M | 75.27 | 11.42 | 损失空间 |
| + Velocity Supervision | M | 84.38 | 21.98 | 轨迹表示 |
| + Hybrid Loss | M | 85.05 | **57.88** | ⚡ 最大跃升 |
| + Data Scaling (L, 50M) | L | 86.07 | 64.79 | 数据 |
| **HDP** (XL, 70M) | XL | **88.94** | 75.38 | 最终版 |
| **HDP-RL** (+ RL) | — | — | **76.20** | 安全增强 |

**相较 Base Model 约 10 倍闭环提升**。混合损失是最大单次跃升（闭环 11.42 → 57.88）。

---

## 9. 训练配置

| 参数 | IL 预训练 | RL 后训练 |
|------|----------|----------|
| GPU | 64×NVIDIA H20 | 32×NVIDIA H20 |
| Batch Size | 160/GPU | — |
| Epochs / Steps | 10 epochs | 8k steps |
| 优化器 | AdamW (lr=5e-4, wd=0.01) | — |
| 噪声调度 | VP (Variance Preserving) | — |
| 采样步数 | 6 (DPM-Solver) | — |
| DiT 层数 $N$ | 6 | — |
| Hidden Dim | 256 | — |
| Multi-Head | 8 | — |
| 混合损失 $\omega$ | 0.1 | — |
| RL $\beta$ | — | 1.0 |
| RL Group Size | — | 32 |
| RL EMA | — | 0.05 |

---

## 10. 与 TOAD 的对比

| 维度 | HDP | TOAD |
|------|-----|------|
| 方法类型 | 训练时改进（损失空间+表示+RL） | **测试时优化**（无需重训练） |
| 即插即用 | ❌ 需重新训练 | ✅ 可用于任意冻结规划器 |
| 核心机制 | 扩散模型生成 + 混合损失监督 + 加权回归 RL | CEM 搜索 + 冻结评分器优化 |
| 数据需求 | 需大规模训练数据 (20M+ 帧) | 无需额外训练数据 |
| 理论保证 | Theorem IV.1（混合损失不改变最优解）+ V.1（加权回归=最优策略分数匹配） | 无显式理论保证（经验性 CEM 搜索） |
| 推理开销 | DPM-Solver 6 步采样 | +1.9~20.4ms CEM 搜索 |
| 互补性 | **生成侧**改进 | **评分/选择侧**改进 |

---

*笔记日期: 2026-07-16*
