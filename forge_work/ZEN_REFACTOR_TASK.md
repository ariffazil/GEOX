# GEOX ZEN REFACTOR — Autonomous Execution Task

> **DITEMPA BUKAN DIBERI.** Non-stop until all contradictions resolved. All measurable.
> **Branch:** `refactor/zen-surface-reduction`
> **Started:** 2026-07-07
> **Sovereign:** Arif (F13, 888)

---

## THE CHAOS MAP (verified 2026-07-07)

### Measurement 1: Orphaned Code — 18,205 lines in 40 files

These files exist in `src/geox_mcp/tools/` but are imported by NEITHER `server.py` NOR `_register.py`. Dead code.

```
abduction.py analog_atlas.py anomalous_contrast.py claims.py compat.py
contrast_views.py crustal_domain_classify.py data.py dst.py
epistemic_client.py evidence_reason.py feature_joint_info.py
forward_model_synthetic.py geomechanics_unified.py geox_interpolate_grid.py
geox_panel_d.py geox_panel_d_async.py geox_seismic_vision_ai.py
horizon_contrast.py ingestion.py integration_wealth.py integration_well.py
macrostrat_client.py map_context.py paleoscan_forge.py provenance_bridge.py
provenance_gpts.py qc.py registry.py section.py seismic_compute.py
seismic_compute_unified.py seismic_well_tie.py spatial_block.py
stratigraphy.py sts.py time4d.py velocity_structural_qc.py
well_correlation.py workflow.py
```

### Measurement 2: Unified+Original Duplicates — 6,622 lines in 9 pairs

Original files that have `_unified.py` replacements. The unified version is what server.py imports.

| Original (DELETE) | Unified (KEEP) | Original Lines |
|---|---|---|
| `basin.py` | `basin_unified.py` | 1070 |
| `doctrine.py` | `doctrine_unified.py` | 193 |
| `evidence.py` | `evidence_unified.py` | 72 |
| `geomechanics.py` | `geomechanics_unified.py` | 138 |
| `petrophysics.py` | `petrophysics_unified.py` | 471 |
| `prospect.py` | `prospect_unified.py` | 772 |
| `seismic_compute.py` | `seismic_compute_unified.py` | 667 |
| `sequence.py` | `sequence_unified.py` | 1185 |
| `vision.py` | `vision_unified.py` | 771 |

### Measurement 3: Async+Sync Duplicates — 8 pairs

Server.py uses the async versions. Sync versions are dead.

| Sync (DELETE) | Async (KEEP) |
|---|---|
| `geox_3d_modeling_gempy.py` | `geox_3d_modeling_gempy_async.py` |
| `geox_geological_cognition.py` | `geox_geological_cognition_async.py` |
| `geox_panel_d.py` | `geox_panel_d_async.py` |
| `geox_physical_reality.py` | `geox_physical_reality_async.py` |
| `geox_segy_trace_reality.py` | `geox_segy_trace_reality_async.py` |
| `geox_wealth_bridge.py` | `geox_wealth_bridge_async.py` |
| `geox_well_tie_bruges.py` | `geox_well_tie_bruges_async.py` |
| `seismic_vision_ai.py` | `seismic_vision_ai_async.py` |

### Measurement 4: Tool Name Proliferation — 118 callable names for ~55 capabilities

- 64 SURFACE_TOOLS in registry.py
- 4 INTERNAL_TOOLS in registry.py
- 68 CANONICAL_PUBLIC_TOOLS (surface + internal)
- 50 CANONICAL_COMPAT_TOOLS (legacy aliases)
- 86 @mcp.tool decorators in server.py (18 NOT in any canonical list)

**Canonical duplicates (same capability, multiple names):**

| Capability | Names | Action |
|---|---|---|
| Land/water | `geox_atlas`, `geox_isitwater`, `geox_context_at_location` | Keep `geox_atlas`, delete others |
| Panel D | `geox_panel_d_render`, `geox_panel_d_render_mcp` | Keep `geox_panel_d_render`, delete `_mcp` |
| Physical reality | `geox_physical_reality_interpret` (TWICE in SURFACE_TOOLS) | Remove duplicate |
| Seismic compute | `geox_seismic_compute`, `geox_egs_seismic_compute` | Keep both (different scopes) |
| Macrostrat | `geox_macrostrat_calibrate`, `geox_query_macrostrat` | Keep `geox_macrostrat_calibrate`, delete `geox_query_macrostrat` |

**The 18 unlisted @mcp.tool in server.py:**
```
geox_bathymetry_ingest geox_climate_reanalysis geox_context_at_location
geox_earthquake_catalog geox_emag2_ingest geox_erddap_query
geox_geochem_kinetics geox_geochem_query geox_geology_map_query
geox_gravity_change_query geox_gravity_magnetic_forward geox_gravity_screen
geox_heatflow_query geox_hydrology_query geox_icgem_models geox_isitwater
geox_joint_inversion geox_judgment_preflight geox_lem_predict geox_mt_forward
geox_ocean_query geox_paleomag_query geox_plate_reconstruct
geox_prithvi_eo_inference geox_query_macrostrat geox_relief_ingest
geox_satellite_catalog geox_seismic_inversion geox_space_weather
geox_stress_query geox_uk_petroleum_query
```

### Measurement 5: Version Drift — 5 disagreeing sources

| Source | Version | Canonical Count |
|---|---|---|
| Live server /health | `v2026.07.06-phase3.1` | 68 |
| Agent card | `2026.07.06` | wrong skills/extensions |
| Capabilities JSON (disk) | `2026.07.06` | 68 |
| Capabilities MCP resource | `2026-06-28` | **30 (STALE)** |
| registry.py comments | `2026-07-03` | **58 then 45 (STALE)** |
| profile/status resource | `v2026.05.27` | **STALE** |
| identity resource | — | `identity_pass: false` |

### Measurement 6: Governance Duplication — 2,383 lines in 5 files

| File | Lines | Keep/Merge/Delete |
|---|---|---|
| `floor_enforcement.py` | 487 | KEEP (core) |
| `organ_governance.py` | 699 | KEEP (core) |
| `geox_middleware.py` | 415 | MERGE into floor_enforcement |
| `federation_safety.py` | 408 | AUDIT — check if orphaned |
| `pai_receipt.py` | 374 | AUDIT — check if orphaned |

### Measurement 7: Schema Bugs

| Tool | Issue |
|---|---|
| `geox_seismic_compute` | Arrays passed as strings via MCP — Pydantic validation error |
| `geox_simulate_*` (4 tools) | Return SESSION_REQUIRED for read-only simulation |
| `geox_map_*` | bbox max 8° not documented in tool description |
| `geox://profile/status` | Shows `v2026.05.27` — stale |

---

## EXECUTION PHASES — Measurable, Non-Stop

### PHASE 1: DELETE DEAD CODE (target: -24,827 lines)

**What:** Delete all orphaned files, unified originals, sync duplicates.
**How:** `git rm` each file. Verify server still starts. Run import check.
**Measure:** `wc -l` before and after on `src/geox_mcp/tools/`.
**Gate:** `python3 -c "from geox_mcp.server import mcp; print('OK')"` must pass.

### PHASE 2: UNIFY TOOL NAMES (target: 118 → ~65 names)

**What:** Remove duplicate tool registrations from server.py. Remove dead aliases from CANONICAL_COMPAT_TOOLS. Add the 18 unlisted tools to canonical or delete them.
**How:** Edit `server.py` to remove duplicate `@mcp.tool` registrations. Edit `registry.py` to remove dead compat aliases.
**Measure:** Count of `@mcp.tool` in server.py. Count of CANONICAL_COMPAT_TOOLS.
**Gate:** `curl http://localhost:8081/health` returns tools count matching registry.

### PHASE 3: SYNC VERSION SOURCES (target: 1 source of truth)

**What:** Make `registry.py` the single source. Auto-generate capabilities resource from registry. Fix agent card. Fix identity resource. Fix profile/status.
**How:** Edit `resources/__init__.py` to read from registry dynamically. Edit `.well-known/agent.json`. Fix identity invariant check.
**Measure:** All version strings across files match. `geox://capabilities` returns correct count. `geox://identity` returns `identity_pass: true`. `geox://surface/truth` returns PASS.
**Gate:** `read_mcp_resource(server="geox", uri="geox://capabilities")` returns 68 tools.

### PHASE 4: COLLAPSE GOVERNANCE (target: 2,383 → ~800 lines)

**What:** Merge `geox_middleware.py` into `floor_enforcement.py`. Audit `federation_safety.py` and `pai_receipt.py` — merge or delete.
**How:** Move middleware functions into floor_enforcement. Remove empty files.
**Measure:** `wc -l` on governance files. Must be ≤800 total.
**Gate:** Server starts, tools still governed.

### PHASE 5: FIX SCHEMA BUGS (target: 0 broken tools)

**What:** Fix `geox_seismic_compute` array validation. Document bbox limits in map tool descriptions. Fix `geox://profile/status` version.
**How:** Fix Pydantic model for seismic_compute. Add bbox docs to tool descriptions. Update profile version.
**Measure:** `geox_seismic_compute(mode="synthetic", vp=[2500,3000], rho=[2.1,2.3], depth=[1000,1100])` returns SUCCESS.
**Gate:** E2E test passes for all previously failing tools.

### PHASE 6: VERIFY — Final Measurement

**What:** Run the full E2E test suite. Compare before/after metrics.
**Measurements (all must improve):**

| Metric | Before | Target |
|---|---|---|
| Tool directory lines | 44,907 | ≤20,000 |
| Orphaned files | 40 | 0 |
| Duplicate implementations | 17 pairs | 0 |
| Callable tool names | 118 | ≤70 |
| Governance files | 5 (2,383 lines) | 2 (≤800 lines) |
| server.py lines | 4,558 | ≤2,000 |
| Version sources | 5 disagreeing | 1 |
| Broken tools | 2 | 0 |
| Surface truth lock | FAIL | PASS |
| Identity invariant | false | true |
| Capabilities resource | 30 (stale) | 68 (live) |

---

## AUTONOMOUS EXECUTION CONTRACT

1. **Non-stop.** Do not ask for permission between phases. Execute all 6 phases sequentially.
2. **Measurable.** Every phase produces before/after numbers. Log them.
3. **Reversible.** Every deletion is via `git rm` (recoverable). Commit after each phase.
4. **Verified.** After each phase, verify server starts and health endpoint responds.
5. **Logged.** Write results to `/root/A-FORGE/forge_work/2026-07-07/GEOX-ZEN-REFACTOR.md`.
6. **Sealed.** When done, report final metrics to sovereign.

**If server fails to start after any phase → `git checkout -- .` to revert that phase, log the failure, continue to next phase.**

---

## DO NOT TOUCH

- `server.py` tool implementations (the async functions) — only remove duplicate registrations
- `geox_core/` — core physics engine, not MCP surface
- `resources/` data files (YAML, JSON) — only fix metadata
- `.well-known/agent.json` structure — only fix version/counts
- Any file outside `src/geox_mcp/` except agent card and capabilities JSON

---

*DITEMPA BUKAN DIBERI. Entropy is the enemy. Clarity is the forge.*
