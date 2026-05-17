# Water & Hydrology

Water is the lifeblood of Earth's systems. Understanding hydrology enables flood prediction, resource management, and coastal operations.

## Overview

The Water domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `flood_model` | Simulate flood scenarios | machine, environment |
| `watershed_delineate` | Define drainage basins | machine |
| `drainage_analysis` | Analyze flow patterns | machine |
| `tidal_model` | Model tides and surge | machine, environment |

## Watershed Delineation

A watershed is the land area that drains to a common outlet.

### Delineation Process

1. Fill sinks in DEM
2. Compute flow direction (D8, D-inf)
3. Accumulate flow to find streams
4. Define pour points at outlets
5. Trace upstream to basin boundaries

### Applications

- **Resource management**: Freshwater allocation
- **Hazard assessment**: Flood-prone areas
- **Ecosystem services**: Habitat delineation

## Drainage Analysis

Flow patterns reveal:
- Stream networks and stream order
- Flow accumulation (upstream area)
- Drainage density
- Basin response time

### Flow Routing

- **D8**: Single flow direction (steepest descent)
- **D-inf**: Multiple flow directions
- **MFD**: Multiple flow direction with slope weighting

## Flood Modeling

Flood models predict:
- **Extent**: Which areas inundate
- **Depth**: Water depth at each point
- **Velocity**: Flow speed (critical for life safety)
- **Arrival time**: When flooding begins

### Model Types

- **1D**: Channel-centered, efficient
- **2D**: Full grid simulation, computationally expensive
- **Hybrid**: 1D channel + 2D floodplain

### Inputs Required

- DEM (terrain)
- Land cover (roughness)
- Rainfall/flow data (forcing)
- Infrastructure (bridges, culverts)

## Tidal Modeling

Tides affect:
- **Navigation**: Clearance under bridges
- **Coastal operations**: Beach landing
- **Harbor design**: Quayside elevation
- **Offshore**: Riser tension

### Tidal Components

- **Astronomical**: M2, S2, N2, K1, O1 (lunar/solar)
- **Meteorological**: Storm surge from weather
- **Shelf resonance**: Coastal amplification

## Constitutional Constraints

Water operations must satisfy:
- **F6 Harm**: Flood models inform evacuation (life safety)
- **F2 Truth**: No underestimation of flood risk
- **F13 Sovereign**: Major dam/release decisions require human approval

## See Also

- [Terrain & Surface](terrain.md) — DEM processing
- [Hazards & Risk](hazards.md) — Multi-risk assessment
- [Flood Model](../../apps/site/skills/flood_model.html) — Skill detail
