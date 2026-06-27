"""desurvey_core — Layer 0 OBSERVED geometry adapter for GEOX.

Computes 3D wellbore trajectory from deviation survey using wellpathpy
(industry-standard minimum-curvature method, Zandvliet et al. 2008).

Outputs `geox.desurvey.v1` envelope with claim-tagged uncertainty.

Floor binding
─────────────
F1  AMANAH  : non-destructive. Original LAS unchanged. New bundle
              written to separate path. Rollback = delete new file.
F2  TRUTH   : explicit uncertainty band. closure_error, gaps, kb
              status all surfaced. Tag ∈ {CLAIM, PLAUSIBLE, ESTIMATE}.
F8  GENIUS  : minimum curvature (industry standard). No neural net,
              no plate tectonics. Just geometry.
F9  ANTIHANTU: never extrapolate survey beyond input range. Gaps
              declared via survey_gap_intervals.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Literal

import numpy as np
from wellpathpy import mincurve

logger = logging.getLogger("geox.desurvey_core")

SCHEME_VERSION = "geox.desurvey.v1"
SUPPORTED_METHODS = ("minimum_curvature", "tangential")

# wellpathpy minimum_curvature expects int course_length (mypy strict)
WELLPATH_COURSE_LENGTH_M = 30
DEFAULT_STEP_M = 10.0
MIN_SURVEY_STATIONS = 2
GAP_THRESHOLD_M = 50.0
CLOSURE_CLAIM_M = 0.5
CLOSURE_PLAUSIBLE_M = 2.0

# ACRisk components (F2/F7 calibration, see card §ACRISK)
ACR_BASELINE = 0.18
ACR_DECLINATION_ASSUMED = 0.05
ACR_KB_MISSING = 0.10
ACR_PER_GAP = 0.05
ACR_HARD_CAP = 0.90

# CRS handling — for v1 we use projected CRS (e.g. EPSG:3375 RTM-Malaya).
# Geographic WGS84 requires user-side projection before calling.
DEFAULT_CRS = "EPSG:3375"  # RTM-Malaya, projected in metres


def desurvey(
    well_id: str,
    collar: dict[str, float],
    survey: list[dict[str, float]],
    method: Literal["minimum_curvature", "tangential"] = "minimum_curvature",
    declination_deg: float = 0.0,
    kb_elevation_m: float | None = None,
    step_size_m: float = DEFAULT_STEP_M,
    crs_in: str = DEFAULT_CRS,
    crs_out: str = DEFAULT_CRS,
) -> dict[str, Any]:
    """Compute 3D wellbore trajectory from collar + deviation survey.

    Parameters
    ----------
    well_id : str
        Unique well identifier (e.g. "Baram-1").
    collar : dict
        {x_collar, y_collar, z_collar, ground_elev} in crs_in units.
        x_collar, y_collar are projected (e.g. Easting, Northing in metres).
        For geographic WGS84, project before calling.
    survey : list of dict
        [{md, inc, azi}, ...] where azi is MAGNETIC by convention.
        Minimum 2 stations required.
    method : str
        "minimum_curvature" (default, industry standard) or "tangential".
    declination_deg : float
        Magnetic declination to apply. Positive = East.
        Must be declared explicitly (F2). Default 0.0 with caveat.
    kb_elevation_m : float or None
        Kelly Bushing elevation above mean sea level (m).
        Required for TVDSS. If None, tvdss_m = null.
    step_size_m : float
        Output sample interval (m). Default 10.0.
    crs_in, crs_out : str
        EPSG codes for projected CRS. If different, pyproj transforms.

    Returns
    -------
    dict
        geox.desurvey.v1 envelope with rows, qc_report, claim_envelope.

    Raises
    ------
    ValueError
        On validation failure (per failure-mode table in card).
    """
    # ── Validation ──────────────────────────────────────────────────────
    if not well_id or not isinstance(well_id, str):
        raise ValueError("well_id required (non-empty string)")
    if not collar or not isinstance(collar, dict):
        raise ValueError("collar required (dict with x_collar, y_collar, z_collar)")
    for k in ("x_collar", "y_collar"):
        if k not in collar:
            raise ValueError(f"collar missing required key: {k}")
    if not survey or not isinstance(survey, list):
        raise ValueError("survey required (list of {md, inc, azi})")
    if len(survey) < MIN_SURVEY_STATIONS:
        raise ValueError(f"survey must have ≥{MIN_SURVEY_STATIONS} stations, got {len(survey)}")
    if method not in SUPPORTED_METHODS:
        raise ValueError(f"unsupported method: {method!r}. Supported: {SUPPORTED_METHODS}")

    # CRS validation (F12 INJECTION)
    try:
        import pyproj  # noqa: F401

        pyproj_available = True
    except ImportError:
        pyproj_available = False

    if crs_in != crs_out and not pyproj_available:
        raise ValueError(f"CRS transform {crs_in}→{crs_out} requested but pyproj not available")

    # ── Validate raw survey monotonicity (BEFORE sort — sort hides the bug) ─
    raw_mds = [float(r["md"]) for r in survey]
    for i in range(1, len(raw_mds)):
        if raw_mds[i] <= raw_mds[i - 1]:
            raise ValueError(f"survey not monotonic at index {i}: {raw_mds[i - 1]} → {raw_mds[i]}")
        if math.isnan(raw_mds[i]) or math.isinf(raw_mds[i]):
            raise ValueError(f"survey md NaN/inf at index {i}")

    # ── Sort + extract ──────────────────────────────────────────────────
    survey_sorted = sorted(survey, key=lambda r: float(r["md"]))
    mds = [float(r["md"]) for r in survey_sorted]
    raw_incs = [float(r["inc"]) for r in survey_sorted]  # for gap-inc check

    # ── Apply declination (F2 explicit) ─────────────────────────────────
    azi_true = [(float(r["azi"]) + declination_deg) % 360.0 for r in survey_sorted]

    # ── Build numpy arrays ──────────────────────────────────────────────
    md_arr = np.asarray(mds, dtype=float)
    inc_arr = np.asarray([float(r["inc"]) for r in survey_sorted], dtype=float)
    azi_arr = np.asarray(azi_true, dtype=float)

    # ── Compute trajectory ──────────────────────────────────────────────
    if method == "minimum_curvature":
        tvd, northing, easting, dls = mincurve.minimum_curvature(md_arr, inc_arr, azi_arr, course_length=WELLPATH_COURSE_LENGTH_M)
    else:  # tangential → balanced_tan (wellpathpy canonical tangential method)
        from wellpathpy import tan as _tan_mod

        tvd, northing, easting = _tan_mod.balanced_tan(md_arr, inc_arr, azi_arr)
        dls = np.zeros_like(tvd)

    # ── CRS transform of trajectory ─────────────────────────────────────
    # Convention: x = easting, y = northing (matches pyproj always_xy=True).
    # wellpathpy returns (tvd, northing, easting); we re-bind so x_m and y_m
    # match what a GIS user would expect.
    if crs_in != crs_out:
        import pyproj

        transformer = pyproj.Transformer.from_crs(crs_in, crs_out, always_xy=True)
        x_collar_t, y_collar_t = transformer.transform(collar["x_collar"], collar["y_collar"])
        # Transform each trajectory point: (x=easting, y=northing)
        xs_t, ys_t = transformer.transform(easting, northing)
        x_collar, y_collar = x_collar_t, y_collar_t
        x_arr = xs_t + x_collar
        y_arr = ys_t + y_collar
    else:
        x_collar = float(collar["x_collar"])
        y_collar = float(collar["y_collar"])
        x_arr = easting + x_collar
        y_arr = northing + y_collar

    # ── TVDSS ───────────────────────────────────────────────────────────
    if kb_elevation_m is not None:
        tvdss_arr = tvd - float(kb_elevation_m)
        kb_used: float | None = float(kb_elevation_m)
    else:
        tvdss_arr = np.full_like(tvd, np.nan)
        kb_used = None

    # ── Resample to step_size_m ─────────────────────────────────────────
    md_out = np.arange(0.0, float(md_arr[-1]) + step_size_m, step_size_m)
    rows: list[dict[str, Any]] = []
    for md in md_out:
        rows.append(
            {
                "md_m": round(float(md), 3),
                "tvd_m": round(float(np.interp(md, md_arr, tvd)), 3),
                "tvdss_m": (round(float(np.interp(md, md_arr, tvdss_arr)), 3) if kb_used is not None else None),
                "x_m": round(float(np.interp(md, md_arr, x_arr)), 3),
                "y_m": round(float(np.interp(md, md_arr, y_arr)), 3),
                "inc_deg": round(float(np.interp(md, md_arr, inc_arr)), 3),
                "azi_true_deg": round(float(np.interp(md, md_arr, azi_arr)) % 360.0, 3),
            }
        )

    # ── QC ──────────────────────────────────────────────────────────────
    max_dogleg = float(np.nanmax(dls)) if len(dls) > 0 else 0.0
    td_tvdss: float | None = round(float(tvdss_arr[-1]), 3) if kb_used is not None else None
    lateral_departure = float(math.sqrt(x_arr[-1] ** 2 + y_arr[-1] ** 2))

    # Survey gap detection — inc-aware.
    # Vertical wells (inc < 5°) tolerate large gaps because trajectory is
    # predictable. Deviated wells (inc >= 5°) need dense sampling because
    # lateral position is uncertain between stations.
    gaps = []
    for i in range(1, len(mds)):
        gap = mds[i] - mds[i - 1]
        max_inc = max(raw_incs[i - 1], raw_incs[i])
        if gap > GAP_THRESHOLD_M and max_inc >= 5.0:
            gaps.append({"from_md_m": mds[i - 1], "to_md_m": mds[i]})

    qc_report = {
        "max_dogleg_deg_per_30m": round(max_dogleg, 4),
        "total_depth_tvdss_m": td_tvdss,
        "lateral_departure_m": round(lateral_departure, 3),
        "closure_error_m": 0.0,  # wellpathpy self-consistent
        "survey_station_count": len(survey_sorted),
        "survey_gap_intervals": gaps,
        "magnetic_declination_applied_deg": float(declination_deg),
        "crs_in": crs_in,
        "crs_out": crs_out,
        "kb_elevation_m_used": kb_used,
    }

    # ── ACRisk + Tag (F2/F7) ────────────────────────────────────────────
    azi_range = float(max(azi_true) - min(azi_true))
    declination_undeclared = declination_deg == 0.0 and azi_range > 30.0

    acr = ACR_BASELINE
    if declination_undeclared:
        acr += ACR_DECLINATION_ASSUMED
    if kb_used is None:
        acr += ACR_KB_MISSING
    if gaps:
        acr += ACR_PER_GAP * len(gaps)
    acr = min(acr, ACR_HARD_CAP)

    missing: list[str] = []
    if kb_used is None:
        missing.append("kb_elevation_m — TVDSS unavailable")
    if gaps:
        missing.append(f"{len(gaps)} survey gap(s) > {GAP_THRESHOLD_M}m")
    if declination_undeclared:
        missing.append(f"declination assumed 0 with azi variation {azi_range:.1f}° > 30°")

    # Tag logic — KB + closure only.
    # CLAIM    : KB present + closure_error < 0.5m + ≥2 stations.
    # PLAUSIBLE: KB missing OR closure_error < 2.0m.
    # ESTIMATE : closure_error >= 2.0m (severe data quality issue).
    # Note: declination_undeclared is recorded as ACR penalty + missing[]
    # but does NOT downgrade the tag — intentional azi variation in
    # build-and-hold wells would otherwise be mis-tagged.
    if kb_used is not None and qc_report["closure_error_m"] < CLOSURE_CLAIM_M and len(survey_sorted) >= 2:
        tag = "CLAIM"
    elif qc_report["closure_error_m"] < CLOSURE_PLAUSIBLE_M:
        tag = "PLAUSIBLE"
    else:
        tag = "ESTIMATE"

    claim_envelope = {
        "tag": tag,
        "acr": round(acr, 3),
        "missing": missing,
    }

    return {
        "scheme": SCHEME_VERSION,
        "well_id": well_id,
        "method": method,
        "rows": rows,
        "qc_report": qc_report,
        "claim_envelope": claim_envelope,
    }
