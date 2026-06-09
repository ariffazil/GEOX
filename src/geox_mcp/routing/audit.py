from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime

from .models import RouteQueryAuditRecord, RouteQueryInput, RouteQueryResult

logger = logging.getLogger("geox.route_query.audit")


def _hash_user_id(user_id: str) -> str:
    salt = os.getenv("GEOX_ROUTE_QUERY_AUDIT_SALT", "geox-route-query")
    return hashlib.sha256(f"{salt}:{user_id}".encode()).hexdigest()[:16]


def emit_route_audit(route_input: RouteQueryInput, result: RouteQueryResult) -> RouteQueryAuditRecord:
    record = RouteQueryAuditRecord(
        timestamp=datetime.now(UTC).isoformat(),
        request_id=route_input.request_id,
        user_id_hash=_hash_user_id(route_input.user_id),
        router_mode=result.mode,
        domain=result.domain,
        risk_level=result.risk_level,
        policy_flags=result.policy_flags,
        allowed_tools=result.allowed_tools,
        reason_code=result.reason_code,
        status=result.status,
        route_version=result.route_version,
        failure_class=result.failure_class,
    )
    logger.info("arifos_route_query_audit=%s", json.dumps(record.model_dump(mode="json"), sort_keys=True))
    return record
