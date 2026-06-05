"""
Test Horizon Contrast Surface — ToAC-as-Attention Pipeline
Eureka GeoX Theory v2026.06.05
"""

from __future__ import annotations

import asyncio
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from geox_mcp.tools.horizon_contrast import (
    geox_horizon_contrast_surface,
    ATTENTION_QUERY_TEMPLATES,
    _compute_background_model,
    _compute_contrast_residuals,
    _attention_weighted_fusion,
    _extract_horizon_candidates,
)


def test_background_model():
    """Verify background model computes running stats correctly."""
    depth = list(np.arange(1000, 1100, 1.0, dtype=float))
    amplitude = list(1000.0 + 0.5 * np.arange(100, dtype=float))  # Linear trend
    coherence = list(0.8 + 0.01 * np.sin(np.arange(100, dtype=float) * 0.1))

    bg = _compute_background_model(
        {"amplitude": amplitude, "coherence": coherence},
        depth,
    )

    assert "background_model" in bg
    assert "amplitude" in bg["background_model"]
    assert "coherence" in bg["background_model"]
    assert "mean" in bg["background_model"]["amplitude"]
    assert "std" in bg["background_model"]["amplitude"]
    assert len(bg["background_model"]["amplitude"]["mean"]) == 100
    print("test_background_model: PASSED")


def test_contrast_residuals():
    """Verify residuals are zero for uniform data, non-zero for anomalies."""
    depth = list(np.arange(1000, 1100, 1.0))
    amplitude = [1.0] * 100  # Uniform — no contrast
    amplitude[50] = 3.0  # Spike at center

    bg = _compute_background_model({"amplitude": amplitude}, depth)
    residuals = _compute_contrast_residuals({"amplitude": amplitude}, bg)

    res = residuals["amplitude"]
    # Spike at index 50 should have high z-score
    assert res[50] > 2.0, f"Expected high residual at spike, got {res[50]}"
    # Background values near zero residual
    assert abs(res[0]) < 1.0, f"Expected near-zero residual in background, got {res[0]}"
    print("test_contrast_residuals: PASSED")


def test_attention_fusion():
    """Verify attention weights sum approximately to 1 and dominant attribute is correct."""
    depth = list(np.arange(1000, 1100, 1.0))
    residuals = {
        "amplitude": list(np.random.randn(100) * 2.0),
        "coherence": list(np.random.randn(100) * 0.5),
        "phase": list(np.random.randn(100) * 1.0),
    }

    query = {"amplitude": 0.6, "coherence": 0.3, "phase": 0.1}
    fusion = _attention_weighted_fusion(residuals, query, depth)

    assert "fused_contrast" in fusion
    assert len(fusion["fused_contrast"]) == 100
    assert "attention_weights" in fusion
    assert fusion["dominant_attribute"] == "amplitude"
    assert abs(sum(fusion["attention_weights"].values()) - 1.0) < 0.01
    print("test_attention_fusion: PASSED")


def test_candidate_extraction():
    """Verify peaks above threshold are detected."""
    depth = list(np.arange(1000, 1100, 1.0))
    fused = [0.0] * 100
    fused[25] = 3.0  # Strong peak
    fused[50] = 2.5  # Strong peak
    fused[75] = 1.0  # Below threshold

    candidates = _extract_horizon_candidates(fused, depth, peak_threshold=1.5, min_separation_m=10.0)

    assert len(candidates) == 2, f"Expected 2 candidates, got {len(candidates)}"
    depths = [c["depth_m"] for c in candidates]
    assert 1025.0 in depths, f"Missing peak at 1025m"
    assert 1050.0 in depths, f"Missing peak at 1050m"
    print("test_candidate_extraction: PASSED")


def test_full_pipeline_background_only():
    """Verify background_only mode returns without fusion."""
    depth = list(np.arange(1000, 1100, 1.0))
    amplitude = list(1000.0 + 0.5 * np.arange(100, dtype=float))

    result = asyncio.run(
        geox_horizon_contrast_surface(
            attribute_data={"amplitude": amplitude},
            depth=depth,
            mode="background_only",
            geological_query="sequence_boundary",
        )
    )

    # Envelope nests primary artifact under 'primary_artifact' key
    pa = result.get("primary_artifact", result)
    assert "background" in pa, f"background not found. Keys: {list(pa.keys())[:10]}"
    assert pa.get("mode") == "background_only"
    assert "fusion" not in pa
    assert "horizon_candidates" not in pa
    print("test_full_pipeline_background_only: PASSED")


def test_full_pipeline_with_well_ties():
    """Verify full pipeline with well ties produces governed output."""
    depth = list(np.arange(1000, 1100, 1.0))
    n = len(depth)

    np.random.seed(42)
    amplitude = list(2.0 + 0.01 * np.arange(n, dtype=float) + 0.3 * np.sin(np.arange(n) * 0.15))
    coherence = list(0.7 + 0.1 * np.random.randn(n))
    phase = list(np.random.randn(n) * 0.5)
    frequency = list(25.0 - 0.05 * np.arange(n, dtype=float) + 1.0 * np.random.randn(n))
    curvature = list(np.random.randn(n) * 0.3)

    # Add a contrast spike at ~1050m (index 50)
    amplitude[50] = 4.5
    coherence[50] = 0.2  # Low coherence = contrast
    phase[48:53] = [2.0] * 5

    result = asyncio.run(
        geox_horizon_contrast_surface(
            attribute_data={
                "amplitude": amplitude,
                "coherence": coherence,
                "phase": phase,
                "frequency": frequency,
                "curvature": curvature,
            },
            depth=depth,
            mode="full",
            geological_query="unconformity",
            well_ties={"Test_Horizon": 1052.0},
            peak_threshold=1.0,
            min_separation_m=15.0,
        )
    )

    # Verify pipeline outputs (nested under primary_artifact in the envelope)
    pa = result.get("primary_artifact", result)
    assert "background" in pa
    assert "contrast_residuals" in pa
    assert "fusion" in pa
    assert "horizon_candidates" in pa
    assert "geological_alignment" in pa

    # horizon_contrast is a top-level envelope key (added after get_standard_envelope)
    hc = result.get("horizon_contrast", {})
    assert "attention_equivalence" in hc
    assert "bias_audit" in hc
    assert "failure_modes" in hc
    assert "pipeline" in hc
    assert len(hc["pipeline"]) == 6

    # Verify bias audit exists
    ba = hc["bias_audit"]
    assert "alternative_queries_suggested" in ba
    assert len(ba["alternative_queries_suggested"]) > 0

    print("test_full_pipeline_with_well_ties: PASSED")


def test_attention_query_templates():
    """Verify all 8 query templates exist with valid attribute weights."""
    expected = [
        "unconformity",
        "flooding_surface",
        "carbonate_platform",
        "channel_system",
        "fault_zone",
        "fluid_contact",
        "sequence_boundary",
        "gas_sand",
    ]
    for name in expected:
        assert name in ATTENTION_QUERY_TEMPLATES, f"Missing template: {name}"
        t = ATTENTION_QUERY_TEMPLATES[name]
        assert "note" in t, f"Template {name} missing note"
        weights = {k: v for k, v in t.items() if k != "note"}
        assert len(weights) == 5, f"Template {name} has {len(weights)} attributes, expected 5"
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01, f"Template {name} weights sum to {total}, expected 1.0"
    print("test_attention_query_templates: PASSED")


def test_custom_query_override():
    """Verify custom query overrides template-based query."""
    depth = list(np.arange(1000, 1010, 1.0))
    amplitude = [1.0] * 10
    amplitude[5] = 3.0

    result = asyncio.run(
        geox_horizon_contrast_surface(
            attribute_data={"amplitude": amplitude},
            depth=depth,
            mode="full",
            geological_query="gas_sand",
            custom_query={"amplitude": 1.0},
        )
    )

    pa = result.get("primary_artifact", result)
    assert pa.get("query_source") == "custom"
    print("test_custom_query_override: PASSED")


if __name__ == "__main__":
    test_background_model()
    test_contrast_residuals()
    test_attention_fusion()
    test_candidate_extraction()
    test_full_pipeline_background_only()
    test_full_pipeline_with_well_ties()
    test_attention_query_templates()
    test_custom_query_override()
    print("\nAll horizon_contrast_surface tests PASSED — ToAC-as-Attention verified.")
