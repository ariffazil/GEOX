"""
BACKWARD COMPATIBILITY SHIM — Use geox_core.physics instead.
"""

from geox_core.physics.parameters import (
    spectral_decay as calculate_spectral_decay,
)
from geox_core.physics.parameters import (
    time_variant_wavelet_params as get_time_variant_wavelet_params,
)

__all__ = ["calculate_spectral_decay", "get_time_variant_wavelet_params"]
