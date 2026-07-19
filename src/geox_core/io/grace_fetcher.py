"""
grace_fetcher.py — Physical Visible Earth: Time-Variable Gravity.

NASA GRACE/GRACE-FO — monthly gravity field solutions showing
mass change from ice melt, groundwater depletion, sea level rise.

Source: NASA JPL / PO.DAAC
URL: https://podaac.jpl.nasa.gov
Access: PO.DAAC API, Earthdata, AWS Open Data
License: Public Domain (NASA)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.grace")

GRACE_BASE = "https://podaac.jpl.nasa.gov"
GRACE_CITATION = (
    "NASA JPL (2024). GRACE/GRACE-FO Level-3 Monthly Mass Grids. "
    "PO.DAAC. https://podaac.jpl.nasa.gov. Public Domain."
)


class GraceQuery(BaseModel):
    minlatitude: float = Field(-90, ge=-90, le=90)
    maxlatitude: float = Field(90, ge=-90, le=90)
    minlongitude: float = Field(-180, ge=-360, le=360)
    maxlongitude: float = Field(180, ge=-360, le=360)
    start_date: str | None = None
    end_date: str | None = None
    product: str = Field("TELLUS_GRAC_L3_MASCON_CRI_GRID", description="GRACE product ID")


class GraceResult(BaseModel):
    ok: bool
    mode: str
    data: list[dict[str, Any]] = []
    count: int = 0
    source_uri: str = GRACE_BASE
    citation: str = GRACE_CITATION
    fetched_at: str = ""
    note: str = ""


class GRACEFetcher:
    def __init__(self):
        self._offline = os.environ.get("GEOX_GRACE_OFFLINE", "1") != "0"

    def query(self, params: GraceQuery) -> GraceResult:
        now = datetime.now(UTC).isoformat()
        if self._offline:
            return GraceResult(
                ok=True, mode="offline_stub",
                data=[{"latitude": 5.0, "longitude": 110.0, "lwe_thickness_cm": -0.5, "date": "2024-01"}],
                count=1, fetched_at=now,
                note="Offline stub. Requires Earthdata token for PO.DAAC."
            )
        return GraceResult(ok=False, mode="live", note="Live requires PO.DAAC API + Earthdata token.", fetched_at=now)
