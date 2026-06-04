"""
BACKWARD COMPATIBILITY SHIM — Use geox_core.physics instead.
"""

from geox_core.physics.parameters import (
    apply_anisotropic_velocity_correction,
    estimate_thomsen_parameters,
)

__all__ = ["estimate_thomsen_parameters", "apply_anisotropic_velocity_correction"]
