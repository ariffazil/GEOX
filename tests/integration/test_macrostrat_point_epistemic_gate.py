"""Live epistemic gate — the two-point regression that must pass before deploy.

Failure class this file exists for (measured 2026-11-27):
    A point click used to fan out to /units + /geologic_units/map and drop
    elevation, hasColumns and refs. Worse, the Denver payload crossed the 4 KB
    compact boundary and lost ``upstream_api`` — the receipt could not name the
    build that answered — while Brunei (small payload) kept it. A size-dependent
    provenance loss is invisible in unit tests; only a live payload shows it.

Two layers:
  A. Upstream Macrostrat (always runs): Brunei has no polygons, Denver does.
     This is the coverage truth, independent of GEOX.
  B. GEOX end-to-end (opt-in ``GEOX_LIVE_MCP=1``): the MCP tool must preserve
     coverage_class, upstream_api through compaction, the HYPOTHESIS ceiling,
     and must never self-seal (vault999_status PENDING).

Run:
  pytest tests/integration/test_macrostrat_point_epistemic_gate.py -m integration
  GEOX_LIVE_MCP=1 GEOX_MCP_URL=https://geox.arif-fazil.com/mcp/ pytest ... -m integration
"""

from __future__ import annotations

import os

import httpx
import pytest

pytestmark = pytest.mark.integration

MACROSTRAT_API = os.environ.get("MACROSTRAT_API_BASE", "https://macrostrat.org/api/v2")
DEFAULT_MCP_URL = os.environ.get("GEOX_MCP_URL", "https://geox.arif-fazil.com/mcp/")

# The two control points. Brunei is the honest-null case; Denver is the
# unit-polygon control. Do not substitute a curated literature coordinate here:
# this gate is about what the pipe actually returns.
BRUNEI = (5.3, 115.0)
DENVER = (39.7392, -104.9903)


def _point(lat: float, lng: float, z: int = 8) -> dict:
    resp = httpx.get(
        f"{MACROSTRAT_API}/mobile/map_query_v2",
        params={"lat": lat, "lng": lng, "z": z},
        timeout=25.0,
        follow_redirects=True,
    )
    resp.raise_for_status()
    payload = resp.json()
    return (payload.get("success") or {}).get("data") or {}


def test_upstream_brunei_reports_no_polygons():
    data = _point(*BRUNEI)
    assert data.get("mapData") == [], "Brunei must carry no map polygons"
    assert data.get("hasColumns") is False


def test_upstream_denver_reports_unit_polygons():
    data = _point(*DENVER)
    assert len(data.get("mapData") or []) >= 1, "Denver must carry a map polygon"
    assert data.get("hasColumns") is True
    assert data.get("elevation") is not None


@pytest.mark.skipif(
    os.getenv("GEOX_LIVE_MCP") != "1",
    reason="set GEOX_LIVE_MCP=1 to probe the deployed MCP surface",
)
async def test_geox_brunei_is_honest_null_and_never_self_seals():
    from fastmcp import Client

    async with Client(DEFAULT_MCP_URL) as client:
        result = await client.call_tool(
            "geox_basin",
            {
                "mode": "macrostrat",
                "macrostrat_mode": "macrostrat_point",
                "lat": BRUNEI[0],
                "lng": BRUNEI[1],
                "z": 8,
                "basin_name": "Brunei",
            },
        )

    data = result.structured_content
    interpreted = data.get("interpreted") or {}

    assert data.get("ok") is True
    assert interpreted.get("coverage_class") == "none"
    assert interpreted.get("unit_count") == 0
    assert interpreted.get("units") == []
    assert interpreted.get("has_columns") is False

    # Regression: provenance must survive the compact boundary even on large
    # payloads. A missing build stamp means the receipt cannot name its source.
    upstream = interpreted.get("upstream_api") or {}
    assert upstream.get("version"), "upstream_api lost — compaction regression"

    # Ceiling: GEOX computes, it does not adjudicate.
    assert (data.get("_well_conformance") or {}).get("claim_state") == "HYPOTHESIS"
    receipt = (data.get("_evidence_envelope") or {}).get("_receipt") or {}
    assert receipt.get("vault999_status") == "PENDING", "GEOX must never self-seal"


@pytest.mark.skipif(
    os.getenv("GEOX_LIVE_MCP") != "1",
    reason="set GEOX_LIVE_MCP=1 to probe the deployed MCP surface",
)
async def test_geox_denver_is_unit_polygon_with_attribution():
    from fastmcp import Client

    async with Client(DEFAULT_MCP_URL) as client:
        result = await client.call_tool(
            "geox_basin",
            {
                "mode": "macrostrat",
                "macrostrat_mode": "macrostrat_point",
                "lat": DENVER[0],
                "lng": DENVER[1],
                "z": 8,
                "basin_name": "Denver",
            },
        )

    data = result.structured_content
    interpreted = data.get("interpreted") or {}

    assert data.get("ok") is True
    assert interpreted.get("coverage_class") == "unit_polygon"
    assert interpreted.get("has_columns") is True
    assert interpreted.get("elevation_m") is not None
    # The compact boundary drops list fields but keeps the count; assert the
    # count, not the (possibly compacted) units list.
    assert int(interpreted.get("unit_count") or 0) >= 1

    upstream = interpreted.get("upstream_api") or {}
    assert upstream.get("available") is True
    assert upstream.get("version"), "upstream_api lost — compaction regression"

    assert "CC-BY" in str(interpreted.get("license"))
    assert "macrostrat" in str(interpreted.get("attribution", "")).lower()
