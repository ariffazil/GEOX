"""
GEOX Unified Tool Registry & Sealing Engine
DITEMPA BUKAN DIBERI

Registry for all GEOX MCP tools with:
- Tool metadata (name, version, status)
- Input/output schemas (JSON Schema compatible)
- Error codes and handling
- arifOS constitutional requirements
- Metabolic stage mapping (000–999)
- Inter-product risk inheritance (VOID/HOLD/AC_Risk propagation)
- SEAL checklist enforcement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Dict, Optional
import json
import logging

logger = logging.getLogger("geox.core.tool_registry")

# ============================================================================
# ENUMS
# ============================================================================

class ToolStatus(Enum):
    """Production readiness status."""
    PROD = "production"      # Fully tested, stable
    PREVIEW = "preview"      # Working but may change
    SCAFFOLD = "scaffold"    # Architecture only, not implemented

class Verdict(str, Enum):
    """Canonical AC_Risk terminal verdicts."""
    SEAL = "SEAL"
    QUALIFY = "QUALIFY"
    HOLD = "HOLD"
    VOID = "VOID"

class DependencyType(str, Enum):
    """Type of inter-product dependency."""
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"

class ErrorCode(Enum):
    """Standardized GEOX error codes."""
    VALIDATION_ERROR = "GEOX_400_VALIDATION"
    INVALID_FORMAT = "GEOX_400_FORMAT"
    MISSING_REQUIRED = "GEOX_400_MISSING"
    OUT_OF_RANGE = "GEOX_400_RANGE"
    FILE_NOT_FOUND = "GEOX_404_FILE"
    DATA_UNAVAILABLE = "GEOX_404_DATA"
    SCALE_UNKNOWN = "GEOX_404_SCALE"
    PHYSICS_VIOLATION = "GEOX_422_PHYSICS"
    IMPOSSIBLE_GEOMETRY = "GEOX_422_GEOMETRY"
    RATLAS_MISMATCH = "GEOX_422_RATLAS"
    GOVERNANCE_HOLD = "GEOX_403_HOLD"
    AC_RISK_VOID = "GEOX_403_VOID"
    FLOOR_VIOLATION = "GEOX_403_FLOOR"
    INTERNAL_ERROR = "GEOX_500_INTERNAL"
    VISION_UNAVAILABLE = "GEOX_500_VISION"
    CALCULATION_ERROR = "GEOX_500_CALC"

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ErrorSpec:
    code: ErrorCode
    message: str
    description: str
    recoverable: bool
    suggested_action: str

@dataclass
class ToolSchema:
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
    name: str
    version: str
    status: ToolStatus
    description: str
    long_description: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)
    input_schema: ToolSchema = field(default_factory=ToolSchema)
    output_schema: ToolSchema = field(default_factory=ToolSchema)
    error_codes: list[ErrorCode] = field(default_factory=list)
    required_floors: list[str] = field(default_factory=list)
    ac_risk_enabled: bool = False
    risk_factors: list[str] = field(default_factory=list)
    dimension: str = "system"
    metabolic_stage: str = "000"
    nature: list[str] = field(default_factory=list)
    timeout_ms: int = 30000
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "description": self.description,
            "dimension": self.dimension,
            "metabolic_stage": self.metabolic_stage,
            "nature": self.nature,
        }

# ============================================================================
# REGISTRY & DEPENDENCIES
# ============================================================================

DEPENDENCY_GRAPH = [
    {"downstream": "CCS", "upstream": "HYDRO", "type": DependencyType.REQUIRED, "weight": 0.9},
    {"downstream": "CCS", "upstream": "STRUCTURAL_GEOLOGY", "type": DependencyType.REQUIRED, "weight": 0.7},
    {"downstream": "HAZARD", "upstream": "STRUCTURAL_GEOLOGY", "type": DependencyType.REQUIRED, "weight": 0.8},
    {"downstream": "SHALLOW_GEOHAZARD", "upstream": "HAZARD", "type": DependencyType.REQUIRED, "weight": 0.85},
    {"downstream": "HYDRO", "upstream": "STRUCTURAL_GEOLOGY", "type": DependencyType.CONDITIONAL, "weight": 0.5},
    {"downstream": "PETROLEUM_SYSTEM", "upstream": "STRUCTURAL_GEOLOGY", "type": DependencyType.REQUIRED, "weight": 0.75},
    {"downstream": "ENVIRONMENTAL", "upstream": "HYDRO", "type": DependencyType.REQUIRED, "weight": 0.85},
    {"downstream": "GEOTHERMAL", "upstream": "FRACTURE", "type": DependencyType.REQUIRED, "weight": 0.65},
]

SEAL_CHECKLISTS: dict[str, list[str]] = {
    "map": ["geox_map_verify_coordinates", "map_interpret_georeference", "cross_audit_transform_lineage"],
    "well": ["geox_well_verify_petrophysics", "well_audit_qc", "well_verify_cutoffs", "cross_audit_transform_lineage"],
    "ccs": ["ccs_verify_caprock_integrity", "ccs_audit_hydro_dependency", "geox_physics_compute_ac_risk", "cross_audit_transform_lineage"],
}

MANDATORY_888HOLD_DIMENSIONS = {"hazard", "hydro", "ccs", "prospect"}

# ============================================================================
# SEALING ENGINE
# ============================================================================

def can_grant_seal(
    product_type: str,
    fired_tools: set[str],
    own_ac_risk: float,
    vault_anchor: bool,
    runtime_healthy: bool,
    upstream_verdicts: Dict[str, str] = None, # {product_type: verdict_str}
    upstream_ac_risks: Dict[str, float] = None, # {product_type: ac_risk_float}
    hold_approved: bool = False,
) -> dict[str, Any]:
    """
    Evaluate whether a SEAL verdict can be granted for a product.
    Combines Checklist enforcement with Risk Inheritance rules.
    """
    failures = []
    reasons = []
    upstream_verdicts = upstream_verdicts or {}
    upstream_ac_risks = upstream_ac_risks or {}

    # 1. Universal Preconditions
    if not vault_anchor: failures.append("Missing vault anchor")
    if not runtime_healthy: failures.append("Runtime not healthy")
    if "cross_audit_transform_lineage" not in fired_tools:
        failures.append("Required metabolizer not fired: cross_audit_transform_lineage")

    # 2. Checklist Enforcement
    checklist = SEAL_CHECKLISTS.get(product_type.lower(), [])
    for tool in checklist:
        if tool not in fired_tools:
            failures.append(f"Required metabolizer not fired: {tool}")

    # 3. Risk Inheritance Logic
    max_inherited_risk = 0.0
    upstreams = [d for d in DEPENDENCY_GRAPH if d["downstream"] == product_type]
    
    for dep in upstreams:
        u_type = dep["upstream"]
        u_verdict = upstream_verdicts.get(u_type, Verdict.VOID.value)
        u_risk = upstream_ac_risks.get(u_type, 1.0)
        
        # Rule 1: VOID Propagation
        if u_verdict == Verdict.VOID.value and dep["type"] == DependencyType.REQUIRED:
            failures.append(f"Hard Block: Required upstream {u_type} is VOID.")
        
        # Rule 2: HOLD Propagation for critical products
        if u_verdict == Verdict.HOLD.value and product_type in ["CCS", "HAZARD", "SHALLOW_GEOHAZARD"]:
            failures.append(f"Hard Block: Critical upstream {u_type} is on HOLD.")

        # Rule 3: AC_Risk Inheritance
        inherited_risk = u_risk * dep["weight"]
        if inherited_risk > max_inherited_risk:
            max_inherited_risk = inherited_risk

    # 4. Final Risk Determination
    final_ac_risk = max(own_ac_risk, max_inherited_risk)
    
    if final_ac_risk >= 0.15:
        failures.append(f"Final AC_Risk {final_ac_risk:.3f} >= 0.15 (Inherited or Own risk too high)")

    # 5. Mandatory 888_HOLD
    if product_type.lower() in MANDATORY_888HOLD_DIMENSIONS and not hold_approved:
        failures.append(f"Dimension {product_type} requires 888_HOLD human sign-off")

    return {
        "can_seal": len(failures) == 0,
        "verdict": Verdict.SEAL.value if len(failures) == 0 else Verdict.HOLD.value,
        "failures": failures,
        "final_ac_risk": round(final_ac_risk, 4),
        "audit_trail": {
            "own_ac_risk": own_ac_risk,
            "max_inherited_risk": max_inherited_risk,
            "upstream_count": len(upstreams)
        }
    }

# ============================================================================
# TOOL REGISTRY CLASS
# ============================================================================

class ToolRegistry:
    """Unified tool registry for GEOX MCP server."""

    _tools: dict[str, ToolMetadata] = {}

    @classmethod
    def get(cls, name: str) -> ToolMetadata | None:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> list[ToolMetadata]:
        return list(cls._tools.values())
    
    # Maintain compatibility with geox/__init__.py
    ToolStatus = ToolStatus
    ErrorCode = ErrorCode


for _wave2_name, _wave2_desc in {
    "geox_compute_sw_ensemble": "Compute Archie/Indonesia/Simandoux water saturation ensemble.",
    "geox_compute_volume_probabilistic": "Compute probabilistic hydrocarbon pore volume.",
    "geox_simulate_basin_charge": "Simulate basin charge timing and probability.",
    "geox_run_sensitivity_sweep": "Run one-at-a-time sensitivity analysis.",
    "geox_ingest_las": "Ingest LAS well-log files with QC manifest.",
    "geox_memory_store_asset": "Store asset evaluation memory with Amanah lock.",
    "geox_memory_recall_asset": "Recall asset evaluation memory.",
    "geox_render_log_track": "Build JSON log-track visualization payload.",
    "geox_render_volume_slice": "Build JSON volume-slice visualization payload.",
}.items():
    ToolRegistry._tools.setdefault(
        _wave2_name,
        ToolMetadata(
            name=_wave2_name,
            version="2026.04-wave2",
            status=ToolStatus.PREVIEW,
            description=_wave2_desc,
            dimension="subsurface",
            metabolic_stage="333",
        ),
    )
