"""Causal Scene — dimension-native v2 ontology for GEOX.

Eureka gap sealed from A-FORGE progenitor (2026-04). Concepts NOT in
canonical GEOX v1 (contracts/schemas/output_schemas.py):
  1. Four witness kinds: Manifold, Truth, Claim, Texture
  2. CausalSceneUISummary + Physics9Item — React-ready UI payload
  3. ContrastOperatorSpec — rigid left/right witness pairing rules
  4. FloorPolicy — GEOX-specific constitutional floor bindings
  5. VerdictCode — semantic verdict enum (pass_green..reject_red)
  6. ContrastVerdict — full governed judgment with policy_evaluations
  7. IntentEnvelope — audit envelope linking intent to floors
  8. PolicyBand + PolicyEvaluation — versioned threshold policies
  9. SamplingAxis/NumericRange — typed spatial sampling descriptors
  10. SupportGeometry discriminated union — grid/stick/track/pointset/volume
"""

from __future__ import annotations
