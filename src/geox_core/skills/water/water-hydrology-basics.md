---
id: geox.water.hydrology-basics
title: Hydrology Basics
domain: water
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [machine-fixed, orbital, environment-field]
scales: [site, corridor, district, region]
horizons: [short, medium]
inputs: [river-network, basin-data, precipitation, soil-moisture]
outputs: [runoff-estimate, storage-levels, channel-capacity]
depends_on: [geox.terrain.drainage-structure]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 3600
  read_only: true
---

# water-hydrology-basics

River, basin, retention, runoff, storage, and channel logic.

## Contract

**Inputs:** river-network, basin-data, precipitation, soil-moisture
**Outputs:** runoff-estimate, storage-levels, channel-capacity

## Behavior

Model the freshwater hydrological cycle for a given area. Compute storage, runoff, and channel conveyance capacity.

## Edges

← terrain-drainage-structure
- → water-floodplain-and-flow
