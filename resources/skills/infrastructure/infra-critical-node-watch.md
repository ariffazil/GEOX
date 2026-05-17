---
id: geox.infrastructure.critical-node-watch
title: Critical Node Watch
domain: infrastructure
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: high
  human_confirmation: false
substrates: [machine-fixed, infrastructure]
scales: [corridor, district, region]
horizons: [immediate, short]
inputs: [network-topology, traffic-flow, historical-failure, node-centrality]
outputs: [critical-node-list, fragility-scores, fallback-nodes]
depends_on: [geox.infrastructure.network-topology]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 3600
  read_only: true
---

# infra-critical-node-watch

Identify high-betweenness assets, fragile dependencies, and fallback nodes.

## Contract

**Inputs:** network-topology, traffic-flow, historical-failure, node-centrality
**Outputs:** critical-node-list, fragility-scores, fallback-nodes

## Behavior

Rank infrastructure nodes by criticality using betweenness centrality, failure history, and redundancy analysis. Flag high-risk single points of failure.

## Edges

← infra-network-topology
- → human-in-loop-888
- → multi-risk-escalation
