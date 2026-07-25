"""Canonical geometry adapters for structural gates.

Chat / interpret payloads often use:
  faults:  {name, sticks:[{cmp,twt_ms}], …}
  horizons:{name, picks:[{cmp,twt_ms}], …}

Gates consume:
  fault_id + points/polyline_xy
  horizon_id + points

This module is the single adapter surface. No silent drop of name/sticks/picks.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _as_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _point_from_item(p: Any, index: int = 0) -> tuple[float, float] | None:
    """Map many stick/pick shapes → (x=cmp/trace, y=twt_ms/depth)."""
    if isinstance(p, (list, tuple)) and len(p) >= 2:
        x, y = _as_float(p[0]), _as_float(p[1])
        if x is not None and y is not None:
            return (x, y)
        return None
    if not isinstance(p, dict):
        return None
    x = None
    for k in ("cmp", "cdp", "x", "trace", "trace_index", "inline", "station", "s"):
        if k in p and p[k] is not None:
            x = _as_float(p[k])
            break
    if x is None:
        x = float(index)
    y = None
    for k in ("twt_ms", "twt", "y", "depth_m", "depth", "z", "sample", "time_ms"):
        if k in p and p[k] is not None:
            y = _as_float(p[k])
            break
    if y is None:
        return None
    return (x, y)


def sticks_or_picks_to_points(obj: dict[str, Any]) -> list[dict[str, float]] | None:
    """Extract polyline points from sticks / picks / points / polyline_xy / polyline."""
    if not isinstance(obj, dict):
        return None

    # Already canonical
    raw = (
        obj.get("points")
        or obj.get("pts")
        or obj.get("sticks")
        or obj.get("picks")
        or obj.get("polyline")
        or obj.get("polyline_xy")
        or obj.get("trace")
        or obj.get("geometry")
    )
    if isinstance(raw, dict):
        # nested GeoJSON-ish
        raw = raw.get("coordinates") or raw.get("points") or raw.get("sticks") or raw.get("picks")
    if not isinstance(raw, (list, tuple)) or not raw:
        return None

    out: list[dict[str, float]] = []
    for i, item in enumerate(raw):
        xy = _point_from_item(item, i)
        if xy is None:
            continue
        out.append({"x": xy[0], "y": xy[1], "cmp": xy[0], "twt_ms": xy[1]})
    return out if len(out) >= 2 else (out if out else None)


def adapt_fault(fault: dict[str, Any], *, reject_anonymous: bool = True) -> dict[str, Any]:
    """Canonicalize one fault: fault_id + points (+ keep sticks for audit).

    P1: anonymous geometry is rejected (ANONYMOUS_GEOMETRY), not defaulted to "unknown".
    """
    if not isinstance(fault, dict):
        return fault
    out = dict(fault)

    # A4 / P1: name → fault_id (mandatory identity)
    if out.get("fault_id") is None:
        for k in ("id", "name", "label", "fault_name", "fid"):
            if out.get(k) is not None and str(out[k]).strip() and str(out[k]).strip().lower() != "unknown":
                out["fault_id"] = str(out[k]).strip()
                break
    if out.get("fault_id") is None or str(out.get("fault_id")).strip().lower() == "unknown":
        # If fault carries geometric keys (max_displacement, length, throw_profile, dip),
        # auto-generate an ID rather than silently rejecting — silent drop blocks K-DIP/K-THROW.
        _has_geom = any(
            out.get(k) is not None
            for k in (
                "max_displacement",
                "length",
                "throw_profile",
                "dip_deg",
                "dip_deg_subsurface",
                "dip_deg_image",
                "dmax_m",
                "Dmax",
                "length_m",
                "L_m",
                "L",
            )
        )
        if _has_geom:
            import hashlib, json as _json

            _stable = _json.dumps({k: out.get(k) for k in sorted(out) if out.get(k) is not None}, sort_keys=True, default=str)
            out["fault_id"] = f"auto-{hashlib.sha256(_stable.encode()).hexdigest()[:8]}"
        elif reject_anonymous:
            out["_reject"] = "ANONYMOUS_GEOMETRY"
            out["_reject_message"] = "Fault requires fault_id or name and has no geometric keys — anonymous geometry refused"
            out.pop("fault_id", None)
        else:
            out["fault_id"] = "unknown"

    pts = sticks_or_picks_to_points(out)
    if pts:
        out["points"] = pts
        # keep sticks if they were the source (provenance)
        if out.get("sticks") is None and out.get("picks") is not None:
            out["sticks"] = out.get("picks")

    return out


def adapt_horizon(horizon: dict[str, Any], *, reject_anonymous: bool = True) -> dict[str, Any]:
    """Canonicalize one horizon: horizon_id + points."""
    if not isinstance(horizon, dict):
        return horizon
    out = dict(horizon)

    if out.get("horizon_id") is None:
        for k in ("id", "name", "label", "horizon_name", "hid"):
            if out.get(k) is not None and str(out[k]).strip() and str(out[k]).strip().lower() != "unknown":
                out["horizon_id"] = str(out[k]).strip()
                break
    if out.get("horizon_id") is None or str(out.get("horizon_id")).strip().lower() == "unknown":
        if reject_anonymous:
            out["_reject"] = "ANONYMOUS_GEOMETRY"
            out["_reject_message"] = "Horizon requires horizon_id or name — anonymous geometry refused"
            out.pop("horizon_id", None)
        else:
            out["horizon_id"] = "unknown"

    pts = sticks_or_picks_to_points(out)
    if pts:
        out["points"] = pts

    return out


def adapt_framework_geometry(framework: dict[str, Any] | None) -> dict[str, Any]:
    """Deep-copy framework; adapt all faults and horizons to canonical geometry.

    Rejected anonymous objects are moved to framework['_rejected'] and excluded
    from faults/horizons lists so gates never see fault_id='unknown' defaults.
    """
    if not framework:
        return {}
    fw = deepcopy(framework)
    rejected: list[dict[str, Any]] = list(fw.get("_rejected") or [])

    def _filter_list(items: list[Any], kind: str) -> list[Any]:
        out: list[Any] = []
        for raw in items:
            if not isinstance(raw, dict):
                out.append(raw)
                continue
            adapted = adapt_fault(raw) if kind == "fault" else adapt_horizon(raw)
            if adapted.get("_reject"):
                rejected.append(
                    {
                        "kind": kind,
                        "error": adapted["_reject"],
                        "message": adapted.get("_reject_message"),
                        "raw_keys": list(raw.keys()),
                    }
                )
                continue
            out.append(adapted)
        return out

    faults = fw.get("faults")
    if isinstance(faults, list):
        fw["faults"] = _filter_list(faults, "fault")
    horizons = fw.get("horizons")
    if isinstance(horizons, list):
        fw["horizons"] = _filter_list(horizons, "horizon")
    for nest_key in ("structural_framework", "framework", "geometry"):
        nested = fw.get(nest_key)
        if isinstance(nested, dict):
            if isinstance(nested.get("faults"), list):
                nested["faults"] = _filter_list(nested["faults"], "fault")
            if isinstance(nested.get("horizons"), list):
                nested["horizons"] = _filter_list(nested["horizons"], "horizon")
    if rejected:
        fw["_rejected"] = rejected
    return fw
