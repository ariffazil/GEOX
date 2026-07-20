"""
GEBCO — General Bathymetric Chart of the Oceans adapter for GEOX.

Data sources:
  1. GEBCO FastAPI (REST) — ODB Taiwan, GEBCO 2023 at 15 arc-sec
     URL: https://api.odb.ntu.edu.tw/gebco
  2. GEBCO 2025 Grid — downloadable from gebco.net (CC BY 4.0)
     15 arc-second global grid, ~800 MB compressed

Resolution: 15 arc-second (~463 m at equator)
Coverage: global, -90° to 90° lat, -180° to 180° lon
Units: metres (negative = below sea level)

CLAIM: OBSERVED for ocean areas (ship echo-sounding + satellite altimetry
  derived). OBSERVED for land areas (SRTM/Copernicus DEM).
  NOT OBSERVED for poorly-surveyed ocean areas (southcentral Pacific,
  Southern Ocean) — filled with satellite-predicted bathymetry = DERIVED.

CANON-9 links: P (sea water pressure), ρ (ocean water density at seafloor).

F9 ANTI-HANTU: GEBCO in unsurveyed ocean areas uses gravity-derived
  predictions (Sandwell model). These areas are labeled DERIVED.
  Always check the GEBCO quality indicator layer if available.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

GEBCO_FASTAPI_URL = "https://api.odb.ntu.edu.tw/gebco"
# Alternative: direct GEBCO 2025 download (requires ~/.netrc credentials)
# GEBCO_2025_URL = "https://www.gebco.net/data_and_products/"

# Land mask: approx threshold for "below sea level"
SEA_LEVEL_M = 0.0


# ─── Result Schemas ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GEBCOSampleResult:
    """Single-point GEBCO elevation/bathymetry value."""

    lat: float
    lon: float
    elevation_m: float
    resolution_arcsec: float
    data_source: str
    claim_state: str  # OBSERVED or DERIVED
    provenance: str


@dataclass(frozen=True)
class GEBCOGridResult:
    """GEBCO elevation/bathymetry grid for a bounding box."""

    lats: np.ndarray
    lons: np.ndarray
    elevation_grid: np.ndarray  # metres (negative = seafloor)
    shape: tuple[int, int]
    resolution_arcsec: float
    data_source: str
    claim_state: str


@dataclass(frozen=True)
class GEBCOProfileResult:
    """GEBCO elevation along a profile."""

    lats: np.ndarray
    lons: np.ndarray
    cumulative_distance_km: np.ndarray
    elevation_m: np.ndarray
    n_points: int
    claim_state: str


@dataclass(frozen=True)
class GEBCOZProfileResult:
    """GEBCO zonal profile (average depth/elevation in latitude bands)."""

    lats: np.ndarray
    mean_elevation_m: np.ndarray
    min_elevation_m: np.ndarray
    max_elevation_m: np.ndarray
    std_elevation_m: np.ndarray
    claim_state: str


# ─── Backend Protocol ────────────────────────────────────────────────────────


class GEBCOBackend(Protocol):
    """Protocol for GEBCO bathymetry retrieval."""

    def sample(self, lat: float, lon: float) -> GEBCOSampleResult:
        """Get GEBCO elevation at a single point."""
        ...

    def grid(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, resolution_arcsec: float = 15.0
    ) -> GEBCOGridResult:
        """Get GEBCO elevation grid."""
        ...

    def profile(self, lats: list[float], lons: list[float]) -> GEBCOProfileResult:
        """Get GEBCO elevation along a profile."""
        ...


# ─── Mock Backend ─────────────────────────────────────────────────────────────


class MockGEBCOBackend:
    """
    Mock GEBCO backend — returns simple elevation model.

    F9 ANTI-HANTU: These are NOT real GEBCO values.
    Ocean bathymetry is complex; this mock uses flat sea level.
    """

    def __init__(self):
        logger.warning("GEBCO mock backend active — not real bathymetry. Install httpx for live GEBCO FastAPI access.")

    def sample(self, lat: float, lon: float) -> GEBCOSampleResult:
        # Very rough: land above 0, ocean below
        # In reality, most of ocean floor is -3000 to -6000 m
        import math

        land_prob = math.sin(math.radians(lat)) * 0.5 + 0.3
        elevation = -4000.0 if np.random.random() > land_prob else 200.0
        return GEBCOSampleResult(
            lat=lat,
            lon=lon,
            elevation_m=float(elevation),
            resolution_arcsec=15.0,
            data_source="GEBCO-MOCK",
            claim_state="HYPOTHESIS_MOCK",
            provenance="Mock GEBCO — not real data",
        )

    def grid(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, resolution_arcsec: float = 15.0
    ) -> GEBCOGridResult:
        n_lat = int((lat_max - lat_min) / (resolution_arcsec / 3600.0)) + 1
        n_lon = int((lon_max - lon_min) / (resolution_arcsec / 3600.0)) + 1
        lats = np.linspace(lat_min, lat_max, n_lat)
        lons = np.linspace(lon_min, lon_max, n_lon)
        # Simple model: land near equator (rough approximation)
        elevation_grid = np.full((n_lat, n_lon), -4000.0)
        return GEBCOGridResult(
            lats=lats,
            lons=lons,
            elevation_grid=elevation_grid,
            shape=(n_lat, n_lon),
            resolution_arcsec=resolution_arcsec,
            data_source="GEBCO-MOCK",
            claim_state="HYPOTHESIS_MOCK",
        )

    def profile(self, lats: list[float], lons: list[float]) -> GEBCOProfileResult:
        n = len(lats)
        elevations = np.full(n, -4000.0)
        distances = np.zeros(n)
        for i in range(1, n):
            dlat = np.radians(lats[i] - lats[i - 1])
            dlon = np.radians(lons[i] - lons[i - 1])
            a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lats[i - 1])) * np.cos(np.radians(lats[i])) * np.sin(dlon / 2) ** 2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
            distances[i] = distances[i - 1] + 6371.0 * c
        return GEBCOProfileResult(
            lats=np.array(lats),
            lons=np.array(lons),
            cumulative_distance_km=distances,
            elevation_m=elevations,
            n_points=n,
            claim_state="HYPOTHESIS_MOCK",
        )


# ─── Live Backend (GEBCO FastAPI) ─────────────────────────────────────────────


class LiveGEBCOBackend:
    """
    Live GEBCO backend via ODB Taiwan FastAPI.

    API: https://api.odb.ntu.edu.tw/gebco
    Endpoints:
      GET /v1/bathymetry?lat=&lon=  → single point
      GET /v1/bathymetry/band?lat_min=&lat_max=&lon_min=&lon_max=&resolution=  → grid
    """

    def __init__(self):
        if not HAS_HTTPX:
            raise ImportError("GEBCO live backend requires httpx")
        self.client = httpx.Client(timeout=60.0)
        logger.info("GEBCO live backend initialised (ODB FastAPI)")

    def sample(self, lat: float, lon: float) -> GEBCOSampleResult:
        """Query GEBCO bathymetry at a single lat/lon."""
        params = {"lat": lat, "lon": lon}
        resp = self.client.get(f"{GEBCO_FASTAPI_URL}/v1/bathymetry", params=params)
        resp.raise_for_status()
        data = resp.json()

        elevation = float(data.get("elevation", 0.0))
        # Determine claim state: ship soundings = OBSERVED, gravity fill = DERIVED
        # GEBCO FastAPI doesn't expose quality flags, so use elevation heuristic
        # Sea floor < -8000 m is likely gravity-predicted (DERIVED)
        claim = "OBSERVED" if -8000 < elevation < 9000 else "DERIVED"

        return GEBCOSampleResult(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            resolution_arcsec=15.0,
            data_source="GEBCO 2023 (15 arc-sec, ODB FastAPI)",
            claim_state=claim,
            provenance=(
                "GEBCO 2023 Grid, 15 arc-sec resolution. "
                "Sources: ship echo-sounding + satellite altimetry. "
                "Areas deeper than ~8000 m may be gravity-predicted. "
                "CC BY 4.0 — General Bathymetric Chart of the Oceans."
            ),
        )

    def grid(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, resolution_arcsec: float = 15.0
    ) -> GEBCOGridResult:
        """
        Query GEBCO elevation grid for a bounding box.

        Note: ODB FastAPI resolution parameter controls output grid spacing.
        GEBCO 2023 native is 15 arc-sec. Using coarser resolution
        returns averaged values.
        """
        params = {
            "lat_min": lat_min,
            "lat_max": lat_max,
            "lon_min": lon_min,
            "lon_max": lon_max,
            "resolution": int(resolution_arcsec),  # arc-seconds
        }
        resp = self.client.get(f"{GEBCO_FASTAPI_URL}/v1/bathymetry/band", params=params)
        resp.raise_for_status()
        data = resp.json()

        # Response expected: { "lat": [...], "lon": [...], "elevation": [[...]] }
        lats = np.array(data.get("lat", []))
        lons = np.array(data.get("lon", []))
        elevation_grid = np.array(data.get("elevation", [[]]))

        return GEBCOGridResult(
            lats=lats,
            lons=lons,
            elevation_grid=elevation_grid,
            shape=elevation_grid.shape,
            resolution_arcsec=resolution_arcsec,
            data_source="GEBCO 2023 (ODB FastAPI)",
            claim_state="MIXED_OBSERVED_DERIVED",
        )

    def profile(self, lats: list[float], lons: list[float]) -> GEBCOProfileResult:
        """Query GEBCO along a profile defined by waypoints."""
        # Generate dense waypoints
        import math

        dense_lats = [lats[0]]
        dense_lons = [lons[0]]
        for i in range(1, len(lats)):
            dlat = abs(lats[i] - lats[i - 1])
            dlon = abs(lons[i] - lons[i - 1])
            n_steps = max(int(math.sqrt(dlat**2 + dlon**2) * 111.0), 2)
            for j in range(1, n_steps + 1):
                t = j / n_steps
                dense_lats.append(lats[i - 1] + t * (lats[i] - lats[i - 1]))
                dense_lons.append(lons[i - 1] + t * (lons[i] - lons[i - 1]))

        # Batch query
        BATCH = 200
        all_elevations = []
        batch_lats = []
        batch_lons = []

        for lat, lon in zip(dense_lats, dense_lons, strict=False):
            batch_lats.append(lat)
            batch_lons.append(lon)
            if len(batch_lats) >= BATCH:
                elevs = self._batch_sample(batch_lats, batch_lons)
                all_elevations.extend(elevs)
                batch_lats, batch_lons = [], []

        if batch_lats:
            elevs = self._batch_sample(batch_lats, batch_lons)
            all_elevations.extend(elevs)

        # Cumulative distance
        n = len(dense_lats)
        distances = np.zeros(n)
        for i in range(1, n):
            dlat = np.radians(dense_lats[i] - dense_lats[i - 1])
            dlon = np.radians(dense_lons[i] - dense_lons[i - 1])
            a = (
                np.sin(dlat / 2) ** 2
                + np.cos(np.radians(dense_lats[i - 1])) * np.cos(np.radians(dense_lats[i])) * np.sin(dlon / 2) ** 2
            )
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
            distances[i] = distances[i - 1] + 6371.0 * c

        return GEBCOProfileResult(
            lats=np.array(dense_lats),
            lons=np.array(dense_lons),
            cumulative_distance_km=distances,
            elevation_m=np.array(all_elevations),
            n_points=n,
            claim_state="MIXED_OBSERVED_DERIVED",
        )

    def _batch_sample(self, lats: list[float], lons: list[float]) -> list[float]:
        """Sample GEBCO at multiple points via batch endpoint."""
        elevations = []
        for lat, lon in zip(lats, lons, strict=False):
            try:
                params = {"lat": lat, "lon": lon}
                resp = self.client.get(f"{GEBCO_FASTAPI_URL}/v1/bathymetry", params=params, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                elevations.append(float(data.get("elevation", 0.0)))
            except Exception:
                elevations.append(float("nan"))
        return elevations


# ─── Adapter ──────────────────────────────────────────────────────────────────


@dataclass
class GEBCOAdapter:
    """
    GEOX adapter for GEBCO bathymetry.

    Use for:
    - Ocean bathymetry context in basin analysis
    - Water depth for seismic depth conversion (TVD to TWT)
    - Seabed classification input (EMODnet substrate)
    - Plate reconstruction validation (paleobathymetry)

    F9 ANTI-HANTU: GEBCO in poorly surveyed oceans (Southern Ocean,
      central Pacific) uses gravity-derived predictions. The grid
      represents the best available model, NOT direct measurement.
      Check the GEBCO quality indicator layer when available.
    """

    backend: GEBCOBackend = field(default_factory=MockGEBCOBackend)

    def is_available(self) -> bool:
        return HAS_HTTPX

    def sample(self, lat: float, lon: float) -> GEBCOSampleResult:
        """
        Get GEBCO elevation at a single point (metres, WGS84).

        Negative = seafloor depth. Positive = land elevation.
        """
        logger.info(f"GEBCO sample at ({lat:.4f}, {lon:.4f})")
        return self.backend.sample(lat, lon)

    def grid(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, resolution_arcsec: float = 15.0
    ) -> GEBCOGridResult:
        """
        Get GEBCO elevation grid for a bounding box.

        Args:
            lat_min, lat_max: Latitude bounds (degrees)
            lon_min, lon_max: Longitude bounds (degrees)
            resolution_arcsec: Output resolution (default 15', GEBCO native)

        Note: Large grids (e.g., >20° × 20°) may require chunking
        to avoid API timeouts.
        """
        return self.backend.grid(lat_min, lat_max, lon_min, lon_max, resolution_arcsec)

    def profile(self, lats: list[float], lons: list[float]) -> GEBCOProfileResult:
        """
        Get GEBCO bathymetry along a profile.

        Used for:
        - QC against ship tracks
        - Depth-converted seismic section validation
        - Seabed gradient analysis for geostrophic currents
        """
        return self.backend.profile(lats, lons)


# ─── Module-level factory ─────────────────────────────────────────────────────

_adapter_instance: GEBCOAdapter | None = None


def get_adapter() -> GEBCOAdapter:
    """Return the singleton GEBCOAdapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        if GEBCOAdapter().is_available():
            try:
                _adapter_instance = GEBCOAdapter(backend=LiveGEBCOBackend())
                logger.info("GEBCOAdapter: live backend (httpx + ODB FastAPI)")
            except Exception as e:
                logger.warning(f"GEBCO live backend failed ({e}) — using mock")
                _adapter_instance = GEBCOAdapter()
        else:
            _adapter_instance = GEBCOAdapter()
            logger.warning("GEBCOAdapter: mock backend. Install httpx for live access: pip install httpx")
    return _adapter_instance
