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
import httpx2  # FastMCP 4 migration

logger = logging.getLogger("geox.wealth_bridge")

WEALTH_MCP_URL = "http://localhost:18082/mcp"
TIMEOUT = 10.0


async def geox_to_wealth_bridge(
    prospect_id: str | None = None,
    mode: str = "prospect",
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
    # ── Sovereign Natural Capital mode inputs (P1, 2026-07-24) ──
    petroleum_reserves_mmboe: float | None = None,
    petroleum_reserve_epistemic: str | None = None,
    petroleum_replacement_ratio: float | None = None,
    petroleum_replacement_epistemic: str | None = None,
    water_security_index: float | None = None,
    water_security_epistemic: str | None = None,
    agricultural_land_ha: float | None = None,
    agricultural_land_epistemic: str | None = None,
    mineral_reserves_value_usd: float | None = None,
    mineral_reserves_epistemic: str | None = None,
    forest_cover_pct: float | None = None,
    forest_cover_epistemic: str | None = None,
    biodiversity_index: float | None = None,
    biodiversity_epistemic: str | None = None,
    flood_exposure_area_km2: float | None = None,
    flood_exposure_epistemic: str | None = None,
    coastal_exposure_km: float | None = None,
    coastal_exposure_epistemic: str | None = None,
    climate_risk_score: float | None = None,
    climate_risk_epistemic: str | None = None,
    energy_import_dependence_pct: float | None = None,
    energy_import_dependence_epistemic: str | None = None,
    physical_infrastructure_score: float | None = None,
    physical_infrastructure_epistemic: str | None = None,
    # ── Evidence provenance ──
    data_source: str | None = None,
) -> dict[str, Any]:
    """Governed bridge: GEOX evidence → WEALTH capital computation via MCP.

    Modes:
      prospect               — petroleum prospect NPV/IRR (default)
      sovereign_natural_capital — national physical balance sheet (P1 2026-07-24)

    The sovereign_natural_capital mode covers petroleum reserves, water security,
    agricultural land, minerals, forest/biodiversity, flood/coastal exposure,
    climate risk, energy-import dependence, and physical infrastructure.
    Every field preserves its own OBS / DER / INT / SPEC classification.
    GEOX supplies physical evidence; WEALTH may derive economic consequences.

    Args:
        mode: "prospect" or "sovereign_natural_capital"
        ... existing prospect params ...

    Returns:
        Federation response with GEOX source evidence + WEALTH result.
    """
    trace_id = f"geox-wealth-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    invocation_id = f"inv-{uuid.uuid4().hex[:8]}"
    geo_session = session_id or f"geox-bridge-{uuid.uuid4().hex[:8]}"
    geo_actor = actor_id or "geox-bridge"

    # ── SOVEREIGN NATURAL CAPITAL MODE ──────────────────────────────
    if mode == "sovereign_natural_capital":
        natural_capital_fields = {
            "petroleum_reserves_mmboe": (petroleum_reserves_mmboe, petroleum_reserve_epistemic or "ESTIMATE"),
            "petroleum_replacement_ratio": (petroleum_replacement_ratio, petroleum_replacement_epistemic or "ESTIMATE"),
            "water_security_index": (water_security_index, water_security_epistemic or "ESTIMATE"),
            "agricultural_land_ha": (agricultural_land_ha, agricultural_land_epistemic or "ESTIMATE"),
            "mineral_reserves_value_usd": (mineral_reserves_value_usd, mineral_reserves_epistemic or "ESTIMATE"),
            "forest_cover_pct": (forest_cover_pct, forest_cover_epistemic or "ESTIMATE"),
            "biodiversity_index": (biodiversity_index, biodiversity_epistemic or "ESTIMATE"),
            "flood_exposure_area_km2": (flood_exposure_area_km2, flood_exposure_epistemic or "ESTIMATE"),
            "coastal_exposure_km": (coastal_exposure_km, coastal_exposure_epistemic or "ESTIMATE"),
            "climate_risk_score": (climate_risk_score, climate_risk_epistemic or "ESTIMATE"),
            "energy_import_dependence_pct": (energy_import_dependence_pct, energy_import_dependence_epistemic or "ESTIMATE"),
            "physical_infrastructure_score": (physical_infrastructure_score, physical_infrastructure_epistemic or "ESTIMATE"),
        }
        provided = {k: {"value": v, "epistemic_tag": e} for k, (v, e) in natural_capital_fields.items() if v is not None}

        if not provided:
            return {
                "tool": "geox_to_wealth_bridge",
                "mode": "sovereign_natural_capital",
                "trace_id": trace_id,
                "status": "UNKNOWN",
                "message": "No natural capital data provided. Requires physical evidence inputs.",
                "fields_available": 0,
                "fields_total": len(natural_capital_fields),
                "epistemic_tag": "UNKNOWN",
                "boundary": "GEOX supplies physical evidence; WEALTH may derive economic consequences.",
                "w0": "OPERATOR_VETO_INTACT / EARTH_EVIDENCE_GATE",
            }

        geox_evidence = {
            "mode": "sovereign_natural_capital",
            "data_source": data_source or "user_reported",
            "fields_provided": len(provided),
            "fields_total": len(natural_capital_fields),
            "missing_fields": sorted(set(natural_capital_fields.keys()) - set(provided.keys())),
            "natural_capital": provided,
            "composite_epistemic_tag": (
                "OBSERVED"
                if all(e in ("OBSERVED", "DERIVED") for _, e in natural_capital_fields.values() if _[0] is not None)
                else "DERIVED"
            ),
            "sovereign_readiness": (
                "READY_FOR_WEALTH" if len(provided) >= 9 else "PARTIAL" if len(provided) >= 5 else "INSUFFICIENT"
            ),
        }

        # ── Bridge to WEALTH wisdom for capital consequence inference ──
        wealth_result = None
        wealth_error = None
        try:
            async with httpx.AsyncClient(
                timeout=TIMEOUT,
                # MCP Streamable HTTP (2025-11-25+): server 406s without this Accept pair
                headers={"Accept": "application/json, text/event-stream"},
            ) as client:
                init_resp = await client.post(
                    WEALTH_MCP_URL,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-11-25",
                            "capabilities": {},
                            "clientInfo": {"name": "GEOX-bridge", "version": "v2026.07.24"},
                        },
                    },
                )
                init_resp.raise_for_status()
                wealth_session = init_resp.headers.get("Mcp-Session-Id", "")
                await client.post(
                    WEALTH_MCP_URL,
                    json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                    headers={"Mcp-Session-Id": wealth_session} if wealth_session else {},
                )
                call_resp = await client.post(
                    WEALTH_MCP_URL,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "capital_wisdom",
                            "arguments": {
                                "mode": "evaluate",
                                "proposal": f"Sovereign natural capital assessment with {len(provided)} fields",
                                "context": {"natural_capital_fields": len(provided), "source": "GEOX-bridge"},
                                "session_id": geo_session,
                                "actor_id": geo_actor,
                            },
                        },
                    },
                    headers={"Mcp-Session-Id": wealth_session} if wealth_session else {},
                )
                call_resp.raise_for_status()
                wealth_data = call_resp.json()
                wealth_result = wealth_data.get("result") if "result" in call_resp else call_resp.get("error")
        except Exception as exc:
            wealth_error = {"message": str(exc)}
            logger.warning(f"GEOX natural capital → WEALTH bridge: {exc}")

        return {
            "tool": "geox_to_wealth_bridge",
            "mode": "sovereign_natural_capital",
            "trace_id": trace_id,
            "invocation_id": invocation_id,
            "session_id": geo_session,
            "actor_id": geo_actor,
            "source_organ": "GEOX",
            "destination_organ": "WEALTH",
            "bridged": wealth_error is None,
            "geox_evidence": geox_evidence,
            "wealth_result": wealth_result,
            "wealth_error": wealth_error,
            "status": "OK" if wealth_error is None else "DEGRADED",
            "message": (
                f"Natural capital assessment with {len(provided)}/{len(natural_capital_fields)} fields bridged to WEALTH"
            ),
            "boundary": "GEOX supplies physical evidence; WEALTH may derive economic consequences.",
        }

    # ── PROSPECT MODE (original) ─────────────────────────────────────
    if prospect_id is None:
        return {
            "tool": "geox_to_wealth_bridge",
            "error": "MISSING_PROSPECT_ID",
            "message": "prospect_id is required for mode='prospect'",
            "trace_id": trace_id,
            "status": "REFUSED",
        }

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

    # Canonical WealthInput contract (F2 epistemic preserved, F1 reversible)
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
        "irreversible": False,  # F1: bridge is read-only
    }

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
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            # MCP Streamable HTTP (2025-11-25+): server 406s without this Accept pair
            headers={"Accept": "application/json, text/event-stream"},
        ) as client:
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

    except (httpx.ConnectError, httpx2.ConnectError):
        wealth_error = {"message": "WEALTH organ unreachable at localhost:18082"}
        logger.warning("WEALTH bridge: connection refused")
    except (httpx.TimeoutException, httpx2.TimeoutException):
        wealth_error = {"message": f"WEALTH call timed out after {TIMEOUT}s"}
        logger.warning("WEALTH bridge: timeout")
    except Exception as exc:
        wealth_error = {"message": f"WEALTH bridge error: {exc}"}
        logger.error(f"WEALTH bridge: {exc}")

    # ── Build federation response ─────────────────────────────────────
    result = {
        "tool": "geox_to_wealth_bridge",
        "prospect_id": prospect_id,
        "trace_id": trace_id,
        "invocation_id": invocation_id,
        "session_id": geo_session,
        "actor_id": geo_actor,
        "source_organ": "GEOX",
        "destination_organ": "WEALTH",
        "epistemic_tag": epistemic_source,
        "epistemic_source_preserved": epistemic_source,  # F2 contract
        "admissibility_check": "PASSED",  # reached only when not blocked (888_HOLD path returns earlier)
        "wealth_input": wealth_input,
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
