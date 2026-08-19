---
id: geox-petrophysics-bounds
name: geox-petrophysics-bounds
version: "1.1.0-2026.08.17"
description: Bounded petrophysical transforms — Vsh, porosity, Sw, AI, permeability, QC. Only bounded deterministic transforms. No black-box predictions without physical constraints.
owner: GEOX
risk_tier: high
floor_scope: [F1, F2, F4, F7, F9]
autonomy_tier: T1
trigger_phrases:
  - "petrophysics"
  - "porosity"
  - "water saturation"
  - "Vsh"
  - "permeability"
  - "geox-petrophysics-bounds"
dependencies:
  mcp_servers:
    - geox
  skills:
    - geox-epistemic-ladder
---

# GEOX Petrophysics Bounds Skill

Only bounded deterministic transforms. No black-box predictions without physical constraints.

## Primary Tools

| Tool | Use for |
|------|---------|
| `geox_petrophysics` | Unified petrophysics: Vsh, porosity, Sw, permeability, net pay, LEM inference, QC |
| `geox_well_ingest` | Load LAS, SEG-Y, DST, deviation, tops |
| `geox_well_qc` | QC depth, curves, completeness |
| `geox_lem_predict` | LEM inference — predict rock properties from well log curves |
| `geox_geomechanics` | Bulk/shear/young modulus, poisson ratio, AI |

## Canonical Transforms

| Property | Inputs | Method | Bounds |
|----------|--------|--------|--------|
| Vsh | GR, SP, N | Linear, Larionov, Clavier, Steiber | 0.0 - 1.0 |
| Porosity (density) | RHOB, ρma, ρf | Density porosity | 0.0 - 0.45 |
| Porosity (neutron) | NPHI | Neutron porosity | 0.0 - 0.45 |
| Porosity (sonic) | DT | Wyllie, Raymer-Hunt | 0.0 - 0.40 |
| Sw (Archie) | Rt, phi, Rw, a, m, n | Archie | 0.0 - 1.0 |
| Sw (Simandoux) | Rt, phi, Rw, Vsh | Simandoux | 0.0 - 1.0 |
| Sw (Indonesia) | Rt, phi, Rw, Vsh | Indonesia | 0.0 - 1.0 |
| AI | Vp, ρ | Acoustic impedance | > 0 |
| VP/VS | Vp, Vs | Ratio | 1.4 - 3.0 |

## QC Rules

| Check | Condition | Action |
|-------|-----------|--------|
| GR range | 0 - 500 API | Flag out-of-range |
| RHOB range | 1.0 - 3.5 g/cc | Flag out-of-range |
| NPHI range | -0.05 - 0.60 V/V | Flag out-of-range |
| DT range | 40 - 300 us/ft | Flag out-of-range |
| Depth monotonicity | Strictly increasing | Reject if non-monotonic |
| Null % | < 50% | Warn if high null |
| Depth step consistency | ±10% of expected | Warn if irregular |

## LAS Validation

| Feature | LAS 2.0 | LAS 3.0 |
|---------|---------|---------|
| Version section | Required | Required |
| Well section | Required | Required |
| Curve section | Required | Required |
| Parameter section | Optional | Optional |
| ASCII data (~A) | Required | Required |
| Null value | -999.0 default | Explicit NULL field |
| Depth unit | From STRT/STOP/STEP suffix | From unit in curve header |

## Critical Rules

1. **Permeability transforms are ALWAYS empirical.** Never present permeability as deterministic truth.
2. **Pressure decisions need calibration.** Never use gradient alone without DST/MDT confirmation.
3. **Archie parameters are assumptions, not facts.** a=1.0, m=2.0, n=2.0 are defaults — document any deviation.
4. **Fluid contacts from logs need pressure confirmation.** Resistivity alone cannot prove fluid type.
5. **Every output declares equations_used, assumptions, and limitations.**

## Forbidden

- Predicting permeability without stating it's empirical
- Claiming fluid type from resistivity alone
- Sw > 1.0 or Sw < 0.0 without explanation
- Porosity > 0.45 without explanation (unconsolidated sands or fractured carbonates)

## Key References

- `/root/GEOX/src/geox_core/engines/petrophysics/` — bounded transform implementations
- `/root/GEOX/src/geox_mcp/tools/petrophysics.py` — MCP tool surface
- `/root/GEOX/canon9/` — CANON-9 physical bounds

**DITEMPA BUKAN DIBERI**
