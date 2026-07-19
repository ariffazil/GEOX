"""
geox_claim — Unified Claim Lifecycle (Phase 2)
═══════════════════════════════════════════════
Absorbs: geox_claim_create, geox_claim_validate, geox_claim_challenge,
         geox_claim_seal, geox_evidence_attach

Modes: create, validate, challenge, seal, attach_evidence

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

from typing import Any, Literal


async def geox_claim(
    mode: Literal["create", "validate", "challenge", "seal", "attach_evidence"] = "create",
    claim_id: str = "",
    challenge_text: str = "",
    alternative_claim_text: str = "",
    alternative_evidence_ids: list[str] | None = None,
    challenge_evidence_ids: list[str] | None = None,
    alternative_uncertainty: dict[str, Any] | None = None,
    challenger_provenance: str = "GEOX Claim Engine",
    ack_irreversible: bool = False,
    seal_verdict: str = "SEAL",
    evidence_id: str = "",
    evidence_type: str = "supporting",
    provenance: str = "GEOX Claim Engine",
    claim_text: str = "",
    claim_type: str = "other",
    truth_class: str = "INTERPRETATION",
    evidence_ids: list[str] | None = None,
    uncertainty_p10: float | None = None,
    uncertainty_p50: float | None = None,
    uncertainty_p90: float | None = None,
    uncertainty_distribution: str = "lognormal",
    alternatives: list[dict[str, Any]] | None = None,
    authority: str = "GEOX_CLAIM_WORKER",
    voxel_state: dict[str, Any] | None = None,  # H3 fix: required for seal mode
) -> dict[str, Any]:
    """Unified claim lifecycle — DRAFT → VALIDATED → SEALED.

    Modes:
      create          - Create a structured interpretation claim
      validate        - Validate claim against 16-field earth_memory_envelope
      challenge       - Challenge existing claim with alternative interpretation
      seal            - Submit validated claim to arifOS for VAULT999 sealing
                       (H3 fix: requires voxel_state for well_constrained check)
      attach_evidence - Attach evidence artifact to existing claim
    """
    kwargs = locals().copy()
    if mode == "validate":
        from geox_mcp.tools.claims import geox_claim_validate as _impl
        return await _impl(claim_id=kwargs.get("claim_id", ""))

    if mode == "challenge":
        from geox_mcp.tools.claims import geox_claim_challenge as _impl
        return await _impl(
            claim_id=kwargs.get("claim_id", ""),
            challenge_text=kwargs.get("challenge_text", ""),
            alternative_claim_text=kwargs.get("alternative_claim_text", ""),
            alternative_evidence_ids=kwargs.get("alternative_evidence_ids", []),
            challenge_evidence_ids=kwargs.get("challenge_evidence_ids"),
            alternative_uncertainty=kwargs.get("alternative_uncertainty"),
            challenger_provenance=kwargs.get("challenger_provenance", "GEOX Claim Engine"),
        )

    if mode == "seal":
        # ── H3 fix (2026-06-22): F2 TRUTH at system level ────────────────────
        # Per ADR-008, well_constrained check (obs_count >= 3 AND residual < 0.3)
        # is the system-level gate before any seal. Caller must pass `voxel_state`
        # dict with `observation_count` and `forward_model_residual` fields.
        voxel_state = kwargs.get("voxel_state")
        if not voxel_state:
            return {
                "status": "HOLD",
                "governance_status": "HOLD",
                "error_code": "F2_TRUTH_VOXEL_REQUIRED",
                "message": (
                    "Seal requires a voxel_state dict with observation_count and "
                    "forward_model_residual fields. Per ADR-008, well_constrained "
                    "check (obs_count >= 3 AND residual < 0.3) is the system-level "
                    "F2 TRUTH gate. Provide voxel_state to proceed."
                ),
                "floor": "F2_TRUTH",
                "guard": "RT3",
                "claim_id": kwargs.get("claim_id", ""),
                "required_action": "Pass voxel_state={observation_count: int, forward_model_residual: float, ...} to geox_claim(mode='seal').",
            }

        obs_count = int(voxel_state.get("observation_count", 0))
        residual = float(voxel_state.get("forward_model_residual", 1.0))
        well_constrained = (obs_count >= 3) and (residual < 0.3)

        if not well_constrained:
            return {
                "status": "HOLD",
                "governance_status": "HOLD",
                "error_code": "F2_TRUTH_NOT_WELL_CONSTRAINED",
                "message": (
                    f"Voxel is not well_constrained. "
                    f"observation_count={obs_count} (need >= 3), "
                    f"forward_model_residual={residual:.4f} (need < 0.3). "
                    f"Per ADR-008, this seal is held until the underlying voxel "
                    f"is sufficiently constrained by observations and forward-model fit."
                ),
                "floor": "F2_TRUTH",
                "guard": "RT3",
                "claim_id": kwargs.get("claim_id", ""),
                "well_constrained": False,
                "observation_count": obs_count,
                "forward_model_residual": residual,
                "required_action": (
                    "Either (a) gather more observations to bring obs_count >= 3, "
                    "or (b) improve forward-model fit to bring residual < 0.3, "
                    "then retry seal."
                ),
            }

        # well_constrained=True → proceed to underlying seal implementation
        from geox_mcp.tools.claims import geox_claim_seal as _impl
        result = await _impl(
            claim_id=kwargs.get("claim_id", ""),
            ack_irreversible=kwargs.get("ack_irreversible", False),
            seal_verdict=kwargs.get("seal_verdict", "SEAL"),
        )
        # Annotate the result with the well_constrained proof (F11 AUDIT)
        if isinstance(result, dict):
            result["well_constrained_check"] = {
                "observation_count": obs_count,
                "forward_model_residual": residual,
                "well_constrained": True,
                "floor_enforced": "F2_TRUTH",
                "adr_reference": "ADR-008",
            }
        return result

    if mode == "attach_evidence":
        from geox_mcp.tools.claims import geox_evidence_attach as _impl
        return await _impl(
            claim_id=kwargs.get("claim_id", ""),
            evidence_id=kwargs.get("evidence_id", ""),
            evidence_type=kwargs.get("evidence_type", "supporting"),
            provenance=kwargs.get("provenance", "GEOX Claim Engine"),
        )

    # Default: create
    from geox_mcp.tools.claims import geox_claim_create as _impl
    return await _impl(
        claim_text=kwargs.get("claim_text", ""),
        claim_type=kwargs.get("claim_type", "other"),
        truth_class=kwargs.get("truth_class", "INTERPRETATION"),
        evidence_ids=kwargs.get("evidence_ids", []),
        uncertainty_p10=kwargs.get("uncertainty_p10"),
        uncertainty_p50=kwargs.get("uncertainty_p50"),
        uncertainty_p90=kwargs.get("uncertainty_p90"),
        uncertainty_distribution=kwargs.get("uncertainty_distribution", "lognormal"),
        alternatives=kwargs.get("alternatives"),
        provenance=kwargs.get("provenance", "GEOX Claim Engine"),
        authority=kwargs.get("authority", "GEOX_CLAIM_WORKER"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Falsification Engine — geox_falsify
# ═══════════════════════════════════════════════════════════════════════════════

import logging
import re

logger = logging.getLogger("geox.falsify")

# ── Falsification Filters (K001–K007) ────────────────────────────────────────

FALSIFICATION_FILTERS: list[dict[str, Any]] = [
    {
        "id": "K001",
        "name": "Physical Plausibility",
        "description": "Does the claim violate known physical constraints?",
        "patterns": [
            (r"porosity\s*(?:of\s*)?(?:>?\s*)?(\d+)\s*%?\s*(?:at|@)\s*(\d+)\s*m", "_check_porosity_depth"),
            (r"permeability\s*(?:of\s*)?(?:>?\s*)?(\d+)\s*m[Dd]", "_check_perm_plausibility"),
            (r"temperature\s*(?:of\s*)?(?:>?\s*)?(\d+)\s*°?C?\s*(?:at|@)\s*(\d+)\s*m", "_check_temperature_depth"),
            (r"pressure\s*(?:of\s*)?(?:>?\s*)?(\d+)\s*(?:MPa|psi|bar)\s*(?:at|@)\s*(\d+)\s*m", "_check_pressure_depth"),
        ],
    },
    {
        "id": "K002",
        "name": "Stratigraphic Consistency",
        "description": "Does the claim respect stratigraphic superposition and known basin history?",
        "patterns": [
            (r"\b(miocene|pliocene|oligocene|eocene|cretaceous|jurassic|triassic|permian|carboniferous|devonian|silurian|ordovician|cambrian)\b", "_check_age_basin_consistency"),
            (r"\b(sandstone|shale|carbonate|limestone|dolomite|coal|evaporite|volcaniclastic)\b", "_check_lithology_depth"),
        ],
    },
    {
        "id": "K003",
        "name": "Geothermal Gradient Check",
        "description": "Is the implied geothermal gradient within plausible range (15-50 °C/km)?",
        "patterns": [
            (r"(\d+)\s*°?C?\s*(?:at|@)\s*(\d+)\s*m", "_check_geothermal_gradient"),
        ],
    },
    {
        "id": "K004",
        "name": "Burial/Compaction Check",
        "description": "Is the claimed porosity consistent with expected compaction at that depth?",
        "patterns": [],
        "handler": "_check_compaction_porosity",
    },
    {
        "id": "K005",
        "name": "Hydrostatic/Pore Pressure Check",
        "description": "Is the claimed pressure within hydrostatic to lithostatic bounds?",
        "patterns": [],
        "handler": "_check_pressure_bounds",
    },
    {
        "id": "K006",
        "name": "Logical Consistency",
        "description": "Does the claim contain internal contradictions?",
        "patterns": [
            (r"both.*and.*(?:simultaneously|at the same time)", "_flag_contradiction"),
            (r"(?:above|overlying).*(?:below|underlying)", "_flag_contradiction"),
            (r"(?:oil|gas|condensate).*(?:dry|barren|sterile)", "_flag_contradiction"),
        ],
    },
    {
        "id": "K007",
        "name": "Evidence Sufficiency",
        "description": "Is the claim supported by evidence or is it speculative?",
        "patterns": [
            (r"(?:might|could|may|possibly|probably|likely|appears|seems|suggests|indicates)", "_flag_speculative"),
            (r"(?:unknown|uncertain|unclear|speculative|hypothetical|unproven)", "_flag_speculative"),
        ],
    },
]


def _check_porosity_depth(match: re.Match, claim: str) -> dict[str, Any]:
    """K001: Check porosity at depth against physical limits."""
    porosity = float(match.group(1))
    depth = float(match.group(2))
    # Athy's law: phi = phi_0 * exp(-c * z), typical phi_0 ~ 0.45, c ~ 0.0004/m
    max_phi = 0.45  # max initial porosity
    decay = 0.0004  # compaction coefficient
    expected_max = max_phi * (2.71828 ** (-decay * depth))
    
    findings = []
    if porosity > 50:
        findings.append({"severity": "FATAL", "reason": f"Porosity {porosity}% exceeds physical maximum (~50%) for sedimentary rocks"})
    elif porosity > expected_max * 100 * 1.3:  # 30% tolerance
        findings.append({"severity": "HIGH", "reason": f"Porosity {porosity}% exceeds Athy-compaction expected max {expected_max*100:.1f}% at {depth}m"})
    elif porosity > expected_max * 100:
        findings.append({"severity": "MEDIUM", "reason": f"Porosity {porosity}% is high but possible at {depth}m (expected max ~{expected_max*100:.1f}%)"})
    else:
        findings.append({"severity": "PASS", "reason": f"Porosity {porosity}% at {depth}m is physically plausible"})
    return {"filter": "K001", "findings": findings}


def _check_perm_plausibility(match: re.Match, claim: str) -> dict[str, Any]:
    perm = float(match.group(1))
    findings = []
    if perm > 10000:
        findings.append({"severity": "HIGH", "reason": f"Permeability {perm}mD is extremely high; verify with analogue data"})
    elif perm < 0.001:
        findings.append({"severity": "INFO", "reason": f"Permeability {perm}mD is very low (<0.001mD); effectively a seal"})
    else:
        findings.append({"severity": "PASS", "reason": f"Permeability {perm}mD is within plausible range for reservoir rocks"})
    return {"filter": "K001", "findings": findings}


def _check_temperature_depth(match: re.Match, claim: str) -> dict[str, Any]:
    temp = float(match.group(1))
    depth = float(match.group(2))
    gradient = (temp - 25) / (depth / 1000)  # assume surface temp 25°C
    findings = []
    if gradient < 10:
        findings.append({"severity": "HIGH", "reason": f"Implied geothermal gradient {gradient:.0f}°C/km is unusually low"})
    elif gradient > 55:
        findings.append({"severity": "FATAL", "reason": f"Implied geothermal gradient {gradient:.0f}°C/km exceeds crustal plausibility"})
    elif gradient > 45:
        findings.append({"severity": "MEDIUM", "reason": f"Implied geothermal gradient {gradient:.0f}°C/km is high (hot basin)"})
    else:
        findings.append({"severity": "PASS", "reason": f"Geothermal gradient {gradient:.0f}°C/km is plausible"})
    return {"filter": "K003", "findings": findings}


def _check_pressure_depth(match: re.Match, claim: str) -> dict[str, Any]:
    findings = []
    findings.append({"severity": "INFO", "reason": "Pressure-depth check: verify against hydrostatic (0.433 psi/ft) and lithostatic (~1.0 psi/ft) gradients"})
    return {"filter": "K005", "findings": findings}


def _check_age_basin_consistency(match: re.Match, claim: str) -> dict[str, Any]:
    age = match.group(1).lower()
    findings = []
    # Malay Basin context: primarily Oligocene-Miocene fill
    malay_valid = ["miocene", "pliocene", "oligocene", "eocene"]
    if age not in malay_valid and "malay" in claim.lower():
        findings.append({"severity": "MEDIUM", "reason": f"{age.title()} age mentioned; Malay Basin fill is primarily Oligocene-Miocene. Verify stratigraphic context."})
    else:
        findings.append({"severity": "PASS", "reason": f"{age.title()} age is consistent with SE Asian basin stratigraphy"})
    return {"filter": "K002", "findings": findings}


def _check_lithology_depth(match: re.Match, claim: str) -> dict[str, Any]:
    lith = match.group(1).lower()
    findings = []
    # Check for depth-related lithology issues
    if "evaporite" in lith:
        findings.append({"severity": "INFO", "reason": "Evaporite presence requires restricted basin conditions — verify depositional model"})
    elif "coal" in lith:
        findings.append({"severity": "INFO", "reason": "Coal indicates terrestrial/fluvio-deltaic deposition — verify paleoenvironment"})
    else:
        findings.append({"severity": "PASS", "reason": f"{lith.title()} lithology is geologically common"})
    return {"filter": "K002", "findings": findings}


def _check_geothermal_gradient(match: re.Match, claim: str) -> dict[str, Any]:
    temp = float(match.group(1))
    depth = float(match.group(2))
    gradient = (temp - 25) / (depth / 1000)
    findings = []
    if 15 <= gradient <= 50:
        findings.append({"severity": "PASS", "reason": f"Geothermal gradient {gradient:.0f}°C/km within normal range (15-50)"})
    elif gradient < 15:
        findings.append({"severity": "MEDIUM", "reason": f"Geothermal gradient {gradient:.0f}°C/km is below normal range (cold basin/foreland)"})
    else:
        findings.append({"severity": "HIGH", "reason": f"Geothermal gradient {gradient:.0f}°C/km above normal range"})
    return {"filter": "K003", "findings": findings}


def _check_compaction_porosity(match: re.Match | None, claim: str) -> dict[str, Any]:
    """K004: Check porosity-depth trend against Athy compaction model."""
    findings = []
    # Extract any depth-porosity pairs
    pairs = re.findall(r"(\d+)\s*%?\s*(?:porosity\s*)?(?:at|@)\s*(\d+)\s*m", claim, re.IGNORECASE)
    if not pairs:
        findings.append({"severity": "INFO", "reason": "No depth-porosity pair found for compaction check"})
    else:
        for poro_str, depth_str in pairs:
            poro = float(poro_str)
            depth = float(depth_str)
            max_phi = 0.45 * (2.71828 ** (-0.0004 * depth)) * 100
            if poro > max_phi * 1.5:
                findings.append({"severity": "HIGH", "reason": f"Porosity {poro}% at {depth}m far exceeds Athy max {max_phi:.1f}%"})
    return {"filter": "K004", "findings": findings}


def _check_pressure_bounds(match: re.Match | None, claim: str) -> dict[str, Any]:
    """K005: Check pressure bounds."""
    findings = []
    findings.append({"severity": "INFO", "reason": "Pressure check requires explicit depth and gradient context. Verify against offset well data."})
    return {"filter": "K005", "findings": findings}


def _flag_contradiction(match: re.Match, claim: str) -> dict[str, Any]:
    return {"filter": "K006", "findings": [{"severity": "HIGH", "reason": f"Potential logical contradiction detected: '{match.group(0)}'"}]}


def _flag_speculative(match: re.Match, claim: str) -> dict[str, Any]:
    return {"filter": "K007", "findings": [{"severity": "INFO", "reason": f"Speculative language: '{match.group(0)}'. Evidence strength should be verified."}]}


async def geox_falsify(
    claim_text: str = "",
    claim_type: str = "general",
    mode: str = "full",
    context: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Popperian falsification engine for geological claims.

    Tests a claim against 7 filters (K001-K007): physical plausibility,
    stratigraphic consistency, geothermal gradient, compaction, pressure,
    logical consistency, and evidence sufficiency.

    Any single filter returning FATAL or HIGH → overall FALSIFIED.
    All filters PASS → SURVIVED (but never PROVEN — Popper).

    DITEMPA BUKAN DIBERI — Forged, Not Given.
    """
    if not claim_text.strip():
        return {
            "execution_status": "INVALID",
            "verdict": "INCONCLUSIVE",
            "filters_run": 0,
            "filters_passed": 0,
            "filters_failed": 0,
            "results": [],
            "honesty_banner": "No claim provided. Falsification requires a claim to test.",
        }

    results: list[dict[str, Any]] = []
    fatal_count = 0
    high_count = 0
    pass_count = 0

    for filt in FALSIFICATION_FILTERS:
        filter_results: list[dict[str, Any]] = []
        
        # Try pattern-based checks (only for patterns belonging to this filter)
        for pattern_str, handler_name in filt.get("patterns", []):
            for match in re.finditer(pattern_str, claim_text, re.IGNORECASE):
                handler = globals().get(handler_name)
                if handler:
                    try:
                        result = handler(match, claim_text)
                        filter_results.extend(result.get("findings", []))
                    except (IndexError, AttributeError, ValueError) as e:
                        logger.debug(f"Handler {handler_name} failed on match: {e}")

        # Try handler-based checks
        handler_name = filt.get("handler")
        if handler_name:
            handler = globals().get(handler_name)
            if handler:
                result = handler(None, claim_text)
                filter_results.extend(result.get("findings", []))

        # Determine filter-level verdict
        severities = [f.get("severity", "PASS") for f in filter_results]
        if "FATAL" in severities:
            filter_verdict = "FALSIFIED"
            fatal_count += 1
        elif "HIGH" in severities:
            filter_verdict = "FALSIFIED"
            high_count += 1
        elif not filter_results:
            filter_verdict = "NOT_TESTED"
        elif all(s == "PASS" for s in severities):
            filter_verdict = "PASS"
            pass_count += 1
        elif all(s in ("PASS", "INFO") for s in severities):
            filter_verdict = "PASS"
            pass_count += 1
        else:
            filter_verdict = "INCONCLUSIVE"

        results.append({
            "filter_id": filt["id"],
            "filter_name": filt["name"],
            "verdict": filter_verdict,
            "findings": filter_results,
        })

    # Overall verdict
    if fatal_count > 0:
        overall_verdict = "FALSIFIED"
        overall_reason = f"{fatal_count} FATAL violation(s) found. Claim cannot be true as stated."
    elif high_count > 0:
        overall_verdict = "FALSIFIED"
        overall_reason = f"{high_count} HIGH-severity issue(s) found. Claim is unlikely to be true."
    elif pass_count == len(results):
        overall_verdict = "SURVIVED"
        overall_reason = "All filters passed. Claim survives falsification (not proven — Popper)."
    else:
        overall_verdict = "INCONCLUSIVE"
        overall_reason = "Insufficient evidence to falsify. More data needed."

    return {
        "execution_status": "SUCCESS",
        "verdict": overall_verdict,
        "reason": overall_reason,
        "filters_run": len(results),
        "filters_passed": pass_count,
        "filters_failed": fatal_count + high_count,
        "results": results,
        "claim_text": claim_text[:500],
        "claim_type": claim_type,
        "mode": mode,
        "epistemic_label": "DER",
        "honesty_banner": "Falsification tests what CANNOT be true. SURVIVED ≠ PROVEN. Any single filter FALSIFIED → overall FALSIFIED.",
    }
