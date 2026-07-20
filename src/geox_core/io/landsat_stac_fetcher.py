"""
landsat_stac_fetcher.py — Physical Visible Earth: Land Surface / Satellite Imagery.

Landsat, MODIS, Sentinel-2 via STAC (SpatioTemporal Asset Catalogs).
Microsoft Planetary Computer + USGS Earthdata as gateways.

Source: NASA/USGS (Landsat), ESA (Sentinel), NASA (MODIS)
Access: STAC API (catalog search + asset download)
License: Public Domain (USGS/NASA), Open (ESA Copernicus)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.landsat_stac")

STAC_BASE = "https://planetarycomputer.microsoft.com/api/stac/v1"
EARTHDATA_CMR = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD"
LANDSAT_CITATION = "USGS/NASA Landsat (2024). Landsat Collection 2 via STAC. Public Domain. Microsoft Planetary Computer gateway."
MODIS_CITATION = "NASA LP DAAC (2024). MODIS Land Products via STAC. Public Domain."


class SatelliteQuery(BaseModel):
    minlatitude: float = Field(..., ge=-90, le=90)
    maxlatitude: float = Field(..., ge=-90, le=90)
    minlongitude: float = Field(..., ge=-360, le=360)
    maxlongitude: float = Field(..., ge=-360, le=360)
    datetime_range: str = Field("2024-01-01/2024-12-31", description="ISO 8601 interval")
    collection: str = Field("landsat-c2-l2", description="landsat-c2-l2 | sentinel-2-l2a | modis")
    cloud_cover_max: float = Field(20.0, ge=0, le=100)
    limit: int = Field(10, ge=1, le=100)


class SatelliteResult(BaseModel):
    ok: bool
    mode: str
    items: list[dict[str, Any]] = []
    count: int = 0
    collection: str = ""
    source_uri: str = STAC_BASE
    citation: str = LANDSAT_CITATION
    fetched_at: str = ""
    note: str = ""


class LandsatSTACFetcher:
    def __init__(self):
        self._offline = os.environ.get("GEOX_STAC_OFFLINE", "1") != "0"

    def query(self, params: SatelliteQuery) -> SatelliteResult:
        now = datetime.now(UTC).isoformat()
        if self._offline:
            return SatelliteResult(
                ok=True,
                mode="offline_stub",
                items=[{"id": "LC08_L2SP_stub", "collection": params.collection, "cloud_cover": 5.0, "datetime": "2024-06-15"}],
                count=1,
                collection=params.collection,
                fetched_at=now,
                note="Offline stub. Requires STAC client (pystac-client).",
            )
        return SatelliteResult(ok=False, mode="live", note="Live requires pystac-client.", fetched_at=now)
