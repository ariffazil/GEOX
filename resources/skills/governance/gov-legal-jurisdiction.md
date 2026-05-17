---
id: geox.governance.legal-jurisdiction
title: Legal Jurisdiction
domain: governance
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: true
  mcp_tool: false
risk:
  class: medium
  human_confirmation: false
substrates: [human, infrastructure, void]
scales: [site, corridor, district, region, nation, maritime]
horizons: [short, medium]
inputs: [location-data, jurisdiction-maps, treaty-data, permit-requirements]
outputs: [jurisdiction-report, legal-constraints, permit-status]
depends_on: [geox.geodesy.coordinate-frames]
legal_domain: international
status: draft
runtime:
  cache_ttl_sec: 86400
  read_only: true
---

# gov-legal-jurisdiction

Maritime vs land, public vs private, airspace, permits, protected zones, sovereign boundaries.

## Contract

**Inputs:** location-data, jurisdiction-maps, treaty-data, permit-requirements
**Outputs:** jurisdiction-report, legal-constraints, permit-status

## Behavior

Determine applicable legal regimes for a given location. Report jurisdictional boundaries, treaty implications, and permit requirements.

## Edges

← geo-coordinate-frames
- → human-in-loop-888
- → peace-maruah-screen
