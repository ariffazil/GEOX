"""
test_crustal_domain_classify.py — Tests for the multi-cell crust-domain classifier
═══════════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Verifies:
  - F4 CLARITY: Pydantic envelope strict validation
  - F2 TRUTH: per-cell classifications are DER-grade
  - F7 HUMILITY: confidence hard-capped at 0.90
  - F11 AUDIT: observation hash present + audit trail
  - F13 SOVEREIGN: sovereignty note preserved in result
  - Multi-cell scenarios: Kinabalu + Layang-Layang + NW Sabah Trough
"""
from __future__ import annotations

import asyncio

import pytest

from geox_mcp.tools.crustal_domain_classify import (
    CrustCellObservation,
    CrustDomainMap,
    CrustDomainRequest,
    _observation_hash,
    geox_crustal_domain_classify,
)
from geox_core.schemas.crust_vp_grammar import CrustZone


# ═══════════════════════════════════════════════════════════════════════════════
# F4 CLARITY — Pydantic envelope strict validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvelopeStrict:
    def test_cell_observation_rejects_extra_fields(self) -> None:
        with pytest.raises(Exception):
            CrustCellObservation(
                vp_km_s=5.5,
                rogue_field="not_allowed",  # type: ignore[call-arg]
            )

    def test_cell_observation_validates_vp_range(self) -> None:
        with pytest.raises(Exception):
            CrustCellObservation(vp_km_s=15.0)  # > 10.0 max

    def test_cell_observation_validates_lat_lon(self) -> None:
        with pytest.raises(Exception):
            CrustCellObservation(vp_km_s=5.5, lat=95.0)  # > 90

    def test_request_requires_at_least_one_cell(self) -> None:
        with pytest.raises(Exception):
            CrustDomainRequest(basin_name="X", cells=[])

    def test_request_requires_basin_name(self) -> None:
        with pytest.raises(Exception):
            CrustDomainRequest(basin_name="", cells=[CrustCellObservation(vp_km_s=5.5)])


# ═══════════════════════════════════════════════════════════════════════════════
# F11 AUDIT — observation hash
# ═══════════════════════════════════════════════════════════════════════════════


class TestObservationHash:
    def test_hash_deterministic(self) -> None:
        cells = [
            CrustCellObservation(vp_km_s=5.5, depth_km=2.0, cell_id="A"),
            CrustCellObservation(vp_km_s=6.0, depth_km=8.0, cell_id="B"),
        ]
        h1 = _observation_hash(cells)
        h2 = _observation_hash(list(reversed(cells)))  # order shouldn't matter
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_hash_changes_with_input(self) -> None:
        c1 = [CrustCellObservation(vp_km_s=5.5, cell_id="A")]
        c2 = [CrustCellObservation(vp_km_s=6.0, cell_id="A")]
        assert _observation_hash(c1) != _observation_hash(c2)


# ═══════════════════════════════════════════════════════════════════════════════
# F2 TRUTH — Per-cell classifications are DER-grade
# ═══════════════════════════════════════════════════════════════════════════════


class TestPerCellClassification:
    def test_classify_single_continental_cell(self) -> None:
        req = CrustDomainRequest(
            basin_name="Kinabalu",
            cells=[
                CrustCellObservation(
                    vp_km_s=6.2,
                    depth_km=2.0,
                    crust_thickness_km=30.0,
                    lat=6.0,
                    lon=116.0,
                    source="OBS-derived",
                    method="joint inversion",
                ),
            ],
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        assert isinstance(result, CrustDomainMap)
        assert result.cell_count == 1
        cell = result.cells[0]
        assert cell.crust_zone == CrustZone.NORMAL_CONTINENTAL
        assert cell.evidence_rank in ("OBS", "DER")
        assert cell.confidence <= 0.90

    def test_classify_hyperthinned_oct_cell(self) -> None:
        req = CrustDomainRequest(
            basin_name="NW Sabah Trough",
            cells=[
                CrustCellObservation(
                    vp_km_s=6.5,
                    depth_km=5.0,
                    crust_thickness_km=6.0,
                    lat=6.5,
                    lon=115.5,
                    source="Huang 2021 analog",
                    method="Vp template",
                ),
            ],
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        assert result.cells[0].crust_zone == CrustZone.HYPERTHINNED_OCT


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-cell scenarios — full integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestMultiCellScenarios:
    def test_layang_layang_column_3_cells(self) -> None:
        """Layang-Layang 1D column: sediment → failed-rift ductile → oceanic."""
        req = CrustDomainRequest(
            basin_name="Layang-Layang",
            cells=[
                # Upper sediment
                CrustCellObservation(
                    vp_km_s=2.5, depth_km=0.5, crust_thickness_km=10.0,
                    cell_id="LL-sed", source="velocity-from-stacking",
                ),
                # Upper crust
                CrustCellObservation(
                    vp_km_s=5.5, depth_km=4.0, crust_thickness_km=10.0,
                    cell_id="LL-upper", source="velocity-from-stacking",
                ),
                # Ductile layer (mid-crust)
                CrustCellObservation(
                    vp_km_s=6.0, depth_km=9.0, crust_thickness_km=10.0,
                    cell_id="LL-ductile", source="OBS analog (Huang 2021)",
                ),
                # Lower crust
                CrustCellObservation(
                    vp_km_s=7.0, depth_km=14.0, crust_thickness_km=10.0,
                    cell_id="LL-lower", source="OBS analog (Huang 2021)",
                ),
            ],
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        assert result.cell_count == 4
        assert "unknown" in result.zone_distribution  # sediment cell
        assert "ductile_mid_crustal" in result.zone_distribution  # LL-ductile

    def test_kinabalu_layang_layang_interface_5_cells(self) -> None:
        """Cross-section: Kinabalu inboard → Layang-Layang mid → NW Sabah trough."""
        req = CrustDomainRequest(
            basin_name="Kinabalu-Layang Interface",
            cells=[
                # Cell 1: Kinabalu inboard (thick continental)
                CrustCellObservation(vp_km_s=6.2, depth_km=2.0, crust_thickness_km=30.0,
                                     lat=6.0, lon=116.5, cell_id="KB-1"),
                # Cell 2: Kinabalu mid-shelf
                CrustCellObservation(vp_km_s=6.0, depth_km=5.0, crust_thickness_km=25.0,
                                     lat=6.2, lon=116.0, cell_id="KB-2"),
                # Cell 3: Layang-Layang proper
                CrustCellObservation(vp_km_s=5.9, depth_km=8.0, crust_thickness_km=12.0,
                                     lat=6.4, lon=115.5, cell_id="LL-1"),
                # Cell 4: NW Sabah Trough (hyperthinned)
                CrustCellObservation(vp_km_s=6.5, depth_km=10.0, crust_thickness_km=7.0,
                                     lat=6.6, lon=115.0, cell_id="NWST-1"),
                # Cell 5: NW Sabah wedge (deep, possible serpentinized)
                CrustCellObservation(
                    vp_km_s=7.7, depth_km=18.0, crust_thickness_km=5.0,
                    heat_flow_mw_m2=55.0,
                    lat=6.8, lon=114.5, cell_id="NWSW-1",
                ),
            ],
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        assert result.cell_count == 5
        # Verify zone distribution
        zones = result.zone_distribution
        # Should see at least: normal_continental, ductile_mid_crustal, hyperthinned_oct,
        # serpentinized_mantle
        assert "normal_continental" in zones
        assert "hyperthinned_oct" in zones
        assert "serpentinized_mantle" in zones


# ═══════════════════════════════════════════════════════════════════════════════
# F13 SOVEREIGN — sovereignty note preserved
# ═══════════════════════════════════════════════════════════════════════════════


class TestSovereigntyNote:
    def test_sovereignty_note_present(self) -> None:
        req = CrustDomainRequest(
            basin_name="X",
            cells=[CrustCellObservation(vp_km_s=5.5, crust_thickness_km=22.0)],
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        assert "sovereign" in result.sovereignty_note.lower()
        assert "888_HOLD" in result.sovereignty_note

    def test_no_automatic_boundary_inference(self) -> None:
        """Tool must NOT collapse cells into regions automatically.

        F13 SOVEREIGN — domain boundaries require human ratification.
        """
        req = CrustDomainRequest(
            basin_name="X",
            cells=[
                CrustCellObservation(vp_km_s=6.0, depth_km=2.0, crust_thickness_km=30.0),
                CrustCellObservation(vp_km_s=6.0, depth_km=2.0, crust_thickness_km=30.0),
                CrustCellObservation(vp_km_s=6.5, depth_km=5.0, crust_thickness_km=7.0),
                CrustCellObservation(vp_km_s=6.5, depth_km=5.0, crust_thickness_km=7.0),
            ],
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        # Result should expose per-cell classifications, NOT a collapsed domain map
        assert len(result.cells) == 4
        # No "domains" or "regions" field — that's sovereign territory
        assert "domains" not in result.model_dump()
        assert "regions" not in result.model_dump()


# ═══════════════════════════════════════════════════════════════════════════════
# F7 HUMILITY — confidence cap
# ═══════════════════════════════════════════════════════════════════════════════


class TestHumilityCap:
    def test_no_classification_above_0_90(self) -> None:
        req = CrustDomainRequest(
            basin_name="X",
            cells=[
                CrustCellObservation(vp_km_s=4.0, crust_thickness_km=5.0),
                CrustCellObservation(vp_km_s=5.5, crust_thickness_km=22.0),
                CrustCellObservation(vp_km_s=6.5, crust_thickness_km=6.0),
                CrustCellObservation(vp_km_s=7.7, crust_thickness_km=6.0, heat_flow_mw_m2=55.0),
                CrustCellObservation(vp_km_s=7.0, crust_thickness_km=15.0),
            ],
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        for cell in result.cells:
            assert cell.confidence <= 0.90, (
                f"F7 VIOLATION: vp={cell.vp_km_s}, conf={cell.confidence}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Diagnostics toggle
# ═══════════════════════════════════════════════════════════════════════════════


class TestDiagnosticsToggle:
    def test_no_diagnostics_by_default(self) -> None:
        req = CrustDomainRequest(
            basin_name="X",
            cells=[CrustCellObservation(vp_km_s=6.0, crust_thickness_km=22.0)],
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        assert result.cells[0].diagnostic_basis == []

    def test_diagnostics_when_requested(self) -> None:
        req = CrustDomainRequest(
            basin_name="X",
            cells=[CrustCellObservation(vp_km_s=6.0, crust_thickness_km=22.0)],
            include_diagnostics=True,
        )
        result = asyncio.run(geox_crustal_domain_classify(req))
        assert len(result.cells[0].diagnostic_basis) > 0
