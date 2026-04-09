# GEOX MCP Server — Deployment Ready

**DITEMPA BUKAN DIBERI**
**Date:** 2026-04-08
**Status:** READY FOR VPS DEPLOYMENT — v0.6.0 Phase B Complete

---

## Summary

Phase B Petrophysics tools shipped. All 11 MCP tools tested and governed. Server ready for Docker deploy to `srv1325122.hstgr.cloud` (Hostinger VPS) behind Traefik at `geox.arif-fazil.com`.

---

## Tool Inventory (11 tools)

| Tool | Phase | Status |
|------|-------|--------|
| `geox_load_seismic_line` | A | Ready |
| `geox_build_structural_candidates` | A | Ready |
| `geox_feasibility_check` | A | Ready |
| `geox_verify_geospatial` | A | Ready |
| `geox_evaluate_prospect` | A | Ready |
| `geox_query_memory` | A | Ready |
| `geox_select_sw_model` | B | Ready |
| `geox_compute_petrophysics` | B | Ready |
| `geox_validate_cutoffs` | B | Ready |
| `geox_petrophysical_hold_check` | B | Ready |
| `geox_health` | — | Ready |

---

## Test Results

| Suite | Passing | Failing |
|-------|---------|---------|
| All tests | 418 | 14 pre-existing (CIGVis renderer + numpy scalar — not blocking) |
| Phase B petrophysics | 36/36 | 0 |

---

## Pre-Deployment Checklist

- FastMCP 2.x/3.x compatibility layer active
- All 11 MCP tools registered + tested
- Health endpoints (/health, /health/details)
- Pydantic v2 schemas with provenance tags (RAW/CORRECTED/DERIVED/POLICY)
- Constitutional floors F1·F2·F4·F7·F9·F11·F13 active
- Version bumped to 0.6.0
- pyproject.toml, smithery.yaml updated to 0.6.0
- CHANGELOG.md updated with Phase B entry
- Dockerfile: multi-stage Python 3.12-slim, port 8000, HEALTHCHECK

---

## VPS Environment Variables Required

`
GEOX_ARIFOS_KERNEL_URL=http://arifosmcp_server:8000/mcp
QDRANT_URL=http://qdrant_memory:6333
GEOX_LOG_LEVEL=INFO
GEOX_TRANSPORT=http
`

---

## Deploy Commands (on VPS)

`ash
git pull origin main
docker compose up -d --build geox_server
curl https://geox.arif-fazil.com/health
curl https://geox.arif-fazil.com/health/details | python3 -m json.tool
`

Expected response: {"ok": true, "version": "0.6.0", "seal": "DITEMPA BUKAN DIBERI"}

---

## Docker Compose Snippet

`yaml
geox_server:
  build: .
  container_name: geox_server
  ports:
    - "8000:8000"
  environment:
    - GEOX_ARIFOS_KERNEL_URL=http://arifosmcp_server:8000/mcp
    - QDRANT_URL=http://qdrant_memory:6333
    - GEOX_LOG_LEVEL=INFO
  restart: unless-stopped
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.geox.rule=Host(`geox.arif-fazil.com`)"
    - "traefik.http.services.geox.loadbalancer.server.port=8000"
`

---

## Constitutional Floors Active

| Floor | Type | Status |
|-------|------|--------|
| F1 AMANAH | Hard | Active |
| F2 TRUTH | Hard | Active |
| F4 CLARITY | Soft | Active |
| F7 HUMILITY | Soft | Active |
| F9 ANTI-HANTU | Hard | Active |
| F11 AUTHORITY | Hard | Active |
| F13 SOVEREIGN | Hard | Active |

---

## Sign-off

**Status:** READY FOR DEPLOYMENT
**Authority:** Delta-Omega-Psi Trinity Architecture
**Seal:** DITEMPA BUKAN DIBERI
**Version:** 0.6.0

---

Deploy when ready.