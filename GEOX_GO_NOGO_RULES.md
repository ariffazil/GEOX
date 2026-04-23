# GEOX Go / No-Go Rules
**Version:** 2026.04.14-SOVEREIGN  
**Seal:** 999_SEAL  
**Motto:** *Ditempa Bukan Diberi* — Forged, Not Given

---

## Preamble

> GEOX’s mission is not "draw nice geology."  
> It is to make **high-stakes Earth decisions under uncertainty** without getting deceived by our own tools.

These 5 rules are **hard gates**. No map, model, section, or volume may influence drilling, CCS, hazard planning, or resource booking unless it has passed all five. Violation of any rule results in automatic **888_HOLD** or **VOID**.

---

## Rule 1: AC_Risk Must Be Computed and Verdict Must Be Known

> **No-Go:** Any product without an explicit `AC_Risk` score and `verdict ∈ {SEAL, QUALIFY, HOLD, VOID}` is **blocked** from influencing any decision.

**Go conditions:**
- `AC_Risk < 0.15` → `SEAL` (proceed with standard QC)
- `0.15 ≤ AC_Risk < 0.35` → `QUALIFY` (proceed with caveats; assumptions must be documented)
- `0.35 ≤ AC_Risk < 0.60` → `HOLD` (must pass 888_HOLD before externalization)
- `AC_Risk ≥ 0.60` → `VOID` (blocked; acquire better data or reduce transforms)

**Enforcement point:** Metabolic stage `666` ALIGN. The `physics_compute_ac_risk` metabolizer must run before any `judge` or `audit` tool.

---

## Rule 2: Physics Verification Must Precede Mathematical Interpretation

> **No-Go:** Any interpretation (`interpret` verb) or inverse inference that lacks a preceding `verify` check against physical laws is **blocked**.

**Go conditions:**
- For `EARTH3D.interpret_horizons`: `earth3d_verify_structural_integrity` must pass.
- For `SECTION.interpret_strata`: `section_verify_attributes` must pass.
- For `MAP.interpret_causal_scene`: `physics_verify_parameters` or `map_verify_coordinates` must pass.
- For `PROSPECT.interpret_structural_candidates`: `physics_verify_parameters` must pass.
- For AI/VLM-assisted interpretation (`section_vision_review`): F9 anti-hantu flag must be `false` or explicitly downgraded.

**Rationale:** Math and AI can fit patterns that violate physics. The `verify` gate ensures the pattern is physically possible before it becomes a belief.

**Enforcement point:** Metabolic stage `555` HEART. `physics_verify_parameters` and dimension-specific `verify` tools are mandatory preconditions for all `interpret` tools.

---

## Rule 3: Cross-Product Risk Inheritance Must Be Resolved

> **No-Go:** Any downstream product (e.g., CCS plan, prospect evaluation, city plan) cannot claim a verdict better than its worst upstream dependency.

**Go conditions:**
- `CCS` plan verdict ≤ `HYDRO` model verdict
- `PROSPECT` evaluation verdict ≤ `PETROLEUM_SYSTEM` map verdict
- `EARTH3D` model `U_phys` ≥ max(`SECTION` interpretation `U_phys`)
- `PLAY_FAIRWAY` verdict ≤ `GEOCHEM` anomaly map verdict
- City-planning product verdict = `HOLD` minimum if any `HAZARD` map is `HOLD`

**Rationale:** A perfect structural trap with unvalidated charge is worthless. A CCS plan on an unvalidated aquifer is dangerous.

**Enforcement point:** Metabolic stage `777` REASON. The `cross_audit_transform_lineage` metabolizer resolves the dependency graph and caps the verdict before `judge` tools run.

---

## Rule 4: Calibration Status Must Be Logged for Time-Bounded Predictions

> **No-Go:** Any product that predicts a future state (hazard, hydro drawdown, CCS plume, reservoir performance) without a calibration entry in the vault is auto-downgraded by one verdict band.

**Go conditions:**
- The vault contains at least one prior calibration event for the `(engine, basin, product_type)` triple.
- OR: The product explicitly carries `calibration_status: "unvalidated"` and `U_phys` is penalized by `+0.15`.
- If the most recent calibration event has `misprediction_ratio > 2.0`, the verdict is auto-downgraded one band (SEAL→QUALIFY, QUALIFY→HOLD, HOLD→VOID).

**Rationale:** An engine that has never been compared to reality is epistemically wounded. An engine that has severely mispredicted before is not trustworthy until recalibrated.

**Enforcement point:** Metabolic stage `666` ALIGN, during `U_phys` estimation.

---

## Rule 5: 888_HOLD Is Mandatory for Civilization-Scale Decisions

> **No-Go:** The following product types **must** route through `888_HOLD` and sovereign human veto before they can influence any external decision, **regardless of AC_Risk**:

1. **HAZARD** public maps or evacuation triggers
2. **HYDRO** public aquifer depletion / contamination forecasts
3. **CCS** certification documents, storage permits, or regulatory filings
4. **Resource Volumetrics / GDE** used for public reserves, investment, or farm-in decisions
5. **Geotechnical** safety certificates for infrastructure (tunnels, dams, nuclear siting)
6. **City-scale planning** products consuming any `HAZARD` or `HYDRO` output

**Go conditions:**
- `sovereign_approval.status == "APPROVED"` with a valid `ticket_id` from the arifOS approval boundary.
- The 888_HOLD ticket includes: product_id, AC_Risk components, floor flags, and a human-signed rationale.

**Rationale:** Some decisions affect cities, water security, and national reserves. No algorithm, however low its AC_Risk, may bypass human sovereignty on these outputs (F13).

**Enforcement point:** Metabolic stage `888` AUDIT. The `physics_judge_verdict` metabolizer auto-flags mandatory HOLD products before they reach `999` SEAL.

---

## Enforcement Summary

| Rule | Metabolic Stage | Violation Result |
|------|-----------------|------------------|
| 1: AC_Risk + verdict required | `666` ALIGN | `VOID` if missing |
| 2: Physics before interpretation | `555` HEART | `HOLD` if skipped |
| 3: Risk inheritance resolved | `777` REASON | Verdict capped to conservative minimum |
| 4: Calibration logged | `666` ALIGN | Auto-downgrade 1 band |
| 5: Mandatory 888_HOLD | `888` AUDIT | `HOLD` until human approval |

---

## What This Prevents

| Classic Failure | Rule That Blocks It |
|-----------------|---------------------|
| Over-confident seismic interpretation (pattern fitting without physics) | Rule 2 |
| Drilling a structurally perfect trap with no charge | Rule 3 |
| CCS certification on an unvalidated hydro model | Rule 3 |
| Evacuation trigger from an uncalibrated hazard engine | Rule 4 |
| Public reserve booking from a single optimistic model | Rule 5 |
| AI hallucination in VLM seismic review | Rules 1 + 2 + 5 |
| Map blunder propagating into city planning | Rules 3 + 5 |

---

## Final Verdict

These 5 rules turn GEOX from a technical geoscience stack into a **civilization-grade decision engine**. They do not make the geology prettier. They make the decision safer.

> **No AC_Risk, no action. No physics check, no interpretation. No inheritance resolution, no downstream seal. No calibration, no prediction. No human veto, no civilization-scale externalization.**

---

**Sealed:** 2026-04-14T05:55:00Z  
**DITEMPA BUKAN DIBERI**
