"""
geox_mcp.session_enforcement — Session binding validation for GEOX.

Forged 2026-07-14 · Closes G2 (Session ID Not Enforced) and W5
(requires_actor_verified Not Enforced). Updated 2026-07-18: local SCT
validation replaces per-call arifOS kernel calls (kernel too slow for
per-tool-call validation).

Strategy:
  1. If caller passes an SCT (sct_v1.<base64>.<hmac>) → verify it through
     the federation SCT gate backed by arifOS. Decoding is never proof.
  2. If caller passes a SEAL-* session_id (not an SCT) → accept with
     basic format check. The SCT gate in the middleware handles full
     verification for SCT-bearing calls.
  3. Reject: empty, anonymous, malformed.

The SCT payload contains:
  - actor: claimant identity (e.g. "FORGE")
  - auth: authority band (OBSERVE_ONLY, LIMITED_MUTATE, FULL, SOVEREIGN)
  - sid: session ID (e.g. "SEAL-b6a8ec704ec64f40")
  - exp: expiry timestamp (unix)
  - iat: issued-at timestamp
  - av: actor verified (boolean)
  - ttl: time-to-live in seconds
  - allowed: list of allowed tools

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("geox_mcp.session_enforcement")


# Authority ranking for GEOX governance
AUTHORITY_LEVELS = (
    "OBSERVE_ONLY",
    "OPERATOR",
    "LIMITED_MUTATE",
    "FULL",
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


# ── C3 REDTEAM FIX 2026-07-18: cached kernel verification for SEAL-* paths ──
import threading

_ARIFOS_BASE = os.getenv("ARIFOS_BASE_URL", "http://localhost:8088")
_ARIFOS_TIMEOUT_S = float(os.getenv("ARIFOS_SESSION_TIMEOUT_S", "3.0"))
_KERNEL_VERIFY_TTL_S = 60.0  # cache TTL

# Three-state sentinel: arifOS unreachable is NOT the same as "valid".
_TRANSPORT_DEGRADED = object()

_kernel_verify_cache: dict[str, tuple[float, Any]] = {}
_kernel_verify_lock = threading.Lock()


def _cached_kernel_verify(
    session_id: str,
    actor_id: str | None = None,
) -> dict[str, Any] | None | object:
    """Cached arifOS kernel session verification (60s TTL).

    C3 REDTEAM FIX 2026-07-18: original per-call arifOS HTTP request was removed
    "because the kernel was too slow" — but format-only acceptance was the leak.
    Cache keeps the latency budget intact while restoring authoritative validation.

    Returns:
      - dict with session info if arifOS confirmed the session
      - None if arifOS rejected the session (definitive rejection)
      - _TRANSPORT_DEGRADED sentinel if arifOS is unreachable (indeterminate)
    """
    now = time.time()
    cache_key = f"{session_id}|{actor_id or ''}"

    with _kernel_verify_lock:
        cached = _kernel_verify_cache.get(cache_key)
        if cached is not None:
            ts, value = cached
            if now - ts < _KERNEL_VERIFY_TTL_S:
                return value
            # Expired — drop and refetch
            _kernel_verify_cache.pop(cache_key, None)

    # Cache miss / expired — call arifOS kernel
    try:
        import httpx

        validate_args: dict[str, Any] = {"mode": "validate", "session_id": session_id}
        if actor_id:
            validate_args["actor_id"] = actor_id

        r = httpx.post(
            f"{_ARIFOS_BASE}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "arif_init",
                    "arguments": validate_args,
                },
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=_ARIFOS_TIMEOUT_S,
        )
        if r.status_code == 200:
            data = r.json()
            result = data.get("result", {}) or {}
            parsed = result
            content = result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        try:
                            parsed = json.loads(item.get("text", "{}"))
                            break
                        except (json.JSONDecodeError, TypeError):
                            pass
            if isinstance(parsed.get("structuredContent"), dict):
                sc = parsed["structuredContent"]
                if "valid" in sc or "session_valid" in sc or "session_id" in sc:
                    parsed = sc
            elif isinstance(parsed.get("result"), dict):
                res_dict = parsed["result"]
                if "valid" in res_dict or "session_valid" in res_dict or "session_id" in res_dict:
                    parsed = res_dict

            status = parsed.get("status", "")
            effective_verdict = parsed.get("effective_verdict", "")
            standing_actor = parsed.get("standing", {}).get("actor", {})
            actor_verified = standing_actor.get("verified") is True or parsed.get("actor_verified") is True
            resp_sid = parsed.get("session_id") or parsed.get("standing", {}).get("session_id")
            # Check result.valid / session_valid
            result_valid = parsed.get("valid", False) or parsed.get("result", {}).get("valid", False)
            result_session_valid = parsed.get("session_valid", False) or parsed.get("result", {}).get("session_valid", False)

            if status == "ERROR" or effective_verdict == "VOID":
                value = None
            elif resp_sid == session_id or result_valid or result_session_valid or status in ("OK", "pending"):
                # Authoritative: kernel confirmed session valid or returned OK/pending
                value = parsed
            elif actor_verified:
                # Fallback: actor verified even if resp_sid missing
                value = parsed
            else:
                # C3 REDTEAM: no round-trip match AND no verified actor → reject
                value = None
        else:
            logger.warning("arifOS session_validate HTTP %s", r.status_code)
            value = None
    except Exception as exc:
        logger.warning("arifOS unreachable for session validation: %s", exc)
        value = _TRANSPORT_DEGRADED

    # Cache the result (including degraded state — arifOS outages shouldn't
    # hammer the kernel on every GEOX call).
    with _kernel_verify_lock:
        _kernel_verify_cache[cache_key] = (now, value)

    return value


def _verify_sct_authoritatively(
    token: str,
    actor_id: str,
    required_authority: str,
) -> Any:
    """Use the federation verifier; it calls arifOS and fails closed."""
    import sys

    aaa_root = "/root/AAA"
    if aaa_root not in sys.path:
        sys.path.insert(0, aaa_root)
    from governance.federation_sct import verify_federation_sct

    return verify_federation_sct(
        token,
        expected_actor=actor_id,
        required_authority=required_authority,
    )


def validate_session(
    session_id: str | None,
    actor_id: str | None,
    required_authority: str = "OBSERVE_ONLY",
) -> ValidationResult:
    """Validate a session_id + actor_id pair.

    Strategy (fast path first):
      1. If session_id is an SCT → verify signature/claims through arifOS
      2. If session_id is a SEAL-* string → basic format validation
      3. Reject: empty, anonymous, malformed

    Args:
        session_id: The session token (SCT or SEAL-* ID).
        actor_id:    The claimed actor.
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

    # ── PATH 1: SCT token — authoritative federation validation ────────
    if session_id.startswith("sct_v1."):
        try:
            verification = _verify_sct_authoritatively(
                session_id,
                actor_id,
                required_authority,
            )
        except Exception as exc:
            return ValidationResult(
                ok=False,
                error_code="TRANSPORT_DEGRADED",
                error_message=f"SCT verifier unavailable; rejected fail-closed ({type(exc).__name__})",
            )
        if not verification.ok:
            return ValidationResult(
                ok=False,
                error_code=verification.error_code or "SCT_INVALID",
                error_message=verification.error_message or "arifOS rejected SCT",
            )

        logger.info(
            "SCT_VALID: actor=%s auth=%s",
            verification.actor,
            verification.authority,
        )
        return ValidationResult(
            ok=True,
            session=verification.claims,
            actor=verification.actor or actor_id,
            authority=verification.authority or required_authority,
        )

    # ── PATH 2: SEAL-* session ID — must be verified against arifOS kernel ──
    # C3 REDTEAM FIX 2026-07-18: Format-only check was the leak. Any SEAL-<8+>
    # string passed (e.g., fabricated SEAL-deadbeef00000000). Per sovereign
    # ruling, GEOX must defer to arifOS kernel for session validity. Result is
    # cached for 60s to amortize per-call cost (was the original reason for
    # removing this check).
    if session_id.startswith("SEAL-"):
        if len(session_id) < 12:
            return ValidationResult(
                ok=False,
                error_code="SESSION_INVALID",
                error_message=f"SEAL session_id too short: {session_id}",
            )

        # Cached kernel verification (60s TTL)
        verified = _cached_kernel_verify(session_id, actor_id)
        if verified is _TRANSPORT_DEGRADED:
            return ValidationResult(
                ok=False,
                error_code="TRANSPORT_DEGRADED",
                error_message=("arifOS unreachable — cannot verify session. C3 REDTEAM: format-only acceptance is forbidden."),
            )
        if verified is None:
            return ValidationResult(
                ok=False,
                error_code="SESSION_INVALID",
                error_message=(f"arifOS rejected session_id (unknown, expired, or forged): {session_id}"),
            )

        # Kernel-verified: extract actor from response
        standing_actor = verified.get("standing", {}).get("actor", {})
        if isinstance(standing_actor, str):
            kernel_actor = standing_actor
        elif isinstance(standing_actor, dict):
            kernel_actor = (
                standing_actor.get("claimed_id")
                or standing_actor.get("canonical_id")
                or standing_actor.get("actor_id")
            )
        else:
            kernel_actor = None
        if not kernel_actor:
            kernel_actor = verified.get("actor_id") or verified.get("actor")
        if isinstance(kernel_actor, dict):
            kernel_actor = kernel_actor.get("actor_id") or kernel_actor.get("claimed_id") or kernel_actor.get("canonical_id")

        # ── FORGED 2026-07-27 (FI-008 · GEOX authority-sync fix) ──
        # The arifOS kernel `validate` mode returns the live authority band in
        # the `actor.authority_level` field of the response envelope, not in
        # `standing.authority.band` (which is the legacy/canonical path that
        # the kernel doesn't always populate on validate responses).
        # Walk the canonical field paths AND the live kernel envelope so a
        # sovereign ignition is never downgraded to OBSERVE_ONLY.
        raw_authority = (
            verified.get("standing", {}).get("authority", {}).get("band")
            or verified.get("authority")
            or (verified.get("actor") or {}).get("authority_level")
            or (verified.get("actor") or {}).get("authority")
            or (verified.get("standing") or {}).get("actor", {}).get("authority_level")
            or (verified.get("result") or {}).get("authority")
            or (verified.get("result") or {}).get("actor", {}).get("authority_level")
        )
        # Normalize OBSERVER→OBSERVE_ONLY, SOVEREIGN→SOVEREIGN, etc.
        _OBSERVER_TO_CANONICAL = {
            "OBSERVER": "OBSERVE_ONLY",
            "OPERATOR": "OPERATOR",
            "LIMITED_MUTATE": "LIMITED_MUTATE",
            "FULL": "FULL",
            "SOVEREIGN": "SOVEREIGN",
        }
        kernel_authority = _OBSERVER_TO_CANONICAL.get(
            str(raw_authority).upper() if raw_authority else "",
            raw_authority or required_authority,
        )

        # Actor binding check
        if (
            kernel_actor
            and isinstance(kernel_actor, str)
            and actor_id
            and isinstance(actor_id, str)
            and kernel_actor.lower() != "anonymous"
            and actor_id.lower() != "anonymous"
            and kernel_actor.casefold() != actor_id.casefold()
        ):
            return ValidationResult(
                ok=False,
                error_code="ACTOR_MISMATCH",
                error_message=(f"actor_id {actor_id!r} does not match kernel session actor {kernel_actor!r}"),
            )

        # Authority check
        if _authority_rank(kernel_authority) < _authority_rank(required_authority):
            return ValidationResult(
                ok=False,
                error_code="INSUFFICIENT_AUTHORITY",
                error_message=(f"session authority {kernel_authority!r} < required {required_authority!r}"),
            )

        logger.info(
            "SEAL_SESSION_KERNEL_VERIFIED: sid=%s actor=%s authority=%s",
            session_id,
            kernel_actor or actor_id,
            kernel_authority,
        )

        return ValidationResult(
            ok=True,
            session=verified,
            actor=kernel_actor or actor_id,
            authority=kernel_authority,
        )

    # ── PATH 3: Unknown format ─────────────────────────────────────────
    return ValidationResult(
        ok=False,
        error_code="SESSION_INVALID",
        error_message=f"session_id format not recognized: {session_id[:16]}...",
    )


def _error_code_to_http_status(error_code: str | None) -> int:
    """Map session validation error codes to HTTP status codes.

    Three-way differentiation (FORGED 2026-07-18):
      400 — client error: missing/malformed session (routine log)
      401 — security event: token present but invalid/forged (→ VAULT999)
      403 — policy event: valid token, insufficient authority
    """
    if error_code is None:
        return 400
    # 400 — missing or malformed client input
    if error_code in ("SESSION_MISSING", "ACTOR_MISSING"):
        return 400
    # 403 — valid identity but insufficient authority
    if error_code in ("INSUFFICIENT_AUTHORITY",):
        return 403
    # 401 — token present but invalid, forged, or unverifiable
    # SESSION_INVALID, SCT_INVALID, ACTOR_MISMATCH, TRANSPORT_DEGRADED
    return 401


def enforce_session_or_400(
    session_id: str | None,
    actor_id: str | None,
    required_authority: str = "OBSERVE_ONLY",
) -> dict[str, Any] | None:
    """Convenience wrapper: returns error dict if validation fails, None if OK.

    Error taxonomy (FORGED 2026-07-18):
      - 400 Missing session    — no token provided (client error, routine log)
      - 401 Invalid session    — token present but invalid/forged (security event)
      - 403 Insufficient auth  — valid token, authority too low (policy event)

    Usage in GEOX tool:
        err = enforce_session_or_400(session_id, actor_id, required_authority="OPERATOR")
        if err is not None:
            return err
    """
    result = validate_session(session_id, actor_id, required_authority)
    if result.ok:
        return None
    http_status = _error_code_to_http_status(result.error_code)
    return {
        "error": result.error_code,
        "http_status": http_status,
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
