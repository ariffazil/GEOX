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
| `cross_dimension_list` | metabolizer | `000` / `777` | Discovery/registry of available dimensions |
| `cross_evidence_list` | metabolizer | `777` | Lists evidence across dimensions for a target |
| `cross_evidence_get` | metabolizer | `888` | Retrieves and audits cross-dimensional evidence |
| `cross_health` | metabolizer | `000` | Health check for the cross-dimension bridge |

### Dimension: EARTH3D (Volume & Structure)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `earth3d_load_volume` | physics + forward | `111` / `222` | Loads 3D seismic or geological volume into memory |
| `earth3d_interpret_horizons` | math + inverse | `333` | Infers horizon surfaces from 3D data |
| `earth3d_model_geometries` | math + forward | `333` | Builds structural geometry models (GemPy) |
| `earth3d_verify_structural_integrity` | physics + metabolizer | `555` | Validates structural model against physical feasibility |

### Dimension: MAP (Spatial Intelligence)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `map_earth_signals` | physics + forward | `111` | Fetches live geophysical signals (USGS, Open-Meteo) |
| `map_verify_coordinates` | physics + forward | `222` | Validates coordinate systems and projections |
| `map_transform_coordinates` | math + forward | `333` | Applies coordinate transformations |
| `map_georeference` | math + forward | `333` / `777` | Binds raster/vector to real-world coordinates |
| `map_project_well` | math + forward | `333` | Projects well paths onto map surfaces |
| `map_get_context_summary` | linguistic + forward | `444` | Generates narrative summary of map context |
| `map_render_scene_context` | linguistic + forward | `444` | Renders a described scene from map data |
| `map_synthesize_causal_scene` | linguistic + forward | `444` | Synthesizes causal narrative from spatial patterns |

### Dimension: PHYSICS (Constitutional Physics & Verdict)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `physics_compute_stoiip` | physics + forward | `222` | Calculates stock tank oil initially in place |
| `physics_verify_physics` | physics + metabolizer | `555` | Checks if an operation violates physical laws |
| `physics_validate_operation` | metabolizer | `555` | Validates operational plan against physical constraints |
| `physics_compute_ac_risk` | metabolizer | `666` | Computes AC_Risk for a physics product |
| `physics_judge_verdict` | metabolizer | `888` | Renders constitutional verdict on a physics output |
| `physics_audit_hold_breach` | metabolizer | `888` | Audits whether a HOLD gate was bypassed |
| `physics_fetch_authoritative_state` | metabolizer | `888` | Retrieves latest authoritative state for appeal |
| `physics_acp_register` | metabolizer | `000` | Registers an agent in the ACP (Anomalous Contrast Protocol) |
| `physics_acp_submit` | metabolizer | `666` | Submits a proposal for ACP evaluation |
| `physics_acp_check_convergence` | metabolizer | `777` | Checks if ACP agents have converged on consensus |
| `physics_acp_status` | metabolizer | `000` | Queries ACP agent status |
| `physics_acp_grant_seal` | metabolizer | `999` | Grants 999_SEAL to an ACP-validated output |

### Dimension: PROSPECT (Resource Evaluation)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `prospect_build_structural_candidates` | math + inverse | `333` | Generates multiple structural hypotheses from data |
| `prospect_verify_feasibility` | metabolizer | `555` | Checks prospect feasibility against constraints |
| `prospect_evaluate` | metabolizer | `666` / `777` | Evaluates prospect with GCOS, AC_Risk, and verdict |

### Dimension: SECTION (2D Subsurface)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `section_observe_well_correlation` | physics + forward | `111` | Loads and displays well-to-section correlations |
| `section_interpret_strata` | math + inverse | `333` | Infers stratigraphic layers from section data |
| `section_synthesize_profile` | math + forward | `333` | Synthesizes a synthetic geological profile |
| `section_vision_review` | linguistic + inverse | `444` | Linguistic review of section interpretation quality |
| `section_audit_attributes` | metabolizer | `888` | Audits section-derived attributes for governance |

### Dimension: TIME4D (Temporal Evolution)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `time4d_simulate_burial` | physics + forward | `222` | Simulates burial and thermal history |
| `time4d_reconstruct_paleo` | math + inverse | `333` | Reconstructs paleo-environments from present data |
| `time4d_verify_timing` | metabolizer | `555` | Validates temporal consistency of events |

### Dimension: WELL (Borehole Intelligence)

| Tool | Nature | Metabolic Stage | Description |
|------|--------|-----------------|-------------|
| `well_load_bundle` | physics + forward | `111` | Loads LAS / DLIS / well log bundles |
| `well_digitize_log` | math + forward | `333` | Digitizes scanned log curves |
| `well_select_sw_model` | math + inverse | `333` | Infers best-fit water saturation model |
| `well_compute_petrophysics` | physics + forward | `222` | Computes porosity, Sw, permeability from logs |
| `well_qc_logs` | math + metabolizer | `555` | Quality-controls well log data |
| `well_validate_cutoffs` | math + metabolizer | `555` | Validates petrophysical cutoffs |
| `well_verify_petrophysics` | physics + metabolizer | `555` | Verifies petrophysical results against physics |
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
| `geox_build_structural_candidates` | `prospect_build_structural_candidates` | math + inverse | `333` |
| `geox_compute_ac_risk` | `physics_compute_ac_risk` | metabolizer | `666` |
| `geox_compute_petrophysics` | `well_compute_petrophysics` | physics + forward | `222` |
| `geox_compute_stoiip` | `physics_compute_stoiip` | physics + forward | `222` |
| `geox_earth_signals` | `map_earth_signals` | physics + forward | `111` |
| `geox_evaluate_prospect` | `prospect_evaluate` | metabolizer | `666` / `777` |
| `geox_feasibility_check` | `prospect_verify_feasibility` | metabolizer | `555` |
| `geox_fetch_authoritative_state` | `physics_fetch_authoritative_state` | metabolizer | `888` |
| `geox_georeference` | `map_georeference` | math + forward | `333` / `777` |
| `geox_load_seismic_line` | `section_observe_well_correlation`* | physics + forward | `111` |
| `geox_malay_basin_pilot` | — (unique legacy resource) | physics + forward | `222` |
| `geox_validate_cutoffs` | `well_validate_cutoffs` | math + metabolizer | `555` |
| `geox_validate_operation` | `physics_validate_operation` | metabolizer | `555` |
| `geox_verify_geospatial` | `map_verify_coordinates`* | physics + forward | `222` |
| `geox_verify_physics` | `physics_verify_physics` | physics + metabolizer | `555` |
| `geox_vision_review` | `section_vision_review`* | linguistic + inverse | `444` |
| `geox_audit_attributes` | `section_audit_attributes`* | metabolizer | `888` |
| `geox_audit_hold_breach` | `physics_audit_hold_breach` | metabolizer | `888` |

*Approximate functional equivalence, not exact identity.

---

## 3. Distribution by Nature

| Nature | Count | Examples |
|--------|-------|----------|
| `physics` | 18 | `earth3d_load_volume`, `physics_compute_stoiip`, `time4d_simulate_burial` |
| `math` | 16 | `earth3d_interpret_horizons`, `map_transform_coordinates`, `well_select_sw_model` |
| `linguistic` | 10 | `map_synthesize_causal_scene`, `section_vision_review`, `geox_set_scene` |
| `forward` | 24 | `map_earth_signals`, `well_compute_petrophysics`, `physics_compute_stoiip` |
| `inverse` | 10 | `prospect_build_structural_candidates`, `time4d_reconstruct_paleo`, `well_select_sw_model` |
| `metabolizer` | 38 | `physics_compute_ac_risk`, `prospect_evaluate`, `cross_evidence_get` |

*Note: Tools can carry multiple natures (e.g., `physics + forward`, `math + inverse`).*

---

## 4. Distribution by Metabolic Stage

| Stage | Count | Primary Tool Examples |
|-------|-------|----------------------|
| `000` INIT | 8 | `cross_dimension_list`, `geox_health`, `physics_acp_register` |
| `111` SENSE | 6 | `map_earth_signals`, `well_load_bundle`, `geox_load_seismic_line` |
| `222` REALITY | 10 | `physics_compute_stoiip`, `time4d_simulate_burial`, `well_compute_petrophysics` |
| `333` THINK | 14 | `earth3d_interpret_horizons`, `map_georeference`, `prospect_build_structural_candidates` |
| `444` EXPLAIN | 8 | `map_render_scene_context`, `section_vision_review`, `geox_synthesize_causal_scene` |
| `555` HEART | 12 | `physics_verify_physics`, `well_qc_logs`, `prospect_verify_feasibility` |
| `666` ALIGN | 8 | `physics_compute_ac_risk`, `prospect_evaluate`, `geox_metabolize` |
| `777` REASON | 6 | `cross_evidence_list`, `physics_acp_check_convergence`, `prospect_evaluate` |
| `888` AUDIT | 10 | `physics_judge_verdict`, `section_audit_attributes`, `geox_petrophysical_hold_check` |
| `999` SEAL | 4 | `physics_acp_grant_seal`, `geox_query_memory` |

---

## 5. The Metabolic Loop in Action

Example: Evaluating a seismic prospect through GEOX

```
000: geox_health ✅              → runtime ready
111: geox_load_seismic_line      → pull raw data (physics+forward)
222: map_earth_signals           → fetch regional context (physics+forward)
333: prospect_build_structural_candidates → generate hypotheses (math+inverse)
333: earth3d_interpret_horizons  → model horizons (math+inverse)
444: section_vision_review       → narrate interpretation (linguistic+inverse)
555: prospect_verify_feasibility → constitutional QC (metabolizer)
555: well_qc_logs                → validate well control (math+metabolizer)
666: prospect_evaluate           → AC_Risk + GCOS (metabolizer)
666: physics_compute_ac_risk     → ToAC score (metabolizer)
777: cross_evidence_list         → gather cross-dimension evidence (metabolizer)
888: physics_judge_verdict       → constitutional judgment (metabolizer)
999: physics_acp_grant_seal      → vault seal (metabolizer)
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
