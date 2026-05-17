# Hazards & Risk

Hazards threaten life and assets. GEOX enables comprehensive risk assessment across multiple hazard types.

## Overview

The Hazards domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `seismic_hazard` | Earthquake risk assessment | machine, environment |
| `landslide_susceptibility` | Slope failure mapping | machine, environment |
| `volcanic_threat` | Volcanic hazard assessment | machine, environment, human |
| `multi_risk` | Composite risk integration | machine, human |

## Seismic Hazard

Earthquake hazard depends on:
- **Source**: Fault location and activity
- **Path**: Wave propagation effects
- **Site**: Local amplification

### Products

- **Probabilistic hazard curves**: Exceedance probability vs intensity
- **Spectral acceleration maps**: Building code input
- **Scenario earthquakes**: Deterministic for planning
- **Ground motion prediction**: Attenuation models

## Landslide Susceptibility

Landslide risk depends on:
- **Terrain**: Slope, aspect, curvature
- **Material**: Lithology, soil depth
- **Hydrology**: Groundwater, drainage
- **Trigger**: Rainfall, earthquake, human

### Susceptibility vs Probability

- **Susceptibility**: Conditional on rainfall/earthquake
- **Probability**: Full probability including trigger likelihood
- **Risk**: Probability × consequences

## Volcanic Threat

Volcanic hazards include:
- **Lava flows**: Slow but destructive
- **Pyroclastic flows**: Fast and deadly
- **Ash fall**: Widespread disruption
- ** Lahars**: Volcanic mudflows

### Threat Assessment

- **Hazard zones**: Proximity to vent
- **Exposure**: Population and assets at risk
- **Warning time**: Available for evacuation
- **Probability**: Recurrence intervals

## Multi-Risk Assessment

Real risk is multi-hazard. Interactions matter:
- **Cascade**: Earthquake → landslide → debris flow
- **Compound**: Rainfall + storm surge + waves
- **Temporal**: Stacking events reduce resilience

### Risk Matrix

| Hazard | Likelihood | Severity | Risk Level |
|--------|------------|----------|------------|
| Flood | High | Medium | High |
| Earthquake | Low | Very High | High |
| Landslide | Medium | Medium | Medium |

## Constitutional Constraints

Hazard operations must satisfy:
- **F6 Harm**: All outputs inform life-safety decisions
- **F2 Truth**: No understatement of risk
- **F7 Confidence**: Uncertainty bounds required
- **F13 Sovereign**: Evacuation orders require human authorization

## See Also

- [Water & Hydrology](water.md) — Flood modeling
- [Governance & Policy](governance.md) — Constitutional gate
- [Seismic Hazard](../../apps/site/skills/seismic_hazard.html) — Skill detail
