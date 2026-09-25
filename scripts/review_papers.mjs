import { readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('.', import.meta.url)), '..');
const dataPath = join(root, 'data', 'papers.json');
const papers = JSON.parse(await readFile(dataPath, 'utf8'));

// These tags are reviewed against the paper title/abstract and the author's
// method description. Keep the list concise because the README has one table
// per requested research track, with no additional topic subsections.
const reviewedTags = {
  '2609-21486': ['Occupancy Representation', 'Token Representation', 'Risk-Aware Planning'],
  '2606-31830': ['Geospatial Priors', 'Anticipatory Planning'],
  '2606-19836': ['Post-Training', 'Interactive Simulation', 'Long-Tail Safety'],
  '2606-19641': ['Self-Play', 'Closed-Loop Reinforcement Learning'],
  '2606-07464': ['Token Compression', 'Long-Context Memory', 'Planning-Aware Learning'],
  '2606-07170': ['Test-Time Optimization', 'Cross-Entropy Search', 'Trajectory Scoring'],
  '2605-31116': ['Scene Tokenization', 'Perception-Free Planning', 'Reconstruction Supervision'],
  '2605-15120': ['Closed-Loop Self-Distillation', 'Trajectory Scoring', 'Multi-Metric Planning'],
  '2605-08084': ['Driving Data Library', 'Multi-Modal Datasets', 'Data Standardization'],
  '2605-04647': ['Discrete Diffusion', 'Trajectory Editing'],
  '2604-15308': ['Diffusion Planning', 'Reinforcement Learning', 'Closed-Loop Adaptation'],
  '2604-08366': ['Data Selection', 'Data Scaling', 'Evaluation Alignment'],
  'guo-flowad-2026': ['Ego-Scene Interaction', 'Scene Flow', 'Closed-Loop Evaluation'],
  '2603-29163': ['Trajectory Scoring', 'Sparse Proposals', 'Multi-Modal Planning'],
  '2602-22801': ['Diffusion Planning', 'Reinforcement Learning', 'Real-World Validation'],
  '2602-20060': ['Flow Matching', 'One-Step Planning', 'Multi-Modal Trajectories'],
  '2602-13936': ['Causal Modeling', 'Motion Prediction', 'Domain Generalization'],
  '2601-12901': ['Reinforcement Fine-Tuning', 'Diffusion Planning', 'Adaptive Trajectories'],
  '2601-05083': ['Register Tokens', 'Vision Transformer Backbone', 'Trajectory Scoring'],
  '2601-01762': ['Lateral-Longitudinal Planning', 'Path-Conditioned Planning'],
  '2512-20563': ['Imitation Learning', 'Privileged Learning', 'Closed-Loop Evaluation'],
  '2512-07745': ['Diffusion Planning', 'Reinforcement Learning', 'Diverse Trajectories'],
  '2512-06865': ['Spatial Retrieval', 'Geospatial Priors', 'Robust Planning'],
  '2512-00470': ['Latent-Space Diffusion', 'Intent-Kinematics Disentanglement', 'Feature Alignment'],
  '2511-18729': ['Flow Matching', 'Safety-Constrained Planning'],
  '2511-17150': ['Diffusion Planning', 'Trajectory Refinement'],
  '2511-16518': ['Embodied Foundation Model', 'Cross-Embodiment Transfer', 'Autonomous Driving'],
  '2511-09013': ['Cooperative Driving', 'Multi-Agent Planning', 'V2X'],
  '2511-01768': ['LiDAR', 'Multi-View Fusion', 'Efficient Transformers'],
  '2510-24108': ['Trajectory Scoring', 'Zero-Shot Planning', 'Policy Optimization'],
  '2508-09158': ['Evolutionary Reinforcement Learning', 'Iterative Planning', 'Closed-Loop Driving'],
  '2508-05402': ['Knowledge Distillation', 'Planning-Centric Learning'],
  '2508-01778': ['HD Map Generation', 'BEV Semantics', 'Sensor Fusion'],
  '2507-14456': ['Mixture-of-Experts', 'Driving Skills', 'Adaptive Planning'],
  '2506-08541': ['Flow Matching', 'Motion Prediction', 'Multi-Modal Forecasting'],
  '2506-07725': ['Dual-System VLM', 'Fast-Slow Planning', 'Inference Efficiency'],
  '2506-06664': ['Trajectory Scoring', 'Multi-Modal Planning'],
  '2506-06659': ['Trajectory Selection', 'Safety Scoring', 'Imitation Learning'],
  '2506-04218': ['Evaluation Benchmark', 'Pseudo-Simulation', 'Open-Loop Metrics'],
  '2506-00034': ['Multi-Sensor Fusion', 'Gaussian Representation', 'End-to-End Planning'],
  '2505-15111': ['Proposal-Centric Planning', 'Iterative Refinement', 'Sparse Representation'],
  '2505-09315': ['Diffusion Planning', 'Multi-Modal Trajectories', 'Trajectory Diversity'],
  '2503-14182': ['Temporal Memory', 'Historical Prediction', 'Trajectory Planning'],
  '2503-12820': ['Knowledge Distillation', 'Expert-Guided Planning', 'Multi-Head Policy'],
  '2503-10434': ['Human Feedback', 'Personalized Driving Styles', 'Trajectory Generation'],
  '2503-08612': ['Hierarchical Planning', 'Multi-Granularity Queries'],
  '2503-07656': ['Unified Perception-Prediction-Planning', 'Transformer Architecture'],
  '2503-05689': ['Flow Matching', 'Goal-Conditioned Planning', 'Multi-Modal Trajectories'],
  '2503-03125': ['Trajectory Momentum', 'Occlusion Robustness', 'End-to-End Planning'],
  '2411-15139': ['Diffusion Policy', 'Real-Time Planning', 'Multi-Modal Trajectories'],
  '2406-15349': ['Benchmarking', 'Non-Reactive Simulation', 'Data-Driven Evaluation'],
  '2406-06978': ['Knowledge Distillation', 'Multi-Teacher Learning', 'Trajectory Selection'],
  '2405-19620': ['Sparse Scene Representation', 'Multi-Task Learning', 'End-to-End Planning'],
  '2402-13243': ['Vectorized Scene Representation', 'End-to-End Planning'],
  '2312-03031': ['BEV Representation', 'Trajectory Planning'],
  '2303-12077': ['Vectorized Scene Representation', 'End-to-End Planning'],
  '2212-10156': ['Unified Autonomous Driving', 'Planning-Oriented Learning'],
  '2207-07601': ['Spatial-Temporal Learning', 'End-to-End Planning', 'Closed-Loop Evaluation'],
  '2205-15997': ['Sensor Fusion', 'Imitation Learning', 'End-to-End Driving'],

  '2609-00111': ['Vision-Language Foundation Model', '3D Perception', 'Joint Planning'],
  '2608-18035': ['Traffic Element Conditioning', 'End-to-End Planning'],
  '2608-12854': ['VLA-WAM Integration', 'Predictive Dynamics', 'Joint Planning'],
  '2608-10413': ['Failure Memory', 'Retrieval Augmentation', 'Distribution Shift'],
  '2608-09591': ['Spatial Reasoning', 'Reasoning Optimization', 'Trajectory Planning'],
  '2608-01755': ['Reinforcement Learning with Verifiable Rewards', 'Reasoning Supervision'],
  '2607-14727': ['Work-Zone Reasoning', 'VLM Planning', 'Robustness'],
  '2607-08072': ['Survey', 'Post-Training', 'Policy Optimization'],
  '2607-06403': ['Generalist VLA', 'Data Scaling', 'Real-World Deployment'],
  '2607-03182': ['Navigation-Conditioned Planning', 'Continuous Actions'],
  '2607-01658': ['Spatial Grounding', 'Action-Grounded Supervision'],
  '2606-24742': ['Cross-Domain Robotics', 'World-Value Modeling'],
  '2606-08525': ['Reward Modeling', 'Trajectory Selection', 'Data Scaling'],
  '2605-23270': ['Causal Flow Matching', 'Trajectory Generation', 'Global Consistency'],
  '2605-21061': ['Inverse Kinematics', 'Future-State Grounding', 'Trajectory Recovery'],
  '2605-04470': ['Counterfactual Learning', 'Interactive Reinforcement Learning', 'Policy Fine-Tuning'],
  '2604-17915': ['Unified Multimodal Decoding', 'Structured Actions', 'End-to-End Planning'],
  '2604-02190': ['Joint Perception and Planning', '3D Grounding', 'VLA'],
  '2604-00813': ['Vision-Geometry-Action', '3D Geometry', 'Action Planning'],
  '2603-28116': ['Chain-of-Thought', 'Reinforcement Fine-Tuning', 'Unified Driving'],
  '2603-14972': ['Takeover Learning', 'Post-Training', 'Distribution Shift'],
  '2603-14851': ['Asynchronous VLA', 'Mixture-of-Transformers', 'Efficient Inference'],
  '2603-11041': ['World Dynamics Reasoning', 'Dynamics Tokens', 'Action Planning'],
  '2603-09465': ['Knowledge Distillation', 'Perception-Planning Alignment'],
  '2603-06049': ['Exploration', 'Reinforcement Learning', 'Policy Improvement'],
  '2603-01928': ['Latent Reasoning', 'Spatio-Temporal Grounding'],
  '2603-01441': ['Language-Action Alignment', 'Parallel Action Generation'],
  '2603-01063': ['Learning from Failures', 'Reinforcement Learning', 'Long-Tail Exploration'],
  '2602-21172': ['Data Efficiency', 'Reasoning-Free VLA', 'Driving Policy'],
  '2602-20794': ['Cross-View Geometry', '3D Grounding', 'VLM'],
  '2602-13329': ['Hierarchical Planning', 'Spatio-Temporal Reasoning', '3D Grounding'],
  '2602-10719': ['Dual-System VLM', 'Vision-Only Backbones', 'Representation Complementarity'],
  '2601-06474': ['Sparse Occupancy', '4D Scene Understanding', 'Unified Planning'],
  '2601-05640': ['Scene-to-Goal Reasoning', 'Hierarchical Planning', '3D Grounding'],
  '2601-05611': ['Latent Future Representation', 'VLM Transfer', 'Trajectory Planning'],
  'bassole-hybriddrivevla-2026': ['Visual Chain-of-Thought', 'Waypoint Evaluation', 'Safety and Comfort'],
  '2512-22939': ['Latent Reasoning', 'Hierarchical Planning', 'Parallel Trajectories'],
  '2512-10719': ['Spatial Awareness', '3D Reasoning', 'VLM Planning'],
  '2512-06112': ['Discrete Flow Matching', 'Parallel Planning', 'Structured Actions'],
  '2512-01830': ['Reasoning Fine-Tuning', 'Reinforcement Learning', 'Driving Policy'],
  '2511-00088': ['Causal Reasoning', 'Trajectory Planning', 'Long-Tail Driving'],
  '2511-00062': ['World Foundation Model', 'Video Generation', 'Flow-Based Modeling'],
  '2509-20109': ['Discrete Diffusion', 'Reflective Reasoning', 'Trajectory Generation'],
  '2509-05578': ['Occupancy Grounding', '3D Spatial Understanding', 'VLA'],
  '2507-23318': ['Visual Token Pruning', 'Efficient Inference', 'VLA'],
  '2506-13757': ['Joint Reasoning and Action', 'Autoregressive VLA', 'Reinforcement Learning'],
  '2506-08052': ['Cognitive Planning', 'Action Tokenization', 'Reinforcement Learning'],
  '2505-19381': ['Diffusion Planning', 'BEV Efficiency', 'Action Diversity'],
  '2505-16278': ['Mixture-of-Experts', 'Scenario Specialization', 'End-to-End Planning'],
  '2505-00284': ['VLM Evaluation', 'Open-Loop Benchmarking', 'Inference Cost'],
  '2503-23463': ['Spatially Grounded Actions', 'Language-Conditioned Driving', 'VLA'],
  '2503-15558': ['Physical Reasoning', 'Embodied Foundation Model'],
  '2503-07608': ['VLM Reasoning', 'Reinforcement Learning', 'Long-Tail Driving'],

  '2609-21712': ['Driving World Model', 'Controllable Simulation'],
  '2609-20377': ['Multimodal Future Prediction', 'World Modeling'],
  '2609-03602': ['World-Action Model', 'Semantic Video Representation'],
  '2608-28404': ['Video Diffusion', 'Driving Data Scaling', 'World Generation'],
  '2608-22187': ['Behavior-Conditioned Generation', 'Driving Simulation', 'World Model'],
  '2608-20974': ['Video JEPA', 'World-Action Modeling', 'Self-Supervised Learning'],
  '2608-20430': ['World-Action Modeling', 'Action-Conditioned Prediction'],
  '2608-19085': ['World-Action Modeling', 'Latent Dynamics'],
  '2608-10107': ['World-Action Modeling', '4D Scene Representation'],
  '2608-07468': ['World-Action Model', 'Training-Time Prediction', 'End-to-End Driving'],
  '2608-03084': ['Video Generation', 'Scene Understanding', 'End-to-End Driving'],
  '2607-29031': ['Action-Centered JEPA', 'Latent Dynamics', 'Planning'],
  '2607-26056': ['Intent-to-Action', 'JEPA', 'Reward-Free Learning'],
  '2607-20988': ['VLA-WAM Integration', 'Latent World Modeling', 'Driving Policy'],
  '2607-17521': ['Geometric Grounding', '3D Scene Modeling', 'Future-Aware Planning'],
  '2606-30421': ['Temporal Causal Dynamics', 'World Modeling', 'End-to-End Planning'],
  '2606-15869': ['World-Action Modeling', 'Efficient Inference', 'Decoupled Video and Action'],
  '2606-03159': ['Interactive Simulation', 'Closed-Loop Evaluation', 'Long-Tail Scenarios'],
  '2606-02800': ['Omnimodal Foundation Model', 'World Generation', 'Physical AI'],
  '2605-24892': ['Video-Based World Modeling', 'Future Reasoning', 'VLA'],
  '2605-18137': ['3D Reconstruction', 'World Generation', 'Autonomous Driving'],
  '2605-17682': ['Occupancy Forecasting', '3D Scene Dynamics', 'Motion Planning'],
  '2605-14696': ['World Model', 'Data-Efficient Planning', 'Annotation-Free Learning'],
  '2605-11596': ['Autoregressive Simulation', 'Long-Horizon Rollout', 'Self-Correction'],
  '2605-11550': ['World-Action Co-Modeling', 'Joint Prediction and Planning'],
  '2605-10564': ['Latent-State Prediction', 'Long-Horizon World Modeling', 'VLM Reasoning'],
  '2605-10426': ['Latent World Reasoning', 'Planning-Oriented VLA', '3D Grounding'],
  '2605-09701': ['Latent World Model', 'Future-Conditioned Planning'],
  '2604-20289': ['Real-Time Simulation', 'Autoregressive Video Generation', 'Inference Efficiency'],
  '2604-04198': ['World-Model Planning', 'Domain Generalization', 'Robustness'],
  '2604-02714': ['Policy Exploration', 'Reinforcement Learning', 'World Modeling'],
  '2604-01765': ['Geometry-Grounded World Model', 'Unified Generation and Planning'],
  '2603-27287': ['Unified VLA and World Model', 'Closed-Loop Planning'],
  '2603-24581': ['Latent World-Action Model', 'Spatial Representation', 'Temporal Dynamics'],
  '2603-19979': ['Simulation Benchmark', 'VLA Evaluation', 'Controllable Scenarios'],
  '2603-16666': ['World-Action Model', 'Training-Time Imagination', 'Inference Efficiency'],
  '2603-14948': ['WorldDrive', 'Scene Generation', 'Motion Planning'],
  '2602-10884': ['Temporal Residual Dynamics', 'World-Model Planning'],
  '2602-06521': ['Unified VLA and World Model', 'Latent Dynamics', 'Joint Planning'],
  '2602-01536': ['Unified Driving World Model', 'Geometry and Dynamics'],
  '2601-22032': ['JEPA', 'Self-Supervised Video Learning', 'Planning Representation'],
  '2601-04453': ['Unified VLM Planning', 'World Modeling', 'End-to-End Driving'],
  '2512-23421': ['World-Action Model', 'Video Generation', 'Joint Planning'],
  '2512-19133': ['Reinforcement Fine-Tuning', 'Latent World Model', 'End-to-End Planning'],
  '2512-04441': ['Trajectory Scoring', 'World-Model Planning', 'Multi-Modal Planning'],
  '2511-23369': ['Driving Simulation', 'Synthetic Data Generation', 'Policy Learning'],
  '2510-12796': ['World-Model Pretraining', 'Data Scaling Laws', 'Policy Learning'],
  '2510-10726': ['3D Reconstruction', 'Geometric Foundation Model', 'World Representation'],
  '2510-04333': ['Alternative-Trajectory Generation', 'Closed-Loop Recovery', 'World Modeling'],
  '2508-06571': ['Inverse Reinforcement Learning', 'Policy Post-Training', 'VLA'],
  '2507-00603': ['Self-Supervised World Model', 'Annotation-Free Planning'],
  '2506-24113': ['Autoregressive Video Diffusion', 'Long-Horizon Prediction', 'Planning'],
  '2504-01941': ['Online Trajectory Evaluation', 'BEV World Model', 'Closed-Loop Planning'],
  '2503-14492': ['Controllable World Generation', 'Multi-Modal Conditioning', 'Simulation'],
  '2501-14729': ['3D Scene Understanding', 'World Generation', 'Unified World Model'],
  '2501-03575': ['World Foundation Model', 'Video Generation', 'Physical AI'],
  '2412-10371': ['Gaussian Representation', '3D Scene Modeling', 'End-to-End Planning'],
  '2406-08481': ['Latent World Model', 'Self-Supervised Representation', 'End-to-End Planning'],
  '2405-17398': ['Driving World Model', 'Controllable Generation', 'Generalization'],
  '2311-16038': ['Occupancy World Model', '3D Scene Forecasting', 'Planning']
};

const methodNames = {
  '2503-03125': 'MomAD',
  '2607-08072': 'Post-Training Survey',
  '2607-06403': 'LingBot-VLA 2.0',
  '2603-06049': 'Curious-VLA',
  '2602-10719': 'Dual-System Driving',
  'bassole-hybriddrivevla-2026': 'HybridDriveVLA',
  '2603-14948': 'WorldDrive'
};

const redirects = {
  'autonomousvision/lead': 'https://github.com/kesai-labs/lead',
  'qiyan98/TrajFlow': 'https://github.com/DSL-Lab/TrajFlow',
  'SunZhigang7/DiffSemanticFusion': 'https://github.com/SunZhigang7/DiffSemanticFusion_MaplessQCNet'
};
const countAliases = {
  'kesai-labs/lead': 'autonomousvision/lead',
  'DSL-Lab/TrajFlow': 'qiyan98/TrajFlow',
  'SunZhigang7/DiffSemanticFusion_MaplessQCNet': 'SunZhigang7/DiffSemanticFusion'
};
const pendingCodeRepositories = {
  '2606-19641': 'https://github.com/montrealrobotics/gigapixel',
  '2604-02714': 'https://github.com/zihaosheng/ExploreVLA'
};
const verifiedProjectPages = {
  '2602-22801': 'https://zhengyinan-air.github.io/Hyper-Diffusion-Planner/',
  '2601-05083': 'https://valeoai.github.io/driving-on-registers/',
  '2601-01762': 'https://yanhaowu.github.io/AlignDrive/',
  '2512-23421': 'https://wm-research.github.io/DriveLaW/',
  '2512-04441': 'https://xiaomi-mlab.github.io/MindDrive/',
  '2604-15308': 'https://hgao-cv.github.io/RAD/'
};
const verifiedCodeRepositories = {
  '2606-07170': 'https://github.com/valeoai/TOAD',
  '2602-22801': 'https://github.com/ZhengYinan-AIR/Hyper-Diffusion-Planner',
  '2601-05083': 'https://github.com/valeoai/DrivoR',
  '2601-01762': 'https://github.com/YanhaoWu/AlignDrive',
  '2601-22032': 'https://github.com/linhanwang/Drive-JEPA',
  '2608-18035': 'https://github.com/ZZongzheng0918/TE-Aware-E2E-AD',
  '2608-01755': 'https://github.com/hzx122/DEFT-RLVR',
  '2607-26056': 'https://github.com/zju3dv/INTACT-JEPA',
  '2606-15869': 'https://github.com/LogosRoboticsGroup/Metis',
  '2605-14696': 'https://github.com/JiaweiXu8/EponaV2',
  '2605-11550': 'https://github.com/COOWAI/DAWN',
  '2604-04198': 'https://github.com/xiaomi-mlab/DriveVA',
  '2603-27287': 'https://github.com/LogosRoboticsGroup/UniWorldVLA',
  '2603-01928': 'https://github.com/luo-yc17/LaST-VLA',
  '2603-01063': 'https://github.com/luo-yc17/ELF-VLA',
  '2602-20794': 'https://github.com/WJ-CV/VGGDrive',
  '2601-06474': 'https://github.com/MSunDYY/SparseOccVLA',
  '2601-05640': 'https://github.com/LogosRoboticsGroup/SGDrive',
  '2512-23421': 'https://github.com/wm-research/DriveLaW',
  '2512-04441': 'https://github.com/xiaomi-mlab/MindDrive',
  '2512-01830': 'https://github.com/wyddmw/OpenREAD',
  '2512-00470': 'https://github.com/jhz1192/Latent-Planner',
  '2511-09013': 'https://github.com/Souig/UniMM-V2X',
  '2510-12796': 'https://github.com/BraveGroup/DriveVLA-W0',
  '2509-20109': 'https://github.com/pixeli99/ReflectDrive',
  '2508-06571': 'https://github.com/IRL-VLA/IRL-VLA',
  '2506-06659': 'https://github.com/William-Yao-2000/DriveSuprim',
  '2505-19381': 'https://github.com/boschresearch/DiffVLA',
  '2503-23463': 'https://github.com/DriveVLA/OpenDriveVLA',
  '2503-14182': 'https://github.com/fudan-zvg/BridgeAD',
  '2503-08612': 'https://github.com/nullmax-vision/HiP-AD',
  '2503-07656': 'https://github.com/Thinklab-SJTU/DriveTransformer',
  '2406-06978': 'https://github.com/NVlabs/Hydra-MDP'
};
const starData = JSON.parse(await readFile(join(root, 'data', 'github-stars.json'), 'utf8'));
const reviewedStarCounts = {
  'ori-mrg/PriorEye': 61,
  'OpenDriveLab/WorldEngine': 506,
  'SpatialRetrievalAD/End2End-Planning': 3,
  'DSL-Lab/TrajFlow': 83,
  'CurryChen77/CraftPolicy': 21,
  'OscarHuangWind/AutoMoT': 61,
  'yaoyao-jpg/DynamicsVLA': 58,
  'Applied-Intuition-Open-Source/nord': 12,
  'pqh22/ColaVLA': 67,
  'zhenghao2519/SpaceDrive': 93,
  'ucla-mobility/AutoVLA': 655,
  'Thinklab-SJTU/DriveMoE': 234,
  'zcliangyue/HorizonDrive': 57,
  'zihaosheng/ExploreVLA': 29,
  'youngzhou1999/DriveDreamer-Policy': 59,
  'yuantianyuan01/FastWAM': 1500,
  'UniDrive-WM/UniDrive-WM': 0,
  'OpenDriveLab/SimScale': 327,
  'Tencent-Hunyuan/HunyuanWorld-Mirror': 1200,
  'vita-epfl/RAP': 164,
  'AutoLab-SAI-SJTU/FlowAD': 18
};
for (const [repository, stars] of Object.entries(reviewedStarCounts)) {
  starData.repositories[repository] = {
    stars,
    url: `https://github.com/${repository}`,
    checkedAt: '2026-09-24'
  };
}
for (const [canonical, alias] of Object.entries(countAliases)) {
  if (!starData.repositories[canonical] && starData.repositories[alias]) {
    starData.repositories[canonical] = {
      ...starData.repositories[alias],
      url: `https://github.com/${canonical}`,
      checkedAt: '2026-09-24'
    };
  }
  delete starData.repositories[alias];
}
starData.updatedAt = new Date().toISOString();
const unresolved = [];

for (const paper of papers) {
  const tags = reviewedTags[paper.id];
  if (!tags) unresolved.push(paper.id);
  else paper.tags = tags;

  if (methodNames[paper.id]) paper.name = methodNames[paper.id];
  const currentRepo = paper.code?.match(/^https:\/\/github\.com\/([^/]+\/[^/#?]+)/i)?.[1]?.replace(/\.git$/i, '');
  if (currentRepo && redirects[currentRepo]) paper.code = redirects[currentRepo];
  if (paper.id === 'guo-flowad-2026') paper.code = 'https://github.com/AutoLab-SAI-SJTU/FlowAD';
  if (verifiedCodeRepositories[paper.id]) paper.code = verifiedCodeRepositories[paper.id];
  if (pendingCodeRepositories[paper.id]) paper.code = pendingCodeRepositories[paper.id];
  if (paper.id === '2601-04453') paper.code = undefined; // Project URL is a template, not an implementation.
  if (verifiedProjectPages[paper.id]) paper.project = verifiedProjectPages[paper.id];
  if (paper.id === '2406-06978' && paper.project === paper.code) paper.project = undefined;
  if (paper.id === '2608-07468') paper.code = 'https://github.com/H-EmbodVis/SimWAM';
  if (paper.id === '2603-06049') paper.code = 'https://github.com/Mashiroln/curious_vla';
  if (paper.id === '2602-10884') paper.code = 'https://github.com/mengtan00/ResWorld';
  if (paper.id === '2602-06521') paper.code = 'https://github.com/liulin815/DriveWorld-VLA';
  if (paper.id === '2506-24113') paper.code = 'https://github.com/Kevin-thu/Epona';

  const repo = paper.code?.match(/^https:\/\/github\.com\/([^/]+\/[^/#?]+)/i)?.[1]?.replace(/\.git$/i, '');
  const cached = repo && (starData.repositories[repo] || starData.repositories[countAliases[repo]]);
  if (cached && Number.isInteger(cached.stars)) paper.stars = cached.stars;
  if (!paper.code || pendingCodeRepositories[paper.id]) paper.stars = null;
  paper.codeStatus = pendingCodeRepositories[paper.id] ? 'pending' : paper.code ? 'released' : 'not-found';
  paper.openSource = paper.codeStatus === 'released';
}

if (unresolved.length) {
  console.error(`Missing reviewed tags for ${unresolved.length} papers: ${unresolved.join(', ')}`);
  process.exit(1);
}

const counts = Object.fromEntries(['e2e', 'vla', 'world-model'].map((track) => [
  track,
  papers.filter((paper) => paper.track === track).length
]));
const currentRepositories = new Set(papers.map((paper) =>
  paper.code?.match(/^https:\/\/github\.com\/([^/]+\/[^/#?]+)/i)?.[1]?.replace(/\.git$/i, '')
).filter(Boolean));
for (const repository of Object.keys(starData.repositories)) {
  if (!currentRepositories.has(repository)) delete starData.repositories[repository];
}
await writeFile(dataPath, `${JSON.stringify(papers, null, 2)}\n`, 'utf8');
await writeFile(join(root, 'data', 'github-stars.json'), `${JSON.stringify(starData, null, 2)}\n`, 'utf8');
console.log(`Applied reviewed tags and code status to ${papers.length} papers: ${JSON.stringify(counts)}.`);
