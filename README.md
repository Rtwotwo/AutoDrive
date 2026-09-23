# Awesome Autonomous Driving Research

A curated research collection for end-to-end autonomous driving, driving world models, vision-language-action models, and public evaluation benchmarks. The catalog is built from a Zotero library and currently contains **172 unique papers**.

Last updated: 2026-09-23. Paper metadata should be checked against the latest arXiv or publisher version before citation.

GitHub star counts are a snapshot from 2026-09-23 and can be refreshed with `npm run update:stars`.

## Table of Contents

- [Papers](#papers)
  - [End-to-End Autonomous Driving](#end-to-end-autonomous-driving)
  - [Vision-Language-Action Models](#vision-language-action-models)
  - [Driving World Models](#driving-world-models)
- [Public Datasets](#public-datasets)
- [Public Evaluation Benchmarks](#public-evaluation-benchmarks)
- [Leaderboard](#leaderboard)
- [Contributing](#contributing)
- [License](#license)

## Papers

### End-to-End Autonomous Driving

| Date / Venue | Method | Paper | Open Source | GitHub Stars | Project |
|---|---|---|---|---:|---|
| 2026-09 | **Driving on Registers, Reasoning on Risk** — Driving on Registers, Reasoning on Risk: Risk-Aware Occupancy for Register-Based End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2609.21486) | No public code | — | — |
| 2026-06 · ECCV 2026 | **PriorEye** — PriorEye: Geospatial Visual Priors for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2606.31830) | No public code | — | [Project](https://ori-mrg.github.io/PriorEye) |
| 2026-06 | **World Engine** — World Engine: Towards the Era of Post-Training for Autonomous Driving | [Paper](https://arxiv.org/abs/2606.19836) | No public code | — | [Project](https://opendrivelab.com/WorldEngine/) |
| 2026-06 | **Gigapixel** — Gigapixel: Scaling Self-Play for End-to-End Driving | [Paper](https://arxiv.org/abs/2606.19641) | No public code | — | — |
| 2026-06 | **COMPACT-VA** — COMPACT-VA: Planning-aligned Token Compression for Long-Context Autonomous Driving | [Paper](https://arxiv.org/abs/2606.07464) | No public code | — | — |
| 2026-06 | **TOAD** — TOAD: Test-Time Trajectory Optimization for Autonomous Driving | [Paper](https://arxiv.org/abs/2606.07170) | No public code | — | [Project](https://valeoai.github.io/TOAD/) |
| 2026-05 | **NTR** — NTR: Neural Token Reconstruction for Scene Token Bottleneck in End-to-End Driving | [Paper](https://arxiv.org/abs/2605.31116) | No public code | — | — |
| 2026-05 | **CLOVER** — CLOVER: Closed-Loop Value Estimation and Ranking for End-to-End Autonomous Driving Planning | [Paper](https://arxiv.org/abs/2605.15120) | [Yes](https://github.com/WilliamXuanYu/CLOVER) | 12 | — |
| 2026-05 | **123D** — 123D: Unifying Multi-Modal Autonomous Driving Data at Scale | [Paper](https://arxiv.org/abs/2605.08084) | [Yes](https://github.com/kesai-labs/py123d) | 396 | — |
| 2026-05 | **ReflectDrive-2** — ReflectDrive-2: Reinforcement-Learning-Aligned Self-Editing for Discrete Diffusion Driving | [Paper](https://arxiv.org/abs/2605.04647) | No public code | — | — |
| 2026-04 | **RAD-2** — RADV2: Scaling Reinforcement Learning in a Generator-Discriminator Framework | [Paper](https://arxiv.org/abs/2604.15308) | No public code | — | — |
| 2026-04 · CVPR 2026 | **MOSAIC** — MOSAIC: Scaling-Aware Data Selection for End-to-End Autonomous Driving Systems | [Paper](https://arxiv.org/abs/2604.08366) | No public code | — | — |
| 2026-03 | **FlowAD** — FlowAD: Ego-Scene Interactive Modeling for Autonomous Driving | [Paper](https://arxiv.org/abs/2603.13399) | No public code | — | — |
| 2026-03 | **SparseDriveV2** — SparseDriveV2: Scoring is All You Need for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2603.29163) | [Yes](https://github.com/swc-17/SparseDriveV2) | 255 | — |
| 2026-02 | **HDP** — HDP: Unleashing the Potential of Diffusion Models for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2602.22801) | No public code | — | — |
| 2026-02 · CVPR 2026 | **MeanFuser** — MeanFuser: Fast One-Step Multi-Modal Trajectory Generation and Adaptive Reconstruction via MeanFlow for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2602.20060) | [Yes](https://github.com/wjl2244/MeanFuser) | 107 | — |
| 2026-02 · ICRA 2026 | **PCM** — PCM: A Generalizable Physics-guided Causal Model for Trajectory Prediction in Autonomous Driving | [Paper](https://arxiv.org/abs/2602.13936) | [Yes](https://github.com/ZY-Zong/Physics-guided-Causal-Model) | 8 | — |
| 2026-01 | **PlannerRFT** — PlannerRFT: Reinforcing Diffusion Planners through Closed-Loop and Sample-Efficient Fine-Tuning | [Paper](https://arxiv.org/abs/2601.12901) | No public code | — | — |
| 2026-01 | **DrivoR** — DrivoR: Driving on Registers | [Paper](https://arxiv.org/abs/2601.05083) | No public code | — | — |
| 2026-01 | **AlignDrive** — AlignDrive: Aligned Lateral-Longitudinal Planning for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2601.01762) | No public code | — | — |
| 2025-12 | **LEAD** — LEAD & LTFv6: Minimizing Learner-Expert Asymmetry in End-to-End Driving | [Paper](https://arxiv.org/abs/2512.20563) | [Yes](https://github.com/autonomousvision/lead) | 229 | — |
| 2025-12 | **DiffusionDriveV2** — DiffusionDriveV2: Reinforcement Learning-Constrained Truncated Diffusion Modeling in End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2512.07745) | [Yes](https://github.com/hustvl/DiffusionDriveV2) | 371 | — |
| 2025-12 | **Spatial Retrieval AD** — Spatial Retrieval AD: Spatial Retrieval Augmented Autonomous Driving | [Paper](https://arxiv.org/abs/2512.06865) | No public code | — | [Project](https://spatialretrievalad.github.io/) |
| 2025-12 | **LAP** — LAP: Fast LAtent Diffusion Planner for Autonomous Driving | [Paper](https://arxiv.org/abs/2512.00470) | No public code | — | — |
| 2025-11 | **GuideFlow** — GuideFlow: Constraint-Guided Flow Matching for Planning in End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2511.18729) | [Yes](https://github.com/liulin815/GuideFlow) | 31 | — |
| 2025-11 · AAAI 2026 | **DiffRefiner** — DiffRefiner: Coarse to Fine Trajectory Planning via Diffusion Refinement with Semantic Interaction for End to End Autonomous Driving | [Paper](https://arxiv.org/abs/2511.17150) | No public code | — | — |
| 2025-11 | **MiMo-Embodied** — MiMo-Embodied: X-Embodied Foundation Model Technical Report | [Paper](https://arxiv.org/abs/2511.16518) | [Yes](https://github.com/XiaomiMiMo/MiMo-Embodied) | 408 | [Project](https://huggingface.co/XiaomiMiMo/MiMo-Embodied-7B) |
| 2025-11 | **UniMM-V2X** — UniMM-V2X: MoE-Enhanced Multi-Level Fusion for End-to-End Cooperative Autonomous Driving | [Paper](https://arxiv.org/abs/2511.09013) | No public code | — | — |
| 2025-11 | **UniLION** — UniLION: Towards Unified Autonomous Driving Model with Linear Group RNNs | [Paper](https://arxiv.org/abs/2511.01768) | [Yes](https://github.com/happinesslz/UniLION) | 61 | — |
| 2025-10 | **ZTRS** — ZTRS: Zero-Imitation End-to-end Autonomous Driving with Trajectory Scoring | [Paper](https://arxiv.org/abs/2510.24108) | [Yes](https://github.com/woxihuanjiangguo/ZTRS) | 77 | — |
| 2025-08 | **EvaDrive** — EvaDrive: Evolutionary Adversarial Policy Optimization for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2508.09158) | No public code | — | — |
| 2025-08 | **DistillDrive** — DistillDrive: End-to-End Multi-Mode Autonomous Driving Distillation by Isomorphic Hetero-Source Planning Model | [Paper](https://arxiv.org/abs/2508.05402) | [Yes](https://github.com/YuruiAI/DistillDrive) | 128 | — |
| 2025-08 | **DiffSemanticFusion** — DiffSemanticFusion: Semantic Raster BEV Fusion for Autonomous Driving via Online HD Map Diffusion | [Paper](https://arxiv.org/abs/2508.01778) | [Yes](https://github.com/SunZhigang7/DiffSemanticFusion) | 56 | — |
| 2025-07 | **GEMINUS** — GEMINUS: Dual-aware Global and Scene-Adaptive Mixture-of-Experts for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2507.14456) | [Yes](https://github.com/newbrains1/GEMINUS) | 18 | — |
| 2025-06 · IROS 2025 | **TrajFlow** — TrajFlow: Multi-modal Motion Prediction via Flow Matching | [Paper](https://arxiv.org/abs/2506.08541) | No public code | — | [Project](https://traj-flow.github.io/) |
| 2025-06 · ICCV 2025 | **ETA** — ETA: Efficiency through Thinking Ahead, A Dual Approach to Self-Driving with Large Models | [Paper](https://arxiv.org/abs/2506.07725) | [Yes](https://github.com/opendrivelab/ETA) | 48 | — |
| 2025-06 · CVPR 2025 | **GTRS** — GTRS: Generalized Trajectory Scoring for End-to-end Multimodal Planning | [Paper](https://arxiv.org/abs/2506.06664) | [Yes](https://github.com/NVlabs/GTRS) | 287 | — |
| 2025-06 · AAAI 2026 | **DriveSuprim** — DriveSuprim: Towards Precise Trajectory Selection for End-to-End Planning | [Paper](https://arxiv.org/abs/2506.06659) | No public code | — | — |
| 2025-06 · CORL 2025 | **NAVSIM** — NAVSIM: Pseudo-Simulation for Autonomous Driving | [Paper](https://arxiv.org/abs/2506.04218) | [Yes](https://github.com/autonomousvision/navsim) | 1,108 | — |
| 2025-06 · NEURIPS 2025 | **GaussianFusion** — GaussianFusion: Gaussian-Based Multi-Sensor Fusion for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2506.00034) | [Yes](https://github.com/Say2L/GaussianFusion) | 96 | — |
| 2025-05 | **iPad** — iPad: Iterative Proposal-centric End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2505.15111) | [Yes](https://github.com/Kguo-cs/iPad) | 144 | — |
| 2025-05 | **TransDiffuser** — TransDiffuser: Diverse Trajectory Generation with Decorrelated Multi-modal Representation for End-to-end Autonomous Driving | [Paper](https://arxiv.org/abs/2505.09315) | No public code | — | — |
| 2025-03 · CVPR 2025 | **Bridging Past and Future** — BridgeAD: Bridging Past and Future End-to-End Autonomous Driving with Historical Prediction and Planning | [Paper](https://arxiv.org/abs/2503.14182) | No public code | — | — |
| 2025-03 | **Hydra-MDP++** — Hydra-MDP++: Advancing End-to-End Driving via Expert-Guided Hydra-Distillation | [Paper](https://arxiv.org/abs/2503.12820) | [Yes](https://github.com/NVlabs/Hydra-MDP) | 417 | — |
| 2025-03 | **TrajHF** — TrajHF: Learning Personalized Driving Styles via Reinforcement Learning from Human Feedback | [Paper](https://arxiv.org/abs/2503.10434) | No public code | — | — |
| 2025-03 | **HiP-AD** — HiP-AD: Hierarchical and Multi-Granularity Planning with Deformable Attention for Autonomous Driving in a Single Decoder | [Paper](https://arxiv.org/abs/2503.08612) | No public code | — | — |
| 2025-03 · ICLR 2025 | **DriveTransformer** — DriveTransformer: Unified Transformer for Scalable End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2503.07656) | No public code | — | — |
| 2025-03 | **GoalFlow** — GoalFlow: Goal-Driven Flow Matching for Multimodal Trajectories Generation in End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2503.05689) | [Yes](https://github.com/YvanYin/GoalFlow) | 425 | — |
| 2025-03 | **Don't Shake the Wheel** — MomAD: Don't Shake the Wheel Momentum-Aware Planning in End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2503.03125) | [Yes](https://github.com/adept-thu/MomAD) | 450 | — |
| 2024-11 · CVPR 2025 | **DiffusionDrive** — DiffusionDriveV1: Truncated Diffusion Model for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2411.15139) | [Yes](https://github.com/hustvl/DiffusionDrive) | 1,501 | — |
| 2024-06 · NEURIPS 2024 | **NAVSIM** — NAVSIM: Data-Driven Non-Reactive Autonomous Vehicle Simulation and Benchmarking | [Paper](https://arxiv.org/abs/2406.15349) | [Yes](https://github.com/autonomousvision/navsim) | 1,108 | — |
| 2024-06 · CVPR 2024 | **Hydra-MDP** — Hydra-MDP: End-to-end Multimodal Planning with Multi-target Hydra-Distillation | [Paper](https://arxiv.org/abs/2406.06978) | [Yes](https://github.com/NVlabs/Hydra-MDP) | 417 | — |
| 2024-05 | **SparseDrive** — SparseDriveV1: End-to-End Autonomous Driving via Sparse Scene Representation | [Paper](https://arxiv.org/abs/2405.19620) | [Yes](https://github.com/swc-17/SparseDrive) | 1,004 | — |
| 2024-02 | **VADv2** — VADv2: End-to-End Vectorized Autonomous Driving via Probabilistic Planning | [Paper](https://arxiv.org/abs/2402.13243) | No public code | — | [Project](https://hgao-cv.github.io/VADv2) |
| 2023-12 · CVPR 2024 | **BEV-Planner** — BEV-Planner: Is Ego Status All You Need for Open-Loop End-to-End Autonomous Driving? | [Paper](https://arxiv.org/abs/2312.03031) | [Yes](https://github.com/NVlabs/BEV-Planner) | 260 | — |
| 2023-03 · ICCV 2023 | **VAD** — VAD: Vectorized Scene Representation for Efficient Autonomous Driving | [Paper](https://arxiv.org/abs/2303.12077) | [Yes](https://github.com/hustvl/VAD) | 1,374 | — |
| 2022-12 · CVPR 2023 | **UniAD** — UniAD: Planning-oriented Autonomous Driving | [Paper](https://arxiv.org/abs/2212.10156) | No public code | — | [Project](https://opendrivelab.github.io/UniAD/) |
| 2022-07 · ECCV 2022 | **ST-P3** — ST-P3: End-to-end Vision-based Autonomous Driving via Spatial-Temporal Feature Learning | [Paper](https://arxiv.org/abs/2207.07601) | [Yes](https://github.com/OpenPerceptionX/ST-P3) | 13 | — |
| 2022-05 | **TransFuser** — TransFuser: Imitation with Transformer-Based Sensor Fusion for Autonomous Driving | [Paper](https://arxiv.org/abs/2205.15997) | No public code | — | — |

### Vision-Language-Action Models

| Date / Venue | Method | Paper | Open Source | GitHub Stars | Project |
|---|---|---|---|---:|---|
| 2026-09 | **Qwen-Drive-1.0** — Qwen-Drive-1.0: An Initial Step towards a Vision-Language Foundation Model for Autonomous Driving | [Paper](https://arxiv.org/abs/2609.00111) | [Yes](https://github.com/QwenLM/Qwen-Drive-1.0) | 468 | — |
| 2026-08 | **Plug-and-Play** — Plug-and-Play: Plug-and-Play Traffic Element Awareness for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2608.18035) | No public code | — | — |
| 2026-08 | **BrainWAM** — BrainWAM: Action-Space Coordination of Semantic Priors and Predictive Dynamics for Autonomous Driving | [Paper](https://arxiv.org/abs/2608.12854) | No public code | — | — |
| 2026-08 | **DriveVLA-M0** — DriveVLA-M0: Failure-Aware Memory Augmentation for Autonomous Driving | [Paper](https://arxiv.org/abs/2608.10413) | [Yes](https://github.com/ZebinX/DriveVLA-M0) | 32 | — |
| 2026-08 | **FactorDrive** — FactorDrive: Adaptive Multi-Step Reasoning Driven by Planning-Critical Factors for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2608.09591) | No public code | — | — |
| 2026-08 | **DEFT-RLVR** — DEFT-RLVR: Deferred Exposure of Future Trajectories for Verifiable Reasoning in Autonomous Driving VLMs | [Paper](https://arxiv.org/abs/2608.01755) | No public code | — | — |
| 2026-07 | **WorkDrive** — WorkDrive: Roadwork Chain of Causation for Autonomous Driving | [Paper](https://arxiv.org/abs/2607.14727) | No public code | — | — |
| 2026-07 | **Post-Training in End-to-End Autonomous Driving** — Post-Training in End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2607.08072) | [Yes](https://github.com/RYNing/Awesome-Post-Training-In-Autonomous-Driving-Papers) | 35 | — |
| 2026-07 | **From Foundation to Application** — LingBot-VLA 2.0: From Foundation to Application: Improving VLA Models in Practice | [Paper](https://arxiv.org/abs/2607.06403) | [Yes](https://github.com/robbyant/lingbot-vla-v2) | 947 | [Project](https://technology.robbyant.com/lingbot-vla-v2) |
| 2026-07 | **AnchorVLA** — AnchorVLA: Bridging Discrete Decisions and Continuous Trajectories for Vision-Language-Action Planning | [Paper](https://arxiv.org/abs/2607.03182) | No public code | — | — |
| 2026-07 · ECCV 2026 | **DriveTeach-VLA** — DriveTeach-VLA: Teaching Vision-Language-Action Models What to See and Where to Look | [Paper](https://arxiv.org/abs/2607.01658) | [Yes](https://github.com/ShivaTeam/DriveTeach-VLA) | 28 | — |
| 2026-06 | **WVM** — WVM: World Value Models for Robotic Manipulation | [Paper](https://arxiv.org/abs/2606.24742) | No public code | — | — |
| 2026-06 | **DriveReward** — DriveReward: A Comprehensive Dataset and Generative Vision-Language Reward Model for Autonomous Driving | [Paper](https://arxiv.org/abs/2606.08525) | No public code | — | — |
| 2026-05 | **ChainFlow-VLA** — ChainFlow-VLA: Causal Flow Planning with Vision-Language Models | [Paper](https://arxiv.org/abs/2605.23270) | [Yes](https://github.com/AFARI-Research/ChainFlow-VLA) | 50 | — |
| 2026-05 | **IKN** — IKN: Grounding Driving VLA via Inverse Kinematics | [Paper](https://arxiv.org/abs/2605.21061) | No public code | — | — |
| 2026-05 | **CRAFT** — CRAFT: Counterfactual-to-Interactive Reinforcement Fine-Tuning for Driving Policies | [Paper](https://arxiv.org/abs/2605.04470) | No public code | — | [Project](https://currychen77.github.io/CRAFT) |
| 2026-04 | **OneDrive** — OneDrive: Unified Multi-Paradigm Driving with Vision-Language-Action Models | [Paper](https://arxiv.org/abs/2604.17915) | [Yes](https://github.com/Z1zyw/OneDrive) | 19 | — |
| 2026-04 | **UniDriveVLA** — UniDriveVLA: Unifying Understanding, Perception, and Action Planning for Autonomous Driving | [Paper](https://arxiv.org/abs/2604.02190) | [Yes](https://github.com/xiaomi-research/unidrivevla) | 246 | — |
| 2026-04 | **DVGT-2** — DVGT-2: Vision-Geometry-Action Model for Autonomous Driving at Scale | [Paper](https://arxiv.org/abs/2604.00813) | [Yes](https://github.com/wzzheng/DVGT) | 362 | — |
| 2026-03 · ICLR 2026 | **AutoDrivetextbackslashtext-Ptextasciicircum3** — AutoDrive-Ptextasciicircum3: Unified Chain of Perception-Prediction-Planning Thought via Reinforcement Fine-Tuning | [Paper](https://arxiv.org/abs/2603.28116) | [Yes](https://github.com/haha-yuki-haha/AutoDrive-P3) | 20 | — |
| 2026-03 | **Learning from Mistakes** — TakeVLA: Learning from Mistakes: Post-Training for Driving VLA with Takeover Data | [Paper](https://arxiv.org/abs/2603.14972) | No public code | — | — |
| 2026-03 | **AutoMoT** — AutoMoT: A Unified Vision-Language-Action Model with Asynchronous Mixture-of-Transformers for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2603.14851) | No public code | — | [Project](https://automot-website.github.io/) |
| 2026-03 | **DynVLA** — DynVLA: Learning World Dynamics for Action Reasoning in Autonomous Driving | [Paper](https://arxiv.org/abs/2603.11041) | No public code | — | [Project](https://yaoyao-jpg.github.io/dynvla) |
| 2026-03 | **EvoDriveVLA** — EvoDriveVLA: Evolving Driving VLA Models via Collaborative Perception-Planning Distillation | [Paper](https://arxiv.org/abs/2603.09465) | [Yes](https://github.com/hey-cjj/EvoDriveVLA) | 50 | — |
| 2026-03 · CVPR 2026 | **Devil is in Narrow Policy** — CuriousVLA: Devil is in Narrow Policy Unleashing Exploration in Driving VLA Models | [Paper](https://arxiv.org/abs/2603.06049) | [Yes](https://github.com/Mashiroln/curious_vla.git) | 133 | — |
| 2026-03 | **LaST-VLA** — LaST-VLA: Thinking in Latent Spatio-Temporal Space for Vision-Language-Action in Autonomous Driving | [Paper](https://arxiv.org/abs/2603.01928) | No public code | — | — |
| 2026-03 | **LinkVLA** — LinkVLA: Unifying Language-Action Understanding and Generation for Autonomous Driving | [Paper](https://arxiv.org/abs/2603.01441) | No public code | — | — |
| 2026-03 | **ELF-VLA** — ELF-VLA: Unleashing VLA Potentials in Autonomous Driving via Explicit Learning from Failures | [Paper](https://arxiv.org/abs/2603.01063) | No public code | — | — |
| 2026-02 · CVPR 2026 | **NoRD** — NoRD: A Data-Efficient Vision-Language-Action Model that Drives without Reasoning | [Paper](https://arxiv.org/abs/2602.21172) | No public code | — | — |
| 2026-02 · CVPR 2026 | **VGGDrive** — VGGDrive: Empowering Vision-Language Models with Cross-View Geometric Grounding for Autonomous Driving | [Paper](https://arxiv.org/abs/2602.20794) | No public code | — | — |
| 2026-02 | **HiST-VLA** — HiST-VLA: A Hierarchical Spatio-Temporal Vision-Language-Action Model for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2602.13329) | No public code | — | — |
| 2026-02 | **HybridDriveVLA** — HybridDriveVLA: From Representational Complementarity to Dual Systems: Synergizing VLM and Vision-Only Backbones for End-to-End Driving | [Paper](https://arxiv.org/abs/2602.10719) | No public code | — | — |
| 2026-01 | **SparseOccVLA** — SparseOccVLA: Bridging Occupancy and Vision-Language Models via Sparse Queries for Unified 4D Scene Understanding and Planning | [Paper](https://arxiv.org/abs/2601.06474) | No public code | — | — |
| 2026-01 | **SGDrive** — SGDrive: Scene-to-Goal Hierarchical World Cognition for Autonomous Driving | [Paper](https://arxiv.org/abs/2601.05640) | No public code | — | — |
| 2026-01 | **LatentVLA** — LatentVLA: Efficient Vision-Language Models for Autonomous Driving via Latent Action Prediction | [Paper](https://arxiv.org/abs/2601.05611) | No public code | — | — |
| 2026 | **HybridDriveVLA** — HybridDriveVLA: Vision-Language-Action Model with Visual CoT reasoning and ToT Evaluation for Autonomous Driving | [Paper](https://openaccess.thecvf.com/content/CVPR2026/html/Bassole_HybridDriveVLA_Vision-Language-Action_Model_with_Visual_CoT_reasoning_and_ToT_Evaluation_CVPR_2026_paper.html) | No public code | — | — |
| 2025-12 · CVPR 2026 | **ColaVLA** — ColaVLA: Leveraging Cognitive Latent Reasoning for Hierarchical Parallel Trajectory Planning in Autonomous Driving | [Paper](https://arxiv.org/abs/2512.22939) | No public code | — | [Project](https://pqh22.github.io/projects/ColaVLA/index.html) |
| 2025-12 | **SpaceDrive** — SpaceDrive: Infusing Spatial Awareness into VLM-based Autonomous Driving | [Paper](https://arxiv.org/abs/2512.10719) | No public code | — | — |
| 2025-12 | **WAM-Flow** — WAM-Flow: Parallel Coarse-to-Fine Motion Planning via Discrete Flow Matching for Autonomous Driving | [Paper](https://arxiv.org/abs/2512.06112) | [Yes](https://github.com/fudan-generative-vision/WAM-Flow) | 367 | — |
| 2025-12 | **OpenREAD** — OpenREAD: Reinforced Open-Ended Reasoning for End-to-End Autonomous Driving with LLM-as-Critic | [Paper](https://arxiv.org/abs/2512.01830) | No public code | — | — |
| 2025-11 | **Alpamayo-R1** — Alpamayo-R1: Bridging Reasoning and Action Prediction for Generalizable Autonomous Driving in the Long Tail | [Paper](https://arxiv.org/abs/2511.00088) | [Yes](https://github.com/NVlabs/alpamayo) | 2,025 | [Project](https://huggingface.co/nvidia/Alpamayo-R1-10B) |
| 2025-11 | **World** — World Simulation with Video Foundation Models for Physical AI | [Paper](https://arxiv.org/abs/2511.00062) | [Yes](https://github.com/nvidia-cosmos/cosmos-predict2.5) | 1,372 | — |
| 2025-09 | **ReflectDrive-1** — ReflectDrive-1: Discrete Diffusion for Reflective Vision-Language-Action Models in Autonomous Driving | [Paper](https://arxiv.org/abs/2509.20109) | No public code | — | — |
| 2025-09 | **OccVLA** — OccVLA: Vision-Language-Action Model with Implicit 3D Occupancy Supervision | [Paper](https://arxiv.org/abs/2509.05578) | No public code | — | — |
| 2025-07 · AAAI 2026 | **FastDriveVLA** — FastDriveVLA: Efficient End-to-End Driving via Plug-and-Play Reconstruction-based Token Pruning | [Paper](https://arxiv.org/abs/2507.23318) | No public code | — | — |
| 2025-06 · NEURIPS 2025 | **AutoVLA** — AutoVLA: A Vision-Language-Action Model for End-to-End Autonomous Driving with Adaptive Reasoning and Reinforcement Fine-Tuning | [Paper](https://arxiv.org/abs/2506.13757) | No public code | — | [Project](https://autovla.github.io/) |
| 2025-06 | **ReCogDrive** — ReCogDrive: A Reinforced Cognitive Framework for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2506.08052) | [Yes](https://github.com/xiaomi-research/recogdrive) | 611 | — |
| 2025-05 | **DiffVLA** — DiffVLA: Vision-Language Guided Diffusion Planning for Autonomous Driving | [Paper](https://arxiv.org/abs/2505.19381) | No public code | — | — |
| 2025-05 | **DriveMoE** — DriveMoE: Mixture-of-Experts for Vision-Language-Action Model in End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2505.16278) | No public code | — | [Project](https://thinklab-sjtu.github.io/DriveMoE/) |
| 2025-05 | **LightEMMA** — LightEMMA: Lightweight End-to-End Multimodal Model for Autonomous Driving | [Paper](https://arxiv.org/abs/2505.00284) | [Yes](https://github.com/michigan-traffic-lab/LightEMMA) | 145 | — |
| 2025-03 | **OpenDriveVLA** — OpenDriveVLA: Towards End-to-end Autonomous Driving with Large Vision Language Action Model | [Paper](https://arxiv.org/abs/2503.23463) | No public code | — | — |
| 2025-03 | **Cosmos-Reason1** — Cosmos-Reason1: From Physical Common Sense To Embodied Reasoning | [Paper](https://arxiv.org/abs/2503.15558) | [Yes](https://github.com/nvidia-cosmos/cosmos-reason1) | 962 | — |
| 2025-03 | **AlphaDrive** — AlphaDrive: Unleashing the Power of VLMs in Autonomous Driving via Reinforcement Learning and Reasoning | [Paper](https://arxiv.org/abs/2503.07608) | [Yes](https://github.com/hustvl/AlphaDrive) | 334 | — |

### Driving World Models

| Date / Venue | Method | Paper | Open Source | GitHub Stars | Project |
|---|---|---|---|---:|---|
| 2026-09 | **ZYT-World** — ZYT-World: A Real-Time Controllable World Model for Closed-Loop Autonomous-Driving Simulation | [Paper](https://arxiv.org/abs/2609.21712) | No public code | — | — |
| 2026-09 | **MM-Future** — MM-Future: Multi-Mode Joint World-Action Modeling for Autonomous Driving | [Paper](https://arxiv.org/abs/2609.20377) | No public code | — | — |
| 2026-09 | **SV-WAM** — SV-WAM: An Efficient Surround-View World-Action Model for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2609.03602) | No public code | — | — |
| 2026-08 | **How Far Can 5,500 Hours of Driving Take You?** — NATIX: How Far Can 5,500 Hours of Driving Take You? A Scaling Law Analysis of Video Diffusion Models | [Paper](https://arxiv.org/abs/2608.28404) | [Yes](https://github.com/valeoai/VATIX) | 21 | — |
| 2026-08 | **BehaviorWorldGen** — BehaviorWorldGen: Closing the Loop between Action Models and World Simulators via Controllable Behavior-Aware Structured World Generation | [Paper](https://arxiv.org/abs/2608.22187) | No public code | — | — |
| 2026-08 | **WA-JEPA** — WA-JEPA: Rethinking the Video JEPA Paradigm for World-Action Modeling in Autonomous Driving | [Paper](https://arxiv.org/abs/2608.20974) | [Yes](https://github.com/AFARI-Research/WA-JEPA) | 63 | — |
| 2026-08 | **RISE** — RISE: Adaptive Imagination for World Action Models | [Paper](https://arxiv.org/abs/2608.20430) | No public code | — | — |
| 2026-08 | **DA-WAM** — DA-WAM: Decision-Aligned Future Latents for Driving World Models | [Paper](https://arxiv.org/abs/2608.19085) | No public code | — | — |
| 2026-08 | **4D-WAM** — 4D-WAM: 4D Consistent World Modeling for Autonomous Driving | [Paper](https://arxiv.org/abs/2608.10107) | No public code | — | — |
| 2026-08 | **SimWAM** — SimWAM: A Simple World Action Model for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2608.07468) | [Yes](https://github.com/H-EmbodVis/SimWAM/) | 181 | — |
| 2026-08 | **SUV** — SUV: Future Scene Understanding as Video Generation for End-to-End Driving | [Paper](https://arxiv.org/abs/2608.03084) | [Yes](https://github.com/ASH-2046/SUV) | 20 | — |
| 2026-07 | **Auto-JEPA** — Auto-JEPA: A Latent World Model of Continuous Intent for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2607.29031) | No public code | — | — |
| 2026-07 | **INTACT** — INTACT: Isomorphic Intent-to-Action Learning for Search-Free World Models | [Paper](https://arxiv.org/abs/2607.26056) | No public code | — | — |
| 2026-07 | **HyWorldVLA** — HyWorldVLA: A Vision-Language-Action Model with Hybrid World Modeling for Autonomous Driving | [Paper](https://arxiv.org/abs/2607.20988) | No public code | — | — |
| 2026-07 | **GeoWorldAD** — GeoWorldAD: Geometry World Action Model for Autonomous Driving | [Paper](https://arxiv.org/abs/2607.17521) | No public code | — | — |
| 2026-06 | **OWMDrive** — OWMDrive: Causality-Aware End-to-End Autonomous Driving via 4D Occupancy World Model | [Paper](https://arxiv.org/abs/2606.30421) | No public code | — | — |
| 2026-06 | **Metis** — Metis: A Generalizable and Efficient World-Action Model for Autonomous Driving and Urban Navigation | [Paper](https://arxiv.org/abs/2606.15869) | No public code | — | — |
| 2026-06 | **NVIDIA OmniDreams** — NVIDIA OmniDreams: Real-Time Generative World Model for Closed-Loop Autonomous Vehicle Simulation | [Paper](https://arxiv.org/abs/2606.03159) | No public code | — | — |
| 2026-06 | **Cosmos 3** — Cosmos 3: Omnimodal World Models for Physical AI | [Paper](https://arxiv.org/abs/2606.02800) | [Yes](https://github.com/nvidia/cosmos) | 11,893 | [Project](https://huggingface.co/collections/nvidia/cosmos3) |
| 2026-05 | **X-Foresight** — X-Foresight: A Joint Vision-Action Causal Forecasting Network via Predictive World Modeling | [Paper](https://arxiv.org/abs/2605.24892) | No public code | — | — |
| 2026-05 | **Xiaomi EV World Model** — Xiaomi EV World Model: A Joint World Model Integrating Reconstruction and Generation for Autonomous Driving | [Paper](https://arxiv.org/abs/2605.18137) | No public code | — | — |
| 2026-05 | **GEM** — GEM: Gaussian Evolution Model for Occupancy Forecasting and Motion Planning | [Paper](https://arxiv.org/abs/2605.17682) | No public code | — | — |
| 2026-05 | **EponaV2** — EponaV2: Driving World Model with Comprehensive Future Reasoning | [Paper](https://arxiv.org/abs/2605.14696) | No public code | — | — |
| 2026-05 | **HorizonDrive** — HorizonDrive: Self-Corrective Autoregressive World Model for Long-horizon Driving Simulation | [Paper](https://arxiv.org/abs/2605.11596) | No public code | — | — |
| 2026-05 | **DAWN** — DAWN: The DAWN of World-Action Interactive Models | [Paper](https://arxiv.org/abs/2605.11550) | No public code | — | — |
| 2026-05 | **DeepSight** — DeepSight: Long-Horizon World Modeling via Latent States Prediction for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2605.10564) | [Yes](https://github.com/hotdogcheesewhite/DeepSight) | 31 | — |
| 2026-05 | **CoWorld-VLA** — CoWorld-VLA: Thinking in a Multi-Expert World Model for Autonomous Driving | [Paper](https://arxiv.org/abs/2605.10426) | [Yes](https://github.com/AFARI-Research/CoWorld-VLA) | 10 | — |
| 2026-05 | **DriveFuture** — DriveFuture: Future-Aware Latent World Models for Autonomous Driving | [Paper](https://arxiv.org/abs/2605.09701) | No public code | — | [Project](https://huggingface.co/spaces/AGC2025/e2e-driving-navhard) |
| 2026-04 | **X-Cache** — X-Cache: Cross-Chunk Block Caching for Few-Step Autoregressive World Models Inference | [Paper](https://arxiv.org/abs/2604.20289) | No public code | — | — |
| 2026-04 · ECCV 2026 | **DriveVA** — DriveVA: Video Action Models are Zero-Shot Drivers | [Paper](https://arxiv.org/abs/2604.04198) | No public code | — | — |
| 2026-04 · ECCV 2026 | **ExploreVLA** — ExploreVLA: Dense World Modeling and Exploration for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2604.02714) | No public code | — | [Project](https://zihaosheng.github.io/ExploreVLA/) |
| 2026-04 | **DriveDreamer-Policy** — DriveDreamer-Policy: A Geometry-Grounded World-Action Model for Unified Generation and Planning | [Paper](https://arxiv.org/abs/2604.01765) | No public code | — | [Project](https://drivedreamer-policy.github.io/) |
| 2026-03 · ECCV 2026 | **Uni-World VLA** — Uni-World VLA: Interleaved World Modeling and Planning for Autonomous Driving | [Paper](https://arxiv.org/abs/2603.27287) | No public code | — | — |
| 2026-03 | **Latent-WAM** — Latent-WAM: Latent World Action Modeling for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2603.24581) | No public code | — | — |
| 2026-03 | **X-World** — X-World: Controllable Ego-Centric Multi-Camera World Models for Scalable End-to-End Driving | [Paper](https://arxiv.org/abs/2603.19979) | No public code | — | — |
| 2026-03 | **Fast-WAM** — Fast-WAM: Do World Action Models Need Test-time Future Imagination? | [Paper](https://arxiv.org/abs/2603.16666) | No public code | — | [Project](https://yuantianyuan01.github.io/FastWAM/) |
| 2026-03 | **Bridging Scene Generation and Planning** — WorldDrive: Bridging Scene Generation and Planning Driving with World Model via Unifying Vision and Motion Representation | [Paper](https://arxiv.org/abs/2603.14948) | [Yes](https://github.com/TabGuigui/WorldDrive) | 80 | — |
| 2026-02 · ICLR 2026 | **ResWorld** — ResWorld: Temporal Residual World Model for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2602.10884) | [Yes](https://github.com/mengtan00/ResWorld.git) | 63 | — |
| 2026-02 | **DriveWorld-VLA** — DriveWorld-VLA: Unified Latent-Space World Modeling with Vision-Language-Action for Autonomous Driving | [Paper](https://arxiv.org/abs/2602.06521) | [Yes](https://github.com/liulin815/DriveWorld-VLA.git) | 127 | — |
| 2026-02 | **UniDWM** — UniDWM: Towards a Unified Driving World Model via Multifaceted Representation Learning | [Paper](https://arxiv.org/abs/2602.01536) | No public code | — | — |
| 2026-01 | **Drive-JEPA** — Drive-JEPA: Video JEPA Meets Multimodal Trajectory Distillation for End-to-End Driving | [Paper](https://arxiv.org/abs/2601.22032) | No public code | — | — |
| 2026-01 | **UniDrive-WM** — UniDrive-WM: Unified Understanding, Planning and Generation World Model For Autonomous Driving | [Paper](https://arxiv.org/abs/2601.04453) | No public code | — | [Project](https://unidrive-wm.github.io/UniDrive-WM) |
| 2025-12 | **DriveLaW** — DriveLaW:Unifying Planning and Video Generation in a Latent Driving World | [Paper](https://arxiv.org/abs/2512.23421) | No public code | — | — |
| 2025-12 | **WorldRFT** — WorldRFT: Latent World Model Planning with Reinforcement Fine-Tuning for Autonomous Driving | [Paper](https://arxiv.org/abs/2512.19133) | No public code | — | — |
| 2025-12 | **MindDrive** — MindDrive: An All-in-One Framework Bridging World Models and Vision-Language Model for End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2512.04441) | No public code | — | — |
| 2025-11 | **SimScale** — SimScale: Learning to Drive via Real-World Simulation at Scale | [Paper](https://arxiv.org/abs/2511.23369) | No public code | — | [Project](https://opendrivelab.com/SimScale) |
| 2025-10 | **DriveVLA-W0** — DriveVLA-W0: World Models Amplify Data Scaling Law in Autonomous Driving | [Paper](https://arxiv.org/abs/2510.12796) | No public code | — | — |
| 2025-10 | **WorldMirror** — WorldMirror: Universal 3D World Reconstruction with Any-Prior Prompting | [Paper](https://arxiv.org/abs/2510.10726) | No public code | — | — |
| 2025-10 | **RAP** — RAP: 3D Rasterization Augmented End-to-End Planning | [Paper](https://arxiv.org/abs/2510.04333) | No public code | — | [Project](https://alan-lanfeng.github.io/RAP/) |
| 2025-08 | **IRL-VLA** — IRL-VLA: Training an Vision-Language-Action Policy via Reward World Model | [Paper](https://arxiv.org/abs/2508.06571) | No public code | — | — |
| 2025-07 · ICCV 2025 | **World4Drive** — World4Drive: End-to-End Autonomous Driving via Intention-aware Physical Latent World Model | [Paper](https://arxiv.org/abs/2507.00603) | [Yes](https://github.com/ucaszyp/World4Drive) | 111 | — |
| 2025-06 · ICCV 2025 | **Epona** — EponaV1: Autoregressive Diffusion World Model for Autonomous Driving | [Paper](https://arxiv.org/abs/2506.24113) | [Yes](https://github.com/Kevin-thu/Epona/) | 388 | [Project](https://kevin-thu.github.io/Epona/) |
| 2025-04 | **WoTE** — WoTE: End-to-End Driving with Online Trajectory Evaluation via BEV World Model | [Paper](https://arxiv.org/abs/2504.01941) | [Yes](https://github.com/liyingyanUCAS/WoTE) | 270 | — |
| 2025-03 | **Cosmos-Transfer1** — Cosmos-Transfer1: Conditional World Generation with Adaptive Multimodal Control | [Paper](https://arxiv.org/abs/2503.14492) | [Yes](https://github.com/nvidia-cosmos/cosmos-transfer1) | 826 | — |
| 2025-01 · ICCV 2025 | **HERMES** — HERMES: A Unified Self-Driving World Model for Simultaneous 3D Scene Understanding and Generation | [Paper](https://arxiv.org/abs/2501.14729) | [Yes](https://github.com/LMD0311/HERMES) | 264 | — |
| 2025-01 | **Cosmos** — Cosmos World Foundation Model Platform for Physical AI | [Paper](https://arxiv.org/abs/2501.03575) | [Yes](https://github.com/nvidia-cosmos/cosmos-predict1) | 473 | — |
| 2024-12 | **GaussianAD** — GaussianAD: Gaussian-Centric End-to-End Autonomous Driving | [Paper](https://arxiv.org/abs/2412.10371) | [Yes](https://github.com/wzzheng/GaussianAD) | 130 | — |
| 2024-06 · ICLR 2025 | **LAW** — LAW: Enhancing End-to-End Autonomous Driving with Latent World Model | [Paper](https://arxiv.org/abs/2406.08481) | [Yes](https://github.com/BraveGroup/LAW) | 391 | — |
| 2024-05 · NEURIPS 2024 | **Vista** — Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability | [Paper](https://arxiv.org/abs/2405.17398) | [Yes](https://github.com/OpenDriveLab/Vista) | 901 | [Project](https://vista-demo.github.io) |
| 2023-11 | **OccWorld** — OccWorld: Learning a 3D Occupancy World Model for Autonomous Driving | [Paper](https://arxiv.org/abs/2311.16038) | [Yes](https://github.com/wzzheng/OccWorld) | 587 | — |

## Public Datasets

The dataset index follows the training and evaluation resources documented by ReCogDrive. Access conditions remain those of each original provider.

| Dataset | Task | Scale | Access | Resources |
|---|---|---|---|---|
| **Talk2Car** | Language Grounding | 11,959 commands · 850 videos | Open | [Homepage](https://github.com/talk2car/Talk2Car) · [Paper](https://arxiv.org/abs/1909.10838) · [Code](https://github.com/talk2car/Talk2Car) |
| **SUTD-TrafficQA** | Traffic Video QA | 10,080 videos · 62,535 QA pairs | Request | [Homepage](https://github.com/sutdcv/SUTD-TrafficQA) · [Paper](https://arxiv.org/abs/2103.15538) · [Code](https://github.com/sutdcv/SUTD-TrafficQA) |
| **DRAMA** | Risk Localization & Captioning | 17,785 scenarios | Open | [Homepage](https://usa.honda-ri.com/drama) · [Paper](https://arxiv.org/abs/2209.10767) |
| **NuScenes-QA** | Multimodal Driving QA | 34,149 scenes · 459,941 QA pairs | Open | [Homepage](https://github.com/qiantianwen/NuScenes-QA) · [Paper](https://arxiv.org/abs/2305.14836) · [Code](https://github.com/qiantianwen/NuScenes-QA) |
| **DriveGPT4 / BDD-X** | Instruction Tuning & Control | 16,803 train · 2,123 test clips | Project | [Homepage](https://tonyxuqaq.github.io/projects/DriveGPT4/) · [Paper](https://arxiv.org/abs/2310.01412) |
| **LingoQA** | Driving Video QA | 28K scenarios · 419K annotations | Open | [Homepage](https://github.com/wayveai/LingoQA) · [Paper](https://arxiv.org/abs/2312.14115) · [Code](https://github.com/wayveai/LingoQA) |
| **DriveLM** | Graph Visual QA | 4,072 train · 799 validation frames | Open | [Homepage](https://github.com/OpenDriveLab/DriveLM) · [Paper](https://arxiv.org/abs/2312.14150) · [Code](https://github.com/OpenDriveLab/DriveLM) |
| **MAPLM** | Map & Traffic Understanding | 2M point clouds · panoramic imagery | Open | [Homepage](https://github.com/LLVM-AD/MAPLM) · [Code](https://github.com/LLVM-AD/MAPLM) |
| **NuInstruct** | Multi-view Instruction QA | 91K pairs · 17 subtasks | Open | [Homepage](https://github.com/xmed-lab/NuInstruct) · [Paper](https://arxiv.org/abs/2401.00988) · [Code](https://github.com/xmed-lab/NuInstruct) |
| **CODA-LM** | Corner-case Evaluation | 9,768 scenarios · 63K+ annotations | Open | [Homepage](https://coda-dataset.github.io/coda-lm/) · [Paper](https://arxiv.org/abs/2404.10595) · [Code](https://github.com/DLUT-LYZ/CODA-LM) |
| **OmniDrive-nuScenes** | 3D Perception & Reasoning | nuScenes-derived · offline and online QA | Open | [Homepage](https://github.com/NVlabs/OmniDrive) · [Paper](https://arxiv.org/abs/2405.01533) · [Code](https://github.com/NVlabs/OmniDrive) |
| **Senna Planning QA** | Planning-oriented QA | Generated from nuScenes | Generation Scripts | [Homepage](https://github.com/hustvl/Senna) · [Paper](https://arxiv.org/abs/2410.22313) · [Code](https://github.com/hustvl/Senna) |

## Public Evaluation Benchmarks

| Benchmark | Track | Evaluation Setting | Primary Metric | Resources |
|---|---|---|---|---|
| **NAVSIM** | End-to-End Planning | Non-reactive simulation | PDMS | [Homepage](https://github.com/autonomousvision/navsim) · [Paper](https://arxiv.org/abs/2406.15349) · [Code](https://github.com/autonomousvision/navsim) |
| **Bench2Drive** | End-to-End Planning | CARLA closed-loop | Driving Score | [Homepage](https://thinklab-sjtu.github.io/Bench2Drive/) · [Paper](https://arxiv.org/abs/2406.03877) · [Code](https://github.com/Thinklab-SJTU/Bench2Drive) |
| **nuPlan** | Planning | Reactive closed-loop | Closed-loop score | [Homepage](https://www.nuplan.org/) · [Paper](https://arxiv.org/abs/2403.04133) · [Code](https://github.com/motional/nuplan-devkit) |
| **CARLA Leaderboard 2.0** | End-to-End Planning | Interactive closed-loop | Driving Score | [Homepage](https://leaderboard.carla.org/) · [Code](https://github.com/carla-simulator/leaderboard) |
| **nuScenes Planning** | Planning / World Model | Open-loop log replay | Avg. L2 / Collision | [Homepage](https://www.nuscenes.org/) · [Paper](https://arxiv.org/abs/1903.11027) · [Code](https://github.com/nutonomy/nuscenes-devkit) |
| **DriveLM** | VLA / Reasoning | Graph VQA | Accuracy / language metrics | [Homepage](https://github.com/OpenDriveLab/DriveLM) · [Paper](https://arxiv.org/abs/2312.14150) · [Code](https://github.com/OpenDriveLab/DriveLM) |
| **Reason2Drive** | VLA / Reasoning | Video-text reasoning | Reasoning score | [Homepage](https://github.com/OpenDriveLab/Reason2Drive) · [Paper](https://arxiv.org/abs/2312.03661) · [Code](https://github.com/OpenDriveLab/Reason2Drive) |
| **DriveBench** | VLA / Reliability | 17 visual reliability settings | Accuracy / language / GPT score | [Homepage](https://drive-bench.github.io/) · [Paper](https://arxiv.org/abs/2501.04003) · [Code](https://github.com/worldbench/DriveBench) |

## Leaderboard

Benchmark results are stored in [data/leaderboard.json](data/leaderboard.json). Submission requirements and reproducibility checks are documented in [benchmark/README.md](benchmark/README.md). Results from different protocol versions, sensor configurations, or data splits are not ranked together.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before adding papers, benchmarks, or leaderboard results. Run `npm run validate` before opening a pull request.

## License

This project is released under the [Apache License 2.0](LICENSE).
