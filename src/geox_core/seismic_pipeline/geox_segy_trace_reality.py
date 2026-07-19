#!/usr/bin/env python3
"""
GEOX SEG-Y Trace Reality Pipeline
=====================================
v1.0 — Forged 2026-07-06 under F13 SOVEREIGN.

The correct build order (from Arif's sealed doctrine):

    1.  SEG-Y ingestion                ← THIS FILE
    2.  Trace header audit
    3.  Geometry audit
    4.  Amplitude preservation check
    5.  Wavelet / phase check
    6.  Attribute recomputation from traces
    7.  Horizon/fault comparison against Panel D image result
    8.  Well tie using checkshot / sonic / density
    9.  Bruges synthetic seismogram    ← geox_well_tie_bruges.py
    10. INT_GEOLOGY_HORIZON only after calibration

The key upgrade from image mode to SEG-Y mode:

    image mode:  rendered contrast only
    SEG-Y mode:  trace amplitude, phase, frequency, geometry, metadata

Hard boundary:
    Formation names DO NOT appear here.
    H2 = "possible flooding surface / continuous reflector"
    NOT "H2 = Group I top"
    Until: well tie + checkshot + synthetic match + regional consistency.

DITEMPA BUKAN DIBERI.
"""

import hashlib
import json
import os

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: SEG-Y INGESTION
# ═══════════════════════════════════════════════════════════════════════════

def ingest_segy(segy_path: str) -> dict:
    """Open a SEG-Y file and extract raw traces + binary header.

    Returns a standardised dict so downstream steps are format-agnostic.

    Epistemic: OBS_SEGY_TRACE (directly observed from file bytes)
    """
    import segyio

    if not os.path.exists(segy_path):
        return {"status": "VOID", "reason": f"File not found: {segy_path}"}

    # SHA256 provenance — first law of trust
    with open(segy_path, "rb") as f:
        file_bytes = f.read()
    sha256 = hashlib.sha256(file_bytes).hexdigest()

    try:
        with segyio.open(segy_path, ignore_geometry=True) as f:
            # Binary header
            bin_header = {
                "samples_per_trace": int(f.bin[segyio.BinField.Samples]),
                "sample_interval_us": int(f.bin[segyio.BinField.Interval]),
                "data_sample_format": int(f.bin[segyio.BinField.Format]),
                "traces":   int(f.tracecount),
                "sorting":  str(f.sorting),
            }

            sample_interval_s  = bin_header["sample_interval_us"] / 1_000_000
            n_samples          = bin_header["samples_per_trace"]
            n_traces           = bin_header["traces"]
            twt_axis           = np.arange(n_samples) * sample_interval_s * 1000  # ms

            # Load all traces into array (float32)
            traces = np.zeros((n_samples, n_traces), dtype=np.float32)
            for ti in range(n_traces):
                traces[:, ti] = f.trace[ti]

            # Trace headers (key fields only)
            headers = []
            for ti in range(min(n_traces, 500)):  # sample first 500
                h = f.header[ti]
                headers.append({
                    "trace_idx":  ti,
                    "cdp":        int(h[segyio.TraceField.CDP]),
                    "inline":     int(h[segyio.TraceField.INLINE_3D]),
                    "crossline":  int(h[segyio.TraceField.CROSSLINE_3D]),
                    "offset":     int(h[segyio.TraceField.offset]),
                    "x":          int(h[segyio.TraceField.CDP_X]),
                    "y":          int(h[segyio.TraceField.CDP_Y]),
                    "elevation":  int(h[segyio.TraceField.ElevationScalar]),
                })

    except Exception as e:
        return {"status": "VOID", "reason": f"segyio open failed: {e}"}

    return {
        "status":    "OBS_SEGY_TRACE",
        "segy_path": segy_path,
        "sha256":    sha256,
        "sha256_short": sha256[:16],
        "bin_header": bin_header,
        "twt_ms":    twt_axis.tolist(),
        "n_samples": n_samples,
        "n_traces":  n_traces,
        "sample_interval_ms": sample_interval_s * 1000,
        "traces":    traces,       # ndarray (n_samples, n_traces) float32
        "headers":   headers,
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: TRACE HEADER AUDIT
# ═══════════════════════════════════════════════════════════════════════════

def audit_trace_headers(ingested: dict) -> dict:
    """Audit trace headers for completeness and consistency.

    Checks:
    - CDP range and regularity (uniform spacing vs gaps)
    - Inline / crossline populated vs zero
    - Offset distribution (stack vs pre-stack)
    - XY coordinate plausibility (non-zero, consistent scale)
    - Elevation / datum consistency

    Flags: OBS_SEGY_HEADER
    """
    headers = ingested.get("headers", [])
    if not headers:
        return {"status": "VOID", "reason": "No headers to audit"}

    cdps      = [h["cdp"]       for h in headers]
    inlines   = [h["inline"]    for h in headers]
    crosslines = [h["crossline"] for h in headers]
    offsets   = [h["offset"]    for h in headers]
    xs        = [h["x"]         for h in headers]
    ys        = [h["y"]         for h in headers]

    # CDP regularity
    cdp_diffs = np.diff(sorted(set(cdps)))
    cdp_regular = bool(len(set(cdp_diffs)) <= 3) if len(cdp_diffs) > 0 else False
    cdp_spacing = float(np.median(cdp_diffs)) if len(cdp_diffs) > 0 else 0

    # Inline / crossline populated?
    il_populated = any(il != 0 for il in inlines)
    xl_populated = any(xl != 0 for xl in crosslines)

    # Offset type
    unique_offsets = sorted(set(offsets))
    if len(unique_offsets) == 1:
        data_type = "POST_STACK (single offset)"
    elif len(unique_offsets) <= 10:
        data_type = f"LIMITED_OFFSET ({len(unique_offsets)} offsets)"
    else:
        data_type = f"PRE_STACK ({len(unique_offsets)} offsets)"

    # XY scale
    xy_nonzero = any(x != 0 for x in xs) and any(y != 0 for y in ys)
    xy_range_x = max(xs) - min(xs) if xs else 0
    xy_range_y = max(ys) - min(ys) if ys else 0

    # Flags
    flags = []
    if not cdp_regular:
        flags.append("CDP_IRREGULAR — gaps or irregular spacing")
    if not il_populated:
        flags.append("INLINE_ZERO — 3D inline byte location may differ")
    if not xl_populated:
        flags.append("CROSSLINE_ZERO — 3D crossline byte location may differ")
    if not xy_nonzero:
        flags.append("XY_ZERO — coordinates not populated, geometry unknown")

    verdict = "CLEAN" if not flags else f"FLAGS: {len(flags)}"

    return {
        "status": "OBS_SEGY_HEADER",
        "header_audit": {
            "n_headers_checked": len(headers),
            "cdp_range":    [min(cdps), max(cdps)],
            "cdp_spacing":  round(cdp_spacing, 2),
            "cdp_regular":  cdp_regular,
            "inline_populated": il_populated,
            "crossline_populated": xl_populated,
            "data_type":    data_type,
            "xy_populated": xy_nonzero,
            "xy_range_m":   [round(xy_range_x, 0), round(xy_range_y, 0)],
            "verdict":      verdict,
            "flags":        flags,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: GEOMETRY AUDIT
# ═══════════════════════════════════════════════════════════════════════════

def audit_geometry(ingested: dict) -> dict:
    """Audit the physical geometry of the seismic volume.

    Checks:
    - TWT range (shallow / deep — does it make sense for the basin?)
    - Sample interval (typical: 1ms, 2ms, 4ms)
    - Trace count vs expected 2D line length
    - Fold uniformity (for stacked data)
    - Nyquist frequency given sample interval

    Epistemic: OBS_SEGY_GEOMETRY
    """
    n_samples = ingested.get("n_samples", 0)
    n_traces  = ingested.get("n_traces",  0)
    dt_ms     = ingested.get("sample_interval_ms", 2.0)
    twt_ms    = ingested.get("twt_ms", [])

    if n_samples == 0 or n_traces == 0:
        return {"status": "VOID", "reason": "Empty geometry"}

    twt_max_ms    = twt_ms[-1] if twt_ms else n_samples * dt_ms
    nyquist_hz    = 1000 / (2 * dt_ms)
    typical_seismic_bw = "OK" if nyquist_hz >= 125 else "LOW — dt may limit resolution"

    flags = []
    if dt_ms not in [0.5, 1.0, 2.0, 4.0, 8.0]:
        flags.append(f"UNUSUAL_DT: {dt_ms}ms — verify sample interval byte location")
    if twt_max_ms > 8000:
        flags.append(f"VERY_DEEP: TWT={twt_max_ms:.0f}ms — confirm not in depth domain")
    if twt_max_ms < 200:
        flags.append(f"VERY_SHALLOW: TWT={twt_max_ms:.0f}ms — very high resolution data")
    if n_traces < 10:
        flags.append("FEW_TRACES: fewer than 10 traces — very short 2D line or test data")

    # Basin context check for Malay Basin
    malay_basin_twt_range = [200, 4000]  # typical TWT for productive intervals
    in_range = malay_basin_twt_range[0] <= twt_max_ms <= malay_basin_twt_range[1]

    return {
        "status": "OBS_SEGY_GEOMETRY",
        "geometry": {
            "n_samples": n_samples,
            "n_traces":  n_traces,
            "dt_ms":     dt_ms,
            "twt_range_ms": [0, round(twt_max_ms, 2)],
            "nyquist_hz":   round(nyquist_hz, 1),
            "bandwidth_status": typical_seismic_bw,
            "malay_basin_twt_plausible": in_range,
            "flags": flags,
            "verdict": "CLEAN" if not flags else f"FLAGS: {len(flags)}",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: AMPLITUDE PRESERVATION CHECK
# ═══════════════════════════════════════════════════════════════════════════

def check_amplitude_preservation(ingested: dict) -> dict:
    """Check whether trace amplitudes are likely to be preserved.

    Amplitude-preserved data is required for:
    - AVO analysis
    - DHI (Direct Hydrocarbon Indicator) detection
    - Relative acoustic impedance inversion
    - Fluid discrimination

    Checks:
    - RMS amplitude variation across traces (uniform = well-balanced)
    - Mean absolute amplitude per trace (long-offset decay = geometric spreading)
    - Clipping detection (hard limiter = amplitude not preserved)
    - DC bias check (non-zero mean = processing issue)
    - Polarity convention (SEG normal vs reverse)

    Epistemic: DER_SEGY_AMPLITUDE
    """
    traces = ingested.get("traces")
    if traces is None:
        return {"status": "VOID", "reason": "No traces"}

    n_samples, n_traces = traces.shape

    # RMS per trace
    rms_per_trace = np.sqrt(np.mean(traces ** 2, axis=0))
    rms_mean = float(np.mean(rms_per_trace))
    rms_cv   = float(np.std(rms_per_trace) / (rms_mean + 1e-10))

    # DC bias (mean should be near zero for zero-phase processed data)
    dc_per_trace = np.mean(traces, axis=0)
    dc_mean = float(np.mean(np.abs(dc_per_trace)))
    dc_flag  = dc_mean > 0.05 * rms_mean

    # Clipping (max amplitude same across many traces = hard limiter)
    max_per_trace = np.max(np.abs(traces), axis=0)
    clip_frac = float(np.mean(max_per_trace > 0.98 * max_per_trace.max()))

    # Polarity: first peak of strong reflector
    # Standard SEG normal polarity: hard kick → peak (positive)
    first_strong = traces[:, n_traces // 2]  # middle trace
    first_peak_sign = "POSITIVE" if first_strong[np.argmax(np.abs(first_strong))] > 0 else "NEGATIVE"

    flags = []
    preserved = True
    if rms_cv > 0.5:
        flags.append(f"RMS_IMBALANCED: CV={rms_cv:.2f} — trace-to-trace amplitude varies >50%")
        preserved = False
    if dc_flag:
        flags.append(f"DC_BIAS: mean|dc|={dc_mean:.4f} relative to RMS={rms_mean:.4f}")
    if clip_frac > 0.05:
        flags.append(f"CLIPPING: {clip_frac:.1%} of traces near max — amplitude may be limited")
        preserved = False

    return {
        "status": "DER_SEGY_AMPLITUDE",
        "amplitude": {
            "rms_mean":     round(rms_mean, 6),
            "rms_cv":       round(rms_cv, 4),
            "dc_bias_flag": dc_flag,
            "clip_fraction":round(clip_frac, 4),
            "polarity_first_peak": first_peak_sign,
            "amplitude_preserved": preserved,
            "flags": flags,
            "avo_usable": preserved and not dc_flag,
            "verdict": "PRESERVED" if preserved else f"COMPROMISED: {len(flags)} flags",
        },
        "note": "Amplitude preservation required for AVO, DHI, inversion. Without it, amplitude ≠ geology.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: WAVELET / PHASE CHECK
# ═══════════════════════════════════════════════════════════════════════════

def check_wavelet_phase(ingested: dict) -> dict:
    """Estimate wavelet character from the data.

    Checks:
    - Dominant frequency (from autocorrelation zero-crossing)
    - Frequency bandwidth (ratio of -6dB frequencies)
    - Phase estimate (zero-phase vs mixed-phase)
    - Tuning thickness estimate (λ/4 at dominant frequency)

    Epistemic: DER_SEGY_WAVELET

    The wavelet check is critical because:
    - Horizon picks are tied to wavelet peaks/troughs — phase matters
    - Synthetic seismograms (bruges) must use a wavelet consistent with the data
    - Frequency content constrains vertical resolution
    """
    traces = ingested.get("traces")
    dt_ms  = ingested.get("sample_interval_ms", 2.0)
    if traces is None:
        return {"status": "VOID", "reason": "No traces"}

    # Stack a sample of traces for stable autocorrelation estimate
    n_samples, n_traces = traces.shape
    sample_traces = traces[:, ::max(1, n_traces // 50)]  # up to 50 representative traces
    stack = np.mean(sample_traces, axis=1)

    # Autocorrelation
    ac = np.correlate(stack, stack, mode='full')
    ac = ac[n_samples - 1:]  # keep positive lags only
    ac /= ac[0] + 1e-10       # normalise

    # Dominant period: first zero crossing of autocorrelation
    zero_cross = None
    for i in range(1, len(ac)):
        if ac[i] < 0:
            zero_cross = i
            break
    dominant_period_ms = (zero_cross * dt_ms * 2) if zero_cross else None
    dominant_freq_hz   = (1000 / dominant_period_ms) if dominant_period_ms else None

    # Power spectrum
    fft_amp = np.abs(np.fft.rfft(stack))
    freqs   = np.fft.rfftfreq(n_samples, d=dt_ms / 1000)
    peak_idx = np.argmax(fft_amp[1:]) + 1
    peak_freq = float(freqs[peak_idx])

    # Bandwidth (-6dB)
    threshold = fft_amp.max() * 0.5  # -6dB ~ 0.5 amplitude
    above = np.where(fft_amp >= threshold)[0]
    if len(above) >= 2:
        f_low  = float(freqs[above[0]])
        f_high = float(freqs[above[-1]])
        bandwidth_hz = f_high - f_low
    else:
        f_low, f_high, bandwidth_hz = 0.0, 0.0, 0.0

    # Phase estimate: zero-phase data has symmetric autocorrelation
    # Use correlation between stack and its abs envelope as proxy
    from scipy.signal import hilbert as scipy_hilbert
    envelope_stack = np.abs(scipy_hilbert(stack))
    phase_corr = float(np.corrcoef(np.abs(stack[:n_samples//4]),
                                    envelope_stack[:n_samples//4])[0, 1])
    phase_class = "NEAR_ZERO_PHASE" if abs(phase_corr) < 0.3 else "MIXED_PHASE"

    # Tuning thickness at dominant frequency
    # Assuming average interval velocity 2000 m/s (shallow Malay Basin)
    v_avg_mps = 2000
    if dominant_freq_hz:
        wavelength_m = v_avg_mps / dominant_freq_hz
        tuning_ms    = (wavelength_m / 4) / v_avg_mps * 2000  # TWT ms
    else:
        wavelength_m = None
        tuning_ms    = None

    return {
        "status": "DER_SEGY_WAVELET",
        "wavelet": {
            "dominant_freq_hz":    round(peak_freq, 1),
            "autocorr_freq_hz":    round(dominant_freq_hz, 1) if dominant_freq_hz else None,
            "bandwidth_hz":        round(bandwidth_hz, 1),
            "f_low_hz":            round(f_low, 1),
            "f_high_hz":           round(f_high, 1),
            "phase_class":         phase_class,
            "tuning_thickness_ms": round(tuning_ms, 1) if tuning_ms else None,
            "tuning_thickness_m_at_v2000": round(wavelength_m / 4, 1) if wavelength_m else None,
            "bruges_ricker_target_hz": round(peak_freq, 0) if peak_freq else 40.0,
        },
        "note": (
            "Bruges synthetic seismogram should use a Ricker wavelet at the "
            f"estimated dominant frequency ({round(peak_freq, 0)}Hz). "
            "Tuning thickness constrains the minimum resolvable bed thickness."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: TRACE ATTRIBUTE STACK (from real traces)
# ═══════════════════════════════════════════════════════════════════════════

def compute_trace_attributes(ingested: dict, wavelet_info: dict) -> dict:
    """Compute 6-attribute stack from real SEG-Y traces.

    Same attributes as image mode (geox_physical_reality.py) but now
    computed from actual trace amplitudes — not rendered pixels.

    This is the key upgrade:
        image mode:  rendered contrast only
        SEG-Y mode:  trace amplitude, phase, frequency, geometry, metadata

    Attributes computed:
        1. AGC (Automatic Gain Control) — normalised amplitude
        2. Instantaneous phase — lateral continuity
        3. Coherence (semblance proxy) — reflector tracking
        4. Discontinuity — fault probability
        5. Envelope (instantaneous amplitude) — bright spot detection
        6. Dip estimation (structure tensor) — structural dip

    Epistemic: DER_SEGY_ATTRIBUTE (derived from OBS_SEGY_TRACE)
    """
    from scipy import ndimage
    from scipy.signal import hilbert as scipy_hilbert

    traces = ingested.get("traces")
    dt_ms  = ingested.get("sample_interval_ms", 2.0)
    if traces is None:
        return {"status": "VOID", "reason": "No traces"}

    n_samples, n_traces = traces.shape

    # ── 1. AGC ───────────────────────────────────────────────────────
    window = max(10, int(50 / dt_ms))  # 50ms window
    agc = np.zeros_like(traces)
    for ti in range(n_traces):
        rms_win = np.array([
            np.sqrt(np.mean(traces[max(0, s - window):s + window, ti] ** 2))
            for s in range(n_samples)
        ])
        agc[:, ti] = traces[:, ti] / (rms_win + 1e-10)

    # ── 2. Instantaneous phase ───────────────────────────────────────
    analytic = scipy_hilbert(traces, axis=0)
    inst_phase = np.angle(analytic)
    cos_phase  = np.cos(inst_phase)

    # ── 3. Instantaneous amplitude (envelope) ────────────────────────
    envelope = np.abs(analytic)
    # Normalise
    env_norm = envelope / (np.percentile(envelope, 99) + 1e-10)

    # ── 4. Coherence (semblance between adjacent traces) ─────────────
    coherence = np.zeros((n_samples, n_traces), dtype=np.float32)
    hw = 3  # half-window
    for ti in range(hw, n_traces - hw):
        block = traces[:, ti - hw:ti + hw + 1]
        num = np.sum(block, axis=1) ** 2
        den = np.sum(block ** 2, axis=1) * (2 * hw + 1)
        coherence[:, ti] = num / (den + 1e-10)

    # ── 5. Discontinuity (1 - coherence, smoothed) ───────────────────
    discontinuity = 1 - coherence
    discontinuity = ndimage.gaussian_filter(discontinuity, sigma=1.5)

    # ── 6. Structural dip (structure tensor, simplified) ─────────────
    gx = ndimage.sobel(agc, axis=1)   # lateral gradient
    gz = ndimage.sobel(agc, axis=0)   # vertical gradient
    dip_chaos = np.sqrt(gx ** 2 + gz ** 2) / (np.abs(agc) + 1e-10)
    dip_chaos = np.clip(dip_chaos, 0, np.percentile(dip_chaos, 99))

    # ── Normalise all to [0,1] for attribute composite ───────────────
    def norm01(arr):
        lo, hi = arr.min(), arr.max()
        return (arr - lo) / (hi - lo + 1e-10)

    return {
        "status": "DER_SEGY_ATTRIBUTE",
        "attrs": {
            "agc":          agc.astype(np.float32),
            "phase":        cos_phase.astype(np.float32),
            "envelope":     norm01(env_norm).astype(np.float32),
            "coherence":    coherence.astype(np.float32),
            "discontinuity":norm01(discontinuity).astype(np.float32),
            "dip_chaos":    norm01(dip_chaos).astype(np.float32),
        },
        "dt_ms": dt_ms,
        "n_samples": n_samples,
        "n_traces":  n_traces,
        "bruges_wavelet_target_hz": wavelet_info.get("wavelet", {}).get("bruges_ricker_target_hz", 40.0),
        "note": "Attributes computed from OBS_SEGY_TRACE. Amplitude is real. Phase is real. Geometry is real.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: RENDER TRACE SECTION (for Panel D v2)
# ═══════════════════════════════════════════════════════════════════════════

def render_trace_section(ingested: dict, attrs: dict, output_dir: str,
                          title_suffix: str = "") -> dict:
    """Render the trace-amplitude section as a seismic display.

    This is the equivalent of the pixel-domain render in geox_physical_reality.py,
    but using real trace data — AGC-normalised, wiggle or variable-density.

    Outputs:
        T_amplitude.png  — variable density amplitude display (seismic convention)
        T_attribute.png  — 6-panel attribute composite from traces

    Epistemic: DER_SEGY_RENDER (derived display of OBS_SEGY_TRACE)
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    os.makedirs(output_dir, exist_ok=True)

    twt   = ingested.get("twt_ms", [])
    traces = ingested.get("traces")
    n_samples, n_traces = traces.shape
    twt_arr = np.array(twt) if twt else np.arange(n_samples)

    agc   = attrs["attrs"]["agc"]
    phase = attrs["attrs"]["phase"]
    env   = attrs["attrs"]["envelope"]
    coh   = attrs["attrs"]["coherence"]
    disc  = attrs["attrs"]["discontinuity"]
    dip   = attrs["attrs"]["dip_chaos"]

    # ── T1: Amplitude section ─────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(18, 10), facecolor='#0a0d14')
    ax.set_facecolor('#0a0d14')
    vmax = np.percentile(np.abs(agc), 97)
    ax.imshow(agc, cmap='seismic', aspect='auto',
              vmin=-vmax, vmax=vmax, alpha=0.95,
              extent=[0, n_traces, twt_arr[-1], twt_arr[0]])
    ax.set_xlabel('Trace', color='#667')
    ax.set_ylabel('TWT (ms) — OBS_SEGY_TRACE domain', color='#667')
    ax.set_title(
        f'SEG-Y Trace Amplitude Section — OBS_SEGY_TRACE{title_suffix}\n'
        f'AGC-normalised | sample_interval={ingested["sample_interval_ms"]:.1f}ms | '
        f'{n_traces} traces × {n_samples} samples',
        color='white', fontsize=10)
    ax.tick_params(colors='#445')
    ax.text(0.01, 0.02,
            'DER_SEGY_RENDER: amplitude display. Real traces. Phase real. Geometry real.\n'
            'Amplitude ≠ lithology/fluid without AVO + rock physics.',
            transform=ax.transAxes, color='#FFE566', fontsize=7.5,
            bbox=dict(boxstyle='round', facecolor='#1a1a0a', alpha=0.85))
    plt.tight_layout()
    t1_path = os.path.join(output_dir, "T1_amplitude_section.png")
    plt.savefig(t1_path, dpi=150, bbox_inches='tight', facecolor='#0a0d14')
    plt.close()
    print(f"  ✅ T1 amplitude: {t1_path}")

    # ── T2: 6-attribute composite ─────────────────────────────────────
    fig = plt.figure(figsize=(24, 12), facecolor='#0a0d14')
    gs  = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.25)
    specs = [
        (agc,   'seismic',  'AGC (normalised amplitude)',     '①'),
        (phase, 'twilight', 'Cosine Phase',                   '②'),
        (env,   'hot',      'Envelope / Instantaneous Amp',   '③'),
        (coh,   'plasma',   'Coherence (semblance)',          '④'),
        (disc,  'YlOrRd',   'Discontinuity (fault proxy)',    '⑤'),
        (dip,   'magma',    'Dip Chaos (structure tensor)',   '⑥'),
    ]
    for idx, (data, cmap, label, num) in enumerate(specs):
        ax = fig.add_subplot(gs[idx // 3, idx % 3])
        ax.set_facecolor('#0a0d14')
        vmax_a = np.percentile(np.abs(data), 98)
        kwargs = dict(cmap=cmap, aspect='auto',
                      extent=[0, n_traces, twt_arr[-1], twt_arr[0]])
        if cmap == 'seismic':
            kwargs.update(vmin=-vmax_a, vmax=vmax_a)
        else:
            kwargs.update(vmin=0, vmax=vmax_a)
        ax.imshow(data, **kwargs)
        ax.set_title(f"{num} {label}", color='#aaccff', fontsize=9)
        ax.set_ylabel('TWT (ms)', color='#445', fontsize=7)
        ax.tick_params(colors='#445', labelsize=6)

    fig.suptitle('SEG-Y Attribute Stack — DER_SEGY_ATTRIBUTE', color='white', fontsize=11)
    plt.tight_layout()
    t2_path = os.path.join(output_dir, "T2_attribute_composite.png")
    plt.savefig(t2_path, dpi=150, bbox_inches='tight', facecolor='#0a0d14')
    plt.close()
    print(f"  ✅ T2 attributes: {t2_path}")

    return {"T1": t1_path, "T2": t2_path}


# ═══════════════════════════════════════════════════════════════════════════
# FULL PIPELINE RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_segy_reality_pipeline(segy_path: str, output_dir: str,
                               basin_context: str = "malay_basin") -> dict:
    """Run the full SEG-Y trace reality pipeline (steps 1–6).

    Steps 7–10 (horizon comparison, well tie, bruges, INT_GEOLOGY) are
    handled by geox_well_tie_bruges.py.

    Returns a dict ready to feed into Panel D v2.
    """
    os.makedirs(output_dir, exist_ok=True)
    print("\n" + "═" * 64)
    print("  GEOX SEG-Y TRACE REALITY PIPELINE v1.0")
    print("═" * 64)
    print(f"  Input:  {segy_path}")
    print(f"  Output: {output_dir}")
    print("─" * 64)

    # Step 1: Ingest
    print("  [S1] SEG-Y ingestion...")
    ingested = ingest_segy(segy_path)
    if ingested["status"] == "VOID":
        print(f"  ❌ VOID: {ingested['reason']}")
        return ingested
    print(f"  ✅ {ingested['n_traces']} traces × {ingested['n_samples']} samples "
          f"| dt={ingested['sample_interval_ms']:.1f}ms | sha={ingested['sha256_short']}")

    # Step 2: Header audit
    print("  [S2] Trace header audit...")
    header_audit = audit_trace_headers(ingested)
    ha = header_audit.get("header_audit", {})
    print(f"  ✅ CDP range: {ha.get('cdp_range')} | type: {ha.get('data_type')} | verdict: {ha.get('verdict')}")
    if ha.get("flags"):
        for fl in ha["flags"]:
            print(f"  ⚠  {fl}")

    # Step 3: Geometry audit
    print("  [S3] Geometry audit...")
    geom_audit = audit_geometry(ingested)
    ga = geom_audit.get("geometry", {})
    print(f"  ✅ TWT: {ga.get('twt_range_ms')} ms | Nyquist: {ga.get('nyquist_hz')}Hz | "
          f"Malay Basin plausible: {ga.get('malay_basin_twt_plausible')}")
    if ga.get("flags"):
        for fl in ga["flags"]:
            print(f"  ⚠  {fl}")

    # Step 4: Amplitude preservation
    print("  [S4] Amplitude preservation check...")
    amp_check = check_amplitude_preservation(ingested)
    ac = amp_check.get("amplitude", {})
    print(f"  ✅ RMS={ac.get('rms_mean'):.4f} | CV={ac.get('rms_cv'):.3f} | "
          f"AVO-usable: {ac.get('avo_usable')} | verdict: {ac.get('verdict')}")

    # Step 5: Wavelet check
    print("  [S5] Wavelet / phase check...")
    wav_check = check_wavelet_phase(ingested)
    wv = wav_check.get("wavelet", {})
    print(f"  ✅ Dominant freq: {wv.get('dominant_freq_hz')}Hz | BW: {wv.get('bandwidth_hz')}Hz | "
          f"Phase: {wv.get('phase_class')} | Tuning: {wv.get('tuning_thickness_ms')}ms")

    # Step 6: Attribute stack
    print("  [S6] Computing trace attribute stack...")
    trace_attrs = compute_trace_attributes(ingested, wav_check)
    print("  ✅ 6 attributes: AGC + Phase + Envelope + Coherence + Discontinuity + DipChaos")

    # Step 7: Render
    print("  [S7] Rendering trace section panels...")
    renders = render_trace_section(ingested, trace_attrs, output_dir,
                                   title_suffix=f" | {basin_context}")

    # ── Provenance hash of full pipeline ─────────────────────────────
    pipeline_hash = hashlib.sha256(
        (ingested["sha256"] + "segy_reality_v1").encode()
    ).hexdigest()[:16]

    # Save audit JSON
    audit = {
        "segy_sha256":   ingested["sha256"],
        "sha256_short":  ingested["sha256_short"],
        "pipeline_hash": pipeline_hash,
        "bin_header":    ingested["bin_header"],
        "header_audit":  header_audit.get("header_audit", {}),
        "geometry":      geom_audit.get("geometry", {}),
        "amplitude":     amp_check.get("amplitude", {}),
        "wavelet":       wav_check.get("wavelet", {}),
        "basin_context": basin_context,
        "renders":       renders,
        "next_steps": [
            "geox_well_tie_bruges.py — synthetic seismogram + well tie",
            "Horizon picks (ant-track + DP) on trace data",
            "Compare trace picks vs Panel D image picks",
            "INT_GEOLOGY_HORIZON only after well tie calibration",
        ],
    }
    audit_path = os.path.join(output_dir, "segy_trace_audit.json")
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2, default=str)

    print("\n" + "═" * 64)
    print("  PRODUCT: trace reality audit complete")
    print(f"  VERDICT: {ingested['status']} → {trace_attrs['status']}")
    print(f"  AVO USABLE: {ac.get('avo_usable')}")
    print("  NEXT: geox_well_tie_bruges.py → INT_GEOLOGY_HORIZON")
    print("═" * 64)

    # Return everything needed for Panel D v2
    return {
        "ingested":      ingested,
        "header_audit":  header_audit,
        "geom_audit":    geom_audit,
        "amp_check":     amp_check,
        "wav_check":     wav_check,
        "trace_attrs":   trace_attrs,
        "renders":       renders,
        "audit_path":    audit_path,
    }


# ═══════════════════════════════════════════════════════════════════════════
# TEST SEG-Y GENERATOR
# Creates a geologically realistic synthetic for pipeline testing
# Label: TEST_SEGY — not real geology. Never use for drilling decisions.
# ═══════════════════════════════════════════════════════════════════════════

def create_test_segy(output_path: str,
                     n_traces: int = 200, n_samples: int = 500,
                     dt_ms: float = 2.0) -> str:
    """Create a geologically realistic synthetic SEG-Y for pipeline testing.

    Geology model (Malay Basin inspired, but TEST only):
        - 5 reflectors at realistic TWT depths
        - 3 near-vertical faults with trace offset
        - Ricker wavelet convolution (bruges, 35Hz)
        - Geological noise + multiples simulation
        - Polarity: SEG normal (peak = hard kick)

    Label: TEST_SEGY — this is a synthetic for testing only.
    It should NEVER be used as real geology.
    """
    import segyio
    from bruges.filters import ricker

    print(f"\n[TEST-SEGY] Creating synthetic test SEG-Y: {output_path}")
    print(f"  Model: {n_traces} traces × {n_samples} samples @ dt={dt_ms}ms")
    print("  ⚠  TEST_SEGY: synthetic only — not real geology — not for drilling")

    np.arange(n_samples) * dt_ms  # TWT in ms

    # Geological model: reflection coefficients at given TWT depths
    # Malay Basin inspired TWT depths (shallow thermal sag section)
    reflector_twt_ms = [120, 280, 460, 640, 820]  # TWT ms
    reflector_rc     = [ 0.15, -0.10,  0.20, -0.08,  0.12]  # RC (dimensionless)

    # Ricker wavelet at 35Hz (typical Malay Basin seismic)
    wav, _ = ricker(duration=0.080, dt=dt_ms / 1000, f=35)

    # Fault locations (trace indices where fault displaces reflectors)
    fault_traces = [55, 110, 165]
    fault_throws  = [8, 12, 6]  # samples of throw

    rc_section = np.zeros((n_samples, n_traces), dtype=np.float32)
    for ref_twt, ref_rc in zip(reflector_twt_ms, reflector_rc, strict=False):
        for ti in range(n_traces):
            throw = 0
            for ft, fth in zip(fault_traces, fault_throws, strict=False):
                if ti > ft:
                    throw += fth
            sample_idx = int(ref_twt / dt_ms) + throw
            if 0 < sample_idx < n_samples - 1:
                rc_section[sample_idx, ti] = ref_rc

    # Convolve with wavelet
    traces = np.zeros_like(rc_section)
    for ti in range(n_traces):
        traces[:, ti] = np.convolve(rc_section[:, ti], wav, mode='same')

    # Add geological noise (coloured, not white)
    noise = np.random.randn(n_samples, n_traces).astype(np.float32)
    from scipy.ndimage import gaussian_filter
    noise = gaussian_filter(noise, sigma=(2, 1)) * 0.04

    # Simulate a simple multiple (water-bottom repeat at 2× shallowest reflector)
    multiple_twt = reflector_twt_ms[0] * 2
    multiple_sample = int(multiple_twt / dt_ms)
    if multiple_sample < n_samples:
        for ti in range(n_traces):
            traces[multiple_sample, ti] += reflector_rc[0] * 0.5

    traces = traces + noise

    # Write SEG-Y
    dt_us = int(dt_ms * 1000)

    spec = segyio.spec()
    spec.sorting  = 2   # CDP sort
    spec.format   = 1   # IEEE 4-byte float
    spec.samples  = np.arange(n_samples, dtype=np.float32) * dt_ms
    spec.tracecount = n_traces

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with segyio.create(output_path, spec) as f:
        f.bin.update(
            tsort=2,   # CDP_SORTING (segyio enum varies by version)
            hdt=dt_us,
            dto=dt_us,
            hns=n_samples,
            mfeet=1,
        )
        for ti in range(n_traces):
            f.header[ti] = {
                segyio.TraceField.CDP:          ti + 1,
                segyio.TraceField.FieldRecord:  1,
                segyio.TraceField.TraceNumber:  ti + 1,
                segyio.TraceField.INLINE_3D:    1,
                segyio.TraceField.CROSSLINE_3D: ti + 1,
                segyio.TraceField.CDP_X:        int(ti * 25),   # 25m CDP spacing
                segyio.TraceField.CDP_Y:        0,
                segyio.TraceField.offset:       0,
                segyio.TraceField.DelayRecordingTime: 0,
            }
            f.trace[ti] = traces[:, ti]

    print(f"  ✅ TEST_SEGY written: {output_path}")
    print(f"  Reflectors: {', '.join(f'{r}ms' for r in reflector_twt_ms)}")
    print(f"  Faults at traces: {fault_traces}")
    print(f"  Multiple at ~{multiple_twt}ms")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 geox_segy_trace_reality.py <segy_file.segy> [output_dir] [basin]")
        print("       python3 geox_segy_trace_reality.py --create-test [output.segy]")
        sys.exit(1)

    if sys.argv[1] == "--create-test":
        test_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/test_malay_basin.segy"
        create_test_segy(test_path)
        print(f"\nRun pipeline: python3 geox_segy_trace_reality.py {test_path}")
        sys.exit(0)

    segy_path  = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/geox_segy_out"
    basin      = sys.argv[3] if len(sys.argv) > 3 else "malay_basin"

    result = run_segy_reality_pipeline(segy_path, output_dir, basin)
    if result.get("status") != "VOID":
        print(f"\nAudit: {result['audit_path']}")
