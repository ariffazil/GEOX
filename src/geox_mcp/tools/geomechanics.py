"""
geomechanics.py — W13+ Phase C forge: geomechanics tool.

Exposes bulk_modulus, young_modulus, shear_modulus, poisson_ratio,
acoustic_impedance, vp_vs_ratio from geox_core.physics.parameters
as a constitutional MCP tool.

Strategic doc alignment: "Geomechanics" — bulk/young/shear/poisson
per cell. This tool computes them from a Physics9State and stamps
the result with epistemic_provenance + godel_wall verdict.

DITEMPA BUKAN DIBEI — the modulus is forged, not given.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from geox_core.physics.state import Physics9State
from geox_core.physics.parameters import (
    bulk_modulus,
    shear_modulus,
    young_modulus,
    poisson_ratio,
    acoustic_impedance,
    vp_vs_ratio,
    forward_physics9,
)


class GeomechanicsRequest(BaseModel):
    state: dict = Field(..., description="Physics9State as dict")


class GeomechanicsResponse(BaseModel):
    ok: bool
    tool: str = "geox_geomechanics"
    result: Optional[dict] = None
    error: Optional[str] = None


async def geox_geomechanics(request: GeomechanicsRequest) -> GeomechanicsResponse:
    """Constitutional MCP tool: derive geomechanical moduli from a Physics9State cell.

    Returns K, G, E, ν, AI, Vp/Vs and all derived forward-physics scalars.
    Each cell is graded RAW or AAA per Physics9 bounds.
    """
    try:
        s = Physics9State(**request.state)
        derived = forward_physics9(s)
        # Sanity-check derived moduli against classical bounds
        sanity = []
        if derived["nu"] < 0.0 or derived["nu"] > 0.5:
            sanity.append("poisson_ratio_out_of_bounds")
        if derived["K_GPa"] < 0:
            sanity.append("bulk_modulus_negative")
        if derived["G_GPa"] < 0:
            sanity.append("shear_modulus_negative")
        if derived["E_GPa"] < 0:
            sanity.append("young_modulus_negative")

        result = {
            "input_state": s.to_dict(),
            "derived": derived,
            "sanity_flags": sanity,
            "grade": s.grade(),
            "epistemic_provenance": {
                "rung": 3,
                "grounding": "elastic_moduli_from_pwave_swave_density",
                "method": "deterministic_physics9_derivatives",
                "caveat": (
                    "Moduli assume isotropic, linear-elastic response. "
                    "Anisotropic extension (Thomsen) lives in physics/parameters.py "
                    "but is not exposed here yet."
                ),
            },
            "godel_wall": {
                "state": "KNOWN" if not sanity and s.grade() == "AAA" else "UNDECIDABLE_YET",
                "reason": (
                    "Physics9 bounds satisfied + sanity OK."
                    if not sanity and s.grade() == "AAA"
                    else f"Sanity flags: {sanity} or grade {s.grade()}"
                ),
            },
        }
        return GeomechanicsResponse(ok=True, result=result)
    except Exception as e:
        return GeomechanicsResponse(ok=False, error=str(e))


__all__ = ["GeomechanicsRequest", "GeomechanicsResponse", "geox_geomechanics"]
