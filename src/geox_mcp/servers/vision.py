"""
GEOX Vision Domain Server — Layer 1 (Vision Ingest) MCP surface
══════════════════════════════════════════════════════════════════════════
Forged 2026-06-07 (autonomous, F13 SOVEREIGN delegation via Arif directive)
DITEMPA BUKAN DIBERI — Forged, Not Given

4 tools (perceptual_inventory, minimax_inference, calibrate, audit) wire
the existing `geox_core.engines.vision` engine to the GEOX MCP public
surface. Vision outputs NEVER reach SEAL without physics validation
(F9 ANTI-HANTU); confidence is hard-capped at 0.90 (F7 HUMILITY);
human_review_required=True when AC_Risk > 0.5 (F13 SOVEREIGN).

Mounted by server.py with namespace=None (original tool names preserved).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from geox_mcp.tools._register import register_tools_on_server
from geox_mcp.tools.vision import (
    geox_vision_audit,
    geox_vision_calibrate,
    geox_vision_minimax_inference,
    geox_vision_perceptual_inventory,
)

_VISION_TOOLS: list[tuple[str, Any]] = [
    ("geox_vision_perceptual_inventory", geox_vision_perceptual_inventory),
    ("geox_vision_minimax_inference", geox_vision_minimax_inference),
    ("geox_vision_calibrate", geox_vision_calibrate),
    ("geox_vision_audit", geox_vision_audit),
]

_VISION_ANNOTATIONS: dict[str, dict] = {
    "geox_vision_perceptual_inventory": {
        "title": "Vision Perceptual Inventory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_vision_minimax_inference": {
        "title": "Vision MiniMax Inference",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,  # VLM calls are non-idempotent
        "openWorldHint": True,  # calls external VLM
    },
    "geox_vision_calibrate": {
        "title": "Vision Calibrate",
        "readOnlyHint": False,  # writes report to /tmp
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_vision_audit": {
        "title": "Vision AC_Risk Audit",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


def create_vision_server() -> FastMCP:
    """Build the vision domain sub-server.

    The Vision V1 engine lives in geox_core/engines/vision/. This
    domain server only registers the 4 MCP-exposed tool functions and
    their MCP annotations. Constitutional enforcement (F5/F7/F9/F11/F13)
    is implemented inside the tool functions themselves.
    """
    server = FastMCP("geox-vision")
    register_tools_on_server(server, _VISION_TOOLS, _VISION_ANNOTATIONS)
    return server
