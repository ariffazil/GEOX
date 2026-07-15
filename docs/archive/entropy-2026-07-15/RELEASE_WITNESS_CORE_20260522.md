# GEOX Witness Core — v2026.05.22

> **GEOX witnesses the Earth. It does not interpret it.**

Birthday release. Hard pruning executed. 36 tools → 10 tools.

---

## What Stayed (10 Tools)

| Tool | Axis | Purpose |
|------|------|---------|
| `geox_data_ingest_bundle` | observe | Ingest LAS, CSV, SEG-Y, structural payloads |
| `geox_data_qc_bundle` | verify | Depth monotonicity, null %, physical range checks |
| `geox_dst_ingest_test` | observe | Structured DST ingestion with derived metrics (observed only) |
| `geox_subsurface_generate_candidates` | reason | Petrophysics: Vsh, φ, Sw, net-pay, permeability (Physics-9 guarded) |
| `geox_subsurface_verify_integrity` | verify | Physics-9 boundary limit enforcement |
| `geox_seismic_well_tie_compute` | reason | Deterministic seismic-to-well tie (convolutional model) |
| `geox_time_depth_anchor` | verify | Checkshot/VSP empirical T-D anchoring |
| `geox_forward_model_synthetic` | reason | Well logs → AI → RC → wavelet → synthetic seismogram |
| `geox_anomalous_contrast_detector` | critique | Theory of Anomalous Contrast (ARIF FAZIL, 2025) |
| `geox_system_registry_status` | identity | Machine-checkable tool manifest and registry truth |

## What Was Cut (26 Tools)

**Interpretive / narrative:**
- `geox_process_abduction` — hypothesis generation
- `geox_evidence_contradiction_scan` — critique layer (belongs in arifOS)
- `geox_evidence_summarize_cross` — synthesis (belongs in arifOS)
- `geox_section_interpret_correlation` — correlation + GR motifs
- `geox_map_context_scene` — spatial scene rendering
- `geox_time4d_analyze_system` — burial / maturity / regime shifts (undetermined without evidence)
- `geox_vision_time_to_depth` — vision-based interpretation (JITU risk)

**Stratigraphy (sequence strat / packages):**
- `geox_well_compute_gr_bins`
- `geox_well_build_packages`
- `geox_well_infer_seq_strat`
- `geox_well_analyze_sequence`
- `geox_stratigraphy_run_pipeline`
- `geox_stratigraphy_preview_config`

**Judgment / governance (belongs in arifOS / APEX):**
- `geox_prospect_evaluate`
- `geox_prospect_judge_preview`
- `geox_prospect_judge_seal`

**Well correlation / inventory:**
- `geox_well_correlation_panel`
- `geox_las_curve_inventory`

**Background tasks:**
- `geox_task_ingest_las_batch`
- `geox_task_metabolize_basin`

**Registry / audit meta-tools:**
- `mcp_health_check`
- `geox_history_audit`
- `geox_contradiction_registry_status`
- `geox_test_receipt_status`
- `geox_bundle_security_audit`
- `geox_resource_registry_status`

## Architecture Changes

- **Physics-9 unified:** `geox_core/physics/` now owns state, parameters, drivers, guards.
- **Backward compatibility:** Old `physics9.py`, `physics_guard.py`, and engine shims re-export from new module.
- **No dynamic registration:** `register_well_tools`, `register_well_correlation_tools`, `register_stratigraphy_tools`, abduction tools, and background task tools removed from bootstrap.
- **Envelope stripped:** `earth_event_anchor` only injected for physics tools; registry tools return plain dicts.

## Test Result

58 passed, 1 skipped, 2 failed (pre-existing E2E artifact-missing failures unrelated to this release).

Anomalous Contrast tests: 5/5 passed — clean output contract verified.

## Cleaned Tools

### `geox_anomalous_contrast_detector`
- Stripped: `earth_event_anchor`, `nine_signal_mapping`, `metabolic`, `humility_score`, `claim_tag`, `claim_state`, `law_capsule`, `floors_checked`, `canon_9_touched`
- Returns: Plain dict with `anomalies`, `recommended_picks`, `volumetric_impact`, `physics` (equations, assumptions, limitations)
- Positioned as visual/physics anomaly detection, not geological interpretation

## Boundary Rule

> GEOX outputs physics-derived abstractions (impedance, reflection coefficient, effective stress, anomaly contrast). It never outputs depositional environment, systems tract, or geological narrative.

Interpretation belongs to arifOS (governance), WEALTH (valuation), or humans.
