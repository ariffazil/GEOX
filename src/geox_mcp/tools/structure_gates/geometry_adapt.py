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


def adapt_fault(fault: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize one fault: fault_id + points (+ keep sticks for audit)."""
    if not isinstance(fault, dict):
        return fault
    out = dict(fault)

    # A4: name → fault_id
    if out.get("fault_id") is None:
        for k in ("id", "name", "label", "fault_name", "fid"):
            if out.get(k) is not None and str(out[k]).strip():
                out["fault_id"] = str(out[k]).strip()
                break
    if out.get("fault_id") is None:
        out["fault_id"] = "unknown"

    pts = sticks_or_picks_to_points(out)
    if pts:
        out["points"] = pts
        # keep sticks if they were the source (provenance)
        if out.get("sticks") is None and out.get("picks") is not None:
            out["sticks"] = out.get("picks")

    return out


def adapt_horizon(horizon: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize one horizon: horizon_id + points."""
    if not isinstance(horizon, dict):
        return horizon
    out = dict(horizon)

    if out.get("horizon_id") is None:
        for k in ("id", "name", "label", "horizon_name", "hid"):
            if out.get(k) is not None and str(out[k]).strip():
                out["horizon_id"] = str(out[k]).strip()
                break
    if out.get("horizon_id") is None:
        out["horizon_id"] = "unknown"

    pts = sticks_or_picks_to_points(out)
    if pts:
        out["points"] = pts

    return out


def adapt_framework_geometry(framework: dict[str, Any] | None) -> dict[str, Any]:
    """Deep-copy framework; adapt all faults and horizons to canonical geometry."""
    if not framework:
        return {}
    fw = deepcopy(framework)
    faults = fw.get("faults")
    if isinstance(faults, list):
        fw["faults"] = [adapt_fault(f) if isinstance(f, dict) else f for f in faults]
    horizons = fw.get("horizons")
    if isinstance(horizons, list):
        fw["horizons"] = [adapt_horizon(h) if isinstance(h, dict) else h for h in horizons]
    for nest_key in ("structural_framework", "framework", "geometry"):
        nested = fw.get(nest_key)
        if isinstance(nested, dict):
            if isinstance(nested.get("faults"), list):
                nested["faults"] = [adapt_fault(f) if isinstance(f, dict) else f for f in nested["faults"]]
            if isinstance(nested.get("horizons"), list):
                nested["horizons"] = [adapt_horizon(h) if isinstance(h, dict) else h for h in nested["horizons"]]
    return fw
