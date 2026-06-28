"""
geometry.py — EGS Geometry Engine
====================================
GEOX EGS: Geometric primitives, spatial queries, distance computations.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import math
from typing import Any

from geox.egs.models.entities import Point3D, SurfaceMesh3D


# ═══════════════════════════════════════════════════════════════════════════════
# Distance & Spatial Computations
# ═══════════════════════════════════════════════════════════════════════════════


def haversine_distance(p1: Point3D, p2: Point3D) -> float:
    """Great-circle distance between two geographic points in meters."""
    R = 6371000.0  # Earth radius in meters
    lat1, lon1 = math.radians(p1.y), math.radians(p1.x)
    lat2, lon2 = math.radians(p2.y), math.radians(p2.x)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def euclidean_distance_3d(p1: Point3D, p2: Point3D) -> float:
    """3D Euclidean distance. Only meaningful in projected CRS."""
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dz = p1.z - p2.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def vertical_distance(p1: Point3D, p2: Point3D) -> float:
    """Vertical separation between two points."""
    return abs(p1.z - p2.z)


# ═══════════════════════════════════════════════════════════════════════════════
# Bounding Box Operations
# ═══════════════════════════════════════════════════════════════════════════════


def bounding_box_contains(bbox: tuple[float, float, float, float], point: Point3D) -> bool:
    """Check if a point falls within a bounding box (min_lon, min_lat, max_lon, max_lat)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= point.x <= max_lon and min_lat <= point.y <= max_lat


def bounding_box_intersects(
    bbox1: tuple[float, float, float, float],
    bbox2: tuple[float, float, float, float],
) -> bool:
    """Check if two bounding boxes intersect."""
    min_lon1, min_lat1, max_lon1, max_lat1 = bbox1
    min_lon2, min_lat2, max_lon2, max_lat2 = bbox2
    return not (max_lon1 < min_lon2 or max_lon2 < min_lon1 or max_lat1 < min_lat2 or max_lat2 < min_lat1)


def bounding_box_area(bbox: tuple[float, float, float, float]) -> float:
    """Approximate area of a bounding box in square km (at equator)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    lon_span = abs(max_lon - min_lon)
    lat_span = abs(max_lat - min_lat)
    # Rough conversion: 1 deg ≈ 111 km
    area_km2 = (lon_span * 111) * (lat_span * 111)
    return area_km2


# ═══════════════════════════════════════════════════════════════════════════════
# Surface Mesh Operations
# ═══════════════════════════════════════════════════════════════════════════════


def mesh_bounding_box(mesh: SurfaceMesh3D) -> tuple[float, float, float, float, float, float]:
    """Compute 3D bounding box of a surface mesh: (min_x, max_x, min_y, max_y, min_z, max_z)."""
    if not mesh.vertices:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    xs = [v.x for v in mesh.vertices]
    ys = [v.y for v in mesh.vertices]
    zs = [v.z for v in mesh.vertices]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def mesh_center(mesh: SurfaceMesh3D) -> Point3D | None:
    """Compute the centroid of a surface mesh."""
    if not mesh.vertices:
        return None
    n = len(mesh.vertices)
    avg_x = sum(v.x for v in mesh.vertices) / n
    avg_y = sum(v.y for v in mesh.vertices) / n
    avg_z = sum(v.z for v in mesh.vertices) / n
    first = mesh.vertices[0]
    return Point3D(x=avg_x, y=avg_y, z=avg_z, crs=first.crs, domain=first.domain)


# ═══════════════════════════════════════════════════════════════════════════════
# Spatial Index (naive — replace with R-tree for production)
# ═══════════════════════════════════════════════════════════════════════════════


class SpatialIndex:
    """Simple spatial index for point-in-polygon / proximity queries.

    Intentionally naive. For production use, replace with R-tree (rtree/geopandas).
    """

    def __init__(self) -> None:
        self._points: list[tuple[str, Point3D]] = []

    def add(self, entity_id: str, point: Point3D) -> None:
        self._points.append((entity_id, point))

    def query_radius(self, center: Point3D, radius_m: float) -> list[tuple[str, float]]:
        """Find all entities within radius_m of center. Returns [(id, dist_m), ...]."""
        results: list[tuple[str, float]] = []
        for entity_id, point in self._points:
            dist = haversine_distance(center, point)
            if dist <= radius_m:
                results.append((entity_id, dist))
        return sorted(results, key=lambda x: x[1])

    def query_bbox(self, bbox: tuple[float, float, float, float]) -> list[tuple[str, Point3D]]:
        """Find all entities within bounding box."""
        results: list[tuple[str, Point3D]] = []
        for entity_id, point in self._points:
            if bounding_box_contains(bbox, point):
                results.append((entity_id, point))
        return results
