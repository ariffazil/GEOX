from __future__ import annotations

import logging
import os
from typing import List, Optional, Literal

from geox_core.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)
from geox_mcp.tools._helpers import (
    _classify_gr_motif,
    CANONICAL_ALIASES,
)

logger = logging.getLogger("geox.canonical.section")


async def geox_section_interpret_correlation(
    section_ref: str,
    well_refs: List[str],
    mode: Literal["correlation", "gr_motif", "sequence_stratigraphy", "gde_trend", "well_tie"] = "correlation",
    well_las_paths: Optional[List[str]] = None,
    tops: Optional[dict] = None,
    zone_definitions: Optional[dict] = None,
    strat_standard: Optional[dict] = None,
    paleoenvironment_input: Optional[List[dict]] = None,
    # ── well_tie parameters ──────────────────────────────────────────────────
    checkshot_ref: Optional[str] = None,
    wavelet_mode: Literal["ricker", "ormsby", "klauder", "estimated"] = "ricker",
    wavelet_freq_hz: Optional[List[float]] = None,
    phase_degrees: float = 0.0,
    polarity: Literal["SEG_NORMAL", "SEG_REVERSE"] = "SEG_NORMAL",
    synthetics_output: bool = False,
    tie_qc_report: bool = True,
    seismic_ref: Optional[str] = None,
    sonic_curve: Optional[str] = "DT",
    density_curve: Optional[str] = "RHOB",
    matrix_density: float = 2.65,
    fluid_density: float = 1.0,
) -> dict:
    """Multi-well stratigraphic correlation and marker interpretation.

    Args:
        section_ref: Section identifier.
        well_refs: List of well artifact_refs or well IDs.
        mode: Interpretation mode.
            - "correlation": standard marker correlation (default).
            - "gr_motif": classify GR motif per well with EOD hints.
            - "sequence_stratigraphy": identify candidate SB/TS/MFS surfaces.
            - "gde_trend": calculate vertical paleoenvironment trends from GDE stacks.
            - "well_tie": full well-to-seismic tie with synthetic seismogram generation.
        well_las_paths: Optional LAS file paths for gr_motif/sequence modes.
        tops: {well_id: {marker_name: depth_m}} for annotation.
        zone_definitions: {zone_name: {top_m, base_m}} for zone-level motif.
        strat_standard: Stratigraphic reference scheme. e.g. {"scheme": "NN_zone", "reference_chart": "GPTS2020"}.
        paleoenvironment_input: List of {well_id, depth_m, gde_code, gde_index} for gde_trend mode.

        # well_tie-specific args
        checkshot_ref: Artifact ref for checkshot table (depth_md → twt_ms).
            Required for accurate T-D conversion. If absent, uses average-velocity from sonic.
        wavelet_mode: Wavelet type: "ricker" | "ormsby" | "klauder" | "estimated".
        wavelet_freq_hz: Wavelet frequency Hz. Scalar for ricker/klauder; [f1,f2,f3,f4] for ormsby.
        phase_degrees: Phase rotation to apply to synthetic trace (degrees).
        polarity: "SEG_NORMAL" (default) or "SEG_REVERSE" (inverts RC sign).
        synthetics_output: If True, register and return synthetic trace artifact ref.
        tie_qc_report: If True, include correlation traces in output.
        seismic_ref: Optional seismic trace artifact for cross-correlation QC.
        sonic_curve: LAS mnemonic for sonic curve (default "DT", also "DT4").
        density_curve: LAS mnemonic for density curve (default "RHOB").
        matrix_density: g/cm³ fallback matrix density when no RHOB available.
        fluid_density: g/cm³ fallback fluid density when no RHOB available.
    """
    import sys

    sys.path.insert(0, "/root/geox")
    import numpy as np

    # ── well_tie mode ────────────────────────────────────────────────────────
    if mode == "well_tie":
        from geox_core.core.welltie import compute_welltie
        from geox_mcp.tools._helpers import _get_artifact

        if not well_refs:
            return get_standard_envelope(
                {
                    "tool": "geox_section_interpret_correlation",
                    "error_code": "NO_WELL_REF",
                    "message": "well_tie mode requires at least one well_ref.",
                },
                tool_class="interpret",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )

        # Resolve LAS path from first well_ref
        first_ref = well_refs[0]
        las_entry = _get_artifact(first_ref)
        if las_entry and las_entry.get("las_path"):
            las_path = las_entry["las_path"]
        elif well_las_paths and len(well_las_paths) > 0:
            las_path = well_las_paths[0]
        else:
            return get_standard_envelope(
                {
                    "tool": "geox_section_interpret_correlation",
                    "error_code": "NO_LAS_PATH",
                    "message": ("well_tie mode requires a well_ref with a registered LAS path or a well_las_paths argument."),
                },
                tool_class="interpret",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )

        try:
            artifact = compute_welltie(
                las_path=las_path,
                checkshot_ref=checkshot_ref,
                wavelet_mode=wavelet_mode,
                wavelet_freq_hz=wavelet_freq_hz,
                phase_degrees=phase_degrees,
                polarity=polarity,
                seismic_ref=seismic_ref,
                sonic_curve=sonic_curve or "DT",
                density_curve=density_curve or "RHOB",
                matrix_density=matrix_density,
                fluid_density=fluid_density,
            )
        except ValueError as e:
            return get_standard_envelope(
                {
                    "tool": "geox_section_interpret_correlation",
                    "error_code": "WELLTIE_COMPUTATION_ERROR",
                    "message": str(e),
                },
                tool_class="interpret",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )

        # Determine claim_state based on tie verdict
        tie_verdict = artifact.get("tie_quality_verdict", "UNDETERMINED")
        if tie_verdict == "UNDETERMINED":
            claim_state = "DERIVED_CANDIDATE"
            execution_status = ExecutionStatus.SUCCESS
            governance_status = GovernanceStatus.HOLD
            artifact_status = ArtifactStatus.COMPUTED
            claim_tag = "HYPOTHESIS"
        else:
            claim_state = "INTERPRETED"
            execution_status = ExecutionStatus.SUCCESS
            governance_status = GovernanceStatus.QUALIFY
            artifact_status = ArtifactStatus.COMPUTED
            claim_tag = "PLAUSIBLE"

        return get_standard_envelope(
            artifact,
            tool_class="interpret",
            execution_status=execution_status,
            governance_status=governance_status,
            artifact_status=artifact_status,
            claim_tag=claim_tag,
            claim_state=claim_state,
            perception_class="DERIVED",
            uncertainty="Moderate" if tie_verdict == "UNDETERMINED" else "Low",
        )

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
        return get_standard_envelope(
            artifact,
            tool_class="interpret",
            claim_tag="HYPOTHESIS",
            claim_state="INTERPRETED",
            perception_class="DERIVED",
            evidence_tag="EVIDENCE_DIRECT",
            strat_standard=strat_standard or {"scheme": "NN_zone", "reference_chart": ""},
        )

    # ── GDE trend mode (ToAC v1: vertical paleoenvironment trend from GDE stacks) ──
    if mode == "gde_trend":
        if not paleoenvironment_input:
            return get_standard_envelope(
                {
                    "tool": "geox_section_interpret_correlation",
                    "error_code": "NO_GDE_INPUT",
                    "message": "gde_trend mode requires paleoenvironment_input: [{well_id, depth_m, gde_code, gde_index}]",
                },
                tool_class="interpret",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )

        # Calculate vertical trend from GDE indices using 3-bin sliding window
        # (same algorithm as Kinabalu Basin 10 m biostrat workbook)
        trend_results: dict[str, list[dict]] = {}
        for entry in paleoenvironment_input:
            wid = entry.get("well_id", "UNKNOWN")
            if wid not in trend_results:
                trend_results[wid] = []
            trend_results[wid].append(entry)

        for wid, gde_entries in trend_results.items():
            gde_entries.sort(key=lambda e: e.get("depth_m", 0))
            gde_indices = np.array([e.get("gde_index", -1) for e in gde_entries], dtype=float)
            for pos in range(len(gde_entries)):
                window_before = gde_indices[max(0, pos - 2) : pos + 1]
                window_after = gde_indices[pos : min(len(gde_entries), pos + 3)]
                shallow = np.nanmean(window_before[window_before >= 0]) if np.any(window_before >= 0) else np.nan
                deep = np.nanmean(window_after[window_after >= 0]) if np.any(window_after >= 0) else np.nan
                if np.isnan(shallow) or np.isnan(deep) or abs(shallow - deep) < 0.75:
                    trend = "STABLE_OR_AMBIGUOUS"
                elif shallow > deep:
                    trend = "DEEPENING_UPWARD"
                else:
                    trend = "SHALLOWING_UPWARD"
                gde_entries[pos]["vertical_trend"] = trend

        return get_standard_envelope(
            {
                "tool": "geox_section_interpret_correlation",
                "section_ref": section_ref,
                "mode": "gde_trend",
                "trend_results": trend_results,
                "claim_state": "DERIVED_CANDIDATE",
                "risk": "Vertical GDE trend is derived from 3-bin sliding window. Requires biostrat/lithology GDE picks as input.",
            },
            tool_class="interpret",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.COMPUTED,
            claim_tag="PLAUSIBLE",
            vertical_trend="COMPOSITE",
            perception_class="DERIVED",
            strat_standard=strat_standard or {"scheme": "NN_zone", "reference_chart": ""},
        )

    # ── GR motif / sequence stratigraphy ─────────────────────────────────
    from geox_core.core.geox_1d import process_las_file

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
            candidate_surfaces.append(
                {
                    "well_id": well_id,
                    "surface_type": "TS_CANDIDATE",
                    "evidence": "Bell motif — fining-upward suggests possible Transgressive Surface",
                    "confidence": motif.get("confidence", 0.5),
                    "depth_m": float(depth_arr[0]) if depth_arr is not None and len(depth_arr) > 0 else None,
                    "claim_state": "DERIVED_CANDIDATE",
                }
            )
        elif m == "FUNNEL":
            candidate_surfaces.append(
                {
                    "well_id": well_id,
                    "surface_type": "MFS_CANDIDATE",
                    "evidence": "Funnel motif — coarsening-upward suggests progradation below possible MFS",
                    "confidence": motif.get("confidence", 0.5),
                    "depth_m": float(depth_arr[0]) if depth_arr is not None and len(depth_arr) > 0 else None,
                    "claim_state": "DERIVED_CANDIDATE",
                }
            )

        # Check tops for gaps suggesting SB
        if tops and well_id in tops:
            well_tops = tops[well_id]
            sorted_tops = sorted(well_tops.items(), key=lambda x: x[1])
            for i in range(len(sorted_tops) - 1):
                mk_a, dep_a = sorted_tops[i]
                mk_b, dep_b = sorted_tops[i + 1]
                gap = dep_b - dep_a
                if gap > 100:  # arbitrary threshold for missing section
                    candidate_surfaces.append(
                        {
                            "well_id": well_id,
                            "surface_type": "SB_CANDIDATE",
                            "evidence": f"Gap of {gap:.0f}m between {mk_a} and {mk_b} — possible erosional truncation / SB",
                            "confidence": 0.4,
                            "depth_m": dep_a,
                            "claim_state": "DERIVED_CANDIDATE",
                        }
                    )

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
