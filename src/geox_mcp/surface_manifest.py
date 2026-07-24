from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

MANIFEST_PATH = Path(__file__).with_name("tools_manifest.yaml")
WORKSPACE_URI = "ui://geox/workspace-v1.html"
WORKSPACE_MIME = "text/html;profile=mcp-app"
# Backward-compatible aliases during the workbench → workspace transition.
WORKBENCH_URI = WORKSPACE_URI
WORKBENCH_MIME = WORKSPACE_MIME

# GravMag Studio (Stage A — forward only). Registered 2026-07-13.
GRAVMAG_STUDIO_URI = "ui://geox/gravmag-studio.html"
GRAVMAG_STUDIO_MIME = WORKSPACE_MIME


@dataclass(frozen=True)
class SurfaceTool:
    name: str
    domain: str
    axis: str
    lane: str
    face: str
    visibility: str
    description: str
    input_schema_source: str
    annotations: dict[str, Any]
    ui: dict[str, Any] | None
    plugin: dict[str, Any]
    governance: dict[str, Any]

    @property
    def is_public(self) -> bool:
        return self.visibility == "public"

    @property
    def is_internal(self) -> bool:
        return self.visibility == "internal"

    @property
    def is_plugin_exposed(self) -> bool:
        return bool(self.plugin.get("exposed", self.is_public))

    @property
    def has_ui(self) -> bool:
        return bool(self.ui and self.ui.get("resource_uri"))


def _normalize_tool(entry: dict[str, Any]) -> SurfaceTool:
    annotations = dict(entry.get("annotations") or {})
    plugin = dict(entry.get("plugin") or {})
    governance = dict(entry.get("governance") or {})
    ui_raw = entry.get("ui")
    ui = dict(ui_raw) if isinstance(ui_raw, dict) else None

    visibility = str(entry.get("visibility") or "public")
    if visibility not in {"public", "internal"}:
        raise ValueError(f"Invalid visibility '{visibility}' for {entry.get('name')}")

    face = str(entry.get("face") or ("internal" if visibility == "internal" else "surface"))
    if face not in {"surface", "internal"}:
        raise ValueError(f"Invalid face '{face}' for {entry.get('name')}")

    if visibility == "internal" and plugin.get("exposed") is True:
        raise ValueError(f"Internal tool cannot be plugin-exposed: {entry.get('name')}")

    if ui:
        if "resource_uri" not in ui:
            raise ValueError(f"UI entry missing resource_uri for {entry.get('name')}")
        ui.setdefault("mime_type", WORKSPACE_MIME)

    return SurfaceTool(
        name=str(entry["name"]),
        domain=str(entry["domain"]),
        axis=str(entry["axis"]),
        lane=str(entry["lane"]),
        face=face,
        visibility=visibility,
        description=str(entry.get("description") or ""),
        input_schema_source=str(entry.get("input_schema_source") or "callable"),
        annotations=annotations,
        ui=ui,
        plugin=plugin,
        governance=governance,
    )


@lru_cache(maxsize=1)
def load_surface_manifest() -> dict[str, Any]:
    payload = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Malformed manifest: {MANIFEST_PATH}")

    tools_raw = payload.get("tools")
    if not isinstance(tools_raw, list):
        raise ValueError("Manifest 'tools' must be a list")

    tools = [_normalize_tool(dict(entry)) for entry in tools_raw]
    names = [tool.name for tool in tools]
    dupes = sorted({name for name in names if names.count(name) > 1})
    if dupes:
        raise ValueError(f"Duplicate manifest tools: {dupes}")

    compat_tools = payload.get("compat_tools") or []
    if not isinstance(compat_tools, list):
        raise ValueError("Manifest 'compat_tools' must be a list")
    compat_names = [str(name) for name in compat_tools]
    compat_dupes = sorted({name for name in compat_names if compat_names.count(name) > 1})
    if compat_dupes:
        raise ValueError(f"Duplicate compat tools: {compat_dupes}")

    return {
        "manifest_version": str(payload.get("manifest_version") or ""),
        "surface_version": str(payload.get("surface_version") or payload.get("manifest_version") or ""),
        "surface_name": str(payload.get("surface_name") or ""),
        "public_count_target": payload.get("public_count_target"),
        "generated_from": str(payload.get("generated_from") or ""),
        "public_transport": str(payload.get("public_transport") or "mcp"),
        "tools": tuple(tools),
        "compat_tools": tuple(compat_names),
        "doctrine": payload.get("doctrine") or {},
    }


def manifest_tools() -> tuple[SurfaceTool, ...]:
    return load_surface_manifest()["tools"]


def manifest_tool_map() -> dict[str, SurfaceTool]:
    return {tool.name: tool for tool in manifest_tools()}


def public_tools() -> tuple[SurfaceTool, ...]:
    return tuple(tool for tool in manifest_tools() if tool.is_public)


def internal_tools() -> tuple[SurfaceTool, ...]:
    return tuple(tool for tool in manifest_tools() if tool.is_internal)


def compat_tools() -> tuple[str, ...]:
    return load_surface_manifest()["compat_tools"]


def public_tool_names() -> list[str]:
    return [tool.name for tool in public_tools()]


def internal_tool_names() -> list[str]:
    return [tool.name for tool in internal_tools()]


def runtime_tool_names() -> list[str]:
    return [tool.name for tool in manifest_tools()]


def plugin_export_tool_names() -> list[str]:
    return [tool.name for tool in public_tools() if tool.is_plugin_exposed]


def ui_tool_names() -> list[str]:
    return [tool.name for tool in public_tools() if tool.has_ui]


def manifest_entries_for_registry() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for tool in manifest_tools():
        entries.append(
            {
                "name": tool.name,
                "domain": tool.domain,
                "axis": tool.axis,
                "lane": tool.lane,
                "visibility": tool.visibility,
                "expose": tool.is_public,
                "app_exposed": tool.is_plugin_exposed,
                "face": tool.face,
            }
        )
    return entries


def webmcp_categories() -> list[dict[str, Any]]:
    categories: dict[str, list[str]] = {}
    for tool in public_tools():
        head = tool.domain.split(".", 1)[0]
        tail = tool.domain.split(".", 1)[1] if "." in tool.domain else tool.domain
        if head == "governance":
            label = "Governance"
        else:
            label = tail.replace("_", " ").title()
        categories.setdefault(label, []).append(tool.name)
    return [
        {"category": category, "tools": sorted(names)}
        for category, names in sorted(categories.items(), key=lambda item: item[0].lower())
    ]


def surface_version() -> str:
    """Constitutional surface version — must match runtime tools/list public count doctrine."""
    return str(load_surface_manifest().get("surface_version") or "")


def surface_attestation() -> dict:
    """Boot/arif_init-class attestation: version + public tool set hash."""
    import hashlib
    import json

    names = public_tool_names()
    payload = {
        "surface_version": surface_version(),
        "surface_name": load_surface_manifest().get("surface_name"),
        "public_count": len(names),
        "public_count_target": load_surface_manifest().get("public_count_target"),
        "public_tools": names,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["surface_hash"] = hashlib.sha256(raw).hexdigest()
    payload["ok"] = (
        payload["public_count_target"] is None
        or int(payload["public_count_target"]) == payload["public_count"]
    )
    if not payload["ok"]:
        payload["error"] = "SURFACE_COUNT_DRIFT"
    return payload
