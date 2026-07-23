"""K-DL — D/L soft likelihood. Missing D or L → UNMEASURED.

Earth bulk D/L ~0.005–0.05; global envelope ~1e-3–1e-1.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

_D_L_LO = 1e-3
_D_L_HI = 1e-1
_EARTH_LO = 0.005
_EARTH_HI = 0.05
_EQUATION = "D/L = max_displacement / length; Earth bulk ~0.005–0.05; global ~1e-3–1e-1"


def gate_k_dl(framework: dict[str, Any]) -> dict[str, Any]:
    faults = framework.get("faults") or []
    if not faults:
        return make_gate_receipt(
            "K-DL", "UNMEASURED", reason="No faults", equation=_EQUATION, gate_type="soft_likelihood"
        )

    findings: list[dict[str, Any]] = []
    kills = passes = unmeas = warns = 0

    for f in faults:
        fid = f.get("fault_id") or f.get("id") or "unknown"
        d = f.get("max_displacement") or f.get("max_throw")
        length = f.get("length") or f.get("length_m") or f.get("length_px")
        linkage = bool(f.get("linkage_story") or f.get("relay_ramp") or f.get("segment_linkage"))

        if d is None and f.get("throw_profile"):
            try:
                throws = []
                for s in f["throw_profile"]:
                    if isinstance(s, dict):
                        throws.append(float(s.get("throw") or s.get("throw_m") or 0))
                    else:
                        throws.append(float(s))
                d = max(throws) if throws else None
            except (TypeError, ValueError):
                d = None
        if length is None and f.get("points"):
            length = float(len(f["points"]))

        if d is None or length is None or float(length) <= 0:
            unmeas += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "UNMEASURED",
                    "status": "UNMEASURED",
                    "reason": "Missing max_displacement or length",
                }
            )
            continue

        ratio = float(d) / float(length)
        if _EARTH_LO <= ratio <= _EARTH_HI:
            passes += 1
            findings.append(
                {"fault_id": fid, "verdict": "PASS", "status": "PASS", "d_over_l": ratio}
            )
        elif _D_L_LO <= ratio <= _D_L_HI:
            warns += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "WARN",
                    "status": "WARN",
                    "d_over_l": ratio,
                    "reason": "Outside Earth bulk band but inside global envelope",
                }
            )
        elif linkage and ratio <= _D_L_HI * 5:
            warns += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "WARN",
                    "status": "WARN",
                    "d_over_l": ratio,
                    "reason": "Outlier softened by linkage_story",
                }
            )
        elif ratio > _D_L_HI or ratio < _D_L_LO:
            # Outside global envelope without linkage → hard KILL
            kills += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "KILL",
                    "status": "KILL",
                    "d_over_l": ratio,
                    "reason": f"D/L={ratio:.3e} outside global envelope without linkage story",
                }
            )
        else:
            unmeas += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "UNMEASURED",
                    "status": "UNMEASURED",
                    "d_over_l": ratio,
                    "reason": "Outside envelope — needs remeasure or linkage",
                }
            )

    if kills:
        status = "KILL"
    elif passes or warns:
        status = "PASS" if not warns else "WARN"
    else:
        status = "UNMEASURED"

    return make_gate_receipt(
        "K-DL",
        status,  # type: ignore[arg-type]
        equation=_EQUATION,
        thresholds={
            "global_lo": _D_L_LO,
            "global_hi": _D_L_HI,
            "earth_lo": _EARTH_LO,
            "earth_hi": _EARTH_HI,
        },
        calculated_result={"kills": kills, "passes": passes, "warns": warns, "unmeasured": unmeas},
        reason=f"kills={kills} passes={passes} warns={warns} unmeasured={unmeas}",
        findings=findings,
        gate_type="soft_likelihood",
    )
