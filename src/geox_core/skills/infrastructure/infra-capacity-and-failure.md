---
id: geox.infrastructure.capacity-and-failure
title: Capacity and Failure
domain: infrastructure
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: high
  human_confirmation: true
substrates: [machine-fixed, infrastructure, machine-mobile]
scales: [site, corridor, district]
horizons: [short, medium]
inputs: [capacity-data, demand-signals, redundancy-config, failure-histories]
outputs: [saturation-levels, throughput-estimate, cascading-failure-paths]
depends_on: [geox.infrastructure.network-topology, geox.infrastructure.critical-node-watch]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 3600
  read_only: false
---

# infra-capacity-and-failure

Estimate saturation, throughput, redundancy, and cascading failure paths.

## Contract

**Inputs:** capacity-data, demand-signals, redundancy-config, failure-histories
**Outputs:** saturation-levels, throughput-estimate, cascading-failure-paths

## Behavior

Assess infrastructure capacity against current and projected demand. Model failure propagation and identify saturation bottlenecks.

## Edges

← infra-network-topology
← critical-node-watch
- → human-in-loop-888
- → multi-risk-escalation
