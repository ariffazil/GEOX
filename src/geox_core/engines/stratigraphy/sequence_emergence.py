"""
sequence_emergence.py — Sequence Emergence Engine (Physics-First)
==================================================================

Sequences EMERGE from accommodation + surfaces + stacking patterns.
They are NOT classified by GR motif rules.

This replaces geox_sequence's infer_seq_strat() — the LST/TST/HST classifier
that Arif correctly identified as "acah-acah pandai."

The EUREKA: Sequence stratigraphy is not a classification system.
It is a physics engine.

Sloss saw this in 1947.
Arif saw it in 2026.
Most geologists still haven't.

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged: 2026-07-03 — the extinction event.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from .accommodation import (
    AccommodationResult,
    StackingPattern,
    SurfaceType,
)
from .surface_first import (
    DepositionalPackage,
    GeometryType,
    StratSurface,
    SurfaceFirstResult,
)

# ═══════════════════════════════════════════════════════════════════════════
# Sequence Scale — from parasequence to Sloss
# ═══════════════════════════════════════════════════════════════════════════


class SequenceScale(StrEnum):
    """Scale of emergent sequence — NOT a classification, a measurement.

    These are TIME scales that emerge from the physics, not labels.
    A Sloss sequence takes 30-60 Myr. A parasequence takes 0.1-1 Myr.
    The scale emerges from the duration between bounding surfaces.
    """

    PARASEQUENCE = "parasequence"  # ~0.1-1 Myr, flooding surface-bounded
    DEPOSITIONAL = "depositional"  # ~1-10 Myr, SB-bounded
    SLOSS = "sloss"  # ~30-60 Myr, major unconformity-bounded


class EmergentSequence(BaseModel):
    """A sequence that EMERGED from physics.

    This is NOT a systems tract assignment. This is a physically-defined
    package of sediment bounded by physically-generated surfaces.
    """

    sequence_id: str = Field(..., description="Unique sequence identifier")
    scale: SequenceScale = Field(..., description="Scale based on duration (emerged, not assigned)")
    age_top_ma: float = Field(..., description="Top age (Ma)")
    age_base_ma: float = Field(..., description="Base age (Ma)")
    duration_myr: float = Field(..., description="Duration (Myr)")
    bounding_surface_top: str = Field(..., description="Top bounding surface ID")
    bounding_surface_base: str = Field(..., description="Base bounding surface ID")
    bounding_type_top: SurfaceType = Field(..., description="Top surface type")
    bounding_type_base: SurfaceType = Field(..., description="Base surface type")
    geometry_top: GeometryType = Field(default=GeometryType.CONCORDANT)
    geometry_base: GeometryType = Field(default=GeometryType.CONCORDANT)
    thickness_m: float = Field(default=0.0, description="Total thickness (m)")
    packages: list[str] = Field(
        default_factory=list,
        description="Package IDs within this sequence",
    )
    stacking_summary: str = Field(
        default="",
        description="Summary of stacking pattern evolution (from physics)",
    )
    accommodation_trend: str = Field(
        default="",
        description="Overall accommodation trend (rising/falling/cyclic)",
    )
    water_depth_range_m: tuple[float, float] = Field(
        default=(0.0, 0.0),
        description="(min, max) water depth during sequence",
    )
    # Resources EMERGE from the architecture, not from labels
    reservoir_potential: str = Field(
        default="unknown",
        description="Reservoir potential based on sand content and stacking",
    )
    seal_potential: str = Field(
        default="unknown",
        description="Seal potential based on flooding surfaces and shales",
    )
    source_potential: str = Field(
        default="unknown",
        description="Source potential based on condensed sections",
    )
    confidence: float = Field(default=0.75, ge=0.0, le=0.90)
    epistemic_label: str = Field(default="DER")


class SequenceEmergenceResult(BaseModel):
    """Output of the sequence emergence engine."""

    sequences: list[EmergentSequence] = Field(
        ...,
        description="Sequences that emerged from physics",
    )
    total_sequences: int = Field(default=0)
    by_scale: dict[str, int] = Field(
        default_factory=dict,
        description="Count of sequences by scale (parasequence/depositional/sloss)",
    )
    key_surfaces_used: list[str] = Field(
        default_factory=list,
        description="Surface IDs that bounded sequences",
    )
    resource_graph: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Resource mapping: reservoirs, seals, sources by sequence ID",
    )
    emergent_summary: str = Field(
        default="",
        description="Human-readable summary of what emerged",
    )
    confidence: float = Field(default=0.75, ge=0.0, le=0.90)
    epistemic_label: str = Field(default="DER")
    assumptions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    note: str = Field(default="")


# ═══════════════════════════════════════════════════════════════════════════
# Sequence Emergence — Physics-Driven
# ═══════════════════════════════════════════════════════════════════════════


def _classify_scale(duration_myr: float) -> SequenceScale:
    """Sequence scale from duration — this is measurement, not classification.

    A Sloss sequence is ~30-60 Myr because that's how long major
    tectonic-eustatic cycles last. Not because Sloss named it.
    """
    if duration_myr < 1.0:
        return SequenceScale.PARASEQUENCE
    elif duration_myr < 10.0:
        return SequenceScale.DEPOSITIONAL
    else:
        return SequenceScale.SLOSS


def _assess_reservoir(packages: list[DepositionalPackage]) -> str:
    """Assess reservoir potential from package physics, not labels."""
    if not packages:
        return "unknown"
    # Count sand-dominated packages (from stacking + thickness)
    prograding = sum(1 for p in packages if p.stacking_pattern == StackingPattern.PROGRADATIONAL)
    thick = sum(1 for p in packages if p.thickness_m > 10.0)
    if prograding > len(packages) * 0.5 and thick > 0:
        return "high — progradational packages with sand potential"
    elif prograding > 0:
        return "moderate — some progradational packages"
    return "low — dominantly retrogradational/aggradational"


def _assess_seal(surfaces: list[StratSurface]) -> str:
    """Assess seal potential from flooding surfaces, not labels."""
    flooding = [s for s in surfaces if s.surface_type in (SurfaceType.FLOODING, SurfaceType.MAXIMUM_FLOODING)]
    if len(flooding) >= 3:
        return "high — multiple flooding surfaces provide intraformational seals"
    elif len(flooding) >= 1:
        return "moderate — flooding surfaces present"
    return "low — few flooding surfaces"


def _assess_source(surfaces: list[StratSurface]) -> str:
    """Assess source potential from MFS and condensed sections."""
    mfs = [s for s in surfaces if s.surface_type == SurfaceType.MAXIMUM_FLOODING]
    if len(mfs) >= 2:
        return "high — multiple MFS indicate condensed sections with organic enrichment"
    elif len(mfs) >= 1:
        return "moderate — MFS present, potential source rock"
    return "low — no significant MFS identified"


def _stacking_summary(packages: list[DepositionalPackage]) -> str:
    """Summarize stacking pattern evolution from physics."""
    if not packages:
        return "no packages"
    patterns = [p.stacking_pattern.value for p in packages]
    # Compress consecutive identical patterns
    compressed = [patterns[0]]
    for p in patterns[1:]:
        if p != compressed[-1]:
            compressed.append(p)
    return " → ".join(compressed)


def _accommodation_trend(packages: list[DepositionalPackage]) -> str:
    """Determine accommodation trend from package data."""
    if not packages:
        return "unknown"
    rising = sum(1 for p in packages if p.accommodation_trend == "rising")
    falling = sum(1 for p in packages if p.accommodation_trend == "falling")
    if rising > falling * 2:
        return "rising"
    elif falling > rising * 2:
        return "falling"
    elif rising > 0 and falling > 0:
        return "cyclic"
    return "stable"


def emerge_sequences(
    surface_result: SurfaceFirstResult,
    accommodation: AccommodationResult,
) -> SequenceEmergenceResult:
    """Let sequences EMERGE from surfaces and accommodation.

    A sequence is a package of sediment bounded by significant surfaces.
    The scale (parasequence/depositional/Sloss) emerges from the DURATION
    between bounding surfaces — not from a classification rule.

    Surfaces are the physics. Sequences are what the physics produces.

    This is the replacement for geox_sequence's infer_seq_strat().

    Parameters
    ----------
    surface_result : SurfaceFirstResult
        Output from generate_surfaces().
    accommodation : AccommodationResult
        Output from simulate_accommodation().
    """
    key_surfaces = surface_result.key_surfaces
    all_surfaces = surface_result.surfaces
    packages = surface_result.packages

    if not key_surfaces and not all_surfaces:
        return SequenceEmergenceResult(
            sequences=[],
            emergent_summary="No significant surfaces — conformable deposition, no sequences emerged",
            assumptions=["No erosion or flooding detected in the accommodation simulation"],
            evidence_gaps=["higher_resolution_eustatic_curve", "sediment_supply_variation"],
            note="Physics produced continuous deposition. This is valid — not every column has sequences.",
        )

    # Build sequences from key surfaces
    sequences: list[EmergentSequence] = []
    seq_counter = 0

    # Use ALL significant surfaces as potential sequence boundaries
    significant = sorted(all_surfaces, key=lambda s: s.age_ma, reverse=True)

    for i in range(len(significant) - 1):
        top = significant[i]
        base = significant[i + 1]

        # A sequence is bounded by surfaces that are significant enough
        is_boundary = (
            top.is_key_surface
            or base.is_key_surface
            or top.surface_type == SurfaceType.SEQUENCE_BOUNDARY
            or base.surface_type == SurfaceType.SEQUENCE_BOUNDARY
            or top.surface_type == SurfaceType.MAXIMUM_FLOODING
            or (top.erosion_m > 1.0)
        )

        if not is_boundary:
            continue

        duration = abs(top.age_ma - base.age_ma)
        if duration < 0.01:  # skip zero-duration
            continue

        seq_counter += 1
        scale = _classify_scale(duration)

        # Find packages within this sequence
        pkg_ids = []
        for pkg in packages:
            if base.age_ma <= pkg.age_base_ma <= top.age_ma:
                pkg_ids.append(pkg.package_id)

        # Water depth range
        relevant_steps = [s for s in accommodation.steps if base.age_ma <= s.time_ma <= top.age_ma]
        if relevant_steps:
            depths = [s.water_depth_m for s in relevant_steps]
            wd_range = (round(min(depths), 1), round(max(depths), 1))
        else:
            wd_range = (0.0, 0.0)

        # Thickness from packages
        thickness = sum(p.thickness_m for p in packages if p.package_id in pkg_ids)

        # Get packages for stacking analysis
        seq_packages = [p for p in packages if p.package_id in pkg_ids]

        # Resource potential (EMERGED from physics)
        reservoir = _assess_reservoir(seq_packages)
        seal = _assess_seal([s for s in significant if base.age_ma <= s.age_ma <= top.age_ma])
        source = _assess_source([s for s in significant if base.age_ma <= s.age_ma <= top.age_ma])

        sequences.append(
            EmergentSequence(
                sequence_id=f"SEQ{seq_counter:03d}",
                scale=scale,
                age_top_ma=top.age_ma,
                age_base_ma=base.age_ma,
                duration_myr=round(duration, 2),
                bounding_surface_top=top.surface_id,
                bounding_surface_base=base.surface_id,
                bounding_type_top=top.surface_type,
                bounding_type_base=base.surface_type,
                geometry_top=top.geometry,
                geometry_base=base.geometry,
                thickness_m=round(thickness, 1),
                packages=pkg_ids,
                stacking_summary=_stacking_summary(seq_packages),
                accommodation_trend=_accommodation_trend(seq_packages),
                water_depth_range_m=wd_range,
                reservoir_potential=reservoir,
                seal_potential=seal,
                source_potential=source,
                confidence=0.75,
                epistemic_label="DER",
            )
        )

    # Build resource graph
    resource_graph: dict[str, list[str]] = {"reservoirs": [], "seals": [], "sources": []}
    for seq in sequences:
        if "high" in seq.reservoir_potential:
            resource_graph["reservoirs"].append(seq.sequence_id)
        if "high" in seq.seal_potential:
            resource_graph["seals"].append(seq.sequence_id)
        if "high" in seq.source_potential:
            resource_graph["sources"].append(seq.sequence_id)

    # Summary
    by_scale: dict[str, int] = {}
    for seq in sequences:
        by_scale[seq.scale.value] = by_scale.get(seq.scale.value, 0) + 1

    parts = []
    for scale, count in by_scale.items():
        parts.append(f"{count} {scale}")
    summary = f"{len(sequences)} sequences emerged: {', '.join(parts)}" if parts else "No sequences emerged"

    return SequenceEmergenceResult(
        sequences=sequences,
        total_sequences=len(sequences),
        by_scale=by_scale,
        key_surfaces_used=[s.surface_id for s in key_surfaces],
        resource_graph=resource_graph,
        emergent_summary=summary,
        confidence=0.75,
        epistemic_label="DER",
        assumptions=[
            "Sequences bounded by significant surfaces (SB, MFS, erosion > 1m)",
            "Scale classification is temporal, not taxonomic",
            "Resource potential inferred from stacking and surface types",
            "1D simulation — lateral extent not computed",
        ],
        evidence_gaps=[
            "seismic_geometry_verification",
            "well_correlation_data",
            "biostratigraphic_calibration",
            "reservoir_quality_measurements",
        ],
        note=(
            f"Sequence emergence: {len(sequences)} sequences from {len(all_surfaces)} surfaces. "
            f"No systems-tract labels assigned. Architecture emerged from accommodation + routing + erosion."
        ),
    )


__all__ = [
    "SequenceScale",
    "EmergentSequence",
    "SequenceEmergenceResult",
    "emerge_sequences",
]
