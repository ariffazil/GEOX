from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Literal

from fastmcp import FastMCP
from geox_core.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
    enrich_envelope_with_metabolic,
)
from geox_mcp.tools._helpers import (
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
from geox_core.compatibility.legacy_aliases import LEGACY_ALIAS_MAP, get_alias_metadata

logger = logging.getLogger("geox.canonical.seismic")


async def geox_seismic_analyze_volume(
    volume_ref: str,
    mode: Literal[
        "load_line", "load_volume", "compute_attribute", "render_slice", "vision_review", "viewer_payload"
    ] = "compute_attribute",
    attribute: str = "rms",
) -> dict:
    """Seismic attribute computation, slice rendering, and interpretation support.

    Args:
        volume_ref: Seismic volume artifact reference.
        mode: Operation mode.
            - "load_line": Load a 2D seismic line.
            - "load_volume": Load a 3D SEG-Y volume.
            - "compute_attribute": Compute seismic attributes (default).
            - "render_slice": Render a slice PNG from the volume.
            - "vision_review": Vision-model review of slice images.
            - "viewer_payload": Prepare payload for seismic viewer app.
        attribute: Seismic attribute to compute (e.g. "rms", "variance", "sweetness", "coherence").
    """
    # FORGET: Removed mock "status": "Computed". F9-Rahmah: no fabrication.
    if not _artifact_exists(volume_ref):
        return get_standard_envelope(
            {"tool": "geox_seismic_analyze_volume", "error_code": "NO_VALID_EVIDENCE",
             "message": f"Seismic volume '{volume_ref}' not found. Ingest SEG-Y via geox_data_ingest_bundle first."},
            tool_class="compute", execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD, artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS", claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[volume_ref],
        )

    # Honest status: volume ingested but attribute computation engine is pending
    artifact = {
        "volume_ref": volume_ref,
        "mode": mode,
        "attribute": attribute,
        "status": "PENDING_ENGINE",
        "note": "Volume evidence present. Real attribute computation (RMS/variance/sweetness) requires SEG-Y engine activation.",
    }
    envelope = get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="HYPOTHESIS",
        claim_state="INGESTED",
        perception_class="DISPLAY",
        evidence_refs=[volume_ref],
        physics_guard={
            "guard_passed": True,
            "physics_version": "geox-seismic-v2026.05.21",
            "equations_used": [],
            "assumptions": ["Volume loaded but attribute computation not yet implemented"],
        },
    )
    envelope["confidence"] = {
        "level": "UNKNOWN",
        "sensitivity_to": ["seg_y_engine_availability", "attribute_algorithm_selection"],
    }
    return enrich_envelope_with_metabolic(envelope, "geox_seismic_analyze_volume")
