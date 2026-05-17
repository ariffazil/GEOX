---
id: geox.terrain.drainage-structure
title: Drainage Structure
domain: terrain
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [machine-fixed, orbital, environment-field]
scales: [site, corridor, district, region]
horizons: [short, medium]
inputs: [terrain-models, hydro-data, soil-data, land-cover]
outputs: [runoff-paths, catchment-areas, blockage-points, erosion-exposure]
depends_on: [geox.terrain.relief-and-slope, geox.water.hydrology-basics]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 86400
  read_only: true
---

# terrain-drainage-structure

Infer runoff paths, catchments, blockage points, and erosion exposure.

## Contract

**Inputs:** terrain-models, hydro-data, soil-data, land-cover
**Outputs:** runoff-paths, catchment-areas, blockage-points, erosion-exposure

## Behavior

Model terrain-driven water movement. Identify catchments, channelize flow paths, and flag potential blockage and erosion surfaces.

## Edges

← terrain-relief-and-slope
← water-hydrology-basics
- → water-floodplain-and-flow
