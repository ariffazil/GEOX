"""K-DIP — dip vs regime prior (Andersonian conditional).

Normal 55–70°, reverse 20–40°, strike-slip subvertical (~75–90°).
Outside range without reactivation evidence → KILL.
Missing dip → INCONCLUSIVE.

VE correction (Alcalde 2019): if only dip_deg_image is supplied and
measurement_context.geometry.vertical_exaggeration (or vertical_exaggeration)
is set, convert apparent dip → true dip before the regime test:
  tan(true) = tan(apparent) / VE

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from typing import Any

# Degrees; inclusive ranges (subsurface / VE-corrected space)
_REGIME_RANGES: dict[str, tuple[float, float]] = {
    "normal": (55.0, 70.0),
    "reverse": (20.0, 40.0),
    "thrust": (20.0, 40.0),
    "strike_slip": (75.0, 90.0),
    "strike-slip": (75.0, 90.0),
}


def _ve_of(framework: dict[str, Any], fault: dict[str, Any]) -> float | None:
    """Vertical exaggeration H:V scale factor (>0). 1.0 = true section."""
    for src in (fault, framework.get("measurement_context") or {}, framework):
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


def _dip_of(fault: dict[str, Any], framework: dict[str, Any]) -> tuple[float | None, dict[str, Any]]:
    """Return (dip_for_test_deg, meta). Prefer subsurface; else image ± VE correction."""
    meta: dict[str, Any] = {}
    if fault.get("dip_deg_subsurface") is not None:
        try:
            return float(fault["dip_deg_subsurface"]), {"domain": "subsurface", "ve_corrected": False}
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

    ve = _ve_of(framework, fault)
    if ve is None or abs(ve - 1.0) < 1e-9:
        meta.update({"domain": "image_or_true", "ve": ve, "ve_corrected": False})
        return apparent, meta

    # tan(true) = tan(apparent) / VE  — protect near-vertical
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
        return {
            "gate": "K-DIP",
            "verdict": "INCONCLUSIVE",
            "reason": "No faults provided",
            "findings": [],
        }

    findings: list[dict[str, Any]] = []
    kills = 0
    passes = 0
    inconclusive = 0

    for f in faults:
        fid = f.get("fault_id") or f.get("id") or "unknown"
        dip, dip_meta = _dip_of(f, framework)
        regime = str(f.get("regime_prior") or f.get("regime") or "unknown").lower().strip()
        reactivation = bool(
            f.get("reactivation_evidence")
            or f.get("reactivation")
            or f.get("fluid_pressure_exception")
        )

        if dip is None:
            inconclusive += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "INCONCLUSIVE",
                    "reason": "Missing dip_deg_image/subsurface",
                }
            )
            continue

        if regime in ("unknown", "", "none"):
            inconclusive += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "INCONCLUSIVE",
                    "dip_deg": dip,
                    "dip_meta": dip_meta,
                    "reason": "regime_prior unknown — cannot apply Andersonian prior",
                }
            )
            continue

        lo_hi = _REGIME_RANGES.get(regime)
        if lo_hi is None:
            inconclusive += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "INCONCLUSIVE",
                    "dip_deg": dip,
                    "regime": regime,
                    "reason": f"Unrecognized regime_prior '{regime}'",
                }
            )
            continue

        lo, hi = lo_hi
        in_range = lo <= dip <= hi
        if in_range:
            passes += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "PASS",
                    "dip_deg": dip,
                    "dip_meta": dip_meta,
                    "regime": regime,
                    "expected_range": [lo, hi],
                }
            )
        elif reactivation:
            passes += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "PASS",
                    "dip_deg": dip,
                    "dip_meta": dip_meta,
                    "regime": regime,
                    "expected_range": [lo, hi],
                    "reason": "Outside range but reactivation/fluid_pressure exception flagged",
                    "epistemic": "SPECULATIVE",
                }
            )
        else:
            kills += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "KILL",
                    "dip_deg": dip,
                    "dip_meta": dip_meta,
                    "regime": regime,
                    "expected_range": [lo, hi],
                    "reason": (
                        f"Dip {dip:.1f}° outside {regime} prior [{lo},{hi}] "
                        "without reactivation evidence"
                    ),
                }
            )

    if kills:
        verdict = "KILL"
        reason = f"{kills} fault(s) fail K-DIP"
    elif passes and not inconclusive:
        verdict = "PASS"
        reason = f"All {passes} fault(s) within regime dip prior"
    elif passes:
        verdict = "PASS"  # hard kills only reject; partial evidence still PASS survivors
        reason = f"{passes} PASS, {inconclusive} INCONCLUSIVE (no KILL)"
    else:
        verdict = "INCONCLUSIVE"
        reason = "No conclusive dip/regime pairs"

    return {
        "gate": "K-DIP",
        "verdict": verdict,
        "reason": reason,
        "findings": findings,
        "type": "hard_conditional",
    }
