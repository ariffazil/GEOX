"""
copernicus_marine_fetcher.py — Physical Visible Earth: Ocean Physics/BGC.

Copernicus Marine Environment Monitoring Service (CMEMS).
306+ products: physical, biogeochemical, waves, sea ice.

Source: EU Copernicus / Mercator Ocean
URL: https://marine.copernicus.eu
Access: copernicusmarine Python toolbox + WMTS + CSW
License: EU Open Data (free with registration)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

CMEMS_BASE = "https://marine.copernicus.eu"
CMEMS_CITATION = (
    "Copernicus Marine Service (2024). CMEMS — Global Ocean Physics and BGC. "
    "https://marine.copernicus.eu. EU Open Data License."
)


class OceanQuery(BaseModel):
    minlatitude: float = Field(-90, ge=-90, le=90)
    maxlatitude: float = Field(90, ge=-90, le=90)
    minlongitude: float = Field(-180, ge=-360, le=360)
    maxlongitude: float = Field(180, ge=-360, le=360)
    variable: str = Field("temperature", description="temperature | salinity | current | chlorophyll | sea_ice")
    depth_m: Optional[float] = None
    date: Optional[str] = None


class OceanResult(BaseModel):
    ok: bool
    mode: str
    data: list[dict[str, Any]] = []
    count: int = 0
    variable: str = ""
    source_uri: str = CMEMS_BASE
    citation: str = CMEMS_CITATION
    fetched_at: str = ""
    note: str = ""


class CopernicusMarineFetcher:
    def __init__(self):
        self._offline = os.environ.get("GEOX_CMEMS_OFFLINE", "1") != "0"

    def query(self, params: OceanQuery) -> OceanResult:
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return OceanResult(
                ok=True, mode="offline_stub",
                data=[{"latitude": 5.0, "longitude": 110.0, params.variable: 28.5}],
                count=1, variable=params.variable, fetched_at=now,
                note="Offline stub. Requires copernicusmarine Python package + registration."
            )
        return OceanResult(ok=False, mode="live", note="Live requires copernicusmarine package.", fetched_at=now)
