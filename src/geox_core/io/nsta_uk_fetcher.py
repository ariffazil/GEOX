"""
nsta_uk_fetcher.py — Physical Visible Earth: UK Petroleum Data.

NSTA (North Sea Transition Authority) — UK offshore wells, fields, licences.
Open Data portal with REST access.

Source: NSTA (formerly OGA/BEIS)
URL: https://www.nstauthority.co.uk
Data: https://data.nstauthority.co.uk
License: Open Government Licence v3.0

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.nsta_uk")

NSTA_BASE = "https://www.nstauthority.co.uk"
NSTA_DATA = "https://data.nstauthority.co.uk"
NSTA_CITATION = (
    "North Sea Transition Authority (2024). UK Petroleum Data. "
    "https://data.nstauthority.co.uk. Open Government Licence v3.0."
)


class WellRecord(BaseModel):
    well_name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    operator: str = ""
    spud_date: str = ""
    total_depth_m: Optional[float] = None
    status: str = ""
    licence: str = ""


class NSTAResult(BaseModel):
    ok: bool
    mode: str
    wells: list[dict[str, Any]] = []
    count: int = 0
    query_params: dict[str, Any] = {}
    source_uri: str = NSTA_DATA
    citation: str = NSTA_CITATION
    fetched_at: str = ""
    note: str = ""


class NSTAQuery(BaseModel):
    minlatitude: Optional[float] = Field(None, ge=-90, le=90)
    maxlatitude: Optional[float] = Field(None, ge=-90, le=90)
    minlongitude: Optional[float] = Field(None, ge=-360, le=360)
    maxlongitude: Optional[float] = Field(None, ge=-360, le=360)
    status: Optional[str] = None
    limit: int = Field(100, ge=1, le=10000)


class NSTAUKFetcher:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or os.environ.get(
            "GEOX_NSTA_CACHE_DIR", "/root/.cache/geox/nsta_uk"
        ))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_NSTA_OFFLINE", "1") != "0"

    def query(self, params: NSTAQuery) -> NSTAResult:
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return self._offline_stub(params.model_dump(exclude_none=True), now)
        return NSTAResult(ok=False, mode="live", note="Live NSTA requires data portal access.", fetched_at=now)

    def _offline_stub(self, qd: dict, now: str) -> NSTAResult:
        samples = [
            {"well_name": "22/14a-1", "latitude": 57.5, "longitude": 1.2, "operator": "NSTA_stub", "status": "SUSPENDED"},
        ]
        return NSTAResult(ok=True, mode="offline_stub", wells=samples, count=len(samples), query_params=qd, fetched_at=now, note="Offline mode (GEOX_NSTA_OFFLINE=1).")
