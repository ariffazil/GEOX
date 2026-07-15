"""
GEOX Wavelet Extract — Phase 4 least-squares / Wiener deconvolution.

s ≈ w * r  →  estimate w given reflectivity r and seismic s.

Frequency-domain Wiener:
  W(f) = S(f) · R*(f) / (|R(f)|² + ε)

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np


def extract_wavelet_least_squares(
    reflectivity: np.ndarray | list[float],
    seismic_trace: np.ndarray | list[float],
    *,
    dt_ms: float = 4.0,
    wavelet_length_ms: float = 120.0,
    epsilon: float = 1e-3,
) -> dict[str, Any]:
    """Estimate wavelet via Wiener deconvolution in frequency domain.

    Returns JSON-serializable dict (lists, not ndarray).
    """
    r = np.asarray(reflectivity, dtype=float).ravel()
    s = np.asarray(seismic_trace, dtype=float).ravel()
    if len(r) < 8 or len(s) < 8:
        return {
            "wavelet": [],
            "condition_number": float("inf"),
            "epsilon_used": float(epsilon),
            "new_synthetic": [],
            "updated_mistie_ms": None,
            "updated_correlation": None,
            "phase_class": "unknown",
            "wavelet_length_ms": wavelet_length_ms,
            "dt_ms": dt_ms,
            "physics_guard": {
                "guard_passed": False,
                "violations": ["traces too short for wavelet extraction"],
            },
        }

    n = min(len(r), len(s))
    r, s = r[:n], s[:n]
    # zero-pad to power of 2 for stable FFT
    n_fft = 1
    while n_fft < n * 2:
        n_fft *= 2

    R = np.fft.rfft(r, n=n_fft)
    S = np.fft.rfft(s, n=n_fft)
    power = np.abs(R) ** 2
    # adaptive epsilon if ill-conditioned
    pmax = float(np.max(power)) if np.max(power) > 0 else 1.0
    eps = float(max(epsilon, 1e-8 * pmax))
    W = S * np.conj(R) / (power + eps)
    w_full = np.fft.irfft(W, n=n_fft)

    # compact support: center wavelet, truncate to length
    n_w = max(3, int(round(wavelet_length_ms / max(dt_ms, 0.1))))
    if n_w % 2 == 0:
        n_w += 1
    # shift peak to center
    peak = int(np.argmax(np.abs(w_full[:n])))
    half = n_w // 2
    # circular extract around peak
    idx = (np.arange(n_w) - half + peak) % len(w_full)
    wavelet = w_full[idx]
    # normalize peak amplitude
    am = np.max(np.abs(wavelet))
    if am > 0:
        wavelet = wavelet / am

    # condition number proxy from power spectrum
    p_pos = power[power > 0]
    if len(p_pos) > 0:
        cond = float(np.max(p_pos) / (np.min(p_pos) + 1e-30))
    else:
        cond = float("inf")

    # new synthetic = wavelet * r
    synth = np.convolve(r, wavelet, mode="same")
    # align lengths
    m = min(len(synth), len(s))
    synth_m, s_m = synth[:m], s[:m]
    # correlation + lag
    if synth_m.std() > 1e-12 and s_m.std() > 1e-12:
        a = (synth_m - synth_m.mean()) / synth_m.std()
        b = (s_m - s_m.mean()) / s_m.std()
        corr_full = np.correlate(a, b, mode="full")
        lags = np.arange(-(m - 1), m)
        peak_i = int(np.argmax(np.abs(corr_full)))
        lag = int(lags[peak_i])
        corr = float(corr_full[peak_i] / m)
        mistie_ms = float(abs(lag) * dt_ms)
    else:
        corr, mistie_ms = 0.0, None

    phase_class: Literal["zero", "minimum", "mixed", "unknown"] = _classify_phase(wavelet)

    # causality: energy after peak vs before
    pk = int(np.argmax(np.abs(wavelet)))
    e_pre = float(np.sum(wavelet[:pk] ** 2))
    e_post = float(np.sum(wavelet[pk:] ** 2))

    return {
        "wavelet": [float(x) for x in wavelet],
        "condition_number": min(cond, 1e12),
        "epsilon_used": eps,
        "new_synthetic": [float(x) for x in synth_m],
        "updated_mistie_ms": mistie_ms,
        "updated_correlation": round(corr, 4) if corr is not None else None,
        "phase_class": phase_class,
        "wavelet_length_ms": float(n_w * dt_ms),
        "dt_ms": float(dt_ms),
        "physics_guard": {
            "guard_passed": bool(np.isfinite(cond) and cond < 1e10),
            "condition_number": min(cond, 1e12),
            "epsilon": eps,
            "compact_support_samples": n_w,
            "energy_pre_peak": e_pre,
            "energy_post_peak": e_post,
            "causality_ratio_post_over_pre": e_post / (e_pre + 1e-12),
            "nyquist_hz": 1000.0 / (2.0 * dt_ms),
            "violations": [] if cond < 1e10 else ["ill-conditioned reflectivity spectrum"],
        },
    }


def _classify_phase(w: np.ndarray) -> Literal["zero", "minimum", "mixed", "unknown"]:
    if len(w) < 3:
        return "unknown"
    pk = int(np.argmax(np.abs(w)))
    mid = len(w) // 2
    # zero-phase: peak near center, roughly symmetric
    left = w[: pk + 1][::-1] if pk > 0 else w[:1]
    right = w[pk:]
    n = min(len(left), len(right))
    if n < 2:
        return "unknown"
    sym = float(np.corrcoef(left[:n], right[:n])[0, 1]) if n > 1 else 0.0
    if abs(pk - mid) <= 2 and sym > 0.7:
        return "zero"
    if pk < mid // 2:
        return "minimum"
    if abs(sym) < 0.3:
        return "mixed"
    return "mixed" if abs(pk - mid) > 2 else "zero"
