---
id: geox.terrain.relief-and-slope
title: Relief and Slope
domain: terrain
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [machine-fixed, machine-mobile, orbital, environment-field]
scales: [site, corridor, district, region]
horizons: [short, medium]
inputs: [dem-data, terrain-models, bathymetry]
outputs: [slope-maps, aspect-maps, ridge-depression-report, movement-penalty]
depends_on: [geox.geodesy.coordinate-frames]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 86400
  read_only: true
---

# terrain-relief-and-slope

Derive slope, aspect, ridge, depression, and movement penalty from terrain.

## Contract

**Inputs:** dem-data, terrain-models, bathymetry
**Outputs:** slope-maps, aspect-maps, ridge-depression-report, movement-penalty

## Behavior

Compute terrain derivatives from elevation data. Identify ridgelines, depressions, and compute movement cost surfaces for planning.

## Edges

← geo-coordinate-frames
← geo-position-fix-fusion
- → terrain-surface-access
- → terrain-drainage-structure
