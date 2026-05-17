---
id: geox.geodesy.coordinate-frames
title: Coordinate Frames
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
substrates: [machine-fixed, machine-mobile, infrastructure, orbital]
scales: [site, corridor, district, region, nation, maritime]
horizons: [immediate, short]
inputs: [lat-lon, projected-grids, local-site-frames, vessel-tracks, image-tiles]
outputs: [transformed-coordinates, frame-report]
depends_on: []
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 3600
  read_only: true
---

# geo-coordinate-frames

Transform between lat/lon, projected grids, local site frames, vessel tracks, and image tiles.

## Contract

**Inputs:** lat-lon, projected-grids, local-site-frames, vessel-tracks, image-tiles
**Outputs:** transformed-coordinates, frame-report

## Behavior

Accept coordinates in any supported reference frame and output transforms to target frames. Report residual errors and frame metadata.

## Edges

- → geo-position-fix-fusion
- → scale-and-tiling
- → terrain-relief-and-slope
- → legal-jurisdiction
