# ChainFlow-VLA: Causal Flow Planning with Vision-Language Models 阅读笔记

> **论文标题**: ChainFlow-VLA: Causal Flow Planning with Vision-Language Models
> **arXiv**: 2605.23270v1, 2026-05-22
> **作者**: Xiyang Wang\*, Xinlin Wang\*, Tingguang Zhou, Gong Chen, Xingtai Gui, Zhi Xu, Xiaolei Wu, Feiyang Tan, Hangning Zhou, Mu Yang
> **机构**: Afari Intelligent Drive (智行者) & Tianjin University & University of Macau
> **代码**: https://github.com/AFARI-Research/ChainFlowVLA
> **关键词**: 端到端自动驾驶、VLA、自回归生成、扩散模型、残差精炼、VLM语义引导

---

## 1. 核心思想与动机

### 1.1 现有方法的根本矛盾

当前端到端自动驾驶系统存在一个**深层的范式冲突**：

| 范式 | 优势 | 劣势 |
|------|------|------|
| **自回归 (AR) 模型** | 通过因果分解捕获交互感知的时间依赖 | 逐步解码导致误差累积，全局结构次优 |
| **扩散 (Diffusion) 模型** | 全局优化轨迹，多模态生成能力强 | 缺乏显式因果约束，交互/安全关键场景不可靠 |

**核心洞察**：现有方法将因果建模与全局优化视为两个独立范式，缺乏在统一轨迹分布中有原则地融合二者的方法。

### 1.2 VLM 集成方式的反思

论文分析了现有 VLM 集成到端到端驾驶的两类方法及其局限：

- **VLM 引导式 (Figure 1a)**：VLM 预测高层特征 → 下游 Action Expert 生成轨迹。**问题**：将丰富场景语义压缩为离散信号，形成信息瓶颈，限制细粒度轨迹优化。

- **特征级融合 (Figure 1b)**：VLM 特征与感知 Backbone 特征融合 → 统一 Action Expert 解码。**问题**：语义推理与物理轨迹生成松耦合，语义信息难以在规划阶段（最需要纠错的阶段）产生直接影响。

**论文的核心主张**：VLM 不应作为直接轨迹生成器，而应作为**关键精炼阶段的语义约束提供者**。

---

## 2. 方法：ChainFlow-VLA 统一概率框架

### 2.1 整体架构

ChainFlow-VLA 将轨迹规划建模为**统一的因果生成-全局精炼过程**（Figure 1c, Figure 2）：

```
多视图图像 + Prompt → VLM (InternVL 2B) → Hidden States h_VLM
                                                        ↓
BEV特征 → AR Generator (Chain) → K个轨迹Proposals → Diffusion Refiner (Flow) → 精炼轨迹
                                      (因果一致性)        (VLM引导残差修正)
```

### 2.2 概率公式推导

#### 任务定义

端到端轨迹规划建模为从观测到未来轨迹的多模态条件分布：

$$P(Y \mid O) \tag{1}$$

其中 $O$ 为多模态观测，$Y = \{y_t\}_{t=1}^{T}$ 为未来轨迹。

#### 自回归因果分解

AR 模型提供轨迹分布的因果分解：

$$P(Y_{AR} \mid O) = \prod_t P(y_t \mid y_{<t}, O) \tag{2}$$

#### 模式条件分布

AR 模型生成 $K$ 个轨迹提议 $\{Y_{AR}^{(k)}\}_{k=1}^{K}$，每个 $Y_{AR}^{(k)}$ 代表一个轨迹模式。在每个提议上条件化，问题归结为建模局部条件分布：

$$P(Y \mid Y_{AR}^{(k)}, O) \tag{3}$$

#### VLM 语义条件化

用 VLM 的隐状态 $h_{VLM}$ 参数化该条件分布：

$$P(Y \mid Y_{AR}^{(k)}, O) \approx P(Y \mid Y_{AR}^{(k)}, h_{VLM}) \tag{4}$$

#### 全概率混合公式（核心公式）

由全概率公式得到隐式混合分布：

$$\boxed{P(Y \mid O) \approx \sum_{k=1}^{K} P(Y \mid Y_{AR}^{(k)}, h_{VLM}) \cdot P(Y_{AR}^{(k)} \mid O)} \tag{5}$$

**该公式是整个框架的数学基石**：将轨迹生成分解为 AR 诱导的模式先验 $P(Y_{AR}^{(k)} \mid O)$ 与 VLM 条件的局部精炼 $P(Y \mid Y_{AR}^{(k)}, h_{VLM})$。

---

## 3. 两阶段实现

### 3.1 Stage 1 — Chain: 自回归轨迹生成

#### 序列因果预测

遵循 AR 分解，逐时间步建模：

$$p(y_t \mid y_{<t}, O) \tag{6}$$

引入强因果归纳偏置，确保时序一致且物理可行的 rollout。

#### 控制空间解码

每个时间步 $t$ 预测控制变量（加速度 $a_t$ 和转向角 $\delta_t$）：

$$(a_t^{(k)}, \delta_t^{(k)}) = \mathcal{H}(y_{<t}^{(k)}, O) \tag{7}$$

其中 $\mathcal{H}$ 是可学习的预测器。

#### 运动学自行车模型约束

通过运动学自行车模型（Bicycle Model）将控制量转换为下一状态：

$$y_t^{(k)} = \text{Bicycle}(y_{t-1}^{(k)}, a_t^{(k)}, \delta_t^{(k)}) \tag{8}$$

**设计意义**：运动学约束强制执行物理可行性，稳定长时域预测。

#### 多模态轨迹提议集

经过 $T$ 步解码后，得到 $K$ 条轨迹提议：

$$Y_{AR} = \{Y_{AR}^{(k)}\}_{k=1}^{K} \tag{9}$$

从建模角度看，该阶段完成了全局轨迹分布的**因果离散化**，为后续 Flow 精炼提供结构化初始化。

---

### 3.2 Stage 2 — Flow: VLM 引导的残差扩散

#### 核心设计：残差空间建模

Flow 模块**不在全局空间建模完整轨迹分布**，而是在每个 AR 提议的**局部残差空间**进行精炼。精炼轨迹表示为：

$$\boxed{Y = Y_{AR}^{(k)} + \Delta Y_k} \tag{10}$$

其中 $\Delta Y_k$ 是第 $k$ 个 AR 提议相对于专家轨迹的修正量。

#### 残差条件分布

Eq. (5) 中的局部条件分布在残差空间中实例化：

$$P(Y \mid Y_{AR}^{(k)}, h_{VLM}) = P(\Delta Y_k \mid Y_{AR}^{(k)}, h_{VLM}) \tag{11}$$

**范式转变**：将轨迹建模从**绝对生成**转为**语义修正**——关注"在当前环境下先验轨迹应如何被调整"。

#### 残差目标

给定专家轨迹 $Y^*$ 和第 $k$ 个 AR 提议，残差目标为：

$$\Delta Y_k = Y^* - Y_{AR}^{(k)} \tag{12}$$

#### 前向扩散过程

对残差目标加噪：

$$z_t^{(k)} = \sqrt{\bar{\alpha}_t} \Delta Y_k + \sqrt{1 - \bar{\alpha}_t} \epsilon, \quad \epsilon \sim \mathcal{N}(0, I) \tag{13}$$

#### 噪声预测（条件去噪）

扩散模型预测注入的噪声，条件包括时间步 $t$、自车状态 $c_{ego}$、VLM 隐状态 $h_{VLM}$ 和 AR 提议 $Y_{AR}^{(k)}$：

$$\boxed{\hat{\epsilon}^{(k)} = \epsilon_\theta(z_t^{(k)}, t, c_{ego}, h_{VLM}, Y_{AR}^{(k)})} \tag{14}$$

**VLM 隐状态通过 Cross-Attention 注入 DiT 的 Transformer 层**，使高层语义信息引导残差去噪过程。

#### 推理：DDIM 采样重建

使用 DDIM 过程采样残差 $\Delta \hat{Y}_k$，重建精炼轨迹：

$$\hat{Y}_k = Y_{AR}^{(k)} + \Delta \hat{Y}_k \tag{15}$$

---

### 3.3 Scorer（评分器）

采用评分头评估每条候选轨迹的效用分数，选择最高分轨迹作为最终输出。评分器作为轨迹分布上的**代理效用函数**。

---

### 3.4 训练目标与目标分配

#### Stage I — AR 模块训练

使用 WTA (Winner-Takes-All) 监督：

$$L_{\text{stage1}} = L_{\text{traj}} + \lambda_1 L_{\text{scorer}} \tag{16}$$

轨迹损失选择与专家轨迹最接近的模式。

#### Stage II — 扩散精炼器训练

$$L_{\text{stage2}} = \lambda_2 L_{\text{diff}} + \lambda_3 L_{\text{traj}} + \lambda_4 L_{\text{scorer}} \tag{17}$$

损失权重：$\lambda_1=1, \lambda_2=10, \lambda_3=20, \lambda_4=4$。

#### 非对称 WTA 分配

扩散监督中，专家轨迹匹配最近的 AR 提议：

$$k^* = \arg\min_k \|Y_{AR}^{(k)} - Y^*\|_2 \tag{18}$$

扩散目标在该选定的 AR 条件模式下计算：

$$L_{\text{diff}} = \|\epsilon - \hat{\epsilon}\|_2^2 \tag{19}$$

**设计精髓**：将模式选择与残差精炼分离，使扩散目标聚焦于 AR 提议周围的局部修正。

---

## 4. 实验与关键结果

### 4.1 NAVSIM v1 基准性能

| 方法 | PDMS | NC | DAC | EP | TTC | Comf. |
|------|------|-----|-----|-----|-----|-----|
| 人类驾驶员 (Oracle) | 94.8 | 100.0 | 100.0 | 87.5 | 100.0 | 100.0 |
| **ChainFlow-VLA (trainval)** | **94.8** | 99.2 | 99.0 | 91.9 | 97.2 | 99.9 |
| RAP-DINO (trainval) | 93.7 | 99.0 | 98.9 | 90.0 | 96.7 | 100.0 |
| DrivoR (trainval) | 93.7 | 99.0 | 98.9 | 90.0 | 96.7 | 100.0 |
| LatentVLA | 92.4 | 98.9 | 98.2 | 88.2 | 96.0 | 100.0 |

**结论**：ChainFlow-VLA 达到与人类驾驶水平 (94.8) 相当的 SOTA 性能。

### 4.2 消融实验

#### 组件贡献 (Table 2)

| ID | AR Generator | DiT Refiner | VLM Guidance | PDMS | EP |
|----|-------------|-------------|--------------|------|-----|
| 0 (DrivoR基线) | ✗ | ✗ | ✗ | 93.7 | 90.0 |
| 1 | ✓ | ✗ | ✗ | 94.0 (+0.3) | 90.8 |
| 2 | ✓ | ✓ | ✗ | 94.1 (+0.4) | 91.0 |
| **3 (Full)** | **✓** | **✓** | **✓** | **94.8 (+1.1)** | **91.9** |

**关键发现**：VLM 引导带来最大增益 (+1.1 PDMS)，主要体现在 Ego Progress (EP) 从 90.0 → 91.9 的显著提升。

#### DiT 设计选择 (Table 3)

- **残差空间 vs 轨迹空间建模**：残差空间 (94.72) >> 轨迹空间 (92.89)
- **VLM 引导源**：环境+轨迹 QA SFT (94.72) > 动作 QA (94.11)

#### 去噪步数 (Table 4)

| N_step | 2 | 4 | 8 | 12 | 16 |
|--------|---|---|---|-----|-----|
| PDMS | 94.68 | 94.72 | 94.74 | **94.85** | 94.67 |

默认使用 4 步以平衡性能与效率。

### 4.3 ChainFlow 泛化性 (Table 5)

将 ChainFlow 模块集成到不同 Backbone（**无需 VLM 特征**）：

- **DiffusionDrive + ChainFlow**：88.1 → 88.9（仅用 6 modes vs 原版 20 modes）
- **iPad + ChainFlow**：91.7 → 92.7

**结论**：ChainFlow 是一个**通用的、即插即用的 Action Expert 模块**。

---

## 5. 核心创新总结

1. **Chain-to-Flow 统一概率框架**：首次将 AR 因果生成与扩散全局精炼统一在同一个全概率混合公式 (Eq. 5) 中，从数学层面桥接两种互补范式。

2. **残差空间建模**：将轨迹生成从绝对空间转为残差空间 (Eq. 10-11)，使扩散模型聚焦于"如何修正 AR 提议"而非"从零生成轨迹"，显著提升学习效率。

3. **VLM 作为语义调节器而非生成器**：通过 VLM 隐状态注入 Cross-Attention 引导残差扩散 (Eq. 14)，使高层语义理解直接影响轨迹修正，而非仅作为特征提取器。

4. **运动学约束的 AR 解码**：在控制空间（加速度、转向角）解码并通过 Bicycle Model (Eq. 7-8) 转换，强制执行物理可行性。

5. **非对称 WTA 训练策略**：将模式选择与残差精炼解耦 (Eq. 18-19)，使扩散目标聚焦于局部修正。

---

## 6. 局限性与未来方向

- **VLM 引导可进一步优化**：当前 VLM 基于通用驾驶理解（环境理解 + 轨迹 QA）训练。由于 Flow 模块本质是轨迹精炼而非动作生成，**面向评分或评判的 VLM**（具备更强轨迹评估能力）可能与任务更匹配。
- **VLM 在扩散目标下未进一步优化**：VLM 隐状态直接使用，未在扩散损失下微调。
- 未来方向：设计面向精炼感知 (refinement-aware) 的 VLM 引导。

---

## 7. 关键公式速查表

| 公式 | 编号 | 含义 |
|------|------|------|
| $P(Y \mid O)$ | (1) | 轨迹条件分布定义 |
| $P(Y_{AR} \mid O) = \prod_t P(y_t \mid y_{<t}, O)$ | (2) | AR 因果分解 |
| $P(Y \mid Y_{AR}^{(k)}, O)$ | (3) | 模式条件分布 |
| $P(Y \mid Y_{AR}^{(k)}, O) \approx P(Y \mid Y_{AR}^{(k)}, h_{VLM})$ | (4) | VLM 语义条件近似 |
| $P(Y \mid O) \approx \sum_k P(Y \mid Y_{AR}^{(k)}, h_{VLM}) \cdot P(Y_{AR}^{(k)} \mid O)$ | (5) | **全概率混合公式（核心）** |
| $p(y_t \mid y_{<t}, O)$ | (6) | 逐步条件预测 |
| $(a_t^{(k)}, \delta_t^{(k)}) = \mathcal{H}(y_{<t}^{(k)}, O)$ | (7) | 控制变量预测 |
| $y_t^{(k)} = \text{Bicycle}(y_{t-1}^{(k)}, a_t^{(k)}, \delta_t^{(k)})$ | (8) | 运动学自行车模型约束 |
| $Y_{AR} = \{Y_{AR}^{(k)}\}_{k=1}^{K}$ | (9) | 多模态轨迹提议集 |
| $Y = Y_{AR}^{(k)} + \Delta Y_k$ | (10) | **残差轨迹表示** |
| $P(Y \mid Y_{AR}^{(k)}, h_{VLM}) = P(\Delta Y_k \mid Y_{AR}^{(k)}, h_{VLM})$ | (11) | 残差空间条件分布 |
| $\Delta Y_k = Y^* - Y_{AR}^{(k)}$ | (12) | 残差监督目标 |
| $z_t^{(k)} = \sqrt{\bar{\alpha}_t} \Delta Y_k + \sqrt{1 - \bar{\alpha}_t} \epsilon$ | (13) | 前向扩散加噪 |
| $\hat{\epsilon}^{(k)} = \epsilon_\theta(z_t^{(k)}, t, c_{ego}, h_{VLM}, Y_{AR}^{(k)})$ | (14) | **VLM 条件噪声预测** |
| $\hat{Y}_k = Y_{AR}^{(k)} + \Delta \hat{Y}_k$ | (15) | DDIM 采样重建 |
| $L_{\text{stage1}} = L_{\text{traj}} + \lambda_1 L_{\text{scorer}}$ | (16) | Stage I 损失 |
| $L_{\text{stage2}} = \lambda_2 L_{\text{diff}} + \lambda_3 L_{\text{traj}} + \lambda_4 L_{\text{scorer}}$ | (17) | Stage II 损失 |
| $k^* = \arg\min_k \|Y_{AR}^{(k)} - Y^*\|_2$ | (18) | 非对称 WTA 模式匹配 |
| $L_{\text{diff}} = \|\epsilon - \hat{\epsilon}\|_2^2$ | (19) | 扩散去噪损失 |

---

## 8. 技术架构图注记

Figure 2 展示了完整架构：
- **左侧**：多视图图像 → DINOv2 编码 → LLM (VLM) → Hidden States $h_{VLM}$
- **中上**：BEV Feature → MLP → Trajectory Query → Autoregressive Decoder Cell（含 Self-Attention + FFN + Bicycle Motion Model）
- **中下**：AR Proposals + VLM Hidden States → DiT Block ×N（含 Self-Attention + Cross-Attention + AdaLN）→ 残差去噪
- **右侧**：精炼轨迹 + Ego Status → Scorer → 最终轨迹选择

VLM 训练时额外包含：场景感知与描述、交通状态评估、关键交通元素识别、运动规划与预测等辅助任务（仅训练阶段）。
