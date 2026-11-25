"""Depth-domain admission and the coupled sensitivity grid.

Uncalibrated time-domain picks are refused for metric balancing. A depth
section still needs an explicit velocity realization and a lateral pick bound.
"""

from __future__ import annotations

from copy import deepcopy

DEPTH_UNITS = {"m", "metre", "metres", "meter", "meters"}
TIME_UNITS = {"ms", "twt", "s_twt", "twt_ms", "s"}
MAX_CELLS = 256


def domain_precheck(payload: dict) -> tuple[str, list[str]]:
    """Return ('OK', []) or ('BLOCKED', reasons). Missing velocity is blocked."""
    reasons: list[str] = []
    domain = str(payload.get("domain", "")).lower()
    z_unit = str(payload.get("z_unit", "")).lower()
    if domain != "depth" or z_unit not in DEPTH_UNITS:
        if domain == "time" or z_unit in TIME_UNITS:
            reasons.append("time_domain_rejected_for_metric_balance")
        elif z_unit not in DEPTH_UNITS:
            reasons.append("z_unit_not_metres")
        else:
            reasons.append("domain_not_depth")
        return "BLOCKED", reasons
    realizations = payload.get("velocity_realizations")
    if not isinstance(realizations, list) or len(realizations) == 0:
        return "BLOCKED", ["velocity_realizations_missing"]
    for item in realizations:
        if not isinstance(item, dict) or not item.get("id"):
            return "BLOCKED", ["velocity_realization_id_missing"]
        if "depth_scale" not in item:
            return "BLOCKED", ["depth_scale_missing"]
        try:
            float(item["depth_scale"])
        except (TypeError, ValueError):
            return "BLOCKED", ["depth_scale_not_numeric"]
    if payload.get("lateral_uncertainty_m") is None and "lateral_uncertainty_m" not in (
        payload.get("sensitivity") or {}
    ):
        return "BLOCKED", ["lateral_uncertainty_m_missing"]
    lateral = payload.get("lateral_uncertainty_m")
    if lateral is not None:
        try:
            if float(lateral) < 0:
                return "BLOCKED", ["lateral_uncertainty_negative"]
        except (TypeError, ValueError):
            return "BLOCKED", ["lateral_uncertainty_not_numeric"]
    return "OK", reasons


def grid_axes(payload: dict) -> tuple[list[float], list[float | None], list[float | None], list[float | None]] | str:
    """Depth scale, paleoslope, out-of-plane shale, lateral uncertainty.

    A string return is a block reason. Paleoslope is not defaulted to zero.
    """
    sensitivity = payload.get("sensitivity") or {}
    if not isinstance(sensitivity, dict):
        return "sensitivity_not_object"
    if "depth_scales" in sensitivity:
        scales = [float(value) for value in sensitivity["depth_scales"]]
    else:
        scales = [float(item["depth_scale"]) for item in payload["velocity_realizations"]]
    if "paleoslopes" in sensitivity:
        slopes: list[float | None] = [None if value is None else float(value) for value in sensitivity["paleoslopes"]]
    else:
        raw_slope = payload.get("paleoslope")
        slopes = [None if raw_slope is None else float(raw_slope)]
    shale = payload.get("mobile_shale") if isinstance(payload.get("mobile_shale"), dict) else {}
    if "mobile_shale_out_of_plane_m2" in sensitivity:
        shale_out: list[float | None] = [
            None if value is None else float(value) for value in sensitivity["mobile_shale_out_of_plane_m2"]
        ]
    else:
        raw_out = shale.get("out_of_plane_m2") if isinstance(shale, dict) else None
        shale_out = [None if raw_out is None else float(raw_out)]
    if "lateral_uncertainty_m" in sensitivity:
        laterals: list[float | None] = [
            None if value is None else float(value) for value in sensitivity["lateral_uncertainty_m"]
        ]
    else:
        raw_lateral = payload.get("lateral_uncertainty_m")
        laterals = [None if raw_lateral is None else float(raw_lateral)]
    count = len(scales) * len(slopes) * len(shale_out) * len(laterals)
    if count > MAX_CELLS or count == 0:
        return "sensitivity_grid_too_large" if count > MAX_CELLS else "sensitivity_grid_empty"
    return scales, slopes, shale_out, laterals


def scaled_section(payload: dict, depth_scale: float, paleoslope: float | None, shale_out: float | None, lateral: float | None) -> dict:
    """Copy the section. Depth scale multiplies vertical measures only."""
    section = deepcopy(payload)
    section.pop("sensitivity", None)
    section.pop("base_fixture", None)
    section["paleoslope"] = paleoslope
    section["lateral_uncertainty_m"] = lateral
    if section.get("datum_z0_m") is not None:
        section["datum_z0_m"] = float(section["datum_z0_m"]) * depth_scale
    fault = section.get("fault")
    if isinstance(fault, dict) and fault.get("throw_m") is not None:
        fault["throw_m"] = float(fault["throw_m"]) * depth_scale
    intervals = []
    for interval in section.get("intervals") or []:
        copied = dict(interval)
        for key in ("fw_thickness_m", "hw_thickness_m"):
            if copied.get(key) is not None:
                copied[key] = float(copied[key]) * depth_scale
        intervals.append(copied)
    section["intervals"] = intervals
    shale = dict(section.get("mobile_shale") or {})
    if shale_out is not None or "out_of_plane_m2" in shale or "mobile_shale" in payload:
        shale["out_of_plane_m2"] = shale_out
    if "in_plane_m2" not in shale and isinstance(payload.get("mobile_shale"), dict):
        shale["in_plane_m2"] = payload["mobile_shale"].get("in_plane_m2")
    section["mobile_shale"] = shale
    section["_depth_scale"] = depth_scale
    return section
