"""
EMAG2v3 — Earth Magnetic Anomaly Grid (2 arc-minute) adapter for GEOX.

NOAA NGDC / NCEI global magnetic anomaly grid.
URL: https://www.ngdc.noaa.gov/geomag/EMAG2.html
REST: https://gis.ngdc.noaa.gov/arcgis/rest/services/EMAG2v3/ImageServer/getSamples

Resolution: 2 arc-minute (~3.7 km at equator)
Coverage: global, -90° to 90° lat, 0° to 360° lon
Units: nT (nanoTesla) — anomaly from IGRF reference field

CLAIM: This is a DERIVED grid — compiled from satellite (CHAMP, Swarm),
  marine, and aeromagnetic surveys. It is NOT observed ground truth.
  Use as BACKGROUND for anomaly interpretation, not as primary data.

CANON-9 links: χ (magnetic susceptibility), Vp (indirect via basement depth).

F9 ANTI-HANTU: EMAG2 at 2' is a MODEL GRID, not raw observation.
  Anomaly = observed_field - IGRF_reference_field. EMAG2 IS the
  anomaly field, but it has been upward-continued, merged, and filtered.
  Treat as DERIVED, not OBSERVED.
"""
from __future__ import annotations

import hashlib
import json
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

EMAG2_ARCGIS_URL = (
    "https://gis.ngdc.noaa.gov/arcgis/rest/services"
    "/EMAG2v3/ImageServer/getSamples"
)
# Default spatial reference: WGS84 (EPSG:4326)
EMAG2_SR = 4326


# ─── Result Schemas ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EMAG2SampleResult:
    """Single-point EMAG2 magnetic anomaly value."""
    lat: float
    lon: float
    anomaly_nT: float
    resolution_arcmin: float
    data_source: str = "EMAG2v3"
    claim_state: str = "DERIVED"
    provenance: str = (
        "NOAA NCEI EMAG2v3, 2 arc-min global magnetic anomaly grid. "
        "Source: satellite (CHAMP/Swarm) + marine + aeromagnetic. "
        "DOI: 10.7289/V5H70D0X"
    )


@dataclass(frozen=True)
class EMAG2GridResult:
    """EMAG2 magnetic anomaly on a regular grid."""
    lats: np.ndarray
    lons: np.ndarray
    anomaly_grid: np.ndarray
    shape: tuple[int, int]
    resolution_arcmin: float = 2.0
    data_source: str = "EMAG2v3"
    claim_state: str = "DERIVED"


@dataclass(frozen=True)
class EMAG2ProfileResult:
    """EMAG2 anomaly values along a profile (for QC against real survey lines)."""
    lats: np.ndarray
    lons: np.ndarray
    cumulative_distance_km: np.ndarray
    anomaly_profile_nT: np.ndarray
    n_points: int
    claim_state: str = "DERIVED"


@dataclass(frozen=True)
class EMAG2Input:
    """Input specification for EMAG2 queries."""
    lat: float
    lon: float
    coordinates: str = "geodetic"  # geodetic | geocentric


# ─── Backend Protocol ────────────────────────────────────────────────────────

class EMAG2Backend(Protocol):
    """Protocol for EMAG2 data retrieval backends."""
    def sample(self, lat: float, lon: float) -> EMAG2SampleResult:
        """Get EMAG2 anomaly at a single lat/lon point."""
        ...
    def grid(
        self,
        lat_min: float, lat_max: float,
        lon_min: float, lon_max: float,
        resolution_arcmin: float = 2.0
    ) -> EMAG2GridResult:
        """Get EMAG2 anomaly grid for a bounding box."""
        ...
    def profile(
        self,
        lats: list[float], lons: list[float]
    ) -> EMAG2ProfileResult:
        """Get EMAG2 anomaly along a profile (list of lat/lon waypoints)."""
        ...


# ─── Mock Backend ─────────────────────────────────────────────────────────────

class MockEMAG2Backend:
    """
    Mock EMAG2 backend — returns synthetic dipole-like anomaly pattern.

    F9 ANTI-HANTU: These are NOT real EMAG2 values.
    Use for geometry and integration testing only.
    """
    def __init__(self):
        logger.warning(
            "EMAG2 mock backend active — not real EMAG2 data. "
            "Install httpx and ensure network access for live EMAG2 queries."
        )

    def sample(self, lat: float, lon: float) -> EMAG2SampleResult:
        # Rough dipole anomaly: max ~200 nT at equator, falls off with lat
        lat_rad = np.radians(lat)
        anomaly = 200.0 * np.sin(lat_rad) * np.cos(np.radians(lon))
        return EMAG2SampleResult(
            lat=lat, lon=lon,
            anomaly_nT=float(anomaly),
            resolution_arcmin=2.0,
            claim_state="HYPOTHESIS_MOCK"
        )

    def grid(
        self,
        lat_min: float, lat_max: float,
        lon_min: float, lon_max: float,
        resolution_arcmin: float = 2.0
    ) -> EMAG2GridResult:
        n_lat = int((lat_max - lat_min) / (resolution_arcmin / 60.0)) + 1
        n_lon = int((lon_max - lon_min) / (resolution_arcmin / 60.0)) + 1
        lats = np.linspace(lat_min, lat_max, n_lat)
        lons = np.linspace(lon_min, lon_max, n_lon)
        anomaly_grid = np.array([
            [
                float(200.0 * np.sin(np.radians(lat)) * np.cos(np.radians(lon)))
                for lon in lons
            ]
            for lat in lats
        ])
        return EMAG2GridResult(
            lats=lats, lons=lons, anomaly_grid=anomaly_grid,
            shape=(n_lat, n_lon), resolution_arcmin=resolution_arcmin,
            claim_state="HYPOTHESIS_MOCK"
        )

    def profile(
        self,
        lats: list[float], lons: list[float]
    ) -> EMAG2ProfileResult:
        n = len(lats)
        anomalies = np.array([
            float(200.0 * np.sin(np.radians(lat)) * np.cos(np.radians(lon)))
            for lat, lon in zip(lats, lons, strict=False)
        ])
        # Compute cumulative distance along profile
        distances = np.zeros(n)
        for i in range(1, n):
            dlat = np.radians(lats[i] - lats[i-1])
            dlon = np.radians(lons[i] - lons[i-1])
            a = np.sin(dlat/2)**2 + np.cos(np.radians(lats[i-1])) * \
                np.cos(np.radians(lats[i])) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            distances[i] = distances[i-1] + 6371.0 * c  # km
        return EMAG2ProfileResult(
            lats=np.array(lats), lons=np.array(lons),
            cumulative_distance_km=distances,
            anomaly_profile_nT=anomalies,
            n_points=n,
            claim_state="HYPOTHESIS_MOCK"
        )


# ─── Live Backend (NOAA ArcGIS REST) ──────────────────────────────────────────

class LiveEMAG2Backend:
    """
    Live EMAG2 backend via NOAA NGDC ArcGIS REST API.

    Endpoint: GET /arcgis/rest/services/EMAG2v3/ImageServer/getSamples
    Parameters:
      geometry: {x, y} or {xmin, ymin, xmax, ymax}
      geometryType: esriGeometryPoint | esriGeometryEnvelope
      sr: EPSG code (4326 = WGS84)
      returnFirstValueOnly: true
      interpolation: Bilinear | NearestNeighbor
      f: json
    """
    def __init__(self):
        if not HAS_HTTPX:
            raise ImportError(
                "EMAG2 live backend requires httpx. "
                "Install: pip install httpx"
            )
        self.client = httpx.Client(timeout=30.0)
        logger.info("EMAG2 live backend initialised (NOAA ArcGIS REST)")

    def sample(self, lat: float, lon: float) -> EMAG2SampleResult:
        """Query EMAG2 anomaly at a single lat/lon point."""
        # ArcGIS uses lon, lat order (x, y)
        params = {
            "geometry": json.dumps({"x": lon, "y": lat}),
            "geometryType": "esriGeometryPoint",
            "sr": EMAG2_SR,
            "returnFirstValueOnly": "true",
            "interpolation": "Bilinear",
            "f": "json",
        }
        resp = self.client.get(EMAG2_ARCGIS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        # Parse response
        if "samples" in data and len(data["samples"]) > 0:
            value = float(data["samples"][0]["value"])
            data["samples"][0].get("location", {})
            # EMAG2 is in nT — already anomaly
            return EMAG2SampleResult(
                lat=lat, lon=lon,
                anomaly_nT=value,
                resolution_arcmin=2.0,
                claim_state="DERIVED"
            )
        else:
            raise ValueError(
                f"EMAG2 sample returned no data for ({lat}, {lon}). "
                f"Response: {data}"
            )

    def grid(
        self,
        lat_min: float, lat_max: float,
        lon_min: float, lon_max: float,
        resolution_arcmin: float = 2.0
    ) -> EMAG2GridResult:
        """
        Query EMAG2 on a regular grid via envelope query.

        Note: ArcGIS getSamples with envelope returns values at grid nodes
        defined by the service's native 2' resolution. For true arbitrary
        resolution, use profile() with generated waypoints.
        """
        params = {
            "geometry": json.dumps({
                "xmin": lon_min, "ymin": lat_min,
                "xmax": lon_max, "ymax": lat_max
            }),
            "geometryType": "esriGeometryEnvelope",
            "sr": EMAG2_SR,
            "returnFirstValueOnly": "false",
            "f": "json",
        }
        resp = self.client.get(EMAG2_ARCGIS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        if "samples" not in data or len(data["samples"]) == 0:
            raise ValueError(f"EMAG2 grid query returned no data: {data}")

        # Extract values and locations
        values = []
        lats_out = []
        lons_out = []
        for sample in data["samples"]:
            loc = sample.get("location", {})
            val = float(sample["value"])
            values.append(val)
            lons_out.append(float(loc.get("x", 0)))
            lats_out.append(float(loc.get("y", 0)))

        lats_arr = np.array(lats_out)
        lons_arr = np.array(lons_out)
        values_arr = np.array(values)

        # Determine grid shape from unique lat/lon counts
        unique_lats = np.unique(lats_arr)
        unique_lons = np.unique(lons_arr)
        n_lat, n_lon = len(unique_lats), len(unique_lons)

        # Reshape into grid
        anomaly_grid = np.full((n_lat, n_lon), np.nan)
        lat_to_idx = {lat: i for i, lat in enumerate(unique_lats)}
        lon_to_idx = {lon: i for i, lon in enumerate(unique_lons)}
        for lat, lon, val in zip(lats_arr, lons_arr, values_arr, strict=False):
            anomaly_grid[lat_to_idx[lat], lon_to_idx[lon]] = val

        return EMAG2GridResult(
            lats=unique_lats, lons=unique_lons,
            anomaly_grid=anomaly_grid,
            shape=anomaly_grid.shape,
            resolution_arcmin=2.0,
            claim_state="DERIVED"
        )

    def profile(
        self,
        lats: list[float], lons: list[float]
    ) -> EMAG2ProfileResult:
        """
        Query EMAG2 along a profile defined by waypoints.

        Generates interpolated points at ~1 km spacing between waypoints.
        """
        if not HAS_HTTPX:
            raise ImportError("EMAG2 profile requires httpx")

        # Generate dense waypoints along the profile
        import math
        dense_lats = [lats[0]]
        dense_lons = [lons[0]]
        for i in range(1, len(lats)):
            dlat = abs(lats[i] - lats[i-1])
            dlon = abs(lons[i] - lons[i-1])
            # Estimate number of 1-km steps
            n_steps = max(int(math.sqrt(dlat**2 + dlon**2) * 111.0), 1)
            for j in range(1, n_steps + 1):
                t = j / n_steps
                dense_lats.append(lats[i-1] + t * (lats[i] - lats[i-1]))
                dense_lons.append(lons[i-1] + t * (lons[i] - lons[i-1]))

        # Batch query (ArcGIS limit ~1000 points per request)
        BATCH = 500
        all_anomalies = []
        for batch_start in range(0, len(dense_lats), BATCH):
            batch_lats = dense_lats[batch_start:batch_start+BATCH]
            batch_lons = dense_lons[batch_start:batch_start+BATCH]

            geometries = [
                {"x": lon, "y": lat}
                for lon, lat in zip(batch_lons, batch_lats, strict=False)
            ]
            params = {
                "geometry": json.dumps(geometries),
                "geometryType": "esriGeometryPoint",
                "sr": EMAG2_SR,
                "returnFirstValueOnly": "true",
                "f": "json",
            }
            resp = self.client.get(EMAG2_ARCGIS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if "samples" in data:
                for s in data["samples"]:
                    all_anomalies.append(float(s["value"]))

        # Cumulative distance
        n = len(dense_lats)
        distances = np.zeros(n)
        for i in range(1, n):
            dlat = np.radians(dense_lats[i] - dense_lats[i-1])
            dlon = np.radians(dense_lons[i] - dense_lons[i-1])
            a = np.sin(dlat/2)**2 + np.cos(np.radians(dense_lats[i-1])) * \
                np.cos(np.radians(dense_lats[i])) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            distances[i] = distances[i-1] + 6371.0 * c

        return EMAG2ProfileResult(
            lats=np.array(dense_lats),
            lons=np.array(dense_lons),
            cumulative_distance_km=distances,
            anomaly_profile_nT=np.array(all_anomalies),
            n_points=n,
            claim_state="DERIVED"
        )


# ─── Adapter ──────────────────────────────────────────────────────────────────

@dataclass
class EMAG2Adapter:
    """
    GEOX adapter for EMAG2v3 global magnetic anomaly grid.

    Use for:
    - Regional magnetic basement depth interpretation
    - QC of ship/aero magnetic surveys against EMAG2 regional trend
    - Input to potential-field inversion (alongside gravity)

    NOT for:
    - Direct mineral exploration targeting (EMAG2 is compiled, filtered,
      upward-continued — resolution is 2 arc-min ~ 3.7 km)
    - Ground-truth substitute for actual magnetic surveys

    F9 ANTI-HANTU: EMAG2 is a MODEL, not OBSERVED data.
      It is derived from satellite + ship + aero merged and upward-
      continued to 4 km altitude equivalent. The 2' grid does NOT
      represent near-surface magnetic variations at <1 km wavelength.
    """
    backend: EMAG2Backend = field(default_factory=MockEMAG2Backend)

    def is_available(self) -> bool:
        """True if httpx is installed and network access is available."""
        return HAS_HTTPX

    def _hash_coords(self, lat: float, lon: float) -> str:
        key = f"{lat:.4f},{lon:.4f}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def sample(self, lat: float, lon: float) -> EMAG2SampleResult:
        """
        Get EMAG2 magnetic anomaly at a single point.

        Args:
            lat: Latitude (degrees, WGS84)
            lon: Longitude (degrees, WGS84)

        Returns:
            EMAG2SampleResult with anomaly in nT
        """
        logger.info(f"EMAG2 sample at ({lat:.4f}, {lon:.4f})")
        result = self.backend.sample(lat, lon)
        logger.info(
            f"EMAG2: anomaly={result.anomaly_nT:.1f} nT "
            f"[{result.claim_state}]"
        )
        return result

    def grid(
        self,
        lat_min: float, lat_max: float,
        lon_min: float, lon_max: float,
        resolution_arcmin: float = 2.0
    ) -> EMAG2GridResult:
        """
        Get EMAG2 anomaly grid for a bounding box.

        Note: Native resolution is 2 arc-min. Queries at finer resolution
        will receive 2' data interpolated. Queries at coarser resolution
        are aggregated. For basin-scale interpretation, 2' is appropriate.
        """
        if (lat_max - lat_min) > 60 or (lon_max - lon_min) > 60:
            logger.warning(
                "Large EMAG2 query area (>60°). Consider chunking or "
                "using a lower resolution to avoid ArcGIS timeout."
            )
        return self.backend.grid(lat_min, lat_max, lon_min, lon_max, resolution_arcmin)

    def profile(
        self,
        lats: list[float], lons: list[float]
    ) -> EMAG2ProfileResult:
        """
        Get EMAG2 anomaly along a survey profile.

        Args:
            lats: List of latitudes for profile waypoints
            lons: List of longitudes for profile waypoints

        Returns:
            EMAG2ProfileResult with distance-normalised anomaly profile

        Use for: QC of real survey line against EMAG2 regional.
        """
        return self.backend.profile(lats, lons)


# ─── Module-level factory ─────────────────────────────────────────────────────

_adapter_instance: EMAG2Adapter | None = None

def get_adapter() -> EMAG2Adapter:
    """Return the singleton EMAG2Adapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        if EMAG2Adapter().is_available():
            try:
                _adapter_instance = EMAG2Adapter(backend=LiveEMAG2Backend())
                logger.info("EMAG2Adapter: live backend (httpx available)")
            except Exception as e:
                logger.warning(f"EMAG2 live backend failed ({e}) — using mock")
                _adapter_instance = EMAG2Adapter()
        else:
            _adapter_instance = EMAG2Adapter()
            logger.warning(
                "EMAG2Adapter: mock backend (httpx not installed). "
                "Install with: pip install httpx"
            )
    return _adapter_instance
