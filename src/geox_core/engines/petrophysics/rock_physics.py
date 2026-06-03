"""
BACKWARD COMPATIBILITY SHIM — Use geox_core.physics instead.
"""

from geox_core.physics.parameters import (
    gardner_density,
    bellotti_velocity_from_density,
    faust_velocity,
)

__all__ = ["gardner_density", "bellotti_velocity_from_density", "faust_velocity"]
