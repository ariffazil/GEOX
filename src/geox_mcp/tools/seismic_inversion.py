"""
seismic_inversion.py — MCP wrapper for W13+ PINN seismic inversion.

W13+ forge: constitutional MCP surface for 1D post-stack seismic inversion.

DITEMPA BUKAN DIBEI — the impedance is forged, not given.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from geox_core.seismic.pinn_inversion import (
    SeismicInversionRequest,
    pinn_invert,
)


class SeismicInversionRequestSchema(BaseModel):
    reflectivity: tuple[float, ...] = Field(default_factory=tuple)
    sample_interval_s: float = 0.002
    initial_impedance: float = 7.0e6
    depth_top_m: float = 0.0
    resistivity_ohm_m: tuple[float, ...] | None = None
    vp_min: float = 1500.0
    vp_max: float = 6000.0
    rho_min: float = 1000.0
    rho_max: float = 5000.0


class SeismicInversionResponse(BaseModel):
    ok: bool
    tool: str = "geox_seismic_inversion"
    result: dict | None = None
    error: str | None = None


async def geox_seismic_inversion(
    request: SeismicInversionRequestSchema,
) -> SeismicInversionResponse:
    """Constitutional MCP tool: 1D post-stack seismic inversion under PINN-style physics constraints.

    Recovers acoustic impedance, Vp, density, with Faust + Gardner priors.
    """
    try:
        req = SeismicInversionRequest(
            reflectivity=request.reflectivity,
            sample_interval_s=request.sample_interval_s,
            initial_impedance=request.initial_impedance,
            depth_top_m=request.depth_top_m,
            resistivity_ohm_m=request.resistivity_ohm_m,
            vp_min=request.vp_min,
            vp_max=request.vp_max,
            rho_min=request.rho_min,
            rho_max=request.rho_max,
        )
        result = pinn_invert(req)
        if not result["ok"]:
            return SeismicInversionResponse(ok=False, error=result.get("error", "pinn_failed"))
        return SeismicInversionResponse(ok=True, result=result)
    except Exception as e:
        return SeismicInversionResponse(ok=False, error=str(e))


__all__ = [
    "SeismicInversionRequestSchema",
    "SeismicInversionResponse",
    "geox_seismic_inversion",
]
