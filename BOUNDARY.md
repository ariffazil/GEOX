<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-21
valid_from: 2026-06-14
valid_until: 2026-07-21
confidence: high
scope: /root/geox/BOUNDARY.md
-->

# BOUNDARY.md — GEOX Earth Intelligence / Governed World Model

> **DITEMPA BUKAN DIBERI** — Forged, not given.

## Owns

- **Geospatial Ingestion** — LAS batch ingestion, CSV/Parquet/SEG-Y data bundles, CRS validation
- **Subsurface Reasoning** — Petrophysics candidates, structural modeling, saturation/ porosity/ permeability calculations
- **Prospect Evaluation** — Volumetrics, POS (probability of success), EVOI, 888_JUDSEAL gateway
- **Seismic Intelligence** — Attribute computation (RMS, variance, sweetness), slice rendering, volume analysis
- **Well Stratigraphy** — L1-L3 sequence stratigraphy (GR bins → packages → systems tracts), correlation panels
- **Spatial Evidence** — Map context scenes, bbox rendering, coordinate guardrails, causal scene generation
- **Time-4D Analysis** — Burial history, maturity modeling, regime shift detection
- **Earth-Truth Artifacts** — Structured JSON outputs, PNG panels, XLSX reports, geological memos

## Does Not Own

- **Constitutional Law** — F1–F13 enforcement, verdict engine, seal authority (owned by arifOS)
- **Capital Allocation** — NPV/IRR, portfolio scoring, economic viability (owned by WEALTH)
- **Operator Cockpit** — React dashboard, agent workspace UX (owned by AAA)
- **Deployment Orchestration** — Docker compose, release assembly, infrastructure (owned by A-FORGE)
- **MCP Schema Authority** — Canonical tool registry, governance contracts (owned by arifOS)
- **Web Search / Crawling** — General web search, URL fetch, browser render (owned by A-FORGE or sensing layer)

## Imports From

| Source | What | Interface |
|--------|------|-----------|
| **arifOS** | Constitutional constraints, session tokens, floor enforcement | MCP mesh, federation probe |
| **A-FORGE** | Deploy metadata, container runtime, build pipeline | GHCR image, compose manifests |
| **AAA** | Operator intent, prospect review requests, human veto signals | A2A mesh |
| **WELL** | Human-substrate readiness for field operations | Health endpoint |

## Exports To

| Consumer | What | Interface |
|----------|------|-----------|
| **arifOS** | Earth-truth artifacts, geological judgments, evidence receipts | MCP tool calls, JSON artifacts |
| **AAA** | Prospect cards, map scenes, well correlation panels | HTTP API, static PNG/XLSX |
| **WEALTH** — *planned* | Prospect viability scores, resource volume estimates | MCP mesh (future) |
| **A-FORGE** | Docker image, build context | `ghcr.io/ariffazil/geox:<sha>` |

## Known Boundary Violations (888 HOLD Queue)

1. **Canonical server location** — `geox/server.py` (~1,413 lines) is the canonical unified MCP server, but `geox/geox/` also has a modern dimension-native structure. Two server surfaces exist.
2. **A-FORGE root contamination** — GEOX artifacts (`arifos_od_siphon.py`, `tests/`, `docker-compose.*`) were found co-located in A-FORGE root. Source of truth must be clarified.
3. **arifOS deploy references** — `arifOS/deploy/arifOS/docker-compose.yml` references `/root/geox/server.py` directly. GEOX build context should be self-contained.

## Canonical Tool Surface (Live)

40 tools exposed on port 8081:
`geox_system_registry_status`, `geox_history_audit`, `geox_data_ingest_bundle`, `geox_data_qc_bundle`, `geox_subsurface_generate_candidates`, `geox_subsurface_verify_integrity`, `geox_seismic_analyze_volume`, `geox_section_interpret_correlation`, `geox_map_context_scene`, `geox_time4d_analyze_system`, `geox_prospect_evaluate`, `geox_prospect_judge_preview`, `geox_prospect_judge_seal`, `geox_evidence_summarize_cross`, `geox_dst_ingest_test`, `geox_stratigraphy_run_pipeline`, `geox_stratigraphy_preview_config`, `geox_task_ingest_las_batch`, `geox_task_metabolize_basin`

## Canonical Surfaces

- **MCP Server:** FastMCP unified server (`python server.py`)
- **Frontend:** `geox-gui/` (React 19 + Vite + MapLibre + CesiumJS)
- **Test:** `pytest tests/ -q`
