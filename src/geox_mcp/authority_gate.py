"""
authority_gate — P0-2 gateway authority enforcement (Phase B).

Forged 2026-07-25 · FI-008 (kimi-code).

The audit identified that ``session_enforcement.py`` exists with full SCT /
SEAL-* / authority-band validation, but ZERO tools called it directly, and
the FastMCP middleware only enforced the SCT gate when an SCT token was
present. Anonymous OBSERVE-ONLY sessions could therefore trigger state-
changing tools (e.g. ``geox_well_ingest`` with ``overwrite=True`` writing
to ``/data/geox_las/audit/...``).

DOCTRINE
========

1. Every ``tools/call`` is admitted through ``enforce_authority`` BEFORE
   the tool body runs. Reversibility: the helper is opt-in via the env
   flag ``GEOX_REQUIRE_SESSION_FOR_MUTATE``; when the flag is off, the
   function is a no-op and the original behavior is restored.

2. ``required_authority_for(tool, args)`` (in ``registry.py``) resolves
   the minimum authority band for the call. OBSERVE_ONLY for read-only
   tools; LIMITED_MUTATE for tools whose ``action_class`` is MUTATE in
   the manifest, OR whose mutating-arg overrides fire (e.g.
   ``overwrite=True``).

3. ``session_enforcement.validate_session`` is the canonical session
   validator. It supports SCT tokens (verified via federation gate)
   and SEAL-* session IDs (verified via arifOS kernel, 60s cache).

4. Rejections carry HTTP-aligned status codes:
     - 401 SESSION_MISSING    — no session_id supplied
     - 401 SESSION_INVALID     — token present but invalid / forged
     - 401 ACTOR_MISMATCH      — session actor ≠ claimed actor
     - 403 INSUFFICIENT_AUTHORITY — session authority < required

REVERSIBILITY
=============

Set ``GEOX_REQUIRE_SESSION_FOR_MUTATE=0`` and the gate becomes a no-op.
Remove the call in ``geox_middleware.GeoxGovernanceMiddleware.on_call_tool``
to revert fully.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox_mcp.authority_gate")


# ── Result envelope ────────────────────────────────────────────────────────


class AuthorityRejection(Exception):
    """Raised when an authority gate rejects a tools/call.

    Carries the audit-grade error envelope so the middleware can serialize
    it as a ``ToolError`` and the client receives machine-parseable JSON.
    """

    def __init__(
        self,
        *,
        error_code: str,
        http_status: int,
        message: str,
        session_id: str | None = None,
        actor_id: str | None = None,
        required_authority: str | None = None,
        session_authority: str | None = None,
        tool_name: str = "",
    ) -> None:
        self.error_code = error_code
        self.http_status = http_status
        self.message = message
        self.session_id = session_id
        self.actor_id = actor_id
        self.required_authority = required_authority
        self.session_authority = session_authority
        self.tool_name = tool_name
        super().__init__(message)

    def to_envelope(self) -> dict[str, Any]:
        """Return the audit-grade rejection envelope for this error."""
        return {
            "error_code": self.error_code,
            "http_status": self.http_status,
            "message": self.message,
            "tool": self.tool_name,
            "session_id": self.session_id or "anonymous",
            "actor_id": self.actor_id or "anonymous",
            "required_authority": self.required_authority,
            "session_authority": self.session_authority,
            "gate": "P0-2 authority_gate (session_enforcement + registry.required_authority_for)",
        }


# ── Authority ranking (mirror of session_enforcement.AUTHORITY_LEVELS) ─────
AUTHORITY_LEVELS: tuple[str, ...] = (
    "OBSERVE_ONLY",
    "OPERATOR",
    "LIMITED_MUTATE",
    "FULL",
    "SOVEREIGN",
)


def _authority_rank(level: str | None) -> int:
    if not level:
        return -1
    try:
        return AUTHORITY_LEVELS.index(level)
    except ValueError:
        return -1


def _http_status_for(error_code: str | None) -> int:
    """Mirror of session_enforcement._error_code_to_http_status.

    Centralized so the authority_gate envelope carries HTTP-aligned status
    codes that match the federation taxonomy.
    """
    if error_code is None:
        return 400
    if error_code in ("SESSION_MISSING", "ACTOR_MISSING"):
        return 400
    if error_code in ("INSUFFICIENT_AUTHORITY",):
        return 403
    # SESSION_INVALID, SCT_INVALID, ACTOR_MISMATCH, TRANSPORT_DEGRADED
    return 401


# ── Identity extraction ────────────────────────────────────────────────────


def extract_identity(
    arguments: dict[str, Any] | None,
) -> tuple[str | None, str | None, str | None]:
    """Extract (session_id, actor_id, session_token) from tool arguments + _envelope fallback.

    FORGED 2026-07-27 (FI-008 · GEOX authority-sync fix):
      The arifOS kernel `validate` mode downgrades live authority to OBSERVER
      on SEAL-* paths (returns actor.authority_level=OBSERVER even when
      the original session was SOVEREIGN). To bypass the downgrade we
      also extract the SCT session_token from arguments/_envelope so
      `validate_session` can route through the SCT path, which decodes
      the signed payload and reads the real `auth` claim (e.g. "FULL").

    Args:
        arguments: parsed tool arguments (possibly containing _envelope).

    Returns:
        (session_id, actor_id, session_token) — any may be None.
    """
    if not isinstance(arguments, dict):
        return None, None, None
    session_id = arguments.get("session_id")
    actor_id = arguments.get("actor_id")
    session_token = (
        arguments.get("session_token")
        or arguments.get("sct")
        or arguments.get("arifos_sct")
    )
    env = arguments.get("_envelope")
    if isinstance(env, dict):
        if not session_id and env.get("session_id"):
            session_id = env["session_id"]
        if not actor_id and env.get("actor_id"):
            actor_id = env["actor_id"]
        if not session_token:
            for k in ("session_token", "sct", "arifos_sct"):
                if env.get(k):
                    session_token = env[k]
                    break
    return session_id, actor_id, session_token


# ── Main gate ─────────────────────────────────────────────────────────────


def enforce_authority(
    *,
    tool_name: str,
    arguments: dict[str, Any] | None,
) -> None:
    """Enforce session + authority for a tools/call. Raises AuthorityRejection.

    No-op when the env flag ``GEOX_REQUIRE_SESSION_FOR_MUTATE`` is off.
    When on, every call must carry a verified session whose authority band
    ranks at or above ``required_authority_for(tool, args)``.
    """
    # Lazy imports to avoid circular dependency at module load.
    from geox_mcp.registry import (
        require_session_for_all,
        required_authority_for,
    )
    from geox_mcp.session_enforcement import validate_session

    if not require_session_for_all():
        # Backward-compat path: GEOX was permissive pre-P0-2. Honor the
        # operator's choice not to enforce (dev / smoke test environments).
        logger.debug(
            "AUTH_GATE: skipped (GEOX_REQUIRE_SESSION_FOR_MUTATE=0) tool=%s",
            tool_name,
        )
        return

    session_id, actor_id, session_token = extract_identity(arguments or {})
    required = required_authority_for(tool_name, arguments or {})

    # ── FORGED 2026-07-27 (FI-008 · GEOX authority-sync fix) ──
    # When the caller presents a session_token (SCT), prefer the SCT path
    # so we read the real `auth` claim from the signed payload instead
    # of the kernel's downgraded validate-mode band.
    if session_token and session_token.startswith("sct_v1."):
        session_id = session_token

    # ── Validate session (SCT or SEAL-*) ──
    # session_enforcement.validate_session handles every error path
    # including missing session_id / actor_id. Its error_code + HTTP
    # status mapping is the canonical federation taxonomy:
    #   SESSION_MISSING / ACTOR_MISSING  → 400  (client error)
    #   SESSION_INVALID / SCT_INVALID    → 401  (security event)
    #   ACTOR_MISMATCH / TRANSPORT_DEGRADED → 401
    #   INSUFFICIENT_AUTHORITY           → 403  (policy event)
    result = validate_session(
        session_id=session_id,
        actor_id=actor_id,
        required_authority=required,
    )

    if not result.ok:
        http_status = _http_status_for(result.error_code)
        # Synthesize a session_id for the envelope when missing, so the
        # audit trail always has a non-null value.
        envelope_session = session_id or "anonymous"
        envelope_actor = actor_id or result.actor or "anonymous"
        raise AuthorityRejection(
            error_code=result.error_code or "SESSION_INVALID",
            http_status=http_status,
            message=result.error_message or "session validation failed",
            session_id=envelope_session,
            actor_id=envelope_actor,
            required_authority=required,
            session_authority=result.authority,
            tool_name=tool_name,
        )

    # ── Defense-in-depth rank check ──
    # validate_session already enforces the rank when required_authority
    # is supplied; this re-check guards against future refactors that
    # might drop the argument silently.
    if _authority_rank(result.authority) < _authority_rank(required):
        raise AuthorityRejection(
            error_code="INSUFFICIENT_AUTHORITY",
            http_status=403,
            message=(
                f"session authority {result.authority!r} < required {required!r} "
                f"for tool '{tool_name}'"
            ),
            session_id=session_id or "anonymous",
            actor_id=actor_id or result.actor or "anonymous",
            required_authority=required,
            session_authority=result.authority,
            tool_name=tool_name,
        )

    logger.info(
        "AUTH_OK: tool=%s session=%s actor=%s authority=%s required=%s",
        tool_name,
        session_id[:12] if session_id else "anonymous",
        result.actor or actor_id or "anonymous",
        result.authority,
        required,
    )
