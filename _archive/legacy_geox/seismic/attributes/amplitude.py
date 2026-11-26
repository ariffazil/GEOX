"""Amplitude-windowed attributes: RMS, variance.

Used for discontinuity detection (variance), bright-spot classification (RMS),
and texture (variance within a neighborhood window).
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter


def _window_sum_squares(volume: np.ndarray, window_size: int) -> np.ndarray:
    """Sum of squares within a cubic window centered on each voxel."""
    sq = volume ** 2
    return uniform_filter(sq, size=window_size, mode="nearest")


def rms_amplitude(
    volume: np.ndarray, window_size: int = 5
) -> np.ndarray:
    """Root-mean-square amplitude over a cubic window.

    Parameters
    ----------
    volume : np.ndarray
        Input seismic amplitude volume (2D or 3D).
    window_size : int
        Cubic window size (odd integer recommended; default 5).
    """
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    sum_sq = _window_sum_squares(volume.astype(np.float64), window_size)
    n_voxels = window_size ** volume.ndim
    # Clip numerical floor (uniform_filter can yield tiny negatives from rounding)
    return np.sqrt(np.clip(sum_sq / n_voxels, 0.0, None))


def variance(volume: np.ndarray, window_size: int = 5) -> np.ndarray:
    """Local variance over a cubic window.

    var = E[x^2] - (E[x])^2
    """
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    v = volume.astype(np.float64)
    mean = uniform_filter(v, size=window_size, mode="nearest")
    mean_sq = uniform_filter(v ** 2, size=window_size, mode="nearest")
    var = mean_sq - mean ** 2
    return np.clip(var, 0.0, None)  # numerical floor
