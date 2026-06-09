from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

_audit = logging.getLogger("geox.discovery.audit")


def log_route_decision(
    request_id: str,
    user_id: str,
    query_snippet: str,
    intent: str,
    mode: str,
    risk_level: str,
    reason_code: str,
    policy_flags: dict[str, Any],
) -> None:
    _emit({
        "event": "route_decision",
        "request_id": request_id,
        "user_id_hash": _hash(user_id),
        "query_snippet": query_snippet[:80],
        "router_intent": intent,
        "router_mode": mode,
        "risk_level": risk_level,
        "reason_code": reason_code,
        "policy_flags": policy_flags,
    })


def log_retrieval_completion(
    request_id: str,
    tools_invoked: list[str],
    exploit_docs: int,
    explore_docs: int,
    contradiction_docs: int,
    top_k: int,
    status: str,
    policy_violations: list[str] | None = None,
) -> None:
    _emit({
        "event": "retrieval_completion",
        "request_id": request_id,
        "tools_invoked": tools_invoked,
        "exploit_docs_used": exploit_docs,
        "explore_docs_used": explore_docs,
        "contradicting_docs_used": contradiction_docs,
        "top_k": top_k,
        "status": status,
        "policy_violations": policy_violations or [],
    })


def log_governance_check(
    request_id: str,
    claim_snippet: str,
    epistemic_tag: str,
    approved: bool,
    overclaim_flags: list[str],
) -> None:
    _emit({
        "event": "governance_check",
        "request_id": request_id,
        "claim_snippet": claim_snippet[:120],
        "epistemic_tag": epistemic_tag,
        "approved": approved,
        "overclaim_flags": overclaim_flags,
    })


def log_guard_block(request_id: str, calling_tool: str) -> None:
    _emit({
        "event": "guard_block",
        "request_id": request_id,
        "calling_tool": calling_tool,
        "reason": "retrieval_tool_called_before_router",
    })


def _emit(record: dict[str, Any]) -> None:
    record["timestamp"] = datetime.now(UTC).isoformat()
    _audit.info(json.dumps(record))


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]
