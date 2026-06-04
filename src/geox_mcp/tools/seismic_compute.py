"""
GEOX Seismic Compute — Unified Seismic Physics Engine
═══════════════════════════════════════════════════════
Forged from the energy of 4 predecessor tools:
  geox_forward_model_synthetic
  geox_seismic_well_tie_compute
  geox_time_depth_anchor
  geox_anomalous_contrast_detector

One entry point. Explicit modes. Honest about pending engines.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastmcp import Context

from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    enrich_envelope_with_metabolic,
    get_standard_envelope,
)
from geox_mcp.tools._helpers import _artifact_exists

logger = logging.getLogger("geox.seismic_compute")

TOOL_NAME = "geox_seismic_compute"


# ═══════════════════════════════════════════════════════════════════════════════
# MODE: synthetic (absorbs geox_forward_model_synthetic)
# ═══════════════════════════════════════════════════════════════════════════════


async def _mode_synthetic(
    well_id: str | None,
    vp: list[float] | None,
    rho: list[float] | None,
    depth: list[float] | None,
    wavelet_type: str,
    wavelet_freq: float,
    wavelet_params: dict | None,
    water_depth_m: float,
    vp_water: float,
    dt_ms: float,
    noise_db: float,
    output_format: str,
) -> dict[str, Any]:
    from geox_mcp.tools.forward_model_synthetic import geox_forward_model_synthetic

    return await geox_forward_model_synthetic(
        well_id=well_id,
        vp=vp,
        rho=rho,
        depth=depth,
        wavelet_type=wavelet_type,  # type: ignore[arg-type]
        wavelet_freq=wavelet_freq,
        wavelet_params=wavelet_params,
        water_depth_m=water_depth_m,
        vp_water=vp_water,
        dt_ms=dt_ms,
        noise_db=noise_db,
        output_format=output_format,  # type: ignore[arg-type]
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MODE: well_tie (absorbs geox_seismic_well_tie_compute)
# ═══════════════════════════════════════════════════════════════════════════════


async def _mode_well_tie(
    well_id: str,
    volume_ref: str,
    extraction_window_ms: float,
    frequency_band: tuple[float, float],
    wavelet_type: str,
    apply_gardner_fallback: bool,
    apply_anisotropy_correction: bool,
    q_factor: float,
) -> dict[str, Any]:
    from geox_mcp.tools.seismic_well_tie import geox_seismic_well_tie_compute

    return await geox_seismic_well_tie_compute(
        well_id=well_id,
        volume_ref=volume_ref,
        extraction_window_ms=extraction_window_ms,
        frequency_band=frequency_band,
        wavelet_type=wavelet_type,  # type: ignore[arg-type]
        apply_gardner_fallback=apply_gardner_fallback,
        apply_anisotropy_correction=apply_anisotropy_correction,
        q_factor=q_factor,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MODE: time_depth_anchor (absorbs geox_time_depth_anchor)
# ═══════════════════════════════════════════════════════════════════════════════


async def _mode_time_depth_anchor(
    well_id: str,
    checkshot_ref: str,
    drift_threshold_ms: float,
    method: str,
) -> dict[str, Any]:
    from geox_mcp.tools.seismic_well_tie import geox_time_depth_anchor

    return await geox_time_depth_anchor(
        well_id=well_id,
        checkshot_ref=checkshot_ref,
        drift_threshold_ms=drift_threshold_ms,
        method=method,  # type: ignore[arg-type]
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MODE: anomalous_contrast (absorbs geox_anomalous_contrast_detector)
# ═══════════════════════════════════════════════════════════════════════════════


async def _mode_anomalous_contrast(
    ai_profile: list[float],
    depth: list[float],
    formation_tops: dict[str, float],
    rc_threshold: float,
    geological_boundary_tolerance_m: float,
    vp: list[float] | None,
    rho: list[float] | None,
) -> dict[str, Any]:
    from geox_mcp.tools.anomalous_contrast import geox_anomalous_contrast_detector

    return await geox_anomalous_contrast_detector(
        ai_profile=ai_profile,
        depth=depth,
        formation_tops=formation_tops,
        rc_threshold=rc_threshold,
        geological_boundary_tolerance_m=geological_boundary_tolerance_m,
        vp=vp,
        rho=rho,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MODE: attribute — HONEST STUB (replaces geox_seismic_analyze_volume phantom)
# ═══════════════════════════════════════════════════════════════════════════════


async def _mode_attribute(volume_ref: str, attribute: str) -> dict[str, Any]:
    if not _artifact_exists(volume_ref):
        return get_standard_envelope(
            {
                "tool": TOOL_NAME,
                "mode": "attribute",
                "error_code": "NO_VALID_EVIDENCE",
                "message": f"Seismic volume '{volume_ref}' not found. Ingest SEG-Y via geox_data_ingest_bundle first.",
            },
            tool_class="compute",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[volume_ref],
        )

    artifact = {
        "tool": TOOL_NAME,
        "mode": "attribute",
        "volume_ref": volume_ref,
        "attribute": attribute,
        "status": "PENDING_ENGINE",
        "note": (
            "Volume evidence present. Real attribute computation (RMS/variance/sweetness) "
            "requires SEG-Y engine activation. This is an honest placeholder, not a fabricated result."
        ),
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
            "physics_version": "geox-seismic-v2026.05.22",
            "equations_used": [],
            "assumptions": ["Volume loaded but attribute computation not yet implemented"],
        },
    )
    envelope["confidence"] = {
        "level": "UNKNOWN",
        "sensitivity_to": ["seg_y_engine_availability", "attribute_algorithm_selection"],
    }
    return enrich_envelope_with_metabolic(envelope, TOOL_NAME)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC TOOL
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_seismic_compute(
    mode: Literal["synthetic", "well_tie", "time_depth_anchor", "anomalous_contrast", "attribute"] = "synthetic",
    # synthetic
    well_id: str | None = None,
    vp: list[float] | None = None,
    rho: list[float] | None = None,
    depth: list[float] | None = None,
    wavelet_type: Literal["ricker", "ormsby", "klauder"] = "ricker",
    wavelet_freq: float = 20.0,
    wavelet_params: dict[str, Any] | None = None,
    water_depth_m: float = 0.0,
    vp_water: float = 1500.0,
    dt_ms: float = 4.0,
    noise_db: float = -18.0,
    output_format: Literal["full", "compact"] = "full",
    # well_tie
    volume_ref: str | None = None,
    extraction_window_ms: float = 100.0,
    frequency_band: tuple[float, float] = (10.0, 50.0),
    apply_gardner_fallback: bool = False,
    apply_anisotropy_correction: bool = False,
    q_factor: float = 100.0,
    # time_depth_anchor
    checkshot_ref: str | None = None,
    drift_threshold_ms: float = 25.0,
    td_method: Literal["checkshot", "vsp", "regional_proxy"] = "checkshot",
    # anomalous_contrast
    ai_profile: list[float] | None = None,
    ac_depth: list[float] | None = None,
    formation_tops: dict[str, float] | None = None,
    rc_threshold: float = 0.05,
    geological_boundary_tolerance_m: float = 5.0,
    ac_vp: list[float] | None = None,
    ac_rho: list[float] | None = None,
    # attribute
    volume_ref_attr: str | None = None,
    attribute: str = "rms",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Unified seismic physics engine.

    Replaces: geox_forward_model_synthetic, geox_seismic_well_tie_compute,
    geox_time_depth_anchor, geox_anomalous_contrast_detector,
    geox_seismic_analyze_volume.

    Parameters
    ----------
    mode : str
        "synthetic" — forward model S = w * r + n.
        "well_tie" — seismic-to-well tie with cross-correlation.
        "time_depth_anchor" — checkshot/VSP anchoring.
        "anomalous_contrast" — detect AC mismatches.
        "attribute" — honest placeholder for future attribute engine.

    Returns
    -------
    Standard GEOX envelope with mode-specific derived artifacts.
    """
    # Hardening: validate free-text inputs at boundary.
    from geox_mcp.tools.kernel._validation import validate_tool_inputs
    _err = validate_tool_inputs(
        "geox_seismic_compute",
        well_id=well_id,
            vp=vp,
            rho=rho,
            depth=depth,
            wavelet_params=wavelet_params,
            volume_ref=volume_ref,
            checkshot_ref=checkshot_ref,
            ai_profile=ai_profile,
            ac_depth=ac_depth,
            formation_tops=formation_tops,
            ac_vp=ac_vp,
            ac_rho=ac_rho,
            volume_ref_attr=volume_ref_attr,
            attribute=attribute,
    )
    if ctx:
        ctx.report_progress(0, 100)

    if _err is not None:
        return _err

    if ctx:
        ctx.report_progress(20, 100)

    if mode == "synthetic":
        if ctx:
            ctx.report_progress(40, 100)
        result = await _mode_synthetic(
            well_id=well_id,
            vp=vp,
            rho=rho,
            depth=depth,
            wavelet_type=wavelet_type,
            wavelet_freq=wavelet_freq,
            wavelet_params=wavelet_params,
            water_depth_m=water_depth_m,
            vp_water=vp_water,
            dt_ms=dt_ms,
            noise_db=noise_db,
            output_format=output_format,
        )
        if ctx:
            ctx.report_progress(100, 100)
        return result

    if mode == "well_tie":
        if not well_id or not volume_ref:
            return get_standard_envelope(
                {"tool": TOOL_NAME, "mode": "well_tie", "error": "well_id and volume_ref required."},
                tool_class="compute",
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )
        if ctx:
            ctx.report_progress(40, 100)
        result = await _mode_well_tie(
            well_id=well_id,
            volume_ref=volume_ref,
            extraction_window_ms=extraction_window_ms,
            frequency_band=frequency_band,
            wavelet_type=wavelet_type,
            apply_gardner_fallback=apply_gardner_fallback,
            apply_anisotropy_correction=apply_anisotropy_correction,
            q_factor=q_factor,
        )
        if ctx:
            ctx.report_progress(100, 100)
        return result

    if mode == "time_depth_anchor":
        if not well_id or not checkshot_ref:
            return get_standard_envelope(
                {"tool": TOOL_NAME, "mode": "time_depth_anchor", "error": "well_id and checkshot_ref required."},
                tool_class="compute",
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )
        if ctx:
            ctx.report_progress(40, 100)
        result = await _mode_time_depth_anchor(
            well_id=well_id,
            checkshot_ref=checkshot_ref,
            drift_threshold_ms=drift_threshold_ms,
            method=td_method,
        )
        if ctx:
            ctx.report_progress(100, 100)
        return result

    if mode == "anomalous_contrast":
        if not ai_profile or not ac_depth or not formation_tops:
            return get_standard_envelope(
                {"tool": TOOL_NAME, "mode": "anomalous_contrast", "error": "ai_profile, ac_depth, and formation_tops required."},
                tool_class="compute",
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )
        if ctx:
            ctx.report_progress(40, 100)
        result = await _mode_anomalous_contrast(
            ai_profile=ai_profile,
            depth=ac_depth,
            formation_tops=formation_tops,
            rc_threshold=rc_threshold,
            geological_boundary_tolerance_m=geological_boundary_tolerance_m,
            vp=ac_vp,
            rho=ac_rho,
        )
        if ctx:
            ctx.report_progress(100, 100)
        return result

    if mode == "attribute":
        if ctx:
            ctx.report_progress(40, 100)
        result = await _mode_attribute(volume_ref=volume_ref_attr or volume_ref or "", attribute=attribute)
        if ctx:
            ctx.report_progress(100, 100)
        return result

    if ctx:
        ctx.report_progress(100, 100)
    return get_standard_envelope(
        {"tool": TOOL_NAME, "error": f"Unknown mode: {mode}"},
        tool_class="compute",
        execution_status=ExecutionStatus.ERROR,
        governance_status=GovernanceStatus.HOLD,
        claim_tag="HYPOTHESIS",
    )
