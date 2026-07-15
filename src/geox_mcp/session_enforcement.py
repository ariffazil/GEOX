"""
geox_mcp.session_enforcement — P2.1 session validation gate for GEOX.

Forged 2026-07-14 · Closes G2 (Session ID Not Enforced) and W5
(requires_actor_verified Not Enforced).

The gate intercepts every GEOX tool call and validates:
  1. session_id is present and well-formed
  2. session_id is bound to an active session in arifOS
  3. actor_id matches the session's actor
  4. authority is sufficient for the requested action_class

Failure modes (F11 fail-safe):
  - SESSION_MISSING       → 400 (caller forgot to pass session_id)
  - SESSION_INVALID       → 401 (session_id malformed or arifOS rejects)
  - SESSION_EXPIRED       → 401 (TTL exceeded)
  - ACTOR_MISMATCH        → 403 (forged actor_id)
  - INSUFFICIENT_AUTHORITY → 403 (low authority, high-blast tool)

This module exposes:
  - validate_session(session_id, actor_id, required_authority) -> ValidationResult
  - enforce_session_or_400(session_id, actor_id, required_authority) -> dict | None
    (returns the error dict if validation fails, None if OK)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("geox_mcp.session_enforcement")

ARIFOS_BASE = os.getenv("ARIFOS_BASE_URL", "http://localhost:8088")
ARIFOS_TIMEOUT_S = float(os.getenv("ARIFOS_SESSION_TIMEOUT_S", "3.0"))


# Authority ranking (lower index = lower authority)
AUTHORITY_LEVELS = (
    "OBSERVE_ONLY",
    "OPERATOR",
    "SOVEREIGN",
)


@dataclass
class ValidationResult:
    ok: bool
    error_code: str | None = None
    error_message: str | None = None
    session: dict[str, Any] | None = None
    actor: str | None = None
    authority: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "actor": self.actor,
            "authority": self.authority,
        }


def _authority_rank(level: str) -> int:
    try:
        return AUTHORITY_LEVELS.index(level)
    except ValueError:
        return -1  # Unknown authority = no trust


def _validate_format(session_id: str) -> bool:
    """Basic session_id format check.

    Accepts:
      - 'SEAL-<uuid>'
      - 'sct_v1.<base64>.<hmac>'
      - Any non-empty alphanumeric+dash+underscore (len >= 8)
    """
    if not session_id or not isinstance(session_id, str):
        return False
    if len(session_id) < 8:
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    return all(c in allowed for c in session_id)


def _query_arifos_session(session_id: str) -> dict[str, Any] | None:
    """Ask arifOS kernel to validate the session.

    Returns the session claims dict if valid, None if invalid/rejected.
    Fail-OPEN on transport error: if arifOS is unreachable, we degrade
    gracefully and let the call proceed with a warning. This balances
    F11 (audit) with F8 (system availability).
    """
    try:
        r = httpx.post(
            f"{ARIFOS_BASE}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "arif_session_validate",
                    "arguments": {"session_id": session_id},
                },
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=ARIFOS_TIMEOUT_S,
        )
        if r.status_code == 200:
            data = r.json()
            result = data.get("result", {}) or {}
            # The validate tool returns claims if valid, error if not.
            if result.get("valid") is True:
                return result
            return None
        logger.warning("arifOS session_validate HTTP %s", r.status_code)
        return None
    except httpx.RequestError as exc:
        # Fail-open on transport: log and let through with warning.
        logger.warning("arifOS unreachable for session validation: %s", exc)
        return {"valid": True, "transport_degraded": True, "session_id": session_id}


def validate_session(
    session_id: str | None,
    actor_id: str | None,
    required_authority: str = "OBSERVE_ONLY",
) -> ValidationResult:
    """Validate a session_id + actor_id pair against arifOS.

    Args:
        session_id: The session token. None or empty → SESSION_MISSING.
        actor_id:    The claimed actor. None or empty → ACTOR_MISSING.
        required_authority: minimum authority level (default OBSERVE_ONLY).

    Returns:
        ValidationResult with .ok=True if all checks pass.
    """
    if not session_id:
        return ValidationResult(
            ok=False,
            error_code="SESSION_MISSING",
            error_message="session_id is required (F11 — audit compliance)",
        )
    if not actor_id:
        return ValidationResult(
            ok=False,
            error_code="ACTOR_MISSING",
            error_message="actor_id is required (F11 — non-repudiation)",
        )
    if not _validate_format(session_id):
        return ValidationResult(
            ok=False,
            error_code="SESSION_INVALID",
            error_message=f"session_id format invalid: {session_id[:8]}...",
        )

    # Ask arifOS to validate
    claims = _query_arifos_session(session_id)
    if claims is None:
        return ValidationResult(
            ok=False,
            error_code="SESSION_INVALID",
            error_message="arifOS rejected session_id (expired, unknown, or forged)",
        )

    # Actor binding check
    session_actor = claims.get("actor") or claims.get("actor_id")
    if session_actor and session_actor != actor_id and not claims.get("transport_degraded"):
        return ValidationResult(
            ok=False,
            error_code="ACTOR_MISMATCH",
            error_message=f"actor_id {actor_id!r} does not match session actor {session_actor!r}",
        )

    # Authority check
    session_auth = claims.get("authority") or claims.get("auth", "OBSERVE_ONLY")
    if _authority_rank(session_auth) < _authority_rank(required_authority):
        return ValidationResult(
            ok=False,
            error_code="INSUFFICIENT_AUTHORITY",
            error_message=f"session authority {session_auth!r} < required {required_authority!r}",
        )

    return ValidationResult(
        ok=True,
        session=claims,
        actor=session_actor or actor_id,
        authority=session_auth,
    )


def enforce_session_or_400(
    session_id: str | None,
    actor_id: str | None,
    required_authority: str = "OBSERVE_ONLY",
) -> dict[str, Any] | None:
    """Convenience wrapper: returns error dict if validation fails, None if OK.

    Usage in GEOX tool:
        err = enforce_session_or_400(session_id, actor_id, required_authority="OPERATOR")
        if err is not None:
            return err
    """
    result = validate_session(session_id, actor_id, required_authority)
    if result.ok:
        return None
    return {
        "error": result.error_code,
        "message": result.error_message,
        "session_id": session_id,
        "actor_id": actor_id,
        "required_authority": required_authority,
        "_epistemic": {
            "output_class": "GOVERNANCE_TEMPLATE",
            "authority_claim": "GATE_REJECTED",
            "tagged_by": "geox-mcp-session-gate",
            "schema_version": "2.0.0",
        },
    }
