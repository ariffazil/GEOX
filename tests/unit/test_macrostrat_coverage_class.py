"""
Offline tests for the Macrostrat coverage-class classifier and the upstream
API build stamp.

F2 TRUTH: a zero from /units is not "no bedrock here". It can mean "no
unit-level polygons, only a generalized map polygon". These tests pin the
classification so a caller never has to infer it from a bare count.

No network: the client's HTTP layer is monkeypatched.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from geox_mcp.tools.macrostrat_client import MacrostratClient  # noqa: E402

pytestmark = pytest.mark.asyncio


def _units_payload(n: int) -> dict:
    return {
        "success": {
            "data": [
                {"unit_id": i, "unit_name": f"Unit {i}", "col_id": 1, "lith": "sandstone"}
                for i in range(n)
            ]
        }
    }


def _map_payload(n: int) -> dict:
    return {
        "success": {
            "data": [
                {
                    "name": "Cenozoic sedimentary rocks",
                    "lith": "carbonate-sandstone-conglomerate",
                    "t_age": 0,
                    "b_age": 66,
                    "best_int_name": "Cenozoic",
                    "color": "#F2F91D",
                    "source_id": 154,
                }
                for _ in range(n)
            ]
        }
    }


class TestCoverageClass:
    async def test_unit_polygon_wins_when_units_exist(self, monkeypatch):
        c = MacrostratClient()

        async def _units(**_kw):
            return _units_payload(3)

        async def _map(**_kw):
            return _map_payload(1)

        monkeypatch.setattr(c, "get_units", _units)
        monkeypatch.setattr(c, "get_geologic_units_map", _map)

        out = await c.get_coverage_class(lat=43.07, lng=-89.40)
        assert out["coverage_class"] == "unit_polygon"
        assert out["unit_polygon_count"] == 3
        assert out["map_polygon_count"] == 1
        assert "formation" in out["coverage_explanation"].lower()

    async def test_map_polygon_when_units_absent(self, monkeypatch):
        """The Malaysia case: /units is empty, /geologic_units/map is not."""
        c = MacrostratClient()

        async def _units(**_kw):
            return _units_payload(0)

        async def _map(**_kw):
            return _map_payload(1)

        monkeypatch.setattr(c, "get_units", _units)
        monkeypatch.setattr(c, "get_geologic_units_map", _map)

        out = await c.get_coverage_class(lat=6.0814, lng=116.7241)
        assert out["coverage_class"] == "map_polygon"
        assert out["unit_polygon_count"] == 0
        assert out["map_polygon_count"] == 1
        assert out["map_unit"] is not None
        assert out["map_unit"]["name"] == "Cenozoic sedimentary rocks"
        assert "no unit-level polygons" in out["coverage_explanation"].lower()

    async def test_none_when_both_layers_empty(self, monkeypatch):
        c = MacrostratClient()

        async def _units(**_kw):
            return _units_payload(0)

        async def _map(**_kw):
            return _map_payload(0)

        monkeypatch.setattr(c, "get_units", _units)
        monkeypatch.setattr(c, "get_geologic_units_map", _map)

        out = await c.get_coverage_class(lat=0.0, lng=-140.0)
        assert out["coverage_class"] == "none"
        assert out["map_unit"] is None

    async def test_prefetched_units_skip_second_units_call(self, monkeypatch):
        """A caller that already fetched units must not trigger a re-fetch."""
        c = MacrostratClient()
        units_calls = {"n": 0}

        async def _units(**_kw):
            units_calls["n"] += 1
            return _units_payload(2)

        async def _map(**_kw):
            return _map_payload(0)

        monkeypatch.setattr(c, "get_units", _units)
        monkeypatch.setattr(c, "get_geologic_units_map", _map)

        out = await c.get_coverage_class(lat=1.0, lng=2.0, units=[{"unit_id": 1}, {"unit_id": 2}])
        assert units_calls["n"] == 0
        assert out["coverage_class"] == "unit_polygon"
        assert out["unit_polygon_count"] == 2

    async def test_geojson_map_payload_is_accepted(self, monkeypatch):
        """The map route sometimes answers GeoJSON; the classifier must cope."""
        c = MacrostratClient()

        async def _units(**_kw):
            return _units_payload(0)

        async def _map(**_kw):
            return {"success": {"data": {"type": "FeatureCollection", "features": _map_payload(1)["success"]["data"]}}}

        monkeypatch.setattr(c, "get_units", _units)
        monkeypatch.setattr(c, "get_geologic_units_map", _map)

        out = await c.get_coverage_class(lat=6.08, lng=116.72)
        assert out["coverage_class"] == "map_polygon"
        assert out["map_polygon_count"] == 1


class TestApiVersionStamp:
    async def test_version_is_read_and_named(self, monkeypatch):
        c = MacrostratClient()

        async def _request(endpoint, params=None, use_cache=True, cache_ttl=86400.0):
            assert endpoint == "version"
            return {
                "service": "api-v2",
                "version": "2.6.0",
                "commit": "0ec2ff00",
                "build_date": "2026-11-03T06:40:03.629Z",
                "repository": "UW-Macrostrat/macrostrat",
            }

        monkeypatch.setattr(c, "_request", _request)
        out = await c.get_api_version()
        assert out["available"] is True
        assert out["version"] == "2.6.0"
        assert out["commit"] == "0ec2ff00"
        assert out["repository"] == "UW-Macrostrat/macrostrat"

    async def test_version_failure_is_honest_not_guessed(self, monkeypatch):
        """An unreachable upstream must not be reported as a known build."""
        c = MacrostratClient()

        async def _request(endpoint, params=None, use_cache=True, cache_ttl=86400.0):
            return {"error": "timeout", "success": {"data": []}}

        monkeypatch.setattr(c, "_request", _request)
        out = await c.get_api_version()
        assert out["available"] is False
        assert out.get("version") is None
