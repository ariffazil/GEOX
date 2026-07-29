"""geox_stac_discover — STAC Catalog Discovery.

SpatioTemporal Asset Catalog (STAC) cloud-native query for COG, GeoParquet,
Zarr datasets. Federated API router. "Move compute to data."

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("geox.canonical.stac_discover")

STAC_CACHE = Path(os.environ.get("GEOX_STAC_CACHE", "/opt/geox/data/stac-cache"))
STAC_CACHE.mkdir(parents=True, exist_ok=True)

# Default STAC catalogs (free, open)
DEFAULT_CATALOGS: dict[str, str] = {
    "earthsearch": "https://earth-search.aws.element84.com/v1",
    "planetary": "https://planetarycomputer.microsoft.com/api/stac/v1",
    "copernicus": "https://catalogue.dataspace.copernicus.eu/stac",
    "usgs": "https://landsatlook.usgs.gov/stac-server",
    "nasa": "https://cmr.earthdata.nasa.gov/stac",
}


async def geox_stac_discover(
    mode: str = "search",
    catalog: str = "earthsearch",
    bbox: list[float] | str | None = None,
    datetime_range: str | None = None,
    collections: list[str] | str | None = None,
    max_items: int = 20,
    item_id: str | None = None,
    collection_id: str | None = None,
    query_bands: list[str] | str | None = None,
    limit: int = 1,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """STAC Catalog query for cloud-native geospatial assets.

    Modes:
        search           — Search STAC items by bbox, datetime, collections.
        describe         — Get collection metadata.
        assets           — List assets (URLs, formats) for an item.
        catalogs         — List available STAC catalogs.
        search_raw       — Raw STAC API search with arbitrary query parameters.

    Args:
        mode: Operation mode.
        catalog: STAC catalog key (earthsearch, planetary, copernicus, usgs, nasa)
                 or a full STAC API URL.
        bbox: [min_lng, min_lat, max_lng, max_lat] bounding box.
        datetime_range: ISO 8601 interval (e.g. "2024-01-01/2024-12-31").
        collections: Filter by STAC collection IDs.
        max_items: Maximum items to return (1-100).
        item_id: Specific STAC item ID (for assets mode).
        collection_id: Specific collection ID (for describe mode).
        query_bands: Filter by specific spectral bands.
        limit: Limit for describe operations.
        session_id, actor_id, trace_id: Federation audit.

    Returns:
        dict with STAC items, collection metadata, or asset manifests.
    """
    _ = (session_id, actor_id, trace_id)

    if isinstance(bbox, str):
        bbox = json.loads(bbox)
    if isinstance(collections, str):
        collections = json.loads(collections)
    if isinstance(query_bands, str):
        query_bands = json.loads(query_bands)

    try:
        from pystac_client import Client
    except ImportError:
        return {"ok": False, "error": "pystac-client not installed", "epistemic": "TOOL_UNAVAILABLE"}

    try:
        # ── Resolve catalog URL ──────────────────────────────────────────
        catalog_url = DEFAULT_CATALOGS.get(catalog, catalog)

        # ── Mode: catalogs ───────────────────────────────────────────────
        if mode == "catalogs":
            return {"ok": True, "catalogs": [{"key": k, "url": v} for k, v in DEFAULT_CATALOGS.items()]}

        # ── Mode: describe ───────────────────────────────────────────────
        if mode == "describe":
            if not collection_id:
                return {"ok": False, "error": "collection_id required for describe"}

            client = Client.open(catalog_url)
            coll = client.get_collection(collection_id)

            if not coll:
                return {"ok": False, "error": f"Collection '{collection_id}' not found"}

            return {
                "ok": True,
                "collection": {
                    "id": coll.id,
                    "title": coll.title or coll.id,
                    "description": coll.description or "",
                    "extent": {
                        "spatial": coll.extent.spatial.to_dict() if coll.extent and coll.extent.spatial else None,
                        "temporal": coll.extent.temporal.to_dict() if coll.extent and coll.extent.temporal else None,
                    }
                    if coll.extent
                    else None,
                    "license": coll.license,
                    "keywords": coll.keywords or [],
                },
            }

        # ── Mode: assets ─────────────────────────────────────────────────
        if mode == "assets":
            if not item_id:
                return {"ok": False, "error": "item_id required for assets"}
            if not collection_id:
                return {"ok": False, "error": "collection_id required for assets"}

            client = Client.open(catalog_url)
            coll = client.get_collection(collection_id)
            if not coll:
                return {"ok": False, "error": f"Collection '{collection_id}' not found"}

            item = coll.get_item(item_id)
            if not item:
                return {"ok": False, "error": f"Item '{item_id}' not found"}

            assets = {}
            for key, asset in item.assets.items():
                assets[key] = {
                    "title": asset.title or key,
                    "href": asset.href,
                    "type": asset.media_type,
                    "roles": asset.roles or [],
                    "description": asset.description or "",
                }

            return {
                "ok": True,
                "item_id": item_id,
                "collection": collection_id,
                "datetime": str(item.datetime) if item.datetime else None,
                "bbox": item.bbox,
                "assets": assets,
                "n_assets": len(assets),
            }

        # ── Mode: search ─────────────────────────────────────────────────
        if mode == "search":
            client = Client.open(catalog_url)

            # Parse collections filter
            coll_list = collections if collections else None

            # Build search
            search_params: dict[str, Any] = {"max_items": min(max_items, 100)}
            if bbox:
                search_params["bbox"] = bbox
            if datetime_range:
                search_params["datetime"] = datetime_range
            if coll_list:
                search_params["collections"] = coll_list
            if query_bands:
                search_params["query"] = {"eo:bands": {"in": query_bands}}

            search = client.search(**search_params)
            items_data = []
            for item in search.items():
                item_info = {
                    "id": item.id,
                    "collection": item.collection_id,
                    "datetime": str(item.datetime) if item.datetime else None,
                    "geometry": item.geometry,
                    "bbox": item.bbox,
                    "assets": list(item.assets.keys()),
                }
                # Include thumbnail URL if available
                if "thumbnail" in item.assets:
                    item_info["thumbnail_url"] = item.assets["thumbnail"].href
                if "rendered_preview" in item.assets:
                    item_info["preview_url"] = item.assets["rendered_preview"].href
                items_data.append(item_info)

            return {
                "ok": True,
                "catalog": catalog,
                "catalog_url": catalog_url,
                "n_items": len(items_data),
                "items": items_data,
            }

        # ── Mode: search_raw ─────────────────────────────────────────────
        if mode == "search_raw":
            try:
                import requests

                search_url = f"{catalog_url.rstrip('/')}/search"
                params: dict[str, Any] = {"limit": min(max_items, 100)}
                if bbox:
                    params["bbox"] = ",".join(str(x) for x in bbox)
                if datetime_range:
                    params["datetime"] = datetime_range
                if collections:
                    params["collections"] = ",".join(collections)

                resp = requests.get(search_url, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                return {
                    "ok": True,
                    "catalog": catalog,
                    "n_items": len(data.get("features", [])),
                    "raw": data,
                }
            except ImportError:
                return {"ok": False, "error": "requests package not available for raw mode"}

        return {
            "ok": False,
            "error": f"Unknown mode: {mode}",
            "valid_modes": [
                "search",
                "describe",
                "assets",
                "catalogs",
                "search_raw",
            ],
        }

    except Exception as e:
        logger.exception("STAC discovery failed")
        return {"ok": False, "error": str(e), "catalog": catalog}
