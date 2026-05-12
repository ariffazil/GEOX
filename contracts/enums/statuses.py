from typing import List, Dict, Any, Optional
from enum import Enum
import os

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

class EvidenceTag(str, Enum):
    EVIDENCE_DIRECT = "EVIDENCE_DIRECT"
    EVIDENCE_MULTI_ZONE = "EVIDENCE_MULTI_ZONE"
    INTERPRET_FROM_LITHOLOGY = "INTERPRET_FROM_LITHOLOGY"
    SOURCE_UNRESOLVED = "SOURCE_UNRESOLVED"
    NN_NOT_PARSED = "NN_NOT_PARSED"
    NO_GDE_SOURCE = "NO_GDE_SOURCE"
    GDE_NOT_MAPPED = "GDE_NOT_MAPPED"
    PROXY_FROM_CONTEXT = "PROXY_FROM_CONTEXT"
    UNKNOWN = "UNKNOWN"

class LithoClass(str, Enum):
    CARBONATE = "CARBONATE"
    HETEROLITHIC = "HETEROLITHIC"
    SAND_PRONE = "SAND_PRONE"
    SILT_PRONE = "SILT_PRONE"
    SHALE_PRONE = "SHALE_PRONE"
    COAL_CARBONACEOUS = "COAL_CARBONACEOUS"
    MIXED_OR_UNSPECIFIED = "MIXED_OR_UNSPECIFIED"
    UNKNOWN = "UNKNOWN"

class VerticalTrend(str, Enum):
    DEEPENING_UPWARD = "DEEPENING_UPWARD"
    SHALLOWING_UPWARD = "SHALLOWING_UPWARD"
    STABLE_OR_AMBIGUOUS = "STABLE_OR_AMBIGUOUS"
    UNKNOWN = "UNKNOWN"

class DepthBasis(str, Enum):
    MD = "MD"
    TVD = "TVD"
    TVDSS = "TVDSS"

class PerceptionClass(str, Enum):
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    DISPLAY = "DISPLAY"
    CORROBORATED = "CORROBORATED"
    HYPOTHESIS = "HYPOTHESIS"

# EARTH.CANON_9 — Nine invariant subsurface quantities
# Every tool that touches subsurface data declares which it reads/writes/constrains.
class Canon9(str, Enum):
    RHO = "rho"          # Bulk density (ρ)
    VP = "Vp"            # P-wave velocity
    VS = "Vs"            # S-wave velocity
    RHO_E = "rho_e"      # Electrical resistivity (ρₑ)
    CHI = "chi"          # Magnetic susceptibility (χ)
    K = "k"              # Permeability
    P = "P"              # Pressure
    T = "T"              # Temperature
    PHI = "phi"          # Porosity (φₜ vs φₑ)

# Which tools touch which Canon9 quantities
CANON9_TOOL_MAP: dict[str, list[str]] = {
    "geox_data_ingest_bundle": ["rho", "rho_e", "phi"],
    "geox_data_qc_bundle":     ["rho", "Vp", "Vs", "rho_e", "chi", "k", "P", "T", "phi"],
    "geox_subsurface_generate_candidates": ["rho", "rho_e", "phi", "k"],
    "geox_subsurface_verify_integrity":    ["Vp", "Vs", "rho", "phi"],
    "geox_seismic_analyze_volume":         ["Vp", "Vs", "rho"],
    "geox_section_interpret_correlation":  [],
    "geox_map_context_scene":              ["chi"],
    "geox_time4d_analyze_system":          ["P", "T"],
    "geox_prospect_evaluate":              ["k", "phi"],
    "geox_prospect_judge_preview":         [],
    "geox_prospect_judge_seal":            [],
    "geox_evidence_summarize_cross":       [],
    "geox_system_registry_status":         [],
    "geox_history_audit":                  [],
    "geox_dst_ingest_test":                ["k", "P", "T"],
}

# Stratigraphic standard schemes (Kinabalu Basin NN-anchor)
class StratStandard(str, Enum):
    NN_ZONE = "NN_zone"
    NP_ZONE = "NP_zone"
    STAGE_SABAH = "Stage_Sabah"
    CYCLE_SARAWAK = "Cycle_Sarawak"
    CUSTOM = "custom"

# GDE (Geological Depositional Environment) vocabulary
GDE_VOCAB: list[dict[str, Any]] = [
    {"pattern": "alluvial|fluvial|floodplain",   "code": "2026_COL",   "label": "Continental / alluvial plain",         "index": 0, "rationale": "Continental fluvial to floodplain system"},
    {"pattern": "lower coastal|coastal plain",   "code": "2026_LCP",   "label": "Lower coastal plain",                  "index": 1, "rationale": "Coastal plain to paralic transition"},
    {"pattern": "supralittoral|littoral|beach|shoreface", "code": "2026_LIT", "label": "Littoral / shoreface",   "index": 2, "rationale": "Littoral to shoreface belt"},
    {"pattern": "intertidal|tidal|estuar|lagoon|mangrove", "code": "2026_TIDAL", "label": "Tidal flat / estuarine", "index": 3, "rationale": "Tidal-flat, estuarine, or restricted marginal marine"},
    {"pattern": "inner neritic|inner sublittoral", "code": "2026_HIN", "label": "Inner neritic",                "index": 4, "rationale": "Shallow marine inner shelf"},
    {"pattern": "middle neritic|middle sublittoral", "code": "2026_HMN", "label": "Middle neritic",              "index": 5, "rationale": "Open marine middle shelf"},
    {"pattern": "outer neritic|outer sublittoral",   "code": "2026_HON", "label": "Outer neritic",              "index": 6, "rationale": "Open marine outer shelf"},
    {"pattern": "upper.*bathyal",                   "code": "2026_UBT", "label": "Upper bathyal",                "index": 7, "rationale": "Upper slope / deep marine"},
    {"pattern": "middle.*bathyal",                  "code": "2026_MBT", "label": "Middle bathyal",               "index": 8, "rationale": "Middle slope / deep marine"},
    {"pattern": "lower.*bathyal",                   "code": "2026_LBT", "label": "Lower bathyal",                "index": 9, "rationale": "Lower slope to basin-floor deep marine"},
    {"pattern": "bathyal",                          "code": "2026_UBT-MBT", "label": "Bathyal undifferentiated", "index": 8, "rationale": "Deep marine bathyal setting"},
    {"pattern": "marine",                           "code": "2026_MARINE", "label": "Marine undifferentiated",    "index": 5, "rationale": "Marine, depth not tightly constrained"},
]

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
    "geox_prospect_judge_preview",
    "geox_prospect_judge_seal",
    "geox_prospect_judge_verdict",
    "geox_evidence_summarize_cross",
    "geox_system_registry_status",
    "geox_history_audit",
]
SEAL = "DITEMPA BUKAN DIBERI"

def enforce_claim_state(
    result: Dict[str, Any],
    evidence_refs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """F2 Truth + F7 Humility: prevent semantic overclaiming.

    Hard rules:
    - No evidence_refs → artifact_status cannot be VERIFIED or SEAL
    - claim_state HYPOTHESIS/INGESTED/NO_VALID_EVIDENCE → artifact_status must be DRAFT or lower
    - confidence_band must be None (or have computed=False) when no evidence
    """
    refs = evidence_refs or result.get("evidence_refs") or []
    artifact_status = result.get("artifact_status", "DRAFT")
    claim_state = result.get("claim_state", "INGESTED")

    if not refs and artifact_status in ("VERIFIED", "SEAL", "COMPUTED"):
        result["artifact_status"] = "DRAFT"
        result["_claim_corrected"] = {
            "reason": "No evidence_refs supplied — downgraded from overclaimed status",
            "original_status": artifact_status,
        }

    if claim_state in ("HYPOTHESIS", "INGESTED", "NO_VALID_EVIDENCE") and artifact_status == "VERIFIED":
        result["artifact_status"] = "DRAFT"
        result["_claim_corrected"] = {
            "reason": "claim_state contradicts artifact_status",
            "original_status": "VERIFIED",
        }

    return result


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
    confidence_band: Optional[Dict[str, Any]] = None,
    physics_guard: Optional[Dict[str, Any]] = None,
    audit_receipt: Optional[Dict[str, str]] = None,
    humility_score: float = 0.0,
    maruah_flag: Optional[Dict[str, Any]] = None,
    tool_version: Optional[str] = None,
    artifact_hash: Optional[str] = None,
    depth_basis: Optional[str] = None,
    depth_datum: Optional[str] = None,
    # ToAC perception bridge fields
    perception_class: Optional[str] = None,
    evidence_tag: Optional[str] = None,
    canon_9_touched: Optional[List[str]] = None,
    vertical_trend: Optional[str] = None,
    litho_class: Optional[str] = None,
    strat_standard: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Canonical MCP Apps Response Envelope — Universal Output Contract v0.7.
    MCP 2025-11-25 alignment: provenance block, structuredContent contract.
    ToAC v1: perception bridge, evidence tag, CANON_9, vertical trend, litho class.

    Required fields: claim_tag, claim_state, confidence_band, physics_guard, evidence_refs,
    uncertainty, provenance, humility_score (F7), maruah_flag (F6).

    Lifecycle claim_state values:
        NO_VALID_EVIDENCE    — no evidence supplied
        INGESTED             — artifact received, not yet QC'd
        QC_VERIFIED         — passed QC gate (Tool 02)
        PLOTTED             — visual artifact produced
        INTERPRETED         — interpretation applied
        DERIVED_CANDIDATE   — derived from QC'd evidence
        SEALED              — irreversible constitutional adjudication
        JUDGE_PREVIEW       — non-binding advisory preview
        888_HOLD           — governance pause
        VOID               — physics/logic breach

    perception_class: ToAC bridge (MEASURED → DERIVED → DISPLAY → CORROBORATED → HYPOTHESIS)
    evidence_tag: Per-output-field evidence provenance tag
    canon_9_touched: Which EARTH.CANON_9 quantities this output touches
    vertical_trend: DEEPENING_UPWARD / SHALLOWING_UPWARD / STABLE_OR_AMBIGUOUS
    litho_class: Canonical lithology classification
    strat_standard: Stratigraphic reference scheme + chart URI
    """
    from datetime import datetime, timezone

    tool_version = tool_version or os.environ.get("GEOX_VERSION", "geox-v2026.05.10")
    now = datetime.now(timezone.utc).isoformat()

    provenance = {
        "tool_name": primary_artifact.get("tool", "unknown"),
        "tool_version": tool_version,
        "artifact_hash": artifact_hash or "",
        "claim_state": claim_state,
        "depth_basis": depth_basis or "MD",
        "depth_datum": depth_datum or "",
        "timestamp_utc": now,
        "evidence_refs": evidence_refs or [],
        "session_id": audit_receipt.get("session_id", "geox-anon") if audit_receipt else "geox-anon",
    }

    response = {
        "execution_status": execution_status.value if isinstance(execution_status, ExecutionStatus) else execution_status,
        "tool_class": tool_class,
        "governance_status": governance_status.value if isinstance(governance_status, GovernanceStatus) else governance_status,
        "artifact_status": artifact_status.value if isinstance(artifact_status, ArtifactStatus) else artifact_status,
        "primary_artifact": primary_artifact,
        "claim_tag": claim_tag,
        "claim_state": claim_state,
        "confidence_band": confidence_band,
        "physics_guard": physics_guard or {"guard_passed": True, "physics_version": "geox-v2026.05.10"},
        "uncertainty": uncertainty,
        "evidence_refs": evidence_refs or [],
        "audit_receipt": audit_receipt or {
            "vault999_ref": "VAULT999-PENDING",
            "timestamp": now,
            "session_id": "geox-anon",
        },
        "humility_score": humility_score,
        "maruah_flag": maruah_flag or {"maruah_flag": "CLEAR", "territory_risk": "none", "recommended_action": "Proceed with standard consent protocols.", "confidence": "HIGH"},
        "diagnostics": diagnostics or {},
        "provenance": provenance,
        "schema_version": "geox-output-v0.7",
        # ToAC v1 perception fields
        "perception_class": perception_class or "HYPOTHESIS",
        "evidence_tag": evidence_tag or "UNKNOWN",
        "canon_9_touched": canon_9_touched or [],
        "vertical_trend": vertical_trend or "UNKNOWN",
        "litho_class": litho_class or "UNKNOWN",
        "strat_standard": strat_standard or {"scheme": "NN_zone", "reference_chart": ""},
    }

    # F2 Truth gate: auto-downgrade overclaimed states
    response = enforce_claim_state(response, evidence_refs=evidence_refs)

    if ui_resource_uri:
        response["_meta"] = {
            "ui": {
                "resourceUri": ui_resource_uri
            }
        }

    return response
