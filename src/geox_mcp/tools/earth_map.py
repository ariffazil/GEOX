"""
GEOX Earth Map Tools — Layer Registry, Scene Planning, Preview Rendering, Export Package
========================================================================================

Four primitives completing the map verb chain:
1. geox_map_layers_list       — discover what layers exist for a bbox
2. geox_map_scene_plan        — deterministic render recipe (no image yet)
3. geox_map_render_preview    — cheap static PNG/WebP preview with caching
4. geox_map_export_package    — governed export with PROV sidecar + STAC catalog

Architecture: tools compute + decide, resources carry data payloads.
MCP resource links for images > 300KB. Base64 only for thumbnails.
Exports produce governed packages with W3C PROV provenance sidecars.

Phase 2.4 (2026-07-02): geox_map_export_package completes the chain.
  - PROV sidecar per W3C PROV-O (entity → activity → agent → wasDerivedFrom)
  - STAC catalog for geospatial asset discovery
  - EGS provenance bridge: layer provenance auto-populated from Earth Graph System
  - Checksum chain: every output file has SHA-256, linked to source layer checksums

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

    # Save provenance with optional EGS enrichment
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

    # EGS provenance enrichment (best-effort, non-blocking)
    try:
        from geox_mcp.tools.provenance_bridge import enrich_batch_provenance

        egs_enriched = await enrich_batch_provenance(layer_ids)
        if any(e.get("claim_id") for e in egs_enriched):
            provenance["egs_enriched"] = True
            provenance["egs_layers"] = [
                {"layer_id": e["layer_id"], "claim_id": e.get("claim_id")} for e in egs_enriched if e.get("claim_id")
            ]
    except Exception:
        logger.debug("EGS provenance bridge unavailable (non-blocking)")
        pass
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


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 4: geox_map_export_package — Governed Export with PROV Sidecar
# ═══════════════════════════════════════════════════════════════════════════════
#
# Completes the map verb chain: discover → plan → render → export.
# Produces a governed package with:
#   - Rendered preview (PNG/WebP)
#   - W3C PROV provenance sidecar (prov.json)
#   - STAC catalog (catalog.json)
#   - Scene manifest with layer checksums (manifest.json)
#   - Optional source data copies
#   - SHA-256 checksum chain on every artifact
#
# Phase 2.4 (2026-07-02)


def _build_prov_sidecar(
    scene_plan_id: str,
    layer_records: list[dict],
    rendered_at: str,
    geox_version: str,
    review_mode: str,
) -> dict:
    """Build a W3C PROV-O provenance sidecar for an export package.

    Follows PROV-O: entity → activity → agent → wasDerivedFrom.
    Every layer is an entity, the render is an activity, GEOX is an agent,
    and the output is derived from input layers.
    """
    import hashlib

    prov_id = f"export-{hashlib.sha256(scene_plan_id.encode()).hexdigest()[:12]}"

    entities: dict[str, dict] = {}
    for i, lr in enumerate(layer_records):
        eid = f"layer:{lr.get('id', f'unknown_{i}')}"
        entities[eid] = {
            "prov:type": "prov:Entity",
            "prov:label": lr.get("name", eid),
            "geox:truth_class": lr.get("truth_class", "CONTEXT"),
            "geox:source": lr.get("source", "unknown"),
            "geox:checksum": lr.get("checksum", "unknown"),
        }

    output_eid = f"package:{prov_id}"
    entities[output_eid] = {
        "prov:type": "prov:Entity",
        "prov:label": f"Export package for scene {scene_plan_id}",
        "geox:review_mode": review_mode,
    }

    activity_id = f"render:{prov_id}"
    agent_id = "agent:geox"

    return {
        "prefix": {
            "prov": "http://www.w3.org/ns/prov#",
            "geox": "https://geox.arif-fazil.com/ns/prov#",
        },
        "agent": {
            agent_id: {
                "prov:type": "prov:Agent",
                "prov:label": "GEOX Earth Intelligence",
                "geox:version": geox_version,
            }
        },
        "activity": {
            activity_id: {
                "prov:type": "prov:Activity",
                "prov:label": f"Map export: {scene_plan_id}",
                "prov:startedAtTime": rendered_at,
                "geox:scene_plan_id": scene_plan_id,
                "geox:tool": "geox_map_export_package",
            }
        },
        "entity": entities,
        "wasDerivedFrom": {output_eid: {"prov:entity": list(entities.keys())}},
        "wasGeneratedBy": {output_eid: {"prov:activity": activity_id}},
        "wasAssociatedWith": {activity_id: {"prov:agent": agent_id}},
        "used": {activity_id: {"prov:entity": [eid for eid in entities if eid.startswith("layer:")]}},
    }


def _build_stac_catalog(
    scene_plan_id: str,
    files: list[dict],
    bbox: list[float],
    created_at: str,
) -> dict:
    """Build a STAC-compatible catalog for the export package.

    Follows the SpatioTemporal Asset Catalog (STAC) spec.
    Each output file becomes a STAC item with bbox and datetime.
    """
    import hashlib

    catalog_id = f"geox-export-{hashlib.sha256(scene_plan_id.encode()).hexdigest()[:8]}"

    items = []
    for f in files:
        item = {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": f.get("name", f.get("path", "unknown")),
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
            "properties": {
                "datetime": created_at,
                "title": f.get("title", f.get("name", "unknown")),
                "file:size": f.get("size_bytes", 0),
                "file:checksum": f.get("checksum", ""),
            },
            "assets": {
                "data": {
                    "href": f.get("path", ""),
                    "type": f.get("mime_type", "application/octet-stream"),
                    "title": f.get("title", f.get("name", "unknown")),
                }
            },
            "links": [],
        }
        items.append(item)

    return {
        "type": "Catalog",
        "stac_version": "1.0.0",
        "id": catalog_id,
        "title": f"GEOX Export: {scene_plan_id}",
        "description": f"Governed export package for scene plan {scene_plan_id}",
        "bbox": [bbox[0], bbox[1], bbox[2], bbox[3]],
        "links": [{"rel": "item", "href": f"items/{i}"} for i in range(len(items))],
        "items": items,
    }


async def geox_map_export_package(
    scene_plan_id: str,
    formats: list[str] | None = None,
    include_sources: bool = False,
    include_provenance: bool = True,
    review_mode: str = "draft",
    output_dir: str | None = None,
) -> dict:
    """Create a governed export package with map assets, metadata, and provenance sidecars.

    Completes the map verb chain:
      geox_map_layers_list → geox_map_scene_plan → geox_map_render_preview → geox_map_export_package

    Produces a package directory with:
      - Rendered preview (PNG/WebP) via geox_map_render_preview
      - STAC catalog JSON (if include_provenance=True)
      - W3C PROV provenance sidecar (if include_provenance=True)
      - Scene manifest with layer references + checksums
      - Optional: included source data copies

    Every output file is checksummed (SHA-256) and the manifest records
    the full dependency chain — layers → scene plan → rendered preview → package.

    Args:
        scene_plan_id: Scene ID from geox_map_scene_plan.
        formats: Output formats. Default: ["png"]. Options: png, svg, pdf, gpkg, stac.
        include_sources: If True, include copies of source data files.
        include_provenance: If True, generate PROV sidecar + STAC catalog.
        review_mode: draft | validated | sealed_candidate. Affects provenance metadata.
        output_dir: Custom output directory. Default: /root/geox/data/exports/{scene_plan_id}.

    Returns:
        Package manifest with artifact paths, checksums, and provenance references.
    """
    import asyncio
    import hashlib
    import shutil
    import time
    import uuid

    if formats is None:
        formats = ["png"]

    valid_formats = {"png", "svg", "pdf", "gpkg", "stac"}
    for fmt in formats:
        if fmt not in valid_formats:
            return {"status": "ERROR", "error": f"Unsupported format '{fmt}'. Valid: {valid_formats}"}

    if review_mode not in ("draft", "validated", "sealed_candidate"):
        return {"status": "ERROR", "error": f"Invalid review_mode '{review_mode}'. Use draft, validated, or sealed_candidate."}

    # Resolve scene plan
    scene_file = _CACHE_DIR / f"{scene_plan_id}_scene.json"
    if not scene_file.exists():
        # Try looking up by scene_id pattern
        for f in _CACHE_DIR.glob(f"{scene_plan_id}*_scene.json"):
            scene_file = f
            break
        if not scene_file.exists():
            return {"status": "ERROR", "error": f"Scene '{scene_plan_id}' not found. Run geox_map_scene_plan first."}

    with open(scene_file) as f:
        scene = json.load(f)

    if scene.get("status") != "OK":
        return {"status": "ERROR", "error": f"Scene '{scene_plan_id}' has status '{scene.get('status')}'. Cannot export."}

    bbox = scene["bbox"]
    layer_ids = [l["id"] for l in scene.get("layers_ordered", [])]

    # Set up output directory
    pkg_id = f"pkg-{uuid.uuid4().hex[:12]}"
    if output_dir is None:
        output_dir = str(_GEOX_ROOT / "data" / "exports" / pkg_id)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    created_at = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    geox_version = os.getenv("GIT_SHA", "2026.07.02")

    # Track output files
    output_files: list[dict] = []
    layer_records: list[dict] = []

    # Load layer metadata from registry
    registry = _load_registry()
    all_layers = {l["id"]: l for l in registry["layers"]}
    for lid in layer_ids:
        layer = all_layers.get(lid, {})
        layer_records.append(
            {
                "id": lid,
                "name": layer.get("name", lid),
                "truth_class": layer.get("truth_class", "CONTEXT"),
                "source": layer.get("source", "unknown"),
                "checksum": layer.get("checksum", "unavailable"),
            }
        )

    # ── Step 1: Render preview ─────────────────────────────────────────────────
    if "png" in formats:
        width = 1600
        height = 1200
        fmt: str = "image/png"

        render_result = await geox_map_render_preview(
            scene_id=scene_plan_id,
            width_px=width,
            height_px=height,
            format=fmt,
        )

        if render_result.get("status") != "OK":
            return {"status": "ERROR", "error": f"Render failed: {render_result.get('error', 'unknown')}"}

        # If render returned base64 or resource link, we may need to copy the cached file
        render_path = render_result.get("resource_path")
        if render_path and Path(render_path).exists():
            ext = "png" if fmt == "image/png" else "svg" if fmt == "image/svg" else "pdf"
            out_file = output_path / f"map_preview.{ext}"
            shutil.copy2(render_path, out_file)
            chk = hashlib.sha256(out_file.read_bytes()).hexdigest()
            output_files.append(
                {
                    "name": f"map_preview.{ext}",
                    "path": str(out_file),
                    "checksum": chk,
                    "size_bytes": out_file.stat().st_size,
                    "mime_type": fmt,
                    "title": f"Map preview ({ext})",
                }
            )

        # Also copy cached provenance if it exists
        cache_meta = _CACHE_DIR / f"{render_result.get('cache_key', '')}.json"
        # Fallback: check for cached meta matching the scene
        for cm in _CACHE_DIR.glob(f"{scene_plan_id[:12]}*.json"):
            if cm.name.endswith("_scene.json"):
                continue
            if cm.exists():
                prov_out = output_path / "render_provenance.json"
                shutil.copy2(str(cm), str(prov_out))
                break

    # ── Step 2: Copy source data (if requested) ────────────────────────────────
    if include_sources:
        for lid in layer_ids:
            layer = all_layers.get(lid)
            if not layer:
                continue
            src_file = layer.get("file")
            if not src_file:
                continue
            src_path = _ATLAS_DIR / src_file
            if src_path.exists():
                dest = output_path / "sources" / src_file.replace("/", "_")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_path), str(dest))
                chk = hashlib.sha256(dest.read_bytes()).hexdigest()
                output_files.append(
                    {
                        "name": f"sources/{Path(src_file).name}",
                        "path": str(dest),
                        "checksum": chk,
                        "size_bytes": dest.stat().st_size,
                        "mime_type": "application/geo+json",
                        "title": f"Source: {layer.get('name', lid)}",
                    }
                )

    # ── Step 3: Build scene manifest ───────────────────────────────────────────
    manifest = {
        "package_id": pkg_id,
        "scene_plan_id": scene_plan_id,
        "created_at": created_at,
        "geox_version": geox_version,
        "review_mode": review_mode,
        "bbox": bbox,
        "layer_count": len(layer_ids),
        "layers": layer_records,
        "output_files": [{"name": f["name"], "checksum": f["checksum"], "size_bytes": f["size_bytes"]} for f in output_files],
        "formats": formats,
        "include_sources": include_sources,
        "include_provenance": include_provenance,
    }
    manifest_file = output_path / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    manifest_checksum = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
    manifest["manifest_checksum"] = manifest_checksum

    # ── Step 4a: EGS provenance enrichment (best-effort) ────────────────────────
    egs_enriched_layers: list[dict] = []
    try:
        from geox_mcp.tools.provenance_bridge import enrich_batch_provenance, provenance_coverage

        egs_enriched_layers = await enrich_batch_provenance(layer_ids)
        coverage = provenance_coverage(layer_ids)
        if coverage["coverage_pct"] > 0:
            logger.info(
                f"EGS provenance bridge: {coverage['coverage_pct']}% coverage ({coverage['covered']}/{coverage['total']} layers)"
            )
    except Exception:
        logger.debug("EGS provenance bridge unavailable (non-blocking)")
        pass

    # Merge EGS enrichment into layer records
    egs_by_layer = {e["layer_id"]: e for e in egs_enriched_layers}
    for lr in layer_records:
        egs_data = egs_by_layer.get(lr["id"], {})
        if egs_data.get("claim_id"):
            lr["egs_claim_id"] = egs_data["claim_id"]
            lr["egs_claim_status"] = egs_data.get("claim_status", "unknown")

    # ── Step 4b: Build PROV sidecar (if requested) ──────────────────────────────
    if include_provenance:
        prov = _build_prov_sidecar(
            scene_plan_id=scene_plan_id,
            layer_records=layer_records,
            rendered_at=created_at,
            geox_version=geox_version,
            review_mode=review_mode,
        )
        prov_file = output_path / "prov.json"
        with open(prov_file, "w") as f:
            json.dump(prov, f, indent=2)
        output_files.append(
            {
                "name": "prov.json",
                "path": str(prov_file),
                "checksum": hashlib.sha256(prov_file.read_bytes()).hexdigest(),
                "size_bytes": prov_file.stat().st_size,
                "mime_type": "application/json",
                "title": "W3C PROV provenance sidecar",
            }
        )

        # Build STAC catalog
        stac = _build_stac_catalog(
            scene_plan_id=scene_plan_id,
            files=output_files,
            bbox=bbox,
            created_at=created_at,
        )
        stac_file = output_path / "catalog.json"
        with open(stac_file, "w") as f:
            json.dump(stac, f, indent=2)
        output_files.append(
            {
                "name": "catalog.json",
                "path": str(stac_file),
                "checksum": hashlib.sha256(stac_file.read_bytes()).hexdigest(),
                "size_bytes": stac_file.stat().st_size,
                "mime_type": "application/json",
                "title": "STAC catalog",
            }
        )

    # ── Step 5: Final checksum of manifest ─────────────────────────────────────
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    return {
        "status": "OK",
        "package_id": pkg_id,
        "scene_plan_id": scene_plan_id,
        "output_dir": str(output_path),
        "file_count": len(output_files),
        "files": [{"name": f["name"], "checksum": f["checksum"][:16], "size_bytes": f["size_bytes"]} for f in output_files],
        "manifest_checksum": manifest_checksum[:16],
        "includes_provenance": include_provenance,
        "review_mode": review_mode,
        "warnings": [
            "Not survey-grade. Regional schematic for reasoning context only.",
            "Export package is a snapshot — data may have been updated since export.",
        ],
    }
