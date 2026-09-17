# GEOX Structural Restoration — Constitutional Principles

## Master Invariant

> **A restoration is admissible only when geometry, chronology, physics, uncertainty and provenance remain mutually consistent. A visually plausible map is not evidence of a valid restoration.**

## The Five Axes of Admissibility

Every restoration product must satisfy all five axes simultaneously:

| Axis | What it checks | Failure mode |
|------|---------------|--------------|
| **Geometry** | Spatial relationships, fold/fault kinematics, area balance | Self-intersection, non-closure, length/area mismatch |
| **Chronology** | Temporal ordering, age constraints, burial/uplift sequences | Age reversal, missing unconformity, stratigraphic disorder |
| **Physics** | Mass balance, thermal constraints, mechanical consistency | Negative thickness, overcompacted porosity, violated Mohr-Coulomb |
| **Uncertainty** | Quantified confidence bounds on each input | Missing uncertainty, hidden extrapolation, false precision |
| **Provenance** | Full chain from input data to output product | Untraced computation, mixed vintages, ghost data |

## Layer Architecture

```
F0: Tectonic Reasoning (tectonic_invariants.yaml)
    → Observation ≠ Explanation (TECT-001)
    → Accommodation is an effect (TECT-002)
    → Basin evolution is event sequence (TECT-006)

F1: Structural Restoration (this layer)
    → Immutable source geometry (SR_INV_001)
    → Consistent coordinate systems (SR_INV_003)
    → Fill-ratio diagnostic guard (SR_INV_007)

F2: Operational Invariants (geox_invariants.yaml)
    → Physics > Narrative (PI-01)
    → Mandatory epistemic tagging (EI-01)
    → Version-controlled outputs (OI-01)
```

## The Observation-Explanation Divide

Restoration products are **observations** of geometric differences between states. They are NOT explanations of tectonic causation.

- An accommodation map shows how much space was created. It does not say WHY.
- A fill-ratio map shows how much sediment filled that space. It does not say what FORCED it.
- A subsidence map shows how much basement moved. It does not say what MECHANISM moved it.

**GEOX invariant:** Restoration products are observations. Tectonic events are explanations. Never confuse the two.

## Accommodation ≠ Subsidence ≠ Thickness

These three quantities are related but distinct:

- **Accommodation** = space available for sediment (water depth + structural space)
  - Contains: subsidence + eustasy + compaction + erosion + water depth + structural deformation
- **Basement subsidence** = movement of the basement reference surface
  - Isolates: tectonic component of vertical movement
- **Sediment thickness** = total sediment deposited
  - May be less than, equal to, or (rarely) greater than accommodation

**GEOX invariant:** Never label sediment thickness, accommodation, and basement subsidence as equivalent quantities.

## The Fill-Ratio Diagnostic Guard

When fill_ratio > 1:

1. **Do NOT** immediately attribute to fault activity
2. **DO** run the10-item diagnostic checklist:
   - Reversed subtraction order
   - Inconsistent restoration ages
   - Mismatched surface extents
   - Unit or datum mismatch
   - Erosion or hiatus
   - Compaction model mismatch
   - Interpolation artefact
   - Missing structural displacement
   - Inappropriate facies/lithology assumption
   - Fault activity (LAST, after all above excluded)

**GEOX invariant:** fill_ratio > 1 triggers DIAGNOSTIC_REVIEW. It never returns FAULT_ACTIVITY_CONFIRMED without independent structural evidence.

## References

- Dahlstrom (1969) — Balanced cross-sections
- Steckler & Watts (1978) — Backstripping
- McKenzie (1978) — Rift subsidence
- Sclater & Christie (1980) — Compaction
- Athy (1930) — Porosity-depth law
- Jervey (1988) — Accommodation space
- Morley (2023, 2024) — NW Sabah NSPW
- Pilia et al. (2023) — Slab breakoff tomography
