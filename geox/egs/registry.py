"""
EGS Registry — Earth Grounding System Runtime
================================================
DITEMPA BUKAN DIBERI — Forged, Not Given.

Central registry for all EGS components. Provides:
- Tool registration for FastMCP server
- Global state initialization
- Engineering resource access

Usage in server.py:
    from geox.egs.registry import register_egs_tools, init_egs_state
    init_egs_state()
    register_egs_tools(mcp)
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from geox.egs.tools.claims import EGS_CLAIM_TOOLS, register_claim_tools
from geox.egs.tools.compute import EGS_COMPUTE_TOOLS, register_compute_tools
from geox.egs.tools.qc import EGS_QC_TOOLS, register_qc_tools
from geox.egs.tools.query import EGS_QUERY_TOOLS, register_query_tools

logger = logging.getLogger("geox.egs.registry")

# EGS Tool Manifest
EGS_CANONICAL_TOOLS: dict[str, dict[str, Any]] = {}
EGS_CANONICAL_TOOLS.update(EGS_QUERY_TOOLS)
EGS_CANONICAL_TOOLS.update(EGS_CLAIM_TOOLS)
EGS_CANONICAL_TOOLS.update(EGS_COMPUTE_TOOLS)
EGS_CANONICAL_TOOLS.update(EGS_QC_TOOLS)

EGS_VERSION = "0.1.0"
EGS_CONTRACT = "2026-06-28-EGS-V1"
EGS_TOOL_COUNT = len(EGS_CANONICAL_TOOLS)


def register_egs_tools(mcp: FastMCP) -> None:
    """Register all EGS tools with a FastMCP server."""
    register_query_tools(mcp)
    register_claim_tools(mcp)
    register_compute_tools(mcp)
    register_qc_tools(mcp)
    logger.info(f"EGS: Registered {EGS_TOOL_COUNT} tools (v{EGS_VERSION})")


def init_egs_state() -> None:
    """Initialize EGS global state.

    Creates the empty earth graph, claim store, and provenance chains.
    Call once at server startup before registering tools.
    """
    from geox.egs.tools.query import _EGS_GRAPH, _EGS_CLAIMS, _EGS_PROVENANCE

    # State is already initialized at import time.
    # This function exists for explicit initialization and logging.
    logger.info(
        f"EGS state initialized: graph v{_EGS_GRAPH.version}, claims={len(_EGS_CLAIMS)}, provenance_chains={len(_EGS_PROVENANCE)}"
    )


def egs_surface_status() -> dict[str, Any]:
    """Return EGS registry surface for federation discovery.

    Matches the geox_surface_status(registry) format.
    """
    return {
        "egs_version": EGS_VERSION,
        "egs_contract": EGS_CONTRACT,
        "canonical_tools": EGS_TOOL_COUNT,
        "tool_names": sorted(EGS_CANONICAL_TOOLS.keys()),
        "tools": {
            name: {
                "description": desc["description"],
                "readOnlyHint": desc.get("readOnlyHint", False),
                "destructiveHint": desc.get("destructiveHint", False),
                "idempotentHint": desc.get("idempotentHint", True),
            }
            for name, desc in EGS_CANONICAL_TOOLS.items()
        },
        "doctrine": "Language models consume EGS; they do not replace it.",
    }
