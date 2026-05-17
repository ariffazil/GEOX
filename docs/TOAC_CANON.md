# ToAC Canon — Theory of Anomalous Contrast
**Version:** 2026.04.14-AAA  
**Seal:** 999_SEAL — Heavy Witness  
**Motto:** *Ditempa Bukan Diberi* — Forged, Not Given  

---

## 1. Canonical Claim

> **ToAC is an epistemological operator, not a physics engine.**  
> It measures the risk that an earth product (map, model, section, volume, grid) has been distorted in the journey from raw signal to human decision.

**AC_Risk equation (canonical form):**

```
AC_Risk = U_phys × D_transform × B_cog
```

Where:
- `U_phys ∈ [0, 1]` — Physical model uncertainty (data sparsity, parameter ignorance, measurement error)
- `D_transform ∈ [1, 3]` — Distortion introduced by processing transforms (GMPE choice, meshing, downsampling, AI inference)
- `B_cog ∈ [0, 1]` — Cognitive bias exposure of the decision-maker (overconfidence, anchoring, single-model fixation)

**Domain:** `AC_Risk ∈ [0, 1]` after capping.

---

## 2. Component Measurement Protocol

### 2.1 U_phys — Physical Model Uncertainty

| Source | Proxy Metric | Measurement Rule |
|--------|-------------|------------------|
| Data density | `N_samples / N_grid_cells` | Log-scaled: `1 - exp(-λ * density)` |
| Parameter ignorance | `P(unmeasured) / P(total)` | Fraction of required parameters estimated rather than measured |
| Calibration residual | RMSE of validation holdout | `U_phys += 0.5 * (RMSE / signal_range)` |
| Boundary condition uncertainty | Qualitative score {low, medium, high} | Mapped to {0.05, 0.15, 0.30} |

**U_phys = 0** is theoretically unreachable (all models are incomplete).  
**U_phys > 0.60** triggers automatic **F7 Humility** escalation.

### 2.2 D_transform — Transform Distortion Factor

Each transform applied to raw data multiplies risk. Base rate = 1.0 (observational only).

| Transform | Risk Factor | Rationale |
|-----------|-------------|-----------|
| `observational` | 1.00 | No processing |
| `linear_scaling` | 1.05 | Minimal distortion |
| `contrast_stretch` | 1.10 | Visual bias introduced |
| `agc_rms` | 1.15 | Amplitude fidelity loss |
| `spectral_balance` | 1.20 | Phase/ amplitude trade-off |
| `depth_conversion` | 1.30 | Velocity model uncertainty |
| `ai_segmentation` | 1.40 | Black-box pattern matching |
| `vlm_inference` | 1.50 | Vision-language coupling adds semantic drift |
| `gmpe_selection` | 1.20 | Ground motion model epistemic uncertainty |
| `mesh_coarsening` | 1.25 | Numerical diffusion / loss of heterogeneity |
| `stochastic_realization` | 1.10 | Must be paired with ensemble count; single realization → 1.80 |
| `policy_translation` | 1.35 | Converting scientific output to actionable policy rule |

`D_transform = Π(factor_i)` capped at 3.0.

### 2.3 B_cog — Cognitive Bias Exposure

| Bias Scenario | B_cog | Trigger Condition |
|---------------|-------|-------------------|
| `physics_validated` | 0.20 | Independent physical check exists |
| `multi_interpreter` | 0.28 | 3+ independent interpretations converged |
| `ai_with_physics` | 0.30 | AI output constrained by physical rules |
| `unaided_expert` | 0.35 | Single expert, no cross-check |
| `ai_vision_only` | 0.42 | Pure pattern recognition, no physics guard |
| `executive_pressure` | 0.55 | Decision timeline shorter than validation time |
| `single_model_collapse` | 0.65 | Multiple hypotheses collapsed to one preferred model |

**B_cog > 0.50** triggers **F9 Anti-Hantu** review.

---

## 3. Verdict Calculus

| AC_Risk Range | Verdict | Human Action Required |
|---------------|---------|----------------------|
| `< 0.15` | **SEAL** | Proceed with standard QC |
| `0.15 — 0.34` | **QUALIFY** | Proceed with caveats; document assumptions |
| `0.35 — 0.59` | **HOLD** | **888_HOLD** — human review mandatory before externalization |
| `≥ 0.60` | **VOID** | Block. Interpretation unsafe. Acquire better data or reduce transforms. |

**Mandatory metadata on every product:**
```json
{
  "ac_risk": 0.31,
  "verdict": "QUALIFY",
  "components": {
    "u_phys": 0.45,
    "d_transform": 1.65,
    "b_cog": 0.42
  },
  "floors_active": ["F2", "F4", "F7", "F9"],
  "timestamp": "2026-04-14T05:30:00Z",
  "seal": "999_SEAL"
}
```

---

## 4. Constitutional Floor Mapping (F1–F13)

ToAC does not replace the floors. It **operationalizes** them into measurable AC_Risk sub-scores.

| Floor | ToAC Integration | Trigger |
|-------|-----------------|---------|
| **F1 Amanah** | Reversibility check on every transform | `D_transform` for destructive processing ≥ 1.80 → HOLD |
| **F2 Truth** | Grounding score = fraction of claims with direct evidence | `U_phys > 0.40` on a truth claim → VOID |
| **F3 Input Clarity** | Task definition entropy | Ambiguous query → SABAR (pre-execution) |
| **F4 Entropy** | Risk accumulation across tool chain | `Σ D_transform > 5.0` across session → HOLD |
| **F6 Harm/Dignity** | Maruah / safety impact assessment | HAZARD output touching populated area → mandatory F6 review |
| **F7 Humility** | Confidence bounding | `U_phys > 0.60` or stated confidence > evidence support → HOLD |
| **F8 Grounding** | Evidence count per tool call | `evidence_count < threshold` → downgrade verdict |
| **F9 Anti-Hantu** | Over-interpretation detection | `B_cog > 0.50` or extrapolation beyond calibration envelope → HOLD |
| **F11 Coherence** | Internal consistency | Contradictory outputs across tools → VOID |
| **F13 Sovereign** | Human veto gate | All dangerous-product externalizations route through 888_HOLD |

---

## 5. Naming-as-Creation Protocol

> **To name a dimension is to instantiate its possibility space, its rights, and its liabilities under arifOS constitutional law.**

### 5.1 Naming Ceremony (Canonical Steps)

1. **Declare the Name** — e.g., `HAZARD`, `HYDRO`, `CCS`
2. **Assign the Dimension Enum** — added to `GeoXAppManifest.Dimension`
3. **Bind Constitutional Floors** — mandatory floor set for all tools under this name
4. **Define the Physics Adapter Contract** — external engine(s) that compute the answer
5. **Set the 888_HOLD Conditions** — which outputs require human veto before release
6. **Seal with `999_SEAL`** — the dimension becomes live in the metabolic loop

### 5.2 Example: Naming `HAZARD`

```python
class Dimension(str, Enum):
    # ... existing dimensions
    HAZARD = "HAZARD"

# Constitutional binding
HAZARD_FLOORS = ["F1", "F2", "F5", "F6", "F8", "F13"]

# 888_HOLD trigger
HOLD_CONDITIONS = {
    "evacuation_zone": True,      # Any evacuation trigger → human veto
    "pga_public_map": True,       # Public-facing hazard map → human veto
    "internal_scenario": False,   # Internal sensitivity study → auto-QUALIFY/HOLD based on AC_Risk
}
```

---

## 6. Physics Adapter Contract

ToAC governs; physics engines compute. The contract between them is thin and strict.

### 6.1 Adapter Interface

Every physics adapter must implement:

```python
async def run_physics(
    inputs: AdapterInputs,
    config: AdapterConfig,
) -> AdapterResult:
    ...
```

Where `AdapterResult` must contain:

| Field | Type | Description |
|-------|------|-------------|
| `raw_output` | dict / array | Unprocessed engine output |
| `uncertainty_bands` | dict | P10/P50/P90 or std dev per grid point |
| `validation_residual` | float | RMSE or equivalent vs. held-out data |
| `transform_stack` | list[str] | Names of transforms applied |
| `computational_cost_ms` | int | Runtime for resource accounting |

### 6.2 Adapter → ToAC Handoff

```python
ac_risk, verdict = toac.evaluate(
    u_phys=estimate_from(adapter_result),
    d_transform=product_of(adapter_result.transform_stack),
    b_cog=detected_bias_scenario,
    domain="HAZARD",  # or HYDRO, CCS, etc.
)
```

### 6.3 Canonical Adapters (Reference List)

| Dimension | Physics Engine | Adapter Role |
|-----------|---------------|--------------|
| HAZARD | OpenQuake / ShakeMap | PSHA, scenario GMFs, damage/loss |
| HYDRO | MODFLOW / SEAWAT | Aquifer flow, saltwater intrusion |
| CCS | TOUGH2 / E300 CO₂ | Plume migration, storage capacity |
| GEOCHEM | sklearn / PySAL / ASTER toolkit | Anomaly thresholding, WofE |
| PETROLEUM_SYSTEM | PetroMod equivalent / Easy%Ro | Burial, maturity, migration |
| FRACTURE | ODA / DFN generator / WSM | Stress, fracture permeability |

**Rule:** Adapters are **thin**. No re-implementation of physics. Only:
- Input marshaling
- Output normalization
- Uncertainty extraction
- Transform logging

---

## 7. 888_HOLD Trigger Matrix

| Output Type | Auto-Externalize? | Condition |
|-------------|-------------------|-----------
| Public hazard map (PGA, tsunami) | **NO** | Always 888_HOLD |
| Aquifer depletion forecast (public) | **NO** | Always 888_HOLD |
| CCS certification document | **NO** | Always 888_HOLD |
| Internal prospect evaluation | YES | AC_Risk driven |
| Seismic structural model | YES | AC_Risk driven |
| Well log interpretation | YES | AC_Risk driven |
| Geochemical anomaly (internal) | YES | AC_Risk driven |
| DFN stochastic realization | YES | Ensemble required; single realization → HOLD |

---

## 8. Summary

**ToAC + Naming-as-Creation do not solve earth physics.**  
They solve the harder problem: **knowing whether the physics output is safe to trust, name, and act upon.**

With this canon:
- Every GEOX product carries an AC_Risk score.
- Every dimension is bound to F1–F13.
- Every physics adapter is a thin, governed wrapper.
- Civilization-critical outputs route through 888_HOLD.

**This is the path from E&P intelligence to planetary intelligence.**

---

**Sealed:** 2026-04-14T05:33:00Z  
**Architect:** arifOS / GEOX Earth Intelligence  
**DITEMPA BUKAN DIBERI**
