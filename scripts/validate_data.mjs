import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const readJson = async (path) => JSON.parse(await readFile(join(root, path), 'utf8'));
const papers = await readJson('data/papers.json');
const citationCache = await readJson('data/citations.json');
const starCache = await readJson('data/github-stars.json');
const githubAudit = await readJson('data/github-audit.json');
const starRecords = new Map(Object.entries(starCache.repositories).map(([name, record]) => [name.toLowerCase(), record]));
const datasets = await readJson('data/datasets.json');
const benchmarks = await readJson('data/benchmarks.json');
const leaderboard = await readJson('data/leaderboard.json');
const errors = [];
const https = (value) => typeof value === 'string' && value.startsWith('https://');
const datasetCategories = new Set([
  'Perception and Multimodal Understanding',
  'Motion, Planning, and Cooperative Driving',
  'Simulation and Synthetic Data'
]);
const benchmarkCategories = new Set([
  'Closed-Loop Planning',
  'Open-Loop and Non-Reactive Planning',
  'VLA and Driving Reasoning',
  'Reliability and Robustness'
]);

function unique(items, label) {
  const seen = new Set();
  for (const item of items) {
    if (!item.id) errors.push(`${label}: missing id`);
    if (seen.has(item.id)) errors.push(`${label}: duplicate id ${item.id}`);
    seen.add(item.id);
  }
}

unique(papers, 'papers'); unique(datasets, 'datasets'); unique(benchmarks, 'benchmarks'); unique(leaderboard, 'leaderboard');
const benchmarkIds = new Set(benchmarks.map((item) => item.id));
for (const paper of papers) {
  const repository = paper.githubRepo?.match(/^https:\/\/github\.com\/([^/]+\/[^/#?]+)\/?$/i)?.[1];
  const stars = repository && starRecords.get(repository.toLowerCase());
  const audit = githubAudit.records?.[paper.id];
  if (paper.githubRepo && !repository) errors.push(`paper ${paper.id}: invalid GitHub repository URL`);
  if (paper.stars !== null && (!repository || stars?.stars !== paper.stars || stars?.checkedAt !== paper.githubStarsCheckedAt)) errors.push(`paper ${paper.id}: GitHub star snapshot mismatch`);
  if (paper.stars !== null && !/^\d{4}-\d{2}-\d{2}$/.test(paper.githubStarsCheckedAt || '')) errors.push(`paper ${paper.id}: a star count requires its observation date`);
  if (paper.stars === null && paper.githubStarsCheckedAt !== null) errors.push(`paper ${paper.id}: unknown stars cannot have an observation date`);
  if (!audit || audit.repository !== paper.githubRepo || audit.codeStatus !== paper.codeStatus || audit.codeScope !== (paper.codeScope || null)) errors.push(`paper ${paper.id}: repository audit mismatch`);
  if (paper.codeScope === 'partial' && paper.codeStatus !== 'released') errors.push(`paper ${paper.id}: partial releases must identify public code`);
  const citation = citationCache.records?.[paper.id];
  if (!(paper.citationCount === null || (Number.isInteger(paper.citationCount) && paper.citationCount >= 0))) errors.push(`paper ${paper.id}: invalid citationCount`);
  if (!['available','not-indexed','unavailable'].includes(paper.citationStatus)) errors.push(`paper ${paper.id}: invalid citationStatus`);
  if (paper.citationSource !== 'OpenAlex') errors.push(`paper ${paper.id}: invalid citationSource`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(paper.citationCheckedAt || '')) errors.push(`paper ${paper.id}: citationCheckedAt must be YYYY-MM-DD`);
  if (paper.citationStatus === 'available' && (!Number.isInteger(paper.citationCount) || !/^https:\/\/openalex\.org\/W\d+$/.test(paper.citationURL || ''))) errors.push(`paper ${paper.id}: available citations require a count and source record`);
  if (paper.citationStatus !== 'available' && paper.citationCount !== null) errors.push(`paper ${paper.id}: unknown citations must use null, not zero`);
  if (!citation || citation.count !== paper.citationCount || citation.source !== paper.citationSource || citation.status !== paper.citationStatus || citation.checkedAt !== paper.citationCheckedAt || citation.url !== paper.citationURL) errors.push(`paper ${paper.id}: citation snapshot mismatch`);
  if (!['e2e','world-model','vla','rsi'].includes(paper.track)) errors.push(`paper ${paper.id}: invalid track`);
  if (typeof paper.summary !== 'string' || paper.summary.trim().length < 40 || paper.summary.trim().length > 500) errors.push(`paper ${paper.id}: summary must be 40-500 characters`);
  if ('category' in paper) errors.push(`paper ${paper.id}: subcategory field is not allowed`);
  if (!Number.isInteger(paper.year) || paper.year < 1980 || paper.year > 2100) errors.push(`paper ${paper.id}: invalid year`);
  if (!/^\d{4}(?:-\d{2})?$/.test(paper.published || '')) errors.push(`paper ${paper.id}: invalid published date`);
  if (!Array.isArray(paper.tags) || !paper.tags.length) errors.push(`paper ${paper.id}: tags required`);
  if (!['released', 'pending', 'not-found'].includes(paper.codeStatus)) errors.push(`paper ${paper.id}: invalid codeStatus`);
  if (paper.openSource !== (paper.codeStatus === 'released')) errors.push(`paper ${paper.id}: openSource must match released code status`);
  if ((paper.codeStatus === 'released' || paper.codeStatus === 'pending') !== Boolean(paper.code)) errors.push(`paper ${paper.id}: code link must match released/pending status`);
  if (paper.stars !== null && (!Number.isInteger(paper.stars) || paper.stars < 0)) errors.push(`paper ${paper.id}: invalid stars`);
  for (const field of ['paper','code','project','githubRepo']) if (paper[field] && !https(paper[field])) errors.push(`paper ${paper.id}: ${field} must use https`);
}
if (Object.keys(githubAudit.records || {}).length !== papers.length) errors.push('repository audit must contain exactly one record per paper');
for (const track of ['e2e','vla','world-model','rsi']) {
  const items = papers.filter((paper) => paper.track === track);
  for (let index = 1; index < items.length; index += 1) {
    if (items[index].published > items[index - 1].published) errors.push(`${track}: papers must be sorted newest first`);
  }
}
for (const dataset of datasets) {
  if (!dataset.task || !dataset.scale || !dataset.access) errors.push(`dataset ${dataset.id}: task, scale, and access are required`);
  if (!datasetCategories.has(dataset.category) || 'group' in dataset) errors.push(`dataset ${dataset.id}: invalid category (or legacy group field)`);
  if (!dataset.paperTitle) errors.push(`dataset ${dataset.id}: paperTitle is required`);
  if (!https(dataset.homepage)) errors.push(`dataset ${dataset.id}: homepage must use https`);
  for (const field of ['paper','code']) if (dataset[field] && !https(dataset[field])) errors.push(`dataset ${dataset.id}: ${field} must use https`);
}
for (const benchmark of benchmarks) {
  if (!benchmark.primaryMetric || typeof benchmark.higherIsBetter !== 'boolean') errors.push(`benchmark ${benchmark.id}: metric metadata required`);
  if (!benchmarkCategories.has(benchmark.category)) errors.push(`benchmark ${benchmark.id}: invalid category`);
  if (!https(benchmark.homepage)) errors.push(`benchmark ${benchmark.id}: homepage must use https`);
}
function checkEntry(entry, source) {
  if (!benchmarkIds.has(entry.benchmarkId)) errors.push(`${source} ${entry.id}: unknown benchmarkId`);
  if (!Number.isFinite(entry.score)) errors.push(`${source} ${entry.id}: score must be finite`);
  if (!['pending','verified','published'].includes(entry.status)) errors.push(`${source} ${entry.id}: invalid status`);
  for (const field of ['code','evidence']) if (!https(entry[field])) errors.push(`${source} ${entry.id}: ${field} must use https`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(entry.date || '')) errors.push(`${source} ${entry.id}: date must be YYYY-MM-DD`);
}
leaderboard.forEach((entry) => checkEntry(entry, 'leaderboard'));

const submissionDir = join(root, 'benchmark', 'submissions');
for (const file of await readdir(submissionDir)) {
  if (!file.endsWith('.json') || file === 'example.json') continue;
  checkEntry(JSON.parse(await readFile(join(submissionDir, file), 'utf8')), `submission ${file}`);
}

if (errors.length) { console.error(`Validation failed (${errors.length})\n- ${errors.join('\n- ')}`); process.exit(1); }
console.log(`Validation passed: ${papers.length} papers, ${datasets.length} datasets, ${benchmarks.length} benchmarks, ${leaderboard.length} leaderboard entries.`);
