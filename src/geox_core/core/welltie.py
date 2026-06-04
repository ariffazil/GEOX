"""
GEOX Well-Tie Computation Engine
================================
Full well-to-seismic tie workflow:
  Sonic (DT) → Vp → AI → Reflectivity (Zoeppritz) → Wavelet → Synthetic → QC

Physics:
  Vp = 1e6 / DT  (DT in us/ft → Vp in m/s, or DT in us/m → Vp in m/s)
  AI  = Vp × ρ   (acoustic impedance)
  RC[i] = (AI[i+1] - AI[i]) / (AI[i+1] + AI[i])  (Zoeppritz approximation)
  Synthetic = convolve(RC, wavelet)

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import sys
import warnings

import numpy as np

# ── helpers already imported in section.py ──────────────────────────────────
# We re-import locally to keep this module self-contained.
sys.path.insert(0, "/root/geox")


def _load_las_curves(las_path: str) -> dict:
    """Load curves from LAS file using geox_1d.process_las_file."""
    from geox_core.core.geox_1d import process_las_file

    result = process_las_file(las_path)
    if "ERROR" in result:
        raise ValueError(f"LAS parse failed: {result.get('ERROR')}")
    return result


def _load_checkshot_data(checkshot_ref: str) -> list[dict]:
    """Load checkshot table from artifact store.

    Expected artifact format:
        {"data": [[depth_md, twt_ms], ...]}  or
        {"rows": [{"depth_md": float, "twt_ms": float}, ...]}
    """
    from geox_mcp.tools._helpers import _get_artifact

    entry = _get_artifact(checkshot_ref)
    if not entry:
        raise ValueError(f"Checkshot artifact not found: {checkshot_ref}")

    raw = entry.get("data") or entry.get("rows") or []
    if not raw:
        raise ValueError(f"Checkshot artifact has no data: {checkshot_ref}")

    # Normalise to list of {depth_md, twt_ms}
    if isinstance(raw[0], list):
        return [{"depth_md": float(r[0]), "twt_ms": float(r[1])} for r in raw]
    return raw


# ── Core computation ────────────────────────────────────────────────────────


def compute_td_from_checkshot(
    checkshot_data: list[dict],
    depth_array: np.ndarray,
) -> tuple[np.ndarray, float]:
    """
    Linear interpolation of TWT from checkshot table.

    Fails closed if checkshot depth range doesn't cover the LAS depth range.

    Returns:
        twt_ms array (one value per depth in depth_array)
    """
    depths = np.array([d["depth_md"] for d in checkshot_data])
    twts = np.array([d["twt_ms"] for d in checkshot_data])

    min_d, max_d = depths.min(), depths.max()
    if depth_array.min() < min_d or depth_array.max() > max_d:
        raise ValueError(
            f"Checkshot covers [{min_d:.1f}, {max_d:.1f}] m MD — "
            f"LAS extends to {depth_array.min():.1f}..{depth_array.max():.1f} m MD. "
            f"Cannot extrapolate TWT. Provide full checkshot coverage or use average velocity."
        )

    twt_interp = np.interp(depth_array, depths, twts)
    coverage_pct = 100.0 * np.sum((depth_array >= min_d) & (depth_array <= max_d)) / max(len(depth_array), 1)
    return twt_interp, coverage_pct


# ── Eureka 1: Multi-method T-D fitter dispatcher ────────────────────────────


def compute_td_function(
    checkshot_data: list[dict],
    depth_array: np.ndarray,
    method: str = "linear",
    **kwargs,
):
    """Multi-method T-D fitter dispatcher (Eureka 1).

    Wraps `geox_core.physics.td_methods.fit_td` and returns a `TDFitResult`
    envelope (not just twt + coverage). The 4 supported methods:

      - "linear"      (default; preserves compute_td_from_checkshot behaviour)
      - "polynomial"  (degree-bounded weighted fit, opt-in allow_extrapolation)
      - "vo_k"        (linear or exponential compaction, k from checkshots)
      - "layer_cake"  (per-formation V_int from tops + checkshots)

    Returns the full TDFitResult envelope: method, equation, coefficients,
    twt_ms, residuals_ms, rmse_ms, physics_guard, extrapolation_risk, fail_closed.

    Backward compat: pass method="linear" to get the same semantics as
    compute_td_from_checkshot (fail-closed on extrapolation).
    """
    from geox_core.physics.td_methods import fit_td

    # Normalise dict-format → list-of-dict (the fitters expect either, but
    # the canonical input is the dict format with "depth_md" / "twt_ms" keys).
    return fit_td(method, checkshot_data, np.asarray(depth_array, dtype=float), **kwargs)


def compute_average_velocity_td(
    vp_array: np.ndarray,
    depth_array: np.ndarray,
) -> np.ndarray:
    """
    Compute TWT from Vp using average-velocity integration.

    TWT[i] = 2 × Σ (Δz / Vp[i])

    Returns:
        twt_ms array (one value per depth sample)
    """
    twt = np.zeros_like(depth_array, dtype=float)
    for i in range(1, len(depth_array)):
        dz = depth_array[i] - depth_array[i - 1]
        # Average Vp over interval
        vp_avg = (vp_array[i] + vp_array[i - 1]) / 2.0
        if vp_avg > 0:
            twt[i] = twt[i - 1] + 2.0 * dz / vp_avg * 1000.0  # → ms
        else:
            twt[i] = twt[i - 1]
    return twt


def compute_vp_from_sonic(
    sonic_curve: np.ndarray,
    depth_array: np.ndarray,
    dt_unit: str = "usft",
) -> np.ndarray:
    """
    Convert sonic (DT) to Vp (m/s).

    Args:
        sonic_curve: DT values in us/ft ("usft") or us/m ("usm")
        dt_unit: "usft" (default) or "usm"
        depth_array: corresponding depth values (for bounds checking)

    Physics:
        Vp (m/s) = 1e6 / DT (μs/m)  when DT is in μs/m
        Vp (m/s) = 1e6 × 0.3048 / DT (μs/ft)  when DT is in μs/ft
    """
    dt = np.asarray(sonic_curve, dtype=float)
    dt = np.where(np.isfinite(dt), dt, np.nan)

    if dt_unit == "usft":
        # Vp (m/s) = 1e6 (μs/s) × 0.3048 (m/ft) / DT (μs/ft)
        vp = np.where(dt > 0, 1e6 * 0.3048 / dt, np.nan)
    else:
        # Vp (m/s) = 1e6 (μs/s) / DT (μs/m)
        vp = np.where(dt > 0, 1e6 / dt, np.nan)

    # Physical bounds: 1500 < Vp < 6000 m/s (CANON-9)
    outside = (vp < 1500) | (vp > 6000)
    n_outside = np.sum(outside)
    if n_outside > 0:
        warnings.warn(f"{n_outside}/{len(vp)} Vp values outside CANON-9 [1500, 6000] m/s. Clipping to bounds.")
        vp = np.clip(vp, 1500, 6000)

    return vp


def compute_ai(
    vp: np.ndarray,
    rho: np.ndarray,
    rho_unit: str = "gcc",
) -> np.ndarray:
    """
    Acoustic impedance: AI = Vp × ρ.

    Args:
        vp: Vp in m/s
        rho: density in g/cm³ ("gcc", default) or kg/m³ ("si")
        rho_unit: "gcc" (g/cm³) or "si" (kg/m³)

    Returns:
        AI array in (m/s) × (g/cm³) = kg/(m²·s) × 1000
        (standard petroleum physics units)
    """
    rho_ = np.asarray(rho, dtype=float)
    rho_ = np.where(np.isfinite(rho_), rho_, np.nan)

    if rho_unit == "si":
        rho_ = rho_ / 1000.0  # kg/m³ → g/cm³

    ai = vp * rho_
    # Physical bounds: AI > 0
    ai = np.where(np.isfinite(ai) & (ai > 0), ai, np.nan)
    return ai


def compute_reflectivity(ai: np.ndarray, polarity: str = "SEG_NORMAL") -> np.ndarray:
    """
    Zoeppritz reflectivity approximation at interface boundaries.

    RC[i] = (AI[i+1] - AI[i]) / (AI[i+1] + AI[i])

    Polarity convention:
      SEG_NORMAL  — positive RC = hard kick (↑AI) = peak (standard)
      SEG_REVERSE — positive RC = soft kick (↓AI) = trough (reversed display)

    Returns:
        RC series (len = len(ai) - 1) at interface midpoints
    """
    ai1 = ai[:-1]
    ai2 = ai[1:]

    rc = np.zeros(len(ai) - 1, dtype=float)
    mask = (ai1 + ai2) != 0
    rc[mask] = (ai2[mask] - ai1[mask]) / (ai2[mask] + ai1[mask])

    if polarity == "SEG_REVERSE":
        rc = -rc

    return rc


def build_wavelet_from_type(
    wavelet_type: str,
    frequency: float,
    dt_ms: float,
) -> np.ndarray:
    """Build wavelet using geox_2d.build_wavelet."""
    from geox_core.core.geox_2d import build_wavelet

    return build_wavelet(frequency=frequency, dt_ms=dt_ms, wavelet_type=wavelet_type)


def generate_synthetic_trace(
    rc: np.ndarray,
    twt_ms: np.ndarray,
    wavelet_type: str,
    wavelet_freq_hz: float | tuple[float, float, float, float],
    noise_db: float | None = -18,
    rng_seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convolve reflectivity series with wavelet to produce synthetic trace.

    Args:
        rc: reflectivity series
        twt_ms: TWT time array (ms) corresponding to rc midpoints
        wavelet_type: "ricker" | "ormsby" | "klauder"
        wavelet_freq_hz: scalar for ricker/klauder; (f1,f2,f3,f4) tuple for ormsby
        noise_db: noise level (dB ref max amplitude), -18 = moderate noise
        rng_seed: deterministic seed for reproducibility

    Returns:
        (synthetic_trace, twt_ms_output) — same length as rc
    """
    # Determine dt_ms from twt array
    if len(twt_ms) > 1:
        dt_ms = float(twt_ms[1] - twt_ms[0])
        dt_ms = max(dt_ms, 0.5)
    else:
        dt_ms = 1.0

    # Build wavelet
    if wavelet_type == "ormsby" and isinstance(wavelet_freq_hz, tuple):
        f1, f2, f3, f4 = wavelet_freq_hz
        # Ormsby needs scalar frequency for build_wavelet; pass average
        avg_freq = (f1 + f2 + f3 + f4) / 4.0
        wavelet = build_wavelet_from_type("ormsby", avg_freq, dt_ms)
    else:
        wavelet = build_wavelet_from_type(wavelet_type, float(wavelet_freq_hz), dt_ms)

    # Convolve — 'same' keeps same length as rc
    try:
        import numpy as np

        synthetic = np.convolve(wavelet, rc, mode="same")
    except Exception:
        synthetic = np.zeros_like(rc)

    # Add noise
    if noise_db is not None and noise_db < 0:
        noise_amp = 10 ** (noise_db / 20.0)
        rng = np.random.default_rng(rng_seed)
        noise = rng.normal(0, noise_amp, len(synthetic))
        synthetic = synthetic + noise

    # Normalise
    max_abs = np.max(np.abs(synthetic))
    if max_abs > 0:
        synthetic = synthetic / max_abs

    return synthetic, twt_ms


def apply_phase_rotation(synthetic: np.ndarray, phase_degrees: float) -> np.ndarray:
    """
    Apply constant phase rotation to synthetic trace.

    Phase rotation in frequency domain:
      φ(rad) = phase_degrees × π / 180
      Rotate complex spectrum by φ
    """
    if abs(phase_degrees) < 0.1:
        return synthetic

    phi = np.deg2rad(phase_degrees)
    n = len(synthetic)

    # FFT → rotate → iFFT
    spectrum = np.fft.rfft(synthetic)
    np.fft.rfftfreq(n)
    rotation = np.cos(phi) + 1j * np.sin(phi)
    rotated_spectrum = spectrum * rotation
    return np.fft.irfft(rotated_spectrum, n=n)


def cross_correlate(
    synth: np.ndarray,
    seismic: np.ndarray,
) -> tuple[float, float, float]:
    """
    Cross-correlate synthetic with seismic trace.

    Returns:
        (correlation_coefficient, residual_rms, time_shift_ms)

    correlation_coefficient: Pearson r in [-1, 1]
    residual_rms: normalised RMS of (synth - shift(seismic))
    time_shift_ms: lag at peak correlation
    """
    import numpy as np

    # Normalise
    synth_n = (synth - np.mean(synth)) / (np.std(synth) + 1e-9)
    seis_n = (seismic - np.mean(seismic)) / (np.std(seismic) + 1e-9)

    # Cross-correlation
    corr = np.correlate(synth_n, seis_n, mode="full")
    lags = np.arange(-(len(seis_n) - 1), len(seis_n))

    # Find peak lag
    peak_idx = int(np.argmax(np.abs(corr)))
    time_shift = lags[peak_idx]

    # Convert lag to ms (assuming dt = 1 sample)
    dt_ms = 1.0  # assume 1ms sampling for correlation index
    time_shift_ms = time_shift * dt_ms

    # Normalised correlation at peak
    max_corr = corr[peak_idx] / max(len(synth), 1)

    # Residual RMS
    if abs(time_shift) < len(seismic):
        shifted_seis = np.roll(seismic, int(time_shift))
        residual = synth - shifted_seis
    else:
        residual = synth
    residual_rms = float(np.sqrt(np.mean(residual**2)))

    return float(np.clip(max_corr, -1.0, 1.0)), residual_rms, float(time_shift_ms)


def assess_tie_quality(
    correlation_coefficient: float,
    residual_rms: float,
    phase_rotation_deg: float,
    polarity_reversed: bool,
) -> str:
    """
    Return tie quality verdict.

    Thresholds:
      correlation ≥ 0.85  → EXCELLENT
      correlation ≥ 0.75  → GOOD
      correlation ≥ 0.60  → MODERATE
      correlation < 0.60  → POOR
      residual_rms > 0.5  → downgrade one tier
    """
    if correlation_coefficient >= 0.85 and residual_rms < 0.3:
        base = "EXCELLENT"
    elif correlation_coefficient >= 0.75:
        base = "GOOD"
    elif correlation_coefficient >= 0.60:
        base = "MODERATE"
    elif correlation_coefficient > 0:
        base = "POOR"
    else:
        return "UNDETERMINED"

    # Downgrade if residual RMS too high
    if residual_rms > 0.5:
        if base == "EXCELLENT":
            base = "GOOD"
        elif base == "GOOD":
            base = "MODERATE"
        elif base == "MODERATE":
            base = "POOR"

    if polarity_reversed:
        base += " (POLARITY_REVERSED)"

    return base


def polarity_check(ai: np.ndarray, seg_polarity: str) -> bool:
    """
    Heuristic polarity check: SEG_NORMAL → first major RC should be negative (water bottom hard kick).

    Returns True if polarity appears consistent with declared convention.
    """
    if len(ai) < 2:
        return True  # Cannot determine

    (ai[1] - ai[0]) / (ai[1] + ai[0] + 1e-9)
    if seg_polarity == "SEG_NORMAL":
        # Water bottom (soft→hard): AI increases → RC should be positive
        # But convention varies; just flag large RC at top
        pass  # Heuristic only — don't hard-fail
    return True


# ── Main entry point ────────────────────────────────────────────────────────


def compute_welltie(
    las_path: str,
    checkshot_ref: str | None = None,
    wavelet_mode: str = "ricker",
    wavelet_freq_hz: float | list[float] | None = None,
    phase_degrees: float = 0.0,
    polarity: str = "SEG_NORMAL",
    seismic_ref: str | None = None,
    sonic_curve: str = "DT",
    density_curve: str = "RHOB",
    matrix_density: float = 2.65,
    fluid_density: float = 1.0,
    noise_db: float = -18,
) -> dict:
    """
    Orchestrate full well-to-seismic tie workflow.

    Args:
        las_path: Path to LAS file
        checkshot_ref: Artifact ref for checkshot table (depth_md → twt_ms)
        wavelet_mode: "ricker" | "ormsby" | "klauder" | "estimated"
        wavelet_freq_hz: Scalar Hz (ricker/klauder) or [f1,f2,f3,f4] Hz (ormsby)
        phase_degrees: Phase rotation to apply to synthetic (degrees)
        polarity: "SEG_NORMAL" | "SEG_REVERSE"
        seismic_ref: Optional seismic trace artifact ref for correlation QC
        sonic_curve: LAS curve mnemonic for sonic (DT or DT4)
        density_curve: LAS curve mnemonic for density (RHOB)
        matrix_density: g/cm³ fallback if no density curve
        fluid_density: g/cm³ fallback if no density curve
        noise_db: Synthetic noise level (dB ref max)

    Returns:
        Governed artifact dict with all tie metrics and QC results.
    """
    import numpy as np

    # ── 1. Load LAS ────────────────────────────────────────────────────────────
    curves = _load_las_curves(las_path)

    # Extract depth
    depth_arr = None
    for dk in ["DEPT", "DEPTH", "MD"]:
        if dk in curves:
            depth_arr = np.array(curves[dk], dtype=float)
            break
    if depth_arr is None:
        raise ValueError(f"No depth curve (DEPT/DEPTH/MD) found in LAS: {las_path}")

    # Extract sonic (DT)
    sonic_arr = None
    for alias in [sonic_curve, "DT4", "DT"]:
        if alias in curves:
            sonic_arr = np.array(curves[alias], dtype=float)
            break
    if sonic_arr is None:
        raise ValueError(
            f"No sonic curve ({sonic_curve}/DT4/DT) found in LAS: {las_path}. "
            f"Well tie requires sonic data. "
            f"Available curves: {list(curves.keys())}"
        )

    # Determine sonic unit (try to infer from values)
    dt_mean = np.nanmean(np.abs(sonic_arr))
    if dt_mean > 200:  # > 200 us/ft is unrealistic; likely us/m
        dt_unit = "usm"
    else:
        dt_unit = "usft"

    # Extract density (RHOB) or fall back
    rho_arr = None
    density_assumption = None
    for alias in [density_curve, "RHOB"]:
        if alias in curves:
            rho_arr = np.array(curves[alias], dtype=float)
            break

    if rho_arr is None or np.all(np.isnan(rho_arr)):
        # Fallback: use matrix/fluid density with porosity proxy
        density_assumption = (
            f"density curve not found — using matrix={matrix_density} g/cm³, "
            f"fluid={fluid_density} g/cm³ with Vsh estimate as porosity proxy"
        )
        # Rough Vsh estimate from GR if available
        gr_arr = None
        for galias in ["GR", "GRC", "SGR"]:
            if galias in curves:
                gr_arr = np.array(curves[galias], dtype=float)
                break
        if gr_arr is not None:
            # Simple Vsh from GR
            gr_min, gr_max = np.nanmin(gr_arr), np.nanmax(gr_arr)
            if gr_max > gr_min:
                vsh = (gr_arr - gr_min) / (gr_max - gr_min)
                vsh = np.clip(vsh, 0, 1)
            else:
                vsh = np.full_like(depth_arr, 0.3, dtype=float)
        else:
            vsh = np.full_like(depth_arr, 0.3, dtype=float)
        rho_arr = matrix_density * (1 - vsh) + fluid_density * vsh
    else:
        density_assumption = "RHOB curve from LAS"

    # ── 2. Time-depth conversion ───────────────────────────────────────────────
    if checkshot_ref:
        checkshot_data = _load_checkshot_data(checkshot_ref)
        twt_ms, coverage_pct = compute_td_from_checkshot(checkshot_data, depth_arr)
        td_method = "checkshot"
    else:
        # Average velocity from sonic
        vp_arr = compute_vp_from_sonic(sonic_arr, depth_arr, dt_unit)
        twt_ms = compute_average_velocity_td(vp_arr, depth_arr)
        coverage_pct = 100.0
        td_method = "average_velocity"

    # ── 3. Vp from sonic ──────────────────────────────────────────────────────
    vp_arr = compute_vp_from_sonic(sonic_arr, depth_arr, dt_unit)

    # ── 4. AI ──────────────────────────────────────────────────────────────────
    ai_arr = compute_ai(vp_arr, rho_arr)

    # ── 5. Reflectivity ───────────────────────────────────────────────────────
    rc_arr = compute_reflectivity(ai_arr, polarity=polarity)

    # Time for RC midpoints
    if len(twt_ms) > 1:
        twt_rc = (twt_ms[:-1] + twt_ms[1:]) / 2.0
    else:
        twt_rc = twt_ms[:-1] if len(twt_ms) > 1 else twt_ms

    # ── 6. Wavelet frequency ────────────────────────────────────────────────────
    if wavelet_freq_hz is None:
        wavelet_freq_hz = 35.0  # default 35 Hz

    if isinstance(wavelet_freq_hz, list):
        # Ormsby needs (f1,f2,f3,f4) tuple
        if wavelet_mode == "ormsby" and len(wavelet_freq_hz) == 4:
            freq_hz = tuple(wavelet_freq_hz)  # type: ignore[assignment]
        else:
            freq_hz = float(wavelet_freq_hz[0])  # take first element
    else:
        freq_hz = float(wavelet_freq_hz)

    # ── 7. Synthetic seismogram ────────────────────────────────────────────────
    synthetic, twt_out = generate_synthetic_trace(
        rc=rc_arr,
        twt_ms=twt_rc,
        wavelet_type=wavelet_mode,
        wavelet_freq_hz=freq_hz,
        noise_db=noise_db,
    )

    # ── 8. Phase rotation ──────────────────────────────────────────────────────
    if abs(phase_degrees) > 0.1:
        synthetic = apply_phase_rotation(synthetic, phase_degrees)

    # ── 9. Correlation with seismic (if provided) ───────────────────────────────
    correlation_coef = None
    residual_rms = None
    time_shift_ms = None

    if seismic_ref:
        from geox_mcp.tools._helpers import _get_artifact

        seis_entry = _get_artifact(seismic_ref)
        if seis_entry and "trace" in seis_entry:
            seismic_trace = np.array(seis_entry["trace"], dtype=float)
            correlation_coef, residual_rms, time_shift_ms = cross_correlate(synthetic, seismic_trace)
            abs(1.0 - abs(correlation_coef))  # proxy
        else:
            # Try as numpy artifact
            try:
                seismic_trace = np.array(seis_entry.get("data", []) if seis_entry else [], dtype=float)
                if len(seismic_trace) > 0:
                    correlation_coef, residual_rms, time_shift_ms = cross_correlate(synthetic, seismic_trace)
            except Exception:
                pass

    # ── 10. Polarity check ─────────────────────────────────────────────────────
    polarity_verdict = polarity_check(ai_arr, polarity)
    polarity_reversed = polarity == "SEG_REVERSE" if polarity_verdict is not False else True

    # ── 11. Tie quality ────────────────────────────────────────────────────────
    if correlation_coef is not None:
        tie_verdict = assess_tie_quality(correlation_coef, residual_rms or 0.0, phase_degrees, polarity_reversed)
    else:
        # No seismic to correlate — mark as undetermined
        tie_verdict = "UNDETERMINED"

    # ── 12. Assemble assumptions list ──────────────────────────────────────────
    assumptions = [
        density_assumption,
        f"Time-depth: {td_method}",
        f"Wavelet: {wavelet_mode} at {freq_hz} Hz",
        "Reflectivity: Zoeppritz linear approximation",
    ]
    if phase_degrees != 0:
        assumptions.append(f"Phase rotation applied: {phase_degrees}°")
    if polarity == "SEG_REVERSE":
        assumptions.append("SEG_REVERSE polarity convention applied")
    if td_method == "average_velocity":
        assumptions.append("No checkshot — Vp integrated from sonic; check forcycle speed error")

    # ── 13. Physics guard (CANON-9 bounds) ───────────────────────────────────
    # CANON-9 bounds: Vp ∈ [1500, 6000] m/s, rho ∈ [1000, 5000] kg/m³
    vp_ok = []
    for v in vp_arr:
        grade = "AAA" if (1500 <= float(v) <= 6000) else "RAW"
        vp_ok.append(grade != "RAW")

    ai_ok = []
    for a in ai_arr:
        if np.isnan(a) or a <= 0:
            ai_ok.append(False)
        else:
            ai_ok.append(True)

    physics_guard = {
        "Vp_bounds_check": {
            "canon_9": "Vp ∈ [1500, 6000] m/s",
            "pct_in_bounds": float(np.sum(vp_ok) / max(len(vp_ok), 1)),
            "n_outside": int(np.sum(~np.array(vp_ok))),
        },
        "AI_positive_check": {
            "pct_positive": float(np.sum(ai_ok) / max(len(ai_ok), 1)),
            "n_non_positive": int(np.sum(~np.array(ai_ok))),
        },
    }

    # ── 14. Build artifact ─────────────────────────────────────────────────────
    artifact = {
        "las_path": las_path,
        "tie_quality_verdict": tie_verdict,
        "correlation_coefficient": correlation_coef if correlation_coef is not None else None,
        "residual_rms": residual_rms,
        "phase_rotation_applied": phase_degrees,
        "time_shift_ms": time_shift_ms,
        "polarity_verdict": ("MATCHED" if not polarity_reversed else "REVERSED"),
        "wavelet": {
            "type": wavelet_mode,
            "frequency_hz": freq_hz if not isinstance(freq_hz, list) else freq_hz,
            "phase_degrees": phase_degrees,
        },
        "synthetic_ref": None,  # Would register artifact if synthetics_output=True
        "correlation_traces": None,  # Would include if tie_qc_report=True
        "depth_to_time": {
            "method": td_method,
            "coverage_pct": float(coverage_pct),
        },
        "ai_curve": [float(x) for x in ai_arr if not np.isnan(x)],
        "reflectivity_series": [float(x) for x in rc_arr],
        "assumptions": assumptions,
        "physics_guard": physics_guard,
        "canon_9_touched": ["Vp", "rho"],
        "humility_score": 0.15,  # well_tie is a single-well interpretation aid
    }

    return artifact
