---
id: flood_model
name: Flood Modeling
domain: water
substrates: [machine, environment]
complexity: 4
mcp_resource: geox://resources/water/flood
verdict_classes: [888_SEAL, 888_QUALIFY, 888_HOLD]
---

# Flood Modeling

Simulate flood extent and depth from rainfall or breach events.

## Description

Executes hydraulic and hydrodynamic flood simulations using input digital elevation models, land cover roughness coefficients, and forcing data (rainfall or dam breach scenarios). Returns inundation extent, depth grids, and arrival time maps.

This skill implements both 1D river routing and 2D overland flow solvers. For operational use, the 2D solver is recommended for complex terrain or urban environments. The skill handles both fluvial (river) and pluvial (surface water) flooding mechanisms.

## Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `dem` | Raster | Digital elevation model (resampled to simulation grid) |
| `hydrology` | Vector | River network and catchment boundaries |
| `forcing_data` | TimeSeries | Rainfall hyetograph or breach hydrograph |
| `roughness` | Table | Manning's n coefficients by land cover class |

## Outputs

| Artifact | Type | Description |
|----------|------|-------------|
| `flood_extent` | Raster | Binary inundation mask (GeoTIFF) |
| `depth_grid` | Raster | Maximum water depth raster (meters) |
| `arrival_time` | Raster | Time to first inundation per cell (hours) |

## Dependencies

- [dem_processing](dem_processing.md) — Prepared elevation surface
- [drainage_analysis](drainage_analysis.md) — River network and flow paths

## Use Cases

- Emergency response planning for flood-prone regions
- Dam break inundation mapping
- Climate change impact assessment on flood regimes
- Insurance risk modeling

## Risk Classification

Flood modeling can trigger **888 HOLD** when:

- Simulation results will inform evacuation decisions
- Input data quality is below F2 Truth threshold
- Model parameters are outside calibrated ranges

## MCP Usage

```json
{
  "tool": "geox_score_risk",
  "arguments": {
    "scenario_type": "flood",
    "parameters": {
      "return_period": 100,
      "rainfall_mm": 250,
      "duration_hours": 24
    }
  }
}
```

## Telemetry Example

```json
{
  "epoch": "2026-04-11T08:30:00+08:00",
  "capability_id": "geox.water.flood-model",
  "surface": "mcp",
  "dS": 0.05,
  "peace2": 0.98,
  "kappa_r": 0.22,
  "confidence": 0.78,
  "verdict": "888_QUALIFY",
  "witness": {"human": true, "ai": true, "earth": true}
}
```

## References

- arifOS F2 Truth — Grounding requirement
- arifOS F6 Harmless — Safety constraint
- arifOS F7 Humility — Uncertainty bounds
