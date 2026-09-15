<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-02
valid_from: 2026-07-02
valid_until: 2026-08-02
confidence: high
scope: /root/geox
changes_since_last_verified:
  - 2026-07-11: MCP Apps registration — 10 ui:// resources, workbench View, MapLibre interactive map
  - 2026-07-11: Registry cleanup — 76 public tools (-4 deregistered, -1 duplicate)
  - 2026-07-11: WebMCP categories synced to live 76-tool surface, session/auth propagation
  - 2026-07-11: Macrostrat integration blueprint + 4 MCP Apps contract deltas
  - 2026-07-11: RECONCILE — 3 competing UI injection paths → 1 canonical (apps/workbench.py)
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
- **Contract epoch:** Runtime fact — `server.py` GEOX_CONTRACT_EPOCH
- **Git version:** `geox-75d66192`

## Canonical Tool Surface

- **Source of truth:** `src/geox_mcp/tools_manifest.yaml` → `surface_manifest.py` → `registry.py`
- **Public tools:** 26 (Capability Graph: 7 families, 3 tiers, 3 packs, 4 discovery profiles, 4 workflows)
- **Runtime discovery:** `tools/list` MCP call or `curl :8081/health`
- **Discovery profiles:** `default` (13 tools), `specialist` (19), `research` (26)
- **Capability packs:** `earth_core` (Tier A), `earth_specialist` (Tier B), `earth_research` (Tier C)
- **Flat tool names unchanged:** `geox_basin`, `geox_well`, `geox_petrophysics`, etc. (no renames)
- **SOT pipeline:** `tools_manifest.yaml` → `generate_all_surfaces.py` → all JSON/YAML/MD surfaces

## Key Updates (2026-07-02 FORGE)

- **Dual surface cleanup**: 16 dead `geox/` submodules archived to `.archive/`
- **entrypoint_unified.sh deprecated** — forwards to `entrypoint.sh`; remove after 2026-07-30
- **Dockerfile confirmed clean** — uses `pyproject.toml` + `pip install .`
- **Live surface verified**: 26 canonical tools on :8081, all ANALYZE class, mutation=false
- **`geox_map_export_package` live** — completes the map verb chain with PROV sidecar + STAC catalog
- **Artifact envelope contract** — `contracts/artifact_envelope.py` — forensic traceability for all tool returns
- **Production readiness audit** — 11-gate scorecard: 72% YELLOW. Gap tracker: `forge_work/FORGE_PRODUCTION_GAPS.md`

## Production Readiness (2026-07-02)

- **Verdict:** YELLOW (72%) — concept strong, production gaps real
- **Gap tracker:** `forge_work/FORGE_PRODUCTION_GAPS.md`
- **Production audit:** `forge_work/PRODUCTION-READINESS-AUDIT-2026-07-02.md`
- **P0 (1 day):** Stamp `_envelope` on 26 tools, fix 1 test failure
- **P1 (8 days):** Unified QC runner, challenge gate, forbidden-claims classifier
- **P2 (7 days):** Risk bands, evidence floors, petrophysics compute gaps
- **Conveyor belt:** Ingest → QC → Compute → Claim → Challenge → Uncertainty → Reproducibility → Safety → arifOS

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
- Artifact envelope (`_envelope`) not yet stamped on all tool returns — integration pending

---

*DITEMPA BUKAN DIBERI — Earth evidence is forged, not given.*
