# DriveFuture: Future-Aware Latent World Models for Autonomous Driving 阅读笔记

> **论文标题**: DriveFuture: Future-Aware Latent World Models for Autonomous Driving
> **arXiv**: 2605.09701v1, 2026-05-10
> **作者**: Yufeng Hong\*, Xiaotian Zhou\*, Yingyan Li, Xiangpo Zhou, Lin Liu, Yadan Luo, Shaoqing Xu, Lei Yang, Ziying Song
> **机构**: 北京理工大学、中科院自动化所、北航、北京交通大学、昆士兰大学、澳门大学、南洋理工大学、燕山大学
> **关键词**: 端到端自动驾驶、潜在世界模型、未来感知、未来条件化规划、渐进式前瞻引导

---

## 1. 核心思想与动机

### 1.1 现有潜在世界模型的根本局限

潜在世界模型（Latent World Models）因其三个优势被视为自动驾驶的重要方向：
1. 在**紧凑潜在空间**中学习动力学，避免昂贵的像素级生成
2. 潜在表示可**抽象掉低级视觉细节**，聚焦规划相关的场景结构、交互和动作后果
3. 时间结构化的表示**天然适配长时域规划**

然而，论文指出了一个**关键局限**：现有潜在世界模型（LAW、World4Drive、WorldRFT、DriveWorld-VLA、DriveVLA-W0、DriveLaW 等）将未来潜在状态主要用于：

| 现有用法 | 问题 |
|----------|------|
| **预测目标 (Prediction Target)** | 只关心"未来能否被预测准确"，不关心"未来信息是否对当前决策有用" |
| **辅助信号 (Auxiliary Signal)** | 未来信息与当前特征在潜在空间中纠缠，无法直接影响规划决策 |

**核心矛盾的类比**：

> 现有方法像是**天气预报员**——擅长预测未来天气（未来状态），但不会用天气预报来**改变今天的出行计划**（当前决策）。

### 1.2 论文的核心主张："终结者"式决策视角

论文提出了一个非常精彩的类比——自动驾驶系统应当像电影《终结者》中的角色一样，**将未来的知识带回现在**：

| 现有范式 | 论文主张 |
|----------|----------|
| 从当前状态预测未来会如何演变 | 用对未来后果的认知**反向重塑**对当前场景的理解和决策 |
| 未来 = 被预测的对象 | 未来 = 影响当前决策的**条件 (Condition)** |
| 反应式控制 (Reactive) | 未来感知决策 (Future-Aware) |

> **核心洞察**：一个理想的自动驾驶系统不应当只是未来的预测器，而应当让**未来状态作为条件，反向影响当前的决策过程**，从而赋予系统更富远见的规划能力。

---

## 2. 方法：DriveFuture 未来感知潜在世界模型

### 2.1 整体架构

DriveFuture 的训练和推理构成一个**统一的未来感知潜在动力学机制**：

```
                        ┌─────────────────────────┐
   训练时:              │  Future Alignment Adapter │
   Observation t+T ──→ │  (Cross-Attn Grounding)   │──→ Zᶜ_{t+T} (未来感知潜在)
                        └─────────────────────────┘
                                   ↑ query
                        ┌─────────────────────────┐
   Observation t ──→    │  Latent Dynamics         │
   Ego Status     ──→   │  Predictor               │──→ Ẑ_{t+T} (预测未来潜在)
   Trajectory τ ──→     └─────────────────────────┘
                                                        ↓
                        ┌─────────────────────────┐
                        │  Planning Decoder        │
                        │  (Diffusion Transformer) │──→ 精炼轨迹
                        └─────────────────────────┘
                                   ↑
                        Z_t (当前场景潜在)

   推理时:   Future Alignment Adapter 被绕过，Zᶜ_{t+T} = Ẑ_{t+T}
             PFG 解决轨迹意图与未来预测的循环依赖
```

---

## 3. 三大核心模块详解

### 3.1 Latent Dynamics Predictor（潜在动力学预测器）

**功能**：给定当前场景潜在 $Z_{t}$ 和轨迹意图 $\tau$，预测未来 $t+T$ 时刻的场景潜在状态。

#### 轨迹条件化潜在预测

将绝对轨迹 $\tau = \{(x_{k}, y_{k}, \theta_{k})\}_{k=1}^{T}$ 编码为差分特征序列 $E_\tau$（使用归一化有限差分 + sin/cos 朝向嵌入），然后通过 Transformer Decoder 进行条件预测：

$$\boxed{\hat{Z}_{t+T} = f_\phi(Q_f; [Z_t \parallel E_\tau])} \tag{1}$$

其中 $Q_{f} \in \mathbb{R}^{K \times d}$ 是可学习的未来查询 token（$K=16$），$[Z_{t} \parallel E_\tau]$ 是拼接的上下文。最终输出 $\hat{Z}_{t+T} \in \mathbb{R}^{K \times d}$ 是紧凑的 $K$ 个 token 的未来潜在预测。

**设计要点**：$K=16$ 是有意为之的**瓶颈设计**——防止世界模型简单复制稠密的未来外观，迫使其编码对规划有高价值的未来信息。

#### 条件源随机化（Conditioning Source Randomization）

为支持推理时的 CFG（无分类器引导），训练时以三种概率采样轨迹条件：

$$\begin{cases} E_\tau \leftarrow \Psi(\tau_{gt}), & \text{w.p. } p_{gt}=0.4 \\ E_\tau \leftarrow \Psi(\tau_{kin}), & \text{w.p. } p_{kin}=0.4 \\ E_\tau \leftarrow E_\varnothing, & \text{w.p. } p_{\varnothing}=0.2 \end{cases} \tag{2}$$

三种模式互补：
- **GT 轨迹**：提供高质量未来意图信号（训练）
- **运动学推演 $\tau_{kin}$**：暴露于可部署的粗糙意图（常加速度模型）
- **空 token $E_\varnothing$**：创建 CFG 所需的无条件分支

**运动学推演** $\tau_{kin}$ 使用常加速度自车模型：
$$\begin{aligned} x_k^{kin} &= v_x t_k + \frac{1}{2} a_x t_k^2 \\ y_k^{kin} &= v_y t_k + \frac{1}{2} a_y t_k^2 \\ \theta_k^{kin} &= \text{atan2}(v_y + a_y t_k, v_x + a_x t_k) \end{aligned} \tag{3}$$

其中 $t_{k} = k\Delta t$。该推演并非精确规划器，而是提供一个**稳定、物理可行的意图方向**。

---

### 3.2 Future Alignment Adapter（未来对齐适配器）

**功能**：在训练时将预测的未来潜在锚定到真实的未来场景观测，同时避免密集重建目标。

#### 训练时的 Cross-Attention Grounding

训练时可访问未来观测 $I_{t+T}$，通过**同一编码器**（梯度截断）编码为真实未来潜在：
$$Z_{t+T} = \text{sg}(\text{enc}(I_{t+T})) \in \mathbb{R}^{64 \times d}$$

然后通过**单层多头 Cross-Attention** 将预测未来潜在 $\hat{Z}_{t+T}$ 锚定到真实未来 BEV token：

$$\boxed{\tilde{Z}_{t+T} = \text{MHA}\big(\text{LN}(\hat{Z}_{t+T}),\; Z_{t+T},\; Z_{t+T}\big)} \tag{4}$$

其中 $\hat{Z}_{t+T}$ 作为 Query（来自预测），$Z_{t+T}$ 作为 Key/Value（来自真实未来）。

**关键设计**：
- **无残差连接**：不连接 $\hat{Z}_{t+T}$，确保 Oracle 条件是纯净的 GT 证据选择
- **保持 $K=16$ token 接口**：无论未来 BEV 分辨率多大，条件化开销恒定
- **梯度截断**：阻止未来分支成为捷径

#### 未来帧缺失时的 Fallback

因为部分训练样本没有未来帧（如序列边界），使用选择性条件化：
$$Z_{t+T}^{c,(i)} = \begin{cases} \tilde{Z}_{t+T}^{(i)}, & i \in \mathcal{S}^+ \\ \hat{Z}_{t+T}^{(i)}, & i \notin \mathcal{S}^+ \end{cases} \tag{5}$$

推理时未来观测不可用，Adapter 被完全绕过：$Z_{t+T}^c = \hat{Z}_{t+T}$。

#### LatentAlign：训练-推理差距的退火桥接

**这是 DriveFuture 最重要的训练策略创新**。核心问题是从训练时的"真实未来条件"到推理时的"自预测条件"存在分布偏移。LatentAlign 通过 Sigmoid 退火实现平滑过渡：

$$\boxed{\alpha(e) = 1 - \frac{1}{1 + \exp[-\gamma(e - e_0)]}, \quad e_0 = \eta E} \tag{6}$$

$$\boxed{\tilde{Z}_{t+T}^c = \alpha(e) \cdot Z_{t+T}^c + (1 - \alpha(e)) \cdot \hat{Z}_{t+T}}$$

其中：
- $e$：当前训练 epoch
- $e_{0}$：退火拐点（如 $e_{0} = 0.83E$）
- $\gamma$：温度参数（控制过渡陡峭程度）
- $\alpha(e)$：从 1 → 0 衰减的混合系数

**物理意义**：

| 训练阶段 | $\alpha(e)$ | 条件来源 | 效果 |
|----------|-------------|----------|------|
| **早期** ($e \ll e_{0}$) | $\approx 1$ | GT 未来潜在 | 稳定学习、快速建立语义基础 |
| **晚期** ($e \gg e_{0}$) | $\approx 0$ | 自预测未来潜在 | 匹配推理分布、消除 gap |
| **过渡期** ($e \approx e_{0}$) | $\approx 0.5$ | 混合 | 平滑过渡 |

---

### 3.3 Planning Decoder（规划解码器）

**功能**：基于当前场景潜在 $Z_{t}$ 和未来感知潜在 $Z_{t+T}^c$ 进行条件扩散轨迹生成。

#### 未来条件化扩散 Transformer (DiT)

轨迹用微分空间表示 $a = (\Delta x, \Delta y, \sin\theta, \cos\theta) \in \mathbb{R}^{T \times 4}$。前向扩散过程：
$$a_s = \sqrt{\bar{\alpha}_s} a_0 + \sqrt{1 - \bar{\alpha}_s} \epsilon, \quad \epsilon \sim \mathcal{N}(0, I) \tag{7}$$

噪声预测器 $\epsilon_\theta$ 是 DiT 架构，接收三个条件：

$$\boxed{\hat{\epsilon} = \epsilon_\theta\big(a_s, s, C_{scene}, Z_{t+T}^c\big)} \tag{8}$$

其中 $C_{scene} = [e_{s} \parallel Z_{t}]$ 是场景上下文（时间步嵌入 + 当前潜在）。

**Cross-Attention 顺序设计**：每个 DiT Block 先 Cross-Attend 到 $C_{scene}$（环境几何），再 Cross-Attend 到 $Z_{t+T}^c$（未来语义修正）。**先理解当前环境，再应用未来修正**。

**零初始化**：未来 Cross-Attention 的输出投影初始化为零——新模块在训练开始时表现为恒等映射，逐步学会利用 $Z_{t+T}^c$。

---

## 4. 训练与推理

### 4.1 训练目标

#### 扩散规划损失
$$L_{plan} = \mathbb{E}_{s,\epsilon,a_0}\left[ \|\epsilon - \epsilon_\theta(a_s, s, C_{scene}, \tilde{Z}_{t+T}^c)\|_2^2 \right] \tag{9}$$

#### BEV 语义辅助损失
防止 BEV 编码器坍缩为仅对轨迹回归有用的表示：
$$L_{bev} = \text{CE}(\hat{Y}_{bev}, Y_{bev}) \tag{10}$$

#### 总损失
$$\boxed{L = \lambda_{plan} L_{plan} + \lambda_{bev} L_{bev}} \tag{11}$$

其中 $\lambda_{plan} = \lambda_{bev} = 10$。

**与现有世界模型的核心区别**：

| | 现有世界模型 | DriveFuture |
|---|---|---|
| 训练目标 | $\min \mathbb{E}[D(f(Z_{t}, a_{t}), Z_{t+T})]$ — 在特征空间中最小化预测误差 | $\min \mathbb{E}[\lVert\epsilon - \epsilon_\theta(a_{s}, s, Z_{t}, f(Z_{t}; E_\tau))\rVert^2]$ — 轨迹去噪损失的梯度**直接塑造世界模型** |
| 未来潜在的作用 | 被动的重建目标 | 主动的规划条件 |
| 优化什么 | 未来状态能否被预测 | 未来信息是否改善轨迹去噪 |

> **关键洞察**：DriveFuture 不要求预测的未来潜在重建未来场景的每个视觉细节，只需保留规划器可以利用的未来信息——车道占用、路径可行性、碰撞相关的运动和交互。

---

### 4.2 推理：Progressive Foresight Guidance (PFG)

#### 问题：推理时的循环依赖

推理时无 GT 轨迹和未来观测，产生循环依赖：

$$\hat{Z}_{t+T} = f(Z_t; E_\tau), \quad \tau = \text{Decode}(Z_t, \hat{Z}_{t+T})$$

即：需要 $\tau$ 来计算 $\hat{Z}_{t+T}$，但 $\tau$ 本身是条件于 $\hat{Z}_{t+T}$ 的去噪输出。

#### PFG 解决方案：双源相位自适应引导

PFG 在每个去噪步计算**三个 CFG 分支**的未来潜在：

$$\begin{aligned} Z_{t+T}^{c,\varnothing} &= f(Z_t, E_\varnothing) &&\text{— 无条件} \\ Z_{t+T}^{c,kin} &= f(Z_t, \Psi(\tau_{kin})) &&\text{— 运动学引导} \\ Z_{t+T}^{c,tw} &= f(Z_t, \Psi(\tau_{tw})) &&\text{— Tweedie 自估计引导} \end{aligned} \tag{13}$$

得到三个噪声预测后，**相位依赖混合**：

$$\boxed{\tilde{\epsilon} = \hat{\epsilon}_\varnothing + w_{kin}(r)(\hat{\epsilon}_{kin} - \hat{\epsilon}_\varnothing) + w_{tw}(r)(\hat{\epsilon}_{tw} - \hat{\epsilon}_\varnothing)} \tag{14}$$

#### Tweedie 公式自估计

从当前噪声样本恢复干净轨迹估计：
$$\hat{a}_0^{(s)} = \frac{a_s - \sqrt{1 - \bar{\alpha}_s} \hat{\epsilon}}{\sqrt{\bar{\alpha}_s}}, \quad \tau_{tw} = \text{cumsum}(\hat{a}_0) \tag{12}$$

**Tweedie 误差分析**：若 $\hat{\epsilon} = \epsilon + \delta$，则：
$$\hat{a}_0^{(s)} - a_0 = -\frac{\sqrt{1 - \bar{\alpha}_s}}{\sqrt{\bar{\alpha}_s}} \delta$$

当 $\bar{\alpha}_s$ 小（高噪声），误差放大因子 $\sqrt{1-\bar{\alpha}_s}/\sqrt{\bar{\alpha}_s}$ 极大——解释了为什么 Tweedie 估计在高噪声时不可靠。

#### 余弦调度 envelope

引导权重采用余弦包络，产生平滑的交接：

$$w_{kin}(r) = \begin{cases} w_{kin}^{max} \cos\left(\frac{\pi}{2} \cdot \frac{r}{\beta}\right), & r < \beta \\ 0, & r \geq \beta \end{cases} \tag{15}$$

$$w_{tw}(r) = \begin{cases} 0, & r \leq \beta \\ \frac{w_{tw}^{max}}{2}\left[1 - \cos\left(\pi \cdot \frac{r - \beta}{1 - \beta}\right)\right], & r > \beta \end{cases}$$

默认参数：$w_{kin}^{max}=1.5, w_{tw}^{max}=2.5, \beta=0.7, \eta=0.3$（$\eta$ 控制两曲线重叠区）。

#### PFG 的三阶段直觉

| 去噪阶段 | $r$ 范围 | 主导源 | 原因 |
|----------|----------|--------|------|
| **高噪声** | $r < \beta$ | $\tau_{kin}$（运动学） | $a_{s}$ 接近高斯，Tweedie 估计不稳定；运动学提供稳定低频先验 |
| **中噪声** | $\beta \approx r$ | 平滑交接 | 两源共存，运动学正则 + 自估计开始可靠 |
| **低噪声** | $r > \beta$ | $\tau_{tw}$（Tweedie） | $\bar{\alpha}_s \approx 1$，自估计精确可信，主导最终精炼 |

---

## 5. 完整算法流程

### 训练步骤 (Algorithm 1)

```
1. 编码当前观测: Z_t, B_t ← E(F)
2. 运动学推演: τ_kin ← KinematicRollout(F.st)
3. 三模 dropout 选择条件 → 预测 Ẑ_{t+T}
4. [若有未来帧] 编码未来观测 → Cross-Attn Grounding → LatentAlign 混合
5. [若无未来帧] Z̃_{t+T} ← Ẑ_{t+T}
6. 前向扩散加噪 → 噪声预测 → L = 10||ε - ε̂||² + 10 L_BEV
```

### 推理步骤 (Algorithm 2)

```
1. 编码当前场景: Z_t ← E(o_t, s_t)
2. 运动学推演: τ_kin ← KinematicRollout(s_t)
3. 计算无条件 + 运动学条件未来潜在 (一次性)
4. for k = 1..100 (轨迹提议):
5.     从高斯噪声初始化 → S步去噪循环
6.     每步: 计算PFG权重 → 无条件预测 → 运动学校正 → Tweedie自估计校正
7.     累积差分重建完整轨迹
8. [可选] GTRS-Dense 评分器选择最优轨迹
```

---

## 6. 实验与关键结果

### 6.1 核心 Benchmark 性能

| Benchmark | 指标 | DriveFuture | 先前最佳 | 备注 |
|-----------|------|-------------|----------|------|
| **NAVSIM-v2 navhard** | EPDMS | **55.5** | 54.6 (DrivoR) | **2026年4月排名第1** |
| NAVSIM-v2 navtest | EPDMS* | **89.9** | 89.3 (Latent-WAM) | SOTA |
| NAVSIM-v1 navtest | PDMS | **90.7** | 91.3 (DriveWorld-VLA, VLA方法) | 世界模型方法中SOTA |

### 6.2 消融实验 (Table 4)

| 配置 | EPDMS | 关键发现 |
|------|-------|----------|
| 无未来帧 | 30.9 | 基线 |
| 直接 MSE 监督未来潜在 | 32.1 (+1.2) | **未来信息作为隐式规划条件远优于特征级回归目标** |
| DriveFuture (w/o PFG) | 34.6 (+3.7) | 未来条件化带来了显著提升 |
| 移除运动学 + GT 引导 | 32.0 (-2.6) | 双源 PFG 不仅是推理启发式，也改善了训练质量 |

**核心启示**：未来信息用于**隐式规划条件**（+3.7）远优于用作**特征级回归目标**（+1.2），验证了论文的核心主张——未来不应是被预测的对象，而应是影响当前决策的条件。

### 6.3 超参数敏感性 (Table 5)

| 参数 | 最优值 | EPDMS | 过小/过大均导致性能下降 |
|------|--------|-------|--------------------------|
| 未来时域 $t_{f}$ | 1.5s | 34.6 | 0.5→30.2, 1.0→31.2 |
| 查询数 $q_{s}$ | 16 | 34.6 | 4→28.2, 64→33.7 |
| 退火拐点 $e_{0}$ | 0.83 | 34.6 | 0.75→29.2, 0.95→28.9 |

### 6.4 与其他方法的相对提升 (Table 6)

| 方法 | EPDMS | DriveFuture 相对提升 |
|------|-------|---------------------|
| TransFuser | 23.1 | **+140.3%** |
| World4Drive | 34.9 | **+59.0%** |
| GTRS-E | 49.4 | +12.3% |
| DrivoR | 54.6 | +1.6% |

---

## 7. 核心贡献总结

### 贡献 1：识别了现有潜在世界模型的关键局限

**发现了"未来预测 vs 未来条件化"的本质区别**。现有模型只关心"未来状态能否被预测准确"，而忽视了更关键的问题——"未来信息能否改善当前决策"。这导致**当前-未来特征在潜在空间中纠缠不清**，模型更擅长模拟未来而不是学习面向规划的决策表示。

### 贡献 2：提出了"面向规划的远见学习"新范式

将自动驾驶从"预测未来会怎样"提升到"**用未来知识反向重塑当前决策**"的层次。具体实现为三个机制：

- **LatentAlign 退火桥接**：通过 Sigmoid 退火训练，让解码器从依赖 GT 未来平滑过渡到依赖自预测未来，优雅地消除训练-推理 gap
- **Cross-Attention Grounding**：以轨迹感知的方式提取 GT 未来证据，避免将未来信息在特征空间中直接回归（那样会带入规划无关的外观细节）
- **规划导向的端到端训练**：扩散去噪损失的梯度直接塑形世界模型（Eq. 11），使世界模型学会编码**对规划有用的未来信息**而非重建全部未来场景

### 贡献 3：提出了 PFG（Progressive Foresight Guidance）

这是一个创新的推理时引导机制，解决了推理时的**循环依赖问题**（轨迹意图 ↔ 未来预测）。PFG 的核心设计包括：

- **双源相位自适应**：运动学先验（低噪声稳定）和 Tweedie 自估计（高噪声不可靠）随去噪进度动态切换
- **余弦平滑交接**：两个引导源在重叠区平滑过渡，避免硬切换带来的轨迹跳变
- **误差感知调度**：基于 Tweedie 公式的误差分析（$\sqrt{1-\bar{\alpha}_s}/\sqrt{\bar{\alpha}_s}$ 放大因子），在高噪声阶段抑制不可靠的自估计

### 贡献 4：SOTA 实验验证

在 NAVSIM 全系列基准上验证了未来条件化潜在世界建模的有效性，**在最具挑战性的 navhard 赛道排名第一**，证明了该方法在闭环长尾场景中的鲁棒性。

---

## 8. 局限性与未来方向

- **依赖预测质量**：推理时使用自预测未来潜在，在高度不确定场景中预测误差可能影响规划
- **近期条件化**：主要聚焦近期未来。更长时域的未来建模可能进一步提升远见能力
- **未来方向**：不确定性感知的未来建模、更长时域条件化、面向精炼感知的 VLM 引导

---

## 9. 关键公式速查表

| 公式 | 编号 | 含义 |
|------|------|------|
| $\hat{Z}_{t+T} = f_\phi(Q_{f}; [Z_{t} \parallel E_\tau])$ | (1) | **轨迹条件化未来潜在预测** |
| 三模条件采样 ($p_{gt}, p_{kin}, p_\varnothing$) | (2) | 条件源随机化 |
| $\tau_{kin}$ 常加速度推演 | (3) | 运动学替代轨迹 |
| $\tilde{Z}_{t+T} = \text{MHA}(\text{LN}(\hat{Z}_{t+T}), Z_{t+T}, Z_{t+T})$ | (4) | **Cross-Attention 未来锚定** |
| 未来帧缺失 fallback | (5) | 选择性条件化 |
| $\tilde{Z}_{t+T}^c = \alpha(e) Z_{t+T}^c + (1-\alpha(e)) \hat{Z}_{t+T}$ | (6) | **LatentAlign 退火混合** |
| $a_{s} = \sqrt{\bar{\alpha}_s} a_{0} + \sqrt{1-\bar{\alpha}_s} \epsilon$ | (7) | 前向扩散加噪 |
| $\hat{\epsilon} = \epsilon_\theta(a_{s}, s, C_{scene}, Z_{t+T}^c)$ | (8) | **未来条件化噪声预测** |
| $L_{plan} = \mathbb{E}[\lVert\epsilon - \hat{\epsilon}\rVert_{2}^2]$ | (9) | 扩散规划损失 |
| $L_{bev} = \text{CE}(\hat{Y}_{bev}, Y_{bev})$ | (10) | BEV 语义辅助损失 |
| $L = \lambda_{plan} L_{plan} + \lambda_{bev} L_{bev}$ | (11) | 总训练目标 |
| $\hat{a}_0^{(s)} = (a_{s} - \sqrt{1-\bar{\alpha}_s}\hat{\epsilon})/\sqrt{\bar{\alpha}_s}$ | (12) | **Tweedie 公式自估计** |
| 三 CFG 分支未来潜在 | (13) | PFG 条件计算 |
| $\tilde{\epsilon} = \hat{\epsilon}_\varnothing + w_{kin}(\hat{\epsilon}_{kin} - \hat{\epsilon}_\varnothing) + w_{tw}(\hat{\epsilon}_{tw} - \hat{\epsilon}_\varnothing)$ | (14) | **PFG 引导噪声混合** |
| $w_{kin}(r), w_{tw}(r)$ 余弦调度 | (15) | 相位自适应权重 |
| $\tau^* = \arg\max_{\tau_{i}} \text{Score}_{PDM}(\tau_{i})$ | (16) | PDM 轨迹选择 |
| PDMS 计算公式 | (17) | NAVSIM-v1 评估指标 |
| EPDMS 计算公式 | (18) | NAVSIM-v2 扩展评估指标 |
| Navhard Stage-2 高斯加权聚合 | (19) | 两阶段评估聚合 |
| $\text{EPDMS}_{navhard} = s_{1} \cdot s_{2}$ | (20) | Navhard 最终得分 |

---

## 10. 与相关工作的关系

| 方法 | 与 DriveFuture 的关系 |
|------|----------------------|
| **LAW** [17] | 最早探索潜在空间未来预测，但仅作为辅助任务 |
| **World4Drive** [18] | 意图感知潜在规划，但未来状态仍是预测目标 |
| **WorldRFT** [19] | 引入强化微调，但未来信息仍未成为规划条件 |
| **DriveVLA-W0** [21] | 世界模型 + VLA，但未来建模侧重数据扩展 |
| **Latent-WAM** [63] | 潜在世界动作建模，最接近的同期工作 |

DriveFuture 与上述工作的**本质区别**：将未来潜在从"预测目标"重新定位为"规划条件"，并为此设计了配套的训练（LatentAlign）和推理（PFG）机制。
