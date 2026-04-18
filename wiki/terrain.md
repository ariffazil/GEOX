# Terrain & Surface

Terrain shapes all surface operations. Understanding elevation, roughness, and drainage is essential for mobility, hazard assessment, and resource management.

## Overview

The Terrain domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `dem_processing` | Process elevation models | machine |
| `surface_classify` | Classify land cover | machine, orbital |
| `roughness_analysis` | Compute terrain roughness | machine |
| `slope_aspect` | Derive slope and aspect | machine, human |

## Digital Elevation Models

DEMs represent terrain as regular grids of elevation values.

### DEM Sources

| Source | Resolution | Coverage | Cost |
|--------|------------|----------|------|
| SRTM | 30m | Global | Free |
| ALOS PALSAR | 12m | Global | Free |
| LiDAR | 1-10m | Regional | High |
| TanDEM-X | 12m | Global | Commercial |

### Void Filling

DEMs have voids (no-data areas) from:
- Radar shadow
- Water bodies
- Processing failures

GEOX uses geodesic interpolation to fill voids while tracking confidence.

## Surface Classification

Land cover classification enables:
- Urban/rural discrimination
- Agricultural mapping
- Forest vs. non-forest
- Wetland delineation

### Classification Schemes

- **LULC**: Land Use/Land Cover (Anderson scheme)
- **Corine**: European inventory
- **NLCD**: US National Land Cover Database
- **Custom**: Domain-specific taxonomies

## Roughness Analysis

Terrain roughness affects:
- **Mobility**: Vehicle traverse speed
- **Radar**: Backscatter simulation
- **Hydrology**: Flow resistance
- **Acoustics**: Sound propagation

### Roughness Metrics

- **RMS Height**: Standard deviation of elevation
- **Correlation Length**: Spatial autocorrelation
- **Breakpoint Frequency**: Terrain texture scale

## Slope & Aspect

Derived from DEM gradient:
- **Slope**: Maximum rate of elevation change (degrees or %)
- **Aspect**: Direction of maximum descent (compass bearing)

### Applications

- **Solar**: Aspect affects irradiance
- **Hydrology**: Slope controls runoff velocity
- **Agriculture**: Slope limits mechanization
- **Construction**: Slope affects stability

## Constitutional Constraints

Terrain operations must satisfy:
- **F6 Harm**: No operations that exacerbate landslides
- **F8 Grounding**: DEM accuracy validated before use
- **F11 Coherence**: Multi-scale terrain consistent

## See Also

- [Water & Hydrology](water.md) — Drainage analysis
- [Mobility & Routing](mobility.md) — Route optimization
- [DEM Processing](../../apps/site/skills/dem_processing.html) — Skill detail
