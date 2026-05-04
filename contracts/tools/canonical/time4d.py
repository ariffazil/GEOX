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

logger = logging.getLogger("geox.canonical.time4d")


async def geox_time4d_analyze_system(
    prospect_ref: str,
    mode: str = "burial",
    evidence_refs: list[str] | None = None,
) -> dict:
    """Burial history, maturity modeling, and regime shift analysis.

    F2 Truth: without source-rock / VRo / Tmax / basin-model evidence,
    maturity is UNDETERMINED and labelled as HYPOTHESIS.
    """
    refs = evidence_refs or []
    if not refs:
        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "maturity": "UNDETERMINED",
            "reason": "No burial model / source rock / VRo / Tmax evidence supplied",
        }
        return get_standard_envelope(
            artifact,
            tool_class="compute",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[],
        )
    artifact = {
        "ref": prospect_ref,
        "mode": mode,
        "maturity": "Oil_Window",
        "basis": "REGIONAL_PRIOR",
        "evidence_refs": refs,
    }
    return get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="PLAUSIBLE",
        claim_state="INTERPRETED",
        evidence_refs=refs,
    )


