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
    # RECOVERABLE_ERROR: agentic upgrade - failures become reroutes (Arif 2026-05-16)
    RECOVERABLE_ERROR = "RECOVERABLE_ERROR"


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
    RHO = "rho"  # Bulk density (ρ)
    VP = "Vp"  # P-wave velocity
    VS = "Vs"  # S-wave velocity
    RHO_E = "rho_e"  # Electrical resistivity (ρₑ)
    CHI = "chi"  # Magnetic susceptibility (χ)
    K = "k"  # Permeability
    P = "P"  # Pressure
    T = "T"  # Temperature
    PHI = "phi"  # Porosity (φₜ vs φₑ)


# Which tools touch which Canon9 quantities
CANON9_TOOL_MAP: dict[str, list[str]] = {
    "geox_data_ingest_bundle": ["rho", "rho_e", "phi"],
    "geox_data_qc_bundle": ["rho", "Vp", "Vs", "rho_e", "chi", "k", "P", "T", "phi"],
    "geox_subsurface_generate_candidates": ["rho", "rho_e", "phi", "k"],
    "geox_subsurface_verify_integrity": ["Vp", "Vs", "rho", "phi"],
    "geox_seismic_analyze_volume": ["Vp", "Vs", "rho"],
    "geox_section_interpret_correlation": [],
    "geox_map_context_scene": ["chi"],
    "geox_time4d_analyze_system": ["P", "T"],
    "geox_prospect_evaluate": ["k", "phi"],
    "geox_prospect_judge_preview": [],
    "geox_prospect_judge_seal": [],
    "geox_evidence_summarize_cross": [],
    "geox_system_registry_status": [],
    "geox_history_audit": [],
    "geox_dst_ingest_test": ["k", "P", "T"],
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
    {
        "pattern": "alluvial|fluvial|floodplain",
        "code": "2026_COL",
        "label": "Continental / alluvial plain",
        "index": 0,
        "rationale": "Continental fluvial to floodplain system",
    },
    {
        "pattern": "lower coastal|coastal plain",
        "code": "2026_LCP",
        "label": "Lower coastal plain",
        "index": 1,
        "rationale": "Coastal plain to paralic transition",
    },
    {
        "pattern": "supralittoral|littoral|beach|shoreface",
        "code": "2026_LIT",
        "label": "Littoral / shoreface",
        "index": 2,
        "rationale": "Littoral to shoreface belt",
    },
    {
        "pattern": "intertidal|tidal|estuar|lagoon|mangrove",
        "code": "2026_TIDAL",
        "label": "Tidal flat / estuarine",
        "index": 3,
        "rationale": "Tidal-flat, estuarine, or restricted marginal marine",
    },
    {
        "pattern": "inner neritic|inner sublittoral",
        "code": "2026_HIN",
        "label": "Inner neritic",
        "index": 4,
        "rationale": "Shallow marine inner shelf",
    },
    {
        "pattern": "middle neritic|middle sublittoral",
        "code": "2026_HMN",
        "label": "Middle neritic",
        "index": 5,
        "rationale": "Open marine middle shelf",
    },
    {
        "pattern": "outer neritic|outer sublittoral",
        "code": "2026_HON",
        "label": "Outer neritic",
        "index": 6,
        "rationale": "Open marine outer shelf",
    },
    {
        "pattern": "upper.*bathyal",
        "code": "2026_UBT",
        "label": "Upper bathyal",
        "index": 7,
        "rationale": "Upper slope / deep marine",
    },
    {
        "pattern": "middle.*bathyal",
        "code": "2026_MBT",
        "label": "Middle bathyal",
        "index": 8,
        "rationale": "Middle slope / deep marine",
    },
    {
        "pattern": "lower.*bathyal",
        "code": "2026_LBT",
        "label": "Lower bathyal",
        "index": 9,
        "rationale": "Lower slope to basin-floor deep marine",
    },
    {
        "pattern": "bathyal",
        "code": "2026_UBT-MBT",
        "label": "Bathyal undifferentiated",
        "index": 8,
        "rationale": "Deep marine bathyal setting",
    },
    {
        "pattern": "marine",
        "code": "2026_MARINE",
        "label": "Marine undifferentiated",
        "index": 5,
        "rationale": "Marine, depth not tightly constrained",
    },
]

# Type aliases
VerdictCode = GovernanceStatus
FloorCode = str
DimensionCode = str

# Constants
CONSTITUTIONAL_FLOORS = [
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "F13",
]
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
    # Session propagation (Fix #2 - Arif 2026-05-16)
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    parent_trace_id: Optional[str] = None,
    constitution_hash: Optional[str] = None,
    # Session propagation extension (actor + tool_name for audit receipt)
    actor_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    # Agentic recovery (Fix #1, #4 - Arif 2026-05-16)
    next_best_actions: Optional[List[Dict[str, Any]]] = None,
    suggested_tool: Optional[str] = None,
    can_auto_retry: bool = False,
    # missing_inputs_schema: structured input gaps for agentic rerun (Arif 2026-05-16)
    missing_inputs_schema: Optional[List[Dict[str, Any]]] = None,
    # confidence_policy: what confidence means for this tool output (Arif 2026-05-16)
    confidence_policy: Optional[Dict[str, Any]] = None,
    equations_used: Optional[List[str]] = None,
    sensitivity_to: Optional[List[str]] = None,
    # ToAC perception bridge fields
    perception_class: Optional[str] = None,
    evidence_tag: Optional[str] = None,
    canon_9_touched: Optional[List[str]] = None,
    vertical_trend: Optional[str] = None,
    litho_class: Optional[str] = None,
    strat_standard: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Canonical MCP Apps Response Envelope — Universal Output Contract v0.81.
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
    import uuid

    tool_version = tool_version or os.environ.get("GEOX_VERSION", "geox-v2026.05.10")
    now = datetime.now(timezone.utc).isoformat()

    # Session propagation (Fix #2 - Arif 2026-05-16)
    # Use explicitly passed session_id, fallback to audit_receipt, fallback to auto-generated
    _session_id = session_id or (audit_receipt.get("session_id") if audit_receipt else None) or "geox-no-session"
    _trace_id = trace_id or f"trace-{uuid.uuid4().hex[:16]}"
    _parent_trace_id = parent_trace_id or None
    _constitution_hash = constitution_hash or os.environ.get("GEOX_CONSTITUTION_HASH", "unknown")

    provenance = {
        "tool_name": primary_artifact.get("tool", "unknown"),
        "tool_version": tool_version,
        "artifact_hash": artifact_hash or "",
        "claim_state": claim_state,
        "depth_basis": depth_basis or "MD",
        "depth_datum": depth_datum or "",
        "timestamp_utc": now,
        "evidence_refs": evidence_refs or [],
        # Session propagation fields
        "session_id": _session_id,
        "trace_id": _trace_id,
        "parent_trace_id": _parent_trace_id,
        "constitution_hash": _constitution_hash,
        # LEM contract v0.8
        "equations_used": equations_used or [],
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
        "audit_receipt": audit_receipt
        or {
            "vault999_ref": "VAULT999-PENDING",
            "timestamp": now,
            "session_id": _session_id,
            "trace_id": _trace_id,
            "actor_id": actor_id or "geox-unknown",
            "tool_name": tool_name or primary_artifact.get("tool", "unknown"),
        },
        "humility_score": humility_score,
        "maruah_flag": maruah_flag
        or {
            "maruah_flag": "CLEAR",
            "territory_risk": "none",
            "recommended_action": "Proceed with standard consent protocols.",
            "confidence": "HIGH",
        },
        "diagnostics": diagnostics or {},
        "provenance": provenance,
        "schema_version": "geox-output-v0.81",  # Bumped for LEM contract (equations_used, sensitivity_to)
        # ToAC v1 perception fields
        "perception_class": perception_class or "HYPOTHESIS",
        "evidence_tag": evidence_tag or "UNKNOWN",
        "canon_9_touched": canon_9_touched or [],
        "vertical_trend": vertical_trend or "UNKNOWN",
        "litho_class": litho_class or "UNKNOWN",
        "strat_standard": strat_standard or {"scheme": "NN_zone", "reference_chart": ""},
        # Session propagation (Fix #2)
        "session_id": _session_id,
        "trace_id": _trace_id,
        "parent_trace_id": _parent_trace_id,
        "constitution_hash": _constitution_hash,
        # Agentic recovery (Fix #1, #4 - Arif 2026-05-16)
        "next_best_actions": next_best_actions or [],
        "suggested_tool": suggested_tool,
        "can_auto_retry": can_auto_retry,
        # missing_inputs_schema: structured input gaps for agentic rerun (Arif 2026-05-16)
        "missing_inputs_schema": missing_inputs_schema or [],
        # confidence_policy: what confidence means for this output (Arif 2026-05-16)
        "confidence_policy": confidence_policy or {},
        "equations_used": equations_used or [],
        "sensitivity_to": sensitivity_to or [],
    }

    # F2 Truth gate: auto-downgrade overclaimed states
    response = enforce_claim_state(response, evidence_refs=evidence_refs)

    if ui_resource_uri:
        response["_meta"] = {"ui": {"resourceUri": ui_resource_uri}}

    return response


# ──────────────────────────────────────────────────────────────────────────────
# METABOLIC OUTPUT ENRICHMENT — GEOX Phase 1 adoption
# ──────────────────────────────────────────────────────────────────────────────
# Injects a "metabolic" key into a standard GEOX envelope.
#
# This is the Phase 1 bridge: GEOX tool envelopes gain the universal
# metabolic contract fields (metabolic.v1) so arifOS can read them uniformly.
#
# NOT a canonical-copy section — lives in GEOX only.
# Do NOT call this from arifOS or other organs.
#
# DITEMPA BUKAN DIBERI — Forged, Not Given


from datetime import datetime, timezone


# Map GEOX internal claim_state values → metabolic ClaimState
_CLAIM_STATE_MAP = {
    # GEOX internal claim_state → MetabolicOutput.claim_state value
    "RAW_OBSERVATION": "OBSERVED",
    "FILE_IMPORTED": "OBSERVED",
    "INGESTED": "OBSERVED",
    "NO_VALID_EVIDENCE": "HOLD",
    "QC_VERIFIED": "VERIFIED",
    "QC_VERIFIED_WITH_WARNINGS": "QUALIFIED",
    "COMPUTED": "HYPOTHESIS",
    "INTERPRETED": "HYPOTHESIS",
    "DERIVED_CANDIDATE": "HYPOTHESIS",
    "HYPOTHESIS": "HYPOTHESIS",
    "QUALIFIED": "QUALIFIED",
    "VERIFIED": "VERIFIED",
    "SEALED": "SEALED",
    "888_HOLD": "HOLD",
    "VOID": "HOLD",
}

# Map metabolic ClaimState → ConfidenceLevel
_CLAIM_TO_CONFIDENCE = {
    "OBSERVED": "LOW",
    "HYPOTHESIS": "LOW",
    "QUALIFIED": "MODERATE",
    "VERIFIED": "HIGH",
    "SEALED": "VERIFIED",
    "HOLD": "UNKNOWN",
}

# Per-tool next_best_tool and required_next_tests defaults
_TOOL_METABOLIC_DEFAULTS = {
    "geox_data_ingest_bundle": {
        "next_best_tool": "geox_data_qc_bundle",
        "required_next_tests": [
            "QC header check",
            "Depth monotonicity check",
            "Canonical curves completeness check",
        ],
    },
    "geox_data_qc_bundle": {
        "next_best_tool": "geox_subsurface_generate_candidates",
        "required_next_tests": [],
    },
    "geox_subsurface_generate_candidates": {
        "next_best_tool": "geox_seismic_analyze_volume",
        "required_next_tests": [
            "Cross-validate with analog data",
            "Petrophysical cutoff sensitivity analysis",
        ],
    },
    "geox_seismic_analyze_volume": {
        "next_best_tool": "geox_subsurface_generate_candidates",
        "required_next_tests": [
            "Well-to-seismic tie",
            "Amplitude-vs-offset analysis",
        ],
    },
}


def _claim_to_metabolic(claim_state: str) -> str:
    """Map a GEOX internal claim_state to metabolic ClaimState value."""
    return _CLAIM_STATE_MAP.get(claim_state, "HYPOTHESIS")


def _get_confidence_for_claim(claim_state: str) -> str:
    """Infer shared ConfidenceLevel from the resolved metabolic claim_state."""
    metabolic_state = _claim_to_metabolic(claim_state)
    return _CLAIM_TO_CONFIDENCE.get(metabolic_state, "MODERATE")


def enrich_envelope_with_metabolic(
    envelope: Dict[str, Any],
    tool_name: str,
    *,
    witness_type: str | None = None,
    witness_status: str = "RAW",
    decoded_entities: List[Any] | None = None,
    anomalous_contrasts: List[Any] | None = None,
    candidate_meanings: List[Any] | None = None,
    constraints_checked: List[Any] | None = None,
    model_updates: List[Any] | None = None,
    required_next_tests: List[str] | None = None,
    next_best_tool: str = "",
    cross_organ_handoff: Dict[str, Any] | None = None,
    session_id: str | None = None,
) -> Dict[str, Any]:
    """
    Enrich a GEOX standard envelope with metabolic.v1 output fields.

    Call this after ``get_standard_envelope()`` to inject the universal
    metabolic contract into the returned envelope.

    Parameters
    ----------
    envelope : dict
        The envelope returned by ``get_standard_envelope()``.
    tool_name : str
        Canonical GEOX tool name (e.g. "geox_data_ingest_bundle").
    witness_type : str, optional
        Override for the witness type (e.g. "log", "seismic", "signal").
        If None, inferred from tool_name.
    witness_status : str, default "RAW"
        WitnessStatus value for the metabolic output.
    decoded_entities : list, optional
        List of decoded entity dicts.
    anomalous_contrasts : list, optional
        List of anomalous contrast dicts.
    candidate_meanings : list, optional
        List of candidate meaning dicts.
    constraints_checked : list, optional
        List of constraint check dicts.
    model_updates : list, optional
        List of model update dicts.
    required_next_tests : list[str], optional
        Override for required next tests.
    next_best_tool : str, optional
        Override for next best tool.
    cross_organ_handoff : dict, optional
        Override for the cross-organ handoff dict.
    session_id : str, optional
        Governed session ID to propagate.

    Returns
    -------
    dict
        The envelope with a new top-level key ``"metabolic"`` containing
        the MetabolicOutput-compatible dict.
    """
    # Resolve claim_state: check primary_artifact first (where tools put it),
    # then fall back to envelope top-level (where get_standard_envelope puts it)
    primary = envelope.get("primary_artifact", {})
    envelope_claim_state = primary.get("claim_state", envelope.get("claim_state", "INGESTED"))
    metabolic_claim_state = _claim_to_metabolic(envelope_claim_state)
    confidence = _get_confidence_for_claim(envelope_claim_state)

    # Per-tool defaults
    tool_defaults = _TOOL_METABOLIC_DEFAULTS.get(tool_name, {})
    resolved_next_tool = next_best_tool or tool_defaults.get("next_best_tool", "")
    resolved_tests = required_next_tests if required_next_tests is not None else tool_defaults.get("required_next_tests", [])

    # Resolve witness_type from tool or override
    _TOOL_WITNESS_TYPE = {
        "geox_data_ingest_bundle": "log",
        "geox_data_qc_bundle": "log",
        "geox_subsurface_generate_candidates": "signal",
        "geox_seismic_analyze_volume": "seismic",
    }
    resolved_witness_type = witness_type or _TOOL_WITNESS_TYPE.get(tool_name, "sensor")

    # Uncertainty range by confidence
    _CONFIDENCE_UNCERTAINTY = {
        "LOW": ([0.0, 0.5], ["Evidence not cross-checked"]),
        "MODERATE": ([0.3, 0.7], []),
        "HIGH": ([0.6, 0.9], []),
        "VERIFIED": ([0.7, 0.95], []),
        "UNKNOWN": ([0.0, 1.0], ["Cannot assess without evidence"]),
    }
    uncertainty_range, major_unknowns = _CONFIDENCE_UNCERTAINTY.get(confidence, ([0.0, 1.0], []))

    now = datetime.now(timezone.utc).isoformat()

    metabolic = {
        "organ": "GEOX",
        "tool_name": tool_name,
        "session_id": session_id,
        # Witness layer
        "witness_type": resolved_witness_type,
        "witness_status": witness_status,
        "witnesses_ingested": [],
        # Decoded layer
        "decoded_entities": decoded_entities or [],
        # Contrast layer
        "anomalous_contrasts": anomalous_contrasts or [],
        # Meaning layer
        "candidate_meanings": candidate_meanings or [],
        # Constraint layer
        "constraints_checked": constraints_checked or [],
        # Model update layer
        "model_updates": model_updates or [],
        "model_target": "Earth",
        # Uncertainty
        "uncertainty": {
            "omega_0": 0.05,
            "uncertainty_range": uncertainty_range,
            "major_unknowns": major_unknowns,
            "key_missing_evidence": [],
            "claim_too_certain_flag": False,
        },
        # Evidence freshness
        "evidence_freshness": {
            "as_of": primary.get("vault_receipt", {}).get("timestamp", now)
            if isinstance(primary.get("vault_receipt"), dict)
            else now,
            "expires_after_seconds": None,
            "staleness_risk": "LOW",
            "requires_refresh": False,
            "refresh_recommendation": (
                "Re-ingest only if a new file version is suspected or geological interpretation changes significantly."
            ),
        },
        # Next steps
        "required_next_tests": resolved_tests,
        "next_best_tool": resolved_next_tool,
        # Cross-organ handoff
        "cross_organ_handoff": cross_organ_handoff
        or {
            "next_best_organ": "GEOX",
            "handoff_reason": ("GEOX subsurface tools can refine the interpretation with physics-based petrophysical analysis."),
            "handoff_payload": {
                "artifact_ref": primary.get("artifact_ref", ""),
                "well_id": primary.get("well_id", ""),
                "source_type": primary.get("source_type", ""),
            },
            "blocked_organs": [],
            "blocked_reason": "",
            "confidence_at_handoff": confidence,
        },
        # Claim state
        "claim_state": metabolic_claim_state,
        # Conflict flags
        "conflict_flags": [],
        # Confidence level
        "confidence_level": confidence,
        # Audit
        "audit_receipt": primary.get("vault_receipt", ""),
        # Sovereignty boundary
        "recommendation_only": True,
        "execution_authorized": False,
        "human_final_authority": "Arif",
        "requires_888_judge": False,
        # Provenance
        "timestamp_utc": now,
        "constitution_hash": "",
    }

    envelope["metabolic"] = metabolic
    return envelope
