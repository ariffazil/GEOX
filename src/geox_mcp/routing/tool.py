from __future__ import annotations

from pydantic import ValidationError

from .audit import emit_route_audit
from .guard import record_route_decision
from .models import DomainHint, RiskContext, RouteQueryInput, TaskType
from .policy import fallback_route, route_query


async def arifos_route_query(
    query: str,
    user_id: str,
    request_id: str,
    user_groups: list[str] | None = None,
    domain_hint: DomainHint = DomainHint.GENERAL,
    current_hypothesis: str | None = None,
    task_type: TaskType | None = None,
    risk_context: RiskContext | None = None,
) -> dict:
    try:
        route_input = RouteQueryInput(
            query=query,
            user_id=user_id,
            user_groups=user_groups or [],
            domain_hint=domain_hint,
            current_hypothesis=current_hypothesis,
            task_type=task_type,
            risk_context=risk_context,
            request_id=request_id,
        )
        result = route_query(route_input)
    except ValidationError as exc:
        raise ValueError(f"MISSING_REQUIRED_INPUT: {exc}") from exc
    except Exception:
        route_input = RouteQueryInput(
            query=query,
            user_id=user_id,
            user_groups=user_groups or [],
            domain_hint=domain_hint,
            current_hypothesis=current_hypothesis,
            task_type=task_type,
            risk_context=risk_context,
            request_id=request_id,
        )
        result = fallback_route(route_input, failure_class="ROUTER_POLICY_INVALID")

    record_route_decision(route_input.request_id, result.mode.value)
    emit_route_audit(route_input, result)
    return result.model_dump(mode="json")
