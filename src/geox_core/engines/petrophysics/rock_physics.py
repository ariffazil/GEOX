"""
BACKWARD COMPATIBILITY SHIM — Use geox_core.physics instead.
"""

from geox_core.physics.parameters import (
    bellotti_velocity_from_density,
    faust_velocity,
    gardner_density,
)

__all__ = ["gardner_density", "bellotti_velocity_from_density", "faust_velocity"]
