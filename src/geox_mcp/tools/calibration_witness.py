"""Calibration Witness MCP tool — register and validate calibration witnesses.

DITEMPA BUKAN DIBERI.
"""
from __future__ import annotations

from typing import Any, Optional


async def geox_calibration_register_witness(
    *,
    witness: dict[str, Any],
    session_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Register a calibration witness for structural interpretation.

    The witness defines the calibrated measurement frame that structural
    gates consume. Without a valid witness, gates return UNMEASURED.
    """
    from geox_mcp.domain.calibration.contracts import CalibrationWitness, WitnessStatus

    try:
        cw = CalibrationWitness(**witness)
    except Exception as e:
        return {
            "status": "VOID",
            "reason": f"Invalid witness schema: {e}",
            "tool_name": "geox_calibration_register_witness",
        }

    # Validate completeness
    blockers = []
    if not cw.axis_calibration_h:
        blockers.append("missing_horizontal_calibration")
    if not cw.axis_calibration_v:
        blockers.append("missing_vertical_calibration")
    if cw.display_domain.vertical_domain.value == "DEPTH" and not cw.velocity_or_td_ref:
        blockers.append("depth_domain_requires_velocity_or_td")

    if blockers:
        cw.status = WitnessStatus.HOLD

    return {
        "tool_name": "geox_calibration_register_witness",
        "witness_id": cw.calibration_witness_id,
        "status": cw.status.value,
        "blockers": blockers,
        "purposes_enabled": [p.value for p in cw.purpose] if not blockers else [],
        "display_domain": cw.display_domain.model_dump(),
        "evidence_ref": cw.evidence_ref.model_dump(),
        "n_picks": len(cw.picks),
        "has_velocity": cw.velocity_or_td_ref is not None,
        "provenance": {
            "tool": "geox_calibration_register_witness",
            "actor_id": actor_id,
            "session_id": session_id,
        },
    }
