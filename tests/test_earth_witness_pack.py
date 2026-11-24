"""The five witness-spine tools have a pack, and that pack stays unlisted.

default, specialist, and research do not show them. The earth_witness
profile does, and it shows those five plus the RT1 recovery tool.
"""

from __future__ import annotations

from geox_mcp.registry import pack_for_tool, tools_for_profile

WITNESS = {
    "geox_calibration_register_witness",
    "geox_extract_display_proxy",
    "geox_register_native_source",
    "geox_extract_native_trace",
    "geox_list_registered_sources",
}


def test_witness_tools_are_in_earth_witness_only() -> None:
    for name in WITNESS:
        assert pack_for_tool(name) == "earth_witness"


def test_witness_pack_is_unlisted_from_default_profiles() -> None:
    for profile in ("default", "specialist", "research", "full"):
        visible = set(tools_for_profile(profile))
        assert visible.isdisjoint(WITNESS), profile


# geox_surface_status is pinned into the earth_witness pack as the RT1 recovery
# tool (tools_manifest.yaml; d0741cf0, 2026-11-12): an operator holding an
# evidence package must be able to enumerate the surface to verify what the
# package claims. The pack stays operator-gated and unlisted elsewhere.
RT1_RECOVERY = {"geox_surface_status"}


def test_earth_witness_profile_is_the_witness_spine_plus_rt1_recovery() -> None:
    assert set(tools_for_profile("earth_witness")) == WITNESS | RT1_RECOVERY
