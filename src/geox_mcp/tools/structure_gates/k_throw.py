"""K-THROW — displacement profile must taper toward tips.

Constant or increasing throw at tip → KILL.
Missing profile → INCONCLUSIVE.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any


def _profile_values(fault: dict[str, Any]) -> list[float] | None:
    prof = fault.get("throw_profile")
    if not prof:
        # allow simple list of throws
        simple = fault.get("throw_samples")
        if isinstance(simple, (list, tuple)) and simple:
            try:
                return [float(x) for x in simple]
            except (TypeError, ValueError):
                return None
        return None
    vals: list[float] = []
    for station in prof:
        if isinstance(station, (int, float)):
            vals.append(float(station))
            continue
        if not isinstance(station, dict):
            continue
        for key in ("throw", "throw_ms", "throw_m", "displacement", "value"):
            if key in station and station[key] is not None:
                try:
                    vals.append(float(station[key]))
                    break
                except (TypeError, ValueError):
                    pass
    return vals if vals else None


def _tip_taper_ok(vals: list[float]) -> tuple[str, str]:
    """Return (verdict, reason) for a throw profile."""
    if len(vals) < 3:
        return "INCONCLUSIVE", "throw_profile needs ≥3 stations"

    tips = [vals[0], vals[-1]]
    mid = vals[1:-1]
    mid_max = max(mid) if mid else max(vals)
    tip_max = max(tips)
    tip_min = min(tips)

    # Increasing toward tip: tip larger than adjacent interior
    grows_to_tip = vals[0] > vals[1] or vals[-1] > vals[-2]
    # Constant throw (no taper): tip ~ mid max
    nearly_constant = tip_max >= 0.9 * mid_max and tip_min >= 0.85 * mid_max and mid_max > 0

    if grows_to_tip and tip_max > 0:
        return "KILL", "Throw increases toward tip (tip growth / no taper)"
    if nearly_constant and mid_max > 0:
        return "KILL", "Throw constant/non-tapering at tips"
    if tip_max <= mid_max * 0.75 or (tip_min < mid_max * 0.5):
        return "PASS", "Throw tapers toward tips"
    # Weak taper
    if tip_max < mid_max:
        return "PASS", "Throw weakly tapers toward tips"
    return "KILL", "Tip throw does not taper relative to mid-fault"


def gate_k_throw(framework: dict[str, Any]) -> dict[str, Any]:
    faults = framework.get("faults") or []
    if not faults:
        return {
            "gate": "K-THROW",
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
        # explicit tip_taper flag from pickers
        tip_flag = str(f.get("tip_taper") or "").lower()
        if tip_flag == "fail":
            kills += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "KILL",
                    "reason": "tip_taper=fail",
                }
            )
            continue
        if tip_flag == "ok":
            passes += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "PASS",
                    "reason": "tip_taper=ok",
                }
            )
            continue

        vals = _profile_values(f)
        if not vals:
            inconclusive += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "INCONCLUSIVE",
                    "reason": "No throw_profile / tip_taper",
                }
            )
            continue

        v, reason = _tip_taper_ok(vals)
        if v == "KILL":
            kills += 1
        elif v == "PASS":
            passes += 1
        else:
            inconclusive += 1
        findings.append(
            {
                "fault_id": fid,
                "verdict": v,
                "reason": reason,
                "throw_profile": vals,
            }
        )

    if kills:
        verdict = "KILL"
        reason = f"{kills} fault(s) fail tip-taper"
    elif passes:
        verdict = "PASS"
        reason = f"{passes} PASS, {inconclusive} INCONCLUSIVE"
    else:
        verdict = "INCONCLUSIVE"
        reason = "No conclusive throw profiles"

    return {
        "gate": "K-THROW",
        "verdict": verdict,
        "reason": reason,
        "findings": findings,
        "type": "hard_mixed",
    }
