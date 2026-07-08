"""
GEOX Spatial Intersection — geometry intersection for geological boundaries.

Computes intersection between two geological spatial objects (polygons,
lines, or points). Pure-math geometry — no shapely dependency needed.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import math
import logging
from typing import Any

logger = logging.getLogger("geox.spatial_intersection")

TOOL_NAME = "geox_spatial_intersection"

# ── Helpers ────────────────────────────────────────────────────────────────


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _shoelace_area(coords: list[tuple[float, float]]) -> float:
    """Polygon area in square km using haversine edge lengths."""
    if len(coords) < 3:
        return 0.0
    n = len(coords)
    area_m2 = 0.0
    for i in range(n):
        j = (i + 1) % n
        x1, y1 = coords[i]
        x2, y2 = coords[j]
        area_m2 += math.radians(x1) * math.radians(y2)
        area_m2 -= math.radians(x2) * math.radians(y1)
    area_m2 = abs(area_m2) * (6371000.0**2) / 2.0
    return area_m2 / 1e6  # km²


def _point_in_polygon(lat: float, lon: float, poly: list[tuple[float, float]]) -> bool:
    """Ray casting point-in-polygon test."""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        yi, xi = poly[i]
        yj, xj = poly[j]
        if ((yi > lon) != (yj > lon)) and (lat < (xj - xi) * (lon - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _polygon_intersection_area(
    poly1: list[tuple[float, float]],
    poly2: list[tuple[float, float]],
    grid_samples: int = 50,
) -> float:
    """Approximate intersection area via grid sampling."""
    if len(poly1) < 3 or len(poly2) < 3:
        return 0.0

    lats = [p[0] for p in poly1] + [p[0] for p in poly2]
    lons = [p[1] for p in poly1] + [p[1] for p in poly2]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    inside_count = 0
    total_count = 0

    for i in range(grid_samples):
        frac_lat = (i + 0.5) / grid_samples
        lat = lat_min + frac_lat * (lat_max - lat_min)
        for j in range(grid_samples):
            frac_lon = (j + 0.5) / grid_samples
            lon = lon_min + frac_lon * (lon_max - lon_min)
            if _point_in_polygon(lat, lon, poly1) and _point_in_polygon(lat, lon, poly2):
                inside_count += 1
            total_count += 1

    bbox_area_km2 = _haversine_km(lat_min, lon_min, lat_min, lon_max) * _haversine_km(lat_min, lon_min, lat_max, lon_min)
    ratio = inside_count / total_count if total_count > 0 else 0.0
    return bbox_area_km2 * ratio


def _intersects_any(poly: list[tuple[float, float]], pts: list[tuple[float, float]]) -> bool:
    """Check if any point from pts lies inside poly."""
    for pt in pts:
        if _point_in_polygon(pt[0], pt[1], poly):
            return True
    return False


def _centroid(coords: list[tuple[float, float]]) -> tuple[float, float]:
    """Simple centroid of coordinate list."""
    if not coords:
        return (0.0, 0.0)
    n = len(coords)
    return (sum(c[0] for c in coords) / n, sum(c[1] for c in coords) / n)


def _classify_overlap(ratio: float) -> str:
    """Classify overlap ratio into semantic buckets."""
    if ratio >= 0.9:
        return "ALMOST_IDENTICAL"
    elif ratio >= 0.5:
        return "SIGNIFICANT_OVERLAP"
    elif ratio >= 0.2:
        return "PARTIAL_OVERLAP"
    elif ratio > 0.0:
        return "MINOR_OVERLAP"
    return "NO_OVERLAP"


# ── Main ───────────────────────────────────────────────────────────────────


def geox_spatial_intersection(
    subject: dict[str, Any],
    target: dict[str, Any],
    mode: str = "intersection",
    crs: str = "EPSG:4326",
) -> dict[str, Any]:
    """Compute spatial intersection between geological boundaries.

    Returns intersection geometry, area (km²), overlap ratio, and classification.
    Supports polygon-polygon, point-polygon, and line-polygon intersection tests.

    Layer Invariant (Eureka 3): This computes spatial geometry. It does NOT
    regrade geological interpretation confidence. GEOX C stays C.
    """
    # Validate input structure
    for name, geom in [("subject", subject), ("target", target)]:
        if not isinstance(geom, dict):
            return {
                "status": "error",
                "error": f"{name} must be a dict with 'type' and 'coordinates'",
                "tool": TOOL_NAME,
            }
        if "type" not in geom or "coordinates" not in geom:
            return {
                "status": "error",
                "error": f"{name} must contain 'type' and 'coordinates'",
                "tool": TOOL_NAME,
            }
        if geom["type"] not in ("polygon", "point", "line"):
            return {
                "status": "error",
                "error": f"{name} type must be 'polygon', 'point', or 'line', got '{geom['type']}'",
                "tool": TOOL_NAME,
            }
        coords = geom["coordinates"]
        if not isinstance(coords, list) or len(coords) == 0:
            return {
                "status": "error",
                "error": f"{name} coordinates must be a non-empty list",
                "tool": TOOL_NAME,
            }
        for pt in coords:
            if not isinstance(pt, dict) or "lat" not in pt or "lon" not in pt:
                return {
                    "status": "error",
                    "error": f"{name} coordinate items must be dicts with 'lat' and 'lon'",
                    "tool": TOOL_NAME,
                }

    sub_type = subject["type"]
    tgt_type = target["type"]

    # Convert to (lat, lon) tuples
    sub_pts = [(p["lat"], p["lon"]) for p in subject["coordinates"]]
    tgt_pts = [(p["lat"], p["lon"]) for p in target["coordinates"]]

    sub_area_km2 = _shoelace_area(sub_pts) if sub_type == "polygon" else 0.0
    tgt_area_km2 = _shoelace_area(tgt_pts) if tgt_type == "polygon" else 0.0

    # Mode dispatch
    if mode == "contains":
        if sub_type == "polygon" and tgt_type == "point":
            contained = _point_in_polygon(tgt_pts[0][0], tgt_pts[0][1], sub_pts)
            return {
                "status": "success",
                "tool": TOOL_NAME,
                "intersects": contained,
                "mode": "contains",
                "classification": "CONTAINS" if contained else "DOES_NOT_CONTAIN",
                "subject_type": sub_type,
                "target_type": tgt_type,
            }
        elif sub_type == "polygon" and tgt_type == "polygon":
            tgt_centroid = _centroid(tgt_pts)
            contained = _point_in_polygon(tgt_centroid[0], tgt_centroid[1], sub_pts)
            return {
                "status": "success",
                "tool": TOOL_NAME,
                "intersects": contained,
                "mode": "contains",
                "classification": "CONTAINS" if contained else "DOES_NOT_CONTAIN",
                "subject_type": sub_type,
                "target_type": tgt_type,
            }
        else:
            return {
                "status": "error",
                "error": "contains mode requires polygon subject",
                "tool": TOOL_NAME,
            }

    elif mode == "touches":
        if sub_type == "polygon" and tgt_type == "point":
            touches = _point_in_polygon(tgt_pts[0][0], tgt_pts[0][1], sub_pts)
        elif sub_type == "polygon" and tgt_type == "line":
            touches = _intersects_any(sub_pts, tgt_pts)
        elif sub_type == "polygon" and tgt_type == "polygon":
            touches = _intersects_any(sub_pts, tgt_pts) or _intersects_any(tgt_pts, sub_pts)
        else:
            touches = False
        return {
            "status": "success",
            "tool": TOOL_NAME,
            "intersects": touches,
            "mode": "touches",
            "subject_type": sub_type,
            "target_type": tgt_type,
        }

    elif mode == "overlap_ratio":
        if sub_type == "polygon" and tgt_type == "polygon":
            intersection_area = _polygon_intersection_area(sub_pts, tgt_pts)
            min_area = min(sub_area_km2, tgt_area_km2) if sub_area_km2 > 0 and tgt_area_km2 > 0 else 0.0
            ratio = intersection_area / min_area if min_area > 0 else 0.0
            ratio = min(ratio, 1.0)
        else:
            intersection_area = 0.0
            ratio = 0.0
        return {
            "status": "success",
            "tool": TOOL_NAME,
            "mode": "overlap_ratio",
            "overlap_ratio": round(ratio, 4),
            "intersection_area_km2": round(intersection_area, 4),
            "subject_area_km2": round(sub_area_km2, 4),
            "target_area_km2": round(tgt_area_km2, 4),
            "classification": _classify_overlap(ratio),
            "subject_type": sub_type,
            "target_type": tgt_type,
        }

    # Default: intersection test
    if sub_type == "point" and tgt_type == "polygon":
        intersects = _point_in_polygon(sub_pts[0][0], sub_pts[0][1], tgt_pts)
    elif sub_type == "polygon" and tgt_type == "point":
        intersects = _point_in_polygon(tgt_pts[0][0], tgt_pts[0][1], sub_pts)
    elif sub_type == "polygon" and tgt_type == "polygon":
        intersection_area = _polygon_intersection_area(sub_pts, tgt_pts)
        intersects = intersection_area > 0.0
        min_area = min(sub_area_km2, tgt_area_km2) if sub_area_km2 > 0 and tgt_area_km2 > 0 else 0.0
        overlap_ratio = min(intersection_area / min_area, 1.0) if min_area > 0 else 0.0
        return {
            "status": "success",
            "tool": TOOL_NAME,
            "mode": "intersection",
            "intersects": intersects,
            "intersection_area_km2": round(intersection_area, 4),
            "subject_area_km2": round(sub_area_km2, 4),
            "target_area_km2": round(tgt_area_km2, 4),
            "overlap_ratio": round(overlap_ratio, 4),
            "classification": _classify_overlap(overlap_ratio),
            "subject_type": sub_type,
            "target_type": tgt_type,
        }
    elif sub_type == "line" and tgt_type == "polygon":
        intersects = _intersects_any(tgt_pts, sub_pts)
    elif sub_type == "polygon" and tgt_type == "line":
        intersects = _intersects_any(sub_pts, tgt_pts)
    else:
        # point-point, point-line, line-line — simple pairwise proximity
        intersects = any(_haversine_km(a[0], a[1], b[0], b[1]) < 0.1 for a in sub_pts for b in tgt_pts)

    return {
        "status": "success",
        "tool": TOOL_NAME,
        "mode": "intersection",
        "intersects": intersects,
        "subject_type": sub_type,
        "target_type": tgt_type,
    }
