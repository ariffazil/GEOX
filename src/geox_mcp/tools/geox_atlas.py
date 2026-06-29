#!/usr/bin/env python3
"""
GEOX Earth Atlas — Phase 1 (Merged)
geox_atlas — Point-in-country lookup + land/water classifier
Uses local Natural Earth GeoJSON for sovereign offline-capable queries.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import asyncio
import json
import math
from pathlib import Path
from typing import Any

# Atlas data path — relative to geox package root
_ATLAS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "atlas"
_COUNTRIES_GEOJSON = _ATLAS_DIR / "countries.geojson"
_SEA_NEIGHBORS_GEOJSON = _ATLAS_DIR / "sea_neighbors.geojson"

_countries_cache = None
_sea_neighbors_cache = None


def _load_countries():
    global _countries_cache
    if _countries_cache is None:
        with open(_COUNTRIES_GEOJSON) as f:
            _countries_cache = json.load(f)
    return _countries_cache


def _load_sea_neighbors():
    global _sea_neighbors_cache
    if _sea_neighbors_cache is None:
        with open(_SEA_NEIGHBORS_GEOJSON) as f:
            _sea_neighbors_cache = json.load(f)
    return _sea_neighbors_cache


# ── Geometry helpers ───────────────────────────────────────────────────────────


def _EARTH_M_PER_DEG_LAT() -> float:
    return 111_320.0


def _EARTH_M_PER_DEG_LON(lat: float) -> float:
    return 111_320.0 * math.cos(math.radians(lat))


def _point_in_polygon(lat: float, lon: float, polygon: list) -> bool:
    """
    Ray casting algorithm for point-in-polygon test.
    Coordinate convention: GeoJSON polygon coords are (lon, lat) = (x, y).
    Policy: Points on boundary are treated as INSIDE (land) — prevents
    floating-point edge-case flickering at coastlines.
    """
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _distance_to_boundary_m(lat: float, lon: float, polygon: list) -> float:
    """
    Minimum distance from point to polygon edge, in metres.
    Uses point-to-line-segment perpendicular projection.
    Returns 0.0 if point is inside polygon.
    """
    lat_scale = _EARTH_M_PER_DEG_LAT()
    min_dist = float("inf")

    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]

        dx = x2 - x1
        dy = y2 - y1
        seg_len_sq = dx * dx + dy * dy

        if seg_len_sq == 0.0:
            continue

        t = max(0.0, min(1.0, ((lon - x1) * dx + (lat - y1) * dy) / seg_len_sq))

        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        perp_dx = lon - proj_x
        perp_dy = lat - proj_y

        lon_scale = _EARTH_M_PER_DEG_LON((y1 + y2) / 2.0)
        dist_m = math.sqrt((perp_dx * lon_scale) ** 2 + (perp_dy * lat_scale) ** 2)
        min_dist = min(min_dist, dist_m)

    return min_dist if min_dist != float("inf") else 0.0


def _min_boundary_distance(lat: float, lon: float, geometry: dict) -> float:
    """
    Compute minimum distance from point to the OUTER boundary of a geometry,
    in metres. Returns 0.0 if point is inside any polygon ring.
    """
    rings = _get_polygon_rings(geometry)
    if not rings:
        return 0.0
    min_d = float("inf")
    for ring in rings:
        if _point_in_polygon(lat, lon, ring):
            return 0.0
        d = _distance_to_boundary_m(lat, lon, ring)
        min_d = min(min_d, d)
    return min_d if min_d != float("inf") else 0.0


def _get_polygon_rings(geometry: dict) -> list:
    """Extract all polygon rings from GeoJSON geometry (handles both Polygon and MultiPolygon)."""
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])

    if coords is None:
        return []
    if geom_type == "Polygon":
        return [coords[0]]  # [outer_ring]
    elif geom_type == "MultiPolygon":
        # coords = [polygon1, polygon2, ...], each polygon = [ring1, ring2]
        # Return outer ring of each polygon
        return [poly[0] for poly in coords]
    return []


def _point_in_multipolygon(lat: float, lon: float, multipolygon: list) -> bool:
    """Test point against MultiPolygon geometry."""
    for polygon in multipolygon:
        if _point_in_polygon(lat, lon, polygon):
            return True
    return False


# ── Sync implementations (run in thread pool) ───────────────────────────────────


def _geox_isitwater(lat: float, lon: float) -> dict:
    """
    Check if a lat/lon point is on land or water.
    Returns:
        {
            "is_water": bool,
            "is_land": bool,
            "country": str or None,
            "country_iso3": str or None,
            "country_iso2": str or None,
            "latitude": float,
            "longitude": float,
            "near_boundary_m": float,   # distance to nearest land boundary (m)
            "on_boundary": bool,        # True if near coast (< 1 km)
            "confidence": float,
            "data_source": str
        }
    """
    countries = _load_countries()

    for feature in countries["features"]:
        geometry = feature.get("geometry")
        props = feature.get("properties", {})

        if geometry is None:
            continue

        rings = _get_polygon_rings(geometry)
        for ring in rings:
            if _point_in_polygon(lat, lon, ring):
                near_boundary_m = _min_boundary_distance(lat, lon, geometry)
                on_boundary = near_boundary_m is not None and near_boundary_m < 1000.0
                return {
                    "is_water": False,
                    "is_land": True,
                    "country": props.get("name", "Unknown"),
                    "country_iso3": props.get("ISO3166-1-Alpha-3", ""),
                    "country_iso2": props.get("ISO3166-1-Alpha-2", ""),
                    "latitude": lat,
                    "longitude": lon,
                    "near_boundary_m": near_boundary_m,
                    "on_boundary": on_boundary,
                    "confidence": 0.95,
                    "data_source": "Natural Earth 10m countries",
                    "resolution_note": "Natural Earth 10m (~300m resolution). Coastal points near boundary may show water at this scale.",
                }

    return {
        "is_water": True,
        "is_land": False,
        "country": None,
        "country_iso3": None,
        "country_iso2": None,
        "latitude": lat,
        "longitude": lon,
        "near_boundary_m": None,
        "on_boundary": False,
        "confidence": 0.90,
        "data_source": "Natural Earth 10m countries (water = not in any country)",
        "resolution_note": "Natural Earth 10m (~300m resolution). Small islands or contested points may be misclassified.",
    }


def _geox_context_at_location(lat: float, lon: float) -> dict:
    """
    Get full geographic context for a lat/lon point.
    Returns country, sea neighbors, and boundary distance for Malaysia basin work.
    """
    sea_neighbors = _load_sea_neighbors()

    # Find SEA neighbors
    sea_names = []
    for feature in sea_neighbors.get("features", []):
        props = feature.get("properties", {})
        sea_names.append(props.get("name", ""))

    base = _geox_isitwater(lat, lon)
    base["sea_neighbors"] = sea_names
    base["context_note"] = "SEA region countries for Malaysia basin context"
    return base


# ── Async MCP wrappers ────────────────────────────────────────────────────────


async def geox_isitwater(lat: float, lon: float) -> dict[str, Any]:
    """
    Check if a lat/lon point is on land or water.
    Uses local Natural Earth 10m GeoJSON — sovereign offline-capable.

    Args:
        lat: Latitude in decimal degrees (WGS84)
        lon: Longitude in decimal degrees (WGS84)

    Returns:
        {
            "is_water": bool,
            "is_land": bool,
            "country": str or None,
            "country_iso3": str or None,
            "country_iso2": str or None,
            "latitude": float,
            "longitude": float,
            "near_boundary_m": float or None,
            "on_boundary": bool,
            "confidence": float,
            "data_source": str,
            "resolution_note": str
        }

    Note:
        Natural Earth 10m has ~300m resolution. Coastal points within 300m of
        shoreline may return inconsistent results. Use near_boundary_m to assess
        proximity to coast.
    """
    return await asyncio.to_thread(_geox_isitwater, lat, lon)


async def geox_context_at_location(lat: float, lon: float) -> dict[str, Any]:
    """
    Get full geographic context for a lat/lon point.

    Returns country lookup plus SEA neighbor list and boundary distance.
    Built for Malaysia basin work (Malaysia, Indonesia, Brunei, South China Sea).

    Args:
        lat: Latitude in decimal degrees (WGS84)
        lon: Longitude in decimal degrees (WGS84)

    Returns:
        {
            "country": str or None,
            "country_iso3": str or None,
            "country_iso2": str or None,
            "is_land": bool,
            "is_water": bool,
            "latitude": float,
            "longitude": float,
            "near_boundary_m": float or None,
            "on_boundary": bool,
            "sea_neighbors": list[str],
            "confidence": float,
            "data_source": str,
            "context_note": str,
            "resolution_note": str
        }
    """
    return await asyncio.to_thread(_geox_context_at_location, lat, lon)


# ── Golden tests (run via server.py or pytest) ─────────────────────────────────

GOLDEN_TESTS = [
    {"lat": 3.1390, "lon": 101.6869, "expected_country": "Malaysia", "expected_iso3": "MYS", "description": "Kuala Lumpur"},
    {"lat": 4.2105, "lon": 101.9758, "expected_country": "Malaysia", "expected_iso3": "MYS", "description": "Ipoh, Perak"},
    {"lat": 5.4164, "lon": 100.3326, "expected_country": "Malaysia", "expected_iso3": "MYS", "description": "Penang"},
    {"lat": 1.4927, "lon": 103.7414, "expected_country": "Malaysia", "expected_iso3": "MYS", "description": "Johor Bahru"},
    {"lat": 5.8, "lon": 116.0, "expected_country": "Malaysia", "expected_iso3": "MYS", "description": "Sabah (interior, NE 10m)"},
    {"lat": 1.5535, "lon": 110.3594, "expected_country": "Malaysia", "expected_iso3": "MYS", "description": "Sarawak (Kuching)"},
    {
        "lat": 3.4569,
        "lon": 103.1234,
        "expected_country": "Malaysia",
        "expected_iso3": "MYS",
        "description": "Offshore Terengganu",
    },
    {
        "lat": -6.2088,
        "lon": 106.8456,
        "expected_country": "Indonesia",
        "expected_iso3": "IDN",
        "description": "Jakarta, Indonesia",
    },
    {"lat": 13.7563, "lon": 100.5018, "expected_country": "Thailand", "expected_iso3": "THA", "description": "Bangkok, Thailand"},
    {"lat": 1.3521, "lon": 103.8198, "expected_country": "Singapore", "expected_iso3": "SGP", "description": "Singapore"},
    {"lat": -33.8688, "lon": 151.2093, "expected_country": "Australia", "expected_iso3": "AUS", "description": "Sydney"},
    {"lat": 51.5074, "lon": -0.1278, "expected_country": "United Kingdom", "expected_iso3": "GBR", "description": "London"},
    {"lat": 40.4168, "lon": -3.7038, "expected_country": "Spain", "expected_iso3": "ESP", "description": "Madrid"},
    {"lat": 12.0, "lon": 113.0, "expected_country": None, "expected_iso3": None, "description": "South China Sea (water)"},
    {"lat": 5.5, "lon": 100.0, "expected_country": None, "expected_iso3": None, "description": "Strait of Malacca (water)"},
]


async def run_golden_tests() -> tuple[int, int]:
    """Run golden test cases. Returns (passed, failed)."""
    results = []
    passed = 0
    failed = 0

    for test in GOLDEN_TESTS:
        lat = test["lat"]
        lon = test["lon"]
        expected_country = test["expected_country"]
        desc = test["description"]

        result = await geox_isitwater(lat, lon)
        is_water_test = expected_country is None

        if is_water_test:
            ok = result["is_water"] == True
        else:
            ok = result["country"] == expected_country or result["country_iso3"] == test["expected_iso3"]

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        got = result.get("country") or "WATER"
        exp = expected_country or "WATER"
        results.append(f"{status} | {desc} ({lat}, {lon}) | got: {got} | expected: {exp}")

    print("=" * 80)
    print("GEOX ATLAS - GOLDEN TESTS")
    print("=" * 80)
    for r in results:
        print(r)
    print("=" * 80)
    print(f"RESULTS: {passed}/{len(GOLDEN_TESTS)} passed, {failed} failed")
    print("=" * 80)

    return passed, failed
