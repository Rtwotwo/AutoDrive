# Awesome Autonomous Driving Research

A curated research collection for end-to-end autonomous driving, driving world models, vision-language-action models, and public evaluation benchmarks. The catalog is built from a Zotero library and currently contains **172 unique papers**.

Last updated: 2026-09-23. Paper metadata should be checked against the latest arXiv or publisher version before citation.

## Table of Contents

- [Papers](#papers)
  - [End-to-End Autonomous Driving](#end-to-end-autonomous-driving)
  - [Vision-Language-Action Models](#vision-language-action-models)
  - [Driving World Models](#driving-world-models)
- [Public Datasets and Benchmarks](#public-datasets-and-benchmarks)
- [Leaderboard](#leaderboard)
- [Contributing](#contributing)
- [License](#license)

## Papers

### End-to-End Autonomous Driving

#### Imitation, Distillation & Privileged Learning

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **BEV-Planner** — BEV-Planner: Is Ego Status All You Need for Open-Loop End-to-End Autonomous Driving? | CVPR 2024 | `BEV` | [Paper](https://arxiv.org/abs/2312.03031) | [Code](https://github.com/NVlabs/BEV-Planner) | — |
| **TransFuser** — TransFuser: Imitation with Transformer-Based Sensor Fusion for Autonomous Driving | 2022 | `BEV` | [Paper](https://arxiv.org/abs/2205.15997) | — | — |

#### Unified Perception-Prediction-Planning

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **MiMo-Embodied** — MiMo-Embodied: X-Embodied Foundation Model Technical Report | 2026 | `Unified Perception-Prediction-Planning` | [Paper](https://arxiv.org/abs/2511.16518) | [Code](https://github.com/XiaomiMiMo/MiMo-Embodied) | [Project](https://huggingface.co/XiaomiMiMo/MiMo-Embodied-7B) |
| **ETA** — ETA: Efficiency through Thinking Ahead, A Dual Approach to Self-Driving with Large Models | ICCV 2025 | `Unified Perception-Prediction-Planning` | [Paper](https://arxiv.org/abs/2506.07725) | [Code](https://github.com/opendrivelab/ETA) | — |

#### Sparse, Vector & Token Representations

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **COMPACT-VA** — COMPACT-VA: Planning-aligned Token Compression for Long-Context Autonomous Driving | 2026 | `Closed-Loop` · `Distillation` | [Paper](https://arxiv.org/abs/2606.07464) | — | — |
| **FlowAD** — FlowAD: Ego-Scene Interactive Modeling for Autonomous Driving | 2026 | `Simulation` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2603.13399) | — | — |
| **Bridging Past and Future** — BridgeAD: Bridging Past and Future End-to-End Autonomous Driving with Historical Prediction and Planning | CVPR 2025 | `Closed-Loop` · `BEV` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2503.14182) | — | — |
| **Don't Shake the Wheel** — MomAD: Don't Shake the Wheel Momentum-Aware Planning in End-to-End Autonomous Driving | 2025 | `Sparse` | [Paper](https://arxiv.org/abs/2503.03125) | [Code](https://github.com/adept-thu/MomAD) | — |
| **DriveTransformer** — DriveTransformer: Unified Transformer for Scalable End-to-End Autonomous Driving | ICLR 2025 | `Closed-Loop` · `BEV` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2503.07656) | — | — |
| **HiP-AD** — HiP-AD: Hierarchical and Multi-Granularity Planning with Deformable Attention for Autonomous Driving in a Single Decoder | 2025 | `Closed-Loop` · `BEV` | [Paper](https://arxiv.org/abs/2503.08612) | — | — |
| **UniLION** — UniLION: Towards Unified Autonomous Driving Model with Linear Group RNNs | 2025 | `3D Occupancy` · `BEV` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2511.01768) | [Code](https://github.com/happinesslz/UniLION) | — |
| **VADv2** — VADv2: End-to-End Vectorized Autonomous Driving via Probabilistic Planning | 2024 | `Closed-Loop` | [Paper](https://arxiv.org/abs/2402.13243) | — | [Project](https://hgao-cv.github.io/VADv2) |
| **UniAD** — UniAD: Planning-oriented Autonomous Driving | CVPR 2023 | `Sparse` | [Paper](https://arxiv.org/abs/2212.10156) | — | [Project](https://opendrivelab.github.io/UniAD/) |
| **VAD** — VAD: Vectorized Scene Representation for Efficient Autonomous Driving | ICCV 2023 | `3D Occupancy` · `Safety` | [Paper](https://arxiv.org/abs/2303.12077) | [Code](https://github.com/hustvl/VAD) | — |

#### Trajectory Scoring & Selection

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **CLOVER** — CLOVER: Closed-Loop Value Estimation and Ranking for End-to-End Autonomous Driving Planning | 2026 | `Closed-Loop` · `Trajectory Scoring` · `Distillation` | [Paper](https://arxiv.org/abs/2605.15120) | [Code](https://github.com/WilliamXuanYu/CLOVER) | — |
| **Driving on Registers, Reasoning on Risk** — Driving on Registers, Reasoning on Risk: Risk-Aware Occupancy for Register-Based End-to-End Autonomous Driving | 2026 | `3D Occupancy` · `Sparse Representation` · `Reasoning` | [Paper](https://arxiv.org/abs/2609.21486) | — | — |
| **DrivoR** — DrivoR: Driving on Registers | 2026 | `Closed-Loop` · `Trajectory Scoring` · `Safety` | [Paper](https://arxiv.org/abs/2601.05083) | — | — |
| **MOSAIC** — MOSAIC: Scaling-Aware Data Selection for End-to-End Autonomous Driving Systems | CVPR 2026 | `Trajectory Scoring` | [Paper](https://arxiv.org/abs/2604.08366) | — | — |
| **NTR** — NTR: Neural Token Reconstruction for Scene Token Bottleneck in End-to-End Driving | 2026 | `Trajectory Scoring` · `Distillation` | [Paper](https://arxiv.org/abs/2605.31116) | — | — |
| **SparseDriveV2** — SparseDriveV2: Scoring is All You Need for End-to-End Autonomous Driving | 2026 | `Trajectory Scoring` · `Sparse Representation` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2603.29163) | [Code](https://github.com/swc-17/SparseDriveV2) | — |
| **TOAD** — TOAD: Test-Time Trajectory Optimization for Autonomous Driving | 2026 | `Closed-Loop` · `Trajectory Scoring` | [Paper](https://arxiv.org/abs/2606.07170) | — | [Project](https://valeoai.github.io/TOAD/) |
| **DriveSuprim** — DriveSuprim: Towards Precise Trajectory Selection for End-to-End Planning | AAAI 2026 | `Trajectory Scoring` · `Distillation` · `Safety` | [Paper](https://arxiv.org/abs/2506.06659) | — | — |
| **iPad** — iPad: Iterative Proposal-centric End-to-End Autonomous Driving | 2025 | `BEV` · `Safety` | [Paper](https://arxiv.org/abs/2505.15111) | [Code](https://github.com/Kguo-cs/iPad) | — |
| **ZTRS** — ZTRS: Zero-Imitation End-to-end Autonomous Driving with Trajectory Scoring | 2025 | `Reinforcement Learning` · `Closed-Loop` · `Trajectory Scoring` | [Paper](https://arxiv.org/abs/2510.24108) | [Code](https://github.com/woxihuanjiangguo/ZTRS) | — |
| **Hydra-MDP** — Hydra-MDP: End-to-end Multimodal Planning with Multi-target Hydra-Distillation | CVPR 2024 | `Distillation` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2406.06978) | [Code](https://github.com/NVlabs/Hydra-MDP) | — |
| **SparseDrive** — SparseDriveV1: End-to-End Autonomous Driving via Sparse Scene Representation | 2024 | `BEV` · `Sparse Representation` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2405.19620) | [Code](https://github.com/swc-17/SparseDrive) | — |

#### Diffusion, Flow & Generative Planning

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **GuideFlow** — GuideFlow: Constraint-Guided Flow Matching for Planning in End-to-End Autonomous Driving | 2026 | `Flow Matching` · `Multi-Modal` · `Safety` | [Paper](https://arxiv.org/abs/2511.18729) | [Code](https://github.com/liulin815/GuideFlow) | — |
| **HDP** — HDP: Unleashing the Potential of Diffusion Models for End-to-End Autonomous Driving | 2026 | `Diffusion` · `Reinforcement Learning` · `Simulation` | [Paper](https://arxiv.org/abs/2602.22801) | — | — |
| **LAP** — LAP: Fast LAtent Diffusion Planner for Autonomous Driving | 2026 | `Diffusion` · `Closed-Loop` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2512.00470) | — | — |
| **MeanFuser** — MeanFuser: Fast One-Step Multi-Modal Trajectory Generation and Adaptive Reconstruction via MeanFlow for End-to-End Autonomous Driving | CVPR 2026 | `Flow Matching` · `Closed-Loop` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2602.20060) | [Code](https://github.com/wjl2244/MeanFuser) | — |
| **PlannerRFT** — PlannerRFT: Reinforcing Diffusion Planners through Closed-Loop and Sample-Efficient Fine-Tuning | 2026 | `Diffusion` · `Reinforcement Learning` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2601.12901) | — | — |
| **RAD-2** — RADV2: Scaling Reinforcement Learning in a Generator-Discriminator Framework | 2026 | `Diffusion` · `Reinforcement Learning` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2604.15308) | — | — |
| **ReflectDrive-2** — ReflectDrive-2: Reinforcement-Learning-Aligned Self-Editing for Discrete Diffusion Driving | 2026 | `Diffusion` · `Reinforcement Learning` | [Paper](https://arxiv.org/abs/2605.04647) | — | — |
| **World Engine** — World Engine: Towards the Era of Post-Training for Autonomous Driving | 2026 | `Reinforcement Learning` · `Safety` | [Paper](https://arxiv.org/abs/2606.19836) | — | [Project](https://opendrivelab.com/WorldEngine/) |
| **DiffRefiner** — DiffRefiner: Coarse to Fine Trajectory Planning via Diffusion Refinement with Semantic Interaction for End to End Autonomous Driving | AAAI 2026 | `Diffusion` | [Paper](https://arxiv.org/abs/2511.17150) | — | — |
| **DiffSemanticFusion** — DiffSemanticFusion: Semantic Raster BEV Fusion for Autonomous Driving via Online HD Map Diffusion | 2025 | `Diffusion` · `BEV` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2508.01778) | [Code](https://github.com/SunZhigang7/DiffSemanticFusion) | — |
| **DiffusionDrive** — DiffusionDriveV1: Truncated Diffusion Model for End-to-End Autonomous Driving | CVPR 2025 | `Diffusion` | [Paper](https://arxiv.org/abs/2411.15139) | [Code](https://github.com/hustvl/DiffusionDrive) | — |
| **DiffusionDriveV2** — DiffusionDriveV2: Reinforcement Learning-Constrained Truncated Diffusion Modeling in End-to-End Autonomous Driving | 2025 | `Diffusion` · `Reinforcement Learning` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2512.07745) | [Code](https://github.com/hustvl/DiffusionDriveV2) | — |
| **DistillDrive** — DistillDrive: End-to-End Multi-Mode Autonomous Driving Distillation by Isomorphic Hetero-Source Planning Model | 2025 | `Reinforcement Learning` · `Closed-Loop` · `Distillation` | [Paper](https://arxiv.org/abs/2508.05402) | [Code](https://github.com/YuruiAI/DistillDrive) | — |
| **EvaDrive** — EvaDrive: Evolutionary Adversarial Policy Optimization for End-to-End Autonomous Driving | 2025 | `Diffusion` · `Reinforcement Learning` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2508.09158) | — | — |
| **GoalFlow** — GoalFlow: Goal-Driven Flow Matching for Multimodal Trajectories Generation in End-to-End Autonomous Driving | 2025 | `Diffusion` · `Flow Matching` · `Trajectory Scoring` | [Paper](https://arxiv.org/abs/2503.05689) | [Code](https://github.com/YvanYin/GoalFlow) | — |
| **GTRS** — GTRS: Generalized Trajectory Scoring for End-to-end Multimodal Planning | CVPR 2025 | `Diffusion` · `Trajectory Scoring` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2506.06664) | [Code](https://github.com/NVlabs/GTRS) | — |
| **TrajFlow** — TrajFlow: Multi-modal Motion Prediction via Flow Matching | IROS 2025 | `Flow Matching` · `Trajectory Scoring` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2506.08541) | — | [Project](https://traj-flow.github.io/) |
| **TrajHF** — TrajHF: Learning Personalized Driving Styles via Reinforcement Learning from Human Feedback | 2025 | `Reinforcement Learning` · `Multi-Modal` · `Safety` | [Paper](https://arxiv.org/abs/2503.10434) | — | — |
| **TransDiffuser** — TransDiffuser: Diverse Trajectory Generation with Decorrelated Multi-modal Representation for End-to-end Autonomous Driving | 2025 | `Diffusion` · `Closed-Loop` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2505.09315) | — | — |

#### Reinforcement Learning & Post-Training

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **123D** — 123D: Unifying Multi-Modal Autonomous Driving Data at Scale | 2026 | `Reinforcement Learning` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2605.08084) | [Code](https://github.com/kesai-labs/py123d) | — |
| **Gigapixel** — Gigapixel: Scaling Self-Play for End-to-End Driving | 2026 | `Closed-Loop` · `BEV` · `Simulation` | [Paper](https://arxiv.org/abs/2606.19641) | — | — |

#### Robustness, Safety & Test-Time Adaptation

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **AlignDrive** — AlignDrive: Aligned Lateral-Longitudinal Planning for End-to-End Autonomous Driving | 2026 | `Reasoning` · `Safety` | [Paper](https://arxiv.org/abs/2601.01762) | — | — |
| **PCM** — PCM: A Generalizable Physics-guided Causal Model for Trajectory Prediction in Autonomous Driving | ICRA 2026 | `Robustness` | [Paper](https://arxiv.org/abs/2602.13936) | [Code](https://github.com/ZY-Zong/Physics-guided-Causal-Model) | — |
| **PriorEye** — PriorEye: Geospatial Visual Priors for End-to-End Autonomous Driving | ECCV 2026 | `Robustness` | [Paper](https://arxiv.org/abs/2606.31830) | — | [Project](https://ori-mrg.github.io/PriorEye) |
| **GaussianFusion** — GaussianFusion: Gaussian-Based Multi-Sensor Fusion for End-to-End Autonomous Driving | NEURIPS 2025 | `BEV` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2506.00034) | [Code](https://github.com/Say2L/GaussianFusion) | — |
| **GEMINUS** — GEMINUS: Dual-aware Global and Scene-Adaptive Mixture-of-Experts for End-to-End Autonomous Driving | 2025 | `Closed-Loop` | [Paper](https://arxiv.org/abs/2507.14456) | [Code](https://github.com/newbrains1/GEMINUS) | — |
| **Hydra-MDP++** — Hydra-MDP++: Advancing End-to-End Driving via Expert-Guided Hydra-Distillation | 2025 | `Distillation` | [Paper](https://arxiv.org/abs/2503.12820) | [Code](https://github.com/NVlabs/Hydra-MDP) | — |
| **LEAD** — LEAD & LTFv6: Minimizing Learner-Expert Asymmetry in End-to-End Driving | 2025 | `Closed-Loop` · `Simulation` | [Paper](https://arxiv.org/abs/2512.20563) | [Code](https://github.com/autonomousvision/lead) | — |
| **NAVSIM** — NAVSIM: Pseudo-Simulation for Autonomous Driving | CORL 2025 | `Closed-Loop` · `Simulation` · `Safety` | [Paper](https://arxiv.org/abs/2506.04218) | [Code](https://github.com/autonomousvision/navsim) | — |
| **Spatial Retrieval AD** — Spatial Retrieval AD: Spatial Retrieval Augmented Autonomous Driving | 2025 | `Robustness` | [Paper](https://arxiv.org/abs/2512.06865) | — | [Project](https://spatialretrievalad.github.io/) |
| **ST-P3** — ST-P3: End-to-end Vision-based Autonomous Driving via Spatial-Temporal Feature Learning | ECCV 2022 | `Closed-Loop` · `BEV` · `Simulation` | [Paper](https://arxiv.org/abs/2207.07601) | [Code](https://github.com/OpenPerceptionX/ST-P3) | — |

#### Cooperative & Multi-Agent Driving

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **UniMM-V2X** — UniMM-V2X: MoE-Enhanced Multi-Level Fusion for End-to-End Cooperative Autonomous Driving | 2025 | `BEV` | [Paper](https://arxiv.org/abs/2511.09013) | — | — |

#### Driving Datasets, Benchmarks & Evaluation

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **NAVSIM** — NAVSIM: Data-Driven Non-Reactive Autonomous Vehicle Simulation and Benchmarking | NEURIPS 2024 | `Closed-Loop` · `BEV` · `Simulation` | [Paper](https://arxiv.org/abs/2406.15349) | [Code](https://github.com/autonomousvision/navsim) | — |

### Vision-Language-Action Models

#### End-to-End VLA

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **DriveMoE** — DriveMoE: Mixture-of-Experts for Vision-Language-Action Model in End-to-End Autonomous Driving | 2025 | `VLA` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2505.16278) | — | [Project](https://thinklab-sjtu.github.io/DriveMoE/) |

#### Dual-System VLM + Planner

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **HybridDriveVLA** — HybridDriveVLA: From Representational Complementarity to Dual Systems: Synergizing VLM and Vision-Only Backbones for End-to-End Driving | 2026 | `Diffusion` · `VLA` | [Paper](https://arxiv.org/abs/2602.10719) | — | — |
| **Plug-and-Play** — Plug-and-Play: Plug-and-Play Traffic Element Awareness for End-to-End Autonomous Driving | 2026 | `Diffusion` · `VLA` · `Trajectory Scoring` | [Paper](https://arxiv.org/abs/2608.18035) | — | — |

#### VLA Reasoning & Reinforcement Learning

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **AutoDrivetextbackslashtext-Ptextasciicircum3** — AutoDrive-Ptextasciicircum3: Unified Chain of Perception-Prediction-Planning Thought via Reinforcement Fine-Tuning | ICLR 2026 | `Reinforcement Learning` · `VLM` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2603.28116) | [Code](https://github.com/haha-yuki-haha/AutoDrive-P3) | — |
| **BrainWAM** — BrainWAM: Action-Space Coordination of Semantic Priors and Predictive Dynamics for Autonomous Driving | 2026 | `World Model` · `VLA` · `Reasoning` | [Paper](https://arxiv.org/abs/2608.12854) | — | — |
| **ChainFlow-VLA** — ChainFlow-VLA: Causal Flow Planning with Vision-Language Models | 2026 | `Diffusion` · `VLM` · `Reasoning` | [Paper](https://arxiv.org/abs/2605.23270) | [Code](https://github.com/AFARI-Research/ChainFlow-VLA) | — |
| **Devil is in Narrow Policy** — CuriousVLA: Devil is in Narrow Policy Unleashing Exploration in Driving VLA Models | CVPR 2026 | `Reinforcement Learning` | [Paper](https://arxiv.org/abs/2603.06049) | [Code](https://github.com/Mashiroln/curious_vla.git) | — |
| **ELF-VLA** — ELF-VLA: Unleashing VLA Potentials in Autonomous Driving via Explicit Learning from Failures | 2026 | `Reinforcement Learning` · `VLA` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2603.01063) | — | — |
| **EvoDriveVLA** — EvoDriveVLA: Evolving Driving VLA Models via Collaborative Perception-Planning Distillation | 2026 | `VLA` · `Closed-Loop` · `Distillation` | [Paper](https://arxiv.org/abs/2603.09465) | [Code](https://github.com/hey-cjj/EvoDriveVLA) | — |
| **HybridDriveVLA** — HybridDriveVLA: Vision-Language-Action Model with Visual CoT reasoning and ToT Evaluation for Autonomous Driving | 2026 | `VLA` · `Reasoning` | [Paper](https://openaccess.thecvf.com/content/CVPR2026/html/Bassole_HybridDriveVLA_Vision-Language-Action_Model_with_Visual_CoT_reasoning_and_ToT_Evaluation_CVPR_2026_paper.html) | — | — |
| **Learning from Mistakes** — TakeVLA: Learning from Mistakes: Post-Training for Driving VLA with Takeover Data | 2026 | `Reinforcement Learning` · `VLA` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2603.14972) | — | — |
| **WorkDrive** — WorkDrive: Roadwork Chain of Causation for Autonomous Driving | 2026 | `Reinforcement Learning` · `VLM` · `Reasoning` | [Paper](https://arxiv.org/abs/2607.14727) | — | — |
| **AlphaDrive** — AlphaDrive: Unleashing the Power of VLMs in Autonomous Driving via Reinforcement Learning and Reasoning | 2025 | `Reinforcement Learning` · `VLM` · `Reasoning` | [Paper](https://arxiv.org/abs/2503.07608) | [Code](https://github.com/hustvl/AlphaDrive) | — |
| **AutoVLA** — AutoVLA: A Vision-Language-Action Model for End-to-End Autonomous Driving with Adaptive Reasoning and Reinforcement Fine-Tuning | NEURIPS 2025 | `Reinforcement Learning` · `VLA` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2506.13757) | — | [Project](https://autovla.github.io/) |
| **Cosmos-Reason1** — Cosmos-Reason1: From Physical Common Sense To Embodied Reasoning | 2025 | `Reinforcement Learning` · `Reasoning` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2503.15558) | [Code](https://github.com/nvidia-cosmos/cosmos-reason1) | — |
| **OpenREAD** — OpenREAD: Reinforced Open-Ended Reasoning for End-to-End Autonomous Driving with LLM-as-Critic | 2025 | `Reinforcement Learning` · `VLM` · `Reasoning` | [Paper](https://arxiv.org/abs/2512.01830) | — | — |
| **ReflectDrive-1** — ReflectDrive-1: Discrete Diffusion for Reflective Vision-Language-Action Models in Autonomous Driving | 2025 | `Diffusion` · `Reinforcement Learning` · `VLA` | [Paper](https://arxiv.org/abs/2509.20109) | — | — |

#### Spatial, Temporal & 3D Grounding

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **DEFT-RLVR** — DEFT-RLVR: Deferred Exposure of Future Trajectories for Verifiable Reasoning in Autonomous Driving VLMs | 2026 | `VLA` · `VLM` · `Reasoning` | [Paper](https://arxiv.org/abs/2608.01755) | — | — |
| **DriveTeach-VLA** — DriveTeach-VLA: Teaching Vision-Language-Action Models What to See and Where to Look | ECCV 2026 | `VLA` · `Distillation` · `Reasoning` | [Paper](https://arxiv.org/abs/2607.01658) | [Code](https://github.com/ShivaTeam/DriveTeach-VLA) | — |
| **DVGT-2** — DVGT-2: Vision-Geometry-Action Model for Autonomous Driving at Scale | 2026 | `VLA` · `Closed-Loop` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2604.00813) | [Code](https://github.com/wzzheng/DVGT) | — |
| **FactorDrive** — FactorDrive: Adaptive Multi-Step Reasoning Driven by Planning-Critical Factors for End-to-End Autonomous Driving | 2026 | `VLM` · `Closed-Loop` · `Reasoning` | [Paper](https://arxiv.org/abs/2608.09591) | — | — |
| **From Foundation to Application** — LingBot-VLA 2.0: From Foundation to Application: Improving VLA Models in Practice | 2026 | `Reasoning` | [Paper](https://arxiv.org/abs/2607.06403) | [Code](https://github.com/robbyant/lingbot-vla-v2) | [Project](https://technology.robbyant.com/lingbot-vla-v2) |
| **HiST-VLA** — HiST-VLA: A Hierarchical Spatio-Temporal Vision-Language-Action Model for End-to-End Autonomous Driving | 2026 | `VLA` · `Closed-Loop` · `Reasoning` | [Paper](https://arxiv.org/abs/2602.13329) | — | — |
| **IKN** — IKN: Grounding Driving VLA via Inverse Kinematics | 2026 | `Diffusion` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2605.21061) | — | — |
| **LaST-VLA** — LaST-VLA: Thinking in Latent Spatio-Temporal Space for Vision-Language-Action in Autonomous Driving | 2026 | `Reinforcement Learning` · `World Model` · `VLA` | [Paper](https://arxiv.org/abs/2603.01928) | — | — |
| **Qwen-Drive-1.0** — Qwen-Drive-1.0: An Initial Step towards a Vision-Language Foundation Model for Autonomous Driving | 2026 | `VLM` · `Closed-Loop` · `3D Occupancy` | [Paper](https://arxiv.org/abs/2609.00111) | [Code](https://github.com/QwenLM/Qwen-Drive-1.0) | — |
| **SGDrive** — SGDrive: Scene-to-Goal Hierarchical World Cognition for Autonomous Driving | 2026 | `VLM` · `Reasoning` · `Safety` | [Paper](https://arxiv.org/abs/2601.05640) | — | — |
| **UniDriveVLA** — UniDriveVLA: Unifying Understanding, Perception, and Action Planning for Autonomous Driving | 2026 | `VLA` · `VLM` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2604.02190) | [Code](https://github.com/xiaomi-research/unidrivevla) | — |
| **VGGDrive** — VGGDrive: Empowering Vision-Language Models with Cross-View Geometric Grounding for Autonomous Driving | CVPR 2026 | `VLM` | [Paper](https://arxiv.org/abs/2602.20794) | — | — |
| **OccVLA** — OccVLA: Vision-Language-Action Model with Implicit 3D Occupancy Supervision | 2025 | `VLA` · `3D Occupancy` · `Reasoning` | [Paper](https://arxiv.org/abs/2509.05578) | — | — |
| **OpenDriveVLA** — OpenDriveVLA: Towards End-to-end Autonomous Driving with Large Vision Language Action Model | 2025 | `Multi-Modal` | [Paper](https://arxiv.org/abs/2503.23463) | — | — |
| **SpaceDrive** — SpaceDrive: Infusing Spatial Awareness into VLM-based Autonomous Driving | 2025 | `Closed-Loop` · `Reasoning` | [Paper](https://arxiv.org/abs/2512.10719) | — | — |
| **WAM-Flow** — WAM-Flow: Parallel Coarse-to-Fine Motion Planning via Discrete Flow Matching for Autonomous Driving | 2025 | `Diffusion` · `Flow Matching` · `VLA` | [Paper](https://arxiv.org/abs/2512.06112) | [Code](https://github.com/fudan-generative-vision/WAM-Flow) | — |

#### Efficient VLA & Deployment

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **Alpamayo-R1** — Alpamayo-R1: Bridging Reasoning and Action Prediction for Generalizable Autonomous Driving in the Long Tail | 2026 | `Diffusion` · `Reinforcement Learning` · `VLM` | [Paper](https://arxiv.org/abs/2511.00088) | [Code](https://github.com/NVlabs/alpamayo) | [Project](https://huggingface.co/nvidia/Alpamayo-R1-10B) |
| **AnchorVLA** — AnchorVLA: Bridging Discrete Decisions and Continuous Trajectories for Vision-Language-Action Planning | 2026 | `VLA` · `Closed-Loop` · `Reasoning` | [Paper](https://arxiv.org/abs/2607.03182) | — | — |
| **AutoMoT** — AutoMoT: A Unified Vision-Language-Action Model with Asynchronous Mixture-of-Transformers for End-to-End Autonomous Driving | 2026 | `VLA` · `VLM` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2603.14851) | — | [Project](https://automot-website.github.io/) |
| **ColaVLA** — ColaVLA: Leveraging Cognitive Latent Reasoning for Hierarchical Parallel Trajectory Planning in Autonomous Driving | CVPR 2026 | `VLA` · `VLM` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2512.22939) | — | [Project](https://pqh22.github.io/projects/ColaVLA/index.html) |
| **CRAFT** — CRAFT: Counterfactual-to-Interactive Reinforcement Fine-Tuning for Driving Policies | 2026 | `Reinforcement Learning` · `VLA` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2605.04470) | — | [Project](https://currychen77.github.io/CRAFT) |
| **DriveVLA-M0** — DriveVLA-M0: Failure-Aware Memory Augmentation for Autonomous Driving | 2026 | `VLA` · `Reasoning` | [Paper](https://arxiv.org/abs/2608.10413) | [Code](https://github.com/ZebinX/DriveVLA-M0) | — |
| **DynVLA** — DynVLA: Learning World Dynamics for Action Reasoning in Autonomous Driving | 2026 | `Reasoning` | [Paper](https://arxiv.org/abs/2603.11041) | — | [Project](https://yaoyao-jpg.github.io/dynvla) |
| **LatentVLA** — LatentVLA: Efficient Vision-Language Models for Autonomous Driving via Latent Action Prediction | 2026 | `VLA` · `VLM` · `Distillation` | [Paper](https://arxiv.org/abs/2601.05611) | — | — |
| **LinkVLA** — LinkVLA: Unifying Language-Action Understanding and Generation for Autonomous Driving | 2026 | `VLA` · `Closed-Loop` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2603.01441) | — | — |
| **NoRD** — NoRD: A Data-Efficient Vision-Language-Action Model that Drives without Reasoning | CVPR 2026 | `VLA` · `Reasoning` | [Paper](https://arxiv.org/abs/2602.21172) | — | — |
| **OneDrive** — OneDrive: Unified Multi-Paradigm Driving with Vision-Language-Action Models | 2026 | `VLA` · `VLM` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2604.17915) | [Code](https://github.com/Z1zyw/OneDrive) | — |
| **Post-Training in End-to-End Autonomous Driving** — Post-Training in End-to-End Autonomous Driving | 2026 | `VLA` · `Multi-Modal` · `Safety` | [Paper](https://arxiv.org/abs/2607.08072) | [Code](https://github.com/RYNing/Awesome-Post-Training-In-Autonomous-Driving-Papers) | — |
| **SparseOccVLA** — SparseOccVLA: Bridging Occupancy and Vision-Language Models via Sparse Queries for Unified 4D Scene Understanding and Planning | 2026 | `Diffusion` · `VLA` · `VLM` | [Paper](https://arxiv.org/abs/2601.06474) | — | — |
| **World** — World Simulation with Video Foundation Models for Physical AI | 2026 | `Reinforcement Learning` · `VLM` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2511.00062) | [Code](https://github.com/nvidia-cosmos/cosmos-predict2.5) | — |
| **WVM** — WVM: World Value Models for Robotic Manipulation | 2026 | `World Model` · `VLM` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2606.24742) | — | — |
| **DiffVLA** — DiffVLA: Vision-Language Guided Diffusion Planning for Autonomous Driving | 2025 | `Diffusion` · `BEV` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2505.19381) | — | — |
| **FastDriveVLA** — FastDriveVLA: Efficient End-to-End Driving via Plug-and-Play Reconstruction-based Token Pruning | AAAI 2026 | `VLA` · `Reasoning` | [Paper](https://arxiv.org/abs/2507.23318) | — | — |
| **LightEMMA** — LightEMMA: Lightweight End-to-End Multimodal Model for Autonomous Driving | 2025 | `VLM` · `Reasoning` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2505.00284) | [Code](https://github.com/michigan-traffic-lab/LightEMMA) | — |
| **ReCogDrive** — ReCogDrive: A Reinforced Cognitive Framework for End-to-End Autonomous Driving | 2025 | `Diffusion` · `VLM` · `Safety` | [Paper](https://arxiv.org/abs/2506.08052) | [Code](https://github.com/xiaomi-research/recogdrive) | — |

#### VLA Datasets, Benchmarks & Surveys

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **DriveReward** — DriveReward: A Comprehensive Dataset and Generative Vision-Language Reward Model for Autonomous Driving | 2026 | `Reinforcement Learning` · `VLM` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2606.08525) | — | — |

### Driving World Models

#### Video Generation & Neural Rendering

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **How Far Can 5,500 Hours of Driving Take You?** — NATIX: How Far Can 5,500 Hours of Driving Take You? A Scaling Law Analysis of Video Diffusion Models | 2026 | `Diffusion` · `Video Generation` | [Paper](https://arxiv.org/abs/2608.28404) | [Code](https://github.com/valeoai/VATIX) | — |
| **X-Foresight** — X-Foresight: A Joint Vision-Action Causal Forecasting Network via Predictive World Modeling | 2026 | `Diffusion` · `World Model` · `VLA` | [Paper](https://arxiv.org/abs/2605.24892) | — | — |
| **Epona** — EponaV1: Autoregressive Diffusion World Model for Autonomous Driving | ICCV 2025 | `Diffusion` · `World Model` · `Video Generation` | [Paper](https://arxiv.org/abs/2506.24113) | [Code](https://github.com/Kevin-thu/Epona/) | [Project](https://kevin-thu.github.io/Epona/) |

#### BEV, Occupancy & 3D World Modeling

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **Auto-JEPA** — Auto-JEPA: A Latent World Model of Continuous Intent for End-to-End Autonomous Driving | 2026 | `World Model` · `3D Occupancy` · `BEV` | [Paper](https://arxiv.org/abs/2607.29031) | — | — |
| **DeepSight** — DeepSight: Long-Horizon World Modeling via Latent States Prediction for End-to-End Autonomous Driving | 2026 | `World Model` · `VLM` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2605.10564) | [Code](https://github.com/hotdogcheesewhite/DeepSight) | — |
| **EponaV2** — EponaV2: Driving World Model with Comprehensive Future Reasoning | 2026 | `Flow Matching` · `World Model` · `Reasoning` | [Paper](https://arxiv.org/abs/2605.14696) | — | — |
| **ExploreVLA** — ExploreVLA: Dense World Modeling and Exploration for End-to-End Autonomous Driving | ECCV 2026 | `Reinforcement Learning` · `World Model` · `VLA` | [Paper](https://arxiv.org/abs/2604.02714) | — | [Project](https://zihaosheng.github.io/ExploreVLA/) |
| **GEM** — GEM: Gaussian Evolution Model for Occupancy Forecasting and Motion Planning | 2026 | `World Model` · `3D Occupancy` | [Paper](https://arxiv.org/abs/2605.17682) | — | — |
| **OWMDrive** — OWMDrive: Causality-Aware End-to-End Autonomous Driving via 4D Occupancy World Model | 2026 | `Diffusion` · `World Model` · `3D Occupancy` | [Paper](https://arxiv.org/abs/2606.30421) | — | — |
| **RAP** — RAP: 3D Rasterization Augmented End-to-End Planning | 2026 | `Closed-Loop` | [Paper](https://arxiv.org/abs/2510.04333) | — | [Project](https://alan-lanfeng.github.io/RAP/) |
| **ResWorld** — ResWorld: Temporal Residual World Model for End-to-End Autonomous Driving | ICLR 2026 | `World Model` · `BEV` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2602.10884) | [Code](https://github.com/mengtan00/ResWorld.git) | — |
| **Uni-World VLA** — Uni-World VLA: Interleaved World Modeling and Planning for Autonomous Driving | ECCV 2026 | `World Model` · `VLA` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2603.27287) | — | — |
| **UniDWM** — UniDWM: Towards a Unified Driving World Model via Multifaceted Representation Learning | 2026 | `Diffusion` · `World Model` · `Reasoning` | [Paper](https://arxiv.org/abs/2602.01536) | [Code](https://github.com/Say2L/UniDWM) | — |
| **X-World** — X-World: Controllable Ego-Centric Multi-Camera World Models for Scalable End-to-End Driving | 2026 | `World Model` · `Simulation` · `Video Generation` | [Paper](https://arxiv.org/abs/2603.19979) | — | — |
| **Xiaomi EV World Model** — Xiaomi EV World Model: A Joint World Model Integrating Reconstruction and Generation for Autonomous Driving | 2026 | `World Model` · `Closed-Loop` · `Simulation` | [Paper](https://arxiv.org/abs/2605.18137) | — | — |
| **ZYT-World** — ZYT-World: A Real-Time Controllable World Model for Closed-Loop Autonomous-Driving Simulation | 2026 | `World Model` · `VLA` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2609.21712) | — | — |
| **DriveVLA-W0** — DriveVLA-W0: World Models Amplify Data Scaling Law in Autonomous Driving | 2025 | `Diffusion` · `World Model` · `VLA` | [Paper](https://arxiv.org/abs/2510.12796) | — | — |
| **HERMES** — HERMES: A Unified Self-Driving World Model for Simultaneous 3D Scene Understanding and Generation | ICCV 2025 | `World Model` · `BEV` · `Reasoning` | [Paper](https://arxiv.org/abs/2501.14729) | [Code](https://github.com/LMD0311/HERMES) | — |
| **WorldMirror** — WorldMirror: Universal 3D World Reconstruction with Any-Prior Prompting | 2025 | `BEV` | [Paper](https://arxiv.org/abs/2510.10726) | — | — |
| **WoTE** — WoTE: End-to-End Driving with Online Trajectory Evaluation via BEV World Model | 2025 | `World Model` · `Closed-Loop` · `BEV` | [Paper](https://arxiv.org/abs/2504.01941) | [Code](https://github.com/liyingyanUCAS/WoTE) | — |
| **GaussianAD** — GaussianAD: Gaussian-Centric End-to-End Autonomous Driving | 2024 | `3D Occupancy` · `BEV` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2412.10371) | [Code](https://github.com/wzzheng/GaussianAD) | — |
| **OccWorld** — OccWorld: Learning a 3D Occupancy World Model for Autonomous Driving | 2023 | `World Model` · `3D Occupancy` · `Sparse Representation` | [Paper](https://arxiv.org/abs/2311.16038) | [Code](https://github.com/wzzheng/OccWorld) | — |

#### Latent World Models

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **Drive-JEPA** — Drive-JEPA: Video JEPA Meets Multimodal Trajectory Distillation for End-to-End Driving | 2026 | `World Model` · `Distillation` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2601.22032) | — | — |
| **DriveFuture** — DriveFuture: Future-Aware Latent World Models for Autonomous Driving | 2026 | `Diffusion` · `World Model` | [Paper](https://arxiv.org/abs/2605.09701) | — | [Project](https://huggingface.co/spaces/AGC2025/e2e-driving-navhard) |
| **DriveWorld-VLA** — DriveWorld-VLA: Unified Latent-Space World Modeling with Vision-Language-Action for Autonomous Driving | 2026 | `World Model` · `VLA` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2602.06521) | [Code](https://github.com/liulin815/DriveWorld-VLA.git) | — |
| **INTACT** — INTACT: Isomorphic Intent-to-Action Learning for Search-Free World Models | 2026 | `World Model` | [Paper](https://arxiv.org/abs/2607.26056) | — | — |
| **DriveLaW** — DriveLaW:Unifying Planning and Video Generation in a Latent Driving World | 2025 | `Diffusion` · `World Model` · `Video Generation` | [Paper](https://arxiv.org/abs/2512.23421) | — | — |
| **LAW** — LAW: Enhancing End-to-End Autonomous Driving with Latent World Model | ICLR 2025 | `World Model` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2406.08481) | [Code](https://github.com/BraveGroup/LAW) | — |

#### World-Action Models

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **4D-WAM** — 4D-WAM: 4D Consistent World Modeling for Autonomous Driving | 2026 | `World Model` · `World-Action` | [Paper](https://arxiv.org/abs/2608.10107) | — | — |
| **BehaviorWorldGen** — BehaviorWorldGen: Closing the Loop between Action Models and World Simulators via Controllable Behavior-Aware Structured World Generation | 2026 | `World-Action Models` | [Paper](https://arxiv.org/abs/2608.22187) | — | — |
| **Bridging Scene Generation and Planning** — WorldDrive: Bridging Scene Generation and Planning Driving with World Model via Unifying Vision and Motion Representation | 2026 | `World Model` · `Distillation` · `Video Generation` | [Paper](https://arxiv.org/abs/2603.14948) | [Code](https://github.com/TabGuigui/WorldDrive) | — |
| **Cosmos 3** — Cosmos 3: Omnimodal World Models for Physical AI | 2026 | `World Model` · `World-Action` · `VLM` | [Paper](https://arxiv.org/abs/2606.02800) | [Code](https://github.com/nvidia/cosmos) | [Project](https://huggingface.co/collections/nvidia/cosmos3) |
| **CoWorld-VLA** — CoWorld-VLA: Thinking in a Multi-Expert World Model for Autonomous Driving | 2026 | `Diffusion` · `World Model` · `VLA` | [Paper](https://arxiv.org/abs/2605.10426) | [Code](https://github.com/AFARI-Research/CoWorld-VLA) | — |
| **DA-WAM** — DA-WAM: Decision-Aligned Future Latents for Driving World Models | 2026 | `World Model` · `Trajectory Scoring` · `Safety` | [Paper](https://arxiv.org/abs/2608.19085) | — | — |
| **DAWN** — DAWN: The DAWN of World-Action Interactive Models | 2026 | `World Model` · `World-Action` · `Safety` | [Paper](https://arxiv.org/abs/2605.11550) | — | — |
| **DriveDreamer-Policy** — DriveDreamer-Policy: A Geometry-Grounded World-Action Model for Unified Generation and Planning | 2026 | `World Model` · `World-Action` · `VLA` | [Paper](https://arxiv.org/abs/2604.01765) | — | [Project](https://drivedreamer-policy.github.io/) |
| **DriveVA** — DriveVA: Video Action Models are Zero-Shot Drivers | ECCV 2026 | `World Model` · `Video Generation` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2604.04198) | — | — |
| **Fast-WAM** — Fast-WAM: Do World Action Models Need Test-time Future Imagination? | 2026 | `VLA` · `Simulation` | [Paper](https://arxiv.org/abs/2603.16666) | — | [Project](https://yuantianyuan01.github.io/FastWAM/) |
| **GeoWorldAD** — GeoWorldAD: Geometry World Action Model for Autonomous Driving | 2026 | `World Model` · `Safety` | [Paper](https://arxiv.org/abs/2607.17521) | — | — |
| **HyWorldVLA** — HyWorldVLA: A Vision-Language-Action Model with Hybrid World Modeling for Autonomous Driving | 2026 | `World Model` · `VLA` · `Reasoning` | [Paper](https://arxiv.org/abs/2607.20988) | — | — |
| **Latent-WAM** — Latent-WAM: Latent World Action Modeling for End-to-End Autonomous Driving | 2026 | `World Model` · `Distillation` | [Paper](https://arxiv.org/abs/2603.24581) | — | — |
| **Metis** — Metis: A Generalizable and Efficient World-Action Model for Autonomous Driving and Urban Navigation | 2026 | `World-Action` · `VLA` · `Video Generation` | [Paper](https://arxiv.org/abs/2606.15869) | — | — |
| **MM-Future** — MM-Future: Multi-Mode Joint World-Action Modeling for Autonomous Driving | 2026 | `Diffusion` · `World-Action` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2609.20377) | — | — |
| **NVIDIA OmniDreams** — NVIDIA OmniDreams: Real-Time Generative World Model for Closed-Loop Autonomous Vehicle Simulation | 2026 | `Diffusion` · `World Model` · `World-Action` | [Paper](https://arxiv.org/abs/2606.03159) | — | — |
| **RISE** — RISE: Adaptive Imagination for World Action Models | 2026 | `Safety` | [Paper](https://arxiv.org/abs/2608.20430) | — | — |
| **SimWAM** — SimWAM: A Simple World Action Model for End-to-End Autonomous Driving | 2026 | `Flow Matching` · `Reinforcement Learning` · `World-Action` | [Paper](https://arxiv.org/abs/2608.07468) | [Code](https://github.com/H-EmbodVis/SimWAM/) | — |
| **SV-WAM** — SV-WAM: An Efficient Surround-View World-Action Model for End-to-End Autonomous Driving | 2026 | `World Model` · `World-Action` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2609.03602) | — | — |
| **UniDrive-WM** — UniDrive-WM: Unified Understanding, Planning and Generation World Model For Autonomous Driving | 2026 | `World Model` · `Reasoning` | [Paper](https://arxiv.org/abs/2601.04453) | — | [Project](https://unidrive-wm.github.io/UniDrive-WM) |
| **WA-JEPA** — WA-JEPA: Rethinking the Video JEPA Paradigm for World-Action Modeling in Autonomous Driving | 2026 | `Flow Matching` · `World-Action` · `Closed-Loop` | [Paper](https://arxiv.org/abs/2608.20974) | [Code](https://github.com/AFARI-Research/WA-JEPA) | — |
| **MindDrive** — MindDrive: An All-in-One Framework Bridging World Models and Vision-Language Model for End-to-End Autonomous Driving | 2025 | `World Model` · `VLM` · `Simulation` | [Paper](https://arxiv.org/abs/2512.04441) | — | — |
| **Vista** — Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability | NEURIPS 2024 | `World Model` | [Paper](https://arxiv.org/abs/2405.17398) | [Code](https://github.com/OpenDriveLab/Vista) | [Project](https://vista-demo.github.io) |

#### Simulation, Data Generation & Scaling

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **HorizonDrive** — HorizonDrive: Self-Corrective Autoregressive World Model for Long-horizon Driving Simulation | 2026 | `World Model` · `Closed-Loop` · `Simulation` | [Paper](https://arxiv.org/abs/2605.11596) | — | — |
| **X-Cache** — X-Cache: Cross-Chunk Block Caching for Few-Step Autoregressive World Models Inference | 2026 | `Diffusion` · `Reinforcement Learning` · `World Model` | [Paper](https://arxiv.org/abs/2604.20289) | — | — |
| **IRL-VLA** — IRL-VLA: Training an Vision-Language-Action Policy via Reward World Model | 2025 | `Reinforcement Learning` · `World Model` · `VLA` | [Paper](https://arxiv.org/abs/2508.06571) | — | — |
| **SimScale** — SimScale: Learning to Drive via Real-World Simulation at Scale | 2025 | `Simulation` · `Safety` | [Paper](https://arxiv.org/abs/2511.23369) | — | [Project](https://opendrivelab.com/SimScale) |

#### World Foundation Models

| Method | Year / Venue | Tags | Paper | Code | Project |
|---|---|---|---|---|---|
| **SUV** — SUV: Future Scene Understanding as Video Generation for End-to-End Driving | 2026 | `Video Generation` | [Paper](https://arxiv.org/abs/2608.03084) | [Code](https://github.com/ASH-2046/SUV) | — |
| **Cosmos** — Cosmos World Foundation Model Platform for Physical AI | 2025 | `World Model` | [Paper](https://arxiv.org/abs/2501.03575) | [Code](https://github.com/nvidia-cosmos/cosmos-predict1) | — |
| **Cosmos-Transfer1** — Cosmos-Transfer1: Conditional World Generation with Adaptive Multimodal Control | 2025 | `Simulation` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2503.14492) | [Code](https://github.com/nvidia-cosmos/cosmos-transfer1) | — |
| **World4Drive** — World4Drive: End-to-End Autonomous Driving via Intention-aware Physical Latent World Model | ICCV 2025 | `World Model` · `Closed-Loop` · `Multi-Modal` | [Paper](https://arxiv.org/abs/2507.00603) | [Code](https://github.com/ucaszyp/World4Drive) | — |
| **WorldRFT** — WorldRFT: Latent World Model Planning with Reinforcement Fine-Tuning for Autonomous Driving | 2025 | `Diffusion` · `Reinforcement Learning` · `World Model` | [Paper](https://arxiv.org/abs/2512.19133) | — | — |

## Public Datasets and Benchmarks

| Benchmark | Track | Evaluation Setting | Primary Metric | Resources |
|---|---|---|---|---|
| **NAVSIM** | End-to-End Planning | Non-reactive simulation | PDMS | [Homepage](https://github.com/autonomousvision/navsim) · [Paper](https://arxiv.org/abs/2406.15349) · [Code](https://github.com/autonomousvision/navsim) |
| **Bench2Drive** | End-to-End Planning | CARLA closed-loop | Driving Score | [Homepage](https://thinklab-sjtu.github.io/Bench2Drive/) · [Paper](https://arxiv.org/abs/2406.03877) · [Code](https://github.com/Thinklab-SJTU/Bench2Drive) |
| **nuPlan** | Planning | Reactive closed-loop | Closed-loop score | [Homepage](https://www.nuplan.org/) · [Paper](https://arxiv.org/abs/2403.04133) · [Code](https://github.com/motional/nuplan-devkit) |
| **CARLA Leaderboard 2.0** | End-to-End Planning | Interactive closed-loop | Driving Score | [Homepage](https://leaderboard.carla.org/) · [Code](https://github.com/carla-simulator/leaderboard) |
| **nuScenes Planning** | Planning / World Model | Open-loop log replay | Avg. L2 / Collision | [Homepage](https://www.nuscenes.org/) · [Paper](https://arxiv.org/abs/1903.11027) · [Code](https://github.com/nutonomy/nuscenes-devkit) |
| **DriveLM** | VLA / Reasoning | Graph VQA | Accuracy / language metrics | [Homepage](https://github.com/OpenDriveLab/DriveLM) · [Paper](https://arxiv.org/abs/2312.14150) · [Code](https://github.com/OpenDriveLab/DriveLM) |
| **Reason2Drive** | VLA / Reasoning | Video-text reasoning | Reasoning score | [Homepage](https://github.com/OpenDriveLab/Reason2Drive) · [Paper](https://arxiv.org/abs/2312.03661) · [Code](https://github.com/OpenDriveLab/Reason2Drive) |

## Leaderboard

Benchmark results are stored in [data/leaderboard.json](data/leaderboard.json). Submission requirements and reproducibility checks are documented in [benchmark/README.md](benchmark/README.md). Results from different protocol versions, sensor configurations, or data splits are not ranked together.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before adding papers, benchmarks, or leaderboard results. Run `npm run validate` before opening a pull request.

## License

This project is released under the [Apache License 2.0](LICENSE).
