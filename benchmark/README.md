# Public Benchmark Submission Guide

This directory defines the submission format for the AutoDrive Research Hub leaderboard. The platform aggregates results from public benchmarks without converting incompatible protocols into a single score.

## Submission Contents

Copy `submissions/example.json` and rename it to the entry's unique `id`. A submission must include:

- `benchmarkId`: an ID from `data/benchmarks.json`;
- `method` and `team`: the display name and responsible organization;
- `split`: the test split, challenge, and protocol version;
- `score`: a value for the benchmark's `primaryMetric`;
- `code`: a public implementation, configuration, and checkpoint;
- `evidence`: a stable link to raw logs, an official submission page, or a paper table;
- `notes`: sensors, backbone, training data, additional pretraining, and the evaluation command.

## Status Values

- `pending`: submitted by the community and awaiting protocol review;
- `published`: reported in a paper or official project but not independently rerun;
- `verified`: reproduced by maintainers or confirmed by the benchmark organizer.

`published` and `verified` describe different evidence levels. The website displays them separately.

## Reproducibility Checklist

- [ ] State the benchmark version, test split, and primary metric.
- [ ] List camera, LiDAR, map, language, and other input modalities.
- [ ] Disclose additional training data, pretrained weights, and closed-source model calls.
- [ ] Fix random seeds or report the mean and variance across runs when applicable.
- [ ] Provide the evaluation command, configuration, environment versions, and checkpoint.
- [ ] Ensure that the JSON score exactly matches the linked evidence.

## Review Process

1. Automated checks validate JSON structure, unique IDs, URLs, and benchmark references.
2. A maintainer reviews the split, protocol version, sensor configuration, and evidence.
3. Incomparable configurations receive separate sub-leaderboards or explicit method labels.
4. Accepted results are added to `data/leaderboard.json`.

## Scientific Scope

A leaderboard result describes performance under one public protocol. Open-loop trajectory errors do not replace closed-loop safety evaluation, and simulation results do not directly establish real-world deployment performance.

