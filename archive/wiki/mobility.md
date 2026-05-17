# Mobility & Routing

Mobility enables action. From evacuation routes to supply chains, understanding how to move through terrain is essential for operations.

## Overview

The Mobility domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `route_optimize` | Find optimal routes | machine, human |
| `accessibility_map` | Compute accessibility surfaces | machine, human |
| `traffic_pattern` | Analyze movement data | machine, infrastructure |
| `terrain_navigate` | Navigate unmapped terrain | machine, void |

## Route Optimization

Route optimization finds the best path given:
- **Origin/Destination**: Start and end points
- **Cost surface**: Friction or impedance
- **Constraints**: Time windows, vehicle limits
- **Objectives**: Shortest, fastest, safest

### Algorithms

- **Dijkstra**: Guaranteed shortest path
- **A***: Heuristic-guided search
- **Contraction hierarchies**: Fast for large networks
- **Genetic algorithms**: Multi-objective optimization

### Cost Factors

- Distance (always)
- Time (speed limits, traffic)
- Terrain (slope limits, roughness)
- Infrastructure (road class, bridge limits)
- Risk (hazard exposure, threat zones)

## Accessibility Mapping

Accessibility answers "how far?" not just "which route?"

### Isochrones

Lines of equal travel time from a point:
- 5-minute walk radius
- 30-minute drive shed
- Emergency response zones

### Friction Surfaces

Continuous cost surfaces for:
- Foot travel in rugged terrain
- Vehicle travel on roads
- Aircraft operations
- Maritime coastal navigation

## Traffic Pattern Analysis

Historical movement reveals:
- Peak congestion times
- Bottleneck locations
- Route preferences
- Anomaly detection

### Data Sources

- **AIS**: Vessel tracking (maritime)
- **ADS-B**: Aircraft tracking
- **Cellular**: Vehicle probes
- **Road sensors**: Loop detectors

## Terrain Navigation

When roads don't exist, terrain navigation applies.

### Challenges

- **No map**: Unmapped or poorly mapped areas
- **Obstacles**: Natural and artificial barriers
- **Degradation**: Weather-affected surfaces
- **Void**: GPS-denied or sensor-denied zones

### Approaches

- **DEM-based**: Slope and roughness constraints
- **Vision-based**: Camera and LiDAR SLAM
- **Dead reckoning**: Inertial navigation
- **Fallback stacking**: Multiple degraded modes

## Constitutional Constraints

Mobility operations must satisfy:
- **F1 Amanah**: Routes must be safe and reversible
- **F6 Harm**: No routes through hazard zones without warning
- **F13 Sovereign**: Critical evacuation routes require human authorization

## See Also

- [Terrain & Surface](terrain.md) — Roughness analysis
- [Governance & Policy](governance.md) — Rights mapping
- [Route Optimize](../../apps/site/skills/route_optimize.html) — Skill detail
