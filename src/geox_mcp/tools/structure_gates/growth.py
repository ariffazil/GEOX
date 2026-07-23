"""K-GROWTH / G4 — syn-kinematic claim requires expansion index > 1.

Growth claimed but EI ≤ 1 → KILL.
No growth claim → INCONCLUSIVE (or PASS if not claimed).

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any


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
        return {
            "gate": "K-GROWTH",
            "verdict": "INCONCLUSIVE",
            "reason": "No syn-kinematic / growth claim — gate idle",
            "findings": [],
            "type": "soft_conditional",
        }

    if ei is None:
        return {
            "gate": "K-GROWTH",
            "verdict": "INCONCLUSIVE",
            "reason": "Growth claimed but expansion_index missing",
            "findings": [{"verdict": "INCONCLUSIVE", "growth_claimed": True}],
            "type": "soft_conditional",
        }

    try:
        ei_f = float(ei)
    except (TypeError, ValueError):
        return {
            "gate": "K-GROWTH",
            "verdict": "INCONCLUSIVE",
            "reason": "Non-numeric expansion_index",
            "findings": [],
            "type": "soft_conditional",
        }

    if ei_f <= 1.0:
        return {
            "gate": "K-GROWTH",
            "verdict": "KILL",
            "reason": f"Growth claimed but EI={ei_f} ≤ 1",
            "findings": [
                {
                    "verdict": "KILL",
                    "expansion_index": ei_f,
                    "growth_claimed": True,
                }
            ],
            "type": "soft_conditional",
        }

    return {
        "gate": "K-GROWTH",
        "verdict": "PASS",
        "reason": f"Growth claim supported by EI={ei_f} > 1",
        "findings": [
            {
                "verdict": "PASS",
                "expansion_index": ei_f,
                "growth_claimed": True,
            }
        ],
        "type": "soft_conditional",
    }
