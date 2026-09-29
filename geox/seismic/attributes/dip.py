"""Dip, azimuth, and coherence via gradient structure tensor (GST).

Per the Copilot forge prompt: "dip must become a dependency service — not
another display attribute." These functions are reused by curvature,
coherence, and chaos — they form the structural-dip backbone.

Reference: van Vliet & Verbeek (1995), Randen et al. (2000).
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, uniform_filter


def _gst_components(volume: np.ndarray, sigma: float = 1.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute GST components (Jxx, Jyy, Jxy) from smoothed gradients.

    Returns Jxx, Jyy, Jxy arrays of the same shape as volume.
    """
    v = gaussian_filter(volume.astype(np.float64), sigma=sigma)
    # Gradients along the last 2 axes (iline, xline). Sample axis is "vertical".
    if volume.ndim == 3:
        gx = np.gradient(v, axis=1)  # along xline
        gy = np.gradient(v, axis=2)  # along sample (or xline? — see note)
        # In a 3D volume (iline, xline, sample), axis=2 is sample (vertical).
        # For dip/azimuth, we want horizontal gradients only — use axis=0 and axis=1.
        g_il = np.gradient(v, axis=0)
        g_xl = np.gradient(v, axis=1)
    else:
        g_il = np.gradient(v, axis=0)
        g_xl = np.gradient(v, axis=1)

    jxx = g_il * g_il
    jyy = g_xl * g_xl
    jxy = g_il * g_xl
    # Smooth the structure tensor components (key for stable dip estimation)
    jxx = gaussian_filter(jxx, sigma=sigma)
    jyy = gaussian_filter(jyy, sigma=sigma)
    jxy = gaussian_filter(jxy, sigma=sigma)
    return jxx, jyy, jxy


def gst_dip(volume: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Dip magnitude in (xline/sample) ratio. Range [0, +inf).

    Computed as the smaller eigenvalue ratio of the GST. For a plane wave
    with normal n, dip = sqrt((1 - l1/(l1+l2))) * scale, but here we use
    the simpler absolute-gradient / vertical-gradient proxy.
    """
    jxx, jyy, jxy = _gst_components(volume, sigma=sigma)
    if volume.ndim == 3:
        # Use the lateral gradient vs the sample-axis gradient
        g_z = np.gradient(gaussian_filter(volume.astype(np.float64), sigma=sigma), axis=2)
        g_z_sq = gaussian_filter(g_z ** 2, sigma=sigma)
    else:
        g_z = np.gradient(gaussian_filter(volume.astype(np.float64), sigma=sigma), axis=1)
        g_z_sq = gaussian_filter(g_z ** 2, sigma=sigma)

    lateral_sq = jxx + jyy
    # tan(dip) = sqrt(lateral_sq) / |g_z|, but we return the magnitude proxy
    denom = g_z_sq + 1e-12
    dip_sq = lateral_sq / denom
    return np.sqrt(dip_sq)


def gst_azimuth(volume: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Azimuth of the GST principal axis in degrees, range [0, 180).

    Convention: 0° = +iline direction, 90° = +xline direction.
    """
    jxx, jyy, jxy = _gst_components(volume, sigma=sigma)
    # Principal axis angle of the 2x2 tensor [[Jxx, Jxy], [Jxy, Jyy]]
    azimuth_rad = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)
    azimuth_deg = np.degrees(azimuth_rad)
    # Wrap to [0, 180)
    azimuth_deg = azimuth_deg % 180.0
    return azimuth_deg


def gst_coherence(
    volume: np.ndarray, window_size: int = 5, sigma: float = 1.0
) -> np.ndarray:
    """Semblance-style coherence over a cubic window.

    Computed as the ratio of summed structure-tensor eigenvalues to summed
    squared gradients, in [0, 1]. 1 = perfectly planar, 0 = chaotic.

    Per Copilot forge: this is the canonical dip-steered coherence primitive.
    """
    v = volume.astype(np.float64)
    # Sum the structure-tensor eigenvalues over the window
    jxx, jyy, jxy = _gst_components(v, sigma=sigma)
    # Eigenvalues of 2x2 tensor [[Jxx, Jxy], [Jxy, Jyy]]
    trace = jxx + jyy
    det = jxx * jyy - jxy ** 2
    disc = np.sqrt(np.clip(trace ** 2 - 4.0 * det, 0.0, None))
    lambda1 = 0.5 * (trace + disc)
    lambda2 = 0.5 * (trace - disc)
    sum_lambda = uniform_filter(lambda1 + lambda2, size=window_size, mode="nearest")

    # Sum of squared gradients in window (denominator)
    if v.ndim == 3:
        g_il = np.gradient(v, axis=0)
        g_xl = np.gradient(v, axis=1)
        g_z = np.gradient(v, axis=2)
    else:
        g_il = np.gradient(v, axis=0)
        g_xl = np.gradient(v, axis=1)
        g_z = np.zeros_like(g_il)
    grad_sq = g_il ** 2 + g_xl ** 2 + g_z ** 2
    sum_grad_sq = uniform_filter(grad_sq, size=window_size, mode="nearest")

    coherence = sum_lambda / (sum_grad_sq + 1e-12)
    return np.clip(coherence, 0.0, 1.0)
