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
    """Hardened anomalous contrast detection — raw physics → governed envelope.

    Cross-Modal Fidelity Theorem (arifOS, 2026-06-05):
      Physical constraint reduces admissible solution space,
      which improves inter-modal fidelity (AI) and inter-survey consistency (geoscience).
      The governed envelope IS the transfer-stable encoding.
    """
    import numpy as np

    from geox_mcp.tools.anomalous_contrast import geox_anomalous_contrast_detector

    raw = await geox_anomalous_contrast_detector(
        ai_profile=ai_profile,
        depth=depth,
        formation_tops=formation_tops,
        rc_threshold=rc_threshold,
        geological_boundary_tolerance_m=geological_boundary_tolerance_m,
        vp=vp,
        rho=rho,
    )

    # ── GOVERNANCE WRAPPER ───────────────────────────────────────────────
    # The raw physics result carries zero governance. We harden it here.
    # This is the bridge: physical constraint → reduced solution space →
    # transfer-stable encoding (Kolmogorov compressibility).

    n_anomalies: int = len(raw.get("anomalies", []))
    total_mistie: float = raw.get("volumetric_impact", {}).get("total_abs_mistie_m", 0.0)

    # ── AC_Risk: computed by L2 governance, not L1 physics ─────────────
    # ToAC canon: AC_Risk = U_phys × D_transform × B_cog
    # U_phys derived from anomaly count + mistie magnitude (both independently contribute)
    # D_transform = 2.0 (seismic → interpreted depth, 2+ transforms per ToAC canon)
    # B_cog = 0.30 (geological formation tops: well-calibrated, but seismic is indirect measurement)
    # Note: the old L1 override (governance_escalation from Phase 1) has been removed.
    # AC_Risk is now the sole basis for constitutional verdicts.
    U_phys = min(1.0, 0.05 + (n_anomalies * 0.20) + (total_mistie / 80.0))
    D_transform = 2.0
    B_cog = 0.30
    AC_Risk = min(1.0, U_phys * D_transform * B_cog)

    if AC_Risk >= 0.60:
        ac_risk_verdict = "VOID"
    elif AC_Risk >= 0.35:
        ac_risk_verdict = "HOLD"
    elif AC_Risk >= 0.15:
        ac_risk_verdict = "QUALIFY"
    else:
        ac_risk_verdict = "SEAL"

    # ── ClaimTag classification ──────────────────────────────────────────
    if n_anomalies == 0:
        claim_tag = "CLAIM"
        gov_status = GovernanceStatus.SEAL
        artifact_status = ArtifactStatus.VERIFIED
        claim_state = "QC_VERIFIED"
    elif n_anomalies <= 2 and total_mistie < 20.0:
        claim_tag = "PLAUSIBLE"
        gov_status = GovernanceStatus.QUALIFY
        artifact_status = ArtifactStatus.IN_REVIEW
        claim_state = "INTERPRETED"
    else:
        claim_tag = "HYPOTHESIS"
        gov_status = GovernanceStatus.HOLD
        artifact_status = ArtifactStatus.IN_REVIEW
        claim_state = "INTERPRETED"

    # ── L1 Advisory Metadata (not verdicts) ───────────────────────────
    # GEOX emits physical signals. arifOS computes constitutional verdicts.
    # This separation preserves APEX stack integrity (L1 ≠ L2).
    dim_spot_flag = False
    worst_l1_advisory = None  # raw physics signal, not a governance verdict
    _l1_severity_rank = {"CRITICAL": 4, "ELEVATED": 3, "WARNING": 2, "MODERATE": 1, "NOMINAL": 0}

    for anomaly in raw.get("anomalies", []):
        ar = anomaly.get("attention_residual", {})
        hr = ar.get("softmax_hallucination_risk", {})
        # Dead zone: near-background with high hallucination risk — L1 signal, not verdict
        if hr.get("risk_level") in ("CRITICAL", "ELEVATED") and anomaly.get("rc_ratio", 1.0) < 1.05:
            dim_spot_flag = True
        # L1 advisory only — do not treat as constitutional verdict
        esc = ar.get("governance_escalation")
        if esc:
            sev = _l1_severity_rank.get(esc.get("advisory_status", "NOMINAL"), 0)
            worst_sev = _l1_severity_rank.get(worst_l1_advisory.get("advisory_status", "NOMINAL") if worst_l1_advisory else "NOMINAL", 0)
            if sev > worst_sev:
                worst_l1_advisory = esc

    # ── arifOS computes verdict from AC_Risk (not from L1 advisory override) ──
    # L1 advisory signals are surfaced as metadata for arifOS to weigh.
    # The constitutional verdict is determined by AC_Risk score alone.
    if ac_risk_verdict == "VOID":
        gov_status = GovernanceStatus.VOID
        claim_tag = "HYPOTHESIS"
        artifact_status = ArtifactStatus.REJECTED
        claim_state = "VOID"
    elif ac_risk_verdict == "HOLD":
        gov_status = GovernanceStatus.HOLD
        claim_tag = "HYPOTHESIS"
        artifact_status = ArtifactStatus.IN_REVIEW
        claim_state = "888_HOLD"
    elif ac_risk_verdict == "QUALIFY":
        gov_status = GovernanceStatus.QUALIFY
        claim_tag = "PLAUSIBLE"
        artifact_status = ArtifactStatus.IN_REVIEW
        claim_state = "INTERPRETED"
    else:
        # SEAL: nothing triggered — n_anomalies==0 and clean profile
        pass  # keep defaults set by n_anomalies branch above

    # ── PhysicsGuard: AI physical range check ─────────────────────────────
    ai_arr = np.array(ai_profile, dtype=float)
    ai_min, ai_max = float(np.min(ai_arr)), float(np.max(ai_arr))
    # Sedimentary rock acoustic impedance: ~3000–30000 kg/m²·s
    # (vp 1500-6000 m/s × rho 2000-5000 kg/m³ for consolidated section)
    ai_phys_lower, ai_phys_upper = 2000.0, 35000.0
    physics_ok = bool(ai_phys_lower <= ai_min <= ai_phys_upper and ai_phys_lower <= ai_max <= ai_phys_upper)

    # ── Envelope construction ────────────────────────────────────────────
    artifact = {**raw, "tool": TOOL_NAME, "mode": "anomalous_contrast"}
    envelope = get_standard_envelope(
        artifact,
        tool_class="compute",
        execution_status=ExecutionStatus.SUCCESS,
        governance_status=gov_status,
        artifact_status=artifact_status,
        claim_tag=claim_tag,
        claim_state=claim_state,
        perception_class="ANOMALY" if n_anomalies > 0 else "DISPLAY",
        evidence_refs=list(formation_tops.keys()),
        dim_spot_flag=dim_spot_flag,
        physics_guard={
            "guard_passed": physics_ok,
            "physics_version": "geox-ac-v2026.06.05",
            "equations_used": raw.get("physics", {}).get("equations_used", []),
            "assumptions": raw.get("physics", {}).get("assumptions", []),
            "limitations": raw.get("physics", {}).get("limitations", []),
            "ai_physical_range_check": {
                "ai_min_kg_m2s": round(ai_min, 1),
                "ai_max_kg_m2s": round(ai_max, 1),
                "physical_bounds_kg_m2s": [ai_phys_lower, ai_phys_upper],
                "passed": physics_ok,
            },
        },
    )

    # ── Anomalous Contrast risk metadata ─────────────────────────────────
    # Maps to: AVO Fluid Factor (Smith & Gidlow, 1987) — deviation from background.
    # The "background" here is the geological formation tops.
    # Anomalies ARE the fluid factor: seismic does not match geological.
    #
    # Eureka GeoX Theory (2026-06-05): This is the AVO-attention isomorphism.
    # ΔF = B_obs − m·A_obs  ↔  δ_i = e_i − ē  ↔  ΔV = verdict − floor_expected
    # All three are instances of: signal = amplify(normalize(obs − background))
    envelope["anomalous_contrast"] = {
        "anomalies_detected": n_anomalies,
        "total_abs_mistie_m": round(total_mistie, 2),
        "contradiction_type": "INTERPRETATION_OBSERVATION_MISMATCH" if n_anomalies > 0 else None,
        "ac_severity": "HIGH" if n_anomalies > 2 else ("MEDIUM" if n_anomalies > 0 else "NONE"),
        "toac_version": "v2026.06.05",
        # AC_Risk computed by L2 governance (arifOS reads this, not L1 advisory)
        "ac_risk": {
            "score": round(AC_Risk, 3),
            "U_phys": round(U_phys, 3),
            "D_transform": D_transform,
            "B_cog": B_cog,
            "verdict": ac_risk_verdict,
        },
        # L1 advisory metadata: raw physics signals for arifOS to weigh
        # NOT a constitutional verdict — separated per APEX L1/L2 stack
        "l1_advisory": {
            "worst_governance_escalation": worst_l1_advisory,
            "dim_spot_flag": dim_spot_flag,
            "toac_note": (
                "L1 advisory only — arifOS computes constitutional verdict from AC_Risk above. "
                "δ_i = e_i − ē surfaces here; ΔV = verdict − floor_expected is arifOS jurisdiction."
            ),
        },
    }

    # ── AVO-Attention Equivalence metadata (Eureka GeoX Theory v2026.06.05) ────
    # Propagate the raw attention_equivalence from the detector output, augmented
    # with governance-level context.
    raw_ae = raw.get("attention_equivalence", {})
    if raw_ae:
        # Augment with per-anomaly AVO class summary
        anomaly_classes = [a.get("avo_class", "?") for a in raw.get("anomalies", [])]
        attention_residuals = [
            a.get("attention_residual", {}).get("softmax_amplification", {}).get("dominance_ratio", 1.0)
            for a in raw.get("anomalies", [])
        ]
        envelope["anomalous_contrast"]["attention_equivalence"] = {
            "theorem": raw_ae.get("theorem", "Eureka GeoX Theory of Anomalous Contrast"),
            "statement": raw_ae.get("statement", ""),
            "avo_class_summary": {
                "classes_detected": sorted(set(anomaly_classes)),
                "class_iii_iv_warning": (
                    "Class III/IV cannot be distinguished from normal-incidence RC alone. "
                    "Pre-stack angle gathers required per Shuey (1985). Class IV is the "
                    "known false-negative hazard in AVO interpretation (Castagna, 1998). "
                    "Attention equivalent: the dim-spot problem — δ_i exists but may be "
                    "masked by softmax normalization, producing α_i ≈ 1/N despite real anomaly."
                )
                if "III/IV" in anomaly_classes
                else None,
            },
            "attention_dominance": {
                "max_dominance_ratio": max(attention_residuals) if attention_residuals else 0.0,
                "mean_dominance_ratio": (
                    round(sum(attention_residuals) / len(attention_residuals), 2) if attention_residuals else 0.0
                ),
                "interpretation": (
                    f"Anomalies dominate attention by {max(attention_residuals):.1f}× the uniform baseline. "
                    f"In transformer terms: these 'keys' collectively hijack the softmax distribution."
                )
                if attention_residuals and max(attention_residuals) > 1.5
                else "No single anomaly dominates attention — distributed across multiple keys.",
            },
            "shared_primitive": raw_ae.get("shared_primitive", []),
            "failure_modes": raw_ae.get("failure_modes", []),
            "independent_convergence": raw_ae.get("independent_convergence", ""),
            "cross_modal_fidelity": {
                "principle": "Physical constraint reduces admissible solution space",
                "envelope_field": "cross_modal_stability",
                "current_value": envelope.get("cross_modal_stability", 0.0),
                "interpretation": (
                    f"cross_modal_stability = {envelope.get('cross_modal_stability', 0.0):.2f}. "
                    f"This measures how well the physical evidence survives transfer "
                    f"across modalities (seismic → text → JSON → attention). "
                    f"Higher values mean the anomaly signature is robust to format changes."
                ),
            },
            "ratified": raw_ae.get("ratified", "2026-06-05"),
            "document": raw_ae.get("document", "docs/AVO_ATTENTION_FORMAL_EQUIVALENCE.md"),
        }

    return enrich_envelope_with_metabolic(envelope, TOOL_NAME)


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
        "anomalous_contrast" — detect AC mismatches with AVO class I-IV,
            attention residual (δ_i = e_i − ē), softmax hallucination risk,
            approximation tier, and boundary condition flags.
            Governed output with ClaimTag + PhysicsGuard + 888_HOLD gating.
            Per the Eureka GeoX Theory: AVO fluid factor ΔF ≡ attention
            residual δ_i ≡ constitutional governance deviation ΔV.
        "attribute" — seismic attribute computation via dynamic registry.

    Returns
    -------
    Standard GEOX envelope with mode-specific derived artifacts.
    For anomalous_contrast: envelope carries attention_equivalence metadata
    (AVO chain, attention chain, shared primitives, failure modes, trilogy ref).
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
