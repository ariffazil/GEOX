"""geox_h3_spatial_index — H3 Hexagonal Spatial Index.

Uniform-adjacency hex grid spatial indexing. Convert lat/lng to H3 cells,
aggregate points by resolution, query spatial relationships.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("geox.canonical.h3_spatial_index")


def _to_h3_cell(lat: float, lng: float, resolution: int = 7) -> str:
    """Convert lat/lng to H3 cell index."""
    import h3

    return h3.latlng_to_cell(lat, lng, resolution)


def _h3_cell_center(h3_cell: str) -> dict[str, float]:
    """Get centre lat/lng of an H3 cell."""
    import h3

    lat, lng = h3.cell_to_latlng(h3_cell)
    return {"lat": lat, "lng": lng}


def _h3_cell_boundary(h3_cell: str) -> list[dict[str, float]]:
    """Return polygon boundary of H3 cell."""
    import h3

    coords = h3.cell_to_boundary(h3_cell)
    return [{"lat": lat, "lng": lng} for lat, lng in coords]


def _h3_k_ring(h3_cell: str, k: int = 1) -> list[str]:
    """Return hexagonal k-ring neighbours."""
    import h3

    return list(h3.grid_disk(h3_cell, k))


def _h3_polygon_fill(polygon: list[dict], resolution: int = 7) -> list[str]:
    """Fill polygon with H3 cells."""
    import h3

    coords = [(p["lat"], p["lng"]) for p in polygon]
    # Ensure counter-clockwise
    return list(h3.polygon_to_cells(h3.Polygon(coords), resolution))


def _h3_resolution_info(res: int) -> dict[str, Any]:
    """Get statistics for a given H3 resolution."""
    import h3

    return {
        "resolution": res,
        "avg_area_km2": round(h3.average_hexagon_area(res, "km2"), 6),
        "avg_edge_length_km": round(h3.average_hexagon_edge_length(res, "km"), 6),
        "total_cells": h3.get_num_cells(res),
    }


async def geox_h3_spatial_index(
    mode: str = "latlng_to_cell",
    lat: float | None = None,
    lng: float | None = None,
    resolution: int = 7,
    h3_cell: str | None = None,
    points: list[dict] | str | None = None,
    k: int = 1,
    polygon: list[dict] | str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """H3 hexagonal spatial indexing toolkit.

    Modes:
        latlng_to_cell  — Convert lat/lng to H3 cell index.
        cell_center     — Get centre lat/lng of an H3 cell.
        cell_boundary   — Get polygon boundary of an H3 cell.
        k_ring          — Return hexagonal k-ring neighbours.
        polygon_fill    — Fill polygon with H3 cells.
        cell_info       — Get H3 resolution statistics.
        aggregate       — Aggregate points into H3 cells by resolution.
        distance        — H3 distance between two cells.

    Args:
        mode: Operation mode.
        lat: Latitude in decimal degrees.
        lng: Longitude in decimal degrees.
        resolution: H3 resolution (0-15). Default 7 (~5 km² hexes).
        h3_cell: H3 cell index string.
        points: List of {lat, lng, ...} dicts for aggregation.
        k: k-ring radius (number of rings).
        polygon: List of {lat, lng} dicts forming a polygon.
        session_id, actor_id, trace_id: Federation audit.

    Returns:
        dict with results.
    """
    _ = (session_id, actor_id, trace_id)

    if isinstance(points, str):
        points = json.loads(points)
    if isinstance(polygon, str):
        polygon = json.loads(polygon)

    try:
        import h3

        if mode == "latlng_to_cell":
            if lat is None or lng is None:
                return {"ok": False, "error": "lat and lng required"}
            cell = _to_h3_cell(lat, lng, resolution)
            return {
                "ok": True,
                "h3_cell": cell,
                "lat": lat,
                "lng": lng,
                "resolution": resolution,
            }

        elif mode == "cell_center":
            if not h3_cell:
                return {"ok": False, "error": "h3_cell required"}
            center = _h3_cell_center(h3_cell)
            return {"ok": True, "h3_cell": h3_cell, "center": center}

        elif mode == "cell_boundary":
            if not h3_cell:
                return {"ok": False, "error": "h3_cell required"}
            boundary = _h3_cell_boundary(h3_cell)
            return {"ok": True, "h3_cell": h3_cell, "boundary": boundary}

        elif mode == "k_ring":
            if not h3_cell:
                return {"ok": False, "error": "h3_cell required"}
            cells = _h3_k_ring(h3_cell, k)
            return {"ok": True, "h3_cell": h3_cell, "k": k, "cells": cells, "count": len(cells)}

        elif mode == "polygon_fill":
            if not polygon:
                return {"ok": False, "error": "polygon required"}
            cells = _h3_polygon_fill(polygon, resolution)
            return {"ok": True, "cells": cells, "count": len(cells), "resolution": resolution}

        elif mode == "cell_info":
            info = _h3_resolution_info(resolution)
            return {"ok": True, **info}

        elif mode == "aggregate":
            if not points:
                return {"ok": False, "error": "points list required"}
            agg: dict[str, int] = {}
            for pt in points:
                cell = _to_h3_cell(pt["lat"], pt["lng"], resolution)
                agg[cell] = agg.get(cell, 0) + 1
            return {
                "ok": True,
                "n_points": len(points),
                "n_cells": len(agg),
                "resolution": resolution,
                "aggregation": agg,
            }

        elif mode == "distance":
            if not h3_cell:
                return {"ok": False, "error": "h3_cell required"}
            # For distance mode, we interpret h3_cell as two cells separated by '|'
            if "|" in h3_cell:
                cell_a, cell_b = h3_cell.split("|", 1)
            else:
                return {"ok": False, "error": "distance mode: h3_cell must be 'cellA|cellB'"}
            dist = h3.grid_distance(cell_a, cell_b)
            return {"ok": True, "cell_a": cell_a, "cell_b": cell_b, "distance_cells": dist}

        else:
            return {
                "ok": False,
                "error": f"Unknown mode: {mode}",
                "valid_modes": [
                    "latlng_to_cell",
                    "cell_center",
                    "cell_boundary",
                    "k_ring",
                    "polygon_fill",
                    "cell_info",
                    "aggregate",
                    "distance",
                ],
            }

    except ImportError:
        return {"ok": False, "error": "h3 package not installed", "epistemic": "TOOL_UNAVAILABLE"}
    except Exception as e:
        logger.exception("H3 spatial index failed")
        return {"ok": False, "error": str(e)}
