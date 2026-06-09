from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from .models import DomainHint, PolicyFlags, RetrievalBudget, RiskContext, RouteMode, RouteQueryInput, RouteQueryResult, TaskType

_POLICY_PATH = Path(__file__).resolve().with_name("arifos_route_query_policy_v1.json")


def _contains_any(query: str, patterns: list[str]) -> bool:
    query_lower = query.lower()
    return any(pattern in query_lower for pattern in patterns)


@lru_cache(maxsize=1)
def load_route_policy() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_POLICY_PATH.read_text(encoding="utf-8")))


def _resolve_mode(route_input: RouteQueryInput, policy: dict[str, Any]) -> tuple[RouteMode, str, str]:
    if route_input.task_type == TaskType.DECISION:
        return RouteMode.HYBRID, "task_type_decision_support", "Decision-support task requires exploit and explore lanes."
    if _contains_any(route_input.query, policy["explore_terms"]):
        return RouteMode.EXPLORE, "intent_exploration_mandatory", "Unknowns/contrast intent detected."
    if _contains_any(route_input.query, policy["exploit_terms"]) or route_input.task_type == TaskType.LOOKUP:
        return RouteMode.EXPLOIT, "intent_known_item_lookup", "Direct known item retrieval."
    if _contains_any(route_input.query, policy["hybrid_terms"]) or route_input.task_type == TaskType.ANALYSIS:
        return RouteMode.HYBRID, "intent_hybrid_assessment", "Assessment intent requires exploit and explore lanes."
    if route_input.current_hypothesis:
        return RouteMode.HYBRID, "hypothesis_present_hybrid", "Hypothesis present; hybrid routing preserves disconfirmation."
    return RouteMode.EXPLOIT, "default_safe_exploit", "No discovery markers detected; safe exploit route."


def _resolve_risk(route_input: RouteQueryInput, policy: dict[str, Any]) -> RiskContext:
    if route_input.risk_context is not None:
        return route_input.risk_context
    return RiskContext(policy["domain_defaults"][route_input.domain_hint.value])


def _build_policy_flags(mode: RouteMode, domain: DomainHint, risk: RiskContext) -> PolicyFlags:
    hse_or_high_risk = domain == DomainHint.HSE or risk == RiskContext.HIGH
    return PolicyFlags(
        explore_required=mode in {RouteMode.EXPLORE, RouteMode.HYBRID},
        disconfirmation_required=mode in {RouteMode.EXPLORE, RouteMode.HYBRID},
        conservative_language_required=hse_or_high_risk,
        citation_required=True,
        hold_if_low_confidence=hse_or_high_risk,
    )


def _filter_allowed_tools(mode: RouteMode, user_groups: list[str], policy: dict[str, Any]) -> tuple[list[str], list[str]]:
    user_scope = sorted({"all", *user_groups})
    allowed_tools: list[str] = []
    for tool_name in policy["tool_lanes"][mode.value]:
        entitlements = policy["entitlement_defaults"].get(tool_name, ["all"])
        if set(entitlements).intersection(user_scope):
            allowed_tools.append(tool_name)
    return allowed_tools, user_scope


def route_query(route_input: RouteQueryInput) -> RouteQueryResult:
    policy = load_route_policy()
    mode, reason_code, reason_text = _resolve_mode(route_input, policy)
    risk_level = _resolve_risk(route_input, policy)
    policy_flags = _build_policy_flags(mode, route_input.domain_hint, risk_level)
    budget = RetrievalBudget(**policy["budgets"][mode.value])
    allowed_tools, entitlement_scope = _filter_allowed_tools(mode, route_input.user_groups, policy)
    return RouteQueryResult(
        mode=mode,
        domain=route_input.domain_hint,
        risk_level=risk_level,
        policy_flags=policy_flags,
        retrieval_budget=budget,
        allowed_tools=allowed_tools,
        reason_code=reason_code,
        reason_text=reason_text,
        route_version=policy["route_version"],
        entitlement_scope=entitlement_scope,
    )


def fallback_route(route_input: RouteQueryInput, failure_class: str) -> RouteQueryResult:
    policy = load_route_policy()
    budget = RetrievalBudget(**policy["budgets"]["exploit"])
    return RouteQueryResult(
        mode=RouteMode.EXPLOIT,
        domain=route_input.domain_hint,
        risk_level=_resolve_risk(route_input, policy),
        policy_flags=PolicyFlags(
            explore_required=False,
            disconfirmation_required=False,
            conservative_language_required=route_input.domain_hint == DomainHint.HSE,
            citation_required=True,
            hold_if_low_confidence=route_input.domain_hint == DomainHint.HSE,
        ),
        retrieval_budget=budget,
        allowed_tools=["enterprise_graph_search"],
        reason_code="routing_fallback_exploit",
        reason_text="Routing unavailable. Defaulting to exploit for safety.",
        route_version=policy["route_version"],
        status="PARTIAL",
        failure_class=failure_class,
        safe_next_action="Retry route query or continue with citation-only exploit retrieval.",
        entitlement_scope=sorted({"all", *route_input.user_groups}),
    )
