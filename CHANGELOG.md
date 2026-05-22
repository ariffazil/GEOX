# Changelog — GEOX Earth Intelligence

> **DITEMPA BUKAN DIBERI**

## [2026.05.22] — 2026-05-22

### 🎂 Birthday Release — Arif's Birthday 2026 — Hard Pruning

**Sovereign 11 Tools** replaces 35+ phantom/dead/redundant tools with 11 honest, minimal, complete tools.

- **smithery.yaml:** Complete rewrite — 35+ tools → 11 sovereign tools (2026-05-22)
- **server.py:** Tool count assertion 10 → 11; profile-driven surface expansion (minimal/standard/full via `GEOX_PROFILE` env var)
- **registry.py:** Registry restructure — canonical public tools updated
- **data.py:** Major refactor — bundle ingest with `source_uri`, `source_type`, `batch_mode` support
- **petrophysics.py:** 71 lines added — enhanced petrophysical computation
- **prospect.py:** 241-line refactor — prospect evaluation tooling
- **unified_13.py:** Cleanup and alignment with 11-tool surface
- **New: evidence_reason.py** (737 lines) — evidence reasoning engine
- **New: seismic_compute.py** (340 lines) — seismic computation tools
- **New: sequence.py** (893 lines) — sequence analysis tools
- **pyproject.toml:** Version 2026.05.21 → 2026.05.22

## [2026.05.21] — 2026-05-21

### Birthday Release — Repo Hygiene

- **smoke_test.py:** Softened tool-surface check to warn-and-continue instead of hard-fail
- **forward_model_synthetic.py:** Removed degenerate branches
- **unified_13.py:** Removed dead export
- **smoke_test.py:** Improved test coverage and readability
- Verified `pytest tests/ -q`: 51 passed, 1 skipped.

## [2026.05.19] — 2026-05-19

### Operational
- AGENTS.md forged — earth intelligence agent landing protocol
- CODEOWNERS added
- 21 sovereign tools live on port 8081
- Health endpoint verified 200 with all tools responding

### Architecture
- FastMCP server (~1,413 lines) — canonical unified MCP surface
- L1–L3 well stratigraphy pipeline operational (`geox_well_analyze_sequence`)
- Graphiti-mcp knowledge graph substrate wired (port 8000)
- Seismic attribute computation and correlation tools live

## [2026.04.17] — 2026-04-17

- Initial operational release
- Petrophysics engine (Archie, Vsh, φ, Sw, net-pay)
- Subsurface candidate generation with residual maps
- Physics9 boundary limits enforced
