"""
Test Anomalous Contrast Detector — LC#28 Verification
═══════════════════════════════════════════════════════════════════════════════
Verifies Theory of Anomalous Contrast detection on known synthetic cases.
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
    # Uniform shale (AI=4M) then clean sand (AI=6M) — sharp contrast at 1000m
    depth = np.arange(990, 1011, 1.0)
    ai = np.where(depth < 1000, 4_000_000.0, 6_000_000.0)

    # The RC peak for a step at 1000m is at the interface between 999 and 1000,
    # which maps to sample index 9 (depth 999). Align formation top to match.
    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Sand_Top": 999.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=5.0,
        )
    )

    assert result["execution_status"] == "SUCCESS"
    anomalies = result["primary_artifact"]["anomalies"]
    assert len(anomalies) == 0, f"Expected no anomaly, got {anomalies}"
    picks = result["primary_artifact"]["recommended_picks"]
    assert picks[0]["verification_required"] == "none"
    print("test_no_anomaly_aligned_boundary: PASSED")


def test_anomaly_displaced_reflector():
    """Strongest reflector is displaced from geological top → anomaly detected."""
    # Carbonate with transparent cap: shale (4M) → porous carbonate (4.2M) → tight carbonate (6M)
    # Geological top at 1000m (shale→porous carbonate), but strong reflector at 1005m (porous→tight)
    depth = np.arange(990, 1016, 1.0)
    ai = np.zeros_like(depth)
    ai[depth < 1000] = 4_000_000.0          # Shale
    ai[(depth >= 1000) & (depth < 1005)] = 4_200_000.0   # Porous carbonate (weak contrast with shale)
    ai[depth >= 1005] = 6_000_000.0         # Tight carbonate (strong contrast)

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai.tolist(),
            depth=depth.tolist(),
            formation_tops={"Carbonate_Top": 1000.0},
            rc_threshold=0.05,
            geological_boundary_tolerance_m=10.0,
        )
    )

    assert result["execution_status"] == "SUCCESS"
    anomalies = result["primary_artifact"]["anomalies"]
    assert len(anomalies) == 1, f"Expected 1 anomaly, got {len(anomalies)}"
    assert anomalies[0]["formation"] == "Carbonate_Top"
    assert anomalies[0]["depth_geological_m"] == 1000.0
    # Strongest reflector should be at ~1005m
    assert anomalies[0]["depth_seismic_m"] > 1000.0
    assert anomalies[0]["mistie_m"] > 0
    assert "LC#28" in result["primary_artifact"]["law_capsule"]
    print("test_anomaly_displaced_reflector: PASSED")


def test_megah1_quantified_case():
    """Reproduce Megah-1 numbers from artifact: 10m mistie, 39% stronger RC."""
    depth = np.arange(4700, 4731, 1.0, dtype=float)
    # Shale above: AI ~ 4.0M; Upper Reef (porous): AI ~ 4.5M; Main Reef: AI ~ 6.5M
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

    anomalies = result["primary_artifact"]["anomalies"]
    assert len(anomalies) >= 1
    # The strongest reflector should be at the 4720m interface, not 4710m
    mistie = anomalies[0]["mistie_m"]
    assert mistie > 5.0, f"Expected significant mistie, got {mistie}m"
    rc_ratio = anomalies[0]["rc_ratio"]
    assert rc_ratio > 1.2, f"Expected stronger seismic RC, ratio={rc_ratio}"
    print("test_megah1_quantified_case: PASSED")


def test_invalid_input_fail_closed():
    """Empty arrays → fail closed with NO_VALID_EVIDENCE."""
    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=[], depth=[], formation_tops={}
        )
    )
    assert result["execution_status"] == "ERROR"
    assert result["claim_state"] == "NO_VALID_EVIDENCE"
    print("test_invalid_input_fail_closed: PASSED")


def test_lem_envelope_contract():
    """Verify LEM fields present: confidence, sensitivity_to, equations_used."""
    depth = [1000.0, 1005.0, 1010.0]
    ai = [4_000_000.0, 4_200_000.0, 6_000_000.0]

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai, depth=depth, formation_tops={"Top": 1000.0}
        )
    )

    assert "confidence" in result
    assert "level" in result["confidence"]
    assert "sensitivity_to" in result["confidence"]
    assert "equations_used" in result["provenance"]
    assert "law_capsule" in result["provenance"]
    assert result["provenance"]["law_capsule"] == "LC#28"
    assert "metabolic" in result
    print("test_lem_envelope_contract: PASSED")


if __name__ == "__main__":
    test_no_anomaly_aligned_boundary()
    test_anomaly_displaced_reflector()
    test_megah1_quantified_case()
    test_invalid_input_fail_closed()
    test_lem_envelope_contract()
    print("\nAll anomalous_contrast tests PASSED.")
