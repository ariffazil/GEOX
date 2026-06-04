"""
GEOX Seismic Blending Engine — Multi-Volume Color-Space Blending
═════════════════════════════════════════════════════════════════
Forged from paleoscan_python Blending / VolumeBlending / HorizonBlending patterns.

Provides pure geoscience compute for blending seismic volumes and horizons:
  • Alpha blending — weighted linear combination
  • RGB blending — assign volumes to R/G/B color channels
  • HSV / HSL blending — map volumes to hue/saturation/lightness

All functions operate on canonical Image2d / Image3d substrates and return
new blended images. No UI widgets, no file I/O — compute only.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np

from geox_core.core.geox_image import Image2d, Image3d

logger = logging.getLogger("geox.seismic.blending")

# ─────────────────── COLOR SPACE UTILITIES ───────────────────


def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    """Vectorized RGB → HSV conversion. Input shape: (..., 3)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, axis=-1)
    mn = np.min(rgb, axis=-1)
    df = mx - mn

    h = np.zeros_like(mx)
    s = np.zeros_like(mx)
    v = mx

    mask = mx != mn
    rc = np.zeros_like(mx)
    gc = np.zeros_like(mx)
    bc = np.zeros_like(mx)
    rc[mask] = ((mx - r) / df)[mask]
    gc[mask] = ((mx - g) / df)[mask]
    bc[mask] = ((mx - b) / df)[mask]

    h = np.where(mask, np.where(mx == r, (bc - gc), np.where(mx == g, 2.0 + rc - bc, 4.0 + gc - rc)), h)
    h = (h / 6.0) % 1.0
    s = np.where(mx > 0, df / mx, s)

    return np.stack([h, s, v], axis=-1)


def _hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
    """Vectorized HSV → RGB conversion. Input shape: (..., 3)."""
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = (h * 6.0).astype(np.int32)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i = i % 6

    r = np.where(i == 0, v, np.where(i == 1, q, np.where(i == 2, p, np.where(i == 3, p, np.where(i == 4, t, v)))))
    g = np.where(i == 0, t, np.where(i == 1, v, np.where(i == 2, v, np.where(i == 3, q, np.where(i == 4, p, p)))))
    b = np.where(i == 0, p, np.where(i == 1, p, np.where(i == 2, t, np.where(i == 3, v, np.where(i == 4, v, q)))))

    return np.stack([r, g, b], axis=-1)


def _rgb_to_hsl(rgb: np.ndarray) -> np.ndarray:
    """Vectorized RGB → HSL conversion. Input shape: (..., 3)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, axis=-1)
    mn = np.min(rgb, axis=-1)
    l = (mx + mn) / 2.0
    df = mx - mn

    h = np.zeros_like(mx)
    s = np.zeros_like(mx)

    mask = mx != mn
    rc = np.zeros_like(mx)
    gc = np.zeros_like(mx)
    bc = np.zeros_like(mx)
    rc[mask] = ((mx - r) / df)[mask]
    gc[mask] = ((mx - g) / df)[mask]
    bc[mask] = ((mx - b) / df)[mask]

    h = np.where(mask, np.where(mx == r, (bc - gc), np.where(mx == g, 2.0 + rc - bc, 4.0 + gc - rc)), h)
    h = (h / 6.0) % 1.0
    s = np.where(l > 0.5, df / (2.0 - mx - mn), np.where(l > 0, df / (mx + mn), s))

    return np.stack([h, s, l], axis=-1)


def _hsl_to_rgb(hsl: np.ndarray) -> np.ndarray:
    """Vectorized HSL → RGB conversion. Input shape: (..., 3)."""
    h, s, l = hsl[..., 0], hsl[..., 1], hsl[..., 2]

    def _hue_to_rgb(p: np.ndarray, q: np.ndarray, t: np.ndarray) -> np.ndarray:
        t = t % 1.0
        return np.where(t < 1 / 6, p + (q - p) * 6 * t,
               np.where(t < 1 / 2, q,
               np.where(t < 2 / 3, p + (q - p) * (2 / 3 - t) * 6, p)))

    q = np.where(l < 0.5, l * (1 + s), l + s - l * s)
    p = 2 * l - q

    r = _hue_to_rgb(p, q, h + 1 / 3)
    g = _hue_to_rgb(p, q, h)
    b = _hue_to_rgb(p, q, h - 1 / 3)

    return np.stack([r, g, b], axis=-1)


# ─────────────────── NORMALIZATION ───────────────────


def _normalize_to_01(data: np.ndarray) -> np.ndarray:
    """Normalize array to [0, 1] range for color mapping."""
    valid = data[~np.isnan(data)]
    if valid.size == 0:
        return np.zeros_like(data)
    dmin = float(valid.min())
    dmax = float(valid.max())
    if dmax == dmin:
        return np.zeros_like(data)
    return np.clip((data - dmin) / (dmax - dmin), 0.0, 1.0)


# ─────────────────── ALPHA BLENDING ───────────────────


def alpha_blend_2d(
    channel1: Image2d,
    channel2: Image2d,
    opacity1: float = 0.5,
    opacity2: float = 0.5,
) -> Image2d:
    """
    Alpha blend two Image2d channels.
    Weights must sum to 1.0 (enforced by clipping).
    """
    if channel1.width != channel2.width or channel1.height != channel2.height:
        raise ValueError("Channel dimensions must match for blending")

    total = opacity1 + opacity2
    if total == 0:
        raise ValueError("Blend opacities cannot all be zero")
    w1 = opacity1 / total
    w2 = opacity2 / total

    out = Image2d(channel1.width, channel1.height, name="alpha_blend")
    out._data = (w1 * channel1._data + w2 * channel2._data).astype(np.float32)
    return out


def alpha_blend_3d(
    channel1: Image3d,
    channel2: Image3d,
    channel3: Image3d | None = None,
    opacity1: float = 0.33,
    opacity2: float = 0.33,
    opacity3: float = 0.34,
) -> Image3d:
    """
    Alpha blend 2 or 3 Image3d channels.
    Weights are normalized to sum to 1.0.
    """
    if channel1.width != channel2.width or channel1.height != channel2.height or channel1.length != channel2.length:
        raise ValueError("Channel dimensions must match for blending")
    if channel3 is not None:
        if (channel1.width != channel3.width or channel1.height != channel3.height or channel1.length != channel3.length):
            raise ValueError("Channel 3 dimensions must match for blending")

    total = opacity1 + opacity2 + (opacity3 if channel3 else 0.0)
    if total == 0:
        raise ValueError("Blend opacities cannot all be zero")
    w1 = opacity1 / total
    w2 = opacity2 / total
    w3 = (opacity3 / total) if channel3 else 0.0

    out = Image3d(channel1.width, channel1.height, channel1.length, name="alpha_blend")
    out._data = (w1 * channel1._data + w2 * channel2._data).astype(np.float32)
    if channel3:
        out._data += (w3 * channel3._data).astype(np.float32)
    return out


# ─────────────────── RGB BLENDING ───────────────────


def rgb_blend_2d(
    red_channel: Image2d,
    green_channel: Image2d,
    blue_channel: Image2d,
) -> Image2d:
    """
    RGB blend three Image2d channels into a single RGB image.
    Returns a 3-band Image2d where each pixel is (R, G, B).
    """
    if not (red_channel.width == green_channel.width == blue_channel.width and
            red_channel.height == green_channel.height == blue_channel.height):
        raise ValueError("All channel dimensions must match for RGB blending")

    r = _normalize_to_01(red_channel._data)
    g = _normalize_to_01(green_channel._data)
    b = _normalize_to_01(blue_channel._data)

    # Store as 3-channel float32 image
    # We use a special convention: height × width × 3
    out_data = np.stack([r, g, b], axis=-1).astype(np.float32)
    out = Image2d(red_channel.width, red_channel.height, name="rgb_blend")
    out._data = out_data  # Note: shape is (H, W, 3) instead of (H, W)
    return out


def rgb_blend_3d(
    red_channel: Image3d,
    green_channel: Image3d,
    blue_channel: Image3d,
) -> Image3d:
    """
    RGB blend three Image3d channels into a single 3-band RGB volume.
    Each frame is (H, W, 3) with normalized R/G/B values.
    """
    if not (red_channel.width == green_channel.width == blue_channel.width and
            red_channel.height == green_channel.height == blue_channel.height and
            red_channel.length == green_channel.length == blue_channel.length):
        raise ValueError("All channel dimensions must match for RGB blending")

    out = Image3d(red_channel.width, red_channel.height, red_channel.length, name="rgb_blend")
    for i in range(red_channel.length):
        r = _normalize_to_01(red_channel._data[i])
        g = _normalize_to_01(green_channel._data[i])
        b = _normalize_to_01(blue_channel._data[i])
        out._data[i] = np.stack([r, g, b], axis=-1).astype(np.float32)
    return out


# ─────────────────── HSV / HSL BLENDING ───────────────────


def hsv_blend_3d(
    hue_channel: Image3d,
    saturation_channel: Image3d,
    value_channel: Image3d,
) -> Image3d:
    """
    HSV blend three Image3d channels into an RGB volume.
    Maps hue_channel → Hue, saturation_channel → Saturation, value_channel → Value.
    """
    if not (hue_channel.width == saturation_channel.width == value_channel.width and
            hue_channel.height == saturation_channel.height == value_channel.height and
            hue_channel.length == saturation_channel.length == value_channel.length):
        raise ValueError("All channel dimensions must match for HSV blending")

    out = Image3d(hue_channel.width, hue_channel.height, hue_channel.length, name="hsv_blend")
    for i in range(hue_channel.length):
        h = _normalize_to_01(hue_channel._data[i])
        s = _normalize_to_01(saturation_channel._data[i])
        v = _normalize_to_01(value_channel._data[i])
        hsv = np.stack([h, s, v], axis=-1)
        rgb = _hsv_to_rgb(hsv)
        out._data[i] = rgb.astype(np.float32)
    return out


def hsl_blend_3d(
    hue_channel: Image3d,
    saturation_channel: Image3d,
    lightness_channel: Image3d,
) -> Image3d:
    """
    HSL blend three Image3d channels into an RGB volume.
    Maps hue_channel → Hue, saturation_channel → Saturation, lightness_channel → Lightness.
    """
    if not (hue_channel.width == saturation_channel.width == lightness_channel.width and
            hue_channel.height == saturation_channel.height == lightness_channel.height and
            hue_channel.length == saturation_channel.length == lightness_channel.length):
        raise ValueError("All channel dimensions must match for HSL blending")

    out = Image3d(hue_channel.width, hue_channel.height, hue_channel.length, name="hsl_blend")
    for i in range(hue_channel.length):
        h = _normalize_to_01(hue_channel._data[i])
        s = _normalize_to_01(saturation_channel._data[i])
        l = _normalize_to_01(lightness_channel._data[i])
        hsl = np.stack([h, s, l], axis=-1)
        rgb = _hsl_to_rgb(hsl)
        out._data[i] = rgb.astype(np.float32)
    return out


# ─────────────────── HORIZON BLENDING ───────────────────


def alpha_blend_horizon_2d(
    channel1: Image2d,
    channel2: Image2d,
    opacity1: float = 0.5,
    opacity2: float = 0.5,
) -> Image2d:
    """Alpha blend two horizon Image2d grids."""
    return alpha_blend_2d(channel1, channel2, opacity1, opacity2)


def alpha_blend_horizon_3d(
    channel1: Image3d,
    channel2: Image3d,
    channel3: Image3d | None = None,
    opacity1: float = 0.33,
    opacity2: float = 0.33,
    opacity3: float = 0.34,
) -> Image3d:
    """Alpha blend two or three horizon Image3d volumes."""
    return alpha_blend_3d(channel1, channel2, channel3, opacity1, opacity2, opacity3)
