from __future__ import annotations

import json
import subprocess
from pathlib import Path

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, CANONICAL_RUNTIME_TOOLS, INTERNAL_TOOLS
from geox_mcp.server import create_app, mcp
from geox_mcp.surface_manifest import WORKSPACE_MIME, manifest_tools, plugin_export_tool_names

create_app()

ROOT = Path(__file__).resolve().parents[1]


def _llms_tools() -> list[str]:
    tools: list[str] = []
    capture = False
    for line in (ROOT / "llms.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() == "## 1. Canonical Tool Surface":
            capture = True
            continue
        if capture and line.startswith("## 2."):
            break
        if capture and ". **geox_" in line:
            tools.append(line.split("**", 2)[1])
    return tools


class TestManifestTopology:
    def test_public_internal_split_is_explicit_and_disjoint(self):
        tools = list(manifest_tools())
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))
        assert set(CANONICAL_PUBLIC_TOOLS).isdisjoint(INTERNAL_TOOLS)
        assert set(CANONICAL_RUNTIME_TOOLS) == set(names)
        assert {tool.name for tool in tools if tool.is_public} == set(CANONICAL_PUBLIC_TOOLS)
        assert {tool.name for tool in tools if tool.is_internal} == set(INTERNAL_TOOLS)

    def test_generated_exports_match_manifest_public(self):
        tools_snapshot = json.loads((ROOT / ".well-known" / "tools.json").read_text(encoding="utf-8"))
        openapi_snapshot = json.loads((ROOT / ".well-known" / "openapi.json").read_text(encoding="utf-8"))
        root_tools = json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))

        manifest_public = set(CANONICAL_PUBLIC_TOOLS)
        expected_app_export = set(plugin_export_tool_names())
        snapshot_public = {tool["name"] for tool in tools_snapshot["tools"] if tool["expose"]}
        snapshot_app_export = {tool["name"] for tool in tools_snapshot["tools"] if tool.get("app_exposed")}
        openapi_public = {tool["name"] for tool in openapi_snapshot["paths"]["/mcp"]["post"]["x-mcp-tools"]}
        root_public = set(root_tools["public"])
        root_app_export = set(root_tools["app_export"])

        assert snapshot_public == manifest_public
        assert snapshot_app_export == expected_app_export
        assert openapi_public == expected_app_export
        assert root_public == manifest_public
        assert root_app_export == expected_app_export
        assert set(_llms_tools()) == manifest_public

    async def test_workbench_resource_is_readable(self):
        resource = await mcp.read_resource("geox://apps/workspace-v1.html")
        content = resource.contents[0]
        assert content.mime_type == WORKSPACE_MIME
        assert "GEOX Workspace" in content.content

    def test_generated_artifacts_are_reproducible(self):
        tracked = [
            ROOT / ".well-known" / "tools.json",
            ROOT / ".well-known" / "openapi.json",
            ROOT / "tools.json",
            ROOT / "llms.txt",
        ]
        before = {path: path.read_text(encoding="utf-8") for path in tracked}
        subprocess.run(
            ["python", "scripts/generate_public_registry.py"],
            cwd=ROOT,
            check=True,
        )
        after = {path: path.read_text(encoding="utf-8") for path in tracked}
        assert after == before
