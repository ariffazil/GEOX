"""
BACKWARD COMPATIBILITY SHIM — Use geox_core.physics instead.
"""
from geox_core.physics.parameters import (
    impedance_array as calculate_acoustic_impedance,
    reflectivity_array as calculate_reflectivity,
    ricker_wavelet as generate_ricker,
    convolve_trace as convolve_synthetic,
)

__all__ = [
    "calculate_acoustic_impedance",
    "calculate_reflectivity",
    "generate_ricker",
    "convolve_synthetic",
]
