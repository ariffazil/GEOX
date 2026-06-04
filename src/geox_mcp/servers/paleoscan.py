"""
GEOX Paleoscan Domain Server — Coordinate Transforms / Frames / Blending / Export
═════════════════════════════════════════════════════════════════════════════════
paleoscan_python v2.0.0 forge — 10 tools for spatial transforms, volume I/O,
seismic attributes, fault sticks, blending, and SEG-Y export.

Mounted by server.py with namespace=None (original names preserved).
DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from geox_mcp.tools._register import register_tools_on_server
from geox_mcp.tools.paleoscan_forge import (
    geox_attribute_registry_list_tool,
    geox_blend_volume_alpha_tool,
    geox_blend_volume_rgb_tool,
    geox_blockspace_resolution_tool,
    geox_coord_transform_tool,
    geox_fault_stick_ingest_tool,
    geox_segy_export_tool,
    geox_seismic_compute_attribute_tool,
    geox_volume_get_frame_tool,
    geox_volume_set_frame_tool,
)

_PALEOSCAN_TOOLS: list[tuple[str, Any]] = [
    ("geox_coord_transform_tool", geox_coord_transform_tool),
    ("geox_blockspace_resolution_tool", geox_blockspace_resolution_tool),
    ("geox_volume_get_frame_tool", geox_volume_get_frame_tool),
    ("geox_volume_set_frame_tool", geox_volume_set_frame_tool),
    ("geox_seismic_compute_attribute_tool", geox_seismic_compute_attribute_tool),
    ("geox_fault_stick_ingest_tool", geox_fault_stick_ingest_tool),
    ("geox_attribute_registry_list_tool", geox_attribute_registry_list_tool),
    ("geox_blend_volume_alpha_tool", geox_blend_volume_alpha_tool),
    ("geox_blend_volume_rgb_tool", geox_blend_volume_rgb_tool),
    ("geox_segy_export_tool", geox_segy_export_tool),
]

_PALEOSCAN_ANNOTATIONS: dict[str, dict] = {
    "geox_coord_transform_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_blockspace_resolution_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_volume_get_frame_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_volume_set_frame_tool": {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
    "geox_seismic_compute_attribute_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_fault_stick_ingest_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_attribute_registry_list_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_blend_volume_alpha_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_blend_volume_rgb_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_segy_export_tool": {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
}


def create_paleoscan_server() -> FastMCP:
    server = FastMCP("geox-paleoscan")
    register_tools_on_server(server, _PALEOSCAN_TOOLS, _PALEOSCAN_ANNOTATIONS)
    return server
