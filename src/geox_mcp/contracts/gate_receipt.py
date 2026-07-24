"""
🌊 GEOX Gate Receipt Envelope — public re-export (PR-B1 reconciled).

Canonical implementation lives at:
    `geox_mcp.domain.seismic_physics.receipts`

This module re-exports for backward compatibility so existing callers
importing from `geox_mcp.contracts.gate_receipt` keep working.

Doctrine (F13):
  - Missing measurement → UNMEASURED. Never a guess.
  - Pass-with-caveat → WARN. Not PASS.
  - Local engine verdicts remain QUALIFIED_CANDIDATE. arifOS SEAL only.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from geox_mcp.domain.seismic_physics.receipts import (
    GateStatus,
    make_gate_receipt as gate_receipt,
    receipt_hash,
)

# ──────────────────────────────────────────────────────────────────────
# Status semantics — explicit (do not guess)
# ──────────────────────────────────────────────────────────────────────

STATUS_LEGEND: dict[str, str] = {
    "PASS": ("All required inputs present, gate math passes thresholds, no exceptions engaged."),
    "WARN": (
        "Gate math passes primary threshold, but a soft caveat holds "
        "(e.g. linkage, reactivation, lithology band edge). "
        "Not a kill; not blind accept."
    ),
    "KILL": ("Required inputs present and gate math exceeds hard thresholds. Model rejected on this gate."),
    "UNMEASURED": (
        "Required input missing or uncalibrated. Gate refuses to compute; "
        "downstream MUST NOT guess. Image-only inputs without scale are "
        "UNMEASURED here, not PASS."
    ),
}


def status_legend() -> str:
    return "\n".join(f"  {k}: {v}" for k, v in STATUS_LEGEND.items())


__all__ = [
    "GateStatus",
    "STATUS_LEGEND",
    "gate_receipt",
    "receipt_hash",
    "status_legend",
]
