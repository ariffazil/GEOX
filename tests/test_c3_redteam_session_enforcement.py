"""
tests/test_c3_redteam_session_enforcement.py — C3 REDTEAM acceptance tests.

Forged 2026-07-18 by kimi-code (FI-008) per sovereign (888) directive.

Acceptance tests (per sovereign ruling, 2026-07-18):

  1. Fabricated session_id → returns SESSION_INVALID (HOLD).
     Specifically: SEAL-deadbeef00000000 + fake actor → SESSION_INVALID,
     NOT format-only acceptance.

  2. Valid session (kernel-verified) → receipt carries real session_id,
     NEVER "anonymous".

  3. SCT token → still validated locally (no regression on fast path).

  4. Actor mismatch on valid session → ACTOR_MISMATCH (HOLD).

  5. Transport degraded (arifOS unreachable) → TRANSPORT_DEGRADED (HOLD),
     NOT format-only fallback. C3 REDTEAM: format-only is forbidden.

DITEMPA BUKAN DIBERI — forged, not given.
"""

from __future__ import annotations

import base64
import json
import time
from types import SimpleNamespace
from unittest.mock import patch

from geox_mcp.session_enforcement import (
    _TRANSPORT_DEGRADED,
    validate_session,
)

# ─── helpers ────────────────────────────────────────────────────────────────


def _make_sct(actor: str = "arif", authority: str = "SOVEREIGN", ttl: int = 3600,
              verified: bool = True) -> str:
    """Build a valid sct_v1 token for tests."""
    now = int(time.time())
    payload = {
        "actor": actor,
        "auth": authority,
        "sid": f"SEAL-{int(time.time()*1000):x}",
        "exp": now + ttl,
        "iat": now,
        "av": verified,
        "ttl": ttl,
        "allowed": ["*"],
    }
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b"=").decode()
    return f"sct_v1.{payload_b64}.deadbeef"


def _mock_kernel_response(
    session_id: str,
    actor_id: str,
    *,
    actor_verified: bool = True,
    authority: str = "OPERATOR",
    status: str = "OK",
    verdict: str = "SEAL",
    session_token: str | None = None,
) -> dict:
    """Build a mock arif_init(mode=validate) response."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": status,
                        "effective_verdict": verdict,
                        "session_id": session_id,
                        "session_token": session_token,
                        "actor_id": actor_id,
                        "standing": {
                            "actor": {
                                "claimed_id": actor_id,
                                "canonical_id": actor_id,
                                "verified": actor_verified,
                            },
                            "authority": {"band": authority},
                            "session_id": session_id,
                        },
                    }),
                }
            ]
        },
    }


# ─── Acceptance Test 1: fabricated session → HOLD ───────────────────────────


class TestC3RedteamFabricatedSession:
    """A fabricated session_id must be REJECTED, not format-accepted."""

    def test_fabricated_seal_deadbeef_returns_hold(self):
        """The exact session_id from the sovereign's REDTEAM must be rejected."""
        # Patch out the network so we test the format-vs-kernel decision.
        # If the kernel is reachable, it will reject (returns None).
        # If unreachable, _TRANSPORT_DEGRADED is returned (also HOLD, NOT format-only).
        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = None  # kernel rejected
            result = validate_session(
                session_id="SEAL-deadbeef00000000",
                actor_id="fake-actor",
                required_authority="OBSERVE_ONLY",
            )

        assert result.ok is False, (
            "C3 REDTEAM REGRESSION: fabricated session_id was accepted. "
            "Format-only acceptance is forbidden after 2026-07-18 fix."
        )
        assert result.error_code in ("SESSION_INVALID", "TRANSPORT_DEGRADED"), (
            f"Expected SESSION_INVALID or TRANSPORT_DEGRADED, got {result.error_code}"
        )

    def test_fabricated_session_transport_degraded_still_holds(self):
        """Even when arifOS is unreachable, format-only is FORBIDDEN."""
        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = _TRANSPORT_DEGRADED
            result = validate_session(
                session_id="SEAL-fabricated-deadbeef",
                actor_id="fake",
                required_authority="OBSERVE_ONLY",
            )

        assert result.ok is False, "Format-only fallback is forbidden (C3 REDTEAM)"
        assert result.error_code == "TRANSPORT_DEGRADED"

    def test_short_session_id_rejected(self):
        """Even valid prefix, too short is rejected."""
        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = None
            result = validate_session(
                session_id="SEAL-abc",
                actor_id="anyone",
                required_authority="OBSERVE_ONLY",
            )
        assert result.ok is False
        assert result.error_code == "SESSION_INVALID"


# ─── Acceptance Test 2: valid session → real session_id in receipt ──────────


class TestC3RedteamValidSessionPreservesId:
    """A kernel-verified valid session must carry the REAL session_id."""

    def test_valid_session_returns_real_session_id_not_anonymous(self):
        """The receipt should carry the kernel-confirmed session_id."""
        valid_session_id = "SEAL-1234567890abcdef"
        valid_actor = "arif"

        # Mock the cached kernel verifier to return a verified response
        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = {
                "session_id": valid_session_id,
                "session_token": "sct_v1.token.signature",
                "actor_id": valid_actor,
                "standing": {
                    "actor": {
                        "claimed_id": valid_actor,
                        "canonical_id": valid_actor,
                        "verified": True,
                    },
                    "authority": {"band": "SOVEREIGN"},
                    "session_id": valid_session_id,
                },
            }

            result = validate_session(
                session_id=valid_session_id,
                actor_id=valid_actor,
                required_authority="OBSERVE_ONLY",
            )

        assert result.ok is True
        # Critical: real session_id must be preserved (NOT "anonymous")
        assert result.actor == valid_actor, (
            f"Receipt actor was {result.actor!r}, expected real actor {valid_actor!r}. "
            "Anonymous coercion is forbidden."
        )
        assert result.session is not None
        assert result.session.get("session_id") == valid_session_id

    def test_valid_session_preserves_authority_band(self):
        """The kernel-confirmed authority band must be preserved, not the requested one."""
        valid_session_id = "SEAL-test-authority"
        valid_actor = "arif"

        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = {
                "session_id": valid_session_id,
                "actor_id": valid_actor,
                "standing": {
                    "actor": {
                        "claimed_id": valid_actor,
                        "verified": True,
                    },
                    "authority": {"band": "SOVEREIGN"},
                    "session_id": valid_session_id,
                },
            }
            result = validate_session(
                session_id=valid_session_id,
                actor_id=valid_actor,
                required_authority="OBSERVE_ONLY",  # asked for OBSERVE_ONLY
            )

        assert result.ok is True
        assert result.authority == "SOVEREIGN", (
            "Authority band must reflect kernel-confirmed band, not the requested minimum."
        )


# ─── Acceptance Test 3: SCT path still works (no regression) ────────────────


class TestC3RedteamSctStillWorks:
    """SCT path must require authoritative signature verification."""

    def test_valid_sct_with_verified_actor_passes(self):
        sct = _make_sct(actor="arif", authority="SOVEREIGN", verified=True)
        with patch("geox_mcp.session_enforcement._verify_sct_authoritatively") as verify:
            verify.return_value = SimpleNamespace(
                ok=True,
                claims={"sid": "SEAL-real", "actor": "arif"},
                actor="arif",
                authority="SOVEREIGN",
                error_code=None,
                error_message=None,
            )
            result = validate_session(
                session_id=sct,
                actor_id="arif",
                required_authority="OPERATOR",
            )
        assert result.ok is True
        assert result.actor == "arif"
        assert result.authority == "SOVEREIGN"

    def test_forged_sct_hmac_rejected(self):
        sct = _make_sct(actor="arif")
        with patch("geox_mcp.session_enforcement._verify_sct_authoritatively") as verify:
            verify.return_value = SimpleNamespace(
                ok=False,
                claims=None,
                actor=None,
                authority=None,
                error_code="SCT_INVALID",
                error_message="arifOS rejected SCT",
            )
            result = validate_session(
                session_id=sct,
                actor_id="arif",
                required_authority="OBSERVE_ONLY",
            )
        assert result.ok is False
        assert result.error_code == "SCT_INVALID"

    def test_sct_actor_mismatch_rejected(self):
        sct = _make_sct(actor="arif", authority="OPERATOR")
        with patch("geox_mcp.session_enforcement._verify_sct_authoritatively") as verify:
            verify.return_value = SimpleNamespace(
                ok=False,
                claims=None,
                actor="arif",
                authority="OPERATOR",
                error_code="ACTOR_MISMATCH",
                error_message="SCT actor mismatch",
            )
            result = validate_session(
                session_id=sct,
                actor_id="someone-else",
                required_authority="OBSERVE_ONLY",
            )
        assert result.ok is False
        assert result.error_code == "ACTOR_MISMATCH"


# ─── Acceptance Test 4: actor binding on kernel-verified session ───────────


class TestC3RedteamActorBinding:
    """Kernel-verified session with mismatched actor_id must HOLD."""

    def test_kernel_verified_actor_mismatch_rejected(self):
        valid_session_id = "SEAL-bound-session"
        session_actor = "arif"

        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = {
                "session_id": valid_session_id,
                "actor_id": session_actor,
                "standing": {
                    "actor": {
                        "claimed_id": session_actor,
                        "canonical_id": session_actor,
                        "verified": True,
                    },
                    "authority": {"band": "SOVEREIGN"},
                    "session_id": valid_session_id,
                },
            }

            # Caller claims a different actor
            result = validate_session(
                session_id=valid_session_id,
                actor_id="forged-actor",
                required_authority="OBSERVE_ONLY",
            )

        assert result.ok is False
        assert result.error_code == "ACTOR_MISMATCH"


# ─── Acceptance Test 5: insufficient authority ─────────────────────────────


class TestC3RedteamInsufficientAuthority:
    """Kernel-verified session with low authority must HOLD for high-blast tools."""

    def test_observe_session_cannot_run_sovereign_tool(self):
        valid_session_id = "SEAL-observer"

        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = {
                "session_id": valid_session_id,
                "actor_id": "observer",
                "standing": {
                    "actor": {
                        "claimed_id": "observer",
                        "verified": True,
                    },
                    "authority": {"band": "OBSERVE_ONLY"},
                    "session_id": valid_session_id,
                },
            }
            result = validate_session(
                session_id=valid_session_id,
                actor_id="observer",
                required_authority="SOVEREIGN",
            )

        assert result.ok is False
        assert result.error_code == "INSUFFICIENT_AUTHORITY"


# ─── Acceptance Test 6: unknown format ──────────────────────────────────────


class TestC3RedteamUnknownFormat:
    """Anything that doesn't match SCT or SEAL-* format is rejected outright."""

    def test_unknown_prefix_rejected(self):
        result = validate_session(
            session_id="garbage-no-prefix-here-1234",
            actor_id="anyone",
            required_authority="OBSERVE_ONLY",
        )
        assert result.ok is False
        assert result.error_code == "SESSION_INVALID"

    def test_empty_session_auto_mints_anon(self):
        """Empty session_id → auto-mint ANON-xxx (not rejected)."""
        result = validate_session(
            session_id="",
            actor_id="anyone",
            required_authority="OBSERVE_ONLY",
        )
        assert result.ok is True
        assert result.session is not None
        assert result.session["type"] == "anon"
        assert result.session["session_id"].startswith("ANON-")
        assert result.session["auto_minted"] is True


# ─── Acceptance Test 7: anonymous coercion is GONE ──────────────────────────


class TestC3RedteamNoAnonymousCoercion:
    """The receipt must never carry the literal 'anonymous' for a valid call."""

    def test_kernel_verified_session_does_not_coerce_to_anonymous(self):
        valid_session_id = "SEAL-real-session-id-12345"
        valid_actor = "real-actor"

        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = {
                "session_id": valid_session_id,
                "actor_id": valid_actor,
                "standing": {
                    "actor": {
                        "claimed_id": valid_actor,
                        "verified": True,
                    },
                    "authority": {"band": "OPERATOR"},
                    "session_id": valid_session_id,
                },
            }
            result = validate_session(
                session_id=valid_session_id,
                actor_id=valid_actor,
                required_authority="OBSERVE_ONLY",
            )

        assert result.ok is True
        # The fix: real actor_id must be preserved, NOT "anonymous"
        assert result.actor != "anonymous", (
            "C3 REDTEAM: result.actor was coerced to 'anonymous'. "
            "Valid kernel-verified sessions must preserve real actor_id."
        )
        assert result.actor == valid_actor
