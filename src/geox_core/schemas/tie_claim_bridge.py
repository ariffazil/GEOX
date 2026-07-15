"""
GEOX Tie-Claim Bridge — Residual Classifier → Claim Grammar
═══════════════════════════════════════════════════════════════════════════════════

Binds the residual classifier (from TieReceipt) to the claim grammar
(from ClaimCard). When a tie produces a residual, this bridge automatically
populates the claim's evidence_against, missing_tests, contradictions,
and promotion constraints.

The residual is not just error — it is the claim's immune system.

Schema:   TieClaimBridge
Version:  1.0.0
Domain:   NATURAL_LAW
Organ:    GEOX

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# RESIDUAL → CLAIM GRAMMAR MAPPING
# ──────────────────────────────────────────────────────────────────────────────
# Each residual class maps to:
#   - evidence_against: what this residual contradicts
#   - missing_tests: what would resolve the residual
#   - claim_constraint: what claims cannot be promoted
#   - ac_risk_delta: how much this residual adds to AC Risk

RESIDUAL_CLAIM_MAP: dict[str, dict[str, Any]] = {
    "time_depth_error": {
        "evidence_against": [
            "Structural depth conversion may be incorrect",
            "Trap geometry and closure may be wrong",
            "Gross rock volume estimate is unreliable",
        ],
        "missing_tests": [
            "Acquire checkshot or VSP data",
            "Verify velocity model against regional trends",
            "Check for anisotropy effects",
        ],
        "claim_constraints": [
            "Cannot promote structural claims beyond INTERPRETED_LOCAL",
            "Cannot use depth-dependent volumetrics",
            "Cannot book reserves without corrected velocity",
        ],
        "ac_risk_delta": 0.25,
        "affected_claim_types": ["structural", "volumetric", "prospect"],
    },
    "wavelet_error": {
        "evidence_against": [
            "Synthetic-to-seismic correlation may be misleading",
            "Phase or amplitude of synthetic is unreliable",
        ],
        "missing_tests": [
            "Extract wavelet from well-seismic tie",
            "Test multiple wavelet phases (0°, 90°, 180°)",
            "Verify polarity convention against known reflectors",
        ],
        "claim_constraints": [
            "Cannot use correlation score as tie validation",
            "All horizon picks based on this tie are suspect",
        ],
        "ac_risk_delta": 0.15,
        "affected_claim_types": ["seismic", "stratigraphic"],
    },
    "log_conditioning_error": {
        "evidence_against": [
            "Well-derived properties (porosity, Vp, rho) may be unreliable",
            "Petrophysical cutoffs may be incorrectly calibrated",
        ],
        "missing_tests": [
            "Check borehole condition (caliper log)",
            "Verify environmental corrections applied",
            "Compare with nearby wells for consistency",
        ],
        "claim_constraints": [
            "Cannot use affected log curves for quantitative claims",
            "Petrophysical analysis on affected intervals is HOLD",
        ],
        "ac_risk_delta": 0.20,
        "affected_claim_types": ["petrophysical", "volumetric"],
    },
    "checkshot_vsp_error": {
        "evidence_against": [
            "Time-depth calibration is unreliable",
            "All time-to-depth conversions are suspect",
        ],
        "missing_tests": [
            "Acquire checkshot data",
            "Run VSP if possible",
            "Use regional velocity function as sanity check",
        ],
        "claim_constraints": [
            "All depth-dependent claims are HOLD",
            "Time-domain interpretation may still be valid",
        ],
        "ac_risk_delta": 0.30,
        "affected_claim_types": ["structural", "stratigraphic", "volumetric"],
    },
    "processing_error": {
        "evidence_against": [
            "Seismic image may contain artifacts",
            "Migration may have introduced smearing or positioning errors",
            "Multiple contamination may create false reflectors",
        ],
        "missing_tests": [
            "Review processing sequence report",
            "Check migration type and aperture",
            "Look for residual multiples on far offsets",
        ],
        "claim_constraints": [
            "Structural interpretation at risk",
            "Amplitude analysis unreliable in affected zones",
        ],
        "ac_risk_delta": 0.20,
        "affected_claim_types": ["seismic", "structural"],
    },
    "stratigraphic_error": {
        "evidence_against": [
            "Horizon correlation may be wrong",
            "Formation tops may be misidentified",
            "Sequence boundaries may be misinterpreted",
        ],
        "missing_tests": [
            "Check biostrat data for age constraints",
            "Verify marker picks against type logs",
            "Cross-validate with regional stratigraphic framework",
        ],
        "claim_constraints": [
            "Cannot promote stratigraphic claims beyond HYPOTHESIS",
            "Well-to-well correlation is suspect",
        ],
        "ac_risk_delta": 0.20,
        "affected_claim_types": ["stratigraphic", "prospect"],
    },
    "rock_physics_error": {
        "evidence_against": [
            "Elastic-fluid-lithology link is unreliable",
            "AVO classification may be wrong",
            "Inversion results may not reflect true lithology or fluid",
        ],
        "missing_tests": [
            "Build rock physics template from well data",
            "Check elastic property separability (sand vs shale, brine vs gas)",
            "Verify fluid substitution model",
        ],
        "claim_constraints": [
            "Cannot claim fluid type from seismic alone",
            "AVO-based prospectivity is HOLD",
            "Inversion-derived lithology maps are HOLD",
        ],
        "ac_risk_delta": 0.30,
        "affected_claim_types": ["petrophysical", "prospect"],
    },
    "scale_error": {
        "evidence_against": [
            "Thin beds may be below seismic resolution",
            "Amplitude may not reflect true thickness (tuning effect)",
            "Well-to-seismic comparison is scale-limited",
        ],
        "missing_tests": [
            "Estimate tuning thickness from well data",
            "Model thin-bed seismic response",
            "Check if target interval is above or below tuning",
        ],
        "claim_constraints": [
            "Cannot convert amplitude directly to thickness",
            "Thin reservoir presence is uncertain from seismic alone",
        ],
        "ac_risk_delta": 0.15,
        "affected_claim_types": ["volumetric", "petrophysical"],
    },
    "lateral_heterogeneity": {
        "evidence_against": [
            "Well may not represent nearby geology",
            "Lateral facies changes may invalidate well-seismic tie beyond well location",
        ],
        "missing_tests": [
            "Check nearby well ties for consistency",
            "Map lateral facies variation from seismic attributes",
            "Verify structural position of well relative to seismic",
        ],
        "claim_constraints": [
            "Tie quality is LOCAL — does not extend to full survey",
            "Lateral extrapolation of well properties is risky",
        ],
        "ac_risk_delta": 0.15,
        "affected_claim_types": ["stratigraphic", "volumetric"],
    },
    "fluid_pressure_error": {
        "evidence_against": [
            "Hydrocarbon or pressure effects may be misidentified",
            "Bright spot may not indicate gas",
            "Pressure prediction may be wrong",
        ],
        "missing_tests": [
            "Check DST or MDT pressure data",
            "Verify fluid type from logs (resistivity, neutron-density crossover)",
            "Model expected AVO response for different fluids",
        ],
        "claim_constraints": [
            "Cannot claim hydrocarbon presence from amplitude alone",
            "Pressure prediction is HOLD without calibration",
        ],
        "ac_risk_delta": 0.25,
        "affected_claim_types": ["petrophysical", "prospect"],
    },
    "structural_error": {
        "evidence_against": [
            "Fault positions may be wrong",
            "Trap integrity is uncertain",
            "Closure may be incorrectly mapped",
        ],
        "missing_tests": [
            "Verify fault picks on multiple lines",
            "Check fault seal capacity",
            "Validate structural map against well control",
        ],
        "claim_constraints": [
            "Structural trap is UNVERIFIED",
            "Cannot promote prospect without structural validation",
        ],
        "ac_risk_delta": 0.25,
        "affected_claim_types": ["structural", "prospect"],
    },
    "governance_error": {
        "evidence_against": [
            "Decision was promoted beyond evidence level",
            "Claim state advancement was premature",
        ],
        "missing_tests": [
            "Review claim promotion history",
            "Verify all required evidence was present at promotion time",
            "Check if AC Risk was assessed before promotion",
        ],
        "claim_constraints": [
            "All claims promoted under this tie must be DOWNGRADED",
            "Re-evaluate claim_state from DRAFT",
        ],
        "ac_risk_delta": 0.35,
        "affected_claim_types": ["all"],
    },
    "good_tie": {
        "evidence_against": [],
        "missing_tests": [
            "Verify with additional wells if available",
            "Monitor for new data that could challenge tie",
        ],
        "claim_constraints": [],
        "ac_risk_delta": 0.0,
        "affected_claim_types": [],
    },
    "unexplained": {
        "evidence_against": [
            "Residual origin is unknown — model integrity uncertain",
        ],
        "missing_tests": [
            "Diagnose residual origin systematically",
            "Test each error class individually",
        ],
        "claim_constraints": [
            "All claims are HOLD until residual is classified",
        ],
        "ac_risk_delta": 0.20,
        "affected_claim_types": ["all"],
    },
}


def bridge_residual_to_claim(
    residual_class: str,
    claim_type: str = "all",
    existing_ac_risk: float = 0.0,
) -> dict[str, Any]:
    """Convert a residual classification into claim grammar fields.

    Parameters
    ----------
    residual_class : str
        One of the ResidualClass values from tie_receipt.py.
    claim_type : str
        The claim type being evaluated (structural, petrophysical, etc.).
        Used to filter which constraints apply.
    existing_ac_risk : float
        Current AC Risk before this residual (0.0-1.0).

    Returns
    -------
    dict
        Claim grammar fields: evidence_against, missing_tests,
        claim_constraints, ac_risk, promotion_allowed.
    """
    mapping = RESIDUAL_CLAIM_MAP.get(residual_class, RESIDUAL_CLAIM_MAP["unexplained"])

    # Filter constraints by claim type
    affected_types = mapping.get("affected_claim_types", [])
    is_affected = "all" in affected_types or claim_type in affected_types

    # Compute AC Risk
    delta = mapping.get("ac_risk_delta", 0.20)
    new_ac_risk = min(1.0, existing_ac_risk + delta) if is_affected else existing_ac_risk

    # Determine promotion permission
    if residual_class == "good_tie":
        promotion_allowed = True
    elif residual_class in ("governance_error", "unexplained") and is_affected:
        promotion_allowed = False
    elif delta >= 0.25 and is_affected:
        promotion_allowed = False
    else:
        promotion_allowed = True  # may proceed with caveats

    return {
        "residual_class": residual_class,
        "claim_type": claim_type,
        "is_affected": is_affected,
        "evidence_against": mapping.get("evidence_against", []),
        "missing_tests": mapping.get("missing_tests", []),
        "claim_constraints": mapping.get("claim_constraints", []) if is_affected else [],
        "ac_risk": round(new_ac_risk, 2),
        "ac_risk_delta": delta if is_affected else 0.0,
        "promotion_allowed": promotion_allowed,
        "anti_hantu": residual_class != "good_tie",
    }
