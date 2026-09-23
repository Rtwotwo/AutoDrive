import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const papersPath = join(root, 'data', 'papers.json');
const cachePath = join(root, 'data', 'github-stars.json');
const papers = JSON.parse(await readFile(papersPath, 'utf8'));

function repositoryFromUrl(url = '') {
  const match = url.match(/^https:\/\/github\.com\/([^/]+)\/([^/#?]+)/i);
  return match ? `${match[1]}/${match[2].replace(/\.git$/i, '')}` : '';
}

let previous = { repositories: {} };
try {
  previous = JSON.parse(await readFile(cachePath, 'utf8'));
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}

const repositories = [...new Set(papers.map((paper) => repositoryFromUrl(paper.code)).filter(Boolean))];
const results = { ...previous.repositories };
let cursor = 0;

async function fetchStars(repository) {
  const response = await fetch(`https://github.com/${repository}`, {
    headers: { 'User-Agent': 'AutoDrive-Research-Hub/1.0', Accept: 'text/html' },
    redirect: 'follow'
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const html = await response.text();
  const value = html.match(/"stargazerCount":(\d+)/)?.[1]
    || html.match(/class="social-count[^>]*">\s*([0-9,.kKmM]+)\s*</)?.[1];
  if (!value) throw new Error('star count not found');
  const normalized = value.toLowerCase().replace(/,/g, '');
  const multiplier = normalized.endsWith('k') ? 1_000 : normalized.endsWith('m') ? 1_000_000 : 1;
  const stars = Math.round(Number.parseFloat(normalized) * multiplier);
  if (!Number.isFinite(stars)) throw new Error('invalid star count');
  results[repository] = { stars, url: `https://github.com/${repository}` };
  console.log(`${repository}: ${stars}`);
}

async function worker() {
  while (cursor < repositories.length) {
    const repository = repositories[cursor++];
    try {
      await fetchStars(repository);
    } catch (error) {
      console.warn(`${repository}: ${error.message}; keeping cached value`);
    }
  }
}

await Promise.all(Array.from({ length: 6 }, worker));
const updatedAt = new Date().toISOString();
await writeFile(cachePath, `${JSON.stringify({ updatedAt, repositories: results }, null, 2)}\n`, 'utf8');

for (const paper of papers) {
  const repository = repositoryFromUrl(paper.code);
  paper.openSource = Boolean(paper.code);
  paper.stars = repository && Number.isInteger(results[repository]?.stars) ? results[repository].stars : null;
}
await writeFile(papersPath, `${JSON.stringify(papers, null, 2)}\n`, 'utf8');
console.log(`Updated ${Object.keys(results).length}/${repositories.length} GitHub repositories at ${updatedAt}.`);
