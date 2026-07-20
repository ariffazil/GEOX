"""
usgs_earthquake_fetcher.py — Physical Visible Earth: Seismic Event Catalog.

USGS FDSN Event Web Service — real-time and historical global earthquake data.
REST API returning GeoJSON/CSV/QuakeML with filtering by time, location,
magnitude, depth, and PAGER alert level.

Source: USGS Earthquake Hazards Program
URL: https://earthquake.usgs.gov/fdsnws/event/1/
License: Public Domain (US Government work)

GEOX adapter doctrine:
- All fetches go through schema-translated client. Raw bytes never returned.
- Offline mode: returns a clearly-marked stub if network is unavailable.
- Provenance always attached (input_hash, source_uri, fetched_at).
- Max 20,000 events per query (USGS server limit).

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.usgs_earthquake")

# ───────────────────────────── CANONICAL URLS ────────────────────────────────────
USGS_FDSN_BASE = "https://earthquake.usgs.gov/fdsnws/event/1"
USGS_QUERY_URL = f"{USGS_FDSN_BASE}/query"
USGS_GEOJSON_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"

USGS_CITATION = (
    "USGS Earthquake Hazards Program (2026). "
    "FDSN Event Web Service — Earthquake Catalog. "
    "U.S. Geological Survey, Department of the Interior. "
    "https://earthquake.usgs.gov/fdsnws/event/1/ "
    "Public Domain."
)

USGS_SOURCES = {
    "fdsn_base": USGS_FDSN_BASE,
    "query_endpoint": USGS_QUERY_URL,
    "geojson_feed": USGS_GEOJSON_FEED,
    "citation": USGS_CITATION,
}


# ───────────────────────────── SCHEMAS ────────────────────────────────────────────
@dataclass(frozen=True)
class EarthquakeEvent:
    """A single earthquake event from the USGS catalog."""

    event_id: str
    time_utc: str
    latitude: float
    longitude: float
    depth_km: float
    magnitude: float
    magnitude_type: str
    place: str
    event_type: str  # "earthquake", "quarry blast", "nuclear explosion", etc.
    status: str  # "automatic", "reviewed", "deleted"
    tsunami_flag: int  # 0 or 1
    felt: int | None = None  # DYFI responses
    cdi: float | None = None  # Community Determined Intensity
    mmi: float | None = None  # Modified Mercalli Intensity
    alert_level: str | None = None  # PAGER: green/yellow/orange/red
    url: str | None = None  # detail page


@dataclass
class EarthquakeCatalogResult:
    """Result envelope for a USGS earthquake catalog query."""

    ok: bool
    mode: str  # "live" | "offline_stub"
    events: list[EarthquakeEvent] = field(default_factory=list)
    count: int = 0
    query_params: dict[str, Any] = field(default_factory=dict)
    source_uri: str = ""
    citation: str = USGS_CITATION
    fetched_at: str = ""
    note: str = ""
    error: str | None = None


# ───────────────────────────── QUERY PARAMETERS ───────────────────────────────────
class EarthquakeQuery(BaseModel):
    """Parameters for a USGS earthquake catalog query."""

    starttime: str | None = Field(None, description="ISO8601 start time (default: NOW - 30 days)")
    endtime: str | None = Field(None, description="ISO8601 end time (default: present)")
    minlatitude: float | None = Field(None, ge=-90, le=90)
    maxlatitude: float | None = Field(None, ge=-90, le=90)
    minlongitude: float | None = Field(None, ge=-360, le=360)
    maxlongitude: float | None = Field(None, ge=-360, le=360)
    latitude: float | None = Field(None, ge=-90, le=90, description="Circle center lat")
    longitude: float | None = Field(None, ge=-180, le=180, description="Circle center lon")
    maxradiuskm: float | None = Field(None, ge=0, le=20002, description="Circle radius km")
    minmagnitude: float | None = Field(None, description="Minimum magnitude")
    maxmagnitude: float | None = Field(None, description="Maximum magnitude")
    mindepth: float | None = Field(None, ge=-100, le=1000, description="Min depth km")
    maxdepth: float | None = Field(None, ge=-100, le=1000, description="Max depth km")
    limit: int = Field(200, ge=1, le=20000, description="Max events to return")
    orderby: str = Field("time", description="time | time-asc | magnitude | magnitude-asc")
    alertlevel: str | None = Field(None, description="PAGER: green/yellow/orange/red")
    eventtype: str | None = Field(None, description="earthquake, quarry blast, etc.")
    format: str = Field("geojson", description="geojson | csv | quakeml")


# ───────────────────────────── FETCHER ────────────────────────────────────────────
class USGSEarthquakeFetcher:
    """Constitutional fetcher for USGS Earthquake Catalog.

    Modes:
    - GEOX_USGS_EQ_OFFLINE=1 (default): returns a stub with sample data.
    - GEOX_USGS_EQ_OFFLINE=0: live HTTP GET to USGS FDSN API.
    """

    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = Path(cache_dir or os.environ.get("GEOX_USGS_EQ_CACHE_DIR", "/root/.cache/geox/usgs_earthquake"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_USGS_EQ_OFFLINE", "1") != "0"

    def query(self, params: EarthquakeQuery) -> EarthquakeCatalogResult:
        """Execute an earthquake catalog query.

        Returns schema-translated events with full provenance.
        """
        now = datetime.now(UTC).isoformat()
        query_dict = params.model_dump(exclude_none=True)

        if self._offline:
            return self._offline_stub(query_dict, now)

        try:
            return self._live_query(params, query_dict, now)
        except Exception as e:
            logger.warning(f"USGS live query failed: {e}, falling back to stub")
            result = self._offline_stub(query_dict, now)
            result.note = f"Live query failed ({e}), returning stub data."
            return result

    def _live_query(self, params: EarthquakeQuery, query_dict: dict, now: str) -> EarthquakeCatalogResult:
        """Execute a live HTTP query to USGS FDSN API."""

        # Build query string
        qp = {k: v for k, v in query_dict.items() if v is not None}
        qp["format"] = "geojson"
        query_string = urllib.parse.urlencode(qp)
        url = f"{USGS_QUERY_URL}?{query_string}"

        logger.info(f"USGS live query: {url}")
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()

        data = json.loads(raw)
        events = self._parse_geojson(data)

        return EarthquakeCatalogResult(
            ok=True,
            mode="live",
            events=events,
            count=len(events),
            query_params=query_dict,
            source_uri=url,
            citation=USGS_CITATION,
            fetched_at=now,
        )

    def _parse_geojson(self, data: dict) -> list[EarthquakeEvent]:
        """Parse USGS GeoJSON response into EarthquakeEvent list."""
        events = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [None, None, None])

            events.append(
                EarthquakeEvent(
                    event_id=feature.get("id", ""),
                    time_utc=datetime.fromtimestamp(props.get("time", 0) / 1000, tz=UTC).isoformat(),
                    latitude=coords[1] if len(coords) > 1 else 0.0,
                    longitude=coords[0] if len(coords) > 0 else 0.0,
                    depth_km=coords[2] if len(coords) > 2 else 0.0,
                    magnitude=props.get("mag", 0.0) or 0.0,
                    magnitude_type=props.get("magType", ""),
                    place=props.get("place", ""),
                    event_type=props.get("type", "earthquake"),
                    status=props.get("status", "automatic"),
                    tsunami_flag=props.get("tsunami", 0),
                    felt=props.get("felt"),
                    cdi=props.get("cdi"),
                    mmi=props.get("mmi"),
                    alert_level=props.get("alert"),
                    url=props.get("url"),
                )
            )
        return events

    def _offline_stub(self, query_dict: dict, now: str) -> EarthquakeCatalogResult:
        """Return a clearly-marked offline stub with sample events."""
        sample_events = [
            EarthquakeEvent(
                event_id="offline_sample_001",
                time_utc="2026-06-25T00:00:00Z",
                latitude=35.6762,
                longitude=139.6503,
                depth_km=10.0,
                magnitude=5.2,
                magnitude_type="mw",
                place="12km NE of Tokyo, Japan",
                event_type="earthquake",
                status="reviewed",
                tsunami_flag=0,
                felt=1200,
                cdi=5.0,
                mmi=4.8,
                alert_level="green",
            ),
            EarthquakeEvent(
                event_id="offline_sample_002",
                time_utc="2026-06-24T18:30:00Z",
                latitude=-5.2,
                longitude=102.1,
                depth_km=35.0,
                magnitude=6.1,
                magnitude_type="mw",
                place="120km SW of Bengkulu, Indonesia",
                event_type="earthquake",
                status="automatic",
                tsunami_flag=1,
                felt=5000,
                cdi=7.0,
                mmi=6.5,
                alert_level="yellow",
            ),
        ]

        return EarthquakeCatalogResult(
            ok=True,
            mode="offline_stub",
            events=sample_events,
            count=len(sample_events),
            query_params=query_dict,
            source_uri=USGS_QUERY_URL,
            citation=USGS_CITATION,
            fetched_at=now,
            note=(
                "Offline mode (GEOX_USGS_EQ_OFFLINE=1). Set to 0 for live USGS API. "
                "Sample events are synthetic placeholders, not real seismic data."
            ),
        )


__all__ = [
    "USGSEarthquakeFetcher",
    "EarthquakeQuery",
    "EarthquakeEvent",
    "EarthquakeCatalogResult",
    "USGS_SOURCES",
    "USGS_CITATION",
]
