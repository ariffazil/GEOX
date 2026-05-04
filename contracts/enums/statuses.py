from typing import List, Dict, Any, Optional
from enum import Enum

class Dimension(str, Enum):
    PROSPECT = "prospect"
    WELL = "well"
    EARTH3D = "earth3d"
    MAP = "map"
    CROSS = "cross"
    SECTION = "section"
    TIME4D = "time4d"
    PHYSICS = "physics"
    DASHBOARD = "dashboard"

class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    HALT = "HALT"

class GovernanceStatus(str, Enum):
    APPROVED = "APPROVED"
    QUALIFY = "QUALIFY"
    HOLD = "HOLD"
    VOID = "VOID"
    SEAL = "SEAL"

Verdict = GovernanceStatus

class ArtifactStatus(str, Enum):
    USABLE = "USABLE"
    STAGED = "STAGED"
    REJECTED = "REJECTED"
    INCOMPLETE = "INCOMPLETE"
    DRAFT = "DRAFT"
    VERIFIED = "VERIFIED"
    COMPUTED = "COMPUTED"
    LOADED = "LOADED"
    IN_REVIEW = "IN_REVIEW"

class FloorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    VOID = "void"
    HALT = "halt"

class Runtime(str, Enum):
    VPS = "vps"
    FASTMCP = "fastmcp"
    LOCAL = "local"

class Transport(str, Enum):
    HTTP = "http"
    MCP = "mcp"
    STDIO = "stdio"
    SSE = "sse"

class ToolCategory(str, Enum):
    FOUNDATION = "foundation"
    PHYSICS = "physics"
    BRIDGE = "bridge"
    DEMO = "demo"
    SYSTEM = "system"

class ProspectVerdict(str, Enum):
    DRO = "DRO"
    DRIL = "DRIL"
    HOLD = "HOLD"
    DROP = "DROP"

class ClaimTag(str, Enum):
    CLAIM = "CLAIM"
    PLAUSIBLE = "PLAUSIBLE"
    HYPOTHESIS = "HYPOTHESIS"

# Type aliases
VerdictCode = GovernanceStatus
FloorCode = str
DimensionCode = str

# Constants
CONSTITUTIONAL_FLOORS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13"]
CANONICAL_TOOLS = [
    "geox_data_ingest_bundle",
    "geox_data_qc_bundle",
    "geox_subsurface_generate_candidates",
    "geox_subsurface_verify_integrity",
    "geox_seismic_analyze_volume",
    "geox_section_interpret_correlation",
    "geox_map_context_scene",
    "geox_time4d_analyze_system",
    "geox_prospect_evaluate",
    "geox_prospect_judge_verdict",
    "geox_evidence_summarize_cross",
    "geox_system_registry_status",
    "geox_history_audit",
]
SEAL = "DITEMPA BUKAN DIBERI"

def get_standard_envelope(
    primary_artifact: Dict[str, Any],
    tool_class: str = "compute",
    execution_status: ExecutionStatus = ExecutionStatus.SUCCESS,
    governance_status: GovernanceStatus = GovernanceStatus.QUALIFY,
    artifact_status: ArtifactStatus = ArtifactStatus.DRAFT,
    uncertainty: str = "Moderate",
    evidence_refs: Optional[List[str]] = None,
    diagnostics: Optional[Dict[str, Any]] = None,
    ui_resource_uri: Optional[str] = None,
    claim_tag: str = "HYPOTHESIS",
    claim_state: str = "INGESTED",
    confidence_band: Optional[Dict[str, float]] = None,
    physics_guard: Optional[Dict[str, Any]] = None,
    audit_receipt: Optional[Dict[str, str]] = None,
    humility_score: float = 0.0,
    maruah_flag: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Canonical MCP Apps Response Envelope — Universal Output Contract v0.4.
    Follows MCP spec + arifOS Governance + MCP Apps UI.
    Required fields: claim_tag, claim_state, confidence_band, physics_guard, evidence_refs,
    uncertainty, audit_receipt, humility_score (F7), maruah_flag (F6).

    Lifecycle claim_state values:
        INGESTED             — artifact received, not yet QC'd
        QC_VERIFIED         — passed QC gate (Tool 02)
        PLOTTED             — visual artifact produced
        INTERPRETED         — interpretation applied
        DECISION_SENSITIVE  — in prospect evaluation pipeline
        BLOCKED             — QC failed or governance HOLD
    """
    from datetime import datetime, timezone
    response = {
        "execution_status": execution_status.value if isinstance(execution_status, ExecutionStatus) else execution_status,
        "tool_class": tool_class,
        "governance_status": governance_status.value if isinstance(governance_status, GovernanceStatus) else governance_status,
        "artifact_status": artifact_status.value if isinstance(artifact_status, ArtifactStatus) else artifact_status,
        "primary_artifact": primary_artifact,
        "claim_tag": claim_tag,
        "claim_state": claim_state,
        "confidence_band": confidence_band or {"p10": 0.0, "p50": 0.0, "p90": 0.0},
        "physics_guard": physics_guard or {"guard_passed": True, "physics_version": "geox-v2026.05.01"},
        "uncertainty": uncertainty,
        "evidence_refs": evidence_refs or [],
        "audit_receipt": audit_receipt or {
            "vault999_ref": "VAULT999-PENDING",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "geox-anon",
        },
        "humility_score": humility_score,
        "maruah_flag": maruah_flag or {"maruah_flag": "CLEAR", "territory_risk": "none", "recommended_action": "Proceed with standard consent protocols.", "confidence": "HIGH"},
        "diagnostics": diagnostics or {}
    }

    if ui_resource_uri:
        response["_meta"] = {
            "ui": {
                "resourceUri": ui_resource_uri
            }
        }

    return response
