# GEOX Tool Taxonomy
**Version:** 2026.04.14-METABOLIC  
**Seal:** 999_SEAL  

---

## 1. Classification Ontology

Every GEOX tool is classified along three axes:

### Axis A: Nature
- **`physics`** — Directly invokes or wraps a physics engine (OpenQuake, MODFLOW, GemPy, Darcy, etc.) or applies constitutive laws
- **`math`** — Applies mathematical transforms, statistics, geometry, compression, or inference operators
- **`linguistic`** — Operates on narrative, meaning, scene synthesis, or visual-language binding
- **`forward`** — Given model/parameter inputs, predicts an observable output
- **`inverse`** — Given observations, infers underlying parameters, structure, or state
- **`metabolizer`** — Part of the 000–999 metabolic loop: governance, AC_Risk, verdict, audit, hold, seal, calibration

### Axis B: Dimension
The canonical GEOX dimension this tool belongs to.

### Axis C: Metabolic Stage (000–999)
The primary arifOS metabolic stage where this tool executes:

| Stage | Name | Function |
|-------|------|----------|
| `000` | INIT | Session setup, registry, health, discovery |
| `111` | SENSE | Raw signal ingestion, loading, sensing |
| `222` | REALITY | Forward physics engine execution |
| `333` | THINK | Mathematical modeling, compression, inversion |
| `444` | EXPLAIN | Narrative generation, scene synthesis, unconstrained description |
| `555` | HEART | Constitutional sanity checks, validation, QC |
| `666` | ALIGN | ToAC evaluation, AC_Risk computation, confidence bounding |
| `777` | REASON | Dimension binding, naming, cross-product inheritance |
| `888` | AUDIT | Human veto, hold gates, breach detection, judgment |
| `999` | SEAL | Vault anchoring, memory storage, final verdict sealing |

---

## 2. Complete Tool Map

### Dimension: CROSS (Cross-Dimension Evidence)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_cross_dimension_list` | metabolizer | `000` / `777` | Discovery/registry of available dimensions |
| `geox_cross_evidence_list` | metabolizer | `777` | Lists evidence across dimensions for a target |
| `geox_cross_evidence_get` | metabolizer | `888` | Retrieves and audits cross-dimensional evidence |
| `geox_cross_health` | metabolizer | `000` | Health check for the cross-dimension bridge |

### Dimension: EARTH3D (Volume & Structure)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_earth3d_load_volume` | physics + forward | `111` / `222` | Loads 3D seismic or geological volume into memory |
| `geox_earth3d_interpret_horizons` | math + inverse | `333` | Infers horizon surfaces from 3D data |
| `geox_earth3d_model_geometries` | math + forward | `333` | Builds structural geometry models (GemPy) |
| `geox_earth3d_verify_structural_integrity` | physics + metabolizer | `555` | Validates structural model against physical feasibility |

### Dimension: MAP (Spatial Intelligence)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_map_earth_signals` | physics + forward | `111` | Fetches live geophysical signals (USGS, Open-Meteo) |
| `geox_map_verify_coordinates` | physics + forward | `222` | Validates coordinate systems and projections |
| `geox_map_transform_coordinates` | math + forward | `333` | Applies coordinate transformations |
| `geox_map_georeference` | math + forward | `333` / `777` | Binds raster/vector to real-world coordinates |
| `geox_map_project_well` | math + forward | `333` | Projects well paths onto map surfaces |
| `geox_map_get_context_summary` | linguistic + forward | `444` | Generates narrative summary of map context |
| `geox_map_render_scene_context` | linguistic + forward | `444` | Renders a described scene from map data |
| `geox_map_synthesize_causal_scene` | linguistic + forward | `444` | Synthesizes causal narrative from spatial patterns |

### Dimension: PHYSICS (Constitutional Physics & Verdict)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_physics_compute_stoiip` | physics + forward | `222` | Calculates stock tank oil initially in place |
| `geox_physics_verify_physics` | physics + metabolizer | `555` | Checks if an operation violates physical laws |
| `geox_physics_validate_operation` | metabolizer | `555` | Validates operational plan against physical constraints |
| `geox_physics_compute_ac_risk` | metabolizer | `666` | Computes AC_Risk for a physics product |
| `geox_physics_judge_verdict` | metabolizer | `888` | Renders constitutional verdict on a physics output |
| `geox_physics_audit_hold_breach` | metabolizer | `888` | Audits whether a HOLD gate was bypassed |
| `geox_physics_fetch_authoritative_state` | metabolizer | `888` | Retrieves latest authoritative state for appeal |
| `geox_physics_acp_register` | metabolizer | `000` | Registers an agent in the ACP (Anomalous Contrast Protocol) |
| `geox_physics_acp_submit` | metabolizer | `666` | Submits a proposal for ACP evaluation |
| `geox_physics_acp_check_convergence` | metabolizer | `777` | Checks if ACP agents have converged on consensus |
| `geox_physics_acp_status` | metabolizer | `000` | Queries ACP agent status |
| `geox_physics_acp_grant_seal` | metabolizer | `999` | Grants 999_SEAL to an ACP-validated output |

### Dimension: PROSPECT (Resource Evaluation)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_prospect_build_structural_candidates` | math + inverse | `333` | Generates multiple structural hypotheses from data |
| `geox_prospect_verify_feasibility` | metabolizer | `555` | Checks prospect feasibility against constraints |
| `geox_prospect_evaluate` | metabolizer | `666` / `777` | Evaluates prospect with GCOS, AC_Risk, and verdict |

### Dimension: SECTION (2D Subsurface)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_section_observe_well_correlation` | physics + forward | `111` | Loads and displays well-to-section correlations |
| `geox_section_interpret_strata` | math + inverse | `333` | Infers stratigraphic layers from section data |
| `geox_section_synthesize_profile` | math + forward | `333` | Synthesizes a synthetic geological profile |
| `geox_section_vision_review` | linguistic + inverse | `444` | Linguistic review of section interpretation quality |
| `geox_section_audit_attributes` | metabolizer | `888` | Audits section-derived attributes for governance |

### Dimension: TIME4D (Temporal Evolution)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_time4d_simulate_burial` | physics + forward | `222` | Simulates burial and thermal history |
| `geox_time4d_reconstruct_paleo` | math + inverse | `333` | Reconstructs paleo-environments from present data |
| `geox_time4d_verify_timing` | metabolizer | `555` | Validates temporal consistency of events |

### Dimension: WELL (Borehole Intelligence)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_well_load_bundle` | physics + forward | `111` | Loads LAS / DLIS / well log bundles |
| `geox_well_digitize_log` | math + forward | `333` | Digitizes scanned log curves |
| `geox_well_select_sw_model` | math + inverse | `333` | Infers best-fit water saturation model |
| `geox_well_compute_petrophysics` | physics + forward | `222` | Computes porosity, Sw, permeability from logs |
| `geox_well_qc_logs` | math + metabolizer | `555` | Quality-controls well log data |
| `geox_well_validate_cutoffs` | math + metabolizer | `555` | Validates petrophysical cutoffs |
| `geox_well_verify_petrophysics` | physics + metabolizer | `555` | Verifies petrophysical results against physics |
| `geox_petrophysical_hold_check` | metabolizer | `888` | 888_HOLD gate for well-based reserve estimates |

### Dimension: GOVERNANCE / SYSTEM (Metabolic Infrastructure)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `geox_list_tools` | metabolizer | `000` | Registry discovery |
| `geox_health` | metabolizer | `000` | Runtime health check |
| `geox_query_memory` | metabolizer | `999` / `000` | Retrieves past evaluations from GEOX memory |
| `geox_metabolize` | metabolizer | `666` – `999` | Full metabolic loop runner (system orchestrator) |
| `geox_set_scene` | linguistic + forward | `444` | Sets a narrative scene context |
| `geox_render_scene_context` | linguistic + forward | `444` | Renders scene (alias) |
| `geox_synthesize_causal_scene` | linguistic + forward | `444` | Synthesizes causal scene (alias) |
| `geox_xxx` | metabolizer | `000` | Test / stub tool |
| `geox_verify_canon` | metabolizer | `555` | Verifies output against canon rules |

### Dimension: LEGACY ALIASES (AAA Grade Surface)

These are deprecated aliases maintained for backward compatibility; they map to canonical tools above.

| Tool | Maps To | Nature | Metabolic Stage |
|------|---------|--------|-----------------|
| `geox_build_structural_candidates` | `geox_prospect_build_structural_candidates` | math + inverse | `333` |
| `geox_compute_ac_risk` | `geox_physics_compute_ac_risk` | metabolizer | `666` |
| `geox_compute_petrophysics` | `geox_well_compute_petrophysics` | physics + forward | `222` |
| `geox_compute_stoiip` | `geox_physics_compute_stoiip` | physics + forward | `222` |
| `geox_earth_signals` | `geox_map_earth_signals` | physics + forward | `111` |
| `geox_evaluate_prospect` | `geox_prospect_evaluate` | metabolizer | `666` / `777` |
| `geox_feasibility_check` | `geox_prospect_verify_feasibility` | metabolizer | `555` |
| `geox_fetch_authoritative_state` | `geox_physics_fetch_authoritative_state` | metabolizer | `888` |
| `geox_georeference` | `geox_map_georeference` | math + forward | `333` / `777` |
| `geox_load_seismic_line` | `geox_section_observe_well_correlation`* | physics + forward | `111` |
| `geox_malay_basin_pilot` | — (unique legacy resource) | physics + forward | `222` |
| `geox_validate_cutoffs` | `geox_well_validate_cutoffs` | math + metabolizer | `555` |
| `geox_validate_operation` | `geox_physics_validate_operation` | metabolizer | `555` |
| `geox_verify_geospatial` | `geox_map_verify_coordinates`* | physics + forward | `222` |
| `geox_verify_physics` | `geox_physics_verify_physics` | physics + metabolizer | `555` |
| `geox_vision_review` | `geox_section_vision_review`* | linguistic + inverse | `444` |
| `geox_audit_attributes` | `geox_section_audit_attributes`* | metabolizer | `888` |
| `geox_audit_hold_breach` | `geox_physics_audit_hold_breach` | metabolizer | `888` |

*Approximate functional equivalence, not exact identity.

---

## 3. Distribution by Nature

| Nature | Count | Examples |
|--------|-------|----------|
| `physics` | 18 | `geox_earth3d_load_volume`, `geox_physics_compute_stoiip`, `geox_time4d_simulate_burial` |
| `math` | 16 | `geox_earth3d_interpret_horizons`, `geox_map_transform_coordinates`, `geox_well_select_sw_model` |
| `linguistic` | 10 | `geox_map_synthesize_causal_scene`, `geox_section_vision_review`, `geox_set_scene` |
| `forward` | 24 | `geox_map_earth_signals`, `geox_well_compute_petrophysics`, `geox_physics_compute_stoiip` |
| `inverse` | 10 | `geox_prospect_build_structural_candidates`, `geox_time4d_reconstruct_paleo`, `geox_well_select_sw_model` |
| `metabolizer` | 38 | `geox_physics_compute_ac_risk`, `geox_prospect_evaluate`, `geox_cross_evidence_get` |

*Note: Tools can carry multiple natures (e.g., `physics + forward`, `math + inverse`).*

---

## 4. Distribution by Metabolic Stage

| Stage | Count | Primary Tool Examples |
|-------|-------|----------------------|
| `000` INIT | 8 | `geox_cross_dimension_list`, `geox_health`, `geox_physics_acp_register` |
| `111` SENSE | 6 | `geox_map_earth_signals`, `geox_well_load_bundle`, `geox_load_seismic_line` |
| `222` REALITY | 10 | `geox_physics_compute_stoiip`, `geox_time4d_simulate_burial`, `geox_well_compute_petrophysics` |
| `333` THINK | 14 | `geox_earth3d_interpret_horizons`, `geox_map_georeference`, `geox_prospect_build_structural_candidates` |
| `444` EXPLAIN | 8 | `geox_map_render_scene_context`, `geox_section_vision_review`, `geox_synthesize_causal_scene` |
| `555` HEART | 12 | `geox_physics_verify_physics`, `geox_well_qc_logs`, `geox_prospect_verify_feasibility` |
| `666` ALIGN | 8 | `geox_physics_compute_ac_risk`, `geox_prospect_evaluate`, `geox_metabolize` |
| `777` REASON | 6 | `geox_cross_evidence_list`, `geox_physics_acp_check_convergence`, `geox_prospect_evaluate` |
| `888` AUDIT | 10 | `geox_physics_judge_verdict`, `geox_section_audit_attributes`, `geox_petrophysical_hold_check` |
| `999` SEAL | 4 | `geox_physics_acp_grant_seal`, `geox_query_memory` |

---

## 5. The Metabolic Loop in Action

Example: Evaluating a seismic prospect through GEOX

```
000: geox_health ✅              → runtime ready
111: geox_load_seismic_line      → pull raw data (physics+forward)
222: geox_map_earth_signals           → fetch regional context (physics+forward)
333: geox_prospect_build_structural_candidates → generate hypotheses (math+inverse)
333: geox_earth3d_interpret_horizons  → model horizons (math+inverse)
444: geox_section_vision_review       → narrate interpretation (linguistic+inverse)
555: geox_prospect_verify_feasibility → constitutional QC (metabolizer)
555: geox_well_qc_logs                → validate well control (math+metabolizer)
666: geox_prospect_evaluate           → AC_Risk + GCOS (metabolizer)
666: geox_physics_compute_ac_risk     → ToAC score (metabolizer)
777: geox_cross_evidence_list         → gather cross-dimension evidence (metabolizer)
888: geox_physics_judge_verdict       → constitutional judgment (metabolizer)
999: geox_physics_acp_grant_seal      → vault seal (metabolizer)
     geox_query_memory            → archive for future recall (metabolizer)
```

---

## 6. Key Insight

> **Physics and math tools are the majority of the codebase, but metabolizers are the majority of the critical path.**  
> Without the metabolizers (555–999), the forward/inverse outputs are ungoverned and unsafe for civilization-scale decisions.

**The civilization-grade jump is to make every 111–444 tool emit into a 555–999 metabolizer before any human or downstream system acts on it.**

---

**Sealed:** 2026-04-14T05:45:00Z  
**DITEMPA BUKAN DIBERI**
