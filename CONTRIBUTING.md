# Contributing

Contributions of papers, datasets, benchmarks, and reproducible results are welcome. Keep each pull request focused on one type of change and cite primary sources that maintainers can verify.

## Adding a Paper

The paper catalog is generated from a Zotero BibTeX export. Add the paper to the Zotero collection, export the library, and run:

```bash
node scripts/sync_zotero.mjs path/to/Autonomous-Driving.bib
```

An eligible paper must:

- directly address end-to-end autonomous driving, driving world models, or vision-language-action driving;
- provide an arXiv, conference, or publisher page;
- have a title, year, and source that can be independently verified;
- use an author-maintained project or repository when code links are included.

## Adding a Benchmark

Edit `data/benchmarks.json` and specify the evaluation setting, data scale, primary metric, and `higherIsBetter`. Clearly distinguish open-loop, non-reactive simulation, reactive simulation, and interactive closed-loop evaluation.

## Submitting a Leaderboard Result

Read `benchmark/README.md`, copy `benchmark/submissions/example.json`, and provide code plus evaluation evidence. Maintainers add accepted entries to `data/leaderboard.json` after reviewing the protocol and evidence.

## Local Checks

```bash
npm run validate
npm run serve
```

Check paper filters, search, benchmark selection, links, and responsive layouts before opening a pull request.

