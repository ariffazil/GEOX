"""Chaos-removal tests: isError truth, map bbox filter, deep_time K-Pg (2026-07-25)."""

from __future__ import annotations

import pytest

from geox_mcp.result_truth import result_is_error, truthy_error
from geox_mcp.tools.deep_time.data_loaders import load_biotic_realm, load_ice_extent
from geox_mcp.tools.deep_time.vector import _mass_extinctions_in_interval
from geox_mcp.tools.earth_map import geox_map_layers_list


def test_empty_error_string_is_not_failure() -> None:
    assert truthy_error("") is False
    assert truthy_error(None) is False
    assert result_is_error({"ok": True, "error": "", "grade": "AAA"}) is False
    assert result_is_error({"ok": True, "result": {"grade": "AAA"}}) is False


def test_truthy_error_and_ok_false() -> None:
    assert result_is_error({"ok": False, "error": "boom"}) is True
    assert result_is_error({"status": "INVALID"}) is True
    assert result_is_error({"status": "NOT_FOUND"}) is True


@pytest.mark.asyncio
async def test_map_layers_north_sea_excludes_sabah() -> None:
    """North Sea bbox must not claim Crocker/Kinabalu available."""
    r = await geox_map_layers_list(bbox=[0.0, 54.0, 3.0, 58.0])  # ~4° span
    assert r["status"] == "OK"
    ids = {L["id"] for L in r["layers"] if L.get("available")}
    for sab in ("sab_crocker", "sab_trusmadi", "sab_kinabalu", "sab_nw_basin"):
        assert sab not in ids, f"{sab} must not be available in North Sea"


@pytest.mark.asyncio
async def test_map_layers_sabah_includes_regional() -> None:
    r = await geox_map_layers_list(bbox=[115.5, 5.0, 118.5, 7.0])
    assert r["status"] == "OK"
    ids = {L["id"] for L in r["layers"]}
    # Sabah regional layers should intersect
    assert any(i.startswith("sab_") for i in ids)


def test_biotic_at_kpg_is_paleogene_not_cretaceous() -> None:
    v = load_biotic_realm(66.0)
    assert v.value is not None
    assert "Paleogene" in str(v.value) or "post-K-Pg" in str(v.value)
    assert "dinosaurs (non-avian)" not in str(v.value)


def test_ice_at_kpg_not_cretaceous_label() -> None:
    v = load_ice_extent(66.0)
    assert "Cretaceous" not in str(v.value)


def test_kpg_mass_extinction_present_at_66() -> None:
    events = _mass_extinctions_in_interval(66.0, 66.0)
    assert events, "K-Pg must be listed at 66 Ma"
    blob = " ".join(str(e.value) + " " + str(e.notes) for e in events)
    assert "K-Pg" in blob
