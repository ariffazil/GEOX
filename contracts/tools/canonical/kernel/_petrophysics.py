# ─── kernel/_petrophysics.py ─── petrophysics computations ───────────────────
# Extracted from _helpers.py (lines 453–1042)
# NO FastMCP imports. Pure business logic.
# Imports geox.core.geox_1d (business logic, not FastMCP).
import os

from ._registry import _get_artifact
from typing import Any, Dict, List, Literal, Optional

def _compute_vsh_from_store(
    artifact_ref: str,
    gr_clean: float,
    gr_shale: float,
    method: str,
    zone_top_m: Optional[float] = None,
    zone_base_m: Optional[float] = None,
) -> dict:
    """Compute Vsh from stored LAS data. Returns stats dict or error dict."""
    import numpy as np
    from geox.core.geox_1d import compute_vsh_gr

    data = _get_well_data_with_depth(artifact_ref, zone_top_m, zone_base_m)
    if "error" in data:
        return data

    curves = data["curves"]
    depth = data["depth"]

    # Find GR using canonical aliases
    gr = None
    gr_mnemonic = None
    for alias in CANONICAL_ALIASES.get("GR", ["GR"]):
        if alias in curves:
            gr = curves[alias]
            gr_mnemonic = alias
            break

    if gr is None:
        return {"error": "GR_CURVE_NOT_FOUND", "available": list(curves.keys())}

    # Apply Vsh method
    igr = np.clip((gr - gr_clean) / max(gr_shale - gr_clean, 1e-6), 0, 1)
    if method == "larionov_tertiary":
        vsh = 0.083 * (2.0 ** (3.7 * igr) - 1.0)
    elif method == "larionov_older":
        vsh = 0.33 * (2.0 ** (2.0 * igr) - 1.0)
    elif method == "clavier":
        vsh = 1.7 - (3.38 - (igr + 0.7) ** 2) ** 0.5
    elif method == "steiber":
        vsh = igr / (3.0 - 2.0 * igr)
    else:  # linear
        vsh = compute_vsh_gr(gr, gr_clean, gr_shale)

    vsh = np.clip(vsh, 0, 1)
    # Replace any NaN from clavier with 0 or 1
    vsh = np.where(np.isnan(vsh), 0.5, vsh)
    valid_mask = ~np.isnan(vsh)
    n_valid = int(valid_mask.sum())

    if n_valid == 0:
        return {"error": "NO_VALID_SAMPLES_IN_ZONE", "artifact_ref": artifact_ref}

    return {
        "gr_mnemonic_used": gr_mnemonic,
        "method": method,
        "gr_clean": gr_clean,
        "gr_shale": gr_shale,
        "n_samples": n_valid,
        "vsh_mean": _safe_reduction(np.nanmean, vsh),
        "vsh_p10": _safe_reduction(lambda x: np.nanpercentile(x, 10), vsh),
        "vsh_p50": _safe_reduction(lambda x: np.nanpercentile(x, 50), vsh),
        "vsh_p90": _safe_reduction(lambda x: np.nanpercentile(x, 90), vsh),
        "net_sand_fraction": _safe_reduction(lambda x: (x < 0.5).mean(), vsh),
        "depth_range_m": [float(depth[0]), float(depth[-1])],
        "curve_stats": {
            "gr_min": _safe_reduction(np.nanmin, gr),
            "gr_max": _safe_reduction(np.nanmax, gr),
        },
        "_vsh_array": vsh,
        "_gr_array": gr,
        "_curves": curves,
        "_depth": depth,
    }


def _compute_porosity_from_store(
    artifact_ref: str,
    matrix_density: float,
    fluid_density: float,
    zone_top_m: Optional[float] = None,
    zone_base_m: Optional[float] = None,
) -> dict:
    """Compute PHIT from stored LAS data using RHOB and/or NPHI. Returns stats dict."""
    import numpy as np
    from geox.core.geox_1d import compute_porosity_rhob, compute_porosity_neutron

    data = _get_well_data_with_depth(artifact_ref, zone_top_m, zone_base_m)
    if "error" in data:
        return data

    curves = data["curves"]
    depth = data["depth"]

    phit = None
    methods_used = []
    rhob_mnemonic = None
    nphi_mnemonic = None

    # Try RHOB first
    for alias in CANONICAL_ALIASES.get("RHOB", ["RHOB"]):
        if alias in curves:
            rhob = curves[alias]
            rhob_mnemonic = alias
            phi_rhob = compute_porosity_rhob(rhob, matrix_density, fluid_density)
            phit = phi_rhob
            methods_used.append(f"density({alias})")
            break

    # Try NPHI
    for alias in CANONICAL_ALIASES.get("NPHI", ["NPHI"]):
        if alias in curves:
            nphi_raw = curves[alias]
            nphi_mnemonic = alias
            phi_nphi = compute_porosity_neutron(nphi_raw)
            if phit is not None:
                # Average density + neutron (standard crossplot approach)
                phit = 0.5 * (phit + phi_nphi)
                methods_used.append(f"neutron({alias})")
            else:
                phit = phi_nphi
                methods_used.append(f"neutron({alias})")
            break

    if phit is None:
        return {"error": "NO_POROSITY_CURVES", "available": list(curves.keys())}

    phit = np.clip(phit, 0, 0.6)
    valid_mask = ~np.isnan(phit)
    n_valid = int(valid_mask.sum())

    if n_valid == 0:
        return {"error": "NO_VALID_POROSITY_SAMPLES", "artifact_ref": artifact_ref}

    return {
        "methods_used": methods_used,
        "rhob_mnemonic_used": rhob_mnemonic,
        "nphi_mnemonic_used": nphi_mnemonic,
        "matrix_density": matrix_density,
        "fluid_density": fluid_density,
        "n_samples": n_valid,
        "phit_mean": _safe_reduction(np.nanmean, phit),
        "phit_p10": _safe_reduction(lambda x: np.nanpercentile(x, 10), phit),
        "phit_p50": _safe_reduction(lambda x: np.nanpercentile(x, 50), phit),
        "phit_p90": _safe_reduction(lambda x: np.nanpercentile(x, 90), phit),
        "phit_max": _safe_reduction(np.nanmax, phit),
        "depth_range_m": [float(depth[0]), float(depth[-1])],
        "_phit_array": phit,   # internal
        "_curves": curves,     # internal
        "_depth": depth,       # internal
    }


def _compute_saturation_from_store(
    artifact_ref: str,
    sw_model: str,
    rw: float,
    a: float,
    m: float,
    n: float,
    vsh_result: dict | None = None,
    phit_result: dict | None = None,
    zone_top_m: Optional[float] = None,
    zone_base_m: Optional[float] = None,
) -> dict:
    """Compute Sw from stored LAS data. Returns stats dict."""
    import numpy as np
    from geox.core.geox_1d import compute_sw_archie, compute_sw_indonesian

    if (vsh_result and "_curves" in vsh_result) or (phit_result and "_curves" in phit_result):
        curves = (vsh_result or {}).get("_curves") or (phit_result or {}).get("_curves")
        depth = (vsh_result or {}).get("_depth") or (phit_result or {}).get("_depth")
    else:
        data = _get_well_data_with_depth(artifact_ref, zone_top_m, zone_base_m)
        if "error" in data:
            return data
        curves = data["curves"]
        depth = data["depth"]

    # Find RT
    rt = None
    rt_mnemonic = None
    for alias in CANONICAL_ALIASES.get("RT", ["RT"]):
        if alias in curves:
            rt = curves[alias]
            rt_mnemonic = alias
            break

    if rt is None:
        return {"error": "RT_CURVE_NOT_FOUND", "available": list(curves.keys())}

    # Get phi from pre-computed or compute fresh
    if phit_result and "_phit_array" in phit_result:
        phi = phit_result["_phit_array"]
    else:
        from geox.core.geox_1d import compute_porosity_rhob
        phi = None
        for alias in CANONICAL_ALIASES.get("RHOB", ["RHOB"]):
            if alias in curves:
                phi = compute_porosity_rhob(curves[alias])
                break
        if phi is None:
            phi = np.full(len(rt), 0.2)  # fallback

    # Get vsh from pre-computed if available
    vsh = None
    if vsh_result and "_vsh_array" in vsh_result:
        vsh = vsh_result["_vsh_array"]
    else:
        vsh = np.full(len(rt), 0.1)  # default

    rn_dummy = np.zeros_like(rt)  # dummy for interface compatibility

    if sw_model == "indonesia":
        sw = compute_sw_indonesian(rt, rn_dummy, phi, vsh, rw=rw, a=a, m=m)
    else:
        sw = compute_sw_archie(rt, rn_dummy, phi, rw=rw, a=a, m=m, n=n)

    sw = np.clip(sw, 0, 1)
    valid_mask = ~np.isnan(sw)
    n_valid = int(valid_mask.sum())

    if n_valid == 0:
        return {"error": "NO_VALID_SATURATION_SAMPLES", "artifact_ref": artifact_ref}

    return {
        "sw_model": sw_model,
        "rt_mnemonic_used": rt_mnemonic,
        "rw": rw,
        "archie_a": a,
        "archie_m": m,
        "archie_n": n,
        "n_samples": n_valid,
        "sw_mean": _safe_reduction(np.nanmean, sw),
        "sw_p10": _safe_reduction(lambda x: np.nanpercentile(x, 10), sw),
        "sw_p50": _safe_reduction(lambda x: np.nanpercentile(x, 50), sw),
        "sw_p90": _safe_reduction(lambda x: np.nanpercentile(x, 90), sw),
        "so_mean": _safe_reduction(lambda x: 1.0 - np.nanmean(x), sw),
        "depth_range_m": [float(depth[0]), float(depth[-1])],
        "_sw_array": sw,
        "_phi_array": phi,
        "_rt_array": rt,
        "_depth": depth,
    }


def _compute_netpay_from_store(
    artifact_ref: str,
    vsh_cutoff: float,
    phi_cutoff: float,
    sw_cutoff: float,
    rt_cutoff: float,
    gr_clean: float,
    gr_shale: float,
    sw_model: str = "archie",
    rw: float = 0.05,
    matrix_density: float = 2.65,
    fluid_density: float = 1.0,
) -> dict:
    """Compute net pay from stored LAS data. All cutoffs explicit in output."""
    import sys
    sys.path.insert(0, "/root/geox")
    import numpy as np

    entry = _get_artifact(artifact_ref)
    if not entry or not entry.get("las_path"):
        return {"error": "NO_LAS_PATH", "artifact_ref": artifact_ref}
    las_path = entry["las_path"]

    from geox.core.geox_1d import process_las_file

    curves = process_las_file(las_path)
    if "ERROR" in curves:
        return {"error": "LAS_PARSE_FAILED", "detail": str(curves["ERROR"][0])}

    # Get depth array
    depth = None
    for dkey in ["DEPT", "DEPTH", "MD"]:
        if dkey in curves:
            depth = curves[dkey]
            break
    if depth is None:
        return {"error": "NO_DEPTH_CURVE", "available": list(curves.keys())}

    # 1. Compute Vsh
    vsh_result = _compute_vsh_from_store(artifact_ref, gr_clean, gr_shale, "linear")
    if "error" in vsh_result:
        return {"error": f"VSH_FAILED: {vsh_result['error']}"}
    vsh = vsh_result["_vsh_array"]

    # 2. Compute Porosity
    phit_result = _compute_porosity_from_store(artifact_ref, matrix_density, fluid_density)
    if "error" in phit_result:
        return {"error": f"PHI_FAILED: {phit_result['error']}"}
    phi = phit_result["_phit_array"]

    # 3. Compute Sw
    sw_result = _compute_saturation_from_store(
        artifact_ref, sw_model, rw, 1.0, 2.0, 2.0,
        vsh_result=vsh_result, phit_result=phit_result
    )
    if "error" in sw_result:
        return {"error": f"SW_FAILED: {sw_result['error']}"}
    sw = sw_result["_sw_array"]

    # Get RT for rt_cutoff
    rt = sw_result.get("_rt_array")

    # 4. Apply cutoffs
    n = len(depth)
    min_len = min(len(vsh), len(phi), len(sw), len(depth))
    vsh = vsh[:min_len]
    phi = phi[:min_len]
    sw = sw[:min_len]
    depth = depth[:min_len]

    reservoir_mask = (vsh <= vsh_cutoff) & (phi >= phi_cutoff)
    pay_mask = reservoir_mask & (sw <= sw_cutoff)
    if rt is not None:
        rt_t = rt[:min_len]
        pay_mask = pay_mask & (rt_t >= rt_cutoff)

    # Compute step (assume uniform)
    step = abs(float(depth[1] - depth[0])) if len(depth) > 1 else 1.0
    gross_thickness = float(len(depth) * step)
    net_reservoir = float(np.sum(reservoir_mask) * step)
    net_pay = float(np.sum(pay_mask) * step)
    ntg = net_pay / gross_thickness if gross_thickness > 0 else 0.0

    # Pay intervals
    pay_intervals = []
    in_pay = False
    start_depth = 0.0
    for i in range(min_len):
        if pay_mask[i] and not in_pay:
            in_pay = True
            start_depth = float(depth[i])
        elif not pay_mask[i] and in_pay:
            in_pay = False
            pay_intervals.append({
                "top_m": start_depth,
                "base_m": float(depth[i - 1]),
                "thickness_m": round(float(depth[i - 1]) - start_depth + step, 2),
                "phi_avg": round(float(np.mean(phi[pay_mask])), 3),
                "sw_avg": round(float(np.mean(sw[pay_mask])), 3),
            })
    if in_pay:
        pay_intervals.append({
            "top_m": start_depth,
            "base_m": float(depth[-1]),
            "thickness_m": round(float(depth[-1]) - start_depth + step, 2),
            "phi_avg": round(float(np.mean(phi[pay_mask])), 3) if np.any(pay_mask) else 0.0,
            "sw_avg": round(float(np.mean(sw[pay_mask])), 3) if np.any(pay_mask) else 0.0,
        })

    return {
        "gross_thickness_m": round(gross_thickness, 2),
        "net_reservoir_m": round(net_reservoir, 2),
        "net_pay_m": round(net_pay, 2),
        "ntg": round(ntg, 4),
        "pay_intervals": pay_intervals,
        "cutoffs_applied": {
            "vsh_cutoff": vsh_cutoff,
            "phi_cutoff": phi_cutoff,
            "sw_cutoff": sw_cutoff,
            "rt_cutoff": rt_cutoff,
        },
        "vsh_stats": {
            "mean": round(float(np.nanmean(vsh)), 3),
            "p50": round(float(np.nanpercentile(vsh, 50)), 3),
        },
        "phi_stats": {
            "mean": round(float(np.nanmean(phi)), 3),
            "p50": round(float(np.nanpercentile(phi, 50)), 3),
        },
        "sw_stats": {
            "mean": round(float(np.nanmean(sw)), 3),
            "p50": round(float(np.nanpercentile(sw, 50)), 3),
        },
    }


def _classify_gr_motif(
    gr: "np.ndarray",
    depth: "np.ndarray",
    zone_top: float | None = None,
    zone_base: float | None = None,
) -> dict:
    """Classify GR log motif. Returns motif dict with EOD hints."""
    import numpy as np

    if zone_top is not None and zone_base is not None:
        mask = (depth >= zone_top) & (depth <= zone_base)
        gr = gr[mask]
        depth = depth[mask]

    if len(gr) < 5:
        return {"motif": "INSUFFICIENT_DATA", "confidence": 0.0, "claim_state": "DERIVED_CANDIDATE"}

    mid = len(gr) // 2
    gr_std = float(np.nanstd(gr))
    gr_range = float(np.nanmax(gr) - np.nanmin(gr))

    # Linear trend coefficient
    try:
        coef = float(np.polyfit(depth, gr, 1)[0])
    except Exception:
        coef = 0.0

    if gr_range < 10:
        motif = "BLOCKY"
        confidence = 0.8
    elif gr_std > 20:
        motif = "SERRATED"
        confidence = 0.7
    elif coef > 0.05:
        motif = "BELL"
        confidence = min(0.9, abs(coef) * 5)
    elif coef < -0.05:
        motif = "FUNNEL"
        confidence = min(0.9, abs(coef) * 5)
    else:
        motif = "BLOCKY"
        confidence = 0.5

    eod_hints = {
        "FUNNEL": ["delta front", "shoreface", "deepwater lobe"],
        "BELL": ["fluvial channel", "tidal channel", "transgressive lag"],
        "BLOCKY": ["amalgamated sand", "debris flow", "thick turbidite"],
        "SERRATED": ["heterolithic", "tidal flat", "interbedded"],
    }

    return {
        "motif": motif,
        "confidence": round(float(confidence), 2),
        "gr_trend": round(float(coef), 4),
        "gr_mean": round(float(np.nanmean(gr)), 1),
        "gr_std": round(float(gr_std), 1),
        "possible_eod": eod_hints.get(motif, ["unknown"]),
        "risk": "motif interpretation requires seismic/fossil tie for EOD confirmation",
        "claim_state": "DERIVED_CANDIDATE",
    }


def _classify_lithology_from_store(
    artifact_ref: str,
    zone_top_m: Optional[float] = None,
    zone_base_m: Optional[float] = None,
) -> dict:
    """Classify lithology from RHOB-NPHI crossplot zones."""
    import numpy as np

    data = _get_well_data_with_depth(artifact_ref, zone_top_m, zone_base_m)
    if "error" in data:
        return data

    curves = data["curves"]
    depth = data["depth"]

    rhob = None
    for alias in CANONICAL_ALIASES.get("RHOB", ["RHOB"]):
        if alias in curves:
            rhob = curves[alias]
            break
    nphi = None
    for alias in CANONICAL_ALIASES.get("NPHI", ["NPHI"]):
        if alias in curves:
            nphi = curves[alias]
            break

    if rhob is None or nphi is None:
        return {"error": "RHOB_OR_NPHI_NOT_FOUND", "available": list(curves.keys())}

    n = min(len(rhob), len(nphi))
    if n == 0:
        return {"error": "NO_SAMPLES_IN_ZONE"}

    rhob = rhob[:n]
    nphi = nphi[:n]

    # Simple RHOB-NPHI lithology classification
    litho_counts = {"sandstone": 0, "shale": 0, "limestone": 0, "dolomite": 0, "gas_effect": 0}
    for i in range(n):
        r = float(rhob[i])
        p = float(nphi[i])
        if np.isnan(r) or np.isnan(p):
            continue
        # Gas effect: NPHI crosses below RHOB porosity line
        phi_rhob_pt = (2.65 - r) / (2.65 - 1.0)
        if p < phi_rhob_pt - 0.06:
            litho_counts["gas_effect"] += 1
        elif r < 2.2 and p > 0.3:
            litho_counts["shale"] += 1
        elif 2.5 <= r <= 2.7 and p <= 0.25:
            litho_counts["sandstone"] += 1
        elif 2.65 <= r <= 2.75 and 0.0 <= p <= 0.25:
            litho_counts["limestone"] += 1
        elif r > 2.75 and p <= 0.15:
            litho_counts["dolomite"] += 1
        else:
            litho_counts["sandstone"] += 1  # default to sandstone

    total = sum(litho_counts.values())
    if total == 0:
        return {"error": "NO_VALID_LITHOLOGY_SAMPLES"}

    dominant = max(litho_counts, key=litho_counts.get)

    return {
        "dominant_lithology": dominant,
        "lithology_fractions": {k: round(v / total, 3) for k, v in litho_counts.items()},
        "n_samples": n,
        "depth_range_m": [float(depth[0]), float(depth[-1])],
        "claim_state": "DERIVED_CANDIDATE",
        "risk": "RHOB-NPHI lithology classification requires core calibration for confirmation",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SOVEREIGN 13 IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

def _safe_reduction(func, arr, default=None):
    """Safely apply a numpy reduction, returning default if array is empty."""
    import numpy as np
    if arr is None or (isinstance(arr, np.ndarray) and arr.size == 0):
        return default
    try:
        res = func(arr)
        if np.isnan(res):
            return default
        return float(res)
    except:
        return default


def _get_well_data_with_depth(
    artifact_ref: str,
    zone_top: Optional[float] = None,
    zone_base: Optional[float] = None,
) -> dict:
    """Helper to load LAS curves and apply depth filtering."""
    import os
    import numpy as np
    from geox.core.geox_1d import process_las_file

    entry = _get_artifact(artifact_ref)
    if not entry or not entry.get("las_path"):
        return {"error": "NO_LAS_PATH"}

    las_path = entry["las_path"]
    if not os.path.exists(las_path):
        return {"error": "LAS_FILE_MISSING"}

    curves = process_las_file(las_path)
    if "ERROR" in curves:
        return {"error": "LAS_PARSE_FAILED", "detail": str(curves["ERROR"][0])}

    # Identify depth curve
    depth = None
    depth_mnemonic = None
    for dk in ["DEPT", "DEPTH", "MD", "DEPTH_MD"]:
        if dk in curves:
            depth = curves[dk]
            depth_mnemonic = dk
            break

    if depth is None:
        return {"error": "DEPTH_CURVE_NOT_FOUND"}

    # Filter by zone if requested
    mask = np.ones(len(depth), dtype=bool)
    if zone_top is not None:
        mask &= (depth >= zone_top)
    if zone_base is not None:
        mask &= (depth <= zone_base)

    if not np.any(mask):
        return {"error": "NO_SAMPLES_IN_ZONE", "depth_range": [float(depth[0]), float(depth[-1])]}

    filtered_curves = {k: v[mask] for k, v in curves.items()}
    return {
        "curves": filtered_curves,
        "depth": depth[mask],
        "depth_mnemonic": depth_mnemonic,
        "mask": mask,
    }


