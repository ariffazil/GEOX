# Changelog

All notable changes are documented here. GEOX follows [Keep a Changelog](https://keepachangelog.com/) principles.

## [0.3.3] - 2026-04-17

### Added
- **Seal C Phase 2**: Real `.las` file ingestion via `lasio>=0.31`
  - `geox/ingest/las_reader.py`: `load_las()`, `curve_manifest_from_bundle()`
  - `geox_well_load_bundle(well_id, las_path)`: accepts optional `.las` file path
  - Provenance changes: `scaffold_fixture` → `las_file:{filename}`
  - Supports LAS 1.2/2.0, curve aliases (DEPT/GR/RT/RHOB/NPHI/CAL/SP)
  - Null values (-999.25 etc.) canonicalised to `np.nan`

## [0.3.2] - 2026-04-17

### Fixed
- `streamable_http_app()` → `mcp.http_app()` (FastMCP 3.x API — `streamable_http_app` does not exist in 3.x)
- `BaseHTTPMiddleware` Bearer auth replaces incompatible FastAPI `Depends()`
- Skill registry: null crash confirmed session-specific, not registration bug

### Verified
- 18 tools registered (scaffold correctly gated behind `GEOX_ENABLE_SCAFFOLD`)
- 33 skills in registry
- 6/6 tests pass
- `/mcp` Streamable HTTP v2 live on port 8081

## [0.3.1] - 2026-04-17

### Added
- **P2-7**: Depth-indexed petrophysics curves
  - 91 depth points (2040–2220m MD, 2m step)
  - Per-point: `depth_md`, `porosity`, `sw`, `vsh`, `net_pay`
  - HC zone (2090–2172m): φ~0.22, Sw~0.35, net_pay=true
  - Water zone: φ~0.08, Sw~0.85, net_pay=false
  - Transition zones at top/bot of HC interval correctly flagged
  - `net_pay_intervals[]`: list of {top_md, bot_md}
  - `net_pay_m`: total paying metres (~86m across 2 intervals)
- **P2-8**: `curve_manifest` on `geox_well_load_bundle`
  - 5 curves: DEPTH_MD, GR, RT, RHOB, NPHI
  - `null_pct` and `range` per curve
- **P2-9**: Evidence chain depth notes updated

## [0.3.0] - 2026-04-17

### Fixed
- **P1-4**: `u_phys` renamed to `u_ambiguity` — formula direction explicit
  - Higher ambiguity = higher risk (intentional inversion documented)
  - `d_transform_base` and `d_transform_effective` now both returned
- **P1-5**: `transform_stack` now accepts dict items — no more `unhashable type: dict`
- **P1-6**: `evidence_credit` mechanism — `D_transform_effective = max(1.0, base − credit)`
  - Credit table: well_load=0.20, qc=0.15, petrophysics=0.40, seismic=0.30, section=0.30
  - Max credit = 1.35 → penalty floors at 1.0, SEAL now reachable

### Added
- Dockerfile (`python:3.12-slim`, `PORT=8081`, `PYTHONPATH` set)
- `GET /health` endpoint — returns seal + service status
- `GET /ready` endpoint
- Bearer token auth via `BaseHTTPMiddleware` — set `GEOX_SECRET_TOKEN`
- Scaffold tools gated behind `GEOX_ENABLE_SCAFFOLD=true` env var
- `requirements.txt`: `fastmcp>=0.7.0` (was `>=0.1.0`)

## [0.2.1] - 2026-04-16

### Added
- 4 missing tools added to public tool table:
  - `geox_well_load_bundle`, `geox_well_qc_logs`
  - `geox_section_interpret_strata`, `geox_cross_summarize_evidence`
- Scaffold disclosure note added to Well Test Fixtures section
- `correlations: []` expected empty state documented

## [0.2.0] - 2026-04-16 — REFLECT-222

### Added
- Canonical README with full tool table, AC_Risk formula, epistemic tags
- 11 domains, 33 skills in registry
- TEARFRAME governance engine
- Anti-Hantu (F9) refusal-first screening
- VAULT999 seal payload on all governed verdicts
- RATLAS — 99 canonical Earth material states

---

## Version History

| Version | Status | Focus |
|---------|--------|-------|
| 0.3.3 | **Current** | LAS real ingestion |
| 0.3.2 | Stable | HTTP transport + auth |
| 0.3.1 | Stable | Depth curves |
| 0.3.0 | Stable | Evidence credit + governance |
| 0.2.1 | Stable | README + tool table |
| 0.2.0 | Stable | Initial public release |
