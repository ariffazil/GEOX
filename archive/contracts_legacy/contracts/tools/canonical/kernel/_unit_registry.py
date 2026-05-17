from __future__ import annotations

from typing import Any


CURVE_BOUNDS: dict[str, dict[str, Any]] = {
    "GR": {"unit": "gAPI", "min": 0.0, "max": 300.0, "null": -999.25},
    "RHOB": {"unit": "g/cc", "min": 1.0, "max": 3.0, "null": -999.25},
    "NPHI": {"unit": "v/v", "min": -0.05, "max": 0.60, "null": -999.25},
    "DT": {"unit": "us/ft", "min": 40.0, "max": 200.0, "null": -999.25},
    "RT": {"unit": "ohm.m", "min": 0.01, "max": 100000.0, "null": -999.25},
    "CALI": {"unit": "in", "min": 4.0, "max": 20.0, "null": -999.25},
    "SP": {"unit": "mV", "min": -200.0, "max": 200.0, "null": -999.25},
    "PE": {"unit": "b/e", "min": 1.0, "max": 6.0, "null": -999.25},
    "VP": {"unit": "m/s", "min": 1500.0, "max": 7000.0, "null": None},
    "VS": {"unit": "m/s", "min": 500.0, "max": 4000.0, "null": None},
    "PHI": {"unit": "v/v", "min": 0.0, "max": 0.45, "null": None},
    "SW": {"unit": "v/v", "min": 0.0, "max": 1.0, "null": None},
    "SO": {"unit": "v/v", "min": 0.0, "max": 1.0, "null": None},
    "SG": {"unit": "v/v", "min": 0.0, "max": 1.0, "null": None},
    "VSH": {"unit": "v/v", "min": 0.0, "max": 1.0, "null": None},
    "K": {"unit": "mD", "min": 0.0, "max": 10000.0, "null": None},
}

RATLAS_REF = "RATLAS:Atlas_of_Log_Responses:bounded-log-physics-v2026.05.14"


def bounds_for(name: str) -> dict[str, Any]:
    key = str(name or "").upper()
    return dict(CURVE_BOUNDS[key])


def finite_non_null(values: Any, name: str) -> Any:
    import numpy as np

    bounds = bounds_for(name)
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    null_value = bounds.get("null")
    if null_value is not None:
        arr = arr[arr != float(null_value)]
    return arr


def validate_curve(values: Any, name: str, *, allow_empty: bool = False) -> dict[str, Any]:
    import numpy as np

    bounds = bounds_for(name)
    arr = finite_non_null(values, name)
    violations: list[str] = []
    if arr.size == 0:
        if not allow_empty:
            violations.append(f"{name.upper()}_NO_VALID_SAMPLES")
        return {
            "guard_passed": not violations,
            "curve": name.upper(),
            "unit": bounds["unit"],
            "n_valid": int(arr.size),
            "violations": violations,
        }

    lo = bounds.get("min")
    hi = bounds.get("max")
    if lo is not None and float(np.nanmin(arr)) < float(lo):
        violations.append(f"{name.upper()}_BELOW_MIN")
    if hi is not None and float(np.nanmax(arr)) > float(hi):
        violations.append(f"{name.upper()}_ABOVE_MAX")
    return {
        "guard_passed": not violations,
        "curve": name.upper(),
        "unit": bounds["unit"],
        "n_valid": int(arr.size),
        "min": float(np.nanmin(arr)),
        "max": float(np.nanmax(arr)),
        "bounds": {"min": lo, "max": hi},
        "violations": violations,
    }


def validate_scalar(value: float, name: str) -> dict[str, Any]:
    return validate_curve([value], name)


def merge_guards(*guards: dict[str, Any]) -> dict[str, Any]:
    violations: list[str] = []
    checked: list[str] = []
    for guard in guards:
        if not guard:
            continue
        checked.append(str(guard.get("curve") or guard.get("name") or "UNKNOWN"))
        violations.extend(list(guard.get("violations") or []))
    return {
        "guard_passed": not violations,
        "physics_version": "geox-unit-registry-v2026.05.14",
        "checked": checked,
        "violations": violations,
    }


def value_contract(
    name: str,
    *,
    method: str,
    source_curves: list[str],
    uncertainty_band: dict[str, float | None] | None = None,
) -> dict[str, Any]:
    bounds = bounds_for(name)
    return {
        "property": name.upper(),
        "unit": bounds["unit"],
        "method": method,
        "uncertainty_band": uncertainty_band or {"p10": None, "p50": None, "p90": None},
        "source_curves": source_curves,
        "RATLAS_ref": RATLAS_REF,
        "bounds": {"min": bounds.get("min"), "max": bounds.get("max")},
    }
