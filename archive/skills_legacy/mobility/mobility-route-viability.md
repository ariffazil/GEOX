---
id: geox.mobility.route-viability
title: Route Viability
domain: mobility
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: true
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [human, machine-mobile, infrastructure]
scales: [site, corridor, district]
horizons: [immediate, short]
inputs: [road-network, weather-state, vehicle-class, closure-reports, terrain-data]
outputs: [route-options, constraints, confidence-band, alternative-routes]
depends_on: [geox.geodesy.coordinate-frames, geox.time.monitoring-triggers, geox.terrain.surface-access]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 1800
  read_only: false
---

# mobility-route-viability

Route feasibility under time, load, weather, road class, and legal access.

## Contract

**Inputs:** road-network, weather-state, vehicle-class, closure-reports, terrain-data
**Outputs:** route-options, constraints, confidence-band, alternative-routes

## Behavior

Evaluate route feasibility across multiple constraints. Generate ranked route options with constraint explanations and confidence bands.

## Edges

← geo-coordinate-frames
← time-monitoring-triggers
← terrain-surface-access
- → chokepoint-detection
- → fleet-patterns
