"""
tests/test_session_error_taxonomy.py — Session error taxonomy: 400/401/403 differentiation.

FORGED 2026-07-18: Tests that enforce_session_or_400 returns correct http_status
for three error classes:
  400 — no token provided (client error, routine)
  401 — token present but invalid/forged (security event)
  403 — valid token, insufficient authority (policy event)
"""

from __future__ import annotations

import time
from unittest.mock import patch

from geox_mcp.session_enforcement import (
    enforce_session_or_400,
    _error_code_to_http_status,
)


# ── _error_code_to_http_status mapping ────────────────────────────────────


class TestErrorTaxonomyMapping:
    """Direct tests on the error-code → HTTP-status mapper."""

    def test_missing_session_is_400(self):
        assert _error_code_to_http_status("SESSION_MISSING") == 400

    def test_missing_actor_is_400(self):
        assert _error_code_to_http_status("ACTOR_MISSING") == 400

    def test_none_code_is_400(self):
        assert _error_code_to_http_status(None) == 400

    def test_invalid_session_is_401(self):
        assert _error_code_to_http_status("SESSION_INVALID") == 401

    def test_sct_invalid_is_401(self):
        assert _error_code_to_http_status("SCT_INVALID") == 401

    def test_actor_mismatch_is_401(self):
        assert _error_code_to_http_status("ACTOR_MISMATCH") == 401

    def test_transport_degraded_is_401(self):
        assert _error_code_to_http_status("TRANSPORT_DEGRADED") == 401

    def test_insufficient_authority_is_403(self):
        assert _error_code_to_http_status("INSUFFICIENT_AUTHORITY") == 403

    def test_unknown_code_defaults_to_401(self):
        assert _error_code_to_http_status("SOME_NEW_CODE") == 401


# ── enforce_session_or_400 integration tests ──────────────────────────────


class TestEnforceSessionTaxonomy:
    """Integration tests: enforce_session_or_400 returns correct http_status."""

    def test_no_session_returns_400(self):
        """No session_id → 400 Missing session (client error)."""
        result = enforce_session_or_400(None, "arif")
        assert result is not None
        assert result["error"] == "SESSION_MISSING"
        assert result["http_status"] == 400

    def test_no_actor_returns_400(self):
        """No actor_id → 400 (client error)."""
        result = enforce_session_or_400("SEAL-abcd1234efgh5678", None)
        assert result is not None
        assert result["error"] == "ACTOR_MISSING"
        assert result["http_status"] == 400

    def test_empty_session_returns_400(self):
        """Empty string session_id → 400 Missing session."""
        result = enforce_session_or_400("", "arif")
        assert result is not None
        assert result["error"] == "SESSION_MISSING"
        assert result["http_status"] == 400

    def test_forged_seal_returns_401(self):
        """Forged SEAL-* rejected by kernel → 401 Invalid session (security event)."""
        with patch("geox_mcp.session_enforcement._cached_kernel_verify", return_value=None):
            result = enforce_session_or_400("SEAL-deadbeef00000000", "arif")
            assert result is not None
            assert result["error"] == "SESSION_INVALID"
            assert result["http_status"] == 401

    def test_unreachable_kernel_returns_401(self):
        """arifOS unreachable (TRANSPORT_DEGRADED) → 401 (fail closed)."""
        from geox_mcp.session_enforcement import _TRANSPORT_DEGRADED
        with patch("geox_mcp.session_enforcement._cached_kernel_verify", return_value=_TRANSPORT_DEGRADED):
            result = enforce_session_or_400("SEAL-abcd1234efgh5678", "arif")
            assert result is not None
            assert result["error"] == "TRANSPORT_DEGRADED"
            assert result["http_status"] == 401

    def test_insufficient_authority_returns_403(self):
        """Valid session but authority too low → 403 (policy event)."""
        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = {
                "standing": {
                    "actor": {"claimed_id": "arif", "verified": True},
                    "authority": {"band": "OBSERVE_ONLY"},
                }
            }
            result = enforce_session_or_400(
                "SEAL-abcd1234efgh5678", "arif", required_authority="FULL"
            )
            assert result is not None
            assert result["error"] == "INSUFFICIENT_AUTHORITY"
            assert result["http_status"] == 403

    def test_valid_session_returns_none(self):
        """Valid session + sufficient authority → None (success)."""
        with patch("geox_mcp.session_enforcement._cached_kernel_verify") as mock_verify:
            mock_verify.return_value = {
                "standing": {
                    "actor": {"claimed_id": "arif", "verified": True},
                    "authority": {"band": "FULL"},
                }
            }
            result = enforce_session_or_400(
                "SEAL-abcd1234efgh5678", "arif", required_authority="OBSERVE_ONLY"
            )
            assert result is None

    def test_all_error_paths_carry_http_status(self):
        """Every non-None result carries an http_status field."""
        codes = [
            enforce_session_or_400(None, None),
            enforce_session_or_400("", "arif"),
        ]
        with patch("geox_mcp.session_enforcement._cached_kernel_verify", return_value=None):
            codes.append(enforce_session_or_400("SEAL-forgedtoken00000", "arif"))
        for result in codes:
            assert result is not None
            assert "http_status" in result
            assert result["http_status"] in (400, 401, 403)
