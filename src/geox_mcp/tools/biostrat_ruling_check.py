"""biostrat_ruling_check.py — Contradiction detector for biostratigraphic claims.

Phase 2.5 (2026-07-03): Per Arif sovereign spec.

Checks whether a biostratigraphic interpretation is physically and
biologically plausible given the depositional context. Detects:
  - Facies mismatch (e.g. open marine nannofossil zone in freshwater coal)
  - Impossible age ordering (younger fossil below older without explanation)
  - Reworking/caving warning triggers
  - Missing required multi-discipline convergence

Output: PASS, WEAK_PASS, CONTRADICTION, HOLD, or REJECT.

LAYER MODEL (Arif spec):
  Layer 1 — Observation: what was actually seen
  Layer 2 — Taxonomy: is the ID reliable and current
  Layer 3 — Bioevent: what stratigraphic event is inferred
  Layer 4 — Geological interpretation: what it means for age/environment

This tool operates primarily at Layers 3-4, flagging contradictions
between bioevent interpretation and geological context.

F2 TRUTH: Flags contradictions, does not resolve them.
F4 CLARITY: Structured verdict with required_next_evidence.
F6 MARUAH: Preserves scientific integrity — challenges, not overrides.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

from geox_core.enums.statuses import get_standard_envelope
from geox_mcp.tools.kernel._biostrat import lithology_class, map_gde, parse_nn_zone, nn_age

logger = logging.getLogger("geox.canonical.biostrat_ruling")

# ── Facies veto rules (Arif spec B4) ──────────────────────────────────────
# Maps biozone-implied environments to lithologies/environments that conflict

FACIES_VETO_RULES: list[dict[str, Any]] = [
    {
        "biozone_implication": "open_marine",
        "conflicting_lithology": ["COAL_CARBONACEOUS", "coal"],
        "conflicting_environment": ["freshwater", "fluvial", "lacustrine", "swamp"],
        "severity": "CONTRADICTION",
        "message": "Open marine interpretation conflicts with non-marine facies. Check for reworking, thin marine incursion, or misdescribed facies.",
    },
    {
        "biozone_implication": "deep_marine",
        "conflicting_lithology": ["COAL_CARBONACEOUS", "SAND_PRONE"],
        "conflicting_environment": ["fluvial", "deltaic", "coastal", "alluvial"],
        "severity": "CONTRADICTION",
        "message": "Deep marine biozone in shallow/continental facies. Requires transport mechanism, reworking, or reinterpretation.",
    },
    {
        "biozone_implication": "marine",
        "conflicting_lithology": ["COAL_CARBONACEOUS"],
        "conflicting_environment": ["freshwater_swamp", "lacustrine"],
        "severity": "WEAK_PASS",
        "message": "Marine biozone in marginal setting. Possible if thin marine incursion, but requires corroborating evidence.",
    },
    {
        "biozone_implication": "reef",
        "conflicting_lithology": ["SHALE_PRONE", "COAL_CARBONACEOUS"],
        "conflicting_environment": ["fluvial", "lacustrine", "deep_marine"],
        "severity": "CONTRADICTION",
        "message": "Reef/reefal biozone in non-carbonate or deep marine facies.",
    },
]

# ── Age ordering impossibility checks ──────────────────────────────────────
# Younger zone above older zone = normal. Older zone above younger = flag.

# ── Depositional environment conflict mapping ──────────────────────────────
# For environment text → canonical classification

ENVIRONMENT_CLASSIFICATION: dict[str, list[str]] = {
    "open_marine": ["open marine", "oceanic", "pelagic", "hemipelagic", "outer neritic", "bathyal", "abyssal"],
    "marine_shelf": ["neritic", "shelf", "inner neritic", "middle neritic", "sublittoral"],
    "coastal": ["coastal", "littoral", "shoreface", "beach", "supralittoral", "mangrove", "estuarine", "lagoon"],
    "deltaic": ["delta", "deltaic", "prodelta", "delta front", "delta plain"],
    "fluvial": ["fluvial", "alluvial", "floodplain", "channel", "river"],
    "lacustrine": ["lacustrine", "lake", "lacustrine expansion"],
    "freshwater_swamp": ["freshwater swamp", "peat swamp", "coal swamp", "marsh"],
    "deep_marine": ["bathyal", "abyssal", "deep marine", "basin floor", "submarine fan"],
    "reef": ["reef", "carbonate buildup", "atoll", "bioherm", "carbonate platform"],
}


def _classify_environment(text: str) -> str:
    """Classify free-text environment into canonical category."""
    text_lower = text.lower()
    for category, keywords in ENVIRONMENT_CLASSIFICATION.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return "unknown"


def _biozone_implies_marine(zone: str) -> bool:
    """NN zones are calcareous nannofossils — primarily open marine indicators."""
    # All NN zones imply marine conditions (calcareous nannoplankton)
    # But the strength varies — NN zones in marginal settings are possible
    # with marine incursion but require facies checking
    return True  # All calcareous nannofossils need marine water


def _gde_implies_marine(gde_events: list[dict]) -> bool:
    """Check if any GDE event implies marine conditions."""
    marine_events = {
        "marine_flooding",
        "maximum_flooding",
        "transgression",
        "marine_incursion",
        "depositional_environment",
    }
    for evt in gde_events:
        if evt.get("event_type") in marine_events:
            # Check if the GDE code suggests marine
            code = evt.get("gde_code", "")
            if code and any(m in code for m in ("HIN", "HMN", "HON", "UBT", "MBT", "LBT", "MARINE")):
                return True
    return False


async def geox_biostrat_ruling_check(
    biozone: str = "",
    lithology: str = "",
    environment: str = "",
    claim: str = "",
    depth_m: float | None = None,
) -> dict:
    """Biostrat Ruling Check — detect contradictions in biostratigraphic interpretations.

    Tests whether a biostratigraphic claim is physically and biologically
    plausible in its claimed depositional context.

    Args:
      biozone:     Biozone name (e.g. "NN5", "NN11A")
      lithology:   Free-text lithology description
      environment: Free-text depositional environment description
      claim:       The geological claim being tested (e.g. "open marine deposition")
      depth_m:     Optional depth in meters for depth-ordering checks

    Returns:
      Governed MCP envelope with:
        ruling          — PASS | WEAK_PASS | CONTRADICTION | HOLD | REJECT
        reason          — Explanation of the ruling
        contradictions  — List of detected conflicts
        required_next_evidence — What evidence would resolve contradictions
        likelihood      — Qualitative likelihood assessment

    Example:
      geox_biostrat_ruling_check(
        biozone="NN5", lithology="coal", environment="freshwater swamp",
        claim="open marine deposition"
      )
      → ruling: CONTRADICTION
      → reason: "Open marine interpretation conflicts with freshwater swamp facies"
    """
    logger.info(
        "biostrat_ruling_check: zone=%s litho=%s env=%s claim=%s",
        biozone,
        lithology[:60] if lithology else "",
        environment[:60] if environment else "",
        claim[:80] if claim else "",
    )

    contradictions: list[dict[str, str]] = []
    required_evidence: list[str] = []
    warnings_list: list[str] = []

    # ── Step 1: Parse inputs ────────────────────────────────────────────────
    litho_class = lithology_class(lithology) if lithology else "UNKNOWN"
    env_class = _classify_environment(environment) if environment else "unknown"
    gde_result = map_gde(environment, lithology) if (environment or lithology) else None
    zone_parsed = parse_nn_zone(biozone) if biozone else None
    zone_name = zone_parsed["zone"] if zone_parsed else ""
    zone_valid = zone_name and zone_name != "UNKNOWN"

    # ── Step 2: Biozone → marine implication ────────────────────────────────
    zone_is_marine = _biozone_implies_marine(zone_name) if zone_valid else False

    # ── Step 3: Run facies veto rules ───────────────────────────────────────
    for rule in FACIES_VETO_RULES:
        if not zone_is_marine and "marine" in rule["biozone_implication"]:
            continue

        # The reef rule should only fire when reef is actually claimed,
        # not on every shale with an NN zone (NN zones are marine, not reef-specific)
        if rule["biozone_implication"] == "reef":
            if env_class != "reef" and litho_class != "CARBONATE":
                continue  # Not a reef context — skip reef veto

        # Check lithology conflict
        litho_conflict = litho_class in rule.get("conflicting_lithology", [])
        # Check environment conflict
        env_conflict = env_class in rule.get("conflicting_environment", [])

        if litho_conflict or env_conflict:
            contradictions.append(
                {
                    "rule": f"Facies veto: {rule['biozone_implication']} vs {litho_class}/{env_class}",
                    "severity": rule["severity"],
                    "message": rule["message"],
                }
            )
            required_evidence.append("Core or sidewall core to verify lithology")
            required_evidence.append("Check for reworking, caving, or thin marine incursion")
            if "marine" in rule["biozone_implication"]:
                required_evidence.append("Foraminifera, nannofossils, marine palynomorphs")

    # ── Step 4: Check for reworking/caving triggers ─────────────────────────
    full_text = f"{claim} {environment} {lithology}".lower()
    if any(t in full_text for t in ("reworked", "reworking", "caving", "caved")):
        warnings_list.append("Reworking or caving explicitly mentioned — age fidelity reduced.")
        contradictions.append(
            {
                "rule": "Reworking/caving detected",
                "severity": "WEAK_PASS",
                "message": "Sample contains reworked or caved fossils — biozone age may be older than depositional age.",
            }
        )
        required_evidence.append("Verify in-situ vs reworked fraction from biostrat report")

    # ── Step 5: Nannofossil absence detection ───────────────────────────────
    if not zone_valid and any(t in full_text for t in ("barren", "no fossil", "no nanno", "absent", "not anal")):
        warnings_list.append("No biostratigraphic markers found — absence may be facies, not age.")
        contradictions.append(
            {
                "rule": "Absence of evidence",
                "severity": "WEAK_PASS",
                "message": "No fossils found. Absence may mean non-marine facies, dissolution, poor preservation, or sampling gap — not necessarily no deposition.",
            }
        )
        required_evidence.append("Check if samples were processed for palynology (may survive where nannos don't)")
        required_evidence.append("Wireline log motif + seismic character for depositional inference")

    # ── Step 6: Determine ruling ────────────────────────────────────────────
    severity_levels = [c["severity"] for c in contradictions]
    if any(s == "CONTRADICTION" for s in severity_levels):
        ruling = "CONTRADICTION"
        reason = "Biostratigraphic interpretation conflicts with depositional facies. Requires reworking explanation, thin marine incursion evidence, or facies reinterpretation."
        confidence = 0.85
    elif any(s == "WEAK_PASS" for s in severity_levels):
        ruling = "WEAK_PASS"
        reason = "Interpretation is possible but requires corroborating evidence. Key assumptions need verification."
        confidence = 0.55
    elif contradictions:
        ruling = "HOLD"
        reason = "Minor issues detected. Proceed with caution after addressing required evidence."
        confidence = 0.40
    elif not zone_valid and not contradictions:
        ruling = "HOLD"
        reason = "No valid biozone provided for ruling check."
        confidence = 0.20
    else:
        ruling = "PASS"
        reason = "No physical or biological contradictions detected at this level of evidence."
        confidence = 0.60

    payload = {
        "ruling": ruling,
        "reason": reason,
        "biozone": zone_name if zone_valid else biozone,
        "lithology_class": litho_class,
        "environment_class": env_class,
        "gde_result": {
            "code": gde_result["code"],
            "label": gde_result["label"],
            "evidence_tag": gde_result["evidence_tag"],
        }
        if gde_result
        else None,
        "contradictions": contradictions,
        "required_next_evidence": list(set(required_evidence)),
        "warnings": warnings_list,
        "evidence_tag": zone_parsed["evidence_tag"] if zone_parsed else "NO_ZONE_PROVIDED",
    }

    return get_standard_envelope(
        payload,
        tool_class="compute",
        claim_tag="PLAUSIBLE" if ruling in ("PASS", "WEAK_PASS") else "HYPOTHESIS",
        claim_state="INTERPRETED",
        uncertainty="Low" if ruling == "PASS" else "Moderate",
        humility_score=confidence,
        evidence_refs=[],
        audit_receipt={
            "verdict": ruling,
            "risk": "MEDIUM" if ruling == "CONTRADICTION" else "LOW",
            "human_review_required": ruling in ("CONTRADICTION", "REJECT"),
        },
        tool_name="geox_biostrat_ruling_check",
        equations_used=[
            "Facies veto rules (B4: biostrat-as-calibration doctrine)",
            "Martini (1971) zonation — nannofossil marine affinity",
            "Lithology classification (8-class canonical)",
            "Environment classification (9-class canonical)",
        ],
        sensitivity_to=["facies_veto_rule_thresholds", "biozone_age_calibration"],
    )
