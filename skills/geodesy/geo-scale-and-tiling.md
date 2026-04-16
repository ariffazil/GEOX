---
id: geox.geodesy.scale-and-tiling
title: Scale and Tiling
domain: geodesy
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [machine-fixed, infrastructure, orbital]
scales: [site, corridor, district, region, nation, maritime]
horizons: [short, medium]
inputs: [multi-scale-data, tile-indexes, resolution-requirements]
outputs: [tiled-data, scale-adjusted-outputs]
depends_on: [geox.geodesy.coordinate-frames]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 7200
  read_only: true
---

# geo-scale-and-tiling

Reason across site, corridor, district, region, nation, maritime sphere.

## Contract

**Inputs:** multi-scale-data, tile-indexes, resolution-requirements
**Outputs:** tiled-data, scale-adjusted-outputs

## Behavior

Segment geographic data into appropriate scale buckets and tile schemes for storage, transmission, and processing efficiency.

## Edges

← geo-coordinate-frames
