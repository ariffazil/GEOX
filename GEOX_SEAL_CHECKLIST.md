# GEOX SEAL Checklist
**Version:** 2026.04.14-CHECKLIST  
**Seal:** 999_SEAL  

---

## Axiom

> A `SEAL` verdict is not a pat on the back. It is a **liability contract**.  
> To grant `SEAL`, every metabolizer in the critical path for that dimension must have fired and passed.

---

## 1. Universal SEAL Preconditions (All Dimensions)

Before **any** dimension can receive `SEAL`, these 4 metabolizers must pass:

1. `physics_compute_ac_risk` → `AC_Risk < 0.15`
2. `cross_audit_transform_lineage` → no unverified transforms in the chain
3. `system_verify_health` → runtime and registry healthy
4. Vault anchor written → `merkle_root` is non-null

If any of these 4 fail, the ceiling verdict is `QUALIFY`.

---

## 2. Dimension-Specific SEAL Checklists

### MAP
**Target product:** Geological map, coordinate grid, spatial context

**Mandatory metabolizers:**
- [ ] `map_verify_coordinates` — CRS valid, bounds physically possible
- [ ] `map_interpret_georeference` — georeference RMSE within tolerance
- [ ] `physics_verify_parameters` — no projection/datum paradox
- [ ] `cross_audit_transform_lineage` — all coordinate transforms logged

**SEAL allowed if:** all above pass + universal preconditions met.

---

### EARTH3D
**Target product:** 3D structural model, mesh, volume

**Mandatory metabolizers:**
- [ ] `earth3d_verify_structural_integrity` — no overlapping faults, no negative volumes
- [ ] `physics_verify_parameters` — density/velocity models physically consistent
- [ ] `section_audit_transform_chain` — all 2D sections that seeded the 3D model are audited
- [ ] `cross_audit_transform_lineage` — full lineage from seismic volume → horizons → solids logged

**SEAL allowed if:** all above pass + universal preconditions met.

---

### SECTION
**Target product:** Seismic section, well correlation panel, stratigraphic correlation

**Mandatory metabolizers:**
- [ ] `section_verify_attributes` — seismic features match transform chain
- [ ] `section_audit_transform_chain` — every filter/resample/AI step logged and scored
- [ ] `geox_vision_review` (or `section_audit_transform_chain` F9 check) — VLM/AI interpretation has no hallucination flags
- [ ] `physics_verify_parameters` — time-depth conversion physically possible

**SEAL allowed if:** all above pass + universal preconditions met.

---

### WELL
**Target product:** Petrophysical interpretation, Sw model, log QC report

**Mandatory metabolizers:**
- [ ] `well_verify_petrophysics` — no anomalous physics violations (F9)
- [ ] `well_audit_qc` — LAS/DLIS data quality passed
- [ ] `well_verify_cutoffs` — cutoffs validated against regional norms
- [ ] `cross_audit_transform_lineage` — digitization → interpretation → model chain logged

**SEAL allowed if:** all above pass + universal preconditions met.

---

### TIME4D
**Target product:** Burial simulation, maturity map, paleo-reconstruction

**Mandatory metabolizers:**
- [ ] `time4d_verify_timing` — trap formation ≥ charge timing
- [ ] `physics_verify_parameters` — heat flow and sedimentation rates within physical bounds
- [ ] `cross_audit_transform_lineage` — age model → burial → maturity chain logged
- [ ] `physics_compute_ac_risk` — `U_phys` penalty applied if unvalidated heat-flow model used

**SEAL allowed if:** all above pass + universal preconditions met.

---

### PROSPECT
**Target product:** Prospect evaluation, GCOS, resource estimate

**Mandatory metabolizers:**
- [ ] `prospect_verify_physical_grounds` — trap geometry physically possible
- [ ] `prospect_compute_feasibility` — technical and economic gates passed
- [ ] `cross_audit_transform_lineage` — petroleum system → structure → volumetrics inheritance resolved
- [ ] `physics_judge_verdict` — 888_JUDGE on causal scene passed without HOLD overrides
- [ ] `physics_audit_hold_breach` — no prior HOLD breaches in this prospect lineage

**SEAL allowed if:** all above pass + universal preconditions met.

**Special rule:** If upstream `PETROLEUM_SYSTEM` product is `< SEAL`, `PROSPECT` ceiling is `QUALIFY` (Rule 3).

---

### PHYSICS (backbone products: STOIIP, physical parameter grids)

**Mandatory metabolizers:**
- [ ] `physics_verify_parameters` — all constitutive equations and parameters physically consistent
- [ ] `physics_verify_operation` — operation within safety bounds
- [ ] `cross_audit_transform_lineage` — full data → model → output chain logged
- [ ] `physics_fetch_authoritative_state` — ground-truth state vector consulted (or `null` documented with `U_phys` penalty)

**SEAL allowed if:** all above pass + universal preconditions met.

---

### HAZARD *(future dimension)*
**Target product:** PGA map, landslide susceptibility, tsunami inundation

**Mandatory metabolizers:**
- [ ] `hazard_verify_gmm_calibration` — GMPE validated against local strong-motion
- [ ] `hazard_audit_data_coverage` — sensor density meets minimum threshold
- [ ] `physics_compute_ac_risk` — `U_phys` includes data density and boundary-condition scores
- [ ] `cross_audit_transform_lineage` — OpenQuake → map → policy translation logged
- [ ] `physics_judge_verdict` — 888_JUDGE on evacuation trigger scenario

**SEAL ceiling:** `QUALIFY` for public maps; `SEAL` only for internal scenario studies.
**888_HOLD:** Mandatory for any product that influences public safety decisions.

---

### HYDRO *(future dimension)*
**Target product:** Aquifer model, drawdown forecast, saltwater intrusion front

**Mandatory metabolizers:**
- [ ] `hydro_verify_boundary_conditions` — recharge and boundaries physically plausible
- [ ] `hydro_audit_well_density` — observation well density meets model resolution requirements
- [ ] `physics_compute_ac_risk` — `U_phys` penalized if unvalidated MODFLOW parameter set used
- [ ] `cross_audit_transform_lineage` — DEM → well data → model → forecast chain logged
- [ ] `physics_judge_verdict` — 888_JUDGE on public depletion forecast

**SEAL ceiling:** `QUALIFY` for public forecasts; `SEAL` only for internal sensitivity studies.
**888_HOLD:** Mandatory for any product that influences public water management.

---

### CCS *(future dimension)*
**Target product:** CO₂ plume forecast, storage capacity cert, caprock integrity report

**Mandatory metabolizers:**
- [ ] `ccs_verify_caprock_integrity` — fault seal and thickness pass Mohr-Coulomb check
- [ ] `ccs_audit_hydro_dependency` — upstream HYDRO model verdict logged and ≥ `QUALIFY`
- [ ] `physics_compute_ac_risk` — `U_phys` penalized if TOUGH2/E300 unvalidated for this basin
- [ ] `cross_audit_transform_lineage` — mesh → EOS → plume → cert chain logged
- [ ] `physics_judge_verdict` — 888_JUDGE on storage permit scenario

**SEAL ceiling:** `QUALIFY` for regulatory filings; `SEAL` only after 5+ years of monitoring data.
**888_HOLD:** Mandatory for all certification and permit documents.

---

## 3. NO-GO Shortcuts

The following shortcuts automatically **void** any `SEAL` attempt:

| Shortcut | Consequence |
|----------|-------------|
| Skip `verify` before `SEAL` | `VOID` |
| Skip `audit` for time-bounded prediction | `VOID` |
| Override upstream `< SEAL` verdict via manual exception | `VOID` + breach logged |
| Grant `SEAL` with `AC_Risk ≥ 0.15` | `VOID` + operator accountability trace |
| Bypass 888_HOLD on mandatory list | `VOID` + F13 breach flag |

---

## 4. Enforcement

These checklists are enforced by the `prospect_judge_evaluation`, `physics_judge_verdict`, and `system_compute_metabolize` metabolizers at stage `888` AUDIT.

**Algorithm:**
```python
def can_grant_seal(product, dimension):
    # Universal
    if product.ac_risk >= 0.15: return False
    if not product.vault_anchor: return False
    if not runtime_healthy(): return False
    if not audit_transform_lineage(product): return False
    
    # Dimension-specific
    checklist = SEAL_CHECKLISTS[dimension]
    for metabolizer in checklist:
        if not metabolizer.has_fired_and_passed(product):
            return False
    
    # 888_HOLD mandatory list
    if dimension in MANDATORY_888HOLD and not product.hold_approved:
        return False
    
    return True
```

---

## 5. Summary

> **SEAL is not granted. It is earned by passing every metabolizer in the critical path.**

This checklist makes the taxonomy operational. It turns the 36 canonical tools from a clean namespace into a **hard enforcement scaffold** for civilization-grade decisions.

---

**Sealed:** 2026-04-14T06:00:00Z  
**DITEMPA BUKAN DIBERI**
