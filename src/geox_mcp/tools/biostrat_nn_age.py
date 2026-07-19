"""biostrat_nn_age.py — GEOX MCP tool for NN zone age resolution.

Phase 2.5 (2026-07-03): Standalone tool per Arif sovereign spec.

Converts a biozone name (e.g. "NN5") to an age bracket with explicit
calibration metadata. KEY: does NOT pretend NN zone ages are universal
constants. The zone-to-age mapping depends on the calibration table.

Design principles (Arif spec):
  - Zone before Ma — biozone name preserved as primary key
  - Calibration explicit — every numeric age cites its table version
  - Not a radiometric age — warning mandatory on every output
  - Uncertainty acknowledged — diachroneity risk flagged

F2 TRUTH: age is a LOOKUP, not a measurement.
F7 HUMILITY: confidence capped at 0.85. Biozone age is scheme-dependent.
F9 ANTI-HANTU: unknown zones return UNKNOWN, not guessed.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging

from geox_core.enums.statuses import get_standard_envelope
from geox_mcp.tools.kernel._biostrat import nn_age, parse_nn_zone

logger = logging.getLogger("geox.canonical.biostrat_nn_age")

# ── Epoch lookup for NN zones ──────────────────────────────────────────────
NN_EPOCH_MAP: dict[str, str] = {
    "NN21": "Holocene-Pleistocene",
    "NN20": "Pleistocene",
    "NN19": "Pleistocene",
    "NN18": "Pleistocene",
    "NN17": "Pleistocene-Gelasian",
    "NN16": "Pliocene-Piacenzian",
    "NN15": "Pliocene-Zanclean",
    "NN14": "Pliocene-Zanclean",
    "NN13": "Miocene-Messinian",
    "NN12": "Miocene-Tortonian",
    "NN11": "Miocene-Tortonian",
    "NN10": "Miocene-Tortonian",
    "NN9": "Miocene-Tortonian",
    "NN8": "Miocene-Serravallian",
    "NN7": "Miocene-Serravallian",
    "NN6": "Miocene-Langhian",
    "NN5": "Miocene-Langhian",
    "NN4": "Miocene-Burdigalian",
    "NN3": "Miocene-Aquitanian",
    "NN2": "Oligocene-Chattian",
    "NN1": "Oligocene-Chattian",
}


async def geox_biostrat_nn_age(
    zone: str = "",
    scheme: str = "Martini",
    calibration: str = "default",
) -> dict:
    """NN Zone Age Resolution — convert biozone to age bracket with calibration metadata.

    Args:
      zone:        Biozone name (e.g. "NN5", "NN11A", "NN19-20").
                    Accepts: NN1-NN21, NP1-NP25, with optional subzone
                    letters (A/B/C). Multi-zone ranges like "NN19-20"
                    resolve to envelope bracket.
      scheme:      Zonation scheme. "Martini" (default) uses Martini 1971.
                    Future: "Bukry", "Okada_Bukry", "Agnini".
      calibration: Calibration table version. "default" = GPTS2020-style
                    lookup built into GEOX. Future: "GTS2012", "GTS2020",
                    "local_table", "operator_specific".

    Returns:
      Governed MCP envelope with:
        zone             — canonical zone name
        scheme           — zonation scheme
        discipline       — fossil group
        age_top_ma       — younger boundary
        age_base_ma      — older boundary
        epoch            — named epoch/series
        calibration      — calibration table version
        not_a_radiometric_age — ALWAYS true. Mandatory warning.
        warnings         — diachroneity warning, scheme limitations

    Example:
      geox_biostrat_nn_age(zone="NN5")
      → age_top_ma=13.65, age_base_ma=14.91, epoch="Miocene-Langhian"

    F2 TRUTH: Biozone age depends on calibration table and regional diachroneity.
    F7 HUMILITY: Zone age is a lookup, not a measurement.
    """
    logger.info("geox_biostrat_nn_age: zone=%s scheme=%s calibration=%s", zone, scheme, calibration)

    if not zone:
        return get_standard_envelope(
            {"zone": "", "error": "No zone provided."},
            tool_class="compute",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            uncertainty="High",
            humility_score=0.0,
            evidence_refs=[],
            audit_receipt={"verdict": "NO_INPUT", "risk": "LOW"},
            tool_name="geox_biostrat_nn_age",
            equations_used=["Martini (1971) zonation lookup"],
            sensitivity_to=["calibration_table_version"],
        )

    # Parse the zone string
    parsed = parse_nn_zone(zone)
    zone_name = parsed["zone"]
    evidence_tag = parsed["evidence_tag"]

    if zone_name == "UNKNOWN" or evidence_tag in ("NN_NOT_PARSED", "SOURCE_UNRESOLVED"):
        return get_standard_envelope(
            {
                "zone": zone,
                "canonical_zone": "UNKNOWN",
                "error": f"Could not parse zone '{zone}'. Provide e.g. 'NN5', 'NN11A'.",
                "evidence_tag": evidence_tag,
            },
            tool_class="compute",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            uncertainty="High",
            humility_score=0.0,
            evidence_refs=[],
            audit_receipt={"verdict": "PARSE_FAILED", "risk": "LOW"},
            tool_name="geox_biostrat_nn_age",
            equations_used=["Martini (1971) zonation lookup"],
            sensitivity_to=["calibration_table_version"],
        )

    # Resolve age
    age_top, age_base = nn_age(zone_name)
    if age_top <= -999:
        return get_standard_envelope(
            {
                "zone": zone_name,
                "scheme": "Martini 1971",
                "discipline": "calcareous_nannofossil",
                "error": f"Zone '{zone_name}' parsed but no age calibration available.",
            },
            tool_class="compute",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            uncertainty="High",
            humility_score=0.0,
            evidence_refs=[],
            audit_receipt={"verdict": "NO_CALIBRATION", "risk": "LOW"},
            tool_name="geox_biostrat_nn_age",
            equations_used=["Martini (1971) zonation lookup"],
            sensitivity_to=["calibration_table_version"],
        )

    # Get epoch
    epoch = NN_EPOCH_MAP.get(zone_name, _guess_epoch(zone_name))

    # Confidence
    if evidence_tag == "EVIDENCE_DIRECT":
        confidence = 0.85
    elif evidence_tag == "EVIDENCE_MULTI_ZONE":
        confidence = 0.70
    else:
        confidence = 0.60

    # Warnings
    warnings_list = [
        "Biozone age depends on calibration table and regional diachroneity.",
        "NN zones are correlation tools, not absolute chronometers.",
        "Bioevents may be diachronous across basins — age bracket is global average.",
    ]

    payload = {
        "zone": zone_name,
        "scheme": "Martini 1971",
        "discipline": "calcareous_nannofossil",
        "age_top_ma": age_top,
        "age_base_ma": age_base,
        "age_bracket_ma": [age_top, age_base],
        "epoch": epoch,
        "calibration": "GPTS2020 (GEOX built-in lookup)",
        "not_a_radiometric_age": True,
        "confidence": confidence,
        "evidence_tag": evidence_tag,
        "warnings": warnings_list,
    }

    return get_standard_envelope(
        payload,
        tool_class="compute",
        claim_tag="PLAUSIBLE",
        claim_state="INTERPRETED",
        uncertainty="Low" if confidence >= 0.80 else "Moderate",
        humility_score=confidence,
        evidence_refs=[f"NN zone {zone_name} ({epoch})"],
        audit_receipt={
            "verdict": "SEAL",
            "risk": "LOW",
            "human_review_required": False,
        },
        tool_name="geox_biostrat_nn_age",
        equations_used=[
            "Martini (1971) Standard Tertiary and Quaternary calcareous nannoplankton zonation",
            "GPTS2020 age calibration table",
        ],
        sensitivity_to=["calibration_table_version", "regional_diachroneity"],
    )


def _guess_epoch(zone_name: str) -> str:
    """Fallback epoch guesser for zones not in NN_EPOCH_MAP."""
    # Extract numeric part
    import re

    m = re.search(r"(\d+)", zone_name)
    if not m:
        return "Neogene"
    n = int(m.group(1))
    if n >= 19:
        return "Pleistocene"
    elif n >= 12:
        return "Pliocene"
    elif n >= 4:
        return "Miocene"
    else:
        return "Oligocene-Miocene"
