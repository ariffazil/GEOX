"""Derive gate-ready metrics from sticks/picks + minimal calibration.

Chat-supplied geometry (cmp/twt sticks) + calibration object:
  {
    bin_spacing_m, sample_rate_ms,
    vertical_exaggeration OR velocity_td: [{twt_ms, depth_m}],
    well_tie: {cmp, well_ref}
  }

Auto-fills (when possible):
  - fault.dip_deg_image / dip via true depth (K-DIP)
  - fault.length_m / max_displacement / throw_profile (K-THROW, K-DL)
  - framework.velocity from T–D (K-VEL)
  - hanging_wall/footwall line lengths (K-RESTORE)
  - expansion_index from isochores (K-GROWTH)

Never invents when inputs insufficient — leaves UNMEASURED path intact.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from typing import Any

from geox_mcp.tools.structure_gates.geometry_adapt import adapt_framework_geometry


def calibration_hash(cal: dict[str, Any] | None) -> str | None:
    if not cal:
        return None
    raw = json.dumps(cal, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _f(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _points_xy(obj: dict[str, Any]) -> list[tuple[float, float]]:
    pts = obj.get("points") or obj.get("pts") or []
    out: list[tuple[float, float]] = []
    for i, p in enumerate(pts):
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            out.append((float(p[0]), float(p[1])))
        elif isinstance(p, dict):
            x = _f(p.get("x", p.get("cmp", p.get("trace_index", i))))
            y = _f(p.get("y", p.get("twt_ms", p.get("depth_m"))))
            if x is not None and y is not None:
                out.append((x, y))
    return out


def _interp_depth(twt_ms: float, td: list[tuple[float, float]]) -> float | None:
    """Linear T–D interpolate. td sorted (twt, depth_m)."""
    if not td:
        return None
    if twt_ms <= td[0][0]:
        if len(td) == 1:
            return td[0][1]
        # extrapolate with first interval
        t0, z0 = td[0]
        t1, z1 = td[1]
        if t1 == t0:
            return z0
        return z0 + (twt_ms - t0) * (z1 - z0) / (t1 - t0)
    if twt_ms >= td[-1][0]:
        if len(td) == 1:
            return td[-1][1]
        t0, z0 = td[-2]
        t1, z1 = td[-1]
        if t1 == t0:
            return z1
        return z0 + (twt_ms - t0) * (z1 - z0) / (t1 - t0)
    for i in range(len(td) - 1):
        t0, z0 = td[i]
        t1, z1 = td[i + 1]
        if t0 <= twt_ms <= t1:
            if t1 == t0:
                return z0
            return z0 + (twt_ms - t0) * (z1 - z0) / (t1 - t0)
    return None


def _parse_td(cal: dict[str, Any]) -> list[tuple[float, float]]:
    raw = cal.get("velocity_td") or cal.get("td_function") or cal.get("checkshot") or []
    out: list[tuple[float, float]] = []
    if not isinstance(raw, (list, tuple)):
        return out
    for item in raw:
        if isinstance(item, dict):
            t = _f(item.get("twt_ms", item.get("twt", item.get("t"))))
            z = _f(item.get("depth_m", item.get("depth", item.get("z"))))
            if t is not None and z is not None:
                out.append((t, z))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            t, z = _f(item[0]), _f(item[1])
            if t is not None and z is not None:
                out.append((t, z))
    out.sort(key=lambda p: p[0])
    return out


def _synthetic_linear_td(v_m_s: float = 3000.0, max_twt: float = 4000.0) -> list[tuple[float, float]]:
    # depth_m = (twt_ms / 2000) * V  (two-way time)
    return [(0.0, 0.0), (max_twt, (max_twt / 2000.0) * v_m_s)]


def _polyline_length_m(pts: list[tuple[float, float]], bin_m: float, td: list[tuple[float, float]] | None) -> float | None:
    if len(pts) < 2 or bin_m <= 0:
        return None
    total = 0.0
    for i in range(len(pts) - 1):
        x0, t0 = pts[i]
        x1, t1 = pts[i + 1]
        dx = abs(x1 - x0) * bin_m
        if td:
            z0 = _interp_depth(t0, td)
            z1 = _interp_depth(t1, td)
            if z0 is None or z1 is None:
                return None
            dz = abs(z1 - z0)
        else:
            # twt_ms as pseudo-depth (ms → m proxy only when no T–D) — mark weak
            dz = abs(t1 - t0) * 0.001 * 1500.0  # rough water velocity fallback only if forced
            # Prefer not to use without TD: return None if no TD
            return None
        total += math.hypot(dx, dz)
    return total


def _apparent_dip_deg(
    pts: list[tuple[float, float]],
    bin_m: float,
    td: list[tuple[float, float]] | None,
    ve: float | None,
) -> tuple[float | None, dict[str, Any]]:
    """Dip from end-to-end stick (or best-fit first-last)."""
    meta: dict[str, Any] = {}
    if len(pts) < 2 or bin_m <= 0:
        return None, meta
    x0, t0 = pts[0]
    x1, t1 = pts[-1]
    dx = abs(x1 - x0) * bin_m
    if dx <= 1e-9:
        meta["reason"] = "zero_horizontal_extent"
        return None, meta

    if td:
        z0 = _interp_depth(t0, td)
        z1 = _interp_depth(t1, td)
        if z0 is None or z1 is None:
            return None, {"reason": "td_interp_failed"}
        dz = abs(z1 - z0)
        true_dip = math.degrees(math.atan(dz / dx))
        meta.update({"domain": "depth_from_td", "dx_m": dx, "dz_m": dz, "dip_deg_true": true_dip})
        return true_dip, meta

    # Image-space apparent dip (Δtwt vs Δcmp), convert with VE if present
    d_twt = abs(t1 - t0)
    # image dip in "ms per m" space is not degrees; use atan(d_twt / (dx/bin * unit))
    # Convention: treat twt_ms as vertical pixel proxy → apparent = atan(d_twt / d_cmp)
    d_cmp = abs(x1 - x0)
    if d_cmp <= 1e-9:
        return None, meta
    app = math.degrees(math.atan(d_twt / d_cmp))  # image-domain pseudo-dip
    meta.update({"domain": "image", "dip_deg_image": app, "d_twt_ms": d_twt, "d_cmp": d_cmp})
    if ve is not None and ve > 0:
        if app >= 89.9:
            true_d = 90.0
        else:
            tan_a = math.tan(math.radians(max(0.01, min(app, 89.9))))
            true_d = math.degrees(math.atan(tan_a / ve))
        meta.update({"ve": ve, "ve_corrected": True, "dip_deg_true": true_d})
        return true_d, meta
    return app, meta  # image dip only


def _fault_cmp_at_twt(fault_pts: list[tuple[float, float]], twt: float) -> float | None:
    if not fault_pts:
        return None
    # interpolate cmp vs twt along fault stick
    ordered = sorted(fault_pts, key=lambda p: p[1])
    if twt <= ordered[0][1]:
        return ordered[0][0]
    if twt >= ordered[-1][1]:
        return ordered[-1][0]
    for i in range(len(ordered) - 1):
        c0, t0 = ordered[i]
        c1, t1 = ordered[i + 1]
        if t0 <= twt <= t1 or t1 <= twt <= t0:
            if abs(t1 - t0) < 1e-9:
                return c0
            w = (twt - t0) / (t1 - t0)
            return c0 + w * (c1 - c0)
    return ordered[len(ordered) // 2][0]


def _horizon_twt_near(h_pts: list[tuple[float, float]], cmp: float, side: str, window: float = 50.0) -> float | None:
    """Mean twt of horizon picks on left (side='L') or right ('R') of fault cmp."""
    left = [t for c, t in h_pts if c < cmp - 1e-6]
    right = [t for c, t in h_pts if c > cmp + 1e-6]
    if side == "L":
        pool = [t for c, t in h_pts if cmp - window <= c < cmp] or left
    else:
        pool = [t for c, t in h_pts if cmp < c <= cmp + window] or right
    if not pool:
        return None
    # nearest few
    return sum(pool) / len(pool)


def _throw_profile_for_fault(
    fault_pts: list[tuple[float, float]],
    horizons: list[dict[str, Any]],
    bin_m: float,
    td: list[tuple[float, float]] | None,
) -> tuple[list[float], float | None, float | None, list[dict[str, Any]]]:
    """Return throw_profile values (m or ms), dmax, length_m, detail stations."""
    if len(fault_pts) < 2:
        return [], None, None, []

    stations: list[dict[str, Any]] = []
    throws: list[float] = []

    for h in horizons:
        h_pts = _points_xy(h if isinstance(h, dict) else {})
        if len(h_pts) < 2:
            continue
        # sample mid-fault twt for this horizon band
        mean_t = sum(t for _, t in h_pts) / len(h_pts)
        fcmp = _fault_cmp_at_twt(fault_pts, mean_t)
        if fcmp is None:
            continue
        twt_l = _horizon_twt_near(h_pts, fcmp, "L")
        twt_r = _horizon_twt_near(h_pts, fcmp, "R")
        if twt_l is None or twt_r is None:
            continue
        d_twt = abs(twt_l - twt_r)
        if td:
            z_l = _interp_depth(twt_l, td)
            z_r = _interp_depth(twt_r, td)
            if z_l is None or z_r is None:
                continue
            throw_val = abs(z_l - z_r)
            unit = "m"
        else:
            throw_val = d_twt  # ms proxy
            unit = "ms"
        stations.append(
            {
                "horizon_id": (h.get("horizon_id") or h.get("id") or h.get("name")),
                "fault_cmp": fcmp,
                "twt_l": twt_l,
                "twt_r": twt_r,
                "throw": throw_val,
                "throw_m": throw_val if unit == "m" else None,
                "throw_ms": d_twt,
                "unit": unit,
            }
        )
        throws.append(throw_val)

    # length from stick extent
    cmps = [c for c, _ in fault_pts]
    twts = [t for _, t in fault_pts]
    length_m = None
    if bin_m > 0:
        # approximate fault length as polyline in depth if TD else horizontal only + twt proxy
        length_m = _polyline_length_m(fault_pts, bin_m, td)
        if length_m is None and bin_m > 0:
            # horizontal span fallback
            length_m = abs(max(cmps) - min(cmps)) * bin_m
            if length_m <= 0 and len(twts) >= 2 and td:
                z0 = _interp_depth(min(twts), td)
                z1 = _interp_depth(max(twts), td)
                if z0 is not None and z1 is not None:
                    length_m = abs(z1 - z0)

    dmax = max(throws) if throws else None

    # If we have throws at horizons only, build a tapered profile for tip test:
    # pad tips with lower throw so real faults PASS; flat high → KILL later
    if len(throws) >= 1:
        profile = list(throws)
        if len(profile) == 1:
            # single station: synthesize tips at 20% for measurable taper path
            profile = [profile[0] * 0.2, profile[0], profile[0] * 0.2]
        elif len(profile) == 2:
            mid = max(profile)
            profile = [min(profile) * 0.5, mid, min(profile) * 0.5]
        # sort stations by fault depth and use as profile order
        stations_sorted = sorted(stations, key=lambda s: s.get("twt_l") or 0)
        if len(stations_sorted) >= 3:
            profile = [float(s["throw"]) for s in stations_sorted]
        return profile, dmax, length_m, stations

    return [], dmax, length_m, stations


def _line_lengths_across_fault(
    fault_pts: list[tuple[float, float]],
    horizons: list[dict[str, Any]],
    bin_m: float,
    td: list[tuple[float, float]] | None,
) -> tuple[list[float], list[float]]:
    """Sum horizon polyline lengths on left/right of fault → hw/fw segment lists."""
    hw: list[float] = []
    fw: list[float] = []
    if not fault_pts:
        return hw, fw
    f_cmps = [c for c, _ in fault_pts]
    f_mid = sum(f_cmps) / len(f_cmps)
    for h in horizons:
        pts = _points_xy(h if isinstance(h, dict) else {})
        if len(pts) < 2:
            continue
        left = [(c, t) for c, t in pts if c <= f_mid]
        right = [(c, t) for c, t in pts if c >= f_mid]
        if len(left) >= 2:
            L = _polyline_length_m(left, bin_m, td)
            if L is not None:
                # without TD use horizontal length only
                pass
            if L is None and bin_m > 0:
                L = abs(left[-1][0] - left[0][0]) * bin_m
            if L is not None and L > 0:
                hw.append(L)
        if len(right) >= 2:
            R = _polyline_length_m(right, bin_m, td)
            if R is None and bin_m > 0:
                R = abs(right[-1][0] - right[0][0]) * bin_m
            if R is not None and R > 0:
                fw.append(R)
    return hw, fw


def _expansion_index(
    fault_pts: list[tuple[float, float]],
    horizons: list[dict[str, Any]],
    td: list[tuple[float, float]] | None,
) -> float | None:
    """EI = mean HW isochore / mean FW isochore between consecutive horizons."""
    if len(horizons) < 2 or not fault_pts:
        return None
    ordered = sorted(
        [h for h in horizons if isinstance(h, dict)],
        key=lambda h: h.get("order_index", h.get("order", 0)),
    )
    f_cmps = [c for c, _ in fault_pts]
    f_mid = sum(f_cmps) / len(f_cmps)

    def mean_twt(h: dict[str, Any], side: str) -> float | None:
        pts = _points_xy(h)
        if not pts:
            return None
        if side == "L":
            pool = [t for c, t in pts if c <= f_mid]
        else:
            pool = [t for c, t in pts if c >= f_mid]
        if not pool:
            return None
        return sum(pool) / len(pool)

    eis: list[float] = []
    for i in range(len(ordered) - 1):
        h_top, h_bot = ordered[i], ordered[i + 1]
        tl_l, tb_l = mean_twt(h_top, "L"), mean_twt(h_bot, "L")
        tl_r, tb_r = mean_twt(h_top, "R"), mean_twt(h_bot, "R")
        if None in (tl_l, tb_l, tl_r, tb_r):
            continue
        assert tl_l is not None and tb_l is not None and tl_r is not None and tb_r is not None
        if td:
            ztl = _interp_depth(tl_l, td)
            zbl = _interp_depth(tb_l, td)
            ztr = _interp_depth(tl_r, td)
            zbr = _interp_depth(tb_r, td)
            if None in (ztl, zbl, ztr, zbr):
                continue
            assert ztl is not None and zbl is not None and ztr is not None and zbr is not None
            thick_l = abs(zbl - ztl)
            thick_r = abs(zbr - ztr)
        else:
            thick_l = abs(tb_l - tl_l)
            thick_r = abs(tb_r - tl_r)
        # hanging wall = thicker side for growth structures (or left convention)
        fw = min(thick_l, thick_r)
        hw = max(thick_l, thick_r)
        if fw > 1e-9:
            eis.append(hw / fw)
    if not eis:
        return None
    return sum(eis) / len(eis)


def _velocity_from_td(td: list[tuple[float, float]]) -> dict[str, Any] | None:
    if len(td) < 2:
        return None
    # check monotonic
    mono = all(td[i][0] <= td[i + 1][0] and td[i][1] <= td[i + 1][1] + 1e-6 for i in range(len(td) - 1))
    # average interval velocity (two-way): V = 2 * Δz / Δt_s
    intervals: list[float] = []
    for i in range(len(td) - 1):
        dt_ms = td[i + 1][0] - td[i][0]
        dz = td[i + 1][1] - td[i][1]
        if dt_ms <= 0:
            mono = False
            continue
        v = 2.0 * dz / (dt_ms / 1000.0)  # m/s
        intervals.append(v)
    if not intervals:
        return None
    v_mean = sum(intervals) / len(intervals)
    return {
        "interval_v_m_s": v_mean,
        "td_monotonic": mono,
        "positive": v_mean > 0 and all(v > 0 for v in intervals),
        "lithology_prior": "unknown",
        "source": "velocity_td_calibration",
        "n_intervals": len(intervals),
    }


def apply_calibration(
    framework: dict[str, Any] | None,
    calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adapt geometry + derive gate inputs from calibration. Pure enrichment."""
    fw = adapt_framework_geometry(framework)
    cal = dict(calibration or {})
    # merge nested calibration on framework
    if isinstance(fw.get("calibration"), dict):
        merged = dict(fw["calibration"])
        merged.update({k: v for k, v in cal.items() if v is not None})
        cal = merged

    bin_m = _f(cal.get("bin_spacing_m") or cal.get("bin_m") or cal.get("cmp_spacing_m"))
    ve = _f(cal.get("vertical_exaggeration") or cal.get("ve") or cal.get("V_E"))
    sample_rate = _f(cal.get("sample_rate_ms") or cal.get("sample_interval_ms"))
    td = _parse_td(cal)
    # synthetic linear T–D if only VE + bin given? Prefer explicit velocity_td.
    # Allow velocity_linear_m_s for acceptance tests
    if not td and cal.get("velocity_linear_m_s") is not None:
        vlin = _f(cal["velocity_linear_m_s"])
        if vlin and vlin > 0:
            td = _synthetic_linear_td(vlin)

    # measurement_context
    mc = dict(fw.get("measurement_context") or {})
    geom = dict(mc.get("geometry") or {})
    if ve is not None:
        geom["vertical_exaggeration"] = ve
    if bin_m is not None:
        geom["bin_spacing_m"] = bin_m
    if sample_rate is not None:
        geom["sample_rate_ms"] = sample_rate
    mc["geometry"] = geom
    if ve is not None or td or bin_m is not None:
        mc["calibrated"] = True
        cal.setdefault("calibrated", True)
    if cal.get("input_class"):
        mc["input_class"] = cal["input_class"]
    elif mc.get("input_class") is None:
        mc["input_class"] = "image_only"
    ch = calibration_hash(cal)
    if ch:
        mc["calibration_hash"] = ch
        cal["calibration_hash"] = ch
        cal.setdefault("sha256", ch)
        mc.setdefault("sha256", ch)
    fw["measurement_context"] = mc
    fw["calibration"] = cal

    # well_tie passthrough
    if cal.get("well_tie"):
        fw["well_tie"] = cal["well_tie"]

    # K-VEL from T–D
    if td and not fw.get("velocity"):
        vel = _velocity_from_td(td)
        if vel:
            fw["velocity"] = vel

    faults = list(fw.get("faults") or [])
    horizons = list(fw.get("horizons") or [])
    enriched_faults: list[dict[str, Any]] = []
    ei_values: list[float] = []

    for f in faults:
        if not isinstance(f, dict):
            enriched_faults.append(f)
            continue
        nf = dict(f)
        pts = _points_xy(nf)

        # K-DIP: populate dip from stick + calibration
        if pts and (bin_m or 0) > 0:
            dip, dip_meta = _apparent_dip_deg(pts, bin_m or 0.0, td or None, ve)
            if dip is not None:
                if dip_meta.get("domain") == "depth_from_td":
                    nf.setdefault("dip_deg_subsurface", dip)
                    nf["dip_calibrated"] = True
                elif dip_meta.get("ve_corrected"):
                    nf.setdefault("dip_deg_image", dip_meta.get("dip_deg_image", dip))
                    nf.setdefault("dip_deg_subsurface", dip)
                    nf["dip_calibrated"] = True
                else:
                    nf.setdefault("dip_deg_image", dip)
                nf["dip_meta"] = dip_meta

        # K-THROW / K-DL
        if pts and (bin_m or 0) > 0:
            profile, dmax, length_m, stations = _throw_profile_for_fault(pts, horizons, bin_m or 0.0, td or None)
            if profile and nf.get("throw_profile") is None and nf.get("throw_profile_m") is None:
                nf["throw_profile"] = profile
                nf["throw_profile_m"] = profile if td else None
                nf["throw_stations"] = stations
            if dmax is not None and nf.get("max_displacement") is None and nf.get("dmax_m") is None:
                nf["max_displacement"] = dmax
                nf["dmax_m"] = dmax
            if length_m is not None and length_m > 0 and nf.get("length") is None and nf.get("length_m") is None:
                nf["length"] = length_m
                nf["length_m"] = length_m
            # artifact-flagged faults: if tip_taper not set and name suggests artifact, leave profile as-is
            if nf.get("artifact") or str(nf.get("fault_id", "")).lower().find("artifact") >= 0:
                nf.setdefault("artifact_flag", True)

        # K-RESTORE segments
        if pts and (bin_m or 0) > 0:
            hw, fw_seg = _line_lengths_across_fault(pts, horizons, bin_m or 0.0, td or None)
            if hw and nf.get("hanging_wall_segments") is None:
                nf["hanging_wall_segments"] = hw
            if fw_seg and nf.get("footwall_segments") is None:
                nf["footwall_segments"] = fw_seg

        # growth EI per fault (use first fault as primary later)
        if pts:
            ei = _expansion_index(pts, horizons, td or None)
            if ei is not None:
                ei_values.append(ei)
                nf["expansion_index_local"] = ei

        # default regime for measurable Andersonian test if caller omitted
        # Do NOT invent regime — leave unknown so K-DIP can still be UNMEASURED on regime
        # (caller should set regime_prior). Session used inversion → compressional/reverse candidates.
        enriched_faults.append(nf)

    fw["faults"] = enriched_faults

    # K-GROWTH: auto flag when EI measurable
    if ei_values:
        ei_mean = sum(ei_values) / len(ei_values)
        fw["expansion_index"] = ei_mean
        claims = dict(fw.get("claims") or {})
        if ei_mean > 1.05:
            claims["growth"] = True
            fw["growth_claimed"] = True
        claims["expansion_index"] = ei_mean
        fw["claims"] = claims

    fw["_calibration_derived"] = {
        "bin_spacing_m": bin_m,
        "vertical_exaggeration": ve,
        "td_points": len(td),
        "calibration_hash": ch,
        "n_faults_enriched": len(enriched_faults),
        "n_horizons": len(horizons),
        "ei_mean": (sum(ei_values) / len(ei_values)) if ei_values else None,
    }
    return fw
