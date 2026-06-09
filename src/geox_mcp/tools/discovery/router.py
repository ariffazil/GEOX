from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

_POLICY_PATH = Path(__file__).parent / "policy_config.json"
_POLICY: dict[str, Any] = json.loads(_POLICY_PATH.read_text())

logger = logging.getLogger("geox.discovery.router")


def _classify_intent(query: str, task_type: str | None) -> str:
    q = query.lower()
    patterns = _POLICY["intent_patterns"]

    if task_type == "lookup":
        return "retrieve_known"

    # Order matters: disconfirmation > explore > decision > retrieve > default
    if any(p in q for p in patterns["disconfirmation"]):
        return "disconfirmation"
    if any(p in q for p in patterns["explore"]):
        return "explore"
    if any(p in q for p in patterns["decision_support"]):
        return "decision_support"
    if any(p in q for p in patterns["retrieve_known"]):
        return "retrieve_known"
    return "interpret"


def _classify_risk(query: str, domain_hint: str, risk_context: str | None) -> str:
    if risk_context in ("high", "critical"):
        return risk_context

    combined = (query + " " + domain_hint).lower()
    patterns = _POLICY["risk_patterns"]

    if any(p in combined for p in patterns["critical"]):
        return "critical"
    if any(p in combined for p in patterns["high"]) or domain_hint == "hse":
        return "high"
    if any(p in combined for p in patterns["medium"]):
        return "medium"
    return "low"


def _build_route(
    intent: str,
    risk: str,
    domain_hint: str,
    current_hypothesis: str | None,
) -> dict[str, Any]:
    if intent == "retrieve_known":
        mode = "exploit"
    elif intent == "disconfirmation":
        mode = "disconfirmation"
    elif intent == "explore":
        mode = "explore"
    elif intent == "decision_support":
        mode = "hybrid"
    else:
        mode = "hybrid" if current_hypothesis else "exploit"

    mode_cfg = dict(_POLICY["modes"][mode])
    risk_ovr = _POLICY["risk_overrides"].get(risk, {})

    confidence_ceiling: float = risk_ovr.get("confidence_ceiling", mode_cfg["confidence_ceiling"])
    disconfirmation_required: bool = risk_ovr.get("disconfirmation_required", mode_cfg["disconfirmation_required"])
    conservative_language_required: bool = risk_ovr.get("conservative_language_required", False)
    hold_if_low_confidence: bool = risk_ovr.get("hold_if_low_confidence", False)

    reason_parts = [f"intent={intent}", f"risk={risk}", f"mode={mode}"]
    if mode_cfg["explore_required"]:
        reason_parts.append("explore_mandatory=true")
    if disconfirmation_required:
        reason_parts.append("disconfirmation_required=true")
    if hold_if_low_confidence:
        reason_parts.append("HOLD_triggered=true")

    return {
        "mode": mode,
        "domain": domain_hint,
        "risk_level": risk,
        "policy_flags": {
            "explore_required": mode_cfg["explore_required"],
            "disconfirmation_required": disconfirmation_required,
            "conservative_language_required": conservative_language_required,
            "citation_required": True,
            "hold_if_low_confidence": hold_if_low_confidence,
        },
        "retrieval_budget": {
            "exploit_ratio": 1.0 - mode_cfg["explore_ratio"],
            "explore_ratio": mode_cfg["explore_ratio"],
            "min_explore_docs": mode_cfg["min_explore_docs"],
            "min_contradicting_docs": mode_cfg["min_contradicting_docs"],
        },
        "allowed_tools": list(_POLICY["allowed_tools_by_mode"].get(mode, ["enterprise_graph_search"])),
        "reason_code": ";".join(reason_parts),
        "reason_text": (
            f"Intent '{intent}', risk '{risk}', mode '{mode}'. "
            + ("Exploration mandatory. " if mode_cfg["explore_required"] else "")
            + ("Disconfirmation required. " if disconfirmation_required else "")
            + ("HOLD: strong assertions blocked. " if hold_if_low_confidence else "")
        ).strip(),
        "route_version": _POLICY["route_version"],
    }


async def arifos_route_query(
    query: str,
    user_id: str,
    request_id: str,
    user_groups: list[str] | None = None,
    domain_hint: str = "general",
    current_hypothesis: str | None = None,
    task_type: str | None = None,
    risk_context: str | None = None,
) -> dict[str, Any]:
    """
    Mandatory pre-router for all enterprise knowledge retrieval.

    MUST be called before office365_search, enterprise_graph_search,
    geox_contrast_search, or geox_disconfirm_evidence_scan.

    Returns the retrieval mode and policy flags. The planner MUST follow
    policy_flags.explore_required and policy_flags.disconfirmation_required
    — these are not suggestions, they are governance rules.

    After calling this: use allowed_tools to select retrieval tools.
    If policy_flags.hold_if_low_confidence=true, do NOT issue strong
    geological recommendations or capital commitments.

    Do NOT skip this tool to save tokens. Routing is governance.
    """
    from geox_mcp.tools.discovery.guard import register_route_completion
    from geox_mcp.tools.discovery.audit_logger import log_route_decision

    try:
        intent = _classify_intent(query, task_type)
        risk = _classify_risk(query, domain_hint, risk_context)
        output = _build_route(intent, risk, domain_hint, current_hypothesis)

        register_route_completion(request_id, output)
        log_route_decision(
            request_id=request_id,
            user_id=user_id,
            query_snippet=query[:80],
            intent=intent,
            mode=output["mode"],
            risk_level=risk,
            reason_code=output["reason_code"],
            policy_flags=output["policy_flags"],
        )

        return output

    except Exception as exc:
        logger.error("arifos_route_query failed: %s", exc)
        fallback: dict[str, Any] = {
            "mode": "exploit",
            "domain": domain_hint,
            "risk_level": "unknown",
            "policy_flags": {
                "explore_required": False,
                "disconfirmation_required": False,
                "conservative_language_required": False,
                "citation_required": True,
                "hold_if_low_confidence": False,
            },
            "retrieval_budget": {
                "exploit_ratio": 1.0,
                "explore_ratio": 0.0,
                "min_explore_docs": 0,
                "min_contradicting_docs": 0,
            },
            "allowed_tools": ["enterprise_graph_search"],
            "reason_code": "ROUTER_DEPENDENCY_DOWN",
            "reason_text": "Router failed — safe fallback to exploit mode. Routing unavailable.",
            "route_version": _POLICY.get("route_version", "v1.0.0"),
            "status": "PARTIAL",
            "failure_class": "ROUTER_DEPENDENCY_DOWN",
            "safe_next_action": "Proceed with exploit mode only. Re-attempt router after diagnosis.",
        }
        try:
            from geox_mcp.tools.discovery.guard import register_route_completion
            register_route_completion(request_id, fallback)
        except Exception:
            pass
        return fallback
