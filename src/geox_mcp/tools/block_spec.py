"""
GEOX Reservoir Block Specification — polygonal boundary, area, metadata.

Defines a structured reservoir block specification from corner-point or
polygon coordinates. Computes geometry (centroid, bbox, area), validates
polygon closure, and returns a structured block specification envelope.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

TOOL_NAME = "geox_block_spec"

_LAT_KM_PER_DEG = 111.0


def _compute_centroid(coords: list[dict[str, float]]) -> dict[str, float]:
    lat_sum = sum(c["lat"] for c in coords)
    lon_sum = sum(c["lon"] for c in coords)
    n = len(coords)
    return {"lat": lat_sum / n, "lon": lon_sum / n}


def _compute_bbox(coords: list[dict[str, float]]) -> dict[str, float]:
    lats = [c["lat"] for c in coords]
    lons = [c["lon"] for c in coords]
    return {
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lon": min(lons),
        "max_lon": max(lons),
    }


def _shoelace_area_km2(coords: list[dict[str, float]]) -> float:
    n = len(coords)
    if n < 3:
        return 0.0
    centroid = _compute_centroid(coords)
    cos_lat = math.cos(math.radians(centroid["lat"]))
    area_deg2 = 0.0
    for i in range(n):
        j = (i + 1) % n
        area_deg2 += coords[i]["lon"] * coords[j]["lat"]
        area_deg2 -= coords[j]["lon"] * coords[i]["lat"]
    area_deg2 = abs(area_deg2) / 2.0
    return area_deg2 * (_LAT_KM_PER_DEG**2) * cos_lat


def _is_closed(coords: list[dict[str, float]]) -> bool:
    if len(coords) < 2:
        return False
    first = coords[0]
    last = coords[-1]
    return first["lat"] == last["lat"] and first["lon"] == last["lon"]


def _auto_close(coords: list[dict[str, float]]) -> list[dict[str, float]]:
    if not _is_closed(coords) and len(coords) >= 3:
        closed = list(coords)
        closed.append(dict(coords[0]))
        return closed
    return list(coords)


def _compute_block_hash(name: str, coords: list[dict[str, float]], block_type: str) -> str:
    raw = json.dumps({"name": name, "coordinates": coords, "block_type": block_type}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


async def geox_block_spec(
    name: str,
    coordinates: list[dict[str, float]],
    crs: str = "EPSG:4326",
    description: str | None = None,
    block_type: str = "reservoir",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Define reservoir block specification with polygonal boundary, area, and metadata.

    Creates a structured block specification from corner-point or polygon coordinates.
    Returns block geometry, computed area (km\u00b2), bounding box, centroid, and classification.

    Args:
        name: Block name/identifier.
        coordinates: List of corner points [{"lat": float, "lon": float}, ...].
        crs: Coordinate reference system (default EPSG:4326).
        description: Free text description.
        block_type: Block classification — reservoir, fault_block, compartment, license_block.
        tags: Classification tags.

    Returns:
        Structured dict with block geometry, area, metadata, and validation.
    """
    if not coordinates:
        return {
            "status": "error",
            "error": "No coordinates provided",
            "tool": TOOL_NAME,
        }

    if len(coordinates) < 3:
        return {
            "status": "error",
            "error": f"Minimum 3 points required, got {len(coordinates)}",
            "tool": TOOL_NAME,
        }

    validated_coords = _auto_close(coordinates)
    n_vertices = len(validated_coords)
    closed = _is_closed(validated_coords)
    centroid = _compute_centroid(validated_coords)
    bbox = _compute_bbox(validated_coords)
    area_km2 = _shoelace_area_km2(validated_coords)
    block_hash = _compute_block_hash(name, validated_coords, block_type)

    return {
        "block_name": name,
        "block_type": block_type,
        "coordinates": validated_coords,
        "centroid": centroid,
        "bbox": bbox,
        "area_km2": round(area_km2, 6),
        "crs": crs,
        "n_vertices": n_vertices,
        "is_closed": closed,
        "description": description,
        "tags": tags or [],
        "block_hash": block_hash,
        "_envelope": {
            "tool": TOOL_NAME,
            "evidence_floor": "DERIVED",
            "method": "Shoelace formula (area) + coordinate averaging (centroid/bbox) + SHA-256 (hash)",
            "limitations": [
                "Area approximation uses cos(lat) scaling at centroid — accurate to ~1% for blocks < 2 degrees extent",
                "Polygon auto-closed if first != last vertex",
                "Flat-earth approximation; use projected CRS for high-latitude precision",
            ],
            "status": "success",
        },
    }
