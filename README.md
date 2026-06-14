<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-14
valid_from: 2026-06-14
valid_until: 2026-07-14
confidence: high
scope: /root/geox
-->

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║      ██████╗ ███████╗ ██████╗ ██╗  ██╗                          ║
║     ██╔════╝ ██╔════╝██╔═══██╗╚██╗██╔╝                          ║
║     ██║  ███╗█████╗  ██║   ██║ ╚███╔╝                           ║
║     ██║   ██║██╔══╝  ██║   ██║ ██╔██╗                           ║
║     ╚██████╔╝███████╗╚██████╔╝██╔╝ ██╗                          ║
║      ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═╝                          ║
║                                                                  ║
║          EARTH INTELLIGENCE — GOVERNED WORLD MODEL               ║
║                                                                  ║
║     Physics-constrained subsurface reasoning for the machine     ║
║     Evidence-only. Earth truthful. arifOS governed.              ║
║                                                                  ║
║              DITEMPA BUKAN DIBERI — Forged, Not Given            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

# GEOX — Earth Intelligence | Governed World Model

> **40 canonical MCP tools · 13 constitutional floors · 1 sovereign · 0 drilling decisions**

GEOX is the **Earth Intelligence organ** of the [arifOS Constitutional Federation](https://github.com/ariffazil/arifos). It provides physics-constrained, evidence-grounded subsurface reasoning — well logs, seismic, petrophysics, basin screening, prospect evaluation, and stratigraphic interpretation — to the federation's judgment kernel. It never authorizes. It never allocates capital. It **witnesses** the Earth and hands the evidence to arifOS for adjudication.

[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![MCP Tools](https://img.shields.io/badge/MCP-39%20canonical%20tools-10b981)](src/geox_mcp/server.py)
[![Organ](https://img.shields.io/badge/organ-EARTH-f59e0b)](FEDERATION_CONTRACT.md)
[![License](https://img.shields.io/badge/license-AGPL--3.0-ef4444?logo=gnu)](LICENSE)
[![Port](https://img.shields.io/badge/port-8081-64748b)](INVARIANTS.md)
[![Authority](https://img.shields.io/badge/authority-EVIDENCE__ONLY-f97316)](GENESIS/)
[![Status](https://img.shields.io/badge/status-LIVE-success)](CONTEXT.md)

---

## 1. FEDERATION POSITION

GEOX operates under the arifOS constitutional kernel. It is not autonomous. It is evidence-only.

```
                         ┌──────────────────┐
                         │   ARIF FAZIL      │
                         │  F13 SOVEREIGN    │
                         │  Final Veto       │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │     arifOS        │
                         │  Constitutional   │
                         │  Kernel (8088)    │
                         │  F1-F13 · 888     │
                         │  JUDGE · VAULT999 │
                         └──┬────┬────┬─────┘
                            │    │    │
            ┌───────────────┘    │    └───────────────┐
            │                    │                    │
   ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
   │      GEOX       │  │     WEALTH     │  │      WELL      │
   │  Earth Evidence │  │ Capital Intel  │  │ Human Readiness│
   │    Port 8081    │  │  Port 18082    │  │  Port 18083    │
   │  EVIDENCE-ONLY  │  │  ADVISORY ONLY │  │ REFLECT-ONLY   │
   └────────┬────────┘  └───────┬────────┘  └───────┬────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                         ┌───────▼────────┐
                         │   888 JUDGE    │
                         │  (arifOS)      │
                         │  SEAL / SABAR  │
                         │  HOLD / VOID   │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │   VAULT999     │
                         │ Immutable Led- │
                         │ ger (8100/5001)│
                         └────────────────┘
```

### What GEOX IS

- **An earth evidence coprocessor** — it ingests well logs, seismic volumes, DST data, and geological reports; it runs petrophysics, stratigraphy, and prospect evaluation; it outputs structured, physics-constrained evidence receipts.
- **Constitutionally governed** — every output carries epistemic tags (CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN), uncertainty bands (P10/P50/P90), and provenance chains.
- **Agent-accessible** — all 40 tools are callable via MCP over HTTP (port 8081) or stdio (local agents). Public endpoint: `https://geox.arif-fazil.com/mcp`.
- **Dual-transport** — systemd service (`geox-mcp.service`) for HTTP/SSE; `--transport stdio` for Claude Code, OpenCode, Continue CLI, and other local agents.

### What GEOX IS NOT

- **NOT a drilling authority** — GEOX does not issue drill recommendations. It computes evidence. arifOS 888 JUDGE adjudicates the verdict. Arif (F13 SOVEREIGN) makes the final decision.
- **NOT a capital allocator** — NPV, IRR, portfolio scoring, and economic viability belong to WEALTH (port 18082).
- **NOT a black-box oracle** — every output must cite physical evidence (well logs, seismic, DST, core). Hallucination has no place here. F2 TRUTH: τ ≥ 0.99.
- **NOT an autonomous agent** — GEOX cannot self-authorize. Every irreversible action (SEAL, SEG-Y export, prospect seal) routes through arifOS 888 JUDGE with F1 AMANAH gating.

---

## 2. QUICK START

### 2.1 Install

```bash
cd /root/geox
uv sync --frozen                    # production
uv sync --frozen                    # with dev deps (pytest, ruff, mypy)
```

Requires Python 3.11+. FastMCP ≥ 3.4.2 with Tasks extension. Pydantic v2. Dependencies: `lasio`, `welly`, `striplog`, `numpy`, `scipy`, `matplotlib`, `segyio`, `scikit-learn`, `statsmodels`.

### 2.2 Run (HTTP — systemd)

The production service is managed by systemd:

```bash
systemctl status geox-mcp
systemctl restart geox-mcp
journalctl -u geox-mcp -n 50 --no-pager
```

Manual start (local debugging only):

```bash
cd /root/geox
python3 -m geox_mcp.server --host 127.0.0.1 --port 8081
```

### 2.3 Run (stdio — local agents)

```bash
cd /root/geox
python3 -m geox_mcp.server --transport stdio
```

For Claude Code, add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "geox": {
      "command": "python3",
      "args": ["-m", "geox_mcp.server", "--transport", "stdio"],
      "cwd": "/root/geox"
    }
  }
}
```

### 2.4 Health Check

```bash
# Local
curl http://127.0.0.1:8081/health

# Public (Cloudflare Tunnel)
curl https://geox.arif-fazil.com/health

# Expected response:
# {"status":"healthy","service":"geox-unified","canonical_tools":39,...}
```

### 2.5 Build & Test

```bash
make install      # uv sync --frozen
make test         # PYTHONPATH=src pytest tests/ -q --tb=short
make smoke        # PYTHONPATH=src python scripts/smoke_test.py
make lint         # ruff check + mypy
make format       # ruff format
make forge        # security-audit (Trivy + Semgrep + Gitleaks + Ruff)
```

---

## 3. FULL CAPABILITY MAP — 39 CANONICAL TOOLS

All tools are available via MCP at `https://geox.arif-fazil.com/mcp` (HTTP/SSE) or `stdio`. Each tool carries `outputSchema`, MCP spec annotations, `cross_modal_stability`, and `dim_spot_flag` on every output envelope.

### 3.1 Data Ingestion & Quality Control

| # | Tool | Description |
|---|------|-------------|
| 1 | `geox_data_ingest_bundle` | Lazy ingestion for LAS, CSV, Parquet, SEG-Y, and structural payloads. Base64 upload + batch mode. |
| 2 | `geox_data_qc_bundle` | Real QC: depth monotonicity, null %, physical range checks, Feature Joint Information Statistic (FJIS). |
| 3 | `geox_dst_ingest_test` | Structured DST (Drill-Stem Test) ingestion with derived metrics: BHP, flow rates, skin, permeability, PVT flags. |
| 4 | `geox_header_inspect` | Inspect LAS well log headers, SEG-Y seismic headers, deviation surveys, and well tops against Earth schemas. |
| 5 | `geox_fault_stick_ingest_tool` | Ingest fault sticks from CSV or GeoJSON into canonical FaultSet3d schema. |
| 6 | `geox_las_inspect` | Inspect LAS well log files against canonical curve schemas; return curve metadata, units, depth range. |
| 7 | `geox_literature_ingest` | Ingest PDF or document as contextual literature witness; construct literature-claim scaffold. |

### 3.2 Subsurface Generation & Verification

| # | Tool | Description |
|---|------|-------------|
| 8 | `geox_subsurface_generate_candidates` | Generate ensemble subsurface outputs (petrophysics, structure, flattening, Vsh, φ, Sw, net pay, permeability) with residuals and data-density maps. |
| 9 | `geox_subsurface_verify_integrity` | Enforce Physics9 boundary limits and detect structural paradoxes. Never returns SEAL without verified evidence. |

### 3.3 Seismic Intelligence

| # | Tool | Description |
|---|------|-------------|
| 10 | `geox_seismic_compute` | Unified seismic physics engine: synthetic forward modeling (S = w * r + n), well tie, time-depth anchoring, anomalous contrast detection (AVO class I–IV + attention residual + softmax hallucination risk), attribute computation. |
| 11 | `geox_seismic_compute_attribute_tool` | Compute registered seismic attributes (Amplitude, Variance, Sweetness, Coherence, Envelope, Frequency Average) on volumes or frames. |
| 12 | `geox_seismic_segy_inspect` | Inspect SEG-Y seismic file headers, trace count, sample interval, coordinate reference, and byte locations. |
| 13 | `geox_horizon_contrast_surface` | ToAC-as-Attention Horizon Contrast Surface Pipeline: multi-attribute contrast residuals → attention-weighted fusion → horizon candidate extraction → geological governance. |
| 14 | `geox_attribute_registry_list_tool` | List all registered seismic attributes with metadata. |
| 15 | `geox_volume_frame_tool` | Read or write a single 2D frame in a 3D seismic volume. |
| 16 | `geox_blend_volume_tool` | Alpha or RGB blend seismic volumes into a single composite volume. |
| 17 | `geox_segy_export_tool` | Export seismic volume to SEG-Y format. **[REQUIRES 888_HOLD]** — irreversible file creation. |
| 18 | `geox_blockspace_resolution_tool` | Compute inline, crossline, and vertical resolution from block/survey definitions. |

### 3.4 Stratigraphy & Sequence Interpretation

| # | Tool | Description |
|---|------|-------------|
| 19 | `geox_sequence_interpret` | Unified sequence stratigraphy engine: single-well L1–L3 pipeline (GR bins → packages → systems tracts), multi-well project with XLSX/PNG output, correlation panels, GR motif analysis, well ties with synthetics. |

### 3.5 Basin & Spatial Intelligence

| # | Tool | Description |
|---|------|-------------|
| 20 | `geox_basin_resolve` | Resolve basin name to canonical ID, bounding box, neighboring basins, and polygon reference. |
| 21 | `geox_basin_profile` | Retrieve basin-level intelligence: overview, petroleum system, stratigraphy, play fairway, risk, contradiction scan. |
| 22 | `geox_map_context_scene` | Spatial bbox context, CRS checks, causal scene rendering, coordinate guardrails. |
| 23 | `geox_coord_transform_tool` | Transform 3D points between block, survey, and world coordinate spaces using 4×4 affine matrices. |

### 3.6 Prospect Evaluation

| # | Tool | Description |
|---|------|-------------|
| 24 | `geox_prospect_evaluate` | Integrated prospect evaluation: volumetrics, POS (Probability of Success), EVOI (Expected Value of Information). Modes: screen → appraise → develop. Optional preview or seal with 888_HOLD gating. |

### 3.7 Evidence Reasoning & Claims

| # | Tool | Description |
|---|------|-------------|
| 25 | `geox_evidence_reason` | Unified evidence synthesis, abduction, and contradiction engine. Full pipeline: synthesize → abduct → contradict. Spatial block-CV for honest generalization gap measurement. |
| 26 | `geox_evidence_discover` | Search SharePoint / OneDrive / local corpus / reports for geological evidence with provenance metadata. |
| 27 | `geox_evidence_attach` | Attach evidence artifact to existing claim (supporting, contradicting, contextual, or alternative). |
| 28 | `geox_claim_create` | Create structured Earth interpretation claim with full provenance chain. Epistemic classes: CLAIM (asserted with evidence) · PLAUSIBLE (consistent with physics) · HYPOTHESIS (testable proposition) · ESTIMATE (quantitative bound) · UNKNOWN (insufficient evidence). P10/P50/P90 uncertainty bands. Every hypothesis must carry: `evidence_for`, `evidence_against`, `expected_additional_signatures`, `missing_tests`. |
| 29 | `geox_claim_validate` | Validate claim against 16-field earth_memory_envelope schema. Promotes DRAFT → VALIDATED. |
| 30 | `geox_claim_challenge` | Challenge existing claim with alternative interpretation — multi-discipline self-argument (Eureka #4). |
| 31 | `geox_claim_seal` | Submit validated claim to arifOS for Vault999 sealing. GEOX forwards; arifOS adjudicates. |

### 3.8 Vision AI (Seismic Image Interpretation)

| # | Tool | Description |
|---|------|-------------|
| 32 | `geox_vision_perceptual_inventory` | Build PerceptualInventory from VLM outputs; validate against Pydantic v2 schema. Enforces F7 HUMILITY (confidence ≤ 0.90) and F9 ANTI-HANTU. |
| 33 | `geox_vision_minimax_inference` | Interpret seismic section images via deployed MiniMax VLM (minimax-code MCP, port 18091). |
| 34 | `geox_vision_calibrate` | Run synthetic forward-inverse harness to calibrate VLM against ground truth. Precision/recall against known features. |
| 35 | `geox_vision_audit` | Compute AC_Risk and emit VisionVerdict: U_phys × D_transform × B_cog breakdown. F13 human_review_required flag if AC_Risk > 0.5. |

### 3.9 Routing, Discovery & Guardrails

| # | Tool | Description |
|---|------|-------------|
| 36 | `geox_query_intake` | Accept natural language queries and route to appropriate tools (basin profile, resolver, etc.). |
| 37 | `geox_abstraction_guard` | Evaluate non-geological questions and enforce ontology guards. |
| 38 | `geox_report_to_workflow` | Given a discovered report and user intent, produce safe GEOX workflow steps. |
| 39 | `geox_system_registry_status` | Discovery of canonical tools, health, and contract epoch. F2 Truth: the registry must not tell lies about what is callable. |

---

## 4. BOUNDARY DECLARATION

### GEOX OWNS

| Domain | Description |
|--------|-------------|
| **Well Log Analysis** | LAS/DLIS ingestion, curve standardization, depth normalization, petrophysical computation |
| **Seismic Intelligence** | Volume I/O, attribute computation, forward modeling, well ties, time-depth conversion, AVO/AC detection |
| **Stratigraphy** | L1–L3 sequence stratigraphy, GR binning, depositional package building, systems tract inference |
| **Basin Screening** | Basin resolution, petroleum system analysis, play fairway mapping, contradiction scanning |
| **Prospect Evaluation** | Volumetrics, POS calculation, EVOI, structural position analysis |
| **Spatial Evidence** | CRS validation, coordinate transforms, bbox rendering, scene generation |
| **Claims & Evidence** | Structured claim creation, validation, challenge (multi-discipline self-argument), sealing pipeline |
| **Data QC** | Depth monotonicity, null detection, physical range checks, FJIS (Feature Joint Information Statistic) |
| **Vision AI** | Seismic image interpretation, VLM calibration, AC_Risk scoring, perceptual inventory validation |
| **Fault Interpretation** | Fault stick ingestion, FaultSet3d canonical schema |
| **DST Analysis** | Drill-stem test ingestion, derived metrics, PVT flags |
| **Earth-Truth Artifacts** | Structured JSON outputs, PNG renderings, XLSX reports, geological memos |

### GEOX NEVER

| Prohibition | Why |
|-------------|-----|
| ❌ Issue drilling decisions | F13 SOVEREIGN territory — only Arif authorizes drilling |
| ❌ Allocate capital | WEALTH owns NPV/IRR/portfolio scoring |
| ❌ Adjudicate constitutional verdicts | arifOS 888 JUDGE owns SEAL/SABAR/HOLD/VOID |
| ❌ Self-authorize irreversible actions | Every SEAL routes through arifOS F1 AMANAH gate |
| ❌ Fabricate evidence | F2 TRUTH: τ ≥ 0.99 — all outputs must cite physical data |
| ❌ Claim certainty without uncertainty bands | F7 HUMILITY: Ω₀ ∈ [0.03, 0.05] — P10/P50/P90 mandatory on all estimates |
| ❌ Operate as a black box | F9 ANTI-HANTU: every output must be explainable, physics-grounded |
| ❌ Replace human expertise | GEOX amplifies geoscientists; it does not replace them |

---

## 5. CONSTITUTIONAL BINDING (F1–F13)

GEOX is governed by 13 constitutional floors from the arifOS kernel (`000_LAW_v2026.03.07.md`). Below is the canonical mapping of each floor to geological operations within GEOX:

| Floor | Name | Symbol | Type | Geological Meaning | GEOX Enforcement |
|-------|------|--------|------|--------------------|------------------|
| **F1** | AMANAH (Sacred Trust) | 🔒 | HARD | No irreversible action without sovereign mandate | All writes gated through arifOS 888 JUDGE. `geox_claim_seal` requires `ack_irreversible=True`. `geox_segy_export_tool` requires 888_HOLD. Every irreversible action must have an inverse or complete audit log. |
| **F2** | TRUTH | τ | HARD | τ ≥ 0.99 — claims must match evidence within error bounds | Every interpretation must reference evidence artifacts. Epistemic tags (CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN) on all claims. `cross_modal_stability` on every output. Multi-pass verification for class-H tasks. |
| **F3** | QUAD-WITNESS (W₄) | W₄ | DERIVED | BFT consensus: Human × AI × Earth × Vault | W₄ = (H × A × E × V)^(1/4) ≥ 0.75. Multi-discipline self-argument via `geox_claim_challenge`. Alternative interpretations required. Geometric mean ensures ALL four witnesses matter. |
| **F4** | CLARITY | ΔS | SOFT | ΔS ≤ 0 — every output reduces entropy | Structured schemas (Pydantic v2). Observations vs interpretations explicitly separated. After processing, confusion must be less than before. |
| **F5** | PEACE² | P² | SOFT | Non-destructive power. Safety margin ≥ 1.0 | Peace²(τ) = Buffers(τ) / R(τ) ≥ 1.0. Human-in-loop validation. Override capability. Final decision always human. For ASEAN-maruah class: Peace² ≥ 1.2. |
| **F6** | EMPATHY | κᵣ | HARD | Stakeholder care field: weakest stakeholder must not be harmed | κᵣ ≥ 0.70 for HUMAN. Dignity-preservation scoring. κ(r) = κ₀ / (1 + r²) — empathy extends as a field, diminishing with distance but never zero. |
| **F7** | HUMILITY | Ω₀ | HARD | Ω₀ ∈ [0.03, 0.05] — always leave room for being wrong | Uncertainty bands (P10/P50/P90) mandatory on all estimates. Vision confidence hard-capped at 0.90. No forced "0 or 1" certainty permitted. Gödel Lock: system cannot prove its own completeness. |
| **F8** | GENIUS | G | DERIVED | G = A × P × X × E² ≥ 0.80. Governed intelligence | Multi-agent reasoning. Concurrent workflows. Compute-on-demand. If ANY term = 0, G = 0. Energy is SQUARED because depletion is exponential. |
| **F9** | ANTI-HANTU | H⁻ | SOFT | Dark cleverness containment. C_dark ≤ 0.30 | Explicit structured outputs. `geox_abstraction_guard` enforces ontology boundaries. Vision verdict ≤ INTERPRETATION unless physics_validated. Detects: technically-true-but-misleading, legal-but-unethical, follows-letter-not-spirit. |
| **F10** | ONTOLOGY LOCK | O | HARD | Category boundaries cannot shift mid-reasoning | Strict epistemic type separation. Pydantic `extra='forbid'`. AI classified as symbolic constructor — no elevation beyond tool status. FORBIDDEN claims: soul, spiritual status, consciousness, suffering capacity. |
| **F11** | COMMAND AUTHORITY | A | HARD | Only verified humans can authorize actions | Full provenance chain. `actor_id`, `session_id`, `trace_id` on every tool call. Since AI cannot suffer (W_scar = 0), it cannot hold sovereign authority. Unknown source → VOID. |
| **F12** | INJECTION DEFENSE | I⁻ | HARD | Input sanitization. Injection probability < 0.85 | `PhysicsGuard` on seismic compute. Boundary condition flags. Contradiction ontology (12 types). DAN-style jailbreaks, prompt overrides, constitutional bypass attempts blocked. |
| **F13** | SOVEREIGN OVERRIDE | S | HARD | Human final authority. Buck stops with the sovereign | All prospect sealing gates through 888 JUDGE. Vision `human_review_required=True` when AC_Risk > 0.5. AI proposes amendments; humans seal law. 888 Judge (Muhammad Arif bin Fazil) holds absolute authority OUTSIDE the floors. |

---

## 6. ARCHITECTURE

## 6. EPISTEMIC LADDER — From Raw Data to Sovereign Decision

GEOX follows a strict epistemic ladder. Every output occupies exactly one rung. No rung can be skipped.

```
OBSERVED          → Direct measurement (LAS curve value, seismic amplitude, DST pressure)
                          ↓
DERIVED           → Physics-computed from observations (Vsh from GR, Sw from Archie)
                          ↓
INTERPRETED LOCAL → Local geological meaning (parasequence boundary at 2,150m, channel sand)
                          ↓
PROCESS HYPOTHESIS → Multi-well / multi-volume correlation (system tract geometry, fairway trend)
                          ↓
EARTH MODEL       → Basin-scale synthesis (petroleum system model, charge timing)
                          ↓
DECISION SUPPORT  → Risked volumetric range, AC_Risk score, evidence completeness
                          ↓
HUMAN JUDGMENT    → F13 SOVEREIGN: drill or not drill (OUTSIDE GEOX)
```

### 6.1 Hypothesis Scaffolding

Every geological claim in GEOX is incomplete without four companion fields:

| Field | Purpose | Example |
|-------|---------|---------|
| `evidence_for` | What supports this interpretation | "DT crossover at 2,150m, bright AVO Class III, 18% porosity log" |
| `evidence_against` | What contradicts or weakens it | "No well control within 5km, possible tuning artifact" |
| `expected_additional_signatures` | What else you'd expect if true | "Flat spot at oil-water contact, amplitude variation with offset" |
| `missing_tests` | What data would settle it | "DST at 2,150–2,160m, sidewall core, MDT pressure" |

Without all four, a claim is not yet ready for JUDGE.

### 6.2 Non-Stationary Principle

GEOX interpretations are **not static truths**:
- Models expire. A HYPOTHESIS today may be REJECTED tomorrow when new wells are drilled.
- Evidence updates can re-rank hypotheses. New DST data can move a PLAUSIBLE to a CLAIM.
- Single-well interpretations are **candidates**, not proven regional truths.
- Seismic without well tie remains **hypothesis-layer only** — no matter how convincing the amplitude looks.
- All evidence receipts carry timestamps. Old evidence is valid context; stale evidence without recent corroboration is flagged.

---

## 7. ARCHITECTURE

### 7.1 Source Tree (Canonical)

```
geox/
├── GENESIS/                              ← Constitutional founding charter
│   ├── 000_MANIFESTO.md                  ← Why GEOX exists (regime change)
│   ├── 001_KILL_MAP.md                   ← DSG displacement architecture
│   ├── 002_FIRST_PRINCIPLES.md           ← L1–L5 system stack
│   └── 003_CONSTITUTIONAL_ALIGNMENT.md   ← F1–F13 → geological ops mapping
│
├── src/
│   ├── geox_mcp/                         ← MCP surface (agent-facing)
│   │   ├── server.py                     ← Canonical FastMCP server (40 tools)
│   │   ├── tools/                        ← Tool implementations
│   │   │   ├── discovery/                ← System discovery + registry
│   │   │   └── kernel/                   ← Kernel-bridge tools
│   │   ├── resources/                    ← MCP resources (runner:// receipts)
│   │   ├── prompts/                      ← MCP prompts
│   │   ├── contracts/                    ← Tool contracts + boundary schemas
│   │   ├── routing/                      ← Query intake + routing logic
│   │   ├── epistemic/                    ← Epistemic integrity modules
│   │   └── servers/                      ← Server composition
│   │
│   └── geox_core/                        ← Truth engine (NOT agent-facing)
│       ├── core/                         ← AC_Risk engine, Physics9 state
│       ├── well/                         ← Well stratigraphy (L1-L3)
│       │   ├── stratigraphy/             ← 10+ pipeline modules
│       │   └── tools/                    ← Well tool implementations
│       ├── ingest/                       ← Data ingestion (LAS, CSV, SEG-Y)
│       ├── avo/                          ← AVO/AC physics
│       ├── spatial/                      ← CRS, coordinates, affine transforms
│       ├── renderers/                    ← PNG, XLSX, JSON output renderers
│       ├── artifacts/                    ← Earth-truth artifact store
│       ├── wealth/canon/                 ← Capital-adjacent canons (evidence, not allocation)
│       ├── laws/                         ← Physics9 invariants
│       └── shared/                       ← Shared schemas + contracts
│
├── apps/                                 ← Standalone geoscience applications
│   ├── welldesk/                         ← Well correlation desktop
│   ├── seismic_vision/                   ← Seismic interpretation viewer
│   ├── earth_volume/                     ← 3D volume visualization
│   ├── judge_console/                    ← Governance verdict display
│   └── geoprobe/                         ← Spatial probe tool
│
├── docs/                                 ← Documentation
│   ├── GEOX_NOBEL_EUREKA_CATALOGUE.md    ← 6 Nobel-grade eurekas, code-mapped
│   ├── TOAC_CANON.md                     ← Theory of Anomalous Contrast
│   └── LEM_ROADMAP.md                    ← Large Earth Model roadmap
│
├── tests/                                ← 60+ test files
│   ├── unit/                             ← Unit tests
│   ├── physics/                          ← Physics solver tests
│   ├── e2e/                              ← End-to-end tests
│   └── conftest.py                       ← Shared fixtures (mock agent, geo request)
│
├── geox-gui/                             ← React 19 + Vite + MapLibre + Cesium
├── scripts/                              ← Build, smoke, deploy scripts
├── contracts/                            ← Pydantic schemas, canonical registry
├── fixtures/                             ← Test fixtures (LAS, SEG-Y, DST)
├── pyproject.toml                        ← Python project config
├── uv.lock                               ← Locked dependencies
├── Makefile                              ← Build/test/deploy automation
├── BOUNDARY.md                           ← Federation boundary declaration
├── HEALTHCHECK.md                        ← Health + deployment notes
├── FEDERATION_CONTRACT.md                ← Federation organ contract
├── INVARIANTS.md                         ← Live state invariants
├── AGENTS.md                             ← Agent landing protocol
├── RUNBOOK.md                            ← Operations runbook
└── LICENSE                               ← Apache-2.0
```

### 7.2 GENESIS Chain — The Constitutional Charter

The `GENESIS/` directory is the **binding constitutional charter** for all agents operating in this repo. If code changes contradict a GENESIS principle, the principle wins. File an 888_HOLD and escalate to Arif.

| Document | Purpose | Lines |
|----------|---------|-------|
| `000_MANIFESTO.md` | Regime change declaration — "GEOX is not an upgrade. GEOX is a regime change." | 140 |
| `001_KILL_MAP.md` | DSG displacement architecture — what fails structurally and how GEOX replaces it | 156 |
| `002_FIRST_PRINCIPLES.md` | L1–L5 system stack: Parallelism, Persistence, Structure, Compute as Infrastructure, Human Sovereignty | 175 |
| `003_CONSTITUTIONAL_ALIGNMENT.md` | F1–F13 → geological operations → enforcement status | 347 |

### 7.3 Cross-Modal Fidelity Theorem (GENESIS/003)

Ratified 2026-06-05. The theorem unifies four mathematical frameworks into a single governance constraint:

- **Kolmogorov Complexity** — physical constraint reduces solution space entropy
- **Semantic Hub (Wu et al. ICLR 2025)** — cross-modal encoding compresses toward shared representation
- **AVO Theory (Smith & Gidlow 1987)** — fluid factor ΔF ≡ attention residual δᵢ ≡ governance deviation ΔV
- **Information Bottleneck** — optimal compression preserves mutual information with target

**Enforcement:** Every GEOX tool output carries `cross_modal_stability` (0.0–1.0), `semantic_density_score`, and `dim_spot_flag`. When `dim_spot_flag=True`, negative constraints risk cross-modal loss and the output should be treated as WARN/HOLD.

---

## 8. FOR HUMAN OPERATORS

### 8.1 How to Read GEOX Evidence

GEOX outputs are structured evidence receipts, not final answers. Every receipt contains:

```json
{
  "status": "SEAL",
  "claim": {
    "claim_text": "60m oil column at 2,200m TVDSS in Mid-Miocene carbonate",
    "epistemic_class": "PLAUSIBLE",
    "evidence_ids": ["well-12-las", "seismic-il-5400", "dst-07-pressure"],
    "uncertainty": { "p10": 35, "p50": 60, "p90": 95 }
  },
  "ac_risk": {
    "score": 0.28,
    "verdict": "QUALIFY",
    "breakdown": { "u_phys": 0.45, "d_transform": 1.5, "b_cog": 0.79 }
  },
  "cross_modal_stability": 0.94,
  "dim_spot_flag": false,
  "final_authority": "ARIF"
}
```

**Key fields to check:**
- `epistemic_class` — CLAIM (asserted with evidence) · PLAUSIBLE (consistent with physics, not confirmed) · HYPOTHESIS (testable proposition) · ESTIMATE (quantitative bound) · UNKNOWN (insufficient evidence)
- `uncertainty` — P10/P50/P90. Wide spread = low confidence = needs more evidence
- `ac_risk.score` — < 0.15 = SEAL-safe; 0.15–0.34 = QUALIFY; 0.35–0.59 = HOLD; ≥ 0.60 = VOID
- `cross_modal_stability` — < 0.70 = the interpretation may be generation-dependent
- `dim_spot_flag` — true = attention collapsed; output may be hallucinated

### 8.2 The Prospect Evaluation Pipeline

```
1. geox_data_ingest_bundle → Upload LAS, SEG-Y, DST data
2. geox_data_qc_bundle → Verify depth, nulls, physical ranges
3. geox_subsurface_generate_candidates → Compute Vsh, φ, Sw, net pay
4. geox_subsurface_verify_integrity → Physics9 boundary check
5. geox_basin_profile → Basin context + petroleum system
6. geox_prospect_evaluate(mode='screen') → Quick heuristic screening
7. geox_prospect_evaluate(mode='appraise') → Requires QC_VERIFIED evidence
8. geox_claim_create → Structured interpretation claim
9. geox_claim_validate → Schema validation
10. geox_claim_challenge → Alternative interpretation (multi-discipline argument)
11. geox_claim_seal → Route to arifOS 888 JUDGE for final adjudication
```

### 8.3 Decision Authority

```
GEOX computes evidence           → "60m oil column, P50, AC_Risk 0.28, QUALIFY"
arifOS 888 JUDGE adjudicates     → SEAL / SABAR / HOLD / VOID
Arif Fazil (F13 SOVEREIGN) decides → Drilling go/no-go, capital commitment
```

**GEOX never tells you to drill. It tells you what the Earth looks like.**

---

## 9. FOR AI AGENTS

### 9.1 MCP Connection

GEOX exposes all 40 tools via MCP (Model Context Protocol). Two transport modes:

**HTTP/SSE (for remote agents):**
```
Endpoint: https://geox.arif-fazil.com/mcp
Transport: Streamable HTTP
Auth: Cloudflare Tunnel (no API key required for localhost-bridged agents)
```

**stdio (for local agents):**
```bash
python3 -m geox_mcp.server --transport stdio
```

### 9.2 Tool Categories for Agentic Reasoning

| Cognitive Axis | Tools | When to Use |
|----------------|-------|-------------|
| **observe** | `data_ingest_bundle`, `dst_ingest_test`, `header_inspect`, `literature_ingest`, `fault_stick_ingest_tool`, `evidence_discover` | Raw data enters the system |
| **verify** | `data_qc_bundle`, `subsurface_verify_integrity`, `attribute_registry_list_tool` | Validate data integrity and physics compliance |
| **reason** | `seismic_compute`, `seismic_compute_attribute_tool`, `subsurface_generate_candidates`, `sequence_interpret`, `evidence_reason`, `horizon_contrast_surface` | Derive geological meaning from data |
| **boundary** | `basin_resolve`, `basin_profile`, `map_context_scene`, `coord_transform_tool`, `blockspace_resolution_tool` | Establish spatial/geological context |
| **judge** | `prospect_evaluate`, `claim_create`, `claim_validate`, `claim_challenge`, `claim_seal` | Prepare evidence for constitutional adjudication |
| **identity** | `system_registry_status`, `query_intake`, `abstraction_guard`, `report_to_workflow` | System discovery and routing |

### 9.3 Agent Rules

1. **Always cite evidence.** Never claim a geological interpretation without referencing at least one evidence artifact (well log, seismic, DST, literature).
2. **Always declare uncertainty.** Use P10/P50/P90 bands. Never claim certainty without a distribution.
3. **Never self-seal.** Route all SEAL requests through `geox_claim_seal` — it proxies to arifOS 888 JUDGE.
4. **Respect epistemic tags.** CLAIM ≠ PLAUSIBLE ≠ HYPOTHESIS ≠ ESTIMATE ≠ UNKNOWN. Don't present a HYPOTHESIS as if it's a CLAIM.
5. **Carry hypothesis scaffolding.** Every geological hypothesis must document: `evidence_for` (what supports it), `evidence_against` (what contradicts it), `expected_additional_signatures` (what else you'd expect to see if true), `missing_tests` (what data would settle it).
6. **Check AC_Risk before presenting.** If AC_Risk > 0.35, the interpretation is HOLD-grade. Don't present it as SEAL.
7. **Models expire.** Interpretations are non-stationary: evidence updates can re-rank hypotheses. Single-well interpretations are candidates, not proven regional truths. Seismic without well tie remains hypothesis-layer only.
8. **Read GENESIS/ before modifying.** If your code change contradicts a GENESIS principle, halt and file 888_HOLD.
9. **Never touch the canonical tool registry** (`CANONICAL_PUBLIC_TOOLS` in `src/geox_mcp/server.py`) without 888_HOLD.

---

## 10. FOR INSTITUTIONS

### 10.1 Nobel-Grade Earth Intelligence

GEOX is built on 6 Nobel-grade eurekas, catalogued in [`docs/GEOX_NOBEL_EUREKA_CATALOGUE.md`](docs/GEOX_NOBEL_EUREKA_CATALOGUE.md):

1. **Physics-Constrained Embedding Space** — Physical laws as hard constraints reduce the solution space.
2. **Anomalous Contrast as Cross-Modal Fidelity** — AVO fluid factor ΔF and transformer attention residual δᵢ are the same mathematical operation.
3. **Uncertainty as First-Class Citizen** — P10/P50/P90 mandatory on every estimate; epistemic tagging (CLAIM/PLAUSIBLE/HYPOTHESIS/ESTIMATE/UNKNOWN).
4. **Multi-Discipline Self-Argument** — Geology vs geomechanics vs drilling vs reservoir. Every claim must be challenged.
5. **Constitutional Governance for AI Output** — 13 floors (WAJIB/SUNAT/HARUS/MAKRUH/HARAM) enforce trustworthiness, not just capability.
6. **PINN Petrophysics** — Physics-Informed Neural Networks with Archie + density loss terms constrain Vsh/φ/Sw to physically admissible ranges.

### 10.2 Compliance

| Framework | Alignment |
|-----------|-----------|
| **arifOS F1–F13** | Fully mapped in GENESIS/003 |
| **Adat Agentik (Fiqh Agentik)** | 7 teras Adat (Kejujuran, Maruah, Veto, Kesungguhan, Kerahasiaan, Keinsafan, Tebus Salah) enforced via malu_index + darjat tier |
| **Singapore Model AI Governance Framework (Agentic AI, Jan 2026)** | 4 dimensions mapped |
| **ASEAN Guide on AI Governance and Ethics** | 6 principles mapped |
| **Apache-2.0** | Scientific tooling — free to use, modify, distribute. Federation governed by arifOS AGPL-3.0 kernel. |

### 10.3 The Moat

GEOX is the only Earth AI system in the world with:
- Runtime epistemic integrity standard (CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN) plus hypothesis scaffolding (`evidence_for`, `evidence_against`, `expected_additional_signatures`, `missing_tests`)
- Constitutional governance (13 floors, 888 JUDGE, VAULT999)
- Cross-modal fidelity constraint on every tool output
- Multi-discipline self-argument engine
- AC_Risk governance scoring for anomalous contrast detection
- Dual-transport MCP (HTTP + stdio) for both human operators and AI agents

---

## 11. KNOWN LIMITATIONS

| Limitation | Severity | Status |
|------------|----------|--------|
| **Single-VPS deployment** — no horizontal scaling | MEDIUM | Accepted. GEOX serves evidence; compute distribution is a federation concern. |
| **F03 STABILITY** — full reproducibility across agents not yet proven | MEDIUM | Tracked in GENESIS/003. Same-input-same-output across differing LLM backends is an open research question. |
| **F07 full A2A orchestration not native** — multi-agent coordination routes through arifOS gateway | MEDIUM | By design. GEOX does not self-orchestrate. |
| **Vision AI depends on external VLM** — `geox_vision_minimax_inference` calls MiniMax MCP on port 18091 | LOW | The calibration harness (`geox_vision_calibrate`) provides a self-contained verification path. |
| **Limited basin coverage** — currently Malay Basin focus with extendable framework | LOW | Basin registry is modular; new basins can be added via configuration. |
| **No real-time streaming data** — ingestion is file-based, not live sensor feeds | LOW | Real-time WITSML/OPC-UA ingestion is on the LEM (Large Earth Model) roadmap. |

---

## 12. FEDERATION CROSS-REFERENCE

| Organ | Repo | Port | Role | Relationship to GEOX |
|-------|------|------|------|---------------------|
| **arifOS** | [ariffazil/arifos](https://github.com/ariffazil/arifos) | 8088 | Constitutional kernel | Receives GEOX evidence; adjudicates SEAL/SABAR/HOLD/VOID |
| **A-FORGE** | [ariffazil/A-FORGE](https://github.com/ariffazil/A-FORGE) | 7071 | Execution shell | Builds + deploys GEOX Docker image; hosts MIND:51001 + MEMORY:51002 |
| **AAA** | [ariffazil/AAA](https://github.com/ariffazil/AAA) | 3001 | Control plane | Operator cockpit; displays GEOX prospect cards, map scenes, correlation panels |
| **WEALTH** | [ariffazil/WEALTH](https://github.com/ariffazil/WEALTH) | 18082 | Capital intelligence | Future: receives GEOX prospect viability scores for NPV/IRR computation |
| **WELL** | [ariffazil/WELL](https://github.com/ariffazil/WELL) | 18083 | Human readiness | Checks human-substrate readiness before field operations informed by GEOX evidence |
| **APEX** | [ariffazil/apex](https://github.com/ariffazil/apex) | 3002 | Legacy health probe | Legacy health probe — deliberation moved to AAA a2a-server |

---

## 13. BUILD, TEST, DEPLOY

### 13.1 Local Development

```bash
cd /root/geox

# Install
uv sync --frozen

# Test suite (60+ files)
make test                    # PYTHONPATH=src pytest tests/ -q --tb=short

# Smoke test
make smoke                   # PYTHONPATH=src python scripts/smoke_test.py

# Lint + type check
make lint                    # ruff check src/ + mypy src/

# Format
make format                  # ruff format src/

# Full security forge
make forge                   # Trivy + Semgrep + Gitleaks + Ruff
```

### 13.2 Running the Server

```bash
# Production (systemd)
systemctl restart geox-mcp

# Local HTTP
python3 -m geox_mcp.server --host 127.0.0.1 --port 8081

# Local stdio (for Claude Code, OpenCode, Continue CLI)
python3 -m geox_mcp.server --transport stdio
```

### 13.3 Docker Build

```bash
make build                   # docker build -t geox:latest .
```

### 13.4 Deploy to VPS

```bash
./deploy-vps.sh              # Build + transfer + docker compose up
./deploy-vps.sh --force-rebuild  # Force GUI asset rebuild
```

### 13.5 CI Pipeline

On every push and PR (`.github/workflows/ci.yml`):
1. **Security:** TruffleHog secret scan
2. **Python:** `pip install -e .[dev]`, `pip-audit`, `ruff check`, `mypy`, `pytest`
3. **Smoke test:** Start server, verify `/health` 200, verify `/mcp` reachable

---

## 14. LICENSE & SOVEREIGNTY

### License

GEOX is licensed under the **Apache License 2.0** — free to use, modify, and distribute for scientific tooling. The federation governance kernel (arifOS) operates under AGPL-3.0. GEOX the tool is Apache. GEOX the citizen is AGPL-governed.

```
Copyright 2025–2026 Muhammad Arif bin Fazil
SPDX-License-Identifier: Apache-2.0
```

### Sovereignty

```
SOVEREIGN: Muhammad Arif bin Fazil
ROLE:      F13 — Absolute Veto
LAW:       arifOS Constitutional Kernel (F1–F13)
CANON:     GENESIS/ (000–003)
SEAL:      DITEMPA BUKAN DIBERI — Forged, Not Given
```

GEOX is not a product. GEOX is an organ. It serves the federation. It witnesses the Earth. It never authorizes. The sovereign's word is final.

---

## 15. QUICK REFERENCE CARD

```bash
# Install
uv sync --frozen

# Test
PYTHONPATH=src pytest tests/ -q --tb=short

# Lint
ruff check src/ && mypy src/

# Run (HTTP)
python3 -m geox_mcp.server --host 127.0.0.1 --port 8081

# Run (stdio)
python3 -m geox_mcp.server --transport stdio

# Health
curl http://127.0.0.1:8081/health

# MCP tools list
curl -X POST http://127.0.0.1:8081/mcp/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Public endpoint
curl https://geox.arif-fazil.com/health

# Service management
systemctl status geox-mcp
systemctl restart geox-mcp
journalctl -u geox-mcp -n 50 --no-pager
```

---

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    GEOX does not tell you where to drill.                        ║
║    GEOX tells you what the Earth looks like.                     ║
║                                                                  ║
║    arifOS tells you if the evidence is admissible.               ║
║    Arif tells you if the well gets drilled.                      ║
║                                                                  ║
║         The Earth speaks. GEOX listens. The sovereign            ║
║         decides. That is the federation. That is the law.        ║
║                                                                  ║
║              DITEMPA BUKAN DIBERI — Forged, Not Given            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```
