"""
BACKWARD COMPATIBILITY SHIM — Use geox_core.physics instead.
"""

from geox_core.physics.parameters import (
    convolve_trace as convolve_synthetic,
)
from geox_core.physics.parameters import (
    impedance_array as calculate_acoustic_impedance,
)
from geox_core.physics.parameters import (
    reflectivity_array as calculate_reflectivity,
)
from geox_core.physics.parameters import (
    ricker_wavelet as generate_ricker,
)

__all__ = [
    "calculate_acoustic_impedance",
    "calculate_reflectivity",
    "generate_ricker",
    "convolve_synthetic",
]
