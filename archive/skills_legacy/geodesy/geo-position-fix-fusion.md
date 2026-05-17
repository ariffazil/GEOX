---
id: geox.geodesy.position-fix-fusion
title: Position Fix Fusion
domain: geodesy
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [machine-mobile, infrastructure, orbital, environment-field]
scales: [site, corridor, district]
horizons: [immediate]
inputs: [gps-gnss, inertial-hints, map-anchors, reported-positions]
outputs: [fused-position, confidence-ellipse, fix-quality]
depends_on: [geox.geodesy.coordinate-frames]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 60
  read_only: true
---

# geo-position-fix-fusion

Fuse GPS/GNSS, inertial hints, map anchors, and reported positions into a usable fix.

## Contract

**Inputs:** gps-gnss, inertial-hints, map-anchors, reported-positions
**Outputs:** fused-position, confidence-ellipse, fix-quality

## Behavior

Combine multiple positioning sources into a single best-estimate position with uncertainty ellipse. Assess fix quality and flag inconsistencies.

## Edges

← geo-coordinate-frames
- → terrain-relief-and-slope
- → hazard-seismic-and-ground-shift
- → fleet-patterns
