"""
Seismic attribute catalog — 2D section lane (display + native)
═══════════════════════════════════════════════════════════════
One taxonomy, two provenances.

WHAT THIS IS
------------
The canonical post-stack seismic attribute taxonomy (Sheriff 2002, *Encyclopedic
Dictionary of Applied Geophysics*, SEG; Chopra & Marfurt 2007, *Seismic Attributes
for Prospect ID and Reservoir Characterization*, SEG) organised into four families:

  A. AMPLITUDE   — mean, energy, RMS, max magnitude, envelope (instantaneous amplitude),
                    variance, sweetness
  B. COMPLEX TRACE — instantaneous phase, cosine phase, instantaneous frequency,
                    instantaneous bandwidth, apparent polarity
  C. FREQUENCY   — dominant frequency, centroid frequency (spectral family)
  D. STRUCTURE   — coherence, discontinuity, semblance, dip, azimuth, curvature

WHAT THIS IS NOT
----------------
Pre-stack / elastic-property attributes are explicitly OUT OF SCOPE for this lane and are
listed in `OUT_OF_SCOPE` with the reason. A display-derived raster carries no offset
information, no velocity model and no sample interval, so AVO classes, acoustic impedance,
Poisson's ratio, anelastic attenuation (Q) and Hz-calibrated spectral bands cannot be
computed here. Their absence is a stated boundary, not an oversight.

ORIENTATION CONTRACT
--------------------
2D section convention used everywhere in this module:
    rows    = TIME  (samples / rows of the section)
    cols    = TRACE (lateral index)
Hilbert / FFT / gradient operators therefore run along axis=0 (time). Frequency-valued
attributes are returned in CYCLES PER SAMPLE (or rad/sample) — NEVER Hz — because this lane
does not own a sample interval. `units` in every spec says so.

PROVENANCE
----------
A raster or extracted grid is DISPLAY_DERIVED_PROXY: prohibited for AVO, amplitude
preservation, phase certification and native well-tie acceptance. SEG-Y trace data is
NATIVE_TRACE. The distinction is a tag, never a different algorithm.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage
from scipy.signal import hilbert

# ─────────────────────────── catalog specs ───────────────────────────

ATTRIBUTE_SPECS: dict[str, dict[str, Any]] = {
    # ── A. amplitude family ──
    "amplitude": {
        "family": "amplitude",
        "formula": "A = |a(t,x)|",
        "units": "normalized amplitude",
        "note": "Point-wise magnitude of the signal. Not energy, not reflectivity.",
    },
    "envelope": {
        "family": "amplitude",
        "formula": "E = |A(t)| where A = Hilbert(a) along time",
        "units": "normalized amplitude",
        "note": "Instantaneous amplitude / envelope. Classic complex-trace attribute.",
    },
    "rms": {
        "family": "amplitude",
        "formula": "RMS = sqrt(mean(a^2) over window)",
        "units": "normalized amplitude",
        "note": "Noise-sensitive by construction (squares every sample in the window).",
    },
    "energy": {
        "family": "amplitude",
        "formula": "E = mean(a^2) over window",
        "units": "amplitude^2 (normalized)",
        "note": "Average energy. Reflectivity proxy in the Sheriff taxonomy.",
    },
    "variance": {
        "family": "amplitude",
        "formula": "Var = mean(a^2) - mean(a)^2 over window",
        "units": "amplitude^2 (normalized)",
        "note": "Texture/variance family.",
    },
    "mean_amplitude": {
        "family": "amplitude",
        "formula": "mean(a) over window",
        "units": "normalized amplitude",
        "note": "Trace bias / DC balance over the window.",
    },
    "max_magnitude": {
        "family": "amplitude",
        "formula": "max(|a|) over window",
        "units": "normalized amplitude",
        "note": "Strongest sample in the window.",
    },
    "sweetness": {
        "family": "amplitude",
        "formula": "S = max_t(env) / sqrt(mean_t(env^2))  (per trace)",
        "units": "dimensionless ratio",
        "note": "Peak-to-RMS shape ratio. High for a clean isolated event.",
    },
    # ── B. complex-trace family ──
    "instantaneous_phase": {
        "family": "complex_trace",
        "formula": "phi = arg(Hilbert(a))",
        "units": "radians (wrapped to -pi..pi)",
        "note": "Instantaneous phase of the analytic signal.",
    },
    "cosine_phase": {
        "family": "complex_trace",
        "formula": "cos(phi)",
        "units": "dimensionless (-1..1)",
        "note": "Phase polarity proxy; used by the RSI horizon tracker.",
    },
    "instantaneous_frequency": {
        "family": "complex_trace",
        "formula": "f_inst = d(unwrap(phi))/dt",
        "units": "rad/sample (NOT Hz — no sample interval in this lane)",
        "note": "Instantaneous frequency of the analytic signal.",
    },
    "instantaneous_bandwidth": {
        "family": "complex_trace",
        "formula": "B = |d(env)/dt| / (2*pi*|f_inst|), capped where f_inst -> 0",
        "units": "dimensionless ratio",
        "note": "Relative bandwidth of the analytic signal.",
    },
    "apparent_polarity": {
        "family": "complex_trace",
        "formula": "sign(Re(A) at the envelope peak of the trace)",
        "units": "{-1, 0, +1}",
        "note": "Apparent wavelet polarity (Sheriff taxonomy).",
    },
    # ── C. frequency family ──
    "dominant_frequency": {
        "family": "frequency",
        "formula": "argmax_k |FFT(a)| per trace",
        "units": "cycles/sample (NOT Hz — no sample interval in this lane)",
        "note": "Peak frequency of the trace spectrum. Inverse relation to layer thickness.",
    },
    "centroid_frequency": {
        "family": "frequency",
        "formula": "sum(f*P) / sum(P) per trace",
        "units": "cycles/sample (NOT Hz)",
        "note": "Spectral centroid (mean frequency content of the trace).",
    },
    # ── D. structure family ──
    "coherence": {
        "family": "structure",
        "formula": "lateral semblance proxy: 1 - normalized cross-correlation of left/right trace windows",
        "units": "dimensionless (0..1)",
        "note": "Continuity between neighbouring traces. Low across faults/channels.",
    },
    "discontinuity": {
        "family": "structure",
        "formula": "1 - coherence",
        "units": "dimensionless (0..1)",
        "note": "Edge/discontinuity emphasis. High across faults.",
    },
    "semblance": {
        "family": "structure",
        "formula": "S = (sum_i a_i)^2 / (N * sum_i a_i^2) over an N-trace window",
        "units": "dimensionless (0..1)",
        "note": "Neidell-Tanner style multi-trace semblance. 1 = perfectly coherent traces.",
    },
    "dip": {
        "family": "structure",
        "formula": "0.5*atan2(2*Jxy, Jxx-Jyy) from the structure tensor (gradient orientation)",
        "units": "radians (dip_deg also provided)",
        "note": "Gradient dip in IMAGE axes (x=trace, y=time). Not geographic.",
    },
    "azimuth": {
        "family": "structure",
        "formula": "0.5*atan2(2*Jxy, Jxx-Jyy) -> direction of maximum slope",
        "units": "degrees from +x (trace) axis, image axes",
        "note": "Dip direction in IMAGE axes. NOT geographic north; no orientation metadata in this lane.",
    },
    "curvature": {
        "family": "structure",
        "formula": "Laplacian of the smoothed section (2D section proxy)",
        "units": "1/sample^2",
        "note": "SECTION proxy. True horizon curvature needs a picked horizon (zen_track_horizon).",
    },
}

# Attributes that exist in the wider industry taxonomy but CANNOT be computed here.
# Each carries the reason it is out of scope — a boundary, not a gap.
OUT_OF_SCOPE: list[dict[str, str]] = [
    {
        "attribute": "AVO / AVO classes (intercept, gradient, far-minus-near, fluid factor)",
        "reason": "Pre-stack: needs offset gathers. A raster or post-stack section carries no offsets.",
        "where_it_lives": "geox_seismic_compute(mode='avo_forward') on synthetic elastic inputs",
    },
    {
        "attribute": "Acoustic impedance (AI = vp * rho)",
        "reason": "Needs a velocity model and density; amplitude alone does not constrain them.",
        "where_it_lives": "inversion lane (geox_seismic_compute mode='inversion')",
    },
    {
        "attribute": "Poisson's ratio / elastic moduli",
        "reason": "Needs elastic parameters (vp, vs). Not derivable from amplitude.",
        "where_it_lives": "geox_geomechanics",
    },
    {
        "attribute": "Anelastic attenuation factor (Q)",
        "reason": "Needs a stack or borehole-calibrated attenuation measurement.",
        "where_it_lives": "not yet in GEOX",
    },
    {
        "attribute": "Hz-calibrated spectral bands (bandpass / spectral decomposition surfaces)",
        "reason": "This lane owns no sample interval, so no band can be named in Hz.",
        "where_it_lives": "dominant_frequency + centroid_frequency here; Hz bands need a SEG-Y sample rate",
    },
]

# Which attributes the 2D display lane can compute (the "common variants" set).
COMMON_VARIANTS: tuple[str, ...] = tuple(ATTRIBUTE_SPECS.keys())


def catalog_manifest() -> dict[str, Any]:
    """Machine-readable statement of what this lane can and cannot compute."""
    return {
        "taxonomy_source": "Sheriff 2002 (SEG Encyclopedic Dictionary); Chopra & Marfurt 2007 (SEG)",
        "families": {
            "amplitude": [k for k, v in ATTRIBUTE_SPECS.items() if v["family"] == "amplitude"],
            "complex_trace": [k for k, v in ATTRIBUTE_SPECS.items() if v["family"] == "complex_trace"],
            "frequency": [k for k, v in ATTRIBUTE_SPECS.items() if v["family"] == "frequency"],
            "structure": [k for k, v in ATTRIBUTE_SPECS.items() if v["family"] == "structure"],
        },
        "attribute_count": len(ATTRIBUTE_SPECS),
        "attributes": ATTRIBUTE_SPECS,
        "out_of_scope": OUT_OF_SCOPE,
        "orientation": "rows=TIME, cols=TRACE; frequency attributes in cycles/sample, never Hz",
    }


# ─────────────────────────── artifact (annotation) scan ───────────────────────────


def detect_artifact_zones_rgb(rgb: np.ndarray) -> np.ndarray:
    """Pass A — flag annotation/artifact zones in a FULL RGB raster.

    Two detectors, both geometry-aware, because a colour test alone is not enough:
      * black ink   — any pixel that is not seismic-conforming colour (any size)
      * uniform patch — a per-channel-uniform rectangle (a colour-conforming but FLAT
        label block, e.g. a red annotation box) passing a fill-ratio/shape filter

    Returns a boolean mask, True = artifact (must not be read as signal).
    """
    if rgb.ndim != 3 or rgb.shape[2] < 3:
        return np.zeros(rgb.shape[:2] if rgb.ndim >= 2 else (0, 0), dtype=bool)

    r = rgb[..., 0].astype(int)
    g = rgb[..., 1].astype(int)
    b = rgb[..., 2].astype(int)

    white_bg = (r > 232) & (g > 232) & (b > 232)
    black_ink = (r < 90) & (g < 90) & (b < 90)

    per_channel_std = np.stack(
        [
            np.sqrt(
                np.clip(
                    ndimage.uniform_filter(rgb[..., c].astype(float) ** 2, 5)
                    - ndimage.uniform_filter(rgb[..., c].astype(float), 5) ** 2,
                    0,
                    None,
                )
            )
            for c in range(3)
        ]
    )
    uniform_patch = (per_channel_std.max(axis=0) < 5.0) & ~white_bg

    art = np.zeros(rgb.shape[:2], dtype=bool)
    # Dilate the uniform-patch candidate before component analysis: a 5x5 window
    # straddling the edge of a flat label block sees mixed colours, so the block's
    # own edge rows are not "uniform" and would be lost. Growing the candidate first
    # keeps the whole label block inside one component.
    candidate = ndimage.binary_dilation(uniform_patch, iterations=2)
    labels, n = ndimage.label(candidate)
    for i in range(1, n + 1):
        m = labels == i
        if m.sum() < 80:
            continue
        ys, xs = np.where(m)
        h = ys.max() - ys.min() + 1
        w = xs.max() - xs.min() + 1
        fill = m.sum() / (h * w)
        if fill > 0.70 and w >= 12 and h >= 4:
            art |= m

    return ndimage.binary_dilation(art | black_ink, iterations=2)


def extract_seismic_convention(rgb: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """Pass B input — signed amplitude proxy from a seismic-convention raster.

    Classic seismic display = white background, RED positive, BLUE negative. The R-B
    channel difference recovers signed amplitude; a grayscale image collapses that
    difference to zero, so grayscale falls back to luminance (polarity lost, and the
    fallback is reported honestly rather than silently).

    Returns (proxy[rows, cols], meta).
    """
    rgb = np.asarray(rgb)
    if rgb.ndim == 2:
        arr = rgb.astype(float)
        arr = arr - arr.mean()
        std = float(arr.std()) or 1.0
        return arr / std, {"extraction": "luma", "polarity": "LOST (grayscale input)"}

    r = rgb[..., 0].astype(float)
    _g = rgb[..., 1].astype(float)
    b = rgb[..., 2].astype(float)
    rb = r - b
    rb_std = float(rb.std())
    is_color_display = rb_std > 8.0

    if is_color_display:
        proxy = rb / 255.0
        art = detect_artifact_zones_rgb(rgb)
        proxy = np.where(art, 0.0, proxy)
        return proxy, {
            "extraction": "rb_seismic_convention",
            "polarity": "PRESERVED (red/blue display)",
            "artifact_pixels_excluded": int(art.sum()),
            "artifact_fraction": float(art.sum() / max(art.size, 1)),
        }

    gray = rgb[..., :3].mean(axis=2)
    arr = gray - gray.mean()
    std = float(arr.std()) or 1.0
    return arr / std, {
        "extraction": "luma",
        "polarity": "LOST (grayscale input, no red/blue convention detected)",
        "artifact_pixels_excluded": 0,
        "artifact_fraction": 0.0,
    }


# ─────────────────────────── attribute computation ───────────────────────────


def compute_new_attributes(amp: np.ndarray, window: int = 11) -> dict[str, np.ndarray]:
    """Compute the attributes NOT already produced by the legacy zen catalog.

    The legacy four (rms, coherence, discontinuity, dip) stay in seismic_zen_f1 so
    existing numbers and contracts do not move.
    """
    if amp.size == 0:
        return {}

    w = max(3, int(window) | 1)
    out: dict[str, np.ndarray] = {}

    analytic = hilbert(amp, axis=0)
    envelope = np.abs(analytic)
    phase = np.angle(analytic)
    phase_unwrapped = np.unwrap(phase, axis=0)

    # ── amplitude family ──
    out["amplitude"] = np.abs(amp)
    out["envelope"] = envelope
    out["energy"] = ndimage.uniform_filter(amp**2, size=w)
    out["variance"] = out["energy"] - ndimage.uniform_filter(amp, size=w) ** 2
    out["mean_amplitude"] = ndimage.uniform_filter(amp, size=w)
    out["max_magnitude"] = ndimage.maximum_filter(np.abs(amp), size=w)

    peak = np.max(envelope, axis=0)
    total = np.sqrt(np.mean(envelope**2, axis=0) + 1e-10)
    out["sweetness"] = np.tile(peak / total, (amp.shape[0], 1))

    # ── complex-trace family ──
    out["instantaneous_phase"] = phase
    out["cosine_phase"] = np.cos(phase)

    inst_f = np.gradient(phase_unwrapped, axis=0)
    out["instantaneous_frequency"] = inst_f

    denom = 2.0 * np.pi * np.maximum(np.abs(inst_f), 1e-3)
    out["instantaneous_bandwidth"] = np.abs(np.gradient(envelope, axis=0)) / denom

    peak_idx = np.argmax(envelope, axis=0)
    cols = np.arange(amp.shape[1])
    out["apparent_polarity"] = np.tile(np.sign(analytic.real[peak_idx, cols]), (amp.shape[0], 1))

    # ── frequency family ──
    spec = np.abs(np.fft.rfft(amp, axis=0)) ** 2
    freqs = np.fft.rfftfreq(amp.shape[0], d=1.0)
    out["dominant_frequency"] = np.tile(freqs[np.argmax(spec, axis=0)], (amp.shape[0], 1))
    psum = np.sum(spec, axis=0) + 1e-10
    out["centroid_frequency"] = np.tile(np.sum(freqs[:, None] * spec, axis=0) / psum, (amp.shape[0], 1))

    # ── structure family ──
    u = ndimage.uniform_filter(amp, size=(1, w))
    v = ndimage.uniform_filter(amp**2, size=(1, w))
    out["semblance"] = (u**2) / (v + 1e-10)

    smoothed = ndimage.gaussian_filter(amp, sigma=1.0)
    gx = ndimage.sobel(smoothed, axis=1)
    gy = ndimage.sobel(smoothed, axis=0)
    jxx = ndimage.gaussian_filter(gx * gx, 2)
    jxy = ndimage.gaussian_filter(gx * gy, 2)
    jyy = ndimage.gaussian_filter(gy * gy, 2)
    orientation = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    out["azimuth"] = np.degrees(orientation)
    out["curvature"] = np.abs(ndimage.laplace(smoothed))

    return out


def summarize_array(a: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(a)),
        "max": float(np.max(a)),
        "mean": float(np.mean(a)),
        "std": float(np.std(a)),
        "p50": float(np.median(a)),
    }
