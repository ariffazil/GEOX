from __future__ import annotations

import geox_mcp.routing.guard as guard_module
from geox_mcp.routing.guard import guard_route_requirement, record_route_decision
from geox_mcp.routing.models import DomainHint, RouteMode, RouteQueryInput, TaskType
from geox_mcp.routing.policy import fallback_route, route_query


def test_route_query_explore_from_unknowns_phrase() -> None:
    result = route_query(
        RouteQueryInput(
            query="What am I missing about Kinabalu basement porosity?",
            user_id="arif.fazil",
            user_groups=["geox-core", "subsurface"],
            domain_hint=DomainHint.GEOLOGY,
            task_type=TaskType.ANALYSIS,
            request_id="req-explore-001",
        )
    )
    assert result.mode == RouteMode.EXPLORE
    assert result.policy_flags.disconfirmation_required is True
    assert "geox_contrast_search" in result.allowed_tools


def test_route_query_exploit_for_known_lookup() -> None:
    result = route_query(
        RouteQueryInput(
            query="Find file KL2_TDR_Finalized.xlsx I edited last week",
            user_id="arif.fazil",
            user_groups=["geox-core"],
            domain_hint=DomainHint.GENERAL,
            task_type=TaskType.LOOKUP,
            request_id="req-exploit-001",
        )
    )
    assert result.mode == RouteMode.EXPLOIT
    assert result.allowed_tools == ["enterprise_graph_search"]


def test_fallback_route_marks_partial() -> None:
    route_input = RouteQueryInput(
        query="Assess risk tradeoffs for basin scenario",
        user_id="arif.fazil",
        user_groups=["geox-core"],
        domain_hint=DomainHint.GEOLOGY,
        task_type=TaskType.DECISION,
        request_id="req-fallback-001",
    )
    result = fallback_route(route_input, failure_class="ROUTER_DEPENDENCY_DOWN")
    assert result.status == "PARTIAL"
    assert result.failure_class == "ROUTER_DEPENDENCY_DOWN"


def test_route_decision_store_records_without_error() -> None:
    record_route_decision("req-guard-001", "explore")


def test_guard_blocks_protected_tool_without_route(monkeypatch) -> None:
    monkeypatch.setattr(guard_module, "GEOX_ROUTE_QUERY_GUARD_ENABLED", True)
    response = guard_route_requirement("enterprise_graph_search", {"request_id": "req-guard-002"})
    assert response is not None
    assert response.status_code == 428
