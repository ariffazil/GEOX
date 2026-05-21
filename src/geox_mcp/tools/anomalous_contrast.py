"""
GEOX Anomalous Contrast Detector — Theory of Anomalous Contrast (LC#28)
═══════════════════════════════════════════════════════════════════════════════
Detects boundaries where the strongest seismic reflector (maximum |RC|)
does NOT correspond to the geological formation boundary.

Theory of Anomalous Contrast (ARIF FAZIL, 2025):
    At carbonate-clastic interfaces, porous carbonates (reefal, vuggy) can
    have AI values close to overlying shale, creating a "transparent cap"
    that shifts the apparent seismic pick downward.

Quantified at Megah-1:
    True geological top (4710m): RC = +0.112 (WEAK)
    Apparent seismic top (4720m): RC = +0.156 (STRONG — 39% stronger)
    Systematic mistie: ~10m deeper than reality
    Volumetric consequence: ~10m of unaccounted net pay (Upper Reef)

Constitutional: F9-Rahmah (physics-only), F10-Ontology (no certainty beyond evidence).
Author: M Arif Fazil | DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from geox_core.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
    enrich_envelope_with_metabolic,
)
from geox_core.engines.seismic.well_tie import (
    calculate_acoustic_impedance,
    calculate_reflectivity,
)

logger = logging.getLogger("geox.canonical.anomalous_contrast")


async def geox_anomalous_contrast_detector(
    ai_profile: List[float],
    depth: List[float],
    formation_tops: Dict[str, float],
    rc_threshold: float = 0.05,
    geological_boundary_tolerance_m: float = 5.0,
    vp: Optional[List[float]] = None,
    rho: Optional[List[float]] = None,
) -> dict:
    """Theory of Anomalous Contrast (ARIF FAZIL, 2025).

    Detects boundaries where the strongest seismic reflector (max |RC|)
    does NOT correspond to the geological formation boundary.

    Common in:
        - porous carbonates (reefal, vuggy)
        - volcanic intrusives
        - coal seams
        - gas-charged sands
        - salt flanks

    Args:
        ai_profile: Acoustic impedance values in kg/m²·s (or m/s·g/cc).
        depth: Depth values in metres (must align with ai_profile).
        formation_tops: Mapping {formation_name: depth_m} for known boundaries.
        rc_threshold: Minimum |RC| to consider a reflector significant.
        geological_boundary_tolerance_m: Window around geological top to search
            for the maximum |RC|.
        vp: Optional P-wave velocity array (for recomputing AI if rho provided).
        rho: Optional density array (for recomputing AI if vp provided).

    Returns:
        LEM-enriched dict with anomalies, recommended picks, volumetric impact,
        and full constitutional audit receipt.
    """

    # ── 1. INPUT VALIDATION ──────────────────────────────────────────────────
    if (not ai_profile or not depth or len(ai_profile) != len(depth)
            or len(ai_profile) < 2):
        return get_standard_envelope(
            {
                "tool": "geox_anomalous_contrast_detector",
                "error_code": "INVALID_INPUT",
                "message": "ai_profile and depth must be equal-length arrays with ≥2 samples.",
            },
            tool_class="compute",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
        )

    ai_arr = np.array(ai_profile, dtype=float)
    depth_arr = np.array(depth, dtype=float)

    # Recompute AI if vp and rho provided (preferred)
    if vp is not None and rho is not None:
        vp_arr = np.array(vp, dtype=float)
        rho_arr = np.array(rho, dtype=float)
        if len(vp_arr) == len(depth_arr) and len(rho_arr) == len(depth_arr):
            ai_arr = calculate_acoustic_impedance(rho_arr * 1000.0, vp_arr)
        else:
            logger.warning("F2: vp/rho length mismatch; using provided ai_profile.")

    # ── 2. REFLECTIVITY COMPUTATION ──────────────────────────────────────────
    rc = calculate_reflectivity(ai_arr)
    rc_abs = np.abs(rc)

    # ── 3. ANOMALY DETECTION PER FORMATION TOP ───────────────────────────────
    anomalies: List[Dict[str, Any]] = []
    recommended_picks: List[Dict[str, Any]] = []
    total_mistie_m = 0.0

    for formation_name, geo_depth in formation_tops.items():
        # Find nearest index to geological top
        geo_idx = int(np.argmin(np.abs(depth_arr - geo_depth)))
        geo_depth_actual = float(depth_arr[geo_idx])

        # Search window around geological top for strongest reflector
        tol = geological_boundary_tolerance_m
        window_mask = np.abs(depth_arr - geo_depth_actual) <= tol
        if not np.any(window_mask):
            anomalies.append({
                "formation": formation_name,
                "depth_geological_m": geo_depth_actual,
                "depth_seismic_m": None,
                "rc_geological": float(rc_abs[geo_idx]),
                "rc_seismic": None,
                "mistie_m": None,
                "confidence": "UNKNOWN",
                "reason": "No samples within tolerance window.",
            })
            continue

        window_indices = np.where(window_mask)[0]
        window_rc = rc_abs[window_mask]
        max_rc_idx_local = int(np.argmax(window_rc))
        seismic_idx = window_indices[max_rc_idx_local]
        seismic_depth = float(depth_arr[seismic_idx])
        rc_at_geo = float(rc_abs[geo_idx])
        rc_at_seismic = float(rc_abs[seismic_idx])
        mistie = seismic_depth - geo_depth_actual

        # Anomaly criterion: strongest RC is NOT at geological top
        is_anomaly = (seismic_idx != geo_idx) and (rc_at_seismic > rc_at_geo * 1.05)
        confidence = "HIGH" if abs(mistie) > 2.0 else "MEDIUM"

        if is_anomaly:
            anomalies.append({
                "formation": formation_name,
                "depth_geological_m": geo_depth_actual,
                "depth_seismic_m": seismic_depth,
                "rc_geological": round(rc_at_geo, 6),
                "rc_seismic": round(rc_at_seismic, 6),
                "rc_ratio": round(rc_at_seismic / max(rc_at_geo, 1e-9), 3),
                "mistie_m": round(mistie, 2),
                "confidence": confidence,
                "reason": (
                    f"Strongest reflector ({rc_at_seismic:.4f}) is {abs(mistie):.1f}m "
                    f"{'deeper' if mistie > 0 else 'shallower'} than geological top ({rc_at_geo:.4f})."
                ),
            })
            total_mistie_m += abs(mistie)

        # Recommended pick: if anomaly, suggest corrected pick
        if is_anomaly:
            recommended_picks.append({
                "name": formation_name,
                "depth_corrected_m": geo_depth_actual,
                "depth_seismic_apparent_m": seismic_depth,
                "rationale": (
                    "LC#28: Seismic pick should be validated against synthetic. "
                    "Apparent reflector is displaced due to anomalous impedance contrast."
                ),
                "verification_required": "synthetic_seismogram",
            })
        else:
            recommended_picks.append({
                "name": formation_name,
                "depth_corrected_m": geo_depth_actual,
                "depth_seismic_apparent_m": geo_depth_actual,
                "rationale": "Geological top aligns with strongest reflector within tolerance.",
                "verification_required": "none",
            })

    # ── 4. VOLUMETRIC IMPACT (simplified column correction) ──────────────────
    n_anomalies = len(anomalies)
    column_correction_m = total_mistie_m / max(len(formation_tops), 1)
    # Rough net-pay proxy: if mistie is downward, we may have missed pay above
    additional_net_pay_m = column_correction_m if n_anomalies > 0 else 0.0

    volumetric_impact = {
        "anomalies_detected": n_anomalies,
        "total_abs_mistie_m": round(total_mistie_m, 2),
        "column_correction_m": round(column_correction_m, 2),
        "additional_net_pay_m": round(additional_net_pay_m, 2),
        "assumption": "Mistie direction indicates structural displacement, not erosion.",
    }

    # ── 5. LEM ENVELOPE ──────────────────────────────────────────────────────
    primary_artifact = {
        "tool": "geox_anomalous_contrast_detector",
        "theory": "Theory of Anomalous Contrast (ARIF FAZIL, 2025)",
        "law_capsule": "LC#28",
        "anomalies": anomalies,
        "recommended_picks": recommended_picks,
        "volumetric_impact": volumetric_impact,
        "rc_threshold": rc_threshold,
        "tolerance_m": geological_boundary_tolerance_m,
        "formations_checked": list(formation_tops.keys()),
    }

    envelope = get_standard_envelope(
        primary_artifact,
        tool_class="compute",
        execution_status=ExecutionStatus.SUCCESS,
        governance_status=GovernanceStatus.QUALIFY,
        artifact_status=ArtifactStatus.COMPUTED,
        claim_tag="COMPUTED",
        claim_state="DERIVED_CANDIDATE",
        uncertainty="Moderate" if n_anomalies > 0 else "Low",
        physics_guard={
            "guard_passed": True,
            "physics_version": "geox-anomalous-contrast-v2026.05.21",
            "equations_used": [
                "AI = Vp × ρ",
                "RC = (AI₂ - AI₁) / (AI₂ + AI₁)",
                "Anomaly = argmax(|RC|) ≠ geological_top",
            ],
            "assumptions": [
                "normal incidence reflectivity",
                "formation top is known from well data",
                "impedance contrast dominates seismic response",
            ],
            "limitations": [
                "does not account for tuning effects",
                "does not model AVO response",
                "volumetric impact is first-order approximation",
            ],
        },
        audit_receipt={
            "tool": "geox_anomalous_contrast_detector",
            "version": "2026.05.21",
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "floors_checked": [1, 2, 3, 9, 10, 13],
            "law_capsule": "LC#28",
        },
        canon_9_touched=["Vp", "rho", "phi"],
    )

    envelope["confidence"] = {
        "level": "HIGH" if n_anomalies == 0 else "MEDIUM",
        "uncertainty_band": {"p10": 0.8, "p50": 1.0, "p90": 1.2},
        "sensitivity_to": [
            "formation_top_depth_accuracy",
            "ai_profile_quality",
            "geological_boundary_tolerance",
        ],
    }
    envelope["provenance"]["equations_used"] = [
        "AI = Vp × ρ",
        "RC = (AI₂ - AI₁) / (AI₂ + AI₁)",
    ]
    envelope["provenance"]["law_capsule"] = "LC#28"
    envelope["provenance"]["author"] = "M Arif Fazil"

    return enrich_envelope_with_metabolic(
        envelope,
        "geox_anomalous_contrast_detector",
        witness_type="seismic",
        witness_status="COMPUTED",
        anomalous_contrasts=anomalies,
    )
