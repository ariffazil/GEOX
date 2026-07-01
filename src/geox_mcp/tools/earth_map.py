"""
GEOX Earth Map Tools — Layer Registry, Scene Planning, Preview Rendering
=========================================================================

Three primitives following ChatGPT's architectural feedback:
1. geox_map_layers_list  — discover what layers exist for a bbox
2. geox_map_scene_plan   — deterministic render recipe (no image yet)
3. geox_map_render_preview — cheap static PNG/WebP preview with caching

Architecture: tools compute + decide, resources carry data payloads.
MCP resource links for images > 300KB. Base64 only for thumbnails.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("geox.canonical.earth_map")

# ── Paths ────────────────────────────────────────────────────────────────────
_GEOX_ROOT = Path(__file__).parent.parent.parent.parent
_ATLAS_DIR = _GEOX_ROOT / "data" / "atlas"
_LAYERS_FILE = _ATLAS_DIR / "layers" / "earth_layers.json"
_CACHE_DIR = _ATLAS_DIR / "cache" / "renders"

# Ensure cache dir exists
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Layer registry cache ─────────────────────────────────────────────────────
_registry_cache: dict | None = None


def _load_registry() -> dict:
    global _registry_cache
    if _registry_cache is None:
        with open(_LAYERS_FILE) as f:
            _registry_cache = json.load(f)
    return _registry_cache


def _reload_registry() -> dict:
    """Force reload from disk (for testing)."""
    global _registry_cache
    _registry_cache = None
    return _load_registry()


# ── Geometry helpers ─────────────────────────────────────────────────────────


def _bbox_intersects(bbox_a: list[float], bbox_b: list[float]) -> bool:
    """Check if two bboxes [min_lon, min_lat, max_lon, max_lat] intersect."""
    return not (
        bbox_a[2] < bbox_b[0]  # a_max_lon < b_min_lon
        or bbox_a[0] > bbox_b[2]  # a_min_lon > b_max_lon
        or bbox_a[3] < bbox_b[1]  # a_max_lat < b_min_lat
        or bbox_a[1] > bbox_b[3]  # a_min_lat > b_max_lat
    )


def _bbox_area_deg2(bbox: list[float]) -> float:
    """Compute bbox area in square degrees."""
    return abs(bbox[2] - bbox[0]) * abs(bbox[3] - bbox[1])


def _validate_bbox(bbox: list[float]) -> str | None:
    """Validate bbox. Returns error string or None if valid."""
    if len(bbox) != 4:
        return "bbox must be [min_lon, min_lat, max_lon, max_lat]"
    if bbox[0] >= bbox[2]:
        return f"min_lon ({bbox[0]}) must be < max_lon ({bbox[2]})"
    if bbox[1] >= bbox[3]:
        return f"min_lat ({bbox[1]}) must be < max_lat ({bbox[3]})"
    if bbox[0] < -180 or bbox[2] > 180:
        return "longitude must be in [-180, 180]"
    if bbox[1] < -90 or bbox[3] > 90:
        return "latitude must be in [-90, 90]"
    return None


# ── TOOL 1: geox_map_layers_list ────────────────────────────────────────────


async def geox_map_layers_list(
    bbox: list[float],
    theme: str | None = None,
    include_unavailable: bool = False,
) -> dict:
    """List available GEOX map layers for a bounding box.

    Args:
        bbox: [min_lon, min_lat, max_lon, max_lat] in EPSG:4326.
        theme: Optional theme filter (regional_geology, basin, structure,
               stratigraphy, petroleum, tectonics, sabah_regional, se_asia).
        include_unavailable: If True, include layers marked available=false.

    Returns:
        Layer catalogue with metadata, truth classes, and availability.
    """
    bbox_err = _validate_bbox(bbox)
    if bbox_err:
        return {"status": "ERROR", "error": bbox_err, "layers": [], "layer_count": 0}

    registry = _load_registry()
    all_layers = registry["layers"]
    guardrails = registry.get("guardrails", {})

    # Check bbox size guardrail
    max_bbox = guardrails.get("max_bbox_degrees", 8.0)
    bbox_span = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
    if bbox_span > max_bbox:
        return {
            "status": "ERROR",
            "error": f"Bbox span {bbox_span:.1f}° exceeds max {max_bbox}°. Reduce bbox or request export.",
            "layers": [],
            "layer_count": 0,
        }

    # Filter by theme if provided
    theme_layer_ids = None
    if theme:
        themes = registry.get("themes", {})
        if theme not in themes:
            return {
                "status": "ERROR",
                "error": f"Unknown theme '{theme}'. Available: {list(themes.keys())}",
                "layers": [],
                "layer_count": 0,
            }
        theme_layer_ids = set(themes[theme])

    # Filter layers
    matched = []
    for layer in all_layers:
        # Theme filter
        if theme_layer_ids is not None and layer["id"] not in theme_layer_ids:
            continue

        # Availability filter
        if not include_unavailable and not layer.get("available", True):
            continue

        # Bbox intersection filter
        layer_bbox = layer.get("bbox")
        if layer_bbox and not _bbox_intersects(bbox, layer_bbox):
            continue

        matched.append(
            {
                "id": layer["id"],
                "name": layer["name"],
                "type": layer["type"],
                "geometry_type": layer.get("geometry_type", "unknown"),
                "source": layer["source"],
                "truth_class": layer["truth_class"],
                "scale": layer.get("scale", "unknown"),
                "available": layer.get("available", True),
                "description": layer.get("description", ""),
            }
        )

    return {
        "status": "OK",
        "bbox": bbox,
        "crs": "EPSG:4326",
        "theme": theme,
        "layers": matched,
        "layer_count": len(matched),
        "guardrails": guardrails,
    }


# ── TOOL 2: geox_map_scene_plan ─────────────────────────────────────────────


async def geox_map_scene_plan(
    bbox: list[float],
    layer_ids: list[str] | None = None,
    theme: str | None = None,
    map_purpose: Literal["context", "interpretation", "qc", "prospect_review", "publication"] = "context",
    style_profile: str = "geox_regional_clean_v1",
    crs: str = "EPSG:4326",
) -> dict:
    """Create a deterministic visual recipe for a geological map scene.

    This is the 'constitution' of the map — layer ordering, styles, warnings,
    and provenance. No image is rendered yet. Inspect this before rendering.

    Args:
        bbox: [min_lon, min_lat, max_lon, max_lat] in EPSG:4326.
        layer_ids: Explicit layer IDs to include. If None, auto-select from theme.
        theme: Theme for auto-selection (used when layer_ids is None).
        map_purpose: Determines truth class restrictions.
        style_profile: Visual style preset.
        crs: Coordinate reference system.

    Returns:
        Scene plan with ordered layers, styles, warnings, and provenance.
    """
    bbox_err = _validate_bbox(bbox)
    if bbox_err:
        return {"status": "ERROR", "error": bbox_err}

    registry = _load_registry()
    all_layers = {l["id"]: l for l in registry["layers"]}
    styles = registry.get("style_profiles", {})
    guardrails = registry.get("guardrails", {})

    # Resolve layers
    if layer_ids:
        resolved_ids = layer_ids
    elif theme:
        themes = registry.get("themes", {})
        if theme not in themes:
            return {"status": "ERROR", "error": f"Unknown theme '{theme}'. Available: {list(themes.keys())}"}
        resolved_ids = themes[theme]
    else:
        # Default: auto-detect from bbox
        resolved_ids = []
        for layer in registry["layers"]:
            if not layer.get("available", True):
                continue
            layer_bbox = layer.get("bbox")
            if layer_bbox and _bbox_intersects(bbox, layer_bbox):
                resolved_ids.append(layer["id"])
            elif not layer_bbox and layer.get("scale") == "global":
                resolved_ids.append(layer["id"])

    # Validate and order layers
    ordered_layers = []
    warnings = []
    for lid in resolved_ids:
        if lid not in all_layers:
            warnings.append(f"Layer '{lid}' not found in registry. Skipped.")
            continue
        layer = all_layers[lid]

        # Truth class gate
        if map_purpose == "context" and layer["truth_class"] == "DECISION_SUPPORT":
            warnings.append(f"Layer '{lid}' is DECISION_SUPPORT — excluded from context maps.")
            continue

        if not layer.get("available", True):
            warnings.append(f"Layer '{lid}' not yet available. Skipped.")
            continue

        ordered_layers.append(
            {
                "id": layer["id"],
                "name": layer["name"],
                "type": layer["type"],
                "truth_class": layer["truth_class"],
                "source": layer["source"],
            }
        )

    # Check layer count guardrail
    max_layers = guardrails.get("max_layers", 12)
    if len(ordered_layers) > max_layers:
        warnings.append(f"Layer count ({len(ordered_layers)}) exceeds max ({max_layers}). Truncating.")
        ordered_layers = ordered_layers[:max_layers]

    # Get style
    style = styles.get(style_profile, styles.get("geox_regional_clean_v1", {}))

    # Generate scene ID
    scene_hash = hashlib.sha256(
        json.dumps(
            {"bbox": bbox, "layers": [l["id"] for l in ordered_layers], "style": style_profile, "purpose": map_purpose},
            sort_keys=True,
        ).encode()
    ).hexdigest()[:12]
    scene_id = f"scene_{scene_hash}"

    # Compute bbox metadata
    center_lon = (bbox[0] + bbox[2]) / 2
    center_lat = (bbox[1] + bbox[3]) / 2
    width_deg = bbox[2] - bbox[0]
    height_deg = bbox[3] - bbox[1]

    return {
        "status": "OK",
        "scene_id": scene_id,
        "bbox": bbox,
        "crs": crs,
        "center": [center_lon, center_lat],
        "width_deg": width_deg,
        "height_deg": height_deg,
        "map_purpose": map_purpose,
        "style_profile": style_profile,
        "style": style,
        "layers_ordered": ordered_layers,
        "layer_count": len(ordered_layers),
        "warnings": warnings,
        "provenance": {
            "generated_by": "geox_map_scene_plan",
            "truth_classes_present": list(set(l["truth_class"] for l in ordered_layers)),
            "scale_warning": "Regional schematic only. Not survey-grade.",
            "sources": list(set(l["source"] for l in ordered_layers)),
        },
    }


# ── TOOL 3: geox_map_render_preview ─────────────────────────────────────────


async def geox_map_render_preview(
    scene_id: str | None = None,
    bbox: list[float] | None = None,
    layer_ids: list[str] | None = None,
    theme: str | None = None,
    width_px: int = 1024,
    height_px: int = 768,
    style_profile: str = "geox_regional_clean_v1",
    format: Literal["image/png", "image/webp"] = "image/png",
) -> dict:
    """Render a static map preview from a scene plan or bbox.

    Either provide scene_id (from geox_map_scene_plan) OR bbox+layer_ids/theme.
    Returns a cached PNG/WebP preview. Images < 300KB returned as base64.
    Larger images returned as resource links.

    Args:
        scene_id: Scene ID from geox_map_scene_plan (preferred).
        bbox: [min_lon, min_lat, max_lon, max_lat] (if no scene_id).
        layer_ids: Layer IDs to render (if no scene_id).
        theme: Theme for auto-selection (if no scene_id and no layer_ids).
        width_px: Preview width (512-1600).
        height_px: Preview height (512-1600).
        style_profile: Visual style preset.
        format: Output format.

    Returns:
        Render result with image content or resource link.
    """
    import asyncio

    registry = _load_registry()
    guardrails = registry.get("guardrails", {})

    # Validate dimensions
    max_w = guardrails.get("max_width_px", 1600)
    max_h = guardrails.get("max_height_px", 1600)
    width_px = max(512, min(width_px, max_w))
    height_px = max(512, min(height_px, max_h))

    # Resolve scene
    if scene_id:
        # Try to load from cache
        scene_file = _CACHE_DIR / f"{scene_id}_scene.json"
        if scene_file.exists():
            with open(scene_file) as f:
                scene = json.load(f)
            bbox = scene["bbox"]
            layer_ids = [l["id"] for l in scene["layers_ordered"]]
            style_profile = scene.get("style_profile", style_profile)
        else:
            return {"status": "ERROR", "error": f"Scene '{scene_id}' not found. Run geox_map_scene_plan first."}
    elif bbox:
        # Generate scene plan on the fly
        scene = await geox_map_scene_plan(
            bbox=bbox,
            layer_ids=layer_ids,
            theme=theme,
            style_profile=style_profile,
        )
        if scene.get("status") != "OK":
            return scene
        scene_id = scene["scene_id"]
        layer_ids = [l["id"] for l in scene["layers_ordered"]]
        # Save scene for future use
        scene_file = _CACHE_DIR / f"{scene_id}_scene.json"
        with open(scene_file, "w") as f:
            json.dump(scene, f, indent=2)
    else:
        return {"status": "ERROR", "error": "Provide either scene_id or bbox."}

    # Check cache
    cache_key = hashlib.sha256(
        json.dumps({"scene": scene_id, "w": width_px, "h": height_px, "fmt": format}, sort_keys=True).encode()
    ).hexdigest()[:16]
    cache_file = _CACHE_DIR / f"{cache_key}.png"
    cache_meta = _CACHE_DIR / f"{cache_key}.json"

    if cache_file.exists():
        age_s = time.time() - cache_file.stat().st_mtime
        ttl = guardrails.get("cache_ttl_seconds", 86400)
        if age_s < ttl:
            # Cache hit
            size_kb = cache_file.stat().st_size / 1024
            result = {
                "status": "OK",
                "scene_id": scene_id,
                "cached": True,
                "cache_age_seconds": int(age_s),
                "width_px": width_px,
                "height_px": height_px,
                "format": format,
                "file_size_kb": round(size_kb, 1),
            }
            if size_kb < 300:
                import base64

                with open(cache_file, "rb") as f:
                    result["image_base64"] = base64.b64encode(f.read()).decode()
                result["return_mode"] = "inline_base64"
            else:
                result["resource_uri"] = f"geox://map/{scene_id}/preview.png"
                result["resource_path"] = str(cache_file)
                result["return_mode"] = "resource_link"
            if cache_meta.exists():
                with open(cache_meta) as f:
                    result["provenance"] = json.load(f)
            return result

    # Render
    try:
        render_result = await _render_map_preview(
            bbox=bbox,
            layer_ids=layer_ids,
            width_px=width_px,
            height_px=height_px,
            style_profile=style_profile,
            output_path=str(cache_file),
        )
    except Exception as exc:
        logger.error(f"Map render failed: {exc}", exc_info=True)
        return {"status": "ERROR", "error": f"Render failed: {exc}"}

    # Save provenance
    provenance = {
        "scene_id": scene_id,
        "bbox": bbox,
        "layers": layer_ids,
        "style_profile": style_profile,
        "rendered_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "width_px": width_px,
        "height_px": height_px,
        "format": format,
        "generated_by": "geox_map_render_preview",
        "truth_classes": render_result.get("truth_classes", []),
        "warnings": [
            "Not survey-grade. Regional schematic for reasoning context only.",
            "Geometry from Natural Earth / GEOX curated synthesis.",
        ],
    }
    with open(cache_meta, "w") as f:
        json.dump(provenance, f, indent=2)

    size_kb = cache_file.stat().st_size / 1024
    result = {
        "status": "OK",
        "scene_id": scene_id,
        "cached": False,
        "width_px": width_px,
        "height_px": height_px,
        "format": format,
        "file_size_kb": round(size_kb, 1),
        "provenance": provenance,
    }

    if size_kb < 300:
        import base64

        with open(cache_file, "rb") as f:
            result["image_base64"] = base64.b64encode(f.read()).decode()
        result["return_mode"] = "inline_base64"
    else:
        result["resource_uri"] = f"geox://map/{scene_id}/preview.png"
        result["resource_path"] = str(cache_file)
        result["return_mode"] = "resource_link"

    return result


# ── Internal renderer ────────────────────────────────────────────────────────


async def _render_map_preview(
    bbox: list[float],
    layer_ids: list[str],
    width_px: int,
    height_px: int,
    style_profile: str,
    output_path: str,
) -> dict:
    """Render a static map preview using matplotlib + contextily basemap.

    This is the cheap renderer — GeoJSON polygons/lines/points over a
    basemap tile. No heavy GIS computation. Survives on a miskin VPS.
    """
    import asyncio

    def _sync_render():
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.collections import LineCollection, PatchCollection
        import numpy as np

        registry = _load_registry()
        all_layers = {l["id"]: l for l in registry["layers"]}
        styles = registry.get("style_profiles", {})
        style = styles.get(style_profile, {})

        # Create figure
        dpi = 100
        fig, ax = plt.subplots(1, 1, figsize=(width_px / dpi, height_px / dpi), dpi=dpi)

        # Set bounds
        ax.set_xlim(bbox[0], bbox[2])
        ax.set_ylim(bbox[1], bbox[3])
        ax.set_aspect("equal")

        # Try to add contextily basemap
        has_basemap = False
        try:
            import contextily as ctx

            # Use OSM tiles for basemap
            ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.3)
            has_basemap = True
        except Exception as e:
            logger.warning(f"contextily basemap failed (no tiles): {e}")
            # Fallback: light grey background
            ax.set_facecolor("#f0f0f0")

        # Color palette for different truth classes
        truth_colors = {
            "CONTEXT": "#4A90D9",
            "INTERPRETATION": "#E67E22",
            "DECISION_SUPPORT": "#E74C3C",
        }
        type_colors = {
            "coastline": "#2C3E50",
            "basin": "#3498DB",
            "fault": "#E74C3C",
            "formation": "#27AE60",
            "granite": "#8E44AD",
            "well": "#F39C12",
            "city": "#2C3E50",
            "river": "#3498DB",
            "boundary": "#7F8C8D",
        }

        truth_classes_rendered = []
        features_rendered = 0

        for lid in layer_ids:
            layer = all_layers.get(lid)
            if not layer:
                continue

            layer_file = _ATLAS_DIR / layer.get("file", "")
            if not layer_file.exists():
                continue

            try:
                with open(layer_file) as f:
                    geojson = json.load(f)
            except Exception:
                continue

            truth_class = layer.get("truth_class", "CONTEXT")
            truth_classes_rendered.append(truth_class)
            color = truth_colors.get(truth_class, "#95A5A6")
            geom_type = layer.get("geometry_type", "polygon")

            alpha = style.get("basin_fill_opacity", 0.35) if geom_type == "polygon" else 0.8
            lw = style.get("fault_line_width", 1.2) if geom_type == "line" else 0.5

            features = geojson.get("features", [])
            for feat in features:
                if features_rendered > 5000:
                    break
                geometry = feat.get("geometry")
                if not geometry:
                    continue

                gtype = geometry.get("type")
                coords = geometry.get("coordinates", [])

                try:
                    if gtype == "Polygon" and geom_type == "polygon":
                        for ring in coords[:1]:  # outer ring only
                            xs = [c[0] for c in ring]
                            ys = [c[1] for c in ring]
                            ax.fill(xs, ys, alpha=alpha, facecolor=color, edgecolor=color, linewidth=lw)
                            features_rendered += 1

                    elif gtype == "MultiPolygon" and geom_type == "polygon":
                        for poly in coords:
                            for ring in poly[:1]:
                                xs = [c[0] for c in ring]
                                ys = [c[1] for c in ring]
                                ax.fill(xs, ys, alpha=alpha, facecolor=color, edgecolor=color, linewidth=lw)
                                features_rendered += 1

                    elif gtype == "LineString" and geom_type == "line":
                        xs = [c[0] for c in coords]
                        ys = [c[1] for c in coords]
                        ax.plot(xs, ys, color=color, linewidth=lw, alpha=0.8)
                        features_rendered += 1

                    elif gtype == "MultiLineString" and geom_type == "line":
                        for line in coords:
                            xs = [c[0] for c in line]
                            ys = [c[1] for c in line]
                            ax.plot(xs, ys, color=color, linewidth=lw, alpha=0.8)
                            features_rendered += 1

                    elif gtype == "Point" and geom_type == "point":
                        ax.plot(coords[0], coords[1], "o", color=color, markersize=4, alpha=0.8)
                        features_rendered += 1

                    elif gtype == "MultiPoint" and geom_type == "point":
                        for pt in coords:
                            ax.plot(pt[0], pt[1], "o", color=color, markersize=4, alpha=0.8)
                            features_rendered += 1

                except Exception:
                    continue

        # Add bbox outline
        ax.plot(
            [bbox[0], bbox[2], bbox[2], bbox[0], bbox[0]],
            [bbox[1], bbox[1], bbox[3], bbox[3], bbox[1]],
            color="black",
            linewidth=1.5,
            linestyle="--",
            alpha=0.5,
        )

        # Title
        ax.set_title(f"GEOX Map Preview — {len(layer_ids)} layers", fontsize=10, pad=10)
        ax.set_xlabel("Longitude", fontsize=8)
        ax.set_ylabel("Latitude", fontsize=8)
        ax.tick_params(labelsize=7)

        # Legend
        legend_handles = []
        for tc in set(truth_classes_rendered):
            legend_handles.append(mpatches.Patch(color=truth_colors.get(tc, "#95A5A6"), label=tc, alpha=0.6))
        if legend_handles:
            ax.legend(handles=legend_handles, loc="lower right", fontsize=7, framealpha=0.8)

        # Save
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        return {
            "features_rendered": features_rendered,
            "truth_classes": list(set(truth_classes_rendered)),
            "has_basemap": has_basemap,
        }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_render)
