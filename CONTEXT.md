<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-02
valid_from: 2026-07-02
valid_until: 2026-08-02
confidence: high
scope: /root/geox
changes_since_last_verified:
  - 16 dead geox/ submodules archived (adapters, artifacts, canonical, etc.)
  - geox/core/ duplicate identified (same as root core/) — kept for test compat
  - entrypoint_unified.sh deprecated (forwards to entrypoint.sh)
  - Dockerfile confirmed using pyproject.toml (no requirements.txt)
  - Known Issues section updated — stale CI issues resolved
-->

# CONTEXT.md — GEOX (Earth Intelligence)

> **Organ:** GEOX | **Port:** 8081 | **Repo:** `ariffazil/geox`
> **Last Updated:** 2026-07-02

## Live State

- **Service:** `geox-mcp.service` (systemd, HTTP mode)
- **Health:** `http://127.0.0.1:8081/health`
- **Public MCP:** `https://geox.arif-fazil.com/mcp`
- **Runtime:** Python 3.11+ / FastMCP 3.4.2 / Pydantic v2
- **Role:** Earth evidence coprocessor — witness, never authorize
- **Contract epoch:** `2026-07-01-GEOX-34TOOLS-PHASE23`
- **Git version:** `geox-75d66192`

## Canonical Tool Surface

- **34 canonical tools** in `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS`
  - 30 surface-facing (well, petrophysics, sequence, seismic, vision, geomechanics, basin, deep time, atlas, earth map, EGS)
  - 4 internal plumbing (claim, evidence, prospect, doctrine)
- **49 compat aliases** in `CANONICAL_COMPAT_TOOLS` — scheduled for deletion 2026-07-30
- Invariant `_EXPECTED_CANONICAL = 34` in `src/geox_mcp/server.py`
- Map surface: `geox_map_layers_list`, `geox_map_scene_plan`, `geox_map_render_preview` (Phase 2.3)
- Missing: `geox_map_export_package` (governed export with PROV sidecar)

## Key Updates (2026-07-02 FORGE)

- **Dual surface cleanup**: 16 dead `geox/` submodules archived to `.archive/`
- **entrypoint_unified.sh deprecated** — forwards to `entrypoint.sh`; remove after 2026-07-30
- **Dockerfile confirmed clean** — uses `pyproject.toml` + `pip install .`
- **Live surface verified**: 34 tools on :8081, all ANALYZE class, mutation=false

## Dependencies

- arifOS MCP kernel (8088) — constitutional judgment
- A-FORGE (7071/7072) — build/deploy actuator
- AAA (3001) — cockpit display / A2A routing
- PostgreSQL, Redis, Qdrant — data layers
- MiniMax VLM MCP (18091) — vision inference backend

## Known Issues

- `geox/core/` duplicates root `core/` — tests depend on `geox.core.*` imports; merge pending
- `entrypoint_unified.sh` deprecated — remove after 2026-07-30
- 49 compat aliases — enforce deletion on 2026-07-30
- No artifact-level PROV sidecar on rendered outputs (build `geox_map_export_package` to fix)

---

*DITEMPA BUKAN DIBERI — Earth evidence is forged, not given.*
