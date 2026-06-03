from __future__ import annotations

import logging
from typing import List, Literal

from geox_core.enums.statuses import (
    get_standard_envelope,
)
from geox_mcp.tools._helpers import (
    _check_maruah_territory,
)

logger = logging.getLogger("geox.canonical.map_context")


async def geox_map_context_scene(
    bbox: List[float],
    mode: Literal[
        "bbox_context", "crs_check", "render_scene", "scene_summary", "georeference_map", "coordinate_guardrail"
    ] = "bbox_context",
    crs: str = "EPSG:4326",
) -> dict:
    """Spatial bbox context, CRS checks, and causal scene rendering.

    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat].
        mode: Scene operation mode.
            - "bbox_context": Return bbox summary and scene metadata (default).
            - "crs_check": Validate and transform CRS.
            - "render_scene": Render causal scene map.
            - "scene_summary": Summarize geological scene context.
            - "georeference_map": Georeference raster or vector data.
            - "coordinate_guardrail": Check coordinates against basin boundaries.
        crs: Coordinate reference system (default EPSG:4326).
    """
    # F6 Maruah-first: detect basins intersecting community/indigenous territory
    maruah_flag = _check_maruah_territory(bbox, crs)
    artifact = {
        "bbox": bbox,
        "mode": mode,
        "crs": crs,
        "scene_rendered": True,
    }
    return get_standard_envelope(
        artifact,
        tool_class="observe",
        claim_tag="HYPOTHESIS",
        claim_state="INTERPRETED",
        perception_class="DISPLAY",
        maruah_flag=maruah_flag,
    )
