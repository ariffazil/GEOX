#!/usr/bin/env node
/**
 * Phase 6: Inline deterministic validation + graph assembly.
 */
const fs = require('fs');
const path = require('path');

const UA_DIR = '/root/GEOX/.ua';
const PROJECT_ROOT = '/root/GEOX';

const assembled = JSON.parse(fs.readFileSync(path.join(UA_DIR, 'intermediate/assembled-graph.json'), 'utf8'));
const layers = JSON.parse(fs.readFileSync(path.join(UA_DIR, 'intermediate/layers.json'), 'utf8'));
const tour = JSON.parse(fs.readFileSync(path.join(UA_DIR, 'intermediate/tour.json'), 'utf8'));

const GIT_COMMIT = 'f154c12072acb38e462aef8c15dcecac14ad164d';
const ANALYZED_AT = new Date().toISOString();

// Build final knowledge graph
const graph = {
  version: '1.0.0',
  project: {
    name: 'GEOX',
    languages: ['python', 'typescript', 'javascript', 'yaml', 'json', 'markdown', 'html', 'css', 'shell', 'dockerfile'],
    frameworks: ['MCP', 'FastAPI', 'React', 'GemPy', 'LanceDB', 'H3', 'STAC'],
    description: 'GEOX — Earth Intelligence Sovereign Kernel. Physics-grounded geological intelligence for exploration, hazard assessment, and earth science. 555_COMPUTE_ONLY.',
    analyzedAt: ANALYZED_AT,
    gitCommitHash: GIT_COMMIT,
  },
  nodes: assembled.nodes,
  edges: assembled.edges,
  layers: layers,
  tour: tour,
};

// Validation
const issues = [];
const warnings = [];

if (!Array.isArray(graph.nodes)) issues.push('graph.nodes is missing or not an array');
if (!Array.isArray(graph.edges)) issues.push('graph.edges is missing or not an array');
if (!Array.isArray(graph.layers)) issues.push('graph.layers is missing or not an array');
if (!Array.isArray(graph.tour)) issues.push('graph.tour is missing or not an array');

const nodeIds = new Set();
const seen = new Map();
graph.nodes.forEach((n, i) => {
  if (!n.id) { issues.push(`Node[${i}] missing id`); return; }
  if (!n.type) issues.push(`Node[${i}] '${n.id}' missing type`);
  if (!n.name) issues.push(`Node[${i}] '${n.id}' missing name`);
  if (!n.summary) issues.push(`Node[${i}] '${n.id}' missing summary`);
  if (!n.tags || !n.tags.length) issues.push(`Node[${i}] '${n.id}' missing tags`);
  if (seen.has(n.id)) issues.push(`Duplicate node ID '${n.id}' at indices ${seen.get(n.id)} and ${i}`);
  else seen.set(n.id, i);
  nodeIds.add(n.id);
});

graph.edges.forEach((e, i) => {
  if (!nodeIds.has(e.source)) warnings.push(`Edge[${i}] source '${e.source}' not found (dangling)`);
  if (!nodeIds.has(e.target)) warnings.push(`Edge[${i}] target '${e.target}' not found (dangling)`);
});

// Check tour/layer references
graph.layers.forEach((layer) => {
  if (!layer.id || !layer.name || !layer.description || !Array.isArray(layer.nodeIds)) {
    issues.push(`Layer missing required fields: ${JSON.stringify(layer).slice(0, 100)}`);
  }
  (layer.nodeIds || []).forEach((id) => {
    if (!nodeIds.has(id)) warnings.push(`Layer '${layer.id}' refs missing node '${id}'`);
  });
});
graph.tour.forEach((step, i) => {
  if (!step.order || !step.title || !step.description || !Array.isArray(step.nodeIds)) {
    issues.push(`Tour step[${i}] missing required fields`);
  }
  (step.nodeIds || []).forEach((id) => {
    if (!nodeIds.has(id)) warnings.push(`Tour step[${i}] refs missing node '${id}'`);
  });
});

// Filter dangling edges (auto-fix where possible)
const beforeEdges = graph.edges.length;
graph.edges = graph.edges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
const droppedEdges = beforeEdges - graph.edges.length;
if (droppedEdges > 0) {
  warnings.push(`Dropped ${droppedEdges} dangling edges during validation`);
}

// Save assembled graph with full structure
const finalGraphPath = path.join(UA_DIR, 'intermediate/assembled-graph.json');
fs.writeFileSync(finalGraphPath, JSON.stringify(graph, null, 2));

// Stats
const stats = {
  totalNodes: graph.nodes.length,
  totalEdges: graph.edges.length,
  totalLayers: graph.layers.length,
  tourSteps: graph.tour.length,
  nodeTypes: graph.nodes.reduce((a, n) => { a[n.type] = (a[n.type] || 0) + 1; return a; }, {}),
  edgeTypes: graph.edges.reduce((a, e) => { a[e.type] = (a[e.type] || 0) + 1; return a; }, {}),
  issuesCount: issues.length,
  warningsCount: warnings.length,
  droppedEdges,
};

const review = { issues, warnings, stats };
fs.writeFileSync(path.join(UA_DIR, 'intermediate/review.json'), JSON.stringify(review, null, 2));

console.log('Phase 6 validation:');
console.log(`  Nodes: ${stats.totalNodes}`);
console.log(`  Edges: ${stats.totalEdges}`);
console.log(`  Layers: ${stats.totalLayers}`);
console.log(`  Tour steps: ${stats.tourSteps}`);
console.log(`  Issues: ${stats.issuesCount}`);
console.log(`  Warnings: ${stats.warningsCount}`);
console.log(`  Dropped dangling edges: ${droppedEdges}`);
if (issues.length > 0) {
  console.log('\nIssues (first 5):');
  for (const issue of issues.slice(0, 5)) console.log(`  - ${issue}`);
}
if (warnings.length > 0) {
  console.log('\nWarnings (first 5):');
  for (const warning of warnings.slice(0, 5)) console.log(`  - ${warning}`);
}

if (issues.length > 0) {
  process.exit(1);
}
