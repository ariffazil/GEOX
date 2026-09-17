"""Earth Reality Graph — node schema and graph-level invariants.

The causal graph that connects physical Earth processes to human interpretation.
Every node carries an epistemic class, evidence class, and confidence.
Edges are evidence-bearing — not decorative.

Forward:  Stress → Geomechanics → Structure → Basin → Petrophysics → Seismic
Inverse:  Seismic → Interpretation → Restoration → Geomechanics → Stress

Forged: 2026-09-14
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Classification Enums
# ═══════════════════════════════════════════════════════════════════════════


class EpistemicClass(StrEnum):
    """What kind of knowledge this node represents.

    CRITICAL: A 'Top Basement' surface is INTERPRETED, not PHYSICAL.
    The geological boundary may physically exist, but its mapped
    seismic surface is an interpretation derived from limited observations.
    """

    PHYSICAL = "PHYSICAL"  # Directly measured from physical reality
    OBSERVED = "OBSERVED"  # Measured by instrument (seismic trace, well log)
    DERIVED = "DERIVED"  # Computed from observations (velocity model, inversion)
    INTERPRETED = "INTERPRETED"  # Human/machine geological object (horizon, fault)
    HYPOTHESISED = "HYPOTHESISED"  # Causal explanation requiring testing
    ASSUMED = "ASSUMED"  # Input without direct evidence
    UNKNOWN = "UNKNOWN"  # Not currently knowable


class EvidenceClass(StrEnum):
    """Provenance classification for node data (SR_INV_010)."""

    MEASURED = "MEASURED"
    PUBLISHED = "PUBLISHED"
    CALCULATED = "CALCULATED"
    MODELLED = "MODELLED"
    INTERPRETED = "INTERPRETED"
    EXTRAPOLATED = "EXTRAPOLATED"
    ASSUMED = "ASSUMED"


class ConfidenceClass(StrEnum):
    """Confidence level for the node."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class GraphLayer(StrEnum):
    """Earth Reality Graph layers (F0–F7).

    Layer ordering encodes the forward causal chain.
    Inverse reasoning traverses from F6/F7 back to F0.
    """

    F0_PHYSICS = "F0_PHYSICS"  # Stress, temperature, gravity, pressure
    F1_GEOMECHANICS = "F1_GEOMECHANICS"  # Strain, failure, reactivation
    F2_STRUCTURAL = "F2_STRUCTURAL"  # Faults, folds, basement fabrics
    F3_BASIN = "F3_BASIN"  # Subsidence, accommodation, fill ratio
    F4_SEDIMENTARY = "F4_SEDIMENTARY"  # Facies, carbonates, clastics
    F5_PETROPHYSICAL = "F5_PETROPHYSICAL"  # Porosity, density, resistivity, velocity
    F6_GEOPHYSICAL = "F6_GEOPHYSICAL"  # Seismic, gravity, magnetics
    F7_HUMAN = "F7_HUMAN"  # Picks, horizons, fault sticks, interpretation


# ═══════════════════════════════════════════════════════════════════════════
# Base Node
# ═══════════════════════════════════════════════════════════════════════════


class EarthNode(BaseModel):
    """Base node in the Earth Reality Graph.

    Every node carries:
    - epistemic_class: what kind of knowledge this is
    - evidence_class: where the data came from
    - confidence: how certain we are
    - source_ids: which other nodes this depends on
    - source_mutated: always False (SR_INV_001)
    """

    node_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique node identifier",
    )
    node_type: str = Field(..., description="Node type identifier")
    name: str = Field(..., description="Human-readable name")
    layer: GraphLayer = Field(..., description="Which Reality Graph layer this node belongs to")
    epistemic_class: EpistemicClass = Field(
        ..., description="What kind of knowledge this represents"
    )

    scenario_id: str | None = Field(
        default=None, description="Restoration scenario this node belongs to"
    )
    spatial_reference_id: str | None = Field(
        default=None, description="Spatial context (basin, block, well)"
    )
    temporal_reference_id: str | None = Field(
        default=None, description="Temporal context (event, age interval)"
    )

    source_ids: list[str] = Field(
        default_factory=list,
        description="IDs of nodes this depends on (upstream edges)",
    )
    evidence_class: EvidenceClass = Field(
        default=EvidenceClass.ASSUMED, description="Provenance classification"
    )
    confidence: ConfidenceClass = Field(
        default=ConfidenceClass.UNKNOWN, description="Confidence level"
    )

    values: dict[str, Any] = Field(
        default_factory=dict, description="Typed values for this node"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Assumptions made"
    )
    uncertainties: list[str] = Field(
        default_factory=list, description="Uncertainty sources"
    )

    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC creation time",
    )
    created_by: str = Field(
        default="", description="Agent or human that created this node"
    )
    source_mutated: Literal[False] = Field(
        default=False,
        description="Must always be False — source geometry is immutable (SR_INV_001)",
    )


# ═══════════════════════════════════════════════════════════════════════════
# F0: Physical Driver Nodes
# ═══════════════════════════════════════════════════════════════════════════


class StressTensorNode(EarthNode):
    """Stress state at a specified location and geological time.

    INVARIANT: A regional stress orientation must include its age
    or event interval. A timeless stress arrow has weak geological meaning.
    """

    layer: Literal[GraphLayer.F0_PHYSICS] = GraphLayer.F0_PHYSICS
    node_type: Literal["stress_tensor"] = "stress_tensor"

    sigma_1_mpa: float | None = Field(default=None, description="σ1 magnitude (MPa)")
    sigma_2_mpa: float | None = Field(default=None, description="σ2 magnitude (MPa)")
    sigma_3_mpa: float | None = Field(default=None, description="σ3 magnitude (MPa)")
    sigma_1_azimuth_deg: float | None = Field(
        default=None, ge=0.0, lt=360.0, description="σ1 azimuth (degrees CW from N)"
    )
    sigma_1_plunge_deg: float | None = Field(
        default=None, description="σ1 plunge (degrees from horizontal)"
    )
    stress_regime: str = Field(
        default="UNKNOWN",
        description="NORMAL, STRIKE_SLIP, REVERSE, TRANSTENSIONAL, TRANSPRESSIONAL, UNKNOWN",
    )
    age_ma: float | None = Field(
        default=None, description="Age this stress state applies to (Ma)"
    )
    event_id: str | None = Field(
        default=None, description="Tectonic event this stress belongs to"
    )


class BoundaryConditionNode(EarthNode):
    """Displacement, force, temperature or pressure boundary condition."""

    layer: Literal[GraphLayer.F0_PHYSICS] = GraphLayer.F0_PHYSICS
    node_type: Literal["boundary_condition"] = "boundary_condition"

    condition_type: str = Field(
        default="displacement",
        description="Type: displacement, force, temperature, pressure",
    )
    direction: str = Field(
        default="", description="Direction or normal of the boundary"
    )
    magnitude: float | None = Field(default=None, description="Magnitude")


class ThermalFieldNode(EarthNode):
    """Temperature or heat-flow field."""

    layer: Literal[GraphLayer.F0_PHYSICS] = GraphLayer.F0_PHYSICS
    node_type: Literal["thermal_field"] = "thermal_field"

    temperature_c: float | None = Field(default=None, description="Temperature (°C)")
    heat_flow_mw_m2: float | None = Field(
        default=None, description="Heat flow (mW/m²)"
    )
    gradient_c_km: float | None = Field(
        default=None, description="Geothermal gradient (°C/km)"
    )


class PressureFieldNode(EarthNode):
    """Pore-pressure field."""

    layer: Literal[GraphLayer.F0_PHYSICS] = GraphLayer.F0_PHYSICS
    node_type: Literal["pressure_field"] = "pressure_field"

    pore_pressure_mpa: float | None = Field(
        default=None, description="Pore pressure (MPa)"
    )
    overpressure_mpa: float | None = Field(
        default=None, description="Overpressure above hydrostatic (MPa)"
    )
    fracture_pressure_mpa: float | None = Field(
        default=None, description="Fracture pressure (MPa)"
    )


# ═══════════════════════════════════════════════════════════════════════════
# F1: Geomechanical Response Nodes
# ═══════════════════════════════════════════════════════════════════════════


class MechanicalLayerNode(EarthNode):
    """Rock-mechanical unit and properties.

    INVARIANT: Assumed strength properties cannot silently produce
    a high-confidence fault-reactivation conclusion.
    """

    layer: Literal[GraphLayer.F1_GEOMECHANICS] = GraphLayer.F1_GEOMECHANICS
    node_type: Literal["mechanical_layer"] = "mechanical_layer"

    youngs_modulus_gpa: float | None = Field(default=None)
    poisson_ratio: float | None = Field(default=None)
    cohesion_mpa: float | None = Field(default=None)
    friction_coefficient: float | None = Field(default=None)
    density_kg_m3: float | None = Field(default=None)
    pore_pressure_mpa: float | None = Field(default=None)
    property_support: str = Field(
        default="UNKNOWN",
        description=(
            "LAB_MEASURED, LOG_DERIVED, REGIONAL_ANALOGUE, ASSUMED, UNKNOWN"
        ),
    )


class FailureStateNode(EarthNode):
    """Mohr–Coulomb or alternative failure condition."""

    layer: Literal[GraphLayer.F1_GEOMECHANICS] = GraphLayer.F1_GEOMECHANICS
    node_type: Literal["failure_state"] = "failure_state"

    failure_criterion: str = Field(
        default="mohr_coulomb",
        description="Failure criterion used (mohr_coulomb, hoek_brown, etc.)",
    )
    tau_applied_mpa: float | None = Field(default=None, description="Applied shear stress (MPa)")
    sigma_n_mpa: float | None = Field(default=None, description="Effective normal stress (MPa)")
    tau_failure_mpa: float | None = Field(default=None, description="Failure shear stress (MPa)")
    safety_factor: float | None = Field(default=None, description="τ_failure / τ_applied")
    is_yielding: bool | None = Field(default=None, description="True if on or beyond failure envelope")


class FaultReactivationNode(EarthNode):
    """Mechanical admissibility of renewed fault movement.

    INVARIANT: Fault reactivation is a geomechanical conclusion,
    not a geometric observation. Requires stress tensor + fault geometry
    + mechanical properties.
    """

    layer: Literal[GraphLayer.F1_GEOMECHANICS] = GraphLayer.F1_GEOMECHANICS
    node_type: Literal["fault_reactivation"] = "fault_reactivation"

    fault_id: str = Field(..., description="Fault being evaluated")
    stress_tensor_id: str = Field(..., description="Stress tensor node ID")
    mechanical_layer_id: str = Field(..., description="Mechanical layer node ID")
    strike_deg: float | None = Field(default=None, description="Fault strike")
    dip_deg: float | None = Field(default=None, description="Fault dip")
    rake_deg: float | None = Field(default=None, description="Resolved rake")
    slip_tendency: float | None = Field(
        default=None, description="τ/σn ratio (slip tendency)"
    )
    dilation_tendency: float | None = Field(
        default=None, description="(σ1-σn)/(σ1-σ3) ratio"
    )
    is_reactivated: bool | None = Field(
        default=None,
        description="True if mechanical conditions favour reactivation",
    )
    confidence: ConfidenceClass = Field(
        default=ConfidenceClass.UNKNOWN,
        description="Must reflect property_support of the mechanical layer",
    )


# ═══════════════════════════════════════════════════════════════════════════
# F2: Structural State Nodes
# ═══════════════════════════════════════════════════════════════════════════


class FaultObservationNode(EarthNode):
    """Seismic discontinuity or attribute response.

    This is NOT a geological fault. It is an instrument observation
    that MAY correspond to a fault.
    """

    layer: Literal[GraphLayer.F2_STRUCTURAL] = GraphLayer.F2_STRUCTURAL
    node_type: Literal["fault_observation"] = "fault_observation"

    survey_id: str = Field(default="", description="Seismic survey ID")
    observed_features: list[str] = Field(
        default_factory=list,
        description=(
            "Observed features: REFLECTOR_OFFSET, REFLECTOR_TERMINATION, "
            "COHERENCE_LOW, CURVATURE_ANOMALY, DIFFRACTION, "
            "AMPLITUDE_DISRUPTION, VELOCITY_DISCONTINUITY"
        ),
    )


class FaultInterpretationNode(EarthNode):
    """Mapped fault sticks or surface.

    This is an INTERPRETATION of fault observations.
    It is not a deformation event, and not a tectonic cause.
    """

    layer: Literal[GraphLayer.F2_STRUCTURAL] = GraphLayer.F2_STRUCTURAL
    node_type: Literal["fault_interpretation"] = "fault_interpretation"

    geometry_uri: str = Field(default="", description="URI to fault geometry data")
    fault_type: str | None = Field(
        default=None,
        description="Normal, reverse, strike-slip, thrust, etc.",
    )
    throw_polarity: str | None = Field(default=None)
    generation_hypothesis_ids: list[str] = Field(
        default_factory=list,
        description="Tectonic event hypotheses for this fault",
    )
    observation_support_ids: list[str] = Field(
        default_factory=list,
        description="FaultObservation nodes that support this interpretation",
    )


class BasementFabricNode(EarthNode):
    """Inherited basement structural trend from gravity/magnetics.

    Gravity sees deeper than seismic. Magnetics sees older than seismic.
    Basement fabric may preserve structural trends that seismic cannot image.
    """

    layer: Literal[GraphLayer.F2_STRUCTURAL] = GraphLayer.F2_STRUCTURAL
    node_type: Literal["basement_fabric"] = "basement_fabric"

    trend_azimuth_deg: float | None = Field(default=None)
    source_type: str = Field(
        default="gravity",
        description="Source: gravity, magnetics, seismic, well, combined",
    )
    wavelength_km: float | None = Field(
        default=None, description="Wavelength of the fabric trend"
    )


class RestorationStateNode(EarthNode):
    """Immutable geometry at one restoration stage.

    SR_INV_001: Source geometry is immutable.
    This node represents a SNAPSHOT, not a transformation.
    """

    layer: Literal[GraphLayer.F2_STRUCTURAL] = GraphLayer.F2_STRUCTURAL
    node_type: Literal["restoration_state"] = "restoration_state"

    age_ma: float = Field(..., description="Age this state represents")
    surface_ids: list[str] = Field(
        default_factory=list, description="Surfaces in this state"
    )
    fault_ids: list[str] = Field(
        default_factory=list, description="Faults in this state"
    )
    crs_epsg: int | None = Field(default=None)
    z_convention: str = Field(default="positive_down")


# ═══════════════════════════════════════════════════════════════════════════
# F3: Basin Response Nodes
# ═══════════════════════════════════════════════════════════════════════════


class SubsidenceNode(EarthNode):
    """Basement subsidence observation.

    SR_INV_005: Subsidence ≠ accommodation ≠ thickness.
    This is an OBSERVATION, not a tectonic explanation (TECT-003).
    """

    layer: Literal[GraphLayer.F3_BASIN] = GraphLayer.F3_BASIN
    node_type: Literal["subsidence"] = "subsidence"

    subsidence_m: float | None = Field(default=None, description="Subsidence (m)")
    mechanism: str = Field(
        default="unknown",
        description="Proposed mechanism (thermal, flexural, tectonic, dynamic)",
    )
    source_state_id: str = Field(
        default="", description="Source restoration state ID"
    )
    target_state_id: str = Field(
        default="", description="Target restoration state ID"
    )


class AccommodationNode(EarthNode):
    """Accommodation space observation.

    TECT-002: Accommodation is an effect, not a cause.
    SR_INV_005: Accommodation ≠ subsidence ≠ thickness.
    """

    layer: Literal[GraphLayer.F3_BASIN] = GraphLayer.F3_BASIN
    node_type: Literal["accommodation"] = "accommodation"

    accommodation_m: float | None = Field(default=None)
    source_state_id: str = Field(default="")
    target_state_id: str = Field(default="")
    subtraction_order: str = Field(
        default="", description="Which state minus which"
    )
    sign_convention: str = Field(default="")


class FillRatioNode(EarthNode):
    """Fill ratio observation.

    SR_INV_007: fill_ratio > 1 is a DIAGNOSTIC ANOMALY, never an automatic
    tectonic interpretation. Diagnostic checklist required.
    """

    layer: Literal[GraphLayer.F3_BASIN] = GraphLayer.F3_BASIN
    node_type: Literal["fill_ratio"] = "fill_ratio"

    fill_ratio: float | None = Field(default=None)
    sediment_thickness_m: float | None = Field(default=None)
    accommodation_m: float | None = Field(default=None)
    status: str = Field(
        default="VALID",
        description="VALID, NEGATIVE, ANOMALY_GT1, INVALID_DENOMINATOR",
    )
    diagnostic_review_required: bool = Field(
        default=False,
        description="True if fill_ratio > 1 (SR_INV_007)",
    )
    diagnostic_checklist_status: str = Field(
        default="NOT_APPLICABLE",
        description="NOT_APPLICABLE, PENDING, COMPLETED",
    )


# ═══════════════════════════════════════════════════════════════════════════
# F4: Sedimentary Nodes
# ═══════════════════════════════════════════════════════════════════════════


class FaciesNode(EarthNode):
    """Depositional facies interpretation."""

    layer: Literal[GraphLayer.F4_SEDIMENTARY] = GraphLayer.F4_SEDIMENTARY
    node_type: Literal["facies"] = "facies"

    facies_type: str = Field(default="", description="Facies classification")
    depositional_environment: str = Field(default="")
    dominant_lithology: str = Field(default="")


# ═══════════════════════════════════════════════════════════════════════════
# F5: Petrophysical Nodes
# ═══════════════════════════════════════════════════════════════════════════


class RockPropertyNode(EarthNode):
    """Rock physical property (porosity, density, velocity, resistivity)."""

    layer: Literal[GraphLayer.F5_PETROPHYSICAL] = GraphLayer.F5_PETROPHYSICAL
    node_type: Literal["rock_property"] = "rock_property"

    property_name: str = Field(
        default="",
        description="Property name (porosity, density, velocity, resistivity, susceptibility)",
    )
    value: float | None = Field(default=None)
    units: str = Field(default="")
    depth_m: float | None = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════════
# F6: Geophysical Response Nodes
# ═══════════════════════════════════════════════════════════════════════════


class GeophysicalObservationNode(EarthNode):
    """Geophysical measurement (seismic trace, gravity grid, magnetic grid).

    This is an OBSERVATION, not a geological object.
    Reflection ≠ Horizon ≠ Event ≠ Cause.
    """

    layer: Literal[GraphLayer.F6_GEOPHYSICAL] = GraphLayer.F6_GEOPHYSICAL
    node_type: Literal["geophysical_observation"] = "geophysical_observation"

    survey_type: str = Field(
        default="seismic",
        description="Type: seismic, gravity, magnetics, MT, well_log",
    )
    survey_id: str = Field(default="")
    measured_quantity: str = Field(
        default="",
        description="What was measured (amplitude, gravity_anomaly, magnetic_field, etc.)",
    )


# ═══════════════════════════════════════════════════════════════════════════
# F7: Human Interpretation Nodes
# ═══════════════════════════════════════════════════════════════════════════


class InterpretationNode(EarthNode):
    """Human or machine-derived geological interpretation.

    This is an INTERPRETATION of observations.
    It is not reality, not an observation, not a hypothesis.
    """

    layer: Literal[GraphLayer.F7_HUMAN] = GraphLayer.F7_HUMAN
    node_type: Literal["interpretation"] = "interpretation"

    interpreter: str = Field(
        default="", description="Who or what made this interpretation"
    )
    interpretation_type: str = Field(
        default="",
        description="Type: horizon_pick, fault_surface, facies_body, etc.",
    )
    observation_support_ids: list[str] = Field(
        default_factory=list,
        description="Observation nodes that support this interpretation",
    )


class TectonicHypothesisNode(EarthNode):
    """Causal explanation requiring testing.

    TECT-001: Observation ≠ Explanation.
    TECT-007: Restoration products support multiple hypotheses.
    """

    layer: Literal[GraphLayer.F7_HUMAN] = GraphLayer.F7_HUMAN
    node_type: Literal["tectonic_hypothesis"] = "tectonic_hypothesis"

    hypothesis: str = Field(default="", description="The hypothesis statement")
    probability: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Relative probability"
    )
    competing_hypothesis_ids: list[str] = Field(
        default_factory=list, description="Other hypotheses explaining same observations"
    )
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    falsification_criteria: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Edges — evidence-bearing connections
# ═══════════════════════════════════════════════════════════════════════════


class EdgeType(StrEnum):
    """Types of edges in the Earth Reality Graph."""

    CAUSES = "causes"  # F→F: physical causation
    PRODUCES = "produces"  # F→F: state production
    MEASURES = "measures"  # Instrument → observation
    INTERPRETS = "interprets"  # Observation → interpretation
    SUPPORTS = "supports"  # Evidence → hypothesis
    CHALLENGES = "challenges"  # Evidence against hypothesis
    CONSTRAINS = "constrains"  # QC constraint
    FALSIFIES = "falsifies"  # Evidence that rejects hypothesis
    INHERITS = "inherits"  # Structural inheritance
    REACTIVATES = "reactivates"  # Fault reactivation


class GraphEdge(BaseModel):
    """An edge in the Earth Reality Graph.

    Every edge is evidence-bearing — not decorative.
    """

    edge_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique edge ID"
    )
    source_node_id: str = Field(..., description="Upstream node")
    target_node_id: str = Field(..., description="Downstream node")
    edge_type: EdgeType = Field(..., description="Type of relationship")
    evidence: str = Field(
        default="", description="Evidence supporting this edge"
    )
    confidence: ConfidenceClass = Field(
        default=ConfidenceClass.UNKNOWN
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ═══════════════════════════════════════════════════════════════════════════
# Graph-Level Invariants
# ═══════════════════════════════════════════════════════════════════════════

GRAPH_INVARIANTS = {
    "GRAPH_INV_001": {
        "name": "Reflection ≠ Horizon",
        "rule": "A measured seismic discontinuity is not a fault or horizon.",
        "layers": ("F6_GEOPHYSICAL", "F7_HUMAN"),
    },
    "GRAPH_INV_002": {
        "name": "Horizon ≠ Event",
        "rule": "A mapped horizon is not a deformation or depositional event.",
        "layers": ("F7_HUMAN", "F3_BASIN"),
    },
    "GRAPH_INV_003": {
        "name": "Event ≠ Cause",
        "rule": "A deformation event is not its tectonic cause.",
        "layers": ("F2_STRUCTURAL", "F0_PHYSICS"),
    },
    "GRAPH_INV_004": {
        "name": "Epistemic class must be honest",
        "rule": "A 'Top Basement' surface is INTERPRETED, not PHYSICAL.",
        "layers": ("F2_STRUCTURAL",),
    },
    "GRAPH_INV_005": {
        "name": "No silent layer crossing",
        "rule": "A node cannot claim to be from a higher layer than its evidence supports.",
        "layers": ("all",),
    },
    "GRAPH_INV_006": {
        "name": "Temporal stress constraint",
        "rule": "A stress tensor must include its age or event interval.",
        "layers": ("F0_PHYSICS",),
    },
    "GRAPH_INV_007": {
        "name": "Property support transparency",
        "rule": "Assumed strength properties cannot silently produce high-confidence fault-reactivation.",
        "layers": ("F1_GEOMECHANICS",),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Node Type Registry
# ═══════════════════════════════════════════════════════════════════════════

NODE_TYPE_REGISTRY: dict[str, type[EarthNode]] = {
    "stress_tensor": StressTensorNode,
    "boundary_condition": BoundaryConditionNode,
    "thermal_field": ThermalFieldNode,
    "pressure_field": PressureFieldNode,
    "mechanical_layer": MechanicalLayerNode,
    "failure_state": FailureStateNode,
    "fault_reactivation": FaultReactivationNode,
    "fault_observation": FaultObservationNode,
    "fault_interpretation": FaultInterpretationNode,
    "basement_fabric": BasementFabricNode,
    "restoration_state": RestorationStateNode,
    "subsidence": SubsidenceNode,
    "accommodation": AccommodationNode,
    "fill_ratio": FillRatioNode,
    "facies": FaciesNode,
    "rock_property": RockPropertyNode,
    "geophysical_observation": GeophysicalObservationNode,
    "interpretation": InterpretationNode,
    "tectonic_hypothesis": TectonicHypothesisNode,
}
