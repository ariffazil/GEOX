# Basement Subsidence Computation

## Concept

```
basement_subsidence = basement_position(state_t1) - basement_position(state_t0)
```

## Guardrails

- Basement surface must represent the same geological boundary in both states
- Report tectonic subsidence separately from stratigraphic accommodation
- Prevent comparison of inconsistent restoration times

## What Basement Subsidence IS

- An OBSERVATION of vertical movement of the basement reference surface
- A component that contributes to accommodation (along with eustasy, loading, etc.)
- More directly tied to tectonic processes than total accommodation

## What Basement Subsidence IS NOT

- A tectonic explanation (TECT-001 / TECT-003)
- The same as accommodation (SR_INV_005)
- The same as sediment thickness (SR_INV_005)

## NW Sabah Context

In NW Sabah, "Top Basement" may represent multiple geological elements (TECT-011): stretched continental crust, Dangerous Grounds blocks, igneous additions, older structural fabrics. Using a single basement surface as reference conflates distinct tectonic histories.

Before computing basement subsidence, assess basement heterogeneity and declare which basement element the surface represents.
