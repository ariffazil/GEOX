"""Fault field alias normalization for structural gates.

Input contracts and demo payloads often use metric-suffixed keys
(dmax_m, length_m, throw_profile_m). Gates historically read canonical
names (max_displacement, length, throw_profile). Without aliasing,
K-DL/K-THROW return UNMEASURED and never falsify — fail-safe but blind.

Normalize once before the gate matrix so kill math can fire.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Canonical ← accepted aliases (first non-None wins; order is preference)
_D_KEYS = (
    "max_displacement",
    "max_displacement_m",
    "max_throw",
    "max_throw_m",
    "dmax_m",
    "dmax",
    "Dmax",
    "D_max",
    "d_max",
    "displacement_max",
    "throw_max_m",
    "throw_max",
    "Dmax_m",
)

_L_KEYS = (
    "length",
    "length_m",
    "length_px",
    "L_m",
    "fault_length_m",
    "trace_length_m",
    "trace_length",
    "L",
)

_PROFILE_KEYS = (
    "throw_profile",
    "throw_profile_m",
    "throw_profile_ms",
    "throw_m_profile",
    "displacement_profile",
    "throw_samples",
    "throw_profile_values",
)


def _first(d: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def normalize_fault(fault: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow-copied fault with canonical gate fields filled from aliases."""
    if not isinstance(fault, dict):
        return fault
    out = dict(fault)

    d = _first(out, _D_KEYS)
    if d is not None and out.get("max_displacement") is None:
        try:
            out["max_displacement"] = float(d)
        except (TypeError, ValueError):
            out["max_displacement"] = d

    length = _first(out, _L_KEYS)
    if length is not None and out.get("length") is None:
        try:
            out["length"] = float(length)
        except (TypeError, ValueError):
            out["length"] = length
    # Keep length_m for callers that only look there
    if out.get("length") is not None and out.get("length_m") is None:
        out["length_m"] = out["length"]

    prof = _first(out, _PROFILE_KEYS)
    if prof is not None and out.get("throw_profile") is None:
        out["throw_profile"] = prof

    # id aliases
    if out.get("fault_id") is None and out.get("id") is not None:
        out["fault_id"] = out["id"]

    return out


def normalize_framework(framework: dict[str, Any] | None) -> dict[str, Any]:
    """Deep-copy framework and normalize every fault entry (and nested variants)."""
    if not framework:
        return {}
    fw = deepcopy(framework)
    faults = fw.get("faults")
    if isinstance(faults, list):
        fw["faults"] = [normalize_fault(f) if isinstance(f, dict) else f for f in faults]
    # Some payloads nest under structural_framework / framework
    for nest_key in ("structural_framework", "framework", "geometry"):
        nested = fw.get(nest_key)
        if isinstance(nested, dict) and isinstance(nested.get("faults"), list):
            nested["faults"] = [
                normalize_fault(f) if isinstance(f, dict) else f for f in nested["faults"]
            ]
    return fw
