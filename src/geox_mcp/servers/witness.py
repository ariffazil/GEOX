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
        "title": "Data Ingest Bundle",
        "ui": {"resourceUri": "ui://well_desk"},
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_data_qc_bundle": {
        "title": "Data QC Bundle",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_dst_ingest_test": {
        "title": "DST Ingest Test",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_las_inspect": {
        "title": "LAS Inspect",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_inspect": {
        "title": "Seismic Inspect",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_deviation_survey_inspect": {
        "title": "Deviation Survey Inspect",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_tops_inspect": {
        "title": "Tops Inspect",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_segy_inspect": {
        "title": "Seismic SEGY Inspect",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_subsurface_generate_candidates": {
        "title": "Subsurface Generate Candidates",
        "ui": {"resourceUri": "ui://earth_volume"},
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_subsurface_verify_integrity": {
        "title": "Subsurface Verify Integrity",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_compute": {
        "title": "Seismic Compute",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_sequence_interpret": {
        "title": "Sequence Interpret",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_evidence_reason": {
        "title": "Evidence Reason",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_prospect_evaluate": {
        "title": "Prospect Evaluate",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_map_context_scene": {
        "title": "Map Context Scene",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_system_registry_status": {
        "title": "System Registry Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_horizon_contrast_surface": {
        "title": "Horizon Contrast Surface",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


_WITNESS_TASKS: set[str] = {
    "geox_data_ingest_bundle",
    "geox_evidence_reason",
}


def create_witness_server() -> FastMCP:
    server = FastMCP("geox-witness")
    register_tools_on_server(server, _WITNESS_TOOLS, _WITNESS_ANNOTATIONS, tasks=_WITNESS_TASKS)
    return server
