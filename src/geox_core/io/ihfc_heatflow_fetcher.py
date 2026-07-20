"""
ihfc_heatflow_fetcher.py — Physical Visible Earth: Global Heat Flow Database.

IHFC (International Heat Flow Commission) Global Heat Flow Database.
~91,000 terrestrial and marine heat-flow measurements from 1,586 publications.

Source: GFZ German Research Centre for Geosciences (hosted for IHFC)
URL: https://heatflow.world
License: Open (GFZ data DOI, citable)
Release: 2024 (latest)

GEOX adapter doctrine:
- All fetches go through schema-translated client.
- Offline mode: returns stub with sample data.
- Provenance always attached.

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

logger = logging.getLogger("geox.io.heatflow")

HEATFLOW_BASE = "https://heatflow.world"
HEATFLOW_CITATION = "Lucazeau, F. (2024). Global Heat Flow Database (IHFC). GFZ Data Services. https://heatflow.world. CC-BY-4.0."


@dataclass
class HeatFlowMeasurement:
    source_uri: str = ""
    fetched_at: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    heat_flow_mw_m2: float = 0.0
    depth_m: float | None = None
    year: int | None = None
    reference: str = ""
    type: str = "terrestrial"  # terrestrial | marine


class HeatFlowResult(BaseModel):
    ok: bool
    mode: str  # "live" | "offline_stub"
    measurements: list[dict[str, Any]] = []
    count: int = 0
    query_params: dict[str, Any] = {}
    source_uri: str = HEATFLOW_BASE
    citation: str = HEATFLOW_CITATION
    fetched_at: str = ""
    note: str = ""


class HeatFlowQuery(BaseModel):
    minlatitude: float | None = Field(None, ge=-90, le=90)
    maxlatitude: float | None = Field(None, ge=-90, le=90)
    minlongitude: float | None = Field(None, ge=-360, le=360)
    maxlongitude: float | None = Field(None, ge=-360, le=360)
    limit: int = Field(100, ge=1, le=10000)


class IHFCHeatFlowFetcher:
    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = Path(cache_dir or os.environ.get("GEOX_HEATFLOW_CACHE_DIR", "/root/.cache/geox/heatflow"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_HEATFLOW_OFFLINE", "1") != "0"

    def query(self, params: HeatFlowQuery) -> HeatFlowResult:
        now = datetime.now(UTC).isoformat()
        if self._offline:
            return self._offline_stub(params.model_dump(exclude_none=True), now)
        return HeatFlowResult(
            ok=False, mode="live", note="Live IHFC API requires dataset download. See heatflow.world.", fetched_at=now
        )

    def _offline_stub(self, qd: dict, now: str) -> HeatFlowResult:
        samples = [
            {"latitude": 4.0, "longitude": 112.0, "heat_flow_mw_m2": 65.0, "type": "marine", "reference": "IHFC 2024"},
            {"latitude": 5.5, "longitude": 115.0, "heat_flow_mw_m2": 78.0, "type": "marine", "reference": "IHFC 2024"},
        ]
        return HeatFlowResult(
            ok=True,
            mode="offline_stub",
            measurements=samples,
            count=len(samples),
            query_params=qd,
            fetched_at=now,
            note="Offline mode (GEOX_HEATFLOW_OFFLINE=1).",
        )
