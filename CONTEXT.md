<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-24
valid_from: 2026-06-24
valid_until: 2026-07-24
confidence: high
scope: /root/geox
-->

# CONTEXT.md — GEOX (Earth Intelligence)

> **Organ:** GEOX | **Port:** 8081 | **Repo:** `ariffazil/geox`
> **Last Updated:** 2026-06-24

## Live State

- **Service:** `geox-mcp.service` (systemd, HTTP mode)
- **Health:** `http://127.0.0.1:8081/health`
- **Public MCP:** `https://geox.arif-fazil.com/mcp`
- **Runtime:** Python 3.11+ / FastMCP 3.4.2 / Pydantic v2
- **Role:** Earth evidence coprocessor — witness, never authorize
- **Contract epoch:** `2026-06-22-GEOX-56TOOLS-v3.0`
- **Git version:** `geox-ead04d1c`

## Canonical Tool Surface

- **16 mode-based tools** in `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS`
- **56 compat names** in `CANONICAL_COMPAT_TOOLS`
- Invariant `_EXPECTED_CANONICAL = 56` in `src/geox_mcp/server.py`

## Key Updates (2026-06-22 W16+ FORGE)

- **Physics-first substrate** deployed: Huang 2021 Vp grammar, intelligence flow, Kinabalu corpus
- **56 canonical tools** stable (40 baseline + 16 added in W2–W15+ tranches)
- **124 new tests** across crustal domain, intelligence flow, floor enforcement
- **Dual MCP transport** verified: HTTP/SSE on 8081, stdio for local agents
- **Floor enforcement wrapper** hardened: F7 humility cap 0.95 → 0.90

## Dependencies

- arifOS MCP kernel (8088) — constitutional judgment
- A-FORGE (7071/7072) — build/deploy actuator
- AAA (3001) — cockpit display / A2A routing
- PostgreSQL, Redis, Qdrant — data layers
- MiniMax VLM MCP (18091) — vision inference backend

## Known Issues

- GitHub Actions `Publish GEOX MCP Image` fails: Dockerfile references missing `requirements.txt` / `requirements-earth.txt` (GEOX uses `pyproject.toml` + `uv.lock`)
- GitHub Actions `Build and deploy Python app to Azure Web App - geox` fails: same `requirements.txt` dependency
- Federation Governance Gate previously failed due to missing `FEDERATION_CONTRACT.md` and `CONTEXT.md` — **resolved 2026-06-24**

---

*DITEMPA BUKAN DIBERI — Earth evidence is forged, not given.*
