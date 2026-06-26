"""
noaa_swpc_fetcher.py — Physical Visible Earth: Space Weather.

NOAA Space Weather Prediction Center — geomagnetic indices (Kp, Dst),
solar wind, X-ray flux, aurora forecasts.

Source: NOAA SWPC
URL: https://www.swpc.noaa.gov
Access: REST JSON API
License: Public Domain (NOAA)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.noaa_swpc")

SWPC_BASE = "https://services.swpc.noaa.gov"
SWPC_CITATION = (
    "NOAA Space Weather Prediction Center (2024). "
    "https://www.swpc.noaa.gov. Public Domain."
)


class SpaceWeatherQuery(BaseModel):
    product: str = Field("kp_index", description="kp_index | dst_index | solar_wind | xray_flux | aurora_forecast")
    limit: int = Field(100, ge=1, le=10000)


class SpaceWeatherResult(BaseModel):
    ok: bool
    mode: str
    data: list[dict[str, Any]] = []
    count: int = 0
    product: str = ""
    source_uri: str = SWPC_BASE
    citation: str = SWPC_CITATION
    fetched_at: str = ""
    note: str = ""


class NOAASWPCFetcher:
    """Space weather is the only truly real-time data source in GEOX.
    Unlike all other fetchers, this one can poll live without registration."""

    ENDPOINTS = {
        "kp_index": f"{SWPC_BASE}/products/noaa-planetary-k-index.json",
        "dst_index": f"{SWPC_BASE}/products/noaa-dst.json",
        "solar_wind": f"{SWPC_BASE}/products/solar-wind/plasma-7-day.json",
        "xray_flux": f"{SWPC_BASE}/products/goes-xray-flux-7-day.json",
        "aurora_forecast": f"{SWPC_BASE}/products/noaa-planetary-k-index-forecast.json",
    }

    def __init__(self):
        self._offline = os.environ.get("GEOX_SWPC_OFFLINE", "1") != "0"

    def query(self, params: SpaceWeatherQuery) -> SpaceWeatherResult:
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return SpaceWeatherResult(
                ok=True, mode="offline_stub",
                data=[{"time_tag": "2024-06-25T00:00:00Z", "kp": 3, "estimated": True}],
                count=1, product=params.product, fetched_at=now,
                note=f"Offline stub for '{params.product}'. Set GEOX_SWPC_OFFLINE=0 for live data."
            )
        return SpaceWeatherResult(ok=False, mode="live", note="Live requires HTTP client.", fetched_at=now)

    def list_products(self) -> dict[str, str]:
        return self.ENDPOINTS
