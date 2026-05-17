---
id: geox.infrastructure.network-topology
title: Network Topology
domain: infrastructure
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [machine-fixed, infrastructure]
scales: [site, corridor, district, region, nation]
horizons: [short, medium]
inputs: [road-data, power-grid, pipeline-data, port-data, telecom-nodes]
outputs: [dependency-graph, interdependency-matrix, critical-paths]
depends_on: [geox.geodesy.coordinate-frames]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 86400
  read_only: true
---

# infra-network-topology

Map roads, grid lines, substations, pipes, ports, depots, and telecom nodes as interdependent graphs.

## Contract

**Inputs:** road-data, power-grid, pipeline-data, port-data, telecom-nodes
**Outputs:** dependency-graph, interdependency-matrix, critical-paths

## Behavior

Build unified infrastructure graphs from heterogeneous source data. Compute interdependency matrices and identify critical paths.

## Edges

← geo-coordinate-frames
- → critical-node-watch
- → capacity-and-failure
- → chokepoint-detection
