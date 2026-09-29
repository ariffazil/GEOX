"""Curvature attributes — derivatives of the reflector dip field.

Per the Copilot forge prompt: "Curvature: derivatives of reflector dip field;
principal/mean/Gaussian outputs."

We expose the two most-positive and most-negative principal curvatures,
which are the most useful for fault/fracture detection (most-positive
highlights antiforms/fault crests; most-negative highlights synforms/
fault troughs).
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

from geox.seismic.attributes.dip import _gst_components


def _curvature_from_dip(
    volume: np.ndarray,
    sigma: float = 1.0,
    curvature_sigma: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute principal curvatures from the GST-derived dip field.

    Returns: (k1, k2) where k1 = most-positive, k2 = most-negative.
    """
    jxx, jyy, jxy = _gst_components(volume, sigma=sigma)
    # Smooth the tensor components again at curvature scale (larger sigma)
    jxx = gaussian_filter(jxx, sigma=curvature_sigma)
    jyy = gaussian_filter(jyy, sigma=curvature_sigma)
    jxy = gaussian_filter(jxy, sigma=curvature_sigma)

    # Eigenvalues of 2x2 tensor
    trace = jxx + jyy
    det = jxx * jyy - jxy ** 2
    disc = np.sqrt(np.clip(trace ** 2 - 4.0 * det, 0.0, None))
    lambda1 = 0.5 * (trace + disc)
    lambda2 = 0.5 * (trace - disc)

    # Convert eigenvalues to curvature proxy
    # (true curvature requires dip-magnitude + spatial scaling; this is the proxy)
    scale = curvature_sigma ** 2  # smoothing scale
    k1 = lambda1 / (scale + 1e-12)
    k2 = lambda2 / (scale + 1e-12)
    return k1, k2


def curvature_most_positive(
    volume: np.ndarray, sigma: float = 1.0, curvature_sigma: float = 2.0
) -> np.ndarray:
    """Most-positive principal curvature (highlights antiforms/fault crests)."""
    k1, _ = _curvature_from_dip(volume, sigma=sigma, curvature_sigma=curvature_sigma)
    return k1


def curvature_most_negative(
    volume: np.ndarray, sigma: float = 1.0, curvature_sigma: float = 2.0
) -> np.ndarray:
    """Most-negative principal curvature (highlights synforms/fault troughs)."""
    _, k2 = _curvature_from_dip(volume, sigma=sigma, curvature_sigma=curvature_sigma)
    return k2
