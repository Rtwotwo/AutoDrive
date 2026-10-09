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

const repositories = [...new Set(papers.map((paper) => repositoryFromUrl(paper.githubRepo || paper.code)).filter(Boolean))];
const results = { ...previous.repositories };
const checkedAt = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai' }).format(new Date());
const headers = { 'User-Agent': 'AutoDrive-Research-Hub/1.0', Accept: 'application/vnd.github+json' };
if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
let apiAvailable = true;
let refreshed = 0;
let cursor = 0;

async function fetchStars(repository) {
  let stars;
  if (apiAvailable) {
    try {
      const response = await fetch(`https://api.github.com/repos/${repository}`, { headers, signal: AbortSignal.timeout(20000) });
      if (response.status === 403 || response.status === 429) apiAvailable = false;
      if (response.ok) stars = (await response.json()).stargazers_count;
    } catch { /* Fall back to an exact count on the public page. */ }
  }
  if (!Number.isInteger(stars)) {
    const response = await fetch(`https://github.com/${repository}`, {
      headers: { 'User-Agent': 'AutoDrive-Research-Hub/1.0', Accept: 'text/html' },
      signal: AbortSignal.timeout(20000)
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const value = html.match(/"stargazerCount":(\d+)/)?.[1]
      || html.match(/id="repo-stars-counter-star"[^>]*title="([\d,]+)"/)?.[1];
    if (!value) throw new Error('exact star count unavailable');
    stars = Number(value.replaceAll(',', ''));
  }
  if (!Number.isInteger(stars) || stars < 0) throw new Error('invalid star count');
  results[repository] = { stars, url: `https://github.com/${repository}`, checkedAt };
  refreshed++;
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

await Promise.all(Array.from({ length: 4 }, worker));
const updatedAt = new Date().toISOString();
await writeFile(cachePath, `${JSON.stringify({ updatedAt, repositories: results }, null, 2)}\n`, 'utf8');

const cache = new Map(Object.entries(results).map(([name, record]) => [name.toLowerCase(), record]));
for (const paper of papers) {
  const repository = repositoryFromUrl(paper.githubRepo || paper.code);
  const record = cache.get(repository.toLowerCase());
  paper.stars = repository && Number.isInteger(record?.stars) ? record.stars : null;
  paper.githubStarsCheckedAt = paper.stars === null ? null : record.checkedAt || previous.updatedAt?.slice(0, 10) || null;
  // Star refreshes preserve the manually audited implementation status.
}
await writeFile(papersPath, `${JSON.stringify(papers, null, 2)}\n`, 'utf8');
await import('./render_readme.mjs');
console.log(`Refreshed ${refreshed}/${repositories.length} GitHub repositories at ${updatedAt}; cached observations retain their original dates.`);
