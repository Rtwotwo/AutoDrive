import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const readJson = async (path) => JSON.parse(await readFile(join(root, path), 'utf8'));
const papers = await readJson('data/papers.json');
const benchmarks = await readJson('data/benchmarks.json');
const leaderboard = await readJson('data/leaderboard.json');
const errors = [];
const https = (value) => typeof value === 'string' && value.startsWith('https://');

function unique(items, label) {
  const seen = new Set();
  for (const item of items) {
    if (!item.id) errors.push(`${label}: missing id`);
    if (seen.has(item.id)) errors.push(`${label}: duplicate id ${item.id}`);
    seen.add(item.id);
  }
}

unique(papers, 'papers'); unique(benchmarks, 'benchmarks'); unique(leaderboard, 'leaderboard');
const benchmarkIds = new Set(benchmarks.map((item) => item.id));
for (const paper of papers) {
  if (!['e2e','world-model','vla'].includes(paper.track)) errors.push(`paper ${paper.id}: invalid track`);
  if (!Number.isInteger(paper.year) || paper.year < 1980 || paper.year > 2100) errors.push(`paper ${paper.id}: invalid year`);
  if (!Array.isArray(paper.tags) || !paper.tags.length) errors.push(`paper ${paper.id}: tags required`);
  for (const field of ['paper','code','project']) if (paper[field] && !https(paper[field])) errors.push(`paper ${paper.id}: ${field} must use https`);
}
for (const benchmark of benchmarks) {
  if (!benchmark.primaryMetric || typeof benchmark.higherIsBetter !== 'boolean') errors.push(`benchmark ${benchmark.id}: metric metadata required`);
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
console.log(`Validation passed: ${papers.length} papers, ${benchmarks.length} benchmarks, ${leaderboard.length} leaderboard entries.`);

