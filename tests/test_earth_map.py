"""Tests for GEOX Earth Map tools — layers_list, scene_plan, render_preview."""

import json
import pytest
from pathlib import Path

# ── Fixtures ─────────────────────────────────────────────────────────────────

SABAH_BBOX = [115.0, 4.0, 119.5, 7.5]
SMALL_BBOX = [116.0, 5.0, 117.0, 6.0]
GLOBAL_BBOX = [-180, -90, 180, 90]
INVALID_BBOX = [119.5, 4.0, 115.0, 7.5]  # min_lon > max_lon


# ── geox_map_layers_list ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_layers_list_sabah():
    from geox_mcp.tools.earth_map import geox_map_layers_list

    result = await geox_map_layers_list(bbox=SABAH_BBOX)
    assert result["status"] == "OK"
    assert result["layer_count"] > 0
    # Should find Sabah-specific layers
    layer_ids = [l["id"] for l in result["layers"]]
    assert "sab_coastline" in layer_ids or "ne_coastline" in layer_ids


@pytest.mark.asyncio
async def test_layers_list_with_theme():
    from geox_mcp.tools.earth_map import geox_map_layers_list

    result = await geox_map_layers_list(bbox=SABAH_BBOX, theme="sabah_regional")
    assert result["status"] == "OK"
    assert result["theme"] == "sabah_regional"


@pytest.mark.asyncio
async def test_layers_list_invalid_bbox():
    from geox_mcp.tools.earth_map import geox_map_layers_list

    result = await geox_map_layers_list(bbox=INVALID_BBOX)
    assert result["status"] == "ERROR"
    assert "error" in result


@pytest.mark.asyncio
async def test_layers_list_too_large_bbox():
    from geox_mcp.tools.earth_map import geox_map_layers_list

    result = await geox_map_layers_list(bbox=GLOBAL_BBOX)
    assert result["status"] == "ERROR"
    assert "exceeds max" in result["error"]


@pytest.mark.asyncio
async def test_layers_list_unknown_theme():
    from geox_mcp.tools.earth_map import geox_map_layers_list

    result = await geox_map_layers_list(bbox=SABAH_BBOX, theme="nonexistent_theme")
    assert result["status"] == "ERROR"
    assert "Unknown theme" in result["error"]


@pytest.mark.asyncio
async def test_layers_list_include_unavailable():
    from geox_mcp.tools.earth_map import geox_map_layers_list

    result_normal = await geox_map_layers_list(bbox=SABAH_BBOX, include_unavailable=False)
    result_all = await geox_map_layers_list(bbox=SABAH_BBOX, include_unavailable=True)
    assert result_all["layer_count"] >= result_normal["layer_count"]


# ── geox_map_scene_plan ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scene_plan_basic():
    from geox_mcp.tools.earth_map import geox_map_scene_plan

    result = await geox_map_scene_plan(bbox=SABAH_BBOX, theme="sabah_regional")
    assert result["status"] == "OK"
    assert "scene_id" in result
    assert result["scene_id"].startswith("scene_")
    assert len(result["layers_ordered"]) > 0
    assert result["bbox"] == SABAH_BBOX


@pytest.mark.asyncio
async def test_scene_plan_with_layer_ids():
    from geox_mcp.tools.earth_map import geox_map_scene_plan

    result = await geox_map_scene_plan(
        bbox=SABAH_BBOX,
        layer_ids=["ne_coastline", "sab_nw_basin"],
    )
    assert result["status"] == "OK"
    assert result["layer_count"] <= 2


@pytest.mark.asyncio
async def test_scene_plan_context_excludes_decision_support():
    from geox_mcp.tools.earth_map import geox_map_scene_plan

    result = await geox_map_scene_plan(
        bbox=SABAH_BBOX,
        layer_ids=["ne_coastline", "sab_nw_basin"],
        map_purpose="context",
    )
    assert result["status"] == "OK"
    for layer in result["layers_ordered"]:
        assert layer["truth_class"] != "DECISION_SUPPORT"


@pytest.mark.asyncio
async def test_scene_plan_provenance():
    from geox_mcp.tools.earth_map import geox_map_scene_plan

    result = await geox_map_scene_plan(bbox=SABAH_BBOX, theme="sabah_regional")
    assert "provenance" in result
    assert "truth_classes_present" in result["provenance"]
    assert "scale_warning" in result["provenance"]


@pytest.mark.asyncio
async def test_scene_plan_auto_detect():
    from geox_mcp.tools.earth_map import geox_map_scene_plan

    # No theme or layer_ids — auto-detect from bbox
    result = await geox_map_scene_plan(bbox=SMALL_BBOX)
    assert result["status"] == "OK"


# ── geox_map_render_preview ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_render_preview_from_bbox():
    from geox_mcp.tools.earth_map import geox_map_render_preview

    result = await geox_map_render_preview(
        bbox=SMALL_BBOX,
        layer_ids=["ne_coastline"],
        width_px=512,
        height_px=512,
    )
    assert result["status"] == "OK"
    assert result["width_px"] == 512
    assert result["height_px"] == 512
    assert "return_mode" in result


@pytest.mark.asyncio
async def test_render_preview_caching():
    from geox_mcp.tools.earth_map import geox_map_render_preview

    # First render
    r1 = await geox_map_render_preview(
        bbox=SMALL_BBOX,
        layer_ids=["ne_coastline"],
        width_px=512,
        height_px=512,
    )
    # Second render (should be cached)
    r2 = await geox_map_render_preview(
        bbox=SMALL_BBOX,
        layer_ids=["ne_coastline"],
        width_px=512,
        height_px=512,
    )
    assert r1["status"] == "OK"
    assert r2["status"] == "OK"
    assert r2.get("cached") is True


@pytest.mark.asyncio
async def test_render_preview_no_input():
    from geox_mcp.tools.earth_map import geox_map_render_preview

    result = await geox_map_render_preview()
    assert result["status"] == "ERROR"
    assert "scene_id or bbox" in result["error"]


# ── Guardrails ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_guardrails_bbox_clamped():
    from geox_mcp.tools.earth_map import geox_map_render_preview

    result = await geox_map_render_preview(
        bbox=SMALL_BBOX,
        layer_ids=["ne_coastline"],
        width_px=9999,  # should be clamped to max
        height_px=9999,
    )
    assert result["status"] == "OK"
    assert result["width_px"] <= 1600
    assert result["height_px"] <= 1600
