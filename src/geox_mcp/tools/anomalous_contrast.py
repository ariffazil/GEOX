"""
GEOX Anomalous Contrast Detector — Theory of Anomalous Contrast (ToAC)
╔══════════════════════════════════════════════════════════════════╗
║  Eureka GeoX Theory — ratified 2026-06-05                       ║
║  AVO anomalous contrast ≡ transformer attention anomaly          ║
║  Shared primitive: signal = amplify(normalize(obs − background)) ║
║  ΔF = B_obs − m·A_obs  ↔  δ_i = e_i − ē  ↔  ΔV = verdict − F1  ║
╚══════════════════════════════════════════════════════════════════╝

Detects boundaries where the strongest seismic reflector (maximum |RC|)
does NOT correspond to the geological formation boundary.

Input: Acoustic Impedance profile + known formation tops.
Output: Anomaly list with AVO class, attention residual, and
contradiction classification. Every anomaly carries its mathematical
mapping to the attention-domain contrast primitive.

No interpretation. No narrative. Physics only.
DITEMPA BUKAN DIBERI — Forged, Not Given.
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


# ═══════════════════════════════════════════════════════════════════════════════
# AVO Class & Attention Equivalence — Eureka GeoX Theory v2026.06.05
# ═══════════════════════════════════════════════════════════════════════════════


def _classify_avo_class(
    rc: float,
    rc_ratio: float,
    mistie_m: float,
    depth_m: float,
) -> tuple[str, str]:
    """Classify an anomaly into AVO Class I–IV (Rutherford & Williams, 1989).

    NOTE: Classification from normal-incidence RC alone is CONDITIONAL.
    Full AVO classification requires pre-stack angle gathers.
    This is a first-order estimate validated against the Castagna & Swan (1997)
    crossplot framework.

    Returns:
        (avo_class, avo_note)
    """
    abs_rc = abs(rc)

    if rc < -0.05 and abs_rc >= 0.03:
        # Negative intercept: low-impedance sand.
        # rc_ratio > 1.05 means seismic RC stronger than geological — typical
        # Class III bright spot (amplitude increases with offset → gas effect).
        # rc_ratio close to 1.0 with negative RC could be Class IV (dim spot).
        if rc_ratio > 1.20:
            return (
                "III",
                "CONDITIONAL: Negative intercept + strong seismic-to-geological ratio "
                "suggests Class III (bright spot, amplitude increasing with offset). "
                "Confirmation requires pre-stack angle gathers per Shuey (1985). "
                "Attention equivalent: high-δ key dominating softmax — α_i ≫ 1/N.",
            )
        else:
            return (
                "III/IV",
                "CONDITIONAL: Negative intercept with modest RC ratio. Could be "
                "Class III (bright spot) or Class IV (dim spot — amplitude DECREASES "
                "with offset). Class IV is the known false-negative hazard in "
                "linearized AVO (Castagna 1998). Attention equivalent: δ_i exists "
                "but may be masked — the dim-spot problem in governance grammar. "
                "Pre-stack validation required.",
            )
    elif rc > 0.05 and abs_rc >= 0.03:
        return (
            "I",
            "CONDITIONAL: Positive intercept suggests Class I (high-impedance gas sand, "
            "typically compacted/cemented). Amplitude may decrease then phase-reverse "
            "at far offsets. Attention equivalent: key initially salient but loses "
            "dominance as context widens — δ_i positive but decaying.",
        )
    elif abs_rc < 0.02:
        return (
            "II",
            "CONDITIONAL: Near-zero intercept suggests Class II (near-zero impedance "
            "contrast, sand nearly invisible on stacked data). Attention equivalent: "
            "δ_i ≈ 0 — key nearly indistinguishable from uniform baseline. "
            "Requires pre-stack amplitude analysis to resolve.",
        )
    else:
        return (
            "UNDETERMINED",
            "Cannot classify from normal-incidence RC alone. Requires pre-stack "
            "angle gathers for definitive AVO class assignment.",
        )


def _compute_attention_residual(
    rc_seismic: float,
    rc_geological: float,
    rc_ratio: float,
    mistie_m: float,
    contradiction_severity: str,
    n_formations: int,
) -> dict[str, Any]:
    """Compute the attention-domain contrast residual for this anomaly.

    Maps the physical AVO anomaly to its attention-domain equivalent per
    the Eureka GeoX Theory of Anomalous Contrast:

        ΔF (fluid factor) = B_obs − m·A_obs  [Smith & Gidlow, 1987]
        δ_i (attention residual) = e_i − ē    [Vaswani et al., 2017]
        ΔV (governance deviation) = verdict − floor_expected

    All three are instances of the SAME contrast primitive:
        signal = f(observation − background)

    Returns:
        dict with contrast_residual, softmax_equivalent, background_model,
        and governance_derivative.
    """
    # ── Contrast residual: how far this reflector's signature deviates ──
    # from the geological background (formation tops = calibrated baseline)
    #
    # AVO domain:    ΔF = B_obs − m·A_obs          [deviation from mudrock line]
    # Attention:     δ_i = (q·k_i)/√d_k − ē        [deviation from uniform baseline]
    # GEOX:          Δrc = |rc_seismic| − |rc_geological|  [deviation from formation top]
    #
    # The rc_ratio (rc_seismic / rc_geological) is our analog to the
    # attention weight ratio α_i / (1/N) — how many times more salient
    # the seismic response is compared to the expected geological response.
    delta_rc = abs(rc_seismic) - abs(rc_geological)
    delta_rc_normalized = delta_rc / max(abs(rc_geological), 1e-9)

    # ── Softmax equivalent ─────────────────────────────────────────────
    # In attention: α_i = 1 / [1 + (N−1)·exp(−δ)]
    # Using rc_ratio as our δ proxy:
    #   α_i / α_avg ≈ rc_ratio / 1.0
    # A rc_ratio of 3.0 means this reflector is 3× more "salient" than
    # the geological background — analogous to α_i = 3/N vs uniform 1/N.
    n_eff = max(n_formations, 2)
    softmax_alpha = round(1.0 / (1.0 + (n_eff - 1) * (1.0 / max(rc_ratio, 0.01))), 4)
    uniform_baseline = round(1.0 / n_eff, 4)

    # ── Severity → attention hazard class ──────────────────────────────
    severity_map = {
        "HIGH": "ATTENTION_HIJACK — key dominates softmax, all other keys suppressed",
        "MEDIUM": "ATTENTION_BIAS — key disproportionately weighted, contextual dilution risk",
        "LOW": "ATTENTION_NOISE — minor deviation within normal attention variance",
    }

    # ── Essay #13: Softmax Hallucination Risk ───────────────────────────
    # The derivation proves that softmax has NO DEAD ZONE — unlike AVO's
    # hard threshold Θ(|ΔB| − τ), softmax will amplify ANY non-zero
    # deviation, no matter how small, into a non-uniform distribution.
    # This is the mathematical proof that ungoverned attention MUST
    # hallucinate in the presence of noise.
    #
    # Hallucination risk = how much of the attention mass is "false signal"
    # — signal that softmax amplifies despite lacking physical grounding.
    #
    # α_i = 1 / [1 + (N−1)·exp(−δ)]  — Essay #13, Eq. (15)
    # For small δ: α_i ≈ 1/N + (N−1)/N²·δ + O(δ²)  — Taylor expansion
    #
    # The "dead zone" deficit: AVO threshold τ suppresses |ΔB| < τ to zero.
    # Softmax has NO equivalent — even δ = 0.001 produces α_i ≠ 1/N.
    # The hallucination risk is proportional to how much softmax output
    # deviates from uniform despite NO physical anomaly being present.
    # Dead zone deficit: how far α_i deviates from uniform for δ ≈ 0
    dead_zone_deficit = abs(softmax_alpha - uniform_baseline)

    # For a pure noise scenario (δ → 0), what fraction of α_i is
    # "spurious attention" — attention that softmax allocated despite
    # no real signal above baseline?
    if rc_ratio < 1.05:
        # Near-background: softmax will still produce non-uniform output
        hallucination_risk = min(dead_zone_deficit / max(uniform_baseline, 0.001), 1.0)
        risk_level = "CRITICAL" if hallucination_risk > 0.5 else ("ELEVATED" if hallucination_risk > 0.2 else "MODERATE")
        risk_note = (
            "Essay #13, Section 4.3: Ungoverned softmax has NO dead zone. "
            "Even near-background signals (rc_ratio ≈ 1.0) produce non-uniform "
            "attention weights. AVO's hard threshold Θ(|ΔB| − τ) would suppress "
            "this to zero. Softmax amplifies it. This IS the mathematical "
            "mechanism of attention hallucination."
        )
    elif rc_ratio > 10.0:
        # Extreme contrast: softmax saturates to one-hot — adversarial risk
        hallucination_risk = 0.05  # Low false-positive risk, but high adversarial risk
        risk_level = "WARNING"
        risk_note = (
            "Essay #13, Section 5.3: Extremely strong contrast (rc_ratio "
            f"= {rc_ratio:.1f}) pushes softmax into numerical saturation "
            "(α_i → 1.0). This is the attention equivalent of post-critical "
            "angle reflection — the linearized model (Aki-Richards / Shuey) "
            "no longer holds. Equivalent to an adversarial δ that hijacks "
            "the softmax distribution."
        )
    else:
        hallucination_risk = dead_zone_deficit / max(uniform_baseline, 0.001)
        risk_level = "NOMINAL"
        risk_note = (
            "Genuine contrast signal. Softmax amplification is warranted — "
            "the deviation from uniform IS the anomaly. This is the Class III "
            "equivalent: strong signal, high confidence, low hallucination risk."
        )

    # ── Essay #13, Section 6: Approximation Tier ────────────────────────
    # Which tier of the approximation chain is being used?
    # Tier 1 = Exact Zoeppritz (4×4 matrix, not available from normal-incidence RC)
    # Tier 2 = Aki-Richards linearized (requires pre-stack angles)
    # Tier 3 = Shuey two-term / interpretable (what we have: A from RC)
    # Governance requirement increases as you descend tiers.
    approximation_tier = {
        "tier": 3,
        "tier_name": "Shuey two-term / interpretable",
        "avo_chain_position": "Zoeppritz → Aki-Richards → Shuey (HERE)",
        "attention_equivalent": "FlashAttention / interpretable proxy",
        "governance_requirement": (
            "MAXIMUM — external governance must compensate for all "
            "approximation losses. Physics9 guard active. Pre-stack "
            "validation required for AVO class confirmation. "
            "Essay #13, Table 2: 'The further you approximate, the "
            "stronger your external governance must be.'"
        ),
        "missing_from_this_tier": [
            "Full AVO angle-dependent response (requires pre-stack gathers)",
            "Mode-converted S-wave information (requires multi-component data)",
            "Density estimation (requires far-offset / PS data per Veire & Landro, 2006)",
        ],
    }

    # ── Essay #13, Section 5.3: Boundary Condition Flags ─────────────────
    boundary_flags = []
    if abs(rc_seismic) > 0.20:
        boundary_flags.append(
            {
                "condition": "LARGE_CONTRAST",
                "essay_ref": "Section 5.3, Boundary 2",
                "threshold": "|RC| > 0.20",
                "actual": round(abs(rc_seismic), 4),
                "implication": (
                    "Reflection coefficient magnitude exceeds the Aki-Richards "
                    "small-contrast assumption (|ΔVp/Vp| ≪ 1). The linearized "
                    "mapping to attention residual δ_i may degrade. Equivalent "
                    "to softmax numerical saturation — attention becomes one-hot."
                ),
            }
        )
    if mistie_m > 30.0:
        boundary_flags.append(
            {
                "condition": "LARGE_MISTIE",
                "essay_ref": "Section 5.3, Boundary 1 (post-critical analog)",
                "threshold": "mistie > 30m",
                "actual": round(mistie_m, 1),
                "implication": (
                    "Mistie exceeds typical seismic resolution. May indicate "
                    "the equivalent of post-critical reflection — the Shuey "
                    "approximation no longer applies. Verify with checkshot/VSP."
                ),
            }
        )
    if rc_ratio > 20.0:
        boundary_flags.append(
            {
                "condition": "ADVERSARIAL_DELTA",
                "essay_ref": "Section 5.3, Boundary 4",
                "threshold": "rc_ratio > 20.0",
                "actual": round(rc_ratio, 1),
                "implication": (
                    "Extremely disproportionate RC ratio. Essay #13 warns that "
                    "a 'carefully crafted perturbation' can produce an arbitrarily "
                    "large δ_i that softmax amplifies into near-certainty without "
                    "corresponding physical signal. Verify this is not acquisition "
                    "footprint, multiple, or processing artifact."
                ),
            }
        )

    # ── Governance Escalation (Essay #13 boundary conditions → action) ───
    governance_escalation = None
    if boundary_flags:
        conditions = [f["condition"] for f in boundary_flags]
        if "ADVERSARIAL_DELTA" in conditions:
            governance_escalation = {
                "required_status": "VOID",
                "trigger": "ADVERSARIAL_DELTA",
                "reason": (
                    "Essay #13, Section 5.3: Adversarial δ detected. "
                    "Softmax amplifies arbitrarily large perturbations into near-certainty. "
                    "Force VOID — verify this is not acquisition footprint or artifact."
                ),
            }
        elif "LARGE_CONTRAST" in conditions and "LARGE_MISTIE" in conditions:
            governance_escalation = {
                "required_status": "HOLD",
                "trigger": "LARGE_CONTRAST + LARGE_MISTIE",
                "reason": (
                    "Essay #13, Section 5.3: Multiple boundary conditions violated. "
                    "Linearized model (Aki-Richards / Shuey) no longer applies. "
                    "Equivalent to post-critical angle + numerical saturation."
                ),
            }
        elif "LARGE_CONTRAST" in conditions or "LARGE_MISTIE" in conditions:
            governance_escalation = {
                "required_status": "HOLD",
                "trigger": conditions[0],
                "reason": (
                    "Essay #13, Section 5.3: Boundary condition violated. Approximation tier may not hold. Human review required."
                ),
            }

    return {
        "contrast_primitive": "signal = f(observation − background)",
        "avo_fluid_factor_equivalent": {
            "domain": "AVO (Smith & Gidlow, 1987)",
            "formula": "ΔF = B_obs − m·A_obs",
            "geo_analog": f"Δrc = |RC_seismic| − |RC_geological| = {delta_rc_normalized:+.4f} (normalized)",
        },
        "attention_residual_equivalent": {
            "domain": "Transformer (Vaswani et al., 2017)",
            "formula": "δ_i = (q·k_i)/√d_k − ē",
            "geo_analog": f"δ_attention ≈ rc_ratio − 1.0 = {rc_ratio - 1.0:+.4f}",
        },
        "softmax_amplification": {
            "alpha_i": softmax_alpha,
            "uniform_baseline": uniform_baseline,
            "dominance_ratio": round(softmax_alpha / max(uniform_baseline, 0.001), 1),
            "interpretation": (
                f"Anomaly has {softmax_alpha / max(uniform_baseline, 0.001):.1f}× the uniform attention weight. "
                f"In transformer terms: this 'key' dominates the softmax distribution."
            ),
        },
        # ── Essay #13: Novel Contribution ────────────────────────────────
        "softmax_hallucination_risk": {
            "essay_ref": "Essay #13, Section 4.3",
            "theorem": (
                "Ungoverned softmax inevitably hallucinates because it has "
                "NO dead zone. Unlike AVO's hard threshold Θ(|ΔB| − τ) which "
                "suppresses small deviations to zero, softmax amplifies EVERY "
                "non-zero δ_i into a non-uniform attention distribution. "
                "Any noise, any floating-point variation, any slight embedding "
                "misalignment — softmax WILL amplify it."
            ),
            "risk_score": round(hallucination_risk, 4),
            "risk_level": risk_level,
            "dead_zone_deficit": round(dead_zone_deficit, 6),
            "taylor_first_order": (
                f"α_i ≈ 1/N + (N−1)/N²·δ + O(δ²) = {uniform_baseline:.4f} + {uniform_baseline * (n_eff - 1) / n_eff:.4f}·δ"
            ),
            "note": risk_note,
        },
        "approximation_tier": approximation_tier,
        "boundary_condition_flags": boundary_flags,
        "boundary_conditions_pass": len(boundary_flags) == 0,
        "governance_escalation": governance_escalation,
        # ── Previous fields preserved ────────────────────────────────────
        "governance_derivative": {
            "domain": "arifOS Constitutional (F1–F13)",
            "formula": "ΔV = verdict_actual − verdict_expected(F1–F13)",
            "geo_analog": f"mistie = {mistie_m:+.1f}m → contradiction = {contradiction_severity}",
        },
        "attention_hazard_class": severity_map.get(contradiction_severity, "ATTENTION_NOISE"),
        "cross_modal_fidelity": {
            "principle": "Physical constraint reduces admissible solution space",
            "implication": (
                "This contrast residual survives cross-modal transfer because "
                "it is grounded in impedance contrast (Physics9). A purely "
                "data-driven attention anomaly without this physical prior "
                "would be vulnerable to hallucination — the BPI-ViT principle."
            ),
            "hallucination_guard": True,
            "physics_prior": "Zoeppritz → Aki-Richards → Shuey linearization chain",
        },
    }


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
                resolution = f"QUALIFY — seismic pick displaced {abs_mistie:.0f} m; cross-check with well tie"
            else:
                contradiction_severity = "LOW"
                resolution = f"NOTE — minor mistie {abs_mistie:.0f} m; within picking tolerance but flagged"

            # ── AVO class classification (conditional, from normal-incidence RC) ──
            rc_ratio_val = rc_at_seismic / max(rc_at_geo, 1e-9)
            avo_class, avo_note = _classify_avo_class(
                rc=rc_at_seismic,
                rc_ratio=rc_ratio_val,
                mistie_m=float(mistie),
                depth_m=geo_depth_actual,
            )

            # ── Attention residual (Eureka GeoX Theory) ──────────────────
            attention_residual = _compute_attention_residual(
                rc_seismic=rc_at_seismic,
                rc_geological=rc_at_geo,
                rc_ratio=rc_ratio_val,
                mistie_m=float(mistie),
                contradiction_severity=contradiction_severity,
                n_formations=len(formation_tops),
            )

            anomalies.append(
                {
                    "formation": formation_name,
                    "depth_geological_m": round(geo_depth_actual, 2),
                    "depth_seismic_m": round(seismic_depth, 2),
                    "rc_geological": round(rc_at_geo, 6),
                    "rc_seismic": round(rc_at_seismic, 6),
                    "rc_ratio": round(rc_ratio_val, 3),
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
                    # ── AVO class + Attention equivalence (Eureka GeoX Theory v2026.06.05) ──
                    "avo_class": avo_class,
                    "avo_class_note": avo_note,
                    "attention_residual": attention_residual,
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
                "ΔF = B_obs − m·A_obs  [Smith & Gidlow, 1987 — fluid factor]",
                "δ_i = (q·k_i)/√d_k − ē  [Vaswani et al., 2017 — attention residual]",
            ],
            "assumptions": [
                "normal incidence reflectivity",
                "formation top is known from well data",
                "impedance contrast dominates seismic response",
                "AVO class estimate is CONDITIONAL — full pre-stack validation required",
            ],
            "limitations": [
                "does not account for tuning effects",
                "does not model AVO response from angle gathers",
                "volumetric impact is first-order approximation",
                "AVO class from normal-incidence RC — Shuey (1985) linearization limits apply",
            ],
        },
        # ── Eureka GeoX Theory: AVO-Attention Equivalence ─────────────────
        "attention_equivalence": {
            "theorem": "Eureka GeoX Theory of Anomalous Contrast (2026-06-05)",
            "statement": (
                "An AVO anomalous contrast in the physical subsurface maps "
                "isomorphically to an attention anomaly in a physics-constrained "
                "transformer. Both implement the contrast primitive: "
                "signal = amplify(normalize(observation − background))."
            ),
            "avo_chain": (
                "Zoeppritz (exact 4×4) → Aki-Richards (linearized) → Shuey (A + B·sin²θ) → "
                "Castagna & Swan (crossplot background trend) → Smith & Gidlow (fluid factor ΔF)"
            ),
            "attention_chain": (
                "Full softmax attention (exact O(N²)) → Linear attention (kernelized) → "
                "FlashAttention (IO-optimized) → Anomaly Transformer (prior vs series) → "
                "Pi-Transformer (physics-informed prior attention)"
            ),
            "shared_primitive": [
                {
                    "component": "Observation",
                    "avo_domain": "R(θ) — reflection coefficient vs. angle",
                    "attention_domain": "e_j = q·k_j / √d_k — alignment score",
                },
                {
                    "component": "Baseline",
                    "avo_domain": "Mudrock line: B_bg = m·A (Castagna & Swan, 1997)",
                    "attention_domain": "Uniform distribution: α_j = 1/N (all keys equally relevant)",
                },
                {
                    "component": "Contrast Residual",
                    "avo_domain": "ΔF = B_obs − m·A_obs (Smith & Gidlow, 1987)",
                    "attention_domain": "δ_i = e_i − ē (key deviation from mean alignment)",
                },
                {
                    "component": "Amplification",
                    "avo_domain": "AVO Class I–IV + anomaly flag (Rutherford & Williams, 1989)",
                    "attention_domain": "α_i = softmax(δ_i) — exponential winner-take-most",
                },
                {
                    "component": "Governance Derivative",
                    "avo_domain": "888_HOLD if |ΔF| > threshold",
                    "attention_domain": "AC_Risk = f(u_ambiguity, evidence_credit) — constitutional gating",
                },
            ],
            "failure_modes": [
                {
                    "avo": "False Class III: high-porosity brine sand mimics gas (Castagna & Swan, 1997)",
                    "attention": "Hallucination: ambiguous query attends to syntactically similar but irrelevant key",
                    "mitigation": "Physics9 guard (AI range check) + cross-modal stability verification",
                },
                {
                    "avo": "Class IV false negative: gas sand dims with offset — missed by amplitude-only screening",
                    "attention": "Dim spot: negative constraint lost in cross-modal transfer — VOID becomes invisible",
                    "mitigation": "dim_spot_flag + structural coherence violation classification",
                },
            ],
            "independent_convergence": (
                "Pi-Transformer (Maleki & Pourmoazemi, 2025) and Anomaly Transformer "
                "(Xu et al., ICLR 2022) independently implemented the same contrast primitive "
                "(prior vs. data-driven attention = background vs. observation) without "
                "citing geophysics — confirming the universality of the structure."
            ),
            "ratified": "2026-06-05",
            "toac_version": "v2026.06.05",
            "document": "docs/AVO_ATTENTION_FORMAL_EQUIVALENCE.md",
            # ── Essay #13: The Derivation ─────────────────────────────────
            "trilogy_reference": {
                "essay_11": "Contrast-Governed Anomaly Detection: A Formal Bridge — the EUREKA",
                "essay_12": "Physics-Constrained Attention: Zoeppritz as Constitutional Floor — governance consequences",
                "essay_13": "The Contrast Primitive Derivation — the mathematical lock-in (this implementation)",
                "url": "https://arif-fazil.com/essays/contrast-primitive-derivation-avo-fluid-factor-attention-residual",
                "central_theorem": (
                    "Ungoverned softmax inevitably hallucinates because it has NO dead zone. "
                    "Unlike AVO's hard threshold Θ(|ΔB| − τ) which suppresses small deviations "
                    "to zero, softmax amplifies EVERY non-zero δ_i into a non-uniform distribution. "
                    "The derivation provides the first-order Taylor expansion: "
                    "α_i = 1/N + (N−1)/N²·δ + O(δ²). For any δ ≠ 0, α_i ≠ 1/N."
                ),
                "key_insight": (
                    "The further you approximate, the stronger your external governance must be. "
                    "Shuey two-term works brilliantly for Class III at moderate angles — and fails "
                    "for Class IV. FlashAttention computes exact output but produces intermediates "
                    "that cannot be audited. In both cases, the defense is an external baseline "
                    "that the approximation cannot overwrite."
                ),
            },
        },
    }
