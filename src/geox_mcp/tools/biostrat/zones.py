"""
biostrat/zones.py — Multi-scheme biostratigraphic zone engine.

DITEMPA BUKAN DIBERI — Forged, Not Given.

Handles zone parsing, age lookup, and cross-scheme mapping for:
- Martini (1971) NN zones (Neogene nannofossil)
- Martini (1971) NP zones (Paleogene nannofossil)
- Sissingh (1977) CC zones (Cretaceous nannofossil)
- Bukry (1973) CN zones (Neogene low-latitude coccolith)
- Okada & Bukry (1980) CP zones (Paleogene low-latitude coccolith)
- Agnini et al. (2014) CNP/CNE/CNO zones
- Blow (1969) N zones (Neogene planktonic foram)
- Blow (1969) P zones (Paleogene planktonic foram)
- Lunt (2016) LBF zones (SE Asia larger benthic foram)

Age data sourced from PBDB timescale scale=5 (calcareous nannoplankton zones)
and scale=24 (planktic foraminiferal primary biozones).
"""

from __future__ import annotations

import re
from typing import Any

from .schemas import Biozone

# ── Zone Age Dictionaries ────────────────────────────────────────────────────
# Format: { zone_id: (age_top_Ma, age_base_Ma) }
# age_top = youngest (closest to present), age_base = oldest

# Martini (1971) — Neogene Nannofossil Zones (NN1–NN21)
NN_ZONES: dict[str, tuple[float, float]] = {
    "NN21": (0.00, 0.29),
    "NN20": (0.29, 0.44),
    "NN19": (0.44, 1.93),
    "NN18": (1.93, 2.39),
    "NN17": (2.39, 3.54),
    "NN16": (3.54, 4.13),
    "NN15": (4.13, 4.53),
    "NN14": (4.53, 5.13),
    "NN13": (5.13, 5.59),
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
    "NN8": (11.79, 12.62),
    "NN7": (12.62, 13.53),
    "NN6": (13.53, 14.62),
    "NN5": (14.62, 15.97),
    "NN4": (15.97, 18.28),
    "NN3": (18.28, 19.79),
    "NN2": (19.79, 21.12),
    "NN1": (21.12, 23.03),
}

# Martini (1971) — Paleogene Nannofossil Zones (NP1–NP25)
NP_ZONES: dict[str, tuple[float, float]] = {
    "NP25": (23.03, 28.10),
    "NP24": (28.10, 29.60),
    "NP23": (29.60, 33.90),
    "NP22": (33.90, 34.70),
    "NP21": (34.70, 37.70),
    "NP20": (37.70, 40.40),
    "NP19": (40.40, 42.90),
    "NP18": (42.90, 46.30),
    "NP17": (46.30, 47.80),
    "NP16": (47.80, 49.10),
    "NP15": (49.10, 50.50),
    "NP14": (50.50, 52.00),
    "NP13": (52.00, 53.70),
    "NP12": (53.70, 54.60),
    "NP11": (54.60, 55.20),
    "NP10": (55.20, 55.80),
    "NP9": (55.80, 56.80),
    "NP8": (56.80, 57.60),
    "NP7": (57.60, 59.20),
    "NP6": (59.20, 61.10),
    "NP5": (61.10, 61.60),
    "NP4": (61.60, 62.50),
    "NP3": (62.50, 63.30),
    "NP2": (63.30, 64.70),
    "NP1": (64.70, 66.00),
}

# Sissingh (1977) — Cretaceous Nannofossil Zones (CC1–CC26)
CC_ZONES: dict[str, tuple[float, float]] = {
    "CC26": (66.0, 67.7),
    "CC25": (67.7, 69.5),
    "CC24": (69.5, 71.3),
    "CC23": (71.3, 72.1),
    "CC22": (72.1, 76.0),
    "CC21": (76.0, 80.5),
    "CC20": (80.5, 83.5),
    "CC19": (83.5, 85.8),
    "CC18": (85.8, 87.5),
    "CC17": (87.5, 89.0),
    "CC16": (89.0, 90.5),
    "CC15": (90.5, 92.5),
    "CC14": (92.5, 94.0),
    "CC13": (94.0, 97.0),
    "CC12": (97.0, 99.5),
    "CC11": (99.5, 103.0),
    "CC10": (103.0, 105.5),
    "CC9": (105.5, 109.0),
    "CC8": (109.0, 112.5),
    "CC7": (112.5, 116.5),
    "CC6": (116.5, 119.5),
    "CC5": (119.5, 122.5),
    "CC4": (122.5, 126.0),
    "CC3": (126.0, 128.5),
    "CC2": (128.5, 130.5),
    "CC1": (130.5, 133.9),
}

# Bukry (1973/1975) — Neogene Low-Latitude Coccolith Zones (CN1–CN15)
CN_ZONES: dict[str, tuple[float, float]] = {
    "CN15": (0.00, 1.93),
    "CN14": (1.93, 3.54),
    "CN13": (3.54, 4.53),
    "CN12": (4.53, 5.59),
    "CN11": (5.59, 8.59),
    "CN10": (8.59, 10.41),
    "CN9": (10.41, 11.79),
    "CN8": (11.79, 12.62),
    "CN7": (12.62, 13.53),
    "CN6": (13.53, 14.62),
    "CN5": (14.62, 15.97),
    "CN4": (15.97, 18.28),
    "CN3": (18.28, 19.79),
    "CN2": (19.79, 21.12),
    "CN1": (21.12, 23.03),
}

# Okada & Bukry (1980) — Paleogene Low-Latitude Coccolith Zones (CP1–CP19)
CP_ZONES: dict[str, tuple[float, float]] = {
    "CP19": (23.03, 28.10),
    "CP18": (28.10, 33.90),
    "CP17": (33.90, 37.70),
    "CP16": (37.70, 42.90),
    "CP15": (42.90, 46.30),
    "CP14": (46.30, 49.10),
    "CP13": (49.10, 50.50),
    "CP12": (50.50, 52.00),
    "CP11": (52.00, 53.70),
    "CP10": (53.70, 55.20),
    "CP9": (55.20, 56.80),
    "CP8": (56.80, 57.60),
    "CP7": (57.60, 59.20),
    "CP6": (59.20, 61.10),
    "CP5": (61.10, 62.50),
    "CP4": (62.50, 63.30),
    "CP3": (63.30, 64.70),
    "CP2": (64.70, 65.50),
    "CP1": (65.50, 66.00),
}

# Blow (1969) — Neogene Planktonic Foram Zones (N1–N23)
N_ZONES: dict[str, tuple[float, float]] = {
    "N23": (0.00, 0.01),
    "N22": (0.01, 0.25),
    "N21": (0.25, 1.81),
    "N20": (1.81, 3.07),
    "N19": (3.07, 3.65),
    "N18": (3.65, 5.08),
    "N17": (5.08, 6.32),
    "N16": (6.32, 8.55),
    "N15": (8.55, 10.45),
    "N14": (10.45, 11.18),
    "N13": (11.18, 12.75),
    "N12": (12.75, 14.80),
    "N11": (14.80, 16.38),
    "N10": (16.38, 17.54),
    "N9": (17.54, 19.04),
    "N8": (19.04, 20.43),
    "N7": (20.43, 21.70),
    "N6": (21.70, 23.03),
    "N5": (23.03, 23.80),
    "N4": (23.80, 25.20),
    "N3": (25.20, 27.50),
    "N2": (27.50, 30.00),
    "N1": (30.00, 33.90),
}

# Blow (1969) — Paleogene Planktonic Foram Zones (P1–P22)
P_ZONES: dict[str, tuple[float, float]] = {
    "P22": (23.03, 28.10),
    "P21": (28.10, 29.60),
    "P20": (29.60, 33.90),
    "P19": (33.90, 36.30),
    "P18": (36.30, 38.00),
    "P17": (38.00, 40.40),
    "P16": (40.40, 42.90),
    "P15": (42.90, 45.50),
    "P14": (45.50, 47.80),
    "P13": (47.80, 49.10),
    "P12": (49.10, 50.50),
    "P11": (50.50, 52.00),
    "P10": (52.00, 53.70),
    "P9": (53.70, 54.60),
    "P8": (54.60, 55.80),
    "P7": (55.80, 56.80),
    "P6": (56.80, 57.60),
    "P5": (57.60, 59.20),
    "P4": (59.20, 61.10),
    "P3": (61.10, 62.50),
    "P2": (62.50, 64.70),
    "P1": (64.70, 66.00),
}

# Lunt (2016) — Larger Benthic Foram Zones (SE Asia)
LBF_ZONES: dict[str, tuple[float, float]] = {
    "Tf1": (0.00, 2.60),
    "Tf2": (2.60, 5.33),
    "Te5": (5.33, 7.10),
    "Te4": (7.10, 11.60),
    "Te3": (11.60, 13.60),
    "Te2": (13.60, 15.90),
    "Te1": (15.90, 23.03),
    "Tg": (23.03, 28.10),
    "Th": (28.10, 33.90),
    "Ti1": (33.90, 37.70),
    "Ti2": (37.70, 42.90),
    "Tj": (42.90, 47.80),
    "Tk": (47.80, 55.80),
    "Tl": (55.80, 66.00),
}

# ── Scheme Registry ──────────────────────────────────────────────────────────

SCHEME_REGISTRY: dict[str, dict[str, Any]] = {
    "Martini_1971_NN": {
        "zones": NN_ZONES,
        "fossil_group": "calcareous_nannofossil",
        "prefix": "NN",
        "reference": "Martini, E. (1971) Proc. 2nd Planktonic Conf. Roma, 2: 739-785.",
        "period": "Neogene",
    },
    "Martini_1971_NP": {
        "zones": NP_ZONES,
        "fossil_group": "calcareous_nannofossil",
        "prefix": "NP",
        "reference": "Martini, E. (1971) Proc. 2nd Planktonic Conf. Roma, 2: 739-785.",
        "period": "Paleogene",
    },
    "Sissingh_1977_CC": {
        "zones": CC_ZONES,
        "fossil_group": "calcareous_nannofossil",
        "prefix": "CC",
        "reference": "Sissingh, F.H. (1977) Proc. K. Ned. Akad. Wet. B80: 56-69.",
        "period": "Cretaceous",
    },
    "Bukry_1973_CN": {
        "zones": CN_ZONES,
        "fossil_group": "calcareous_nannofossil",
        "prefix": "CN",
        "reference": "Bukry, D. (1973) Initial Rep. DSDP 20: 75-80.",
        "period": "Neogene",
    },
    "Okada_Bukry_1980_CP": {
        "zones": CP_ZONES,
        "fossil_group": "calcareous_nannofossil",
        "prefix": "CP",
        "reference": "Okada, H. & Bukry, D. (1980) Mar. Micropaleontol. 5: 321-325.",
        "period": "Paleogene",
    },
    "Blow_1969_N": {
        "zones": N_ZONES,
        "fossil_group": "planktonic_foram",
        "prefix": "N",
        "reference": "Blow, W.H. (1969) Proc. 1st Int. Conf. Planktonic Microfossils, 1: 199-422.",
        "period": "Neogene",
    },
    "Blow_1969_P": {
        "zones": P_ZONES,
        "fossil_group": "planktonic_foram",
        "prefix": "P",
        "reference": "Blow, W.H. (1969) Proc. 1st Int. Conf. Planktonic Microfossils, 1: 199-422.",
        "period": "Paleogene",
    },
    "Lunt_2016_LBF": {
        "zones": LBF_ZONES,
        "fossil_group": "larger_benthic_foram",
        "prefix": "T",
        "reference": "Lunt, P. (2016) SE Asia larger foraminifera biozonation.",
        "period": "Cenozoic",
    },
}

# ── Zone Parsing ─────────────────────────────────────────────────────────────

# Regex patterns for each scheme
_ZONE_PATTERNS = {
    "NN": re.compile(r"\bNN\s*([0-9]{1,2}[A-C]?)\b", re.I),
    "NP": re.compile(r"\bNP\s*([0-9]{1,2})\b", re.I),
    "CC": re.compile(r"\bCC\s*([0-9]{1,2})\b", re.I),
    "CN": re.compile(r"\bCN\s*([0-9]{1,2})\b", re.I),
    "CP": re.compile(r"\bCP\s*([0-9]{1,2})\b", re.I),
    "N": re.compile(r"\bN\s*([0-9]{1,2})\b"),
    "P": re.compile(r"\bP\s*([0-9]{1,2})\b"),
    "LBF": re.compile(r"\bT[a-l]\s*([0-9]?)\b", re.I),
}


def parse_zone(text: str) -> list[dict[str, str]]:
    """Parse free-text for biostratigraphic zone codes.

    Returns a list of detected zones with scheme, zone_id, and evidence tag.
    Supports NN, NP, CC, CN, CP, N, P, and LBF (T-letter) patterns.

    Args:
        text: Free-text string that may contain zone codes.

    Returns:
        List of dicts: {"zone": "NN21", "scheme": "Martini_1971_NN", "evidence_tag": ...}
    """
    if not text:
        return []

    results: list[dict[str, str]] = []

    # Try each pattern
    for prefix, pattern in _ZONE_PATTERNS.items():
        matches = pattern.findall(text.upper())
        for m in matches:
            if prefix == "NN":
                zone_id = f"NN{m}"
                scheme = "Martini_1971_NN"
            elif prefix == "NP":
                zone_id = f"NP{m}"
                scheme = "Martini_1971_NP"
            elif prefix == "CC":
                zone_id = f"CC{m}"
                scheme = "Sissingh_1977_CC"
            elif prefix == "CN":
                zone_id = f"CN{m}"
                scheme = "Bukry_1973_CN"
            elif prefix == "CP":
                zone_id = f"CP{m}"
                scheme = "Okada_Bukry_1980_CP"
            elif prefix == "N":
                zone_id = f"N{m}"
                scheme = "Blow_1969_N"
            elif prefix == "P":
                zone_id = f"P{m}"
                scheme = "Blow_1969_P"
            elif prefix == "LBF":
                # LBF pattern is T + letter + optional digit
                zone_id = f"T{m}" if m else ""
                scheme = "Lunt_2016_LBF"
            else:
                continue

            if not zone_id:
                continue

            results.append(
                {
                    "zone": zone_id,
                    "scheme": scheme,
                    "evidence_tag": "EVIDENCE_DIRECT",
                }
            )

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        key = (r["zone"], r["scheme"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


def zone_age(zone_id: str, scheme: str | None = None) -> tuple[float, float]:
    """Look up (age_top_Ma, age_base_Ma) for a zone.

    Args:
        zone_id: Zone code, e.g. "NN21", "NP25", "N17"
        scheme: Optional scheme name for disambiguation

    Returns:
        (age_top_Ma, age_base_Ma) or (-999.25, -999.25) if not found
    """
    if not zone_id:
        return (-999.25, -999.25)

    zone_upper = zone_id.upper().strip()

    # If scheme is provided, look up directly
    if scheme and scheme in SCHEME_REGISTRY:
        zones = SCHEME_REGISTRY[scheme]["zones"]
        if zone_upper in zones:
            return zones[zone_upper]

    # Try all schemes
    for _name, info in SCHEME_REGISTRY.items():
        if zone_upper in info["zones"]:
            return info["zones"][zone_upper]

    return (-999.25, -999.25)


def zone_to_biozone(zone_id: str, scheme: str | None = None) -> Biozone | None:
    """Convert a zone_id to a full Biozone object.

    Args:
        zone_id: Zone code
        scheme: Optional scheme name

    Returns:
        Biozone object or None if not found
    """
    zone_upper = zone_id.upper().strip()

    # Try specified scheme first, then all
    schemes_to_try = [scheme] if scheme else []
    schemes_to_try.extend(SCHEME_REGISTRY.keys())

    for s in schemes_to_try:
        if s not in SCHEME_REGISTRY:
            continue
        info = SCHEME_REGISTRY[s]
        zones = info["zones"]
        if zone_upper in zones:
            top, base = zones[zone_upper]
            return Biozone(
                zone_id=zone_upper,
                scheme=s,  # type: ignore[arg-type]
                fossil_group=info["fossil_group"],  # type: ignore[arg-type]
                age_top_ma=top,
                age_base_ma=base,
                reference=info["reference"],
            )
    return None


def resolve_scheme_for_zone(zone_id: str) -> str | None:
    """Determine which scheme a zone belongs to.

    Args:
        zone_id: Zone code, e.g. "NN21"

    Returns:
        Scheme name or None
    """
    zone_upper = zone_id.upper().strip()
    for name, info in SCHEME_REGISTRY.items():
        if zone_upper in info["zones"]:
            return name
    return None


def list_zones_for_scheme(scheme: str) -> list[dict[str, Any]]:
    """List all zones in a given scheme with their age ranges.

    Args:
        scheme: Scheme name, e.g. "Martini_1971_NN"

    Returns:
        List of zone dicts
    """
    if scheme not in SCHEME_REGISTRY:
        return []

    info = SCHEME_REGISTRY[scheme]
    result = []
    for zone_id, (top, base) in info["zones"].items():
        result.append(
            {
                "zone_id": zone_id,
                "age_top_ma": top,
                "age_base_ma": base,
                "scheme": scheme,
                "fossil_group": info["fossil_group"],
                "period": info["period"],
            }
        )
    return result


def get_scheme_reference(scheme: str) -> str:
    """Get the bibliographic reference for a scheme.

    Args:
        scheme: Scheme name

    Returns:
        Reference string
    """
    if scheme in SCHEME_REGISTRY:
        return SCHEME_REGISTRY[scheme]["reference"]
    return ""


# ── Convenience: Re-export NN parser for backward compatibility ──────────────


def parse_nn_zone(value: str) -> dict[str, str]:
    """Legacy-compatible NN zone parser.

    Returns:
        {"zone": "NN19", "source_text": "NN19-20", "evidence_tag": "EVIDENCE_DIRECT"}
    """
    text = (value or "").strip()
    upper = text.upper()
    if not text:
        return {"zone": "UNKNOWN", "source_text": "", "evidence_tag": "NO_SOURCE"}
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
    """Legacy-compatible NN age lookup."""
    return zone_age(zone, "Martini_1971_NN")
