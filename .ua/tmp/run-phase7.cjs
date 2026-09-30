#!/usr/bin/env node
/**
 * Phase 7: Save knowledge-graph.json + meta.json atomically.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const UA_DIR = '/root/GEOX/.ua';
const PROJECT_ROOT = '/root/GEOX';
const SKILL_DIR = '/root/.opencode/skills/understand';

const GIT_COMMIT = 'f154c12072acb38e462aef8c15dcecac14ad164d';

// Load final graph (with layers + tour)
const graph = JSON.parse(fs.readFileSync(path.join(UA_DIR, 'intermediate/assembled-graph.json'), 'utf8'));

// 1) Atomic write of knowledge-graph.json
const tmpGraph = path.join(UA_DIR, 'knowledge-graph.json.tmp');
fs.writeFileSync(tmpGraph, JSON.stringify(graph, null, 2));
fs.renameSync(tmpGraph, path.join(UA_DIR, 'knowledge-graph.json'));
console.log(`Wrote ${UA_DIR}/knowledge-graph.json`);

// 2) Build fingerprints baseline (must succeed before meta.json)
const filePaths = graph.nodes
  .filter(n => n.type === 'file' || n.type === 'config' || n.type === 'document' ||
               n.type === 'service' || n.type === 'pipeline' || n.type === 'resource' ||
               n.type === 'schema' || n.type === 'table' || n.type === 'endpoint')
  .map(n => n.filePath)
  .filter(Boolean);

const fingerprintInput = {
  projectRoot: PROJECT_ROOT,
  filePaths: filePaths,
  gitCommitHash: GIT_COMMIT,
};
const fpInputPath = path.join(UA_DIR, 'intermediate/fingerprint-input.json');
fs.writeFileSync(fpInputPath, JSON.stringify(fingerprintInput, null, 2));
console.log(`Wrote fingerprint-input.json (${filePaths.length} files)`);

try {
  const out = execFileSync('node', [
    path.join(SKILL_DIR, 'build-fingerprints.mjs'),
    fpInputPath,
  ], { stdio: ['ignore', 'pipe', 'pipe'], timeout: 180000 }).toString();
  if (!out.includes('Fingerprints baseline:')) {
    throw new Error('build-fingerprints.mjs did not emit baseline line:\n' + out);
  }
  console.log('Fingerprints baseline built successfully');
} catch (err) {
  console.error('Fingerprint build failed:', err.message);
  process.exit(1);
}

// 3) Write meta.json
const meta = {
  lastAnalyzedAt: new Date().toISOString(),
  gitCommitHash: GIT_COMMIT,
  version: '1.0.0',
  analyzedFiles: filePaths.length,
};
const metaPath = path.join(UA_DIR, 'meta.json');
fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2));
console.log(`Wrote ${UA_DIR}/meta.json`);

// 4) Final summary
const kgStats = fs.statSync(path.join(UA_DIR, 'knowledge-graph.json'));
const metaStats = fs.statSync(metaPath);
console.log('\n=== FINAL ===');
console.log(`knowledge-graph.json: ${(kgStats.size / 1024).toFixed(1)} KB`);
console.log(`meta.json: ${metaStats.size} bytes`);
console.log(`Nodes: ${graph.nodes.length}`);
console.log(`Edges: ${graph.edges.length}`);
console.log(`Layers: ${graph.layers.length}`);
console.log(`Tour steps: ${graph.tour.length}`);
