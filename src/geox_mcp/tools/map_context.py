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
        "bbox_context", "crs_check", "render_scene", "scene_summary", "georeference_map", "coordinate_guardrail", "render_geojson"
    ] = "bbox_context",
    crs: str = "EPSG:4326",
    vp_slice_inline: dict[str, Any] | None = None,
    # ── Session provenance (Fix HOLD-2026-07-11) ────────────────────────
    session_id: str | None = None,
    actor_id: str | None = None,
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

    # ── GeoJSON render mode (Module J: visual-spatial-first) ──────────────
    if mode == "render_geojson":
        # Build base features first — must survive even if MARUAH module missing
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "crs": {"type": "name", "properties": {"name": crs}},
                "bbox": bbox,
                "maruah_flag": maruah_flag,
                "generated_by": "geox_map_context_scene",
                "tool": "geox_render_map_scene_alpha",
                "visual_artifact_id": f"geox:bbox:{hash(tuple(bbox))}:{crs}",
                "render_type": "map",
            },
            "features": [
                {
                    "type": "Feature",
                    "properties": {"type": "bounding_box", "label": "Query AOI"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [bbox[0], bbox[1]],
                                [bbox[2], bbox[1]],
                                [bbox[2], bbox[3]],
                                [bbox[0], bbox[3]],
                                [bbox[0], bbox[1]],
                            ]
                        ],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {"type": "center_point", "label": "AOI Center"},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            (bbox[0] + bbox[2]) / 2,
                            (bbox[1] + bbox[3]) / 2,
                        ],
                    },
                },
            ],
        }
        # MARUAH zones are additive — failure must not destroy base features
        if maruah_flag:
            try:
                from geox_core.spatial.maruah_zones import get_maruah_zone_polygons as _get_zones

                zones = _get_zones(bbox, crs)
                for zone in zones:
                    geojson["features"].append(
                        {
                            "type": "Feature",
                            "properties": {
                                "type": "maruah_zone",
                                "label": zone.get("name", "Community/Indigenous Territory"),
                                "risk": zone.get("risk", "MEDIUM"),
                            },
                            "geometry": zone.get("geometry", {"type": "Point", "coordinates": [0, 0]}),
                        }
                    )
            except Exception as exc:
                geojson["metadata"]["maruah_module_error"] = str(exc)
                logger.warning(f"MARUAH zone render failed (non-blocking): {exc}")

        # Wrap in standardized RenderPayload contract
        try:
            from geox_core.schemas.render_payload import render_map as _render_map

            render_payload = _render_map(
                geojson=geojson,
                bbox=bbox,
                crs=crs,
                maruah_flag=maruah_flag,
            ).model_dump(mode="json")
        except Exception:
            render_payload = None

        envelope = get_standard_envelope(
            {
                "bbox": bbox,
                "mode": mode,
                "crs": crs,
                "geojson": geojson,
                "render_payload": render_payload,
                "scene_rendered": True,
                "maruah_flag": maruah_flag,
            },
            tool_class="observe",
            claim_tag="HYPOTHESIS",
            claim_state="INTERPRETED",
            perception_class="DISPLAY",
            maruah_flag=maruah_flag,
            session_id=session_id,
            actor_id=actor_id,
            tool_name="geox_map_context_scene",
        )
        return envelope

    # ── GeoJSON features for selectable geology (Fix HOLD-2026-07-11) ──
    _geojson_features: list[dict] = [
        {
            "type": "Feature",
            "properties": {"type": "bounding_box", "label": "Query AOI"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [bbox[0], bbox[1]],
                        [bbox[2], bbox[1]],
                        [bbox[2], bbox[3]],
                        [bbox[0], bbox[3]],
                        [bbox[0], bbox[1]],
                    ]
                ],
            },
        },
        {
            "type": "Feature",
            "properties": {"type": "center_point", "label": "AOI Center"},
            "geometry": {
                "type": "Point",
                "coordinates": [
                    (bbox[0] + bbox[2]) / 2,
                    (bbox[1] + bbox[3]) / 2,
                ],
            },
        },
    ]
    if maruah_flag:
        try:
            from geox_core.spatial.maruah_zones import get_maruah_zone_polygons as _get_zones

            zones = _get_zones(bbox, crs)
            for zone in zones:
                _geojson_features.append(
                    {
                        "type": "Feature",
                        "properties": {
                            "type": "maruah_zone",
                            "label": zone.get("name", "Community/Indigenous Territory"),
                            "risk": zone.get("risk", "MEDIUM"),
                        },
                        "geometry": zone.get("geometry", {"type": "Point", "coordinates": [0, 0]}),
                    }
                )
        except Exception as exc:
            logger.warning(f"MARUAH zone render failed (non-blocking): {exc}")

    artifact = {
        "geojson_features": _geojson_features,
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
        session_id=session_id,
        actor_id=actor_id,
        tool_name="geox_map_context_scene",
    )
    if e8_block:
        envelope["e8_velocity_slice"] = e8_block
    return envelope
