"""K-RESTORE / G5 — restoration stub. Missing metrics → UNMEASURED."""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

_DEFAULT_TOL = 0.05
_EQUATION = "residual = |restored_length_or_area - original| / original; KILL if residual > tol"


def gate_k_restore(framework: dict[str, Any]) -> dict[str, Any]:
    restore = framework.get("restore") or framework.get("restoration") or {}
    if not restore and framework.get("restore_residual") is None:
        return make_gate_receipt(
            "K-RESTORE",
            "UNMEASURED",
            reason="No restoration residual provided (stub)",
            equation=_EQUATION,
            gate_type="hard_veto_stub",
        )

    residual = restore.get("residual") if isinstance(restore, dict) else None
    if residual is None:
        residual = framework.get("restore_residual")
    closes = restore.get("closes") if isinstance(restore, dict) else framework.get("restore_closes")
    self_intersect = (
        restore.get("self_intersection")
        if isinstance(restore, dict)
        else framework.get("restore_self_intersection")
    )
    tol = float(
        (restore.get("tolerance") if isinstance(restore, dict) else None)
        or framework.get("restore_tolerance")
        or _DEFAULT_TOL
    )
    findings: list[dict[str, Any]] = []
    if self_intersect is True:
        findings.append({"verdict": "KILL", "reason": "Restore self-intersection"})
    if closes is False:
        findings.append({"verdict": "KILL", "reason": "Restore does not close"})
    if residual is not None:
        try:
            r = abs(float(residual))
            if r > tol:
                findings.append(
                    {"verdict": "KILL", "reason": f"residual {r} > tol {tol}", "residual": r}
                )
            else:
                findings.append(
                    {"verdict": "PASS", "reason": f"residual {r} within {tol}", "residual": r}
                )
        except (TypeError, ValueError):
            findings.append({"verdict": "UNMEASURED", "reason": "Non-numeric residual"})

    if any(f.get("verdict") == "KILL" for f in findings):
        status = "KILL"
        reason = "Restoration hard veto"
    elif any(f.get("verdict") == "PASS" for f in findings):
        status = "PASS"
        reason = "Restoration within tolerance"
    else:
        status = "UNMEASURED"
        reason = "Incomplete restoration metrics"

    return make_gate_receipt(
        "K-RESTORE",
        status,  # type: ignore[arg-type]
        equation=_EQUATION,
        thresholds={"tolerance": tol},
        calculated_result={"residual": residual},
        reason=reason,
        findings=findings,
        gate_type="hard_veto_stub",
    )
