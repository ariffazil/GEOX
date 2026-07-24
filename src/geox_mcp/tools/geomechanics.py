"""
geomechanics.py — W13+ Phase C forge: geomechanics tool.

Exposes bulk_modulus, young_modulus, shear_modulus, poisson_ratio,
acoustic_impedance, vp_vs_ratio from geox_core.physics.parameters
as a constitutional MCP tool.

Strategic doc alignment: "Geomechanics" — bulk/young/shear/poisson
per cell. This tool computes them from a Physics13State and stamps
the result with epistemic_provenance + godel_wall verdict.

DITEMPA BUKAN DIBEI — the modulus is forged, not given.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.geomechanics")

from geox_core.physics.parameters import (
    compute_buoyancy,
    forward_physics9,
)
from geox_core.physics.state import Physics13State


class GeomechanicsRequest(BaseModel):
    state: dict = Field(..., description="Physics13State as dict — partial fields OK, from_raw_dict() coerces")
    thickness_m: float | None = Field(
        default=None,
        description="Column thickness [m] for buoyancy computation. Not part of 9-dial — pass explicitly.",
    )
    rho_fluid: float | None = Field(
        default=1025.0,
        description="Fluid density [kg/m³] for buoyancy. Default seawater 1025.",
    )


class GeomechanicsResponse(BaseModel):
    ok: bool
    tool: str = "geox_geomechanics"
    result: dict | None = None
    error: str = ""


async def geox_geomechanics(request: GeomechanicsRequest) -> GeomechanicsResponse:
    """Constitutional MCP tool: derive geomechanical moduli from a Physics13State cell.

    Returns K, G, E, ν, AI, Vp/Vs and all derived forward-physics scalars.
    Each cell is graded RAW or AAA per Physics9 bounds.

    A1 fix (2026-06-28): uses Physics13State.from_raw_dict() so callers can pass
    partial/mixed-type dicts without hitting SESSION_REQUIRED.  Buoyancy is
    available when thickness_m is provided.
    """
    # F1 AMANAH: validate input structure before computation
    if not isinstance(request.state, dict):
        return GeomechanicsResponse(ok=False, result={}, error="state must be a dict")

    # SURVIVAL-OF-THE-FITTEST FIX 2026-07-24: alias normalization.
    # Accept common suffix-typed aliases (rho_kg_m3, vp_m_s, vs_m_s) so
    # callers using SI-with-units keys still derive the canonical keys.
    # This is a one-way copy — we do not mutate the caller's dict.
    state = dict(request.state)
    if "rho" not in state and "rho_kg_m3" in state:
        state["rho"] = state["rho_kg_m3"]
    if "vp" not in state and "vp_m_s" in state:
        state["vp"] = state["vp_m_s"]
    if "vs" not in state and "vs_m_s" in state:
        state["vs"] = state["vs_m_s"]

    if not all(k in state for k in ("rho", "vp", "vs")):
        return GeomechanicsResponse(
            ok=False,
            result={},
            error=f"state dict must contain 'rho', 'vp', 'vs' (required Physics9 fields; aliases rho_kg_m3/vp_m_s/vs_m_s accepted). Got: {list(request.state.keys())}",
        )

    try:
        # A1 fix: from_raw_dict() handles partial/mixed-type dicts gracefully
        s = Physics13State.from_raw_dict(request.state)
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

        # A1 fix: optional buoyancy computation (not part of 9-dial, requires thickness)
        if request.thickness_m is not None:
            buoyancy = compute_buoyancy(
                rho_material=s.rho,
                thickness_m=request.thickness_m,
                rho_fluid=request.rho_fluid or 1025.0,
            )
            result["buoyancy"] = buoyancy
            result["epistemic_provenance"]["grounding"] = (
                "elastic_moduli_from_pwave_swave_density + buoyancy_column_from_density_contrast"
            )

        return GeomechanicsResponse(ok=True, result=result)
    except TypeError as e:
        return GeomechanicsResponse(ok=False, result={}, error=f"TYPE_ERROR: {e}")
    except ValueError as e:
        return GeomechanicsResponse(ok=False, result={}, error=f"VALUE_ERROR: {e}")
    except Exception as e:
        logger.exception("geox_geomechanics unexpected error")
        return GeomechanicsResponse(ok=False, result={}, error=f"UNEXPECTED: {e}")


__all__ = ["GeomechanicsRequest", "GeomechanicsResponse", "geox_geomechanics"]
