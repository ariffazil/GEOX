"""
Tests for spatial_block module (Eureka 2026-06-05, Burlamaque 2026-06-04 Step 3).

Verifies:
- Empty / invalid input handling
- Spatial block + fold assignment
- Synthetic dataset (clear spatial autocorrelation) shows gap > 1.0
- Random dataset (no spatial structure) shows gap ≈ 1.0
- Verdict mapping (gap_ratio thresholds)

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import math
import random
from typing import Any

import pytest

from geox_mcp.tools.spatial_block import (
    _assign_blocks,
    _assign_folds,
    _haversine_km,
    _percentiles,
    run_spatial_block_validate,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Unit tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_haversine_zero():
    assert _haversine_km(0.0, 0.0, 0.0, 0.0) == 0.0


def test_haversine_one_degree_latitude_approx_111km():
    # 1 degree of latitude ~ 111 km
    d = _haversine_km(0.0, 0.0, 1.0, 0.0)
    assert 110.0 < d < 112.0


def test_assign_blocks_returns_consistent_ids():
    coords = [
        (3.0, 101.0),
        (3.001, 101.0),  # same block as above
        (3.5, 101.5),  # different block
    ]
    blocks = _assign_blocks(coords, block_size_km=5.0)
    assert blocks[0] == blocks[1]
    assert blocks[0] != blocks[2]
    assert len(set(blocks)) == 2


def test_assign_folds_round_robin():
    block_ids = [0, 0, 1, 1, 2, 2, 3, 3]
    folds = _assign_folds(block_ids, n_folds=4)
    # All samples in same block must be in same fold
    for bid in {0, 1, 2, 3}:
        block_folds = [folds[i] for i, b in enumerate(block_ids) if b == bid]
        assert len(set(block_folds)) == 1
    # All 4 folds used
    assert set(folds) == {0, 1, 2, 3}


def test_assign_folds_raises_for_too_few():
    with pytest.raises(ValueError):
        _assign_folds([0, 1, 2], n_folds=1)


def test_percentiles_basic():
    p = _percentiles([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert p["p10"] == pytest.approx(1.9, rel=0.05)
    assert p["p50"] == pytest.approx(5.5, rel=0.05)
    assert p["p90"] == pytest.approx(9.1, rel=0.05)


def test_percentiles_empty():
    p = _percentiles([])
    assert p == {"p10": 0.0, "p50": 0.0, "p90": 0.0}


def test_gini_safe_returns_0_for_empty():
    # Stub: gini lives in prospect.py (not spatial_block). Just verify import path is clean.
    from geox_mcp.tools.prospect import _gini_coefficient

    assert _gini_coefficient([]) == 0.0
    assert _gini_coefficient([0, 0, 0]) == 0.0
    # Perfect equality
    assert _gini_coefficient([1, 1, 1, 1]) == 0.0
    # Max inequality
    assert _gini_coefficient([0, 0, 0, 1]) > 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# Integration tests with synthetic data
# ═══════════════════════════════════════════════════════════════════════════════


def _make_spatially_correlated_samples(n: int = 200, seed: int = 42) -> list[dict[str, Any]]:
    """Generate samples with strong spatial autocorrelation.

    Cluster 0 (south): feature_x ∈ [-1, -0.5]
    Cluster 1 (north): feature_x ∈ [0.5, 1.0]
    No overlap in feature space between clusters.

    With spatial block holdout, the RF only sees one cluster's feature
    range and must extrapolate to the other — high RMSE.
    With random holdout, train and test both see mixed feature_x ranges
    — good interpolation, low RMSE.
    """
    rng = random.Random(seed)
    samples = []
    for i in range(n):
        cluster = i % 2
        lat = 3.0 + cluster * 1.0  # ~111 km apart
        lon = 101.0 + rng.uniform(-0.1, 0.1)
        # Strong separation in feature space
        if cluster == 0:
            feature_x = -0.75 + rng.uniform(-0.25, 0.25)  # [-1.0, -0.5]
        else:
            feature_x = 0.75 + rng.uniform(-0.25, 0.25)  # [0.5, 1.0]
        # value depends on feature_x (so model can learn)
        value = 5.0 * feature_x + rng.gauss(0, 0.1)
        samples.append(
            {
                "lat": lat,
                "lon": lon,
                "value": value,
                "feature_x": feature_x,
                "feature_noise": rng.gauss(0, 1),
            }
        )
    return samples


def _make_random_samples(n: int = 200, seed: int = 42) -> list[dict[str, Any]]:
    """Generate samples with NO spatial structure.

    feature_x and value are independent of lat/lon. Both spatial-CV
    and random-CV should generalize equally well.
    """
    rng = random.Random(seed)
    samples = []
    for i in range(n):
        lat = rng.uniform(0.0, 5.0)
        lon = rng.uniform(100.0, 105.0)
        feature_x = rng.gauss(0, 1)
        # value depends on feature_x (so model CAN learn), but no spatial structure
        value = 2.0 * feature_x + rng.gauss(0, 0.3)
        samples.append(
            {
                "lat": lat,
                "lon": lon,
                "value": value,
                "feature_x": feature_x,
                "feature_noise": rng.gauss(0, 1),
            }
        )
    return samples


def test_empty_input_returns_void():
    res = run_spatial_block_validate([])
    assert res["verdict"] == "VOID"
    assert "error" in res


def test_too_few_samples_returns_void():
    samples = [{"lat": 3.0, "lon": 101.0, "value": 1.0}]
    res = run_spatial_block_validate(samples)
    assert res["verdict"] == "VOID"


def test_spatially_correlated_data_shows_gap():
    """When data is spatially clustered, spatial-CV should be much worse than random-CV.

    Uses block_size_km=30 to ensure each cluster fits in a single block,
    forcing the surrogate RF to extrapolate to held-out feature space.
    """
    samples = _make_spatially_correlated_samples(n=200, seed=42)
    res = run_spatial_block_validate(
        samples,
        block_size_km=30.0,  # 30km block = 1 cluster per block
        n_folds=4,
    )
    # The verdict for spatially-correlated data should NOT be SEAL
    # (we are NOT in a position to claim clean generalization)
    assert res["verdict"] in ("HOLD", "VOID", "QUALIFY"), f"Expected spatial hold/void, got {res['verdict']}"
    # The key invariant: gap_ratio > 1.5 means spatial-CV is materially
    # harder than random-CV — the article's whole point
    assert res["spatial_gap_ratio"] > 1.5, f"Expected gap_ratio > 1.5, got {res['spatial_gap_ratio']}"
    assert res["n_blocks"] >= 2
    assert res["n_samples"] == 200


def test_random_data_shows_no_gap():
    """When data has no spatial structure, gap_ratio should be close to 1.0."""
    samples = _make_random_samples(n=300, seed=42)
    res = run_spatial_block_validate(
        samples,
        block_size_km=10.0,
        n_folds=4,
    )
    # Random data should generalize equally well spatially
    assert res["spatial_gap_ratio"] < 1.5
    # Should SEAL or QUALIFY
    assert res["verdict"] in ("SEAL", "QUALIFY", "HOLD")


def test_invalid_coordinates_filtered():
    """Samples with invalid lat/lon should be filtered out."""
    samples = [
        {"lat": 91.0, "lon": 0.0, "value": 1.0},  # invalid lat
        {"lat": 0.0, "lon": 181.0, "value": 1.0},  # invalid lon
    ] + _make_random_samples(n=100, seed=1)
    res = run_spatial_block_validate(samples)
    # Should still produce a result, filtering the bad coords
    assert res["n_samples"] >= 95  # some may be filtered
    assert "verdict" in res


def test_block_reliability_capped_at_20():
    """block_reliability should cap at 20 entries to keep envelope small."""
    samples = _make_random_samples(n=500, seed=42)
    res = run_spatial_block_validate(samples, block_size_km=1.0)
    assert "block_reliability" in res
    assert len(res["block_reliability"]) <= 20


def test_returns_receipt_fields():
    """All required receipt fields present."""
    samples = _make_random_samples(n=100, seed=42)
    res = run_spatial_block_validate(samples)
    for k in (
        "verdict",
        "verdict_reason",
        "n_samples",
        "n_blocks",
        "n_folds",
        "block_size_km",
        "feature_keys",
        "per_fold_rmse",
        "per_fold_r2",
        "spatial_cv_rmse",
        "random_cv_rmse",
        "spatial_gap_p10_p50_p90",
        "spatial_gap_ratio",
    ):
        assert k in res, f"Missing receipt field: {k}"


def test_max_samples_downsampling():
    """When n > max_samples, downsampling is applied deterministically."""
    samples = _make_random_samples(n=1000, seed=42)
    res = run_spatial_block_validate(samples, max_samples=200, block_size_km=50.0)
    # n_samples may be < max_samples after invalid coord filter
    assert res["n_samples"] <= 200
    assert res["n_samples_total"] == 1000
