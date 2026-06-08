"""
Tests for geox_contrast_views — Band A raster-only contrast pipeline.

Phase 1 scope: amplitude_envelope, edge_map, texture_energy.
Phase 2 (planned): horizontal_gradient, vertical_gradient, local_dip,
                   phase_symmetry, frequency_content, ac_risk_heatmap.

Verifies F1-F13 compliance:
  F2 TRUTH    — outputs are CLAIM/HYPOTHESIS, never SEAL
  F4 CLARITY  — every attribute carries axis + normalization metadata
  F7 HUMILITY — outputs are PHYSICAL SIGNALS, not interpretations
  F9 ANTIHANTU — no "this IS a fault" — only "this is a gradient signal"
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path
_GEOX_SRC = Path("/root/geox/src")
if str(_GEOX_SRC) not in sys.path:
    sys.path.insert(0, str(_GEOX_SRC))

from geox_mcp.tools.contrast_views import (
    geox_contrast_views,
    _load_raster,
    _amplitude_envelope,
    _edge_map,
    _texture_energy,
    PHASE1_MODES,
    PHASE2_MODES,
    _MODE_REGISTRY,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def synthetic_faulted_section() -> np.ndarray:
    """Synthetic seismic-like image with:
    - 3 layered packages (different intensities = facies)
    - 1 vertical fault (sharp edge)
    - 1 angular unconformity (oblique bright reflector)
    - 1 chaotic zone (high variance = mass transport deposit)
    """
    np.random.seed(42)
    H, W = 128, 256
    img = np.zeros((H, W), dtype=np.float64)

    # Layered package 1 (shallow, low intensity)
    for row in range(0, 30):
        img[row, :] = 0.2 + 0.05 * np.sin(row * 0.5)

    # Bright unconformity at row 35
    img[34:36, :] = 0.8

    # Layered package 2 (medium intensity, between rows 40-80)
    for row in range(40, 80):
        img[row, :] = 0.5 + 0.1 * np.sin((row - 40) * 0.3)

    # Clinoform: oblique reflector
    for col in range(W):
        row = int(70 + 20 * (col / W))
        if 0 <= row < H:
            img[row, :] = 0.9
            if row + 1 < H:
                img[row + 1, :] = 0.6

    # Vertical fault at col 100 (sharp edge, large contrast across)
    img[:, 99] = 0.95
    img[:, 100] = 0.1

    # Chaotic zone (rows 100-115, cols 50-200)
    chaotic = np.random.RandomState(0).uniform(0.3, 0.9, (15, 150))
    img[100:115, 50:200] = chaotic

    # Add gaussian noise
    img += np.random.RandomState(1).normal(0, 0.02, img.shape)
    return np.clip(img, 0, 1)


@pytest.fixture
def saved_synthetic_path(tmp_path, synthetic_faulted_section):
    """Save the synthetic section to a temp file for the raster-loading path."""
    from PIL import Image

    arr8 = (synthetic_faulted_section * 255).astype(np.uint8)
    path = tmp_path / "synthetic_section.png"
    Image.fromarray(arr8, mode="L").save(path)
    return str(path)


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests — primitive kernels
# ─────────────────────────────────────────────────────────────────────────────


def test_amplitude_envelope_is_normalized_input(synthetic_faulted_section):
    out = _amplitude_envelope(synthetic_faulted_section)
    assert out.shape == synthetic_faulted_section.shape
    np.testing.assert_array_equal(out, synthetic_faulted_section)


def test_edge_map_detects_sharp_transitions(synthetic_faulted_section):
    """The vertical fault at col 99/100 should produce a strong edge signal."""
    out = _edge_map(synthetic_faulted_section, sigma=0.5)
    assert out.shape == synthetic_faulted_section.shape
    # Edge magnitude should be high at the fault column
    fault_col = out[:, 99:101].mean()
    smooth_col = out[:, 50:52].mean()
    assert fault_col > smooth_col, (
        f"Edge at fault (col 99-100) should be stronger than at smooth col: {fault_col:.4f} vs {smooth_col:.4f}"
    )


def test_edge_map_respects_sigma(synthetic_faulted_section):
    out_sharp = _edge_map(synthetic_faulted_section, sigma=0.1)
    out_smooth = _edge_map(synthetic_faulted_section, sigma=3.0)
    # Sharper sigma preserves more detail; smoother sigma suppresses small features
    # The sum of the edge map should be smaller with higher sigma
    assert out_smooth.sum() < out_sharp.sum()


def test_texture_energy_is_high_in_chaotic_zone(synthetic_faulted_section):
    """Chaotic zone (rows 100-115, cols 50-200) should have higher local
    variance than the layered package (rows 40-80)."""
    out = _texture_energy(synthetic_faulted_section, window=7)
    assert out.shape == synthetic_faulted_section.shape
    # Note: rows 100-115 are near the image edge; uniform_filter reflects
    # so the boundary doesn't drop variance artificially.
    chaotic_var = out[100:115, 50:200].mean()
    layered_var = out[40:80, 50:200].mean()
    assert chaotic_var > layered_var, (
        f"Chaotic zone should have higher local variance than layered: chaotic={chaotic_var:.5f} vs layered={layered_var:.5f}"
    )


def test_texture_energy_rejects_invalid_window():
    img = np.zeros((32, 32))
    with pytest.raises(ValueError, match="window must be odd"):
        _texture_energy(img, window=4)
    with pytest.raises(ValueError, match="window must be odd"):
        _texture_energy(img, window=2)


def test_load_raster_normalizes_to_unit_interval(synthetic_faulted_section):
    out = _load_raster(synthetic_faulted_section)
    assert out.min() >= 0.0
    assert out.max() <= 1.0


def test_load_raster_from_png(saved_synthetic_path):
    out = _load_raster(saved_synthetic_path)
    assert out.ndim == 2
    assert out.shape == (128, 256)
    assert 0.0 <= out.min() <= out.max() <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Async tool surface tests
# ─────────────────────────────────────────────────────────────────────────────


def test_default_modes_are_phase1(synthetic_faulted_section):
    """No `modes` arg → all 3 Phase 1 modes."""
    res = asyncio.run(geox_contrast_views(source=synthetic_faulted_section))
    assert res["governance_status"] == "QUALIFY"
    pa = res["primary_artifact"]
    assert pa["summary"]["n_attributes_requested"] == 3
    assert pa["summary"]["n_attributes_computed"] == 3
    returned_modes = {a["mode"] for a in pa["attributes"]}
    assert returned_modes == set(PHASE1_MODES)


def test_explicit_modes_subset(synthetic_faulted_section):
    res = asyncio.run(
        geox_contrast_views(
            source=synthetic_faulted_section,
            modes=["edge_map", "texture_energy"],
        )
    )
    pa = res["primary_artifact"]
    assert pa["summary"]["n_attributes_computed"] == 2
    assert {a["mode"] for a in pa["attributes"]} == {"edge_map", "texture_energy"}


def test_invalid_mode_returns_hold(synthetic_faulted_section):
    res = asyncio.run(
        geox_contrast_views(
            source=synthetic_faulted_section,
            modes=["amplitude_envelope", "non_existent_mode"],
        )
    )
    assert res["governance_status"] == "HOLD"
    assert res["primary_artifact"]["error_code"] == "INVALID_MODE"
    assert "non_existent_mode" in res["primary_artifact"]["message"]
    assert "amplitude_envelope" in res["primary_artifact"]["valid_modes"]


def test_multi_image_not_yet_supported():
    res = asyncio.run(geox_contrast_views(source=["/tmp/a.png", "/tmp/b.png"]))
    assert res["governance_status"] == "HOLD"
    assert res["primary_artifact"]["error_code"] == "MULTI_IMAGE_NOT_YET_SUPPORTED"


def test_raster_load_fail_returns_hold():
    res = asyncio.run(geox_contrast_views(source="/nonexistent/path/to.png"))
    assert res["governance_status"] == "HOLD"
    assert res["primary_artifact"]["error_code"] == "RASTER_LOAD_FAIL"


def test_loads_from_png_path(saved_synthetic_path):
    res = asyncio.run(geox_contrast_views(source=saved_synthetic_path))
    assert res["governance_status"] == "QUALIFY"
    assert res["primary_artifact"]["image_shape"] == [128, 256]


def test_every_attribute_carries_axis_and_provenance(synthetic_faulted_section):
    """F4 CLARITY: each attribute must carry axis + normalization metadata."""
    res = asyncio.run(geox_contrast_views(source=synthetic_faulted_section))
    for a in res["primary_artifact"]["attributes"]:
        assert "axis" in a
        assert "normalization" in a
        assert "computation" in a
        # Physical axis names (no "fault" or "horizon" — those are LLM interpretations)
        assert a["axis"] in {
            "reflection_strength",
            "structural_discontinuity",
            "seismic_facies_character",
        }


def test_every_attribute_has_summary_for_llm(synthetic_faulted_section):
    """Each attribute should have a compact summary (min/max/mean/percentiles)
    so an LLM can reason about the global signal without the full grid."""
    res = asyncio.run(geox_contrast_views(source=synthetic_faulted_section))
    for a in res["primary_artifact"]["attributes"]:
        assert "summary" in a
        s = a["summary"]
        for k in ("min", "max", "mean", "p50", "p95", "p99"):
            assert k in s
            assert isinstance(s[k], float)


def test_thumbnail_is_downsampled(synthetic_faulted_section):
    """Thumbnail should be <= 64x64 so it's LLM-friendly."""
    res = asyncio.run(geox_contrast_views(source=synthetic_faulted_section))
    for a in res["primary_artifact"]["attributes"]:
        thumb = np.array(a["thumbnail"])
        assert thumb.ndim == 2
        assert max(thumb.shape) <= 64


def test_verdict_qualify_on_clean_compute(synthetic_faulted_section):
    res = asyncio.run(geox_contrast_views(source=synthetic_faulted_section))
    assert res["governance_status"] == "QUALIFY"
    assert res["claim_state"] == "PLAUSIBLE"


def test_image_provenance_is_carried_through(synthetic_faulted_section):
    res = asyncio.run(
        geox_contrast_views(
            source=synthetic_faulted_section,
            image_provenance={
                "source": "PETRONAS 2024 KL2V1 TWT composite",
                "scale_bar_TWT_ms": [0, 4000],
                "crs": "TWT_ms",
                "well_ties": ["Kinabalu-1", "Layang-Layang-1"],
            },
            basin_context="Malay Basin — Sabah offshore",
        )
    )
    pa = res["primary_artifact"]
    assert pa["basin_context"] == "Malay Basin — Sabah offshore"
    assert pa["image_provenance"]["source"] == "PETRONAS 2024 KL2V1 TWT composite"


def test_phase2_modes_explicitly_rejected():
    """Phase 2 modes are documented in the road map but not yet implemented.
    The tool must fail closed if asked for them."""
    for m in PHASE2_MODES:
        res = asyncio.run(
            geox_contrast_views(
                source=np.zeros((64, 64)),
                modes=[m],
            )
        )
        assert res["governance_status"] == "HOLD", f"Phase 2 mode {m} should be rejected"
        assert res["primary_artifact"]["error_code"] == "INVALID_MODE", f"Phase 2 mode {m} should be in error"


def test_doctrine_8_missing_evidence_surface(synthetic_faulted_section):
    """When no provenance / basin_context supplied, Doctrine 8 missing_evidence
    must list what would improve confidence."""
    res = asyncio.run(geox_contrast_views(source=synthetic_faulted_section))
    missing = res["primary_artifact"]["summary"]["missing_evidence"]
    assert any("image_provenance" in m for m in missing)
    assert any("basin_context" in m for m in missing)


def test_failure_in_one_mode_doesnt_kill_others(monkeypatch, synthetic_faulted_section):
    """If one mode throws, the others should still surface. (audit primitive
    — you can see what worked and what didn't.)"""
    from geox_mcp.tools import contrast_views

    original = contrast_views._texture_energy

    def failing_kernel(img, **kwargs):
        raise RuntimeError("intentional failure for test")

    monkeypatch.setattr(contrast_views, "_texture_energy", failing_kernel)
    try:
        res = asyncio.run(geox_contrast_views(source=synthetic_faulted_section))
        pa = res["primary_artifact"]
        assert pa["summary"]["n_attributes_computed"] == 2
        assert pa["summary"]["n_attributes_failed"] == 1
        failed = [a for a in pa["attributes"] if "error" in a]
        assert len(failed) == 1
        assert failed[0]["mode"] == "texture_energy"
        assert "intentional failure" in failed[0]["error"]
    finally:
        monkeypatch.setattr(contrast_views, "_texture_energy", original)
