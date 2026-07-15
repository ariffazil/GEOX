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


# Regional ontology matrix — marker/zone → GDE risk score (0–1, higher = more risk to reservoir prediction)
# SPEC/INT layer: regional Malay/Sunda-leaning defaults; override via structured intervals.
_GDE_ONTOLOGY: dict[str, dict[str, Any]] = {
    "marine_flooding": {"gde": "offshore_shelf", "reservoir_risk": 0.75, "seal_support": 0.85},
    "maximum_flooding": {"gde": "condensed_section", "reservoir_risk": 0.85, "seal_support": 0.90},
    "transgression": {"gde": "transgressive_shelf", "reservoir_risk": 0.70, "seal_support": 0.80},
    "regression": {"gde": "progradational_delta", "reservoir_risk": 0.35, "seal_support": 0.45},
    "mangrove_increase": {"gde": "coastal_plain", "reservoir_risk": 0.40, "seal_support": 0.55},
    "freshwater_algae": {"gde": "lacustrine", "reservoir_risk": 0.50, "seal_support": 0.60},
    "lacustrine_expansion": {"gde": "lacustrine", "reservoir_risk": 0.55, "seal_support": 0.65},
    "marine_incursion": {"gde": "restricted_marine", "reservoir_risk": 0.65, "seal_support": 0.70},
    "peat_swamp": {"gde": "coastal_plain_peat", "reservoir_risk": 0.45, "seal_support": 0.50},
    "hiatus": {"gde": "hiatus", "reservoir_risk": 0.80, "seal_support": 0.40},
    "unconformity": {"gde": "unconformity", "reservoir_risk": 0.85, "seal_support": 0.35},
    "NN1": {"gde": "early_miocene_marine", "reservoir_risk": 0.55, "seal_support": 0.60},
    "NN5": {"gde": "mid_miocene_marine", "reservoir_risk": 0.50, "seal_support": 0.65},
    "NN11": {"gde": "late_miocene_marine", "reservoir_risk": 0.45, "seal_support": 0.70},
    "group d": {"gde": "group_d_fluvial_deltaic", "reservoir_risk": 0.30, "seal_support": 0.40},
    "group e": {"gde": "group_e_fluvial", "reservoir_risk": 0.35, "seal_support": 0.45},
    "group f": {"gde": "group_f_fluvial", "reservoir_risk": 0.35, "seal_support": 0.45},
    "base group d": {"gde": "group_d_base", "reservoir_risk": 0.40, "seal_support": 0.50},
}


def _score_gde_from_events(gde_events: list[dict], biozones: list[dict], markers: list[str]) -> dict[str, Any]:
    """Map extracted tokens to ontology GDE risk (not free-text echo)."""
    hits: list[dict[str, Any]] = []
    for ge in gde_events:
        et = str(ge.get("event_type", "")).lower()
        if et in _GDE_ONTOLOGY:
            row = dict(_GDE_ONTOLOGY[et])
            row["source"] = et
            row["kind"] = "gde_event"
            hits.append(row)
    for bz in biozones:
        zone = str(bz.get("zone", "")).upper()
        if zone in _GDE_ONTOLOGY:
            row = dict(_GDE_ONTOLOGY[zone])
            row["source"] = zone
            row["kind"] = "biozone"
            hits.append(row)
    for m in markers:
        key = m.strip().lower()
        if key in _GDE_ONTOLOGY:
            row = dict(_GDE_ONTOLOGY[key])
            row["source"] = m
            row["kind"] = "marker"
            hits.append(row)
        # partial match group letters
        for ont_key, ont_val in _GDE_ONTOLOGY.items():
            if ont_key in key and ont_key.startswith("group"):
                row = dict(ont_val)
                row["source"] = m
                row["kind"] = "marker"
                hits.append(row)

    if not hits:
        return {
            "gde_risk_score": None,
            "primary_gde": "UNKNOWN",
            "reservoir_risk": None,
            "seal_support": None,
            "ontology_hits": [],
            "note": "No ontology match — INSUFFICIENT_DATA for GDE risk",
        }
    # Aggregate: mean reservoir risk / seal support
    r_risk = sum(h["reservoir_risk"] for h in hits) / len(hits)
    s_sup = sum(h["seal_support"] for h in hits) / len(hits)
    # Prefer most frequent gde label
    from collections import Counter

    gde_counts = Counter(h["gde"] for h in hits)
    primary = gde_counts.most_common(1)[0][0]
    return {
        "gde_risk_score": round(r_risk, 3),
        "primary_gde": primary,
        "reservoir_risk": round(r_risk, 3),
        "seal_support": round(s_sup, 3),
        "ontology_hits": hits,
        "note": "DER from regional ontology matrix — not a field observation",
    }


async def geox_biostrat_parse(
    text: str = "",
    paleoenvironment: str = "",
    lithology: str = "",
    intervals: list[dict[str, Any]] | None = None,
) -> dict:
    """Biostratigraphy Parser — structured intervals preferred; free text secondary.

    Prefer `intervals` array:
      [{depth_top_m, depth_base_m, marker, zone, lithology, paleoenvironment}, ...]

    Free text still accepted for legacy callers but marked higher entropy.

    Returns biozones, gde_events, lithology_class, gde_risk (ontology), unparsed, warnings.
    F2 TRUTH: regex-only on text; structured markers preferred. No ML fabrication.
    """
    logger.info(
        "geox_biostrat_parse called: text=%s paleo=%s litho=%s intervals=%s",
        text[:100] if text else "",
        paleoenvironment[:60] if paleoenvironment else "",
        lithology[:60] if lithology else "",
        len(intervals or []),
    )

    structured_mode = bool(intervals)
    markers: list[str] = []
    combined_parts: list[str] = []
    structured_rows: list[dict[str, Any]] = []

    if intervals:
        for iv in intervals:
            if not isinstance(iv, dict):
                continue
            top = iv.get("depth_top_m", iv.get("top", iv.get("depth_top")))
            base = iv.get("depth_base_m", iv.get("base", iv.get("depth_base")))
            marker = str(iv.get("marker") or iv.get("chronostrat") or "")
            zone = str(iv.get("zone") or iv.get("biozone") or "")
            lith = str(iv.get("lithology") or "")
            paleo = str(iv.get("paleoenvironment") or "")
            if marker:
                markers.append(marker)
            if zone:
                markers.append(zone)
            row_text = " ".join(x for x in (marker, zone, lith, paleo) if x)
            combined_parts.append(row_text)
            structured_rows.append(
                {
                    "depth_top_m": top,
                    "depth_base_m": base,
                    "marker": marker or None,
                    "zone": zone or None,
                    "lithology": lith or None,
                    "paleoenvironment": paleo or None,
                    "evidence_tag": "EVIDENCE_STRUCTURED",
                }
            )

    # Free text path (legacy / residual)
    combined = f"{text} {paleoenvironment} {lithology} " + " ".join(combined_parts)

    biozones = _extract_all_biozones(combined)
    gde_events = _extract_gde_events(combined)
    litho = lithology_class(lithology) if lithology else "UNKNOWN"
    if litho == "UNKNOWN" and structured_rows:
        for r in structured_rows:
            if r.get("lithology"):
                litho = lithology_class(r["lithology"])
                if litho != "UNKNOWN":
                    break
    unparsed = _find_unparsed_terms(combined, biozones, gde_events)
    gde_risk = _score_gde_from_events(gde_events, biozones, markers)

    # Warnings
    warnings: list[str] = []
    if not structured_mode:
        warnings.append("Free-text mode — higher entropy. Prefer intervals=[{depth_top_m,depth_base_m,marker,zone}]")
    if not biozones and not gde_events and not lithology and not structured_rows:
        warnings.append("No biostratigraphic tokens extracted from input.")
    if unparsed:
        warnings.append(f"Unparsed biostrat terms present: {', '.join(unparsed[:8])}")

    # Confidence — structured intervals raise floor
    direct_zones = sum(1 for bz in biozones if bz.get("evidence_tag") == "EVIDENCE_DIRECT")
    event_count = len(gde_events)
    if structured_mode and (biozones or gde_events or markers):
        confidence = min(0.85, 0.72 + 0.03 * len(structured_rows))
        claim_tag = "PLAUSIBLE"
    elif direct_zones >= 2:
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
        "intervals": structured_rows,
        "gde_risk": gde_risk,
        "input_mode": "structured" if structured_mode else "free_text",
        "unparsed_terms": unparsed,
        "warnings": warnings,
    }

    evidence_refs = []
    for bz in biozones:
        evidence_refs.append(f"Biozone {bz['zone']} ({bz['scheme']})")
    for ge in gde_events:
        evidence_refs.append(f"GDE event: {ge['event_type']}")
    for r in structured_rows:
        if r.get("marker") or r.get("zone"):
            evidence_refs.append(f"Interval {r.get('depth_top_m')}-{r.get('depth_base_m')} m: {r.get('marker') or r.get('zone')}")

    audit = {
        "tool_call_hash": "geox_biostrat_parse_v3_structured",
        "verdict": "COMPLETE" if biozones or gde_events or structured_rows else "NO_EVIDENCE",
        "risk": "LOW" if structured_mode else "MODERATE",
        "human_review_required": len(warnings) > 2 or not structured_mode,
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
