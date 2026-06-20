from enum import Enum

from pydantic import BaseModel, Field


class VelocityQCGate(str, Enum):
    MULTI_VELOCITY_CONVERGENCE = "multi_velocity_convergence"
    WELL_TIE_TOLERANCE = "well_tie_tolerance"
    TOMOGRAPHY_SENSITIVITY = "tomography_sensitivity"
    PP_PS_JOINT_INVERSION = "pp_ps_joint_inversion"
    PUSHDOWN_DIAGNOSTIC = "pushdown_diagnostic"
    ANISOTROPY_CALIBRATION = "anisotropy_calibration"
    CURVATURE_ANALYSIS = "curvature_analysis"
    LITHOLOGICAL_PLAUSIBILITY = "lithological_plausibility"

class VelocityFailureMode(str, Enum):
    TOMOGRAPHIC_SMOOTHING = "tomographic_smoothing"
    ANISOTROPY_MISPARAMETERIZATION = "anisotropy_misparameterization"
    GAS_CLOUD_PUSHDOWN = "gas_cloud_pushdown"
    CARBONATE_INVERSIONS = "carbonate_inversions"
    COMPACTION_DISEQUILIBRIUM = "compaction_disequilibrium"
    MULTI_VALUED_RAYS = "multi_valued_rays"

class VelocityLineageEvent(BaseModel):
    """Tracks the evolution of the velocity model."""
    model_version: str
    timestamp: str
    change_reason: str

class VelocityStructuralClaim(BaseModel):
    """
    Constitutional claim grammar for a velocity-driven structural mapping.
    Enforces the GEOX Epistemic Ladder (Rung 5: EARTHMODEL) and requires explicit
    evidence/contradiction documentation.
    
    FEDERATION USAGE POLICY:
    If `is_structural_proxy_valid == False`:
      1. Proxy may be visualized but MUST NOT be used for auto well placement, 
         volume estimates, or trap risking without a human F13 override.
      2. Any planner proposal that touches this horizon must tag itself with 
         `depends_on_untrusted_proxy({proxy_id})`.
    """
    proxy_id: str = Field(default_factory=lambda: "proxy_auto", description="Unique ID for this structural proxy packet.")
    cube_id: str
    source_model_version: str = Field(..., description="Version of the source velocity model (e.g., 'FWI_v3').")
    epistemic_rung: str = Field(default="EARTHMODEL", description="Velocity cubes for structure are always Rung 5 models, never facts.")
    
    # Provenance & Lineage
    lineage: list[VelocityLineageEvent] = Field(default_factory=list, description="Audit trail of why this model version exists.")
    evidence_handles: list[str] = Field(default_factory=list, description="URIs pointing to QC artifacts (e.g., geox://qc/welltie/123).")
    
    cleared_qc_gates: list[VelocityQCGate]
    failed_qc_gates: list[VelocityQCGate]
    identified_failure_modes: list[VelocityFailureMode]
    
    # Claim Grammar Enforcement
    evidence_for: str = Field(..., description="Evidence supporting this Vint model as a valid structural proxy.")
    evidence_against: str = Field(..., description="Contradicting evidence or unresolved artifacts (e.g., residual moveout).")
    missing_tests: list[str] = Field(..., description="Required QC gates that were not performed.")
    
    uncertainty_band: str = Field(default="P10-P90 Not Calculated", description="Uncertainty spread across realizations (e.g., '±50m at 3km depth').")
    ac_risk: float = Field(..., ge=0.0, le=1.0, description="Calculated Anomalous Contrast Risk. >0.70 means highly unsafe for structural decisions.")
    is_structural_proxy_valid: bool = Field(..., description="Final verdict on whether this volume can be used for structural framework.")

class VelocityRenderPayload(BaseModel):
    """
    The Binary Transport Envelope. 
    Does not contain the 3D cube data, only the URI for binary streaming.
    """
    renderable: bool = True
    cube_manifest_uri: str
    claim: VelocityStructuralClaim
