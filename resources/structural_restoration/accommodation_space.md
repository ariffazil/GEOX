# Accommodation Space Computation

## Concept

```
accommodation = elevation(restored_depositional_state)
              - elevation(reference_state)
```

The exact sign depends on the project's Z convention. GEOX must determine and record that convention before computing.

## What Accommodation IS

- The combined consequence of: tectonic subsidence + eustatic change + sediment loading + compaction + erosion + water depth + structural deformation
- An OBSERVATION of a geometric difference between two restoration states
- A necessary input for fill-ratio computation

## What Accommodation IS NOT

- A tectonic explanation (TECT-001)
- A primary cause (TECT-002)
- Equivalent to sediment thickness (SR_INV_005)
- Equivalent to basement subsidence (SR_INV_005)

## Mandatory Outputs

- Accommodation grid
- Invalid and negative-cell mask
- Subtraction order (which state minus which)
- Source lineage (input surface IDs and hashes)
- Scenario identifier
- Uncertainty reference

## Relationship to Existing Engines

GEOX currently has an accommodation engine at `src/geox_core/engines/stratigraphy/accommodation.py` that performs **forward physics simulation** (McKenzie subsidence + eustasy + Airy isostasy + Athy compaction). This is useful for forward modelling but is NOT the same as **state differencing** between two restoration states.

The structural restoration `compute_accommodation_space` tool operates on two input surfaces (source state and restored state) and computes their difference. The existing forward engine remains available for scenario modelling.
