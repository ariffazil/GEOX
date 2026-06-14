"""
GEOX Witness Core — Canonical 30-Tool Orchestrator (COMPATIBILITY SHIM)
═══════════════════════════════════════════════════════════════════════
This module is retained for backward compatibility.

New code should use the domain-server composition in geox_mcp.servers:
  - geox_mcp.servers.witness     → 16 observe/verify tools
  - geox_mcp.servers.paleoscan   → 10 paleoscan_python v2.0.0 forge tools
  - geox_mcp.servers.claims      → 4 H5 claim engine tools

The shared registration engine lives in geox_mcp.tools._register.
DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
from geox_mcp.tools._register import register_tools_on_server
from geox_mcp.tools.claims import (
    geox_claim_challenge,
    geox_claim_create,
    geox_claim_seal,
    geox_evidence_attach,
)

# ── Canonical tool implementations ───────────────────────────────────────────
from geox_mcp.tools.data import geox_data_ingest_bundle
from geox_mcp.tools.dst import geox_dst_ingest_test
from geox_mcp.tools.evidence_reason import geox_evidence_reason
from geox_mcp.tools.ingestion import (
    geox_deviation_survey_inspect,
    geox_las_inspect,
    geox_seismic_inspect,
    geox_seismic_segy_inspect,
    geox_tops_inspect,
)
from geox_mcp.tools.map_context import geox_map_context_scene
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
from geox_mcp.tools.petrophysics import (
    geox_subsurface_generate_candidates,
    geox_subsurface_verify_integrity,
)
from geox_mcp.tools.prospect import geox_prospect_evaluate
from geox_mcp.tools.qc import geox_data_qc_bundle
from geox_mcp.tools.registry import geox_system_registry_status
from geox_mcp.tools.seismic_compute import geox_seismic_compute
from geox_mcp.tools.sequence import geox_sequence_interpret
from geox_mcp.tools.discovery import arifos_route_query

logger = logging.getLogger("geox.unified13")

# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY REGISTRY — Kept for compatibility with external importers
# ═══════════════════════════════════════════════════════════════════════════════

_TOOL_REGISTRY: list[tuple[str, Any]] = [
    ("geox_data_ingest_bundle", geox_data_ingest_bundle),
    ("geox_data_qc_bundle", geox_data_qc_bundle),
    ("geox_dst_ingest_test", geox_dst_ingest_test),
    ("geox_las_inspect", geox_las_inspect),
    ("geox_seismic_inspect", geox_seismic_inspect),
    ("geox_deviation_survey_inspect", geox_deviation_survey_inspect),
    ("geox_tops_inspect", geox_tops_inspect),
    ("geox_seismic_segy_inspect", geox_seismic_segy_inspect),
    ("geox_subsurface_generate_candidates", geox_subsurface_generate_candidates),
    ("geox_subsurface_verify_integrity", geox_subsurface_verify_integrity),
    ("geox_seismic_compute", geox_seismic_compute),
    ("geox_sequence_interpret", geox_sequence_interpret),
    ("geox_evidence_reason", geox_evidence_reason),
    ("geox_prospect_evaluate", geox_prospect_evaluate),
    ("geox_map_context_scene", geox_map_context_scene),
    ("geox_system_registry_status", geox_system_registry_status),
    # paleoscan_python v2.0.0 forge
    ("geox_coord_transform_tool", geox_coord_transform_tool),
    ("geox_blockspace_resolution_tool", geox_blockspace_resolution_tool),
    ("geox_volume_get_frame_tool", geox_volume_get_frame_tool),
    ("geox_volume_set_frame_tool", geox_volume_set_frame_tool),
    ("geox_seismic_compute_attribute_tool", geox_seismic_compute_attribute_tool),
    ("geox_fault_stick_ingest_tool", geox_fault_stick_ingest_tool),
    ("geox_attribute_registry_list_tool", geox_attribute_registry_list_tool),
    # paleoscan_python v2.0.0 forge — blending + export
    ("geox_blend_volume_alpha_tool", geox_blend_volume_alpha_tool),
    ("geox_blend_volume_rgb_tool", geox_blend_volume_rgb_tool),
    ("geox_segy_export_tool", geox_segy_export_tool),
    # H5: Claim Engine
    ("geox_claim_create", geox_claim_create),
    ("geox_claim_challenge", geox_claim_challenge),
    ("geox_evidence_attach", geox_evidence_attach),
    ("geox_claim_seal", geox_claim_seal),
    # Discovery governance router (L0 mandatory pre-router)
    ("arifos_route_query", arifos_route_query),
]

_TOOL_ANNOTATIONS: dict[str, dict] = {
    "geox_data_ingest_bundle": {
        "ui": {"resourceUri": "ui://well_desk"},
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_data_qc_bundle": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_dst_ingest_test": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_las_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_deviation_survey_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_tops_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_segy_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_subsurface_generate_candidates": {
        "ui": {"resourceUri": "ui://earth_volume"},
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_subsurface_verify_integrity": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_compute": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_sequence_interpret": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_evidence_reason": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_prospect_evaluate": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_map_context_scene": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_system_registry_status": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
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
    # Discovery governance router
    "arifos_route_query": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    # H5: Claim Engine
    "geox_claim_create": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_claim_challenge": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_evidence_attach": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_claim_seal": {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY REGISTRATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════


def register_unified_tools(mcp: FastMCP, profile: str = "full") -> None:
    """Legacy entry-point: registers all 30 tools on a single FastMCP server.

    ⚠️  DEPRECATED: server.py now uses domain-server composition via mcp.mount().
    This function is kept for backward compatibility with tests and external callers.
    """
    logger.warning("register_unified_tools() is deprecated; use domain-server composition via geox_mcp.servers")

    register_tools_on_server(mcp, _TOOL_REGISTRY, _TOOL_ANNOTATIONS)

    if len(CANONICAL_PUBLIC_TOOLS) != 30:
        raise ValueError(f"F0_CONSTITUTION_BREACH: Expected 30 sovereign tools, got {len(CANONICAL_PUBLIC_TOOLS)}")
    logger.info(f"Witness Core surface: IGNITED ({len(CANONICAL_PUBLIC_TOOLS)} canonical tools)")
