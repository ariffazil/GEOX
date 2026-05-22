"""
BACKWARD COMPATIBILITY SHIM — Use geox_core.physics instead.
"""
from geox_core.physics.parameters import (
    estimate_thomsen_parameters,
    apply_anisotropic_velocity_correction,
)

__all__ = ["estimate_thomsen_parameters", "apply_anisotropic_velocity_correction"]
