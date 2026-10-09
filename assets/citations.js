const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[character]));

export function formatCitations(value) {
  return Number.isInteger(value) && value >= 0 ? new Intl.NumberFormat('en-US').format(value) : 'N/A';
}

export function compareCitations(a, b) {
  const first = Number.isInteger(a.citationCount) ? a.citationCount : -1;
  const second = Number.isInteger(b.citationCount) ? b.citationCount : -1;
  return second - first || String(b.published || '').localeCompare(String(a.published || '')) || String(a.name || '').localeCompare(String(b.name || ''), 'en');
}

export function citationMarkup(paper) {
  const value = formatCitations(paper.citationCount);
  const available = value !== 'N/A';
  const source = paper.citationSource || 'OpenAlex';
  const date = paper.citationCheckedAt || 'Date unavailable';
  const title = available ? `${source} citations, checked ${date}. One matched record; version counts are not summed.`
    : `${source}, checked ${date}. A matching citation record is not indexed or could not be retrieved; N/A does not mean zero.`;
  const label = `<span aria-hidden="true">↗</span> Cited by <strong>${value}</strong>`;
  const url = /^https:\/\/openalex\.org\/W\d+$/.test(paper.citationURL || '') ? paper.citationURL : '';
  const badge = available && url
    ? `<a class="citation-count" href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer" title="${escapeHTML(title)}">${label}</a>`
    : `<span class="citation-count unavailable" title="${escapeHTML(title)}">${label}</span>`;
  return `<div class="paper-citation">${badge}<small>${escapeHTML(source)} · ${escapeHTML(date)}</small></div>`;
}
