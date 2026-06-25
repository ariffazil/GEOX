"""
gplates_fetcher.py — Physical Visible Earth: Plate Tectonic Reconstruction.

GPlates Web Service + GPlately — reconstruct geometries through deep time.
Rotation models: Müller 2019/2022, Merdith 2021, Scotese PALEOMAP.

Source: EarthByte Group (University of Sydney)
URL: https://www.gplates.org
GWS: https://gws.gplates.org
GPlately: https://github.com/GPlates/gplately
License: GPL-2.0 (GPlates), models vary (mostly CC-BY)

DITEMPA BUKAN DIBERI — open data is forged through trust envelope.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.io.gplates")

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


class ReconstructionRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    age_ma: float = Field(..., ge=0, le=4100, description="Age in millions of years")
    model: str = Field("Muller2019", description="Muller2019 | Muller2022 | Merdith2021 | Scotese2021")


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
    minlatitude: float = Field(-90, ge=-90, le=90)
    maxlatitude: float = Field(90, ge=-90, le=90)
    minlongitude: float = Field(-180, ge=-360, le=360)
    maxlongitude: float = Field(180, ge=-360, le=360)
    age_ma: float = Field(0, ge=0, le=4100)
    model: str = Field("Muller2019")


class PlateVelocityResult(BaseModel):
    ok: bool
    mode: str
    velocities: list[dict[str, Any]] = []
    count: int = 0
    age_ma: Optional[float] = None
    model: str = ""
    source_uri: str = GPLATES_GWS_BASE
    citation: str = GPLATES_CITATION
    fetched_at: str = ""
    note: str = ""


class GPlatesFetcher:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or os.environ.get(
            "GEOX_GPLATES_CACHE_DIR", "/root/.cache/geox/gplates"
        ))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._offline = os.environ.get("GEOX_GPLATES_OFFLINE", "1") != "0"

    def reconstruct(self, req: ReconstructionRequest) -> ReconstructionResult:
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return ReconstructionResult(
                ok=True, mode="offline_stub",
                reconstructed_lat=req.latitude * 0.9,  # stub rotation
                reconstructed_lon=req.longitude + req.age_ma * 0.05,
                age_ma=req.age_ma, plate_id=101, model=req.model,
                fetched_at=now,
                note="Offline stub. Set GEOX_GPLATES_OFFLINE=0 + install pyGPlates for live reconstruction."
            )
        return ReconstructionResult(ok=False, mode="live", note="Live GPlates requires pyGPlates + GWS.", fetched_at=now)

    def velocities(self, req: PlateVelocityRequest) -> PlateVelocityResult:
        now = datetime.now(timezone.utc).isoformat()
        if self._offline:
            return PlateVelocityResult(
                ok=True, mode="offline_stub",
                velocities=[{"latitude": 0, "longitude": 110, "velocity_cm_yr": 2.5, "azimuth": 45}],
                count=1, age_ma=req.age_ma, model=req.model,
                fetched_at=now, note="Offline stub."
            )
        return PlateVelocityResult(ok=False, mode="live", note="Live requires pyGPlates.", fetched_at=now)
