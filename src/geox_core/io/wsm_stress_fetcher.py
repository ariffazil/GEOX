"""
wsm_stress_fetcher.py — Physical Visible Earth: World Stress Map.

WSM 2025 (GFZ) — ~100,000 crustal stress orientation measurements.
Breakouts, focal mechanisms, overcoring, hydraulic fracturing.

Source: GFZ German Research Centre for Geosciences
URL: https://www.world-stress-map.org
License: CC-BY-4.0
CASMO API: https://www.world-stress-map.org/casmo

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.wsm")

WSM_BASE = "https://www.world-stress-map.org"
WSM_CASMO = f"{WSM_BASE}/casmo"
WSM_CITATION = (
    "Heidbach, O. et al. (2025). World Stress Map 2025. "
    "GFZ German Research Centre for Geosciences. "
    "https://www.world-stress-map.org. CC-BY-4.0."
)


@dataclass
class StressRecord:
    source_uri: str = ""
    fetched_at: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    azimuth_deg: float = 0.0  # SHmax orientation
    quality: str = "C"  # A-E
    type: str = "BO"  # BO=borehole breakout, FM=focal mechanism, etc.
    depth_km: float | None = None
    regime: str = ""  # NF, SS, TF


class StressResult(BaseModel):
    ok: bool
    mode: str
    records: list[dict[str, Any]] = []
    count: int = 0
    query_params: dict[str, Any] = {}
    source_uri: str = WSM_BASE
    citation: str = WSM_CITATION
    fetched_at: str = ""
    note: str = ""


class StressQuery(BaseModel):
    minlatitude: float | None = Field(None, ge=-90, le=90)
    maxlatitude: float | None = Field(None, ge=-90, le=90)
    minlongitude: float | None = Field(None, ge=-360, le=360)
    maxlongitude: float | None = Field(None, ge=-360, le=360)
    quality: str | None = Field(None, description="A-E quality filter")
    limit: int = Field(100, ge=1, le=50000)


class WSMStressFetcher:
    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = Path(cache_dir or os.environ.get(
            "GEOX_WSM_CACHE_DIR", "/root/.cache/geox/wsm"
        ))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_WSM_OFFLINE", "1") != "0"

    def query(self, params: StressQuery) -> StressResult:
        now = datetime.now(UTC).isoformat()
        if self._offline:
            return self._offline_stub(params.model_dump(exclude_none=True), now)
        return StressResult(ok=False, mode="live", note="Live WSM requires CASMO API access or CSV download.", fetched_at=now)

    def _offline_stub(self, qd: dict, now: str) -> StressResult:
        samples = [
            {"latitude": 2.0, "longitude": 110.0, "azimuth_deg": 35.0, "quality": "B", "type": "BO", "regime": "SS"},
            {"latitude": 6.0, "longitude": 116.0, "azimuth_deg": 15.0, "quality": "C", "type": "FM", "regime": "TF"},
        ]
        return StressResult(ok=True, mode="offline_stub", records=samples, count=len(samples), query_params=qd, fetched_at=now, note="Offline mode (GEOX_WSM_OFFLINE=1).")
