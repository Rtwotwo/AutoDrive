const paths = {
  papers: 'data/papers.json',
  datasets: 'data/datasets.json',
  benchmarks: 'data/benchmarks.json',
  leaderboard: 'data/leaderboard.json'
};

const state = { papers: [], datasets: [], benchmarks: [], leaderboard: [], track: 'all', query: '' };
const $ = (selector) => document.querySelector(selector);

async function loadData() {
  const [papers, datasets, benchmarks, leaderboard] = await Promise.all(
    Object.values(paths).map(async (path) => {
      const response = await fetch(path);
      if (!response.ok) throw new Error(`Unable to load ${path}`);
      return response.json();
    })
  );
  state.papers = papers;
  state.datasets = datasets;
  state.benchmarks = benchmarks;
  state.leaderboard = leaderboard;
}

function renderMetrics() {
  const latest = Math.max(...state.papers.map((paper) => paper.year));
  $('#heroMetrics').innerHTML = [
    [state.papers.length, 'CURATED PAPERS'],
    [state.benchmarks.length, 'PUBLIC BENCHMARKS'],
    [state.datasets.length, 'PUBLIC DATASETS'],
    [latest, 'LATEST YEAR']
  ].map(([value, label]) => `<div><strong>${value}</strong><span>${label}</span></div>`).join('');
}

function paperCard(paper) {
  const trackLabel = { e2e: 'END-TO-END', 'world-model': 'WORLD MODEL', vla: 'VLA' }[paper.track];
  const stars = Number.isInteger(paper.stars) ? new Intl.NumberFormat('en-US').format(paper.stars) : '—';
  const sourceStatus = paper.openSource ? `OPEN SOURCE · ★ ${stars}` : 'NO PUBLIC CODE';
  const links = [
    paper.paper ? `<a href="${paper.paper}" target="_blank" rel="noopener">Paper ↗</a>` : '',
    paper.code ? `<a href="${paper.code}" target="_blank" rel="noopener">Code ↗</a>` : '',
    paper.project ? `<a href="${paper.project}" target="_blank" rel="noopener">Project ↗</a>` : ''
  ].filter(Boolean).join('');
  return `<article class="paper-card" data-track="${paper.track}">
    <div class="paper-meta"><span class="track-pill ${paper.track}">${trackLabel}</span><span>${paper.published}${paper.venue !== String(paper.year) ? ` · ${paper.venue}` : ''}</span></div>
    <h3>${paper.name}</h3><p class="paper-title">${paper.title}</p>
    <div class="tag-list">${paper.tags.map((tag) => `<span>${tag}</span>`).join('')}</div>
    <div class="paper-footer"><span class="source-status ${paper.openSource ? 'available' : ''}">${sourceStatus}</span><div>${links}</div></div>
  </article>`;
}

function renderPapers() {
  const query = state.query.trim().toLowerCase();
  const filtered = state.papers.filter((paper) => {
    const trackMatch = state.track === 'all' || paper.track === state.track;
    const text = [paper.name, paper.title, paper.venue, ...(paper.tags || []), ...(paper.datasets || [])].join(' ').toLowerCase();
    return trackMatch && (!query || text.includes(query));
  });
  $('#paperGrid').innerHTML = filtered.map(paperCard).join('');
  $('#paperCount').textContent = `Showing ${filtered.length} of ${state.papers.length} papers`;
  $('#paperEmpty').hidden = filtered.length !== 0;
}

function datasetCard(item) {
  const links = [
    `<a href="${item.homepage}" target="_blank" rel="noopener">Homepage ↗</a>`,
    item.paper ? `<a href="${item.paper}" target="_blank" rel="noopener">Paper ↗</a>` : '',
    item.code ? `<a href="${item.code}" target="_blank" rel="noopener">Code ↗</a>` : ''
  ].filter(Boolean).join('');
  return `<article class="benchmark-card dataset-card">
    <div class="benchmark-top"><span class="benchmark-track">${item.task}</span><span class="access ${item.access === 'Open' ? 'open' : ''}">${item.access}</span></div>
    <h3>${item.name}</h3><p>${item.description}</p>
    <dl><div><dt>ROLE</dt><dd>Training / Research</dd></div><div><dt>SCALE</dt><dd>${item.scale}</dd></div><div><dt>REFERENCE</dt><dd>ReCogDrive</dd></div></dl>
    <div class="benchmark-links">${links}</div>
  </article>`;
}

function renderDatasets() {
  $('#datasetGrid').innerHTML = state.datasets.map(datasetCard).join('');
}

function benchmarkCard(item) {
  return `<article class="benchmark-card">
    <div class="benchmark-top"><span class="benchmark-track">${item.track}</span><span class="access ${item.access === 'Open' ? 'open' : ''}">${item.access}</span></div>
    <h3>${item.name}</h3><p>${item.description}</p>
    <dl><div><dt>SETTING</dt><dd>${item.setting}</dd></div><div><dt>PRIMARY METRIC</dt><dd>${item.primaryMetric}</dd></div><div><dt>SCALE</dt><dd>${item.scale}</dd></div></dl>
    <div class="benchmark-links"><a href="${item.homepage}" target="_blank" rel="noopener">Homepage ↗</a>${item.paper ? `<a href="${item.paper}" target="_blank" rel="noopener">Paper ↗</a>` : ''}${item.code ? `<a href="${item.code}" target="_blank" rel="noopener">Code ↗</a>` : ''}</div>
  </article>`;
}

function renderBenchmarks() {
  $('#benchmarkGrid').innerHTML = state.benchmarks.map(benchmarkCard).join('');
  const select = $('#leaderboardBenchmark');
  select.innerHTML = state.benchmarks.map((item) => `<option value="${item.id}">${item.name}</option>`).join('');
  const firstWithResults = state.leaderboard[0]?.benchmarkId || state.benchmarks[0]?.id;
  if (firstWithResults) select.value = firstWithResults;
}

function renderLeaderboard() {
  const benchmarkId = $('#leaderboardBenchmark').value;
  const benchmark = state.benchmarks.find((item) => item.id === benchmarkId);
  const entries = state.leaderboard
    .filter((entry) => entry.benchmarkId === benchmarkId)
    .sort((a, b) => (benchmark?.higherIsBetter === false ? a.score - b.score : b.score - a.score));
  $('#metricHeading').textContent = benchmark?.primaryMetric || 'METRIC';
  if (!entries.length) {
    $('#leaderboardBody').innerHTML = '<tr><td colspan="7" class="no-results">No reviewed results yet. Submit the first reproducible entry.</td></tr>';
    return;
  }
  $('#leaderboardBody').innerHTML = entries.map((entry, index) => `<tr>
    <td><span class="rank ${index < 3 ? `top-${index + 1}` : ''}">${String(index + 1).padStart(2, '0')}</span></td>
    <td><strong>${entry.method}</strong><small>${entry.date}</small></td>
    <td>${entry.team}</td><td>${entry.split}</td><td><strong>${entry.score}</strong></td>
    <td><span class="status ${entry.status}">${entry.status === 'published' ? 'Published' : entry.status === 'verified' ? 'Verified' : 'Pending'}</span></td>
    <td><a href="${entry.evidence}" target="_blank" rel="noopener">View ↗</a></td>
  </tr>`).join('');
}

function bindEvents() {
  $('#trackFilters').addEventListener('click', (event) => {
    const button = event.target.closest('[data-track]');
    if (!button) return;
    state.track = button.dataset.track;
    document.querySelectorAll('.filter').forEach((item) => item.classList.toggle('active', item === button));
    renderPapers();
  });
  $('#paperSearch').addEventListener('input', (event) => { state.query = event.target.value; renderPapers(); });
  $('#leaderboardBenchmark').addEventListener('change', renderLeaderboard);
  $('#themeToggle').addEventListener('click', () => {
    const dark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  });
}

async function init() {
  if (localStorage.getItem('theme') === 'dark') document.documentElement.classList.add('dark');
  try {
    await loadData();
    renderMetrics(); renderPapers(); renderDatasets(); renderBenchmarks(); renderLeaderboard(); bindEvents();
  } catch (error) {
    document.body.insertAdjacentHTML('afterbegin', `<div class="load-error">${error.message}. Start the local server with <code>npm run serve</code>.</div>`);
    console.error(error);
  }
}

init();
