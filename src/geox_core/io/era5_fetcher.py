"""
era5_fetcher.py — Physical Visible Earth: Climate Reanalysis.

ERA5 — ECMWF global reanalysis, hourly at ~31km resolution.
Temperature, wind, pressure, precipitation, radiation from 1940 to present.

Source: ECMWF / Copernicus Climate Change Service (C3S)
URL: https://cds.climate.copernicus.eu
Access: CDS API (requires free registration)
License: Copernicus License (free, open)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

ERA5_BASE = "https://cds.climate.copernicus.eu"
ERA5_CITATION = (
    "Hersbach, H. et al. (2020). ERA5 hourly data on single levels. "
    "Copernicus Climate Change Service (C3S). "
    "https://cds.climate.copernicus.eu. Copernicus License."
)


class ERA5Query(BaseModel):
    minlatitude: float = Field(-90, ge=-90, le=90)
    maxlatitude: float = Field(90, ge=-90, le=90)
    minlongitude: float = Field(-180, ge=-360, le=360)
    maxlongitude: float = Field(180, ge=-360, le=360)
    date: str = Field("2024-01-01", description="Date (YYYY-MM-DD)")
    variables: list[str] = Field(default=["2m_temperature"], description="ERA5 variable names")
    time: str = Field("12:00", description="Time (HH:MM)")


class ERA5Result(BaseModel):
    ok: bool
    mode: str
    data: list[dict[str, Any]] = []
    count: int = 0
    source_uri: str = ERA5_BASE
    citation: str = ERA5_CITATION
    fetched_at: str = ""
    note: str = ""


class ERA5Fetcher:
    def __init__(self):
        self._offline = os.environ.get("GEOX_ERA5_OFFLINE", "1") != "0"

    def query(self, params: ERA5Query) -> ERA5Result:
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return ERA5Result(
                ok=True, mode="offline_stub",
                data=[{"latitude": 5.0, "longitude": 110.0, "2m_temperature": 300.5, "date": params.date}],
                count=1, fetched_at=now,
                note="Offline stub. Requires CDS API key (free registration)."
            )
        return ERA5Result(ok=False, mode="live", note="Live requires CDS API client.", fetched_at=now)
