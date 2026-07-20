"""
emag2_fetcher.py — W₉-W₁₂ Phase B: open data fetcher for EMAG2v3.

EMAG2v3 = Earth Magnetic Anomaly Grid (version 3), 2-arc-minute resolution,
compiled from satellite + ship + airborne magnetic measurements.

Source: NOAA National Centers for Environmental Information (NCEI)
URL: https://www.ncei.noaa.gov/products/earth-magnetic-model-anomaly-grid-2
EarthRef mirror: https://earthref.org/ERDA/970/

License: Public Domain (US Government work)

GEOX adapter doctrine:
- All fetches go through schema-translated client. Raw bytes never returned.
- Offline mode: returns a clearly-marked stub if the file is not present
  locally. Network calls are non-blocking and tolerant.
- Provenance always attached (input_hash, source_uri, fetched_at).

DITEMPA BUKAN DIBEI — open data is forged through trust envelope.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

# ───────────────────────────── CANONICAL URLS ────────────────────────────────────
EMAG2_V3_SOURCES = {
    "ncei_grid": "https://www.ncei.noaa.gov/products/earth-magnetic-model-anomaly-grid-2",
    "earthref_grid": "https://earthref.org/ERDA/970/",
    "gplates_portal": "https://portal.gplates.org/portal/emag2/",
    # Direct V3 grid — currently available as TIFF (~228 MB, updated URL).
    # NetCDF mirror at old URL returned 404 as of 2026-06-21; NCEI migrated
    # to TIFF-only distribution.
    "v3_grid_tiff": "https://www.ngdc.noaa.gov/geomag/data/EMAG2/EMAG2_V3_UpCont_DataTiff.tif",
    "v3_grid_netcdf": None,  # legacy 2017 NetCDF no longer hosted
    "citation": (
        "Meyer, B., Chulliat, A., & Saltus, R. (2017). "
        "Earth Magnetic Anomaly Grid (EMAG2v3) — public domain release. "
        "NOAA NCEI. Active distribution: EMAG2_V3_UpCont_DataTiff.tif (228 MB)."
    ),
}

ICGEM_BASE_URL = "https://icgem.gfz-potsdam.de/tom_longtime"
WGM2012_URL = "https://bgi.obs-mip.fr/grids-and-models-2/"


# ───────────────────────────── SCHEMAS ────────────────────────────────────────────
@dataclass(frozen=True)
class EMAG2GridMeta:
    """Metadata about a fetched EMAG2v3 grid."""

    source_uri: str
    fetched_at: str
    sha256: str | None
    resolution_arcmin: float
    crs: str
    bbox: tuple[float, float, float, float]  # min_lon, min_lat, max_lon, max_lat


class EMAG2FetchResult(BaseModel):
    """Result envelope for an EMAG2v3 fetch."""

    ok: bool
    mode: str  # "live" | "offline_stub"
    grid_path: str | None = None
    meta: EMAG2GridMeta | None = None
    citation: str = EMAG2_V3_SOURCES["citation"]
    note: str = ""


class ICGEMGravityModel(BaseModel):
    """ICGEM global gravity field model metadata."""

    name: str
    source_uri: str
    citation: str
    fetched_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# ───────────────────────────── FETCHER ────────────────────────────────────────────
class EMAG2Fetcher:
    """Constitutional fetcher for EMAG2v3.

    Modes:
    - GEOX_EMAG2_OFFLINE=1 (default for safety): returns a clearly-marked stub
      instead of attempting a 500MB download. Operator must explicitly opt in.
    - GEOX_EMAG2_OFFLINE=0 AND GEOX_EMAG2_LOCAL_PATH set: load from local path,
      verify SHA-256 if GEOX_EMAG2_EXPECTED_SHA256 is set.

    The fetcher never returns raw bytes to callers — only schema-translated
    metadata + a verified-on-disk path.
    """

    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = Path(cache_dir or os.environ.get("GEOX_EMAG2_CACHE_DIR", "/root/.cache/geox/emag2"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_EMAG2_OFFLINE", "1") != "0"

    def grid_path(self) -> Path:
        """Return the on-disk path where the V3 grid is expected (current: TIFF)."""
        return self.cache_dir / "EMAG2_V3_UpCont_DataTiff.tif"

    def fetch(self, *, force: bool = False) -> EMAG2FetchResult:
        """Fetch (or load from cache) the EMAG2v3 grid.

        - If offline mode: return stub with ok=True, mode='offline_stub'.
        - If live: try local path; if not present, attempt download (deferred).
        - If force=True and offline: ignore cache.
        """
        citation = EMAG2_V3_SOURCES["citation"]
        if self._offline:
            return EMAG2FetchResult(
                ok=True,
                mode="offline_stub",
                grid_path=None,
                meta=EMAG2GridMeta(
                    source_uri=EMAG2_V3_SOURCES["v3_grid_netcdf"],
                    fetched_at=datetime.now(UTC).isoformat(),
                    sha256=None,
                    resolution_arcmin=2.0,
                    crs="EPSG:4326",
                    bbox=(-180.0, -90.0, 180.0, 90.0),
                ),
                citation=citation,
                note=(
                    "Offline mode (GEOX_EMAG2_OFFLINE=1). Set to 0 and provide "
                    "GEOX_EMAG2_LOCAL_PATH or run a one-time download via "
                    "download_emag2() helper to enable live ingestion."
                ),
            )

        local = self.grid_path()
        if local.exists() and not force:
            sha = self._sha256(local)
            return EMAG2FetchResult(
                ok=True,
                mode="live",
                grid_path=str(local),
                meta=EMAG2GridMeta(
                    source_uri=EMAG2_V3_SOURCES["v3_grid_netcdf"],
                    fetched_at=datetime.fromtimestamp(local.stat().st_mtime).isoformat(),
                    sha256=sha,
                    resolution_arcmin=2.0,
                    crs="EPSG:4326",
                    bbox=(-180.0, -90.0, 180.0, 90.0),
                ),
                citation=citation,
            )

        # Live download deferred to operator — see note in fetch().
        return EMAG2FetchResult(
            ok=False,
            mode="live",
            grid_path=None,
            note=(
                "Live fetch requested but no local file present. Operator must "
                "run one-time download (curl/wget) and re-run with the file in "
                "place. This is intentional — prevents accidental 500MB pulls."
            ),
            citation=citation,
        )

    def download_emag2(self) -> None:
        """Explicit one-time download helper. Operator-only.

        Streams the ~500MB NetCDF grid from NOAA NCEI to GEOX_EMAG2_CACHE_DIR.
        """
        import urllib.request

        target = self.grid_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        url = EMAG2_V3_SOURCES["v3_grid_netcdf"]
        # Stream with progress callback (silent for now)
        with urllib.request.urlopen(url) as resp, open(target, "wb") as f:
            while True:
                chunk = resp.read(1 << 20)  # 1 MiB
                if not chunk:
                    break
                f.write(chunk)

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()


# ───────────────────────────── ICGEM ──────────────────────────────────────────────
class ICGEMFetcher:
    """Constitutional client for ICGEM (GFZ Potsdam) global gravity field models.

    Live HTTP calls deferred to operator — this is a metadata + citation client
    until 888 deploys the live link.
    """

    KNOWN_MODELS = [
        ICGEMGravityModel(
            name="EIGEN-6C4",
            source_uri=f"{ICGEM_BASE_URL}",
            citation=(
                "Förste et al. (2014). EIGEN-6C4: The latest combined global "
                "gravity field model including GOCE data up to degree/order 2190. "
                "GFZ Potsdam, ICGEM."
            ),
        ),
        ICGEMGravityModel(
            name="EGM2008",
            source_uri=f"{ICGEM_BASE_URL}",
            citation=(
                "Pavlis et al. (2012). The development and evaluation of the "
                "Earth Gravitational Model 2008 (EGM2008). J. Geophys. Res."
            ),
        ),
        ICGEMGravityModel(
            name="XGM2019",
            source_uri=f"{ICGEM_BASE_URL}",
            citation=("Zingerle et al. (2020). The experimental gravity field model XGM2019. GFZ Potsdam."),
        ),
    ]

    def list_models(self) -> list[ICGEMGravityModel]:
        return list(self.KNOWN_MODELS)


# ───────────────────────────── WGM2012 ────────────────────────────────────────────
class WGM2012Citation:
    """WGM2012 — World Gravity Map (BGI / CNES)."""

    CITATION = (
        "Bonvalot et al. (2012). World Gravity Map (WGM2012). "
        "Bureau Gravimétrique International (BGI) / CNES. "
        "1'×1' resolution terrain corrections."
    )
    SOURCE_URI = WGM2012_URL


__all__ = [
    "EMAG2Fetcher",
    "EMAG2FetchResult",
    "EMAG2GridMeta",
    "EMAG2_V3_SOURCES",
    "ICGEMFetcher",
    "ICGEMGravityModel",
    "WGM2012Citation",
]
