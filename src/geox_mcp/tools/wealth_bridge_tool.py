"""
geox_to_wealth_bridge — Cross-organ GEOX→WEALTH data bridge
═══════════════════════════════════════════════════════════

Converts GEOX prospect evaluation data into WEALTH score_kernel input.
Simplified MCP wrapper — takes flat dict inputs, returns WealthInput format.

Constitutional rules:
  F2: epistemic_source is PASSED THROUGH, never upgraded
  F1: irreversible=False for read-only scoring calls
  F13: blocked nodes cannot enter WEALTH pipeline

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.wealth_bridge")


async def geox_to_wealth_bridge(
    prospect_id: str,
    npv_usd: float | None = None,
    irr: float | None = None,
    breakeven_usd: float | None = None,
    discount_rate: float = 0.10,
    risk_geo: float = 0.0,
    sigma_market: float = 0.0,
    sigma_policy: float = 0.0,
    admissibility: str = "admitted",
    epistemic_source: str = "ESTIMATE",
    penalty_infinite: bool = False,
    carbon_cost_usd: float = 0.0,
    delay_risk: float = 0.0,
    required_modifications: list[str] | None = None,
    peace2: float = 1.0,
    d_s: float = 0.0,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Bridge GEOX prospect data to WEALTH score_kernel input.

    Converts prospect economics + governance data into the WealthInput
    format expected by WEALTH capital intelligence organ.

    Args:
        prospect_id: Unique prospect identifier.
        npv_usd: Net present value in USD.
        irr: Internal rate of return (0-1).
        breakeven_usd: Breakeven price per unit.
        discount_rate: Discount rate (default 10%).
        risk_geo: Geological risk (0-1).
        sigma_market: Market volatility.
        sigma_policy: Policy risk.
        admissibility: Governance status (admitted/blocked/conditional).
        epistemic_source: Evidence quality tag (OBS/DER/INT/SPEC/ESTIMATE).
            F2: NEVER upgraded — passed through as-is.
        penalty_infinite: Whether penalty is infinite (blocked prospect).
        carbon_cost_usd: Carbon cost per tCO2e.
        delay_risk: Delay risk factor (0-1).
        required_modifications: List of required modifications.
        peace2: Peace² score (de-escalation factor).
        d_s: Entropy delta.
        session_id: MCP session ID.
        actor_id: Actor ID.

    Returns:
        WealthInput-compatible dict for WEALTH score_kernel.
    """
    # F13: blocked nodes cannot cross
    if admissibility == "blocked":
        return {
            "tool": "geox_to_wealth_bridge",
            "error": "ADMISSIBILITY_BLOCKED",
            "message": f"Prospect {prospect_id} is governance-blocked. Cannot pass to WEALTH.",
            "888_HOLD": True,
        }

    # Maruah score: 1 - sigma_policy - modification_penalty
    mod_count = len(required_modifications or [])
    mod_penalty = mod_count * 0.05
    maruah = max(0.0, 1.0 - sigma_policy - mod_penalty)

    # Build WealthInput
    wealth_input = {
        "base_rate": discount_rate,
        "d_s": d_s,
        "peace2": peace2,
        "maruah_score": round(maruah, 4),
        "epistemic_source": epistemic_source,  # F2: never upgraded
        "wealth_signals": {
            "npv_usd": npv_usd,
            "irr": irr,
            "breakeven": breakeven_usd,
            "sigma_geo": risk_geo,
            "sigma_market": sigma_market,
            "sigma_policy": sigma_policy,
        },
        "extractive_signals": {
            "admissibility": admissibility,
            "penalty_inf": penalty_infinite,
            "carbon_cost": carbon_cost_usd,
            "delay_risk": delay_risk,
        },
        "task_definition": f"score_resource_node:{prospect_id}",
        "irreversible": False,  # F1: always reversible for read-only
    }

    return {
        "tool": "geox_to_wealth_bridge",
        "prospect_id": prospect_id,
        "wealth_input": wealth_input,
        "bridged": True,
        "epistemic_source_preserved": epistemic_source,
        "admissibility_check": "PASSED",
    }
