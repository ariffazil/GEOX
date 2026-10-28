"""2026-10-28 — geox_basin unified-mode dispatch must never silently fall through.

Measured live 2026-10-28 on :8081: mode in {macrostrat, macrostrat_units,
mass_balance, thermal, massbalance, mass_balance_mb} all returned the IDENTICAL
basin-profile payload with ok:true and mode:"overview". The MCP schema exposes
`mode` as a bare string (no enum), so a caller had no way to detect that the
requested mode was not executed.

Root cause: `mode` is dispatched by explicit branches; every unhandled string
fell through to the profile default. af-fix #1 (2026-09-09) hardened
mode="backstrip" only.

Contract after this fix:
  * an executable mode runs its own engine;
  * a mode whose engine exists but whose inputs are not in the unified
    signature refuses honestly and names the dedicated tool;
  * an unknown mode refuses and lists the executable modes.
In no case may an unexecuted mode return a profile payload with ok:true.
"""

from __future__ import annotations

import asyncio

from geox_mcp.tools.basin_unified import geox_basin

# Keys that only a real basin-profile payload carries. If one of these shows up
# on an unexecuted mode, the mode silently fell through.
_PROFILE_ONLY_KEYS = ("observed", "process_hypotheses", "prior_art_claims")


def _run(**kwargs):
    return asyncio.run(geox_basin(**kwargs))


def test_profile_mode_still_executes():
    result = _run(mode="profile", basin_name="malay_basin", profile_mode="overview")
    # In-process the profile returns the standard envelope with the payload
    # nested under primary_artifact; the MCP layer adds the top-level `ok`.
    assert result.get("ok") is True or result.get("execution_status") == "SUCCESS"
    artifact = result.get("primary_artifact") or {}
    assert artifact.get("mode") == "overview"


def test_mass_balance_refuses_instead_of_returning_profile():
    result = _run(mode="mass_balance", basin_name="malay_basin")
    assert result.get("ok") is False
    assert result.get("isError") is True
    assert result.get("governance_status") == "HOLD"
    assert result.get("claim_state") == "INVALID_MODE_FOR_THIS_TOOL"
    assert result.get("mode_echo") == "mass_balance"
    assert result.get("required_tool") == "geox_sediment_mass_balance"
    assert "source_eroded_km3" in result.get("required_params", [])
    # the tell-tale of the silent fall-through
    assert not any(k in result for k in _PROFILE_ONLY_KEYS)


def test_thermal_refuses_instead_of_returning_profile():
    result = _run(mode="thermal", basin_name="malay_basin")
    assert result.get("ok") is False
    assert result.get("isError") is True
    assert result.get("governance_status") == "HOLD"
    assert result.get("claim_state") == "INVALID_MODE_FOR_THIS_TOOL"
    assert result.get("mode_echo") == "thermal"
    assert result.get("required_tool") == "geox_thermal_maturity_history"
    assert "burial_history" in result.get("required_params", [])
    assert not any(k in result for k in _PROFILE_ONLY_KEYS)


def test_unknown_mode_refuses_and_lists_executable_modes():
    result = _run(mode="macrostrat_units", basin_name="malay_basin")
    assert result.get("ok") is False
    assert result.get("isError") is True
    assert result.get("claim_state") == "INVALID_MODE_FOR_THIS_TOOL"
    assert result.get("mode_echo") == "macrostrat_units"
    assert "profile" in result.get("valid_modes", [])
    assert "macrostrat" in result.get("valid_modes", [])
    assert not any(k in result for k in _PROFILE_ONLY_KEYS)


def test_macrostrat_mode_does_not_return_a_profile():
    """macrostrat has a dispatch branch — it must reach the macrostrat engine.

    Without lat/lng the macrostrat_* profile modes refuse (they need a point);
    what must never happen is a basin profile with ok:true.
    """
    result = _run(mode="macrostrat", basin_name="malay_basin")
    assert result.get("mode") != "overview"
    assert not (result.get("ok") is True and result.get("mode") == "overview"), (
        "mode='macrostrat' fell through to the profile default"
    )


def test_backstrip_refusal_shape_preserved():
    """af-fix #1 (2026-09-09) must not regress."""
    result = _run(mode="backstrip", basin_name="malay_basin")
    assert result.get("ok") is False
    assert result.get("claim_state") == "INVALID_MODE_FOR_THIS_TOOL"
    assert result.get("required_tool") == "geox_basin_backstrip"
    assert not any(k in result for k in _PROFILE_ONLY_KEYS)


# ── Disclosure must survive the compact boundary ────────────────────────────
# Measured live 2026-10-28: an anonymous (public) session asking for
# kinabalu_basin received `observed: {}` and a compacted `interpreted` with
# NO disclosure anywhere in the payload — indistinguishable from "no evidence
# exists". Two breaks fed that:
#   1. basin_unified read `disclosure` from the envelope top level, but the
#      builder writes it INSIDE primary_artifact → withheld_claims was
#      structurally pinned to 0 (zero-laundered count).
#   2. compact_structured_for_ui dropped the disclosure key entirely.
# Both are fixed; these tests pin the fix.


def test_public_disclosure_reports_the_real_withheld_count():
    result = _run(mode="profile", basin_name="kinabalu_basin")
    disclosure = result.get("_disclosure")
    assert isinstance(disclosure, dict), "outer disclosure stamp missing"
    assert disclosure.get("projection") == "PUBLIC"
    # Kinabalu carries enterprise-only claims; the count must be real, not 0.
    assert disclosure.get("withheld_claims", 0) > 0, "withheld count was zero-laundered"
    assert disclosure.get("rule")
    assert disclosure.get("reason")


def test_disclosure_survives_compaction():
    from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui

    result = _run(mode="profile", basin_name="kinabalu_basin")
    compact = compact_structured_for_ui(result, tool="geox_basin", app_id="basin_explorer")
    assert "disclosure" in compact, "inner disclosure dropped at the compact boundary"
    assert isinstance(compact["disclosure"], dict)
    assert compact["disclosure"].get("projection") == "PUBLIC"
    assert "_disclosure" in compact, "envelope-level disclosure dropped"
    assert compact["_disclosure"].get("withheld_claims", 0) > 0
