#!/usr/bin/env python3
"""Phase 5: Deterministic tour based on entry points and major sections."""

import json

UA_DIR = "/root/GEOX/.ua"
PROJECT_ROOT = "/root/GEOX"

with open(f"{UA_DIR}/intermediate/assembled-graph.json") as f:
    g = json.load(f)
with open(f"{UA_DIR}/intermediate/layers.json") as f:
    layers = json.load(f)

node_by_id = {n["id"]: n for n in g["nodes"]}

# Tour steps — structured narrative for the GEOX codebase
TOUR_STEPS = [
    {
        "order": 1,
        "title": "Project Overview",
        "description": "GEOX — Earth Intelligence Engine. Physics-grounded geological intelligence for exploration, hazard assessment, and earth science. Authority 555_COMPUTE_ONLY, lives at 127.0.0.1:8081.",
        "nodeIds": ["document:README.md", "document:FEDERATION.md", "document:CLAUDE.md"],
    },
    {
        "order": 2,
        "title": "Federation Contract",
        "description": "How GEOX plugs into the arifOS federation: what it computes, what it refuses, and the constitutional floors it obeys.",
        "nodeIds": ["document:FEDERATION_CONTRACT.md", "document:PROTOCOL_CONFORMANCE.md", "document:FEDERATION_MAP.md"],
    },
    {
        "order": 3,
        "title": "Canonical Surface (Live MCP)",
        "description": "The live public MCP surface: 26 canonical tools, ghost tracking, authority ceiling. The truth is :8081/health, not prose.",
        "nodeIds": ["config:CANONICAL_PUBLIC_SURFACE.json", "config:GEOX_MCP_APPS_SURFACE.json", "config:organ.yaml"],
    },
    {
        "order": 4,
        "title": "MCP Apps — The User Surfaces",
        "description": "Twelve MCP apps render GEOX evidence for humans: well-desk (petrophysics), seismic-vision, earth-volume, judge-console, geoprobe.",
        "nodeIds": [
            "file:apps/1_welldesk.py",
            "file:apps/2_seismic_vision.py",
            "file:apps/3_earth_volume.py",
            "file:apps/4_judge_console.py",
            "file:apps/5_geoprobe.py",
        ],
    },
    {
        "order": 5,
        "title": "Well Desk Front-End (React/JS)",
        "description": "The Well Desk React app: physics modules (Gassmann, VpVsRho, Archie), tracks, multi-panel correlation. Bridges to MCP via MCPBridge.js.",
        "nodeIds": ["file:apps/well-desk/src/bridge/MCPBridge.js"],
    },
    {
        "order": 6,
        "title": "Core: Basin Analysis",
        "description": "Basin profiling, subsidence backstripping, source rock maturity, tectonic reconstruction, Macrostrat evidence, paleobiology.",
        "nodeIds": [],
    },
    {
        "order": 7,
        "title": "Core: Seismic & Geophysics",
        "description": "SEG-Y ingest, horizon picking, AVO forward (Zoeppritz/Shuey/LMR/Castagna), fault sticks, contrast metabolize, geomechanics.",
        "nodeIds": [],
    },
    {
        "order": 8,
        "title": "Core: Petrophysics",
        "description": "LAS ingest, Vsh/porosity/Sw via Archie & SIMANDOUX, net-pay, LEM inference, well QC (depth monotonicity, physical range).",
        "nodeIds": [],
    },
    {
        "order": 9,
        "title": "Core: Claims & Falsification",
        "description": "Popperian claim lifecycle: create → validate → challenge → falsify → seal. Every claim carries truth class (OBS/DER/INT/SPEC) and uncertainty P10/P50/P90.",
        "nodeIds": [],
    },
    {
        "order": 10,
        "title": "Core: Mapping & 3D Models",
        "description": "Geological maps (scene_plan), spatial indexing (H3, LanceDB, STAC), 2D cross-sections, GemPy 3D implicit modeling.",
        "nodeIds": [],
    },
    {
        "order": 11,
        "title": "Cross-Organ Bridges",
        "description": "How GEOX reaches WEALTH (NPV/EMV/Kelly) and WELL (homeostasis/dignity). Bridges route through arifOS, never mutate production state directly.",
        "nodeIds": [],
    },
    {
        "order": 12,
        "title": "Infrastructure & Deployment",
        "description": "Docker, docker-compose, systemd unit (geox-mcp.service), ops scripts, GitHub Actions CI/CD, security/identity config.",
        "nodeIds": ["service:Dockerfile", "service:Dockerfile.local", "service:docker-compose.yml"],
    },
    {
        "order": 13,
        "title": "Schemas, Contracts & Identity",
        "description": "JSON Schemas, Pydantic models, MCP envelopes, OAuth, identity.toml, capability registry, contract tests.",
        "nodeIds": [],
    },
    {
        "order": 14,
        "title": "OKF — Sabah Baseline",
        "description": "Ocean-Knowledge-Fabric Sabah basin baseline: ingest templates, fixtures, evidence packs for reproducible demos.",
        "nodeIds": [],
    },
]


# Populate nodeIds by querying layer data
def find_nodes_in_layer(layer_id, prefix=None):
    for layer in layers:
        if layer["id"] == layer_id:
            ids = layer["nodeIds"]
            if prefix:
                ids = [i for i in ids if i.startswith(prefix)]
            return ids[:6]
    return []


# Fill in steps 6-11 from layer data
TOUR_STEPS[5]["nodeIds"] = find_nodes_in_layer("layer:core-basin")
TOUR_STEPS[6]["nodeIds"] = find_nodes_in_layer("layer:core-seismic")
TOUR_STEPS[7]["nodeIds"] = find_nodes_in_layer("layer:core-petrophysics")
TOUR_STEPS[8]["nodeIds"] = find_nodes_in_layer("layer:core-claim")
TOUR_STEPS[9]["nodeIds"] = find_nodes_in_layer("layer:core-map") + find_nodes_in_layer("layer:core-model")
TOUR_STEPS[10]["nodeIds"] = find_nodes_in_layer("layer:core-wealth") + find_nodes_in_layer("layer:core-well")
TOUR_STEPS[12]["nodeIds"] = find_nodes_in_layer("layer:schema-contracts") + find_nodes_in_layer("layer:identity-security")
TOUR_STEPS[13]["nodeIds"] = find_nodes_in_layer("layer:okf-baseline")

# Drop empty steps
final_steps = []
for s in TOUR_STEPS:
    if s["nodeIds"]:
        final_steps.append(s)

print(f"Tour steps: {len(final_steps)}")

# Validate node IDs exist
node_ids = set(node_by_id.keys())
missing = []
for s in final_steps:
    for nid in s["nodeIds"]:
        if nid not in node_ids:
            missing.append((s["order"], nid))

print(f"Missing node IDs in tour: {len(missing)}")
if missing[:5]:
    print(f"  Examples: {missing[:5]}")
    # Drop missing IDs
    for s in final_steps:
        s["nodeIds"] = [nid for nid in s["nodeIds"] if nid in node_ids]

with open(f"{UA_DIR}/intermediate/tour.json", "w") as f:
    json.dump(final_steps, f, indent=2)

print(f"Wrote {UA_DIR}/intermediate/tour.json")
