# ToAC AC_Risk Specification
**Version:** 2026.04.14-OPERATIONAL  
**Seal:** 999_SEAL  

---

## 1. Canonical Equation

```
AC_Risk = min(1.0, U_phys × D_transform × B_cog)
```

All three components are estimated **per product**, **per engine**, and **per basin** where calibration data exists.

---

## 2. U_phys — Physical Model Uncertainty

### 2.1 Inputs

U_phys is derived from five proxies, combined as a weighted sum:

| Proxy | Symbol | Weight | Measurement Rule |
|-------|--------|--------|------------------|
| Data sparsity | `S` | 0.30 | `1 - exp(-λ × N_samples / N_grid_cells)` |
| Parameter ignorance | `P` | 0.25 | Fraction of required params estimated (not measured) |
| Calibration residual | `R` | 0.25 | `RMSE / signal_range` capped at 1.0 |
| Boundary condition uncertainty | `B` | 0.15 | `{low: 0.05, medium: 0.15, high: 0.30}` |
| Temporal extrapolation | `T` | 0.05 | `(forecast_horizon / calibration_horizon) - 1` capped at 1.0 |

### 2.2 Formula

```
U_phys = 0.30*S + 0.25*P + 0.25*R + 0.15*B + 0.05*T
```

**Range:** `[0.0, 1.0]`  
**Interpretation:**
- `< 0.20` — Strong physical constraint, dense data
- `0.20–0.40` — Moderate uncertainty, standard exploration context
- `0.40–0.60` — Significant gaps, requires explicit documentation
- `> 0.60` — **F7 Humility escalation**: confidence claims must be bounded downward

---

## 3. D_transform — Transform Distortion Factor

### 3.1 Base Rate

`D_transform` starts at 1.0 (pure observation, no processing).

### 3.2 Transform Multipliers

| Transform | Factor |
|-----------|--------|
| observational | 1.00 |
| linear_scaling | 1.05 |
| contrast_stretch | 1.10 |
| agc_rms | 1.15 |
| spectral_balance | 1.20 |
| depth_conversion | 1.30 |
| gmpe_selection | 1.20 |
| mesh_coarsening | 1.25 |
| ai_segmentation | 1.40 |
| vlm_inference | 1.50 |
| policy_translation | 1.35 |
| stochastic_realization (single) | 1.80 |
| stochastic_realization (ensemble ≥ 20) | 1.10 |

### 3.3 Formula

```
D_transform = min(3.0, Π factor_i)
```

**Interpretation:**
- `< 1.5` — Minimal distortion, near-observational
- `1.5–2.0` — Moderate processing, standard for interpreted products
- `2.0–2.5` — Heavy AI or coarse modeling; caveat required
- `> 2.5` — **F9 Anti-Hantu escalation**: high risk of over-interpretation

---

## 4. B_cog — Cognitive Bias Exposure

### 4.1 Scenarios

| Scenario | B_cog | Condition |
|----------|-------|-----------|
| physics_validated | 0.20 | Independent physical check exists |
| multi_interpreter | 0.28 | 3+ independent interpretations |
| ai_with_physics | 0.30 | AI constrained by physics rules |
| unaided_expert | 0.35 | Single expert, no cross-check |
| ai_vision_only | 0.42 | Pure pattern recognition |
| executive_pressure | 0.55 | Timeline shorter than validation time |
| single_model_collapse | 0.65 | Multiple hypotheses collapsed to one |

### 4.2 Override Rules

- If `executive_pressure` AND `single_model_collapse` both apply, use **0.70**.
- If any `HOLD` condition exists in the 888_HOLD matrix, `B_cog` floor is **0.35**.

---

## 5. Calibration Loop

### 5.1 Trigger

A calibration event occurs whenever a time-bounded prediction is compared against a later measurement:
- HAZARD: predicted PGA vs. observed strong motion
- HYDRO: predicted drawdown vs. observed water level
- CCS: predicted plume extent vs. monitoring well CO₂
- PETROLEUM_SYSTEM: predicted maturity vs. well vitrinite reflectance

### 5.2 Misprediction Metric

```
Misprediction = |prediction - observation| / uncertainty_stated
```

Where `uncertainty_stated` is the P90–P10 range (or 2σ) that was reported with the product.

### 5.3 Feedback Rules

| Misprediction | Action |
|---------------|--------|
| `< 1.0` | Prediction within stated bounds. Slightly reduce `U_phys` by 5%. |
| `1.0–2.0` | Prediction outside stated bounds. Increase `U_phys` by 10%. Increase `D_transform` penalty for the specific transform stack by 0.05. |
| `> 2.0` | Severe under-confidence or model failure. Increase `U_phys` by 20%. Flag engine for basin-specific recalibration. Verdict for next run auto-downgraded one band. |

### 5.4 Basin-Specific Persistence

Calibration adjustments are stored per `(engine, basin, product_type)` triple in the arifOS vault:

```json
{
  "engine": "OpenQuake",
  "basin": "Malay_Basin",
  "product_type": "hazard_pga_map",
  "u_phys_adjustment": 0.12,
  "d_transform_penalty": 0.05,
  "calibration_events": 7,
  "last_updated": "2026-04-14T05:40:00Z"
}
```

---

## 6. Verdict Mapping

| AC_Risk | Verdict | Required Action |
|---------|---------|-----------------|
| `< 0.15` | **SEAL** | Proceed with standard QC |
| `0.15–0.34` | **QUALIFY** | Proceed with caveats; document assumptions |
| `0.35–0.59` | **HOLD** | **888_HOLD** mandatory before externalization |
| `≥ 0.60` | **VOID** | Block. Acquire better data or reduce transforms. |

### 6.1 Floor Overrides

- **F2 Truth** (`U_phys > 0.40` on a truth claim) → minimum verdict **QUALIFY**
- **F7 Humility** (`U_phys > 0.60`) → minimum verdict **HOLD**
- **F9 Anti-Hantu** (`B_cog > 0.50` OR `D_transform > 2.5`) → minimum verdict **HOLD**
- **F1 Amanah** (destructive transform stack ≥ 1.80) → minimum verdict **HOLD**
- **F13 Sovereign** (mandatory 888_HOLD product list) → always **HOLD** regardless of AC_Risk

---

## 7. Output Schema

Every GEOX product must emit:

```json
{
  "ac_risk": 0.31,
  "verdict": "QUALIFY",
  "components": {
    "u_phys": 0.45,
    "u_phys_proxies": {"S": 0.30, "P": 0.50, "R": 0.40, "B": 0.15, "T": 0.00},
    "d_transform": 1.65,
    "transform_stack": ["gmpe_selection", "mesh_coarsening"],
    "b_cog": 0.42,
    "bias_scenario": "ai_with_physics"
  },
  "floors_triggered": ["F2", "F4"],
  "calibration_status": {
    "engine": "OpenQuake",
    "basin": "Malay_Basin",
    "events": 7,
    "u_phys_adjustment": 0.12
  },
  "timestamp": "2026-04-14T05:40:00Z",
  "seal": "999_SEAL"
}
```

---

**Sealed:** 2026-04-14T05:40:00Z  
**DITEMPA BUKAN DIBERI**
