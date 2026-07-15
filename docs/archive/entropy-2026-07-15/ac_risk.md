# AC_Risk — Theory of Anomalous Contrast

## The Formula

```
AC_Risk = u_ambiguity × D_transform_effective × B_cog

u_ambiguity            = physical ambiguity (0.0 = certain, 1.0 = fully unknown)
D_transform_effective   = max(1.0, D_transform_base − evidence_credit)
B_cog                  = cognitive bias loading (0.20 = rational, 0.42 = ai_vision_only)
```

**Direction note:** Higher `u_ambiguity` = higher risk. This is intentional.
`u_ambiguity` = 1.0 means "we know nothing about physical reality" — maximally uncertain.
This naming was chosen over `u_evidence` to make the direction unambiguous per F2/F4 floors.

## Verdict Thresholds

| AC_Risk Range | Verdict | Action |
|---------------|---------|--------|
| `< 0.15` | `SEAL` | Proceed — low risk, physically grounded |
| `0.15 – 0.35` | `QUALIFY` | Proceed with documented caveats |
| `0.35 – 0.60` | `HOLD` | 888_HOLD enforced — human review required |
| `≥ 0.60` | `VOID` | Stop — physics violation or governance breach |

## D_transform — Transform Chain

Each display or interpretation transform applied to the data multiplies the distortion penalty:

| Transform | Multiplier |
|-----------|------------|
| `linear_scaling` | 1.00 |
| `contrast_stretch` | 1.05 |
| `agc_rms` | 1.15 |
| `agc_inst` | 1.25 |
| `spectral_balance` | 1.20 |
| `depth_conversion` | 1.30 |
| `ai_segmentation` | 1.40 |
| `vlm_inference` | 1.50 |

```
D_transform_base = ∏ (multiplier per transform)
D_transform_base = min(D_transform_base, 3.0)
```

## Evidence Credit

Each verified tool call in the GEOX pipeline reduces `D_transform`:

| Tool | Evidence Credit |
|------|----------------|
| `geox_well_load_bundle` | +0.20 |
| `geox_well_qc_logs` | +0.15 |
| `geox_well_compute_petrophysics` | +0.40 |
| `geox_seismic_load_line` / `load_volume` | +0.30 |
| `geox_section_interpret_strata` | +0.30 |

```
D_transform_effective = max(1.0, D_transform_base − total_credit)
```

Max credit = **1.35** → penalty floors at 1.0.

## B_cog — Cognitive Bias Loading

| Scenario | B_cog |
|---------|-------|
| `physics_validated` | 0.20 |
| `multi_interpreter` | 0.28 |
| `ai_with_physics` | 0.30 |
| `unaided_expert` | 0.35 |
| `ai_vision_only` | 0.42 (default) |

## Example: BEK-2 Prospect

Pipeline: `load_bundle` → `qc_logs` → `petrophysics` → `section_correlation`

```
u_ambiguity       = 0.45    (honest — real depth data loaded)
D_transform_base  = 1.0     (no seismic transforms)
evidence_credit   = 0.20 + 0.15 + 0.40 + 0.30 = 1.05
B_cog             = 0.30   (ai_with_physics)

D_transform_effective = max(1.0, 1.0 − 1.05) = 1.0
AC_Risk = 0.45 × 1.0 × 0.30 = 0.135

VERDICT: SEAL (0.135 < 0.15)
```

## Governance Layers

Every `compute_ac_risk_governed` call wraps AC_Risk with:

1. **ClaimTag** — CLAIM / PLAUSIBLE / HYPOTHESIS / UNKNOWN based on TEARFRAME scores
2. **TEARFRAME** — Truth (≥0.85 for CLAIM), Echo (≥0.75), Amanah (LOCK for SEAL), Rasa (context fit)
3. **Anti-Hantu** — F9 screen, fail-closed on empathy/feeling attribution
4. **888_HOLD** — enforced if: AC_Risk ≥ 0.35, `irreversible_action=True`, or `amanah_locked=False`
5. **VAULT999 payload** — full sealed record with all components
