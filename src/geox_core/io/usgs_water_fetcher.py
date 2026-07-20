"""
usgs_water_fetcher.py — Physical Visible Earth: Streamflow & Groundwater.

USGS Water Services — real-time and historical streamflow, groundwater,
and water quality for the United States.

Source: USGS Water Resources
URL: https://waterservices.usgs.gov
Access: REST API (JSON/CSV)
License: Public Domain (USGS)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.usgs_water")

USGS_WATER_BASE = "https://waterservices.usgs.gov/nwis"
USGS_WATER_CITATION = (
    "USGS Water Resources (2024). National Water Information System. https://waterservices.usgs.gov. Public Domain."
)


class WaterQuery(BaseModel):
    minlatitude: float | None = Field(None, ge=-90, le=90)
    maxlatitude: float | None = Field(None, ge=-90, le=90)
    minlongitude: float | None = Field(None, ge=-360, le=360)
    maxlongitude: float | None = Field(None, ge=-360, le=360)
    state_code: str | None = Field(None, description="US state FIPS code")
    site_type: str | None = Field(None, description="ST=stream, GW=well, SP=spring")
    parameter_code: str = Field("00060", description="00060=discharge, 00010=temperature, 72019=GW level")
    period: str = Field("P7D", description="ISO 8601 duration (e.g., P7D, P30D, P1Y)")
    limit: int = Field(100, ge=1, le=10000)


class WaterResult(BaseModel):
    ok: bool
    mode: str
    sites: list[dict[str, Any]] = []
    count: int = 0
    query_params: dict[str, Any] = {}
    source_uri: str = USGS_WATER_BASE
    citation: str = USGS_WATER_CITATION
    fetched_at: str = ""
    note: str = ""


class USGSWaterFetcher:
    def __init__(self):
        self._offline = os.environ.get("GEOX_USGS_WATER_OFFLINE", "1") != "0"

    def query(self, params: WaterQuery) -> WaterResult:
        now = datetime.now(UTC).isoformat()
        if self._offline:
            return WaterResult(
                ok=True,
                mode="offline_stub",
                sites=[
                    {
                        "site_code": "12345678",
                        "site_name": "Sample Creek",
                        "latitude": 38.9,
                        "longitude": -77.0,
                        "value": 150.0,
                        "unit": "cfs",
                    }
                ],
                count=1,
                query_params=params.model_dump(exclude_none=True),
                fetched_at=now,
                note="Offline stub. USGS Water covers US only.",
            )
        return WaterResult(ok=False, mode="live", note="Live requires HTTP client to USGS Water Services.", fetched_at=now)
