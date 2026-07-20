"""
ppigrf — IGRF-14 magnetic field model adapter for GEOX.

Supports: field components (Be, Bn, Bu), total intensity (F),
         magnetic declination (D), grid prediction.

CLAIM: Derivation of D, F at survey coordinates = DERIVED.
CANON-9 links: χ (magnetic susceptibility context), MWD tool correction.

F9 ANTI-HANTU: This adapter computes from IGRF-14 coefficients —
it does not sense the real Earth field. Anomaly = observed - IGRF.
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

logger = logging.getLogger(__name__)

# ─── Result Schemas ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class IGRFResult:
    """Result from a single-point IGRF field computation."""

    Be: float  # East component (nT)
    Bn: float  # North component (nT)
    Bu: float  # Up component (nT)
    F: float  # Total field intensity (nT)
    D: float  # Declination (degrees, positive East)
    I: float  # Inclination (degrees, positive down)
    lat: float
    lon: float
    alt_km: float
    date_year: float
    model: str = "IGRF-14"
    claim_state: str = "DERIVED"
    provenance: str = "ppigrf IGRF-14 coefficients, DOI: 10.5883/IGRF-14"


@dataclass(frozen=True)
class IGRFGridResult:
    """Result from a grid of IGRF field computations."""

    lats: np.ndarray
    lons: np.ndarray
    F_grid: np.ndarray
    D_grid: np.ndarray
    shape: tuple[int, int]
    resolution_arcmin: float
    date_year: float
    model: str = "IGRF-14"
    claim_state: str = "DERIVED"
    provenance: str = "ppigrf IGRF-14 coefficients, DOI: 10.5883/IGRF-14"


@dataclass(frozen=True)
class MagneticDeclinationResult:
    """Magnetic declination only — common MWD correction output."""

    D_deg: float
    I_deg: float
    F_nT: float
    lat: float
    lon: float
    alt_km: float
    date_year: float
    claim_state: str = "DERIVED"
    provenance: str = "ppigrf IGRF-14"


@dataclass(frozen=True)
class IGRFInput:
    """Input specification for IGRF field computation."""

    lat: float
    lon: float
    date_year: float  # no default — must be explicit
    alt_km: float = 0.0
    coordinates: str = "geodetic"  # geodetic | geocentric


# ─── Backend Protocol ────────────────────────────────────────────────────────


class IGRFBackend(Protocol):
    """Protocol for IGRF computation backends."""

    def field(self, lat: float, lon: float, alt_km: float, date_year: float) -> IGRFResult:
        """Compute IGRF field components at a single point."""
        ...

    def grid(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, resolution_arcmin: float, date_year: float
    ) -> IGRFGridResult:
        """Compute IGRF on a regular grid."""
        ...

    def declination(self, lat: float, lon: float, alt_km: float, date_year: float) -> MagneticDeclinationResult:
        """Compute magnetic declination at a single point (MWD use case)."""
        ...


# ─── Mock Backend (no ppigrf installed) ─────────────────────────────────────


class MockIGRFBackend:
    """
    Mock IGRF-14 backend — returns physically plausible values
    based on dipole approximation for testing without ppigrf installed.

    F9 ANTI-HANTU: These are NOT real field values.
    Use for geometry/shape testing only. Never claim as real data.
    """

    IGRF14_DIPOLE_MOMENT = 7.794e22  # Approximate Earth dipole moment
    IGRF14_INCLINATION = 66.0  # Approximate dipole inclination (degrees)

    def field(self, lat: float, lon: float, alt_km: float, date_year: float) -> IGRFResult:
        # Simple dipole approximation
        lat_rad = math.radians(lat)
        # Horizontal component approximation
        F_approx = 25_000 + 15_000 * math.sin(lat_rad)  # nT, rough dipole
        I_approx = self.IGRF14_INCLINATION * math.sin(lat_rad)
        D_approx = 0.0  # Dipole has no declination; real D varies with longitude
        return IGRFResult(
            Be=0.0,
            Bn=0.0,
            Bu=0.0,
            F=F_approx,
            D=D_approx,
            I=I_approx,
            lat=lat,
            lon=lon,
            alt_km=alt_km,
            date_year=date_year,
            model="IGRF-14-MOCK",
            claim_state="HYPOTHESIS_MOCK",
        )

    def grid(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, resolution_arcmin: float, date_year: float
    ) -> IGRFGridResult:
        n_lat = int((lat_max - lat_min) / (resolution_arcmin / 60.0)) + 1
        n_lon = int((lon_max - lon_min) / (resolution_arcmin / 60.0)) + 1
        lats = np.linspace(lat_min, lat_max, n_lat)
        lons = np.linspace(lon_min, lon_max, n_lon)
        F_grid = np.array([[25_000 + 15_000 * math.sin(math.radians(lat)) for lon in lons] for lat in lats])
        return IGRFGridResult(
            lats=lats,
            lons=lons,
            F_grid=F_grid,
            D_grid=np.zeros_like(F_grid),
            shape=(n_lat, n_lon),
            resolution_arcmin=resolution_arcmin,
            date_year=date_year,
            model="IGRF-14-MOCK",
            claim_state="HYPOTHESIS_MOCK",
        )

    def declination(self, lat: float, lon: float, alt_km: float, date_year: float) -> MagneticDeclinationResult:
        result = self.field(lat, lon, alt_km, date_year)
        return MagneticDeclinationResult(
            D_deg=result.D,
            I_deg=result.I,
            F_nT=result.F,
            lat=lat,
            lon=lon,
            alt_km=alt_km,
            date_year=date_year,
            claim_state="HYPOTHESIS_MOCK",
        )


# ─── Live Backend (ppigrf installed) ─────────────────────────────────────────


class LiveIGRFBackend:
    """
    Live IGRF-14 backend using ppigrf.
    ppigrf is pure Python / numpy — no Fortran compiler required.
    """

    def __init__(self):
        import ppigrf  # noqa: F401 — raises ImportError if not installed

        self.ppigrf = __import__("ppigrf")
        logger.info("IGRF live backend initialised with ppigrf")

    def field(self, lat: float, lon: float, alt_km: float, date_year: float) -> IGRFResult:
        # ppigrf.igrf() returns (Be, Bn, Bu) in nT for geocentric coords
        # Input: lat/lon in degrees, alt in km, decimal year
        import ppigrf

        # Convert geodetic to geocentric if needed
        # ppigrf.igrf expects geodetic (lat, lon, alt_km, year)
        Be, Bn, Bu = ppigrf.igrf(lon, lat, alt_km, date_year)
        # Total field
        F = math.sqrt(Be**2 + Bn**2 + Bu**2)
        # Declination: D = arctan2(Be, Bn)
        D = math.degrees(math.atan2(Be, Bn))
        # Inclination: I = arctan2(Bu, sqrt(Be² + Bn²))
        H = math.sqrt(Be**2 + Bn**2)
        I = math.degrees(math.atan2(Bu, H))
        return IGRFResult(
            Be=float(Be),
            Bn=float(Bn),
            Bu=float(Bu),
            F=float(F),
            D=float(D),
            I=float(I),
            lat=lat,
            lon=lon,
            alt_km=alt_km,
            date_year=date_year,
            model="IGRF-14",
            claim_state="DERIVED",
        )

    def grid(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, resolution_arcmin: float, date_year: float
    ) -> IGRFGridResult:
        import ppigrf

        n_lat = int((lat_max - lat_min) / (resolution_arcmin / 60.0)) + 1
        n_lon = int((lon_max - lon_min) / (resolution_arcmin / 60.0)) + 1
        lats = np.linspace(lat_min, lat_max, n_lat)
        lons = np.linspace(lon_min, lon_max, n_lon)
        F_grid = np.zeros((n_lat, n_lon))
        D_grid = np.zeros((n_lat, n_lon))
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                Be, Bn, Bu = ppigrf.igrf(lon, lat, 0.0, date_year)
                F_grid[i, j] = math.sqrt(Be**2 + Bn**2 + Bu**2)
                D_grid[i, j] = math.degrees(math.atan2(Be, Bn))
        return IGRFGridResult(
            lats=lats,
            lons=lons,
            F_grid=F_grid,
            D_grid=D_grid,
            shape=(n_lat, n_lon),
            resolution_arcmin=resolution_arcmin,
            date_year=date_year,
            model="IGRF-14",
            claim_state="DERIVED",
        )

    def declination(self, lat: float, lon: float, alt_km: float, date_year: float) -> MagneticDeclinationResult:
        result = self.field(lat, lon, alt_km, date_year)
        return MagneticDeclinationResult(
            D_deg=result.D,
            I_deg=result.I,
            F_nT=result.F,
            lat=lat,
            lon=lon,
            alt_km=alt_km,
            date_year=date_year,
            claim_state="DERIVED",
        )


# ─── Adapter ─────────────────────────────────────────────────────────────────


@dataclass
class IGRFAdapter:
    """
    GEOX adapter for IGRF-14 Earth magnetic field model.

    Use for:
    - MWD (Measurement While Drilling) declination correction
    - Magnetic anomaly baseline removal (anomaly = observed - IGRF)
    - Regional magnetic interpretation (IGRF as regional trend)

    CANON-9 variable: χ (magnetic susceptibility context) — IGRF
    provides the background field against which anomaly is measured.

    Anti-Hantu: IGRF is a model, NOT an observation. The true Earth
    field deviates from IGRF by tens to thousands of nT — these
    deviations ARE the magnetic anomaly and are what we explore for.
    """

    backend: IGRFBackend = field(default_factory=MockIGRFBackend)

    def is_available(self) -> bool:
        """True if ppigrf is installed and live backend is active."""
        try:
            __import__("ppigrf")
            return True
        except ImportError:
            return False

    def _hash_input(self, lat: float, lon: float, alt_km: float, date_year: float) -> str:
        key = f"{lat:.4f},{lon:.4f},{alt_km:.4f},{date_year:.4f}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def field(self, lat: float, lon: float, alt_km: float = 0.0, date_year: float = 2025.0) -> IGRFResult:
        """
        Compute IGRF-14 field components at a single point.

        Args:
            lat: Geodetic latitude (degrees)
            lon: Longitude (degrees)
            alt_km: Altitude above WGS84 ellipsoid (km)
            date_year: Decimal year (e.g., 2025.5 for mid-2025)

        Returns:
            IGRFResult with Be, Bn, Bu, F, D, I components

        Example:
            >>> result = adapter.field(lat=5.0, lon=110.0, alt_km=0.0, date_year=2025.0)
            >>> print(f"Declination: {result.D:.2f}°, Inclination: {result.I:.2f}°")
        """
        logger.info(
            f"IGRF field at ({lat:.4f}, {lon:.4f}, {alt_km:.4f} km), year {date_year:.4f}, backend={type(self.backend).__name__}"
        )
        result = self.backend.field(lat, lon, alt_km, date_year)
        self._hash_input(lat, lon, alt_km, date_year)
        logger.info(f"IGRF result: F={result.F:.1f} nT, D={result.D:.2f}°, I={result.I:.2f}° [{result.claim_state}]")
        return result

    def declination(self, lat: float, lon: float, alt_km: float = 0.0, date_year: float = 2025.0) -> MagneticDeclinationResult:
        """
        Compute magnetic declination — primary MWD correction tool.

        Returns:
            MagneticDeclinationResult with D (degrees East), I, and F

        Anti-Hantu: Declination changes with time (secular variation).
        Always use the correct decimal year. Using a stale IGRF epoch
        for MWD correction introduces systematic error proportional to
        the time gap × secular variation rate (~30-60 nT/decade).
        """
        return self.backend.declination(lat, lon, alt_km, date_year)

    def grid(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        resolution_arcmin: float = 10.0,
        date_year: float = 2025.0,
    ) -> IGRFGridResult:
        """
        Compute IGRF-14 on a regular grid — for regional grid preparation.

        Args:
            lat_min, lat_max: Latitude bounds (degrees)
            lon_min, lon_max: Longitude bounds (degrees)
            resolution_arcmin: Grid resolution (arc-minutes). Default 10'.
            date_year: Decimal year for temporal epoch

        Returns:
            IGRFGridResult with F_grid and D_grid arrays

        Note:
            Grid computation scales as O(n²). For basin-scale (5°×5° at 10'):
            ~900 points — fast. For regional (20°×20° at 1'): ~144,000 points
            — consider coarser resolution or chunking.
        """
        if resolution_arcmin < 1.0:
            logger.warning(f"High resolution {resolution_arcmin}' may be slow. Consider >= 2'.")
        return self.backend.grid(lat_min, lat_max, lon_min, lon_max, resolution_arcmin, date_year)


# ─── Module-level factory ─────────────────────────────────────────────────────

_adapter_instance: IGRFAdapter | None = None


def get_adapter() -> IGRFAdapter:
    """Return the singleton IGRFAdapter instance (live if ppigrf installed)."""
    global _adapter_instance
    if _adapter_instance is None:
        if IGRFAdapter().is_available():
            _adapter_instance = IGRFAdapter(backend=LiveIGRFBackend())
            logger.info("IGRFAdapter: live backend (ppigrf installed)")
        else:
            _adapter_instance = IGRFAdapter(backend=MockIGRFBackend())
            logger.warning("IGRFAdapter: mock backend (ppigrf not installed). Install with: pip install ppigrf")
    return _adapter_instance
