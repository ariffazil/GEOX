---
id: geox.atmosphere.weather-state
title: Weather State
domain: atmosphere
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [machine-fixed, machine-mobile, orbital, environment-field]
scales: [site, corridor, district, region]
horizons: [immediate, short]
inputs: [meteo-data, satellite-imagery, radar-data, station-reports]
outputs: [weather-envelope, visibility, wind-field, sensor-degradation]
depends_on: [geox.sensing.observation-intake]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 900
  read_only: true
---

# atmo-weather-state

Current weather envelope for operations, visibility, rainfall, wind, heat, and sensor degradation.

## Contract

**Inputs:** meteo-data, satellite-imagery, radar-data, station-reports
**Outputs:** weather-envelope, visibility, wind-field, sensor-degradation

## Behavior

Synthesize current atmospheric conditions from multiple sources. Compute operational envelopes for different sensor modalities.

## Edges

← sense-observation-intake
- → terrain-surface-access
- → water-maritime-state
- → radiation-and-solar
- → seasonality-and-monsoon
