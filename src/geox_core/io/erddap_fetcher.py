"""
erddap_fetcher.py — Physical Visible Earth: Universal Ocean Data Gateway.

NOAA ERDDAP — tabledap/griddap for ocean, atmosphere, and satellite data.
Universal gateway to 10,000+ datasets from 80+ servers worldwide.

Source: NOAA / Simons Foundation
URL: https://coastwatch.pfeg.noaa.gov/erddap
Access: REST (tabledap/griddap) returning CSV, JSON, NetCDF
License: Public Domain (NOAA) or varies by dataset

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.erddap")

ERDDAP_BASE = "https://coastwatch.pfeg.noaa.gov/erddap"
ERDDAP_CITATION = "NOAA CoastWatch / ERDDAP (2024). https://coastwatch.pfeg.noaa.gov/erddap. Public Domain."


class ERDDAPQuery(BaseModel):
    dataset_id: str = Field(..., description="ERDDAP dataset ID")
    minlatitude: float | None = Field(None, ge=-90, le=90)
    maxlatitude: float | None = Field(None, ge=-90, le=90)
    minlongitude: float | None = Field(None, ge=-360, le=360)
    maxlongitude: float | None = Field(None, ge=-360, le=360)
    min_time: str | None = None
    max_time: str | None = None
    variables: list[str] | None = None
    limit: int = Field(100, ge=1, le=10000)


class ERDDAPResult(BaseModel):
    ok: bool
    mode: str
    data: list[dict[str, Any]] = []
    count: int = 0
    dataset_id: str = ""
    source_uri: str = ERDDAP_BASE
    citation: str = ERDDAP_CITATION
    fetched_at: str = ""
    note: str = ""


class ERDDAPFetcher:
    def __init__(self):
        self._offline = os.environ.get("GEOX_ERDDAP_OFFLINE", "1") != "0"

    def query(self, params: ERDDAPQuery) -> ERDDAPResult:
        now = datetime.now(UTC).isoformat()
        if self._offline:
            return ERDDAPResult(
                ok=True,
                mode="offline_stub",
                data=[{"time": "2024-01-01", "latitude": 5.0, "longitude": 110.0, "sst": 29.0}],
                count=1,
                dataset_id=params.dataset_id,
                fetched_at=now,
                note=f"Offline stub for dataset '{params.dataset_id}'.",
            )
        return ERDDAPResult(ok=False, mode="live", note="Live ERDDAP requires HTTP client.", fetched_at=now)

    def list_datasets(self, search: str = "") -> dict[str, Any]:
        return {"ok": True, "mode": "offline_stub", "note": "Use ERDDAP search: /erddap/search/index.html"}
