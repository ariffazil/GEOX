"""
etopo_fetcher.py — Physical Visible Earth: Global Relief Model.

ETOPO 2022 — NOAA NCEI global terrain model integrating topography,
bathymetry, and shoreline data. 15/30/60 arc-second resolution.

Source: NOAA National Centers for Environmental Information (NCEI)
URL: https://www.ncei.noaa.gov/products/etopo-global-relief-model
License: Public Domain (US Government work)

Access patterns:
- Grid Extract API: bbox subset download (server-side cropping)
- Direct GeoTiff/NetCDF download for full resolution
- OPeNDAP via NCEI THREDDS for subsetting without full download

GEOX adapter doctrine:
- All fetches go through schema-translated client. Raw bytes never returned.
- Offline mode: returns a clearly-marked stub if network is unavailable.
- Provenance always attached (input_hash, source_uri, fetched_at).

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.etopo")

# ───────────────────────────── CANONICAL URLS ────────────────────────────────────
ETOPO_BASE = "https://www.ncei.noaa.gov/products/etopo-global-relief-model"
ETOPO_GRID_EXTRACT = "https://www.ncei.noaa.gov/maps/grid-extract/"

# ETOPO 2022 direct GeoTiff URLs (15 arc-second)
ETOPO_2022_SOURCES = {
    "bedrock_15s_tiff": "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/15s_bed_elev_gtif/",
    "surface_15s_tiff": "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/15s_surface_elev_gtif/",
    "geoid_15s_tiff": "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/15s_geoid_gtif/",
    "bedrock_30s_tiff": "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/30s/30s_bed_elev_gtif/ETOPO_2022_v1_30s_N90W180_bed.tif",
    "surface_30s_tiff": "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/30s/30s_surface_elev_gtif/ETOPO_2022_v1_30s_N90W180_surface.tif",
    "bedrock_60s_tiff": "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/60s_bed_elev_gtif/ETOPO_2022_v1_60s_N90W180_bed.tif",
    "surface_60s_tiff": "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/60s_surface_elev_gtif/ETOPO_2022_v1_60s_N90W180_surface.tif",
    "grid_extract_api": ETOPO_GRID_EXTRACT,
}

# OPeNDAP THREDDS endpoints for server-side subsetting
ETOPO_THREDDS = {
    "bedrock_15s_netcdf": "https://www.ngdc.noaa.gov/thredds/catalog/global/ETOPO2022/15s/15s_bed_elev_netcdf/catalog.html",
    "surface_15s_netcdf": "https://www.ngdc.noaa.gov/thredds/catalog/global/ETOPO2022/15s/15s_surface_elev_netcdf/catalog.html",
}

ETOPO_CITATION = (
    "NOAA National Centers for Environmental Information. 2022: "
    "ETOPO 2022 15 Arc-Second Global Relief Model. "
    "NOAA National Centers for Environmental Information. "
    "DOI: 10.25921/fd45-gt74. Public Domain."
)


# ───────────────────────────── SCHEMAS ────────────────────────────────────────────
@dataclass(frozen=True)
class ETOPOGridMeta:
    """Metadata about an ETOPO grid subset."""

    source_uri: str
    fetched_at: str
    sha256: str | None
    resolution_arcsec: int  # 15, 30, or 60
    version: str  # "bedrock" | "ice_surface"
    crs: str  # "EPSG:4326"
    bbox: tuple[float, float, float, float]  # min_lon, min_lat, max_lon, max_lat
    elevation_min_m: float | None = None
    elevation_max_m: float | None = None
    rows: int | None = None
    cols: int | None = None


class ETOPOFetchResult(BaseModel):
    """Result envelope for an ETOPO fetch."""

    ok: bool
    mode: str  # "live" | "offline_stub" | "cached"
    grid_path: str | None = None
    meta: ETOPOGridMeta | None = None
    citation: str = ETOPO_CITATION
    note: str = ""
    error: str | None = None


class ETOPOExtractRequest(BaseModel):
    """Request for an ETOPO grid extract (bbox subset)."""

    west: float = Field(..., ge=-180, le=180, description="Western longitude")
    east: float = Field(..., ge=-180, le=180, description="Eastern longitude")
    south: float = Field(..., ge=-90, le=90, description="Southern latitude")
    north: float = Field(..., ge=-90, le=90, description="Northern latitude")
    resolution: int = Field(15, description="Arc-seconds: 15, 30, or 60")
    version: str = Field("bedrock", description="bedrock | ice_surface")
    output_format: str = Field("netcdf", description="netcdf | geotiff")


# ───────────────────────────── FETCHER ────────────────────────────────────────────
class ETOPOFetcher:
    """Constitutional fetcher for ETOPO 2022 Global Relief Model.

    Modes:
    - GEOX_ETOPO_OFFLINE=1 (default): returns a clearly-marked stub.
    - GEOX_ETOPO_OFFLINE=0: attempts local cache or Grid Extract API.

    The fetcher handles:
    - Full-resolution cached files (pre-downloaded)
    - Grid Extract API for bbox subsets (server-side crop)
    - Graceful degradation to offline stub
    """

    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = Path(cache_dir or os.environ.get(
            "GEOX_ETOPO_CACHE_DIR", "/root/.cache/geox/etopo"
        ))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_ETOPO_OFFLINE", "1") != "0"

    def fetch_global(
        self,
        resolution: int = 15,
        version: str = "bedrock",
        output_format: str = "geotiff",
    ) -> ETOPOFetchResult:
        """Fetch the full global ETOPO grid.

        Args:
            resolution: 15, 30, or 60 arc-seconds
            version: "bedrock" or "ice_surface"
            output_format: "geotiff" or "netcdf"
        """
        now = datetime.now(UTC).isoformat()

        if self._offline:
            return self._offline_stub(
                resolution=resolution,
                version=version,
                bbox=(-180.0, -90.0, 180.0, 90.0),
                now=now,
            )

        # Check local cache
        cached = self._check_cache(resolution, version, output_format)
        if cached:
            return cached

        return ETOPOFetchResult(
            ok=False,
            mode="live",
            note=(
                "Live fetch requested but no cached file found. Operator must "
                "run one-time download (ETOPO grid extract or direct download) "
                "and place in cache dir. This prevents accidental large pulls."
            ),
            citation=ETOPO_CITATION,
        )

    def fetch_bbox(self, request: ETOPOExtractRequest) -> ETOPOFetchResult:
        """Fetch an ETOPO subset for a bounding box.

        In offline mode, returns a stub. In live mode, checks cache for
        matching bbox files.
        """
        now = datetime.now(UTC).isoformat()

        if self._offline:
            return self._offline_stub(
                resolution=request.resolution,
                version=request.version,
                bbox=(request.west, request.south, request.east, request.north),
                now=now,
            )

        # Check for cached bbox subset
        cache_key = self._bbox_cache_key(request)
        cached_path = self.cache_dir / cache_key
        if cached_path.exists():
            return ETOPOFetchResult(
                ok=True,
                mode="cached",
                grid_path=str(cached_path),
                meta=ETOPOGridMeta(
                    source_uri=ETOPO_GRID_EXTRACT,
                    fetched_at=datetime.fromtimestamp(
                        cached_path.stat().st_mtime
                    ).isoformat(),
                    sha256=self._sha256(cached_path),
                    resolution_arcsec=request.resolution,
                    version=request.version,
                    crs="EPSG:4326",
                    bbox=(request.west, request.south, request.east, request.north),
                ),
                citation=ETOPO_CITATION,
            )

        return ETOPOFetchResult(
            ok=False,
            mode="live",
            note=(
                f"No cached ETOPO subset for bbox ({request.west},{request.south},"
                f"{request.east},{request.north}). Use Grid Extract API: {ETOPO_GRID_EXTRACT}"
            ),
            citation=ETOPO_CITATION,
        )

    def _check_cache(
        self, resolution: int, version: str, output_format: str
    ) -> ETOPOFetchResult | None:
        """Check local cache for a matching ETOPO file."""
        pattern = f"etopo2022_{resolution}s_{version}*"
        matches = list(self.cache_dir.glob(pattern))
        if matches:
            path = matches[0]
            return ETOPOFetchResult(
                ok=True,
                mode="cached",
                grid_path=str(path),
                meta=ETOPOGridMeta(
                    source_uri=ETOPO_BASE,
                    fetched_at=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                    sha256=self._sha256(path),
                    resolution_arcsec=resolution,
                    version=version,
                    crs="EPSG:4326",
                    bbox=(-180.0, -90.0, 180.0, 90.0),
                ),
                citation=ETOPO_CITATION,
            )
        return None

    def _bbox_cache_key(self, request: ETOPOExtractRequest) -> str:
        """Generate a cache filename for a bbox subset."""
        return (
            f"etopo2022_{request.resolution}s_{request.version}_"
            f"{request.west:.1f}_{request.south:.1f}_{request.east:.1f}_{request.north:.1f}"
            f".{request.output_format}"
        )

    def _offline_stub(
        self,
        resolution: int,
        version: str,
        bbox: tuple[float, float, float, float],
        now: str,
    ) -> ETOPOFetchResult:
        """Return a clearly-marked offline stub."""
        return ETOPOFetchResult(
            ok=True,
            mode="offline_stub",
            grid_path=None,
            meta=ETOPOGridMeta(
                source_uri=ETOPO_BASE,
                fetched_at=now,
                sha256=None,
                resolution_arcsec=resolution,
                version=version,
                crs="EPSG:4326",
                bbox=bbox,
            ),
            citation=ETOPO_CITATION,
            note=(
                "Offline mode (GEOX_ETOPO_OFFLINE=1). Set to 0 for live data. "
                "Place downloaded ETOPO files in cache dir for local access."
            ),
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()


__all__ = [
    "ETOPOFetcher",
    "ETOPOFetchResult",
    "ETOPOGridMeta",
    "ETOPOExtractRequest",
    "ETOPO_2022_SOURCES",
    "ETOPO_CITATION",
]
