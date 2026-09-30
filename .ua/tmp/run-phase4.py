#!/usr/bin/env python3
"""Phase 4: Deterministic layer assignment based on directory structure."""
import json, os
from collections import defaultdict, Counter

UA_DIR = '/root/GEOX/.ua'
PROJECT_ROOT = '/root/GEOX'

with open(f'{UA_DIR}/intermediate/assembled-graph.json') as f:
    g = json.load(f)

# Build a file-level node index
file_nodes = [n for n in g['nodes'] if n['type'] in ('file', 'config', 'document', 'service', 'pipeline', 'resource', 'schema', 'table', 'endpoint')]
file_node_ids = {n['id'] for n in file_nodes}
print(f"File-level nodes: {len(file_nodes)}")

# Layer rules
LAYER_RULES = [
    ('entry-point', '🟢 Entry Points', 'Top-level project metadata, README, entry scripts.', lambda fp: fp in ('README.md', 'pyproject.toml', 'package.json') or fp.startswith('entrypoint.sh') or fp.startswith('Dockerfile')),
    ('governance', '🏛️ Governance & Federation', 'Constitutional floors, federation contracts, governance docs.', lambda fp: fp.startswith('docs/GOVERNANCE') or '/FEDERATION' in fp or '/governance/' in fp.lower() or fp.startswith('CLAUDE.md') or fp.startswith('AGENTS.md') or fp.startswith('FEDERATION') or 'constitutional' in fp.lower() or fp.startswith('GENESIS')),
    ('mcp-apps', '🖥️ MCP Apps & Surfaces', 'GEOX MCP Apps: welldesk, seismic vision, earth volume, judge console.', lambda fp: fp.startswith('apps/') or '/geox-gui/' in fp or fp.startswith('geox-gui/')),
    ('apps-well-desk', '💎 Apps: Well Desk', 'Well Desk front-end (React/JS).', lambda fp: fp.startswith('apps/well-desk/')),
    ('core-basin', '🛢️ Core: Basin Analysis', 'Basin profiling, subsidence, source rocks, deep time, tectonics.', lambda fp: any(s in fp for s in ('basin', 'subsidence', 'backstrip', 'source_rock', 'deep_time', 'paleobiodb', 'tecton'))),
    ('core-seismic', '🌊 Core: Seismic & Geophysics', 'Seismic interpretation, AVO, well ties, geomechanics.', lambda fp: any(s in fp for s in ('seismic', 'avo', 'geomechanic', 'stress_polygon', 'glof'))),
    ('core-petrophysics', '⛏️ Core: Petrophysics', 'LAS ingest, Vsh/porosity/Sw, Archie, LEM, well QC.', lambda fp: any(s in fp for s in ('petrophysic', 'well_qc', 'well_ingest', 'archie', 'porosity', 'perm_'))),
    ('core-claim', '📜 Core: Claims & Evidence', 'Claim lifecycle, falsification, evidence ingestion.', lambda fp: any(s in fp for s in ('claim', 'evidence', 'falsif', 'contradict'))),
    ('core-map', '🗺️ Core: Mapping & Spatial', 'Geological maps, scene planning, spatial indexing (H3, LanceDB, STAC).', lambda fp: any(s in fp for s in ('/map/', 'spatial', 'h3_index', 'lancedb', 'stac_', 'scene_plan'))),
    ('core-model', '🪨 Core: Geological Models', 'Subsurface modeling, GemPy 3D, geological_generate.', lambda fp: any(s in fp for s in ('/model/', 'gempy', 'geological_gen'))),
    ('core-wealth', '💰 Core: Capital (WEALTH)', 'Wealth organ computation: NPV, IRR, EMV, Kelly, Markowitz.', lambda fp: '/wealth/' in fp or 'capital_' in fp),
    ('core-well', '🩺 Core: WELL Vitality', 'Vit organ: homeostasis, dignity, fatigue, reliability.', lambda fp: '/well/' in fp or 'well_assess' in fp or 'well_' in fp.lower()),
    ('ingest', '📥 Ingest & Loaders', 'Data ingestion pipelines, loaders, normalization.', lambda fp: fp.startswith('ingest/') or '/ingest/' in fp),
    ('tools-utilities', '🔧 Tools & Utilities', 'Helper modules, schemas, validators, common utilities.', lambda fp: '/tools/' in fp or '/utils/' in fp or '/common/' in fp or fp.startswith('geox/utils')),
    ('schema-contracts', '📐 Schemas & Contracts', 'JSON Schema, Pydantic models, API contracts, MCP envelopes.', lambda fp: fp.startswith('schemas/') or fp.startswith('contracts/') or fp.startswith('compatibility/')),
    ('fixtures-data', '🧪 Fixtures & Demo Data', 'Synthetic fixtures, demo basins, test data, macroscale datasets.', lambda fp: fp.startswith('fixtures/') or fp.startswith('data/')),
    ('infra-cicd', '⚙️ Infrastructure & CI/CD', 'Docker, docker-compose, GitHub Actions, deployment manifests.', lambda fp: fp.startswith('.github/') or fp.startswith('infra/') or 'Dockerfile' in fp or 'docker-compose' in fp or fp.startswith('ops/')),
    ('config-build', '🔨 Config & Build', 'Build configs (Makefile, pyproject), lint, type-check, package metadata.', lambda fp: fp.startswith('config/') or fp in ('Makefile', 'docker-compose.yml', 'docker-compose.dev.yml') or fp.startswith('scripts/')),
    ('identity-security', '🔐 Identity & Security', 'Auth, OAuth, secrets, identity files.', lambda fp: fp.startswith('oauth/') or fp.startswith('allowed_signers') or 'identity.toml' in fp or '/security' in fp.lower() or '/auth/' in fp),
    ('well-timeseries', '📈 Well Timeseries', 'Well production timeseries, decline curves, RRR.', lambda fp: 'geox_timeseries' in fp or '/decline' in fp),
    ('output-artifacts', '📤 Outputs & Artifacts', 'Generated outputs, artifacts, plots.', lambda fp: fp.startswith('outputs/') or fp.startswith('artifacts/')),
    ('docs-architecture', '📚 Docs: Architecture & Contracts', 'Architecture, FEDERATION contracts, integration guides.', lambda fp: fp.startswith('docs/ARCHITECTURE') or '/FEDERATION' in fp or 'FEDERATION' in fp or 'CONTRACT' in fp or fp.startswith('docs/INTEGRATION')),
    ('docs-runbook', '📖 Docs: Runbooks & Guides', 'Operational runbooks, GEOX-specific guides.', lambda fp: fp.startswith('docs/') and ('RUNBOOK' in fp.upper() or 'GUIDE' in fp.upper() or 'BLUEPRINT' in fp.upper() or 'DOCTRINE' in fp.upper())),
    ('docs-capability', '🧭 Docs: Capability & Maps', 'Capability maps, context maps, blueprint docs.', lambda fp: fp.startswith('docs/') and ('CAPABILITY' in fp.upper() or 'MAP' in fp.upper() or 'CONTEXT' in fp.upper())),
    ('docs-meta', '📜 Docs: Meta & Changelog', 'Changelog, contributing, code of conduct, license.', lambda fp: fp.startswith('docs/') and any(s in fp.upper() for s in ('CHANGELOG', 'CONTRIBUTING', 'CODE_OF_CONDUCT', 'NOTICE', 'LICENSE'))),
    ('docs-general', '📚 Docs: General', 'Other documentation.', lambda fp: fp.startswith('docs/')),
    ('okf-baseline', '🪶 OKF: Sabah Baseline', 'OKF (Ocean-Knowledge-Fabric) Sabah baseline data.', lambda fp: fp.startswith('okf/')),
    ('other', '📦 Other', 'Miscellaneous or top-level files.', lambda fp: True),
]

# Apply layer rules (first match wins)
node_to_layer = {}
unmatched = []
for n in file_nodes:
    fp = n['filePath']
    assigned = False
    for layer_id, layer_name, layer_desc, rule in LAYER_RULES[:-1]:  # exclude 'other' for first pass
        if rule(fp):
            node_to_layer[n['id']] = layer_id
            assigned = True
            break
    if not assigned:
        node_to_layer[n['id']] = 'other'
        unmatched.append(fp)

print(f"Unmatched (assigned to 'other'): {len(unmatched)}")
if unmatched[:5]:
    print(f"  Examples: {unmatched[:5]}")

# Build layers array
layer_node_map = defaultdict(list)
for n in file_nodes:
    layer_node_map[node_to_layer[n['id']]].append(n['id'])

layers = []
for layer_id, layer_name, layer_desc, _ in LAYER_RULES:
    if layer_node_map.get(layer_id):
        layers.append({
            'id': f'layer:{layer_id}',
            'name': layer_name,
            'description': layer_desc,
            'nodeIds': sorted(layer_node_map[layer_id]),
        })

print(f"\nLayers: {len(layers)}")
for l in layers:
    print(f"  {l['id']}: {len(l['nodeIds'])} files")

# Save layers.json
with open(f'{UA_DIR}/intermediate/layers.json', 'w') as f:
    json.dump(layers, f, indent=2)

print(f"\nWrote {UA_DIR}/intermediate/layers.json")
