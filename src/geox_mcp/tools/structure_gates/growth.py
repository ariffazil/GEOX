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
            inputs={"growth_claimed": False},
            thresholds={"ei_min": 1.0},
            calculated_result={"expansion_index": None},
            exceptions_considered=["sedimentary mimic (Castelltort caveat)"],
            evidence_refs=[
                "Thorsen 1963 — Growth fault EI test",
                "Castelltort et al. — sedimentary vs tectonic mimic",
            ],
            gate_type="soft_conditional",
        )

    if ei is None:
        return make_gate_receipt(
            "K-GROWTH",
            "UNMEASURED",
            reason="Growth claimed but expansion_index missing",
            equation=_EQUATION,
            inputs={"growth_claimed": True, "expansion_index": None},
            thresholds={"ei_min": 1.0},
            calculated_result={"expansion_index": None, "growth_claimed": True},
            evidence_refs=["Thorsen 1963 — Growth fault EI test"],
            exceptions_considered=["sedimentary mimic (Castelltort caveat)"],
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
            inputs={"expansion_index": ei},
            thresholds={"ei_min": 1.0},
            calculated_result={"expansion_index": None, "ei_type": type(ei).__name__},
            evidence_refs=["Thorsen 1963 — Growth fault EI test"],
            gate_type="soft_conditional",
        )

    if ei_f <= 1.0:
        return make_gate_receipt(
            "K-GROWTH",
            "KILL",
            reason=f"Growth claimed but EI={ei_f} ≤ 1",
            equation=_EQUATION,
            inputs={"expansion_index": ei_f, "growth_claimed": True},
            thresholds={"ei_min": 1.0},
            exceptions_considered=["sedimentary mimic (Castelltort caveat)"],
            evidence_refs=["Thorsen 1963 — Growth fault EI test"],
            calculated_result={"expansion_index": ei_f},
            findings=[{"verdict": "KILL", "expansion_index": ei_f, "growth_claimed": True}],
            gate_type="soft_conditional",
        )

    # PASS-with-caveat → WARN (EI>1 supports but does not prove — Castelltort mimic)
    return make_gate_receipt(
        "K-GROWTH",
        "WARN",
        reason=f"EI={ei_f} > 1 supports growth (mimic caveat applies)",
        equation=_EQUATION,
        inputs={"expansion_index": ei_f, "growth_claimed": True},
        thresholds={"ei_min": 1.0},
        exceptions_considered=["sedimentary mimic (Castelltort caveat)"],
        evidence_refs=[
            "Thorsen 1963 — Growth fault EI test",
            "Castelltort et al. — sedimentary vs tectonic mimic",
        ],
        calculated_result={"expansion_index": ei_f},
        findings=[{
            "verdict": "WARN",
            "expansion_index": ei_f,
            "growth_claimed": True,
            "reason": "EI>1 supports growth but does not prove it; sedimentary mimic possible",
        }],
        gate_type="soft_conditional",
    )
