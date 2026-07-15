#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geox_mcp.surface_manifest import (  # noqa: E402
    MANIFEST_PATH,
    WORKSPACE_MIME,
    WORKSPACE_URI,
    manifest_tools,
    plugin_export_tool_names,
    public_tools,
)


def _public_tool_row(tool) -> dict:
    return {
        "name": tool.name,
        "description": tool.description or tool.name.replace("geox_", "GEOX ").replace("_", " "),
        "domain": tool.domain,
        "axis": tool.axis,
        "lane": tool.lane,
        "parameters": {
            "type": "object",
            "properties": {
                "arguments": {"type": "object", "description": "Tool-specific arguments"},
                "session_id": {"type": "string", "description": "arifOS constitutional session ID"},
                "actor_id": {"type": "string", "description": "Calling actor identifier"},
                "trace_id": {"type": "string", "description": "Trace identifier propagated end-to-end"},
            },
        },
    }


def build_tools_snapshot() -> dict:
    app_export = set(plugin_export_tool_names())
    tools = []
    for tool in manifest_tools():
        tools.append(
            {
                "name": tool.name,
                "description": tool.description or tool.name.replace("geox_", "GEOX ").replace("_", " "),
                "version": "2026.07.15",
                "domain": tool.domain,
                "axis": tool.axis,
                "lane": tool.lane,
                "expose": tool.is_public,
                "app_exposed": tool.name in app_export,
                "face": tool.face,
                "ui": tool.ui,
                "mime_type": tool.ui.get("mime_type") if tool.ui else None,
            }
        )
    return {
        "$schema": "arifOS/tools-manifest/v2",
        "organ": "geox",
        "version": "2026.07.15",
        "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "canonical_tools": len(tools),
        "surface_tools": sum(1 for tool in tools if tool["expose"]),
        "internal_tools": sum(1 for tool in tools if not tool["expose"]),
        "policy": "ZEN-15: public == plugin export == CANONICAL_PUBLIC_TOOLS (no phantom app names)",
        "tools": tools,
    }


def build_openapi_snapshot() -> dict:
    app_export = set(plugin_export_tool_names())
    public_rows = [_public_tool_row(tool) for tool in public_tools() if tool.name in app_export]
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "GEOX Earth Intelligence API",
            "description": (
                "MCP Apps is the portable protocol. ChatGPT is one host and plugin-distribution environment. "
                "window.openai is optional progressive enhancement."
            ),
            "version": "2026.07.15",
        },
        "paths": {
            "/mcp": {
                "post": {
                    "summary": "MCP JSON-RPC 2.0 endpoint",
                    "description": (
                        "Plugin submission, review and publication use metadata scanned "
                        "or snapshotted from this live MCP endpoint. "
                        "x-mcp-tools MUST equal the 15 ZEN-15 canonical public tools."
                    ),
                    "operationId": "mcpEndpoint",
                    "x-mcp-tools": public_rows,
                }
            }
        },
    }


def build_root_tools_manifest() -> dict:
    app_export = set(plugin_export_tool_names())
    return {
        "version": "2026.07.15",
        "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "policy": "ZEN-15 single public surface — app_export must equal public",
        "public": [tool.name for tool in public_tools()],
        "app_export": [tool.name for tool in public_tools() if tool.name in app_export],
        "internal": [tool.name for tool in manifest_tools() if tool.is_internal],
    }


def build_llms_txt() -> str:
    public = list(public_tools())
    lines = [
        f"# GEOX — Earth Intelligence Sovereign Kernel ({len(public)} Public Tools)",
        "> Doctrine: Physics before narrative. Governed evidence only.",
        "> Surface: generated from src/geox_mcp/tools_manifest.yaml",
        "",
        "## 1. Canonical Tool Surface",
        "",
    ]
    for idx, tool in enumerate(public, start=1):
        description = tool.description or tool.name.replace("geox_", "").replace("_", " ")
        lines.append(f"{idx}. **{tool.name}**: {description}")
    lines.extend(
        [
            "",
            "## 2. Agent Reasoning Logic",
            "- Evidence before interpretation.",
            "- Governance stays server-side.",
            f"- App-enabled workspace URI: `{WORKSPACE_URI}` ({WORKSPACE_MIME}).",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    write_json(ROOT / ".well-known" / "tools.json", build_tools_snapshot())
    write_json(ROOT / ".well-known" / "openapi.json", build_openapi_snapshot())
    write_json(ROOT / "tools.json", build_root_tools_manifest())
    (ROOT / "llms.txt").write_text(build_llms_txt(), encoding="utf-8")
    print("generated: .well-known/tools.json .well-known/openapi.json tools.json llms.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
