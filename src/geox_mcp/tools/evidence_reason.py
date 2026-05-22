"""
GEOX Evidence Reason — Unified Evidence Synthesis, Abduction & Contradiction Engine
═══════════════════════════════════════════════════════════════════════════════════════
Forged from the energy of 3 predecessor tools:
  geox_evidence_summarize_cross
  geox_process_abduction
  geox_evidence_contradiction_scan

One entry point. Phase-driven. Natural agent workflow: synthesize → abduct → contradict.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, Literal

from geox_core.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)
from geox_mcp.tools._helpers import _get_artifact

logger = logging.getLogger("geox.evidence_reason")

TOOL_NAME = "geox_evidence_reason"


# ═══════════════════════════════════════════════════════════════════════════════
# ABDUCTION GRAMMAR (forged from abduction.py)
# ═══════════════════════════════════════════════════════════════════════════════

_GRAMMAR_RULES: list[dict[str, Any]] = [
    {
        "name": "coarsening_upward_clean_top",
        "patterns": {"gr_trend": "decreasing_upward", "vclay_trend": "decreasing_upward", "rhob_trend": "increasing_upward"},
        "candidates": [
            {"process": "shoreface progradation", "mechanism": "sediment supply exceeded accommodation", "prior": 0.35,
             "required_context": ["marine_shale_below", "clean_sand_top"]},
            {"process": "delta front mouth bar", "mechanism": "fluvial input into standing water", "prior": 0.25,
             "required_context": ["distributary_channel_evidence"]},
            {"process": "fan lobe progradation", "mechanism": "turbidity current deceleration", "prior": 0.15,
             "required_context": ["deepwater_context"]},
        ],
    },
    {
        "name": "fining_upward_blocky",
        "patterns": {"gr_trend": "increasing_upward", "vclay_trend": "increasing_upward", "motif": "blocky"},
        "candidates": [
            {"process": "channel fill", "mechanism": "fluvial or tidal channel abandonment", "prior": 0.40,
             "required_context": ["erosional_base"]},
            {"process": "crevasse splay", "mechanism": "levee breach during flood", "prior": 0.20,
             "required_context": ["near_channel"]},
        ],
    },
    {
        "name": "high_gr_condensed",
        "patterns": {"gr_peak": "high", "thickness_m": "thin", "lateral_extent": "regional"},
        "candidates": [
            {"process": "maximum flooding surface", "mechanism": "maximum transgression and condensation", "prior": 0.30,
             "required_context": ["regional_correlation", "biostrat"]},
            {"process": "volcanic ash bed", "mechanism": "airfall tephra deposition", "prior": 0.15,
             "required_context": ["geochemical_fingerprint"]},
            {"process": "organic-rich flooding", "mechanism": "high productivity + anoxia", "prior": 0.20,
             "required_context": ["low_rho", "high_resistivity"]},
        ],
    },
    {
        "name": "blocky_low_gr_cuts_shale",
        "patterns": {"gr_shape": "blocky", "gr_value": "low", "base_contact": "sharp"},
        "candidates": [
            {"process": "channel incision", "mechanism": "base-level fall or avulsion", "prior": 0.35,
             "required_context": ["erosional_base", "3d_seismic"]},
            {"process": "turbidite lobe", "mechanism": "density flow deceleration", "prior": 0.20,
             "required_context": ["deepwater_context"]},
        ],
    },
]


_ARTIFACT_STORE_DIR = Path("/data/geox_las")


def _load_artifact(artifact_ref: str) -> dict[str, Any]:
    if artifact_ref.startswith("well_las:"):
        artifact_id = artifact_ref.replace("well_las:", "")
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
    return {"ref": artifact_ref, "type": "metadata", "note": "Reference-only; no file loaded"}


def _extract_evidence_summary(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "gr_trend": "unknown", "vclay_trend": "unknown", "rhob_trend": "unknown",
        "motif": "unknown", "gr_shape": "unknown", "gr_value": "unknown",
        "base_contact": "unknown", "thickness_m": "unknown", "lateral_extent": "unknown",
        "has_core": False, "has_biostrat": False, "has_correlation": False, "well_count": 1,
        "gr_mean_api": None, "gr_motif_class": None, "dn_dominant_lithology": None,
        "dn_lithology_fractions": {}, "rt_mean_ohmm": None, "vsh_mean": None,
        "phi_mean": None, "sw_mean": None, "phi_density_mean": None, "phi_sonic_mean": None,
    }
    for art in artifacts:
        meta = art.get("metadata", {})
        if isinstance(meta, dict):
            for key in summary:
                if key in meta:
                    summary[key] = meta[key]
        payload = art.get("payload", art)
        if isinstance(payload, dict):
            if "gr_mean" in payload:
                summary["gr_mean_api"] = payload["gr_mean"]
            if "motif" in payload:
                summary["gr_motif_class"] = payload["motif"]
            if "dominant_lithology" in payload:
                summary["dn_dominant_lithology"] = payload["dominant_lithology"]
            if "lithology_fractions" in payload:
                summary["dn_lithology_fractions"] = payload["lithology_fractions"]
            if "vsh_mean" in payload:
                summary["vsh_mean"] = payload["vsh_mean"]
            if "phi_mean" in payload:
                summary["phi_mean"] = payload["phi_mean"]
            if "sw_mean" in payload:
                summary["sw_mean"] = payload["sw_mean"]
            if "rt_mean" in payload:
                summary["rt_mean_ohmm"] = payload["rt_mean"]
            if "phi_density_mean" in payload:
                summary["phi_density_mean"] = payload["phi_density_mean"]
            if "phi_sonic_mean" in payload:
                summary["phi_sonic_mean"] = payload["phi_sonic_mean"]
    wells = set()
    for art in artifacts:
        ref = art.get("ref", "")
        if "well" in ref.lower():
            wells.add(ref)
    summary["well_count"] = max(1, len(wells))
    return summary


def _build_evidence_for(rule: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    ev_for = []
    for pattern_key in rule["patterns"]:
        ev_value = evidence.get(pattern_key, "unknown")
        if ev_value != "unknown":
            ev_for.append(f"{pattern_key}: {ev_value}")
    return ev_for


def _build_evidence_against(candidate: dict[str, Any], evidence: dict[str, Any], missing_context: list[str]) -> list[str]:
    against = [f"Missing required context: {ctx}" for ctx in missing_context]
    if evidence.get("well_count", 1) < 2:
        against.append("Single well only — no lateral control")
    if not evidence.get("has_core"):
        against.append("No core description")
    if not evidence.get("has_biostrat"):
        against.append("No biostratigraphic control")
    return against


def _build_missing_tests(candidate: dict[str, Any], evidence: dict[str, Any], missing_context: list[str]) -> list[str]:
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


def _match_rules(evidence: dict[str, Any]) -> list[dict[str, Any]]:
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
                score = max(0.05, min(0.95, score))
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
    candidates.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidates:
        del c["_score"]
    return candidates


# ═══════════════════════════════════════════════════════════════════════════════
# CONTRADICTION SCAN (forged from abduction.py)
# ═══════════════════════════════════════════════════════════════════════════════


def _derive_gr_lithology(gr_mean_api: float | None) -> str | None:
    if gr_mean_api is None:
        return None
    if gr_mean_api < 75:
        return "sand"
    if gr_mean_api > 120:
        return "shale"
    return "interbedded"


def _derive_rt_lithology(rt_mean_ohmm: float | None) -> str | None:
    if rt_mean_ohmm is None:
        return None
    if rt_mean_ohmm > 10:
        return "resistive"
    if rt_mean_ohmm < 2:
        return "conductive"
    return "intermediate"


def _processes_incompatible(a: str, b: str) -> bool:
    if "shoreface" in a and "deepwater" in b:
        return True
    if "deepwater" in a and "shoreface" in b:
        return True
    if "channel" in a and "shoreface" in b:
        return True
    if "shoreface" in a and "channel" in b:
        return True
    return False


def _contradiction_scan(hypotheses: list[dict[str, Any]], evidence: dict[str, Any]) -> dict[str, Any]:
    contradictions = []
    penalty_scores = []
    auto_hold_triggers: list[dict[str, Any]] = []

    gr_litho = _derive_gr_lithology(evidence.get("gr_mean_api"))
    dn_litho = evidence.get("dn_dominant_lithology")
    rt_litho = _derive_rt_lithology(evidence.get("rt_mean_ohmm"))
    vsh_mean = evidence.get("vsh_mean")
    phi_mean = evidence.get("phi_mean")
    phi_density = evidence.get("phi_density_mean")
    phi_sonic = evidence.get("phi_sonic_mean")
    thickness = evidence.get("thickness_m")
    motif = evidence.get("motif")
    gr_trend = evidence.get("gr_trend")

    for i, hyp in enumerate(hypotheses):
        penalties = 0.0
        issues = []

        # C1
        if "marine_shale_below" in str(hyp.get("expected_additional_signatures", [])):
            if evidence.get("has_marine_shale_below") is False:
                penalties += 0.25
                issues.append("C1: Predicts marine shale below but evidence indicates terrestrial")

        # C2
        if hyp["process"] in ["fan lobe progradation", "turbidite lobe"]:
            if evidence.get("depo_context") == "shoreface":
                penalties += 0.30
                issues.append("C2: Deepwater process incompatible with shoreface context")
                auto_hold_triggers.append({"code": "C2", "severity": "critical", "detail": hyp["process"] + " in shoreface"})

        # C3
        if hyp["confidence"] in ["high", "moderate-high"]:
            if not evidence.get("has_core") and not evidence.get("has_biostrat"):
                penalties += 0.20
                issues.append("C3: High confidence claimed without core or biostrat")

        # C4
        for j, other in enumerate(hypotheses):
            if i >= j:
                continue
            if _processes_incompatible(hyp["process"], other["process"]):
                penalties += 0.15
                issues.append(f"C4: Incompatible with hypothesis '{other['process']}'")

        # C5
        if gr_litho and dn_litho:
            if gr_litho == "sand" and dn_litho == "shale":
                penalties += 0.35
                issues.append("C5: GR indicates sand but density-neutron indicates shale")
                auto_hold_triggers.append({"code": "C5", "severity": "critical", "detail": "GR sand vs DN shale"})
            elif gr_litho == "shale" and dn_litho == "sandstone":
                penalties += 0.30
                issues.append("C5: GR indicates shale but density-neutron indicates sandstone")
                auto_hold_triggers.append({"code": "C5", "severity": "high", "detail": "GR shale vs DN sandstone"})

        # C6
        if gr_litho and rt_litho:
            if gr_litho == "shale" and rt_litho == "resistive":
                penalties += 0.30
                issues.append("C6: GR indicates shale but resistivity is resistive")
                auto_hold_triggers.append({"code": "C6", "severity": "high", "detail": "GR shale vs RT resistive"})
            elif gr_litho == "sand" and rt_litho == "conductive":
                penalties += 0.25
                issues.append("C6: GR indicates sand but resistivity is conductive")

        # C7
        if phi_density is not None and phi_sonic is not None:
            if abs(phi_density - phi_sonic) > 0.10:
                penalties += 0.25
                issues.append(f"C7: Density porosity ({phi_density:.3f}) vs sonic porosity ({phi_sonic:.3f}) disagree by >0.10")

        # C8
        if vsh_mean is not None and phi_mean is not None:
            if vsh_mean > 0.5 and phi_mean > 0.25:
                penalties += 0.30
                issues.append(f"C8: High Vsh ({vsh_mean:.2f}) incompatible with high porosity ({phi_mean:.3f})")
                auto_hold_triggers.append({"code": "C8", "severity": "high", "detail": f"Vsh={vsh_mean:.2f} vs phi={phi_mean:.3f}"})

        # C9
        if motif == "FUNNEL" and gr_trend == "increasing_upward":
            penalties += 0.25
            issues.append("C9: FUNNEL motif contradicts increasing GR trend")
        elif motif == "BELL" and gr_trend == "decreasing_upward":
            penalties += 0.25
            issues.append("C9: BELL motif contradicts decreasing GR trend")

        # C10
        if thickness is not None and thickness != "unknown":
            try:
                t = float(thickness)
                if t < 2.0 and hyp["process"] in ["shoreface progradation", "delta front mouth bar"]:
                    penalties += 0.20
                    issues.append(f"C10: {hyp['process']} claimed in {t:.1f}m interval — too thin")
            except (ValueError, TypeError):
                pass

        # C11
        lateral = evidence.get("lateral_extent")
        if lateral == "discontinuous" and hyp["process"] in ["shoreface progradation", "delta front mouth bar"]:
            penalties += 0.20
            issues.append("C11: Shoreface/delta-front process incompatible with discontinuous lateral extent")

        # C12
        tie_corr = evidence.get("max_cross_correlation")
        if tie_corr is not None and tie_corr < 0.70:
            penalties += 0.25
            issues.append(f"C12: Low seismic-well tie correlation ({tie_corr:.2f})")
            if evidence.get("caliper_deviation", 0) > 2.0:
                issues.append("Eureka 1: Borehole washouts detected — density log likely compromised")
            if evidence.get("is_gas_zone") and evidence.get("velocity_drop_anomaly"):
                issues.append("Eureka 2: Unseen gas cloud suspected")
            if evidence.get("seismic_discontinuity") == "high":
                issues.append("Eureka 3: Sub-seismic faulting suspected")

        contradictions.append({"process": hyp["process"], "issues": issues, "penalty": round(penalties, 3)})
        penalty_scores.append(penalties)

    max_penalty = max(penalty_scores) if penalty_scores else 0.0
    recommendation = (
        "888HOLD triggered — severe contradictions detected" if auto_hold_triggers else
        "Re-rank hypotheses after penalty application" if any(p > 0 for p in penalty_scores) else
        "No major contradictions detected"
    )
    return {
        "contradictions": contradictions,
        "penalty_scores": penalty_scores,
        "max_penalty": max_penalty,
        "recommendation": recommendation,
        "auto_hold_triggers": auto_hold_triggers,
        "auto_hold": len(auto_hold_triggers) > 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════


async def _phase_synthesize(evidence_refs: list[str], export_format: str, output_path: str | None) -> dict[str, Any]:
    artifact = {
        "refs": evidence_refs,
        "graph": "synthesized",
        "contradictions": [],
        "visual_artifact_policy": (
            "Visual artifacts (PNG, SVG, HTML) in the evidence graph are supporting evidence only. "
            "Every visual artifact must be accompanied by its claim_state, depth_basis, and artifact validation status."
        ),
    }
    result = get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="DERIVED",
        claim_state="INTERPRETED",
        perception_class="DERIVED",
    )
    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            if export_format == "csv":
                with open(output_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["artifact_ref", "claim_state", "note"])
                    for ref in evidence_refs:
                        entry = _get_artifact(ref)
                        cs = entry.get("claim_state", "UNKNOWN") if entry else "NOT_REGISTERED"
                        writer.writerow([ref, cs, ""])
            else:
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2, default=str)
            result["export_written"] = True
            result["export_path"] = output_path
            result["export_format"] = export_format
        except Exception as exc:
            result["export_written"] = False
            result["export_error"] = str(exc)
    return result


async def _phase_abduct(evidence_refs: list[str], scale: str, depo_context: str, claim_strictness: str) -> dict[str, Any]:
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
            "next_best_actions": [{"tool": "geox_data_ingest_bundle", "reason": "Re-ingest missing evidence", "priority": "critical"}],
            "audit_receipt": {"acrisk": 1.0, "verdict": "VOID", "floors": ["F2 TRUTH"]},
            "human_final_authority": "Arif",
            "error": f"Failed to load {len(failed)} artifact(s): {[a['ref'] for a in failed]}",
        }

    evidence = _extract_evidence_summary(artifacts)
    evidence["depo_context"] = depo_context
    evidence["scale"] = scale
    hypotheses = _match_rules(evidence)

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
        "next_best_actions": [
            {"tool": "geox_evidence_reason", "reason": "Run contradiction scan", "priority": "high", "parameters": {"phase": "contradict"}}
        ],
        "audit_receipt": {
            "acrisk": 0.45 if len(hypotheses) >= 2 else 0.60,
            "verdict": "QUALIFY" if len(hypotheses) >= 2 else "HOLD",
            "floors": [],
        },
        "human_final_authority": "Arif",
    }


async def _phase_contradict(evidence_refs: list[str], hypotheses: list[dict] | None) -> dict[str, Any]:
    artifacts = [_load_artifact(ref) for ref in evidence_refs]
    evidence = _extract_evidence_summary(artifacts)

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
            "claim_limits": ["Contradiction scan requires hypotheses. Call geox_evidence_reason with phase='abduct' first."],
            "next_best_actions": [{"tool": "geox_evidence_reason", "reason": "Generate hypotheses before scanning", "priority": "critical", "parameters": {"phase": "abduct"}}],
            "audit_receipt": {"acrisk": 0.50, "verdict": "HOLD", "floors": ["F4 HUMILITY"]},
            "human_final_authority": "Arif",
        }

    scan = _contradiction_scan(hypotheses, evidence)
    for i, hyp in enumerate(hypotheses):
        penalty = scan["penalty_scores"][i]
        if penalty > 0.20:
            confidence_order = ["low", "low-moderate", "moderate", "moderate-high", "high"]
            current_idx = confidence_order.index(hyp["confidence"]) if hyp["confidence"] in confidence_order else 2
            new_idx = max(0, current_idx - 1)
            hyp["confidence"] = confidence_order[new_idx]

    confidence_rank = {"high": 5, "moderate-high": 4, "moderate": 3, "low-moderate": 2, "low": 1}
    hypotheses.sort(key=lambda h: confidence_rank.get(h["confidence"], 0), reverse=True)

    if scan.get("auto_hold"):
        claim_state = "888_HOLD"
        execution_status = "HOLD"
        verdict = "VOID"
        acrisk = 0.85
        floors = ["F2 TRUTH", "F9 ANTI-HANTU"]
    else:
        claim_state = "DECISION_SUPPORT"
        execution_status = "SUCCESS"
        verdict = "QUALIFY" if scan["max_penalty"] < 0.30 else "HOLD"
        acrisk = 0.35 + scan["max_penalty"] * 0.5
        floors = []

    return {
        "execution_status": execution_status,
        "tool_class": "audit",
        "claim_state": claim_state,
        "observed": {},
        "derived": {},
        "local_interpretation": {},
        "process_hypotheses": hypotheses,
        "decision_support": {
            "contradictions": scan["contradictions"],
            "max_penalty": scan["max_penalty"],
            "recommendation": scan["recommendation"],
            "auto_hold_triggers": scan.get("auto_hold_triggers", []),
            "auto_hold_triggered": scan.get("auto_hold", False),
            "hold_reason": scan["recommendation"] if scan.get("auto_hold") else None,
        },
        "artifact_refs": {},
        "evidence_refs": evidence_refs,
        "claim_limits": [
            "Contradiction scan is DECISION_SUPPORT, not geological truth.",
            "Penalties are heuristic — not physics-based.",
            "Auto-888HOLD fires when curve contradictions exceed safety threshold.",
        ],
        "next_best_actions": [
            {"tool": "geox_evidence_reason", "reason": "Synthesize final ranking", "priority": "high", "parameters": {"phase": "synthesize"}}
            if not scan.get("auto_hold") else
            {"tool": "geox_data_qc_bundle", "reason": "Re-QC conflicting curves before re-abduction", "priority": "critical"}
        ],
        "audit_receipt": {"acrisk": acrisk, "verdict": verdict, "floors": floors},
        "human_final_authority": "Arif",
    }


async def _phase_full(evidence_refs: list[str], scale: str, depo_context: str, claim_strictness: str, export_format: str, output_path: str | None) -> dict[str, Any]:
    abduct_result = await _phase_abduct(evidence_refs, scale, depo_context, claim_strictness)
    if abduct_result.get("execution_status") == "ERROR":
        return abduct_result

    hypotheses = abduct_result.get("process_hypotheses", [])
    contradict_result = await _phase_contradict(evidence_refs, hypotheses)
    if contradict_result.get("claim_state") == "888_HOLD":
        return contradict_result

    synthesize_result = await _phase_synthesize(evidence_refs, export_format, output_path)

    # Merge into unified output
    return {
        "tool": TOOL_NAME,
        "phase": "full",
        "execution_status": "SUCCESS",
        "tool_class": "reason",
        "claim_state": "DECISION_SUPPORT",
        "observed": {},
        "derived": {},
        "local_interpretation": {},
        "process_hypotheses": contradict_result.get("process_hypotheses", []),
        "decision_support": {
            **contradict_result.get("decision_support", {}),
            "synthesis": synthesize_result.get("primary_artifact", {}),
        },
        "artifact_refs": abduct_result.get("artifact_refs", {}),
        "evidence_refs": evidence_refs,
        "claim_limits": abduct_result.get("claim_limits", []) + contradict_result.get("claim_limits", []),
        "next_best_actions": [
            {"tool": "geox_prospect_evaluate", "reason": "Evaluate prospect with reasoned evidence", "priority": "high"}
        ],
        "audit_receipt": contradict_result.get("audit_receipt", {}),
        "human_final_authority": "Arif",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC TOOL
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_evidence_reason(
    phase: Literal["synthesize", "abduct", "contradict", "full"] = "full",
    evidence_refs: list[str] | None = None,
    hypotheses: list[dict] | None = None,
    scale: Literal["parasequence", "systems_tract", "basin"] = "parasequence",
    depo_context: Literal["shoreface", "deltaic", "deepwater", "carbonate", "unknown"] = "unknown",
    claim_strictness: Literal["screen", "appraise", "decision"] = "screen",
    export_format: Literal["json", "csv"] = "json",
    output_path: str | None = None,
) -> dict[str, Any]:
    """Unified evidence synthesis, abduction, and contradiction engine.

    Replaces: geox_evidence_summarize_cross, geox_process_abduction,
    geox_evidence_contradiction_scan.

    Parameters
    ----------
    phase : str
        "synthesize" — cross-domain evidence graph + optional export.
        "abduct" — generate and rank competing geological process hypotheses.
        "contradict" — attack hypotheses and surface contradictions (requires hypotheses).
        "full" — synthesize → abduct → contradict in one call.

    evidence_refs : list[str]
        Artifact refs to reason over.
    hypotheses : list[dict]
        Required for phase="contradict". If absent, returns guidance.
    scale, depo_context, claim_strictness :
        Passed to abduction phase.
    export_format, output_path :
        Passed to synthesis phase.

    Returns
    -------
    Unified envelope with process_hypotheses, decision_support (contradictions),
    claim_limits, and next_best_actions.
    """
    refs = evidence_refs or []

    if phase == "synthesize":
        return await _phase_synthesize(refs, export_format, output_path)

    if phase == "abduct":
        return await _phase_abduct(refs, scale, depo_context, claim_strictness)

    if phase == "contradict":
        return await _phase_contradict(refs, hypotheses)

    if phase == "full":
        return await _phase_full(refs, scale, depo_context, claim_strictness, export_format, output_path)

    return get_standard_envelope(
        {"tool": TOOL_NAME, "error": f"Unknown phase: {phase}"},
        tool_class="compute",
        execution_status=ExecutionStatus.ERROR,
        governance_status=GovernanceStatus.HOLD,
        claim_tag="HYPOTHESIS",
    )
