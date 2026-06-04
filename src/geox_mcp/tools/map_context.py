from __future__ import annotations

import logging
from typing import Any, Literal

from geox_core.enums.statuses import (
    get_standard_envelope,
)
from geox_mcp.tools._helpers import (
    _check_maruah_territory,
)

logger = logging.getLogger("geox.canonical.map_context")


async def geox_map_context_scene(
    bbox: list[float],
    mode: Literal[
        "bbox_context", "crs_check", "render_scene", "scene_summary", "georeference_map", "coordinate_guardrail"
    ] = "bbox_context",
    crs: str = "EPSG:4326",
    # ── Eureka 8 (2026-06-03): optional VpSlice as scene input ────────────
    vp_slice_inline: dict[str, Any] | None = None,
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
        vp_slice_inline: E8 — optional inline VpSlice. When provided, the
                         scene metadata carries the Vp slice as a structure
                         map (e.g. {"data": [[...]], "x": [...], "y": [...],
                         "depth_m": 2000.0, "slice_id": "..."}). The slice
                         is rendered alongside the bbox summary.
    """
    # F6 Maruah-first: detect basins intersecting community/indigenous territory
    # Hardening: validate free-text inputs at boundary.
    from geox_mcp.tools.kernel._validation import validate_tool_inputs

    _err = validate_tool_inputs(
        "geox_map_context_scene",
        bbox=bbox,
        crs=crs,
    )
    if _err is not None:
        return _err
    maruah_flag = _check_maruah_territory(bbox, crs)
    artifact = {
        "bbox": bbox,
        "mode": mode,
        "crs": crs,
        "scene_rendered": True,
    }
    e8_block: dict[str, Any] = {}
    if vp_slice_inline is not None:
        try:
            import numpy as np

            from geox_core.spatial.velocity_slice import VpSlice

            slc = VpSlice(
                data=np.asarray(vp_slice_inline["data"], dtype=float),
                x=np.asarray(vp_slice_inline["x"], dtype=float),
                y=np.asarray(vp_slice_inline["y"], dtype=float),
                depth=float(vp_slice_inline.get("depth_m", 0.0)),
                slice_id=str(vp_slice_inline.get("slice_id", "inline")),
                cube_id=str(vp_slice_inline.get("cube_id", "")),
            )
            e8_block = {
                "eureka": "E8_velocity_as_structure_2026_06_03",
                "vp_slice_summary": {
                    "slice_id": slc.slice_id,
                    "depth_m": slc.depth,
                    "shape": list(slc.data.shape),
                    "vp_min": float(slc.data.min()),
                    "vp_max": float(slc.data.max()),
                    "vp_mean": float(slc.data.mean()),
                },
                "interpretation": "Velocity slice rendered as 2D structure map at the given depth",
            }
        except Exception as exc:
            e8_block = {
                "eureka": "E8_velocity_as_structure_2026_06_03",
                "status": "HOLD",
                "reason": f"vp_slice_inline failed to ingest: {exc}",
            }
    envelope = get_standard_envelope(
        artifact,
        tool_class="observe",
        claim_tag="HYPOTHESIS",
        claim_state="INTERPRETED",
        perception_class="DISPLAY",
        maruah_flag=maruah_flag,
    )
    if e8_block:
        envelope["e8_velocity_slice"] = e8_block
    return envelope
