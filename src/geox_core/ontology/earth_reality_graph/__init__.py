"""earth_reality_graph — Earth Reality Graph ontology for GEOX.

Seismic is an observation layer.
Geomechanics is a causality layer.
Restoration is an inverse engine linking the two.

Earth computes forward. GEOX computes backward.

The graph separates:
  PHYSICAL DRIVER → GEOMECHANICAL RESPONSE → GEOLOGICAL STATE
  → ROCK PROPERTY STATE → GEOPHYSICAL RESPONSE → OBSERVATION
  → INTERPRETATION → TECTONIC HYPOTHESES

Constitutional invariant:
  Reflection ≠ Horizon ≠ Event ≠ Cause.
  Each is a separate node connected by evidence-bearing edges.

Forged: 2026-09-14
"""
