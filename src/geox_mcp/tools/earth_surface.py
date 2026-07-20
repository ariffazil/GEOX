"""
earth_surface.py — MCP tools for the Physical Visible Earth.

Three tools covering the surface/skin of the planet:
  1. geox_earthquake_catalog  — USGS FDSN seismic event catalog
  2. geox_relief_ingest       — ETOPO 2022 global topography + bathymetry
  3. geox_bathymetry_ingest   — GEBCO_2026 ocean floor terrain

These are the "visible skin" of the Earth — complementary to GEOX's
existing subsurface tools (well logs, seismic reflection, gravity/mag).

All tools follow GEOX constitutional envelope:
  - Provenance attached (source_uri, fetched_at, citation)
  - Mode field (live | offline_stub | cached | opendap)
  - F2 TRUTH: data labeled with epistemic status
  - F7 HUMILITY: offline mode clearly marked

DITEMPA BUKAN DIBERI — the physical earth is forged through evidence.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from geox_core.io.etopo_fetcher import (
    ETOPO_CITATION,
    ETOPOExtractRequest,
    ETOPOFetcher,
)
from geox_core.io.gebco_fetcher import (
    GEBCO_CITATION,
    GEBCOExtractRequest,
    GEBCOFetcher,
)
from geox_core.io.usgs_earthquake_fetcher import (
    USGS_CITATION,
    EarthquakeEvent,
    EarthquakeQuery,
    USGSEarthquakeFetcher,
)

logger = logging.getLogger("geox.tools.earth_surface")


# ───────────────────────────── 1. EARTHQUAKE CATALOG ─────────────────────────────


class EarthquakeCatalogRequest(BaseModel):
    """Request for USGS earthquake catalog query."""

    starttime: str | None = Field(None, description="ISO8601 start (default: NOW-30d)")
    endtime: str | None = Field(None, description="ISO8601 end (default: now)")
    minlatitude: float | None = Field(None, ge=-90, le=90)
    maxlatitude: float | None = Field(None, ge=-90, le=90)
    minlongitude: float | None = Field(None, ge=-360, le=360)
    maxlongitude: float | None = Field(None, ge=-360, le=360)
    latitude: float | None = Field(None, ge=-90, le=90, description="Circle center lat")
    longitude: float | None = Field(None, ge=-180, le=180, description="Circle center lon")
    maxradiuskm: float | None = Field(None, ge=0, le=20002, description="Circle radius km")
    minmagnitude: float | None = Field(None, description="Minimum magnitude")
    maxmagnitude: float | None = Field(None, description="Maximum magnitude")
    mindepth: float | None = Field(None, ge=-100, le=1000, description="Min depth km")
    maxdepth: float | None = Field(None, ge=-100, le=1000, description="Max depth km")
    limit: int = Field(100, ge=1, le=20000, description="Max events to return")
    orderby: str = Field("time", description="time | time-asc | magnitude | magnitude-asc")
    alertlevel: str | None = Field(None, description="PAGER: green/yellow/orange/red")
    eventtype: str | None = Field(None, description="earthquake, quarry blast, etc.")


class EarthquakeCatalogResponse(BaseModel):
    """Response from USGS earthquake catalog query."""

    ok: bool
    tool: str = "geox_earthquake_catalog"
    mode: str  # "live" | "offline_stub"
    events: list[dict[str, Any]] = []
    count: int = 0
    query_params: dict[str, Any] = {}
    source_uri: str = ""
    citation: str = USGS_CITATION
    fetched_at: str = ""
    note: str = ""
    epistemic_status: str = "OBSERVED"  # real seismic events


async def geox_earthquake_catalog(
    request: EarthquakeCatalogRequest,
) -> EarthquakeCatalogResponse:
    """Query the USGS Earthquake Catalog for seismic events.

    Returns real-time and historical earthquake data with location,
    magnitude, depth, PAGER alert level, and tsunami flags.

    Data source: USGS FDSN Event Web Service (Public Domain).
    Epistemic status: OBSERVED — these are measured seismic events.

    Modes:
    - Default (offline): returns sample events for schema validation.
    - Set GEOX_USGS_EQ_OFFLINE=0: live API query to USGS.
    """
    try:
        fetcher = USGSEarthquakeFetcher()
        query = EarthquakeQuery(**request.model_dump())
        result = fetcher.query(query)

        return EarthquakeCatalogResponse(
            ok=result.ok,
            mode=result.mode,
            events=[_event_to_dict(e) for e in result.events],
            count=result.count,
            query_params=result.query_params,
            source_uri=result.source_uri,
            citation=result.citation,
            fetched_at=result.fetched_at,
            note=result.note,
        )
    except Exception as e:
        logger.error(f"geox_earthquake_catalog failed: {e}")
        return EarthquakeCatalogResponse(
            ok=False,
            mode="error",
            note=f"Error: {e}",
        )


def _event_to_dict(e: EarthquakeEvent) -> dict[str, Any]:
    """Convert EarthquakeEvent to a dict for JSON serialization."""
    return {
        "event_id": e.event_id,
        "time_utc": e.time_utc,
        "latitude": e.latitude,
        "longitude": e.longitude,
        "depth_km": e.depth_km,
        "magnitude": e.magnitude,
        "magnitude_type": e.magnitude_type,
        "place": e.place,
        "event_type": e.event_type,
        "status": e.status,
        "tsunami_flag": e.tsunami_flag,
        "felt": e.felt,
        "cdi": e.cdi,
        "mmi": e.mmi,
        "alert_level": e.alert_level,
        "url": e.url,
    }


# ───────────────────────────── 2. RELIEF INGEST (ETOPO) ─────────────────────────


class ReliefIngestRequest(BaseModel):
    """Request for ETOPO global relief data."""

    mode: str = Field("global", description="global | bbox")
    west: float | None = Field(None, ge=-180, le=180)
    east: float | None = Field(None, ge=-180, le=180)
    south: float | None = Field(None, ge=-90, le=90)
    north: float | None = Field(None, ge=-90, le=90)
    resolution: int = Field(15, description="Arc-seconds: 15, 30, or 60")
    version: str = Field("bedrock", description="bedrock | ice_surface")
    output_format: str = Field("geotiff", description="geotiff | netcdf")


class ReliefIngestResponse(BaseModel):
    """Response from ETOPO relief ingest."""

    ok: bool
    tool: str = "geox_relief_ingest"
    mode: str  # "live" | "offline_stub" | "cached"
    grid_path: str | None = None
    meta: dict[str, Any] | None = None
    citation: str = ETOPO_CITATION
    note: str = ""
    epistemic_status: str = "OBSERVED"  # measured elevation data


async def geox_relief_ingest(
    request: ReliefIngestRequest,
) -> ReliefIngestResponse:
    """Ingest ETOPO 2022 global relief data (topography + bathymetry).

    Returns elevation grid metadata and file path (if cached/downloaded).
    Supports global fetch or bounding box subsetting.

    Data source: NOAA NCEI ETOPO 2022 (Public Domain).
    Epistemic status: OBSERVED — measured elevation/bathymetry.

    Modes:
    - Default (offline): returns stub metadata for schema validation.
    - Set GEOX_ETOPO_OFFLINE=0: checks local cache for downloaded files.
    - For bbox subsets: use Grid Extract API at ncei.noaa.gov/maps/grid-extract/
    """
    try:
        fetcher = ETOPOFetcher()

        if request.mode == "bbox" and all(v is not None for v in [request.west, request.east, request.south, request.north]):
            extract = ETOPOExtractRequest(
                west=request.west,
                east=request.east,
                south=request.south,
                north=request.north,
                resolution=request.resolution,
                version=request.version,
                output_format=request.output_format,
            )
            result = fetcher.fetch_bbox(extract)
        else:
            result = fetcher.fetch_global(
                resolution=request.resolution,
                version=request.version,
                output_format=request.output_format,
            )

        meta_dict = None
        if result.meta:
            meta_dict = {
                "source_uri": result.meta.source_uri,
                "fetched_at": result.meta.fetched_at,
                "resolution_arcsec": result.meta.resolution_arcsec,
                "version": result.meta.version,
                "crs": result.meta.crs,
                "bbox": list(result.meta.bbox),
                "elevation_min_m": result.meta.elevation_min_m,
                "elevation_max_m": result.meta.elevation_max_m,
            }

        return ReliefIngestResponse(
            ok=result.ok,
            mode=result.mode,
            grid_path=result.grid_path,
            meta=meta_dict,
            citation=result.citation,
            note=result.note,
        )
    except Exception as e:
        logger.error(f"geox_relief_ingest failed: {e}")
        return ReliefIngestResponse(
            ok=False,
            mode="error",
            note=f"Error: {e}",
        )


# ───────────────────────────── 3. BATHYMETRY INGEST (GEBCO) ─────────────────────


class BathymetryIngestRequest(BaseModel):
    """Request for GEBCO bathymetry data."""

    mode: str = Field("global", description="global | bbox")
    west: float | None = Field(None, ge=-180, le=180)
    east: float | None = Field(None, ge=-180, le=180)
    south: float | None = Field(None, ge=-90, le=90)
    north: float | None = Field(None, ge=-90, le=90)
    variant: str = Field("ice_surface", description="ice_surface | sub_ice | tid")
    output_format: str = Field("netcdf", description="netcdf | geotiff")


class BathymetryIngestResponse(BaseModel):
    """Response from GEBCO bathymetry ingest."""

    ok: bool
    tool: str = "geox_bathymetry_ingest"
    mode: str  # "live" | "offline_stub" | "cached" | "opendap"
    grid_path: str | None = None
    opendap_url: str | None = None
    meta: dict[str, Any] | None = None
    citation: str = GEBCO_CITATION
    note: str = ""
    epistemic_status: str = "OBSERVED"  # measured bathymetry


async def geox_bathymetry_ingest(
    request: BathymetryIngestRequest,
) -> BathymetryIngestResponse:
    """Ingest GEBCO_2026 global bathymetry grid (ocean floor terrain).

    Returns bathymetry grid metadata and access path (OPeNDAP URL or cached file).
    Supports global fetch or bounding box subsetting via OPeNDAP.

    Data source: GEBCO/IHO/UNESCO (Public Domain).
    Epistemic status: OBSERVED — measured ocean depth.

    Modes:
    - Default (offline): returns stub metadata for schema validation.
    - Set GEOX_GEBCO_OFFLINE=0: OPeNDAP subsetting from CEDA server.
    - For full grid: download from download.gebco.net (~4 GB).
    """
    try:
        fetcher = GEBCOFetcher()

        if request.mode == "bbox" and all(v is not None for v in [request.west, request.east, request.south, request.north]):
            extract = GEBCOExtractRequest(
                west=request.west,
                east=request.east,
                south=request.south,
                north=request.north,
                variant=request.variant,
                output_format=request.output_format,
            )
            result = fetcher.fetch_bbox(extract)
        else:
            result = fetcher.fetch_global(
                variant=request.variant,
                output_format=request.output_format,
            )

        meta_dict = None
        if result.meta:
            meta_dict = {
                "source_uri": result.meta.source_uri,
                "fetched_at": result.meta.fetched_at,
                "resolution_arcsec": result.meta.resolution_arcsec,
                "grid_version": result.meta.grid_version,
                "variant": result.meta.variant,
                "crs": result.meta.crs,
                "bbox": list(result.meta.bbox),
                "depth_min_m": result.meta.depth_min_m,
                "depth_max_m": result.meta.depth_max_m,
            }

        return BathymetryIngestResponse(
            ok=result.ok,
            mode=result.mode,
            grid_path=result.grid_path,
            opendap_url=result.opendap_url,
            meta=meta_dict,
            citation=result.citation,
            note=result.note,
        )
    except Exception as e:
        logger.error(f"geox_bathymetry_ingest failed: {e}")
        return BathymetryIngestResponse(
            ok=False,
            mode="error",
            note=f"Error: {e}",
        )


__all__ = [
    "geox_earthquake_catalog",
    "geox_relief_ingest",
    "geox_bathymetry_ingest",
]
