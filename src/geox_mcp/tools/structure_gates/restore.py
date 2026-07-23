"""K-RESTORE / G5 — restoration balance stub.

Hard veto when caller supplies restore residuals outside tolerance.
Without restore metrics → INCONCLUSIVE (stub is honest).

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_TOL = 0.05  # 5% line-length / area residual


def gate_k_restore(framework: dict[str, Any]) -> dict[str, Any]:
    restore = framework.get("restore") or framework.get("restoration") or {}
    if not restore and framework.get("restore_residual") is None:
        return {
            "gate": "K-RESTORE",
            "verdict": "INCONCLUSIVE",
            "reason": "No restoration residual provided (stub — run balance offline)",
            "findings": [],
            "type": "hard_veto_stub",
        }

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
                    {
                        "verdict": "KILL",
                        "reason": f"Restore residual {r} > tolerance {tol}",
                        "residual": r,
                        "tolerance": tol,
                    }
                )
            else:
                findings.append(
                    {
                        "verdict": "PASS",
                        "reason": f"Restore residual {r} within {tol}",
                        "residual": r,
                        "tolerance": tol,
                    }
                )
        except (TypeError, ValueError):
            findings.append({"verdict": "INCONCLUSIVE", "reason": "Non-numeric residual"})

    if any(f.get("verdict") == "KILL" for f in findings):
        verdict = "KILL"
        reason = "Restoration hard veto"
    elif any(f.get("verdict") == "PASS" for f in findings) and not any(
        f.get("verdict") == "INCONCLUSIVE" for f in findings
    ):
        verdict = "PASS"
        reason = "Restoration within tolerance"
    else:
        verdict = "INCONCLUSIVE"
        reason = "Incomplete restoration metrics"

    return {
        "gate": "K-RESTORE",
        "verdict": verdict,
        "reason": reason,
        "findings": findings,
        "type": "hard_veto_stub",
    }
