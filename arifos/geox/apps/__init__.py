"""
GEOX Volume App — DITEMPA BUKAN DIBERI

App module for volume context and 3D visualization.

This is the user-facing app that uses the renderer adapters
to provide volume context views.

Architecture:
  GEOX tools → VolumeApp → SceneCompiler → CigvisAdapter → cigvis
"""

from arifos.geox.apps.volume_app.app import VolumeApp
from arifos.geox.apps.volume_app.tools import (
    geox_open_volume_context,
    geox_volume_compile_scene,
    geox_volume_render_snapshot,
    geox_volume_launch_interactive,
    geox_volume_add_horizon,
    geox_volume_add_wells,
)

__all__ = [
    "VolumeApp",
    "geox_open_volume_context",
    "geox_volume_compile_scene",
    "geox_volume_render_snapshot",
    "geox_volume_launch_interactive",
    "geox_volume_add_horizon",
    "geox_volume_add_wells",
]
