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
