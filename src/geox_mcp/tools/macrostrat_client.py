"""
macrostrat_client.py — Dedicated Macrostrat API client for GEOX

Integrates UW-Madison Macrostrat geological database (Shanan Peters lab)
into the GEOX Earth Intelligence organ.

API: https://macrostrat.org/api/v2
License: CC-BY-4.0 (attribution required)
Citation: Peters et al. (2018) Macrostrat: a platform for geological data
          integration and deep-time Earth crust research.

Provides:
  - All 10+ Macrostrat API endpoints with typed responses
  - Per-point, bbox, and radius spatial queries
  - Persistent SQLite + in-memory TTL cache (survives restart)
  - Malay Basin SE Asia specific caching
  - CC-BY-4.0 auto-attribution

F2 TRUTH: All data is OBSERVED directly from the Macrostrat API.
           GEOX does not reinterpret Macrostrat data — it preserves
           the epistemic level as PROCESS_HYPOTHESIS (regional surface geology,
           not subsurface truth).

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("geox.macrostrat")

# ── Constants ─────────────────────────────────────────────────────────────────

MACROSTRAT_BASE = "https://macrostrat.org/api/v2"
MACROSTRAT_LICENSE = "CC-BY-4.0"
MACROSTRAT_CITATION = "Peters et al. (2018) doi:10.17605/OSF.IO/YNAXW"

# In-memory TTL: geology doesn't change fast
_IN_MEMORY_CACHE: dict[str, tuple[float, Any]] = {}
_IN_MEMORY_TTL = 3600.0  # 1 hour

# Repo root for persistent cache
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CACHE_DIR = Path(os.environ.get("GEOX_MACROSTRAT_CACHE_DIR", str(_REPO_ROOT / "resources" / "macrostrat_cache")))
_CACHE_DB = _CACHE_DIR / "macrostrat_cache.db"

# SE Asia strategic basin locations for cache warming
SE_ASIA_HOTSPOTS: list[dict[str, Any]] = [
    {"name": "Malay Basin", "lat": 5.5, "lng": 104.5, "radius_km": 200},
    {"name": "Sabah Basin", "lat": 6.0, "lng": 116.0, "radius_km": 200},
    {"name": "Sarawak Basin", "lat": 3.5, "lng": 113.0, "radius_km": 200},
    {"name": "Brunei", "lat": 5.0, "lng": 115.0, "radius_km": 150},
    {"name": "North Sumatra", "lat": 4.5, "lng": 98.0, "radius_km": 150},
    {"name": "South Sumatra", "lat": -3.0, "lng": 105.0, "radius_km": 150},
    {"name": "Kutei Basin", "lat": -1.0, "lng": 117.0, "radius_km": 200},
    {"name": "Song Hong Basin", "lat": 20.0, "lng": 108.0, "radius_km": 150},
    {"name": "Nam Con Son", "lat": 7.5, "lng": 108.0, "radius_km": 150},
    {"name": "Pattani Basin", "lat": 8.0, "lng": 102.0, "radius_km": 150},
]


# ── Cache Layer ────────────────────────────────────────────────────────────────

def _init_cache_db() -> None:
    """Create persistent SQLite cache if it doesn't exist."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(_CACHE_DB)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS macrostrat_cache (
                cache_key TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL,
                params TEXT NOT NULL,
                response TEXT NOT NULL,
                cached_at REAL NOT NULL,
                ttl REAL NOT NULL DEFAULT 86400
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_endpoint
            ON macrostrat_cache(endpoint)
        """)
        conn.commit()


def _build_cache_key(endpoint: str, params: dict[str, Any]) -> str:
    """Deterministic cache key from endpoint + sorted params."""
    canonical = {k: v for k, v in params.items() if v is not None}
    # Round lat/lng to 4dp for cache locality
    if "lat" in canonical:
        canonical["lat"] = round(float(canonical["lat"]), 4)
    if "lng" in canonical:
        canonical["lng"] = round(float(canonical["lng"]), 4)
    param_str = json.dumps(canonical, sort_keys=True, default=str)
    return f"{endpoint}:{hash(param_str)}"


def _get_from_persistent_cache(cache_key: str) -> Any | None:
    """Check persistent SQLite cache. Returns parsed JSON or None."""
    try:
        with sqlite3.connect(str(_CACHE_DB)) as conn:
            row = conn.execute(
                "SELECT response, cached_at, ttl FROM macrostrat_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if row and (time.time() - row[1]) < row[2]:
                return json.loads(row[0])
    except Exception as exc:
        logger.debug("Persistent cache read error: %s", exc)
    return None


def _set_persistent_cache(cache_key: str, endpoint: str, params: dict[str, Any],
                          response: Any, ttl: float = 86400.0) -> None:
    """Write to persistent SQLite cache."""
    try:
        with sqlite3.connect(str(_CACHE_DB)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO macrostrat_cache
                   (cache_key, endpoint, params, response, cached_at, ttl)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (cache_key, endpoint, json.dumps(params, sort_keys=True, default=str),
                 json.dumps(response), time.time(), ttl),
            )
            conn.commit()
    except Exception as exc:
        logger.debug("Persistent cache write error: %s", exc)


# ── Macrostrat Client ──────────────────────────────────────────────────────────

class MacrostratClient:
    """Dedicated client for the Macrostrat API v2.

    Usage:
        client = MacrostratClient()
        units = await client.get_units(lat=3.5, lng=103.5)
        columns = await client.get_columns(lat=3.5, lng=103.5, radius_km=100)
        liths = await client.get_lithologies()
        map_units = await client.get_geologic_units_map(lat=3.5, lng=103.5)
    """

    def __init__(self, base_url: str = MACROSTRAT_BASE, timeout: float = 30.0) -> None:
        self.base_url = base_url
        self.timeout = timeout
        _init_cache_db()

    # ── Core HTTP ────────────────────────────────────────────────────────

    async def _request(self, endpoint: str, params: dict[str, Any] | None = None,
                       use_cache: bool = True, cache_ttl: float = 86400.0) -> dict[str, Any]:
        """Make a Macrostrat API request with multi-layer caching.

        Cache layers (tried in order):
          1. In-memory TTL dict (fastest, 1hr TTL)
          2. Persistent SQLite (survives restart, defaults 24hr TTL)
          3. Live HTTP request
        """
        params = params or {}
        cache_key = _build_cache_key(endpoint, params) if use_cache else ""

        # Layer 1: in-memory cache
        if use_cache and cache_key in _IN_MEMORY_CACHE:
            cached_at, data = _IN_MEMORY_CACHE[cache_key]
            if (time.monotonic() - cached_at) < _IN_MEMORY_TTL:
                logger.debug("Memory cache HIT: %s", cache_key[:60])
                return data  # type: ignore[return-value]

        # Layer 2: persistent cache
        if use_cache:
            cached = _get_from_persistent_cache(cache_key)
            if cached is not None:
                # Promote to in-memory for faster subsequent access
                _IN_MEMORY_CACHE[cache_key] = (time.monotonic(), cached)
                logger.debug("Persistent cache HIT: %s", cache_key[:60])
                return cached  # type: ignore[return-value]

        # Layer 3: live HTTP
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Macrostrat HTTP %s: %s @ %s", exc.response.status_code, endpoint, params)
            return {"error": f"HTTP {exc.response.status_code}", "success": {"data": []}}
        except httpx.TimeoutException:
            logger.warning("Macrostrat timeout: %s @ %s", endpoint, params)
            return {"error": "timeout", "success": {"data": []}}
        except Exception as exc:
            logger.warning("Macrostrat error (%s): %s", endpoint, exc)
            return {"error": str(exc), "success": {"data": []}}

        # Populate both caches
        if use_cache:
            _IN_MEMORY_CACHE[cache_key] = (time.monotonic(), data)
            _set_persistent_cache(cache_key, endpoint, params, data, ttl=cache_ttl)
            logger.debug("Cache SET: %s", cache_key[:60])

        return data

    # ── Units ────────────────────────────────────────────────────────────

    async def get_units(self, lat: float | None = None, lng: float | None = None,
                        radius_km: float | None = None,
                        bbox: tuple[float, float, float, float] | None = None,
                        col_id: int | None = None,
                        unit_id: int | None = None,
                        interval_name: str | None = None,
                        strat_name_id: int | None = None,
                        project_id: int | None = None,
                        all_units: bool = False,
                        **extra: Any) -> dict[str, Any]:
        """Get rock units from Macrostrat.

        Returns units near a point, within a radius, or in a bbox.
        The richest endpoint — lithology, age, thickness, formation names.
        """
        params: dict[str, Any] = {"format": "json"}
        if all_units:
            params["all"] = True
        else:
            if lat is not None and lng is not None:
                params["lat"] = lat
                params["lng"] = lng
            if bbox:
                params["lng"] = f"{bbox[0]},{bbox[2]}"
                params["lat"] = f"{bbox[1]},{bbox[3]}"
        if radius_km:
            params["radius"] = radius_km
        if col_id:
            params["col_id"] = col_id
        if unit_id:
            params["unit_id"] = unit_id
        if interval_name:
            params["interval_name"] = interval_name
        if strat_name_id:
            params["strat_name_id"] = strat_name_id
        if project_id:
            params["project_id"] = project_id
        params.update(extra)
        return await self._request("units", params)

    # ── Columns ──────────────────────────────────────────────────────────

    async def get_columns(self, lat: float | None = None, lng: float | None = None,
                          radius_km: float | None = None,
                          bbox: tuple[float, float, float, float] | None = None,
                          col_id: int | None = None,
                          col_name: str | None = None,
                          col_group: str | None = None,
                          project_id: int | None = None,
                          all_columns: bool = False,
                          **extra: Any) -> dict[str, Any]:
        """Get stratigraphic columns.

        Columns define the regional rock packages ordered by age.
        Returns GeoJSON FeatureCollection when format=geojson.
        """
        params: dict[str, Any] = {"format": "geojson"}
        if all_columns:
            params["all"] = True
        else:
            if lat is not None and lng is not None:
                params["lat"] = lat
                params["lng"] = lng
            if bbox:
                params["lng"] = f"{bbox[0]},{bbox[2]}"
                params["lat"] = f"{bbox[1]},{bbox[3]}"
        if radius_km:
            params["radius"] = radius_km
        if col_id:
            params["col_id"] = col_id
        if col_name:
            params["col_name"] = col_name
        if col_group:
            params["col_group"] = col_group
        if project_id:
            params["project_id"] = project_id
        params.update(extra)
        return await self._request("columns", params)

    # ── Geologic Map Units ───────────────────────────────────────────────

    async def get_geologic_units_map(self, lat: float | None = None,
                                      lng: float | None = None,
                                      radius_km: float | None = None,
                                      bbox: tuple[float, float, float, float] | None = None,
                                      source_id: int | None = None,
                                      scale: str | None = None,
                                      all_units: bool = False,
                                      **extra: Any) -> dict[str, Any]:
        """Get geologic map polygons (2.5M+ features).

        This is Macrostrat's richest spatial dataset — homogenized maps
        from 225+ sources at multiple scales (tiny → large).
        """
        params: dict[str, Any] = {}
        if all_units:
            params["all"] = True
        else:
            if lat is not None and lng is not None:
                params["lat"] = lat
                params["lng"] = lng
            if bbox:
                params["lng"] = f"{bbox[0]},{bbox[2]}"
                params["lat"] = f"{bbox[1]},{bbox[3]}"
        if radius_km:
            params["radius"] = radius_km
        if source_id:
            params["source_id"] = source_id
        if scale:
            params["scale"] = scale
        params.update(extra)
        return await self._request("geologic_units/map", params)

    # ── Definitions ──────────────────────────────────────────────────────

    async def get_lithologies(self, all_: bool = True) -> dict[str, Any]:
        """Get lithology types (214 rock types)."""
        return await self._request("defs/lithologies", {"all": all_} if all_ else {})

    async def get_environments(self, all_: bool = True) -> dict[str, Any]:
        """Get depositional environments."""
        return await self._request("defs/environments", {"all": all_} if all_ else {})

    async def get_strat_names(self, strat_name: str | None = None,
                               rank: str | None = None,
                               all_: bool = False,
                               limit: int = 50) -> dict[str, Any]:
        """Get stratigraphic names lexicon (51k+ entries).

        Resolves formation, member, group names to ages, lithology, and hierarchy.
        """
        params: dict[str, Any] = {}
        if all_:
            params["all"] = True
        if strat_name:
            params["strat_name"] = strat_name
        if rank:
            params["rank"] = rank
        if limit and not all_:
            params["limit"] = limit
        return await self._request("defs/strat_names", params)

    async def get_intervals(self, all_: bool = True) -> dict[str, Any]:
        """Get geologic time intervals (1,716 entries)."""
        return await self._request("defs/intervals", {"all": all_} if all_ else {})

    async def get_minerals(self, all_: bool = True) -> dict[str, Any]:
        """Get mineral types."""
        return await self._request("defs/minerals", {"all": all_} if all_ else {})

    async def get_sources(self, all_: bool = True, scale: str | None = None) -> dict[str, Any]:
        """Get map sources (225+ maps from surveys worldwide)."""
        params: dict[str, Any] = {}
        if all_:
            params["all"] = True
        if scale:
            params["scale"] = scale
        return await self._request("defs/sources", params)

    # ── Fossils ──────────────────────────────────────────────────────────

    async def get_fossils(self, unit_id: int | None = None,
                           interval_name: str | None = None,
                           taxon: str | None = None,
                           col_id: int | None = None,
                           limit: int = 50) -> dict[str, Any]:
        """Get PBDB fossil occurrences matched to Macrostrat units."""
        params: dict[str, Any] = {}
        if unit_id:
            params["unit_id"] = unit_id
        if interval_name:
            params["interval_name"] = interval_name
        if taxon:
            params["taxon"] = taxon
        if col_id:
            params["col_id"] = col_id
        if limit:
            params["limit"] = limit
        return await self._request("fossils", params)

    # ── Stats ────────────────────────────────────────────────────────────

    async def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        return await self._request("stats", {"all": True})

    # ── Utility ──────────────────────────────────────────────────────────

    def get_units_summary(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract and normalize units from API response."""
        success = data.get("success", {})
        raw = success.get("data", [])
        if isinstance(raw, dict):
            raw = raw.get("features", raw)
        if isinstance(raw, list):
            return raw
        return []

    def get_columns_summary(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract and normalize columns from API GeoJSON response."""
        success = data.get("success", {})
        raw = success.get("data", {})
        if isinstance(raw, dict):
            features = raw.get("features", [])
        elif isinstance(raw, list):
            features = raw
        else:
            features = []
        result = []
        for feat in features:
            props = feat.get("properties", {})
            result.append({
                "col_id": props.get("col_id"),
                "col_name": props.get("col_name"),
                "col_group": props.get("col_group"),
                "lat": props.get("lat"),
                "lng": props.get("lng"),
                "col_type": props.get("col_type"),
                "project_id": props.get("project_id"),
            })
        return result

    # ── Attribution ──────────────────────────────────────────────────────

    @staticmethod
    def attribution_text() -> str:
        """CC-BY-4.0 attribution for reports using Macrostrat data."""
        return (
            "*Geological data provided by Macrostrat (macrostrat.org) "
            "under CC-BY-4.0 license. "
            "Citation: Peters et al. (2018) "
            "doi:10.17605/OSF.IO/YNAXW*"
        )

    @staticmethod
    def attribution_markdown() -> str:
        return f"**Macrostrat:** {MACROSTRAT_CITATION} | Data: [macrostrat.org](https://macrostrat.org) (CC-BY-4.0)"

    # ── Cache Management ─────────────────────────────────────────────────

    @staticmethod
    def cache_stats() -> dict[str, Any]:
        """Return cache statistics."""
        mem_count = len(_IN_MEMORY_CACHE)
        disk_count = 0
        try:
            with sqlite3.connect(str(_CACHE_DB)) as conn:
                disk_count = conn.execute("SELECT COUNT(*) FROM macrostrat_cache").fetchone()[0]
        except Exception:
            pass
        return {
            "memory_entries": mem_count,
            "disk_entries": disk_count,
            "cache_db_path": str(_CACHE_DB),
            "memory_ttl_seconds": _IN_MEMORY_TTL,
            "disk_default_ttl_seconds": 86400,
        }

    @staticmethod
    def clear_cache() -> dict[str, Any]:
        """Clear both cache layers."""
        before = len(_IN_MEMORY_CACHE)
        _IN_MEMORY_CACHE.clear()
        try:
            with sqlite3.connect(str(_CACHE_DB)) as conn:
                conn.execute("DELETE FROM macrostrat_cache")
                conn.commit()
        except Exception as exc:
            return {"cleared_memory": before, "disk_error": str(exc)}
        return {"cleared_memory": before, "cleared_disk": True}

    # ── SE Asia Cache Warming ────────────────────────────────────────────

    async def warm_se_asia(self) -> dict[str, Any]:
        """Pre-cache Macrostrat data for key SE Asian basins.

        This is critical because Macrostrat has ZERO native SE Asia coverage.
        Warming the cache ensures at least the World map data is available.
        """
        results: dict[str, Any] = {"warmed": [], "errors": []}
        for hotspot in SE_ASIA_HOTSPOTS:
            try:
                # Units near basin
                units = await self.get_units(
                    lat=hotspot["lat"], lng=hotspot["lng"],
                    radius_km=hotspot["radius_km"],
                )
                unit_count = len(self.get_units_summary(units))
                # Geologic map polygons
                maps = await self.get_geologic_units_map(
                    lat=hotspot["lat"], lng=hotspot["lng"],
                    radius_km=hotspot["radius_km"],
                )
                results["warmed"].append({
                    "basin": hotspot["name"],
                    "lat": hotspot["lat"],
                    "lng": hotspot["lng"],
                    "units_found": unit_count,
                    "maps_found": len(maps.get("success", {}).get("data", [])),
                })
                logger.info("SE Asia cache warm: %s = %d units",
                            hotspot["name"], unit_count)
            except Exception as exc:
                results["errors"].append({"basin": hotspot["name"], "error": str(exc)})
                logger.warning("SE Asia cache warm FAIL: %s: %s", hotspot["name"], exc)
        return results
