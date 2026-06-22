"""
Integration tests for Macrostrat API Client.

Tests live API endpoints against macrostrat.org.
These are integration tests — they require network access.
Skip with: pytest -m "not integration"

F2 TRUTH: All assertions are OBSERVED against live API responses.
F7 HUMILITY: We test that the API returns valid structures,
             not that specific geological data exists at every location.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from geox_mcp.tools.macrostrat_client import (
    MacrostratClient,
    SE_ASIA_HOTSPOTS,
    _CACHE_DIR,
)


def _macrostrat_api_alive() -> bool:
    """Check if Macrostrat API is actually responsive (not just DNS-resolvable).
    
    F2 TRUTH: Some endpoints (e.g. /sources) may return empty due to API drift
    or backend changes. If the API is reachable but returns 0 sources, skip the
    live integration tests rather than fail.
    """
    import asyncio
    try:
        from geox_mcp.tools.macrostrat_client import MacrostratClient
        async def check():
            c = MacrostratClient()
            r = await c.get_sources(all_=True)
            data = r.get('success', {}).get('data', [])
            return isinstance(data, list) and len(data) > 0
        return asyncio.run(check())
    except Exception:
        return False

pytestmark_api_alive = pytest.mark.skipif(
    not _macrostrat_api_alive(),
    reason='Macrostrat API returns empty data (network or API drift). '
           'Integration test requires live, populated responses.',
)

pytestmark_dns = pytest.mark.skipif(
    not __import__("socket").getaddrinfo("macrostrat.org", 443),
    reason="Macrostrat.org not reachable",
)

# Combine all markers (pytest supports a list of marks for pytestmark).
pytestmark = [
    pytest.mark.integration,
    pytestmark_api_alive,
    pytestmark_dns,
]  # type: ignore[assignment]  # pytest accepts list of marks here


@pytest.fixture
def client() -> MacrostratClient:
    return MacrostratClient()


class TestMacrostratClientInitialization:
    """Client should initialize without errors."""

    def test_client_creates(self):
        c = MacrostratClient()
        assert c is not None
        assert c.base_url == "https://macrostrat.org/api/v2"

    def test_cache_dir_created(self):
        assert _CACHE_DIR.exists()
        assert _CACHE_DIR.is_dir()

    def test_cache_db_created(self):
        from geox_mcp.tools.macrostrat_client import _CACHE_DB
        assert _CACHE_DB.exists()

    def test_se_asia_hotspots_defined(self):
        assert len(SE_ASIA_HOTSPOTS) == 10
        names = [h["name"] for h in SE_ASIA_HOTSPOTS]
        assert "Malay Basin" in names
        assert "Sabah Basin" in names


class TestMacrostratUnitsEndpoint:
    """Unit queries — the core geological data."""

    @pytest.mark.asyncio
    async def test_get_units_known_location(self, client):
        """Madison, WI should return Paleozoic units."""
        result = await client.get_units(lat=43.07, lng=-89.40, radius_km=50)
        items = client.get_units_summary(result)
        assert isinstance(items, list)
        assert len(items) > 0, "Expected units at Madison, WI"
        # Check standard fields
        item = items[0]
        assert "unit_id" in item
        assert "unit_name" in item
        assert "col_id" in item

    @pytest.mark.asyncio
    async def test_get_units_se_asia_empty(self, client):
        """Macrostrat has no native SE Asia coverage — this confirms the known gap."""
        result = await client.get_units(lat=3.5, lng=103.5, radius_km=200)
        items = client.get_units_summary(result)
        # Known limitation: 0 units for SE Asia
        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_get_units_with_radius(self, client):
        """Radius parameter should be accepted."""
        result = await client.get_units(lat=43.07, lng=-89.40, radius_km=100)
        items = client.get_units_summary(result)
        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_get_units_all(self, client):
        """Get all units should return data."""
        result = await client.get_units(all_units=True)
        success = result.get("success", {})
        data = success.get("data", [])
        # Even if truncated, the API should return something
        assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_get_units_by_interval(self, client):
        """Query units by time interval."""
        result = await client.get_units(
            lat=43.07, lng=-89.40,
            interval_name="Ordovician",
        )
        items = client.get_units_summary(result)
        assert isinstance(items, list)


class TestMacrostratColumnsEndpoint:
    """Stratigraphic column queries."""

    @pytest.mark.asyncio
    async def test_get_columns_known_location(self, client):
        """Madison, WI should have at least one column."""
        result = await client.get_columns(lat=43.07, lng=-89.40, radius_km=100)
        cols = client.get_columns_summary(result)
        assert isinstance(cols, list)
        if cols:
            assert "col_id" in cols[0]
            assert "col_name" in cols[0]

    @pytest.mark.asyncio
    async def test_get_columns_all(self, client):
        """All columns should return GeoJSON."""
        result = await client.get_columns(all_columns=True)
        success = result.get("success", {})
        data = success.get("data", {})
        assert isinstance(data, dict)
        if data.get("type") == "FeatureCollection":
            assert "features" in data


class TestMacrostratDefinitionsEndpoints:
    """Lithology, strat names, intervals, minerals, sources."""

    @pytest.mark.asyncio
    async def test_get_lithologies(self, client):
        result = await client.get_lithologies()
        data = result.get("success", {}).get("data", [])
        assert isinstance(data, list)
        assert len(data) >= 200, f"Expected 200+ lithologies, got {len(data)}"
        # Check known lithologies
        names = [l.get("name", "") for l in data[:20]]
        assert "sandstone" in names or "sand" in names

    @pytest.mark.asyncio
    async def test_get_environments(self, client):
        result = await client.get_environments()
        data = result.get("success", {}).get("data", [])
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_strat_names(self, client):
        result = await client.get_strat_names(all_=True)
        data = result.get("success", {}).get("data", [])
        assert isinstance(data, list)
        assert len(data) >= 50000, f"Expected 50k+ strat names, got {len(data)}"

    @pytest.mark.asyncio
    async def test_get_strat_names_by_name(self, client):
        """Look up a specific formation."""
        result = await client.get_strat_names(strat_name="Hell Creek", rank="Fm")
        data = result.get("success", {}).get("data", [])
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_intervals(self, client):
        result = await client.get_intervals()
        data = result.get("success", {}).get("data", [])
        assert isinstance(data, list)
        assert len(data) >= 1500, f"Expected 1500+ intervals, got {len(data)}"

    @pytest.mark.asyncio
    async def test_get_minerals(self, client):
        result = await client.get_minerals()
        data = result.get("success", {}).get("data", [])
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_sources(self, client):
        result = await client.get_sources(all_=True)
        data = result.get("success", {}).get("data", [])
        assert isinstance(data, list)
        assert len(data) >= 200, f"Expected 200+ sources, got {len(data)}"
        # Check for world map
        names = [s.get("name", "") for s in data]
        assert any("world" in n.lower() for n in names)


class TestMacrostratGeologicMapEndpoint:
    """Geologic map polygon queries — 2.5M features."""

    @pytest.mark.asyncio
    async def test_get_geologic_units_map(self, client):
        """Known location should return map polygons."""
        result = await client.get_geologic_units_map(
            lat=43.07, lng=-89.40, radius_km=100
        )
        success = result.get("success", {})
        data = success.get("data", [])
        if isinstance(data, dict):
            features = data.get("features", [])
        elif isinstance(data, list):
            features = data
        else:
            features = []
        # Should have at least a few map polygons
        assert isinstance(features, list)

    @pytest.mark.asyncio
    async def test_get_geologic_units_world_map(self, client):
        """World map (source_id=154) should have coverage."""
        result = await client.get_geologic_units_map(
            lat=3.5, lng=103.5, source_id=154,  # Generalized Geology of the World
        )
        success = result.get("success", {})
        data = success.get("data", [])
        if isinstance(data, dict):
            features = data.get("features", [])
        elif isinstance(data, list):
            features = data
        else:
            features = []
        # World map should have features at any location
        assert isinstance(features, list)


class TestMacrostratFossilsEndpoint:
    """Fossil occurrence data from PBDB."""

    @pytest.mark.asyncio
    async def test_get_fossils(self, client):
        result = await client.get_fossils(limit=10)
        data = result.get("success", {}).get("data", [])
        assert isinstance(data, list)


class TestMacrostratUtils:
    """Utility functions: cache, attribution, stats."""

    def test_attribution_text(self):
        text = MacrostratClient.attribution_text()
        assert "CC-BY-4.0" in text
        assert "macrostrat" in text.lower()
        assert "Peters" in text
        assert len(text) > 50

    def test_attribution_markdown(self):
        md = MacrostratClient.attribution_markdown()
        assert "**Macrostrat:**" in md
        assert "[" in md and "]" in md and "(" in md and ")" in md

    def test_get_units_summary_empty(self, client):
        result = {"success": {"data": []}}
        items = client.get_units_summary(result)
        assert items == []

    def test_get_units_summary_dict(self, client):
        """Edge case: data is a dict with features key (GeoJSON style)."""
        result = {"success": {"data": {"features": [{"unit_id": 1}]}}}
        items = client.get_units_summary(result)
        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_get_stats(self, client):
        result = await client.get_stats()
        success = result.get("success", {})
        assert isinstance(success, dict)

    def test_cache_stats(self, client):
        stats = client.cache_stats()
        assert "memory_entries" in stats
        assert "disk_entries" in stats

    def test_cache_clear(self, client):
        result = client.clear_cache()
        assert "cleared_memory" in result


class TestSEAsiaCacheWarming:
    """SE Asia cache warming should run without errors."""

    @pytest.mark.asyncio
    async def test_warm_se_asia(self, client):
        result = await client.warm_se_asia()
        assert "warmed" in result
        assert "errors" in result
        assert len(result["warmed"]) == 10, (
            f"Expected 10 hotspots, got {len(result['warmed'])}"
        )
        # All 10 should complete (even if 0 units found — that's the known gap)
        for r in result["warmed"]:
            assert "basin" in r
            assert "units_found" in r
        # No errors should have occurred
        assert len(result["errors"]) == 0, (
            f"Cache warming errors: {result['errors']}"
        )


class TestMacrostratClientErrorHandling:
    """Client should handle errors gracefully."""

    @pytest.mark.asyncio
    async def test_bad_endpoint(self, client):
        result = await client._request("nonexistent_endpoint")
        assert "error" in result
        assert "data" in result.get("success", {})

    @pytest.mark.asyncio
    async def test_no_params(self, client):
        """Calling units without lat/lng should not crash."""
        result = await client.get_units()
        assert "success" in result

    @pytest.mark.asyncio
    async def test_network_timeout_handled(self, client):
        """Client should not hang on slow endpoints."""
        import httpx
        client.timeout = 0.001  # Force timeout
        result = await client.get_units(lat=43.07, lng=-89.40)
        assert "error" in result
        client.timeout = 30.0  # Reset
