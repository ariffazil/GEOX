<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-21
valid_from: 2026-06-14
valid_until: 2026-07-21
confidence: high
scope: /root/geox
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

**54 canonical tools** (W2-W13+ FORGE 2026-06-21) across subsurface, sensing, stratigraphy, seismic, horizon interpretation, prospect evaluation, vision, **multi-physics joint inversion (Physics9), CSEM/MT, biostrat, geomechanics, foundation model backing engines, doctrine layer (Gap X/3/5), and federation integration (WELL/WEALTH)**.

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
- Changes to the tool registry (54 canonical tools in `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS`)
- Changes to Physics9 boundary limits
- Live foundation model weight deployment (Prithvi-EO-2.0, TerraMind, Clay, Aurora)
- Production deployment without verified build + test pass

### W2-W13+ FORGE Status (2026-06-21)
- 14 new canonical tools added since 40-tool baseline:
  - **3 doctrine**: `geox_doctrine_assumption_register`, `_anti_beautiful_one`, `_godel_review` (Gap X/3/5 closed)
  - **1 foundation model**: `geox_prithvi_eo_inference` (Prithvi-EO-2.0 NASA/IBM, mock default)
  - **3 nonseismic + open data**: `geox_gravity_magnetic_forward` (HarmonIC), `geox_emag2_ingest` (NOAA), `geox_icgem_models` (GFZ)
  - **4 multi-physics**: `geox_joint_inversion` (N-modal fusion), `geox_mt_forward` (CSEM/MT), `geox_biostrat_constraint`, `geox_seismic_inversion` (1D PINN)
  - **3 integration**: `geox_geomechanics`, `geox_well_decision_class` (WELL gate), `geox_wealth_feed` (WEALTH feed)
- Tests: 89 passing, 3 skipped (live-server drift, expected pre-deploy)
- Constitutional invariant `_EXPECTED_CANONICAL = 54` in `server.py`
- Service restarted 2026-06-21; pushed commit `657b9eb0` to `origin/main`

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
| `src/geox_mcp/server.py` | Canonical unified MCP server (~1,200 lines, 40 tools) |
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

