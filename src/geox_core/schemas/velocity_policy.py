from pydantic import BaseModel, Field
from typing import Dict
from geox_core.schemas.velocity_mapping import VelocityQCGate, VelocityFailureMode

class VelocityACRiskPolicy(BaseModel):
    """
    Basin-specific risk appetite and penalty configurations.
    Allows operators to tune how strictly they enforce structural proxies 
    without changing the underlying engine code.
    """
    policy_name: str = Field(default="GLOBAL_DEFAULT", description="Name of the risk policy (e.g., 'MALAY_BASIN_STRICT')")
    
    # Thresholds
    max_acceptable_ac_risk: float = Field(default=0.60, description="Above this risk, the volume is rejected as a structural proxy.")
    base_irreducible_risk: float = Field(default=0.10, description="The baseline epistemic uncertainty inherent in any velocity model.")

    # Penalty weights for missing QC gates
    qc_penalty_map: Dict[VelocityQCGate, float] = Field(default_factory=lambda: {
        VelocityQCGate.MULTI_VELOCITY_CONVERGENCE: 0.15,
        VelocityQCGate.WELL_TIE_TOLERANCE: 0.20,
        VelocityQCGate.TOMOGRAPHY_SENSITIVITY: 0.10,
        VelocityQCGate.PP_PS_JOINT_INVERSION: 0.05,
        VelocityQCGate.PUSHDOWN_DIAGNOSTIC: 0.15,
        VelocityQCGate.ANISOTROPY_CALIBRATION: 0.20,
        VelocityQCGate.CURVATURE_ANALYSIS: 0.10,
        VelocityQCGate.LITHOLOGICAL_PLAUSIBILITY: 0.15,
    })

    # Penalty weights for identified failure modes
    failure_mode_penalty_map: Dict[VelocityFailureMode, float] = Field(default_factory=lambda: {
        VelocityFailureMode.TOMOGRAPHIC_SMOOTHING: 0.25,
        VelocityFailureMode.ANISOTROPY_MISPARAMETERIZATION: 0.35,
        VelocityFailureMode.GAS_CLOUD_PUSHDOWN: 0.30,
        VelocityFailureMode.CARBONATE_INVERSIONS: 0.25,
        VelocityFailureMode.COMPACTION_DISEQUILIBRIUM: 0.20,
        VelocityFailureMode.MULTI_VALUED_RAYS: 0.40,
    })
