"""
geox_contradiction_scan — Contradiction Detection & Classification
═════════════════════════════════════════════════════════════════

Wraps the13-type contradiction ontology (epistemic/contradiction_ontology.py)
as an MCP tool for cross-claim contradiction detection.

Scans pairs of claims or claim+evidence for contradictions, classifies
them by type, severity, and resolution path.

Contradiction types (13):
  MEASUREMENT_CONFLICT, DATUM_CONFLICT, MODEL_PHYSICS_VIOLATION,
  INTERPRETATION_OBSERVATION_MISMATCH, MODEL_MEASUREMENT_MISMATCH,
  JUDGMENT_EVIDENCE_CONFLICT, NARRATIVE_OVERRUN, CROSS_MODAL_CONFLICT,
  MISSING_GROUNDING, BEAUTIFUL_ONE_DRIFT, CIRCULAR_REASONING,
  STRUCTURAL_COHERENCE_VIOLATION, UNKNOWN

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from geox_mcp.epistemic.contradiction_ontology import (
    CONTRADICTION_RESOLUTION,
    CONTRADICTION_SEVERITY,
    ContradictionRecord,
    ContradictionSeverity,
    ContradictionType,
    ResolutionPath,
)

logger = logging.getLogger("geox.contradiction_scan")


def _classify_contradiction(
    claim_a: dict[str, Any],
    claim_b: dict[str, Any],
) -> tuple[ContradictionType, str]:
    """Classify the contradiction type between two claims.

    Returns (type, reason) tuple.
    """
    a_text = claim_a.get("text", claim_a.get("claim_text", ""))
    b_text = claim_b.get("text", claim_b.get("claim_text", ""))
    a_tool = claim_a.get("tool", "unknown")
    b_tool = claim_b.get("tool", "unknown")
    a_rung = claim_a.get("epistemic_rung", 5)
    b_rung = claim_b.get("epistemic_rung", 5)
    a_type = claim_a.get("type", "").lower()
    b_type = claim_b.get("type", "").lower()

    # CIRCULAR_REASONING: claims reference each other
    if a_text and b_text and a_text in b_text and b_text in a_text:
        return ContradictionType.CIRCULAR_REASONING, "Claims reference each other"

    # MEASUREMENT_CONFLICT: two measurements disagree
    if a_tool in ("petrophysics", "seismic_compute") and b_tool in ("petrophysics", "seismic_compute"):
        if claim_a.get("value") and claim_b.get("value"):
            if abs(claim_a["value"] - claim_b["value"]) > claim_a.get("tolerance", 0.1):
                return ContradictionType.MEASUREMENT_CONFLICT, f"Values differ: {claim_a['value']} vs {claim_b['value']}"

    # MODEL_PHYSICS_VIOLATION: model output violates physics
    if "physics" in a_type or "model" in a_type:
        if claim_a.get("violates_constraint"):
            return ContradictionType.MODEL_PHYSICS_VIOLATION, claim_a["violates_constraint"]

    # INTERPRETATION_OBSERVATION_MISMATCH
    if "interpretation" in a_type and "observation" in b_type:
        return ContradictionType.INTERPRETATION_OBSERVATION_MISMATCH, "Interpretation contradicts observation"
    if "observation" in a_type and "interpretation" in b_type:
        return ContradictionType.INTERPRETATION_OBSERVATION_MISMATCH, "Observation contradicts interpretation"

    # CROSS_MODAL_CONFLICT: same object, different modalities
    a_modality = claim_a.get("modality", "")
    b_modality = claim_b.get("modality", "")
    if a_modality and b_modality and a_modality != b_modality:
        if claim_a.get("ref") == claim_b.get("ref"):
            return (
                ContradictionType.CROSS_MODAL_CONFLICT,
                f"Same ref ({claim_a['ref']}) contradicts across {a_modality} vs {b_modality}",
            )

    # MISSING_GROUNDING: claim has no lower-rung support
    if a_rung >= 5 and not claim_a.get("evidence_refs"):
        return ContradictionType.MISSING_GROUNDING, f"Claim at rung {a_rung} with no evidence refs"

    # NARRATIVE_OVERRUN: story exceeds grounding
    if "narrative" in a_type or "story" in a_type:
        if a_rung > b_rung + 2:
            return ContradictionType.NARRATIVE_OVERRUN, f"Narrative rung {a_rung} exceeds evidence rung {b_rung} by >2"

    # BEAUTIFUL_ONE_DRIFT: rhetorical coherence exceeds evidence
    if claim_a.get("confidence", 0) > 0.9 and a_rung > 3:
        return ContradictionType.BEAUTIFUL_ONE_DRIFT, f"High confidence ({claim_a['confidence']}) at rung {a_rung}"

    # Default
    return ContradictionType.UNKNOWN, "Unable to classify contradiction automatically"


def _build_record(
    claim_a: dict[str, Any],
    claim_b: dict[str, Any],
    contradiction_type: ContradictionType,
    reason: str,
    session_id: str,
) -> dict[str, Any]:
    """Build a contradiction record from classification result."""
    severity = CONTRADICTION_SEVERITY.get(contradiction_type, ContradictionSeverity.MEDIUM)
    resolution = CONTRADICTION_RESOLUTION.get(contradiction_type, ResolutionPath.ESCALATE)

    a_rung = claim_a.get("epistemic_rung", 5)
    b_rung = claim_b.get("epistemic_rung", 5)

    # Lower rung wins (iron law)
    if a_rung <= b_rung:
        winning, losing = claim_a, claim_b
        win_rung, lose_rung = a_rung, b_rung
    else:
        winning, losing = claim_b, claim_a
        win_rung, lose_rung = b_rung, a_rung

    record = ContradictionRecord(
        contradiction_id=str(uuid.uuid4())[:12],
        contradiction_type=contradiction_type,
        severity=severity,
        resolution_path=resolution,
        claim_a=claim_a.get("text", claim_a.get("claim_text", ""))[:200],
        claim_a_rung=a_rung,
        claim_a_tool=claim_a.get("tool", "unknown"),
        claim_b=claim_b.get("text", claim_b.get("claim_text", ""))[:200],
        claim_b_rung=b_rung,
        claim_b_tool=claim_b.get("tool", "unknown"),
        winning_claim=winning.get("text", winning.get("claim_text", ""))[:200],
        winning_rung=win_rung,
        losing_claim=losing.get("text", losing.get("claim_text", ""))[:200],
        losing_rung=lose_rung,
        verdict=resolution.value.upper(),
        resolution_notes=reason,
        session_id=session_id,
    )

    return record.to_dict()


async def geox_contradiction_scan(
    claims: list[dict[str, Any]],
    mode: str = "pairwise",
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Scan a set of claims for contradictions using the13-type ontology.

    Args:
        claims: List of claims to scan. Each claim dict should have:
            - text/claim_text: the claim statement
            - type: claim type (observation, interpretation, etc.)
            - tool: source tool name
            - epistemic_rung: 1-7 (1=measurement, 7=narrative)
            - evidence_refs: list of evidence references (optional)
            - modality: data modality (optional)
            - ref: reference ID for cross-modal matching (optional)
            - confidence: 0-1 confidence (optional)
            - value: numeric value for measurement claims (optional)
            - tolerance: tolerance for measurement comparison (optional)
        mode: Scan mode:
            - pairwise: compare all pairs (O(n²))
            - sequential: compare adjacent pairs only (O(n))
        session_id: MCP session ID.
        actor_id: Actor ID for audit trail.

    Returns:
        Structured scan result with contradictions, severity summary,
        and888_HOLD trigger if FATAL contradictions found.
    """
    sid = session_id or "unknown"
    contradictions = []

    if mode == "pairwise":
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                ctype, reason = _classify_contradiction(claims[i], claims[j])
                if ctype != ContradictionType.UNKNOWN:
                    record = _build_record(claims[i], claims[j], ctype, reason, sid)
                    contradictions.append(record)
    elif mode == "sequential":
        for i in range(len(claims) - 1):
            ctype, reason = _classify_contradiction(claims[i], claims[i + 1])
            if ctype != ContradictionType.UNKNOWN:
                record = _build_record(claims[i], claims[i + 1], ctype, reason, sid)
                contradictions.append(record)

    # Severity summary
    fatal_count = sum(1 for c in contradictions if c["severity"] == "fatal")
    high_count = sum(1 for c in contradictions if c["severity"] == "high")
    medium_count = sum(1 for c in contradictions if c["severity"] == "medium")
    low_count = sum(1 for c in contradictions if c["severity"] in ("low", "negligible"))

    # Overall verdict
    if fatal_count > 0:
        overall = "VOID"
        hold = True
    elif high_count > 0:
        overall = "HOLD"
        hold = True
    elif medium_count > 0:
        overall = "FLAG"
        hold = False
    else:
        overall = "CLEAR"
        hold = False

    return {
        "tool": "geox_contradiction_scan",
        "mode": mode,
        "claims_scanned": len(claims),
        "contradictions_found": len(contradictions),
        "overall_verdict": overall,
        "888_HOLD": hold,
        "severity_summary": {
            "fatal": fatal_count,
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
        },
        "contradictions": contradictions,
        "ontology_types": [t.value for t in ContradictionType],
    }
