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
    """Extract simplified evidence summary from loaded artifacts.

    Hardened for contradiction scan: derives lithology signals from
    GR motif, density-neutron crossplot, and petrophysics metadata.
    """
    summary: dict[str, Any] = {
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
        # Hardened fields — curve-based lithology signals
        "gr_mean_api": None,
        "gr_motif_class": None,
        "dn_dominant_lithology": None,
        "dn_lithology_fractions": {},
        "rt_mean_ohmm": None,
        "vsh_mean": None,
        "phi_mean": None,
        "sw_mean": None,
        "phi_density_mean": None,
        "phi_sonic_mean": None,
    }

    for art in artifacts:
        # Parse artifact metadata for pattern hints
        meta = art.get("metadata", {})
        if isinstance(meta, dict):
            for key in summary:
                if key in meta:
                    summary[key] = meta[key]

        # Hardened: extract curve-derived lithology from artifact payload
        payload = art.get("payload", art)
        if isinstance(payload, dict):
            # GR motif results
            if "gr_mean" in payload:
                summary["gr_mean_api"] = payload["gr_mean"]
            if "motif" in payload:
                summary["gr_motif_class"] = payload["motif"]
            # Lithology classification results
            if "dominant_lithology" in payload:
                summary["dn_dominant_lithology"] = payload["dominant_lithology"]
            if "lithology_fractions" in payload:
                summary["dn_lithology_fractions"] = payload["lithology_fractions"]
            # Petrophysics results
            if "vsh_mean" in payload:
                summary["vsh_mean"] = payload["vsh_mean"]
            if "phi_mean" in payload:
                summary["phi_mean"] = payload["phi_mean"]
            if "sw_mean" in payload:
                summary["sw_mean"] = payload["sw_mean"]
            if "rt_mean" in payload:
                summary["rt_mean_ohmm"] = payload["rt_mean"]
            # Porosity from different methods
            if "phi_density_mean" in payload:
                summary["phi_density_mean"] = payload["phi_density_mean"]
            if "phi_sonic_mean" in payload:
                summary["phi_sonic_mean"] = payload["phi_sonic_mean"]

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

                candidates.append(
                    {
                        "process": cand["process"],
                        "mechanism": cand["mechanism"],
                        "evidence_for": _build_evidence_for(rule, evidence),
                        "evidence_against": _build_evidence_against(cand, evidence, missing_context),
                        "expected_additional_signatures": cand.get("expected_signatures", []),
                        "missing_tests": _build_missing_tests(cand, evidence, missing_context),
                        "confidence": _score_to_confidence(score),
                        "claim_state": "PROCESS_HYPOTHESIS",
                        "_score": score,
                    }
                )

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


def _build_evidence_against(candidate: dict[str, Any], evidence: dict[str, Any], missing_context: list[str]) -> list[str]:
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


def _build_missing_tests(candidate: dict[str, Any], evidence: dict[str, Any], missing_context: list[str]) -> list[str]:
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


def _derive_gr_lithology(gr_mean_api: float | None) -> str | None:
    """Derive lithology from GR mean: sand < 75, shale > 120, interbedded in between."""
    if gr_mean_api is None:
        return None
    if gr_mean_api < 75:
        return "sand"
    if gr_mean_api > 120:
        return "shale"
    return "interbedded"


def _derive_rt_lithology(rt_mean_ohmm: float | None) -> str | None:
    """Derive lithology from RT mean: resistive > 10 (sand/carb), conductive < 2 (shale)."""
    if rt_mean_ohmm is None:
        return None
    if rt_mean_ohmm > 10:
        return "resistive"
    if rt_mean_ohmm < 2:
        return "conductive"
    return "intermediate"


def _contradiction_scan(hypotheses: list[dict[str, Any]], evidence: dict[str, Any]) -> dict[str, Any]:
    """Systematically attack hypotheses and surface contradictions.

    Hardened detectors:
      C1-C4: Original context/process contradictions
      C5:    GR lithology vs Density-Neutron lithology mismatch
      C6:    GR lithology vs Resistivity lithology mismatch
      C7:    Porosity method inconsistency (density vs sonic)
      C8:    Vsh vs φ contradiction (shale cannot have high porosity)
      C9:    Trend contradiction (coarsening vs fining)
      C10:   Thickness vs process scale mismatch
      C11:   Lateral extent vs process continuity mismatch
    """
    contradictions = []
    penalty_scores = []
    auto_hold_triggers: list[dict[str, Any]] = []

    # Pre-compute derived lithology signals
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

        # ═══════════════════════════════════════════════════════════════════════
        # C1: Marine shale below vs terrestrial evidence
        # ═══════════════════════════════════════════════════════════════════════
        if "marine_shale_below" in str(hyp.get("expected_additional_signatures", [])):
            if evidence.get("has_marine_shale_below") is False:
                penalties += 0.25
                issues.append("C1: Predicts marine shale below but evidence indicates terrestrial")

        # ═══════════════════════════════════════════════════════════════════════
        # C2: Deepwater process in shoreface context
        # ═══════════════════════════════════════════════════════════════════════
        if hyp["process"] in ["fan lobe progradation", "turbidite lobe"]:
            if evidence.get("depo_context") == "shoreface":
                penalties += 0.30
                issues.append("C2: Deepwater process incompatible with shoreface context")
                auto_hold_triggers.append({"code": "C2", "severity": "critical", "detail": hyp["process"] + " in shoreface"})

        # ═══════════════════════════════════════════════════════════════════════
        # C3: High confidence without core or biostrat
        # ═══════════════════════════════════════════════════════════════════════
        if hyp["confidence"] in ["high", "moderate-high"]:
            if not evidence.get("has_core") and not evidence.get("has_biostrat"):
                penalties += 0.20
                issues.append("C3: High confidence claimed without core or biostrat")

        # ═══════════════════════════════════════════════════════════════════════
        # C4: Incompatible process pairs
        # ═══════════════════════════════════════════════════════════════════════
        for j, other in enumerate(hypotheses):
            if i >= j:
                continue
            if _processes_incompatible(hyp["process"], other["process"]):
                penalties += 0.15
                issues.append(f"C4: Incompatible with hypothesis '{other['process']}'")

        # ═══════════════════════════════════════════════════════════════════════
        # C5: GR lithology vs Density-Neutron lithology mismatch
        # GR says Sand + DN says Shale  →  auto 888HOLD
        # ═══════════════════════════════════════════════════════════════════════
        if gr_litho and dn_litho:
            if gr_litho == "sand" and dn_litho == "shale":
                penalties += 0.35
                issues.append("C5: GR indicates sand but density-neutron indicates shale")
                auto_hold_triggers.append({"code": "C5", "severity": "critical", "detail": "GR sand vs DN shale"})
            elif gr_litho == "shale" and dn_litho == "sandstone":
                penalties += 0.30
                issues.append("C5: GR indicates shale but density-neutron indicates sandstone")
                auto_hold_triggers.append({"code": "C5", "severity": "high", "detail": "GR shale vs DN sandstone"})

        # ═══════════════════════════════════════════════════════════════════════
        # C6: GR lithology vs Resistivity lithology mismatch
        # GR says Shale + RT says Resistive  →  contradiction (shale is conductive)
        # ═══════════════════════════════════════════════════════════════════════
        if gr_litho and rt_litho:
            if gr_litho == "shale" and rt_litho == "resistive":
                penalties += 0.30
                issues.append("C6: GR indicates shale but resistivity is resistive (sand/carbonate signature)")
                auto_hold_triggers.append({"code": "C6", "severity": "high", "detail": "GR shale vs RT resistive"})
            elif gr_litho == "sand" and rt_litho == "conductive":
                penalties += 0.25
                issues.append("C6: GR indicates sand but resistivity is conductive (shale signature)")

        # ═══════════════════════════════════════════════════════════════════════
        # C7: Porosity method inconsistency
        # Density porosity high but sonic porosity low  →  contradiction
        # ═══════════════════════════════════════════════════════════════════════
        if phi_density is not None and phi_sonic is not None:
            if abs(phi_density - phi_sonic) > 0.10:
                penalties += 0.25
                issues.append(f"C7: Density porosity ({phi_density:.3f}) vs sonic porosity ({phi_sonic:.3f}) disagree by >0.10")

        # ═══════════════════════════════════════════════════════════════════════
        # C8: Vsh vs φ contradiction
        # High Vsh (>0.5) with high φ (>0.25) → shale cannot have clean-sand porosity
        # ═══════════════════════════════════════════════════════════════════════
        if vsh_mean is not None and phi_mean is not None:
            if vsh_mean > 0.5 and phi_mean > 0.25:
                penalties += 0.30
                issues.append(f"C8: High Vsh ({vsh_mean:.2f}) incompatible with high porosity ({phi_mean:.3f})")
                auto_hold_triggers.append(
                    {"code": "C8", "severity": "high", "detail": f"Vsh={vsh_mean:.2f} vs phi={phi_mean:.3f}"}
                )

        # ═══════════════════════════════════════════════════════════════════════
        # C9: Trend contradiction
        # Coarsening-upward (FUNNEL motif) but GR trend increasing (fining)
        # ═══════════════════════════════════════════════════════════════════════
        if motif == "FUNNEL" and gr_trend == "increasing_upward":
            penalties += 0.25
            issues.append("C9: FUNNEL motif (coarsening-upward) contradicts increasing GR trend (fining-upward)")
        elif motif == "BELL" and gr_trend == "decreasing_upward":
            penalties += 0.25
            issues.append("C9: BELL motif (fining-upward) contradicts decreasing GR trend (coarsening-upward)")

        # ═══════════════════════════════════════════════════════════════════════
        # C10: Thickness vs process scale mismatch
        # Shoreface/delta front in < 2m interval  →  scale mismatch
        # ═══════════════════════════════════════════════════════════════════════
        if thickness is not None and thickness != "unknown":
            try:
                t = float(thickness)
                if t < 2.0 and hyp["process"] in ["shoreface progradation", "delta front mouth bar"]:
                    penalties += 0.20
                    issues.append(f"C10: {hyp['process']} claimed in {t:.1f}m interval — too thin for process scale")
            except (ValueError, TypeError):
                pass

        # ═══════════════════════════════════════════════════════════════════════
        # C11: Lateral extent vs process continuity mismatch
        # Shoreface requires lateral continuity; discontinuous evidence contradicts
        # ═══════════════════════════════════════════════════════════════════════
        lateral = evidence.get("lateral_extent")
        if lateral == "discontinuous" and hyp["process"] in ["shoreface progradation", "delta front mouth bar"]:
            penalties += 0.20
            issues.append("C11: Shoreface/delta-front process incompatible with discontinuous lateral extent")

        # ═══════════════════════════════════════════════════════════════════════
        # C12: Seismic-Well Tie Mismatch & Eureka Vectors
        # Correlation < 0.70 → Audit mismatch reasons
        # ═══════════════════════════════════════════════════════════════════════
        tie_corr = evidence.get("max_cross_correlation")
        if tie_corr is not None and tie_corr < 0.70:
            penalties += 0.25
            issues.append(f"C12: Low seismic-well tie correlation ({tie_corr:.2f})")

            # Eureka Vector 1: Geomechanical Mismatch
            if evidence.get("caliper_deviation", 0) > 2.0:
                issues.append("Eureka 1: Borehole washouts detected — density log likely compromised, creating AI bias.")

            # Eureka Vector 2: Fluid Substitution
            if evidence.get("is_gas_zone") and evidence.get("velocity_drop_anomaly"):
                issues.append("Eureka 2: Unseen gas cloud suspected — lowering velocity and breaking regional T-D assumption.")

            # Eureka Vector 3: Structural Reality
            if evidence.get("seismic_discontinuity") == "high":
                issues.append("Eureka 3: Sub-seismic faulting suspected — acoustic wave smearing detected.")

        contradictions.append(
            {
                "process": hyp["process"],
                "issues": issues,
                "penalty": round(penalties, 3),
            }
        )
        penalty_scores.append(penalties)

    max_penalty = max(penalty_scores) if penalty_scores else 0.0
    recommendation = (
        "888HOLD triggered — severe contradictions detected"
        if auto_hold_triggers
        else "Re-rank hypotheses after penalty application"
        if any(p > 0 for p in penalty_scores)
        else "No major contradictions detected"
    )

    return {
        "contradictions": contradictions,
        "penalty_scores": penalty_scores,
        "max_penalty": max_penalty,
        "recommendation": recommendation,
        "auto_hold_triggers": auto_hold_triggers,
        "auto_hold": len(auto_hold_triggers) > 0,
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
            "audit_receipt": {
                "acrisk": 1.0,
                "verdict": "VOID",
                "floor_signals": [
                    {"domain": "truth_risk", "value": "high", "trigger": "evidence_load_failed", "raw": len(failed)}
                ],
                "floor_authority": "arifOS",
            },
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
        hypotheses.append(
            {
                "process": "alternative_unspecified",
                "mechanism": "Insufficient data to distinguish process",
                "evidence_for": ["Data matches no strong pattern"],
                "evidence_against": ["Pattern ambiguity high"],
                "expected_additional_signatures": [],
                "missing_tests": ["More complete log suite", "Core description", "Seismic context"],
                "confidence": "low",
                "claim_state": "PROCESS_HYPOTHESIS",
            }
        )

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
        next_best_actions.append(
            {"tool": "geox_data_ingest_bundle", "reason": "Add core data if available", "priority": "medium"}
        )
    if evidence.get("well_count", 1) < 2:
        next_best_actions.append(
            {"tool": "geox_section_interpret_correlation", "reason": "Correlate to adjacent wells", "priority": "medium"}
        )

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
            "floor_signals": [],
            "floor_authority": "arifOS",
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
            "audit_receipt": {
                "acrisk": 0.50,
                "verdict": "HOLD",
                "floor_signals": [{"domain": "uncertainty_band", "value": "wide", "trigger": "no_hypotheses", "raw": None}],
                "floor_authority": "arifOS",
            },
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

    # Auto-888HOLD: severe contradictions override DECISION_SUPPORT
    if scan.get("auto_hold"):
        claim_state = "888_HOLD"
        execution_status = "HOLD"
        verdict = "VOID"
        acrisk = 0.85
        # GEOX is an evidence organ — it signals domain risk, not constitutional floors.
        # Floors (F1-F13) are enforced by arifOS, not GEOX.
        truth_risk = "high" if scan["max_penalty"] >= 0.30 else "moderate"
        hallucination_risk = "high" if scan["max_penalty"] >= 0.30 else "moderate"
        floor_signals = [
            {"domain": "truth_risk", "value": truth_risk, "trigger": "max_penalty", "raw": scan["max_penalty"]},
            {
                "domain": "hallucination_risk",
                "value": hallucination_risk,
                "trigger": "contradiction_detected",
                "raw": len(scan.get("contradictions", [])),
            },
        ]
    else:
        claim_state = "DECISION_SUPPORT"
        execution_status = "SUCCESS"
        verdict = "QUALIFY" if scan["max_penalty"] < 0.30 else "HOLD"
        acrisk = 0.35 + scan["max_penalty"] * 0.5
        floor_signals = []

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
        },
        "artifact_refs": {},
        "evidence_refs": evidence_refs,
        "claim_limits": [
            "Contradiction scan is DECISION_SUPPORT, not geological truth.",
            "Penalties are heuristic — not physics-based.",
            "Auto-888HOLD fires when curve contradictions exceed safety threshold.",
        ],
        "next_best_actions": [
            {"tool": "geox_evidence_summarize_cross", "reason": "Synthesize final ranking", "priority": "high"}
            if not scan.get("auto_hold")
            else {"tool": "geox_data_qc_bundle", "reason": "Re-QC conflicting curves before re-abduction", "priority": "critical"}
        ],
        "audit_receipt": {
            "acrisk": acrisk,
            "verdict": verdict,
            "floor_signals": floor_signals,
            "floor_authority": "arifOS",
        },
        "human_final_authority": "Arif",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# H3 — BATCH TASK TOOLS (SEP-1686 background execution)
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_task_metabolize_basin(
    well_refs: list[str],
    basin_context: str,
    canon9_profile: str = "malay_basin",
) -> dict[str, Any]:
    """CANON-9 loop over multiple wells. Long-running. Returns task envelope.

    For each well_ref, generates petrophysics candidates and aggregates
    basin-level statistics (mean Vsh, φ, Sw, net-pay thickness).

    Args:
        well_refs: List of well artifact references.
        basin_context: Free-text basin name or code for metadata.
        canon9_profile: Physics parameter profile — selects defaults for
            Archie coefficients, matrix density, Rw, etc.
    """
    if not well_refs:
        return {
            "execution_status": "ERROR",
            "tool_class": "compute",
            "claim_state": "NO_VALID_EVIDENCE",
            "observed": {},
            "derived": {},
            "local_interpretation": {},
            "process_hypotheses": [],
            "decision_support": {},
            "artifact_refs": {},
            "evidence_refs": [],
            "claim_limits": ["well_refs list is empty. Provide at least one well."],
            "next_best_actions": [{"tool": "geox_data_ingest_bundle", "reason": "Ingest wells first", "priority": "critical"}],
            "audit_receipt": {
                "acrisk": 0.50,
                "verdict": "HOLD",
                "floor_signals": [{"domain": "uncertainty_band", "value": "wide", "trigger": "empty_well_refs", "raw": 0}],
                "floor_authority": "arifOS",
            },
            "human_final_authority": "Arif",
        }

    # Select CANON-9 defaults by profile
    profile_defaults: dict[str, Any] = {
        "malay_basin": {
            "rw": 0.05,
            "archie_m": 2.0,
            "archie_n": 2.0,
            "matrix_density": 2.65,
            "fluid_density": 1.0,
            "vsh_cutoff": 0.5,
            "phi_cutoff": 0.1,
            "sw_cutoff": 0.6,
        },
        "generic": {
            "rw": 0.05,
            "archie_m": 2.0,
            "archie_n": 2.0,
            "matrix_density": 2.65,
            "fluid_density": 1.0,
            "vsh_cutoff": 0.5,
            "phi_cutoff": 0.1,
            "sw_cutoff": 0.6,
        },
    }
    defaults = profile_defaults.get(canon9_profile, profile_defaults["generic"])

    # Lazy import to avoid circular dependency at module load
    from geox_mcp.tools.petrophysics import geox_subsurface_generate_candidates

    per_well_results: list[dict[str, Any]] = []
    success_count = 0
    error_count = 0

    for well_ref in well_refs:
        try:
            result = await geox_subsurface_generate_candidates(
                target_class="petrophysics",
                evidence_refs=[well_ref],
                **defaults,
            )
            payload = result.get("payload", result)
            status = payload.get("execution_status", "UNKNOWN")
            if status == "SUCCESS":
                success_count += 1
            else:
                error_count += 1
            per_well_results.append(
                {
                    "well_ref": well_ref,
                    "status": status,
                    "artifact_ref": payload.get("artifact_ref"),
                    "claim_state": payload.get("claim_state", "UNKNOWN"),
                    "physics_guard": payload.get("physics_guard"),
                }
            )
        except Exception as exc:
            error_count += 1
            per_well_results.append(
                {
                    "well_ref": well_ref,
                    "status": "ERROR",
                    "error": str(exc),
                    "claim_state": "NO_VALID_EVIDENCE",
                }
            )

    all_ok = error_count == 0
    batch_status = "SUCCESS" if all_ok else "PARTIAL"
    verdict = "QUALIFY" if all_ok else "HOLD"

    # Aggregate simple basin metrics from successful wells
    basin_metrics: dict[str, Any] = {
        "well_count": len(well_refs),
        "success_count": success_count,
        "error_count": error_count,
        "basin_context": basin_context,
        "canon9_profile": canon9_profile,
    }

    return {
        "execution_status": batch_status,
        "tool_class": "compute",
        "claim_state": "DECISION_SUPPORT" if all_ok else "HYPOTHESIS",
        "observed": {},
        "derived": basin_metrics,
        "local_interpretation": {
            "per_well": per_well_results,
            "aggregation_method": "canonical_profile_loop",
        },
        "process_hypotheses": [],
        "decision_support": {
            "recommendation": "Proceed to basin-scale prospect evaluation"
            if all_ok
            else "Review failed wells before basin aggregation",
            "next_tool": "geox_prospect_evaluate" if all_ok else "geox_data_qc_bundle",
        },
        "artifact_refs": {},
        "evidence_refs": well_refs,
        "claim_limits": [
            "Basin metabolization is DECISION_SUPPORT, not resource booking.",
            "Per-well physics guards must be reviewed individually.",
        ],
        "next_best_actions": [
            {"tool": "geox_evidence_summarize_cross", "reason": "Synthesize basin-wide evidence", "priority": "high"}
        ],
        "audit_receipt": {
            "acrisk": 0.30 + (error_count / max(len(well_refs), 1)) * 0.40,
            "verdict": verdict,
            "floor_signals": [],
            "floor_authority": "arifOS",
        },
        "human_final_authority": "Arif",
    }
