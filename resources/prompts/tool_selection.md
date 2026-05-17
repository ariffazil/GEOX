# GEOX Tool Selection Guide

## Well Sequence Stratigraphy Workflow
1. `geox_data_ingest_bundle` → get artifact_ref
2. `geox_data_qc_bundle` → verify artifact_ref
3. `geox_las_curve_inventory` → check available curves
4. `geox_well_analyze_sequence` → run L1-L3 pipeline
5. `geox_evidence_summarize_cross` → synthesize with other wells

## Prospect Evaluation Workflow
1. `geox_data_ingest_bundle` → load all wells/seismic
2. `geox_data_qc_bundle` → verify evidence
3. `geox_subsurface_generate_candidates` → build petrophysical model
4. `geox_map_context_scene` → get spatial context
5. `geox_time4d_analyze_system` → check charge timing
6. `geox_prospect_evaluate` → evaluate
7. `geox_prospect_judge_preview` → reversible preview
8. Human review → `geox_prospect_judge_seal` (irreversible)

## Failure Recovery
- `ARTIFACT_NOT_FOUND` → re-ingest with source_uri or content_base64
- `QC_ENGINE_FAILED` → check LAS path exists; try shallow QC
- `NO_VALID_EVIDENCE` → list missing_inputs_schema and ask for data
- `GR_PHYSICS_GUARD_FAILED` → run QC; check for bad GR values
- `PINN_PHYSICS_RESIDUAL_EXCEEDED` → 888HOLD: physics-constrained loss above
  threshold. Check: (a) Archie parameters match local calibration, (b) density-porosity
  crossplot consistent with mineral model, (c) Gardner relation within Vp range for formation.
- `WLFM_THIN_BED_FAILURE` → lithology output is PLAUSIBLE, not CLAIM. Route to
  `geox_evidence_contradiction_scan`. Apply high B_cog penalty.

## Foundation Model Routing

### Well-Log FM (WLFM + PINN)
- If `geox_well_analyze_sequence` outputs lithology with low confidence AND
  thinly interbedded interval → add WLFM token clustering as second opinion.
- If `geox_subsurface_generate_candidates` runs in PINN mode AND
  physics residual > threshold → 888HOLD before any Sw/porosity claim.
- Cross-well lithology correlation → use WLFM cross-well invariant embeddings
  as input to `geox_section_interpret_correlation`.

### Seismic FM (PRISM + TGS + SAM-Fault)
- If offshore_basin AND salt_present → route to TGS salt model (primary) + PRISM salt (secondary).
  - claim_limit: TGS 23% improvement floor; PRISM OOD 15% degradation on North Sea
- If fault_network_complexity > 0.7 → route to SAM-Fault (zero-shot) + PRISM fault ensemble.
  - claim_limit: SAM IoU 61.3% zero-shot; dense fault networks over-segmented — apply multi-scale coherence voting
  - Visual governance: SAM-style fault segmentation uses dip angle + azimuth + coherence cues as prompt inputs
- If horizon_continuity < 0.5 → route to PRISM horizon tracker.
  - claim_limit: MAE 2.1 samples; salt flanks require multi-attribute voting
- If out_of_distribution_basin AND no local calibration → 888HOLD: PRISM OOD 15% degradation — local well tie + FM fine-tuning required before seismic-only structural claims.
- Seismic-only structural interpretation → always DERIVED, never OBSERVED — always require well tie anchor.
