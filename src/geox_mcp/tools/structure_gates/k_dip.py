"""K-DIP — dip vs regime prior (Andersonian conditional).

Without calibrated true dip → UNMEASURED (never guess).
With true/VE-corrected dip outside regime without exception → KILL.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

_REGIME_RANGES: dict[str, tuple[float, float]] = {
    "normal": (55.0, 70.0),
    "reverse": (20.0, 40.0),
    "thrust": (20.0, 40.0),
    "strike_slip": (75.0, 90.0),
    "strike-slip": (75.0, 90.0),
}

_EQUATION = (
    "true_dip = atan(tan(apparent_dip)/VE) when only image dip + VE; "
    "else use dip_deg_subsurface. Test true_dip ∈ regime_range."
)


def validate_k_dip(coords: Any, regime: str) -> dict[str, Any]:
    """Validates if the dip of a proposed fault plane conforms to Andersonian geomechanics.
    coords: Nx3 numpy array or list of spatial points (x, y, z) defining the fault surface.
    regime: one of 'extensional', 'compressional', 'strike_slip', 'normal', 'reverse', 'thrust'
    """
    import numpy as np

    coords_arr = np.asarray(coords, dtype=np.float64)
    if len(coords_arr) < 3:
        return {"status": "INCONCLUSIVE", "verdict": "INCONCLUSIVE", "reason": "Insufficient points for dip calculation"}

    centroid = coords_arr.mean(axis=0)
    shifted = coords_arr - centroid

    _, _, vh = np.linalg.svd(shifted)
    normal = vh[2, :]

    nz = normal[2] if len(normal) > 2 else normal[-1]
    norm_magnitude = np.linalg.norm(normal)

    if norm_magnitude == 0:
        return {"status": "REJECTED", "verdict": "KILL", "reason": "Zero-magnitude normal vector"}

    dip_rad = np.arccos(np.clip(np.abs(nz) / (norm_magnitude + 1e-9), 0.0, 1.0))
    dip_deg = float(np.degrees(dip_rad))

    if dip_deg > 90.0:
        dip_deg = 180.0 - dip_deg

    regime_clean = regime.lower().strip()
    bounds_map = {
        "extensional": (45.0, 75.0),
        "normal": (45.0, 75.0),
        "compressional": (15.0, 45.0),
        "thrust": (15.0, 45.0),
        "reverse": (15.0, 45.0),
        "strike_slip": (75.0, 90.0),
        "strike-slip": (75.0, 90.0),
    }

    min_dip, max_dip = bounds_map.get(regime_clean, (0.0, 90.0))

    if min_dip <= dip_deg <= max_dip:
        return {
            "status": "PASSED",
            "verdict": "PASS",
            "dip_calculated": float(dip_deg),
            "regime": regime,
            "bounds": [min_dip, max_dip],
        }
    else:
        return {
            "status": "REJECTED",
            "verdict": "KILL",
            "dip_calculated": float(dip_deg),
            "regime": regime,
            "bounds": [min_dip, max_dip],
            "reason": f"Calculated dip of {dip_deg:.1f} degrees violates Andersonian limits [{min_dip}, {max_dip}] for a {regime} regime.",
        }


def _ve_of(framework: dict[str, Any], fault: dict[str, Any]) -> float | None:
    for src in (fault, framework.get("measurement_context") or {}, framework.get("calibration") or {}, framework):
        if not isinstance(src, dict):
            continue
        for key in ("vertical_exaggeration", "ve", "V_E"):
            if key in src and src[key] is not None:
                try:
                    ve = float(src[key])
                    if ve > 0:
                        return ve
                except (TypeError, ValueError):
                    pass
        geom = src.get("geometry") if isinstance(src.get("geometry"), dict) else None
        if geom and geom.get("vertical_exaggeration") is not None:
            try:
                ve = float(geom["vertical_exaggeration"])
                if ve > 0:
                    return ve
            except (TypeError, ValueError):
                pass
    return None


def _is_calibrated(framework: dict[str, Any], fault: dict[str, Any]) -> bool:
    if fault.get("dip_deg_subsurface") is not None:
        return True
    if fault.get("dip_calibrated") is True or fault.get("dip_is_true") is True:
        return True
    mc = framework.get("measurement_context") or {}
    cal = framework.get("calibration") or {}
    if mc.get("calibrated") or cal.get("calibrated"):
        return True
    # VE present allows conversion of image dip → true
    if _ve_of(framework, fault) is not None:
        return True
    return False


def _true_dip(fault: dict[str, Any], framework: dict[str, Any]) -> tuple[float | None, dict[str, Any]]:
    meta: dict[str, Any] = {}
    if fault.get("dip_deg_subsurface") is not None:
        try:
            return float(fault["dip_deg_subsurface"]), {
                "domain": "subsurface",
                "ve_corrected": False,
            }
        except (TypeError, ValueError):
            pass

    apparent = None
    for key in ("dip_deg_image", "dip_deg", "dip"):
        if fault.get(key) is not None:
            try:
                apparent = float(fault[key])
                meta["source_key"] = key
                break
            except (TypeError, ValueError):
                continue
    if apparent is None:
        return None, meta

    if not _is_calibrated(framework, fault):
        meta.update({"domain": "image_uncalibrated", "unmeasured": True, "dip_deg_image": apparent})
        return None, meta  # signal UNMEASURED

    ve = _ve_of(framework, fault)
    if ve is None or abs(ve - 1.0) < 1e-9:
        # calibrated flag without VE: treat image dip as true only if explicitly calibrated
        if fault.get("dip_calibrated") or fault.get("dip_is_true") or (
            (framework.get("measurement_context") or {}).get("calibrated")
            or (framework.get("calibration") or {}).get("calibrated")
        ):
            meta.update({"domain": "calibrated_image", "ve": ve or 1.0, "ve_corrected": False})
            return apparent, meta
        meta.update({"domain": "image_uncalibrated", "unmeasured": True})
        return None, meta

    if apparent >= 89.9:
        true_dip = 90.0
    else:
        tan_a = math.tan(math.radians(max(0.01, min(apparent, 89.9))))
        true_dip = math.degrees(math.atan(tan_a / ve))
    meta.update(
        {
            "domain": "ve_corrected",
            "ve": ve,
            "ve_corrected": True,
            "dip_deg_image": apparent,
            "dip_deg_true": true_dip,
        }
    )
    return true_dip, meta


def gate_k_dip(framework: dict[str, Any]) -> dict[str, Any]:
    faults = framework.get("faults") or []
    if not faults:
        return make_gate_receipt(
            "K-DIP",
            "UNMEASURED",
            reason="No faults provided",
            equation=_EQUATION,
            inputs={"n_faults": 0},
            thresholds={"regime_ranges_deg": _REGIME_RANGES},
            calculated_result={"kills": 0, "passes": 0, "warns": 0, "unmeasured": 0},
            exceptions_considered=["reactivation_evidence", "fluid_pressure_exception"],
            evidence_refs=[
                "Anderson 1951 — The dynamics of faulting",
                "Célérier 2008 — ROG: potential for renewed slip",
                "Alcalde 2019 — VE bias in apparent dip measurements",
            ],
            gate_type="hard_conditional",
        )

    findings: list[dict[str, Any]] = []
    kills = passes = warns = unmeas = 0
    inputs_acc: list[dict[str, Any]] = []

    for f in faults:
        fid = f.get("fault_id") or f.get("id") or "unknown"
        dip, dip_meta = _true_dip(f, framework)
        regime = str(f.get("regime_prior") or f.get("regime") or "unknown").lower().strip()
        reactivation = bool(
            f.get("reactivation_evidence")
            or f.get("reactivation")
            or f.get("fluid_pressure_exception")
        )
        inputs_acc.append({"fault_id": fid, "regime": regime, "dip_meta": dip_meta})

        if dip is None:
            unmeas += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "UNMEASURED",
                    "status": "UNMEASURED",
                    "reason": (
                        "True dip unmeasured — need dip_deg_subsurface, "
                        "VE for image dip, or calibrated=true"
                    ),
                    "dip_meta": dip_meta,
                }
            )
            continue

        if regime in ("unknown", "", "none"):
            unmeas += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "UNMEASURED",
                    "status": "UNMEASURED",
                    "dip_deg": dip,
                    "reason": "regime_prior unknown",
                    "dip_meta": dip_meta,
                }
            )
            continue

        lo_hi = _REGIME_RANGES.get(regime)
        if lo_hi is None:
            unmeas += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "UNMEASURED",
                    "status": "UNMEASURED",
                    "dip_deg": dip,
                    "regime": regime,
                    "reason": f"Unrecognized regime '{regime}'",
                }
            )
            continue

        lo, hi = lo_hi
        if lo <= dip <= hi:
            passes += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "PASS",
                    "status": "PASS",
                    "dip_deg": dip,
                    "dip_meta": dip_meta,
                    "regime": regime,
                    "expected_range": [lo, hi],
                }
            )
        elif reactivation:
            warns += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "WARN",
                    "status": "WARN",
                    "dip_deg": dip,
                    "dip_meta": dip_meta,
                    "regime": regime,
                    "expected_range": [lo, hi],
                    "reason": "Outside range; reactivation/fluid_pressure exception",
                    "epistemic": "SPECULATIVE",
                }
            )
        else:
            kills += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "KILL",
                    "status": "KILL",
                    "dip_deg": dip,
                    "dip_meta": dip_meta,
                    "regime": regime,
                    "expected_range": [lo, hi],
                    "reason": f"Dip {dip:.1f}° outside {regime} prior [{lo},{hi}]",
                }
            )

    if kills:
        status = "KILL"
        reason = f"{kills} fault(s) fail K-DIP"
    elif unmeas and not passes and not warns:
        status = "UNMEASURED"
        reason = "True dip not measurable without calibration"
    elif passes or warns:
        status = "PASS" if not warns else "WARN"
        reason = f"passes={passes} warns={warns} unmeasured={unmeas}"
    else:
        status = "UNMEASURED"
        reason = "No conclusive dip/regime pairs"

    return make_gate_receipt(
        "K-DIP",
        status,  # type: ignore[arg-type]
        inputs={"faults": inputs_acc},
        equation=_EQUATION,
        thresholds={"regime_ranges_deg": _REGIME_RANGES},
        calculated_result={"kills": kills, "passes": passes, "warns": warns, "unmeasured": unmeas},
        exceptions_considered=["reactivation_evidence", "fluid_pressure_exception"],
        evidence_refs=[
            "Anderson 1951 — The dynamics of faulting",
            "Célérier 2008 — ROG: potential for renewed slip",
            "Alcalde 2019 — VE bias in apparent dip measurements",
        ],
        reason=reason,
        findings=findings,
        gate_type="hard_conditional",
    )
