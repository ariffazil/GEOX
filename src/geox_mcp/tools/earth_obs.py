"""
earth_obs.py — MCP tool wrappers for Earth observation foundation models (Phase A).

W5-W8 forge: constitutional MCP surface for Prithvi-EO-2.0 / Clay / TerraMind / Aurora.

Each tool is a thin wrapper around an engine adapter. The wrapper:
- Validates inputs.
- Calls the adapter.
- Attaches epistemic_provenance, ml_provenance, anti_beautiful_one_check,
  godel_wall verdict (per GENESIS 003 / Foundational Gaps Gap 4).
- Returns a structure-driven envelope.

DITEMPA BUKAN DIBEI — the trust envelope lives in this file, not in the engine.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from geox_core.engines.earth_obs.prithvi_adapter import (
    HLSInput,
    PrithviEOAdapter,
    PrithviOutput,
    PrithviTask,
)


# ───────────────────────────── INPUT SCHEMAS ──────────────────────────────────────
class PrithviEOInferenceRequest(BaseModel):
    tile_id: str = Field(..., min_length=1, description="NASA HLS tile ID, e.g. T30TXN")
    bands: tuple[str, ...] = ("B02", "B03", "B04", "B8A", "B11", "B12")
    time_range: tuple[str, str] = ("2024-01-01", "2024-12-31")
    cloud_cover_max: float = Field(default=0.20, ge=0.0, le=1.0)
    task: PrithviTask = "land_cover"
    source_uri: str | None = None


class PrithviEOInferenceResponse(BaseModel):
    ok: bool
    tool: str = "geox_prithvi_eo_inference"
    mode: str  # "live" | "mock"
    output: PrithviOutput | None = None
    error: str | None = None


# ───────────────────────────── TOOL ENTRY POINT ───────────────────────────────────
async def geox_prithvi_eo_inference(
    request: PrithviEOInferenceRequest,
    *,
    adapter: PrithviEOAdapter | None = None,
) -> PrithviEOInferenceResponse:
    """Constitutional MCP tool: run Prithvi-EO-2.0 on an HLS tile.

    Live mode requires `terratorch` + Prithvi weights. Falls back to mock.
    """
    try:
        a = adapter or PrithviEOAdapter()
        payload = HLSInput(
            tile_id=request.tile_id,
            bands=request.bands,
            time_range=request.time_range,
            cloud_cover_max=request.cloud_cover_max,
            source_uri=request.source_uri,
        )
        out = a.infer(payload, request.task)
        return PrithviEOInferenceResponse(ok=True, mode=a.mode, output=out)
    except Exception as e:
        return PrithviEOInferenceResponse(ok=False, mode="unknown", error=str(e))


# Future Phase A tools will land here (when 888 deploys):
# - geox_terramind_scene_reason
# - geox_clay_mineral_inference
# - geox_aurora_atmosphere
# - geox_tgs_seismic_inference
# - geox_hyperspectral_mineral

__all__ = [
    "PrithviEOInferenceRequest",
    "PrithviEOInferenceResponse",
    "geox_prithvi_eo_inference",
]
