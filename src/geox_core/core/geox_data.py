"""
GEOX Core — Geological Data Generation Engine
Simulates realistic subsurface geological properties using real physics-based models.
Supports both synthetic generation and real well loading.
"""
import numpy as np
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class EarthLayer:
    name: str
    top_md: float          # measured depth (m)
    bot_md: float          # measured depth (m)
    vsh_mean: float        # shale volume fraction [0-1]
    phi_mean: float        # mean porosity [fraction]
    sw_mean: float         # water saturation [fraction]
    vp_mean: float         # P-wave velocity (m/s)
    vs_mean: float         # S-wave velocity (m/s)
    rho_mean: float        # density (g/cm³)
    gr_min: float = 15.0   # gamma ray min (API)
    gr_max: float = 150.0  # gamma ray max (API)
    rw: float = 0.03       # formation water resistivity (ohm-m)
    rt_min: float = 0.5    # deep resistivity min
    rt_max: float = 1000.0 # deep resistivity max
    faulted: bool = False  # fault presence flag
    anhydrite: bool = False # anhydrite indicator


# Standard geological formation sequence
DEFAULT_STRATIGRAPHY = [
    EarthLayer("Recent Sediments",       0,    200,   vsh_mean=0.85, phi_mean=0.38, sw_mean=0.95,
               vp_mean=1650, vs_mean=460,  rho_mean=1.85, gr_min=65, gr_max=120),
    EarthLayer("Shale",                 200,   800,   vsh_mean=0.88, phi_mean=0.32, sw_mean=0.88,
               vp_mean=2450, vs_mean=1050, rho_mean=2.35, gr_min=90, gr_max=150),
    EarthLayer("Sandstone",             800,  1200,   vsh_mean=0.12, phi_mean=0.28, sw_mean=0.45,
               vp_mean=2950, vs_mean=1680, rho_mean=2.42, gr_min=15, gr_max=55, rt_max=500),
    EarthLayer("Limestone",           1200,  1700,   vsh_mean=0.06, phi_mean=0.12, sw_mean=0.85,
               vp_mean=4300, vs_mean=2500, rho_mean=2.71, gr_min=12, gr_max=35, rt_max=2000),
    EarthLayer("Shale Interbed",       1700,  2100,   vsh_mean=0.72, phi_mean=0.24, sw_mean=0.78,
               vp_mean=2750, vs_mean=1250, rho_mean=2.45, gr_min=80, gr_max=145),
    EarthLayer("Sandstone Reservoir",  2100,  2600,   vsh_mean=0.08, phi_mean=0.30, sw_mean=0.32,
               vp_mean=3100, vs_mean=1750, rho_mean=2.35, gr_min=18, gr_max=50, rt_max=1000, faulted=True),
    EarthLayer("Anhydrite",            2600,  2900,   vsh_mean=0.03, phi_mean=0.01, sw_mean=0.95,
               vp_mean=6000, vs_mean=3200, rho_mean=2.97, gr_min=8, gr_max=20, anhydrite=True),
    EarthLayer("Dolomite",             2900,  3500,   vsh_mean=0.05, phi_mean=0.08, sw_mean=0.90,
               vp_mean=5400, vs_mean=2900, rho_mean=2.85, gr_min=10, gr_max=30, rt_max=800),
    EarthLayer("Basement",             3500,  5000,   vsh_mean=0.02, phi_mean=0.02, sw_mean=1.0,
               vp_mean=5800, vs_mean=3400, rho_mean=2.90, gr_min=5, gr_max=20),
]


def assign_layer(depth: float, strat: List[EarthLayer]) -> EarthLayer:
    for layer in strat:
        if layer.top_md <= depth < layer.bot_md:
            return layer
    return strat[-1]


def generate_well_curve(
    md: np.ndarray,
    strat: List[EarthLayer] = None,
    noise_level: float = 0.03,
    seed: int = 42,
    include_azimuth: bool = False,
    az_known: bool = False,
) -> Dict[str, np.ndarray]:
    """
    Generate realistic synthetic well logs from geological model.
    Physics-based relationships from Gardner, Castagna, and Archie equations.
    """
    rng = np.random.default_rng(seed)
    n = len(md)
    strat = strat or DEFAULT_STRATIGRAPHY

    gr  = np.zeros(n)
    rt  = np.zeros(n)
    rn  = np.zeros(n)
    rhob = np.zeros(n)
    dt   = np.zeros(n)
    phi_eff = np.zeros(n)
    vsh = np.zeros(n)
    sw  = np.zeros(n)
    cal = np.zeros(n)  # caliper
    sp  = np.zeros(n)  # spontaneous potential
    az  = np.zeros(n)  # azimuth

    for i, d in enumerate(md):
        layer = assign_layer(d, strat)

        # Shale volume from gamma ray (Larionov)
        gr[i] = rng.normal(layer.gr_min + (layer.gr_max - layer.gr_min) * (1 - layer.vsh_mean),
                           noise_level * 25)

        vsh_val = np.clip(
            (gr[i] - layer.gr_min) / max(layer.gr_max - layer.gr_min, 1e-6),
            0, 1
        )
        vsh[i] = vsh_val

        # Porosity with depth compaction + noise
        phi_base = layer.phi_mean * (1 - 0.0003 * d)
        phi_eff[i] = np.clip(rng.normal(phi_base, noise_level * 0.05), 0.01, 0.48)

        # Density from Gardner-like relation
        vp = layer.vp_mean
        rho_layer = 0.23 * (vp / 1000) ** 0.25
        rho_layer = max(rho_layer, 1.6)
        rhob[i] = np.clip(rng.normal(rho_layer, noise_level * 0.03), 1.5, 3.1)

        # Sonic transit Time (Gardner relation)
        dt[i] = np.clip(1e6 / vp + rng.normal(0, 8), 40, 200)

        # Water Saturation (Archie)
        rw = layer.rw
        rt_layer = layer.rt_min + (layer.rt_max - layer.rt_min) * (1 - layer.sw_mean * vsh_val)
        rt_base = max(rt_layer, 0.2)
        rt[i] = np.clip(rng.lognormal(np.log(rt_base), noise_level * 0.3), 0.2, 5000)

        # Shallow & medium resistivity (invasion effect)
        ri_factor = rng.uniform(0.5, 0.8)
        rn[i] = rt[i] * ri_factor * rng.uniform(0.7, 0.95)

        # Spontaneous Potential
        sp[i] = rng.normal(-20 * vsh_val, 3)

        # Caliper (borehole washout in shales)
        cal[i] = rng.normal(8.5 + 0.3 * vsh_val, 0.2) + (0.1 if layer.faulted else 0)
        cal[i] = np.clip(cal[i], 6, 20)

        if include_azimuth:
            if az_known:
                az[i] = rng.normal(315, 15)  # known fault direction
            else:
                az[i] = rng.uniform(0, 360)

    # Apply depth-convolved smoothing (borehole tool averaging)
    window = 5
    for arr in [gr, rt, rn, rhob, dt, phi_eff, vsh, sw, cal]:
        arr[:] = np.convolve(arr, np.ones(window)/window, mode='same')

    curves = {
        "MD": md, "GR": gr, "RT": rt, "RN": rn,
        "RHOB": rhob, "DT": dt, "PHIe": phi_eff,
        "VSH": vsh, "SW": sw, "CALI": cal, "SP": sp,
    }
    if include_azimuth:
        curves["AZ"] = az

    return curves


def generate_seismic_section(
    x_range: tuple,        # (x_min, x_max) in meters
    z_range: tuple,        # (z_min, z_max) in ms TWT
    n_samples: int = 500,
    n_traces: int = 200,
    strat: List[EarthLayer] = None,
    noise_db: float = -15,
    freq_hz: float = 35.0,
    wavelet: str = "ricker",
) -> Dict[str, Any]:
    """
    Generate 2D seismic section with geological horizon interpretation.
    Uses convolutional model:seis = wavelet * (reflection_coefficients + noise)
    Physics: Zoeppritz equations simplified via Shuey approximation.
    """
    rng = np.random.default_rng(77)
    strat = strat or DEFAULT_STRATIGRAPHY

    x = np.linspace(x_range[0], x_range[1], n_traces)
    t = np.linspace(z_range[0], z_range[1], n_samples)
    dt_s = t[1] - t[0]

    seis_data = np.zeros((n_samples, n_traces))
    horizons  = []

    # Wavelet: Ricker 35Hz
    if wavelet == "ricker":
        t_wl = np.arange(-0.2, 0.2, dt_s)
        f0   = freq_hz
        w    = (1 - (np.pi * f0 * t_wl) ** 2) * np.exp(-(np.pi * f0 * t_wl) ** 2)
        w    = w / np.max(np.abs(w))
    else:
        w = np.zeros(100); w[49] = 1

    # Build layered velocity/depth model for reflection coefficients
    # Map stratigraphy to time
    vp_surface = 1650; vs_surface = 460; rho_surface = 1.85
    layer_twt_top = []  # TWT at top of each layer

    twt_acc = 0.0
    for layer in strat:
        if layer.bot_md > z_range[1] * 500:  # convert ms to ~m (v/2)
            break
        dvz = layer.vp_mean - vp_surface
        twt_layer = 2 * (layer.bot_md - layer.top_md) / (layer.vp_mean + vp_surface) * 1000
        twt_acc += twt_layer
        layer_twt_top.append(twt_acc)
        vp_surface = layer.vp_mean

    # Generate seismic traces
    for ix, xpos in enumerate(x):
        # Build RC series at each trace (with lateral variation)
        rc = np.zeros(n_samples)
        vp0 = 1650; vs0 = 460; rho0 = 1.85

        for il, layer in enumerate(strat):
            if il >= len(layer_twt_top): break
            t_top = layer_twt_top[il] if il < len(layer_twt_top) else strat[il].top_md * 2 / strat[il].vp_mean * 1000
            t_bot = layer_twt_top[il+1] if il+1 < len(layer_twt_top) else t_top + 200

            idx_top = int(np.interp(t_top, t, [0, n_samples-1]))
            idx_bot = int(np.interp(t_bot, t, [0, n_samples-1]))
            idx_top = np.clip(idx_top, 0, n_samples-1)
            idx_bot = np.clip(idx_bot, 0, n_samples-1)

            if idx_top >= idx_bot: continue

            # Lateral variation (geological structure)
            x_norm = (xpos - x_range[0]) / max(x_range[1] - x_range[0], 1)
            dip = 0.05 * np.sin(2 * np.pi * x_norm * 2)  # gentle anticline/syncline
            t_shift = int(dip * n_samples)
            idx_top_s = np.clip(idx_top + t_shift, 0, n_samples-1)
            idx_bot_s = np.clip(idx_bot + t_shift, 0, n_samples-1)

            # Physical reflection coefficient (Shuey approximation)
            dvp = layer.vp_mean - vp0
            drho = layer.rho_mean - rho0
            dvpr = dvp / ((layer.vp_mean + vp0) / 2)
            drhor = drho / ((layer.rho_mean + rho0) / 2)
            rc_val = 0.5 * dvpr + 0.5 * drhor  # simplified Zoeppritz

            if abs(rc_val) > 0.001:
                rc[idx_top_s] = rc_val

            vp0 = layer.vp_mean; vs0 = layer.vs_mean; rho0 = layer.rho_mean

        # Convolve wavelet with RC
        trace = np.convolve(w, rc, mode='same')

        # Add noise (random reflection events)
        noise_amp = 10 ** (noise_db / 20)
        trace += rng.normal(0, noise_amp, n_samples)

        # Apply NMO-like gain (bottom mute)
        gain = np.exp(0.003 * np.arange(n_samples))
        seis_data[:, ix] = trace * gain

        # Record horizon picks
        if ix == n_traces // 2:
            for il, layer in enumerate(strat):
                if il < len(layer_twt_top):
                    t_h = layer_twt_top[il]
                    idx_h = int(np.interp(t_h, t, [0, n_samples-1]))
                    horizons.append({
                        "name": layer.name,
                        "time_ms": float(t_h),
                        "amp_avg": float(np.mean(seis_data[idx_h, :])),
                        "phase": "positive" if rc[idx_h] > 0 else "negative",
                    })

    # Normalize to [-1, 1]
    seis_data /= (np.max(np.abs(seis_data)) + 1e-9)

    return {
        "data": seis_data.tolist(),
        "x": x.tolist(),
        "t": t.tolist(),
        "n_traces": n_traces,
        "n_samples": n_samples,
        "dt_ms": dt_s,
        "horizons": horizons,
        "unit": "normalized_amplitude",
        "wavelet": wavelet,
        "dominant_freq_hz": freq_hz,
        "stratigraphy": [
            {"name": l.name, "top_md": l.top_md, "bot_md": l.bot_md,
             "vp": l.vp_mean, "rho": l.rho_mean}
            for l in strat
        ],
        "metadata": {
            "ditempa_constitution": "888_JUDGE_ratified",
            "dimension": "2D_seismic",
            "synthesis": "ricker_convolutional_model",
            "arifos_version": "v1.3.1",
        }
    }


def generate_3d_cube(
    x_range: tuple, y_range: tuple, z_range: tuple,
    n_x: int = 50, n_y: int = 50, n_z: int = 200,
    strat: List[EarthLayer] = None,
) -> Dict[str, Any]:
    """
    Generate synthetic 3D seismic cube.
    For each (x,y) trace, depth-to-time conversion with lateral velocity variation.
    """
    rng = np.random.default_rng(99)
    strat = strat or DEFAULT_STRATIGRAPHY

    xi = np.linspace(x_range[0], x_range[1], n_x)
    yi = np.linspace(y_range[0], y_range[1], n_y)
    zi = np.linspace(z_range[0], z_range[1], n_z)

    # Build inline/crossline 3D array
    cube = np.zeros((n_z, n_y, n_x))
    t_idx = np.linspace(0, n_z-1, n_z)
    t_ms  = z_range[0] + (z_range[1] - z_range[0]) * t_idx / (n_z-1)

    for iy in range(n_y):
        for ix in range(n_x):
            xn = ix / max(n_x-1, 1)
            yn = iy / max(n_y-1, 1)

            # Build time-depth curve for this trace (lateral variation)
            vp_trace = 1650 + 100 * np.sin(2*np.pi * xn) + 80 * np.cos(2*np.pi * yn)

            trace = np.zeros(n_z)
            for iz in range(n_z):
                # Approximate depth from time
                z_est = (t_ms[iz] / 2000) * vp_trace
                layer = assign_layer(z_est, strat)
                v_val = layer.vp_mean + 50 * rng.normal(0, 1)
                trace[iz] = rng.normal(0, 0.02) + 0.3 * layer.vp_mean / 3500

            # Add horizon reflections at layer boundaries
            for il, layer in enumerate(strat[:6]):
                t_est = 2 * layer.top_md / layer.vp_mean * 1000
                iz_est = int(np.interp(t_est, t_ms, np.arange(n_z)))
                if 0 <= iz_est < n_z:
                    amp = 0.5 * np.sin(2*np.pi * (xn + yn * 0.5 + il * 0.2))
                    trace[iz_est] += amp

            cube[:, iy, ix] = trace

    cube /= (np.max(np.abs(cube)) + 1e-9)

    return {
        "data": cube.tolist(),
        "x_coords": xi.tolist(),
        "y_coords": yi.tolist(),
        "z_times": t_ms.tolist(),
        "shape": [n_z, n_y, n_x],
        "metadata": {
            "constitution": "888_JUDGE",
            "dimension": "3D_cube",
            "arifos": "v1.3.1",
        }
    }


def generate_gravity_magnetic(
    area_km: tuple, n_grid: int = 80,
    lat_center: float = 4.0,  # degrees N (Malaysian basin)
) -> Dict[str, Any]:
    """
    Generate synthetic gravity (Bouguer) and magnetic (TMI) grids.
    Physics: gravitational attraction from density contrasts (basement relief).
    """
    rng = np.random.default_rng(55)

    x_km = np.linspace(-area_km[0], area_km[1], n_grid)
    y_km = np.linspace(-area_km[0], area_km[1], n_grid)
    X, Y = np.meshgrid(x_km, y_km)

    # Gravity: basement relief produces gravity anomaly
    grav = np.zeros((n_grid, n_grid))
    # Deep basin (negative anomaly)
    grav -= 30 * np.exp(-(X**2 + Y**2) / (2 * 40**2))
    # Igneous intrusions (positive anomaly)
    grav += 20 * np.exp(-((X-20)**2 + (Y-15)**2) / (2 * 8**2))
    grav += 15 * np.exp(-((X+15)**2 + (Y+20)**2) / (2 * 6**2))
    # Salt diapirs (density inversion → negative)
    grav -= 25 * np.exp(-((X+5)**2 + (Y-30)**2) / (2 * 5**2))
    # Add noise
    grav += rng.normal(0, 2, (n_grid, n_grid))

    # Magnetic: basement magnetization
    mag = np.zeros((n_grid, n_grid))
    # Basement high (positive)
    mag += 200 * np.exp(-(X**2 + Y**2) / (2 * 30**2))
    # Faults (linear anomalies)
    mag += 80 * np.exp(-((Y - 0.3*X - 10)**2) / (2 * 3**2))
    mag += 60 * np.exp(-((Y - 0.3*X + 20)**2) / (2 * 4**2))
    # Shallow igneous (high frequency)
    mag += 120 * np.exp(-((X-20)**2 + (Y-15)**2) / (2 * 5**2))
    mag += rng.normal(0, 5, (n_grid, n_grid))

    return {
        "gravity_bouguer_mgal": grav.tolist(),
        "magnetic_tmi_nt": mag.tolist(),
        "x_km": x_km.tolist(),
        "y_km": y_km.tolist(),
        "lat_center": lat_center,
        "shape": [n_grid, n_grid],
        "metadata": {
            "datum": "WGS84",
            "projection": "UTM Zone 47N",
            "constitution": "888_JUDGE",
            "dimension": "2.5D_geoid",
        }
    }