# Contributing

欢迎补充论文、数据集、基准和可复现结果。为了让目录长期可信，请把一次 Pull Request 限制在一种变更类型，并提供可核对的一手来源。

## 新增论文

编辑 `data/papers.json`，保持按研究方向和年份组织。必要字段包括唯一 `id`、简称、完整标题、方向、年份、会议、标签、数据集和论文链接。

收录条件：

- 与端到端自动驾驶、驾驶世界模型或 VLA 直接相关；
- 至少有 arXiv、会议论文页或出版社页面；
- 标题、年份和作者项目链接可交叉核对；
- 不使用博客聚合、搜索结果页或二次转载作为唯一来源。

## 新增基准

编辑 `data/benchmarks.json`，说明评测形态、数据规模、核心指标和 `higherIsBetter`。开放环、闭环、反应式和非反应式协议必须明确标注。

## 提交榜单结果

先阅读 `benchmark/README.md`，然后复制 `benchmark/submissions/example.json`。所有结果都必须提供代码与评测证据。维护者审核后再把条目加入 `data/leaderboard.json`。

## 本地检查

```bash
npm run validate
npm run serve
```

检查网站卡片、筛选、基准切换、移动端布局和所有新增链接。

