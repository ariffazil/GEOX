"""
earthchem_fetcher.py — Physical Visible Earth: Geochemistry Database.

EarthChem/PetDB — open igneous geochemical and geochronological analyses.
REST API v4 with geospatial queries.

Source: Columbia University / LDEO
URL: https://www.earthchem.org
API: https://petdb.org/earthchemapi/v4
License: Open (CC-BY)

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

logger = logging.getLogger("geox.io.earthchem")

EARTHCHEM_API = "https://petdb.org/earthchemapi/v4"
EARTHCHEM_CITATION = (
    "EarthChem (2024). EarthChem Portal / PetDB. "
    "Columbia University / LDEO. https://www.earthchem.org. CC-BY."
)


class GeochemSample(BaseModel):
    sample_id: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    rock_type: str = ""
    age_ma: Optional[float] = None
    sio2: Optional[float] = None
    mgo: Optional[float] = None
    al2o3: Optional[float] = None
    reference: str = ""


class GeochemResult(BaseModel):
    ok: bool
    mode: str
    samples: list[dict[str, Any]] = []
    count: int = 0
    query_params: dict[str, Any] = {}
    source_uri: str = EARTHCHEM_API
    citation: str = EARTHCHEM_CITATION
    fetched_at: str = ""
    note: str = ""


class GeochemQuery(BaseModel):
    minlatitude: Optional[float] = Field(None, ge=-90, le=90)
    maxlatitude: Optional[float] = Field(None, ge=-90, le=90)
    minlongitude: Optional[float] = Field(None, ge=-360, le=360)
    maxlongitude: Optional[float] = Field(None, ge=-360, le=360)
    rock_type: Optional[str] = None
    min_sio2: Optional[float] = None
    max_sio2: Optional[float] = None
    limit: int = Field(100, ge=1, le=10000)


class EarthChemFetcher:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or os.environ.get(
            "GEOX_EARTHCHEM_CACHE_DIR", "/root/.cache/geox/earthchem"
        ))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_EARTHCHEM_OFFLINE", "1") != "0"

    def query(self, params: GeochemQuery) -> GeochemResult:
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return self._offline_stub(params.model_dump(exclude_none=True), now)
        return GeochemResult(ok=False, mode="live", note="Live EarthChem API requires httpx client. See EARTHCHEM_API.", fetched_at=now)

    def _offline_stub(self, qd: dict, now: str) -> GeochemResult:
        samples = [
            {"sample_id": "EC_stub_001", "latitude": 4.5, "longitude": 112.0, "rock_type": "basalt", "sio2": 49.5, "mgo": 7.2},
            {"sample_id": "EC_stub_002", "latitude": 2.0, "longitude": 109.0, "rock_type": "granite", "sio2": 72.1, "mgo": 0.8},
        ]
        return GeochemResult(ok=True, mode="offline_stub", samples=samples, count=len(samples), query_params=qd, fetched_at=now, note="Offline mode (GEOX_EARTHCHEM_OFFLINE=1).")
