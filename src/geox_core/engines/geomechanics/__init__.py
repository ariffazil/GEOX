"""geomechanics — Causality layer for GEOX Earth Reality Graph.

Geomechanics sits between physics (F0) and structure (F2).
It answers: "Why was that geometry allowed to form?"

Stress + Rock Strength + Boundary Conditions → Failure → Faulting

This is the causality layer that restoration software (MOVE) lacks.
MOVE computes: Present Geometry → Restore → Past Geometry.
GEOX computes: Past Geometry → Infer Deformation → Infer Stress (inverse).

Forged: 2026-09-14
"""
