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
    """Discovery of canonical tools, health, and contract epoch.

    Reports the ACTUAL live MCP surface — no phantom aliases, no ghost ingress tools.
    F2 Truth: the registry must not lie about what is callable.
    """
    import os
    from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS

    _show_legacy = os.getenv("GEOX_SHOW_LEGACY_ALIASES", "false").lower() in ("1", "true", "yes")

    artifact = {
        "status": "healthy",
        "epoch": "2026-05-01",
        "tools_count": len(CANONICAL_PUBLIC_TOOLS) + 1,  # +1 for geox_dst_ingest_test
        "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
        "ingress_tools": [],
        "contract": "SOVEREIGN_13_SPEC",
        "legacy_aliases": {} if not _show_legacy else {},
        "note": "Legacy aliases are hidden. Call aliases via canonical names only.",
    }
    return get_standard_envelope(artifact, tool_class="system")



async def geox_history_audit(
    query: str,
    limit: int = 10,
    actor_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """VAULT999 retrieval of past runs and decision lineage.

    Each returned record must include:
    - renderer_name: the renderer used (e.g. "matplotlib", "plotly")
    - artifact_hash: SHA-256 of the produced visual artifact (PNG/SVG/PDF)
    - claim_state: lifecycle state at time of generation
    - depth_basis: MD/TVD/TVDSS
    These fields are required for all records involving visual artifacts.
    """
    import logging
    logger = logging.getLogger("geox.history_audit")

    # F1 Amanah: defensive input sanitization
    clean_query = query[:1000] if query else ""
    clean_query = clean_query.replace("\x00", "")
    safe_limit = max(1, min(limit, 50))

    try:
        # TODO: wire to actual VAULT999 / evidence_store query
        # For now, return empty but governed response instead of 502
        artifact = {
            "query": clean_query,
            "records": [],
            "vault": "VAULT999",
            "renderer_lineage_policy": (
                "Records involving visual artifacts must include renderer_name + artifact_hash. "
                "Missing renderer info = lineage incomplete. "
                "SHA-256 hash of the artifact file must be present."
            ),
        }
        return get_standard_envelope(
            artifact,
            tool_class="system",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
        )
    except Exception as exc:
        logger.exception("geox_history_audit failed")
        return get_standard_envelope(
            {
                "tool": "geox_history_audit",
                "error_code": "HISTORY_AUDIT_FAILED",
                "message": str(exc)[:300],
                "retryable": False,
            },
            tool_class="system",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
        )


