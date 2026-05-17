"""
GEOX 2D — Seismic Cross-Section Generator & Interpreter
Convolutional seismogram modelling, horizon picking, fault interpretation,
amplitude analysis, and time-depth conversion.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class HorizonPick:
    name: str
    time_ms: float
    x_positions: List[float]
    amplitudes: List[float]
    phase: str       # "positive" or "negative"
    continuity: float  # 0-1 confidence
    fault_positions: List[float]
    arifos_grade: str  # "AAA" / "TRUST-GRADED" / "RAW"


@dataclass
class SeismicSection:
    data: np.ndarray        # (n_samples, n_traces)
    x_coords: np.ndarray
    t_coords: np.ndarray    # time in ms
    horizons: List[HorizonPick]
    faults: List[Dict]      # fault interpretation
    metadata: Dict


def build_wavelet(frequency: float, dt_ms: float, wavelet_type: str = "ricker") -> np.ndarray:
    """Build seismic wavelet for convolution modelling."""
    n_wl = int(200 / dt_ms)
    if n_wl % 2 == 0:
        n_wl += 1
    t_wl = (np.arange(n_wl) - n_wl // 2) * dt_ms

    if wavelet_type == "ricker":
        f0 = frequency
        w = (1 - (np.pi * f0 * t_wl / 1000) ** 2) * np.exp(-(np.pi * f0 * t_wl / 1000) ** 2)
    elif wavelet_type == "ormsby":
        f1, f2, f3, f4 = frequency * 0.5, frequency * 0.8, frequency * 1.2, frequency * 2.0
        w = np.zeros_like(t_wl)
        for fn, fn1 in [(f4, f3), (f2, f1)]:
            w += (np.sin(2*np.pi*fn1*t_wl/1000) - np.sin(2*np.pi*fn*t_wl/1000)) / (np.pi*t_wl/1000 + 1e-6)
    elif wavelet_type == "klauder":
        t_k = t_wl / 1000
        duration = abs(t_k[-1] - t_k[0])
        k = frequency * 0.2
        f1 = frequency - k/2; f2 = frequency + k/2
        w = np.sin(np.pi * k * t_k) / (np.pi * k * t_k + 1e-9) * np.cos(2*np.pi*frequency*t_k)
    else:
        w = np.zeros(n_wl); w[n_wl//2] = 1

    w = w / (np.max(np.abs(w)) + 1e-9)
    return w


def apply_nmo_velocity(seis_data: np.ndarray, t_coords: np.ndarray, 
                        x_coords: np.ndarray, velocities: np.ndarray) -> np.ndarray:
    """
    Apply Normal Moveout correction for CDP gather.
    t_nmo = sqrt(t0^2 + x^2 / v_rms^2)
    """
    n_samples, n_traces = seis_data.shape
    corrected = np.zeros_like(seis_data)
    
    for ix, xpos in enumerate(x_coords):
        for it, t0 in enumerate(t_coords):
            v_rms = velocities[min(it, len(velocities)-1)]
            t_nmo_sq = t0**2 + (xpos**2) / (max(v_rms**2, 1))
            t_nmo = np.sqrt(t_nmo_sq)
            # Interpolate from original data
            t_idx = np.interp(t_nmo, t_coords, np.arange(len(t_coords)))
            if 0 <= t_idx < n_samples:
                corrected[it, ix] = np.interp(t_idx, np.arange(n_samples), seis_data[:, ix])
            else:
                corrected[it, ix] = 0
    return corrected


def generate_synthetic_seismogram(
    curves: Dict[str, np.ndarray],
    vp_col: str = "DT",
    rho_col: str = "RHOB",
    wavelet_freq: float = 35.0,
    wavelet_type: str = "ricker",
    noise_db: float = -18,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic seismogram from well logs.
    Method: Zoeppritz reflectivity → Ricker wavelet convolution.
    Input: well curves (must have MD, DT or VP, RHOB)
    Output: synthetic trace array (time domain)
    """
    md = curves.get("MD", np.array([0]))
    dt = curves.get(vp_col, curves.get("DT", np.full_like(md, 200)))
    rhob = curves.get(rho_col, curves.get("RHOB", np.full_like(md, 2.35)))

    # Convert DT to VP (if DT used)
    if vp_col == "DT":
        vp = 1e6 / np.clip(dt, 40, 300)
    else:
        vp = curves.get("VP", np.full_like(md, 3000))
    rho = rhob

    # Time-depth relationship (average velocity)
    t_ms = np.zeros_like(md)
    dt_avg = np.mean(np.diff(md) / (np.diff(t_ms/1000 + 1)) if np.any(t_ms > 0) else [1])
    for i in range(1, len(md)):
        t_ms[i] = t_ms[i-1] + 2 * (md[i] - md[i-1]) / vp[i] * 1000

    # Reflection coefficients
    rc = np.zeros(len(vp))
    for i in range(1, len(vp)):
        dv = rho[i] * vp[i] - rho[i-1] * vp[i-1]
        z_sum = rho[i] * vp[i] + rho[i-1] * vp[i-1]
        rc[i] = dv / (z_sum + 1e-9)

    # Build wavelet
    dt_sampling = t_ms[1] - t_ms[0] if len(t_ms) > 1 else 1.0
    wavelet = build_wavelet(wavelet_freq, max(dt_sampling, 0.5), wavelet_type)

    # Convolve
    synthetic = np.convolve(wavelet, rc, mode='same')

    # Add noise
    if noise_db < 0:
        noise_amp = 10 ** (noise_db / 20)
        noise = np.random.default_rng(42).normal(0, noise_amp, len(synthetic))
        synthetic += noise

    return synthetic, t_ms


def interpret_horizons(seis_data: np.ndarray, t_coords: np.ndarray,
                        x_coords: np.ndarray, 
                        horizon_times: List[float],
                        layer_names: List[str]) -> List[HorizonPick]:
    """
    Auto-pick horizons from seismic data at specified time values.
    Computes amplitude characteristics and phase.
    """
    picks = []
    for i, (t_h, name) in enumerate(zip(horizon_times, layer_names)):
        t_idx = int(np.interp(t_h, t_coords, np.arange(len(t_coords))))
        t_idx = np.clip(t_idx, 0, seis_data.shape[0] - 1)

        amplitudes = seis_data[t_idx, :]
        avg_amp = float(np.mean(amplitudes))
        phase = "positive" if avg_amp > 0 else "negative"

        # Continuity check (how many traces have similar amplitude sign)
        same_sign = np.sum(np.sign(amplitudes) == np.sign(avg_amp))
        continuity = same_sign / len(amplitudes)

        # Fault detection: look for lateral discontinuities
        trace_diffs = np.abs(np.diff(amplitudes))
        fault_indices = np.where(trace_diffs > 2 * np.std(trace_diffs))[0]
        fault_x = [float(x_coords[fi]) for fi in fault_indices[:5]]

        pick = HorizonPick(
            name=name,
            time_ms=t_h,
            x_positions=x_coords.tolist(),
            amplitudes=amplitudes.tolist(),
            phase=phase,
            continuity=continuity,
            fault_positions=fault_x,
            arifos_grade="TRUST-GRADED" if continuity > 0.8 else "RAW",
        )
        picks.append(pick)

    return picks


def build_2d_section(
    x_range: Tuple[float, float],
    z_range: Tuple[float, float],
    n_traces: int = 200,
    n_samples: int = 500,
    structure_type: str = "anticline",
    fault_present: bool = True,
    noise_db: float = -18,
) -> SeismicSection:
    """
    Generate 2D seismic section with geological structure.
    structure_type: "anticline", "syncline", "fault_block", "horizon_slice", "salt_dome"
    """
    rng = np.random.default_rng(77)
    x = np.linspace(x_range[0], x_range[1], n_traces)
    t = np.linspace(z_range[0], z_range[1], n_samples)
    dt = t[1] - t[0]

    data = np.zeros((n_samples, n_traces))
    horizons = []
    faults = []

    # Build geological structure
    def structure_depth(x_pos: float, t_range: Tuple[float, float], layer: int) -> float:
        t_span = t_range[1] - t_range[0]
        x_norm = (x_pos - x_range[0]) / max(x_range[1] - x_range[0], 1)

        if structure_type == "anticline":
            # Dome/anticline
            base = t_range[0] + layer * t_span / 6
            dip = -80 * np.exp(-((x_norm - 0.5)**2) / 0.08)
            return base + dip
        elif structure_type == "syncline":
            base = t_range[0] + layer * t_span / 6
            dip = +120 * np.exp(-((x_norm - 0.5)**2) / 0.06)
            return base + dip
        elif structure_type == "fault_block":
            base = t_range[0] + layer * t_span / 6
            dip = -60 * x_norm
            fault_x = x_range[0] + 0.4 * (x_range[1] - x_range[0])
            if abs(x_pos - fault_x) < (x_range[1] - x_range[0]) * 0.03:
                dip += 80 * np.exp(-((x_pos - fault_x)**2) / 0.002)
            return base + dip
        elif structure_type == "salt_dome":
            base = t_range[0] + layer * t_span / 6
            center_x = (x_range[0] + x_range[1]) / 2
            radius = (x_range[1] - x_range[0]) * 0.1
            dist = np.sqrt((x_pos - center_x)**2 + 5e7)
            if dist < radius:
                return base - 100 * (1 - dist / radius)
            return base
        else:
            return t_range[0] + layer * t_span / 6

    # Generate traces
    wavelet = build_wavelet(35.0, dt, "ricker")

    # Layer definitions with reflection coefficients
    layers = [
        {"name": "Sea Floor",           "rc": -0.6,  "color": "#4488ff"},
        {"name": "Recent Shale",         "rc":  0.15, "color": "#aabb44"},
        {"name": "Upper Sand",           "rc": -0.25, "color": "#ddbb66"},
        {"name": "Mid Shale",            "rc":  0.10, "color": "#88aa55"},
        {"name": "Limestone Top",        "rc": -0.35, "color": "#cc9966"},
        {"name": "Basal Sand",           "rc": -0.20, "color": "#eecc55"},
    ]

    for ix, xpos in enumerate(x):
        trace = np.zeros(n_samples)

        for layer in layers:
            t_layer = structure_depth(xpos, z_range, layers.index(layer))
            t_idx = int(np.interp(t_layer, t, np.arange(n_samples)))
            t_idx = np.clip(t_idx, 0, n_samples - 1)

            # Add reflection with some lateral variation
            rc_val = layer["rc"] * (1 + 0.1 * rng.normal(0, 1))
            amp = rc_val * 0.8
            trace[t_idx] += amp

            # Add intra-layer reflections (dim)
            for sub in range(3):
                t_sub = t_layer + (sub + 1) * (z_range[1] - z_range[0]) / (len(layers) * 4)
                i_sub = int(np.interp(t_sub, t, np.arange(n_samples)))
                i_sub = np.clip(i_sub, 0, n_samples - 1)
                trace[i_sub] += 0.1 * rng.normal(0, 1) * rc_val

        # Convolve wavelet
        trace = np.convolve(wavelet, trace, mode='same')

        # Add noise
        trace += rng.normal(0, 10 ** (noise_db / 20), n_samples)

        # NMO gain
        gain = np.exp(0.004 * np.arange(n_samples))
        data[:, ix] = trace * gain

        # Record horizon at center trace
        if ix == n_traces // 2:
            for layer in layers:
                t_layer = structure_depth(xpos, z_range, layers.index(layer))
                amp_at = int(np.interp(t_layer, t, np.arange(n_samples)))
                amp_at = np.clip(amp_at, 0, n_samples - 1)
                horizons.append(HorizonPick(
                    name=layer["name"],
                    time_ms=float(t_layer),
                    x_positions=x.tolist(),
                    amplitudes=data[amp_at, :].tolist(),
                    phase="positive" if layer["rc"] > 0 else "negative",
                    continuity=0.75 + 0.1 * rng.random(),
                    fault_positions=[],
                    arifos_grade="AAA",
                ))

    data /= (np.max(np.abs(data)) + 1e-9)

    # Fault interpretation
    if fault_present:
        fault_x = x_range[0] + 0.4 * (x_range[1] - x_range[0])
        faults.append({
            "type": "normal",
            "x_position": float(fault_x),
            "vertical_extent_ms": float(z_range[1] - z_range[0]),
            "throw_m": 50,
            "arifos_grade": "TRUST-GRADED",
        })

    return SeismicSection(
        data=data, x_coords=x, t_coords=t,
        horizons=horizons, faults=faults,
        metadata={
            "structure_type": structure_type,
            "n_traces": n_traces,
            "dominant_freq_hz": 35.0,
            "constitution": "888_JUDGE",
            "dimension": "2D",
        }
    )


def export_segy(seismic_section: SeismicSection, output_path: str) -> Dict[str, Any]:
    """Export seismic section to SEG-Y format using segyio."""
    try:
        import segyio

        spec = segyio.spec()
        spec.offsets = 1
        spec.sorting = 2  # CDP
        spec.format  = 5  # IBM float
        spec.samples = seismic_section.t_coords.tolist()

        with segyio.create(output_path, spec) as f:
            for i, tr in enumerate(seismic_section.data.T):
                f.trace[i] = tr
                f.header[i] = {
                    segyio.su.tracf: i + 1,
                    segyio.su.cdps: i + 1,
                    segyio.su.ep:   1,
                }
        return {"status": "ok", "path": output_path, "traces": seismic_section.data.shape[1]}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def amplitude_analysis(seis_data: np.ndarray, window_ms: float,
                       t_coords: np.ndarray, x_coords: np.ndarray) -> Dict[str, np.ndarray]:
    """
    RMS amplitude, instantaneous phase, frequency analysis.
    Returns amplitude map over the section.
    """
    n_samples, n_traces = seis_data.shape
    dt = t_coords[1] - t_coords[0]
    win_samples = max(int(window_ms / dt), 3)

    rms = np.zeros((n_traces,))
    for ix in range(n_traces):
        windowed = seis_data[:, ix]
        rms[ix] = np.sqrt(np.mean(windowed ** 2))

    # Envelope (instantaneous amplitude)
    from scipy.signal import hilbert
    envelope = np.abs(hilbert(seis_data, axis=0))

    return {
        "rms_amplitude": rms.tolist(),
        "max_amplitude": np.max(seis_data, axis=0).tolist(),
        "envelope_slice": envelope[len(t_coords)//2, :].tolist(),
        "x_coords": x_coords.tolist(),
        "metadata": {
            "window_ms": window_ms,
            "dimension": "2D_amplitude",
        }
    }