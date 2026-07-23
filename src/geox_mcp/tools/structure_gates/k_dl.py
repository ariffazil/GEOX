"""K-DL — max displacement / length soft likelihood (~1e-3 to 1e-1).

Extreme outliers without linkage story → KILL.
Missing D or L → INCONCLUSIVE.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

_D_L_LO = 1e-3
_D_L_HI = 1e-1


def gate_k_dl(framework: dict[str, Any]) -> dict[str, Any]:
    faults = framework.get("faults") or []
    if not faults:
        return {
            "gate": "K-DL",
            "verdict": "INCONCLUSIVE",
            "reason": "No faults",
            "findings": [],
        }

    findings: list[dict[str, Any]] = []
    kills = 0
    passes = 0
    inconclusive = 0

    for f in faults:
        fid = f.get("fault_id") or f.get("id") or "unknown"
        d = f.get("max_displacement") or f.get("max_throw")
        length = f.get("length") or f.get("length_m") or f.get("length_px")
        linkage = bool(f.get("linkage_story") or f.get("relay_ramp") or f.get("segment_linkage"))

        if d is None or length is None:
            # try derive from throw_profile + points
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
                length = float(len(f["points"]))  # pixel proxy only
            if d is None or length is None or float(length) <= 0:
                inconclusive += 1
                findings.append(
                    {
                        "fault_id": fid,
                        "verdict": "INCONCLUSIVE",
                        "reason": "Missing max_displacement or length",
                    }
                )
                continue

        ratio = float(d) / float(length)
        if _D_L_LO <= ratio <= _D_L_HI:
            passes += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "PASS",
                    "d_over_l": ratio,
                    "envelope": [_D_L_LO, _D_L_HI],
                }
            )
        elif linkage and ratio <= _D_L_HI * 5:
            passes += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "PASS",
                    "d_over_l": ratio,
                    "reason": "Outlier softened by linkage_story",
                }
            )
        elif ratio > _D_L_HI * 10 or ratio < _D_L_LO / 10:
            kills += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "KILL",
                    "d_over_l": ratio,
                    "reason": f"D/L={ratio:.3e} extreme vs global envelope without linkage story",
                }
            )
        else:
            # soft: REVIEW as INCONCLUSIVE rather than hard KILL
            inconclusive += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "INCONCLUSIVE",
                    "d_over_l": ratio,
                    "reason": "Outside envelope — soft likelihood, needs linkage or remeasure",
                }
            )

    if kills:
        verdict = "KILL"
    elif passes and not kills:
        verdict = "PASS"
    else:
        verdict = "INCONCLUSIVE"

    return {
        "gate": "K-DL",
        "verdict": verdict,
        "reason": f"kills={kills} passes={passes} inconclusive={inconclusive}",
        "findings": findings,
        "type": "soft_likelihood",
    }
