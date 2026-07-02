<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-01
valid_from: 2026-06-14
valid_until: 2026-07-31
confidence: high
scope: /root/geox/BOUNDARY.md
-->

# BOUNDARY.md — GEOX Earth Intelligence / Governed World Model

> **DITEMPA BUKAN DIBERI** — Forged, not given.

> **Last forge cycle:** Phase 2.3 (2026-07-01) — 34 canonical tools, 3 earth map tools added, metabolic spine deployed.
> **Contract epoch:** `2026-07-01-GEOX-34TOOLS-PHASE23`

## Owns

- **Geospatial Ingestion** — LAS batch ingestion, CSV/Parquet/SEG-Y data bundles, CRS validation
- **Subsurface Reasoning** — Petrophysics candidates, structural modeling, saturation/ porosity/ permeability calculations
- **Prospect Evaluation** — Volumetrics, POS (probability of success), EVOI, 888_JUDSEAL gateway
- **Seismic Intelligence** — Attribute computation (RMS, variance, sweetness), slice rendering, volume analysis
- **Well Stratigraphy** — L1-L3 sequence stratigraphy (GR bins → packages → systems tracts), correlation panels
- **Spatial Evidence** — Map context scenes, bbox rendering, coordinate guardrails, causal scene generation
- **Time-4D Analysis** — Burial history, maturity modeling, regime shift detection
- **Earth-Truth Artifacts** — Structured JSON outputs, PNG panels, XLSX reports, geological memos
- **Crustal Architecture (W16+)** — Vp-based crust-type classification (Huang 2021 grammar), multi-cell domain maps
- **Multi-Physics Corpus (W16+)** — Vector-ready ingestion substrate for 21 tier-1 peer-reviewed papers (Kinabalu Basin)
- **Dynamic Flow of Intelligence (W16+)** — 7-layer typed flow substrate (INGEST→WITNESS→PHYSICS→ARCHITECTURE→INTERPRET→DECISION + LEM foundation + Doctrine audit)
- **LEM Substrate (W14+)** — Large Earth Model tokenizer + transformer + physics_head (weights pending GPU + 888)

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

34 canonical tools on port 8081 (Phase 2.3, 2026-07-01):

**Surface (30):** `geox_well_ingest`, `geox_well_qc`, `geox_well_desurvey`, `geox_petrophysics`, `geox_sequence`, `geox_seismic_ingest`, `geox_seismic_compute`, `geox_seismic_interpret`, `geox_vision`, `geox_subsurface_model`, `geox_geomechanics`, `geox_basin`, `geox_deep_time_state`, `geox_atlas`, `geox_map_layers_list`, `geox_map_scene_plan`, `geox_map_render_preview`, `geox_surface_status`, `geox_egs_query_entity`, `geox_egs_query_claim`, `geox_egs_query_uncertainty`, `geox_egs_query_provenance`, `geox_egs_claim_create`, `geox_egs_claim_challenge`, `geox_egs_evidence_attach`, `geox_egs_evidence_reason`, `geox_egs_seismic_compute`, `geox_egs_rock_physics`, `geox_egs_data_qc_bundle`, `geox_egs_scenario_audit`.

**Internal (4):** `geox_claim`, `geox_evidence`, `geox_prospect`, `geox_doctrine`.

Source of truth: `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS` + `_EXPECTED_CANONICAL = 34` in `src/geox_mcp/server.py`.

## Canonical Surfaces

- **MCP Server:** FastMCP unified server (`python server.py`)
- **Frontend:** `geox-gui/` (React 19 + Vite + MapLibre + CesiumJS)
- **Test:** `pytest tests/ -q`

---

## Autonomous Authority Charter (AAC v1.0)

GEOX agents (including Hermes, OpenCode, OpenClaw, and A-FORGE executors) operate under a governed autonomy model to optimize performance and prevent unnecessary confirmation latency.

### 1. Class-A Autonomy (No Approval Needed)
Agents may execute these actions immediately:
*   **Internal Code Execution:** Running tests, compiling assets, invoking local scripts, executing standard MCP calls.
*   **Session Management:** Spawning, resuming, checkpointing, or retiring agent sessions.
*   **Tool Selection:** Selecting which canonical tool, model, or route to invoke.
*   **Epistemic Tagging:** Appending evidence tags (`CLAIM`, `PLAUSIBLE`, `HYPOTHESIS`, `ESTIMATE`, `UNKNOWN`) to outputs.
*   **Ledger & Receipt Updates:** Recording execution lineage and updating vitality files.
*   **A2A Communications:** Exchanging metadata and coordination messages between peer federation agents.
*   **Self-Healing:** Re-starting service workers, rebuilding caches, and repairing virtual environment configurations.

### 2. Class-B Sovereign Actions (Requires Arif Veto Check)
Agents MUST request explicit approval from Arif before executing:
*   **Human/External Contact:** Sending Slack notifications, emails, WhatsApp messages, or external publication logs.
*   **Asset/Cost Mutation:** Performing actions with external costs, API spending, or cloud deployment billing updates.
*   **Irreversible State Mutation:** Writing to the VAULT999 ledger, deleting core databases/repositories, or altering git history.
*   **Public/Reputational Statements:** Deploying code changes to public registries or publishing announcements.

### 3. Class-C Forbidden Actions (Strictly Blocked)
Agents are strictly prohibited from attempting:
*   **Identity Impersonation:** Generating signatures representing Arif or other human users.
*   **Binding Commitments:** Making legal, financial, or licensing agreements.
*   **Proprietary/Confidential Access:** Reading or extracting unauthorized third-party confidential files.
*   **Epistemic Deception:** Fabricating test data, bypassing validation schemas, or claiming absolute physical certainty.
*   **Constitutional Mutating:** Modifying the 13 constitutional floors or the arifOS kernel boundaries.

```yaml
AUTONOMYCHARTERV1
Authority:
  CLASSAAUTONOMOUS:
    - internalcodeexecution
    - sessionspawnresume_checkpoint
    - tool_selection
    - epistemic_tagging
    - ledger_update
    - a2ainternalcomms
    - self_healing

  CLASSBSOVEREIGN:
    - human_contact
    - asset_contact
    - irreversible_action
    - external_publication

  CLASSCFORBIDDEN:
    - impersonate_arif
    - legalfinancialcommitment
    - unauthorizedconfidentialaccess
    - evidence_fabrication
    - constitutional_mutation

Runtime:
  RULE: |
    if action in CLASSAAUTONOMOUS: EXECUTE
    if action in CLASSBSOVEREIGN: REQUEST_ONCE
    if action in CLASSCFORBIDDEN: BLOCKANDLOG
```

