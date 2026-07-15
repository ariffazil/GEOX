"""
GEOX Well-Tie MCP Compute Functions — Phase 3-4.
═════════════════════════════════════════════════════════════════════

Three governed computation functions that feed into the existing Pydantic
schema builders (mistie_rms.py, wavelet_extract.py, td_methods/base.py).

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations
from typing import Any
import numpy as np
from geox_core.core.welltie import compute_td_function, cross_correlate
from geox_core.schemas.mistie_rms import MistieRMSInput, build_mistie_receipt as _build_mistie
from geox_core.schemas.wavelet_extract import WaveletExtractInput, build_wavelet_receipt as _build_wavelet

def _arr(x):
    return np.asarray(x, dtype=float)


def compute_mistie_rms(inp: MistieRMSInput) -> dict[str, Any]:
    """Compute RMS mistie between synthetic and seismic traces."""
    synth = _arr(inp.synthetic_trace)
    seism = _arr(inp.seismic_trace)
    dt, n = inp.dt_ms, len(synth)

    corr_coef, residual_rms, time_shift_ms = cross_correlate(synth, seism)

    lag_idx = round(time_shift_ms / dt)
    if lag_idx > 0:
        synth_shifted = np.concatenate([np.zeros(lag_idx), synth[:-lag_idx]])
    elif lag_idx < 0:
        synth_shifted = np.concatenate([synth[-lag_idx:], np.zeros(-lag_idx)])
    else:
        synth_shifted = synth.copy()

    t1, t2 = inp.time_window_ms
    i1, i2 = max(0, int(t1 / dt)), min(n, int(t2 / dt) + 1)
    if i2 <= i1 + 5:
        i1, i2 = 0, n
    s_win, r_win = synth_shifted[i1:i2], seism[i1:i2]
    mask = np.isfinite(s_win) & np.isfinite(r_win)
    if mask.sum() < 5:
        raise ValueError("Too few valid samples in mistie window")
    s_w, r_w = s_win[mask], r_win[mask]
    residual = s_w - r_w
    rms = float(np.sqrt(np.mean(residual**2)))
    norm_rms = float(rms / (np.std(r_w) + 1e-9))
    local_corr = float(np.corrcoef(s_w, r_w)[0,1]) if len(s_w) > 2 else 0.0

    per_interval = [{"interval_name": "target_zone", "top_ms": float(t1), "base_ms": float(t2), "rms_ms": rms, "correlation": local_corr}]

    residual_class = "unexplained"
    residual_desc = ""
    if rms <= inp.threshold_ms * 0.5:
        residual_class = "good_tie"
    elif abs(time_shift_ms) > inp.max_lag_ms * 0.5:
        residual_class = "time_depth_error"
        residual_desc = f"Large lag {time_shift_ms:.1f} ms suggests time-depth error"

    phys = {"bounds_ok": True, "lag_ok": abs(time_shift_ms) <= inp.max_lag_ms, "correlation_ok": corr_coef >= 0.40, "violations": []}
    if abs(time_shift_ms) > inp.max_lag_ms:
        phys["violations"].append(f"Lag {time_shift_ms:.1f} ms exceeds max {inp.max_lag_ms:.0f} ms")

    return _build_mistie(
        well_name=inp.well_name, optimal_lag_ms=float(time_shift_ms), rms_mistie_ms=rms,
        correlation_coefficient=float(corr_coef), residual_rms_normalized=norm_rms,
        threshold_ms=inp.threshold_ms, max_lag_searched_ms=inp.max_lag_ms,
        samples_in_window=len(s_w), per_interval=per_interval,
        residual_class=residual_class, residual_description=residual_desc, physics_guard=phys, session_id=inp.session_id)


def extract_wavelet_least_squares(inp: WaveletExtractInput) -> dict[str, Any]:
    """Wiener least-squares wavelet extraction: W = S·R*/(|R|²+ε)."""
    r = _arr(inp.reflectivity_series)
    s = _arr(inp.seismic_trace)
    dt, eps, wavelet_samps = inp.dt_ms, inp.epsilon, int(inp.wavelet_length_ms / dt)
    n = min(len(r), len(s))
    r, s = r[:n], s[:n]

    R = np.fft.rfft(r); S = np.fft.rfft(s)
    freqs = np.fft.rfftfreq(n, d=dt/1000.0)
    R_power = np.abs(R)**2
    R_max = max(np.max(R_power), 1e-12)
    condition_number = float(R_max / (np.min(R_power[R_power>0] or 1) + 1e-12))
    W_hat = S * np.conj(R) / (R_power + eps)
    signal_mask = R_power > eps * R_max
    if not np.any(signal_mask):
        raise ValueError("No frequency bins above noise floor — increase ε or check data")
    W_hat[~signal_mask] = 0.0

    w_full = np.fft.irfft(W_hat, n=n)
    if len(w_full) > wavelet_samps:
        energy = np.convolve(w_full**2, np.ones(21), mode='same')
        peak_idx = int(np.argmax(energy))
        half = wavelet_samps // 2
        start = max(0, peak_idx - half)
        w = w_full[start:min(n, start + wavelet_samps)]
    else:
        w = w_full

    q1_len = max(1, len(w)//4)
    pre_ring = float(np.sum(w[:q1_len]**2) / (np.sum(w**2) + 1e-12))
    if pre_ring < 0.10: pc = "zero_phase"
    elif pre_ring > 0.40: pc = "minimum_phase"
    else: pc = "mixed_phase"
    W_fft = np.fft.rfft(w, n=n)
    phase_deg = float(np.degrees(np.angle(np.mean(W_fft[signal_mask[:len(W_fft)]]))))
    W_mag = np.abs(W_fft)
    W_peak = np.max(W_mag) or 1.0
    above = freqs[:len(W_mag)][W_mag >= W_peak/np.sqrt(2)]
    bandwidth = float(np.max(above)-np.min(above)) if len(above)>1 else 0.0

    new_synth = np.convolve(r, w, mode='same')[:n]
    cmask = np.isfinite(new_synth) & np.isfinite(s)
    new_corr = float(np.corrcoef(new_synth[cmask], s[cmask])[0,1]) if cmask.sum()>10 else 0.0
    new_rms = float(np.sqrt(np.mean((new_synth[cmask]-s[cmask])**2)))

    old_corr = 0.0
    try:
        from geox_core.core.welltie import build_wavelet_from_type
        ricker = build_wavelet_from_type("ricker", 20.0, dt)
        osyn = np.convolve(r, ricker, mode='same')[:n]
        omask = np.isfinite(osyn) & np.isfinite(s)
        old_corr = float(np.corrcoef(osyn[omask], s[omask])[0,1]) if omask.sum()>10 else 0.0
    except: pass

    phys = {"compact_support": len(w) <= wavelet_samps+10, "causality_ok": pre_ring<0.60, "pre_ring_ratio": pre_ring, "spectral_division_ok": condition_number < inp.max_condition_number*10, "violations": []}
    if phys["compact_support"]==False: phys["violations"].append("Wavelet exceeds compact support")
    if phys["causality_ok"]==False: phys["violations"].append(f"Pre-ring ratio {pre_ring:.2f} suggests non-causal")

    return _build_wavelet(
        well_name=inp.well_name, wavelet=[float(x) for x in w], dt_ms=dt,
        phase_class=pc, phase_degrees_estimated=phase_deg, condition_number=condition_number,
        epsilon_used=eps, spectral_bandwidth_hz=bandwidth,
        new_synthetic=[float(x) for x in new_synth], new_correlation=new_corr,
        new_rms_mistie_ms=new_rms, old_correlation=old_corr,
        max_condition_number=inp.max_condition_number, min_correlation_after=inp.min_correlation_after,
        physics_guard=phys, session_id=inp.session_id)


def compute_td_calibrate(*, las_path, checkshot_path=None, checkshot_data=None, method="linear", velocity_bounds=(1500.0,6000.0), residual_threshold_pct=10.0):
    import json, numpy as np
    cs_data = checkshot_data
    if checkshot_path and not cs_data:
        with open(checkshot_path) as f:
            raw = json.load(f)
        cs_data = raw if isinstance(raw, list) else (raw.get("checkshots", [raw]) if isinstance(raw, dict) else [raw])
    if not cs_data:
        raise ValueError("checkshot_path or checkshot_data required")
    curves = {}
    with open(las_path) as f:
        in_data = False
        for line in f:
            line = line.strip()
            if line.startswith("~A"): in_data = True; continue
            if in_data and line:
                parts = line.split()
                if len(parts) >= 1: curves.setdefault("DEPT",[]).append(float(parts[0]))
    depth = np.array(curves["DEPT"], dtype=float)
    result = compute_td_function(cs_data, depth, method=method)
    receipt = result.to_dict() if hasattr(result, "to_dict") else result
    receipt["_source"] = {"las_path": las_path, "checkshot": checkshot_path or "inline_data", "method": method}
    return receipt
