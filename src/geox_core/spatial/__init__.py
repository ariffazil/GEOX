"""
geox_core.spatial — Eureka 8: Velocity IS Structure

2.5D extension of the T-D workflow. A horizontal slice of the velocity
field at a constant depth is a 2D structural map. This module provides
the three primitives that make the velocity-as-structure eureka
operational:

  1. slice_velocity_cube   — extract VpSlice (2D map) at constant depth
  2. structural_attribution — decompose Vp variation into 5 geological signals
  3. bootstrap_structure   — sparse 1D well anchors + dense 2.5D Vp field
                              → 2D structure map at any depth (or TWT)

Plus a synthetic cube generator with embedded anticline, fault, and
gas pocket for testing.

Theory reference: docs/eureka_insights/E8_VELOCITY_AS_STRUCTURE_2026_06_03.md

DITEMPA BUKAN DIBERI — velocity is the earth, integrated over time.
"""

from geox_core.spatial.velocity_slice import (
    StructuralMap,
    VpCube,
    VpSlice,
    bootstrap_structure,
    slice_velocity_cube,
    structural_attribution,
    synth_cube_with_structure,
)

__all__ = [
    "VpCube",
    "VpSlice",
    "StructuralMap",
    "slice_velocity_cube",
    "structural_attribution",
    "bootstrap_structure",
    "synth_cube_with_structure",
]
