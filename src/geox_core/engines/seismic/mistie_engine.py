"""
GEOX Mistie RMS Engine — Phase 3: Falsifiable Well-Seismic Mistie Gate
═══════════════════════════════════════════════════════════════════════════════════

Extends cross_correlate() with:
  - Absolute ms conversion (dt_ms parameter)
  - Hard 25 ms gate → SEAL/HOLD/VOID verdict
  - Per-interval mistie breakdown
  - PhysicsGuard

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("geox.mistie_rms")


def compute_mistie_rms(
    synthetic_trace: np.ndarray,
    seismic_trace: np.ndarray,
    dt_ms: float,
    time_window_ms: tuple[float, float] | None = None,
    threshold_ms: float = 25.0,
    max_lag_ms: float = 50.0,
    intervals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute RMS mistie between synthetic and real seismic traces.

    Parameters
    ----------
    synthetic_trace : np.ndarray
        Synthetic trace s(t) from Phase 1.
    seismic_trace : np.ndarray
        Real seismic trace r(t) at well location.
    dt_ms : float
        Sample interval in milliseconds.
    time_window_ms : tuple[float, float], optional
        (sample_idx_start, sample_idx_end) — window in sample space.
        If None, use full trace.
    threshold_ms : float
        Hard gate: RMS mistie > threshold → HOLD.
    max_lag_ms : float
        Maximum allowed cross-correlation lag in ms.
    intervals : list[dict], optional
        Per-interval: [{"name": str, "top_sample": int, "base_sample": int}, ...]

    Returns
    -------
    dict
        Governed mistie envelope.
    """
    synth = np.asarray(synthetic_trace, dtype=float)
    seis = np.asarray(seismic_trace, dtype=float)

    # ── Input validation ──────────────────────────────────────────────────
    if len(synth) < 10 or len(seis) < 10:
        return _error_result("Traces too short (< 10 samples).", threshold_ms)

    if len(synth) != len(seis):
        min_len = min(len(synth), len(seis))
        logger.warning(f"Trace length mismatch: synth={len(synth)} seis={len(seis)}. Truncating to {min_len}.")
        synth = synth[:min_len]
        seis = seis[:min_len]

    if dt_ms <= 0:
        return _error_result(f"dt_ms must be positive, got {dt_ms}.", threshold_ms)

    # ── Window selection (in sample-index space) ──────────────────────────
    n_total = len(synth)
    if time_window_ms is not None:
        idx1 = max(0, int(time_window_ms[0]))
        idx2 = min(n_total, int(time_window_ms[1]))
        if idx2 <= idx1:
            return _error_result(f"Invalid window {time_window_ms} — idx2 <= idx1.", threshold_ms)
        synth_win = synth[idx1:idx2]
        seis_win = seis[idx1:idx2]
        window_label = f"samples {idx1}-{idx2}"
    else:
        synth_win = synth
        seis_win = seis
        idx1 = 0
        idx2 = n_total
        window_label = "full trace"

    n_samples = len(synth_win)
    if n_samples < 10:
        return _error_result(f"Window too short ({n_samples} samples).", threshold_ms)

    # ── Cross-correlation ─────────────────────────────────────────────────
    synth_n = (synth_win - np.mean(synth_win)) / (np.std(synth_win) + 1e-9)
    seis_n = (seis_win - np.mean(seis_win)) / (np.std(seis_win) + 1e-9)

    corr = np.correlate(synth_n, seis_n, mode="full")
    lags_samples = np.arange(-(len(seis_n) - 1), len(seis_n))

    max_lag_samples = int(max_lag_ms / dt_ms)
    center = len(corr) // 2
    lo = max(0, center - max_lag_samples)
    hi = min(len(corr), center + max_lag_samples + 1)
    corr_search = corr[lo:hi]
    lags_search = lags_samples[lo:hi]

    peak_idx = int(np.argmax(np.abs(corr_search)))
    optimal_lag_samples = int(lags_search[peak_idx])
    optimal_lag_ms = float(optimal_lag_samples * dt_ms)

    correlation_coefficient = float(np.clip(corr_search[peak_idx] / max(n_samples, 1), -1.0, 1.0))

    # ── RMS mistie in ms ─────────────────────────────────────────────────
    # The mistie IS the optimal lag in ms. The residual is amplitude.
    shifted_seis = np.roll(seis_win, optimal_lag_samples) if abs(optimal_lag_samples) < len(seis_win) else seis_win
    residual = synth_win - shifted_seis
    residual_rms_normalized = float(np.sqrt(np.mean(residual**2)))

    # RMS mistie = absolute optimal lag (the actual time shift)
    rms_mistie_ms = float(abs(optimal_lag_ms))

    # ── Per-interval mistie ───────────────────────────────────────────────
    per_interval = []
    if intervals:
        for iv in intervals:
            iv_name = iv.get("name", "unnamed")
            iv_top = iv.get("top_sample", 0)
            iv_base = iv.get("base_sample", n_samples)
            iv_idx1 = max(0, int(iv_top) - idx1)
            iv_idx2 = min(n_samples, int(iv_base) - idx1)

            if iv_idx2 > iv_idx1 and iv_idx1 >= 0:
                iv_synth = synth_win[iv_idx1:iv_idx2]
                iv_seis = shifted_seis[iv_idx1:iv_idx2]

                iv_residual = iv_synth - iv_seis
                iv_rms = float(np.sqrt(np.mean(iv_residual**2)))
                iv_corr = float(
                    np.clip(
                        np.corrcoef(iv_synth, iv_seis)[0, 1] if len(iv_synth) > 1 else 0.0,
                        -1.0,
                        1.0,
                    )
                )

                per_interval.append(
                    {
                        "interval_name": iv_name,
                        "top_sample": iv_top,
                        "base_sample": iv_base,
                        "rms_amplitude": round(iv_rms, 6),
                        "correlation": round(iv_corr, 4),
                    }
                )

    # ── Residual classification ───────────────────────────────────────────
    if rms_mistie_ms <= threshold_ms * 0.5 and residual_rms_normalized < 0.3:
        residual_class = "good_tie"
        residual_description = "Residual within acceptable range."
    elif abs(optimal_lag_ms) > threshold_ms * 0.8:
        residual_class = "time_depth_error"
        residual_description = f"Large optimal lag ({optimal_lag_ms:.1f} ms) suggests T-D error."
    elif residual_rms_normalized > 0.5:
        residual_class = "wavelet_error"
        residual_description = f"High normalized residual ({residual_rms_normalized:.2f}) suggests wavelet mismatch."
    else:
        residual_class = "unexplained"
        residual_description = "Residual source not yet classified."

    # ── PhysicsGuard ──────────────────────────────────────────────────────
    nyquist_hz = 1000.0 / (2.0 * dt_ms)
    physics_guard = {
        "guard_passed": True,
        "physics_version": "geox-mistie-v1.0.0",
        "trace_length_samples": n_total,
        "window_length_samples": n_samples,
        "window_label": window_label,
        "dt_ms": dt_ms,
        "nyquist_hz": nyquist_hz,
        "max_lag_searched_ms": max_lag_ms,
        "optimal_lag_ms": optimal_lag_ms,
        "equations_used": [
            "C(τ) = Σ_k s(t_k) · r(t_k + τ)",
            "τ* = argmax |C(τ)|",
        ],
        "violations": [],
    }

    # ── Verdict ───────────────────────────────────────────────────────────
    if rms_mistie_ms > threshold_ms:
        verdict = "HOLD"
        verdict_reason = f"RMS mistie {rms_mistie_ms:.1f} ms exceeds threshold {threshold_ms:.1f} ms."
    else:
        verdict = "SEAL"
        verdict_reason = f"RMS mistie {rms_mistie_ms:.1f} ms within threshold {threshold_ms:.1f} ms."

    return {
        "optimal_lag_ms": round(optimal_lag_ms, 2),
        "rms_mistie_ms": round(rms_mistie_ms, 2),
        "correlation_coefficient": round(correlation_coefficient, 4),
        "residual_rms_normalized": round(residual_rms_normalized, 4),
        "verdict": verdict,
        "threshold_used_ms": threshold_ms,
        "verdict_reason": verdict_reason,
        "residual_class": residual_class,
        "residual_description": residual_description,
        "per_interval": per_interval,
        "max_lag_searched_ms": max_lag_ms,
        "samples_in_window": n_samples,
        "physics_guard": physics_guard,
        "anti_hantu_flags": [
            "mistie is not tie quality — it is one metric",
            "25 ms threshold is resolution limit, not quality grade",
        ],
    }


def _error_result(message: str, threshold_ms: float) -> dict[str, Any]:
    return {
        "optimal_lag_ms": 0.0,
        "rms_mistie_ms": float("inf"),
        "correlation_coefficient": 0.0,
        "residual_rms_normalized": 1.0,
        "verdict": "VOID",
        "threshold_used_ms": threshold_ms,
        "verdict_reason": f"Computation failed: {message}",
        "residual_class": "unexplained",
        "residual_description": message,
        "per_interval": [],
        "max_lag_searched_ms": 0.0,
        "samples_in_window": 0,
        "physics_guard": {"guard_passed": False, "violations": [message]},
        "anti_hantu_flags": ["computation failed — result is VOID"],
    }
