# GEOX Orthogonal Tool Specification
**Version:** 2026.04.14-ORTHOGONAL  
**Seal:** 999_SEAL  

---

## 1. Orthogonality Axioms

1. **One tool = one atomic operation.** No tool may both observe and judge.
2. **One dimension = one namespace.** A MAP tool never computes WELL petrophysics.
3. **Six canonical verbs only:** `observe`, `interpret`, `compute`, `verify`, `judge`, `audit`.
4. **No aliases in canonical surface.** Legacy `geox_*` names are thin shims only.
5. **Metabolic tools are dimension-agnostic but scope-aware.** They consume outputs, they do not replace physics engines.

---

## 2. Canonical Verb Definitions

| Verb | Nature | Metabolic Stage | What it does |
|------|--------|-----------------|--------------|
| `observe` | Forward | `111` SENSE | Pull raw signal into the witness context. No interpretation. |
| `interpret` | Inverse / Linguistic | `333` THINK / `444` EXPLAIN | Infer structure or meaning from observations. |
| `compute` | Math / Forward | `222` REALITY / `333` THINK | Run mathematical or physical calculation on known inputs. |
| `verify` | Metabolizer | `555` HEART | Check consistency, bounds, or physical possibility. |
| `judge` | Metabolizer | `888` AUDIT | Render verdict (SEAL/QUALIFY/HOLD/VOID) with sovereign weight. |
| `audit` | Metabolizer | `888` AUDIT / `999` SEAL | Trace lineage, detect breaches, seal history. |

---

## 3. Orthogonal Tool Matrix

### 3.1 MAP (Spatial Intelligence)

| Verb | Tool | Description |
|------|------|-------------|
| observe | `map_observe_earth_signals` | Fetch live Earth signals (USGS, Open-Meteo, DEM, SAR). |
| observe | `map_observe_context_summary` | Query spatial fabric summary within bounds. |
| interpret | `map_interpret_georeference` | Bind raster/vector to real-world coordinates. |
| interpret | `map_interpret_coordinate_transform` | Project between CRS. |
| interpret | `map_interpret_causal_scene` | Synthesize causal narrative from spatial elements for 888_JUDGE. |
| compute | `map_compute_well_projection` | Project well trajectory into map coordinates. |
| verify | `map_verify_coordinates` | Check if coordinates are within valid geospatial bounds. |

**Deprecated aliases:** `map_earth_signals` → `map_observe_earth_signals`; `map_georeference` → `map_interpret_georeference`; `map_transform_coordinates` → `map_interpret_coordinate_transform`; `map_synthesize_causal_scene` → `map_interpret_causal_scene`; `map_project_well` → `map_compute_well_projection`; `map_verify_coordinates` → `map_verify_coordinates` (keep, canonical); `map_get_context_summary` → `map_observe_context_summary`; `map_render_scene_context` → `map_observe_context_summary` (merge — rendering is observation). `geox_verify_geospatial` → `map_verify_coordinates`.

### 3.2 EARTH3D (Volume & Structure)

| Verb | Tool | Description |
|------|------|-------------|
| observe | `earth3d_observe_volume` | Load 3D seismic or geological volume. |
| interpret | `earth3d_interpret_horizons` | Infer horizon surfaces from 3D data. |
| compute | `earth3d_compute_geometries` | Build architectural geometries from interpreted horizons. |
| verify | `earth3d_verify_structural_integrity` | Check model for structural paradoxes. |

**Deprecated aliases:** `earth3d_load_volume` → `earth3d_observe_volume`; `earth3d_model_geometries` → `earth3d_compute_geometries`.

### 3.3 SECTION (2D Subsurface)

| Verb | Tool | Description |
|------|------|-------------|
| observe | `section_observe_well_correlation` | Fetch raw correlation data between specified wells. |
| interpret | `section_interpret_strata` | Correlate stratigraphic units across wells in a section. |
| compute | `section_compute_profile` | Synthesize a 2D vertical profile from the Earth model. |
| verify | `section_verify_attributes` | Check extracted seismic features against transforms. |
| audit | `section_audit_transform_chain` | Audit the transform-chain for extracted features. |

**Deprecated aliases:** `section_synthesize_profile` → `section_compute_profile`; `section_audit_attributes` → `section_audit_transform_chain`; `geox_load_seismic_line` → `section_observe_well_correlation` or `earth3d_observe_volume` depending on data type; `geox_audit_attributes` → `section_audit_transform_chain`.

### 3.4 WELL (Borehole Intelligence)

| Verb | Tool | Description |
|------|------|-------------|
| observe | `well_observe_bundle` | Load LAS/DLIS log bundle into witness context. |
| interpret | `well_interpret_digitize_log` | Trace analog logs into governed digital outputs. |
| interpret | `well_interpret_sw_model` | Recommend Water Saturation model from formation context. |
| compute | `well_compute_petrophysics` | Execute physics-9 grounded petrophysical calculations. |
| verify | `well_verify_cutoffs` | Validate petrophysical cutoffs against regional norms. |
| verify | `well_verify_petrophysics` | Governance check for anomalous petrophysics (F9). |
| audit | `well_audit_qc` | Perform and log quality control on loaded logs. |

**Deprecated aliases:** `well_load_bundle` → `well_observe_bundle`; `well_digitize_log` → `well_interpret_digitize_log`; `well_select_sw_model` → `well_interpret_sw_model`; `well_compute_petrophysics` → `well_compute_petrophysics` (keep, canonical); `well_validate_cutoffs` → `well_verify_cutoffs`; `well_verify_petrophysics` → `well_verify_petrophysics` (keep); `well_qc_logs` → `well_audit_qc`; `geox_compute_petrophysics` → `well_compute_petrophysics`; `geox_validate_cutoffs` → `well_verify_cutoffs`.

### 3.5 TIME4D (Temporal Evolution)

| Verb | Tool | Description |
|------|------|-------------|
| interpret | `time4d_interpret_paleo` | Reconstruct paleo-geography at a specific time (Ma). |
| compute | `time4d_compute_burial` | Simulate sediment burial and thermal maturation. |
| verify | `time4d_verify_timing` | Check temporal relationship between trap formation and charge. |

**Deprecated aliases:** `time4d_reconstruct_paleo` → `time4d_interpret_paleo`; `time4d_simulate_burial` → `time4d_compute_burial`.

### 3.6 PROSPECT (Resource Evaluation)

| Verb | Tool | Description |
|------|------|-------------|
| interpret | `prospect_interpret_structural_candidates` | Generate structural trap candidates. |
| compute | `prospect_compute_feasibility` | Run technical and economic gating calculations. |
| verify | `prospect_verify_physical_grounds` | Check prospect against physical possibility. |
| judge | `prospect_judge_evaluation` | Evaluate hydrocarbon potential with 888_JUDGE verdict. |
| audit | `prospect_audit_risk_factors` | Audit GCOS and AC_Risk lineage. |

**Deprecated aliases:** `prospect_build_structural_candidates` → `prospect_interpret_structural_candidates`; `prospect_verify_feasibility` → `prospect_compute_feasibility` + `prospect_verify_physical_grounds` (split); `prospect_evaluate` → `prospect_judge_evaluation`; `geox_evaluate_prospect` → `prospect_judge_evaluation`; `geox_feasibility_check` → `prospect_compute_feasibility`.

### 3.7 PHYSICS (Governance & Math Backbone)

| Verb | Tool | Description |
|------|------|-------------|
| observe | `physics_observe_authoritative_state` | Fetch ground-truth physical state vector from vault. |
| compute | `physics_compute_stoiip` | Calculate Stock Tank Oil Initially In Place. |
| compute | `physics_compute_ac_risk` | Compute AC_Risk = U_phys × D_transform × B_cog. |
| verify | `physics_verify_parameters` | Check physical parameters for consistency (e.g. Gardner). |
| verify | `physics_verify_operation` | Check if operation adheres to safety and physical bounds. |
| judge | `physics_judge_verdict` | Execute Sovereign 888_JUDGE on a causal scene. |
| audit | `physics_audit_hold_breach` | Investigate if 888_HOLD conditions were bypassed. |

**Deprecated aliases:** `physics_fetch_authoritative_state` → `physics_observe_authoritative_state`; `physics_verify_physics` → `physics_verify_parameters`; `physics_validate_operation` → `physics_verify_operation`.

### 3.8 CROSS (Cross-Dimension Infrastructure)

| Verb | Tool | Description |
|------|------|-------------|
| observe | `cross_observe_evidence` | Retrieve evidence across dimensions for a target. |
| interpret | `cross_interpret_dimension_map` | Map relationships between dimensions. |
| verify | `cross_verify_health` | Health check for cross-dimension bridge. |
| audit | `cross_audit_transform_lineage` | Audit full transform lineage across dimensions. |

**Deprecated aliases:** `cross_evidence_get` → `cross_observe_evidence`; `cross_evidence_list` → `cross_observe_evidence` (merge); `cross_dimension_list` → `cross_interpret_dimension_map`; `cross_health` → `cross_verify_health`.

### 3.9 SYSTEM (Runtime & Metabolic Orchestration)

| Verb | Tool | Description |
|------|------|-------------|
| observe | `system_observe_registry` | List available tools and dimensions. |
| compute | `system_compute_metabolize` | Run the full 000–999 metabolic loop. |
| verify | `system_verify_health` | Runtime health check. |
| audit | `system_audit_session` | Seal session and write to VAULT999. |

**Deprecated aliases:** `geox_list_tools` → `system_observe_registry`; `geox_health` → `system_verify_health`; `geox_metabolize` → `system_compute_metabolize`; `geox_query_memory` → `cross_observe_evidence` or `system_audit_session` depending on use case.

---

## 4. Deprecation Matrix (Legacy → Canonical)

| Legacy Tool | Canonical Target | Action |
|-------------|------------------|--------|
| `geox_build_structural_candidates` | `prospect_interpret_structural_candidates` | Alias + warning |
| `geox_compute_ac_risk` | `physics_compute_ac_risk` | Alias + warning |
| `geox_compute_petrophysics` | `well_compute_petrophysics` | Alias + warning |
| `geox_compute_stoiip` | `physics_compute_stoiip` | Alias + warning |
| `geox_earth_signals` | `map_observe_earth_signals` | Alias + warning |
| `geox_evaluate_prospect` | `prospect_judge_evaluation` | Alias + warning |
| `geox_feasibility_check` | `prospect_compute_feasibility` | Alias + warning |
| `geox_fetch_authoritative_state` | `physics_observe_authoritative_state` | Alias + warning |
| `geox_georeference` | `map_interpret_georeference` | Alias + warning |
| `geox_load_seismic_line` | `section_observe_well_correlation` | Alias + warning |
| `geox_malay_basin_pilot` | `map_observe_context_summary` + `prospect_judge_evaluation` | Deprecate; move to data source |
| `geox_petrophysical_hold_check` | `well_verify_petrophysics` | Alias + warning |
| `geox_query_memory` | `system_audit_session` / `cross_observe_evidence` | Context-dependent alias |
| `geox_validate_cutoffs` | `well_verify_cutoffs` | Alias + warning |
| `geox_validate_operation` | `physics_verify_operation` | Alias + warning |
| `geox_verify_geospatial` | `map_verify_coordinates` | Alias + warning |
| `geox_verify_physics` | `physics_verify_parameters` | Alias + warning |
| `geox_vision_review` | `section_audit_transform_chain` (F9 check) | Alias + warning |
| `geox_audit_attributes` | `section_audit_transform_chain` | Alias + warning |
| `geox_audit_hold_breach` | `physics_audit_hold_breach` | Alias + warning |
| `geox_xxx` | — | Delete |
| `map_render_scene_context` | `map_observe_context_summary` | Merge |
| `map_synthesize_causal_scene` | `map_interpret_causal_scene` | Rename |
| `section_synthesize_profile` | `section_compute_profile` | Rename |
| `time4d_simulate_burial` | `time4d_compute_burial` | Rename |
| `well_digitize_log` | `well_interpret_digitize_log` | Rename |
| `well_load_bundle` | `well_observe_bundle` | Rename |
| `well_qc_logs` | `well_audit_qc` | Rename |
| `well_select_sw_model` | `well_interpret_sw_model` | Rename |

---

## 5. Cross-Dimension Composition Rules

Tools compose across dimensions through **evidence passing**, not functional aliasing.

```
EARTH3D.observe_volume
    ↓
EARTH3D.interpret_horizons
    ↓
SECTION.interpret_strata
    ↓
PROSPECT.interpret_structural_candidates
    ↓
PHYSICS.compute_stoiip
    ↓
PHYSICS.compute_ac_risk
    ↓
PROSPECT.judge_evaluation
    ↓
PHYSICS.judge_verdict
    ↓
CROSS.audit_transform_lineage
    ↓
SYSTEM.audit_session
```

**Rule:** A downstream tool may only consume the **output envelope** of an upstream tool. It may not re-implement the upstream tool's logic.

---

## 6. Metabolic Integration

Every `observe`, `interpret`, and `compute` tool must emit:

```json
{
  "transform_stack": ["observational", "ai_segmentation"],
  "u_phys_estimate": 0.35,
  "evidence_count": 12
}
```

Every `verify`, `judge`, and `audit` tool must consume:

```json
{
  "upstream_envelope": { ... },
  "ac_risk": 0.31,
  "verdict": "QUALIFY"
}
```

---

## 7. Net Result

- **Before orthogonality:** ~82 tools with aliases, overlaps, and namespace pollution.
- **After orthogonality:** ~36 canonical tools across 9 dimensions, each with a single metabolic role.
- **Civilization impact:** The metabolic loop (555–999) can now govern the forward/inverse chain (111–444) without ambiguity about which tool owns which decision.

---

**Sealed:** 2026-04-14T05:50:00Z  
**DITEMPA BUKAN DIBERI**
