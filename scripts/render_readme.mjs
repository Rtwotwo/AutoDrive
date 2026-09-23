import { readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('.', import.meta.url)), '..');
const readJson = async (name) => JSON.parse(await readFile(join(root, 'data', name), 'utf8'));
const [papers, datasets, benchmarks] = await Promise.all([
  readJson('papers.json'), readJson('datasets.json'), readJson('benchmarks.json')
]);

const tracks = [
  ['e2e', 'End-to-End Autonomous Driving'],
  ['vla', 'Vision-Language-Action Models'],
  ['world-model', 'Driving World Models']
];
const datasetGroups = [
  'Perception and Scene Understanding',
  'Motion and Cooperative Driving',
  'Simulation and Closed-Loop Evaluation',
  'Language and VLA'
];
const iconText = {
  method: '\u{1F9E0}', year: '\u{1F5D3}\uFE0F', tags: '\u{1F3F7}\uFE0F',
  paper: '\u{1F4C4}', github: '\u{1F4BB}', project: '\u{1F310}',
  dataset: '\u{1F30D}'
};
const dash = '\u2014';
const esc = (value) => String(value ?? '').replaceAll('|', '\\|');
const html = (value) => esc(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const icon = (emoji, url, title) => url ? `[${emoji}](${url} "${title}")` : dash;
const badgeLink = (alt, badgeUrl, targetUrl) => targetUrl ? `[![${alt}](${badgeUrl})](${targetUrl})` : dash;
const paperBadge = (url) => {
  if (!url) return dash;
  const arxivId = url.match(/arxiv\.org\/abs\/([^/?#]+)/i)?.[1]?.replace(/v\d+$/, '');
  const label = arxivId ? `arXiv-${arxivId}` : 'Paper-Open';
  const color = arxivId ? 'b31b1b' : '2457a7';
  return badgeLink(arxivId ? 'arXiv' : 'Paper', `https://img.shields.io/badge/${label}-${color}?style=flat-square`, url);
};
const githubBadge = (url) => {
  if (!url) return dash;
  try {
    const parsed = new URL(url);
    if (parsed.hostname.toLowerCase() === 'github.com') {
      const [owner, repo] = parsed.pathname.split('/').filter(Boolean);
      if (owner && repo) {
        const cleanRepo = repo.replace(/\.git$/, '');
        return badgeLink('GitHub stars', `https://img.shields.io/github/stars/${owner}/${cleanRepo}?style=social`, url);
      }
    }
  } catch {}
  return badgeLink('Code', 'https://img.shields.io/badge/Code-Open-source-181717?logo=github&style=flat-square', url);
};
const resources = (item) => [
  icon(iconText.dataset, item.homepage, 'Dataset homepage'),
  icon(iconText.paper, item.paper, 'Paper'),
  icon(iconText.github, item.code, 'Dataset, download, or code')
].filter((value) => value !== dash).join(' ');

let readme = '# Awesome Autonomous Driving Research\n\n';
readme += `A curated research collection for end-to-end autonomous driving, driving world models, vision-language-action models, public datasets, and reproducible evaluation. The catalog currently contains **${papers.length} papers** across three research tracks.\n\n`;
const reviewDate = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString().slice(0, 10);
readme += `Last updated: ${reviewDate}. Verify paper metadata against the latest arXiv or publisher version before citation.\n\n`;
readme += '## Table of Contents\n\n- [Papers](#papers)\n';
for (const [, title] of tracks) readme += `  - [${title}](#${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')})\n`;
readme += '- [Public Datasets](#public-datasets)\n- [Public Evaluation Benchmarks](#public-evaluation-benchmarks)\n- [Leaderboard](#leaderboard)\n- [License](#license)\n\n';
readme += '## Papers\n\n';
readme += 'GitHub links point to public code repositories checked against the paper or its official project page. A dash means no public author/team code repository was identified in this review. GitHub badges display live star counts.\n\n';

for (const [track, title] of tracks) {
  const trackPapers = papers.filter((item) => item.track === track);
  const codeCount = trackPapers.filter((paper) => paper.openSource && paper.code).length;
  readme += `### ${title}\n\n`;
  readme += `_${trackPapers.length} papers; ${codeCount} with a verified public code link._\n\n`;
  const years = [...new Set(trackPapers.map((paper) => paper.year))].sort((a, b) => b - a);
  for (const year of years) {
    readme += `<details open>\n<summary>${year}</summary>\n\n`;
    readme += `| ${iconText.method} **Method** | ${iconText.year} **Year / Venue** | ${iconText.tags} **Tags** | ${iconText.paper} **Paper** | ${iconText.github} **GitHub** | ${iconText.project} **Project** |\n`;
    readme += '|---|---|---|---|---|---|\n';
    for (const paper of trackPapers.filter((item) => item.year === year)) {
      const yearVenue = paper.venue === String(paper.year) ? String(paper.year) : esc(paper.venue);
      const methodTitle = `**${esc(paper.name)}**<br><sub>${html(paper.title)}</sub>`;
      const tags = paper.tags.map((tag) => `\`${esc(tag)}\``).join(' · ');
      const project = paper.project ? icon(iconText.project, paper.project, 'Official project page') : dash;
      readme += `| ${methodTitle} | ${yearVenue} | ${tags} | ${paperBadge(paper.paper)} | ${githubBadge(paper.code)} | ${project} |\n`;
    }
    readme += '\n</details>\n\n';
  }
}

readme += '## Public Datasets\n\n';
readme += 'The catalog combines datasets and data resources from [GE2EAD](https://github.com/AutoLab-SAI-SJTU/GE2EAD), [GenAI4AD](https://github.com/taco-group/GenAI4AD), and [ReCogDrive](https://github.com/xiaomi-research/recogdrive). Dataset availability and access requirements follow the original providers.\n\n';
for (const group of datasetGroups) {
  const items = datasets.filter((item) => item.group === group);
  if (!items.length) continue;
  readme += `### ${group}\n\n`;
  readme += '| Dataset / Method and Paper Title | Task | Scale | Access | Resources |\n';
  readme += '|---|---|---|---|:---:|\n';
  for (const item of items) {
    const nameTitle = `**${esc(item.name)}**<br><sub>${html(item.paperTitle)}</sub>`;
    readme += `| ${nameTitle} | ${esc(item.task)} | ${esc(item.scale)} | ${esc(item.access)} | ${resources(item)} |\n`;
  }
  readme += '\n';
}

readme += '## Public Evaluation Benchmarks\n\n';
readme += '| Benchmark | Track | Evaluation Setting | Primary Metric | Resources |\n|---|---|---|---|:---:|\n';
for (const item of benchmarks) {
  const links = [
    icon(iconText.dataset, item.homepage, 'Benchmark homepage'),
    icon(iconText.paper, item.paper, 'Paper'),
    icon(iconText.github, item.code, 'Code')
  ].filter((value) => value !== dash).join(' ');
  readme += `| **${esc(item.name)}** | ${esc(item.track)} | ${esc(item.setting)} | ${esc(item.primaryMetric)} | ${links} |\n`;
}

readme += '\n## Leaderboard\n\n';
readme += 'Benchmark results are stored in [data/leaderboard.json](data/leaderboard.json). Each entry preserves its evaluation protocol, data split, and reproducibility evidence. Results from incompatible protocols are not ranked together.\n\n';
readme += '## License\n\nThis project is released under the [Apache License 2.0](LICENSE).\n';

await writeFile(join(root, 'README.md'), readme, 'utf8');
console.log(`Rendered README for ${papers.length} papers, ${datasets.length} datasets, and ${benchmarks.length} benchmarks.`);
