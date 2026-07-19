"""
onegeology_fetcher.py — Physical Visible Earth: National Geological Maps.

OneGeology — global aggregator of national geological surveys via OGC WMS.
Maps from BGS (UK), GNS (NZ), GA (Australia), SGU (Sweden), etc.

Source: OneGeology Project
URL: https://www.onegeology.org
Access: OGC WMS services
License: Varies by survey (mostly open)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.onegeology")

ONEGEOLOGY_BASE = "https://www.onegeology.org"
ONEGEOLOGY_WMS_CATALOG = "https://portal.onegeology.org/OnegeologyGlobal/MapServer/WMSServer"
ONEGEOLOGY_CITATION = (
    "OneGeology (2024). Global Geological Maps Portal. "
    "https://www.onegeology.org. Various national survey licenses."
)


class GeologyMapQuery(BaseModel):
    minlatitude: float = Field(..., ge=-90, le=90)
    maxlatitude: float = Field(..., ge=-90, le=90)
    minlongitude: float = Field(..., ge=-360, le=360)
    maxlongitude: float = Field(..., ge=-360, le=360)
    layers: str | None = Field(None, description="WMS layer name")
    output_format: str = Field("application/json", description="WMS GetFeatureInfo format")


class GeologyMapResult(BaseModel):
    ok: bool
    mode: str
    features: list[dict[str, Any]] = []
    count: int = 0
    wms_url: str = ""
    source_uri: str = ONEGEOLOGY_BASE
    citation: str = ONEGEOLOGY_CITATION
    fetched_at: str = ""
    note: str = ""


class OneGeologyFetcher:
    def __init__(self):
        self._offline = os.environ.get("GEOX_ONEGEOLOGY_OFFLINE", "1") != "0"

    def query(self, params: GeologyMapQuery) -> GeologyMapResult:
        now = datetime.now(UTC).isoformat()
        if self._offline:
            return GeologyMapResult(
                ok=True, mode="offline_stub",
                features=[{"properties": {"LITHOLOGY": "Sandstone", "AGE": "Miocene"}}],
                count=1, wms_url=ONEGEOLOGY_WMS_CATALOG, fetched_at=now,
                note="Offline stub. Live requires WMS GetMap/GetFeatureInfo."
            )
        return GeologyMapResult(ok=False, mode="live", note="Live requires WMS client.", fetched_at=now)
