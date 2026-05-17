---
id: geox.mobility.chokepoint-detection
title: Chokepoint Detection
domain: mobility
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [machine-fixed, machine-mobile, infrastructure]
scales: [corridor, district, region]
horizons: [short, medium]
inputs: [infrastructure-graph, traffic-flow, historical-bottlenecks]
outputs: [chokepoint-list, criticality-scores, fallback-options]
depends_on: [geox.infrastructure.network-topology, geox.mobility.route-viability]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 3600
  read_only: true
---

# mobility-chokepoint-detection

Bridges, ports, junctions, ferries, canal locks, passes, and single-node dependencies.

## Contract

**Inputs:** infrastructure-graph, traffic-flow, historical-bottlenecks
**Outputs:** chokepoint-list, criticality-scores, fallback-options

## Behavior

Identify high-dependency nodes in mobility networks. Score chokepoint criticality and suggest fallback routes.

## Edges

← infra-network-topology
← mobility-route-viability
