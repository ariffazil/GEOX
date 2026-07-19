"""
surface_first.py — Surface-First Engine (Physics-First)
=========================================================

Generates erosion, flooding, MFS, ravinement, and truncation surfaces
from accommodation simulation output.

These surfaces are REAL, MAPPABLE, FALSIFIABLE.
They are Sloss's physics, not Exxon's taxonomy.

Replaces: the concept of "systems tracts" with actual surfaces.
A surface is a physical object. A systems tract is a cartoon.

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged: 2026-07-03 — the extinction event.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from .accommodation import (
    AccommodationResult,
    AccommodationStep,
    StackingPattern,
    SurfaceType,
)

# ═══════════════════════════════════════════════════════════════════════════
# Surface Types — the REAL objects of stratigraphy
# ═══════════════════════════════════════════════════════════════════════════


class GeometryType(StrEnum):
    """Geometric relationships between surfaces and strata."""

    ONLAP = "onlap"  # strata terminate landward against a surface
    DOWNLAP = "downlap"  # strata terminate seaward against a surface
    TOPLAP = "toplap"  # strata terminate at their top (progradation)
    TRUNCATION = "truncation"  # strata are cut off (erosion)
    CONCORDANT = "concordant"  # strata parallel to surface


class StratSurface(BaseModel):
    """A physically-generated stratigraphic surface.

    This is a REAL object — not an interpretation label.
    It has a type, an age, a geometry, and evidence requirements.
    """

    surface_id: str = Field(..., description="Unique surface identifier")
    surface_type: SurfaceType = Field(..., description="Physical surface type")
    age_ma: float = Field(..., ge=0.0, description="Age of the surface (Ma)")
    geometry: GeometryType = Field(default=GeometryType.CONCORDANT)
    water_depth_m: float = Field(default=0.0, description="Water depth at formation (m)")
    erosion_m: float = Field(default=0.0, description="Erosion magnitude (m)")
    accommodation_change_m: float = Field(
        default=0.0,
        description="ΔA — accommodation change that formed this surface (m)",
    )
    is_key_surface: bool = Field(
        default=False,
        description="Whether this is a key mappable surface (SB, MFS, MRS)",
    )
    correlative_extent_km: float | None = Field(
        default=None,
        description="Estimated lateral extent (km). Sloss-scale = 1000s km",
    )
    evidence_required: list[str] = Field(
        default_factory=list,
        description="What evidence is needed to confirm this surface",
    )
    confidence: float = Field(default=0.75, ge=0.0, le=0.90)


class DepositionalPackage(BaseModel):
    """A package of sediment between two surfaces.

    This is what Exxon calls a "systems tract" but without the label.
    It's just the sediment between two physically-defined surfaces.
    """

    package_id: str = Field(..., description="Unique package identifier")
    top_surface_id: str = Field(..., description="Younger bounding surface")
    base_surface_id: str = Field(..., description="Older bounding surface")
    age_top_ma: float = Field(..., description="Top age (Ma)")
    age_base_ma: float = Field(..., description="Base age (Ma)")
    thickness_m: float = Field(..., description="Package thickness (m)")
    stacking_pattern: StackingPattern = Field(..., description="Dominant stacking pattern")
    water_depth_top_m: float = Field(default=0.0)
    water_depth_base_m: float = Field(default=0.0)
    dominant_lithology: str = Field(default="unknown")
    # NOT a systems tract label. Just physics.
    accommodation_trend: str = Field(
        default="",
        description="Rising/falling/stable accommodation",
    )


class SurfaceFirstResult(BaseModel):
    """Output of the surface-first engine."""

    surfaces: list[StratSurface] = Field(..., description="All generated surfaces")
    packages: list[DepositionalPackage] = Field(..., description="Packages between surfaces")
    key_surfaces: list[StratSurface] = Field(
        default_factory=list,
        description="Key mappable surfaces (SB, MFS, MRS)",
    )
    num_erosion_surfaces: int = Field(default=0)
    num_flooding_surfaces: int = Field(default=0)
    num_mfs: int = Field(default=0)
    num_sequence_boundaries: int = Field(default=0)
    emergent_architecture: str = Field(
        default="",
        description="Summary of the emergent stratigraphic architecture",
    )
    confidence: float = Field(default=0.75, ge=0.0, le=0.90)
    epistemic_label: str = Field(default="DER")
    note: str = Field(default="")


# ═══════════════════════════════════════════════════════════════════════════
# Surface Generation — Physics-Driven
# ═══════════════════════════════════════════════════════════════════════════


def _infer_geometry(
    step: AccommodationStep,
    prev_step: AccommodationStep | None,
) -> GeometryType:
    """Infer geometric relationship from physics, not rules."""
    if step.surface_type == SurfaceType.EROSION:
        return GeometryType.TRUNCATION
    if step.surface_type == SurfaceType.SEQUENCE_BOUNDARY:
        return GeometryType.TRUNCATION
    if step.surface_type == SurfaceType.MAXIMUM_FLOODING:
        return GeometryType.DOWNLAP  # strata downlap onto MFS
    if step.surface_type == SurfaceType.FLOODING:
        return GeometryType.ONLAP  # strata onlap onto flooding surface
    if step.stacking_pattern == StackingPattern.PROGRADATIONAL:
        return GeometryType.TOPLAP  # progradation = toplap at top
    return GeometryType.CONCORDANT


def _accommodation_change(
    step: AccommodationStep,
    prev_step: AccommodationStep | None,
) -> float:
    """Compute ΔA (accommodation change) between steps."""
    if prev_step is None:
        return 0.0
    return step.total_accommodation_m - prev_step.total_accommodation_m


def generate_surfaces(
    accommodation: AccommodationResult,
    min_surface_magnitude_m: float = 0.5,
) -> SurfaceFirstResult:
    """Generate stratigraphic surfaces from accommodation simulation.

    Surfaces EMERGE from physics:
    - Erosion surfaces where accommodation drops below sediment
    - Flooding surfaces where water depth increases
    - MFS at maximum water depth
    - Sequence boundaries at major erosion events
    - Ravinement at flooding + erosion combo

    This is Sloss's physics, not Exxon's taxonomy.

    Parameters
    ----------
    accommodation : AccommodationResult
        Output from simulate_accommodation().
    min_surface_magnitude_m : float
        Minimum accommodation change to generate a surface (m).
        Filters noise from real surfaces.
    """
    surfaces: list[StratSurface] = []
    packages: list[DepositionalPackage] = []
    prev_step: AccommodationStep | None = None
    surface_counter = 0

    steps = accommodation.steps
    if not steps:
        return SurfaceFirstResult(
            surfaces=[],
            packages=[],
            note="Empty accommodation result — no surfaces generated",
        )

    for _i, step in enumerate(steps):
        delta_a = _accommodation_change(step, prev_step)

        # Generate surface if significant
        if step.surface_type != SurfaceType.CONFORMABLE:
            # Only generate if magnitude exceeds threshold
            if abs(delta_a) >= min_surface_magnitude_m or step.erosion_m >= min_surface_magnitude_m:
                surface_counter += 1
                geo = _infer_geometry(step, prev_step)
                is_key = step.is_sequence_boundary or step.is_maximum_flooding

                surfaces.append(
                    StratSurface(
                        surface_id=f"S{surface_counter:03d}",
                        surface_type=step.surface_type,
                        age_ma=step.time_ma,
                        geometry=geo,
                        water_depth_m=step.water_depth_m,
                        erosion_m=step.erosion_m,
                        accommodation_change_m=round(delta_a, 1),
                        is_key_surface=is_key,
                        evidence_required=_evidence_for_surface(step.surface_type),
                        confidence=0.75,
                    )
                )

        # Generate package between surfaces
        if prev_step is not None and surface_counter >= 2:
            # Find the two most recent surfaces
            top_id = surfaces[-1].surface_id if surfaces else "S000"
            base_id = surfaces[-2].surface_id if len(surfaces) >= 2 else "S000"

            # Only create package if surfaces are different
            if top_id != base_id:
                thickness = abs(step.sediment_thickness_m - prev_step.sediment_thickness_m)
                if thickness > 0.1:
                    trend = "rising" if delta_a > 0 else "falling" if delta_a < 0 else "stable"
                    packages.append(
                        DepositionalPackage(
                            package_id=f"P{len(packages) + 1:03d}",
                            top_surface_id=top_id,
                            base_surface_id=base_id,
                            age_top_ma=step.time_ma,
                            age_base_ma=prev_step.time_ma,
                            thickness_m=round(thickness, 1),
                            stacking_pattern=step.stacking_pattern,
                            water_depth_top_m=step.water_depth_m,
                            water_depth_base_m=prev_step.water_depth_m,
                            accommodation_trend=trend,
                        )
                    )

        prev_step = step

    # Key surfaces
    key_surfaces = [s for s in surfaces if s.is_key_surface]

    # Emergent architecture summary
    arch_parts = []
    if accommodation.num_sequence_boundaries > 0:
        arch_parts.append(f"{accommodation.num_sequence_boundaries} sequence boundaries")
    if accommodation.num_flooding_surfaces > 0:
        arch_parts.append(f"{accommodation.num_flooding_surfaces} flooding surfaces")
    if accommodation.num_maximum_flooding > 0:
        arch_parts.append(f"{accommodation.num_maximum_flooding} MFS")
    if accommodation.emergent_stacking:
        arch_parts.append(f"stacking: {'→'.join(accommodation.emergent_stacking)}")
    arch_summary = ", ".join(arch_parts) if arch_parts else "conformable deposition"

    return SurfaceFirstResult(
        surfaces=surfaces,
        packages=packages,
        key_surfaces=key_surfaces,
        num_erosion_surfaces=accommodation.num_erosion_surfaces,
        num_flooding_surfaces=accommodation.num_flooding_surfaces,
        num_mfs=accommodation.num_maximum_flooding,
        num_sequence_boundaries=accommodation.num_sequence_boundaries,
        emergent_architecture=arch_summary,
        confidence=0.75,
        epistemic_label="DER",
        note=(
            f"Surface-first: {len(surfaces)} surfaces, {len(packages)} packages generated "
            f"from physics. No systems-tract labels assigned. Architecture emerged from "
            f"subsididence + eustasy + sediment."
        ),
    )


def _evidence_for_surface(surface_type: SurfaceType) -> list[str]:
    """What evidence is needed to confirm each surface type."""
    base = ["seismic_reflector", "well_log_marker"]
    if surface_type == SurfaceType.EROSION:
        return base + ["truncation_geometry", "paleosol_evidence", "incised_valley"]
    if surface_type == SurfaceType.SEQUENCE_BOUNDARY:
        return base + ["subaerial_unconformity", "karst", "incised_valley", "forced_regression"]
    if surface_type == SurfaceType.FLOODING:
        return base + ["deepening_fauna", "retrogradational_stacking", "condensed_section"]
    if surface_type == SurfaceType.MAXIMUM_FLOODING:
        return base + ["peak_gamma_ray", "condensed_fauna", "downlap_geometry"]
    if surface_type == SurfaceType.RAVINEMENT:
        return base + ["lag_deposit", "wave_erosion_geometry"]
    return base


__all__ = [
    "GeometryType",
    "StratSurface",
    "DepositionalPackage",
    "SurfaceFirstResult",
    "generate_surfaces",
]
