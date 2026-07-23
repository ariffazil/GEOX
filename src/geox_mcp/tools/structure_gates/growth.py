"""K-GROWTH — growth claim requires EI>1. No claim → UNMEASURED (idle)."""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

_EQUATION = "EI = hanging_wall_thickness / footwall_thickness; growth claim requires EI > 1"


def gate_k_growth(framework: dict[str, Any]) -> dict[str, Any]:
    claims = framework.get("claims") or {}
    growth_claimed = bool(
        claims.get("growth")
        or claims.get("syn_kinematic")
        or framework.get("growth_claimed")
        or framework.get("syn_kinematic")
    )
    ei = claims.get("expansion_index")
    if ei is None:
        ei = framework.get("expansion_index")

    if not growth_claimed:
        return make_gate_receipt(
            "K-GROWTH",
            "UNMEASURED",
            reason="No syn-kinematic / growth claim — gate idle",
            equation=_EQUATION,
            gate_type="soft_conditional",
        )

    if ei is None:
        return make_gate_receipt(
            "K-GROWTH",
            "UNMEASURED",
            reason="Growth claimed but expansion_index missing",
            equation=_EQUATION,
            findings=[{"verdict": "UNMEASURED", "growth_claimed": True}],
            gate_type="soft_conditional",
        )

    try:
        ei_f = float(ei)
    except (TypeError, ValueError):
        return make_gate_receipt(
            "K-GROWTH",
            "UNMEASURED",
            reason="Non-numeric expansion_index",
            equation=_EQUATION,
            gate_type="soft_conditional",
        )

    if ei_f <= 1.0:
        return make_gate_receipt(
            "K-GROWTH",
            "KILL",
            reason=f"Growth claimed but EI={ei_f} ≤ 1",
            equation=_EQUATION,
            thresholds={"ei_min": 1.0},
            calculated_result={"expansion_index": ei_f},
            findings=[{"verdict": "KILL", "expansion_index": ei_f, "growth_claimed": True}],
            gate_type="soft_conditional",
        )

    return make_gate_receipt(
        "K-GROWTH",
        "PASS",
        reason=f"Growth claim supported by EI={ei_f} > 1",
        equation=_EQUATION,
        thresholds={"ei_min": 1.0},
        calculated_result={"expansion_index": ei_f},
        findings=[{"verdict": "PASS", "expansion_index": ei_f, "growth_claimed": True}],
        gate_type="soft_conditional",
    )
