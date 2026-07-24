"""Batch A: demo registry wells hydrate curves for p0-viz."""
from __future__ import annotations

import pytest

from geox_mcp.tools.integration_well import (
    _load_well_curves_for_ui,
    _resolve_demo_entry,
    geox_well_desk_open,
    geox_well_desk_petro,
)


def test_demo_registry_resolves_kinabalu_and_sandakan():
    assert _resolve_demo_entry("DEMO-KINABALU") is not None
    assert _resolve_demo_entry("DEMO_SANDAKAN_A") is not None
    assert _resolve_demo_entry("DEMO_WELL_A") is not None
    assert _resolve_demo_entry("DEMO-VOLVE") is not None


def test_load_curves_demo_kinabalu():
    loaded = _load_well_curves_for_ui("DEMO-KINABALU")
    assert loaded["status"] == "loaded", loaded
    assert loaded.get("depths")
    assert loaded.get("curves")
    assert loaded.get("provenance_badge")
    assert loaded.get("data_class") in ("DEMO", "SYNTHETIC_LABEL", "OPEN_OSS")


def test_load_curves_demo_sandakan_a():
    loaded = _load_well_curves_for_ui("DEMO_WELL_A")
    assert loaded["status"] == "loaded", loaded
    assert "GR" in (loaded.get("curves") or {})
    assert len(loaded["depths"]) >= 10


def test_unknown_well_no_las():
    loaded = _load_well_curves_for_ui("XYZ-99-NOT-A-WELL")
    assert loaded["status"] == "no_las"


@pytest.mark.asyncio
async def test_desk_open_returns_curves():
    res = await geox_well_desk_open(well_id="DEMO-KINABALU", mode="open")
    sc = getattr(res, "structured_content", None) or {}
    assert sc.get("ok") is True
    assert sc.get("curves")
    assert sc.get("depths")
    assert sc.get("data_class")
    assert sc.get("seal_status") == "NOT_SEALED" or sc.get("epistemic", {}).get("seal_status") == "NOT_SEALED"


@pytest.mark.asyncio
async def test_desk_petro_advisory():
    res = await geox_well_desk_petro(well_id="DEMO_WELL_A")
    assert res.get("authority_claim") == "ADVISORY"
    assert res.get("seal_status") == "NOT_SEALED"
    # ok may be True if lem path works, or False with clear error — never crash
    assert "well_id" in res
