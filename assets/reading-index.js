const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[character]));

function metricCeiling(papers, field) {
  const values = papers.map(paper => paper[field]).filter(value => Number.isInteger(value) && value >= 0).sort((a, b) => a - b);
  if (!values.length) return 0;
  return Math.max(1, values[Math.max(0, Math.ceil(values.length * 0.95) - 1)]);
}

function normalizedSignal(value, ceiling) {
  if (!Number.isInteger(value) || value < 0) return null;
  if (ceiling <= 0) return 0;
  return Math.min(100, 100 * Math.log1p(value) / Math.log1p(ceiling));
}

export function computeReadingIndices(papers) {
  const citationCeiling = metricCeiling(papers, 'citationCount');
  const starCeiling = metricCeiling(papers, 'stars');
  return new Map(papers.map(paper => {
    const citations = normalizedSignal(paper.citationCount, citationCeiling);
    const stars = normalizedSignal(paper.stars, starCeiling);
    const signals = [citations, stars].filter(Number.isFinite);
    const score = signals.length ? Math.round(signals.reduce((sum, value) => sum + value, 0) / signals.length) : null;
    return [paper.id, {
      score,
      coverage: signals.length === 2 ? 'Complete' : signals.length === 1 ? 'Partial' : 'N/A',
      citationSignal: citations === null ? null : Math.round(citations),
      starSignal: stars === null ? null : Math.round(stars)
    }];
  }));
}

export function compareReadingIndices(a, b, scores) {
  const first = scores.get(a.id)?.score;
  const second = scores.get(b.id)?.score;
  if (first === null || first === undefined) return second === null || second === undefined ? 0 : 1;
  if (second === null || second === undefined) return -1;
  return second - first || String(b.published || '').localeCompare(String(a.published || '')) || String(a.name || '').localeCompare(String(b.name || ''), 'en');
}

export function readingIndexMarkup(paper, readingIndex) {
  const score = readingIndex?.score;
  const scoreLabel = Number.isInteger(score) ? `${score}<small>/100</small>` : 'N/A';
  const coverage = readingIndex?.coverage || 'N/A';
  const candidate = paper.githubRepo || paper.code || '';
  const repo = /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/.test(candidate)
    ? candidate.replace(/\/$/, '') : '';
  const starLabel = Number.isInteger(paper.stars) ? new Intl.NumberFormat('en-US').format(paper.stars) : 'N/A';
  const stars = repo
    ? `<a class="github-star-count" href="${escapeHTML(repo)}" target="_blank" rel="noopener noreferrer" title="Paper-related GitHub repository; checked ${escapeHTML(paper.githubStarsCheckedAt || 'date unavailable')}. Stars belong to the repository and may cover several papers.">★ ${starLabel} GitHub stars</a>`
    : `<span class="github-star-count unavailable" title="No verified paper-related GitHub repository was found">★ N/A GitHub stars</span>`;
  const title = 'Equal-weight average of log-scaled citation and GitHub star counts, each capped at the catalog 95th percentile. Partial means only one signal is available; this is an attention cue, not a quality or readability judgment.';
  return `<div class="reading-signals" title="${escapeHTML(title)}"><span class="reading-index"><strong>${scoreLabel}</strong><small>READING INDEX · ${escapeHTML(coverage)}</small></span>${stars}</div>`;
}
