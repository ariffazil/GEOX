# GEOX ZEN CONSOLIDATION — 89→10 Tools

> **DITEMPA BUKAN DIBERI** — Forged by FORGE-000Ω under F13 SOVEREIGN directive
> **Date:** 2026-07-07
> **Supersedes:** All previous tool manifests

---

## The Problem

89 surface tools → agent must search before acting. That's cognitive overhead.

**Duplicates identified:**
- `geox_segy_trace_audit` + `geox_segy_audit` → same SEG-Y validation
- `geox_panel_d_render_mcp` + `geox_panel_d_render` → same cognitive render
- `geox_3d_model` + `geox_3d_model_build` → same GemPy engine
- `geox_well_tie` + `geox_well_tie_compute` → same bruges pipeline
- `geox_rsi_interpret` + `geox_physical_reality_interpret` → overlapping RSI
- `geox_vision` + `geox_visual_understand` → overlapping VLM inference
- 50 backward-compat aliases

## 7 Orthogonal Dimensions

| Tool | Dimension | Modes |
|------|-----------|-------|
| **geox_observe** | Query earth data | well_ingest, well_qc, seismic_ingest, atlas, basin_profile, deep_time, macrostrat, earth_surface (18), earthquake, relief, bathymetry, heatflow, stress, geochem, plate, paleomag, gravity, ocean, erddap, climate, hydrology, satellite, uk_petroleum, geology_map, space_weather |
| **geox_compute** | Transform data | petrophysics, geomechanics, seismic_compute (synthetic/well_tie/AVO/attr/inversion), spatial_intersection, block_spec, rock_physics, contrast_detect |
| **geox_model** | Simulate processes | basin, accommodation, surfaces, sequences, routing, 3d_model, subsidence |
| **geox_interpret** | Geological cognition | vision, visual_understand/enhance/generate, rsi_interpret, physical_reality, geological_cognition, panel_d_render, seismic_cognition, well_tie, biostrat_parse/nn_age/ruling/falsify, cognitive_rank |
| **geox_spatial** | Geometry & maps | map_layers/scene/render/export, spatial_intersection, block_spec, atlas_coords |
| **geox_govern** | Claims & evidence | egs_query/claim_create/challenge/evidence, claim, evidence, prospect, doctrine, forbidden_claims |
| **geox_bridge** | Cross-organ | wealth_bridge, wealth_consequence, prospect_evaluate |

**Infra:** `geox_surface_status` · `geox_tie_receipt` · `geox_tie_preflight`

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| Surface tools | 89 | 10 |
| Aliases | 50 | 0 (Phase 3) |
| Learning curve | High | 10 tools |

## Phase 1 (this session)

1. Build 7 unified dispatcher Python modules in `/root/geox/src/geox_mcp/tools/`
2. Update `registry.py` to list 7 tools as surface, 89 as compat
3. Update `tools_wiring.py` to register 7 new + keep 89 as compat wrappers
4. Keep all existing individual tools as working compat dispatchers — zero regression
