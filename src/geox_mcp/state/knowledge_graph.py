"""
GEOX Knowledge Graph — H3 Geological Relations
════════════════════════════════════════════════
Seeded knowledge base of Malaysian basin geology.
Auto-populates GeoxWorkspace.relations when context is set.

Structure:
  relations[entity] = [related_entities]
  e.g., relations["Group H"] = ["Nuri-1", "Malikai-1", "Stage III inversion"]

H3 Architecture:
  H2 workspace → H3 knowledge graph → H4 Earth Twin → H5 QQQ reasoning

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any

# ── Malaysian Basin Knowledge Graph ──────────────────────────────────────────

_BASIN_WELLS: dict[str, list[str]] = {
    "Sabah": [
        "Nuri-1",
        "Malikai-1",
        "Kikeh-1",
        "Kikeh-2",
        "Kikeh Deep-1",
        "Gumusut-1",
        "Kakap-1",
        "Pisang-1",
        "Ubah-1",
        "Rotan-1",
        "Bunga Dahlia-1",
        "Bunga Orkid-1",
        "Samarang-1",
        "Erb West-1",
    ],
    "Kinabalu": [
        "Nuri-1",
        "Banjaran-1",
        "Kinabalu Deep-1",
    ],
    "Malay": [
        "M3-1",
        "M4-1",
        "Bunga Raya-1",
        "Angsi-1",
        "Beranang-1",
        "Dulang-1",
        "Tapis-1",
        "Guntong-1",
        "Seligi-1",
        "Pulai-1",
    ],
    "Sarawak": [
        "M1-1",
        "M2-1",
        "B11-1",
        "E8-1",
        "F6-1",
        "Helang-1",
        "F23-1",
        "Jintan-1",
        "Kanowit-1",
    ],
    "Baram Delta": [
        "Baram-1",
        "Baronia-1",
        "Betty-1",
        "Bokor-1",
        "Fairley-1",
        "Seria-1",
        "Champion-1",
        "Ampa-1",
    ],
    "North Luconia": [
        "M1-1",
        "Jintan-1",
        "F23-1",
    ],
}

_BASIN_FORMATIONS: dict[str, list[str]] = {
    "Sabah": [
        "Stage IV",
        "Stage III",
        "Stage II",
        "Group H",
        "Group I",
        "Belait Formation",
        "Setap Shale",
        "Meligan Formation",
        "Temburong Formation",
        "Crocker Formation",
        "Trusmadi Formation",
        "Kudat Formation",
        "Labang Formation",
    ],
    "Kinabalu": [
        "Group H",
        "Stage IV clastics",
        "Stage III carbonates",
        "Crocker Formation",
        "Trusmadi Formation",
    ],
    "Malay": [
        "Group K",
        "Group L",
        "Group M",
        "Group B",
        "Group D",
        "Group E",
        "Seligi Formation",
        "Tapis Formation",
        "Pulai Formation",
    ],
    "Sarawak": [
        "Cycle I",
        "Cycle II",
        "Cycle III",
        "Cycle IV",
        "Cycle V",
        "Nyalau Formation",
        "Lambir Formation",
        "Miri Formation",
    ],
    "Baram Delta": [
        "Cycle V",
        "Cycle VI",
        "Cycle VII",
        "Cycle VIII",
        "Miri Formation",
        "Lambir Formation",
        "Setap Shale",
    ],
}

_BASIN_PLAYS: dict[str, dict[str, list[str]]] = {
    "Sabah": {
        "Group H": ["Nuri-1", "Malikai-1", "Kikeh-1", "Kikeh-2"],
        "Group I": ["Gumusut-1", "Kakap-1"],
        "Stage IV": ["Kikeh Deep-1", "Banjaran-1"],
    },
    "Kinabalu": {
        "Group H": ["Nuri-1", "Banjaran-1", "Kinabalu Deep-1"],
        "Stage IV": ["Kinabalu Deep-1"],
    },
    "Malay": {
        "Group K": ["M3-1", "M4-1", "Bunga Raya-1"],
        "Group L": ["Dulang-1", "Tapis-1", "Guntong-1"],
        "Group M": ["Angsi-1", "Seligi-1"],
    },
    "Sarawak": {
        "Cycle II": ["B11-1", "Helang-1"],
        "Cycle III": ["E8-1", "F6-1"],
        "Cycle IV": ["F23-1", "Jintan-1"],
    },
    "Baram Delta": {
        "Cycle V": ["Baronia-1", "Betty-1"],
        "Cycle VI": ["Bokor-1", "Fairley-1"],
        "Cycle VII": ["Ampa-1", "Champion-1"],
    },
}

_BASIN_PAPERS: dict[str, list[str]] = {
    "Sabah": [
        "Cottam et al. 2013 (JGS) — Kinabalu granite cooling rate 360°C/Myr [DER]",
        "Cullen et al. 2010 (AAPG) — NW Borneo deepwater fold-thrust belts",
        "Morley et al. 2011 (Mar. Pet. Geol.) — Sabah Basin structural evolution",
        "Hutchison 2005 (GSM) — Geology of North-West Borneo",
    ],
    "Kinabalu": [
        "Cottam et al. 2013 (JGS) — Kinabalu granite cooling rate 360°C/Myr [DER]",
        "Hutchison 2005 (GSM) — Geology of North-West Borneo",
    ],
    "Malay": [
        "Madon et al. 2021 (GSM) — Malay Basin petroleum systems",
        "Madon 2021 (GSM) — Malay Basin stratigraphy and structure",
        "Ngah et al. 1996 (GSM) — Tertiary stratigraphy of Malay Basin",
    ],
    "Sarawak": [
        "Mat-Zin & Swarbrick 1997 (AAPG) — Baram Delta overpressure",
        "Mazlan et al. 2019 (GSM) — Sarawak Basin tectonostratigraphy",
    ],
    "Baram Delta": [
        "Mat-Zin & Swarbrick 1997 (AAPG) — Baram Delta overpressure",
        "Sandal 1996 (GSM) — Geology and hydrocarbon resources of Negara Brunei Darussalam",
    ],
}

_BASIN_EVENTS: dict[str, list[str]] = {
    "Sabah": [
        "Stage I rifting (Eocene)",
        "Stage II extension (Oligo-Miocene)",
        "Stage III compression (~8 Ma)",
        "Deepwater fold-thrust belt",
        "Kinabalu granite emplacement (7-8 Ma)",
    ],
    "Kinabalu": [
        "Stage III compression (~8 Ma)",
        "Kinabalu granite emplacement (7-8 Ma)",
        "Rapid exhumation 360°C/Myr",
    ],
    "Malay": [
        "Syn-rift (Oligocene)",
        "Post-rift thermal sag (Miocene)",
        "Basin inversion (Pliocene-Pleistocene)",
    ],
    "Sarawak": [
        "Rifting (Late Eocene)",
        "Drift (Oligo-Miocene)",
        "Baram Delta progradation (Mio-Pliocene)",
    ],
    "Baram Delta": [
        "Delta progradation (Middle Miocene)",
        "Shale diapirism",
        "Growth fault development",
    ],
}


def seed_relations(basin: str, play: str | None = None, well_id: str | None = None) -> dict[str, list[str]]:
    """Seed knowledge graph relations from basin/play/well context.

    Returns a relations dict ready to merge into GeoxWorkspace.
    """
    relations: dict[str, list[str]] = {}

    # Basin → wells
    wells = _BASIN_WELLS.get(basin, [])
    if wells:
        relations[basin] = list(dict.fromkeys(wells))  # dedup

    # Play → wells
    if play and basin in _BASIN_PLAYS:
        play_wells = _BASIN_PLAYS[basin].get(play, [])
        if play_wells:
            relations[play] = list(dict.fromkeys(play_wells))

    # Basin → formations
    formations = _BASIN_FORMATIONS.get(basin, [])
    if formations:
        key = f"{basin} Formations"
        relations[key] = formations

    # Basin → plays
    if basin in _BASIN_PLAYS:
        plays = list(_BASIN_PLAYS[basin].keys())
        if plays:
            key = f"{basin} Plays"
            relations[key] = plays

    # Basin → papers
    papers = _BASIN_PAPERS.get(basin, [])
    if papers:
        key = f"{basin} Papers"
        relations[key] = papers

    # Basin → tectonic events
    events = _BASIN_EVENTS.get(basin, [])
    if events:
        key = f"{basin} Events"
        relations[key] = events

    # Well → related wells in same play
    if well_id and play and basin in _BASIN_PLAYS:
        play_wells = _BASIN_PLAYS[basin].get(play, [])
        siblings = [w for w in play_wells if w != well_id]
        if siblings:
            relations[well_id] = siblings

    return relations


def get_basin_summary(basin: str) -> dict[str, Any]:
    """Get a summary knowledge card for a basin."""
    return {
        "basin": basin,
        "wells": _BASIN_WELLS.get(basin, []),
        "formations": _BASIN_FORMATIONS.get(basin, []),
        "plays": list(_BASIN_PLAYS.get(basin, {}).keys()),
        "papers": _BASIN_PAPERS.get(basin, []),
        "events": _BASIN_EVENTS.get(basin, []),
        "well_count": len(_BASIN_WELLS.get(basin, [])),
        "formation_count": len(_BASIN_FORMATIONS.get(basin, [])),
        "play_count": len(_BASIN_PLAYS.get(basin, {})),
        "paper_count": len(_BASIN_PAPERS.get(basin, [])),
    }


def list_basins() -> list[str]:
    """List all known basins in the knowledge graph."""
    return sorted(_BASIN_WELLS.keys())
