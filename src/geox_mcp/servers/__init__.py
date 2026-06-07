"""GEOX MCP Domain Servers — Composition units for mcp.mount()."""

from __future__ import annotations

from geox_mcp.servers.claims import create_claims_server
from geox_mcp.servers.paleoscan import create_paleoscan_server
from geox_mcp.servers.vision import create_vision_server
from geox_mcp.servers.witness import create_witness_server

__all__ = [
    "create_witness_server",
    "create_paleoscan_server",
    "create_claims_server",
    "create_vision_server",
]
