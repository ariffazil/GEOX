"""K-THROW — displacement profile must taper toward tips.

Missing profile → UNMEASURED. Constant/increasing tip throw → KILL.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt
from geox_mcp.tools.structure_gates.normalize import normalize_fault

_EQUATION = (
    "Barnett 1987: throw max near centre, taper to 0 at elliptical tip-line. "
    "KILL if tip throw grows vs interior or near-constant high."
)


def _profile_values(fault: dict[str, Any]) -> list[float] | None:
    # normalize_fault maps throw_profile_m / throw_samples → throw_profile
    f = normalize_fault(fault) if isinstance(fault, dict) else {}
    prof = f.get("throw_profile")
    if not prof:
        return None
    vals: list[float] = []
    for station in prof:
        if isinstance(station, (int, float)):
            vals.append(float(station))
            continue
        if not isinstance(station, dict):
            continue
        for key in ("throw", "throw_ms", "throw_m", "displacement", "dmax_m", "value"):
            if key in station and station[key] is not None:
                try:
                    vals.append(float(station[key]))
                    break
                except (TypeError, ValueError):
                    pass
    return vals if vals else None


def _tip_taper_ok(vals: list[float]) -> tuple[str, str]:
    if len(vals) < 3:
        return "UNMEASURED", "throw_profile needs ≥3 stations"
    tips = [vals[0], vals[-1]]
    mid = vals[1:-1]
    mid_max = max(mid) if mid else max(vals)
    tip_max = max(tips)
    tip_min = min(tips)
    grows_to_tip = vals[0] > vals[1] or vals[-1] > vals[-2]
    nearly_constant = tip_max >= 0.9 * mid_max and tip_min >= 0.85 * mid_max and mid_max > 0
    if grows_to_tip and tip_max > 0:
        return "KILL", "Throw increases toward tip (tip growth / no taper)"
    if nearly_constant and mid_max > 0:
        return "KILL", "Throw constant/non-tapering at tips"
    if tip_max <= mid_max * 0.75 or (tip_min < mid_max * 0.5):
        return "PASS", "Throw tapers toward tips"
    if tip_max < mid_max:
        return "PASS", "Throw weakly tapers toward tips"
    return "KILL", "Tip throw does not taper relative to mid-fault"


def gate_k_throw(framework: dict[str, Any]) -> dict[str, Any]:
    faults = framework.get("faults") or []
    if not faults:
        return make_gate_receipt(
            "K-THROW",
            "UNMEASURED",
            reason="No faults provided",
            equation=_EQUATION,
            gate_type="hard_mixed",
        )

    findings: list[dict[str, Any]] = []
    kills = passes = unmeas = 0

    for raw in faults:
        f = normalize_fault(raw) if isinstance(raw, dict) else {}
        fid = f.get("fault_id") or f.get("id") or "unknown"
        tip_flag = str(f.get("tip_taper") or "").lower()
        if tip_flag == "fail":
            kills += 1
            findings.append({"fault_id": fid, "verdict": "KILL", "status": "KILL", "reason": "tip_taper=fail"})
            continue
        if tip_flag == "ok":
            passes += 1
            findings.append({"fault_id": fid, "verdict": "PASS", "status": "PASS", "reason": "tip_taper=ok"})
            continue
        vals = _profile_values(f)
        if not vals:
            unmeas += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "UNMEASURED",
                    "status": "UNMEASURED",
                    "reason": (
                        "No throw_profile / tip_taper "
                        "(accepts aliases: throw_profile_m, throw_samples, …)"
                    ),
                }
            )
            continue
        v, reason = _tip_taper_ok(vals)
        if v == "KILL":
            kills += 1
        elif v == "PASS":
            passes += 1
        else:
            unmeas += 1
        findings.append(
            {
                "fault_id": fid,
                "verdict": v,
                "status": v,
                "reason": reason,
                "throw_profile": vals,
            }
        )

    if kills:
        status, reason = "KILL", f"{kills} fault(s) fail tip-taper"
    elif passes:
        status, reason = "PASS", f"passes={passes} unmeasured={unmeas}"
    else:
        status, reason = "UNMEASURED", "No conclusive throw profiles"

    return make_gate_receipt(
        "K-THROW",
        status,  # type: ignore[arg-type]
        inputs={"n_faults": len(faults)},
        equation=_EQUATION,
        thresholds={"tip_vs_mid_ratio_kill": 0.9},
        calculated_result={"kills": kills, "passes": passes, "unmeasured": unmeas},
        reason=reason,
        findings=findings,
        gate_type="hard_mixed",
    )
