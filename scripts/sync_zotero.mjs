import { readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const bibPath = process.argv[2];
if (!bibPath) {
  console.error('Usage: node scripts/sync_zotero.mjs <path-to-zotero-export.bib>');
  process.exit(1);
}

const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const source = await readFile(resolve(bibPath), 'utf8');

function parseBibtex(text) {
  const entries = [];
  let cursor = 0;
  while (cursor < text.length) {
    const at = text.indexOf('@', cursor);
    if (at < 0) break;
    const open = text.indexOf('{', at);
    const comma = text.indexOf(',', open);
    if (open < 0 || comma < 0) break;
    const type = text.slice(at + 1, open).trim().toLowerCase();
    const key = text.slice(open + 1, comma).trim();
    let i = comma + 1;
    const fields = {};
    while (i < text.length) {
      while (i < text.length && /[\s,]/.test(text[i])) i += 1;
      if (text[i] === '}') { i += 1; break; }
      const nameStart = i;
      while (i < text.length && /[A-Za-z0-9_-]/.test(text[i])) i += 1;
      const name = text.slice(nameStart, i).trim().toLowerCase();
      while (i < text.length && /\s/.test(text[i])) i += 1;
      if (!name || text[i] !== '=') { i += 1; continue; }
      i += 1;
      while (i < text.length && /\s/.test(text[i])) i += 1;
      let value = '';
      if (text[i] === '{') {
        let depth = 1;
        const start = ++i;
        while (i < text.length && depth > 0) {
          if (text[i] === '{' && text[i - 1] !== '\\') depth += 1;
          else if (text[i] === '}' && text[i - 1] !== '\\') depth -= 1;
          i += 1;
        }
        value = text.slice(start, i - 1);
      } else if (text[i] === '"') {
        const start = ++i;
        while (i < text.length && !(text[i] === '"' && text[i - 1] !== '\\')) i += 1;
        value = text.slice(start, i);
        i += 1;
      } else {
        const start = i;
        while (i < text.length && text[i] !== ',' && text[i] !== '}') i += 1;
        value = text.slice(start, i).trim();
      }
      fields[name] = value.trim();
    }
    entries.push({ type, key, ...fields });
    cursor = i;
  }
  return entries;
}

function clean(value = '') {
  return value
    .replace(/\\textasciitilde\s*/g, '~')
    .replace(/\\textendash\s*/g, '–')
    .replace(/\\textemdash\s*/g, '—')
    .replace(/\\&/g, '&')
    .replace(/\\%/g, '%')
    .replace(/\\_/g, '_')
    .replace(/\\(?:textbf|textit|emph|mathrm|mathbf|mathit)\s*\{([^{}]*)\}/g, '$1')
    .replace(/\{([^{}]*)\}/g, '$1')
    .replace(/[{}]/g, '')
    .replace(/\$([^$]+)\$/g, '$1')
    .replace(/\\/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function https(url = '') {
  return clean(url).replace(/^http:\/\//i, 'https://');
}

function arxivId(entry) {
  const haystack = `${entry.doi || ''} ${entry.url || ''} ${entry.note || ''}`;
  return haystack.match(/(?:arXiv[.:/]|abs\/)(\d{4}\.\d{4,5})/i)?.[1] || '';
}

function extractLinks(entry) {
  // Zotero's annotation field usually preserves author-provided project URLs
  // more faithfully than abstracts copied from publisher pages.
  const text = [entry.annote, entry.abstract, entry.url].filter(Boolean).join(' ');
  const links = [...text.matchAll(/https?:\/\/[^\s}<)]+/g)]
    .map((match) => match[0].replace(/[.,;]+$/, ''));
  const code = links.find((link) => /github\.com\//i.test(link));
  const project = links.find((link) => !/github\.com|arxiv\.org/i.test(link));
  return {
    code: code ? https(code) : undefined,
    project: project ? https(project) : undefined
  };
}

function methodName(entry, title) {
  const short = clean(entry.shorttitle || '');
  if (short && short.length <= 48 && !/^(towards|end-to-end|a |the )/i.test(short)) return short;
  const colon = title.split(':')[0].trim();
  if (colon.length <= 48 && colon.split(' ').length <= 6) return colon;
  const keyPart = entry.key.split('_').slice(1, -1).join('-');
  return keyPart
    ? keyPart.replace(/\b\w/g, (character) => character.toUpperCase())
    : title.split(' ').slice(0, 5).join(' ');
}

function classify(title, abstract, year) {
  const text = `${title} ${abstract}`.toLowerCase();
  const titleText = title.toLowerCase();
  const vla = /vision[-– ]language[-– ]action|\bvla\b|vision[-– ]language model|large vision[-– ]language|large language model|language[-– ]action|language-guided|multimodal model/.test(text);
  const world = /world[-– ]action|world model|world-model|world modeling|world-modeling|world simulation|world simulator|world generation|world reconstruction|world foundation|world dynamics|world cognition|world value|video generation|scene generation|neural rendering|future scene|occupancy world/.test(text);
  const benchmark = /benchmark|dataset|leaderboard|score basis audit|survey|taxonomy|position paper/.test(titleText);

  if (benchmark) {
    if (vla) return ['vla', 'VLA Datasets, Benchmarks & Surveys'];
    if (world) return ['world-model', 'World Model Benchmarks & Surveys'];
    return ['e2e', 'Driving Datasets, Benchmarks & Evaluation'];
  }

  if (vla && !/world[-– ]action|world model|world-model/.test(titleText)) {
    if (/efficient|lightweight|compression|pruning|deployment|real-time|latent action/.test(text)) return ['vla', 'Efficient VLA & Deployment'];
    if (/occupancy|spatial|geometry|geometric|3d|cross-view|spatio-temporal|grounding/.test(text)) return ['vla', 'Spatial, Temporal & 3D Grounding'];
    if (/reinforcement|post-training|reasoning|chain|thinking|exploration|failure|critic|self-edit|reflection/.test(text)) return ['vla', 'VLA Reasoning & Reinforcement Learning'];
    if (/dual|bridg|planner|planning decision|high-level/.test(text)) return ['vla', 'Dual-System VLM + Planner'];
    if (!/\bvla\b|vision[-– ]language[-– ]action/.test(titleText)) return ['vla', 'Driving VLMs & Scene Reasoning'];
    return ['vla', 'End-to-End VLA'];
  }

  if (world) {
    if (/world[-– ]action|\bwam\b|generation and planning|understanding, planning and generation|action model/.test(text)) return ['world-model', 'World-Action Models'];
    if (/foundation model|cosmos|platform|omnimodal/.test(text)) return ['world-model', 'World Foundation Models'];
    if (/occupancy|3d|bev|geometry|geometric|reconstruction/.test(text)) return ['world-model', 'BEV, Occupancy & 3D World Modeling'];
    if (/latent|jepa|feature prediction|predictive dynamics/.test(text)) return ['world-model', 'Latent World Models'];
    if (/simulation|simulator|data scaling|data generation|synthetic|pseudo/.test(text)) return ['world-model', 'Simulation, Data Generation & Scaling'];
    return ['world-model', 'Video Generation & Neural Rendering'];
  }

  if (/cooperative|v2x|federated|multi-agent/.test(text)) return ['e2e', 'Cooperative & Multi-Agent Driving'];
  if (/diffusion|flow matching|generative|autoregressive/.test(text)) return ['e2e', 'Diffusion, Flow & Generative Planning'];
  if (/scoring|ranking|selection|candidate|trajectory evaluation|value estimation/.test(text)) return ['e2e', 'Trajectory Scoring & Selection'];
  if (/reinforcement|post-training|\bdpo\b|\brft\b|\bgrpo\b|rlvr|self-play|human feedback|policy optimization/.test(text)) return ['e2e', 'Reinforcement Learning & Post-Training'];
  if (/sparse|vector|token|register|query|mamba|linear rnn/.test(text)) return ['e2e', 'Sparse, Vector & Token Representations'];
  if (/robust|safety|safe |uncertainty|test-time|retrieval|corridor|adversarial/.test(text)) return ['e2e', 'Robustness, Safety & Test-Time Adaptation'];
  if (/distill|privileged|teacher|expert|imitation|cheating/.test(text) || year <= 2022) return ['e2e', 'Imitation, Distillation & Privileged Learning'];
  return ['e2e', 'Unified Perception-Prediction-Planning'];
}

function tagsFor(title, abstract, category) {
  const text = `${title} ${abstract}`.toLowerCase();
  const candidates = [
    ['Diffusion', 'diffusion'],
    ['Flow Matching', 'flow matching'],
    ['Reinforcement Learning', 'reinforcement'],
    ['World Model', 'world model'],
    ['World-Action', 'world-action'],
    ['VLA', 'vision-language-action'],
    ['VLM', 'vision-language model'],
    ['Closed-Loop', 'closed-loop'],
    ['Trajectory Scoring', 'scoring'],
    ['3D Occupancy', 'occupancy'],
    ['BEV', "bird’s eye|bird's eye|\\bbev\\b"],
    ['Simulation', 'simulation'],
    ['Distillation', 'distill'],
    ['Sparse Representation', 'sparse'],
    ['Reasoning', 'reasoning'],
    ['Video Generation', 'video generation'],
    ['Multi-Modal', 'multi-modal|multimodal'],
    ['Safety', 'safety|safe driving']
  ];
  const tags = candidates
    .filter(([, pattern]) => new RegExp(pattern).test(text))
    .map(([tag]) => tag)
    .slice(0, 3);
  return tags.length ? tags : [category.split(/[,&]/)[0].trim()];
}

const rawEntries = parseBibtex(source);
const seen = new Set();
const papers = [];

for (const entry of rawEntries) {
  const title = clean(entry.title);
  const year = Number.parseInt(clean(entry.year), 10);
  if (!title || !Number.isInteger(year)) continue;
  const arxiv = arxivId(entry);
  const dedupeKey = arxiv || title.toLowerCase().replace(/[^a-z0-9]+/g, '');
  if (seen.has(dedupeKey)) continue;
  seen.add(dedupeKey);

  const abstract = clean(entry.abstract || '');
  const [track, category] = classify(title, abstract, year);
  const extra = extractLinks(entry);
  const knownPaperUrls = {
    'FlowAD: Ego-Scene Interactive Modeling for Autonomous Driving': 'https://arxiv.org/abs/2603.13399'
  };
  const fallbackUrl = entry.url ? https(entry.url) : entry.doi ? `https://doi.org/${clean(entry.doi)}` : '';
  const paperUrl = arxiv ? `https://arxiv.org/abs/${arxiv}` : knownPaperUrls[title] || fallbackUrl;
  const venueMatch = clean(entry.annote || '').match(/\b(CVPR|ICCV|ECCV|NeurIPS|ICLR|ICML|CoRL|AAAI|IROS|ICRA)\s*(\d{4})\b/i);
  const venueNote = venueMatch ? `${venueMatch[1].toUpperCase()} ${venueMatch[2]}` : '';
  const id = (arxiv || entry.key)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

  papers.push({
    id,
    name: methodName(entry, title),
    title,
    track,
    category,
    year,
    venue: venueNote ? clean(venueNote) : String(year),
    tags: tagsFor(title, abstract, category),
    datasets: [],
    paper: paperUrl || undefined,
    code: extra.code,
    project: extra.project && extra.project !== paperUrl ? extra.project : undefined,
    zoteroKey: entry.key
  });
}

const trackOrder = { e2e: 0, vla: 1, 'world-model': 2 };
papers.sort((a, b) =>
  trackOrder[a.track] - trackOrder[b.track]
  || a.category.localeCompare(b.category)
  || b.year - a.year
  || a.name.localeCompare(b.name)
);

const categoryOrder = {
  e2e: [
    'Imitation, Distillation & Privileged Learning',
    'Unified Perception-Prediction-Planning',
    'Sparse, Vector & Token Representations',
    'Trajectory Scoring & Selection',
    'Diffusion, Flow & Generative Planning',
    'Reinforcement Learning & Post-Training',
    'Robustness, Safety & Test-Time Adaptation',
    'Cooperative & Multi-Agent Driving',
    'Driving Datasets, Benchmarks & Evaluation'
  ],
  'world-model': [
    'Video Generation & Neural Rendering',
    'BEV, Occupancy & 3D World Modeling',
    'Latent World Models',
    'World-Action Models',
    'Simulation, Data Generation & Scaling',
    'World Foundation Models',
    'World Model Benchmarks & Surveys'
  ],
  vla: [
    'Driving VLMs & Scene Reasoning',
    'End-to-End VLA',
    'Dual-System VLM + Planner',
    'VLA Reasoning & Reinforcement Learning',
    'Spatial, Temporal & 3D Grounding',
    'Efficient VLA & Deployment',
    'VLA Datasets, Benchmarks & Surveys'
  ]
};

const trackTitles = {
  e2e: 'End-to-End Autonomous Driving',
  vla: 'Vision-Language-Action Models',
  'world-model': 'Driving World Models'
};

const link = (label, url) => url ? `[${label}](${url})` : '—';
const anchor = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

let readme = '# Awesome Autonomous Driving Research\n\n';
readme += `A curated research collection for end-to-end autonomous driving, driving world models, vision-language-action models, and public evaluation benchmarks. The catalog is built from a Zotero library and currently contains **${papers.length} unique papers**.\n\n`;
const updatedAt = new Date().toISOString().slice(0, 10);
readme += `Last updated: ${updatedAt}. Paper metadata should be checked against the latest arXiv or publisher version before citation.\n\n`;
readme += '## Table of Contents\n\n- [Papers](#papers)\n';
for (const title of Object.values(trackTitles)) readme += `  - [${title}](#${anchor(title)})\n`;
readme += '- [Public Datasets and Benchmarks](#public-datasets-and-benchmarks)\n';
readme += '- [Leaderboard](#leaderboard)\n- [Contributing](#contributing)\n- [License](#license)\n\n';
readme += '## Papers\n\n';

for (const [track, title] of Object.entries(trackTitles)) {
  readme += `### ${title}\n\n`;
  for (const category of categoryOrder[track]) {
    const items = papers.filter((paper) => paper.track === track && paper.category === category);
    if (!items.length) continue;
    readme += `#### ${category}\n\n`;
    readme += '| Method | Year / Venue | Tags | Paper | Code | Project |\n';
    readme += '|---|---|---|---|---|---|\n';
    for (const paper of items) {
      const method = paper.name.replace(/\|/g, '\\|');
      const paperTitle = paper.title.replace(/\|/g, '\\|');
      const tags = paper.tags.map((tag) => `\`${tag}\``).join(' · ');
      readme += `| **${method}** — ${paperTitle} | ${paper.venue} | ${tags} | ${link('Paper', paper.paper)} | ${link('Code', paper.code)} | ${link('Project', paper.project)} |\n`;
    }
    readme += '\n';
  }
}

const benchmarks = JSON.parse(await readFile(resolve(root, 'data/benchmarks.json'), 'utf8'));
readme += '## Public Datasets and Benchmarks\n\n';
readme += '| Benchmark | Track | Evaluation Setting | Primary Metric | Resources |\n';
readme += '|---|---|---|---|---|\n';
for (const item of benchmarks) {
  const resources = [link('Homepage', item.homepage), link('Paper', item.paper), link('Code', item.code)]
    .filter((item) => item !== '—')
    .join(' · ');
  readme += `| **${item.name}** | ${item.track} | ${item.setting} | ${item.primaryMetric} | ${resources} |\n`;
}

readme += '\n## Leaderboard\n\n';
readme += 'Benchmark results are stored in [data/leaderboard.json](data/leaderboard.json). Submission requirements and reproducibility checks are documented in [benchmark/README.md](benchmark/README.md). Results from different protocol versions, sensor configurations, or data splits are not ranked together.\n\n';
readme += '## Contributing\n\n';
readme += 'Please read [CONTRIBUTING.md](CONTRIBUTING.md) before adding papers, benchmarks, or leaderboard results. Run `npm run validate` before opening a pull request.\n\n';
readme += '## License\n\n';
readme += 'This project is released under the [Apache License 2.0](LICENSE).\n';

await writeFile(resolve(root, 'data/papers.json'), `${JSON.stringify(papers, null, 2)}\n`, 'utf8');
await writeFile(resolve(root, 'README.md'), readme, 'utf8');

console.log(`Imported ${papers.length} unique papers from ${rawEntries.length} Zotero entries.`);
for (const [track, title] of Object.entries(trackTitles)) {
  console.log(`${title}: ${papers.filter((paper) => paper.track === track).length}`);
}
