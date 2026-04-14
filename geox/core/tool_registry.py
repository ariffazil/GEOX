"""
GEOX Unified Tool Registry — Single Source of Truth
DITEMPA BUKAN DIBERI

Registry for all GEOX MCP tools with:
- Tool metadata (name, version, status)
- Input/output schemas (JSON Schema compatible)
- Error codes and handling
- arifOS constitutional requirements
- Metabolic stage mapping (000–999)
- Dimension and nature classification (orthogonal taxonomy)
- SEAL checklist enforcement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
import json


class ToolStatus(Enum):
    """Production readiness status."""
    PROD = "production"      # Fully tested, stable
    PREVIEW = "preview"      # Working but may change
    SCAFFOLD = "scaffold"    # Architecture only, not implemented


class ErrorCode(Enum):
    """Standardized GEOX error codes."""
    # Validation errors (400 range)
    VALIDATION_ERROR = "GEOX_400_VALIDATION"
    INVALID_FORMAT = "GEOX_400_FORMAT"
    MISSING_REQUIRED = "GEOX_400_MISSING"
    OUT_OF_RANGE = "GEOX_400_RANGE"

    # Data errors (404 range)
    FILE_NOT_FOUND = "GEOX_404_FILE"
    DATA_UNAVAILABLE = "GEOX_404_DATA"
    SCALE_UNKNOWN = "GEOX_404_SCALE"

    # Physics errors (422 range)
    PHYSICS_VIOLATION = "GEOX_422_PHYSICS"
    IMPOSSIBLE_GEOMETRY = "GEOX_422_GEOMETRY"
    RATLAS_MISMATCH = "GEOX_422_RATLAS"

    # Governance errors (403 range)
    GOVERNANCE_HOLD = "GEOX_403_HOLD"
    AC_RISK_VOID = "GEOX_403_VOID"
    FLOOR_VIOLATION = "GEOX_403_FLOOR"

    # System errors (500 range)
    INTERNAL_ERROR = "GEOX_500_INTERNAL"
    VISION_UNAVAILABLE = "GEOX_500_VISION"
    CALCULATION_ERROR = "GEOX_500_CALC"


@dataclass
class ErrorSpec:
    """Error specification for documentation and handling."""
    code: ErrorCode
    message: str
    description: str
    recoverable: bool
    suggested_action: str


@dataclass
class ToolSchema:
    """JSON Schema compatible tool schema."""
    type: str = "object"
    properties: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    additional_properties: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "properties": self.properties,
            "required": self.required,
            "additionalProperties": self.additional_properties,
        }


@dataclass
class ToolMetadata:
    """Complete metadata for a GEOX tool."""
    # Identity
    name: str
    version: str
    status: ToolStatus

    # Documentation
    description: str
    long_description: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)

    # Schemas
    input_schema: ToolSchema = field(default_factory=ToolSchema)
    output_schema: ToolSchema = field(default_factory=ToolSchema)

    # Error handling
    error_codes: list[ErrorCode] = field(default_factory=list)

    # arifOS governance
    required_floors: list[str] = field(default_factory=list)
    ac_risk_enabled: bool = False
    risk_factors: list[str] = field(default_factory=list)

    # Metabolic classification
    dimension: str = "system"
    metabolic_stage: str = "000"  # 000–999
    nature: list[str] = field(default_factory=list)  # physics, math, linguistic, forward, inverse, metabolizer

    # Runtime
    timeout_ms: int = 30000
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "description": self.description,
            "long_description": self.long_description,
            "examples": self.examples,
            "input_schema": self.input_schema.to_dict(),
            "output_schema": self.output_schema.to_dict(),
            "error_codes": [e.value for e in self.error_codes],
            "required_floors": self.required_floors,
            "ac_risk_enabled": self.ac_risk_enabled,
            "risk_factors": self.risk_factors,
            "dimension": self.dimension,
            "metabolic_stage": self.metabolic_stage,
            "nature": self.nature,
            "timeout_ms": self.timeout_ms,
            "retryable": self.retryable,
        }


# ============================================================================
# ERROR SPECIFICATIONS
# ============================================================================

ERROR_REGISTRY: dict[ErrorCode, ErrorSpec] = {
    ErrorCode.VALIDATION_ERROR: ErrorSpec(
        code=ErrorCode.VALIDATION_ERROR,
        message="Input validation failed",
        description="The provided input failed validation checks.",
        recoverable=True,
        suggested_action="Check input parameters against schema and retry."
    ),
    ErrorCode.INVALID_FORMAT: ErrorSpec(
        code=ErrorCode.INVALID_FORMAT,
        message="Invalid file format",
        description="The provided file is not in an acceptable format.",
        recoverable=True,
        suggested_action="Convert file to supported format (SEGY, PNG, JPEG, TIFF)."
    ),
    ErrorCode.MISSING_REQUIRED: ErrorSpec(
        code=ErrorCode.MISSING_REQUIRED,
        message="Missing required parameter",
        description="A required input parameter was not provided.",
        recoverable=True,
        suggested_action="Provide all required parameters listed in the schema."
    ),
    ErrorCode.OUT_OF_RANGE: ErrorSpec(
        code=ErrorCode.OUT_OF_RANGE,
        message="Parameter out of valid range",
        description="A numeric parameter is outside acceptable bounds.",
        recoverable=True,
        suggested_action="Adjust parameter to within documented range."
    ),
    ErrorCode.FILE_NOT_FOUND: ErrorSpec(
        code=ErrorCode.FILE_NOT_FOUND,
        message="File not found",
        description="The specified file path does not exist or is inaccessible.",
        recoverable=True,
        suggested_action="Verify file path and permissions."
    ),
    ErrorCode.DATA_UNAVAILABLE: ErrorSpec(
        code=ErrorCode.DATA_UNAVAILABLE,
        message="Required data unavailable",
        description="External data source required for operation is unavailable.",
        recoverable=True,
        suggested_action="Check data source connectivity or try alternative data."
    ),
    ErrorCode.SCALE_UNKNOWN: ErrorSpec(
        code=ErrorCode.SCALE_UNKNOWN,
        description="Cannot determine physical scale from input.",
        message="Scale information missing or ambiguous",
        recoverable=False,
        suggested_action="Provide scale bar, grid coordinates, or explicit scale factor."
    ),
    ErrorCode.PHYSICS_VIOLATION: ErrorSpec(
        code=ErrorCode.PHYSICS_VIOLATION,
        message="Physical impossibility detected",
        description="The interpretation violates known physical constraints.",
        recoverable=False,
        suggested_action="Review interpretation against RATLAS or acquire better data."
    ),
    ErrorCode.IMPOSSIBLE_GEOMETRY: ErrorSpec(
        code=ErrorCode.IMPOSSIBLE_GEOMETRY,
        message="Geometrically impossible structure",
        description="Structural geometry violates physical possibility.",
        recoverable=False,
        suggested_action="Validate against geological principles (F7)."
    ),
    ErrorCode.RATLAS_MISMATCH: ErrorSpec(
        code=ErrorCode.RATLAS_MISMATCH,
        message="Material properties inconsistent with RATLAS",
        description="Interpreted rock properties don't match known analogs.",
        recoverable=False,
        suggested_action="Check velocity/density values or update RATLAS query."
    ),
    ErrorCode.GOVERNANCE_HOLD: ErrorSpec(
        code=ErrorCode.GOVERNANCE_HOLD,
        message="Operation blocked by governance HOLD",
        description="AC_Risk exceeds threshold requiring human review (888_HOLD).",
        recoverable=False,
        suggested_action="Escalate to qualified interpreter; review risk factors."
    ),
    ErrorCode.AC_RISK_VOID: ErrorSpec(
        code=ErrorCode.AC_RISK_VOID,
        message="Operation VOID — critical risk",
        description="AC_Risk ≥ 0.75. Interpretation unsafe.",
        recoverable=False,
        suggested_action="Acquire better data or ground-truth validation."
    ),
    ErrorCode.FLOOR_VIOLATION: ErrorSpec(
        code=ErrorCode.FLOOR_VIOLATION,
        message="Constitutional floor violated",
        description="Operation violates required arifOS floor (F1-F13).",
        recoverable=False,
        suggested_action="Review constitutional requirements for this operation."
    ),
    ErrorCode.INTERNAL_ERROR: ErrorSpec(
        code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error",
        description="Unexpected error occurred during processing.",
        recoverable=True,
        suggested_action="Retry after brief delay; contact support if persistent."
    ),
    ErrorCode.VISION_UNAVAILABLE: ErrorSpec(
        code=ErrorCode.VISION_UNAVAILABLE,
        message="Vision model unavailable",
        description="VLM backend not responding or misconfigured.",
        recoverable=True,
        suggested_action="Check VLM service status or use non-vision fallback."
    ),
    ErrorCode.CALCULATION_ERROR: ErrorSpec(
        code=ErrorCode.CALCULATION_ERROR,
        message="Calculation failed",
        description="Numerical error during computation.",
        recoverable=True,
        suggested_action="Check input data quality or use alternative method."
    ),
}


# ============================================================================
# SEAL CHECKLIST
# ============================================================================

SEAL_CHECKLISTS: dict[str, list[str]] = {
    "map": [
        "map_verify_coordinates",
        "map_interpret_georeference",
        "physics_verify_parameters",
        "cross_audit_transform_lineage",
    ],
    "earth3d": [
        "earth3d_verify_structural_integrity",
        "physics_verify_parameters",
        "section_audit_transform_chain",
        "cross_audit_transform_lineage",
    ],
    "section": [
        "section_verify_attributes",
        "section_audit_transform_chain",
        "geox_vision_review",
        "physics_verify_parameters",
    ],
    "well": [
        "well_verify_petrophysics",
        "well_audit_qc",
        "well_verify_cutoffs",
        "cross_audit_transform_lineage",
    ],
    "time4d": [
        "time4d_verify_timing",
        "physics_verify_parameters",
        "cross_audit_transform_lineage",
        "physics_compute_ac_risk",
    ],
    "prospect": [
        "prospect_verify_physical_grounds",
        "prospect_compute_feasibility",
        "cross_audit_transform_lineage",
        "physics_judge_verdict",
        "physics_audit_hold_breach",
    ],
    "physics": [
        "physics_verify_parameters",
        "physics_verify_operation",
        "cross_audit_transform_lineage",
        "physics_observe_authoritative_state",
    ],
    "hazard": [
        "hazard_verify_gmm_calibration",
        "hazard_audit_data_coverage",
        "physics_compute_ac_risk",
        "cross_audit_transform_lineage",
        "physics_judge_verdict",
    ],
    "hydro": [
        "hydro_verify_boundary_conditions",
        "hydro_audit_well_density",
        "physics_compute_ac_risk",
        "cross_audit_transform_lineage",
        "physics_judge_verdict",
    ],
    "ccs": [
        "ccs_verify_caprock_integrity",
        "ccs_audit_hydro_dependency",
        "physics_compute_ac_risk",
        "cross_audit_transform_lineage",
        "physics_judge_verdict",
    ],
}

MANDATORY_888HOLD_DIMENSIONS = {
    "hazard", "hydro", "ccs", "prospect"
}

# ============================================================================
# CANONICAL ORTHOGONAL TOOL REGISTRY
# ============================================================================

GEOX_TOOLS: dict[str, ToolMetadata] = {
    # ========================================================================
    # MAP — 7 tools
    # ========================================================================
    "map_observe_earth_signals": ToolMetadata(
        name="map_observe_earth_signals",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Fetch live Earth signals (USGS, Open-Meteo, DEM, SAR).",
        dimension="map",
        metabolic_stage="111",
        nature=["physics", "forward"],
        required_floors=["F2"],
    ),
    "map_observe_context_summary": ToolMetadata(
        name="map_observe_context_summary",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Query spatial fabric summary within bounds.",
        dimension="map",
        metabolic_stage="111",
        nature=["linguistic", "forward"],
        required_floors=["F4"],
    ),
    "map_interpret_georeference": ToolMetadata(
        name="map_interpret_georeference",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Bind raster/vector to real-world coordinates.",
        dimension="map",
        metabolic_stage="333",
        nature=["math", "forward"],
        required_floors=["F4", "F11"],
    ),
    "map_interpret_coordinate_transform": ToolMetadata(
        name="map_interpret_coordinate_transform",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Project between coordinate reference systems.",
        dimension="map",
        metabolic_stage="333",
        nature=["math", "forward"],
        required_floors=["F4"],
    ),
    "map_interpret_causal_scene": ToolMetadata(
        name="map_interpret_causal_scene",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Synthesize causal narrative from spatial elements for 888_JUDGE.",
        dimension="map",
        metabolic_stage="444",
        nature=["linguistic", "forward"],
        required_floors=["F2", "F9"],
    ),
    "map_compute_well_projection": ToolMetadata(
        name="map_compute_well_projection",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Project well trajectory into map coordinates.",
        dimension="map",
        metabolic_stage="333",
        nature=["math", "forward"],
        required_floors=["F4"],
    ),
    "map_verify_coordinates": ToolMetadata(
        name="map_verify_coordinates",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Check if coordinates are within valid geospatial bounds.",
        dimension="map",
        metabolic_stage="555",
        nature=["math", "metabolizer"],
        required_floors=["F4", "F11"],
    ),

    # ========================================================================
    # EARTH3D — 4 tools
    # ========================================================================
    "earth3d_observe_volume": ToolMetadata(
        name="earth3d_observe_volume",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Load 3D seismic or geological volume.",
        dimension="earth3d",
        metabolic_stage="111",
        nature=["physics", "forward"],
        required_floors=["F4"],
    ),
    "earth3d_interpret_horizons": ToolMetadata(
        name="earth3d_interpret_horizons",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Infer horizon surfaces from 3D data.",
        dimension="earth3d",
        metabolic_stage="333",
        nature=["math", "inverse"],
        required_floors=["F2", "F7", "F9"],
    ),
    "earth3d_compute_geometries": ToolMetadata(
        name="earth3d_compute_geometries",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Build architectural geometries from interpreted horizons.",
        dimension="earth3d",
        metabolic_stage="333",
        nature=["math", "forward"],
        required_floors=["F4", "F11"],
    ),
    "earth3d_verify_structural_integrity": ToolMetadata(
        name="earth3d_verify_structural_integrity",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Check model for structural paradoxes.",
        dimension="earth3d",
        metabolic_stage="555",
        nature=["math", "metabolizer"],
        required_floors=["F2", "F9"],
    ),

    # ========================================================================
    # SECTION — 5 tools
    # ========================================================================
    "section_observe_well_correlation": ToolMetadata(
        name="section_observe_well_correlation",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Fetch raw correlation data between specified wells.",
        dimension="section",
        metabolic_stage="111",
        nature=["physics", "forward"],
        required_floors=["F4"],
    ),
    "section_interpret_strata": ToolMetadata(
        name="section_interpret_strata",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Correlate stratigraphic units across wells in a section.",
        dimension="section",
        metabolic_stage="333",
        nature=["linguistic", "inverse"],
        required_floors=["F2", "F7"],
    ),
    "section_compute_profile": ToolMetadata(
        name="section_compute_profile",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Synthesize a 2D vertical profile from the Earth model.",
        dimension="section",
        metabolic_stage="333",
        nature=["math", "forward"],
        required_floors=["F4"],
    ),
    "section_verify_attributes": ToolMetadata(
        name="section_verify_attributes",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Check extracted seismic features against transforms.",
        dimension="section",
        metabolic_stage="555",
        nature=["math", "metabolizer"],
        required_floors=["F4", "F9"],
    ),
    "section_audit_transform_chain": ToolMetadata(
        name="section_audit_transform_chain",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Audit the transform-chain for extracted features.",
        dimension="section",
        metabolic_stage="888",
        nature=["metabolizer"],
        required_floors=["F9", "F11"],
    ),

    # ========================================================================
    # WELL — 7 tools
    # ========================================================================
    "well_observe_bundle": ToolMetadata(
        name="well_observe_bundle",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Load LAS/DLIS log bundle into witness context.",
        dimension="well",
        metabolic_stage="111",
        nature=["physics", "forward"],
        required_floors=["F4"],
    ),
    "well_interpret_digitize_log": ToolMetadata(
        name="well_interpret_digitize_log",
        version="0.9.0",
        status=ToolStatus.PREVIEW,
        description="Trace analog logs into governed digital outputs.",
        dimension="well",
        metabolic_stage="333",
        nature=["math", "linguistic", "inverse"],
        required_floors=["F2", "F4"],
    ),
    "well_interpret_sw_model": ToolMetadata(
        name="well_interpret_sw_model",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Recommend Water Saturation model from formation context.",
        dimension="well",
        metabolic_stage="333",
        nature=["math", "linguistic", "inverse"],
        required_floors=["F2", "F7"],
    ),
    "well_compute_petrophysics": ToolMetadata(
        name="well_compute_petrophysics",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Execute physics-9 grounded petrophysical calculations.",
        dimension="well",
        metabolic_stage="222",
        nature=["math", "physics", "forward"],
        required_floors=["F2", "F4", "F7"],
    ),
    "well_verify_cutoffs": ToolMetadata(
        name="well_verify_cutoffs",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Validate petrophysical cutoffs against regional norms.",
        dimension="well",
        metabolic_stage="555",
        nature=["math", "metabolizer"],
        required_floors=["F4"],
    ),
    "well_verify_petrophysics": ToolMetadata(
        name="well_verify_petrophysics",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Governance check for anomalous petrophysics (F9).",
        dimension="well",
        metabolic_stage="555",
        nature=["physics", "metabolizer"],
        required_floors=["F9"],
    ),
    "well_audit_qc": ToolMetadata(
        name="well_audit_qc",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Perform and log quality control on loaded logs.",
        dimension="well",
        metabolic_stage="888",
        nature=["metabolizer"],
        required_floors=["F4", "F11"],
    ),

    # ========================================================================
    # TIME4D — 3 tools
    # ========================================================================
    "time4d_interpret_paleo": ToolMetadata(
        name="time4d_interpret_paleo",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Reconstruct paleo-geography at a specific time (Ma).",
        dimension="time4d",
        metabolic_stage="333",
        nature=["math", "linguistic", "inverse"],
        required_floors=["F2", "F7", "F11"],
    ),
    "time4d_compute_burial": ToolMetadata(
        name="time4d_compute_burial",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Simulate sediment burial and thermal maturation.",
        dimension="time4d",
        metabolic_stage="222",
        nature=["math", "physics", "forward"],
        required_floors=["F2", "F4"],
    ),
    "time4d_verify_timing": ToolMetadata(
        name="time4d_verify_timing",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Check temporal relationship between trap formation and charge.",
        dimension="time4d",
        metabolic_stage="555",
        nature=["math", "metabolizer"],
        required_floors=["F2", "F4"],
    ),

    # ========================================================================
    # PROSPECT — 5 tools
    # ========================================================================
    "prospect_interpret_structural_candidates": ToolMetadata(
        name="prospect_interpret_structural_candidates",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Generate structural trap candidates for a prospect.",
        dimension="prospect",
        metabolic_stage="333",
        nature=["math", "linguistic", "inverse"],
        required_floors=["F2", "F7", "F9"],
    ),
    "prospect_compute_feasibility": ToolMetadata(
        name="prospect_compute_feasibility",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Run technical and economic gating calculations.",
        dimension="prospect",
        metabolic_stage="333",
        nature=["math", "forward"],
        required_floors=["F4", "F7"],
    ),
    "prospect_verify_physical_grounds": ToolMetadata(
        name="prospect_verify_physical_grounds",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Check prospect against physical possibility.",
        dimension="prospect",
        metabolic_stage="555",
        nature=["physics", "metabolizer"],
        required_floors=["F2", "F9"],
    ),
    "prospect_judge_evaluation": ToolMetadata(
        name="prospect_judge_evaluation",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Evaluate hydrocarbon potential with 888_JUDGE verdict.",
        dimension="prospect",
        metabolic_stage="888",
        nature=["math", "linguistic", "metabolizer"],
        required_floors=["F1", "F2", "F4", "F7", "F9", "F13"],
        ac_risk_enabled=True,
    ),
    "prospect_audit_risk_factors": ToolMetadata(
        name="prospect_audit_risk_factors",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Audit GCOS and AC_Risk lineage.",
        dimension="prospect",
        metabolic_stage="888",
        nature=["metabolizer"],
        required_floors=["F11"],
    ),

    # ========================================================================
    # PHYSICS — 7 tools
    # ========================================================================
    "physics_observe_authoritative_state": ToolMetadata(
        name="physics_observe_authoritative_state",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Fetch ground-truth physical state vector from vault.",
        dimension="physics",
        metabolic_stage="111",
        nature=["physics", "forward"],
        required_floors=["F2", "F11"],
    ),
    "physics_compute_stoiip": ToolMetadata(
        name="physics_compute_stoiip",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Calculate Stock Tank Oil Initially In Place.",
        dimension="physics",
        metabolic_stage="222",
        nature=["math", "physics", "forward"],
        required_floors=["F2", "F4", "F7"],
    ),
    "physics_compute_ac_risk": ToolMetadata(
        name="physics_compute_ac_risk",
        version="1.1.0",
        status=ToolStatus.PROD,
        description="Compute AC_Risk = U_phys × D_transform × B_cog.",
        dimension="physics",
        metabolic_stage="666",
        nature=["math", "metabolizer"],
        required_floors=["F2", "F4", "F7", "F9"],
        ac_risk_enabled=True,
    ),
    "physics_verify_parameters": ToolMetadata(
        name="physics_verify_parameters",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Check physical parameters for consistency (e.g. Gardner).",
        dimension="physics",
        metabolic_stage="555",
        nature=["physics", "metabolizer"],
        required_floors=["F2", "F9"],
    ),
    "physics_verify_operation": ToolMetadata(
        name="physics_verify_operation",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Check if operation adheres to safety and physical bounds.",
        dimension="physics",
        metabolic_stage="555",
        nature=["physics", "metabolizer"],
        required_floors=["F1", "F8"],
    ),
    "physics_judge_verdict": ToolMetadata(
        name="physics_judge_verdict",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Execute Sovereign 888_JUDGE on a causal scene.",
        dimension="physics",
        metabolic_stage="888",
        nature=["linguistic", "metabolizer"],
        required_floors=["F1", "F2", "F7", "F9", "F13"],
    ),
    "physics_audit_hold_breach": ToolMetadata(
        name="physics_audit_hold_breach",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Investigate if 888_HOLD conditions were bypassed.",
        dimension="physics",
        metabolic_stage="888",
        nature=["metabolizer"],
        required_floors=["F11", "F13"],
    ),

    # ========================================================================
    # CROSS — 4 tools
    # ========================================================================
    "cross_observe_evidence": ToolMetadata(
        name="cross_observe_evidence",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Retrieve evidence across dimensions for a target.",
        dimension="cross",
        metabolic_stage="111",
        nature=["metabolizer"],
        required_floors=["F11"],
    ),
    "cross_interpret_dimension_map": ToolMetadata(
        name="cross_interpret_dimension_map",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Map relationships between dimensions.",
        dimension="cross",
        metabolic_stage="777",
        nature=["linguistic", "metabolizer"],
        required_floors=["F11"],
    ),
    "cross_verify_health": ToolMetadata(
        name="cross_verify_health",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Health check for cross-dimension bridge.",
        dimension="cross",
        metabolic_stage="555",
        nature=["metabolizer"],
        required_floors=["F4"],
    ),
    "cross_audit_transform_lineage": ToolMetadata(
        name="cross_audit_transform_lineage",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Audit full transform lineage across dimensions.",
        dimension="cross",
        metabolic_stage="888",
        nature=["metabolizer"],
        required_floors=["F9", "F11"],
    ),

    # ========================================================================
    # SYSTEM — 4 tools
    # ========================================================================
    "system_observe_registry": ToolMetadata(
        name="system_observe_registry",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="List available tools and dimensions.",
        dimension="system",
        metabolic_stage="000",
        nature=["metabolizer"],
        required_floors=["F4"],
    ),
    "system_compute_metabolize": ToolMetadata(
        name="system_compute_metabolize",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Run the full 000–999 metabolic loop.",
        dimension="system",
        metabolic_stage="666",
        nature=["metabolizer"],
        required_floors=["F1", "F2", "F4", "F7", "F9", "F13"],
    ),
    "system_verify_health": ToolMetadata(
        name="system_verify_health",
        version="1.0.0",
        status=ToolStatus.PROD,
        description="Runtime health check.",
        dimension="system",
        metabolic_stage="000",
        nature=["metabolizer"],
        required_floors=["F4"],
    ),
    "system_audit_session": ToolMetadata(
        name="system_audit_session",
        version="1.0.0",
        status=ToolStatus.PREVIEW,
        description="Seal session and write to VAULT999.",
        dimension="system",
        metabolic_stage="999",
        nature=["metabolizer"],
        required_floors=["F1", "F11", "F13"],
    ),

    # ========================================================================
    # FUTURE DIMENSIONS (scaffold)
    # ========================================================================
    "hazard_verify_gmm_calibration": ToolMetadata(
        name="hazard_verify_gmm_calibration",
        version="0.1.0",
        status=ToolStatus.SCAFFOLD,
        description="Verify GMPE calibration against local strong-motion data.",
        dimension="hazard",
        metabolic_stage="555",
        nature=["physics", "metabolizer"],
        required_floors=["F2", "F8"],
    ),
    "hazard_audit_data_coverage": ToolMetadata(
        name="hazard_audit_data_coverage",
        version="0.1.0",
        status=ToolStatus.SCAFFOLD,
        description="Audit sensor density and data coverage for hazard map.",
        dimension="hazard",
        metabolic_stage="888",
        nature=["metabolizer"],
        required_floors=["F4", "F11"],
    ),
    "hydro_verify_boundary_conditions": ToolMetadata(
        name="hydro_verify_boundary_conditions",
        version="0.1.0",
        status=ToolStatus.SCAFFOLD,
        description="Verify hydrogeological boundary conditions.",
        dimension="hydro",
        metabolic_stage="555",
        nature=["physics", "metabolizer"],
        required_floors=["F2", "F6", "F8"],
    ),
    "hydro_audit_well_density": ToolMetadata(
        name="hydro_audit_well_density",
        version="0.1.0",
        status=ToolStatus.SCAFFOLD,
        description="Audit observation well density against model resolution.",
        dimension="hydro",
        metabolic_stage="888",
        nature=["metabolizer"],
        required_floors=["F4", "F11"],
    ),
    "ccs_verify_caprock_integrity": ToolMetadata(
        name="ccs_verify_caprock_integrity",
        version="0.1.0",
        status=ToolStatus.SCAFFOLD,
        description="Verify caprock integrity for CO₂ storage.",
        dimension="ccs",
        metabolic_stage="555",
        nature=["physics", "metabolizer"],
        required_floors=["F2", "F8"],
    ),
    "ccs_audit_hydro_dependency": ToolMetadata(
        name="ccs_audit_hydro_dependency",
        version="0.1.0",
        status=ToolStatus.SCAFFOLD,
        description="Audit upstream hydro dependency for CCS plan.",
        dimension="ccs",
        metabolic_stage="777",
        nature=["metabolizer"],
        required_floors=["F3", "F11"],
    ),
}


# ============================================================================
# SEAL ENFORCEMENT
# ============================================================================

def can_grant_seal(
    product_dimension: str,
    fired_tools: set[str],
    ac_risk: float,
    vault_anchor: bool,
    runtime_healthy: bool,
    hold_approved: bool = False,
) -> dict[str, Any]:
    """
    Evaluate whether a SEAL verdict can be granted for a product.
    Enforces GEOX_SEAL_CHECKLIST.md and GEOX_GO_NOGO_RULES.md.
    """
    failures = []

    # Universal preconditions
    if ac_risk >= 0.15:
        failures.append(f"AC_Risk {ac_risk} >= 0.15 (must be < 0.15 for SEAL)")
    if not vault_anchor:
        failures.append("Missing vault anchor")
    if not runtime_healthy:
        failures.append("Runtime not healthy")
    if "cross_audit_transform_lineage" not in fired_tools:
        failures.append("cross_audit_transform_lineage not fired")

    # Dimension-specific checklist
    checklist = SEAL_CHECKLISTS.get(product_dimension, [])
    for tool in checklist:
        if tool not in fired_tools:
            failures.append(f"Required metabolizer not fired: {tool}")

    # Mandatory 888_HOLD
    if product_dimension in MANDATORY_888HOLD_DIMENSIONS and not hold_approved:
        failures.append(f"Dimension {product_dimension} requires 888_HOLD approval")

    return {
        "can_seal": len(failures) == 0,
        "failures": failures,
        "dimension": product_dimension,
    }


# ============================================================================
# REGISTRY API
# ============================================================================

class ToolRegistry:
    """Unified tool registry for GEOX MCP server."""

    _tools: dict[str, ToolMetadata] = GEOX_TOOLS
    _handlers: dict[str, Callable] = {}

    @classmethod
    def get(cls, name: str) -> ToolMetadata | None:
        """Get tool metadata by name."""
        return cls._tools.get(name)

    @classmethod
    def list_tools(
        cls,
        status_filter: ToolStatus | None = None,
        include_scaffold: bool = True
    ) -> list[ToolMetadata]:
        """List all tools with optional filtering."""
        tools = cls._tools.values()

        if status_filter:
            tools = [t for t in tools if t.status == status_filter]
        elif not include_scaffold:
            tools = [t for t in tools if t.status != ToolStatus.SCAFFOLD]

        return list(tools)

    @classmethod
    def list_tools_dict(
        cls,
        status_filter: ToolStatus | None = None,
        include_scaffold: bool = True
    ) -> list[dict[str, Any]]:
        """List tools as dictionaries."""
        return [t.to_dict() for t in cls.list_tools(status_filter, include_scaffold)]

    @classmethod
    def list_by_dimension(cls, dimension: str) -> list[ToolMetadata]:
        """List tools for a specific dimension."""
        return [t for t in cls._tools.values() if t.dimension == dimension]

    @classmethod
    def list_by_stage(cls, stage: str) -> list[ToolMetadata]:
        """List tools for a specific metabolic stage."""
        return [t for t in cls._tools.values() if t.metabolic_stage == stage]

    @classmethod
    def list_by_nature(cls, nature: str) -> list[ToolMetadata]:
        """List tools with a specific nature tag."""
        return [t for t in cls._tools.values() if nature in t.nature]

    @classmethod
    def register_handler(cls, tool_name: str, handler: Callable) -> None:
        """Register a handler function for a tool."""
        cls._handlers[tool_name] = handler

    @classmethod
    def get_handler(cls, tool_name: str) -> Callable | None:
        """Get handler for a tool."""
        return cls._handlers.get(tool_name)

    @classmethod
    def get_error_spec(cls, code: ErrorCode) -> ErrorSpec:
        """Get error specification."""
        return ERROR_REGISTRY[code]

    @classmethod
    def get_capabilities(cls) -> dict[str, Any]:
        """Get server capabilities summary."""
        all_tools = cls.list_tools()
        prod_tools = [t for t in all_tools if t.status == ToolStatus.PROD]
        preview_tools = [t for t in all_tools if t.status == ToolStatus.PREVIEW]
        scaffold_tools = [t for t in all_tools if t.status == ToolStatus.SCAFFOLD]

        # Distribution by nature
        nature_counts = {}
        for t in all_tools:
            for n in t.nature:
                nature_counts[n] = nature_counts.get(n, 0) + 1

        # Distribution by metabolic stage
        stage_counts = {}
        for t in all_tools:
            stage_counts[t.metabolic_stage] = stage_counts.get(t.metabolic_stage, 0) + 1

        return {
            "server": {
                "name": "GEOX Earth Witness",
                "version": "2.0.0-ORTHOGONAL",
                "seal": "DITEMPA BUKAN DIBERI"
            },
            "tool_count": {
                "total": len(all_tools),
                "production": len(prod_tools),
                "preview": len(preview_tools),
                "scaffold": len(scaffold_tools)
            },
            "governance": {
                "floors_active": ["F1", "F2", "F4", "F7", "F9", "F11", "F13"],
                "ac_risk_enabled": True,
                "theory": "ToAC (Theory of Anomalous Contrast)"
            },
            "taxonomy": {
                "nature_distribution": nature_counts,
                "stage_distribution": stage_counts,
            },
            "tools": [t.name for t in all_tools]
        }


def create_standardized_error(
    code: ErrorCode,
    detail: str = "",
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create a standardized error response."""
    spec = ERROR_REGISTRY[code]

    return {
        "error": True,
        "code": code.value,
        "message": spec.message,
        "description": spec.description,
        "detail": detail,
        "recoverable": spec.recoverable,
        "suggested_action": spec.suggested_action,
        "context": context or {},
        "seal": "DITEMPA BUKAN DIBERI"
    }


# ============================================================================
# SELF-TEST
# ============================================================================

if __name__ == "__main__":
    print("GEOX Unified Tool Registry — Orthogonal Taxonomy")
    print("=" * 60)

    # List all tools
    print("\nRegistered Tools:")
    for tool in ToolRegistry.list_tools():
        status_icon = {
            ToolStatus.PROD: "✅",
            ToolStatus.PREVIEW: "🟡",
            ToolStatus.SCAFFOLD: "🔴"
        }.get(tool.status, "❓")
        print(f"  {status_icon} {tool.name} [{tool.dimension}] ({tool.metabolic_stage}) — {', '.join(tool.nature)}")

    # Show capabilities
    print("\nServer Capabilities:")
    caps = ToolRegistry.get_capabilities()
    print(f"  Total tools: {caps['tool_count']['total']}")
    print(f"  Production: {caps['tool_count']['production']}")
    print(f"  Preview: {caps['tool_count']['preview']}")
    print(f"  Scaffold: {caps['tool_count']['scaffold']}")
    print(f"  Nature distribution: {caps['taxonomy']['nature_distribution']}")
    print(f"  Stage distribution: {caps['taxonomy']['stage_distribution']}")

    # Show SEAL evaluation example
    print("\nExample SEAL Evaluation:")
    seal_result = can_grant_seal(
        product_dimension="prospect",
        fired_tools={
            "prospect_verify_physical_grounds",
            "prospect_compute_feasibility",
            "cross_audit_transform_lineage",
            "physics_judge_verdict",
            "physics_audit_hold_breach",
        },
        ac_risk=0.12,
        vault_anchor=True,
        runtime_healthy=True,
        hold_approved=True,
    )
    print(f"  Can seal: {seal_result['can_seal']}")
    if seal_result['failures']:
        print(f"  Failures: {seal_result['failures']}")

    # Show error example
    print("\nExample Error Response:")
    error = create_standardized_error(
        ErrorCode.GOVERNANCE_HOLD,
        detail="AC_Risk=0.68 exceeds HOLD threshold",
        context={"ac_risk": 0.68, "verdict": "HOLD"}
    )
    print(json.dumps(error, indent=2))
