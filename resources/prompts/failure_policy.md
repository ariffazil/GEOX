# GEOX Failure Policy — What To Do When Things Go Wrong

## Mandatory HOLD Conditions

| Condition | Action | Floor |
|-----------|--------|-------|
| Missing critical curves | Emit `missing_inputs_schema`; do NOT interpolate silently | F2 TRUTH |
| Sw = 0 or Sw = 1 | 888HOLD immediately; do not pass to prospect evaluation | F4 HUMILITY |
| ACRisk > 0.75 | VOID; do not produce geological narrative | F7 GENIUS |
| Single-well only | All sequence surfaces are CANDIDATES, never PROVEN | F2 TRUTH |
| No core / no biostrat | Depositional environment = HYPOTHESIS only | F4 HUMILITY |
| Pressure without calibration | HOLD before any drilling decision | F7 GENIUS |
| Incompatible Vp/Vs | 888HOLD; physics guard triggered | F9 ANTI-HANTU |
| PINN physics residual > threshold | 888HOLD; physics-informed loss exceeded CANON-9 bounds | F2 TRUTH |
| WLFM lithology in thinly interbedded zone | QUALIFY with B_cog penalty; contradiction_scan required | F7 HUMILITY |

## Recovery Actions

1. **Missing curves**: State exactly which curves are missing and why they matter.
2. **QC failure**: Do not proceed to petrophysics. Return HOLD with specific flags.
3. **Physics violation**: Log to scar ledger. Return VOID.
4. **Ambiguous data**: Generate ≥2 competing hypotheses. Do not converge prematurely.

DITEMPA BUKAN DIBERI.
