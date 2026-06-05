"""
GEOX Witness Domain Server — Observe / Verify / Ingest
══════════════════════════════════════════════════════
Canonical witness tools: well ingest, LAS, seismic inspection,
petrophysics, sequence, evidence, prospect, map context, registry.

Mounted by server.py with namespace=None (original names preserved).
DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from geox_mcp.tools._register import register_tools_on_server
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
from geox_mcp.tools.petrophysics import (
    geox_subsurface_generate_candidates,
    geox_subsurface_verify_integrity,
)
from geox_mcp.tools.prospect import geox_prospect_evaluate
from geox_mcp.tools.qc import geox_data_qc_bundle
from geox_mcp.tools.registry import geox_system_registry_status
from geox_mcp.tools.seismic_compute import geox_seismic_compute
from geox_mcp.tools.sequence import geox_sequence_interpret
from geox_mcp.tools.horizon_contrast import geox_horizon_contrast_surface

_WITNESS_TOOLS: list[tuple[str, Any]] = [
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
    ("geox_horizon_contrast_surface", geox_horizon_contrast_surface),
]

_WITNESS_ANNOTATIONS: dict[str, dict] = {
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
    "geox_horizon_contrast_surface": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


def create_witness_server() -> FastMCP:
    server = FastMCP("geox-witness")
    register_tools_on_server(server, _WITNESS_TOOLS, _WITNESS_ANNOTATIONS)
    return server
