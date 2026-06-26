"""
geox_subsurface_model — Subsurface Modeling (Phase 2)
═════════════════════════════════════════════════════
Absorbs: geox_joint_inversion, geox_gravity_magnetic_forward, geox_mt_forward

Modes: joint_inversion, gravity_magnetic, mt_forward

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations
from typing import Any, Literal

async def geox_subsurface_model(
    mode: Literal["joint_inversion", "gravity_magnetic", "mt_forward"] = "joint_inversion",
    survey_type: str = "gravity",
    easting_m: tuple[float, ...] | None = None,
    northing_m: tuple[float, ...] | None = None,
    prisms: list[dict[str, Any]] | None = None,
    magnetization_a_m: float = 0.0,
    field_declination_deg: float = 0.0,
    field_inclination_deg: float = 0.0,
    layers: list[dict[str, Any]] | None = None,
    frequencies_hz: list[float] | None = None,
    observations: dict[str, Any] | None = None,
    prior: dict[str, Any] | None = None,
    max_iter: int = 50,
    tolerance: float = 0.001,
) -> dict[str, Any]:
    """Unified subsurface modeling — multi-physics inversion, gravity/mag, MT.

    Modes:
      joint_inversion  - Fuse N modalities into one Physics9State per cell
      gravity_magnetic - Gravity/magnetic forward model via HarmonIC
      mt_forward       - 1D CSEM/MT apparent resistivity + phase
    """
    kwargs = locals().copy()
    if mode == "gravity_magnetic":
        from geox_mcp.tools.geophysics_nonseismic import geox_gravity_magnetic_forward as _impl
        return await _impl(**{k: v for k, v in kwargs.items() if k != "mode"})

    if mode == "mt_forward":
        from geox_mcp.tools.multi_physics import geox_mt_forward as _impl
        return await _impl(
            layers=kwargs.get("layers"),
            frequencies_hz=kwargs.get("frequencies_hz"),
        )

    # Default: joint_inversion
    from geox_mcp.tools.multi_physics import geox_joint_inversion as _impl
    return await _impl(
        observations=kwargs.get("observations"),
        prior=kwargs.get("prior"),
        max_iter=kwargs.get("max_iter", 50),
        tolerance=kwargs.get("tolerance", 0.001),
    )
