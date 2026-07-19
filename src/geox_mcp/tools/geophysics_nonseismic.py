"""
geophysics_nonseismic.py — MCP tool wrappers for nonseismic geophysics (Phase B).

W9-W12 forge: constitutional MCP surface for:
- Gravity (Bouguer / free-air) via HarmonIC
- Magnetics (TMI) via HarmonIC
- EMAG2v3 global magnetic anomaly grid
- ICGEM gravity field models

DITEMPA BUKAN DIBEI — nonseismic physics is forged, not given.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from geox_core.engines.geophysics.harmonica_adapter import (
    GravityMagneticInput,
    HarmonICAdapter,
    NonseismicOutput,
    SurveyType,
)
from geox_core.io.emag2_fetcher import (
    EMAG2Fetcher,
    EMAG2FetchResult,
    ICGEMFetcher,
)


# ───────────────────────────── GRAVITY/MAGNETIC FORWARD ───────────────────────────
class GravityMagneticForwardRequest(BaseModel):
    survey_type: SurveyType = "gravity"
    easting_m: tuple[float, ...] = Field(..., min_length=1)
    northing_m: tuple[float, ...] = Field(..., min_length=1)
    prisms: list[dict] = Field(default_factory=list)
    magnetization_a_m: float = 0.0
    field_declination_deg: float = 0.0
    field_inclination_deg: float = 0.0


class GravityMagneticForwardResponse(BaseModel):
    ok: bool
    tool: str = "geox_gravity_magnetic_forward"
    mode: str
    output: NonseismicOutput | None = None
    error: str | None = None


async def geox_gravity_magnetic_forward(
    request: GravityMagneticForwardRequest,
    *,
    adapter: HarmonICAdapter | None = None,
) -> GravityMagneticForwardResponse:
    """Constitutional MCP tool: forward-model gravity or magnetic anomaly grid."""
    try:
        a = adapter or HarmonICAdapter()
        payload = GravityMagneticInput(
            survey_type=request.survey_type,
            easting_m=request.easting_m,
            northing_m=request.northing_m,
            prisms=list(request.prisms),
            magnetization_a_m=request.magnetization_a_m,
            field_declination_deg=request.field_declination_deg,
            field_inclination_deg=request.field_inclination_deg,
        )
        out = a.forward(payload)
        return GravityMagneticForwardResponse(ok=True, mode=a.mode, output=out)
    except Exception as e:
        return GravityMagneticForwardResponse(ok=False, mode="unknown", error=str(e))


# ───────────────────────────── EMAG2v3 GRID FETCH ────────────────────────────────
class EMAG2FetchRequest(BaseModel):
    force: bool = Field(default=False, description="Re-attempt even if cached")


class EMAG2FetchResponse(BaseModel):
    ok: bool
    tool: str = "geox_emag2_ingest"
    result: EMAG2FetchResult | None = None
    error: str | None = None


async def geox_emag2_ingest(
    request: EMAG2FetchRequest,
    *,
    fetcher: EMAG2Fetcher | None = None,
) -> EMAG2FetchResponse:
    """Constitutional MCP tool: fetch EMAG2v3 global magnetic anomaly grid.

    Default mode: offline_stub. Set GEOX_EMAG2_OFFLINE=0 + local file to enable.
    """
    try:
        f = fetcher or EMAG2Fetcher()
        r = f.fetch(force=request.force)
        return EMAG2FetchResponse(ok=r.ok, result=r)
    except Exception as e:
        return EMAG2FetchResponse(ok=False, error=str(e))


# ───────────────────────────── ICGEM MODELS LIST ─────────────────────────────────
class ICGEMListRequest(BaseModel):
    pass


class ICGEMListResponse(BaseModel):
    ok: bool
    tool: str = "geox_icgem_models"
    models: list = Field(default_factory=list)


async def geox_icgem_models(
    request: ICGEMListRequest,
    *,
    fetcher: ICGEMFetcher | None = None,
) -> ICGEMListResponse:
    """Constitutional MCP tool: list ICGEM global gravity field models."""
    f = fetcher or ICGEMFetcher()
    return ICGEMListResponse(ok=True, models=[m.model_dump() for m in f.list_models()])


__all__ = [
    "GravityMagneticForwardRequest",
    "GravityMagneticForwardResponse",
    "geox_gravity_magnetic_forward",
    "EMAG2FetchRequest",
    "EMAG2FetchResponse",
    "geox_emag2_ingest",
    "ICGEMListRequest",
    "ICGEMListResponse",
    "geox_icgem_models",
]
