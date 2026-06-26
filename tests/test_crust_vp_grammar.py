"""
test_crust_vp_grammar.py — Tests for the Huang 2021 Vp crust-type grammar
═══════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Verifies the Vp-based classification function against the canonical Huang
et al. (2021) zones, including Sabah-specific test cases for the
Layang-Layang ⇄ Kinabalu interface.
"""
from __future__ import annotations

import pytest

from geox_core.schemas.crust_vp_grammar import (
    CrustClassification,
    CrustColumn,
    CrustZone,
    DUCTILE_DEPTH_BOT_KM,
    DUCTILE_DEPTH_TOP_KM,
    DUCTILE_VP_TOP_THRESHOLD,
    HYPERTHINNED_THICKNESS_KM,
    HVL_VP_THRESHOLD,
    LOWER_CRUST_VP_MAX,
    NORMAL_CONTINENTAL_THICKNESS_KM,
    NORMAL_CONTINENTAL_VP_MAX,
    NORMAL_CONTINENTAL_VP_MIN,
    SERPENTINIZED_HEATFLOW_MW_M2,
    SERPENTINIZED_VP,
    STRETCHED_LOWER_CRUST_VP,
    STRETCHED_THICKNESS_KM,
    STRETCHED_UPPER_CRUST_VP_MAX,
    VpObservation,
    classify_column,
    vp_zone_classify,
)


# ═══════════════════════════════════════════════════════════════════════════════
# F2 TRUTH — Huang 2021 canonical zone signatures
# ═══════════════════════════════════════════════════════════════════════════════


class TestHuangCanonicalZones:
    """Each Huang 2021 zone, verified against its canonical Vp signature."""

    def test_xisha_bank_normal_continental(self) -> None:
        c = vp_zone_classify(vp_km_s=5.5, crust_thickness_km=25.0)
        assert c.zone == CrustZone.NORMAL_CONTINENTAL
        assert c.confidence >= 0.70

    def test_xisha_trough_stretched_continental(self) -> None:
        c = vp_zone_classify(vp_km_s=5.8, crust_thickness_km=12.0)
        assert c.zone == CrustZone.STRETCHED_CONTINENTAL
        assert c.confidence >= 0.60

    def test_zhongsha_trough_failed_rift_ductile(self) -> None:
        c = vp_zone_classify(
            vp_km_s=6.0,
            crust_thickness_km=10.0,
            depth_km=10.0,
        )
        assert c.zone == CrustZone.DUCTILE_MID_CRUSTAL
        assert c.confidence >= 0.80

    def test_zhongshanan_oct_hyperthinned(self) -> None:
        c = vp_zone_classify(vp_km_s=6.5, crust_thickness_km=6.0)
        assert c.zone == CrustZone.HYPERTHINNED_OCT
        assert c.confidence >= 0.70

    def test_zhongshanan_serpentinized_mantle(self) -> None:
        c = vp_zone_classify(
            vp_km_s=7.7,
            crust_thickness_km=6.0,
            heat_flow_mw_m2=50.0,
        )
        assert c.zone == CrustZone.SERPENTINIZED_MANTLE
        assert c.confidence >= 0.80

    def test_zhongsha_lower_crust_magmatic(self) -> None:
        c = vp_zone_classify(vp_km_s=7.0, crust_thickness_km=15.0)
        assert c.zone == CrustZone.LOWER_CRUST_MAGMATIC
        assert c.confidence >= 0.60


# ═══════════════════════════════════════════════════════════════════════════════
# F2 TRUTH — Edge cases + boundary conditions
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_sediment_vp_returns_unknown(self) -> None:
        c = vp_zone_classify(vp_km_s=3.0, crust_thickness_km=1.0)
        assert c.zone == CrustZone.UNKNOWN
        assert c.confidence <= 0.20

    def test_sub_moho_vp_returns_unknown(self) -> None:
        c = vp_zone_classify(vp_km_s=8.7, crust_thickness_km=30.0)
        assert c.zone == CrustZone.UNKNOWN
        assert c.confidence <= 0.20

    def test_oceanic_layer3_with_thin_crust(self) -> None:
        # Vp 7.5 in thin crust → oceanic crust (layer 3), not hyperthinned
        c = vp_zone_classify(vp_km_s=7.5, crust_thickness_km=5.0)
        assert c.zone == CrustZone.OCEANIC_CRUST

    def test_oceanic_layer2_in_hyperthinned_oct(self) -> None:
        # Vp 4.0 in thin crust → hyperthinned OCT (layer 2)
        c = vp_zone_classify(vp_km_s=4.0, crust_thickness_km=5.0)
        assert c.zone == CrustZone.HYPERTHINNED_OCT

    def test_high_vp_oct_returns_oceanic_not_hyperthinned(self) -> None:
        # Vp > 7.0 in thin crust → oceanic (rule 4 has Vp cap)
        c = vp_zone_classify(vp_km_s=7.55, crust_thickness_km=7.0)
        assert c.zone == CrustZone.OCEANIC_CRUST

    def test_serpentinized_window_lower_bound(self) -> None:
        c = vp_zone_classify(
            vp_km_s=7.6,
            crust_thickness_km=7.0,
            heat_flow_mw_m2=55.0,
        )
        assert c.zone == CrustZone.SERPENTINIZED_MANTLE

    def test_serpentinized_window_upper_bound(self) -> None:
        c = vp_zone_classify(
            vp_km_s=7.9,
            crust_thickness_km=6.0,
            heat_flow_mw_m2=60.0,
        )
        assert c.zone == CrustZone.SERPENTINIZED_MANTLE

    def test_just_below_serpentinized_window_is_oceanic(self) -> None:
        c = vp_zone_classify(vp_km_s=7.55, crust_thickness_km=7.0)
        assert c.zone == CrustZone.OCEANIC_CRUST


# ═══════════════════════════════════════════════════════════════════════════════
# F7 HUMILITY — confidence floor
# ═══════════════════════════════════════════════════════════════════════════════


class TestHumilityCap:
    def test_no_classification_above_0_90(self) -> None:
        """No classification should ever exceed 0.90 (F7 floor)."""
        test_vps = [4.0, 5.0, 5.5, 5.8, 6.0, 6.5, 7.0, 7.5, 7.7, 8.0]
        test_thicks = [5.0, 10.0, 15.0, 22.0, 30.0]
        for vp in test_vps:
            for thick in test_thicks:
                c = vp_zone_classify(vp_km_s=vp, crust_thickness_km=thick)
                assert c.confidence <= 0.90, (
                    f"F7 VIOLATION: vp={vp}, thick={thick}, conf={c.confidence}"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# F4 CLARITY — Pydantic envelope validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestPydanticEnvelope:
    def test_classification_no_extra_fields(self) -> None:
        with pytest.raises(Exception):
            CrustClassification(
                zone=CrustZone.NORMAL_CONTINENTAL,
                confidence=0.5,
                rogue_field="not_allowed",  # type: ignore[call-arg]
            )

    def test_vp_observation_validates_range(self) -> None:
        with pytest.raises(Exception):
            VpObservation(vp_km_s=15.0, depth_km=5.0)  # too fast

    def test_vp_observation_validates_minimum(self) -> None:
        with pytest.raises(Exception):
            VpObservation(vp_km_s=0.5, depth_km=5.0)  # too slow

    def test_classification_has_alternatives(self) -> None:
        """F4 CLARITY — no single-hypothesis classification."""
        c = vp_zone_classify(vp_km_s=6.5, crust_thickness_km=6.0)
        assert len(c.alternative_zones) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Sabah-specific cases — Layang-Layang ⇄ Kinabalu
# ═══════════════════════════════════════════════════════════════════════════════


class TestSabahKinabaluCases:
    """Conjectured Vp signatures for Sabah basins derived from conjugate
    margin logic. These are INT-grade (interpreted) until OBS data arrives."""

    def test_kinabalu_inboard_normal_continental(self) -> None:
        # Dangerous Grounds inboard — thick continental ~30 km
        c = vp_zone_classify(vp_km_s=6.2, crust_thickness_km=30.0)
        assert c.zone == CrustZone.NORMAL_CONTINENTAL

    def test_layang_layang_mid_crust_ductile(self) -> None:
        # Layang-Layang mid-crust (predicted ductile layer ~9 km depth)
        c = vp_zone_classify(
            vp_km_s=5.9,
            crust_thickness_km=8.0,
            depth_km=9.0,
        )
        assert c.zone == CrustZone.DUCTILE_MID_CRUSTAL

    def test_nw_sabah_trough_hyperthinned(self) -> None:
        # NW Sabah trough → OCT-equivalent
        c = vp_zone_classify(vp_km_s=6.4, crust_thickness_km=7.0)
        assert c.zone == CrustZone.HYPERTHINNED_OCT

    def test_nw_sabah_wedge_serpentinized(self) -> None:
        # If refraction finds Vp ~7.7 under NW Sabah wedge
        c = vp_zone_classify(
            vp_km_s=7.7,
            crust_thickness_km=5.0,
            heat_flow_mw_m2=55.0,
        )
        assert c.zone == CrustZone.SERPENTINIZED_MANTLE


# ═══════════════════════════════════════════════════════════════════════════════
# classify_column — convenience function
# ═══════════════════════════════════════════════════════════════════════════════


class TestColumnClassification:
    def test_classify_zhongsha_trough_column(self) -> None:
        """Reconstruct Zhongsha Trough column from Vp observations."""
        column = CrustColumn(
            name="zhongsha_trough_test",
            basin_context="Zhongsha Trough (Huang 2021 analog)",
            observations=[
                VpObservation(
                    vp_km_s=4.5,
                    depth_km=2.0,
                    source="OBS2013-1",
                    method="wide-angle refraction",
                ),
                VpObservation(
                    vp_km_s=5.8,
                    depth_km=6.0,
                    source="OBS2013-1",
                    method="wide-angle refraction",
                ),
                VpObservation(
                    vp_km_s=6.3,
                    depth_km=10.0,
                    source="OBS2013-1",
                    method="wide-angle refraction",
                ),
                VpObservation(
                    vp_km_s=6.7,
                    depth_km=14.0,
                    source="OBS2013-1",
                    method="wide-angle refraction",
                ),
                VpObservation(
                    vp_km_s=8.0,
                    depth_km=20.0,
                    source="OBS2013-1",
                    method="wide-angle refraction",
                ),
            ],
        )
        result = classify_column(column)
        assert len(result.classifications) == 5
        # Each classification should be valid
        for c in result.classifications:
            assert isinstance(c, CrustClassification)
            assert c.zone in CrustZone

    def test_classify_returns_new_column(self) -> None:
        """classify_column should not mutate input."""
        column = CrustColumn(
            name="t",
            basin_context="t",
            observations=[
                VpObservation(vp_km_s=5.5, depth_km=2.0),
            ],
        )
        result = classify_column(column)
        assert result is not column
        assert len(column.classifications) == 0  # original unchanged


# ═══════════════════════════════════════════════════════════════════════════════
# Constants sanity — Huang 2021 source values
# ═══════════════════════════════════════════════════════════════════════════════


class TestSourceConstants:
    """Verify that the module's constants match the Huang 2021 paper."""

    def test_normal_continental_range(self) -> None:
        assert NORMAL_CONTINENTAL_VP_MIN == 5.0
        assert NORMAL_CONTINENTAL_VP_MAX == 6.8

    def test_stretched_upper_vp(self) -> None:
        assert STRETCHED_UPPER_CRUST_VP_MAX == 6.0

    def test_ductile_vp_threshold(self) -> None:
        assert DUCTILE_VP_TOP_THRESHOLD == 6.4

    def test_ductile_depth_window(self) -> None:
        assert DUCTILE_DEPTH_TOP_KM == 8.0
        assert DUCTILE_DEPTH_BOT_KM == 13.0

    def test_serpentinized_vp(self) -> None:
        assert SERPENTINIZED_VP == 7.7

    def test_serpentinized_heat_flow(self) -> None:
        # Heat flow too cold for partial melting → must be serpentinization
        assert SERPENTINIZED_HEATFLOW_MW_M2 == 60.0

    def test_hvl_threshold(self) -> None:
        assert HVL_VP_THRESHOLD == 7.2
