"""
geox_geomechanics — Geomechanics (Phase 2)
══════════════════════════════════════════
Absorbs: geox_geomechanics, geox_blockspace_resolution_tool, geox_coord_transform_tool

Modes: derive_moduli, blockspace, coord_transform, stress_polygon

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations
import math
from typing import Any, Literal


def _compute_stress_polygon(
    depth_m: float | None = None,
    sv_mpa: float | None = None,
    pp_mpa: float = 10.0,
    friction_coefficient: float = 0.6,
    avg_density_kg_m3: float = 2300.0,
    water_depth_m: float = 0.0,
) -> dict[str, Any]:
    """Zoback (2010) frictional stress polygon.

    Bounds Shmin and SHmax from Andersonian faulting theory using
    the coefficient of friction μ to define the stress ratios at
    which faults are critically stressed.

    Physics:
      σ_ratio = (√(μ² + 1) + μ)²   — frictional limit ratio
      Normal faulting:  Shmin_min = (Sv - Pp) / σ_ratio + Pp
      Reverse faulting: SHmax_max = (Sv - Pp) · σ_ratio + Pp
      Strike-slip:      both bounds active

    Returns vertices A (hydrostatic) → B (normal) → C (strike-slip) → D (reverse)
    forming the stress polygon in (Sh, SH) space.

    F2 TRUTH: All values are DERIVED from textbook rock mechanics.
    F7 HUMILITY: Confidence cap 0.90 — lab μ may differ from in-situ.
    """
    # Compute Sv if not provided
    if sv_mpa is None:
        if depth_m is None:
            return {"ok": False, "error": "Either depth_m or sv_mpa is required"}
        if water_depth_m > 0:
            sv_mpa = (1025.0 * 9.81 * water_depth_m + avg_density_kg_m3 * 9.81 * depth_m) / 1e6
        else:
            sv_mpa = avg_density_kg_m3 * 9.81 * depth_m / 1e6

    sigma_v = sv_mpa - pp_mpa  # effective vertical stress
    if sigma_v < 0:
        return {"ok": False, "error": f"Pore pressure {pp_mpa} MPa exceeds Sv {sv_mpa} MPa — unphysical"}

    mu = friction_coefficient
    n = math.sqrt(mu * mu + 1.0) + mu
    n_sq = n * n  # frictional limit ratio

    # Stress polygon vertices (Sh, SH)
    shmin_normal = sigma_v / n_sq + pp_mpa  # normal faulting limit
    shmax_reverse = sigma_v * n_sq + pp_mpa  # reverse faulting limit
    shmin_ss = shmin_normal  # strike-slip lower bound
    shmax_ss = shmax_reverse  # strike-slip upper bound

    return {
        "ok": True,
        "tool": "geox_geomechanics",
        "mode": "stress_polygon",
        "sv_mpa": round(sv_mpa, 2),
        "pp_mpa": round(pp_mpa, 2),
        "sigma_v_effective_mpa": round(sigma_v, 2),
        "friction_coefficient": mu,
        "friction_angle_deg": round(math.degrees(math.atan(mu)), 1),
        "stress_ratio_n_sq": round(n_sq, 4),
        "stress_polygon_vertices": {
            "A_hydrostatic": {"sh_mpa": round(pp_mpa, 2), "sh_max_mpa": round(pp_mpa, 2)},
            "B_normal_limit": {"sh_mpa": round(shmin_normal, 2), "sh_max_mpa": round(sv_mpa, 2)},
            "C_strike_slip": {"sh_mpa": round(shmin_ss, 2), "sh_max_mpa": round(shmax_ss, 2)},
            "D_reverse_limit": {"sh_mpa": round(sv_mpa, 2), "sh_max_mpa": round(shmax_reverse, 2)},
        },
        "epistemic_provenance": {
            "rung": 3,
            "grounding": "zoback_2010_reservoir_geomechanics_andersonian_faulting",
            "method": "deterministic_stress_polygon",
            "caveat": (
                "Assumes isotropic friction. In-situ μ may differ from lab values. "
                "Stress polygon bounds are theoretical limits — real stress states "
                "may lie inside the polygon, not on its edges."
            ),
        },
        "f7_humility": {"confidence_cap": 0.90},
    }


async def geox_geomechanics(
    mode: Literal["derive_moduli", "blockspace", "coord_transform"] = "derive_moduli",
    block_width: float = 1.0,
    block_height: float = 1.0,
    block_length: float = 1.0,
    survey_x_min: float = 0.0,
    survey_x_max: float = 1.0,
    survey_z_min: float = 0.0,
    survey_z_max: float = 1.0,
    survey_y_min: float = 0.0,
    survey_y_max: float = 1.0,
    points: list[dict[str, Any]] | None = None,
    from_space: str = "",
    to_space: str = "",
    x: float = 0.0,
    y: float = 0.0,
    from_crs: str = "",
    to_crs: str = "",
    allow_unknown_crs: bool = False,
    world_p0: list[float] | None = None,
    world_p1: list[float] | None = None,
    world_p2: list[float] | None = None,
    world_p3: list[float] | None = None,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Geomechanics — derive K/G/E/ν/AI, coordinate transforms, block resolution.

    Modes:
      derive_moduli   - K, G, E, ν, AI from Physics13State
      blockspace      - Inline/crossline resolution from block/survey geometry
      coord_transform - CRS reprojection or local affine transform
    """
    kwargs = locals().copy()
    if mode == "blockspace":
        from geox_mcp.tools.paleoscan_forge import geox_blockspace_resolution_tool as _impl

        return await _impl(
            block_width=kwargs.get("block_width", 1),
            block_height=kwargs.get("block_height", 1),
            block_length=kwargs.get("block_length", 1),
            survey_x_min=kwargs.get("survey_x_min", 0),
            survey_x_max=kwargs.get("survey_x_max", 1),
            survey_z_min=kwargs.get("survey_z_min", 0),
            survey_z_max=kwargs.get("survey_z_max", 1),
            survey_y_min=kwargs.get("survey_y_min", 0),
            survey_y_max=kwargs.get("survey_y_max", 1),
        )

    if mode == "coord_transform":
        from geox_mcp.tools.paleoscan_forge import geox_coord_transform_tool as _impl

        return await _impl(
            points=kwargs.get("points"),
            from_space=kwargs.get("from_space"),
            to_space=kwargs.get("to_space"),
            x=kwargs.get("x"),
            y=kwargs.get("y"),
            from_crs=kwargs.get("from_crs"),
            to_crs=kwargs.get("to_crs"),
            **{
                k: v
                for k, v in kwargs.items()
                if k
                in (
                    "allow_unknown_crs",
                    "block_width",
                    "block_height",
                    "block_length",
                    "survey_x_min",
                    "survey_x_max",
                    "survey_z_min",
                    "survey_z_max",
                    "survey_y_min",
                    "survey_y_max",
                    "world_p0",
                    "world_p1",
                    "world_p2",
                    "world_p3",
                )
            },
        )

    # Default: derive_moduli
    from geox_mcp.tools.geomechanics import geox_geomechanics as _impl

    return await _impl(state=kwargs.get("state", {}))
