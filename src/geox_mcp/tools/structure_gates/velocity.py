"""K-VEL / G7 — interval velocity. Missing V → UNMEASURED (never invent regional V)."""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

_LITHO_V: dict[str, tuple[float, float]] = {
    "shale": (1800.0, 4500.0),
    "sand": (1500.0, 5000.0),
    "sandstone": (1500.0, 5000.0),
    "carbonate": (3000.0, 7000.0),
    "limestone": (3000.0, 7000.0),
    "salt": (4000.0, 5000.0),
    "water": (1400.0, 1600.0),
    "unknown": (1400.0, 7000.0),
}
_EQUATION = "interval_V must be >0, monotonic T–D, and within lithology band"


def gate_k_vel(framework: dict[str, Any]) -> dict[str, Any]:
    vel = framework.get("velocity") or {}
    if not vel and framework.get("interval_v_m_s") is None:
        return make_gate_receipt(
            "K-VEL",
            "UNMEASURED",
            reason="No velocity / T–D provided — will not substitute regional V",
            equation=_EQUATION,
            gate_type="hard_veto",
        )

    v = vel.get("interval_v_m_s") if isinstance(vel, dict) else None
    if v is None:
        v = framework.get("interval_v_m_s")
    litho = str(
        (vel.get("lithology_prior") if isinstance(vel, dict) else None)
        or framework.get("lithology_prior")
        or "unknown"
    ).lower()
    monotonic = vel.get("td_monotonic") if isinstance(vel, dict) else framework.get("td_monotonic")
    positive = vel.get("positive") if isinstance(vel, dict) else framework.get("v_positive")
    findings: list[dict[str, Any]] = []

    if positive is False or (v is not None and float(v) <= 0):
        findings.append({"verdict": "KILL", "reason": "Non-positive velocity"})
    if monotonic is False:
        findings.append({"verdict": "KILL", "reason": "T–D non-monotonic"})

    if v is not None:
        try:
            vv = float(v)
            lo, hi = _LITHO_V.get(litho, _LITHO_V["unknown"])
            if vv < 500 or vv > 9000:
                findings.append(
                    {"verdict": "KILL", "reason": f"V={vv} physically impossible", "v": vv}
                )
            elif not (lo <= vv <= hi):
                findings.append(
                    {
                        "verdict": "KILL",
                        "reason": f"V={vv} outside lithology {litho} [{lo},{hi}]",
                        "v": vv,
                    }
                )
            else:
                findings.append(
                    {"verdict": "PASS", "reason": f"V={vv} ok for {litho}", "v": vv}
                )
        except (TypeError, ValueError):
            findings.append({"verdict": "UNMEASURED", "reason": "Non-numeric velocity"})
    elif not findings:
        return make_gate_receipt(
            "K-VEL",
            "UNMEASURED",
            reason="Velocity fields incomplete",
            equation=_EQUATION,
            gate_type="hard_veto",
        )

    if any(f.get("verdict") == "KILL" for f in findings):
        status = "KILL"
    elif any(f.get("verdict") == "PASS" for f in findings):
        status = "PASS"
    else:
        status = "UNMEASURED"

    return make_gate_receipt(
        "K-VEL",
        status,  # type: ignore[arg-type]
        equation=_EQUATION,
        thresholds={"lithology_bands_m_s": _LITHO_V},
        calculated_result={"v": v, "lithology": litho},
        reason=f"combined={status}",
        findings=findings,
        gate_type="hard_veto",
    )
