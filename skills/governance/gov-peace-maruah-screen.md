---
id: geox.governance.peace-maruah-screen
title: Peace Maruah Screen
domain: governance
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: true
  mcp_tool: false
risk:
  class: high
  human_confirmation: true
substrates: [human, infrastructure, void]
scales: [district, region, nation]
horizons: [short, medium, long]
inputs: [action-proposal, social-context, stability-indicators, dignity-metrics]
outputs: [screen-result, stability-impact, dignity-flag]
depends_on: [geox.governance.legal-jurisdiction]
legal_domain: international
status: draft
runtime:
  cache_ttl_sec: 3600
  read_only: false
---

# gov-peace-maruah-screen

Reject options that are physically feasible but socially destabilizing or dignity-damaging.

## Contract

**Inputs:** action-proposal, social-context, stability-indicators, dignity-metrics
**Outputs:** screen-result, stability-impact, dignity-flag

## Behavior

Screen action proposals against social stability and dignity impact models. Reject or flag actions that may cause dignity harm or destabilize peace.

## Edges

← legal-jurisdiction
← human-in-loop-888
