"""
Test Anomalous Contrast Detector — LC#28 Verification
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
    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=[], depth=[], formation_tops={}
        )
    )
    assert "error" in result
    assert result["anomalies"] == []
    assert result["recommended_picks"] == []
    print("test_invalid_input_fail_closed: PASSED")


def test_plain_output_contract():
    """Verify clean output fields: no envelope, no claim_state, no metabolic."""
    depth = [1000.0, 1005.0, 1010.0]
    ai = [4_000_000.0, 4_200_000.0, 6_000_000.0]

    result = asyncio.run(
        geox_anomalous_contrast_detector(
            ai_profile=ai, depth=depth, formation_tops={"Top": 1000.0}
        )
    )

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


if __name__ == "__main__":
    test_no_anomaly_aligned_boundary()
    test_anomaly_displaced_reflector()
    test_megah1_quantified_case()
    test_invalid_input_fail_closed()
    test_plain_output_contract()
    print("\nAll anomalous_contrast tests PASSED.")
