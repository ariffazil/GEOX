# CONTEXT.md — GEOX (Earth Intelligence)

> **Organ:** GEOX | **Port:** 8081 | **Repo:** `ariffazil/geox`
> **Kernel SoT:** `ariffazil/arifos` (FEDERATION_CONTRACT.md + GENESIS/000)
> **Last Updated:** 2026-06-21

## Live State
- **Service:** `geox-mcp.service` (systemd, enabled)
- **Health:** `http://127.0.0.1:8081/health`
- **Tools:** **54 canonical MCP tools** (40 → 54 after W2-W13+ FORGE 2026-06-21)
- **Git version (live):** `geox-657b9eb0`
- **Last forge:** `feat(geox): W2-W13+ multi-physics Earth Witness + integration layer` (commit 657b9eb0, pushed to origin/main)
- **License:** Apache-2.0 (scientific tooling; federation governed by kernel AGPL-3.0)

## Open Data Caches
- **EMAG2v3 V3 TIFF** — 239,593,097 bytes (228.5 MB), SHA-256 `719db9d060a423b7292f09fa4312e7d0ebd4e284ba652079b34e3d05be5a370a`, at `/root/.cache/geox/emag2/EMAG2_V3_UpCont_DataTiff.tif`
- Resolution: 2 arcmin, global (-180° → 180°, -90° → 90°)
- Source: NOAA NCEI `https://www.ngdc.noaa.gov/geomag/data/EMAG2/EMAG2_V3_UpCont_DataTiff.tif`

## Dependencies
- arifOS MCP kernel (port 8088) — constitutional judgment
- WEALTH organ (port 18082) — receives GEOX wealth_feed for NPV/IRR modelling
- WELL organ (port 18083) — provides operator readiness state for decision_class gating
- Caddy reverse proxy for public endpoint

## Current Focus
- **Operational.** 54 tools live (post W2-W13+ FORGE).
- Multi-physics Earth Witness forge complete: joint_inversion + CSEM/MT + biostrat + PINN.
- Doctrine layer (Gap X/3/5) wired into MCP surface.
- Foundation model backing engine (Prithvi-EO-2.0) scaffolded; live weights deferred (needs GPU + 888).
- WELL/WEALTH integration tools live; full federation call pending.

## Known Issues
- GENESIS/003 uses old F01-F09 floor numbering — needs F13 realignment (still pending)
- Foundation model live mode not yet deployed (Prithvi-EO-2.0 weights pending GPU + 888)
- Bayesian joint inversion (replacing IRLS baseline) deferred to next forge tranche
- EMAG2v3 NetCDF variant 404 at NCEI; only TIFF available (fetcher updated)
- arifOS federation identity_unverified on live service (known limitation, not blocking)

## Recent Forge Receipts
- 2026-06-21: `/root/forge_work/2026-06-21_geox-w2-w13-multiphysics-earth-witness.md`
- 2026-06-21: Commit `657b9eb0` on `origin/main`
- 2026-06-14: `/root/geox/forge_work/2026-06-14-multi-repo-sweep-04.md` (legacy)
- 2026-06-14: `/root/geox/forge_work/2026-06-14-GEOX-forge-cycle-03.md` (legacy)
