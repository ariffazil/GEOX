"""
GEOX Process Abduction + Contradiction Scan
============================================
Tier 4 Earth Intelligence: pattern → competing process hypotheses.
Pure consumer pattern: takes evidence_refs only, never calls upstream tools.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("geox.abduction")

# ═══════════════════════════════════════════════════════════════════════════════
# GEOLOGICAL GRAMMAR — Pattern → Candidate Processes
# Each rule: pattern signature → candidate processes with priors
# DITEMPA BUKAN DIBERI
# ═══════════════════════════════════════════════════════════════════════════════

_GRAMMAR_RULES: list[dict[str, Any]] = [
    {
        "name": "coarsening_upward_clean_top",
        "patterns": {
            "gr_trend": "decreasing_upward",
            "vclay_trend": "decreasing_upward",
            "rhob_trend": "increasing_upward",
        },
        "candidates": [
            {
                "process": "shoreface progradation",
                "mechanism": "sediment supply exceeded accommodation",
                "prior": 0.35,
                "required_context": ["marine_shale_below", "clean_sand_top"],
                "expected_signatures": [
                    "offshore marine shale below interval",
                    "lateral sand continuity in seismic",
                    "low-angle offshore dip in dipmeter",
                ],
            },
            {
                "process": "delta front mouth bar",
                "mechanism": "fluvial input into standing water",
                "prior": 0.25,
                "required_context": ["distributary_channel_evidence"],
                "expected_signatures": [
                    "crevasse splay deposits nearby",
                    "interbedded shale-sand heterolithics",
                    "radial progradation in dipmeter",
                ],
            },
            {
                "process": "fan lobe progradation",
                "mechanism": "turbidity current deceleration",
                "prior": 0.15,
                "required_context": ["deepwater_context"],
                "expected_signatures": [
                    "lobe fringe shale drapes",
                    "amalgamated sand bases",
                    "no wave ripples",
                ],
            },
        ],
    },
    {
        "name": "fining_upward_blocky",
        "patterns": {
            "gr_trend": "increasing_upward",
            "vclay_trend": "increasing_upward",
            "motif": "blocky",
        },
        "candidates": [
            {
                "process": "channel fill",
                "mechanism": "fluvial or tidal channel abandonment",
                "prior": 0.40,
                "required_context": ["erosional_base"],
                "expected_signatures": [
                    "erosional base cutting underlying shale",
                    "lateral accretion surfaces in image log",
                    "abrupt top contact with overbank mud",
                ],
            },
            {
                "process": "crevasse splay",
                "mechanism": "levee breach during flood",
                "prior": 0.20,
                "required_context": ["near_channel"],
                "expected_signatures": [
                    "thinning-upward splay fringe",
                    "rooted horizons near top",
                    "proximal to channel axis",
                ],
            },
        ],
    },
    {
        "name": "high_gr_condensed",
        "patterns": {
            "gr_peak": "high",
            "thickness_m": "thin",
            "lateral_extent": "regional",
        },
        "candidates": [
            {
                "process": "maximum flooding surface",
                "mechanism": "maximum transgression and condensation",
                "prior": 0.30,
                "required_context": ["regional_correlation", "biostrat"],
                "expected_signatures": [
                    "condensed fauna / nannofossil abundance",
                    "downlap terminations on seismic",
                    "maximum gamma ray in cycle",
                ],
            },
            {
                "process": "volcanic ash bed",
                "mechanism": "airfall tephra deposition",
                "prior": 0.15,
                "required_context": ["geochemical_fingerprint"],
                "expected_signatures": [
                    "bentonite texture in core",
                    "sharp base and top",
                    "geochemical K-feldspar spike",
                ],
            },
            {
                "process": "organic-rich flooding",
                "mechanism": "high productivity + anoxia",
                "prior": 0.20,
                "required_context": ["low_rho", "high_resistivity"],
                "expected_signatures": [
                    "very high GR, low RHOB",
                    "elevated resistivity",
                    "potential source rock",
                ],
            },
        ],
    },
    {
        "name": "blocky_low_gr_cuts_shale",
        "patterns": {
            "gr_shape": "blocky",
            "gr_value": "low",
            "base_contact": "sharp",
        },
        "candidates": [
            {
                "process": "channel incision",
                "mechanism": "base-level fall or avulsion",
                "prior": 0.35,
                "required_context": ["erosional_base", "3d_seismic"],
                "expected_signatures": [
                    "erosional scour at base",
                    "lateral accretion in image log",
                    "channel-form geometry in seismic",
                ],
            },
            {
                "process": "turbidite lobe",
                "mechanism": "density flow deceleration",
                "prior": 0.20,
                "required_context": ["deepwater_context"],
                "expected_signatures": [
                    "graded bedding base",
                    "amalgamated tops",
                    "lobe fringe shales",
                ],
            },
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# EVIDENCE LOADER — Read artifacts from the artifact store
# ═══════════════════════════════════════════════════════════════════════════════

_ARTIFACT_STORE_DIR = Path("/data/geox_las")


def _load_artifact(artifact_ref: str) -> dict[str, Any]:
    """Load an artifact by reference. Supports well_las:ID and geox://artifact/ID formats."""
    # Try to find artifact file
    if artifact_ref.startswith("well_las:"):
        artifact_id = artifact_ref.replace("well_las:", "")
        # Search for matching file
        for ext in [".json", ".las", ".csv"]:
            path = _ARTIFACT_STORE_DIR / f"{artifact_id}{ext}"
            if path.exists():
                return {"ref": artifact_ref, "type": "well_las", "path": str(path)}
        return {"ref": artifact_ref, "type": "well_las", "error": "Artifact not found in store"}

    if artifact_ref.startswith("geox://artifact/"):
        artifact_id = artifact_ref.replace("geox://artifact/", "")
        for ext in [".json", ".las", ".csv"]:
            path = _ARTIFACT_STORE_DIR / f"{artifact_id}{ext}"
            if path.exists():
                return {"ref": artifact_ref, "type": "artifact", "path": str(path)}
        return {"ref": artifact_ref, "type": "artifact", "error": "Artifact not found in store"}

    # Generic / unknown ref — pass through as metadata
    return {"ref": artifact_ref, "type": "metadata", "note": "Reference-only; no file loaded"}


def _extract_evidence_summary(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract simplified evidence summary from loaded artifacts."""
    summary = {
        "gr_trend": "unknown",
        "vclay_trend": "unknown",
        "rhob_trend": "unknown",
        "motif": "unknown",
        "gr_shape": "unknown",
        "gr_value": "unknown",
        "base_contact": "unknown",
        "thickness_m": "unknown",
        "lateral_extent": "unknown",
        "has_core": False,
        "has_biostrat": False,
        "has_correlation": False,
        "well_count": 1,
    }

    for art in artifacts:
        # Parse artifact metadata for pattern hints
        meta = art.get("metadata", {})
        if isinstance(meta, dict):
            for key in summary:
                if key in meta:
                    summary[key] = meta[key]

    # Count wells from refs
    wells = set()
    for art in artifacts:
        ref = art.get("ref", "")
        if "well" in ref.lower():
            wells.add(ref)
    summary["well_count"] = max(1, len(wells))

    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# ABDUCTION ENGINE — Pattern match → rank hypotheses
# ═══════════════════════════════════════════════════════════════════════════════


def _match_rules(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Match evidence against grammar rules. Return candidate processes with scores."""
    candidates: list[dict[str, Any]] = []

    for rule in _GRAMMAR_RULES:
        match_score = 0.0
        total_patterns = len(rule["patterns"])
        for pattern_key, pattern_value in rule["patterns"].items():
            ev_value = evidence.get(pattern_key, "unknown")
            if ev_value == pattern_value:
                match_score += 1.0
            elif ev_value != "unknown" and pattern_value in str(ev_value):
                match_score += 0.5

        if match_score > 0:
            confidence_ratio = match_score / total_patterns
            for cand in rule["candidates"]:
                # Penalize if required context is missing
                context_penalty = 0.0
                missing_context = []
                for req in cand.get("required_context", []):
                    if req == "marine_shale_below" and evidence.get("has_marine_shale_below") is not True:
                        context_penalty += 0.1
                        missing_context.append(req)
                    elif req == "regional_correlation" and evidence.get("has_correlation") is not True:
                        context_penalty += 0.15
                        missing_context.append(req)
                    elif req == "biostrat" and evidence.get("has_biostrat") is not True:
                        context_penalty += 0.15
                        missing_context.append(req)
                    elif req == "core" and evidence.get("has_core") is not True:
                        context_penalty += 0.1
                        missing_context.append(req)
                    elif req == "3d_seismic" and evidence.get("has_3d_seismic") is not True:
                        context_penalty += 0.1
                        missing_context.append(req)
                    elif req == "deepwater_context" and evidence.get("depo_context") != "deepwater":
                        context_penalty += 0.1
                        missing_context.append(req)

                score = cand["prior"] * confidence_ratio - context_penalty
                score = max(0.05, min(0.95, score))  # clamp

                candidates.append({
                    "process": cand["process"],
                    "mechanism": cand["mechanism"],
                    "evidence_for": _build_evidence_for(rule, evidence),
                    "evidence_against": _build_evidence_against(cand, evidence, missing_context),
                    "expected_additional_signatures": cand.get("expected_signatures", []),
                    "missing_tests": _build_missing_tests(cand, evidence, missing_context),
                    "confidence": _score_to_confidence(score),
                    "claim_state": "PROCESS_HYPOTHESIS",
                    "_score": score,
                })

    # Sort by score descending
    candidates.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidates:
        del c["_score"]

    return candidates


def _build_evidence_for(rule: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    """Build evidence_for list from matched patterns."""
    ev_for = []
    for pattern_key in rule["patterns"]:
        ev_value = evidence.get(pattern_key, "unknown")
        if ev_value != "unknown":
            ev_for.append(f"{pattern_key}: {ev_value}")
    return ev_for


def _build_evidence_against(
    candidate: dict[str, Any], evidence: dict[str, Any], missing_context: list[str]
) -> list[str]:
    """Build evidence_against list."""
    against = []
    for ctx in missing_context:
        against.append(f"Missing required context: {ctx}")
    if evidence.get("well_count", 1) < 2:
        against.append("Single well only — no lateral control")
    if not evidence.get("has_core"):
        against.append("No core description")
    if not evidence.get("has_biostrat"):
        against.append("No biostratigraphic control")
    return against


def _build_missing_tests(
    candidate: dict[str, Any], evidence: dict[str, Any], missing_context: list[str]
) -> list[str]:
    """Build missing_tests list."""
    tests = []
    if evidence.get("well_count", 1) < 2:
        tests.append("Correlate to adjacent wells")
    if not evidence.get("has_core"):
        tests.append("Core or cuttings description")
    if not evidence.get("has_biostrat"):
        tests.append("Biostratigraphic analysis")
    if not evidence.get("has_3d_seismic"):
        tests.append("3D seismic amplitude extraction")
    for sig in candidate.get("expected_signatures", []):
        tests.append(f"Verify expected signature: {sig}")
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for t in tests:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def _score_to_confidence(score: float) -> str:
    if score >= 0.70:
        return "high"
    if score >= 0.55:
        return "moderate-high"
    if score >= 0.40:
        return "moderate"
    if score >= 0.25:
        return "low-moderate"
    return "low"


# ═══════════════════════════════════════════════════════════════════════════════
# CONTRADICTION SCANNER — Attack hypotheses systematically
# ═══════════════════════════════════════════════════════════════════════════════


def _contradiction_scan(hypotheses: list[dict[str, Any]], evidence: dict[str, Any]) -> dict[str, Any]:
    """Systematically attack hypotheses and surface contradictions."""
    contradictions = []
    penalty_scores = []

    for i, hyp in enumerate(hypotheses):
        penalties = 0.0
        issues = []

        # Contradiction 1: If process predicts marine shale below but evidence says terrestrial
        if "marine_shale_below" in str(hyp.get("expected_additional_signatures", [])):
            if evidence.get("has_marine_shale_below") is False:
                penalties += 0.25
                issues.append("Predicts marine shale below but evidence indicates terrestrial")

        # Contradiction 2: If process requires deepwater but context is shoreface
        if hyp["process"] in ["fan lobe progradation", "turbidite lobe"]:
            if evidence.get("depo_context") == "shoreface":
                penalties += 0.30
                issues.append("Deepwater process incompatible with shoreface context")

        # Contradiction 3: If confidence is high but critical evidence is missing
        if hyp["confidence"] in ["high", "moderate-high"]:
            if not evidence.get("has_core") and not evidence.get("has_biostrat"):
                penalties += 0.20
                issues.append("High confidence claimed without core or biostrat")

        # Contradiction 4: Incompatible process pairs
        for j, other in enumerate(hypotheses):
            if i >= j:
                continue
            if _processes_incompatible(hyp["process"], other["process"]):
                penalties += 0.15
                issues.append(f"Incompatible with hypothesis '{other['process']}'")

        contradictions.append({
            "process": hyp["process"],
            "issues": issues,
            "penalty": penalties,
        })
        penalty_scores.append(penalties)

    return {
        "contradictions": contradictions,
        "penalty_scores": penalty_scores,
        "max_penalty": max(penalty_scores) if penalty_scores else 0.0,
        "recommendation": "Re-rank hypotheses after penalty application" if any(p > 0 for p in penalty_scores) else "No major contradictions detected",
    }


def _processes_incompatible(a: str, b: str) -> bool:
    """Check if two processes are mutually exclusive in standard geological models."""
    # Shoreface and deepwater fan are incompatible
    if "shoreface" in a and "deepwater" in b:
        return True
    if "deepwater" in a and "shoreface" in b:
        return True
    # Channel and shoreface are generally incompatible in same interval
    if "channel" in a and "shoreface" in b:
        return True
    if "shoreface" in a and "channel" in b:
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# MCP TOOL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_process_abduction(
    evidence_refs: list[str],
    scale: Literal["parasequence", "systems_tract", "basin"] = "parasequence",
    depo_context: Literal["shoreface", "deltaic", "deepwater", "carbonate", "unknown"] = "unknown",
    claim_strictness: Literal["screen", "appraise", "decision"] = "screen",
) -> dict[str, Any]:
    """Generate and rank competing geological process hypotheses from evidence.

    Pure consumer pattern: reads pre-computed evidence artifacts only.
    Does NOT call upstream tools. Agent must have called ingest/QC/petrophysics first.
    """
    # Load artifacts
    artifacts = [_load_artifact(ref) for ref in evidence_refs]
    failed = [a for a in artifacts if "error" in a]

    if failed:
        return {
            "execution_status": "ERROR",
            "tool_class": "abduct",
            "claim_state": "888_HOLD",
            "observed": {},
            "derived": {},
            "local_interpretation": {},
            "process_hypotheses": [],
            "decision_support": {},
            "artifact_refs": {},
            "evidence_refs": evidence_refs,
            "claim_limits": ["Cannot abduct from missing evidence."],
            "next_best_actions": [
                {"tool": "geox_data_ingest_bundle", "reason": "Re-ingest missing evidence", "priority": "critical"}
            ],
            "audit_receipt": {"acrisk": 1.0, "verdict": "VOID", "floors": ["F2 TRUTH"]},
            "human_final_authority": "Arif",
            "error": f"Failed to load {len(failed)} artifact(s): {[a['ref'] for a in failed]}",
        }

    # Extract evidence summary
    evidence = _extract_evidence_summary(artifacts)
    evidence["depo_context"] = depo_context
    evidence["scale"] = scale

    # Run abduction
    hypotheses = _match_rules(evidence)

    # Enforce minimum hypotheses for ambiguous data
    if len(hypotheses) < 2 and claim_strictness in ["appraise", "decision"]:
        hypotheses.append({
            "process": "alternative_unspecified",
            "mechanism": "Insufficient data to distinguish process",
            "evidence_for": ["Data matches no strong pattern"],
            "evidence_against": ["Pattern ambiguity high"],
            "expected_additional_signatures": [],
            "missing_tests": ["More complete log suite", "Core description", "Seismic context"],
            "confidence": "low",
            "claim_state": "PROCESS_HYPOTHESIS",
        })

    # Build claim limits
    claim_limits = [
        "All outputs are PROCESS_HYPOTHESIS, not DECISION_SUPPORT.",
        f"Scale: {scale}. Do not extrapolate to larger scales without evidence.",
    ]
    if scale == "parasequence":
        claim_limits.append("Single-parasequence interpretation. No systems tract assignment.")
    if depo_context == "unknown":
        claim_limits.append("Depositional context unknown — hypotheses are broadly speculative.")
    if not evidence.get("has_core"):
        claim_limits.append("No core — lithology and depositional environment are candidates only.")
    if evidence.get("well_count", 1) < 2:
        claim_limits.append("Single well — no lateral continuity claims.")

    next_best_actions = [
        {"tool": "geox_evidence_contradiction_scan", "reason": "Attack hypotheses for contradictions", "priority": "high"},
    ]
    if not evidence.get("has_core"):
        next_best_actions.append({"tool": "geox_data_ingest_bundle", "reason": "Add core data if available", "priority": "medium"})
    if evidence.get("well_count", 1) < 2:
        next_best_actions.append({"tool": "geox_section_interpret_correlation", "reason": "Correlate to adjacent wells", "priority": "medium"})

    return {
        "execution_status": "SUCCESS",
        "tool_class": "abduct",
        "claim_state": "PROCESS_HYPOTHESIS",
        "observed": {},
        "derived": {},
        "local_interpretation": {},
        "process_hypotheses": hypotheses,
        "decision_support": {},
        "artifact_refs": {"abduction_result": f"abduction:{scale}:{depo_context}"},
        "evidence_refs": evidence_refs,
        "claim_limits": claim_limits,
        "next_best_actions": next_best_actions,
        "audit_receipt": {
            "acrisk": 0.45 if len(hypotheses) >= 2 else 0.60,
            "verdict": "QUALIFY" if len(hypotheses) >= 2 else "HOLD",
            "floors": [],
        },
        "human_final_authority": "Arif",
    }


async def geox_evidence_contradiction_scan(
    evidence_refs: list[str],
    hypotheses: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Systematically attack hypotheses and surface contradictions.

    Pure consumer: takes evidence_refs and optional hypotheses.
    If hypotheses not provided, loads them from the most recent abduction artifact.
    """
    # Load evidence
    artifacts = [_load_artifact(ref) for ref in evidence_refs]
    evidence = _extract_evidence_summary(artifacts)

    # If hypotheses not provided directly, we can't scan — return guidance
    if not hypotheses:
        return {
            "execution_status": "PARTIAL",
            "tool_class": "audit",
            "claim_state": "HOLD",
            "observed": {},
            "derived": {},
            "local_interpretation": {},
            "process_hypotheses": [],
            "decision_support": {},
            "artifact_refs": {},
            "evidence_refs": evidence_refs,
            "claim_limits": ["Contradiction scan requires hypotheses. Call geox_process_abduction first."],
            "next_best_actions": [
                {"tool": "geox_process_abduction", "reason": "Generate hypotheses before scanning", "priority": "critical"}
            ],
            "audit_receipt": {"acrisk": 0.50, "verdict": "HOLD", "floors": ["F4 HUMILITY"]},
            "human_final_authority": "Arif",
        }

    # Run contradiction scan
    scan = _contradiction_scan(hypotheses, evidence)

    # Re-rank hypotheses with penalties
    for i, hyp in enumerate(hypotheses):
        penalty = scan["penalty_scores"][i]
        # Adjust confidence downward if penalty is significant
        if penalty > 0.20:
            confidence_order = ["low", "low-moderate", "moderate", "moderate-high", "high"]
            current_idx = confidence_order.index(hyp["confidence"]) if hyp["confidence"] in confidence_order else 2
            new_idx = max(0, current_idx - 1)
            hyp["confidence"] = confidence_order[new_idx]

    # Sort by effective confidence
    confidence_rank = {"high": 5, "moderate-high": 4, "moderate": 3, "low-moderate": 2, "low": 1}
    hypotheses.sort(key=lambda h: confidence_rank.get(h["confidence"], 0), reverse=True)

    return {
        "execution_status": "SUCCESS",
        "tool_class": "audit",
        "claim_state": "DECISION_SUPPORT",
        "observed": {},
        "derived": {},
        "local_interpretation": {},
        "process_hypotheses": hypotheses,
        "decision_support": {
            "contradictions": scan["contradictions"],
            "max_penalty": scan["max_penalty"],
            "recommendation": scan["recommendation"],
        },
        "artifact_refs": {},
        "evidence_refs": evidence_refs,
        "claim_limits": [
            "Contradiction scan is DECISION_SUPPORT, not geological truth.",
            "Penalties are heuristic — not physics-based.",
        ],
        "next_best_actions": [
            {"tool": "geox_evidence_summarize_cross", "reason": "Synthesize final ranking", "priority": "high"}
        ],
        "audit_receipt": {
            "acrisk": 0.35 + scan["max_penalty"] * 0.5,
            "verdict": "QUALIFY" if scan["max_penalty"] < 0.30 else "HOLD",
            "floors": [],
        },
        "human_final_authority": "Arif",
    }
