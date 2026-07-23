"""K-DIP — dip vs regime prior (Andersonian conditional).

Normal 55–70°, reverse 20–40°, strike-slip subvertical (~75–90°).
Outside range without reactivation evidence → KILL.
Missing dip → INCONCLUSIVE.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

# Degrees; inclusive ranges (image-space or subsurface — caller labels domain)
_REGIME_RANGES: dict[str, tuple[float, float]] = {
    "normal": (55.0, 70.0),
    "reverse": (20.0, 40.0),
    "thrust": (20.0, 40.0),
    "strike_slip": (75.0, 90.0),
    "strike-slip": (75.0, 90.0),
}


def _dip_of(fault: dict[str, Any]) -> float | None:
    for key in ("dip_deg_subsurface", "dip_deg_image", "dip_deg", "dip"):
        v = fault.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None


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
        dip = _dip_of(f)
        regime = str(f.get("regime_prior") or f.get("regime") or "unknown").lower().strip()
        reactivation = bool(f.get("reactivation_evidence") or f.get("reactivation"))

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
        # strike-slip also accepts near-vertical mirrored 0–15 from vertical already in range
        if in_range:
            passes += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "PASS",
                    "dip_deg": dip,
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
                    "regime": regime,
                    "expected_range": [lo, hi],
                    "reason": "Outside range but reactivation_evidence=true",
                }
            )
        else:
            kills += 1
            findings.append(
                {
                    "fault_id": fid,
                    "verdict": "KILL",
                    "dip_deg": dip,
                    "regime": regime,
                    "expected_range": [lo, hi],
                    "reason": (
                        f"Dip {dip}° outside {regime} prior [{lo},{hi}] "
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
