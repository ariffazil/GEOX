"""
gplates_fetcher.py — Physical Visible Earth: Plate Tectonic Reconstruction.

GPlates Web Service + GPlately — reconstruct geometries through deep time.
Rotation models: Müller 2019, Merdith 2021, Seton 2012, Scotese PALEOMAP.

Modes:
  offline    — GEOX_GPLATES_OFFLINE=1 (default): stub responses, no network
  gws        — GEOX_GPLATES_OFFLINE=0: live GWS REST API (gws.gplates.org)
  pygplates  — pyGPlates installed + rot files: local computation (future)

Source: EarthByte Group (University of Sydney)
URL: https://www.gplates.org
GWS: https://gws.gplates.org
GPlately: https://github.com/GPlates/gplately
License: GPL-2.0 (GPlates), models vary (mostly CC-BY)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.

Forged: 2026-07-03 — P0 GPlates Live Mode (GWS REST)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.gplates")

# ── Constants ─────────────────────────────────────────────────────────────
GPLATES_GWS_BASE = "https://gws.gplates.org"
GPLATES_CITATION = (
    "Müller, R.D. et al. (2022). A global plate model including "
    "mantle-plume driven spreading ridges. Gondwana Research. "
    "GPlates: https://www.gplates.org. GPL-2.0."
)
GPLATELY_CITATION = (
    "Mather, B.R. et al. (2023). Deep time spatio-temporal data analysis "
    "using pyGPlates with PlateTectonicTools and GPlately. "
    "Geoscience Data Journal. doi:10.1002/gdj3.185"
)

# Model name mapping: GEOX → GWS
_MODEL_MAP: dict[str, str] = {
    "Muller2019": "MULLER2019",
    "Muller2022": "MULLER2022",
    "Merdith2021": "MERDITH2021",
    "Scotese2021": "SCOTESE2021",
    "Seton2012": "SETON2012",
    "Cao2024": "CAO2024",
}
_VALID_MODELS: frozenset[str] = frozenset(_MODEL_MAP.keys()) | frozenset(_MODEL_MAP.values())

# Sentinel for "no data" from GWS
_GWS_NODATA = 999.99
_GWS_TIMEOUT = 15  # seconds

# ── Request/Response Models ────────────────────────────────────────────────


class ReconstructionRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    age_ma: float = Field(..., ge=0, le=4100, description="Age in millions of years")
    model: str = Field("Muller2019", description="Muller2019 | Muller2022 | Merdith2021 | Scotese2021 | Seton2012 | Cao2024")


class ReconstructionResult(BaseModel):
    ok: bool
    mode: str
    reconstructed_lat: Optional[float] = None
    reconstructed_lon: Optional[float] = None
    age_ma: Optional[float] = None
    plate_id: Optional[int] = None
    model: str = ""
    source_uri: str = GPLATES_GWS_BASE
    citation: str = GPLATES_CITATION
    fetched_at: str = ""
    note: str = ""


class PlateVelocityRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    age_ma: float = Field(0, ge=0, le=4100)
    model: str = Field("Muller2019")
    delta_t_ma: float = Field(1.0, ge=0.1, le=10.0, description="Time delta for velocity calculation (Myr)")


class PlateVelocityResult(BaseModel):
    ok: bool
    mode: str
    velocity_cm_yr: Optional[float] = None
    azimuth_deg: Optional[float] = None
    lat_rate_cm_yr: Optional[float] = None
    lon_rate_cm_yr: Optional[float] = None
    plate_id: Optional[int] = None
    age_ma: Optional[float] = None
    model: str = ""
    source_uri: str = GPLATES_GWS_BASE
    citation: str = GPLATES_CITATION
    fetched_at: str = ""
    note: str = ""


class PaleoCoastlineRequest(BaseModel):
    age_ma: float = Field(..., ge=0, le=4100)
    model: str = Field("Muller2019")


class PaleoCoastlineResult(BaseModel):
    ok: bool
    mode: str
    coastlines_geojson: dict[str, Any] = {}
    age_ma: Optional[float] = None
    model: str = ""
    source_uri: str = GPLATES_GWS_BASE
    citation: str = GPLATES_CITATION
    fetched_at: str = ""
    note: str = ""


# ── GPlatesFetcher ─────────────────────────────────────────────────────────


class GPlatesFetcher:
    """GPlates tectonic reconstruction fetcher.

    Modes (in order of priority):
      1. pygplates  — pyGPlates + rot files installed (local, no network)
      2. gws        — GWS REST API (network required)
      3. offline    — stub responses (always available)
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or os.environ.get("GEOX_GPLATES_CACHE_DIR", "/root/.cache/geox/gplates"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_GPLATES_OFFLINE", "1") != "0"
        self._pygplates_available = self._check_pygplates()
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        self._cache_ttl = int(os.environ.get("GEOX_GPLATES_CACHE_TTL", "86400"))

    # ── Initialization Helpers ──────────────────────────────────────────

    @staticmethod
    def _check_pygplates() -> bool:
        try:
            import pygplates  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def _resolve_model(model: str) -> str:
        """Map GEOX model name to GWS model name."""
        return _MODEL_MAP.get(model, model.upper())

    # ── Cache Helpers ───────────────────────────────────────────────────

    def _cache_key(self, endpoint: str, params: dict[str, Any]) -> str:
        raw = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _cache_get(self, key: str) -> Optional[dict[str, Any]]:
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
        try:
            data = json.loads(cache_file.read_text())
            age_s = time.time() - data.get("_cached_at", 0)
            if age_s < self._cache_ttl:
                return data
        except (json.JSONDecodeError, OSError):
            pass
        return None

    def _cache_set(self, key: str, data: dict[str, Any]) -> None:
        data["_cached_at"] = time.time()
        cache_file = self.cache_dir / f"{key}.json"
        try:
            cache_file.write_text(json.dumps(data))
        except OSError:
            pass

    # ── GWS API Calls ───────────────────────────────────────────────────

    def _gws_reconstruct(
        self, lon: float, lat: float, age_ma: float, model: str
    ) -> tuple[Optional[float], Optional[float], Optional[int]]:
        """Call GWS reconstruct_points. Returns (lon, lat, plate_id) or (None, None, None)."""
        gws_model = self._resolve_model(model)
        params = {"lon": lon, "lat": lat, "time": age_ma, "model": gws_model}
        cache_key = self._cache_key("reconstruct", params)
        cached = self._cache_get(cache_key)
        if cached:
            return cached.get("lon"), cached.get("lat"), cached.get("plate_id")

        try:
            url = f"{GPLATES_GWS_BASE}/reconstruct/reconstruct_points"
            resp = self._session.get(url, params=params, timeout=_GWS_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            coords = data.get("coordinates", [[]])
            if coords and coords[0]:
                r_lon, r_lat = coords[0][0], coords[0][1]
                if abs(r_lon - _GWS_NODATA) < 0.01 or abs(r_lat - _GWS_NODATA) < 0.01:
                    # GWS returns (999.99, 999.99) for no data
                    self._cache_set(cache_key, {"lon": None, "lat": None, "plate_id": None})
                    return None, None, None
                plate_id = data.get("plate_id")
                self._cache_set(cache_key, {"lon": r_lon, "lat": r_lat, "plate_id": plate_id})
                return r_lon, r_lat, plate_id
        except requests.RequestException as e:
            logger.warning(f"GWS reconstruct failed: {e}")
        return None, None, None

    def _gws_coastlines(self, age_ma: float, model: str) -> Optional[dict[str, Any]]:
        """Call GWS reconstruct/coastlines. Returns GeoJSON feature collection or None."""
        gws_model = self._resolve_model(model)
        params = {"time": age_ma, "model": gws_model}
        cache_key = self._cache_key("coastlines", params)
        cached = self._cache_get(cache_key)
        if cached:
            return cached.get("geojson")

        try:
            url = f"{GPLATES_GWS_BASE}/reconstruct/coastlines/"
            resp = self._session.get(url, params=params, timeout=_GWS_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            self._cache_set(cache_key, {"geojson": data})
            return data
        except requests.RequestException as e:
            logger.warning(f"GWS coastlines failed: {e}")
        return None

    # ── Public API ──────────────────────────────────────────────────────

    def reconstruct(self, req: ReconstructionRequest) -> ReconstructionResult:
        """Reconstruct a point to its paleo-position at age_ma."""
        now = datetime.now(timezone.utc).isoformat()

        # ── pyGPlates local mode ─────────────────────────────────
        if self._pygplates_available and not self._offline:
            return self._reconstruct_pygplates(req, now)

        # ── GWS REST mode ─────────────────────────────────────────
        if not self._offline:
            r_lon, r_lat, plate_id = self._gws_reconstruct(
                lon=req.longitude,
                lat=req.latitude,
                age_ma=req.age_ma,
                model=req.model,
            )
            if r_lon is not None and r_lat is not None:
                return ReconstructionResult(
                    ok=True,
                    mode="gws_live",
                    reconstructed_lat=r_lat,
                    reconstructed_lon=r_lon,
                    age_ma=req.age_ma,
                    plate_id=plate_id,
                    model=req.model,
                    source_uri=GPLATES_GWS_BASE,
                    citation=GPLATES_CITATION,
                    fetched_at=now,
                    note=f"GWS {self._resolve_model(req.model)} model, live reconstruction.",
                )
            # GWS returned no data — try other models
            return ReconstructionResult(
                ok=False,
                mode="gws_nodata",
                reconstructed_lat=None,
                reconstructed_lon=None,
                age_ma=req.age_ma,
                plate_id=None,
                model=req.model,
                source_uri=GPLATES_GWS_BASE,
                citation=GPLATES_CITATION,
                fetched_at=now,
                note=f"GWS returned no data for age={req.age_ma} Ma with model {req.model}. Point may be outside model coverage.",
            )

        # ── Offline stub mode ─────────────────────────────────────
        return ReconstructionResult(
            ok=True,
            mode="offline_stub",
            reconstructed_lat=req.latitude * 0.9,  # stub rotation
            reconstructed_lon=req.longitude + req.age_ma * 0.05,
            age_ma=req.age_ma,
            plate_id=101,
            model=req.model,
            source_uri=GPLATES_GWS_BASE,
            citation=GPLATES_CITATION,
            fetched_at=now,
            note="Offline stub. Set GEOX_GPLATES_OFFLINE=0 for live GWS reconstruction.",
        )

    def _reconstruct_pygplates(self, req: ReconstructionRequest, now: str) -> ReconstructionResult:
        """pyGPlates local reconstruction. Stub — requires rot files."""
        return ReconstructionResult(
            ok=False,
            mode="pygplates",
            note="pyGPlates installed but no rotation files loaded. Set GEOX_GPLATES_ROT_DIR to directory containing .rot files.",
            fetched_at=now,
        )

    def velocity(self, req: PlateVelocityRequest) -> PlateVelocityResult:
        """Compute plate velocity at a point by finite-difference of two reconstructions."""
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return PlateVelocityResult(
                ok=True,
                mode="offline_stub",
                velocity_cm_yr=2.5,
                azimuth_deg=45.0,
                plate_id=101,
                age_ma=req.age_ma,
                model=req.model,
                source_uri=GPLATES_GWS_BASE,
                citation=GPLATES_CITATION,
                fetched_at=now,
                note="Offline stub. Set GEOX_GPLATES_OFFLINE=0 for live velocity.",
            )

        # Compute velocity via finite-difference of two close reconstructions
        dt = req.delta_t_ma
        # Ensure t1 >= 0 (GWS rejects negative ages)
        t1 = max(0.0, req.age_ma - dt / 2)
        t2 = req.age_ma + dt / 2
        if t1 >= t2:
            t1 = 0.0
            t2 = dt

        r1_lon, r1_lat, _ = self._gws_reconstruct(
            lon=req.longitude,
            lat=req.latitude,
            age_ma=t1,
            model=req.model,
        )
        r2_lon, r2_lat, _ = self._gws_reconstruct(
            lon=req.longitude,
            lat=req.latitude,
            age_ma=t2,
            model=req.model,
        )

        if r1_lon is None or r2_lon is None or r1_lat is None or r2_lat is None:
            return PlateVelocityResult(
                ok=False,
                mode="gws_nodata",
                age_ma=req.age_ma,
                model=req.model,
                source_uri=GPLATES_GWS_BASE,
                citation=GPLATES_CITATION,
                fetched_at=now,
                note=f"GWS returned no data for velocity at age={req.age_ma} Ma.",
            )

        # Simple finite-difference velocity (all values type-narrowed above)
        import math

        _r1_lon: float = r1_lon
        _r2_lon: float = r2_lon
        _r1_lat: float = r1_lat
        _r2_lat: float = r2_lat
        dlon = _r2_lon - _r1_lon
        dlat = _r2_lat - _r1_lat
        # Convert degrees to cm (approximate: 1° ≈ 111.32 km at equator)
        km_per_deg_lat = 111.32
        km_per_deg_lon = 111.32 * math.cos(math.radians((r1_lat + r2_lat) / 2))
        dx_km = dlon * km_per_deg_lon
        dy_km = dlat * km_per_deg_lat
        distance_km = math.sqrt(dx_km**2 + dy_km**2)
        velocity_cm_yr = (distance_km * 1e5) / (dt * 1e6)  # km/Myr → cm/yr
        azimuth_deg = (math.degrees(math.atan2(dx_km, dy_km)) + 360) % 360

        return PlateVelocityResult(
            ok=True,
            mode="gws_finite_difference",
            velocity_cm_yr=round(velocity_cm_yr, 3),
            azimuth_deg=round(azimuth_deg, 1),
            lat_rate_cm_yr=round(dlat * 111.32 * 1e5 / (dt * 1e6), 4),
            lon_rate_cm_yr=round(dlon * km_per_deg_lon * 1e5 / (dt * 1e6), 4),
            plate_id=None,
            age_ma=req.age_ma,
            model=req.model,
            source_uri=GPLATES_GWS_BASE,
            citation=GPLATES_CITATION,
            fetched_at=now,
            note=f"Finite-difference velocity over Δt={dt} Myr via GWS {self._resolve_model(req.model)}.",
        )

    def paleocoastlines(self, req: PaleoCoastlineRequest) -> PaleoCoastlineResult:
        """Fetch paleo-coastlines for a given age."""
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return PaleoCoastlineResult(
                ok=True,
                mode="offline_stub",
                age_ma=req.age_ma,
                model=req.model,
                source_uri=GPLATES_GWS_BASE,
                citation=GPLATES_CITATION,
                fetched_at=now,
                note="Offline stub. Set GEOX_GPLATES_OFFLINE=0 for live paleogeography.",
            )

        geojson = self._gws_coastlines(req.age_ma, req.model)
        if geojson:
            return PaleoCoastlineResult(
                ok=True,
                mode="gws_live",
                coastlines_geojson=geojson,
                age_ma=req.age_ma,
                model=req.model,
                source_uri=GPLATES_GWS_BASE,
                citation=GPLATES_CITATION,
                fetched_at=now,
                note=f"GWS {self._resolve_model(req.model)} model coastlines at {req.age_ma} Ma.",
            )
        return PaleoCoastlineResult(
            ok=False,
            mode="gws_failed",
            age_ma=req.age_ma,
            model=req.model,
            source_uri=GPLATES_GWS_BASE,
            citation=GPLATES_CITATION,
            fetched_at=now,
            note=f"GWS coastlines failed for age={req.age_ma} Ma.",
        )

    def available_models(self) -> list[str]:
        """Return list of available plate models (GEOX canonical names)."""
        return sorted(_MODEL_MAP.keys())

    def mode(self) -> str:
        """Return current operating mode."""
        if self._pygplates_available:
            return "pygplates"
        if not self._offline:
            return "gws"
        return "offline"


# ── Convenience functions ──────────────────────────────────────────────────


def reconstruct_point(lat: float, lon: float, age_ma: float, model: str = "Muller2019") -> ReconstructionResult:
    """One-shot point reconstruction."""
    fetcher = GPlatesFetcher()
    return fetcher.reconstruct(ReconstructionRequest(latitude=lat, longitude=lon, age_ma=age_ma, model=model))


def get_velocity(lat: float, lon: float, age_ma: float = 0, model: str = "Muller2019") -> PlateVelocityResult:
    """One-shot velocity query."""
    fetcher = GPlatesFetcher()
    return fetcher.velocity(PlateVelocityRequest(latitude=lat, longitude=lon, age_ma=age_ma, model=model))


__all__ = [
    "GPlatesFetcher",
    "ReconstructionRequest",
    "ReconstructionResult",
    "PlateVelocityRequest",
    "PlateVelocityResult",
    "PaleoCoastlineRequest",
    "PaleoCoastlineResult",
    "reconstruct_point",
    "get_velocity",
    "GPLATES_GWS_BASE",
    "GPLATES_CITATION",
    "GPLATELY_CITATION",
]
