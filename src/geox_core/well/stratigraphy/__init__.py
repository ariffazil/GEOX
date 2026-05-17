"""
GEOX Well Stratigraphy — Generalized L1-L3 Sequence Stratigraphy Pipeline
═══════════════════════════════════════════════════════════════════════════════

Architecture:
  L1  10 m SENSING    — GR stats per configurable bin
  L2  PACKAGE BUILDER — merge bins into geological packages (bottom-up)
  L3  SEQ STRAT       — assign systems tract per package + depo env

Config-driven: no hardcoded wells, intervals, or depositional environments.
KL2 (Kinabalu Basin 2026) was the SOT that proved this architecture.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations
