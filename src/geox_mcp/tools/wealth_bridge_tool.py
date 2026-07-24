"""
geox_to_wealth_bridge — Governed GEOX→WEALTH MCP client bridge
═══════════════════════════════════════════════════════════

Calls WEALTH organ via MCP call_tool() with federation envelope.
Replaces payload-only adapter with governed cross-organ transaction.

Constitutional rules:
  F2: epistemic_source is PASSED THROUGH, never upgraded
  F1: irreversible=False for read-only scoring calls
  F13: blocked nodes cannot enter WEALTH pipeline
  ABI v1.0: carries session_id, actor_id, trace_id, epistemic_tag

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("geox.wealth_bridge")

WEALTH_MCP_URL = "http://localhost:18082/mcp"
TIMEOUT = 10.0


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
    """Governed bridge: GEOX evidence → WEALTH capital computation via MCP.

    Creates an MCP session with WEALTH, invokes capital_primitive
    with NPV mode, and returns both GEOX source evidence and WEALTH
    capital interpretation. Never reinterprets geological observations.

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
        penalty_infinite: Whether penalty is infinite (blocked prospect).
        carbon_cost_usd: Carbon cost per tCO2e.
        delay_risk: Delay risk factor (0-1).
        required_modifications: List of required modifications.
        peace2: Peace² score.
        d_s: Entropy delta.
        session_id: arifOS session ID for federation envelope.
        actor_id: Authenticated actor identity.

    Returns:
        Federation response with GEOX source evidence + WEALTH result.
    """
    trace_id = f"geox-wealth-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    invocation_id = f"inv-{uuid.uuid4().hex[:8]}"
    geo_session = session_id or f"geox-bridge-{uuid.uuid4().hex[:8]}"
    geo_actor = actor_id or "geox-bridge"

    # F13: blocked nodes cannot cross
    if admissibility == "blocked":
        return {
            "tool": "geox_to_wealth_bridge",
            "error": "ADMISSIBILITY_BLOCKED",
            "message": f"Prospect {prospect_id} is governance-blocked.",
            "888_HOLD": True,
            "trace_id": trace_id,
            "epistemic_tag": epistemic_source,
            "status": "REFUSED",
        }

    # Maruah score: 1 - sigma_policy - modification_penalty
    mod_count = len(required_modifications or [])
    mod_penalty = mod_count * 0.05
    maruah = max(0.0, 1.0 - sigma_policy - mod_penalty)

    # GEOX evidence payload (preserved verbatim)
    geox_evidence = {
        "prospect_id": prospect_id,
        "npv_usd": npv_usd,
        "irr": irr,
        "breakeven_usd": breakeven_usd,
        "risk_geo": risk_geo,
        "sigma_market": sigma_market,
        "sigma_policy": sigma_policy,
        "maruah_score": round(maruah, 4),
        "admissibility": admissibility,
        "carbon_cost_usd": carbon_cost_usd,
        "epistemic_source": epistemic_source,
    }

    # ── Call WEALTH via MCP ────────────────────────────────────────────
    wealth_result = None
    wealth_error = None

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Step 1: Initialize MCP session with WEALTH
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "GEOX-bridge", "version": "v2026.07.23"},
                },
            }
            init_resp = await client.post(WEALTH_MCP_URL, json=init_req)
            init_resp.raise_for_status()
            init_data = init_resp.json()

            # Extract session ID from response header
            wealth_session = init_resp.headers.get("Mcp-Session-Id", "")
            if not wealth_session and "result" in init_data:
                wealth_session = init_data.get("result", {}).get("sessionId", "")

            # Step 2: Send initialized notification
            await client.post(
                WEALTH_MCP_URL,
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                headers={"Mcp-Session-Id": wealth_session} if wealth_session else {},
            )

            # Step 3: Call capital_primitive with NPV mode
            call_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "capital_primitive",
                    "arguments": {
                        "mode": "npv",
                        "cash_flows": [-npv_usd if npv_usd else 0],
                        "discount_rate": discount_rate,
                        "session_id": geo_session,
                        "actor_id": geo_actor,
                    },
                },
            }
            headers = {"Mcp-Session-Id": wealth_session} if wealth_session else {}
            call_resp = await client.post(WEALTH_MCP_URL, json=call_req, headers=headers)
            call_resp.raise_for_status()
            call_data = call_resp.json()

            if "result" in call_data:
                wealth_result = call_data["result"]
            elif "error" in call_data:
                wealth_error = call_data["error"]
            else:
                wealth_error = {"message": "Unexpected WEALTH response", "raw": call_data}

    except httpx.ConnectError:
        wealth_error = {"message": "WEALTH organ unreachable at localhost:18082"}
        logger.warning("WEALTH bridge: connection refused")
    except httpx.TimeoutException:
        wealth_error = {"message": f"WEALTH call timed out after {TIMEOUT}s"}
        logger.warning("WEALTH bridge: timeout")
    except Exception as exc:
        wealth_error = {"message": f"WEALTH bridge error: {exc}"}
        logger.error(f"WEALTH bridge: {exc}")

    # ── Build federation response ─────────────────────────────────────
    result = {
        "tool": "geox_to_wealth_bridge",
        "trace_id": trace_id,
        "invocation_id": invocation_id,
        "session_id": geo_session,
        "actor_id": geo_actor,
        "source_organ": "GEOX",
        "destination_organ": "WEALTH",
        "epistemic_tag": epistemic_source,
        "bridged": wealth_error is None,
        "geox_evidence": geox_evidence,
    }

    if wealth_result is not None:
        result["wealth_result"] = wealth_result
        result["status"] = "OK"
        result["message"] = f"Prospect {prospect_id} bridged to WEALTH capital_primitive"
    else:
        result["wealth_error"] = wealth_error
        result["status"] = "DEGRADED"
        result["message"] = (
            f"Prospect {prospect_id}: GEOX evidence ready, WEALTH unavailable ({wealth_error.get('message', 'unknown')})"
        )

    return result
