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


# Physics13 fields from_raw_dict() fills with defaults when absent (rho/vp/vs are required above).
_OPTIONAL_STATE_FIELDS = ("rho_e", "chi", "k", "P", "T", "phi", "epsilon", "delta", "gamma")


def _grade_supplied(s: Physics13State, supplied: dict) -> tuple[str, list[str]]:
    """Physics13State.grade(), but only over bounds the caller actually supplied.

    A defaulted phi (0.2) always sits inside 0.02-0.45, so grading it would turn a
    default into evidence. Returns (grade, fields_checked).
    """
    checks = [("vp", 1500 <= s.vp <= 6000), ("rho", 1000 <= s.rho <= 5000)]
    if "phi" in supplied:
        checks.append(("phi", 0.02 <= s.phi <= 0.45))
    grade = "AAA" if all(ok for _, ok in checks) else "RAW"
    return grade, [name for name, _ in checks]


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

    # Hard physical input validation (natural law gate)
    try:
        vp_val = float(state["vp"])
        vs_val = float(state["vs"])
        rho_val = float(state["rho"])
    except (ValueError, TypeError) as e:
        return GeomechanicsResponse(
            ok=False,
            result={"grade": "REJECTED_UNPHYSICAL"},
            error=f"PHYSICS_GUARD_VIOLATION: vp, vs, and rho must be numeric: {e}",
        )

    if vp_val <= 0 or vs_val <= 0 or rho_val <= 0:
        return GeomechanicsResponse(
            ok=False,
            result={"grade": "REJECTED_UNPHYSICAL"},
            error=f"PHYSICS_GUARD_VIOLATION: vp ({vp_val}), vs ({vs_val}), and rho ({rho_val}) must all be positive.",
        )

    if vs_val >= vp_val:
        return GeomechanicsResponse(
            ok=False,
            result={"grade": "REJECTED_UNPHYSICAL"},
            error=f"PHYSICS_GUARD_VIOLATION: vs ({vs_val}) >= vp ({vp_val}) is physically impossible for elastic rocks (violates positive bulk modulus and strain energy constraints).",
        )

    try:
        # A1 fix: from_raw_dict() handles partial/mixed-type dicts gracefully.
        # T1 (2026-11-24): pass the alias-NORMALISED dict. Passing request.state
        # validated vp_m_s=4000 above and then silently computed with vp=3000.
        s = Physics13State.from_raw_dict(state)
        derived: dict[str, float | None] = dict(forward_physics9(s))

        # Which Physics13 fields were filled by from_raw_dict defaults, not the caller.
        defaults_applied = [f for f in _OPTIONAL_STATE_FIELDS if f not in state]
        # Derived scalars that depend on a defaulted input are not evidence — null them.
        if "k" in defaults_applied or "rho" not in state:
            derived["thermal_diff"] = None
        if "phi" in defaults_applied or "P" in defaults_applied:
            derived["fatigue_proxy"] = None

        # Sanity-check derived moduli against classical bounds
        sanity = []
        if derived["nu"] < 0.0 or derived["nu"] > 0.5:
            sanity.append("poisson_ratio_out_of_bounds")
        if derived["K_GPa"] <= 0:
            sanity.append("bulk_modulus_non_positive")
        if derived["G_GPa"] <= 0:
            sanity.append("shear_modulus_non_positive")
        if derived["E_GPa"] <= 0:
            sanity.append("young_modulus_non_positive")

        if sanity:
            return GeomechanicsResponse(
                ok=False,
                result={
                    "input_state": s.to_dict(),
                    "derived": {},
                    "sanity_flags": sanity,
                    "grade": "REJECTED_UNPHYSICAL",
                },
                error=f"PHYSICS_GUARD_VIOLATION: derived elastic properties violate physical bounds: {sanity}",
            )

        grade, grade_basis = _grade_supplied(s, state)
        result = {
            "input_state": s.to_dict(),
            "derived": derived,
            "moduli": {k: derived[k] for k in ("K_GPa", "G_GPa", "E_GPa", "nu")},
            "defaults_applied": defaults_applied,
            "sanity_flags": sanity,
            "grade": grade,
            "grade_basis": grade_basis,
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
                "state": "KNOWN" if not sanity and grade == "AAA" else "UNDECIDABLE_YET",
                "reason": (
                    "Physics9 bounds satisfied + sanity OK."
                    if not sanity and grade == "AAA"
                    else f"Sanity flags: {sanity} or grade {grade}"
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
