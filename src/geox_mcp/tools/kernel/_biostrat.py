"""
kernel/_biostrat.py — Biostratigraphy parsing, NN zone lookup, GDE mapping.
ToAC v1: evidence-tagged abstraction from source text to structured codes.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import re
from typing import Any

# ── NN Zone Age Lookup (GPTS2020-style) ──────────────────────────────────────
NN_AGES: dict[str, tuple[float, float]] = {
    "NN21": (0.00, 0.46),
    "NN20": (0.46, 1.04),
    "NN19": (1.04, 1.73),
    "NN18": (1.73, 2.31),
    "NN17": (2.31, 3.54),
    "NN16": (3.54, 4.13),
    "NN15": (4.13, 4.37),
    "NN14": (4.37, 5.04),
    "NN13": (5.04, 5.59),
    "NN12": (5.59, 6.91),
    "NN11C": (6.91, 7.42),
    "NN11B": (7.42, 7.67),
    "NN11A": (7.67, 8.59),
    "NN11": (6.91, 8.59),
    "NN10B": (8.59, 9.53),
    "NN10A": (9.53, 10.41),
    "NN10": (8.59, 10.41),
    "NN9C": (10.41, 10.80),
    "NN9B": (10.80, 11.21),
    "NN9A": (11.21, 11.79),
    "NN9": (10.41, 11.79),
    "NN8": (11.79, 12.12),
    "NN7": (12.12, 13.12),
    "NN6": (13.12, 13.65),
    "NN5": (13.65, 14.91),
    "NN4": (14.91, 17.95),
    "NN3": (17.95, 19.01),
    "NN2": (19.01, 20.44),
    "NN1": (20.44, 23.03),
}

# ── GDE (Geological Depositional Environment) Rules ──────────────────────────
GDE_RULES: list[tuple[str, str, str, int, str]] = [
    (r"alluvial|fluvial|floodplain", "2026_COL", "Continental / alluvial plain", 0, "Continental fluvial to floodplain system"),
    (r"lower coastal|coastal plain|coastal", "2026_LCP", "Lower coastal plain", 1, "Coastal plain to paralic transition"),
    (r"supralittoral|littoral|beach|shoreface", "2026_LIT", "Littoral / shoreface", 2, "Littoral to shoreface belt"),
    (
        r"intertidal|tidal|estuar|lagoon|mangrove",
        "2026_TIDAL",
        "Tidal flat / estuarine",
        3,
        "Tidal-flat, estuarine, or restricted marginal marine",
    ),
    (r"inner neritic|inner sublittoral", "2026_HIN", "Inner neritic", 4, "Shallow marine inner shelf"),
    (r"middle neritic|middle sublittoral", "2026_HMN", "Middle neritic", 5, "Open marine middle shelf"),
    (r"outer neritic|outer sublittoral", "2026_HON", "Outer neritic", 6, "Open marine outer shelf"),
    (r"upper.*bathyal", "2026_UBT", "Upper bathyal", 7, "Upper slope / deep marine"),
    (r"middle.*bathyal", "2026_MBT", "Middle bathyal", 8, "Middle slope / deep marine"),
    (r"lower.*bathyal", "2026_LBT", "Lower bathyal", 9, "Lower slope to basin-floor deep marine"),
    (r"bathyal", "2026_UBT-MBT", "Bathyal undifferentiated", 8, "Deep marine bathyal setting"),
    (r"marine", "2026_MARINE", "Marine undifferentiated", 5, "Marine, depth not tightly constrained"),
]


def clean_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and str(value) == "nan"):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_nn_zone(value: str) -> dict[str, str]:
    """Parse nannofossil zone text into structured NN zone + evidence tag.

    Returns:
        {"zone": "NN19", "source_text": "NN19-20", "evidence_tag": "EVIDENCE_DIRECT"}
        or {"zone": "UNKNOWN", "source_text": "...", "evidence_tag": "NN_NOT_PARSED"}
    """
    text = clean_text(value)
    upper = text.upper()
    if not text:
        return {"zone": "UNKNOWN", "source_text": "", "evidence_tag": "NO_GDE_SOURCE"}
    if re.search(r"INDET|BARREN|NOT ANALY|ABSENT|UNKNOWN", upper):
        return {"zone": "UNKNOWN", "source_text": text, "evidence_tag": "SOURCE_UNRESOLVED"}
    matches = re.findall(r"\bNN\s*([0-9]{1,2}[A-C]?)\b", upper)
    if not matches:
        return {"zone": "UNKNOWN", "source_text": text, "evidence_tag": "NN_NOT_PARSED"}
    zones = [f"NN{m}" for m in matches]
    if len(zones) == 1:
        return {"zone": zones[0], "source_text": text, "evidence_tag": "EVIDENCE_DIRECT"}
    return {"zone": "-".join(zones), "source_text": text, "evidence_tag": "EVIDENCE_MULTI_ZONE"}


def nn_age(zone: str) -> tuple[float, float]:
    """Return (age_top_Ma, age_base_Ma) for a parsed NN zone string."""
    if not zone or zone == "UNKNOWN":
        return (-999.25, -999.25)
    parts = zone.split("-")
    ages = [NN_AGES[p] for p in parts if p in NN_AGES]
    if not ages:
        return (-999.25, -999.25)
    return (min(a[0] for a in ages), max(a[1] for a in ages))


def map_gde(paleoenvironment: str, lithology: str = "") -> dict[str, Any]:
    """Map free-text paleoenvironment + lithology to canonical GDE code.

    Returns:
        {"code": "2026_HIN", "label": "Inner neritic", "index": 4,
         "rationale": "...", "evidence_tag": "EVIDENCE_DIRECT" | "INTERPRET_FROM_LITHOLOGY" | ...}
    """
    text = f"{clean_text(paleoenvironment)} {clean_text(lithology)}".lower()
    if not text.strip():
        return {
            "code": "UNKNOWN",
            "label": "UNKNOWN",
            "index": -1,
            "rationale": "No paleoenvironment/lithology source",
            "evidence_tag": "NO_GDE_SOURCE",
        }
    for pattern, code, label, index, rationale in GDE_RULES:
        if re.search(pattern, text, flags=re.I):
            tag = "EVIDENCE_DIRECT" if clean_text(paleoenvironment) else "INTERPRET_FROM_LITHOLOGY"
            return {"code": code, "label": label, "index": index, "rationale": rationale, "evidence_tag": tag}
    if re.search(r"sand|sandstone|silt|clay|mud|shale", text, flags=re.I):
        return {
            "code": "2026_CLASTIC_UNDIFF",
            "label": "Clastic undifferentiated",
            "index": 4,
            "rationale": "Lithology present but no water-depth term",
            "evidence_tag": "INTERPRET_FROM_LITHOLOGY",
        }
    return {
        "code": "UNKNOWN",
        "label": "UNKNOWN",
        "index": -1,
        "rationale": "No mapped GDE vocabulary term",
        "evidence_tag": "GDE_NOT_MAPPED",
    }


def lithology_class(lithology: str) -> str:
    """Classify lithology text into canonical LithoClass."""
    text = clean_text(lithology).lower()
    if not text:
        return "UNKNOWN"
    if re.search(r"limestone|carbonate|dolomite|chalk", text):
        return "CARBONATE"
    if re.search(r"interbedded|alternating|sandy and shaly|sand.*shale|shale.*sand|heterolithic", text):
        return "HETEROLITHIC"
    if re.search(r"sandstone|sand\b|sandy", text) and not re.search(r"shale|clay|mud", text):
        return "SAND_PRONE"
    if re.search(r"silt|silty", text):
        return "SILT_PRONE"
    if re.search(r"shale|clay|mud|argill", text):
        return "SHALE_PRONE"
    if re.search(r"coal|carbonaceous", text):
        return "COAL_CARBONACEOUS"
    return "MIXED_OR_UNSPECIFIED"
