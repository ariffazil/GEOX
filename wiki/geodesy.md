# Geodesy & Position

Geodesy provides the coordinate foundation for all Earth Intelligence operations. Without precise positioning, no spatial analysis is meaningful.

## Overview

The Geodesy domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `coordinate_transform` | Transform between CRS | machine |
| `datum_alignment` | Align to common datum | machine, human |
| `gps_rtk` | Centimeter positioning | machine, infrastructure |
| `gravity_model` | Geoid and gravity computation | machine, orbital |

## Coordinate Reference Systems

A coordinate reference system (CRS) defines how positions relate to physical locations.

### Common CRS Types

- **Geographic**: Lat/Lon on ellipsoid (WGS84)
- **Projected**: Cartesian meters (UTM, State Plane)
- **Local**: Site-specific frames for engineering
- **Body-fixed**: Vehicle/ship-centered coordinates

### Transformation Pipeline

```
Raw GPS → WGS84 → ITRF → Local Datum → Projected Grid → Site Frame
```

Each transformation introduces error. GEOX tracks uncertainty through the chain.

## Datums

A datum defines the reference surface:
- **Horizontal**: Ellipsoid (WGS84, GRS80)
- **Vertical**: Geoid (EGM96, GEOID12B)

### Why Datums Matter

The same lat/lon can differ by meters depending on datum. Maritime operations especially require careful datum handling at boundaries.

## GPS RTK

Real-Time Kinematic GPS achieves centimeter-level accuracy:
- **Base station**: Known reference point
- **Rover**: Moving receiver
- **Corrections**: Carrier phase differences
- **Latency**: Sub-second for real-time applications

### RTK Requirements

- Clear sky view (multipath mitigation)
- Base-rover distance < 20km for best accuracy
- Dual-frequency receivers for ionospheric correction

## Gravity Model

Gravity varies by location due to:
- Earth mass distribution
- Topography
- Lateral density variations

### Applications

- **Orthometric heights**: True elevation above sea level
- **Geoid modeling**: Reference for vertical datums
- **Geophysical exploration**: Anomaly detection

## Constitutional Constraints

Geodesy operations must satisfy:
- **F8 Grounding**: Coordinate traceability maintained
- **F2 Truth**: Transformation uncertainty reported
- **F11 Coherence**: Consistent reference frames across operations

## See Also

- [Sensing & Signals](sensing.md) — Signal acquisition
- [Terrain & Surface](terrain.md) — DEM processing
- [Coordinate Transform](../../apps/site/skills/coordinate_transform.html) — Skill detail
