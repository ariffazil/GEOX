"""RT1 recovery derivation — the suggested tool must be DERIVED and CALLABLE.

F2 TRUTH / F8 LAW enforcement for the RT1 guard.

The bug class this closes: RT1's rejection message hardcoded
``geox_surface_status`` as the recovery suggestion while that tool belonged to
NO capability pack — so it was invisible to every discovery profile
(``tools_for_profile('research')`` returned 20 of 26 tools). The guard
recommended a tool the caller could not resolve through the documented
discovery path. A literal suggestion cannot detect its own staleness; a
derived one can.

These tests assert the derivation contract:
  1. ghost rejection      -> geox_surface_status, and it is callable
  2. discovery-name rej.  -> geox_surface_status, and it is callable
  3. no callable recovery -> None (never a fabricated name)
  4. the pinned tool is present in every discovery profile (Step 2 invariant)

Lane 333d · Step 2 + Step 3 · 2026-10-01
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any

import pytest

from geox_mcp import registry as reg
from geox_mcp.registry import (
    derive_recovery_tool,
    pack_for_tool,
    public_tool_names,
    recovery_is_callable,
    tools_for_profile,
)

RECOVERY_TOOL = "geox_surface_status"


# ── Step 3: derivation contract ───────────────────────────────────────────


class TestRecoveryDerivation:
    """derive_recovery_tool must return a callable tool, or None."""

    def test_ghost_tool_rejection_suggests_callable_recovery(self) -> None:
        """Given RT1 rejects geox_well_desk_open (a ghost), the suggestion is
        geox_surface_status — and that tool is genuinely callable."""
        rejected = "geox_well_desk_open"
        # Precondition: it really is off the executable surface (it is a ghost /
        # deregistered name). If it ever becomes public again this test should
        # be revisited rather than silently passing.
        assert rejected not in public_tool_names()

        recovery = derive_recovery_tool(rejected)

        assert recovery == RECOVERY_TOOL
        assert recovery_is_callable(recovery) is True
        assert recovery in public_tool_names(), (
            f"derived recovery '{recovery}' is not in public_tool_names() — RT1 would recommend an uncallable tool"
        )

    def test_discovery_named_rejection_suggests_callable_recovery(self) -> None:
        """A tool whose name suggests discovery also resolves to the recovery tool."""
        rejected = "geox_discover_stuff"
        assert rejected not in public_tool_names()

        recovery = derive_recovery_tool(rejected)

        assert recovery == RECOVERY_TOOL
        assert recovery_is_callable(recovery) is True
        assert recovery in public_tool_names()

    def test_arbitrary_unknown_tool_suggests_callable_recovery(self) -> None:
        """Any unknown name still gets a real, callable recovery path."""
        recovery = derive_recovery_tool("totally_made_up_tool")

        assert recovery == RECOVERY_TOOL
        assert recovery_is_callable(recovery) is True

    def test_derived_recovery_is_never_fabricated(self) -> None:
        """Invariant: whatever is returned is always in the callable surface."""
        for rejected in (
            "geox_well_desk_open",
            "geox_discover_stuff",
            "geox_3d_model",
            "geox_claim",
            "geox_glof",
            "unknown",
            "",
        ):
            recovery = derive_recovery_tool(rejected)
            if recovery is not None:
                assert recovery in public_tool_names(), (
                    f"derive_recovery_tool('{rejected}') returned '{recovery}' "
                    f"which is NOT callable — fabricated recovery suggestion"
                )

    def test_negative_case_no_callable_recovery_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If no callable recovery tool exists, return None — never a name.

        Simulated by emptying the callable surface: every candidate then fails
        the ``name in callable_surface`` test, so derivation must yield None
        rather than fall back to a hardcoded literal.
        """
        monkeypatch.setattr(reg, "public_tool_names", lambda: [])

        assert derive_recovery_tool("geox_well_desk_open") is None
        assert recovery_is_callable(None) is False

    def test_negative_case_no_matching_name_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A callable surface with no recovery-shaped tool must also yield None."""
        monkeypatch.setattr(reg, "public_tool_names", lambda: ["geox_basin", "geox_claim"])

        assert derive_recovery_tool("geox_well_desk_open") is None

    def test_recovery_is_callable_rejects_none_and_unknown(self) -> None:
        assert recovery_is_callable(None) is False
        assert recovery_is_callable("") is False
        assert recovery_is_callable("geox_not_a_real_tool") is False

    def test_derived_recovery_is_non_mutating(self) -> None:
        """A recovery hint must not point at a mutating tool."""
        recovery = derive_recovery_tool("geox_well_desk_open")
        assert recovery is not None
        assert reg._is_non_mutating(recovery) is True


# ── Step 3: RT1 error message must carry the derived suggestion ───────────


class TestRT1MessageIsDerived:
    """The middleware error text must embed the derived name, not a literal.

    These tests call the REAL GeoxGovernanceMiddleware.on_call_tool — not a
    reimplementation of its composition. A test that reproduces the code it
    claims to verify measures its own construction, not the substrate.
    """

    @staticmethod
    def _middleware() -> Any:
        from geox_mcp.geox_middleware import GeoxGovernanceMiddleware

        return GeoxGovernanceMiddleware(
            canonical_public_tools={"geox_basin"},
            canonical_internal_tools=set(),
            canonical_compat_tools=set(),
            arifos_route_query_enabled=False,
            check_governance_fn=None,
        )

    @staticmethod
    def _invoke_rt1(tool_name: str) -> str:
        """Drive the real middleware to the RT1 branch; return its message."""
        import asyncio

        from fastmcp.exceptions import ToolError

        class _Msg:
            def __init__(self, name: str, arguments: dict) -> None:
                self.name = name
                self.arguments = arguments

        class _Ctx:
            def __init__(self, name: str) -> None:
                self.message = _Msg(name, {})

        mw = TestRT1MessageIsDerived._middleware()

        async def _run() -> str:
            try:
                await mw.on_call_tool(_Ctx(tool_name), lambda c: None)
            except ToolError as exc:
                return str(exc)
            return "<NO_TOOLERROR>"

        return asyncio.run(_run())

    def test_ghost_rejection_message_contains_derived_recovery(self) -> None:
        msg = self._invoke_rt1("geox_well_desk_open")
        assert msg.startswith("RT1_GUARD:"), msg
        assert RECOVERY_TOOL in msg
        assert "recommended_next: geox_surface_status" in msg
        assert "verified-callable=True" in msg

    def test_discovery_name_rejection_message_contains_derived_recovery(self) -> None:
        msg = self._invoke_rt1("geox_discover_stuff")
        assert msg.startswith("RT1_GUARD:"), msg
        assert "recommended_next: geox_surface_status" in msg

    def test_message_exposes_machine_checkable_marker(self) -> None:
        """The recommended_next token must be parseable, not buried in prose."""
        msg = self._invoke_rt1("some_unknown_tool")
        assert "recommended_next:" in msg

    def test_message_renders_null_when_no_callable_recovery(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Negative case, end-to-end through the real middleware:
        with no callable recovery tool the guard must say recommended_next: null
        and must NOT fabricate a tool name."""
        monkeypatch.setattr(reg, "public_tool_names", lambda: [])

        msg = self._invoke_rt1("geox_well_desk_open")

        assert msg.startswith("RT1_GUARD:"), msg
        assert "recommended_next: null" in msg
        assert "verified-callable=False" in msg
        # the hint must NOT recommend a specific uncallable tool
        assert "Use geox_surface_status(mode='registry')" not in msg
        assert "registry defect" in msg

    def test_source_has_no_hardcoded_recovery_literal(self) -> None:
        """Regression guard: the RT1 raise must not reintroduce a literal.

        The pre-fix code contained ``Use geox_surface_status(mode='registry')``
        as an f-string literal. This asserts the RT1 block now routes through
        derive_recovery_tool instead.
        """
        from pathlib import Path

        src = Path(reg.__file__).parent / "geox_middleware.py"
        text = src.read_text()

        assert "derive_recovery_tool" in text, "RT1 must derive its recovery suggestion"
        assert "recommended_next:" in text, "RT1 must expose recommended_next for machine parsing"

        # Isolate the RT1 block and assert it contains no literal tool name.
        start = text.index("# ── RT1: tool name must be in executable surface")
        end = text.index("# ── T7: Deprecation warning", start)
        rt1_block = text[start:end]
        assert RECOVERY_TOOL not in rt1_block, (
            "RT1 block must not hardcode 'geox_surface_status' — the suggestion must come from derive_recovery_tool()"
        )


# ── Step 2: recovery tool is pinned in every discovery profile ────────────


class TestRecoveryToolPinned:
    """geox_surface_status must be reachable through every profile."""

    def test_recovery_tool_has_a_capability_pack(self) -> None:
        assert pack_for_tool(RECOVERY_TOOL) is not None, (
            f"{RECOVERY_TOOL} belongs to no capability pack — it would be invisible to every discovery profile"
        )

    def test_recovery_tool_present_in_every_profile(self) -> None:
        from geox_mcp.registry import discovery_profile_names

        profiles = discovery_profile_names()
        assert profiles, "no discovery profiles defined"
        for profile in profiles:
            tools = tools_for_profile(profile)
            assert RECOVERY_TOOL in tools, (
                f"profile '{profile}' does not expose {RECOVERY_TOOL}; RT1 recovery would be invisible under this profile"
            )

    def test_research_profile_contains_recovery_tool(self) -> None:
        """The specific incident: research profile resolved 20 of 26 tools."""
        tools = tools_for_profile("research")
        assert RECOVERY_TOOL in tools

    def test_every_profile_is_a_subset_of_the_callable_surface(self) -> None:
        """No profile may advertise a tool that is not callable."""
        from geox_mcp.registry import discovery_profile_names

        callable_surface = set(public_tool_names())
        for profile in discovery_profile_names():
            stray = set(tools_for_profile(profile)) - callable_surface
            assert not stray, f"profile '{profile}' advertises non-callable tools: {sorted(stray)}"


# ── Cross-check: derivation and pinning agree ─────────────────────────────


def test_derived_recovery_is_visible_through_discovery() -> None:
    """End-to-end invariant closing the incident:
    the tool RT1 derives must also be discoverable through a profile.

    Before the fix these two disagreed — RT1 recommended geox_surface_status
    while every discovery profile omitted it.
    """
    recovery = derive_recovery_tool("geox_well_desk_open")
    assert recovery is not None
    assert recovery_is_callable(recovery)
    assert recovery in tools_for_profile("research")
    assert recovery in tools_for_profile("default")
