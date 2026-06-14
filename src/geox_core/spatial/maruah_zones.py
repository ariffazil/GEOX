"""
MARUAH Zone Polygons — Community/Indigenous Territory Overlay
================================================================
Returns polygon geometries for known community/indigenous territories
that intersect a given bounding box. Used by geox_map_context_scene
to render MARUAH-sensitive regions as GeoJSON overlays.

This is a STUB implementation. Real polygon data should come from:
  - JKOG (Jawatankuasa Kawasan Orang Asli) gazetted boundaries
  - NAP (Native Adjudication Process) polygons from state survey
  - Community-mapped territories via participatory GIS

Until then, this module returns an empty list — the MARUAH flag still
fires correctly from _check_maruah_territory() in map_context.py,
but no polygon geometry is rendered.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.spatial.maruah_zones")

# Well-known community territories (stub data for known basins)
# Format: {name: {"risk": str, "bbox": [min_lon, min_lat, max_lon, max_lat]}}
_KNOWN_TERRITORIES: dict[str, dict[str, Any]] = {
    "Sabah_Interior": {
        "risk": "HIGH",
        "bbox": [115.5, 5.0, 117.5, 6.5],
        "name": "Sabah Interior Native Territories",
    },
    "Sarawak_Barum": {
        "risk": "HIGH",
        "bbox": [109.5, 1.0, 111.5, 3.0],
        "name": "Sarawak Baram River Basin Communities",
    },
    "Peninsular_OrangAsli": {
        "risk": "MEDIUM",
        "bbox": [101.0, 3.0, 102.5, 4.5],
        "name": "Peninsular Malaysia Orang Asli Settlements",
    },
}


def get_maruah_zone_polygons(bbox: list[float], crs: str = "EPSG:4326") -> list[dict[str, Any]]:
    """Return GeoJSON-style polygon features for MARUAH-sensitive zones
    that intersect the given bounding box.

    Args:
        bbox: [min_lon, min_lat, max_lon, max_lat]
        crs: Coordinate reference system (default EPSG:4326)

    Returns:
        List of GeoJSON Feature objects with simple bounding-box geometries.
        Each feature has:
          - type: "Feature"
          - properties: {name, risk, description}
          - geometry: {type: "Polygon", coordinates: [[...]]}
    """
    zones: list[dict[str, Any]] = []

    for zone_id, info in _KNOWN_TERRITORIES.items():
        zb = info["bbox"]
        # Check bbox intersection
        if (bbox[0] <= zb[2] and bbox[2] >= zb[0] and
            bbox[1] <= zb[3] and bbox[3] >= zb[1]):
            # Intersecting — emit as simple bbox polygon
            zones.append({
                "type": "Feature",
                "properties": {
                    "name": info.get("name", zone_id),
                    "type": "maruah_zone",
                    "risk": info.get("risk", "MEDIUM"),
                    "description": f"MARUAH-sensitive territory: {info.get('name', zone_id)}",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [zb[0], zb[1]],
                        [zb[2], zb[1]],
                        [zb[2], zb[3]],
                        [zb[0], zb[3]],
                        [zb[0], zb[1]],
                    ]],
                },
            })
            logger.info(f"MARUAH zone intersected: {info.get('name', zone_id)} (risk={info['risk']})")

    if not zones:
        logger.debug(f"No MARUAH zones intersect bbox={bbox}")

    return zones
