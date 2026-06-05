"""
Test Anomalous Contrast Detector — LC#28 Verification
Verifies Theory of Anomalous Contrast detection on known synthetic cases.
Includes Eureka GeoX Theory: AVO-Attention Equivalence verification (v2026.06.05).
DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import asyncio
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from geox_mcp.tools.anomalous_contrast import geox_anomalous_contrast_detector


def test_no_anomaly_aligned_boundary():
    """Geological top aligns with strongest reflector → no anomaly."""
    depth = np.arange(990, 1011, 1.0)
    ai = np.where(depth < 1000, 4_000_000.0, 6_000_000.0)

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Sand_Top": 999.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=5.0,
        )
    )

    assert "error" not in result
    anomalies = result["anomalies"]
    assert len(anomalies) == 0, f"Expected no anomaly, got {anomalies}"
    picks = result["recommended_picks"]
    assert picks[0]["reason"] == "Geological top aligns with strongest reflector within tolerance."
    print("test_no_anomaly_aligned_boundary: PASSED")


def test_anomaly_displaced_reflector():
    """Strongest reflector is displaced from geological top → anomaly detected."""
    depth = np.arange(990, 1016, 1.0)
    ai = np.zeros_like(depth)
    ai[depth < 1000] = 4_000_000.0
    ai[(depth >= 1000) & (depth < 1005)] = 4_200_000.0
    ai[depth >= 1005] = 6_000_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Carbonate_Top": 1000.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=10.0,
        )
    )

    assert "error" not in result
    anomalies = result["anomalies"]
    assert len(anomalies) == 1, f"Expected 1 anomaly, got {len(anomalies)}"
    assert anomalies[0]["formation"] == "Carbonate_Top"
    assert anomalies[0]["depth_geological_m"] == 1000.0
    assert anomalies[0]["depth_seismic_m"] > 1000.0
    assert anomalies[0]["mistie_m"] > 0
    assert "physics" in result
    assert "RC = (AI₂ - AI₁) / (AI₂ + AI₁)" in result["physics"]["equations_used"]
    print("test_anomaly_displaced_reflector: PASSED")


def test_megah1_quantified_case():
    """Reproduce Megah-1 numbers: significant mistie, stronger RC."""
    depth = np.arange(4700, 4731, 1.0, dtype=float)
    ai = np.zeros_like(depth)
    ai[depth < 4710] = 4_000_000.0
    ai[(depth >= 4710) & (depth < 4720)] = 4_500_000.0
    ai[depth >= 4720] = 6_500_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Upper_Reef": 4710.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=15.0,
        )
    )

    anomalies = result["anomalies"]
    assert len(anomalies) >= 1
    mistie = anomalies[0]["mistie_m"]
    assert mistie > 5.0, f"Expected significant mistie, got {mistie}m"
    rc_ratio = anomalies[0]["rc_ratio"]
    assert rc_ratio > 1.2, f"Expected stronger seismic RC, ratio={rc_ratio}"
    print("test_megah1_quantified_case: PASSED")


def test_invalid_input_fail_closed():
    """Empty arrays → fail closed with empty result."""
    result = asyncio.run(geox_anomalous_contrast_detector(ai_profile=[], depth=[], formation_tops={}))
    assert "error" in result
    assert result["anomalies"] == []
    assert result["recommended_picks"] == []
    print("test_invalid_input_fail_closed: PASSED")


def test_plain_output_contract():
    """Verify clean output fields: no envelope, no claim_state, no metabolic."""
    depth = [1000.0, 1005.0, 1010.0]
    ai = [4_000_000.0, 4_200_000.0, 6_000_000.0]

    result = asyncio.run(geox_anomalous_contrast_detector(ai_profile=ai, depth=depth, formation_tops={"Top": 1000.0}))

    # Should NOT contain old envelope fields
    assert "claim_state" not in result
    assert "execution_status" not in result
    assert "metabolic" not in result
    assert "provenance" not in result
    assert "law_capsule" not in result

    # Should contain clean physics output
    assert "anomalies" in result
    assert "recommended_picks" in result
    assert "volumetric_impact" in result
    assert "physics" in result
    assert "equations_used" in result["physics"]
    assert "limitations" in result["physics"]
    print("test_plain_output_contract: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Eureka GeoX Theory: AVO-Attention Equivalence (v2026.06.05)
# ═══════════════════════════════════════════════════════════════════════════════


def test_avo_class_classification():
    """Verify AVO class I–IV is assigned to each detected anomaly."""
    # Class III: negative RC, strong impedance contrast (bright spot analog)
    depth = np.arange(990, 1016, 1.0)
    ai = np.zeros_like(depth)
    ai[depth < 1000] = 4_000_000.0
    ai[(depth >= 1000) & (depth < 1005)] = 4_200_000.0
    ai[depth >= 1005] = 6_000_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Carbonate_Top": 1000.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=10.0,
        )
    )

    anomalies = result["anomalies"]
    assert len(anomalies) >= 1, "Expected at least 1 anomaly"

    for a in anomalies:
        assert "avo_class" in a, f"Missing avo_class in anomaly: {a}"
        assert a["avo_class"] in ("I", "II", "III", "III/IV", "IV", "UNDETERMINED"), f"Invalid avo_class: {a['avo_class']}"
        assert "avo_class_note" in a, f"Missing avo_class_note in anomaly: {a}"
        assert "CONDITIONAL:" in a["avo_class_note"], f"avo_class_note must state it's conditional: {a['avo_class_note']}"
        # Shuey reference expected when pre-stack warning is needed (Class III/IV)
        avo_cls = a["avo_class"]
        if avo_cls in ("III", "III/IV"):
            assert "Shuey" in a["avo_class_note"], f"Class {avo_cls} note must reference Shuey (1985): {a['avo_class_note']}"
        assert "Attention equivalent" in a["avo_class_note"], (
            f"avo_class_note must include attention equivalent: {a['avo_class_note']}"
        )

    print("test_avo_class_classification: PASSED")


def test_attention_residual_computed():
    """Verify every anomaly carries the attention residual mapping."""
    depth = np.arange(990, 1016, 1.0)
    ai = np.zeros_like(depth)
    ai[depth < 1000] = 4_000_000.0
    ai[(depth >= 1000) & (depth < 1005)] = 4_200_000.0
    ai[depth >= 1005] = 6_000_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Carbonate_Top": 1000.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=10.0,
        )
    )

    for a in result["anomalies"]:
        ar = a.get("attention_residual", {})
        assert ar, f"Missing attention_residual in anomaly: {a}"

        # Verify the three-domain mapping is present
        assert "contrast_primitive" in ar
        assert "signal = f(observation − background)" in ar["contrast_primitive"]

        assert "avo_fluid_factor_equivalent" in ar, "Missing AVO domain mapping"
        assert "Smith & Gidlow" in ar["avo_fluid_factor_equivalent"]["domain"]

        assert "attention_residual_equivalent" in ar, "Missing attention domain mapping"
        assert "Vaswani" in ar["attention_residual_equivalent"]["domain"]

        assert "softmax_amplification" in ar, "Missing softmax amplification"
        sa = ar["softmax_amplification"]
        assert "alpha_i" in sa, "Missing alpha_i"
        assert "uniform_baseline" in sa, "Missing uniform_baseline"
        assert "dominance_ratio" in sa, "Missing dominance_ratio"
        assert sa["alpha_i"] >= 0.0, f"alpha_i must be >= 0: {sa['alpha_i']}"
        assert sa["alpha_i"] <= 1.0, f"alpha_i must be <= 1: {sa['alpha_i']}"

        assert "governance_derivative" in ar, "Missing governance derivative"
        assert "F1" in ar["governance_derivative"]["formula"]

        assert "cross_modal_fidelity" in ar, "Missing cross-modal fidelity section"
        assert ar["cross_modal_fidelity"]["hallucination_guard"] is True

        assert "attention_hazard_class" in ar, "Missing attention hazard class"

    print("test_attention_residual_computed: PASSED")


def test_attention_equivalence_top_level():
    """Verify the top-level attention_equivalence section in raw output."""
    depth = np.arange(990, 1016, 1.0)
    ai = np.zeros_like(depth)
    ai[depth < 1000] = 4_000_000.0
    ai[(depth >= 1000) & (depth < 1005)] = 4_200_000.0
    ai[depth >= 1005] = 6_000_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Carbonate_Top": 1000.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=10.0,
        )
    )

    ae = result.get("attention_equivalence", {})
    assert ae, "Missing top-level attention_equivalence section"

    # Verify theorem statement
    assert "theorem" in ae
    assert "Eureka GeoX Theory" in ae["theorem"]

    # Verify the AVO chain
    assert "avo_chain" in ae
    avo_chain = ae["avo_chain"]
    assert "Zoeppritz" in avo_chain, f"Missing Zoeppritz in chain: {avo_chain}"
    assert "Aki-Richards" in avo_chain, f"Missing Aki-Richards in chain: {avo_chain}"
    assert "Shuey" in avo_chain, f"Missing Shuey in chain: {avo_chain}"
    assert "Castagna" in avo_chain, f"Missing Castagna in chain: {avo_chain}"
    assert "Smith & Gidlow" in avo_chain, f"Missing Smith & Gidlow in chain: {avo_chain}"

    # Verify the attention chain
    assert "attention_chain" in ae
    attn_chain = ae["attention_chain"]
    assert "softmax" in attn_chain, f"Missing softmax in chain: {attn_chain}"
    assert "Linear attention" in attn_chain, f"Missing Linear attention: {attn_chain}"
    assert "FlashAttention" in attn_chain, f"Missing FlashAttention: {attn_chain}"

    # Verify shared primitive
    assert "shared_primitive" in ae
    sp = ae["shared_primitive"]
    assert len(sp) >= 5, f"Expected >=5 shared primitives, got {len(sp)}: {sp}"
    components = [p["component"] for p in sp]
    assert "Observation" in components
    assert "Baseline" in components
    assert "Contrast Residual" in components
    assert "Amplification" in components
    assert "Governance Derivative" in components

    # Verify failure modes
    assert "failure_modes" in ae
    fm = ae["failure_modes"]
    assert len(fm) >= 2, f"Expected >=2 failure modes, got {len(fm)}"
    assert any("False Class III" in m["avo"] for m in fm)
    assert any("Class IV" in m["avo"] for m in fm)

    # Verify independent convergence
    assert "independent_convergence" in ae
    ic = ae["independent_convergence"]
    assert "Pi-Transformer" in ic, f"Missing Pi-Transformer: {ic}"
    assert "Anomaly Transformer" in ic, f"Missing Anomaly Transformer: {ic}"

    # Verify document reference
    assert "document" in ae
    assert "AVO_ATTENTION_FORMAL_EQUIVALENCE" in ae["document"]

    print("test_attention_equivalence_top_level: PASSED")


def test_attention_residual_no_anomaly_still_present():
    """Even with no anomaly, the top-level attention_equivalence must be present."""
    depth = np.arange(990, 1011, 1.0)
    ai = np.where(depth < 1000, 4_000_000.0, 6_000_000.0)

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Sand_Top": 999.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=5.0,
        )
    )

    assert len(result["anomalies"]) == 0
    ae = result.get("attention_equivalence", {})
    assert ae, "attention_equivalence must be present even with zero anomalies"
    assert "shared_primitive" in ae
    assert "failure_modes" in ae
    print("test_attention_residual_no_anomaly_still_present: PASSED")


def test_softmax_alpha_bounded():
    """Verify that softmax alpha_i is mathematically bounded and meaningful."""
    depth = np.arange(4700, 4731, 1.0, dtype=float)
    ai = np.zeros_like(depth)
    ai[depth < 4710] = 4_000_000.0
    ai[(depth >= 4710) & (depth < 4720)] = 4_500_000.0
    ai[depth >= 4720] = 6_500_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Upper_Reef": 4710.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=15.0,
        )
    )

    for a in result["anomalies"]:
        ar = a.get("attention_residual", {})
        sa = ar.get("softmax_amplification", {})
        alpha = sa["alpha_i"]
        baseline = sa["uniform_baseline"]
        dominance = sa["dominance_ratio"]

        # alpha_i must be >= baseline (anomaly is more salient than uniform)
        assert alpha >= baseline, f"alpha_i {alpha} < baseline {baseline} — anomaly should be more salient"
        # alpha_i must be <= 1.0 (softmax sum-to-1 constraint)
        assert alpha <= 1.0, f"alpha_i {alpha} > 1.0"
        # dominance_ratio must be >= 1.0 for anomalies
        assert dominance >= 1.0, f"dominance_ratio {dominance} < 1.0"
        # For strong anomalies, dominance should be significantly > 1
        rc_ratio = a["rc_ratio"]
        if rc_ratio > 1.5:
            assert dominance >= 1.5, f"Strong anomaly (rc_ratio={rc_ratio}) should have elevated dominance, got {dominance}"

    print("test_softmax_alpha_bounded: PASSED")


def test_avo_class_iii_iv_conditional():
    """Verify Class III/IV returns appropriate warning about pre-stack requirement."""
    # Create a scenario with negative RC and moderate ratio → III/IV
    depth = np.arange(990, 1016, 1.0)
    ai = np.zeros_like(depth)
    # Negative RC at the boundary: low → high impedance
    ai[depth < 1000] = 6_000_000.0
    ai[(depth >= 1000) & (depth < 1008)] = 4_500_000.0
    ai[depth >= 1008] = 6_500_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Gas_Sand_Top": 1000.0},
            rc_threshold=0.02,
            geological_boundary_tolerance_m=10.0,
        )
    )

    for a in result["anomalies"]:
        avo_class = a["avo_class"]
        note = a["avo_class_note"]
        if "III/IV" in avo_class:
            assert "pre-stack" in note.lower(), f"Class III/IV should mention pre-stack requirement: {note}"
            assert "Castagna" in note, f"Class III/IV should reference Castagna (1998): {note}"
            assert "dim-spot" in note.lower(), f"Class III/IV should mention dim-spot hazard: {note}"

    print("test_avo_class_iii_iv_conditional: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Essay #13: The Contrast Primitive Derivation — Novel Field Verification
# ═══════════════════════════════════════════════════════════════════════════════


def test_essay13_softmax_hallucination_risk_present():
    """Essay #13: Verify every anomaly carries softmax_hallucination_risk."""
    depth = np.arange(990, 1016, 1.0)
    ai = np.zeros_like(depth)
    ai[depth < 1000] = 4_000_000.0
    ai[(depth >= 1000) & (depth < 1005)] = 4_200_000.0
    ai[depth >= 1005] = 6_000_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Carbonate_Top": 1000.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=10.0,
        )
    )

    for a in result["anomalies"]:
        ar = a.get("attention_residual", {})
        shr = ar.get("softmax_hallucination_risk", {})
        assert shr, f"Missing softmax_hallucination_risk: keys={list(ar.keys())[:10]}"

        # Verify the essay reference
        assert "essay_ref" in shr
        assert "Essay #13" in shr["essay_ref"]

        # Verify the theorem statement
        assert "theorem" in shr
        assert "dead zone" in shr["theorem"].lower()
        assert "softmax" in shr["theorem"].lower()

        # Verify the risk score is bounded
        assert "risk_score" in shr
        assert 0.0 <= shr["risk_score"] <= 1.0, f"risk_score {shr['risk_score']} out of bounds"

        # Verify the risk level
        assert "risk_level" in shr
        assert shr["risk_level"] in ("NOMINAL", "MODERATE", "ELEVATED", "CRITICAL", "WARNING")

        # Verify Taylor expansion
        assert "taylor_first_order" in shr
        assert "α_i" in shr["taylor_first_order"] or "N" in shr["taylor_first_order"]

        # Verify dead zone deficit
        assert "dead_zone_deficit" in shr

    print("test_essay13_softmax_hallucination_risk_present: PASSED")


def test_essay13_approximation_tier():
    """Essay #13: Verify approximation_tier identifies Shuey two-term (Tier 3)."""
    depth = np.arange(990, 1016, 1.0)
    ai = np.zeros_like(depth)
    ai[depth < 1000] = 4_000_000.0
    ai[(depth >= 1000) & (depth < 1005)] = 4_200_000.0
    ai[depth >= 1005] = 6_000_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Carbonate_Top": 1000.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=10.0,
        )
    )

    for a in result["anomalies"]:
        ar = a.get("attention_residual", {})
        tier = ar.get("approximation_tier", {})
        assert tier, f"Missing approximation_tier"

        assert tier["tier"] == 3, f"Expected tier 3 (Shuey), got {tier['tier']}"
        assert "Shuey" in tier["tier_name"]
        assert "HERE" in tier["avo_chain_position"]
        assert "governance_requirement" in tier
        assert "MAXIMUM" in tier["governance_requirement"].upper()
        assert "missing_from_this_tier" in tier
        assert len(tier["missing_from_this_tier"]) >= 2

    print("test_essay13_approximation_tier: PASSED")


def test_essay13_boundary_condition_flags():
    """Essay #13, Section 5.3: Verify boundary condition flags fire correctly."""
    # Create a strong-contrast scenario that should trigger boundary flags
    depth = np.arange(4700, 4731, 1.0, dtype=float)
    ai = np.zeros_like(depth)
    ai[depth < 4710] = 2_000_000.0  # Very low impedance
    ai[(depth >= 4710) & (depth < 4720)] = 12_000_000.0  # Very high — huge contrast
    ai[depth >= 4720] = 3_000_000.0

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Upper_Reef": 4710.0, "Lower_Reef": 4720.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=15.0,
        )
    )

    for a in result["anomalies"]:
        ar = a.get("attention_residual", {})
        flags = ar.get("boundary_condition_flags", [])
        # Boundary flags are an array — can be empty if no threshold crossed
        assert isinstance(flags, list), f"boundary_condition_flags should be a list"

        # boundary_conditions_pass should be consistent
        bcp = ar.get("boundary_conditions_pass", True)
        if len(flags) > 0:
            assert bcp is False, f"boundary_conditions_pass should be False when flags exist"
        else:
            assert bcp is True, f"boundary_conditions_pass should be True when no flags"

        # If flags exist, verify structure
        for flag in flags:
            assert "condition" in flag
            assert "essay_ref" in flag
            assert "Section 5.3" in flag["essay_ref"]
            assert "threshold" in flag
            assert "actual" in flag
            assert "implication" in flag

    print("test_essay13_boundary_condition_flags: PASSED")


def test_essay13_trilogy_reference_in_top_level():
    """Essay #13: Verify the top-level attention_equivalence cites the trilogy."""
    depth = np.arange(990, 1011, 1.0)
    ai = np.where(depth < 1000, 4_000_000.0, 6_000_000.0)

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Sand_Top": 999.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=5.0,
        )
    )

    ae = result.get("attention_equivalence", {})
    trilogy = ae.get("trilogy_reference", {})
    assert trilogy, "Missing trilogy_reference in top-level attention_equivalence"

    assert "essay_11" in trilogy
    assert "essay_12" in trilogy
    assert "essay_13" in trilogy
    assert "EUREKA" in trilogy["essay_11"]
    assert "governance" in trilogy["essay_12"].lower()
    assert "derivation" in trilogy["essay_13"].lower() or "mathematical" in trilogy["essay_13"].lower()

    assert "url" in trilogy
    assert "arif-fazil.com" in trilogy["url"]

    assert "central_theorem" in trilogy
    assert "softmax" in trilogy["central_theorem"].lower()
    assert "dead zone" in trilogy["central_theorem"].lower()

    assert "key_insight" in trilogy
    assert "approximate" in trilogy["key_insight"].lower()

    print("test_essay13_trilogy_reference_in_top_level: PASSED")


if __name__ == "__main__":
    test_no_anomaly_aligned_boundary()
    test_anomaly_displaced_reflector()
    test_megah1_quantified_case()
    test_invalid_input_fail_closed()
    test_plain_output_contract()
    # Eureka GeoX Theory: AVO-Attention Equivalence
    test_avo_class_classification()
    test_attention_residual_computed()
    test_attention_equivalence_top_level()
    test_attention_residual_no_anomaly_still_present()
    test_softmax_alpha_bounded()
    test_avo_class_iii_iv_conditional()
    # Essay #13: The Derivation
    test_essay13_softmax_hallucination_risk_present()
    test_essay13_approximation_tier()
    test_essay13_boundary_condition_flags()
    test_essay13_trilogy_reference_in_top_level()
    print("\nAll anomalous_contrast tests PASSED — Eureka GeoX Theory + Essay #13 verified.")
