<div id="top" align="center">

# AutoDrive Research Hub

### 自动驾驶前沿论文追踪与公共测试基准平台

[![Papers](https://img.shields.io/badge/Papers-35-ff5c35?style=flat-square)](#精选论文)
[![Tracks](https://img.shields.io/badge/Tracks-E2E%20%7C%20World%20Model%20%7C%20VLA-6678ff?style=flat-square)](#研究版图)
[![Benchmarks](https://img.shields.io/badge/Public_Benchmarks-7-c8f33d?style=flat-square)](#公共测试基准)
[![License](https://img.shields.io/badge/License-Apache--2.0-black?style=flat-square)](LICENSE)

一个面向研究者的自动驾驶知识入口：持续追踪 **端到端驾驶（End-to-End）**、**世界模型（World Model）** 与 **视觉-语言-动作模型（VLA）**，并通过公开测试协议、结构化数据和可审计提交构建社区排行榜。

[浏览网站](#本地运行) · [查看基准](benchmark/README.md) · [贡献论文](CONTRIBUTING.md) · [提交结果](#提交排行榜结果)

</div>

> 最后人工整理：2026-09-23。论文条目以 arXiv、会议主页和作者官方代码库为主要来源；正式引用前请再次核对论文最新版本。

## 项目目标

- 🗂️ **统一分类**：用一致的字段组织方法、年份、会议、标签、数据集、论文、代码和项目主页。
- 🧭 **研究路线**：明确区分端到端规划、世界动力学建模和语言驱动行动三条主线，同时保留交叉方向。
- 🧪 **协议优先**：开放环、闭环、反应式和非反应式评测分别记录，拒绝没有依据的跨协议总排名。
- 🏁 **公共榜单**：排行榜条目使用 JSON 提交，并要求提供代码、配置和原始评测证据。
- 🌐 **零后端发布**：网站可直接部署到 GitHub Pages；本地只需要 Node.js 18+。

## 研究版图

```text
Autonomous Driving Foundation Models
├── End-to-End Driving
│   ├── Imitation learning & privileged learning
│   ├── Planning-oriented unified stacks
│   ├── Sparse / vectorized scene representations
│   └── Generative, diffusion & flow policies
├── World Models
│   ├── Pixel/video generative worlds
│   ├── BEV & occupancy dynamics
│   ├── Latent dynamics and self-supervision
│   └── Simulation, data generation & policy learning
└── Vision-Language-Action
    ├── Driving QA & chain reasoning
    ├── Language-conditioned closed-loop driving
    ├── Generalist multimodal policies
    └── Dual-system VLM + numerical planner
```

### 方向说明

| 方向 | 核心问题 | 代表范式 | 重点指标 |
|---|---|---|---|
| End-to-End | 如何从传感器输入直接得到安全、实时的轨迹或控制？ | UniAD、VAD、SparseDrive、DiffusionDrive | 闭环驾驶分、碰撞、舒适性、延迟 |
| World Model | 如何学习可用于预测、生成和决策的交通世界动力学？ | GAIA-1、DriveDreamer、Drive-WM、LAW | 时空一致性、可控性、规划增益 |
| VLA | 如何让视觉理解、语言推理和驾驶动作形成统一策略？ | LMDrive、DriveLM、DriveVLM、Senna、EMMA | 决策正确率、指令遵循、闭环安全 |

## 精选论文

完整的机器可读列表位于 [`data/papers.json`](data/papers.json)，网站支持按方向和关键词筛选。

<details open>
<summary><b>🚗 End-to-End Driving</b></summary>

| 年份 | 方法 | 论文 | 代码 | 关键词 |
|---|---|---|---|---|
| 2026 | SparseDriveV2 | [arXiv](https://arxiv.org/abs/2603.29163) | [GitHub](https://github.com/swc-17/SparseDriveV2) | Scoring, Factorized Vocabulary |
| 2025 | DiffusionDrive | [arXiv](https://arxiv.org/abs/2411.15139) | [GitHub](https://github.com/hustvl/DiffusionDrive) | Diffusion Policy, Multi-Modal Planning |
| 2024 | SparseDrive | [arXiv](https://arxiv.org/abs/2405.19620) | [GitHub](https://github.com/swc-17/SparseDrive) | Sparse Representation, Parallel Planner |
| 2024 | GenAD | [arXiv](https://arxiv.org/abs/2402.11502) | [GitHub](https://github.com/OpenDriveLab/GenAD) | Generative Modeling, Prediction |
| 2023 | VAD | [arXiv](https://arxiv.org/abs/2303.12077) | [GitHub](https://github.com/hustvl/VAD) | Vectorized Scene, Efficiency |
| 2023 | UniAD | [arXiv](https://arxiv.org/abs/2212.10156) | [GitHub](https://github.com/OpenDriveLab/UniAD) | Unified Stack, Planning-Oriented |
| 2022 | TCP | [arXiv](https://arxiv.org/abs/2206.08129) | [GitHub](https://github.com/OpenDriveLab/TCP) | Trajectory, Control |
| 2021 | TransFuser | [arXiv](https://arxiv.org/abs/2104.09224) | [GitHub](https://github.com/autonomousvision/transfuser) | Sensor Fusion, Transformer |

</details>

<details open>
<summary><b>🌍 World Model</b></summary>

| 年份 | 方法 | 论文 | 代码 / 项目 | 关键词 |
|---|---|---|---|---|
| 2026 | DriveWorld-VLA | [arXiv](https://arxiv.org/abs/2602.06521) | [GitHub](https://github.com/liulin815/DriveWorld-VLA) | World Model, VLA |
| 2025 | World4Drive | [arXiv](https://arxiv.org/abs/2507.00603) | [GitHub](https://github.com/ucaszyp/World4Drive) | Physical Latent Space, Intention |
| 2025 | LAW | [arXiv](https://arxiv.org/abs/2406.08481) | [GitHub](https://github.com/BraveGroup/LAW) | Latent Dynamics, Self-Supervision |
| 2024 | Vista | [arXiv](https://arxiv.org/abs/2405.17398) | [Project](https://opendrivelab.com/Vista/) | Generalization, Controllability |
| 2024 | DriveDreamer-2 | [arXiv](https://arxiv.org/abs/2403.06845) | [GitHub](https://github.com/f1yfisher/DriveDreamer2) | HD Map, Traffic Generation |
| 2023 | Drive-WM | [arXiv](https://arxiv.org/abs/2311.17918) | [Project](https://drive-wm.github.io/) | Multi-View Forecasting, Planning |
| 2023 | DriveDreamer | [arXiv](https://arxiv.org/abs/2309.09777) | [GitHub](https://github.com/JeffWang987/DriveDreamer) | Diffusion, Controllable Generation |
| 2023 | GAIA-1 | [arXiv](https://arxiv.org/abs/2309.17080) | [Project](https://wayve.ai/thinking/introducing-gaia1/) | Video Tokens, Generative World Model |

</details>

<details open>
<summary><b>🤖 Vision-Language-Action</b></summary>

| 年份 | 方法 | 论文 | 代码 / 项目 | 关键词 |
|---|---|---|---|---|
| 2026 | UniDriveVLA | [arXiv](https://arxiv.org/abs/2604.02190) | [GitHub](https://github.com/xiaomi-research/unidrivevla) | Unified VLA, Expert Decoupling |
| 2025 | VLA4AD Survey | [arXiv](https://arxiv.org/abs/2506.24044) | [GitHub](https://github.com/JohnsonJiang1996/Awesome-VLA4AD) | Survey, Taxonomy |
| 2024 | EMMA | [arXiv](https://arxiv.org/abs/2410.23262) | [Project](https://waymo.com/research/emma/) | Generalist Model, Textual Trajectory |
| 2024 | Senna | [arXiv](https://arxiv.org/abs/2410.22313) | [GitHub](https://github.com/hustvl/Senna) | Dual System, Planning QA |
| 2024 | DriveVLM | [arXiv](https://arxiv.org/abs/2402.12289) | [GitHub](https://github.com/tsinghua-mars-lab/DriveVLM) | Hierarchical Planning, Dual System |
| 2024 | DriveLM | [arXiv](https://arxiv.org/abs/2312.14150) | [GitHub](https://github.com/OpenDriveLab/DriveLM) | Graph VQA, Reasoning |
| 2024 | LMDrive | [arXiv](https://arxiv.org/abs/2312.07488) | [GitHub](https://github.com/opendilab/LMDrive) | Closed-Loop, Instruction Following |
| 2023 | DriveGPT4 | [arXiv](https://arxiv.org/abs/2310.01412) | [GitHub](https://github.com/tonychenxyz/DriveGPT4) | Video LLM, Control |

</details>

## 公共测试基准

| 基准 | 方向 | 评测形态 | 核心指标 | 入口 |
|---|---|---|---|---|
| NAVSIM | End-to-End Planning | 非反应式短时仿真 | PDMS | [Paper](https://arxiv.org/abs/2406.15349) · [Code](https://github.com/autonomousvision/navsim) |
| Bench2Drive | End-to-End Planning | CARLA 闭环 | Driving Score | [Paper](https://arxiv.org/abs/2406.03877) · [Code](https://github.com/Thinklab-SJTU/Bench2Drive) |
| nuPlan | Planning | 反应式闭环 | Closed-loop score | [Website](https://www.nuplan.org/) · [Code](https://github.com/motional/nuplan-devkit) |
| CARLA Leaderboard 2.0 | End-to-End Planning | 交互式闭环 | Driving Score | [Leaderboard](https://leaderboard.carla.org/) |
| nuScenes Planning | Planning / World Model | 开放环回放 | Avg. L2 / Collision | [Dataset](https://www.nuscenes.org/) |
| DriveLM | VLA / Reasoning | Graph VQA | Accuracy / language metrics | [Paper](https://arxiv.org/abs/2312.14150) |
| Reason2Drive | VLA / Reasoning | Video-text reasoning | Reasoning score | [Paper](https://arxiv.org/abs/2312.03661) |

基准元数据位于 [`data/benchmarks.json`](data/benchmarks.json)，已审核的结果位于 [`data/leaderboard.json`](data/leaderboard.json)。协议版本、数据划分或传感器配置不同的结果不应放入同一排名。

## 提交排行榜结果

1. 复制 [`benchmark/submissions/example.json`](benchmark/submissions/example.json)，并以唯一的 `id` 命名文件。
2. 填写 `benchmarkId`、方法、团队、测试划分、分数、代码与评测证据。
3. 在仓库根目录运行 `npm run validate`。
4. 发起 Pull Request；维护者核对协议和证据后，将条目合并到 `data/leaderboard.json`。

详细证据要求和审核规则见 [`benchmark/README.md`](benchmark/README.md)。

## 本地运行

```bash
npm run validate
npm run serve
```

浏览器打开 <http://127.0.0.1:8000>。项目没有运行时依赖，不需要 `npm install`。

## GitHub Pages 发布

仓库包含 Pages 工作流。推送到 `main` 后，在 GitHub 仓库设置中将 **Pages → Source** 设为 **GitHub Actions**，即可发布静态网站。

## 项目结构

```text
.
├── index.html                    # 研究与排行榜网站
├── assets/                       # 样式与交互脚本
├── data/
│   ├── papers.json               # 论文目录（唯一数据源）
│   ├── benchmarks.json           # 基准元数据与协议说明
│   └── leaderboard.json          # 已审核榜单结果
├── benchmark/
│   ├── README.md                 # 提交与审核规范
│   ├── schemas/                  # 提交 JSON Schema
│   └── submissions/              # 社区候选结果
├── scripts/                      # 数据校验与本地静态服务器
└── .github/workflows/            # PR 校验与 Pages 发布
```

## 收录与维护原则

- 论文优先选择有公开预印本，并在方法、实验或影响力上具有代表性的工作。
- 条目必须链接到作者或机构维护的论文、代码、项目和数据页面。
- 不根据单一开放环 L2 指标推断真实闭环安全性。
- 同名基准出现协议升级时，应新增版本字段或独立榜单，不能覆盖旧结果。
- `published` 表示论文中公开报告的结果；`verified` 表示维护者按公开配置复核；两者含义不同。

## 致谢

项目的信息架构参考了 [Awesome-GE2EAD](https://github.com/AutoLab-SAI-SJTU/GE2EAD)，并针对 End-to-End、World Model、VLA 三条路线和公共评测工作流重新设计。感谢所有公开论文、代码、数据集和评测平台的作者。

## License

Apache License 2.0。详见 [`LICENSE`](LICENSE)。

<p align="right"><a href="#top">返回顶部 ↑</a></p>
