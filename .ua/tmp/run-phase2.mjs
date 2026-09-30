#!/usr/bin/env node
/**
 * Phase 2 deterministic runner.
 * For each batch in batches.json: run extract-structure.mjs, build batch-N.json.
 * No LLM — uses deterministic metadata from extract + batchImportData.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = '/root/.opencode/skills/understand';
const UA_DIR = '/root/GEOX/.ua';
const PROJECT_ROOT = '/root/GEOX';

const batchesJson = JSON.parse(fs.readFileSync(path.join(UA_DIR, 'intermediate/batches.json'), 'utf8'));
const batches = batchesJson.batches;
const totalBatches = batchesJson.totalBatches;

console.log(`[Phase 2] Processing ${totalBatches} batches deterministically`);

// Map fileCategory to node type prefix
function nodeTypeFor(fileCategory, language, filePath) {
  if (fileCategory === 'code') return 'file';
  if (fileCategory === 'config') return 'config';
  if (fileCategory === 'docs') return 'document';
  if (fileCategory === 'script') return 'file';
  if (fileCategory === 'markup') return 'file';
  if (fileCategory === 'data') {
    if (language === 'graphql' || filePath.endsWith('.proto') || filePath.endsWith('.prisma')) return 'schema';
    if (filePath.endsWith('.sql')) return 'table';
    if (language === 'openapi' || language === 'swagger') return 'endpoint';
    return 'file';
  }
  if (fileCategory === 'infra') {
    if (/Dockerfile|docker-compose/.test(filePath)) return 'service';
    if (/\.github\/workflows|\.gitlab-ci|Jenkinsfile|CircleCI/.test(filePath)) return 'pipeline';
    if (/\.tf$|\.tfvars$|CloudFormation|Vagrantfile/.test(filePath)) return 'resource';
    return 'service';
  }
  return 'file';
}

function tagsForCategory(fileCategory, language, filePath) {
  const tags = [];
  if (fileCategory === 'code') tags.push('code');
  if (fileCategory === 'config') tags.push('configuration');
  if (fileCategory === 'docs') tags.push('documentation');
  if (fileCategory === 'infra') tags.push('infrastructure');
  if (fileCategory === 'data') tags.push('data');
  if (fileCategory === 'script') tags.push('script');
  if (fileCategory === 'markup') tags.push('markup');
  if (language) tags.push(language);
  // Pattern hints
  if (/test|spec/i.test(filePath)) tags.push('test');
  if (filePath === 'README.md') tags.push('entry-point', 'documentation');
  if (filePath.endsWith('__init__.py')) tags.push('package-marker');
  if (filePath.endsWith('.py') && /main\.py$/.test(filePath)) tags.push('entry-point');
  if (/Dockerfile/.test(filePath)) tags.push('containerization', 'deployment');
  if (/docker-compose/.test(filePath)) tags.push('orchestration');
  if (/\.github\/workflows/.test(filePath)) tags.push('ci-cd');
  return Array.from(new Set(tags)).slice(0, 6);
}

function complexityFromLines(nonEmpty, fileCategory) {
  if (fileCategory === 'docs' || fileCategory === 'config') {
    if (nonEmpty < 30) return 'simple';
    if (nonEmpty < 150) return 'moderate';
    return 'complex';
  }
  if (nonEmpty < 50) return 'simple';
  if (nonEmpty < 200) return 'moderate';
  return 'complex';
}

function summarizeFromData(file, extract) {
  const r = extract.results.find(x => x.path === file.path);
  if (!r) return '';
  const parts = [];
  if (r.functions?.length) parts.push(`${r.functions.length} function(s)`);
  if (r.classes?.length) parts.push(`${r.classes.length} class(es)`);
  if (r.exports?.length) parts.push(`${r.exports.length} export(s)`);
  return parts.join(', ');
}

let totalNodes = 0;
let totalEdges = 0;
let totalFunctions = 0;
let totalClasses = 0;
let totalImports = 0;
const errors = [];

for (const batch of batches) {
  const { batchIndex, files, batchImportData } = batch;
  const inputPath = path.join(UA_DIR, `tmp/ua-file-analyzer-input-${batchIndex}.json`);
  const extractPath = path.join(UA_DIR, `tmp/extracted/extract-${batchIndex}.json`);
  const outPath = path.join(UA_DIR, `intermediate/batch-${batchIndex}.json`);

  // Build input for extract-structure.mjs
  const inputObj = {
    projectRoot: PROJECT_ROOT,
    batchFiles: files,
    batchImportData: batchImportData || {},
  };
  fs.writeFileSync(inputPath, JSON.stringify(inputObj));

  try {
    execFileSync('node', [
      path.join(SKILL_DIR, 'extract-structure.mjs'),
      inputPath,
      extractPath,
    ], { stdio: ['ignore', 'pipe', 'pipe'], timeout: 60000 });
  } catch (err) {
    const stderr = err.stderr ? err.stderr.toString().slice(0, 500) : err.message;
    errors.push({ batch: batchIndex, error: 'extract-structure failed', stderr });
    // Still write an empty batch file to avoid merge dropping batches
    fs.writeFileSync(outPath, JSON.stringify({ nodes: [], edges: [] }));
    continue;
  }

  const extract = JSON.parse(fs.readFileSync(extractPath, 'utf8'));
  const resultsByPath = new Map(extract.results.map(r => [r.path, r]));

  const nodes = [];
  const edges = [];

  // 1) File-level nodes + function/class nodes
  for (const file of files) {
    const r = resultsByPath.get(file.path);
    const nodeType = nodeTypeFor(file.fileCategory, file.language, file.path);
    const id = `${nodeType}:${file.path}`;
    const nonEmpty = r?.nonEmptyLines ?? Math.max(1, Math.floor(file.sizeLines * 0.7));
    const summaryParts = [];
    if (r) {
      if (r.functions?.length) summaryParts.push(`Defines ${r.functions.length} function(s)`);
      if (r.classes?.length) summaryParts.push(`${r.classes.length} class(es)`);
      if (r.exports?.length) summaryParts.push(`exports ${r.exports.length} symbol(s)`);
    }
    if (summaryParts.length === 0) {
      summaryParts.push(`${file.language || 'unknown'} ${file.fileCategory} file (${nonEmpty} non-empty lines).`);
    }
    nodes.push({
      id,
      type: nodeType,
      name: path.basename(file.path),
      filePath: file.path,
      summary: summaryParts.join('; '),
      tags: tagsForCategory(file.fileCategory, file.language, file.path),
      complexity: complexityFromLines(nonEmpty, file.fileCategory),
    });
    totalNodes++;

    // Function and class nodes (code files only)
    if (r && file.fileCategory === 'code') {
      for (const fn of r.functions || []) {
        const lineCount = (fn.endLine || fn.startLine) - (fn.startLine || 0);
        if (lineCount < 10 && !fn.name.match(/^[A-Z_]/)) continue; // significance filter
        const fnId = `function:${file.path}:${fn.name}`;
        nodes.push({
          id: fnId,
          type: 'function',
          name: fn.name,
          filePath: file.path,
          lineRange: [fn.startLine, fn.endLine],
          summary: `${fn.name}(${(fn.params || []).join(', ')}) — ${lineCount} line(s).`,
          tags: ['function'],
          complexity: lineCount > 100 ? 'complex' : lineCount > 30 ? 'moderate' : 'simple',
        });
        edges.push({
          source: id,
          target: fnId,
          type: 'contains',
          direction: 'forward',
          weight: 1.0,
        });
        totalFunctions++;
      }
      for (const cls of r.classes || []) {
        const lineCount = (cls.endLine || cls.startLine) - (cls.startLine || 0);
        const methodCount = (cls.methods || []).length;
        if (lineCount < 20 && methodCount < 2) continue;
        const clsId = `class:${file.path}:${cls.name}`;
        nodes.push({
          id: clsId,
          type: 'class',
          name: cls.name,
          filePath: file.path,
          lineRange: [cls.startLine, cls.endLine],
          summary: `Class ${cls.name} with ${methodCount} method(s).`,
          tags: ['class'],
          complexity: lineCount > 200 ? 'complex' : lineCount > 50 ? 'moderate' : 'simple',
        });
        edges.push({
          source: id,
          target: clsId,
          type: 'contains',
          direction: 'forward',
          weight: 1.0,
        });
        totalClasses++;
      }
    }
  }

  // 2) Import edges (1:1 emission per the skill rule)
  for (const file of files) {
    const nodeType = nodeTypeFor(file.fileCategory, file.language, file.path);
    const srcId = `${nodeType}:${file.path}`;
    const imports = batchImportData?.[file.path] || [];
    for (const targetPath of imports) {
      edges.push({
        source: srcId,
        target: `file:${targetPath}`,
        type: 'imports',
        direction: 'forward',
        weight: 0.7,
      });
      totalImports++;
    }
  }

  totalEdges += edges.length;

  fs.writeFileSync(outPath, JSON.stringify({ nodes, edges }, null, 2));

  if (batchIndex % 10 === 0 || batchIndex === totalBatches) {
    process.stdout.write(`  batch ${batchIndex}/${totalBatches}: ${nodes.length} nodes, ${edges.length} edges (cumulative nodes=${totalNodes}, edges=${totalEdges})\n`);
  }
}

console.log(`\n[Phase 2] Done. Total nodes=${totalNodes}, edges=${totalEdges}, functions=${totalFunctions}, classes=${totalClasses}, imports=${totalImports}`);
console.log(`[Phase 2] Errors: ${errors.length}`);
if (errors.length > 0) {
  console.log(JSON.stringify(errors.slice(0, 5), null, 2));
}
