---
id: geox.water.maritime-state
title: Maritime State
domain: water
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
scales: [corridor, district, maritime]
horizons: [immediate, short]
inputs: [current-data, wave-data, tide-data, weather-forecast]
outputs: [current-maps, wave-state, anchorage-conditions, nearshore-access]
depends_on: [geox.atmosphere.weather-state, geox.geodesy.coordinate-frames]
legal_domain: maritime
status: draft
runtime:
  cache_ttl_sec: 1800
  read_only: true
---

# water-maritime-state

Currents, wave state, anchorage logic, and nearshore access conditions.

## Contract

**Inputs:** current-data, wave-data, tide-data, weather-forecast
**Outputs:** current-maps, wave-state, anchorage-conditions, nearshore-access

## Behavior

Assess maritime surface conditions for vessel operations. Compute currents, wave state, and nearshore access feasibility.

## Edges

← atmo-weather-state
← geo-coordinate-frames
