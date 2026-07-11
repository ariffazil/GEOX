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
from fastmcp.apps import AppConfig, ResourceCSP

from geox_mcp.apps.workbench import GEOX_UI_APPS
from geox_mcp.tools._register import register_tools_on_server
from geox_mcp.tools.basin import (
    geox_abstraction_guard,
    geox_basin_profile,
    geox_basin_resolve,
    geox_literature_ingest,
    geox_query_intake,
)
from geox_mcp.tools.data import (
    geox_data_ingest_bundle,
    geox_evidence_discover,
    geox_report_to_workflow,
)
from geox_mcp.tools.dst import geox_dst_ingest_test
from geox_mcp.tools.evidence_reason import geox_evidence_reason
from geox_mcp.tools.horizon_contrast import geox_horizon_contrast_surface
from geox_mcp.tools.ingestion import (
    geox_header_inspect,
    geox_las_inspect,
    geox_seismic_segy_inspect,
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

_WITNESS_TOOLS: list[tuple[str, Any]] = [
    ("geox_data_ingest_bundle", geox_data_ingest_bundle),
    ("geox_data_qc_bundle", geox_data_qc_bundle),
    ("geox_dst_ingest_test", geox_dst_ingest_test),
    ("geox_header_inspect", geox_header_inspect),
    ("geox_evidence_discover", geox_evidence_discover),
    ("geox_report_to_workflow", geox_report_to_workflow),
    ("geox_subsurface_generate_candidates", geox_subsurface_generate_candidates),
    ("geox_subsurface_verify_integrity", geox_subsurface_verify_integrity),
    ("geox_seismic_compute", geox_seismic_compute),
    ("geox_sequence_interpret", geox_sequence_interpret),
    ("geox_evidence_reason", geox_evidence_reason),
    ("geox_prospect_evaluate", geox_prospect_evaluate),
    ("geox_map_context_scene", geox_map_context_scene),
    ("geox_system_registry_status", geox_system_registry_status),
    ("geox_horizon_contrast_surface", geox_horizon_contrast_surface),
    ("geox_basin_resolve", geox_basin_resolve),
    ("geox_basin_profile", geox_basin_profile),
    ("geox_query_intake", geox_query_intake),
    ("geox_abstraction_guard", geox_abstraction_guard),
    ("geox_literature_ingest", geox_literature_ingest),
    ("geox_las_inspect", geox_las_inspect),
    ("geox_seismic_segy_inspect", geox_seismic_segy_inspect),
]

_WITNESS_ANNOTATIONS: dict[str, dict] = {
    "geox_data_ingest_bundle": {
        "title": "Data Ingest Bundle",
        "ui": {"resourceUri": "ui://geox/workbench-v1.html"},
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
    "geox_header_inspect": {
        "title": "Header Inspect",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_evidence_discover": {
        "title": "Evidence Discover",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_report_to_workflow": {
        "title": "Report to Workflow",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,  # P1.3: external_side_effect — output may feed downstream decision pipelines
        "mcp_safety_tier": "Tier 0 (interpretive)",
        "output_class": "DRAFT_REPORT",
        "fiqh_class": "wajib_guarded",
        "requires_human_review": True,
        "can_mutate_model": False,
        "can_touch_ops": False,
        "reversible": True,
    },
    "geox_subsurface_generate_candidates": {
        "title": "Subsurface Generate Candidates",
        "ui": {"resourceUri": "ui://geox/workbench-v1.html"},
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
        "ui": {"resourceUri": "ui://geox/workbench-v1.html"},
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
        "ui": {"resourceUri": "ui://geox/workbench-v1.html"},
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_map_context_scene": {
        "title": "Map Context Scene",
        "ui": {"resourceUri": "ui://geox/workbench-v1.html"},
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
    "geox_basin_resolve": {
        "title": "Basin Resolve",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_basin_profile": {
        "title": "Basin Profile",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_query_intake": {
        "title": "Query Intake",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_abstraction_guard": {
        "title": "Abstraction Guard",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_literature_ingest": {
        "title": "Literature Ingest",
        "readOnlyHint": True,
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
    "geox_seismic_segy_inspect": {
        "title": "SEG-Y Inspect",
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

# ── MCP App View bindings (forged 2026-07-11) ─────────────────────────────
# Maps visual GEOX tools to the unified workbench resource.
# When registered via register_tools_on_server(apps=...), the tool's metadata
# advertises ui.resourceUri so MCP Apps hosts (ChatGPT, Claude, Copilot) know
# to render the workbench iframe after a tool call.
_WITNESS_APPS: dict[str, AppConfig] = {
    name: AppConfig(
        resourceUri="ui://geox/workbench-v1.html",
        visibility=["app", "model"],
    )
    for name in (
        "geox_map_context_scene",
        "geox_seismic_compute",
        "geox_horizon_contrast_surface",
        "geox_subsurface_generate_candidates",
        "geox_prospect_evaluate",
        "geox_volume_get_frame_tool",  # backward-compat alias
        "geox_seismic_compute_attribute_tool",  # backward-compat alias
    )
}


def create_witness_server() -> FastMCP:
    server = FastMCP("geox-witness")
    register_tools_on_server(server, _WITNESS_TOOLS, _WITNESS_ANNOTATIONS, tasks=_WITNESS_TASKS, apps=_WITNESS_APPS)
    return server
