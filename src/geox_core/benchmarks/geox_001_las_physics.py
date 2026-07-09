"""
GEOX-001 LAS Physics — F2 anchor from curves, not summary tables.

Computes from LAS arrays:
  density porosity · neutron porosity · composite φ · Vsh · AI · RC
  optional Sw (Archie) when RT present

This is the Petrel-delta first step: 1D math before 3D grids.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from geox_core.core.geox_1d import (
    compute_porosity_dt,
    compute_porosity_neutron,
    compute_porosity_rhob,
    compute_sw_archie,
    compute_vsh_gr,
)
from geox_core.core.welltie import compute_ai, compute_reflectivity, compute_vp_from_sonic


def compute_las_physics(
    curves: dict[str, list[float] | np.ndarray],
    *,
    matrix_density: float = 2.65,
    fluid_density: float = 1.0,
    rw: float = 0.03,
    dt_unit: str = "usft",
) -> dict[str, Any]:
    """Derive petrophysics + elastic series from LAS curve dicts.

    All outputs labeled DER (computed). Input curves remain OBS when from file.
    """
    def _arr(*keys: str) -> np.ndarray | None:
        for k in keys:
            if k in curves and curves[k] is not None:
                return np.asarray(curves[k], dtype=float)
        return None

    depth = np.asarray(curves["DEPT"], dtype=float)
    dt = _arr("DT", "AC")
    if dt is None:
        raise ValueError("LAS physics requires DT or AC sonic curve")
    rhob = _arr("RHOB", "DEN")
    gr = _arr("GR")
    nphi = _arr("NPHI", "NEU")
    rt = _arr("RT", "RDEP")

    # unit heuristic: mean |DT|
    if dt_unit == "usft" and np.nanmean(np.abs(dt)) > 200:
        dt_unit = "usm"

    vp = compute_vp_from_sonic(dt, depth, dt_unit=dt_unit)
    if rhob is None:
        from geox_core.physics.parameters import gardner_density

        rhob = gardner_density(vp) / 1000.0
        rhob_source = "DER_GARDNER"
    else:
        if np.nanmedian(rhob) > 10:
            rhob = rhob / 1000.0
        rhob_source = "OBS_RHOB"

    phi_d = compute_porosity_rhob(rhob, matrix_density, fluid_density)
    # us/ft matrix ~55.5, fluid ~189 for Wyllie; us/m uses geox_1d defaults
    if dt_unit == "usft":
        phi_s = compute_porosity_dt(dt, dt_ma=55.5, dt_f=189.0)
    else:
        phi_s = compute_porosity_dt(dt)

    if nphi is not None:
        n = nphi.copy()
        if np.nanmedian(np.abs(n)) > 1.0:
            n = n / 100.0
        phi_n = np.clip(n, -0.05, 0.6)
        phi_n_source = "OBS_NPHI"
    else:
        phi_n = phi_d.copy()
        phi_n_source = "ABSENT_NPHI_USE_PHID"

    phi_total = np.clip(0.5 * (phi_d + phi_n), 0.0, 0.45)
    vsh = compute_vsh_gr(gr) if gr is not None else np.zeros_like(depth)
    phi_e = np.clip(phi_total * (1.0 - vsh), 0.0, 0.4)

    ai = compute_ai(vp, rhob, rho_unit="gcc")
    rc = compute_reflectivity(ai, polarity="SEG_NORMAL")

    sw = None
    if rt is not None:
        sw = compute_sw_archie(rt, phi_n if nphi is not None else phi_d, phi_e, rw=rw)

    # Zone stats (whole window P10/P50/P90 of effective porosity)
    finite = np.isfinite(phi_e)
    phi_vals = phi_e[finite]
    if len(phi_vals) == 0:
        phi_stats = {"p10": None, "p50": None, "p90": None}
    else:
        phi_stats = {
            "p10": float(np.percentile(phi_vals, 10)),
            "p50": float(np.percentile(phi_vals, 50)),
            "p90": float(np.percentile(phi_vals, 90)),
            "mean": float(np.mean(phi_vals)),
            "n": int(len(phi_vals)),
        }

    net = (phi_e >= 0.08) & (vsh <= 0.5)
    if sw is not None:
        net = net & (sw <= 0.70)
    net_to_gross = float(np.mean(net)) if len(net) else 0.0

    return {
        "epistemic": {
            "curves": "OBS" if rhob_source.startswith("OBS") else "DER",
            "porosity": "DER",
            "vsh": "DER" if gr is not None else "SPEC",
            "ai_rc": "DER",
            "sw": "DER" if sw is not None else "ABSENT",
        },
        "rhob_source": rhob_source,
        "phi_n_source": phi_n_source,
        "dt_unit": dt_unit,
        "stats": {
            "phi_e": phi_stats,
            "net_to_gross": round(net_to_gross, 4),
            "vp_mean": float(np.nanmean(vp)),
            "ai_mean": float(np.nanmean(ai)),
            "depth_range_m": [float(np.nanmin(depth)), float(np.nanmax(depth))],
        },
        "series": {
            "depth_m": depth.tolist(),
            "vp_ms": vp.tolist(),
            "rhob_gcc": rhob.tolist(),
            "phi_density": phi_d.tolist(),
            "phi_sonic": phi_s.tolist(),
            "phi_neutron": phi_n.tolist(),
            "phi_effective": phi_e.tolist(),
            "vsh": vsh.tolist(),
            "ai": ai.tolist(),
            "rc": rc.tolist(),
            "sw": sw.tolist() if sw is not None else None,
            "net_flag": net.astype(int).tolist(),
        },
        "equations": {
            "phi_density": "φ_d = (ρ_ma - ρ_b) / (ρ_ma - ρ_f)",
            "phi_sonic": "φ_s = (Δt - Δt_ma) / (Δt_f - Δt_ma)  [Wyllie]",
            "phi_e": "φ_e = φ_t · (1 - Vsh)",
            "ai": "AI = Vp · ρ",
            "rc": "RC = (AI₂ - AI₁) / (AI₂ + AI₁)",
            "sw": "Sw = [(a·Rw)/(Rt·φ^m)]^(1/n)  [Archie]",
        },
        "anti_hantu": [
            "porosity is DERIVED from logs — not a table citation",
            "impedance is not lithology",
            "Sw requires Rw assumption — SPEC unless formation water measured",
        ],
    }
