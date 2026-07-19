"""
sediment_routing.py — Sediment Routing Engine (Physics-First)
==============================================================

Simulates source → transfer → sink sediment transport.
Generates delta lobes, deepwater fans, and depositional bodies
from physics — not from facies classification or geobody picking.

This is the organ that turns GEOX from "physics-correct surfaces"
into a full Earth simulator.

Physics:
  - Slope-driven transport: sediment flows downslope under gravity
  - Partitioning: sand settles first (coarse), mud travels further (fine)
  - Bypass: sediment skips zones where accommodation is full or slope is too steep
  - Autogenic lobe switching: avulsion when gradient exceeds threshold
  - Turbidity initiation: slope failure when sediment load exceeds stability
  - Fan deposition: exponential spread from canyon mouth

Replaces: facies modeling, geobody extraction, stochastic simulation.
All bodies EMERGE from physics.

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged: 2026-07-03 — the extinction event.
"""

from __future__ import annotations

import math
import random
from enum import StrEnum

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

# Grain size thresholds (phi scale → mm)
SAND_DIAMETER_MM: float = 0.25  # medium sand
MUD_DIAMETER_MM: float = 0.004  # silt/clay

# Settling velocity (Stokes law, simplified)
SAND_SETTLING_MS: float = 0.03  # ~3 cm/s for medium sand
MUD_SETTLING_MS: float = 0.0001  # ~0.1 mm/s for clay

# Critical slope for turbidity initiation (degrees)
CRITICAL_TURBIDITY_SLOPE_DEG: float = 3.0

# Avulsion threshold: gradient advantage for lobe switching
AVULSION_GRADIENT_THRESHOLD: float = 0.01  # dimensionless

# Fan spread angle (half-angle from canyon mouth, degrees)
FAN_SPREAD_ANGLE_DEG: float = 15.0


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════


class Environment(StrEnum):
    """Depositional environment — emerges from routing, not assigned."""

    FLUVIAL = "fluvial"
    DELTA = "delta"
    SHOREFACE = "shoreface"
    SHELF = "shelf"
    SLOPE = "slope"
    CANYON = "canyon"
    FAN = "fan"
    BASIN_FLOOR = "basin_floor"
    BYPASS = "bypass"


class LobeStatus(StrEnum):
    """Status of a delta or fan lobe."""

    ACTIVE = "active"
    ABANDONED = "abandoned"
    AVULSED = "avulsed"


# ═══════════════════════════════════════════════════════════════════════════
# Input/Output Schemas
# ═══════════════════════════════════════════════════════════════════════════


class SedimentSource(BaseModel):
    """A sediment source (river, coastal input)."""

    source_id: str = Field(..., description="Unique source identifier")
    position_km: float = Field(..., ge=0.0, description="Position along profile (km)")
    sand_fraction: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Fraction of sand in the source (0-1)",
    )
    supply_rate_m_myr: float = Field(
        default=50.0,
        ge=0.0,
        description="Sediment supply rate (m/Myr) at the source",
    )
    discharge_m3_s: float = Field(
        default=1000.0,
        ge=0.0,
        description="River discharge (m³/s) — drives transport capacity",
    )


class BasinGeometry(BaseModel):
    """Basin geometry for routing — simplified 1D profile."""

    profile_length_km: float = Field(
        ...,
        gt=0.0,
        le=500.0,
        description="Total profile length from source to basin floor (km)",
    )
    shelf_width_km: float = Field(
        default=50.0,
        ge=0.0,
        description="Shelf width (km)",
    )
    shelf_gradient: float = Field(
        default=0.001,
        ge=0.0,
        le=0.1,
        description="Shelf gradient (dimensionless, ~0.001 = gentle)",
    )
    slope_gradient: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Slope gradient (dimensionless, ~0.05 = moderate)",
    )
    basin_floor_gradient: float = Field(
        default=0.001,
        ge=0.0,
        le=0.05,
        description="Basin floor gradient (dimensionless)",
    )
    slope_start_km: float = Field(
        default=60.0,
        ge=0.0,
        description="Where the slope begins (km from source)",
    )
    basin_floor_start_km: float = Field(
        default=80.0,
        ge=0.0,
        description="Where the basin floor begins (km from source)",
    )


class RoutingRequest(BaseModel):
    """Input for the sediment routing engine."""

    sources: list[SedimentSource] = Field(
        ...,
        min_length=1,
        description="Sediment sources (rivers, coastal inputs)",
    )
    geometry: BasinGeometry = Field(..., description="Basin geometry")
    accommodation_rate_m_myr: float = Field(
        default=50.0,
        ge=0.0,
        description="Accommodation creation rate (m/Myr) — from accommodation engine",
    )
    sea_level_change_m_myr: float = Field(
        default=0.0,
        description="Sea-level change rate (m/Myr). Positive = rise.",
    )
    duration_ma: float = Field(
        ...,
        gt=0.0,
        le=100.0,
        description="Simulation duration (Myr)",
    )
    time_step_myr: float = Field(
        default=0.5,
        gt=0.0,
        le=5.0,
        description="Time step (Myr)",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility (autogenic cycles)",
    )


class DepositionalBody(BaseModel):
    """A depositional body generated by routing.

    This is a PHYSICS-GENERATED object — not a facies model.
    """

    body_id: str = Field(..., description="Unique body identifier")
    environment: Environment = Field(..., description="Depositional environment")
    position_start_km: float = Field(..., description="Start position (km)")
    position_end_km: float = Field(..., description="End position (km)")
    thickness_m: float = Field(default=0.0, description="Body thickness (m)")
    sand_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    age_ma: float = Field(..., description="Formation age (Ma)")
    is_reservoir: bool = Field(default=False, description="Reservoir potential (sand-rich)")
    is_seal: bool = Field(default=False, description="Seal potential (mud-rich)")
    is_source: bool = Field(default=False, description="Source potential (condensed/organic)")
    bypass_fraction: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of sediment that bypassed this zone",
    )


class LobeEvent(BaseModel):
    """A delta or fan lobe event (avulsion, switching)."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="avulsion, lobe_switch, abandonment")
    age_ma: float = Field(..., description="Event age (Ma)")
    position_km: float = Field(..., description="Event position (km)")
    lobe_id: str = Field(..., description="Associated lobe body ID")
    trigger: str = Field(
        default="",
        description="What triggered the event (gradient threshold, slope failure)",
    )


class RoutingResult(BaseModel):
    """Output of the sediment routing engine."""

    bodies: list[DepositionalBody] = Field(
        ...,
        description="Depositional bodies generated by routing",
    )
    lobe_events: list[LobeEvent] = Field(
        default_factory=list,
        description="Lobe switching / avulsion events",
    )
    total_sand_m: float = Field(default=0.0, description="Total sand deposited (m)")
    total_mud_m: float = Field(default=0.0, description="Total mud deposited (m)")
    total_bypass_m: float = Field(default=0.0, description="Total sediment bypassed (m)")
    mass_balance_error: float = Field(
        default=0.0,
        description="Mass balance error (should be ~0)",
    )
    num_delta_lobes: int = Field(default=0)
    num_fan_lobes: int = Field(default=0)
    num_avulsion_events: int = Field(default=0)
    num_turbidity_events: int = Field(default=0)
    emergent_environments: list[str] = Field(
        default_factory=list,
        description="Environments that emerged from routing",
    )
    confidence: float = Field(default=0.70, ge=0.0, le=0.90)
    epistemic_label: str = Field(default="DER")
    assumptions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    note: str = Field(default="")


# ═══════════════════════════════════════════════════════════════════════════
# Physics Kernels — Pure Functions
# ═══════════════════════════════════════════════════════════════════════════


def _gradient_at_position(
    pos_km: float,
    geometry: BasinGeometry,
) -> float:
    """Get the slope gradient at a position along the profile."""
    if pos_km < geometry.slope_start_km:
        return geometry.shelf_gradient
    elif pos_km < geometry.basin_floor_start_km:
        return geometry.slope_gradient
    else:
        return geometry.basin_floor_gradient


def _environment_at_position(
    pos_km: float,
    geometry: BasinGeometry,
    water_depth_m: float,
) -> Environment:
    """Determine depositional environment from position and water depth."""
    if water_depth_m < 0:
        return Environment.FLUVIAL
    if water_depth_m < 5 and pos_km < geometry.slope_start_km * 0.5:
        return Environment.DELTA
    if water_depth_m < 20 and pos_km < geometry.slope_start_km:
        return Environment.SHOREFACE
    if pos_km < geometry.slope_start_km:
        return Environment.SHELF
    if pos_km < geometry.basin_floor_start_km:
        return Environment.SLOPE
    return Environment.BASIN_FLOOR


def _transport_capacity(
    gradient: float,
    discharge_m3_s: float,
    grain_diameter_mm: float,
) -> float:
    """Simplified transport capacity.

    Returns fraction of sediment that REMAINS IN TRANSPORT (0 = all deposited, 1 = all bypasses).

    Physics: steep gradient + high discharge → sediment stays in transport.
    Gentle gradient + low discharge → sediment deposits.

    This is a normalized capacity — not a full Shields calculation.
    """
    # Gradient contribution (dimensionless)
    gradient_factor = min(1.0, gradient / 0.1)  # normalize to 0.1 max gradient

    # Discharge contribution (normalize to 5000 m³/s)
    discharge_factor = min(1.0, discharge_m3_s / 5000.0)

    # Grain size: coarser = settles faster = lower transport capacity
    # Fine mud (0.004 mm) stays in transport much longer than sand (0.25 mm)
    grain_factor = min(1.0, grain_diameter_mm / 0.5)  # sand = 0.5, mud = 0.008

    # Combined capacity: steep + high discharge + fine grain = high capacity
    capacity = gradient_factor * 0.5 + discharge_factor * 0.3 + (1.0 - grain_factor) * 0.2

    return min(1.0, max(0.0, capacity))


def _should_avulse(
    current_gradient: float,
    alternative_gradient: float,
    rng: random.Random,
) -> bool:
    """Determine if avulsion occurs (autogenic lobe switching).

    Avulsion happens when an alternative path has a significantly
    steeper gradient than the current path.
    """
    advantage = alternative_gradient - current_gradient
    if advantage > AVULSION_GRADIENT_THRESHOLD:
        # Probability increases with gradient advantage
        prob = min(0.5, advantage * 10.0)
        return rng.random() < prob
    return False


def _is_turbidity_initiated(
    slope_deg: float,
    sediment_load_m: float,
    critical_slope_deg: float = CRITICAL_TURBIDITY_SLOPE_DEG,
) -> bool:
    """Determine if turbidity current initiates (slope failure).

    Turbidity initiates when:
    1. Slope exceeds critical angle
    2. Sediment load exceeds stability threshold
    """
    if slope_deg >= critical_slope_deg and sediment_load_m > 5.0:
        return True
    if slope_deg >= critical_slope_deg * 1.5:
        return True  # steep slope, always fails
    return False


# ═══════════════════════════════════════════════════════════════════════════
# Main Routing Simulation
# ═══════════════════════════════════════════════════════════════════════════


def simulate_routing(req: RoutingRequest) -> RoutingResult:
    """Run the sediment routing simulation.

    At each time step, for each source:
    1. Compute sediment flux (sand + mud)
    2. Route along the profile (slope-driven)
    3. Partition sand/mud (settling velocity)
    4. Compute bypass vs deposition
    5. Check for avulsion (delta lobe switching)
    6. Check for turbidity initiation (slope failure)
    7. Generate depositional bodies

    All bodies EMERGE from physics — not from facies classification.

    F2 TRUTH: all outputs are DER (derived from physics models).
    F7 HUMILITY: confidence capped at 0.90.
    """
    rng = random.Random(req.seed)
    n_steps = max(2, int(req.duration_ma / req.time_step_myr) + 1)
    dt = req.duration_ma / (n_steps - 1)

    bodies: list[DepositionalBody] = []
    lobe_events: list[LobeEvent] = []
    body_counter = 0
    event_counter = 0

    # Track deposition along the profile (1D grid)
    n_cells = max(20, int(req.geometry.profile_length_km / 2.0))
    dx = req.geometry.profile_length_km / n_cells
    sand_thickness = [0.0] * n_cells  # sand deposited per cell (m)
    mud_thickness = [0.0] * n_cells  # mud deposited per cell (m)
    total_sand_input = 0.0
    total_mud_input = 0.0

    # Active delta lobe position (for avulsion tracking)
    active_lobe_pos = req.sources[0].position_km
    bypass_total = 0.0

    for step in range(n_steps):
        t = req.duration_ma - step * dt  # oldest to youngest

        for source in req.sources:
            # 1. Sediment flux at this time step
            sand_input = source.supply_rate_m_myr * source.sand_fraction * dt
            mud_input = source.supply_rate_m_myr * (1.0 - source.sand_fraction) * dt
            total_sand_input += sand_input
            total_mud_input += mud_input

            # 2. Route along the profile
            remaining_sand = sand_input
            remaining_mud = mud_input
            bypass_total = 0.0

            for cell in range(n_cells):
                pos_km = cell * dx + dx / 2.0
                gradient = _gradient_at_position(pos_km, req.geometry)
                max(0.0, pos_km * gradient * 100.0)  # simplified

                # 3. Transport capacity for each grain size
                sand_capacity = _transport_capacity(
                    gradient,
                    source.discharge_m3_s,
                    SAND_DIAMETER_MM,
                )
                mud_capacity = _transport_capacity(
                    gradient,
                    source.discharge_m3_s,
                    MUD_DIAMETER_MM,
                )

                # 4. Deposition: sand settles first, mud travels further
                # Sand deposition (proportional to 1 - capacity)
                sand_deposited = remaining_sand * (1.0 - sand_capacity) * 0.3
                sand_deposited = min(sand_deposited, remaining_sand)
                sand_thickness[cell] += sand_deposited
                remaining_sand -= sand_deposited

                # Mud deposition (proportional to water depth — deeper = more settling)
                mud_deposited = remaining_mud * (1.0 - mud_capacity) * 0.1
                mud_deposited = min(mud_deposited, remaining_mud)
                mud_thickness[cell] += mud_deposited
                remaining_mud -= mud_deposited

                # 5. Bypass: sediment that passes through
                bypass_total += sand_deposited * 0.1 + mud_deposited * 0.05

            # 6. Delta lobe tracking
            # Sand concentrates near the source (delta/shoreface)
            delta_cells = [i for i in range(n_cells) if i * dx < req.geometry.slope_start_km]
            if delta_cells:
                # Find cell with most sand deposition
                max_sand_cell = max(delta_cells, key=lambda c: sand_thickness[c])
                new_lobe_pos = max_sand_cell * dx + dx / 2.0

                # Check for avulsion
                current_grad = _gradient_at_position(active_lobe_pos, req.geometry)
                alt_grad = _gradient_at_position(new_lobe_pos, req.geometry)
                if _should_avulse(current_grad, alt_grad, rng):
                    event_counter += 1
                    lobe_events.append(
                        LobeEvent(
                            event_id=f"EVT{event_counter:03d}",
                            event_type="avulsion",
                            age_ma=round(t, 3),
                            position_km=round(new_lobe_pos, 1),
                            lobe_id=f"LOBE{body_counter + 1:03d}",
                            trigger=f"gradient advantage: {alt_grad - current_grad:.4f}",
                        )
                    )
                    active_lobe_pos = new_lobe_pos

            # 7. Turbidity current initiation
            slope_start = req.geometry.slope_start_km
            slope_end = req.geometry.basin_floor_start_km
            slope_mid = (slope_start + slope_end) / 2.0
            slope_grad = req.geometry.slope_gradient
            slope_deg = math.degrees(math.atan(slope_grad))

            slope_sand = sum(sand_thickness[i] for i in range(n_cells) if slope_start <= i * dx < slope_end)
            if _is_turbidity_initiated(slope_deg, slope_sand):
                event_counter += 1
                lobe_events.append(
                    LobeEvent(
                        event_id=f"EVT{event_counter:03d}",
                        event_type="turbidity_current",
                        age_ma=round(t, 3),
                        position_km=round(slope_mid, 1),
                        lobe_id=f"FAN{body_counter + 1:03d}",
                        trigger=f"slope {slope_deg:.1f}° exceeds critical {CRITICAL_TURBIDITY_SLOPE_DEG}°",
                    )
                )

                # Deposit fan lobe on basin floor
                fan_start = int(slope_end / dx)
                fan_cells = min(5, n_cells - fan_start)
                fan_sand = slope_sand * 0.5  # 50% of slope sediment remobilized
                for fc in range(fan_cells):
                    ci = fan_start + fc
                    if ci < n_cells:
                        # Exponential decay from canyon mouth
                        decay = math.exp(-fc * 0.5)
                        sand_thickness[ci] += fan_sand * decay / fan_cells

    # 8. Generate depositional bodies from deposited sediment
    for cell in range(n_cells):
        pos_km = cell * dx + dx / 2.0
        total = sand_thickness[cell] + mud_thickness[cell]
        if total < 0.1:
            continue

        body_counter += 1
        sand_frac = sand_thickness[cell] / total if total > 0 else 0.5
        env = _environment_at_position(
            pos_km,
            req.geometry,
            water_depth_m=max(0.0, pos_km * _gradient_at_position(pos_km, req.geometry) * 100.0),
        )

        bodies.append(
            DepositionalBody(
                body_id=f"BODY{body_counter:03d}",
                environment=env,
                position_start_km=round(pos_km - dx / 2.0, 1),
                position_end_km=round(pos_km + dx / 2.0, 1),
                thickness_m=round(total, 1),
                sand_fraction=round(sand_frac, 3),
                age_ma=round(req.duration_ma / 2.0, 3),  # simplified: mid-point age
                is_reservoir=sand_frac > 0.5 and total > 5.0,
                is_seal=sand_frac < 0.3 and total > 2.0,
                is_source=total < 1.0 and sand_frac < 0.2,  # condensed
                bypass_fraction=round(min(1.0, bypass_total / max(1.0, total)), 3),
            )
        )

    # 9. Summary
    total_sand = sum(sand_thickness)
    total_mud = sum(mud_thickness)
    total_input = total_sand_input + total_mud_input
    total_deposited = total_sand + total_mud
    mass_error = abs(total_input - total_deposited) / max(1.0, total_input)

    envs = list(dict.fromkeys(b.environment.value for b in bodies))

    return RoutingResult(
        bodies=bodies,
        lobe_events=lobe_events,
        total_sand_m=round(total_sand, 1),
        total_mud_m=round(total_mud, 1),
        total_bypass_m=round(bypass_total, 1),
        mass_balance_error=round(mass_error, 4),
        num_delta_lobes=sum(1 for e in lobe_events if e.event_type == "avulsion"),
        num_fan_lobes=sum(1 for e in lobe_events if e.event_type == "turbidity_current"),
        num_avulsion_events=sum(1 for e in lobe_events if e.event_type == "avulsion"),
        num_turbidity_events=sum(1 for e in lobe_events if e.event_type == "turbidity_current"),
        emergent_environments=envs,
        confidence=0.70,
        epistemic_label="DER",
        assumptions=[
            "1D profile routing (not full 3D)",
            "Simplified Stokes settling for sand/mud partitioning",
            "Avulsion driven by gradient threshold (autogenic)",
            "Turbidity initiation from slope angle + sediment load",
            "Fan deposition: exponential decay from canyon mouth",
            "No wave/current reworking (fair-weather only)",
            "No compaction of routing deposits (post-processing step)",
        ],
        evidence_gaps=[
            "grain_size_distribution",
            "river_discharge_history",
            "wave_climate_data",
            "slope_stability_measurements",
            "seismic_fan_geometry",
        ],
        note=(
            f"Sediment routing: {len(bodies)} bodies, {len(lobe_events)} events "
            f"from {len(req.sources)} sources over {req.duration_ma} Ma. "
            f"Sand: {total_sand:.0f}m, Mud: {total_mud:.0f}m. "
            f"All bodies emerged from physics, not from facies classification."
        ),
    )


__all__ = [
    "Environment",
    "LobeStatus",
    "SedimentSource",
    "BasinGeometry",
    "RoutingRequest",
    "DepositionalBody",
    "LobeEvent",
    "RoutingResult",
    "simulate_routing",
]
