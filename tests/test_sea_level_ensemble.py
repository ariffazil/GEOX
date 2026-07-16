"""
test_sea_level_ensemble.py — Dual-source sea-level ensemble tests.

Tests Miller 2020 + Haq & Ogg 2024 cross-validation, sequence boundary
registry, Sabah correlation, and physics consistency gate.

DITEMPA BUKAN DIBERI — Earth physics is forged, not given.
"""

from __future__ import annotations

import pytest


class TestSeaLevelEnsemble:
    """Test dual-source sea-level loader."""

    def test_miller_2020_loads(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_miller_2020

        est = load_miller_2020(0.0)
        assert est.source.value == "miller_2020"
        assert est.sea_level_m is not None

    def test_haq_ogg_2024_loads(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_haq_ogg_2024

        est = load_haq_ogg_2024(23.0)
        assert est.source.value == "haq_ogg_2024"
        assert est.sea_level_m is not None

    def test_ensemble_returns_both_sources(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sea_level_ensemble

        est = load_sea_level_ensemble(23.0)
        assert est.source.value == "ensemble"
        assert est.sea_level_m is not None
        assert est.agreement in ("AGREE", "DISAGREE")

    def test_ensemble_agreement_flag(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sea_level_ensemble

        est = load_sea_level_ensemble(23.0)
        assert est.agreement in ("AGREE", "DISAGREE", "SINGLE_SOURCE", "NO_DATA")

    def test_ensemble_citation_includes_both(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sea_level_ensemble

        est = load_sea_level_ensemble(23.0)
        assert "Miller" in est.source_citation
        assert "Haq" in est.source_citation


class TestSequenceBoundaries:
    """Test Haq & Ogg 2024 sequence boundary registry."""

    def test_loads_all_boundaries(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sequence_boundaries

        sbs = load_sequence_boundaries()
        assert len(sbs) > 30, f"Expected >30 SBs, got {len(sbs)}"

    def test_filters_by_age(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sequence_boundaries

        sbs = load_sequence_boundaries(age_min_ma=20, age_max_ma=25)
        assert all(20 <= s.age_ma <= 25 for s in sbs)

    def test_filters_by_amplitude(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sequence_boundaries

        sbs = load_sequence_boundaries(min_amplitude="major")
        assert all(s.amplitude == "major" for s in sbs)

    def test_mi1_at_23Ma_is_major(self):
        """Mi-1 (23 Ma) should be a major sequence boundary."""
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sequence_boundaries

        sbs = load_sequence_boundaries(age_min_ma=22.5, age_max_ma=23.5, min_amplitude="major")
        assert len(sbs) >= 1, "Mi-1 at ~23 Ma should be a major SB"

    def test_mmct_at_14Ma_is_major(self):
        """MMCT (14 Ma) should be a major sequence boundary."""
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sequence_boundaries

        sbs = load_sequence_boundaries(age_min_ma=13.5, age_max_ma=14.5, min_amplitude="major")
        assert len(sbs) >= 1, "MMCT at ~14 Ma should be a major SB"

    def test_oi1_at_34Ma_is_major(self):
        """Oi-1 (34 Ma) should be a major sequence boundary."""
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sequence_boundaries

        sbs = load_sequence_boundaries(age_min_ma=33.5, age_max_ma=34.5, min_amplitude="major")
        assert len(sbs) >= 1, "Oi-1 at ~34 Ma should be a major SB"


class TestSabahCorrelation:
    """Test Sabah unconformity correlation with Haq SBs."""

    def test_sabah_correlation_loads(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sabah_boundary_correlation

        corrs = load_sabah_boundary_correlation()
        assert len(corrs) == 4, f"Expected 4 Sabah surfaces, got {len(corrs)}"

    def test_bmu_correlates_with_mi1(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sabah_boundary_correlation

        corrs = load_sabah_boundary_correlation()
        bmu = next(c for c in corrs if c["sabah_surface"] == "BMU/TCU")
        assert bmu["correlation"] in ("STRONG", "MODERATE"), f"BMU/TCU correlation: {bmu['correlation']} (Δ={bmu['delta_ma']} Ma)"

    def test_dru_correlates_with_mmct(self):
        from geox_mcp.tools.deep_time.sea_level_ensemble import load_sabah_boundary_correlation

        corrs = load_sabah_boundary_correlation()
        dru = next(c for c in corrs if c["sabah_surface"] == "DRU")
        assert dru["correlation"] in ("STRONG", "MODERATE"), f"DRU correlation: {dru['correlation']} (Δ={dru['delta_ma']} Ma)"


class TestPhysicsConsistency:
    """Test physics consistency gate."""

    def test_consistent_warm_ice_free(self):
        from geox_mcp.tools.deep_time.physics_consistency import check_physics_consistency

        result = check_physics_consistency(
            age_ma=50.0,
            co2_ppm=1000,
            temp_anomaly_c=10.0,
            ice_extent="Ice-free (warm Eocene)",
            sea_level_m=60.0,
        )
        assert result.consistent, f"Should be consistent: {result.warnings}"

    def test_consistent_cold_has_ice(self):
        from geox_mcp.tools.deep_time.physics_consistency import check_physics_consistency

        result = check_physics_consistency(
            age_ma=0.0,
            co2_ppm=280,
            temp_anomaly_c=-1.0,
            ice_extent="Pleistocene glacial-interglacial cycles",
            sea_level_m=-10.0,
        )
        assert result.consistent, f"Should be consistent: {result.warnings}"

    def test_inconsistent_high_co2_with_ice(self):
        from geox_mcp.tools.deep_time.physics_consistency import check_physics_consistency

        result = check_physics_consistency(
            age_ma=15.0,
            co2_ppm=800,
            temp_anomaly_c=3.0,
            ice_extent="Quasi-permanent Antarctic ice sheet",
            sea_level_m=-20.0,
        )
        assert not result.consistent
        assert any("HIGH CO₂" in w for w in result.warnings)

    def test_inconsistent_ice_free_post_mmct(self):
        from geox_mcp.tools.deep_time.physics_consistency import check_physics_consistency

        result = check_physics_consistency(
            age_ma=10.0,
            co2_ppm=400,
            temp_anomaly_c=2.0,
            ice_extent="Ice-free (warm-house state)",
            sea_level_m=20.0,
        )
        assert not result.consistent
        assert any("post-MMCT" in w for w in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
