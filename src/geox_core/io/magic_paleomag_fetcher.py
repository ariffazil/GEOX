"""
magic_paleomag_fetcher.py — Physical Visible Earth: Paleomagnetism Database.

MagIC (Magnetics Information Consortium) — rock paleomagnetic measurements
and derived virtual geomagnetic poles.

Source: EarthRef / UCSD
URL: https://www.earthref.org/MagIC
Access: REST API + PmagPy Python library
License: CC-BY-4.0

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.magic")

MAGIC_BASE = "https://www.earthref.org/MagIC"
MAGIC_API = "https://api.earthref.org/v1/MagIC"
MAGIC_CITATION = (
    "Tauxe, L. et al. (2024). MagIC Database. "
    "Magnetics Information Consortium / EarthRef. "
    "https://www.earthref.org/MagIC. CC-BY-4.0."
)


class PaleomagQuery(BaseModel):
    minlatitude: float | None = Field(None, ge=-90, le=90)
    maxlatitude: float | None = Field(None, ge=-90, le=90)
    minlongitude: float | None = Field(None, ge=-360, le=360)
    maxlongitude: float | None = Field(None, ge=-360, le=360)
    min_age_ma: float | None = None
    max_age_ma: float | None = None
    limit: int = Field(100, ge=1, le=10000)


class PaleomagResult(BaseModel):
    ok: bool
    mode: str
    records: list[dict[str, Any]] = []
    count: int = 0
    query_params: dict[str, Any] = {}
    source_uri: str = MAGIC_API
    citation: str = MAGIC_CITATION
    fetched_at: str = ""
    note: str = ""


class MagICFetcher:
    def __init__(self):
        self._offline = os.environ.get("GEOX_MAGIC_OFFLINE", "1") != "0"

    def query(self, params: PaleomagQuery) -> PaleomagResult:
        now = datetime.now(UTC).isoformat()
        if self._offline:
            return PaleomagResult(
                ok=True,
                mode="offline_stub",
                records=[
                    {
                        "latitude": 4.0,
                        "longitude": 112.0,
                        "age_ma": 15.0,
                        "declination": 355.0,
                        "inclination": 5.0,
                        "polarity": "normal",
                    }
                ],
                count=1,
                query_params=params.model_dump(exclude_none=True),
                fetched_at=now,
                note="Offline stub. Set GEOX_MAGIC_OFFLINE=0 for live MagIC API.",
            )
        return PaleomagResult(ok=False, mode="live", note="Live MagIC API requires httpx.", fetched_at=now)
