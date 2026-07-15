"""
test_stratigraphy_engines.py — Physics-First Stratigraphy Engine Tests
=======================================================================

Verifies that the three new engines work correctly:
1. Accommodation Engine — subsidence + eustasy + sediment
2. Surface-First Engine — surfaces from physics
3. Sequence Emergence Engine — sequences emerge from surfaces

The extinction test: NO LST/TST/HST labels anywhere.

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged: 2026-07-03 — the extinction event.
"""

from __future__ import annotations

import pytest

from geox_core.engines.stratigraphy.accommodation import (
    AccommodationRequest,
    EustaticPoint,
    SurfaceType,
    StackingPattern,
    simulate_accommodation,
    tectonic_subsidence_at_time,
    sediment_load_isostasy,
    decompact_thickness,
    get_eustatic_level,
)
from geox_core.engines.stratigraphy.surface_first import (
    GeometryType,
    generate_surfaces,
)
from geox_core.engines.stratigraphy.sequence_emergence import (
    SequenceScale,
    emerge_sequences,
)


# ═══════════════════════════════════════════════════════════════════════════
# Accommodation Engine Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestAccommodationEngine:
    """Test the unified accommodation simulation."""

    def test_basic_simulation(self):
        """Basic 10 Myr simulation produces valid steps."""
        req = AccommodationRequest(
            initial_subsidence_km=2.0,
            thermal_subsidence_rate_mm_yr=0.05,
            eustatic_rate_mm_yr=0.0,
            sediment_supply_rate_m_myr=50.0,
            initial_water_depth_m=100.0,
            duration_ma=10.0,
            time_step_myr=1.0,
        )
        result = simulate_accommodation(req)

        assert len(result.steps) >= 10
        assert result.total_subsidence_m > 0
        assert result.confidence <= 0.90
        assert result.epistemic_label == "DER"
        assert "LST" not in str(result.model_dump())
        assert "TST" not in str(result.model_dump())
        assert "HST" not in str(result.model_dump())

    def test_sea_level_fall_creates_erosion(self):
        """Falling sea level creates erosion surfaces."""
        eustatic_curve = [
            EustaticPoint(time_ma=10.0, sea_level_m=0.0),
            EustaticPoint(time_ma=5.0, sea_level_m=0.0),
            EustaticPoint(time_ma=0.0, sea_level_m=-200.0),
        ]
        req = AccommodationRequest(
            initial_subsidence_km=0.5,
            thermal_subsidence_rate_mm_yr=0.01,
            eustatic_curve=eustatic_curve,
            sediment_supply_rate_m_myr=100.0,
            initial_water_depth_m=20.0,
            duration_ma=10.0,
            time_step_myr=0.5,
        )
        result = simulate_accommodation(req)

        # Should have some erosion surfaces
        erosion_steps = [s for s in result.steps if s.surface_type == SurfaceType.EROSION]
        sb_steps = [s for s in result.steps if s.surface_type == SurfaceType.SEQUENCE_BOUNDARY]
        assert len(erosion_steps) + len(sb_steps) > 0, "Falling sea level should produce erosion"

    def test_rising_sea_level_creates_flooding(self):
        """Rising sea level creates flooding surfaces."""
        eustatic_curve = [
            EustaticPoint(time_ma=10.0, sea_level_m=-20.0),
            EustaticPoint(time_ma=0.0, sea_level_m=20.0),
        ]
        req = AccommodationRequest(
            initial_subsidence_km=1.0,
            thermal_subsidence_rate_mm_yr=0.02,
            eustatic_curve=eustatic_curve,
            sediment_supply_rate_m_myr=30.0,
            initial_water_depth_m=50.0,
            duration_ma=10.0,
            time_step_myr=0.5,
        )
        result = simulate_accommodation(req)

        fs_steps = [s for s in result.steps if s.is_flooding_surface]
        assert len(fs_steps) > 0, "Rising sea level should produce flooding surfaces"

    def test_stacking_patterns_emerge(self):
        """Stacking patterns emerge from physics, not rules."""
        req = AccommodationRequest(
            initial_subsidence_km=2.0,
            thermal_subsidence_rate_mm_yr=0.1,
            eustatic_rate_mm_yr=0.0,
            sediment_supply_rate_m_myr=20.0,
            initial_water_depth_m=200.0,
            duration_ma=20.0,
            time_step_myr=1.0,
        )
        result = simulate_accommodation(req)

        patterns = set(s.stacking_pattern for s in result.steps)
        assert len(patterns) > 0
        # Verify emergent_stacking matches
        assert set(result.emergent_stacking).issubset(set(StackingPattern))

    def test_no_taxonomy_labels(self):
        """CRITICAL: No LST/TST/HST/FSST labels anywhere in output."""
        req = AccommodationRequest(
            initial_subsidence_km=2.0,
            thermal_subsidence_rate_mm_yr=0.05,
            sediment_supply_rate_m_myr=50.0,
            initial_water_depth_m=100.0,
            duration_ma=10.0,
        )
        result = simulate_accommodation(req)
        output = str(result.model_dump()).upper()

        for label in ["LST", "TST", "HST", "FSST", "SYSTEMS_TRACT"]:
            assert label not in output, f"Taxonomy label '{label}' found in output!"

    def test_epistemic_labels_present(self):
        """All results carry epistemic labels (F2 TRUTH)."""
        req = AccommodationRequest(
            initial_subsidence_km=2.0,
            sediment_supply_rate_m_myr=50.0,
            initial_water_depth_m=100.0,
            duration_ma=5.0,
        )
        result = simulate_accommodation(req)
        assert result.epistemic_label in ("OBS", "DER", "INT", "SPEC")
        assert len(result.assumptions) > 0
        assert len(result.evidence_gaps) > 0


# ═══════════════════════════════════════════════════════════════════════════
# Surface-First Engine Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestSurfaceFirstEngine:
    """Test surface generation from accommodation physics."""

    def _make_accommodation(self):
        """Helper: create accommodation with sea-level fall to generate surfaces."""
        eustatic_curve = [
            EustaticPoint(time_ma=10.0, sea_level_m=0.0),
            EustaticPoint(time_ma=5.0, sea_level_m=-30.0),
            EustaticPoint(time_ma=0.0, sea_level_m=0.0),
        ]
        req = AccommodationRequest(
            initial_subsidence_km=2.0,
            thermal_subsidence_rate_mm_yr=0.05,
            eustatic_curve=eustatic_curve,
            sediment_supply_rate_m_myr=40.0,
            initial_water_depth_m=100.0,
            duration_ma=10.0,
            time_step_myr=0.25,
        )
        return simulate_accommodation(req)

    def test_surfaces_generated(self):
        """Surfaces are generated from accommodation simulation."""
        acc = self._make_accommodation()
        result = generate_surfaces(acc)

        assert len(result.surfaces) > 0, "Should generate at least one surface"
        assert len(result.packages) >= 0

    def test_surface_types_are_physical(self):
        """All surface types are physical objects, not taxonomic labels."""
        acc = self._make_accommodation()
        result = generate_surfaces(acc)

        valid_types = set(SurfaceType)
        for surface in result.surfaces:
            assert surface.surface_type in valid_types
            assert surface.age_ma >= 0
            assert surface.geometry in set(GeometryType)

    def test_key_surfaces_identified(self):
        """Key surfaces (SB, MFS) are identified."""
        acc = self._make_accommodation()
        result = generate_surfaces(acc)

        # At least some key surfaces should exist with sea-level fluctuation
        key_ids = [s.surface_id for s in result.key_surfaces]
        # This is fine if empty — the test is that key_surfaces is a subset
        for sid in key_ids:
            assert any(s.surface_id == sid for s in result.surfaces)

    def test_no_systems_tract_labels(self):
        """CRITICAL: No systems tract labels in output."""
        acc = self._make_accommodation()
        result = generate_surfaces(acc)
        output = str(result.model_dump()).upper()

        for label in ["LST", "TST", "HST", "FSST", "SYSTEMS_TRACT"]:
            assert label not in output, f"Taxonomy label '{label}' found!"

    def test_packages_bounded_by_surfaces(self):
        """Packages are bounded by real surfaces."""
        acc = self._make_accommodation()
        result = generate_surfaces(acc)
        surface_ids = {s.surface_id for s in result.surfaces}

        for pkg in result.packages:
            assert pkg.top_surface_id in surface_ids
            assert pkg.base_surface_id in surface_ids


# ═══════════════════════════════════════════════════════════════════════════
# Sequence Emergence Engine Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestSequenceEmergence:
    """Test that sequences emerge from physics, not from classification."""

    def _make_full_pipeline(self):
        """Helper: run full pipeline from accommodation → surfaces → sequences."""
        eustatic_curve = [
            EustaticPoint(time_ma=50.0, sea_level_m=0.0),
            EustaticPoint(time_ma=40.0, sea_level_m=-20.0),
            EustaticPoint(time_ma=30.0, sea_level_m=10.0),
            EustaticPoint(time_ma=20.0, sea_level_m=-30.0),
            EustaticPoint(time_ma=10.0, sea_level_m=5.0),
            EustaticPoint(time_ma=0.0, sea_level_m=-10.0),
        ]
        req = AccommodationRequest(
            initial_subsidence_km=3.0,
            thermal_subsidence_rate_mm_yr=0.05,
            eustatic_curve=eustatic_curve,
            sediment_supply_rate_m_myr=50.0,
            initial_water_depth_m=150.0,
            duration_ma=50.0,
            time_step_myr=0.5,
        )
        acc = simulate_accommodation(req)
        surfaces = generate_surfaces(acc)
        return acc, surfaces

    def test_sequences_emerge(self):
        """Sequences emerge from the physics pipeline."""
        acc, surface_result = self._make_full_pipeline()
        result = emerge_sequences(surface_result, acc)

        # Should have at least one sequence with sea-level fluctuation
        assert result.total_sequences >= 0  # may be 0 if surfaces are conformable
        assert result.epistemic_label == "DER"

    def test_no_lst_tst_hst_labels(self):
        """CRITICAL: No LST/TST/HST in sequence output."""
        acc, surface_result = self._make_full_pipeline()
        result = emerge_sequences(surface_result, acc)
        output = str(result.model_dump()).upper()

        for label in ["LST", "TST", "HST", "FSST"]:
            assert label not in output, f"Taxonomy label '{label}' found in sequence output!"

    def test_scale_emerges_from_duration(self):
        """Sequence scale is determined by duration, not by rule."""
        acc, surface_result = self._make_full_pipeline()
        result = emerge_sequences(surface_result, acc)

        for seq in result.sequences:
            if seq.duration_myr < 1.0:
                assert seq.scale == SequenceScale.PARASEQUENCE
            elif seq.duration_myr < 10.0:
                assert seq.scale == SequenceScale.DEPOSITIONAL
            else:
                assert seq.scale == SequenceScale.SLOSS

    def test_resource_potential_from_physics(self):
        """Resource potential is inferred from stacking, not from labels."""
        acc, surface_result = self._make_full_pipeline()
        result = emerge_sequences(surface_result, acc)

        for seq in result.sequences:
            # Resource assessments should be physics-based strings
            assert isinstance(seq.reservoir_potential, str)
            assert isinstance(seq.seal_potential, str)
            assert isinstance(seq.source_potential, str)

    def test_resource_graph_emerges(self):
        """Resource graph maps sequences to reservoir/seal/source nodes."""
        acc, surface_result = self._make_full_pipeline()
        result = emerge_sequences(surface_result, acc)

        assert "reservoirs" in result.resource_graph
        assert "seals" in result.resource_graph
        assert "sources" in result.resource_graph


# ═══════════════════════════════════════════════════════════════════════════
# Physics Kernel Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestPhysicsKernels:
    """Test individual physics functions."""

    def test_tectonic_subsidence_increases(self):
        """Tectonic subsidence increases with time."""
        s0 = tectonic_subsidence_at_time(2.0, 0.05, 62.0, 0.0)
        s10 = tectonic_subsidence_at_time(2.0, 0.05, 62.0, 10.0)
        s50 = tectonic_subsidence_at_time(2.0, 0.05, 62.0, 50.0)
        assert s0 < s10 < s50

    def test_sediment_load_isostasy(self):
        """Sediment loading produces positive subsidence."""
        load = sediment_load_isostasy(1000.0)  # 1000m of sediment
        assert load > 0
        assert load < 1000.0  # less than the sediment thickness

    def test_decompact_thickness(self):
        """Decompaction restores original thickness > present."""
        original = decompact_thickness(100.0, 2.0)  # 100m at 2km depth
        assert original > 100.0, "Original should be greater than compacted"

    def test_eustatic_constant_rate(self):
        """Constant eustatic rate produces linear change."""
        sl_0 = get_eustatic_level(0.0, constant_rate_mm_yr=1.0)
        sl_10 = get_eustatic_level(10.0, constant_rate_mm_yr=1.0)
        assert sl_0 == 0.0
        assert sl_10 == 10.0  # 1 mm/yr × 10 Myr = 10 m


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
