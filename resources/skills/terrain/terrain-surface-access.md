---
id: geox.terrain.surface-access
title: Surface Access
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
substrates: [human, machine-mobile, environment-field]
scales: [site, corridor, district]
horizons: [immediate, short]
inputs: [terrain-data, surface-type, weather-state, vehicle-class]
outputs: [traversability-scores, access-routes, constraint-report]
depends_on: [geox.terrain.relief-and-slope, geox.atmosphere.weather-state]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 3600
  read_only: false
---

# terrain-surface-access

Estimate traversability for foot, wheeled, tracked, drone support, and construction access.

## Contract

**Inputs:** terrain-data, surface-type, weather-state, vehicle-class
**Outputs:** traversability-scores, access-routes, constraint-report

## Behavior

Assess surface conditions and compute access feasibility for different mobility classes. Include weather degradation effects.

## Edges

← terrain-relief-and-slope
← atmo-weather-state
- → route-viability
