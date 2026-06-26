"""
gebco_fetcher.py — Physical Visible Earth: Global Bathymetry Grid.

GEBCO_2026 Grid — IHO/UNESCO global terrain model for ocean and land.
15 arc-second interval grid, elevation in meters, with Type Identifier Grid.

Source: General Bathymetric Chart of the Oceans (GEBCO)
URL: https://www.gebco.net/data-products/gridded-bathymetry-data
Data: https://data.ceda.ac.uk/bodc/gebco/global/gebco_2026/
OPeNDAP: via CEDA (NERC Centre for Environmental Data Analysis)
License: Public Domain (IHO/UNESCO)

Access patterns:
- Direct NetCDF download (~4 GB global)
- OPeNDAP via CEDA for server-side subsetting (bbox extraction without full download)
- User-defined area download: https://download.gebco.net/
- WMS: https://www.gebco.net/data-products/gebco-web-services/web-map-service

GEOX adapter doctrine:
- All fetches go through schema-translated client. Raw bytes never returned.
- Offline mode: returns a clearly-marked stub if network is unavailable.
- Provenance always attached (input_hash, source_uri, fetched_at).
- OPeNDAP subsetting is the preferred live path (avoids 4GB download).

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.gebco")

# ───────────────────────────── CANONICAL URLS ────────────────────────────────────
GEBCO_BASE = "https://www.gebco.net/data-products/gridded-bathymetry-data"
GEBCO_DOWNLOAD_APP = "https://download.gebco.net/"

# CEDA OPeNDAP endpoints (server-side subsetting)
GEBCO_OPENDAP = {
    "ice_surface_netcdf": "https://data.ceda.ac.uk/bodc/gebco/global/gebco_2026/ice_surface_elevation/netcdf",
    "sub_ice_netcdf": "https://data.ceda.ac.uk/bodc/gebco/global/gebco_2026/sub_ice_topography_bathymetry/netcdf",
    "tid_netcdf": "https://data.ceda.ac.uk/bodc/gebco/global/gebco_2026/type_identifier_grid/netcdf",
}

# Direct download URLs
GEBCO_2026_SOURCES = {
    "ice_surface_netcdf": "https://dap.ceda.ac.uk/bodc/gebco/global/gebco_2026/ice_surface_elevation/netcdf/GEBCO_2026.zip?download=1",
    "ice_surface_geotiff": "https://dap.ceda.ac.uk/bodc/gebco/global/gebco_2026/ice_surface_elevation/geotiff/gebco_2026_geotiff.zip?download=1",
    "sub_ice_netcdf": "https://dap.ceda.ac.uk/bodc/gebco/global/gebco_2026/sub_ice_topography_bathymetry/netcdf/GEBCO_2026_sub_ice.zip?download=1",
    "sub_ice_geotiff": "https://dap.ceda.ac.uk/bodc/gebco/global/gebco_2026/sub_ice_topography_bathymetry/geotiff/gebco_2026_sub_ice_topo_geotiff.zip?download=1",
    "tid_netcdf": "https://dap.ceda.ac.uk/bodc/gebco/global/gebco_2026/type_identifier_grid/netcdf/gebco_2026_tid.zip?download=1",
    "opendap_endpoint": GEBCO_OPENDAP["ice_surface_netcdf"],
    "download_app": GEBCO_DOWNLOAD_APP,
    "wms": "https://www.gebco.net/data-products/gebco-web-services/web-map-service",
}

GEBCO_CITATION = (
    "GEBCO Bathymetric Compilation Group 2026 (2026). "
    "The GEBCO_2026 Grid - a continuous terrain model for oceans and land "
    "at 15 arc-second intervals. doi:10.5285/4f68d5c7-45eb-f999-e063-7086abc036fa. "
    "Public Domain."
)


# ───────────────────────────── SCHEMAS ────────────────────────────────────────────
@dataclass(frozen=True)
class GEBCOGridMeta:
    """Metadata about a GEBCO grid subset."""

    source_uri: str
    fetched_at: str
    sha256: Optional[str]
    resolution_arcsec: int = 15
    grid_version: str = "GEBCO_2026"
    variant: str = "ice_surface"  # "ice_surface" | "sub_ice" | "tid"
    crs: str = "EPSG:4326"
    bbox: tuple[float, float, float, float] = (-180.0, -90.0, 180.0, 90.0)
    depth_min_m: Optional[float] = None
    depth_max_m: Optional[float] = None
    rows: Optional[int] = None
    cols: Optional[int] = None


class GEBCOFetchResult(BaseModel):
    """Result envelope for a GEBCO fetch."""

    ok: bool
    mode: str  # "live" | "offline_stub" | "cached" | "opendap"
    grid_path: Optional[str] = None
    opendap_url: Optional[str] = None
    meta: Optional[GEBCOGridMeta] = None
    citation: str = GEBCO_CITATION
    note: str = ""
    error: Optional[str] = None


class GEBCOExtractRequest(BaseModel):
    """Request for a GEBCO grid subset."""

    west: float = Field(..., ge=-180, le=180, description="Western longitude")
    east: float = Field(..., ge=-180, le=180, description="Eastern longitude")
    south: float = Field(..., ge=-90, le=90, description="Southern latitude")
    north: float = Field(..., ge=-90, le=90, description="Northern latitude")
    variant: str = Field("ice_surface", description="ice_surface | sub_ice | tid")
    output_format: str = Field("netcdf", description="netcdf | geotiff")


# ───────────────────────────── FETCHER ────────────────────────────────────────────
class GEBCOFetcher:
    """Constitutional fetcher for GEBCO_2026 Bathymetry Grid.

    Modes:
    - GEOX_GEBCO_OFFLINE=1 (default): returns a clearly-marked stub.
    - GEOX_GEBCO_OFFLINE=0: attempts local cache or OPeNDAP subsetting.

    The fetcher handles:
    - OPeNDAP subsetting (preferred — server-side bbox crop, no 4GB download)
    - Full-resolution cached files (pre-downloaded global grid)
    - Graceful degradation to offline stub
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or os.environ.get(
            "GEOX_GEBCO_CACHE_DIR", "/root/.cache/geox/gebco"
        ))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_GEBCO_OFFLINE", "1") != "0"

    def fetch_global(
        self,
        variant: str = "ice_surface",
        output_format: str = "netcdf",
    ) -> GEBCOFetchResult:
        """Fetch the full global GEBCO grid.

        Args:
            variant: "ice_surface", "sub_ice", or "tid"
            output_format: "netcdf" or "geotiff"
        """
        now = datetime.now(timezone.utc).isoformat()

        if self._offline:
            return self._offline_stub(variant=variant, bbox=(-180.0, -90.0, 180.0, 90.0), now=now)

        # Check local cache
        cached = self._check_cache(variant, output_format)
        if cached:
            return cached

        return GEBCOFetchResult(
            ok=False,
            mode="live",
            note=(
                "Live fetch requested but no cached file found. Operator must "
                "run one-time download from CEDA or use the download app. "
                "For bbox subsets, use OPeNDAP (set GEOX_GEBCO_OFFLINE=0)."
            ),
            citation=GEBCO_CITATION,
        )

    def fetch_bbox(self, request: GEBCOExtractRequest) -> GEBCOFetchResult:
        """Fetch a GEBCO subset for a bounding box.

        Prefers OPeNDAP for server-side subsetting. Falls back to local cache.
        """
        now = datetime.now(timezone.utc).isoformat()

        if self._offline:
            return self._offline_stub(
                variant=request.variant,
                bbox=(request.west, request.south, request.east, request.north),
                now=now,
            )

        # Try OPeNDAP subsetting
        opendap_url = self._build_opendap_url(request)
        if opendap_url:
            return GEBCOFetchResult(
                ok=True,
                mode="opendap",
                opendap_url=opendap_url,
                meta=GEBCOGridMeta(
                    source_uri=opendap_url,
                    fetched_at=now,
                    sha256=None,
                    resolution_arcsec=15,
                    grid_version="GEBCO_2026",
                    variant=request.variant,
                    crs="EPSG:4326",
                    bbox=(request.west, request.south, request.east, request.north),
                ),
                citation=GEBCO_CITATION,
                note=(
                    "OPeNDAP URL generated for server-side subsetting. "
                    "Use with xarray/opendap client to fetch the actual data."
                ),
            )

        # Check cache
        cache_key = self._bbox_cache_key(request)
        cached_path = self.cache_dir / cache_key
        if cached_path.exists():
            return GEBCOFetchResult(
                ok=True,
                mode="cached",
                grid_path=str(cached_path),
                meta=GEBCOGridMeta(
                    source_uri=GEBCO_BASE,
                    fetched_at=datetime.fromtimestamp(cached_path.stat().st_mtime).isoformat(),
                    sha256=self._sha256(cached_path),
                    resolution_arcsec=15,
                    grid_version="GEBCO_2026",
                    variant=request.variant,
                    crs="EPSG:4326",
                    bbox=(request.west, request.south, request.east, request.north),
                ),
                citation=GEBCO_CITATION,
            )

        return GEBCOFetchResult(
            ok=False,
            mode="live",
            note=(
                f"No cached GEBCO subset for bbox ({request.west},{request.south},"
                f"{request.east},{request.north}). Use download app: {GEBCO_DOWNLOAD_APP}"
            ),
            citation=GEBCO_CITATION,
        )

    def _build_opendap_url(self, request: GEBCOExtractRequest) -> Optional[str]:
        """Build an OPeNDAP URL for server-side bbox subsetting.

        Format: {base}/GEBCO_2026.nc?elevation[{lat_start}:{lat_end}][{lon_start}:{lon_end}]
        This requires knowing the grid indices, which we approximate from degrees.
        """
        base = GEBCO_OPENDAP.get(f"{request.variant}_netcdf")
        if not base:
            return None

        # GEBCO_2026 is 15 arc-second = 240 samples/degree
        # Grid: 86400 x 43200 (lon x lat), starting at -180, -90
        samples_per_deg = 240
        lon_start = int((request.west + 180) * samples_per_deg)
        lon_end = int((request.east + 180) * samples_per_deg)
        lat_start = int((request.south + 90) * samples_per_deg)
        lat_end = int((request.north + 90) * samples_per_deg)

        # OPeNDAP constraint expression
        return (
            f"{base}/GEBCO_2026.nc"
            f"?elevation[{lat_start}:1:{lat_end}][{lon_start}:1:{lon_end}]"
        )

    def _check_cache(self, variant: str, output_format: str) -> Optional[GEBCOFetchResult]:
        """Check local cache for a matching GEBCO file."""
        pattern = f"gebco_2026_{variant}*"
        matches = list(self.cache_dir.glob(pattern))
        if matches:
            path = matches[0]
            return GEBCOFetchResult(
                ok=True,
                mode="cached",
                grid_path=str(path),
                meta=GEBCOGridMeta(
                    source_uri=GEBCO_BASE,
                    fetched_at=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                    sha256=self._sha256(path),
                    resolution_arcsec=15,
                    grid_version="GEBCO_2026",
                    variant=variant,
                    crs="EPSG:4326",
                    bbox=(-180.0, -90.0, 180.0, 90.0),
                ),
                citation=GEBCO_CITATION,
            )
        return None

    def _bbox_cache_key(self, request: GEBCOExtractRequest) -> str:
        """Generate a cache filename for a bbox subset."""
        return (
            f"gebco_2026_{request.variant}_"
            f"{request.west:.1f}_{request.south:.1f}_{request.east:.1f}_{request.north:.1f}"
            f".{request.output_format}"
        )

    def _offline_stub(
        self,
        variant: str,
        bbox: tuple[float, float, float, float],
        now: str,
    ) -> GEBCOFetchResult:
        """Return a clearly-marked offline stub."""
        return GEBCOFetchResult(
            ok=True,
            mode="offline_stub",
            grid_path=None,
            meta=GEBCOGridMeta(
                source_uri=GEBCO_BASE,
                fetched_at=now,
                sha256=None,
                resolution_arcsec=15,
                grid_version="GEBCO_2026",
                variant=variant,
                crs="EPSG:4326",
                bbox=bbox,
            ),
            citation=GEBCO_CITATION,
            note=(
                "Offline mode (GEOX_GEBCO_OFFLINE=1). Set to 0 for live OPeNDAP. "
                "For full grid: download from CEDA or use download.gebco.net."
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
    "GEBCOFetcher",
    "GEBCOFetchResult",
    "GEBCOGridMeta",
    "GEBCOExtractRequest",
    "GEBCO_2026_SOURCES",
    "GEBCO_CITATION",
]
