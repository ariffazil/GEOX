"""Known-answer tests for geox_model flexure + physics_section + critical_taper modes."""
import pytest
from geox_mcp.tools.model_physics import compute_flexure, critical_taper_reference


class TestFlexure:
    """Validated against session-computed table (2026-10-06, Copilot+333-AGI)."""

    def test_te10_sediment_continuous(self):
        r = compute_flexure(te_km=10, infill="sediment", plate="continuous")
        row = r["results"][0]
        assert row["te_km"] == 10
        assert abs(row["forebulge_distance_km"] - 129) < 3   # 128.7

    def test_te10_sediment_broken(self):
        r = compute_flexure(te_km=10, infill="sediment", plate="broken")
        assert abs(r["results"][0]["forebulge_distance_km"] - 97) < 3   # 96.7

    def test_te5_water_continuous(self):
        r = compute_flexure(te_km=5, infill="water", plate="continuous")
        assert abs(r["results"][0]["forebulge_distance_km"] - 61) < 3   # 60.7

    def test_te5_water_broken(self):
        r = compute_flexure(te_km=5, infill="water", plate="broken")
        assert abs(r["results"][0]["forebulge_distance_km"] - 46) < 3   # 45.5

    def test_te15_sediment_continuous(self):
        r = compute_flexure(te_km=15, infill="sediment", plate="continuous")
        assert abs(r["results"][0]["forebulge_distance_km"] - 174) < 4  # 174.2

    def test_te30_sediment_continuous(self):
        r = compute_flexure(te_km=30, infill="sediment", plate="continuous")
        assert abs(r["results"][0]["forebulge_distance_km"] - 293) < 5  # 293.4

    def test_sweep_returns_table(self):
        r = compute_flexure(te_km=[5, 10, 15, 20, 30])
        assert len(r["results"]) == 5

    def test_default_sweep(self):
        r = compute_flexure()
        assert len(r["results"]) == 5

    def test_invalid_infill(self):
        with pytest.raises(ValueError):
            compute_flexure(infill="magma")

    def test_invalid_plate(self):
        with pytest.raises(ValueError):
            compute_flexure(plate="quantum")


class TestCriticalTaper:
    def test_reference_gated(self):
        r = critical_taper_reference()
        assert r["status"] == "REFERENCE_GATED"
        assert len(r["references"]) >= 3
        assert "known_answer_for_test" in r
