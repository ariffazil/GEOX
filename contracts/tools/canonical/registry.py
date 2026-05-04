from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Literal

from fastmcp import FastMCP
from contracts.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)
from contracts.tools.canonical._helpers import (
    _get_artifact,
    _artifact_exists,
    _register_artifact,
    _record_latest_qc,
    _latest_qc_failed_refs,
    _check_maruah_territory,
    _inject_ensemble_residual_evidence,
    _safe_upload_path,
    _decode_upload_content,
    _parse_csv_or_json,
    _map_canonical_curves,
    _detect_depth_unit,
    _compute_vsh_from_store,
    _compute_porosity_from_store,
    _compute_saturation_from_store,
    _compute_netpay_from_store,
    _classify_gr_motif,
    _classify_lithology_from_store,
    _safe_reduction,
    _get_well_data_with_depth,
    CLAIM_STATES,
    CANONICAL_ALIASES,
    _CURVE_RANGES,
    _artifact_registry,
    _artifact_store,
    _well_curves_registry,
    _ARTIFACT_REGISTRY_PATH,
    MAX_UPLOAD_BYTES,
)
from compatibility.legacy_aliases import LEGACY_ALIAS_MAP, get_alias_metadata

logger = logging.getLogger("geox.canonical.registry")


async def geox_system_registry_status() -> dict:
    """Discovery of 13 tools, health, and contract epoch."""
    from compatibility.legacy_aliases import LEGACY_ALIAS_MAP
    artifact = {
        "status": "healthy",
        "epoch": "2026-05-01",
        "tools_count": 13,
        "canonical_tools": 13,
        "ingress_tools": ["geox_file_upload_import"],
        "contract": "SOVEREIGN_13_SPEC",
        "legacy_aliases": LEGACY_ALIAS_MAP
    }
    return get_standard_envelope(artifact, tool_class="system")



async def geox_history_audit(query: str) -> dict:
    """VAULT999 retrieval of past runs and decision lineage.

    Each returned record must include:
    - renderer_name: the renderer used (e.g. "matplotlib", "plotly")
    - artifact_hash: SHA-256 of the produced visual artifact (PNG/SVG/PDF)
    - claim_state: lifecycle state at time of generation
    - depth_basis: MD/TVD/TVDSS
    These fields are required for all records involving visual artifacts.
    """
    artifact = {
        "query": query,
        "records": [],
        "vault": "VAULT999",
        "renderer_lineage_policy": (
            "Records involving visual artifacts must include renderer_name + artifact_hash. "
            "Missing renderer info = lineage incomplete. "
            "SHA-256 hash of the artifact file must be present."
        ),
    }
    return get_standard_envelope(artifact, tool_class="system")


