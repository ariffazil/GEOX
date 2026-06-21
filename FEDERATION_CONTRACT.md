# FEDERATION CONTRACT — GEOX (Earth Intelligence)

> **This organ operates under the arifOS Constitutional Federation.**
> **Machine-readable contract:** [arifOS/federation/GEOX.yaml](https://github.com/ariffazil/arifos/blob/main/federation/GEOX.yaml)
> **Canonical prose contract:** [ariffazil/arifos/FEDERATION_CONTRACT.md](https://github.com/ariffazil/arifos/blob/main/FEDERATION_CONTRACT.md)
> **Canonical status:** [ariffazil/arifos/FEDERATION_STATUS.md](https://github.com/ariffazil/arifos/blob/main/FEDERATION_STATUS.md)
> **Kernel canon:** [ariffazil/arifos/GENESIS/000_KERNEL_CANON.md](https://github.com/ariffazil/arifos/blob/main/GENESIS/000_KERNEL_CANON.md)

## Organ Identity

| Field | Value |
|-------|-------|
| **Organ** | GEOX — Earth Intelligence |
| **Repo** | `ariffazil/geox` |
| **Port** | 8081 |
| **Role** | Evidence-only earth coprocessor |
| **Canonical tools** | **54** (40 baseline + 14 W2-W13+ FORGE 2026-06-21) |
| **Floors enforced** | F1–F13 (delegated to arifOS kernel) |
| **Domain law** | NATURAL_LAW |
| **Identity anchor** | physics_manifest_hash (NOT constitution_hash) |
| **License** | Apache-2.0 (scientific tooling; federation governed by kernel AGPL-3.0) |

## Boundaries

**OWNS:** Well logs, seismic, petrophysics, basin screening, prospect evaluation, stratigraphic interpretation, claim generation, **multi-physics joint inversion (Physics9), CSEM/MT, biostrat, geomechanics, foundation model backing engines, doctrine layer (Gap X/3/5), and federation integration (WELL/WEALTH)**.
**NEVER:** Issue drilling decisions, authorize capital allocation, adjudicate constitutional verdicts, final-answer sovereign decisions, deploy FM weights without 888_HOLD, modify canonical tool registry without 888_HOLD.

## Four Transport Lanes

| Lane | Max Authority | Lease Required | Session Required | Tools |
|------|--------------|----------------|-----------------|-------|
| **Discovery** | OBSERVE | No | No | `geox_system_registry_status`, `geox_attribute_registry_list_tool`, `geox_basin_resolve`, `geox_query_intake`, `geox_query_macrostrat`, `geox_icgem_models` |
| **Evidence** | ANALYZE | No | No | `geox_data_ingest_bundle`, `geox_data_qc_bundle`, `geox_dst_ingest_test`, `geox_header_inspect`, `geox_las_inspect`, `geox_seismic_segy_inspect`, `geox_evidence_discover`, `geox_evidence_attach`, `geox_literature_ingest`, `geox_fault_stick_ingest_tool`, `geox_volume_frame_tool`, `geox_vision_perceptual_inventory`, `geox_vision_calibrate`, `geox_emag2_ingest` |
| **Reasoning** | ANALYZE | Yes | Yes | `geox_subsurface_generate_candidates`, `geox_subsurface_verify_integrity`, `geox_seismic_compute`, `geox_seismic_compute_attribute_tool`, `geox_sequence_interpret`, `geox_evidence_reason`, `geox_prospect_evaluate`, `geox_map_context_scene`, `geox_horizon_contrast_surface`, `geox_coord_transform_tool`, `geox_blockspace_resolution_tool`, `geox_blend_volume_tool`, `geox_basin_profile`, `geox_vision_minimax_inference`, `geox_vision_audit`, `geox_report_to_workflow`, `geox_abstraction_guard`, `geox_prithvi_eo_inference`, `geox_gravity_magnetic_forward`, `geox_mt_forward`, `geox_biostrat_constraint`, `geox_seismic_inversion`, `geox_geomechanics` |
| **Judgment** | GOVERNED | Yes | Yes | `geox_claim_create`, `geox_claim_validate`, `geox_claim_challenge`, `geox_claim_seal`, `geox_segy_export_tool`, `geox_doctrine_assumption_register`, `geox_doctrine_anti_beautiful_one`, `geox_doctrine_godel_review`, `geox_joint_inversion`, `geox_well_decision_class`, `geox_wealth_feed` |

## Envelope Compliance

Every GEOX tool output MUST conform to the universal envelope (`get_standard_envelope()` in `geox_core/enums/statuses.py`). Required fields:

- `execution_status` (SUCCESS | ERROR | HALT | RECOVERABLE_ERROR)
- `tool_class`
- `claim_state`
- `observed` / `derived` / `interpreted`
- `evidence_refs` / `artifact_refs`
- `claim_limits` / `missing_inputs_schema`
- `next_best_actions` / `audit_receipt`
- `human_final_authority` = "Arif"

## Authority Chain

```
Arif (F13 SOVEREIGN)
  → arifOS kernel (session → lease → authority → audit)
  → arif_kernel_route(mode=bridge, organ=geox)
  → GEOX tool (with lease-gated lane enforcement)
  → GEOX universal envelope (claim_state + evidence_refs)
  → arif_judge_deliberate
  → SEAL / QUALIFY / HOLD / VOID / 888_HOLD
  → arif_vault_seal (if SEAL verdict)
```

## Three Hard Separations

1. **Intelligence ≠ Authority** — GEOX says "Evidence supports interpretation X." arifOS says "This claim is qualified, not sealed, because gap Y remains."
2. **Tools ≠ Organs** — GEOX is an organ with identity, contract, health, schema hash, authority boundary, domain law. Not a pile of tools.
3. **Resources ≠ Memory (until sealed)** — Only SEALED or explicitly QUALIFIED claims enter durable arifOS memory.

## Contract Compliance

- [x] Points to kernel SoT from README
- [x] Machine-readable YAML at `arifOS/federation/GEOX.yaml`
- [x] Four-lane tool classification with authority gating
- [x] Universal output envelope (v0.81 + metabolic)
- [x] GENESIS/ doctrine (000-003)
- [x] Surfaces organ identity in /health
- [x] Routes irreversible actions through arifOS 888 JUDGE
- [x] Claim state machine (contracts/claim_state_machine.yaml)
- [x] Maintains AGENTS.md with federation boot sequence

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
