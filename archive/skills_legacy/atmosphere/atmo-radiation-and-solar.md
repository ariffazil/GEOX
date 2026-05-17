---
id: geox.atmosphere.radiation-and-solar
title: Radiation and Solar
domain: atmosphere
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [orbital, environment-field, celestial]
scales: [site, corridor, district, region]
horizons: [immediate, short, medium]
inputs: [solar-position, cloud-cover, aerosol-data, topography]
outputs: [daylight-geometry, solar-forcing, thermal-load, pv-potential]
depends_on: [geox.atmosphere.weather-state, geox.geodesy.coordinate-frames]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 3600
  read_only: true
---

# atmo-radiation-and-solar

Daylight geometry, solar forcing, thermal loading, PV relevance, and remote-sensing illumination.

## Contract

**Inputs:** solar-position, cloud-cover, aerosol-data, topography
**Outputs:** daylight-geometry, solar-forcing, thermal-load, pv-potential

## Behavior

Compute solar geometry and atmospheric transmission. Output daylight windows, thermal loading estimates, and PV generation potential.

## Edges

← atmo-weather-state
← geo-coordinate-frames
