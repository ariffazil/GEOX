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

logger = logging.getLogger("geox.canonical.section")


async def geox_section_interpret_correlation(
    section_ref: str,
    well_refs: List[str],
    mode: Literal["correlation", "gr_motif", "sequence_stratigraphy"] = "correlation",
    well_las_paths: Optional[List[str]] = None,
    tops: Optional[dict] = None,
    zone_definitions: Optional[dict] = None,
) -> dict:
    """Multi-well stratigraphic correlation and marker interpretation.

    Args:
        section_ref: Section identifier.
        well_refs: List of well artifact_refs or well IDs.
        mode: Interpretation mode.
            - "correlation": standard marker correlation (default).
            - "gr_motif": classify GR motif per well with EOD hints.
            - "sequence_stratigraphy": identify candidate SB/TS/MFS surfaces.
        well_las_paths: Optional LAS file paths for gr_motif/sequence modes.
        tops: {well_id: {marker_name: depth_m}} for annotation.
        zone_definitions: {zone_name: {top_m, base_m}} for zone-level motif.
    """
    import sys
    sys.path.insert(0, "/root/geox")
    import numpy as np

    if mode == "correlation":
        artifact = {
            "section_ref": section_ref,
            "wells": well_refs,
            "markers": [],
            "tie_type_policy": (
                "Each marker tie must be tagged: observed (well log pick), "
                "derived (from seismic interpretation), or hypothesized (GR motif extrapolation). "
                "Untagged markers default to hypothesized."
            ),
        }
        return get_standard_envelope(artifact, tool_class="interpret")

    # ── GR motif / sequence stratigraphy ─────────────────────────────────
    from geox.core.geox_1d import process_las_file

    # Build list of (well_id, las_path) pairs
    well_sources: list[tuple[str, str]] = []
    for i, ref in enumerate(well_refs):
        entry = _get_artifact(ref)
        if entry and entry.get("las_path"):
            well_sources.append((ref, entry["las_path"]))
        elif well_las_paths and i < len(well_las_paths):
            well_sources.append((ref, well_las_paths[i]))

    if not well_sources:
        # Try well_las_paths standalone
        if well_las_paths:
            for i, lp in enumerate(well_las_paths):
                wid = well_refs[i] if i < len(well_refs) else f"well_{i}"
                well_sources.append((wid, lp))

    if not well_sources:
        return get_standard_envelope(
            {
                "tool": "geox_section_interpret_correlation",
                "error_code": "NO_LAS_SOURCES",
                "message": "No LAS paths available. Provide well_refs with registered artifacts or well_las_paths.",
                "claim_state": "NO_VALID_EVIDENCE",
            },
            tool_class="interpret",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
        )

    motifs_by_well: dict[str, dict] = {}
    for well_id, las_path in well_sources:
        if not os.path.exists(las_path):
            motifs_by_well[well_id] = {"error": "LAS_FILE_NOT_FOUND"}
            continue
        curves = process_las_file(las_path)
        if "ERROR" in curves:
            motifs_by_well[well_id] = {"error": "LAS_PARSE_FAILED"}
            continue
        gr = None
        for alias in CANONICAL_ALIASES.get("GR", ["GR"]):
            if alias in curves:
                gr = curves[alias]
                break
        depth = None
        for dk in ["DEPT", "DEPTH", "MD"]:
            if dk in curves:
                depth = curves[dk]
                break
        if gr is None or depth is None:
            motifs_by_well[well_id] = {"error": "GR_OR_DEPTH_NOT_FOUND"}
            continue

        if zone_definitions:
            for zone_name, zdef in zone_definitions.items():
                zt = zdef.get("top_m")
                zb = zdef.get("base_m")
                motif = _classify_gr_motif(gr, depth, zt, zb)
                motifs_by_well[well_id] = {**motif, "zone": zone_name}
        else:
            motif = _classify_gr_motif(gr, depth)
            motifs_by_well[well_id] = motif

    if mode == "gr_motif":
        return get_standard_envelope(
            {
                "tool": "geox_section_interpret_correlation",
                "section_ref": section_ref,
                "mode": "gr_motif",
                "wells_processed": len(well_sources),
                "motifs_by_well": motifs_by_well,
                "claim_state": "DERIVED_CANDIDATE",
                "risk": "motif interpretation requires seismic/fossil tie for EOD confirmation",
            },
            tool_class="interpret",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.COMPUTED,
            claim_tag="PLAUSIBLE",
        )

    # ── Sequence stratigraphy ─────────────────────────────────────────────
    candidate_surfaces: list[dict] = []
    for well_id, motif in motifs_by_well.items():
        if "error" in motif:
            continue
        m = motif.get("motif", "UNKNOWN")
        depth_arr = None
        for _, las_path in well_sources:
            curves = process_las_file(las_path)
            for dk in ["DEPT", "DEPTH", "MD"]:
                if dk in curves:
                    depth_arr = curves[dk]
                    break
            if depth_arr is not None:
                break

        # Look for pattern-based surface candidates
        if m == "BELL":
            candidate_surfaces.append({
                "well_id": well_id,
                "surface_type": "TS_CANDIDATE",
                "evidence": "Bell motif — fining-upward suggests possible Transgressive Surface",
                "confidence": motif.get("confidence", 0.5),
                "depth_m": float(depth_arr[0]) if depth_arr is not None and len(depth_arr) > 0 else None,
                "claim_state": "DERIVED_CANDIDATE",
            })
        elif m == "FUNNEL":
            candidate_surfaces.append({
                "well_id": well_id,
                "surface_type": "MFS_CANDIDATE",
                "evidence": "Funnel motif — coarsening-upward suggests progradation below possible MFS",
                "confidence": motif.get("confidence", 0.5),
                "depth_m": float(depth_arr[0]) if depth_arr is not None and len(depth_arr) > 0 else None,
                "claim_state": "DERIVED_CANDIDATE",
            })

        # Check tops for gaps suggesting SB
        if tops and well_id in tops:
            well_tops = tops[well_id]
            sorted_tops = sorted(well_tops.items(), key=lambda x: x[1])
            for i in range(len(sorted_tops) - 1):
                mk_a, dep_a = sorted_tops[i]
                mk_b, dep_b = sorted_tops[i + 1]
                gap = dep_b - dep_a
                if gap > 100:  # arbitrary threshold for missing section
                    candidate_surfaces.append({
                        "well_id": well_id,
                        "surface_type": "SB_CANDIDATE",
                        "evidence": f"Gap of {gap:.0f}m between {mk_a} and {mk_b} — possible erosional truncation / SB",
                        "confidence": 0.4,
                        "depth_m": dep_a,
                        "claim_state": "DERIVED_CANDIDATE",
                    })

    return get_standard_envelope(
        {
            "tool": "geox_section_interpret_correlation",
            "section_ref": section_ref,
            "mode": "sequence_stratigraphy",
            "wells_processed": len(well_sources),
            "motifs_by_well": motifs_by_well,
            "candidate_surfaces": candidate_surfaces,
            "claim_state": "DERIVED_CANDIDATE",
            "risk": "Sequence stratigraphy from GR motifs only — requires fossil biozone tie, seismic terminations, and core observation for validation. All surfaces are DERIVED_CANDIDATE.",
        },
        tool_class="interpret",
        execution_status=ExecutionStatus.SUCCESS,
        artifact_status=ArtifactStatus.COMPUTED,
        claim_tag="PLAUSIBLE",
    )


