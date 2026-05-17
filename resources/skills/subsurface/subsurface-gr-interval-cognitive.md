---
id: geox.subsurface.gr-interval-cognitive
title: Cognitive GR Interval Extraction
domain: subsurface
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [environment-field, human]
scales: [site]
horizons: [immediate, short]
inputs: [gamma-ray-log, depth-md, biostrat-nn-picks]
outputs: [cognitive-intervals, stratigraphic-motifs, shale-side-shading]
depends_on: []
legal_domain: public
status: production
impl_file: gr_intervals.py
drift_sensitivity: medium
---

# subsurface.gr-interval-cognitive

Cognitive extraction of GR log intervals for stratigraphic and sedimentary interpretation. Applies GR binning, motif classification, and shale-side shading based on operator-defined cutoffs.

## Contract

**Inputs:** gamma-ray-log, depth-md, biostrat-nn-picks
**Outputs:** cognitive-intervals (MD top/base pairs), stratigraphic-motifs (fining/coarsening/blocky), shale-side-shading (left/right/none)

## Constraints

- GR values must be in API units (0–300 range expected)
- Depth must be strictly monotonic (MD)
- No physics violation possible — interpretive tool only

## Edges

- → formation-evaluation
- → seismic-interpretation
