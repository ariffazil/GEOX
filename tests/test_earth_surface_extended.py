"""Tests for Extended Earth Dimensions (D4-D17) fetchers and MCP tools.
14 sources: HeatFlow, WSM, GPlates, EarthChem, NSTA, CMEMS, ERDDAP,
OneGeology, MagIC, GRACE, ERA5, USGS Water, STAC, NOAA SWPC.
"""

from __future__ import annotations

import pytest


# ── D4: Heat Flow ──
class TestHeatFlowFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.ihfc_heatflow_fetcher import IHFCHeatFlowFetcher, HeatFlowQuery
        r = IHFCHeatFlowFetcher().query(HeatFlowQuery())
        assert r.ok and r.mode == "offline_stub" and r.count > 0

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_heatflow_query, HeatFlowRequest
        r = await geox_heatflow_query(HeatFlowRequest())
        assert r["ok"] and r["tool"] == "geox_heatflow_query"


# ── D5: Crustal Stress ──
class TestStressFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.wsm_stress_fetcher import WSMStressFetcher, StressQuery
        r = WSMStressFetcher().query(StressQuery())
        assert r.ok and r.mode == "offline_stub" and r.count > 0

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_stress_query, StressRequest
        r = await geox_stress_query(StressRequest())
        assert r["ok"] and r["tool"] == "geox_stress_query"


# ── D7: Plate Reconstruction ──
class TestGPlatesFetcher:
    def test_offline_reconstruct(self):
        from geox_core.io.gplates_fetcher import GPlatesFetcher, ReconstructionRequest
        r = GPlatesFetcher().reconstruct(ReconstructionRequest(latitude=4.0, longitude=112.0, age_ma=100))
        assert r.ok and r.mode == "offline_stub" and r.reconstructed_lat is not None

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_plate_reconstruct, PlateReconstructRequest
        r = await geox_plate_reconstruct(PlateReconstructRequest(latitude=4.0, longitude=112.0, age_ma=100))
        assert r["ok"] and r["tool"] == "geox_plate_reconstruct"


# ── D6: Geochemistry ──
class TestEarthChemFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.earthchem_fetcher import EarthChemFetcher, GeochemQuery
        r = EarthChemFetcher().query(GeochemQuery())
        assert r.ok and r.mode == "offline_stub" and r.count > 0

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_geochem_query, GeochemRequest
        r = await geox_geochem_query(GeochemRequest())
        assert r["ok"] and r["tool"] == "geox_geochem_query"


# ── D15: UK Petroleum ──
class TestNSTAFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.nsta_uk_fetcher import NSTAUKFetcher, NSTAQuery
        r = NSTAUKFetcher().query(NSTAQuery())
        assert r.ok and r.mode == "offline_stub" and r.count > 0

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_uk_petroleum_query, UKPetroleumRequest
        r = await geox_uk_petroleum_query(UKPetroleumRequest())
        assert r["ok"] and r["tool"] == "geox_uk_petroleum_query"


# ── D10: Copernicus Marine ──
class TestCopernicusMarineFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.copernicus_marine_fetcher import CopernicusMarineFetcher, OceanQuery
        r = CopernicusMarineFetcher().query(OceanQuery())
        assert r.ok and r.mode == "offline_stub"

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_ocean_query, OceanRequest
        r = await geox_ocean_query(OceanRequest())
        assert r["ok"] and r["tool"] == "geox_ocean_query"


# ── D10: ERDDAP ──
class TestERDDAPFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.erddap_fetcher import ERDDAPFetcher, ERDDAPQuery
        r = ERDDAPFetcher().query(ERDDAPQuery(dataset_id="jplMURSST41"))
        assert r.ok and r.mode == "offline_stub" and r.dataset_id == "jplMURSST41"

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_erddap_query, ERDDAPRequest
        r = await geox_erddap_query(ERDDAPRequest(dataset_id="jplMURSST41"))
        assert r["ok"] and r["tool"] == "geox_erddap_query"


# ── D16: OneGeology ──
class TestOneGeologyFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.onegeology_fetcher import OneGeologyFetcher, GeologyMapQuery
        r = OneGeologyFetcher().query(GeologyMapQuery(minlatitude=4, maxlatitude=6, minlongitude=110, maxlongitude=115))
        assert r.ok and r.mode == "offline_stub"

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_geology_map_query, GeologyMapRequest
        r = await geox_geology_map_query(GeologyMapRequest(minlatitude=4, maxlatitude=6, minlongitude=110, maxlongitude=115))
        assert r["ok"] and r["tool"] == "geox_geology_map_query"


# ── D8: Paleomagnetism ──
class TestMagICFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.magic_paleomag_fetcher import MagICFetcher, PaleomagQuery
        r = MagICFetcher().query(PaleomagQuery())
        assert r.ok and r.mode == "offline_stub" and r.count > 0

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_paleomag_query, PaleomagRequest
        r = await geox_paleomag_query(PaleomagRequest())
        assert r["ok"] and r["tool"] == "geox_paleomag_query"


# ── D9: GRACE-FO ──
class TestGRACEFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.grace_fetcher import GRACEFetcher, GraceQuery
        r = GRACEFetcher().query(GraceQuery())
        assert r.ok and r.mode == "offline_stub"

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_gravity_change_query, GraceRequest
        r = await geox_gravity_change_query(GraceRequest())
        assert r["ok"] and r["tool"] == "geox_gravity_change_query"


# ── D11: ERA5 ──
class TestERA5Fetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.era5_fetcher import ERA5Fetcher, ERA5Query
        r = ERA5Fetcher().query(ERA5Query())
        assert r.ok and r.mode == "offline_stub"

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_climate_reanalysis, ClimateReanalysisRequest
        r = await geox_climate_reanalysis(ClimateReanalysisRequest())
        assert r["ok"] and r["tool"] == "geox_climate_reanalysis"


# ── D12: USGS Water ──
class TestUSGSWaterFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.usgs_water_fetcher import USGSWaterFetcher, WaterQuery
        r = USGSWaterFetcher().query(WaterQuery())
        assert r.ok and r.mode == "offline_stub" and r.count > 0

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_hydrology_query, HydrologyRequest
        r = await geox_hydrology_query(HydrologyRequest())
        assert r["ok"] and r["tool"] == "geox_hydrology_query"


# ── D14: Landsat/STAC ──
class TestLandsatSTACFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.landsat_stac_fetcher import LandsatSTACFetcher, SatelliteQuery
        r = LandsatSTACFetcher().query(SatelliteQuery(minlatitude=4, maxlatitude=6, minlongitude=110, maxlongitude=115))
        assert r.ok and r.mode == "offline_stub"

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_satellite_catalog, SatelliteCatalogRequest
        r = await geox_satellite_catalog(SatelliteCatalogRequest(minlatitude=4, maxlatitude=6, minlongitude=110, maxlongitude=115))
        assert r["ok"] and r["tool"] == "geox_satellite_catalog"


# ── D17: Space Weather ──
class TestNOAASWPCFetcher:
    def test_offline_returns_stub(self):
        from geox_core.io.noaa_swpc_fetcher import NOAASWPCFetcher, SpaceWeatherQuery
        r = NOAASWPCFetcher().query(SpaceWeatherQuery())
        assert r.ok and r.mode == "offline_stub" and r.count > 0

    @pytest.mark.asyncio
    async def test_mcp_tool(self):
        from geox_mcp.tools.earth_surface_2 import geox_space_weather, SpaceWeatherRequest
        r = await geox_space_weather(SpaceWeatherRequest())
        assert r["ok"] and r["tool"] == "geox_space_weather"

    def test_list_products(self):
        from geox_core.io.noaa_swpc_fetcher import NOAASWPCFetcher
        p = NOAASWPCFetcher().list_products()
        assert "kp_index" in p and "solar_wind" in p


# ── REGISTRY: verify 33 canonical tools (DEFERRED to Phase 3) ──
# Phase 2 Clean Architecture locked the canonical surface to 16 tools (2026-06-25).
# The 33-tool expansion is deferred. Fetcher coverage is in classes above.
@pytest.mark.skipif(
    True,  # Phase 3 deferred
    reason="Phase 3 deferred: 33-tool Earth Dimensions expansion requires 888_HOLD. "
           "See geox/AGENTS.md.",
)
class TestCanonicalRegistry33:
    def test_33_canonical_tools(self):
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
        assert len(CANONICAL_PUBLIC_TOOLS) == 33

    def test_surface_vs_internal_split(self):
        from geox_mcp.registry import SURFACE_TOOLS, INTERNAL_TOOLS
        assert len(SURFACE_TOOLS) == 29, f"Expected 29 surface tools, got {len(SURFACE_TOOLS)}"
        assert len(INTERNAL_TOOLS) == 4, f"Expected 4 internal tools, got {len(INTERNAL_TOOLS)}"
        assert len(SURFACE_TOOLS) + len(INTERNAL_TOOLS) == 33

    def test_internal_tools_are_governance(self):
        from geox_mcp.registry import INTERNAL_TOOLS
        # Internal = claim, evidence, prospect, doctrine
        assert "geox_claim" in INTERNAL_TOOLS
        assert "geox_evidence" in INTERNAL_TOOLS
        assert "geox_prospect" in INTERNAL_TOOLS
        assert "geox_doctrine" in INTERNAL_TOOLS

    def test_surface_tools_include_earth_data(self):
        from geox_mcp.registry import SURFACE_TOOLS
        # Surface includes all D1-D17 earth data tools
        assert "geox_earthquake_catalog" in SURFACE_TOOLS
        assert "geox_relief_ingest" in SURFACE_TOOLS
        assert "geox_heatflow_query" in SURFACE_TOOLS
        assert "geox_plate_reconstruct" in SURFACE_TOOLS
        assert "geox_ocean_query" in SURFACE_TOOLS

    def test_extended_earth_tools_present(self):
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
        expected = [
            "geox_heatflow_query", "geox_stress_query", "geox_geochem_query",
            "geox_plate_reconstruct", "geox_paleomag_query", "geox_gravity_change_query",
            "geox_ocean_query", "geox_erddap_query", "geox_climate_reanalysis",
            "geox_hydrology_query", "geox_satellite_catalog", "geox_uk_petroleum_query",
            "geox_geology_map_query", "geox_space_weather",
        ]
        for t in expected:
            assert t in CANONICAL_PUBLIC_TOOLS, f"{t} missing from CANONICAL_PUBLIC_TOOLS"

    def test_manifest_has_face_field(self):
        from geox_mcp.registry import GEOX_TOOL_MANIFEST
        for entry in GEOX_TOOL_MANIFEST:
            assert "face" in entry, f"{entry['name']} missing 'face' field"
            assert entry["face"] in ("surface", "internal"), f"{entry['name']} has invalid face: {entry['face']}"
