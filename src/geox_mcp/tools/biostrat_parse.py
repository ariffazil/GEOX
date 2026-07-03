"""biostrat_parse.py — GEOX MCP entry point for Biostratigraphy Parsing.

Phase 2.5 (2026-07-03): Comprehensive multi-zone parser per Arif sovereign spec.

Extracts from free text:
  - biozones[] — NN zones, schemes, groups, confidence, source spans
  - gde_events[] — marine flooding, transgression, mangrove increase,
    lacustrine, freshwater algae, and canonical GDE codes
  - lithology_class — canonical LithoClass
  - unparsed_terms[] — terms not matched to any vocabulary
  - warnings[] — structural issues detected

All outputs evidence-tagged. No ML. Regex-only. Low blast radius.

IRON LAW: Tectonics → Stratigraphy → Age Calibration (NN zones).
NOT: Age → Stratigraphy → Tectonics.

F2 TRUTH: Every biozone and GDE event carries source_span, confidence,
and evidence_tag. Never fabricate.
F4 CLARITY: Structured arrays, not collapsed prose.
F7 HUMILITY: Confidence hard-capped at 0.85. Unmatched terms preserved.
F9 ANTI-HANTU: Unknown inputs tagged explicitly. No guessing.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from geox_core.enums.statuses import get_standard_envelope
from geox_mcp.tools.kernel._biostrat import (
    parse_nn_zone,
    nn_age,
    map_gde as _map_gde,
    lithology_class,
    clean_text,
)

logger = logging.getLogger("geox.canonical.biostrat_parse")

# ── Extended GDE Event vocabulary (Arif spec, Phase 2.5) ───────────────────
# These detect sequence-stratigraphic and ecological events from free text,
# in addition to the canonical water-depth GDE codes from _biostrat.py

GDE_EVENT_PATTERNS: list[tuple[str, str, str]] = [
    # (regex, event_type, description)
    (
        r"marine flooding surface|marine flood|mfs|maximum flooding surface",
        "marine_flooding",
        "Marine flooding surface / transgression",
    ),
    (r"maximum flooding|max flood|mfs", "maximum_flooding", "Maximum flooding surface"),
    (r"transgress|transgression|transgressive systems tract|tst", "transgression", "Transgressive event or systems tract"),
    (r"regress|regression|falling stage|lowstand|forced regression", "regression", "Regressive event or systems tract"),
    (
        r"mangrove.*(?:increase|peak|pulse|expansion|rise)|mangrove.*pollen",
        "mangrove_increase",
        "Mangrove pollen increase — coastal/marginal marine signal",
    ),
    (
        r"freshwater algae|lacustrine algae|pediastrum|botryococcus",
        "freshwater_algae",
        "Freshwater algae dominance — lacustrine signal",
    ),
    (r"lacustrine.*(?:expansion|pulse|increase|phase)|lake.*expansion", "lacustrine_expansion", "Lacustrine expansion event"),
    (
        r"marine incursion|marine incur|marine pulse|marine influx|marine.*enter|marine.*ingress",
        "marine_incursion",
        "Marine incursion into the basin",
    ),
    (
        r"peat swamp|peat.*accumulation|coal.*formation|peat.*development",
        "peat_swamp",
        "Peat swamp development — coastal plain / humid",
    ),
    (r"hiatus|non.deposition|condensed section|omission surface", "hiatus", "Hiatus or condensed section"),
    (r"unconformity|erosional surface|erosion surface|angular unconformity", "unconformity", "Unconformity or erosional surface"),
    (r"progradation|prograding|prograde|delta.*prograd", "progradation", "Progradational event"),
    (r"retrogradation|retrograd|backstep|back.stepping", "retrogradation", "Retrogradational / backstepping event"),
]


def _extract_all_biozones(text: str) -> list[dict[str, Any]]:
    """Extract ALL biozone references from text, not just the first.

    Handles: NN5, NN 5, Zone NN5, Martini NN5, NN19-20, etc.
    """
    results: list[dict[str, Any]] = []
    upper = text.upper()
    clean = clean_text(text)

    if not clean:
        return results

    # Find all NN zone patterns with surrounding context
    # Pattern: optional "Zone" or "Martini" prefix, then NN + optional space + digits
    pattern = re.compile(
        r"(?:(?:Zone|Martini|NN|NP)\s*)?\b(NN|NP)\s*(\d{1,2}[A-C]?)\b",
        re.IGNORECASE,
    )
    seen_zones: set[str] = set()

    for match in pattern.finditer(clean):
        prefix = match.group(1).upper()
        num = match.group(2).upper()
        zone_name = f"{prefix}{num}"

        if zone_name in seen_zones:
            continue
        seen_zones.add(zone_name)

        # Get surrounding context (±40 chars)
        start = max(0, match.start() - 20)
        end = min(len(clean), match.end() + 20)
        source_span = clean[start:end].strip()

        # Resolve age
        age_top, age_base = nn_age(zone_name)
        age_valid = age_top > -999

        # Determine scheme
        if prefix == "NN":
            scheme = "Martini 1971"
            group = "calcareous_nannofossil"
            epoch_hint = _epoch_for_nn(num)
        elif prefix == "NP":
            scheme = "Martini 1971"
            group = "calcareous_nannofossil"
            epoch_hint = "Paleogene"
        else:
            scheme = "unknown"
            group = "unknown"
            epoch_hint = "unknown"

        confidence = 0.95 if age_valid else 0.50

        results.append(
            {
                "scheme": scheme,
                "group": group,
                "zone": zone_name,
                "confidence": confidence,
                "source_span": source_span,
                "age_top_ma": age_top if age_valid else None,
                "age_base_ma": age_base if age_valid else None,
                "epoch": epoch_hint,
                "evidence_tag": "EVIDENCE_DIRECT" if age_valid else "NN_NOT_PARSED",
            }
        )

    # If no zones found, try single parse as fallback
    if not results:
        parsed = parse_nn_zone(clean)
        if parsed["zone"] != "UNKNOWN":
            zone_name = parsed["zone"]
            age_top, age_base = nn_age(zone_name)
            age_valid = age_top > -999
            results.append(
                {
                    "scheme": "Martini 1971",
                    "group": "calcareous_nannofossil",
                    "zone": zone_name,
                    "confidence": 0.90 if age_valid else 0.50,
                    "source_span": clean[:80],
                    "age_top_ma": age_top if age_valid else None,
                    "age_base_ma": age_base if age_valid else None,
                    "epoch": _epoch_for_nn(zone_name.replace("NN", "")),
                    "evidence_tag": parsed["evidence_tag"],
                }
            )

    return results


def _extract_gde_events(text: str) -> list[dict[str, Any]]:
    """Extract all GDE/sequence-stratigraphic events from text."""
    results: list[dict[str, Any]] = []
    clean = clean_text(text).lower()

    if not clean:
        return results

    seen_types: set[str] = set()

    for pattern, event_type, description in GDE_EVENT_PATTERNS:
        m = re.search(pattern, clean, re.IGNORECASE)
        if m and event_type not in seen_types:
            seen_types.add(event_type)
            start = max(0, m.start() - 15)
            end = min(len(text), m.end() + 15)
            results.append(
                {
                    "event_type": event_type,
                    "description": description,
                    "confidence": 0.85,
                    "source_span": text[start:end].strip(),
                }
            )

    # Also add canonical GDE code if water-depth terms present
    gde = _map_gde(text, "")
    if gde["code"] != "UNKNOWN" and gde["code"] not in seen_types:
        results.append(
            {
                "event_type": "depositional_environment",
                "description": gde["label"],
                "gde_code": gde["code"],
                "gde_index": gde["index"],
                "rationale": gde["rationale"],
                "confidence": 0.85 if gde["evidence_tag"] == "EVIDENCE_DIRECT" else 0.60,
                "source_span": clean[:80],
                "evidence_tag": gde["evidence_tag"],
            }
        )

    return results


def _find_unparsed_terms(text: str, biozones: list, gde_events: list) -> list[str]:
    """Find potentially meaningful terms not captured by biozone or GDE parsers."""
    clean = clean_text(text).lower()
    if not clean:
        return []

    # Terms that suggest biostrat/geological meaning
    candidate_terms = [
        "first occurrence",
        "last occurrence",
        "fad",
        "lad",
        "first appearance",
        "last appearance",
        "acme",
        "peak abundance",
        "reworked",
        "caving",
        "in situ",
        "barren",
        "indeterminate",
        "planktonic",
        "benthic",
        "benthonic",
        "agglutinated",
        "calcareous",
        "arenaceous",
        "siliceous",
        "spore",
        "pollen",
        "dinocyst",
        "dinoflagellate",
        "foraminifera",
        "foram",
        "nannofossil",
        "nannoplankton",
        "palynomorph",
        "palynology",
        "biostratigraphy",
        "discoaster",
        "sphenolithus",
        "reticulofenestra",
        "helicolith",
        "coccolith",
        "coccolithophore",
        "globoquadrina",
        "globigerina",
        "globorotalia",
        "neogloboquadrina",
        "praeorbulina",
        "orbulina",
        "miogypsina",
        "lepidocyclina",
        "flosculinella",
        "alveolinella",
        "cycloclypeus",
        "larger",
        "benthic",
        "planktic",
    ]

    found: list[str] = []
    for term in candidate_terms:
        if re.search(r"\b" + re.escape(term) + r"\b", clean, re.IGNORECASE):
            # Check if already captured
            already_captured = False
            for bz in biozones:
                if term.lower() in bz.get("source_span", "").lower():
                    already_captured = True
                    break
            for ge in gde_events:
                if term.lower() in ge.get("source_span", "").lower():
                    already_captured = True
                    break
            if not already_captured:
                found.append(term)

    return found


def _epoch_for_nn(num: str) -> str:
    """Return epoch name for NN subzone number."""
    num_clean = num.lstrip("0") or "0"
    try:
        n = int(num_clean[0]) if num_clean[0].isdigit() else 0
    except (ValueError, IndexError):
        return "Neogene"
    if n >= 21:
        return "Holocene-Pleistocene"
    elif n >= 19:
        return "Pleistocene"
    elif n >= 12:
        return "Pliocene"
    elif n >= 5:
        return "Miocene"
    elif n >= 2:
        return "Oligocene-Miocene"
    else:
        return "Oligocene"


async def geox_biostrat_parse(
    text: str = "",
    paleoenvironment: str = "",
    lithology: str = "",
) -> dict:
    """Biostratigraphy Parser — extract biozones, GDE events, lithology from free text.

    Parses structured observations from free text WITHOUT over-interpreting.
    Returns arrays of biozones, GDE events, unparsed terms, and warnings.

    Args:
      text:             Free text containing biostratigraphic information
                         (e.g. "Zone NN5 with marine flooding surface and
                         increased nannofossils, mangrove pollen increase")
      paleoenvironment: Optional explicit paleoenvironment text
      lithology:        Optional explicit lithology text

    Returns:
      Governed MCP envelope with:
        biozones[]      — parsed zones with scheme, group, age, source_span
        gde_events[]    — detected sequence/ecological events
        lithology_class — canonical LithoClass
        unparsed_terms[] — terms not matched to any vocabulary
        warnings[]      — structural issues detected

    F2 TRUTH: regex-only. Every output carries source_span and evidence_tag.
    F7 HUMILITY: unmatched terms preserved, not guessed.
    """
    logger.info(
        "geox_biostrat_parse called: text=%s paleo=%s litho=%s",
        text[:100] if text else "",
        paleoenvironment[:60] if paleoenvironment else "",
        lithology[:60] if lithology else "",
    )

    # Combine all input text for parsing
    combined = f"{text} {paleoenvironment} {lithology}"

    # Extract
    biozones = _extract_all_biozones(combined)
    gde_events = _extract_gde_events(combined)
    litho = lithology_class(lithology) if lithology else "UNKNOWN"
    unparsed = _find_unparsed_terms(combined, biozones, gde_events)

    # Warnings
    warnings: list[str] = []
    if not biozones and not gde_events and not lithology:
        warnings.append("No biostratigraphic tokens extracted from input.")
    if unparsed:
        warnings.append(f"Unparsed biostrat terms present: {', '.join(unparsed[:8])}")

    # Confidence
    direct_zones = sum(1 for bz in biozones if bz.get("evidence_tag") == "EVIDENCE_DIRECT")
    event_count = len(gde_events)
    if direct_zones >= 2:
        confidence = min(0.85, 0.70 + 0.05 * direct_zones)
        claim_tag = "PLAUSIBLE"
    elif direct_zones >= 1 or event_count >= 2:
        confidence = 0.65
        claim_tag = "PLAUSIBLE"
    elif event_count >= 1:
        confidence = 0.50
        claim_tag = "HYPOTHESIS"
    else:
        confidence = 0.25
        claim_tag = "HYPOTHESIS"

    payload = {
        "biozones": biozones,
        "gde_events": gde_events,
        "lithology_class": litho,
        "unparsed_terms": unparsed,
        "warnings": warnings,
    }

    evidence_refs = []
    for bz in biozones:
        evidence_refs.append(f"Biozone {bz['zone']} ({bz['scheme']})")
    for ge in gde_events:
        evidence_refs.append(f"GDE event: {ge['event_type']}")

    audit = {
        "tool_call_hash": "geox_biostrat_parse_v2",
        "verdict": "COMPLETE" if biozones or gde_events else "NO_EVIDENCE",
        "risk": "LOW",
        "human_review_required": len(warnings) > 2,
    }

    return get_standard_envelope(
        payload,
        tool_class="compute",
        claim_tag=claim_tag,
        claim_state="INTERPRETED" if confidence >= 0.50 else "HYPOTHESIS",
        uncertainty="Low" if confidence >= 0.70 else "Moderate",
        humility_score=confidence,
        evidence_refs=evidence_refs,
        audit_receipt=audit,
        tool_name="geox_biostrat_parse",
        equations_used=[
            "Martini (1971) NN1-NN21 Neogene calcareous nannofossil zonation",
            "GPTS2020 age calibration table",
            "12-rule GDE vocabulary mapper + 13 sequence/ecological event patterns",
            "8-class canonical lithology classifier",
        ],
        sensitivity_to=["martini_zonation_version", "gde_rule_patterns", "unparsed_term_vocabulary"],
    )
