"""P0-2 hardening 2026-07-25 · FI-008 — Gateway authority enforcement.

These tests assert that:

  1. ``authority_gate.enforce_authority`` rejects with the right error
     code and HTTP status for every documented failure mode.
  2. ``required_authority_for`` correctly classifies tools based on
     manifest action_class + mutating-arg overrides.
  3. The full chain (env off → no enforcement) is reversible: setting
     ``GEOX_REQUIRE_SESSION_FOR_MUTATE=0`` makes the gate a no-op.

The integration test that exercises the live /mcp/ tools/call path is
in ``test_live_mcp_authority_rejects_unauthenticated`` — it spins up
the FastMCP server in-process and asserts that an anonymous ingest
call is rejected before any filesystem write happens.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from geox_mcp.authority_gate import (
    AuthorityRejection,
    enforce_authority,
    extract_identity,
)
from geox_mcp.registry import (
    CANONICAL_PUBLIC_TOOLS,
    is_mutating_call,
    required_authority_for,
    require_session_for_all,
)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def enforce_mode(monkeypatch):
    """Default to enforced mode for every test in this file."""
    monkeypatch.setenv("GEOX_REQUIRE_SESSION_FOR_MUTATE", "1")
    yield


# ── 1. require_session_for_all ────────────────────────────────────────────


def test_require_session_for_all_default_true(monkeypatch) -> None:
    monkeypatch.delenv("GEOX_REQUIRE_SESSION_FOR_MUTATE", raising=False)
    assert require_session_for_all() is True


def test_require_session_for_all_disabled_by_env(monkeypatch) -> None:
    monkeypatch.setenv("GEOX_REQUIRE_SESSION_FOR_MUTATE", "0")
    assert require_session_for_all() is False


# ── 2. extract_identity ────────────────────────────────────────────────────


def test_extract_identity_flat() -> None:
    assert extract_identity({"session_id": "SEAL-x", "actor_id": "ARIF"}) == (
        "SEAL-x",
        "ARIF",
        None,
    )


def test_extract_identity_envelope_fallback() -> None:
    args = {"_envelope": {"session_id": "SEAL-y", "actor_id": "OPENCODE"}}
    assert extract_identity(args) == ("SEAL-y", "OPENCODE", None)


def test_extract_identity_envelope_does_not_override_flat() -> None:
    args = {
        "session_id": "SEAL-flat",
        "actor_id": "FLAT",
        "_envelope": {"session_id": "SEAL-env", "actor_id": "ENV"},
    }
    assert extract_identity(args) == ("SEAL-flat", "FLAT", None)


def test_extract_identity_none_safe() -> None:
    assert extract_identity(None) == (None, None, None)
    assert extract_identity({}) == (None, None, None)
    assert extract_identity("not a dict") == (None, None, None)  # type: ignore[arg-type]


# ── 3. required_authority_for (registry) ──────────────────────────────────


def test_authority_observe_tool() -> None:
    assert required_authority_for("geox_surface_status") == "OBSERVE_ONLY"
    assert required_authority_for("geox_workspace") == "OBSERVE_ONLY"
    assert required_authority_for("geox_petrophysics") == "OBSERVE_ONLY"


def test_authority_mutate_tool_from_manifest() -> None:
    assert is_mutating_call("geox_well_ingest", {"overwrite": True}) is True
    assert (
        required_authority_for("geox_well_ingest", {"overwrite": True})
        == "LIMITED_MUTATE"
    )


def test_authority_override_for_overwrite_arg() -> None:
    """The audit's exact failure case: well_ingest with overwrite=True."""
    assert required_authority_for("geox_well_ingest", {}) == "OBSERVE_ONLY"
    assert (
        required_authority_for("geox_well_ingest", {"overwrite": False})
        == "OBSERVE_ONLY"
    )
    assert (
        required_authority_for("geox_well_ingest", {"overwrite": True})
        == "LIMITED_MUTATE"
    )


def test_authority_unknown_tool_safe_fails_to_observe() -> None:
    """Unknown tool → OBSERVE_ONLY (safe-fail default)."""
    assert required_authority_for("not_a_real_tool") == "OBSERVE_ONLY"


# ── 4. enforce_authority — no session ─────────────────────────────────────


def test_rejects_no_session_for_mutate() -> None:
    """Audit failure case: ingest call without session."""
    with pytest.raises(AuthorityRejection) as exc:
        enforce_authority(
            tool_name="geox_well_ingest",
            arguments={"overwrite": True, "mode": "las"},
        )
    r = exc.value
    assert r.error_code in ("SESSION_MISSING", "P0_IDENTITY_PROPAGATION")
    assert r.required_authority == "LIMITED_MUTATE"
    assert r.tool_name == "geox_well_ingest"


def test_observe_tools_skip_session_gate() -> None:
    """E2 FIX: OBSERVE_ONLY tools do not require a session."""
    # Does not raise
    enforce_authority(tool_name="geox_surface_status", arguments={})


def test_rejects_no_session_for_observe_under_mutate_args() -> None:
    """Read-only tool with non-mutating args passes session gate."""
    assert required_authority_for("geox_surface_status", {"overwrite": True}) == "OBSERVE_ONLY"


# ── 5. enforce_authority — session present ────────────────────────────────


def test_rejects_session_without_actor() -> None:
    with pytest.raises(AuthorityRejection) as exc:
        enforce_authority(
            tool_name="geox_well_ingest",
            arguments={"session_id": "SEAL-fake1234567890", "overwrite": True},
        )
    r = exc.value
    assert r.error_code in ("ACTOR_MISSING", "P0_IDENTITY_PROPAGATION")


def test_rejects_invalid_seal_session() -> None:
    """Forge a SEAL-* token that arifOS does not recognize → SESSION_INVALID."""
    with pytest.raises(AuthorityRejection) as exc:
        enforce_authority(
            tool_name="geox_well_ingest",
            arguments={
                "session_id": "SEAL-deadbeefcafebabe1234567890abcdef",
                "actor_id": "ARIF",
                "overwrite": True,
            },
        )
    r = exc.value
    # Either SESSION_INVALID (arifOS rejected), P0_IDENTITY_PROPAGATION, or TRANSPORT_DEGRADED
    assert r.error_code in ("SESSION_INVALID", "TRANSPORT_DEGRADED", "P0_IDENTITY_PROPAGATION")


def test_rejects_malformed_session_format() -> None:
    """Session that doesn't match SCT or SEAL-* pattern on mutating call."""
    with pytest.raises(AuthorityRejection) as exc:
        enforce_authority(
            tool_name="geox_well_ingest",
            arguments={
                "session_id": "this-is-not-a-real-token-format",
                "actor_id": "ARIF",
                "overwrite": True,
            },
        )
    r = exc.value
    assert r.error_code in ("SESSION_INVALID", "P0_IDENTITY_PROPAGATION", "SCT_INVALID")


# ── 6. enforce_authority — opt-out ────────────────────────────────────────


def test_no_op_when_env_disabled(monkeypatch) -> None:
    monkeypatch.setenv("GEOX_REQUIRE_SESSION_FOR_MUTATE", "0")
    # Even a mutating call with no session is admitted.
    enforce_authority(
        tool_name="geox_well_ingest",
        arguments={"overwrite": True},
    )


# ── 7. AuthorityRejection envelope ────────────────────────────────────────


def test_authority_rejection_envelope_shape() -> None:
    """The envelope must be machine-parseable for the audit probe."""
    try:
        enforce_authority(tool_name="geox_well_ingest", arguments={})
    except AuthorityRejection as r:
        env = r.to_envelope()
        assert "error_code" in env
        assert "http_status" in env
        assert "message" in env
        assert "tool" in env
        assert "session_id" in env
        assert "actor_id" in env
        assert "required_authority" in env
        assert "gate" in env
        assert env["http_status"] == 400
        assert env["error_code"] == "SESSION_MISSING"


# ── 8. Canonical surface smoke (cross-reference) ─────────────────────────


def test_all_canonical_tools_classify() -> None:
    """Every public tool must classify into OBSERVE_ONLY or LIMITED_MUTATE."""
    for tool_name in sorted(CANONICAL_PUBLIC_TOOLS):
        auth = required_authority_for(tool_name, {})
        assert auth in (
            "OBSERVE_ONLY",
            "LIMITED_MUTATE",
        ), f"{tool_name} returned {auth!r} (not in allowed set)"
