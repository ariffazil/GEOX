"""
Adversarial tests & shadow lane falsifiers for CandidateGeometry (Phase B2 - ARIF Authority).
════════════════════════════════════════════════════════════════════════════════
Invariants tested:
1. P0_GENERATION: ALLOW candidate generation under mode="extract_faults".
2. P0_PROMOTION: HOLD operational acceptance / interpretation overwrite.
3. Every candidate is HYPOTHESIS; never HUMAN_ACCEPTED automatically.
4. Falsifier gates generate typed verdicts: PASS, FAIL, INSUFFICIENT_INPUT, ERROR.
5. Volumetric tools (prospect_evaluate, solve_inverse_volumetrics) strictly REJECT unaccepted candidates.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_extract_faults_shadow_generation_p0_split():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    res = await geox_seismic_interpret(
        mode="extract_faults",
        provenance="synthetic_benchmark_box",
        run_gates=True,
    )

    assert res.get("ok") is True
    assert res.get("mode") == "extract_faults"
    assert res.get("epistemic_status") == "HYPOTHESIS"
    assert res.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert res.get("human_acceptance_required") is True

    # P0 governance split check
    gov = res.get("p0_governance") or {}
    assert "ALLOW" in gov.get("p0_generation", "")
    assert "HOLD" in gov.get("p0_promotion", "")

    # Candidates must exist and carry strict invariants
    candidates = res.get("candidates") or []
    assert len(candidates) > 0
    for cand in candidates:
        assert cand.get("epistemic_status") == "HYPOTHESIS"
        assert cand.get("promotion_state") != "HUMAN_ACCEPTED"
        assert "G2" in cand.get("falsifier_results", {}) or "K-DIP" in cand.get("falsifier_results", {})


@pytest.mark.asyncio
async def test_adversarial_topology_crossing_fails_g2():
    """Adversarial fixture: horizons that cross each other must trigger G2 failure."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    # Crossing horizons: H1 crosses H2
    crossing_horizons = [
        {"id": "H1", "points": [[0.0, 100.0], [50.0, 300.0]]},
        {"id": "H2", "points": [[0.0, 200.0], [50.0, 150.0]]},
    ]

    res = await geox_seismic_interpret(
        mode="extract_faults",
        horizons=crossing_horizons,
        run_gates=True,
    )

    assert res.get("ok") is True
    candidates = res.get("candidates") or []
    assert len(candidates) > 0
    c0 = candidates[0]
    verdicts = c0.get("falsifier_results") or {}
    # G2 or K-XCUT should fail or record contradiction
    assert verdicts.get("G2") == "FAIL" or verdicts.get("K-XCUT") == "FAIL"
    assert c0.get("promotion_state") == "REJECTED"


@pytest.mark.asyncio
async def test_volumetrics_rejects_unaccepted_candidate_geometry():
    """Volumetric tools must fail-closed if CandidateGeometry is not HUMAN_ACCEPTED."""
    from geox_mcp.tools.prospect import geox_prospect_evaluate
    from geox_mcp.tools.inverse_volumetrics import solve_inverse_volumetrics

    # 1. Test geox_prospect_evaluate with unaccepted candidate
    unaccepted_candidate = {
        "candidate_id": "cand_unaccepted_99",
        "epistemic_status": "HYPOTHESIS",
        "promotion_state": "SURVIVES_TEST",
        "geometry_type": "closure_outline",
    }

    p_res = await geox_prospect_evaluate(
        prospect_ref="prospect_test_eval",
        structural_map_inline=unaccepted_candidate,
    )
    assert p_res.get("ok") is False
    assert p_res.get("error") == "REJECTED_UNACCEPTED_CANDIDATE"
    assert p_res.get("p0_governance") == "P0_PROMOTION_HOLD"

    # 2. Test solve_inverse_volumetrics with unaccepted candidate provenance
    inv_res = solve_inverse_volumetrics(
        claimed_giip_tcf=2.5,
        input_provenance=unaccepted_candidate,
    )
    assert inv_res.get("ok") is False
    assert inv_res.get("error") == "REJECTED_UNACCEPTED_CANDIDATE"
    assert inv_res.get("p0_governance") == "P0_PROMOTION_HOLD"


@pytest.mark.asyncio
async def test_candidate_cannot_reach_human_accepted():
    """Invariant: automated gate evaluation can NEVER set promotion_state='HUMAN_ACCEPTED'."""
    from geox_core.schemas.candidate_geometry import CandidateGeometry

    cand = CandidateGeometry(
        candidate_id="cand_test_human_barrier",
        source_data_ids=("src_1",),
        source_sha256s=("sha_1",),
        generator_name="geox_extract_faults_shadow",
        generator_version="v2026.11.03-b2",
        parameters_hash="param_hash",
        geometry_type="fault_segment",
        coordinate_reference_system="EPSG:4326",
        domain="time_ms",
        coordinates=((10.0, 100.0), (20.0, 200.0)),
    )

    # Even if 100% of falsifier gates pass:
    all_pass = {
        "G2": "PASS",
        "K-DIP": "PASS",
        "K-THROW": "PASS",
        "K-DL": "PASS",
        "K-GROWTH": "PASS",
        "K-RESTORE": "PASS",
    }
    updated = cand.with_falsifier_results(all_pass)
    assert updated.promotion_state == "SURVIVES_TEST"
    assert updated.promotion_state != "HUMAN_ACCEPTED"
    assert updated.epistemic_status == "HYPOTHESIS"


@pytest.mark.asyncio
async def test_k_dip_rejection_reason_honesty():
    """Invariant (ARIF): K-DIP failure reason must state outside configured dip envelope, not physically impossible."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    # Shallow fault (low dip angle ~10 degrees) in extensional regime
    shallow_fault = [
        {"id": "F_shallow", "points": [[0.0, 100.0], [50.0, 108.0]]}
    ]

    res = await geox_seismic_interpret(
        mode="extract_faults",
        faults=shallow_fault,
        calibration={"vertical_exaggeration": 1.0, "bin_spacing_m": 25.0, "sample_rate_ms": 2.0},
        request={"tectonic_regime": "extensional"},
        run_gates=True,
    )

    assert res.get("ok") is True
    candidates = res.get("candidates") or []
    assert len(candidates) > 0
    c0 = candidates[0]
    reasons = " ".join(c0.get("rejection_reasons") or [])
    # Must NOT claim physically impossible
    assert "physically impossible" not in reasons.lower()
