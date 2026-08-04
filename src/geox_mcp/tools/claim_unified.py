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
            (
                r"\b(miocene|pliocene|oligocene|eocene|cretaceous|jurassic|triassic|permian|carboniferous|devonian|silurian|ordovician|cambrian)\b",
                "_check_age_basin_consistency",
            ),
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
    {
        "id": "K008",
        "name": "Thermal Maturity Bounds Check",
        "description": "Is the claimed maturity consistent with burial depth and expected geothermal gradient?",
        "patterns": [
            (r"(\d+\.?\d*)\s*%\s*(?:Ro|vitrinite|matur)", "_check_maturity_depth_consistency"),
        ],
        "handler": "_check_maturity_claims",
    },
    {
        "id": "K008b",
        "name": "Gradient Plausibility (OCT-aware)",
        "description": "Is the claimed gradient within expected range for the basin type?",
        "patterns": [],
        "handler": "_check_gradient_basin_type",
    },
    {
        # Session distillation 2026-08-04 (Rotan/NSPW EUREKA): pressure connectivity
        # is a present-day snapshot; hydrocarbon migration is a multi-Ma history.
        # Conflating the two produces overconfident charge claims (Copilot audit caught 5).
        "id": "K009",
        "name": "Pressure Snapshot ≠ Migration History",
        "description": (
            "Hard rule: present-day pressure connectivity is a snapshot; "
            "hydrocarbon migration is a history. Claims that equate connected "
            "pressure compartments with proven migration pathways must be "
            "demoted unless they carry independent charge evidence (isotopes, "
            "FIS, biomarkers, timed fill indicators)."
        ),
        "patterns": [
            (
                r"(?:pressure\s+connect|connected\s+pressure|pressure\s+communicat|"
                r"hydrostatic\s+connect|same\s+pressure\s+regime)",
                "_check_pressure_vs_migration",
            ),
            (
                r"(?:therefore|thus|hence|proves?|implies?|confirms?).{0,40}"
                r"(?:migrat|charge|fill|kitchen|source\s*rock)",
                "_check_pressure_vs_migration",
            ),
            (
                r"(?:migrat|charge|fill).{0,40}"
                r"(?:because|due\s+to|from).{0,40}pressure",
                "_check_pressure_vs_migration",
            ),
        ],
        "handler": "_check_pressure_vs_migration_handler",
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
        findings.append(
            {"severity": "FATAL", "reason": f"Porosity {porosity}% exceeds physical maximum (~50%) for sedimentary rocks"}
        )
    elif porosity > expected_max * 100 * 1.3:  # 30% tolerance
        findings.append(
            {
                "severity": "HIGH",
                "reason": f"Porosity {porosity}% exceeds Athy-compaction expected max {expected_max * 100:.1f}% at {depth}m",
            }
        )
    elif porosity > expected_max * 100:
        findings.append(
            {
                "severity": "MEDIUM",
                "reason": f"Porosity {porosity}% is high but possible at {depth}m (expected max ~{expected_max * 100:.1f}%)",
            }
        )
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
        findings.append(
            {"severity": "FATAL", "reason": f"Implied geothermal gradient {gradient:.0f}°C/km exceeds crustal plausibility"}
        )
    elif gradient > 45:
        findings.append({"severity": "MEDIUM", "reason": f"Implied geothermal gradient {gradient:.0f}°C/km is high (hot basin)"})
    else:
        findings.append({"severity": "PASS", "reason": f"Geothermal gradient {gradient:.0f}°C/km is plausible"})
    return {"filter": "K003", "findings": findings}


def _check_pressure_depth(match: re.Match, claim: str) -> dict[str, Any]:
    findings = []
    findings.append(
        {
            "severity": "INFO",
            "reason": "Pressure-depth check: verify against hydrostatic (0.433 psi/ft) and lithostatic (~1.0 psi/ft) gradients",
        }
    )
    return {"filter": "K005", "findings": findings}


def _check_age_basin_consistency(match: re.Match, claim: str) -> dict[str, Any]:
    age = match.group(1).lower()
    findings = []
    # Malay Basin context: primarily Oligocene-Miocene fill
    malay_valid = ["miocene", "pliocene", "oligocene", "eocene"]
    if age not in malay_valid and "malay" in claim.lower():
        findings.append(
            {
                "severity": "MEDIUM",
                "reason": f"{age.title()} age mentioned; Malay Basin fill is primarily Oligocene-Miocene. Verify stratigraphic context.",
            }
        )
    else:
        findings.append({"severity": "PASS", "reason": f"{age.title()} age is consistent with SE Asian basin stratigraphy"})
    return {"filter": "K002", "findings": findings}


def _check_lithology_depth(match: re.Match, claim: str) -> dict[str, Any]:
    lith = match.group(1).lower()
    findings = []
    # Check for depth-related lithology issues
    if "evaporite" in lith:
        findings.append(
            {"severity": "INFO", "reason": "Evaporite presence requires restricted basin conditions — verify depositional model"}
        )
    elif "coal" in lith:
        findings.append(
            {"severity": "INFO", "reason": "Coal indicates terrestrial/fluvio-deltaic deposition — verify paleoenvironment"}
        )
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
        findings.append(
            {
                "severity": "MEDIUM",
                "reason": f"Geothermal gradient {gradient:.0f}°C/km is below normal range (cold basin/foreland)",
            }
        )
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
                findings.append(
                    {"severity": "HIGH", "reason": f"Porosity {poro}% at {depth}m far exceeds Athy max {max_phi:.1f}%"}
                )
    return {"filter": "K004", "findings": findings}


def _check_pressure_bounds(match: re.Match | None, claim: str) -> dict[str, Any]:
    """K005: Check pressure bounds."""
    findings = []
    findings.append(
        {
            "severity": "INFO",
            "reason": "Pressure check requires explicit depth and gradient context. Verify against offset well data.",
        }
    )
    return {"filter": "K005", "findings": findings}


def _flag_contradiction(match: re.Match, claim: str) -> dict[str, Any]:
    return {
        "filter": "K006",
        "findings": [{"severity": "HIGH", "reason": f"Potential logical contradiction detected: '{match.group(0)}'"}],
    }


def _flag_speculative(match: re.Match, claim: str) -> dict[str, Any]:
    return {
        "filter": "K007",
        "findings": [
            {"severity": "INFO", "reason": f"Speculative language: '{match.group(0)}'. Evidence strength should be verified."}
        ],
    }


# ── K008: Thermal Maturity Checks ──────────────────────────────────────────


def _check_maturity_depth_consistency(match: re.Match, claim: str) -> dict[str, Any]:
    """K008: If Ro is claimed, check it's consistent with expected depth/gradient."""
    ro = float(match.group(1))
    findings: list[dict[str, Any]] = []

    if ro > 4.5:
        findings.append(
            {
                "severity": "FATAL",
                "reason": f"Ro={ro}% exceeds physical maximum for vitrinite reflectance (~4.5%). Check calibration.",
            }
        )
    elif ro < 0.2:
        findings.append(
            {
                "severity": "HIGH",
                "reason": f"Ro={ro}% is below minimum for any thermal alteration. Check measurement.",
            }
        )
    elif ro > 2.0 and "oil" in claim.lower():
        findings.append(
            {
                "severity": "MEDIUM",
                "reason": f"Ro={ro}% is in dry gas window (>2.0), yet 'oil' is claimed. Check charge timing.",
            }
        )
    else:
        findings.append(
            {
                "severity": "PASS",
                "reason": f"Ro={ro}% is within physically plausible range (0.2-4.5)",
            }
        )

    return {"filter": "K008", "findings": findings}


def _check_maturity_claims(match: re.Match | None, claim: str) -> dict[str, Any]:
    """K008: Check thermal maturity claims for physical consistency."""
    findings: list[dict[str, Any]] = []

    has_oil = bool(re.search(r"\boil\b", claim, re.IGNORECASE))
    has_gas = bool(re.search(r"\bgas\b", claim, re.IGNORECASE))
    has_immature = bool(re.search(r"\bimmatur", claim, re.IGNORECASE))
    has_overmature = bool(re.search(r"\bovermatur", claim, re.IGNORECASE))

    if has_oil and has_overmature:
        findings.append(
            {
                "severity": "MEDIUM",
                "reason": "Claim mentions both oil and overmaturity. Oil is typically destroyed above Ro~1.3%.",
            }
        )
    if has_immature and has_oil:
        findings.append(
            {
                "severity": "MEDIUM",
                "reason": "Claim mentions both immaturity and oil. Source must be mature to generate oil.",
            }
        )
    if not findings:
        findings.append({"severity": "PASS", "reason": "No maturity contradictions detected"})

    return {"filter": "K008", "findings": findings}


def _check_gradient_basin_type(match: re.Match | None, claim: str) -> dict[str, Any]:
    """K008b: Check if claimed gradient is consistent with known basin type."""
    findings: list[dict[str, Any]] = []

    is_sabah = bool(re.search(r"\b(sabah|dangerous\s*ground|nw\s*borneo)\b", claim, re.IGNORECASE))
    is_oct = bool(re.search(r"\b(hyperextend|oct|ocean.continent|exhum|serpentin)\b", claim, re.IGNORECASE))

    grad_match = re.search(r"(\d+)\s*(?:°C/km|C/km|deg.?C.?km)", claim, re.IGNORECASE)
    if grad_match:
        grad = float(grad_match.group(1))
        if is_sabah and grad < 30:
            findings.append(
                {
                    "severity": "HIGH",
                    "reason": f"Gradient {grad}°C/km is below expected for Sabah hyperextended margin (documented 50-65°C/km locally)",
                }
            )
        elif is_oct and grad < 35:
            findings.append(
                {
                    "severity": "MEDIUM",
                    "reason": f"Gradient {grad}°C/km is low for OCT-influenced basin. Expect >35°C/km.",
                }
            )
        elif grad > 70:
            findings.append(
                {
                    "severity": "HIGH",
                    "reason": f"Gradient {grad}°C/km exceeds crustal plausibility without active magmatism.",
                }
            )
        else:
            findings.append(
                {
                    "severity": "PASS",
                    "reason": f"Gradient {grad}°C/km is plausible for the basin context",
                }
            )
    else:
        findings.append({"severity": "INFO", "reason": "No gradient value detected in claim"})

    return {"filter": "K008b", "findings": findings}


# ── K009: Pressure Snapshot ≠ Migration History (2026-08-04 distillation) ──


def _check_pressure_vs_migration(match: re.Match, claim: str) -> dict[str, Any]:
    """K009: Flag claims that treat present-day pressure connectivity as migration proof."""
    text = (claim or "").lower()
    findings: list[dict[str, Any]] = []

    pressure_lang = any(
        k in text
        for k in (
            "pressure connect",
            "connected pressure",
            "pressure communicat",
            "same pressure",
            "hydrostatic connect",
            "pressure continuity",
            "pressure continuity",
            "pressure compartment",
        )
    )
    migration_lang = any(
        k in text for k in ("migrat", "charge", "fill", "kitchen", "source rock", "source-rock")
    )
    equates = any(
        k in text
        for k in (
            "therefore",
            "thus",
            "hence",
            "proves",
            "prove",
            "implies",
            "imply",
            "confirms",
            "confirm",
            "because of pressure",
            "due to pressure",
            "from pressure",
        )
    )

    if pressure_lang and migration_lang and equates:
        findings.append(
            {
                "severity": "HIGH",
                "reason": (
                    "K009: Claim equates present-day pressure connectivity with hydrocarbon "
                    "migration/charge history. Pressure is a snapshot; migration is multi-Ma. "
                    "Require independent charge evidence (isotopes/FIS/biomarkers/timed fill) "
                    "or demote claim to INT/SPEC. epistemic→PROVISIONAL."
                ),
                "rule": "PRESSURE_SNAPSHOT_NE_MIGRATION_HISTORY",
                "epistemic_action": "DOWNGRADE_TO_INT_OR_SPEC",
            }
        )
    elif pressure_lang and migration_lang:
        findings.append(
            {
                "severity": "INFO",
                "reason": (
                    "K009 advisory: claim mentions both pressure connectivity and migration. "
                    "Keep them ontologically separate unless independent charge evidence is cited."
                ),
                "rule": "PRESSURE_SNAPSHOT_NE_MIGRATION_HISTORY",
            }
        )
    else:
        findings.append(
            {
                "severity": "PASS",
                "reason": "No pressure-connectivity→migration conflation detected",
            }
        )

    return {"filter": "K009", "findings": findings}


def _check_pressure_vs_migration_handler(match: re.Match | None, claim: str) -> dict[str, Any]:
    """Handler entry for K009 when no pattern match (full-text scan)."""
    return _check_pressure_vs_migration(match, claim)  # type: ignore[arg-type]


# ── geox_falsify ─────────────────────────────────────────────────────────


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

    Structural claim types route to G/K structure gates:
      structural_fault | structural_horizon | structural_framework

    Any single filter returning FATAL or HIGH → overall FALSIFIED.
    All filters PASS → SURVIVED (but never PROVEN — Popper).

    DITEMPA BUKAN DIBERI — Forged, Not Given.
    """
    ctype = (claim_type or "general").strip().lower()
    # ── Structural physics gates (Phase C) ──
    if ctype in (
        "structural_fault",
        "structural_horizon",
        "structural_framework",
        "structure",
        "fault_framework",
    ):
        from geox_mcp.tools.structure_validate import geox_structure_validate

        fw: dict[str, Any] = {}
        if isinstance(context, dict):
            fw = dict(context)
            # accept nested framework key
            if "framework" in fw and isinstance(fw["framework"], dict):
                nested = dict(fw["framework"])
                nested.update({k: v for k, v in fw.items() if k != "framework"})
                fw = nested
        if isinstance(evidence, dict):
            for k in ("faults", "horizons", "velocity", "restore", "claims", "measurement_context"):
                if k in evidence and k not in fw:
                    fw[k] = evidence[k]

        if not claim_text.strip() and not fw.get("faults") and not fw.get("horizons"):
            return {
                "execution_status": "INVALID",
                "verdict": "INCONCLUSIVE",
                "filters_run": 0,
                "filters_passed": 0,
                "filters_failed": 0,
                "results": [],
                "claim_type": claim_type,
                "honesty_banner": "Structural falsify needs claim_text or context.faults/horizons.",
            }

        # If only claim text, leave framework empty → structure_validate empty HOLD
        sv = await geox_structure_validate(framework=fw or None, claim_text=claim_text)
        kills = sv.get("kills") or []
        passes = sv.get("passes") or []
        overall = sv.get("overall_verdict", "INCONCLUSIVE")
        gate_results = []
        for gname, gval in (sv.get("gates") or {}).items():
            gate_results.append(
                {
                    "filter_id": gname,
                    "filter_name": gname,
                    "verdict": (
                        "FALSIFIED"
                        if gval.get("verdict") == "KILL"
                        else ("PASS" if gval.get("verdict") == "PASS" else "INCONCLUSIVE")
                    ),
                    "findings": gval.get("findings") or [{"reason": gval.get("reason")}],
                }
            )
        return {
            "execution_status": "SUCCESS",
            "verdict": overall if overall != "FALSIFIED" else "FALSIFIED",
            "reason": (f"Structural gates: kills={kills}, passes={passes}. combined={sv.get('combined_gate_verdict')}"),
            "filters_run": len(gate_results),
            "filters_passed": len(passes),
            "filters_failed": len(kills),
            "results": gate_results,
            "structure_validate": sv,
            "claim_text": (claim_text or "")[:500],
            "claim_type": claim_type,
            "mode": mode,
            "epistemic_label": "DER",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "seal_authority": "arifOS_only",
            "honesty_banner": ("Structural falsification via K-*/G* gates. SURVIVED ≠ proven. arifOS SEAL only."),
        }

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

        results.append(
            {
                "filter_id": filt["id"],
                "filter_name": filt["name"],
                "verdict": filter_verdict,
                "findings": filter_results,
            }
        )

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
