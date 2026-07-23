"""
geox_falsify — Popperian Falsification Engine for GEOX Claims
═════════════════════════════════════════════════════════════

Wraps the 7 Kill Matrix filters (K001-K007) + contradiction scan
into a single MCP tool for claim-level falsification.

GENESIS/015 architecture: physics must prove the claim is right.
A single KILL → claim rejected. REVIEW > 0 → treat as KILL until resolved.
All PASS → PROCEED to arifOS 888_JUDGE.

Kill Matrix:
  K001: Climate-Archetype Fit (Icehouse vs Greenhouse)
  K002: Slope Angle Geometry
  K003: Resolution-Thickness Test
  K004: Rim Crest Amplitude Test
  K005: False Positive Indicator Test
  K006: Reservoir Quality Pre-Check
  K007: Mud Volcano Probability Assessment

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger("geox.falsify")


# ── Kill Matrix Filter Implementations ──────────────────────────────────────


def _k001_climate_archetype(context: dict[str, Any]) -> dict[str, Any]:
    """K001: Climate-Archetype Fit.

    Icehouse: high relief, narrow shelves, sand-rich turbidites.
    Greenhouse: low relief, wide shelves, carbonate platforms.
    Mismatch = KILL.
    """
    climate = context.get("climate_archetype", "").lower()
    depositional = context.get("depositional_environment", "").lower()
    age_ma = context.get("age_ma")

    issues = []

    # Icehouse check
    if "icehouse" in climate:
        if "carbonate_platform" in depositional and age_ma and age_ma < 35:
            issues.append(
                f"K001: Icehouse climate ({climate}) with carbonate platform at {age_ma} Ma — "
                "carbonate platforms rare in icehouse. Check age/archetype."
            )
    # Greenhouse check
    elif "greenhouse" in climate:
        if "turbidite" in depositional and age_ma and age_ma > 50:
            issues.append(
                f"K001: Greenhouse climate ({climate}) with turbidites at {age_ma} Ma — "
                "turbidite systems less common in greenhouse. Not KILL but REVIEW."
            )

    if issues:
        return {"filter": "K001", "verdict": "REVIEW", "issues": issues}
    return {"filter": "K001", "verdict": "PASS", "issues": []}


def _k002_slope_angle(context: dict[str, Any]) -> dict[str, Any]:
    """K002: Slope Angle Geometry.

    Slope > 40° with no internal reflectors = volcanic intrusion or mass transport.
    Slope < 2° with mounding = possible reef buildup.
    """
    slope_deg = context.get("slope_angle_deg")
    has_internal_reflectors = context.get("has_internal_reflectors", True)
    issues = []

    if slope_deg is not None:
        if slope_deg > 40 and not has_internal_reflectors:
            issues.append(
                f"K002: Slope {slope_deg}° > 40° with no internal reflectors — "
                "likely volcanic intrusion or mass transport deposit. KILL."
            )
            return {"filter": "K002", "verdict": "KILL", "issues": issues}
        elif slope_deg > 30:
            issues.append(f"K002: Slope {slope_deg}° > 30° — steep. Review for false positive.")
            return {"filter": "K002", "verdict": "REVIEW", "issues": issues}

    return {"filter": "K002", "verdict": "PASS", "issues": []}


def _k003_resolution_thickness(context: dict[str, Any]) -> dict[str, Any]:
    """K003: Resolution-Thickness Test.

    Bed thickness < tuning thickness (λ/4) cannot be resolved seismically.
    Typical tuning thickness: 25-30 ms TWT for conventional seismic.
    """
    bed_thickness_m = context.get("bed_thickness_m")
    velocity_m_s = context.get("velocity_m_s", 2500)
    frequency_hz = context.get("frequency_hz", 30)
    issues = []

    if bed_thickness_m is not None and velocity_m_s and frequency_hz:
        wavelength_m = velocity_m_s / frequency_hz
        tuning_thickness_m = wavelength_m / 4
        if bed_thickness_m < tuning_thickness_m:
            issues.append(
                f"K003: Bed thickness {bed_thickness_m}m < tuning thickness {tuning_thickness_m:.1f}m "
                f"(λ/4 at {frequency_hz}Hz, {velocity_m_s}m/s) — below seismic resolution. REVIEW."
            )
            return {"filter": "K003", "verdict": "REVIEW", "issues": issues}

    return {"filter": "K003", "verdict": "PASS", "issues": []}


def _k004_rim_crest_amplitude(context: dict[str, Any]) -> dict[str, Any]:
    """K004: Rim Crest Amplitude Test.

    Carbonate buildups show rim-crest amplitude anomalies.
    No rim crest + no mounding = not a carbonate buildup.
    """
    has_rim_crest = context.get("has_rim_crest_amplitude", False)
    has_mounding = context.get("has_mounding", False)
    claim_type = context.get("claim_type", "").lower()
    issues = []

    if "carbonate" in claim_type or "reef" in claim_type or "buildup" in claim_type:
        if not has_rim_crest and not has_mounding:
            issues.append(
                "K004: Carbonate buildup claim but no rim crest amplitude and no mounding — likely not a carbonate buildup. KILL."
            )
            return {"filter": "K004", "verdict": "KILL", "issues": issues}

    return {"filter": "K004", "verdict": "PASS", "issues": []}


def _k005_false_positive(context: dict[str, Any]) -> dict[str, Any]:
    """K005: False Positive Indicator Test.

    Cross-checks against known false positive signatures:
    - Mud volcano: chaotic surface, no rim, no internal reflectors
    - Volcanic intrusion: steep slope, no reflectors
    - Basement high: high Vp, no onlap
    - Salt diapir: transparent core, rim syncline
    """
    issues = []
    indicators = []

    # Mud volcano check
    if (
        context.get("surface_morphology") == "chaotic"
        and not context.get("has_rim_structure", False)
        and not context.get("has_internal_reflectors", True)
    ):
        indicators.append("mud_volcano")
        issues.append("K005: Chaotic surface + no rim + no reflectors → mud volcano signature.")

    # Volcanic intrusion check
    slope = context.get("slope_angle_deg", 0) or 0
    if slope > 40 and not context.get("has_internal_reflectors", True):
        indicators.append("volcanic_intrusion")
        issues.append(f"K005: Slope {slope}° + no reflectors → volcanic intrusion signature.")

    # Basement high check
    vp = context.get("vp_km_s", 0) or 0
    if vp > 5.5 and not context.get("has_onlap", False):
        indicators.append("basement_high")
        issues.append(f"K005: Vp {vp} km/s > 5.5 + no onlap → basement high.")

    # Salt diapir check
    if context.get("core_transparency") == "transparent" and context.get("has_rim_syncline", False):
        indicators.append("salt_diapir")
        issues.append("K005: Transparent core + rim syncline → salt diapir signature.")

    if indicators:
        verdict = "KILL" if len(indicators) >= 2 else "REVIEW"
        return {"filter": "K005", "verdict": verdict, "issues": issues, "indicators": indicators}

    return {"filter": "K005", "verdict": "PASS", "issues": []}


def _k006_reservoir_quality(context: dict[str, Any]) -> dict[str, Any]:
    """K006: Reservoir Quality Pre-Check.

    Vp > 5.5 km/s = no reservoir quality (tight/crystalline).
    Porosity < 5% = sub-commercial unless fractured.
    """
    issues = []
    vp = context.get("vp_km_s")
    porosity = context.get("porosity_pct")

    if vp is not None and vp > 5.5:
        issues.append(f"K006: Vp {vp} km/s > 5.5 — tight/crystalline, no reservoir quality. KILL.")
        return {"filter": "K006", "verdict": "KILL", "issues": issues}

    if porosity is not None and porosity < 5:
        issues.append(f"K006: Porosity {porosity}% < 5% — sub-commercial unless fractured. REVIEW.")
        return {"filter": "K006", "verdict": "REVIEW", "issues": issues}

    return {"filter": "K006", "verdict": "PASS", "issues": []}


def _k007_mud_volcano(context: dict[str, Any]) -> dict[str, Any]:
    """K007: Mud Volcano Probability Assessment.

    Computes mud volcano probability from5 seismic indicators:
    1. Chaotic surface morphology
    2. No rim structure
    3. No internal reflectors
    4. Isolated mound shape
    5. Steep flanks (>25°)

    3+ indicators = HIGH probability → KILL.
    2 indicators = MODERATE → REVIEW.
    """
    score = 0
    indicators = []

    if context.get("surface_morphology") == "chaotic":
        score += 1
        indicators.append("chaotic_surface")
    if not context.get("has_rim_structure", False):
        score += 1
        indicators.append("no_rim")
    if not context.get("has_internal_reflectors", True):
        score += 1
        indicators.append("no_reflectors")
    if context.get("mound_shape") == "isolated":
        score += 1
        indicators.append("isolated_mound")
    slope = context.get("slope_angle_deg", 0) or 0
    if slope > 25:
        score += 1
        indicators.append(f"steep_flanks_{slope}deg")

    if score >= 3:
        return {
            "filter": "K007",
            "verdict": "KILL",
            "issues": [f"K007: Mud volcano probability HIGH ({score}/5 indicators): {', '.join(indicators)}"],
            "score": score,
            "indicators": indicators,
        }
    elif score == 2:
        return {
            "filter": "K007",
            "verdict": "REVIEW",
            "issues": [f"K007: Mud volcano probability MODERATE ({score}/5 indicators): {', '.join(indicators)}"],
            "score": score,
            "indicators": indicators,
        }

    return {"filter": "K007", "verdict": "PASS", "issues": [], "score": score}


# ── Kill Matrix Orchestrator ────────────────────────────────────────────────

KILL_MATRIX = {
    "K001": _k001_climate_archetype,
    "K002": _k002_slope_angle,
    "K003": _k003_resolution_thickness,
    "K004": _k004_rim_crest_amplitude,
    "K005": _k005_false_positive,
    "K006": _k006_reservoir_quality,
    "K007": _k007_mud_volcano,
}


def _run_kill_matrix(
    context: dict[str, Any],
    filters: list[str] | None = None,
) -> dict[str, Any]:
    """Run selected Kill Matrix filters against context data."""
    active_filters = filters or list(KILL_MATRIX.keys())
    results = []
    kills = 0
    reviews = 0

    for fid in active_filters:
        fn = KILL_MATRIX.get(fid)
        if fn is None:
            results.append({"filter": fid, "verdict": "ERROR", "issues": [f"Unknown filter: {fid}"]})
            continue

        result = fn(context)
        results.append(result)

        if result["verdict"] == "KILL":
            kills += 1
        elif result["verdict"] == "REVIEW":
            reviews += 1

    # Overall verdict
    if kills > 0:
        overall = "KILL"
    elif reviews > 0:
        overall = "REVIEW"
    else:
        overall = "PROCEED"

    return {
        "overall_verdict": overall,
        "kills": kills,
        "reviews": reviews,
        "passes": len(active_filters) - kills - reviews,
        "total_filters": len(active_filters),
        "filter_results": results,
    }


# ── Contradiction Scan (lightweight) ────────────────────────────────────────


def _contradiction_scan_light(
    claim_text: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Lightweight contradiction scan against evidence.

    Checks for basic physical contradictions:
    - Temperature vs depth (geothermal gradient)
    - Porosity vs depth (compaction)
    - Lithology vs depositional environment
    - Age vs structural setting
    """
    contradictions = []

    # Temperature-depth check
    temp = evidence.get("temperature_c")
    depth = evidence.get("depth_m")
    if temp and depth and depth > 0:
        gradient = temp / (depth / 1000)  # °C/km
        if gradient > 80:
            contradictions.append(
                {
                    "type": "geothermal_gradient",
                    "detail": f"Gradient {gradient:.1f}°C/km > 80 — unusually high. Check data.",
                    "severity": "review",
                }
            )
        elif gradient < 10:
            contradictions.append(
                {
                    "type": "geothermal_gradient",
                    "detail": f"Gradient {gradient:.1f}°C/km < 10 — unusually low. Check data.",
                    "severity": "review",
                }
            )

    # Porosity-depth compaction check
    porosity = evidence.get("porosity_pct")
    if porosity and depth:
        expected_phi = max(2, 40 - (depth / 1000) * 5)  # Simple Athy compaction
        if abs(porosity - expected_phi) > 15:
            contradictions.append(
                {
                    "type": "compaction",
                    "detail": f"Porosity {porosity}% vs expected ~{expected_phi:.0f}% at {depth}m — anisotropic or fractured.",
                    "severity": "review",
                }
            )

    # Lithology-environment check
    litho = evidence.get("lithology", "").lower()
    env = evidence.get("depositional_environment", "").lower()
    if "coal" in litho and "deep_marine" in env:
        contradictions.append(
            {
                "type": "facies",
                "detail": "Coal in deep marine environment — impossible without transport/reworking.",
                "severity": "critical",
            }
        )

    return {
        "contradictions": contradictions,
        "contradiction_count": len(contradictions),
        "critical_count": sum(1 for c in contradictions if c.get("severity") == "critical"),
    }


# ── Main Tool ───────────────────────────────────────────────────────────────


async def geox_falsify(
    claim_text: str = "Structural claim falsification",
    claim_type: str = "general",
    mode: Literal["full", "quick", "physics_only", "kill_matrix_only"] = "full",
    kill_matrix: list[str] | None = None,
    context: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    regime: str | None = None,
    proposal_coords: list[list[float]] | None = None,
    coords: list[list[float]] | None = None,
    max_disp: float | None = None,
    length: float | None = None,
    distances: list[float] | None = None,
    displacements: list[float] | None = None,
    epistemic_tag: str | None = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Popperian falsification engine — tests claims against physical filters.

    GENESIS/015 architecture: physics must prove the claim is right.
    Runs the 7 Kill Matrix filters (K001-K007) + structural physics gates (K-DIP, etc.) + contradiction scan.
    """
    ctx = dict(context or {})
    ev = dict(evidence or {})

    # Extract direct arguments into context if passed top-level
    if regime:
        ctx["regime"] = regime
    if proposal_coords or coords:
        ctx["proposal_coords"] = proposal_coords or coords
    if max_disp is not None:
        ctx["max_disp"] = max_disp
    if length is not None:
        ctx["length"] = length
    if distances:
        ctx["distances"] = distances
    if displacements:
        ctx["displacements"] = displacements
    if epistemic_tag:
        ctx["epistemic_tag"] = epistemic_tag

    result: dict[str, Any] = {
        "claim_text": claim_text,
        "claim_type": claim_type,
        "mode": mode,
        "session_id": session_id or "GEOX-SESSION-ACTIVE",
        "tool": "geox_falsify",
    }

    # Execute K-DIP NumPy gate if coordinate points and regime are supplied
    p_coords = ctx.get("proposal_coords") or ctx.get("coords")
    p_regime = ctx.get("regime") or ctx.get("structural_regime")
    if p_coords and p_regime:
        from geox_mcp.tools.structure_gates.k_dip import validate_k_dip
        dip_res = validate_k_dip(p_coords, p_regime)
        result["k_dip_gate"] = dip_res
        if dip_res.get("status") in ("REJECTED", "KILL"):
            result["overall_verdict"] = "KILL"
            result["status"] = "REJECTED"
            result["gate"] = "K-DIP"
            result["reason"] = dip_res.get("reason")
            result["888_HOLD"] = True

    # Execute K-SCALE gate if max_disp and length are supplied
    p_max_disp = ctx.get("max_disp") or ctx.get("max_displacement")
    p_length = ctx.get("length") or ctx.get("fault_length")
    if p_max_disp is not None and p_length is not None:
        from geox_mcp.tools.structure_gates.k_dl import validate_k_scale
        scale_res = validate_k_scale(p_max_disp, p_length)
        result["k_scale_gate"] = scale_res
        if scale_res.get("status") in ("REJECTED", "KILL") and result.get("overall_verdict") != "KILL":
            result["overall_verdict"] = "KILL"
            result["status"] = "REJECTED"
            result["gate"] = "K-SCALE"
            result["reason"] = scale_res.get("reason")
            result["888_HOLD"] = True

    # Execute K-TAPER gate if distances and displacements profile supplied
    p_dists = ctx.get("distances")
    p_disps = ctx.get("displacements")
    if p_dists and p_disps and p_max_disp and p_length:
        from geox_mcp.tools.structure_gates.k_throw import validate_k_taper
        taper_res = validate_k_taper(p_dists, p_disps, float(p_max_disp), float(p_length) / 2.0)
        result["k_taper_gate"] = taper_res
        if taper_res.get("status") in ("REJECTED", "KILL") and result.get("overall_verdict") != "KILL":
            result["overall_verdict"] = "KILL"
            result["status"] = "REJECTED"
            result["gate"] = "K-TAPER"
            result["reason"] = taper_res.get("reason")
            result["888_HOLD"] = True

    # Run Kill Matrix
    if mode in ("full", "quick", "kill_matrix_only"):
        km_result = _run_kill_matrix(ctx, kill_matrix)
        result["kill_matrix"] = km_result
        if "overall_verdict" not in result:
            result["overall_verdict"] = km_result["overall_verdict"]
        elif km_result["overall_verdict"] == "KILL":
            result["overall_verdict"] = "KILL"
    else:
        result["kill_matrix"] = {"overall_verdict": "SKIPPED", "reason": f"mode={mode}"}

    # Run contradiction scan
    if mode in ("full", "physics_only"):
        scan = _contradiction_scan_light(claim_text, ev)
        result["contradiction_scan"] = scan

        # Escalate if critical contradictions found
        if scan["critical_count"] > 0:
            result["overall_verdict"] = "KILL"
            result["888_HOLD"] = True
            result["hold_reason"] = f"{scan['critical_count']} critical contradictions detected"
    elif mode not in ("full", "physics_only"):
        result["contradiction_scan"] = {"status": "SKIPPED", "reason": f"mode={mode}"}

    # Final verdict summary
    verdict = result.get("overall_verdict", "UNKNOWN")
    result["summary"] = {
        "verdict": verdict,
        "proceed_to_judge": verdict == "PROCEED",
        "requires_resolution": verdict == "REVIEW",
        "falsified": verdict == "KILL",
    }

    logger.info(
        "geox_falsify: claim_type=%s mode=%s verdict=%s",
        claim_type,
        mode,
        verdict,
    )

    return result
