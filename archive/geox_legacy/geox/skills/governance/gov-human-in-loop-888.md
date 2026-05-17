---
id: geox.governance.human-in-loop-888
title: Human in Loop 888
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
substrates: [human]
scales: [site, corridor, district, region]
horizons: [immediate, short]
inputs: [action-proposal, risk-assessment, reversibility-check]
outputs: [confirmation-required, hold-status, override-report]
depends_on: [geox.hazards.multi-risk-escalation, geox.infrastructure.capacity-and-failure]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 60
  read_only: false
---

# gov-human-in-loop-888

Define irreversible thresholds and force human confirmation.

## Contract

**Inputs:** action-proposal, risk-assessment, reversibility-check
**Outputs:** confirmation-required, hold-status, override-report

## Behavior

Intercept high-risk action proposals. Apply 888 HOLD protocol: block irreversible actions, require human confirmation, and generate audit trail.

## Edges

← multi-risk-escalation
← infra-capacity-and-failure
← critical-node-watch
- → peace-maruah-screen
