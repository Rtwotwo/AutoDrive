import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('.', import.meta.url)), '..');
const paperPath = join(root, 'data/papers.json');
const cachePath = join(root, 'data/citations.json');
const papers = JSON.parse(await readFile(paperPath, 'utf8'));
let previous = { records: {} };
try { previous = JSON.parse(await readFile(cachePath, 'utf8')); } catch (error) { if (error.code !== 'ENOENT') throw error; }
const checkedAt = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai' }).format(new Date());
const fields = 'id,title,doi,cited_by_count,publication_year,type';
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const normalized = (value = '') => value.toLowerCase().normalize('NFKD').replace(/\\[a-z]+/g, '').replace(/[^a-z0-9]/g, '');
const titles = (paper) => {
  const list = [paper.title, ...(paper.citationTitleAliases || [])];
  for (const title of [...list]) {
    const colon = title.indexOf(':');
    if (colon > 0 && colon < 28 && title.length - colon > 35) list.push(title.slice(colon + 1));
  }
  return new Set(list.map(normalized));
};
const doiOf = (paper) => {
  const arxiv = paper.paper?.match(/arxiv\.org\/(?:abs|html|pdf)\/(\d{4}\.\d{4,5})/i)?.[1];
  return (paper.doi || (arxiv ? `10.48550/arxiv.${arxiv}` : paper.paper?.match(/doi\.org\/(.+)/i)?.[1]) || '').toLowerCase();
};
const works = new Map();
const failures = [];

async function request(url) {
  const target = new URL(url);
  if (process.env.OPENALEX_API_KEY) target.searchParams.set('api_key', process.env.OPENALEX_API_KEY);
  for (let attempt = 0; attempt < 2; attempt++) {
    const response = await fetch(target, { signal: AbortSignal.timeout(30000), headers: { 'User-Agent': 'AutoDrive-public-research-catalog/1.0' } });
    if (response.status === 404) return null;
    if (response.status === 429 && attempt === 0) { await delay(5000); continue; }
    if (!response.ok) throw new Error(`OpenAlex HTTP ${response.status}`);
    return response.json();
  }
}

// Search several complete titles at once to include formally published records
// as well as their arXiv counterparts. Accept only exact normalized-title matches
// (or reviewed title aliases), never the first search hit or a fuzzy match.
const groups = [];
let group = [];
for (const paper of papers) {
  const query = paper.title.replace(/\\[a-z]+/g, ' ').replace(/[^a-zA-Z0-9\s-]/g, ' ').replace(/\s+/g, ' ').trim();
  if (group.length && (group.length >= 35 || encodeURIComponent([...group, query].join('|')).length > 6500)) {
    groups.push(group); group = [];
  }
  group.push(query);
}
if (group.length) groups.push(group);

for (let index = 0; index < groups.length; index++) {
  const url = new URL('https://api.openalex.org/works');
  url.searchParams.set('filter', 'title.search:' + groups[index].join('|'));
  url.searchParams.set('select', fields);
  url.searchParams.set('per-page', '200');
  try {
    const data = await request(url);
    for (const work of data?.results || []) works.set(work.id, work);
    console.log(`Title batch ${index + 1}/${groups.length}: ${data?.results?.length || 0} records.`);
    if (data?.meta?.count > 200) {
      url.searchParams.set('page', '2');
      const next = await request(url);
      for (const work of next?.results || []) works.set(work.id, work);
    }
  } catch (error) {
    failures.push({ stage: 'title-batch', batch: index + 1, error: error.message });
    console.warn(`Title batch ${index + 1}: ${error.message}`);
  }
  await delay(1200);
}

function candidatesFor(paper) {
  const titleSet = titles(paper);
  const doi = doiOf(paper);
  return [...works.values()].filter(work => {
    if (!Number.isInteger(work.cited_by_count) || work.cited_by_count < 0) return false;
    const exactTitle = titleSet.has(normalized(work.title));
    const exactDOI = doi && work.doi?.toLowerCase() === 'https://doi.org/' + doi;
    return exactTitle && (exactDOI || Math.abs(work.publication_year - paper.year) <= 2);
  });
}

// Identifier lookup also handles newly indexed papers and records missed by
// search. A missing work is unknown, not evidence of zero citations.
for (const paper of papers.filter(paper => !candidatesFor(paper).length)) {
  const doi = doiOf(paper);
  if (!doi) continue;
  try {
    const data = await request('https://api.openalex.org/works/https://doi.org/' + doi + '?select=' + fields);
    if (data?.id) works.set(data.id, data);
  } catch (error) {
    failures.push({ stage: 'identifier', paperId: paper.id, error: error.message });
  }
  await delay(400);
}

const records = {};
for (const paper of papers) {
  const matches = candidatesFor(paper).sort((a, b) => b.cited_by_count - a.cited_by_count || Number(a.type === 'preprint') - Number(b.type === 'preprint'));
  const match = matches[0];
  const failed = failures.some(item => item.paperId === paper.id);
  let record;
  if (match) {
    record = {
      count: match.cited_by_count, source: 'OpenAlex', url: match.id, checkedAt,
      status: 'available', matchedTitle: match.title, doi: match.doi,
      publicationYear: match.publication_year, recordType: match.type,
      match: match.doi?.toLowerCase() === 'https://doi.org/' + doiOf(paper) ? 'doi-and-title' : 'exact-title',
      candidates: matches.map(work => ({ url: work.id, count: work.cited_by_count, doi: work.doi, type: work.type }))
    };
  } else if (failed && previous.records[paper.id]?.status === 'available') {
    // Keep the original retrieval date when preserving an earlier observation.
    record = { ...previous.records[paper.id], refreshError: 'Latest identifier lookup failed.' };
  } else {
    record = { count: null, source: 'OpenAlex', checkedAt, status: failed ? 'unavailable' : 'not-indexed' };
  }
  records[paper.id] = record;
  paper.citationCount = record.count;
  paper.citationSource = record.source;
  paper.citationStatus = record.status;
  paper.citationCheckedAt = record.checkedAt;
  if (record.url) paper.citationURL = record.url; else delete paper.citationURL;
}
const cache = {
  source: 'OpenAlex', checkedAt,
  policy: 'Use the highest cited_by_count among exact-title/DOI-matched versions of the same paper. Never sum version counts. A verified 0 differs from N/A.',
  records, failures
};
await writeFile(cachePath, JSON.stringify(cache, null, 2) + '\n');
await writeFile(paperPath, JSON.stringify(papers, null, 2) + '\n');
const available = papers.filter(paper => Number.isInteger(paper.citationCount)).length;
console.log(`Citation snapshot: ${available}/${papers.length} matched; ${papers.length - available} N/A; checked ${checkedAt}.`);
await import('./render_readme.mjs');
