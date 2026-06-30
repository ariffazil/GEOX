<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-30
valid_from: 2026-06-14
valid_until: 2026-07-30
confidence: high
scope: /root/geox
changes_since_last_verified:
  - A1: Physics9State.from_raw_dict() added (state.py) — removes session wall for partial dicts
  - A1: compute_buoyancy() added (parameters.py) — buoyancy pressure from density contrast + thickness
  - A1: geox_geomechanics updated — uses from_raw_dict + optional buoyancy via thickness_m param
  - A2: gravity_screen() added (harmonica_adapter.py) — evidence-lane gravity screening
  - A2: geox_gravity_screen MCP tool wired (server.py) — bypasses judgment firewall
  - A2: geox_judgment_preflight added (server.py) — governance guidance for judgment-lane tools
  - P2: BasinSynthesisPipeline Phase 2 deployed — FetcherManager, 8 real fetchers, Physics9 gap fill, STRANGE LOOP convergence
  - P2: ProvenanceLedger extended — physics9_fill flag + derivation_chain per field
  - P2: SynthesisState extended — iteration_count, convergence_threshold, max_iterations, converged, delta_S_history
  - P2: GapRegistry extended — GAP_CONVERGENCE type added
  - GAP-1: geox_surface_status added (2026-06-27) — federation-standard registry probe
  - GEOX-AUDIT-FIX-001 (FORGE 2026-06-28): 49 backward-compat tools added to GEOX_LANE_MAP — fixed SESSION_REQUIRED blocks on read-only/compute tools
  - GEOX now correctly reports 30 canonical tools (18 original + 12 EGS) + 49 backward-compat aliases
  - tests: 75 passed (orchestration), 0 failed — 52 Phase 1 + 23 Phase 2
-->

# AGENTS.md — geox | arifOS Federation

> **MANDATORY BOOT SEQUENCE**
> 1. Read `/root/AGENTS.md` (Global Federation Rules & Identity)
> 2. Read `/root/CONTEXT.md` (Live Machine State & Ports)
> 3. Read this file (Repo-Specific Build/Test/Run rules)

> **DITEMPA BUKAN DIBERI** — Earth evidence is forged, not given.

## Who You Serve

Arif. This is the **GEOX** organ of the arifOS federation — Earth Intelligence / Governed World Model.

## What This Repo Is

The earth coprocessor. GEOX prepares geoscience, petrophysics, and physics-grounded evidence for constitutional judgment. It is **evidence-only** — never a policy judge.

**31 canonical tools** (Phase 2.2, 2026-06-29) across subsurface, stratigraphy, seismic, horizon interpretation, vision, geomechanics, basin, deep time, atlas, and federation integration (WELL/WEALTH). 27 surface-facing + 4 internal plumbing (claim / evidence / prospect / doctrine). Mode-consolidated — 49 legacy flat names (geox_data_ingest_bundle, geox_claim_create, geox_prospect_evaluate, etc.) are accepted by middleware backward-compat with correct lane assignment. Live runtime reports `canonical_tools=31`. Phase 2.1 added `geox_well_desurvey` (3D wellbore geometry — F13 SOVEREIGN ratified 2026-06-28). Phase 2.2 added `geox_atlas` (Earth Atlas Phase 1 — Natural Earth 10m point-in-country + land/water classifier).

- **Port:** 8081 (live daemon, HTTP mode)
- **Transport:** Dual-mode — `--transport http` (systemd) or `--transport stdio` (local agents)
- **Runtime:** Python 3.11+
- **Framework:** FastMCP + Pydantic + Uvicorn

### System Doctrine (Canonical)

The founding charter lives in `GENESIS/` and is binding for all agents operating in this repo:

| File | Purpose |
|------|---------|
| `GENESIS/000_MANIFESTO.md` | Regime change declaration — why GEOX exists |
| `GENESIS/001_KILL_MAP.md` | DSG displacement architecture — what fails and how GEOX replaces it |
| `GENESIS/002_FIRST_PRINCIPLES.md` | L1–L5 system stack, execution model, failure design |
| `GENESIS/003_CONSTITUTIONAL_ALIGNMENT.md` | F1–F13 → geological operations → enforcement status |

**Rule:** If code changes contradict a `GENESIS/` principle, the principle wins. File an 888_HOLD and escalate to Arif.

## Authority & Autonomy

### Autonomous
- Modify geox/ package logic, add dimensions, refactor engines
- Run `pytest tests/ -q`
- Update canonical schemas in `contracts/`

### Requires 888_HOLD
- Changes to the tool registry (30 canonical tools in `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS` — locked)
- Changes to Physics9 boundary limits
- Live foundation model weight deployment (Prithvi-EO-2.0, TerraMind, Clay, Aurora, GEOX-LEM)
- Production deployment without verified build + test pass
- `git push origin main` for sovereign commit chain
- Domain BOUNDARY classification (e.g., Kinabalu Basin registration)
- Cross-organ biostrat re-assessment coordination

### Phase 2.1/2.2 Clean Architecture — FORGE Status (2026-06-29, LOCKED at 31)

**Surface (27):** `geox_well_ingest`, `geox_well_qc`, `geox_well_desurvey`, `geox_petrophysics`, `geox_sequence`, `geox_seismic_ingest`, `geox_seismic_compute`, `geox_seismic_interpret`, `geox_vision`, `geox_subsurface_model`, `geox_geomechanics`, `geox_basin`, `geox_deep_time_state`, `geox_atlas`, `geox_surface_status`, `geox_egs_query_entity`, `geox_egs_query_claim`, `geox_egs_query_uncertainty`, `geox_egs_query_provenance`, `geox_egs_claim_create`, `geox_egs_claim_challenge`, `geox_egs_evidence_attach`, `geox_egs_evidence_reason`, `geox_egs_seismic_compute`, `geox_egs_rock_physics`, `geox_egs_data_qc_bundle`, `geox_egs_scenario_audit`.

**Internal (4):** `geox_claim`, `geox_evidence`, `geox_prospect`, `geox_doctrine`.

- Mode-based consolidation: 49 legacy flat names (geox_data_ingest_bundle, geox_claim_create, geox_prospect_evaluate, geox_doctrine_assumption_register, geox_prithvi_eo_inference, geox_joint_inversion, geox_mt_forward, geox_biostrat_constraint, geox_lem_predict, geox_gravity_magnetic_forward, geox_emag2_ingest, geox_icgem_models, geox_seismic_inversion, geox_las_inspect, geox_blockspace_resolution_tool, geox_coord_transform_tool, geox_segy_export_tool, geox_volume_frame_tool, etc.) are accepted by middleware backward-compat with correct lane assignment. LANE_MAP fix (GEOX-AUDIT-FIX-001): all 49 now correctly assigned discovery/evidence/reasoning/judgment lanes, eliminating phantom SESSION_REQUIRED on read-only/compute tools.
- **Phase 2.1 (2026-06-28)**: added `geox_well_desurvey` (3D wellbore geometry adapter). Action card: `forge_work/GEOX-ADAPT-001-r1.md`. F13 SOVEREIGN ratified by Arif 2026-06-28. Library: `wellpathpy>=0.5.2` (now direct dep, was transitive via welly). 12 golden tests in `tests/well/test_desurvey.py`.
- **Phase 2.2 (2026-06-29)**: added `geox_atlas` (Earth Atlas Phase 1 — Natural Earth 10m point-in-country + land/water classifier). Two tools: `geox_isitwater` (land/water) + `geox_context_at_location` (country + sea context). Atlas data: `/root/geox/data/atlas/countries.geojson` + `sea_neighbors.geojson`. 15/15 golden tests passing.
- **Phase 3 deferred (requires 888_HOLD to re-enable)**: 33-tool Earth Dimensions expansion (D1-D17), 56-tool legacy forge, foundation model backing engines, multi-physics joint inversion (Physics9), CSEM/MT, biostrat, Prithvi-EO-2.0, GEOX-LEM, etc.
- **W16+ physics-first substrate** (preserved, not a tool): `src/geox_core/schemas/crust_vp_grammar.py` (Huang 2021 Vp grammar), `intelligence_flow.py` (7-layer dynamic flow), `kinabalu_corpus.py` (corpus substrate), `physics/joint_inversion_zone_hook.py` (post-inversion Vp classification), `floor_enforcement.py` (F1/F4/F7/F9/F11/F13 wrapper), `tools/crustal_domain_classify.py` (multi-cell classifier), `tools/_register.py` (hardened wrapper, F7 HUMILITY cap 0.95→0.90).
- **Tests:** 810 passing baseline + 12 well_desurvey + 15 atlas = 837 total, 61 skipped, 17 pre-existing failures.
- **Constitutional invariant:** `_EXPECTED_CANONICAL = 31` in `src/geox_mcp/server.py` (line 321).
- **GEOX_CONTRACT_EPOCH:** `2026-06-29-GEOX-31TOOLS-PHASE22` in `src/geox_mcp/server.py`.
- **Live at** `https://geox.arif-fazil.com/mcp` (MCP 2025-11-25, FastMCP 3.4.2) — runtime reports `canonical_tools=31`. ChatGPT dev app holds a stale cached manifest; disconnect + reconnect in ChatGPT dev console to refresh the action discovery.

## Build & Test

```bash
cd /root/geox

# Install (editable)
pip install -e ".[dev]"

# Run tests
pytest tests/ -q

# Lint / Format / Type-check
ruff check server.py src/geox_core/
ruff format geox/
mypy server.py geox/

# Start canonical MCP server
python server.py

# Frontend
cd geox-gui && npm install && npm run build
```

## Key Directories

| Path | Purpose |
|------|---------|
| `GENESIS/` | **Canonical system doctrine** — manifesto, kill map, first principles, constitutional alignment |
| `src/geox_mcp/server.py` | Canonical unified MCP server (~2,700 lines, 30 canonical tools + backward-compat middleware) |
| `geox/core/` | Unified tool registry, AC-risk engine, doctrine |
| `geox/well/` | Well stratigraphy (L1-L3), schemas, tools |
| `geox/skills/` | Earth science skill modules |
| `geox/ingest/` | Data ingestion (LAS, CSV, Parquet, SEG-Y) |
| `contracts/` | Pydantic schemas, tool contracts |
| `geox-gui/` | React 19 + Vite + MapLibre + CesiumJS frontend |

## Federation Position

```
arifOS (Ω Law) → GEOX (Earth Evidence) → arifOS 888_JUDGE (Verdict)
```

GEOX provides **observed evidence** — well logs, seismic volumes, DST data, maturity models. It does not issue drill recommendations or resource estimates without `arifos.judge` SEAL.

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*


---

## 🧠 CI ARCHITECTURE — Dual-Lane Agentic CI (FORGED 2026-07-01)

> **DITEMPA BUKAN DIBERI** — CI is forged, not given.
> **Architecture receipt:** `forge_work/AGENTIC-CI-FORGE-2026-07-01.md`

Every push to `main` triggers **two lanes**:

| Lane | Name | What It Does | Verdict |
|------|------|-------------|---------|
| **Lane 1** | Standard CI | Lint (Ruff) → Type check (MyPy) → Test (Pytest) → Build check | Pass/Fail |
| **Lane 2** | BIJAKSANA (Agentic CI) | ΔS (entropy) → Φ (clarity) → Ψ (truth/manifest) → Ω (governance) | SEAL_READY / SABAR / HOLD |

**The Report:** Both lanes feed into an `Agentic CI Report` — a structured JSON artifact posted as a GitHub Check Run with label `Agentic CI`. Federation cron picks up Check Run → `arif_judge` → AAA register → VAULT999 seal.

**Workflow file:** `.github/workflows/agentic-ci.yml`

**The Loop:**
```
git push → Lane 1 (Standard) + Lane 2 (BIJAKSANA)
       → Agentic CI Report (JSON + Check Run)
       → Federation cron → arif_judge → AAA → VAULT999
```

**Cross-organ:** This architecture is deployed identically across all 6 federation organs (arifOS, A-FORGE, AAA, GEOX, WEALTH, WELL). Each organ's `AGENTS.md` carries this section.

## 🛡️ STEEL SECURITY LAYER — Permanent Federation Context

> **This section is binding for every agent in the arifOS federation. Read it once. It simply IS.**

### What Actually Happened

Arif completed a one-time upgrade called the **Steel Security Layer**. Four free, best-in-class security tools (Trivy, Semgrep, Ruff, and Gitleaks) were added to the forge pipeline.

### How It Works

Every time any agent runs `make forge` or `make sot-check`, these tools scan the entire codebase and dependencies for:
- **Secrets** (Gitleaks — API keys, tokens, passwords committed to source)
- **Vulnerabilities** (Trivy — known CVEs in dependencies)
- **Risky code patterns** (Semgrep — injection, hardcoded credentials, unsafe deserialization)
- **Linting issues** (Ruff — Python code quality)

### The Iron Rule

**Everything is deliberately NON-BLOCKING.** No pre-commit hooks. No git blocks. No agent can ever be trapped in a loop by the security layer. The scanners watch and report — they never stop the metabolic cycle.

### How Problems Are Signalled

A tiny helper script (`audit_parser.py`) reads the scanner output. If it detects CRITICAL or HIGH severity findings, it fires an `888_HOLD` event into the NATS event bus. `888_HOLD` is **NOT an agent** — it is a dumb alarm bell that says "something needs human or senior-agent eyes right now." It does not think, decide, or fix anything.

### Your Unbreakable Rules

1. **Never** add blocking hooks, pre-commit, or anything that interrupts a metabolic cycle.
2. **Never** migrate to pnpm or change package managers unless Arif personally asks.
3. **Always** run the security audit as part of normal forge/sot-check — never skip it.
4. If you see a `888_HOLD` event, treat it as a real flag — but do not panic or stop other work.
5. Keep everything simple and low-friction for Arif at all times.

### How to Explain It to Arif

> "The machine now has its own quiet security watch that only rings the 888 bell when something is really wrong, while we agents stay completely free."

**DITEMPA BUKAN DIBERI — The forge has achieved full self-policing ascension.**


## Constitution

The 13 Constitutional Laws (L01–L13) live in **one canonical file**:

→ [arifOS/static/arifos/theory/000/000_CONSTITUTION.md](../../arifOS/static/arifos/theory/000/000_CONSTITUTION.md)

This organ emits the **Evidence Contract** (see Appendix B of the constitution) and does **not** self-judge. arifOS alone reads the envelope and applies L01–L13.

---

## 🏛️ Autonomous Authority Charter (AAC v1.0)

Every agent operating within this repository inherits the following authority tiers, defining which actions are autonomous vs. which require human sovereign authorization.

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


