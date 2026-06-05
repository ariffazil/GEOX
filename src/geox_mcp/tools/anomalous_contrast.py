"""
GEOX Anomalous Contrast Detector — Theory of Anomalous Contrast

Detects boundaries where the strongest seismic reflector (maximum |RC|)
does NOT correspond to the geological formation boundary.

Input: Acoustic Impedance profile + known formation tops.
Output: Plain anomaly list with mismatch distance and RC strength.

No interpretation. No narrative. Physics only.
"""

from __future__ import annotations

import logging
from typing import Any

from geox_core.physics import (
    impedance_array as calculate_acoustic_impedance,
)
from geox_core.physics import (
    reflectivity_array as calculate_reflectivity,
)

logger = logging.getLogger("geox.canonical.anomalous_contrast")


async def geox_anomalous_contrast_detector(
    ai_profile: list[float],
    depth: list[float],
    formation_tops: dict[str, float],
    rc_threshold: float = 0.05,
    geological_boundary_tolerance_m: float = 5.0,
    vp: list[float] | None = None,
    rho: list[float] | None = None,
) -> dict[str, Any]:
    """
    Detect physical/visual anomalies between seismic response and known geological boundaries.

    Args:
        ai_profile: Acoustic impedance values in kg/m²·s.
        depth: Depth values in metres (must align with ai_profile).
        formation_tops: Mapping {formation_name: depth_m} for known boundaries.
        rc_threshold: Minimum |RC| to consider a reflector significant.
        geological_boundary_tolerance_m: Window around geological top to search for max |RC|.
        vp: Optional P-wave velocity array (recomputes AI if rho also provided).
        rho: Optional density array (recomputes AI if vp also provided).

    Returns:
        Plain dict with anomalies, recommended picks, and volumetric impact.
    """

    import numpy as np

    # ── 1. INPUT VALIDATION ──────────────────────────────────────────────────
    if not ai_profile or not depth or len(ai_profile) != len(depth) or len(ai_profile) < 2:
        return {
            "error": "ai_profile and depth must be equal-length arrays with ≥2 samples.",
            "anomalies": [],
            "recommended_picks": [],
            "volumetric_impact": {},
        }

    ai_arr = np.array(ai_profile, dtype=float)
    depth_arr = np.array(depth, dtype=float)

    if vp is not None and rho is not None:
        vp_arr = np.array(vp, dtype=float)
        rho_arr = np.array(rho, dtype=float)
        if len(vp_arr) == len(depth_arr) and len(rho_arr) == len(depth_arr):
            ai_arr = calculate_acoustic_impedance(rho_arr * 1000.0, vp_arr)
        else:
            logger.warning("F2: vp/rho length mismatch; using provided ai_profile.")

    # ── 2. REFLECTIVITY ──────────────────────────────────────────────────────
    rc = calculate_reflectivity(ai_arr)
    rc_abs = np.abs(rc)

    # ── 3. ANOMALY DETECTION PER FORMATION TOP ───────────────────────────────
    anomalies: list[dict[str, Any]] = []
    recommended_picks: list[dict[str, Any]] = []
    total_mistie_m = 0.0

    for formation_name, geo_depth in formation_tops.items():
        geo_idx = int(np.argmin(np.abs(depth_arr - geo_depth)))
        geo_depth_actual = float(depth_arr[geo_idx])

        tol = geological_boundary_tolerance_m
        window_mask = np.abs(depth_arr - geo_depth_actual) <= tol
        if not np.any(window_mask):
            anomalies.append(
                {
                    "formation": formation_name,
                    "depth_geological_m": geo_depth_actual,
                    "depth_seismic_m": None,
                    "rc_geological": float(rc_abs[geo_idx]),
                    "rc_seismic": None,
                    "mistie_m": None,
                    "reason": "No samples within tolerance window.",
                }
            )
            recommended_picks.append(
                {
                    "formation": formation_name,
                    "depth_geological_m": geo_depth_actual,
                    "depth_seismic_apparent_m": None,
                    "reason": "No samples within tolerance window.",
                }
            )
            continue

        window_indices = np.where(window_mask)[0]
        window_rc = rc_abs[window_mask]
        max_rc_idx_local = int(np.argmax(window_rc))
        seismic_idx = window_indices[max_rc_idx_local]
        seismic_depth = float(depth_arr[seismic_idx])
        rc_at_geo = float(rc_abs[geo_idx])
        rc_at_seismic = float(rc_abs[seismic_idx])
        mistie = seismic_depth - geo_depth_actual

        is_anomaly = (seismic_idx != geo_idx) and (rc_at_seismic > rc_at_geo * 1.05)

        if is_anomaly:
            # ── Contradiction classification ────────────────────────────
            # Theory of Anomalous Contrast (ToAC): each anomaly is an
            # INTERPRETATION_OBSERVATION_MISMATCH per contradiction ontology.
            # Seismic reflector = INTERPRETATION (derived from impedance contrast)
            # Geological top = OBSERVATION (measured from well log / core)
            # The contradiction is the ANOMALOUS CONTRAST — the fluid factor
            # of governance: deviation from the calibrated background.
            abs_mistie = abs(mistie)
            if abs_mistie > 20.0:
                contradiction_severity = "HIGH"
                resolution = "DEMOTE — seismic pick displaced >20 m; validate with checkshot/VSP"
            elif abs_mistie > 5.0:
                contradiction_severity = "MEDIUM"
                resolution = "QUALIFY — seismic pick displaced {:.0f} m; cross-check with well tie".format(abs_mistie)
            else:
                contradiction_severity = "LOW"
                resolution = "NOTE — minor mistie {:.0f} m; within picking tolerance but flagged".format(abs_mistie)

            anomalies.append(
                {
                    "formation": formation_name,
                    "depth_geological_m": round(geo_depth_actual, 2),
                    "depth_seismic_m": round(seismic_depth, 2),
                    "rc_geological": round(rc_at_geo, 6),
                    "rc_seismic": round(rc_at_seismic, 6),
                    "rc_ratio": round(rc_at_seismic / max(rc_at_geo, 1e-9), 3),
                    "mistie_m": round(mistie, 2),
                    "reason": (
                        f"Strongest reflector ({rc_at_seismic:.4f}) is {abs(mistie):.1f}m "
                        f"{'deeper' if mistie > 0 else 'shallower'} than geological top ({rc_at_geo:.4f})."
                    ),
                    # ── Contradiction ontology classification ────────────
                    "contradiction_type": "INTERPRETATION_OBSERVATION_MISMATCH",
                    "contradiction_severity": contradiction_severity,
                    "resolution": resolution,
                    "toac_version": "v2026.06.05",
                }
            )
            total_mistie_m += abs(mistie)
            recommended_picks.append(
                {
                    "formation": formation_name,
                    "depth_geological_m": round(geo_depth_actual, 2),
                    "depth_seismic_apparent_m": round(seismic_depth, 2),
                    "reason": "Seismic pick displaced from geological top.",
                }
            )
        else:
            recommended_picks.append(
                {
                    "formation": formation_name,
                    "depth_geological_m": round(geo_depth_actual, 2),
                    "depth_seismic_apparent_m": round(geo_depth_actual, 2),
                    "reason": "Geological top aligns with strongest reflector within tolerance.",
                }
            )

    # ── 4. VOLUMETRIC IMPACT ─────────────────────────────────────────────────
    n_anomalies = len(anomalies)
    column_correction_m = total_mistie_m / max(len(formation_tops), 1)
    additional_net_pay_m = column_correction_m if n_anomalies > 0 else 0.0

    return {
        "anomalies": anomalies,
        "recommended_picks": recommended_picks,
        "volumetric_impact": {
            "anomalies_detected": n_anomalies,
            "total_abs_mistie_m": round(total_mistie_m, 2),
            "column_correction_m": round(column_correction_m, 2),
            "additional_net_pay_m": round(additional_net_pay_m, 2),
        },
        "rc_threshold": rc_threshold,
        "tolerance_m": geological_boundary_tolerance_m,
        "formations_checked": list(formation_tops.keys()),
        "physics": {
            "equations_used": [
                "AI = Vp × ρ",
                "RC = (AI₂ - AI₁) / (AI₂ + AI₁)",
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
    }
