const savedKey = 'autodrive-saved-papers-v1';
const labels = {
  e2e: 'End-to-End',
  'world-model': 'World Model',
  vla: 'Vision · Language · Action',
  rsi: 'Recursive Self-Improvement'
};
const framing = {
  e2e: 'This paper belongs to end-to-end driving. Focus on how sensor inputs and scene representations support executable driving decisions.',
  'world-model': 'This paper belongs to driving world models. Focus on how it represents scene states, forecasts futures, or supports downstream driving tasks.',
  vla: 'This paper belongs to vision-language-action research. Focus on how reasoning is grounded in visual scenes and translated into executable actions.',
  rsi: 'This paper belongs to recursive self-improvement research. Focus on the feedback loop, repeated optimization, and evidence of safe policy improvement.'
};
const prompts = {
  e2e: [
    'Are the main results open-loop, closed-loop, or both? Do the metrics capture safety in interactive traffic?',
    'Do baselines use the same sensors, data splits, training budget, and planning horizon?',
    'Do ablations isolate the benefits of the central representation or training strategy?'
  ],
  'world-model': [
    'How are temporal consistency, controllability, and long-horizon rollout stability measured?',
    'Do gains in visual or predictive quality improve downstream driving policies?',
    'Are generated futures checked for physical plausibility and safety-critical events?'
  ],
  vla: [
    'How are natural-language instructions grounded in the scene and mapped to the action space?',
    'Does evaluation cover long-tail scenes, ambiguous instructions, and closed-loop interactions?',
    'When decisions fail, can perception, reasoning, and action-decoding errors be distinguished?'
  ],
  rsi: [
    'What safety constraints, independent regression tests, and stopping rules govern each improvement round?',
    'Are gains consistent across scenarios or concentrated in a few evaluation subsets?',
    'How do repeated updates preserve driving behaviors that were already reliable?'
  ]
};
const byId = new Map();
let papers = [];
let currentId = null;
let sortedVisible = [];
let savedOnly = false;
const $ = (selector, root = document) => root.querySelector(selector);
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[character]));

function safeURL(value) {
  try {
    const url = new URL(value, window.location.href);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
  } catch {
    return '';
  }
}

function externalLink(url, label, className = '') {
  const href = safeURL(url);
  return href ? '<a class="' + escapeHTML(className) + '" href="' + escapeHTML(href) + '" target="_blank" rel="noopener noreferrer">' + label + '</a>' : '';
}

function readSaved() {
  try {
    const list = JSON.parse(localStorage.getItem(savedKey) || '[]');
    return new Set(Array.isArray(list) ? list : []);
  } catch {
    return new Set();
  }
}

function writeSaved(saved) {
  try { localStorage.setItem(savedKey, JSON.stringify(Array.from(saved))); } catch { /* Storage is optional. */ }
}

function enhanceCards() {
  const grid = $('#paperGrid');
  if (!grid) return;
  grid.querySelectorAll('.paper-card').forEach((card) => {
    const paper = byId.get(card.dataset.paperId);
    if (!paper) return;
    card.dataset.paperId = paper.id;
    if ($('.paper-card-actions', card)) return;
    const saved = readSaved().has(paper.id);
    const actions = document.createElement('div');
    actions.className = 'paper-card-actions';
    actions.innerHTML = '<a class="paper-read-link" href="#paper/' + encodeURIComponent(paper.id) + '" data-open-paper="' + escapeHTML(paper.id) + '" aria-haspopup="dialog">Open detailed analysis <span aria-hidden="true">→</span></a>' +
      '<button class="bookmark-button" type="button" data-save-paper="' + escapeHTML(paper.id) + '" aria-label="' + (saved ? 'Remove saved paper' : 'Save paper') + '" aria-pressed="' + String(saved) + '" title="' + (saved ? 'Remove from saved papers' : 'Save for later') + '">' + (saved ? '★' : '☆') + '</button>';
    card.appendChild(actions);
  });
  applyListControls();
}

function applyListControls() {
  const grid = $('#paperGrid');
  if (!grid) return;
  const cards = Array.from(grid.querySelectorAll('.paper-card'));
  const order = $('#paperSort')?.value || 'newest';
  cards.sort((left, right) => {
    const a = byId.get(left.dataset.paperId) || {};
    const b = byId.get(right.dataset.paperId) || {};
    if (order === 'title') return String(a.name || '').localeCompare(String(b.name || ''), 'en', { sensitivity: 'base' });
    const result = (Number(a.year) || 0) - (Number(b.year) || 0) || String(a.published || '').localeCompare(String(b.published || ''));
    return order === 'oldest' ? result : -result;
  });
  const saved = readSaved();
  cards.forEach((card) => {
    card.hidden = savedOnly && !saved.has(card.dataset.paperId);
    const button = $('.bookmark-button', card);
    const isSaved = saved.has(card.dataset.paperId);
    if (button) {
      button.setAttribute('aria-pressed', String(isSaved));
      button.setAttribute('aria-label', isSaved ? 'Remove saved paper' : 'Save paper');
      button.title = isSaved ? 'Remove from saved papers' : 'Save for later';
      button.textContent = isSaved ? '★' : '☆';
    }
    grid.appendChild(card);
  });
  sortedVisible = cards.filter((card) => !card.hidden).map((card) => byId.get(card.dataset.paperId)).filter(Boolean);
  const savedCount = $('#savedCount');
  if (savedCount) savedCount.textContent = String(saved.size);
  const savedButton = $('#savedOnly');
  if (savedButton) {
    savedButton.setAttribute('aria-pressed', String(savedOnly));
    savedButton.classList.toggle('active', savedOnly);
  }
  const count = $('#paperCount');
  if (count) count.textContent = savedOnly ? sortedVisible.length + ' saved papers' : 'Showing ' + sortedVisible.length + ' of ' + papers.length + ' papers';
  const empty = $('#paperEmpty');
  if (empty) empty.hidden = sortedVisible.length !== 0;
}
function relatedPapers(paper) {
  const tags = new Set(paper.tags || []);
  const datasets = new Set(paper.datasets || []);
  return papers.filter((item) => item.id !== paper.id).map((item) => {
    const sharedTags = (item.tags || []).filter((tag) => tags.has(tag)).length;
    const sharedDatasets = (item.datasets || []).filter((dataset) => datasets.has(dataset)).length;
    return { paper: item, score: sharedTags * 3 + sharedDatasets * 2 + (item.track === paper.track ? 1 : 0) };
  }).filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || (Number(b.paper.year) || 0) - (Number(a.paper.year) || 0))
    .slice(0, 4);
}

function analysisMarkup(paper) {
  const track = labels[paper.track] || 'Research';
  const sentences = String(paper.summary || 'The curated index does not yet contain a summary for this paper.')
    .match(/[^.!?。！？]+[.!?。！？]?/g)?.map((part) => part.trim()).filter(Boolean) || [];
  const steps = sentences.map((part, index) => '<li class="analysis-step"><span>' + String(index + 1).padStart(2, '0') + '</span><p>' + escapeHTML(part) + '</p></li>').join('');
  const tags = (paper.tags || []).map((tag) => '<span class="detail-chip">' + escapeHTML(tag) + '</span>').join('');
  const datasets = (paper.datasets || []).map((item) => '<span class="detail-chip">' + escapeHTML(item) + '</span>').join('');
  const questions = (prompts[paper.track] || prompts.e2e).concat([
    'Do ablations isolate the claimed contribution, and are comparison settings consistent?',
    'Which assumptions, failure cases, and compute costs are discussed, and how do they limit transfer?'
  ]);
  const related = relatedPapers(paper).map((item) =>
    '<li><button type="button" class="related-paper" data-open-paper="' + escapeHTML(item.paper.id) + '">' +
    '<span class="related-track">' + escapeHTML(labels[item.paper.track] || 'Research') + ' · ' + escapeHTML(item.paper.year) + '</span>' +
    '<strong>' + escapeHTML(item.paper.name) + '</strong>' +
    '<small>' + escapeHTML((item.paper.summary || '').slice(0, 145)) + ((item.paper.summary || '').length > 145 ? '…' : '') + '</small></button></li>'
  ).join('');
  const code = paper.code
    ? externalLink(paper.code, paper.codeStatus === 'pending' ? 'Open official repository (code pending) ↗' : paper.codeScope === 'partial' ? 'Open released component ↗' : 'Open implementation ↗', 'detail-resource-link')
    : (paper.openSource
      ? '<span class="resource-state">The catalog marks public code as available but does not record a direct repository link.</span>'
      : '<span class="resource-state">No released implementation link is recorded in the current catalog.</span>');
  const source = externalLink(paper.paper, 'Read the original paper ↗', 'button primary detail-source');
  const project = externalLink(paper.project, 'Project page ↗', 'button secondary');
  const saved = readSaved().has(paper.id);
  return '<div class="paper-detail-head">' +
    '<div class="detail-kicker"><span>' + escapeHTML(track.toUpperCase()) + '</span><span>' + escapeHTML(paper.year) + (paper.venue && paper.venue !== String(paper.year) ? ' · ' + escapeHTML(paper.venue) : '') + '</span><span>ID ' + escapeHTML(paper.id) + '</span></div>' +
    '<h1 class="paper-detail-title" id="paperDialogTitle" tabindex="-1">' + escapeHTML(paper.name) + '</h1>' +
    '<p class="paper-detail-full-title">' + escapeHTML(paper.title) + '</p>' +
    '<div class="detail-action-row">' + source + project +
      '<button class="button secondary" type="button" data-copy-paper-link="' + escapeHTML(paper.id) + '">Copy page link</button>' +
      '<button class="button secondary detail-save" type="button" data-save-paper="' + escapeHTML(paper.id) + '" aria-pressed="' + String(saved) + '">' + (saved ? '★ Saved' : '☆ Save paper') + '</button></div>' +
    '<div class="detail-navigation"><button type="button" data-adjacent-paper="-1">← Previous paper</button><span>Shareable detail page</span><button type="button" data-adjacent-paper="1">Next paper →</button></div></div>' +
    '<div class="paper-detail-grid"><div class="analysis-main">' +
      '<section class="analysis-card analysis-lead"><div class="analysis-section-label"><span>01</span> RESEARCH FRAMING</div><h2>What problem does this paper address?</h2>' +
        '<p class="analysis-framing">' + escapeHTML(framing[paper.track] || framing.e2e) + '</p><p class="analysis-source-summary">' + escapeHTML(paper.summary || 'A summary is not yet available in this catalog.') + '</p>' +
        '<p class="analysis-footnote">This framing uses the catalog title, tags, and summary. Consult the original paper for the precise problem definition.</p></section>' +
      '<section class="analysis-card"><div class="analysis-section-label"><span>02</span> ARGUMENT FLOW</div><h2>Follow the technical approach</h2>' +
        '<p class="section-help">These points follow the sentences in the curated summary to help trace the method.</p><ol class="analysis-steps">' + steps + '</ol></section>' +
      '<section class="analysis-card"><div class="analysis-section-label"><span>03</span> READER CHECKLIST</div><h2>Questions for a closer reading</h2>' +
        '<p class="section-help">Use these questions to assess the evidence while reading the full paper.</p><ul class="reader-prompts">' +
        questions.map((question) => '<li><span aria-hidden="true">↗</span><p>' + escapeHTML(question) + '</p></li>').join('') + '</ul></section>' +
      '</div><aside class="analysis-aside">' +
        '<section class="analysis-card fact-card"><div class="analysis-section-label"><span>04</span> PAPER FACTS</div>' +
          '<dl class="paper-facts"><div><dt>Research track</dt><dd>' + escapeHTML(track) + '</dd></div><div><dt>Year / Venue</dt><dd>' + escapeHTML(paper.venue || paper.year) + '</dd></div><div><dt>Catalog ID</dt><dd>' + escapeHTML(paper.id) + '</dd></div></dl>' +
          '<h3>Topics</h3><div class="detail-chip-list">' + (tags || '<span class="muted-copy">No topic tags recorded</span>') + '</div>' +
          '<h3>Datasets and evaluation</h3><div class="detail-chip-list">' + (datasets || '<span class="muted-copy">No datasets recorded in this catalog</span>') + '</div></section>' +
        '<section class="analysis-card evidence-card"><div class="analysis-section-label"><span>05</span> EVIDENCE AND REPRODUCTION</div><h2>What the catalog records</h2>' +
          '<p>' + escapeHTML(paper.summary || 'A summary is not yet available in this catalog.') + '</p><div class="resource-status"><strong>Public implementation</strong>' + code + (paper.codeNote ? '<span class="resource-state">' + escapeHTML(paper.codeNote) + '</span>' : '') + '</div>' +
          '<p class="analysis-footnote">Open the original paper to verify specific metrics, limitations, ablations, and page references.</p></section>' +
        '<section class="analysis-card related-card"><div class="analysis-section-label"><span>06</span> RELATED PAPERS</div><h2>Explore related topics and datasets</h2>' +
          (related ? '<ul class="related-paper-list">' + related + '</ul>' : '<p class="muted-copy">No papers with shared tags or datasets were found.</p>') +
        '</section></aside></div>';
}

function renderDetail(paper) {
  $('#paperDetailContent').innerHTML = analysisMarkup(paper);
  $('#paperDetailContent').scrollTop = 0;
  document.title = paper.name + ' | AutoDrive Research Hub';
}

function openPaper(id, historyMode = 'push') {
  const paper = byId.get(id);
  if (!paper) return;
  const dialog = $('#paperDialog');
  const alreadyOpen = dialog.open;
  currentId = id;
  renderDetail(paper);
  const hash = '#paper/' + encodeURIComponent(id);
  if (historyMode === 'push' && !alreadyOpen && location.hash !== hash) history.pushState({ paperId: id }, '', hash);
  else if (historyMode === 'replace' && location.hash !== hash) history.replaceState({ paperId: id }, '', hash);
  if (!alreadyOpen) dialog.showModal();
  document.body.classList.add('paper-dialog-open');
  setTimeout(() => $('.paper-detail-title', dialog)?.focus(), 0);
}

function closePaper() {
  if ($('#paperDialog').open) $('#paperDialog').close();
}

function syncRoute() {
  const match = location.hash.match(/^#paper\/(.+)$/);
  if (match) {
    let id = '';
    try { id = decodeURIComponent(match[1]); } catch { id = match[1]; }
    openPaper(id, 'none');
  } else if ($('#paperDialog').open) {
    $('#paperDialog').close();
  }
}
function toggleSaved(id) {
  const saved = readSaved();
  if (saved.has(id)) saved.delete(id);
  else saved.add(id);
  writeSaved(saved);
  enhanceCards();
  const paper = byId.get(currentId);
  if (paper) renderDetail(paper);
}

function moveToAdjacent(delta) {
  const list = sortedVisible.length ? sortedVisible : papers;
  const index = list.findIndex((paper) => paper.id === currentId);
  if (index < 0) return;
  const paper = list[index + Number(delta)];
  if (paper) openPaper(paper.id, 'replace');
}

function resetFilters() {
  savedOnly = false;
  $('#paperSearch').value = '';
  $('#paperSearch').dispatchEvent(new Event('input', { bubbles: true }));
  $('#paperSort').value = 'newest';
  $('[data-track="all"]', $('#trackFilters'))?.click();
  applyListControls();
}

function bindEvents() {
  document.addEventListener('click', async (event) => {
    const open = event.target.closest('[data-open-paper]');
    if (open) {
      event.preventDefault();
      openPaper(open.dataset.openPaper, $('#paperDialog').open ? 'replace' : 'push');
      return;
    }
    const save = event.target.closest('[data-save-paper]');
    if (save) {
      event.preventDefault();
      toggleSaved(save.dataset.savePaper);
      return;
    }
    const adjacent = event.target.closest('[data-adjacent-paper]');
    if (adjacent) {
      moveToAdjacent(adjacent.dataset.adjacentPaper);
      return;
    }
    if (event.target.closest('[data-close-paper]')) {
      closePaper();
      return;
    }
    const copy = event.target.closest('[data-copy-paper-link]');
    if (copy) {
      const id = copy.dataset.copyPaperLink;
      const url = location.origin + location.pathname + location.search + '#paper/' + encodeURIComponent(id);
      try {
        await navigator.clipboard.writeText(url);
        copy.textContent = 'Link copied';
        setTimeout(() => { if (copy.isConnected) copy.textContent = 'Copy page link'; }, 1500);
      } catch {
        copy.textContent = 'Use the address bar link';
      }
    }
  });

  $('#paperSort').addEventListener('change', applyListControls);
  $('#savedOnly').addEventListener('click', () => {
    savedOnly = !savedOnly;
    applyListControls();
  });
  $('#clearSearch').addEventListener('click', () => {
    $('#paperSearch').value = '';
    $('#paperSearch').dispatchEvent(new Event('input', { bubbles: true }));
    $('#paperSearch').focus();
  });
  $('#resetPaperFilters').addEventListener('click', resetFilters);

  const dialog = $('#paperDialog');
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) closePaper();
  });
  dialog.addEventListener('close', () => {
    document.body.classList.remove('paper-dialog-open');
    document.title = 'AutoDrive Research Hub';
    currentId = null;
    if (location.hash.startsWith('#paper/')) {
      history.replaceState(history.state, '', location.pathname + location.search + '#papers');
    }
  });
  window.addEventListener('hashchange', syncRoute);
  window.addEventListener('popstate', syncRoute);

  $('#menuToggle').addEventListener('click', () => {
    const button = $('#menuToggle');
    const nav = $('#primaryNav');
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    button.setAttribute('aria-label', expanded ? 'Open navigation' : 'Close navigation');
    nav.classList.toggle('open', !expanded);
  });
  $('#primaryNav').addEventListener('click', (event) => {
    if (!event.target.closest('a')) return;
    $('#primaryNav').classList.remove('open');
    $('#menuToggle').setAttribute('aria-expanded', 'false');
    $('#menuToggle').setAttribute('aria-label', 'Open navigation');
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === '/' && !$('#paperDialog').open && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
      event.preventDefault();
      $('#paperSearch').focus();
      $('#papers').scrollIntoView({ behavior: 'smooth' });
    }
  });
}

async function initPaperAnalysis() {
  window.addEventListener('papers-rendered', enhanceCards);
  try {
    const response = await fetch('data/papers.json');
    if (!response.ok) throw new Error('Unable to load paper records.');
    papers = await response.json();
    papers.forEach((paper) => {
      byId.set(paper.id, paper);
    });
    bindEvents();
    enhanceCards();
    syncRoute();
  } catch (error) {
    console.error('Paper analysis page could not load:', error);
  }
}

initPaperAnalysis();
