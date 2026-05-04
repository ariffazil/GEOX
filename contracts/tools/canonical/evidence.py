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

logger = logging.getLogger("geox.canonical.evidence")


async def geox_evidence_summarize_cross(
    evidence_refs: List[str],
    export_format: Literal["json", "csv"] = "json",
    output_path: Optional[str] = None,
) -> dict:
    """Cross-domain synthesis into a causal evidence graph.

    Args:
        evidence_refs: List of artifact refs to synthesize.
        export_format: Output format if output_path is provided ("json" or "csv").
        output_path: If provided, write the evidence summary to this path.
    """
    artifact = {
        "refs": evidence_refs,
        "graph": "synthesized",
        "contradictions": [],
        "visual_artifact_policy": (
            "Visual artifacts (PNG, SVG, HTML) in the evidence graph are supporting "
            "evidence only — they do not constitute physical truth by themselves. "
            "Every visual artifact must be accompanied by its claim_state, depth_basis, "
            "and artifact validation status. Do not promote a visual artifact to "
            "physical evidence without explicit unit + depth + QC verification."
        ),
    }
    result = get_standard_envelope(artifact, tool_class="compute")

    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            if export_format == "csv":
                with open(output_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["artifact_ref", "claim_state", "note"])
                    for ref in evidence_refs:
                        entry = _get_artifact(ref)
                        cs = entry.get("claim_state", "UNKNOWN") if entry else "NOT_REGISTERED"
                        writer.writerow([ref, cs, ""])
            else:
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2, default=str)
            result["export_written"] = True
            result["export_path"] = output_path
            result["export_format"] = export_format
        except Exception as exc:
            result["export_written"] = False
            result["export_error"] = str(exc)

    return result


