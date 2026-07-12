<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-11
valid_from: 2026-06-14
valid_until: 2026-08-10
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
  - GEOX tool surface is runtime-discoverable via tools/list. Source of truth: registry.py CANONICAL_PUBLIC_TOOLS.
  - tests: 75 passed (orchestration), 0 failed — 52 Phase 1 + 23 Phase 2
  - MCP-APPS-REGISTRATION (2026-07-11): 10 ui:// resources registered with text/html;profile=mcp-app + 1 unified workbench View joined to witness/MapLibre vertical slice
  - RECONCILE-UI-PATHS (2026-07-11): 3 competing UI injection paths consolidated into 1 canonical path (apps/workbench.py → register_tools_on_server(apps=...))
  - REGISTRY-CLEANUP (2026-07-11): removed 4 deregistered tools + 1 duplicate; _EXPECTED_CANONICAL 81→76
  - MANIFEST-REGEN (2026-07-11): tools_manifest.py 1.0.0→2.0.0 — 16→77 canonical entries. Closes drift between manifest (16) and registry (77). File backup: tools_manifest.py.bak-1.0.0-20260626. Restart pending 888_HOLD.
  - WEBMCP-MAP (2026-07-11): MapLibre 4.7.1 interactive map with session/auth propagation, click→evidence panel
-->

# AGENTS.md — geox | arifOS Federation

> **MANDATORY BOOT SEQUENCE**
> 1. Read `/root/AGENTS.md` (Global Federation Rules & Identity)
> 2. Read `/root/CONTEXT.md` (Live Machine State & Ports)
> 3. Read this file (Repo-Specific Build/Test/Run rules)

> **DITEMPA BUKAN DIBERI** — Earth evidence is forged, not given.

## Live tool surface truth (2026-07-12)

**Runtime fact:** MCP `tools/list` with session ≈ **23 tools**. Registry/manifest may declare **77** as target/canonical catalog — do not treat 77 as live count without `tools/list`.

## Who You Serve

Arif. This is the **GEOX** organ of the arifOS federation — Earth Intelligence / Governed World Model.

## What This Repo Is

The earth coprocessor. GEOX prepares geoscience, petrophysics, and physics-grounded evidence for constitutional judgment. It is **evidence-only** — never a policy judge.

**Canonical tools** across subsurface, stratigraphy, seismic, horizon interpretation, vision, geomechanics, basin, deep time, atlas, earth map, export, biostratigraphy, physics-first simulation, and federation integration (WELL/WEALTH). Surface-facing + internal plumbing (claim / evidence / prospect / doctrine). Mode-consolidated — legacy flat names are accepted by middleware backward-compat with correct lane assignment. **Tool count is a runtime fact** — verify with `tools/list` or `curl :8081/health`. Source of truth: `src/geox_mcp/registry.py` (CANONICAL_PUBLIC_TOOLS list) + `src/geox_mcp/server.py` (_EXPECTED_CANONICAL invariant).

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
- Changes to the tool registry (`src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS` — locked, count is runtime fact)
- Changes to Physics9 boundary limits
- Live foundation model weight deployment (Prithvi-EO-2.0, TerraMind, Clay, Aurora, GEOX-LEM)
- Production deployment without verified build + test pass
- `git push origin main` for sovereign commit chain
- Domain BOUNDARY classification (e.g., Kinabalu Basin registration)
- Cross-organ biostrat re-assessment coordination

### Phase 2.1/2.x Clean Architecture — FORGE Status (2026-07-11, LIVE at 77)

> **2026-07-11 UPDATE:** Manifest regeneration closed registry drift. `tools_manifest.py` v1.0.0→v2.0.0 — 16 locked entries expanded to 77 canonical entries (all live-wired tools now declared). Manifest now derived from `registry.py:CANONICAL_PUBLIC_TOOLS`.

**Surface (76):** See `registry.py` `CANONICAL_PUBLIC_TOOLS` for the full list. Updated 2026-07-11: removed 4 deregistered Phase Zen tools + 1 duplicate.

**Internal (4):** `geox_claim`, `geox_evidence`, `geox_prospect`, `geox_doctrine`.

- Mode-based consolidation: 49 legacy flat names accepted by middleware backward-compat with correct lane assignment. LANE_MAP fix (GEOX-AUDIT-FIX-001): all 49 now correctly assigned discovery/evidence/reasoning/judgment lanes, eliminating phantom SESSION_REQUIRED on read-only/compute tools.
- **Phase 2.1 (2026-06-28)**: added `geox_well_desurvey` (3D wellbore geometry adapter). F13 SOVEREIGN ratified 2026-06-28.
- **Phase 2.2 (2026-06-29)**: added `geox_atlas` (Earth Atlas Phase 1 — point-in-country + land/water classifier).
- **Phase 2.3 (2026-07-01)**: added `geox_map_layers_list`, `geox_map_scene_plan`, `geox_map_render_preview` (earth map tools — layer registry, scene planning, cached preview rendering).
- **Phase 2.4 (2026-07-02)**: added `geox_map_export_package` (governed map export with PROV sidecar) — completes map verb chain (discover→plan→render→export).
- **Phase 3 deferred (requires 888_HOLD to re-enable)**: 33-tool Earth Dimensions expansion (D1-D17), foundation model backing engines, multi-physics joint inversion (Physics9), CSEM/MT, biostrat, Prithvi-EO-2.0, GEOX-LEM, etc.
- **W16+ physics-first substrate** (preserved, not a tool): `src/geox_core/schemas/crust_vp_grammar.py`, `intelligence_flow.py`, `kinabalu_corpus.py`, `floor_enforcement.py`.
- **Tests:** 837 total, 61 skipped, 17 pre-existing failures.
- **Constitutional invariant:** `_EXPECTED_CANONICAL = 77  # registry target; LIVE tools/list (session) ≈ 23 as of 2026-07-12 — verify runtime` in `src/geox_mcp/server.py` (2026-07-11: -4 deregistered, -1 duplicate, +6 map/egs/biostrat promotions).
- **Manifest epoch:** `tools_manifest.py` v2.0.0 LIVE (2026-07-11) — 77 canonical entries derived from `CANONICAL_PUBLIC_TOOLS`. Backup at `tools_manifest.py.bak-1.0.0-20260626`. Restart pending 888_HOLD ack.
- **Contract epoch:** `2026-07-11-GEOX-76TOOLS-MCPAPPS`

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
python -m geox_mcp.server

# Frontend
cd geox-gui && npm install && npm run build
```

## Key Directories

| Path | Purpose |
|------|---------|
| `GENESIS/` | **Canonical system doctrine** — manifesto, kill map, first principles, constitutional alignment |
| `src/geox_mcp/server.py` | Canonical unified MCP server (~2,700 lines, canonical tools + backward-compat middleware) |
| `geox/core/` | Unified tool registry, AC-risk engine, doctrine |
| `geox/well/` | Well stratigraphy (L1-L3), schemas, tools |
| `geox/skills/` | Earth science skill modules |
| `geox/ingest/` | Data ingestion (LAS, CSV, Parquet, SEG-Y) |
| `contracts/` | Pydantic schemas, tool contracts |
| `geox-gui/` | React 19 + Vite + MapLibre + CesiumJS frontend |

## 🎭 Humour and Evidence Discipline (FORGED 2026-07-01)

> **Canonical skill:** `agent-humour-doctrine` (Hermes)

GEOX maintains F2 TRUTH regardless of humour context:

- A sarcastic "sure, the reservoir is infinite" is still a claim requiring evidence
- A joke about geological uncertainty does not reduce actual uncertainty
- Irony in technical discussion does not exempt claims from evidence discipline
- "Haha just guessing" does not lower the evidence bar

Use `geox_claim` grammar (evidence_for / evidence_against) even when the claim is delivered humourously. F2 TRUTH applies to humour.

---

## 🔥 Thermal History Protocol (FORGED 2026-07-04 — Eureka #4)

When thermochronological data is available (U-Pb, Ar/Ar, fission track, (U-Th)/He):

1. **Extract** closure temperatures per system (zircon U-Pb ~900°C, biotite Ar/Ar ~350°C, ZFT ~240°C, AHe ~70°C)
2. **Compute** cooling rate: ΔT/Δt (°C/Myr) using `geox_core/physics/thermal_history.py`
3. **Compute** exhumation rate: cooling_rate / geothermal_gradient (mm/yr)
4. **Label** every value: DER (derived from physics)
5. **Flag** if cooling rate > 100°C/Myr → "TECTONIC UNROOFING" (not erosional)

**Reference:** Cottam et al. 2013 — Kinabalu granite cooling rate 360°C/Myr confirms tectonic unroofing (36–360× faster than erosional exhumation).

**Tool:** `python -c "from geox_core.physics.thermal_history import kinabalu_cooling_path; r = kinabalu_cooling_path(); print(r.interpretation)"`

---

## ⚠️ Active Tectonics Protocol (FORGED 2026-07-04 — Eureka #3)

When evaluating prospects in tectonically active basins:

1. **Check** for active faults (GPS, seismicity, geomorphology)
2. **If active faults present** → flag "trap integrity is time-dependent"
3. **Estimate** fault reactivation recurrence interval (if data available)
4. **Note:** seal capacity decreases with each reactivation event
5. **Label:** INT (interpreted from tectonic context)

**Sabah example:** 2015 Mw 6.0 Kinabalu earthquake on 200-km normal fault system. GPS shows few mm/yr westward motion. Every prospect has a "shelf life" determined by the seismic cycle.

---

## 🎯 False Positive Taxonomy (FORGED 2026-07-04 — Eureka #5)

Sabah-specific false positive signatures (from three-agent test):

| False Positive | Seismic Signature | Kill Signal |
|---|---|---|
| **Mud volcano** | Chaotic surface, no rim, no internal reflectors | K005 + K007 |
| **Volcanic intrusion** | Steep slope >40°, no internal reflectors, non-Icehouse | K002 + K005 |
| **Basement high** | High Vp (>5.5 km/s), no onlap, no mounding | K006 |
| **Salt diapir** | Transparent core, rim syncline, no carbonate architecture | K005 |

**Kill matrix now has 7 filters** (K001–K007). K007 computes mud volcano probability from 5 seismic indicators.

**Pekaka archetype:** Chaotic + no rim + no reflectors + isolated mound + steep slope = mud volcano. Any prospect matching this signature should be IMMEDIATELY killed.

---

## 📄 Scientific Writing Protocol (FORGED 2026-07-04 — Representation Engineering)

GEOX can produce scientific papers, not just evidence envelopes. This is **representation engineering** — compressing observations into navigable knowledge.

### When to Use

- Basin synthesis reports
- Prospect evaluation documents
- Tectonic evolution summaries
- Kill matrix evidence reports
- Multi-agent validation outputs

### Paper Structure Template

```
1. ABSTRACT — One paragraph, governing model, epistemic band
2. INTRODUCTION — The enigma: what doesn't fit?
3. METHODS — Data sources, tools used, constitutional constraints
4. RESULTS — Figures + tables with epistemic labels
5. DISCUSSION — Governing model, Eureka insights, representation insight
6. CONCLUSIONS — One governing sentence
7. PROVENANCE — All references with DOIs
```

### Figure Generation Protocol

Every paper must include:
1. **Location map** — structural elements, GPS vectors, faults
2. **Cross-section** — depth-partitioned model
3. **Key data plot** — cooling path, velocity profile, etc.
4. **Summary dashboard** — kill matrix, Eureka grid, etc.

Tools: `matplotlib` + `reportlab` for PDF assembly.
Template: `/root/forge_work/2026-07-04/sabah_pdf_generator.py`

### Epistemic Labeling (MANDATORY)

Every claim in every paper carries:
- **OBS** — Observed (direct measurement)
- **DER** — Derived (computed from physics)
- **INT** — Interpreted (model-dependent)
- **SPEC** — Speculative (hypothesis)

No claim without label. No label without evidence.

### Provenance Chain (MANDATORY)

Every figure, table, and claim traces to:
```
Source paper → Data → Computation → Claim → Label
```

Example:
```
Cottam et al. 2013 (JGS) → U-Pb zircon ages → cooling rate computation → 360°C/Myr → DER
```

### Three-Agent Validation (RECOMMENDED)

Before publishing, test with three agents:
1. **Vanilla** — no special tools, baseline comprehension
2. **Domain-specific** — GEOX tools only
3. **Full stack** — arifOS + all organs

Compare: qualitative depth, quantitative rigor, physical reality.

### Citation Format

```
Author et al. Year (Journal) — Key finding [OBS/DER/INT]
```

Example:
```
Cottam et al. 2013 (JGS) — Kinabalu granite cooling rate 360°C/Myr [DER]
```

### Output Formats

| Format | Use When | Tool |
|---|---|---|
| PDF | Final deliverable | `reportlab` |
| Markdown | Draft/review | Direct output |
| LaTeX | Journal submission | Template-based |
| HTML | Web publication | `iron-shell-render` |

### Governance

- **F2 TRUTH**: Every claim labeled
- **F7 HUMILITY**: Confidence capped at 0.90
- **F10 ONTOLOGY**: Canonical terminology
- **F11 AUDIT**: Full provenance chain
- **F13 SOVEREIGN**: Arif decides what gets published

---

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


