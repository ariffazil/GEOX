"""Forward–Inverse workflow for GEOX Earth Reality Graph.

Forward Earth:
  Stress → Geomechanics → Structure → Sedimentation → Rock Properties → Velocity → Seismic

Restoration = Inverse Geomechanics:
  Present Geometry → Infer Deformation → Infer Stress

Constitutional statement:
  Earth computes forward. GEOX computes backward.
  Seismic is an observation layer. Geomechanics is a causality layer.
  Restoration is an inverse engine linking the two.

Forged: 2026-09-14
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from ..ontology.earth_reality_graph.graph_schema import (
    ConfidenceClass,
    EdgeType,
    EpistemicClass,
    GraphEdge,
    GraphLayer,
)


class WorkflowDirection(StrEnum):
    """Direction of reasoning through the Reality Graph."""

    FORWARD = "forward"  # Physics → Geomechanics → Structure → Seismic
    INVERSE = "inverse"  # Seismic → Interpretation → Restoration → Stress
    LOOP = "loop"  # Forward prediction + inverse validation (closure)


class WorkflowStep(BaseModel):
    """One step in a forward–inverse workflow."""

    step_id: str = Field(..., description="Step identifier")
    direction: WorkflowDirection = Field(..., description="Forward or inverse")
    source_layer: GraphLayer = Field(..., description="Layer being read from")
    target_layer: GraphLayer = Field(..., description="Layer being written to")
    action: str = Field(
        ..., description="What this step does (compute, infer, validate, interpret)"
    )
    inputs: list[str] = Field(
        default_factory=list, description="Input node IDs"
    )
    outputs: list[str] = Field(
        default_factory=list, description="Output node IDs"
    )
    qc_check: str | None = Field(
        default=None, description="QC check applied at this step"
    )
    verdict: str = Field(default="PENDING", description="Step verdict")


class ForwardInverseWorkflow(BaseModel):
    """A complete forward–inverse workflow through the Reality Graph.

    Forward path: predict what seismic should look like given stress/geology.
    Inverse path: infer stress/geology from what seismic shows.
    Loop: forward prediction + inverse validation = closure.
    """

    workflow_id: str = Field(..., description="Unique workflow ID")
    workflow_type: WorkflowDirection = Field(
        ..., description="Forward, inverse, or loop"
    )
    basin_name: str = Field(default="", description="Basin this applies to")
    steps: list[WorkflowStep] = Field(..., description="Ordered steps")

    # Context
    stress_phases: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Stress phases evaluated (for inverse workflows)",
    )
    tectonic_events: list[str] = Field(
        default_factory=list, description="Tectonic event IDs involved"
    )

    # Audit
    assumptions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    confidence: ConfidenceClass = Field(default=ConfidenceClass.UNKNOWN)


# ═══════════════════════════════════════════════════════════════════════════
# Standard Workflows
# ═══════════════════════════════════════════════════════════════════════════


def build_forward_workflow(
    basin_name: str,
    stress_phases: list[dict[str, Any]],
) -> ForwardInverseWorkflow:
    """Build a standard forward workflow: Stress → Seismic.

    Forward path through the Reality Graph:
    1. F0: Define stress tensor(s)
    2. F1: Compute failure state and fault reactivation
    3. F2: Generate structural state (faults, folds)
    4. F3: Compute basin response (subsidence, accommodation)
    5. F4: Assign sedimentary response (facies, thickness)
    6. F5: Compute rock properties (porosity, density, velocity)
    7. F6: Compute geophysical response (reflectivity, impedance)
    8. F7: Predict what seismic should show
    """
    steps = [
        WorkflowStep(
            step_id="FWD-1",
            direction=WorkflowDirection.FORWARD,
            source_layer=GraphLayer.F0_PHYSICS,
            target_layer=GraphLayer.F1_GEOMECHANICS,
            action="Compute failure state from stress tensor + rock properties",
            qc_check="GRAPH_INV_007: property_support transparency",
        ),
        WorkflowStep(
            step_id="FWD-2",
            direction=WorkflowDirection.FORWARD,
            source_layer=GraphLayer.F1_GEOMECHANICS,
            target_layer=GraphLayer.F2_STRUCTURAL,
            action="Generate structural state from failure conditions",
        ),
        WorkflowStep(
            step_id="FWD-3",
            direction=WorkflowDirection.FORWARD,
            source_layer=GraphLayer.F2_STRUCTURAL,
            target_layer=GraphLayer.F3_BASIN,
            action="Compute basin response from structural state",
        ),
        WorkflowStep(
            step_id="FWD-4",
            direction=WorkflowDirection.FORWARD,
            source_layer=GraphLayer.F3_BASIN,
            target_layer=GraphLayer.F4_SEDIMENTARY,
            action="Assign sedimentary response to accommodation",
        ),
        WorkflowStep(
            step_id="FWD-5",
            direction=WorkflowDirection.FORWARD,
            source_layer=GraphLayer.F4_SEDIMENTARY,
            target_layer=GraphLayer.F5_PETROPHYSICAL,
            action="Compute rock properties from facies and burial",
        ),
        WorkflowStep(
            step_id="FWD-6",
            direction=WorkflowDirection.FORWARD,
            source_layer=GraphLayer.F5_PETROPHYSICAL,
            target_layer=GraphLayer.F6_GEOPHYSICAL,
            action="Compute geophysical response from rock properties",
        ),
        WorkflowStep(
            step_id="FWD-7",
            direction=WorkflowDirection.FORWARD,
            source_layer=GraphLayer.F6_GEOPHYSICAL,
            target_layer=GraphLayer.F7_HUMAN,
            action="Predict seismic image from geophysical response",
        ),
    ]

    return ForwardInverseWorkflow(
        workflow_id=f"fwd-{basin_name.lower().replace(' ', '-')}",
        workflow_type=WorkflowDirection.FORWARD,
        basin_name=basin_name,
        steps=steps,
        stress_phases=stress_phases,
        assumptions=[
            "Stress tensor is representative of the tectonic phase",
            "Rock properties are calibrated (not assumed)",
            "No unmodelled boundary conditions",
        ],
    )


def build_inverse_workflow(
    basin_name: str,
    seismic_interpretation_ids: list[str],
    stress_phases: list[dict[str, Any]],
) -> ForwardInverseWorkflow:
    """Build a standard inverse workflow: Seismic → Stress.

    Inverse path through the Reality Graph:
    1. F7: Start with seismic interpretation (fault sticks, horizons)
    2. F6: Validate against geophysical observations
    3. F5: Infer rock properties from well data
    4. F3: Compute restoration products (accommodation, subsidence)
    5. F2: Geomechanical QC of fault interpretations
    6. F1: Infer stress conditions from fault geometry
    7. F0: Test against independent stress indicators
    8. HYPOTHESIS: Rank tectonic scenarios
    """
    steps = [
        WorkflowStep(
            step_id="INV-1",
            direction=WorkflowDirection.INVERSE,
            source_layer=GraphLayer.F7_HUMAN,
            target_layer=GraphLayer.F6_GEOPHYSICAL,
            action="Validate interpretation against seismic observations",
            qc_check="GRAPH_INV_001: Reflection ≠ Horizon",
        ),
        WorkflowStep(
            step_id="INV-2",
            direction=WorkflowDirection.INVERSE,
            source_layer=GraphLayer.F6_GEOPHYSICAL,
            target_layer=GraphLayer.F5_PETROPHYSICAL,
            action="Infer rock properties from well calibration",
        ),
        WorkflowStep(
            step_id="INV-3",
            direction=WorkflowDirection.INVERSE,
            source_layer=GraphLayer.F5_PETROPHYSICAL,
            target_layer=GraphLayer.F3_BASIN,
            action="Compute restoration products (state differencing)",
        ),
        WorkflowStep(
            step_id="INV-4",
            direction=WorkflowDirection.INVERSE,
            source_layer=GraphLayer.F3_BASIN,
            target_layer=GraphLayer.F2_STRUCTURAL,
            action="Geomechanical QC of fault interpretations",
            qc_check="SR_INV_008 + TECT-004: fault generation from relational evidence",
        ),
        WorkflowStep(
            step_id="INV-5",
            direction=WorkflowDirection.INVERSE,
            source_layer=GraphLayer.F2_STRUCTURAL,
            target_layer=GraphLayer.F1_GEOMECHANICS,
            action="Infer stress conditions from fault geometry + kinematics",
            qc_check="TECT-005: stress rotation outranks fault orientation",
        ),
        WorkflowStep(
            step_id="INV-6",
            direction=WorkflowDirection.INVERSE,
            source_layer=GraphLayer.F1_GEOMECHANICS,
            target_layer=GraphLayer.F0_PHYSICS,
            action="Test inferred stress against independent indicators",
            qc_check="SR_INV_014: independent structural validation",
        ),
        WorkflowStep(
            step_id="INV-7",
            direction=WorkflowDirection.INVERSE,
            source_layer=GraphLayer.F0_PHYSICS,
            target_layer=GraphLayer.F7_HUMAN,
            action="Rank tectonic scenarios with competing hypotheses",
            qc_check="TECT-007: restoration products support multiple hypotheses",
        ),
    ]

    return ForwardInverseWorkflow(
        workflow_id=f"inv-{basin_name.lower().replace(' ', '-')}",
        workflow_type=WorkflowDirection.INVERSE,
        basin_name=basin_name,
        steps=steps,
        stress_phases=stress_phases,
        assumptions=[
            "Seismic interpretation is a geological hypothesis, not ground truth",
            "Well calibration points are accurate",
            "Multiple tectonic phases may contribute to present geometry",
        ],
        evidence_gaps=[
            "Independent stress indicators (borehole breakout, focal mechanisms)",
            "Basement fabric from gravity/magnetics",
            "Biostrat calibration of restoration ages",
        ],
    )


def build_loop_workflow(
    basin_name: str,
    stress_phases: list[dict[str, Any]],
    seismic_interpretation_ids: list[str],
) -> ForwardInverseWorkflow:
    """Build a loop workflow: Forward prediction + Inverse validation.

    This is the closure test: does the forward model reproduce
    what the inverse model infers?
    """
    forward = build_forward_workflow(basin_name, stress_phases)
    inverse = build_inverse_workflow(
        basin_name, seismic_interpretation_ids, stress_phases
    )

    # Add the closure step
    closure_step = WorkflowStep(
        step_id="LOOP-CLOSURE",
        direction=WorkflowDirection.LOOP,
        source_layer=GraphLayer.F7_HUMAN,
        target_layer=GraphLayer.F0_PHYSICS,
        action=(
            "Compare forward prediction with inverse inference. "
            "If they disagree, identify which Reality Graph layer "
            "introduced the discrepancy."
        ),
    )

    all_steps = forward.steps + inverse.steps + [closure_step]

    return ForwardInverseWorkflow(
        workflow_id=f"loop-{basin_name.lower().replace(' ', '-')}",
        workflow_type=WorkflowDirection.LOOP,
        basin_name=basin_name,
        steps=all_steps,
        stress_phases=stress_phases,
        assumptions=forward.assumptions + inverse.assumptions,
        evidence_gaps=inverse.evidence_gaps,
    )


__all__ = [
    "WorkflowDirection",
    "WorkflowStep",
    "ForwardInverseWorkflow",
    "build_forward_workflow",
    "build_inverse_workflow",
    "build_loop_workflow",
]
