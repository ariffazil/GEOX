"""
kernel/_biostrat.py — Biostratigraphy parsing, zone lookup, GDE mapping.
ToAC v1: evidence-tagged abstraction from source text to structured codes.

═══════════════════════════════════════════════════════════════════════════════
SOVEREIGN LEGACY NOTICE — 2026-07-21 (T2.6-S2 corpus + A1 canonicalisation)
═══════════════════════════════════════════════════════════════════════════════
This module carries age dictionaries (NN_AGES, NP_AGES, CC_AGES, UC_AGES) that
DIVERGE from the canonical registry in geox_mcp/tools/biostrat/zones.py by up
to 11.1 Myr (CC1, see BIOSTRAT-T2_6-S1-OBSERVE-RECEIPT divergence table).

For new GEOX biostrat code: use geox_mcp.tools.biostrat.zones.zone_to_biozone()
or SCHEME_REGISTRY (canonical per ARIF A1 approval, 2026-07-21).

This module is retained ONLY for:
  - validate_zone_domain() — cross-era mismatch guard (no age lookup).
  - parse_nn_zone() — legacy text parsing helper.
  - lithology_class() / map_gde() — taxonomy-of-lithology + GDE mapping
    (independent of age registries).

nn_age() / _ALL_ZONES — DO NOT IMPORT FOR AGE LOOKUP. Use zones.py.

═══════════════════════════════════════════════════════════════════════════════

Supports: NN (Neogene nannofossil), NP (Paleogene nannofossil),
          CC (Cretaceous nannofossil, Sissingh 1977),
          UC (Upper Cretaceous nannofossil, Burnett 1998).

FIX 2026-07-06: Added CC/UC/NP zones + domain validator.
  NN = Cenozoic/Neogene-Quaternary only (0–23 Ma)
  NP = Paleogene only (23–66 Ma)
  CC = Cretaceous only (66–145 Ma)
  UC = Upper Cretaceous only (66–100 Ma)
  Cross-era zone misuse is BLOCKED by validate_zone_domain().

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import re
from typing import Any

# ── Era Boundaries (Ma, ICS v2024/12) ────────────────────────────────────────
_MESOZOIC_START = 251.9  # Permian-Triassic boundary
_CRETACEOUS_START = 145.0  # Jurassic-Cretaceous boundary
_CRETACEOUS_END = 66.0  # Cretaceous-Paleogene (K-Pg) boundary
_CENOZOIC_START = 66.0  # K-Pg boundary
_PALEOGENE_END = 23.0  # Paleogene-Neogene boundary
_NEogene_END = 2.6  # Neogene-Quaternary boundary

# ── NN Zone Age Lookup — Neogene Nannofossil (Martini 1971, 0–23 Ma) ────────
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

# ── NP Zone Age Lookup — Paleogene Nannofossil (Martini 1971, 23–66 Ma) ────
NP_AGES: dict[str, tuple[float, float]] = {
    "NP25": (23.03, 27.99),
    "NP24": (27.99, 33.89),
    "NP23": (33.89, 37.71),
    "NP22": (37.71, 39.58),
    "NP21": (39.58, 41.03),
    "NP20": (41.03, 42.57),
    "NP19": (42.57, 45.72),
    "NP18": (45.72, 48.61),
    "NP17": (48.61, 49.11),
    "NP16": (49.11, 52.77),
    "NP15": (52.77, 53.70),
    "NP14": (53.70, 54.63),
    "NP13": (54.63, 55.56),
    "NP12": (55.56, 57.55),
    "NP11": (57.55, 59.24),
    "NP10": (59.24, 61.64),
    "NP9": (61.64, 62.53),
    "NP8": (62.53, 63.25),
    "NP7": (63.25, 63.80),
    "NP6": (63.80, 64.68),
    "NP5": (64.68, 65.19),
    "NP4": (65.19, 65.56),
    "NP3": (65.56, 65.84),
    "NP2": (65.84, 66.00),
    "NP1": (66.00, 66.05),
}

# ── CC Zone Age Lookup — Cretaceous Nannofossil (Sissingh 1977, 66–145 Ma) ──
CC_AGES: dict[str, tuple[float, float]] = {
    "CC26": (66.00, 67.60),  # late Maastrichtian
    "CC25": (67.60, 69.20),  # early Maastrichtian
    "CC24": (69.20, 71.10),  # late Campanian
    "CC23": (71.10, 73.20),  # mid Campanian
    "CC22": (73.20, 76.20),  # early Campanian
    "CC21": (76.20, 80.60),  # late Santonian
    "CC20": (80.60, 83.60),  # early Santonian
    "CC19": (83.60, 85.80),  # late Coniacian
    "CC18": (85.80, 87.50),  # early Coniacian
    "CC17": (87.50, 89.00),  # late Turonian
    "CC16": (89.00, 91.00),  # mid Turonian
    "CC15": (91.00, 93.00),  # early Turonian
    "CC14": (93.00, 93.90),  # Cenomanian-Turonian boundary (OAE-2)
    "CC13": (93.90, 96.00),  # late Cenomanian
    "CC12": (96.00, 97.50),  # mid Cenomanian
    "CC11": (97.50, 99.60),  # early Cenomanian
    "CC10": (99.60, 100.50),  # late Albian
    "CC9": (100.50, 105.30),  # mid Albian
    "CC8": (105.30, 109.00),  # early Albian
    "CC7": (109.00, 112.20),  # late Aptian
    "CC6": (112.20, 118.00),  # mid Aptian
    "CC5": (118.00, 121.60),  # early Aptian
    "CC4": (121.60, 126.30),  # late Barremian
    "CC3": (126.30, 130.00),  # Hauterivian-Barremian
    "CC2": (130.00, 136.40),  # Valanginian
    "CC1": (136.40, 145.00),  # Berriasian-Valanginian
}

# ── UC Zone Age Lookup — Upper Cretaceous Nannofossil (Burnett 1998, 66–100 Ma)
UC_AGES: dict[str, tuple[float, float]] = {
    "UC20": (66.00, 67.60),  # late Maastrichtian
    "UC19": (67.60, 69.20),  # early Maastrichtian
    "UC18": (69.20, 71.10),  # late Campanian
    "UC17": (71.10, 73.20),  # mid Campanian
    "UC16": (73.20, 76.20),  # early Campanian
    "UC15": (76.20, 80.60),  # late Santonian
    "UC14": (80.60, 83.60),  # early Santonian
    "UC13": (83.60, 85.80),  # late Coniacian
    "UC12": (85.80, 87.50),  # early Coniacian
    "UC11": (87.50, 89.00),  # late Turonian
    "UC10": (89.00, 91.00),  # mid Turonian
    "UC9": (91.00, 93.00),  # early Turonian
    "UC8": (93.00, 93.90),  # Cenomanian-Turonian boundary (OAE-2)
    "UC7": (93.90, 96.00),  # late Cenomanian
    "UC6": (96.00, 97.50),  # mid Cenomanian
    "UC5": (97.50, 99.60),  # early Cenomanian
}

# ── Unified Zone Registry ────────────────────────────────────────────────────
# Maps zone prefix → (age_dict, scheme_name, period_domain, era)
_ZONE_SCHEMES: dict[str, tuple[dict, str, str, str]] = {
    "NN": (NN_AGES, "Martini_1971_NN", "Neogene-Quaternary", "Cenozoic"),
    "NP": (NP_AGES, "Martini_1971_NP", "Paleogene", "Cenozoic"),
    "CC": (CC_AGES, "Sissingh_1977_CC", "Cretaceous", "Mesozoic"),
    "UC": (UC_AGES, "Burnett_1998_UC", "Upper Cretaceous", "Mesozoic"),
}

# All zones in one lookup (for cross-scheme age resolution)
_ALL_ZONES: dict[str, tuple[float, float]] = {**NN_AGES, **NP_AGES, **CC_AGES, **UC_AGES}


def validate_zone_domain(zone: str, claimed_stage_or_age: str | float | None = None) -> dict[str, Any]:
    """Validate that a biozone's scheme is appropriate for the claimed age/stage.

    This is the core fix for the NN21-on-Cretaceous bug:
    NN zones are Neogene-Quaternary (0–23 Ma) only.
    Using NN21 to date a Campanian (72–84 Ma) sample is a 72-million-year error.

    Parameters
    ----------
    zone : str
        Zone code, e.g. "NN21", "CC23", "UC18", "NP15"
    claimed_stage_or_age : str or float, optional
        If str: stage name (e.g. "Campanian", "Cretaceous")
        If float: age in Ma

    Returns
    -------
    dict with keys:
        zone, scheme, period_domain, era, zone_age_top, zone_age_base,
        domain_valid: bool, verdict: "VALID" | "CROSS_ERA_MISMATCH" | "UNKNOWN_SCHEME",
        warning: str or None
    """
    zone_upper = zone.strip().upper()
    prefix = re.match(r"([A-Z]+)", zone_upper)
    if not prefix:
        return {
            "zone": zone,
            "domain_valid": False,
            "verdict": "UNKNOWN_SCHEME",
            "warning": f"Cannot parse zone prefix from '{zone}'",
        }

    prefix_str = prefix.group(1)
    scheme_info = _ZONE_SCHEMES.get(prefix_str)

    if not scheme_info:
        return {
            "zone": zone,
            "domain_valid": False,
            "verdict": "UNKNOWN_SCHEME",
            "warning": f"Zone prefix '{prefix_str}' not in registry (known: NN, NP, CC, UC)",
        }

    age_dict, scheme_name, period_domain, era = scheme_info
    zone_ages = age_dict.get(zone_upper)

    if not zone_ages:
        return {
            "zone": zone,
            "scheme": scheme_name,
            "period_domain": period_domain,
            "era": era,
            "domain_valid": False,
            "verdict": "UNKNOWN_ZONE",
            "warning": f"Zone '{zone_upper}' not found in {scheme_name}",
        }

    result = {
        "zone": zone_upper,
        "scheme": scheme_name,
        "period_domain": period_domain,
        "era": era,
        "zone_age_top_ma": zone_ages[0],
        "zone_age_base_ma": zone_ages[1],
        "domain_valid": True,
        "verdict": "VALID",
        "warning": None,
    }

    if claimed_stage_or_age is None:
        return result

    # Determine claimed era from stage name or numeric age
    claimed_era = None
    claimed_age_ma = None

    if isinstance(claimed_stage_or_age, (int, float)):
        claimed_age_ma = float(claimed_stage_or_age)
    elif isinstance(claimed_stage_or_age, str):
        stage_lower = claimed_stage_or_age.lower()
        # Map common stage names to eras
        _CRETACEOUS_STAGES = {
            "berriasian",
            "valanginian",
            "hauterivian",
            "barremian",
            "aptian",
            "albian",
            "cenomanian",
            "turonian",
            "coniacian",
            "santonian",
            "campanian",
            "maastrichtian",
            "cretaceous",
        }
        _PALEOGENE_STAGES = {
            "danian",
            "selandian",
            "thanetian",
            "ypresian",
            "lutetian",
            "bartonian",
            "priabonian",
            "paleocene",
            "eocene",
            "paleogene",
        }
        _NEOGENE_STAGES = {
            "aquitanian",
            "burdigalian",
            "langhian",
            "serravallian",
            "tortonian",
            "messinian",
            "zanclean",
            "piacenzian",
            "gelasian",
            "neogene",
            "miocene",
            "pliocene",
            "pleistocene",
            "holocene",
            "quaternary",
        }

        if stage_lower in _CRETACEOUS_STAGES:
            claimed_era = "Mesozoic"
        elif stage_lower in _PALEOGENE_STAGES:
            claimed_era = "Cenozoic"
            if stage_lower in {"paleocene", "danian", "selandian", "thanetian"}:
                claimed_age_ma = 60.0  # midpoint
            elif stage_lower in {"eocene", "ypresian", "lutetian", "bartonian", "priabonian"}:
                claimed_age_ma = 45.0
        elif stage_lower in _NEOGENE_STAGES:
            claimed_era = "Cenozoic"
            if stage_lower in {"miocene", "aquitanian", "burdigalian", "langhian", "serravallian", "tortonian", "messinian"}:
                claimed_age_ma = 15.0
            elif stage_lower in {"pliocene", "zanclean", "piacenzian"}:
                claimed_age_ma = 3.5
            elif stage_lower in {"pleistocene", "quaternary", "holocene", "gelasian"}:
                claimed_age_ma = 1.0

    # Check for cross-era mismatch
    if claimed_era and claimed_era != era:
        result["domain_valid"] = False
        result["verdict"] = "CROSS_ERA_MISMATCH"
        result["warning"] = (
            f"Zone {zone_upper} belongs to {era} ({period_domain}, "
            f"{zone_ages[0]}–{zone_ages[1]} Ma) but claimed context is {claimed_era} "
            f"(stage: {claimed_stage_or_age}). This is a {era}-{claimed_era} mismatch. "
            f"Use {'CC' if claimed_era == 'Mesozoic' else 'NP'} zones instead."
        )
        return result

    # Check numeric age mismatch (if we have both)
    if claimed_age_ma is not None:
        if claimed_age_ma < zone_ages[0] - 5 or claimed_age_ma > zone_ages[1] + 5:
            result["domain_valid"] = False
            result["verdict"] = "AGE_MISMATCH"
            result["warning"] = (
                f"Zone {zone_upper} spans {zone_ages[0]}–{zone_ages[1]} Ma "
                f"but claimed age is {claimed_age_ma} Ma. "
                f"Difference exceeds 5 Myr tolerance."
            )
            return result

    return result


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
    """Parse nannofossil zone text into structured zone + evidence tag.

    FIX 2026-07-06: Now handles NN, NP, CC, UC zone schemes.
    Previously only matched NN zones — Cretaceous zones were silently dropped.

    Returns:
        {"zone": "CC23", "scheme": "Sissingh_1977_CC", "source_text": "CC23", "evidence_tag": "EVIDENCE_DIRECT"}
        or {"zone": "UNKNOWN", "source_text": "...", "evidence_tag": "NN_NOT_PARSED"}
    """
    text = clean_text(value)
    upper = text.upper()
    if not text:
        return {"zone": "UNKNOWN", "source_text": "", "evidence_tag": "NO_GDE_SOURCE"}
    if re.search(r"INDET|BARREN|NOT ANALY|ABSENT|UNKNOWN", upper):
        return {"zone": "UNKNOWN", "source_text": text, "evidence_tag": "SOURCE_UNRESOLVED"}

    # Try all zone schemes: NN, NP, CC, UC
    for prefix, pattern in [
        ("NN", r"\bNN\s*([0-9]{1,2}[A-C]?)\b"),
        ("NP", r"\bNP\s*([0-9]{1,2}[A-C]?)\b"),
        ("CC", r"\bCC\s*([0-9]{1,2})\b"),
        ("UC", r"\bUC\s*([0-9]{1,2})\b"),
    ]:
        matches = re.findall(pattern, upper)
        if matches:
            zones = [f"{prefix}{m}" for m in matches]
            scheme = _ZONE_SCHEMES.get(prefix, (None, "unknown", "unknown", "unknown"))[1]
            if len(zones) == 1:
                return {"zone": zones[0], "scheme": scheme, "source_text": text, "evidence_tag": "EVIDENCE_DIRECT"}
            return {"zone": "-".join(zones), "scheme": scheme, "source_text": text, "evidence_tag": "EVIDENCE_MULTI_ZONE"}

    return {"zone": "UNKNOWN", "source_text": text, "evidence_tag": "NN_NOT_PARSED"}


def nn_age(zone: str) -> tuple[float, float]:
    """Return (age_top_Ma, age_base_Ma) for any nannofossil zone (NN/NP/CC/UC).

    FIX 2026-07-06: Now resolves across all zone schemes, not just NN.
    Previously returned (-999.25, -999.25) for CC/UC/NP zones.
    """
    if not zone or zone == "UNKNOWN":
        return (-999.25, -999.25)
    parts = zone.split("-")
    ages = [_ALL_ZONES[p] for p in parts if p in _ALL_ZONES]
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
    """Classify lithology text into canonical LithoClass.

    FIX 2026-07-21 (T2.6-S3 F2): vocabulary extended so falsify G1's
    substring check ('evaporite' in litho_class.lower(), etc.) fires for
    the canonical lithology trigger words used by FOSSIL_ECOLOGY in
    biostrat_falsify.py (COAL_CARBONACEOUS, evaporite, red_bed,
    continental_conglomerate).

    The returned class name is the literal trigger word (lowercased) where
    possible, so G1's `if bad_litho.lower() in litho_class.lower()` matches.
    """
    text = clean_text(lithology).lower()
    if not text:
        return "UNKNOWN"
    if re.search(r"limestone|carbonate|dolomite|chalk", text):
        return "CARBONATE"
    # Evaporite family — needed by G1's excluded_lithologies check for
    # calcareous_nannofossil + planktonic_foraminifera.
    if re.search(r"evaporite|anhydrite|gypsum|halite|salt\b", text):
        return "evaporite"
    # Red beds — needed by G1 for calcareous_nannofossil.
    if re.search(r"red.bed|redbed|red sandstone|red.shale", text):
        return "red_bed"
    # Continental conglomerate — needed by G1 for calcareous_nannofossil.
    if re.search(r"continental.conglomerate|fluvial.conglomerate|alluvial.conglomerate", text):
        return "continental_conglomerate"
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
