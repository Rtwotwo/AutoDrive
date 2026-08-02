# GTRS: Generalized Trajectory Scoring for End-to-end Multimodal Planning 阅读笔记

> **论文标题**: Generalized Trajectory Scoring for End-to-end Multimodal Planning
> **arXiv**: 2506.06664v1, 2025-06-07
> **作者**: Zhenxin Li\*, Wenhao Yao\*, Zi Wang, Xinglong Sun, Joshua Chen, Nadine Chang, Maying Shen, Zuxuan Wu, Shiyi Lan, Jose M. Alvarez
> **机构**: NVIDIA Research + 复旦大学
> **项目主页**: https://github.com/NVlabs/GTRS
> **荣誉**: **Navsim v2 Challenge 冠军方案**
> **关键词**: 端到端多模态规划、轨迹评分器、词汇表泛化、扩散策略、传感器增强

---

## 1. 核心问题与创新动机

端到端多模态规划的标准流程：生成多条候选轨迹 $\to$ 评分器评分 $\to$ 选择最高分轨迹。现有方法分为两类：

| 类型 | 方法 | 优势 | 劣势 |
|------|------|------|------|
| **静态词汇表评分** | Hydra-MDP, ZTRS 等 | 覆盖广，粗粒度离散化好 | 无法细粒度适应，灵活性差 |
| **动态生成评分** | DiffusionDrive 等 | 精细精确，场景适配 | 训练仅见窄分布，无法泛化到未见轨迹 |

**GTRS 核心洞察**：一个鲁棒的轨迹评分器必须**同时在粗粒度和细粒度轨迹分布上训练**，才能发展出真正的泛化能力。

---

## 2. 方法详解：GTRS 的三大支柱

### 2.1 轨迹生成器：扩散策略 (Diffusion Policy, DP)

#### 动机

静态词汇表覆盖广但缺乏细粒度精度；需要动态生成器提供**安全关键场景中的精细轨迹提案**。

#### 方法

采用基于 Diffusion Policy [4] 的轨迹生成器，架构包含三部分：

1. **图像骨干 (Image Backbone)**：提取多视图图像特征
2. **BEV 编码器**：BEV Queries 通过 Transformer Encoder 关注图像特征 $\to$ BEV 特征表示
3. **扩散 Transformer (Diffusion Transformer)**：以 BEV 特征为条件，通过去噪过程生成 $N=100$ 条轨迹提案 $\mathcal{V}_{dp}$

#### 扩散公式

**DDPM 前向过程**：逐步向真值轨迹 $\tau_{0}$ 添加高斯噪声

$$q(\tau_t | \tau_{t-1}) = \mathcal{N}\left(\tau_t; \sqrt{1 - \beta_t}\tau_{t-1}, \beta_t I\right) \tag{2a}$$

可用重参数化直接表达任意时间步：

$$\tau_t = \sqrt{\bar{\alpha}_t}\tau_0 + \sqrt{1 - \bar{\alpha}_t}\epsilon, \quad \epsilon \sim \mathcal{N}(0, I) \tag{2b}$$

其中 $\bar{\alpha}_t = \prod_{s=1}^{t}(1 - \beta_{s})$，$\beta_{t}$ 为 DDPM 噪声调度。

**去噪网络训练目标**（ϵ-matching loss）：

$$\mathcal{L}_{\text{diff}} = \mathbb{E}_{t, \tau_0, \epsilon}\left[\|\epsilon_\theta(\tau_t, t, C_{\text{BEV}}) - \epsilon\|^2_2\right] \tag{2c}$$

其中 $C_{\text{BEV}}$ 为 BEV 编码器输出的 BEV 特征（作为扩散条件），$\epsilon_\theta$ 为 Diffusion Transformer 预测的噪声。

**轨迹输入归一化**：对真值轨迹航点做一阶差分转为速度序列，使数值分布更集中：

$$\tau_0^{\text{input}} = \left\{(x_{l+1} - x_l,\ y_{l+1} - y_l)\right\}_{l=1}^{L-1} \tag{2d}$$

#### 训练细节

- **BEV 分割头**（遵循 Transfuser [5]）：对 BEV 特征提供辅助监督
- **噪声调度**：DDPM scheduling [10]，100 步去噪
- **推理生成**：从 $\mathcal{N}(0, I)$ 采样噪声 $\tau_{T}$，经 100 步 DDPM 去噪生成 100 条轨迹提案 $\mathcal{V}_{dp}$
- 使用后视图 + 后左 + 后右视图构建 BEV

---

### 2.2 词汇表泛化评分器 (GTRS-Dense)

这是 GTRS 的**最核心创新**。

#### 关键设计：训练-推理词汇表不匹配

$$\boxed{\text{训练: } \mathcal{V}_{XL} \text{ (16,384 条)} \quad\longrightarrow\quad \text{推理: } \mathcal{V}_L \text{ (8,192 条)}}$$

**刻意制造不对称**，迫使模型学会泛化而非记忆特定轨迹。

#### 词汇表 Dropout (Vocabulary Dropout)

在训练时，每个 batch 从 $\mathcal{V}_{XL}$ 中**随机丢弃一半轨迹**。该策略同时达到三个目的：

| 效果 | 机制 |
|------|------|
| (1) 对齐训练/推理 token 数 | 训练时实际参与 token 数与推理一致 |
| (2) 制造分布偏移 | 迫使模型适应随机变化的轨迹分布 |
| (3) 正则化 | 防止过拟合特定轨迹模式 |

#### 架构

基于 Hydra-MDP [18] 但有关键改进：
- **图像骨干**：提取多视图图像特征
- **轨迹分词器 (Trajectory Tokenizer)**：将候选轨迹编码为特征 tokens
- **Transformer Decoder**：建模轨迹 tokens 与图像 tokens 的复杂交互
- **输出**：每条候选轨迹的评分

#### 评分器推理公式

**轨迹 Token 化**：将候选轨迹 $\tau^{(i)}$ 编码为特征表示

$$\mathbf{z}_i = \text{Tokenizer}\left(\tau^{(i)}\right), \quad \tau^{(i)} \in \mathcal{V} \tag{3a}$$

**Transformer Decoder 评分**：轨迹 tokens 作为 Query，图像 tokens 作为 Key/Value，通过交叉注意力建模轨迹-场景交互：

$$\text{Score}(\tau^{(i)}) = \text{MLP}\left(\text{CrossAttn}\left(Q=\mathbf{z}_i,\ K=\mathbf{F}_{\text{img}},\ V=\mathbf{F}_{\text{img}}\right)\right) \tag{3b}$$

其中 $\mathbf{F}_{\text{img}}$ 为图像骨干提取的多视图图像特征。

**推理时最优轨迹选择**：

$$\tau^{\star} = \arg\max_{\tau \in \mathcal{V}_{dp} \cup \mathcal{V}_L} \text{Score}(\tau) \tag{3c}$$

**设计哲学**：评分器仅在静态词汇表上训练 $\to$ 发展广泛泛化能力；推理时动态生成器提供场景特化精度。避免将扩散采样嵌入训练循环的计算开销和不稳定性。

---

### 2.3 传感器增强 + 精炼评分器 (GTRS-Aug)

#### 问题

传感器输入的多样性（视角变化、环境差异）导致评分器在域外场景中不可靠；安全关键场景中相似轨迹需要精细判别。

#### 2.3.1 结构化传感器扰动

对输入图像施加**受控的 2D 水平视角旋转**（非随机增强）：

- 目标：让模型在变化的观测条件下保持一致的轨迹评估
- 标签一致性：对训练真值施加相应变换

#### 2.3.2 精炼训练机制 (Refinement Training)

**仅训练时使用**：额外引入一个 Transformer Decoder，对 top-$k$ 最有希望的候选轨迹进行渐进式分数精炼。

核心是一个**自蒸馏 (Self-Distillation)** 框架，由模型自身的 EMA 副本提供软监督信号：

$$\boxed{\tilde{y}_i^m = \hat{y}_i^m + \text{clip}\left(s_{i,\text{teacher}}^m - y_i^m,\; -\delta^m,\; \delta^m\right)} \tag{1}$$

**符号含义**：

| 符号 | 含义 |
|------|------|
| $\tilde{y}_i^m$ | 精炼后的目标分数（用于监督精炼解码器） |
| $\hat{y}_i^m$ | 真实标签分数 (ground-truth score) |
| $s_{i,\text{teacher}}^m$ | Teacher 模型（EMA 副本）的预测分数 |
| $y_{i}^m$ | 当前模型的分数 |
| $\delta^m$ | 裁剪参数，确保精炼目标在真值合理范围内 |
| $m$ | 指标索引（NC, DAC, TTC 等子指标） |

**工作原理**：
- Teacher 模型 (EMA) 提供比 ground-truth 更平滑的软标签
- $\text{clip}(s_{\text{teacher}} - y, -\delta, \delta)$：如果 teacher 认为当前模型预测偏差大，则修正目标；但裁剪限制在 $[-\delta, \delta]$ 内防止偏离真值太远
- 本质是一种 **soft self-distillation + bounded correction** 机制

---

## 3. 推理时集成

训练完成后，轨迹生成器 DP 和两个评分器（GTRS-Dense / GTRS-Aug）在推理时组合：

```
传感器输入 → DP 生成 Vdp → Vdp ∪ VL → Tokenize → Scorer 评分 → argmax → 最优轨迹
```

**GTRS-E（最终集成方案）**：集成 GTRS-Dense 和 GTRS-Aug 共 6 个模型变体（3 种骨干 × 2 种评分器），对每个模型的分数取平均后 argmax：

$$\text{Score}_{\text{ensemble}}(\tau) = \frac{1}{6}\sum_{k=1}^{6} \text{Score}_k(\tau) \tag{3d}$$

$$\tau^{\star} = \arg\max_{\tau \in \mathcal{V}_{dp} \cup \mathcal{V}_L} \text{Score}_{\text{ensemble}}(\tau) \tag{3e}$$

---

## 4. 核心公式汇总

### 4.1 扩散轨迹生成 (DP)

**DDPM 前向过程**：

$$q(\tau_t | \tau_{t-1}) = \mathcal{N}\left(\tau_t; \sqrt{1 - \beta_t}\tau_{t-1}, \beta_t I\right) \tag{2a}$$

**重参数化**：

$$\tau_t = \sqrt{\bar{\alpha}_t}\tau_0 + \sqrt{1 - \bar{\alpha}_t}\epsilon, \quad \epsilon \sim \mathcal{N}(0, I) \tag{2b}$$

**去噪训练目标**：

$$\mathcal{L}_{\text{diff}} = \mathbb{E}_{t, \tau_0, \epsilon}\left[\|\epsilon_\theta(\tau_t, t, C_{\text{BEV}}) - \epsilon\|^2_2\right] \tag{2c}$$

**轨迹输入归一化**（一阶差分）：

$$\tau_0^{\text{input}} = \left\{(x_{l+1} - x_l,\ y_{l+1} - y_l)\right\}_{l=1}^{L-1} \tag{2d}$$

### 4.2 轨迹评分 (GTRS-Dense)

**轨迹 Token 化 + Transformer 评分**：

$$\mathbf{z}_i = \text{Tokenizer}\left(\tau^{(i)}\right) \tag{3a}$$

$$\text{Score}(\tau^{(i)}) = \text{MLP}\left(\text{CrossAttn}\left(Q=\mathbf{z}_i,\ K=\mathbf{F}_{\text{img}},\ V=\mathbf{F}_{\text{img}}\right)\right) \tag{3b}$$

**最优轨迹选择**：

$$\tau^{\star} = \arg\max_{\tau \in \mathcal{V}_{dp} \cup \mathcal{V}_L} \text{Score}(\tau) \tag{3c}$$

**多模型集成**：

$$\text{Score}_{\text{ensemble}}(\tau) = \frac{1}{6}\sum_{k=1}^{6} \text{Score}_k(\tau) \tag{3d}$$

### 4.3 词汇表泛化

**训练-推理不匹配**：

$$\mathcal{V}_{\text{train}} = \mathcal{V}_{XL}\ (16{,}384),\quad \mathcal{V}_{\text{infer}} = \mathcal{V}_L\ (8{,}192),\quad \mathcal{V}_{\text{dynamic}} = \mathcal{V}_{dp}\ (100)$$

**词汇表 Dropout**：

$$\mathcal{V}_{XL}^{\text{(batch)}} = \left\{\tau \in \mathcal{V}_{XL} \mid \text{Bernoulli}(p=0.5)=1\right\}$$

### 4.4 精炼训练 (GTRS-Aug)

**传感器扰动**：对输入图像施加受控水平旋转

$$I_{\text{aug}} = \text{Rotate}_{2D}(I, \theta),\quad \theta \sim \mathcal{U}(-\theta_{\max}, \theta_{\max})$$

**自蒸馏精炼目标**：

$$\tilde{y}_i^m = \hat{y}_i^m + \text{clip}\left(s_{i,\text{teacher}}^m - y_i^m,\; -\delta^m,\; \delta^m\right) \tag{1}$$

---

## 5. 关键设计选择总结

| 设计选择 | 说明 | 消融验证 |
|----------|------|----------|
| **超密集词汇表训练** | 16,384 条全面覆盖轨迹空间 | $\mathcal{V}_{XL}$ vs $\mathcal{V}_L$：泛化大幅提升 |
| **词汇表 Dropout** | 每 batch 随机丢弃一半轨迹 | 最佳结果 43.4 EPDMS，无 dropout 仅 42.0 |
| **训练-推理不匹配** | 训练 16K → 推理 8K | 故意制造分布偏移 $\to$ 鲁棒性 |
| **动态仅在推理时加入** | 训练不用 DP 样本 | 避免扩散采样嵌入训练的不稳定 |
| **视角旋转扰动** | 受控 2D 水平旋转 | 域外泛化显著提升 |
| **精炼自蒸馏** | EMA Teacher + Clip 修正 | +2.8 EPDMS over baseline |
| **模型集成** | 6 模型变体平均分数 | 49.4 EPDMS（冠军方案） |

---

## 6. 递进式消融路线 (Table 1)

| 方法 | 训练词汇 | 推理词汇 | EPDMS | 关键解释 |
|------|---------|---------|-------|----------|
| DP w/o Scorer | — | $\mathcal{V}_{dp}$ (Random) | 25.6 | 随机选：baseline 下限 |
| GTRS-Dense | $\mathcal{V}_{XL}$ | $\mathcal{V}_{dp}$ | 36.7 | ⚡ 零样本泛化：仅在静态集训练，却在动态集有效评分 (+11.1) |
| GTRS-Dense | $\mathcal{V}_{XL}$ | $\mathcal{V}_{XL}$ | 39.7 | 训练推理一致，泛化差 |
| GTRS-Dense | $\mathcal{V}_{XL}$ | $\mathcal{V}_{dp} \cup \mathcal{V}_{XL}$ | 40.8 | 动+静结合 +1.1 |
| GTRS-Dense | $\mathcal{V}_{XL}$ | $\mathcal{V}_{dp} \cup \mathcal{V}_L$ | 42.0 | 降低词汇复杂度 $\to$ 合成数据泛化更好 |
| **GTRS-Dense + Dropout** | $\mathcal{V}_{XL}$ (Dropout) | $\mathcal{V}_{dp} \cup \mathcal{V}_L$ | **43.4** | ✅ 最终最佳 |
| GTRS-Aug | $\mathcal{V}_L$ | $\mathcal{V}_{dp} \cup \mathcal{V}_L$ | **43.4** | 增强+精炼同样最佳 |

**关键结论**：
1. 仅在静态词汇表训练的评分器能**零样本**泛化到动态提案（36.7 > 25.6）
2. 词汇表 Dropout 是最关键改进（43.4 > 42.0）
3. GTRS-Aug 达到同等最佳，说明增强+精炼也极其有效

---

## 7. Navhard Benchmark 主要结果 (Table 2)

| 方法 | 骨干 | Stage 1 EPDMS | Stage 2 EPDMS | 总 EPDMS |
|------|------|:---:|:---:|:---:|
| PDM-Closed [6] | GT Perception | 51.3 | — | **51.3** |
| LTF [5] | ResNet34 | — | — | 23.1 |
| GTRS-Dense (best single) | ViT-L | — | — | 45.3 |
| GTRS-Aug (best single) | EVA-ViT-L | — | — | 44.7 |
| GTRS-E-Lite (2 model ensemble) | EVA-ViT-L | — | — | 46.6 |
| **GTRS-E (6 model ensemble)** | 混合 | — | — | **49.4** |

**GTRS-E 仅用传感器输入，接近使用真值感知的特权规划器 PDM-Closed (49.4 vs 51.3)**。

---

## 8. 训练配置

| 参数 | 值 |
|------|-----|
| GPU | 24×NVIDIA A100 |
| 训练数据 | Navtrain（Navhard 未用于训练） |
| Epochs | 20（评分器）/ 50（轨迹生成器 DP） |
| Batch Size | 528 |
| 学习率 | $2 \times 10^{-4}$ |
| Weight Decay | 0.0 |
| 输入图像 | 前视图 + 前左裁剪 + 前右裁剪拼接 |
| 评分器图像分辨率 | 512×2048（Dense）/ 256×1024（Aug） |
| DP 去噪步数 | 100 (DDPM) |
| DP 生成提案数 | $N=100$ |

---

## 9. 创新点总结

| # | 创新 | 类型 | 核心机制 |
|---|------|------|----------|
| 1 | **超密集词汇表 + 训练-推理不匹配** | 训练策略 | 训练 16K $\to$ 推理 8K，迫使泛化 |
| 2 | **词汇表 Dropout** | 正则化 | 每 batch 随机丢弃一半轨迹，防止过拟合 + 制造分布偏移 |
| 3 | **动态仅在推理时注入** | 架构设计 | 避免扩散采样嵌入训练的计算开销和不稳定性 |
| 4 | **结构化传感器扰动** | 数据增强 | 受控 2D 水平视角旋转，提升域外泛化 |
| 5 | **EMA Teacher 精炼训练** | 蒸馏 | 自蒸馏 soft label + Clip 有界修正 (公式 1) |
| 6 | **多模型集成评分** | 推理策略 | 6 个变体分数平均，最终冠军方案 |

---

## 10. 与 HDP / TOAD 的对比

| 维度 | HDP | TOAD | GTRS |
|------|-----|------|------|
| 方法类型 | 训练时改进（扩散生成） | 测试时优化（评分器搜索） | **训练时改进（评分器泛化）** |
| 核心对象 | 轨迹**生成器** | 轨迹**搜索器** | 轨迹**评分器** |
| 即插即用 | ❌ 需重新训练 | ✅ | ❌ 需重新训练 |
| 核心机制 | 扩散模型 + 混合损失 + RL | CEM + 冻结评分器 | 词汇表泛化 + Dropout + 精炼 |
| 扩散模型角色 | **直接生成最终轨迹** | 不使用 | **生成候选提案**（供评分器选择） |
| 数据需求 | 20M+ 帧 | 无需 | Navtrain |
| 推理范式 | 扩散去噪生成 | 评分器搜索优化 | 扩散生成候选 + 评分器选择 |
| 互补性 | **生成侧** | **评分/选择侧** | **评分器泛化侧** |

---

## 11. 对后续工作的启示

1. **"训练-推理不匹配"是有益的**：GTRS 刻意制造不匹配来增强泛化，这与通常追求的训练推理一致性原则相反——是一个反直觉但有效的设计。

2. **静态词汇表训练 + 动态推理**：评分器不需要在动态提案上训练也能泛化到动态提案。这避免了扩散采样嵌入训练的不稳定。

3. **TOAD 正好揭示了 GTRS 的弱点**：TOAD 论文指出 GTRS scorer 在 CEM 搜索中失败（因为它是在固定词汇表上训练的）。GTRS 的词汇表泛化虽然跨词汇表有效，但在完全自由的连续轨迹空间搜索中仍不可靠——这解释了为什么 TOAD 只能用 DrivoR 的**解耦**评分器。

4. **NVIDIA 的方案演进**：Hydra-MDP → GTRS → 此脉络体现了从"固定词汇评分"到"泛化词汇评分"的演进，但离"自由空间搜索评分"（TOAD 所需）还有距离。

---

*笔记日期: 2026-07-16*
