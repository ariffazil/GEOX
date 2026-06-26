"""Tests for Physical Visible Earth fetchers and MCP tools:
- USGS Earthquake Catalog (usgs_earthquake_fetcher)
- ETOPO Global Relief (etopo_fetcher)
- GEBCO Bathymetry (gebco_fetcher)
- earth_surface.py MCP tool wrappers
"""

from __future__ import annotations

import os
import pytest

from geox_core.io.usgs_earthquake_fetcher import (
    USGSEarthquakeFetcher,
    EarthquakeQuery,
    EarthquakeEvent,
    EarthquakeCatalogResult,
    USGS_SOURCES,
    USGS_CITATION,
)
from geox_core.io.etopo_fetcher import (
    ETOPOFetcher,
    ETOPOExtractRequest,
    ETOPOFetchResult,
    ETOPOGridMeta,
    ETOPO_2022_SOURCES,
    ETOPO_CITATION,
)
from geox_core.io.gebco_fetcher import (
    GEBCOFetcher,
    GEBCOExtractRequest,
    GEBCOFetchResult,
    GEBCOGridMeta,
    GEBCO_2026_SOURCES,
    GEBCO_CITATION,
)


# ════════════════════════════════════════════════════════════════════════════════
# 1. USGS EARTHQUAKE CATALOG
# ════════════════════════════════════════════════════════════════════════════════
class TestUSGSEarthquakeFetcher:
    def test_offline_mode_returns_stub(self):
        fetcher = USGSEarthquakeFetcher()
        result = fetcher.query(EarthquakeQuery())
        assert result.ok is True
        assert result.mode == "offline_stub"
        assert len(result.events) > 0
        assert result.citation == USGS_CITATION

    def test_offline_events_have_required_fields(self):
        fetcher = USGSEarthquakeFetcher()
        result = fetcher.query(EarthquakeQuery())
        event = result.events[0]
        assert isinstance(event, EarthquakeEvent)
        assert event.event_id
        assert event.time_utc
        assert -90 <= event.latitude <= 90
        assert -180 <= event.longitude <= 180
        assert event.magnitude >= 0
        assert event.event_type

    def test_offline_respects_query_params(self):
        fetcher = USGSEarthquakeFetcher()
        query = EarthquakeQuery(minmagnitude=5.0, limit=50)
        result = fetcher.query(query)
        assert result.ok is True
        assert result.query_params["minmagnitude"] == 5.0

    def test_citation_is_public_domain(self):
        assert "Public Domain" in USGS_CITATION

    def test_sources_have_required_keys(self):
        assert "fdsn_base" in USGS_SOURCES
        assert "query_endpoint" in USGS_SOURCES
        assert "geojson_feed" in USGS_SOURCES

    def test_query_model_validates(self):
        q = EarthquakeQuery(
            starttime="2026-01-01",
            endtime="2026-06-01",
            minmagnitude=4.0,
            limit=100,
        )
        assert q.starttime == "2026-01-01"
        assert q.limit == 100

    def test_circle_query_params(self):
        q = EarthquakeQuery(latitude=35.0, longitude=140.0, maxradiuskm=200)
        assert q.latitude == 35.0
        assert q.maxradiuskm == 200

    def test_event_to_dict_roundtrip(self):
        event = EarthquakeEvent(
            event_id="test_001",
            time_utc="2026-06-25T00:00:00Z",
            latitude=35.0,
            longitude=140.0,
            depth_km=10.0,
            magnitude=5.5,
            magnitude_type="mw",
            place="Test Location",
            event_type="earthquake",
            status="reviewed",
            tsunami_flag=0,
        )
        assert event.event_id == "test_001"
        assert event.magnitude == 5.5


# ════════════════════════════════════════════════════════════════════════════════
# 2. ETOPO GLOBAL RELIEF
# ════════════════════════════════════════════════════════════════════════════════
class TestETOPOFetcher:
    def test_offline_global_returns_stub(self):
        fetcher = ETOPOFetcher()
        result = fetcher.fetch_global()
        assert result.ok is True
        assert result.mode == "offline_stub"
        assert result.meta is not None
        assert result.meta.resolution_arcsec == 15
        assert result.meta.version == "bedrock"
        assert result.meta.crs == "EPSG:4326"
        assert result.citation == ETOPO_CITATION

    def test_offline_bbox_returns_stub(self):
        fetcher = ETOPOFetcher()
        request = ETOPOExtractRequest(
            west=100.0, east=110.0, south=0.0, north=10.0
        )
        result = fetcher.fetch_bbox(request)
        assert result.ok is True
        assert result.mode == "offline_stub"
        assert result.meta.bbox == (100.0, 0.0, 110.0, 10.0)

    def test_resolution_variants(self):
        fetcher = ETOPOFetcher()
        for res in [15, 30, 60]:
            result = fetcher.fetch_global(resolution=res)
            assert result.ok is True
            assert result.meta.resolution_arcsec == res

    def test_version_variants(self):
        fetcher = ETOPOFetcher()
        for ver in ["bedrock", "ice_surface"]:
            result = fetcher.fetch_global(version=ver)
            assert result.ok is True
            assert result.meta.version == ver

    def test_citation_is_public_domain(self):
        assert "Public Domain" in ETOPO_CITATION

    def test_sources_have_required_keys(self):
        assert "bedrock_15s_tiff" in ETOPO_2022_SOURCES
        assert "surface_15s_tiff" in ETOPO_2022_SOURCES
        assert "grid_extract_api" in ETOPO_2022_SOURCES

    def test_extract_request_validates(self):
        req = ETOPOExtractRequest(
            west=95.0, east=105.0, south=-5.0, north=5.0,
            resolution=30, version="ice_surface"
        )
        assert req.west == 95.0
        assert req.resolution == 30
        assert req.version == "ice_surface"


# ════════════════════════════════════════════════════════════════════════════════
# 3. GEBCO BATHYMETRY
# ════════════════════════════════════════════════════════════════════════════════
class TestGEBCOFetcher:
    def test_offline_global_returns_stub(self):
        fetcher = GEBCOFetcher()
        result = fetcher.fetch_global()
        assert result.ok is True
        assert result.mode == "offline_stub"
        assert result.meta is not None
        assert result.meta.resolution_arcsec == 15
        assert result.meta.grid_version == "GEBCO_2026"
        assert result.meta.variant == "ice_surface"
        assert result.citation == GEBCO_CITATION

    def test_offline_bbox_returns_stub(self):
        fetcher = GEBCOFetcher()
        request = GEBCOExtractRequest(
            west=100.0, east=110.0, south=0.0, north=10.0
        )
        result = fetcher.fetch_bbox(request)
        assert result.ok is True
        assert result.mode == "offline_stub"
        assert result.meta.bbox == (100.0, 0.0, 110.0, 10.0)

    def test_variant_types(self):
        fetcher = GEBCOFetcher()
        for variant in ["ice_surface", "sub_ice", "tid"]:
            result = fetcher.fetch_global(variant=variant)
            assert result.ok is True
            assert result.meta.variant == variant

    def test_opendap_url_generation(self):
        fetcher = GEBCOFetcher()
        request = GEBCOExtractRequest(
            west=100.0, east=105.0, south=0.0, north=5.0
        )
        # OPeNDAP URL is only generated in live mode, but we can test the method
        url = fetcher._build_opendap_url(request)
        # In offline mode this may return None depending on env
        # The method itself should not crash
        assert url is None or isinstance(url, str)

    def test_citation_is_public_domain(self):
        assert "Public Domain" in GEBCO_CITATION

    def test_sources_have_required_keys(self):
        assert "ice_surface_netcdf" in GEBCO_2026_SOURCES
        assert "opendap_endpoint" in GEBCO_2026_SOURCES
        assert "download_app" in GEBCO_2026_SOURCES

    def test_extract_request_validates(self):
        req = GEBCOExtractRequest(
            west=95.0, east=105.0, south=-5.0, north=5.0,
            variant="sub_ice"
        )
        assert req.west == 95.0
        assert req.variant == "sub_ice"


# ════════════════════════════════════════════════════════════════════════════════
# 4. MCP TOOL WRAPPERS (earth_surface.py)
# ════════════════════════════════════════════════════════════════════════════════
class TestEarthSurfaceMCPTools:
    @pytest.mark.asyncio
    async def test_earthquake_catalog_offline(self):
        from geox_mcp.tools.earth_surface import (
            geox_earthquake_catalog,
            EarthquakeCatalogRequest,
        )
        request = EarthquakeCatalogRequest()
        result = await geox_earthquake_catalog(request)
        assert result.ok is True
        assert result.mode == "offline_stub"
        assert result.count > 0
        assert result.tool == "geox_earthquake_catalog"

    @pytest.mark.asyncio
    async def test_relief_ingest_offline(self):
        from geox_mcp.tools.earth_surface import (
            geox_relief_ingest,
            ReliefIngestRequest,
        )
        request = ReliefIngestRequest()
        result = await geox_relief_ingest(request)
        assert result.ok is True
        assert result.mode == "offline_stub"
        assert result.tool == "geox_relief_ingest"
        assert result.epistemic_status == "OBSERVED"

    @pytest.mark.asyncio
    async def test_bathymetry_ingest_offline(self):
        from geox_mcp.tools.earth_surface import (
            geox_bathymetry_ingest,
            BathymetryIngestRequest,
        )
        request = BathymetryIngestRequest()
        result = await geox_bathymetry_ingest(request)
        assert result.ok is True
        assert result.mode == "offline_stub"
        assert result.tool == "geox_bathymetry_ingest"
        assert result.epistemic_status == "OBSERVED"

    @pytest.mark.asyncio
    async def test_relief_ingest_bbox(self):
        from geox_mcp.tools.earth_surface import (
            geox_relief_ingest,
            ReliefIngestRequest,
        )
        request = ReliefIngestRequest(
            mode="bbox", west=100, east=110, south=0, north=10
        )
        result = await geox_relief_ingest(request)
        assert result.ok is True
        assert result.meta is not None

    @pytest.mark.asyncio
    async def test_bathymetry_ingest_bbox(self):
        from geox_mcp.tools.earth_surface import (
            geox_bathymetry_ingest,
            BathymetryIngestRequest,
        )
        request = BathymetryIngestRequest(
            mode="bbox", west=100, east=110, south=0, north=10
        )
        result = await geox_bathymetry_ingest(request)
        assert result.ok is True
        assert result.meta is not None


# ════════════════════════════════════════════════════════════════════════════════
# 5. REGISTRY — verify 33 canonical tools (DEFERRED to Phase 3)
# ════════════════════════════════════════════════════════════════════════════════
# Phase 2 Clean Architecture locked the canonical surface to 16 tools (2026-06-25).
# The 33-tool Earth Dimension expansion (D1-D17) is deferred to Phase 3 and requires
# 888_HOLD per geox/AGENTS.md. These tests are preserved (not deleted) and will be
# re-enabled when Phase 3 lands. Until then, the fetcher tests above cover the
# underlying USGS/ETOPO/GEBCO machinery and the canonical surface is validated by
# tests/test_canonical_public_surface.py.
@pytest.mark.skipif(
    True,  # Phase 3 deferred — set to False when 33-tool expansion is restored
    reason="Phase 3 deferred: 33-tool Earth Dimensions expansion requires 888_HOLD. "
           "See geox/AGENTS.md. Fetcher-level coverage continues in classes above.",
)
class TestCanonicalRegistry19:
    def test_19_canonical_tools(self):
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
        assert len(CANONICAL_PUBLIC_TOOLS) == 33

    def test_surface_earth_tools_present(self):
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
        assert "geox_earthquake_catalog" in CANONICAL_PUBLIC_TOOLS
        assert "geox_relief_ingest" in CANONICAL_PUBLIC_TOOLS
        assert "geox_bathymetry_ingest" in CANONICAL_PUBLIC_TOOLS

    def test_surface_earth_in_manifest(self):
        from geox_mcp.registry import GEOX_TOOL_MANIFEST
        names = [t["name"] for t in GEOX_TOOL_MANIFEST]
        assert "geox_earthquake_catalog" in names
        assert "geox_relief_ingest" in names
        assert "geox_bathymetry_ingest" in names
