from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp.exceptions import ToolError

from geox_mcp.server import create_app, mcp
from geox_mcp.surface_manifest import WORKSPACE_MIME, WORKSPACE_URI, manifest_tool_map, manifest_tools

create_app()


def _extract_feature_collection(payload: dict) -> dict:
    artifact = payload.get("primary_artifact", payload)
    if isinstance(artifact.get("geojson"), dict):
        return artifact["geojson"]
    if isinstance(artifact.get("geojson_features"), list):
        return {"type": "FeatureCollection", "features": artifact["geojson_features"]}
    raise AssertionError("No GeoJSON payload found")


class TestWorkspaceSurface:
    async def test_map_context_scene_exposes_workspace_uri(self):
        entry = manifest_tool_map()["geox_map_context_scene"]
        assert entry.ui == {"resource_uri": WORKSPACE_URI, "mime_type": WORKSPACE_MIME}

    def test_only_map_context_scene_binds_workspace_ui(self):
        ui_bound = [tool.name for tool in manifest_tools() if tool.ui]
        assert ui_bound == ["geox_map_context_scene"]

    async def test_workspace_resource_list_and_read(self):
        resources = await mcp.list_resources()
        uris = {str(getattr(resource, "uri", "")) for resource in resources}
        assert WORKSPACE_URI in uris

        resource = await mcp.read_resource("geox://apps/workspace-v1.html")
        content = resource.contents[0]
        assert content.mime_type == WORKSPACE_MIME
        assert "<!doctype html>" in content.content.lower()
        assert "GEOX Workspace" in content.content
        assert "No mutation path is enabled." in content.content

    def test_workspace_bundle_is_local_and_self_contained(self):
        html = Path("/root/GEOX/src/geox_mcp/ui/workspace_v1.html").read_text(encoding="utf-8")
        assert "http://" not in html
        assert "https://" not in html
        assert "fetch(" not in html

    async def test_map_context_scene_preserves_identity_and_geojson(self):
        result = await mcp.call_tool(
            "geox_map_context_scene",
            {
                "bbox": [115.5, 4.0, 120.0, 7.5],
                "mode": "render_geojson",
                "session_id": "SEAL-map",
                "actor_id": "ARIF",
                "trace_id": "trace-map",
            },
        )
        payload = result.structured_content
        feature_collection = _extract_feature_collection(payload)
        features = feature_collection["features"]

        assert payload["session_id"] == "SEAL-map"
        assert payload["actor_id"] == "ARIF"
        assert payload["trace_id"] == "trace-map"
        assert payload["provenance"]["session_id"] == "SEAL-map"
        assert payload["provenance"]["actor_id"] == "ARIF"
        assert payload["provenance"]["trace_id"] == "trace-map"
        assert payload["audit_receipt"]["session_id"] == "SEAL-map"
        assert payload["audit_receipt"]["actor_id"] == "ARIF"
        assert payload["audit_receipt"]["trace_id"] == "trace-map"
        assert payload["physics_guard"]["guard_passed"] is True
        assert feature_collection["type"] == "FeatureCollection"
        assert payload["primary_artifact"]["bbox"] == [115.5, 4.0, 120.0, 7.5]
        assert payload["primary_artifact"]["crs"] == "EPSG:4326"
        assert payload["primary_artifact"]["scene_rendered"] is True
        assert len(features) >= 3
        assert {feature["id"] for feature in features} >= {"aoi-bbox", "aoi-center"}
        assert all(feature["properties"].get("selectable") for feature in features)

    async def test_safe_follow_up_call_preserves_identity(self):
        result = await mcp.call_tool(
            "geox_map_context_scene",
            {
                "bbox": [115.5, 4.0, 120.0, 7.5],
                "mode": "bbox_context",
                "session_id": "SEAL-followup",
                "actor_id": "ARIF",
                "trace_id": "trace-followup",
            },
        )
        payload = result.structured_content
        assert payload["session_id"] == "SEAL-followup"
        assert payload["actor_id"] == "ARIF"
        assert payload["trace_id"] == "trace-followup"

    async def test_anonymous_mode_only_when_identity_absent(self):
        result = await mcp.call_tool(
            "geox_map_context_scene",
            {
                "bbox": [115.5, 4.0, 120.0, 7.5],
                "mode": "bbox_context",
            },
        )
        payload = result.structured_content
        assert payload.get("actor_id") in (None, "anonymous")
        assert payload.get("session_id") in (None, "anonymous")

    async def test_invalid_call_returns_governed_hold(self):
        with pytest.raises(ToolError) as excinfo:
            await mcp.call_tool(
                "geox_basin",
                {
                    "arguments": {"mode": "profile", "basin_name": "missing-basin"},
                    "session_id": "SEAL-hold",
                    "actor_id": "ARIF",
                    "trace_id": "trace-hold",
                },
            )
        payload = json.loads(str(excinfo.value))
        error_data = payload["error"]["data"]
        assert error_data["verdict"] == "HOLD"
        assert error_data["session_id"] == "SEAL-hold"
        assert error_data["guard"] == "SCHEMA_REJECTION"
