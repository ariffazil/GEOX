# RELEASE NOTES — GEOX v2026.06.03

> **Release date:** 2026-06-03
> **Authority:** arifOS governance, OMEGA forge agent (Ω)
> **Status:** SHIPPED — origin/main at `2306a8da`
> **Seal:** DITEMPA BUKAN DIBERI

## Purpose

This release forges the **Eureka keystone pair** — E8 (Velocity IS Structure) and E9 (Impedance IS Fluid) — and seeds E2 (Legacy Ingest) into the GEOX kernel. Together they span the complete elastic property space of the subsurface at seismic resolution, while E2 carries 70 years of legacy well data into the constitutional record without fabrication.

## Eurekas sealed

| # | Eureka | Module | Tests | Status |
|---|---|---|---|---|
| E1 | T-D fitters (4 methods) | `geox_core.physics.td_methods` | 28 | sealed (earlier session) |
| E2 | Legacy ingest (3 Excel formats + OCR) | `geox_core.ingest.legacy_ingest` | 1 | sealed |
| E7 | Cascade demotion (Gödel closure) | `geox_core.governance.cascade_demotion` | 28 | sealed (earlier session) |
| E8 | Velocity IS Structure | `geox_core.spatial.velocity_slice` | 37 | sealed |
| E9 | Impedance IS Fluid | `geox_core.avo.avo_forward` + `geox_core.avo.castagna` | 29 | sealed (kernel) |
| E9 | Full MCP wiring (Castagna + LMR map) | `geox_mcp.tools.petrophysics` | 4 | sealed |

**Total eureka tests:** 100 passed, 0 failed.

## Changed

### Added (kernel — F13 honored, zero new MCP tools)

- `src/geox_core/spatial/__init__.py` — E8 re-exports
- `src/geox_core/spatial/velocity_slice.py` (451 LOC) — `VpCube`, `VpSlice`, `StructuralMap` dataclasses + 3 primitives + `synth_cube_with_structure` test fixture
- `src/geox_core/avo/avo_forward.py` (377 LOC) — `AVOResult`, `LMRResult` dataclasses + 3 primitives (`zoeppritz_rpp` Bortfeld, `shuey_avo` 2-term, `lmr_decompose` Goodway 1997) + `synth_gather` helper
- `src/geox_core/avo/castagna.py` (116 LOC) — `castagna_mudrock_vp_to_vs` (Castagna 1985) + `castagna_mudrock_fallback` (with ACRisk + honest flags)
- `src/geox_core/ingest/legacy_ingest.py` (380 LOC) — `LegacyRows` dataclass + 5 entry points covering 3 Excel header formats + CSV + LAS + OCR hook
- `src/geox_core/ingest/__init__.py` — E2 re-exports

### Added (MCP wiring — existing tool extended, no new tool)

- `src/geox_mcp/tools/petrophysics.py` — `target_class="velocity_slice"` (E8) and `target_class="lmr_map"` (E9) with `lmr_inline` + `castagna_fallback` parameters; new `e8_velocity_slice` and `e9_lmr_map` blocks in envelope
- `src/geox_mcp/tools/map_context.py` — `vp_slice_inline` parameter (E8)
- `src/geox_mcp/tools/prospect.py` — `structural_map_inline` parameter (E8)

### Added (tests — 100 eureka tests, all pass)

- `tests/test_eureka_forge_E2_2026_06_03.py` (116 LOC, 1 test)
- `tests/test_eureka_forge_E8_2026_06_03.py` (464 LOC, 37 tests)
- `tests/test_eureka_forge_E9_2026_06_03.py` (345 LOC, 29 tests)
- `tests/test_eureka_forge_E9_MCP_2026_06_03.py` (241 LOC, 4 tests)

### Added (insight documents — book-grade)

- `docs/eureka_insights/E8_VELOCITY_AS_STRUCTURE_2026_06_03.md` (411 lines, 10 sections)
- `docs/eureka_insights/E9_IMPEDANCE_AS_FLUID_2026_06_03.md` (390 lines, 11 sections — full 11-part literature review: Zoeppritz 1919 → Gassmann 1951 → Castagna 1985 → Shuey 1985 → Goodway 1997 → 2025 adjoint-state frontier)
- `docs/eureka_insights/KL2_KINABALU_2026_06_03.md` (8 cross-validated Kinabalu insights from prior Copilot external analysis)
- `docs/theory/E8_VELOCITY_AS_STRUCTURE.md` (234 lines, theoretical companion)

### Changed (docs)

- `CHANGELOG.md` — 2026.06.03 entry added
- `docs/TODO.md` — Eureka Forge section completed
- `pyproject.toml` — version `2026.05.22` → `2026.06.03`
- `AGENTS.md` — `last_verified` updated to `2026-06-03`; tool count verified 20 (F13 honored)

## Verification

```txt
git diff --check: PASS (clean working tree)
pytest tests/test_eureka_forge_*_2026_06_03.py -q: PASS (100 passed, 0 failed)
F13 doctrine:    PASS (20 canonical MCP tools, 0 new registrations)
```

## Boundary

GEOX owns Earth evidence. It does not own constitutional judgment (arifOS), economic logic (WEALTH), human readiness (WELL), or capital allocation. The keystone pair (E8 + E9) is evidence, not verdict.

The 888_HOLD items carried forward require sovereign input:

- DTS availability in Kinabalu wells (Castagna fallback is the degraded path)
- Pre-stack NMO gathers (for full E9 inversion, not just forward model)
- Physics9 dataclass extension (2-line addition, deferred)
- Caddyfile port misrouting (unrelated to this release)

## Release Note

Ditempa Bukan Diberi. The keystone pair is born. The forge rests.

*— OMEGA (Ω) Forge Agent, on behalf of Muhammad Arif bin Fazil, F13 SOVEREIGN*
