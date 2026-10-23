#!/usr/bin/env python3
"""Create Sarawak basin registry entries in GEOX.

Field defect 2026-10-23: resources/basins/ held 11 entries — all Sabah plus Malay Basin.
No Sarawak province existed, so a working Sarawak geologist got a dead end.

Content discipline: every quantitative field that is not backed by a named public source is
left null with an explicit data_gap note. Qualitative geological characterisation is limited to
what is standard published synthesis (Sarawak Cycles framework, province definitions). Nothing
here is invented to look complete.
"""
import os
import textwrap
from pathlib import Path

ROOT = Path("/root/GEOX/resources/basins")

COMMON_GAPS = [
    "area_sq_km: not published per province in a single citable source; left null",
    "reserves and resources by province: not stated here — use a competent persons report, not a registry",
    "well counts and discovery inventories: not maintained in GEOX",
]

ENTRIES = {
    # ── umbrella ────────────────────────────────────────────────────────────
    "sarawak_basin": {
        "name": "Sarawak Basin",
        "id": "SARAWAK_BASIN",
        "location": "Offshore and onshore Sarawak, NW Borneo, Malaysia; South China Sea margin",
        "tectonic": "Cenozoic marginal basin system shaped by South China Sea opening, the West Baram Line, "
                    "and the Rajang accretionary complex to the south; divided into provinces with "
                    "distinct subsidence and sedimentary provenance histories",
        "framework": "Sarawak Cycles I to VIII (transgressive-regressive packages bounded by regional unconformities)",
        "status": "Mature to frontier, depending on province. Baram and Balingian mature; Central Luconia "
                  "a mature carbonate province; North and West Luconia largely frontier deepwater",
        "hc": "Gas-dominant, with significant oil in Baram and Balingian; Central Luconia carbonate build-ups "
              "are gas-bearing",
        "aliases": ["sarawak", "sarawak basin", "sk basin", "offshore sarawak", "sarawak offshore"],
        "provinces": ["baram", "balingian", "central_luconia", "north_luconia", "west_luconia"],
    },
    # ── provinces ───────────────────────────────────────────────────────────
    "north_luconia": {
        "name": "North Luconia",
        "id": "NORTH_LUCONIA",
        "location": "Deepwater offshore Sarawak, NW Borneo; north of the Central Luconia carbonate province",
        "tectonic": "Deepwater province on extended continental crust at the junction of the East Natuna, "
                    "West Luconia and North Luconia depositional systems; Oligocene rifting produced tilted "
                    "fault blocks whose crests nucleated carbonate build-ups",
        "framework": "Sarawak Cycles, with Oligo-Miocene carbonate build-ups and clastic intervals. "
                     "Cycle V and Cycle VII intervals are the principal described reservoir targets",
        "status": "Frontier. Sparsely drilled relative to province area — on the order of a dozen exploration "
                  "wells across more than 30,000 sq km of province (published figure, see bibliography)",
        "hc": "Gas-dominant. Carbonate build-up play with amplitude support and gas-cloud indications. "
              "Competent persons reporting on individual prospects assigns a high probability of a gas case",
        "aliases": ["north luconia", "north_luconia", "luconia north", "nl"],
        "reservoir": "Oligo-Miocene carbonate build-ups (argillaceous to clean), with clastic intervals in "
                     "Cycles I to III where penetrated",
        "source": "Syn-rift and post-rift shales below and adjacent to the build-ups; province-scale maturity "
                  "is not publicly calibrated at prospect locations",
        "seal": "Regional clastic drape over drowned build-ups. Seal quality is not publicly quantified "
                "anywhere in this province — this is the least evidenced play element",
        "trap": "Four-way dip closures over build-up crests on tilted fault blocks",
        "prospectivity_note": "Block 2A (operator INPEX Malaysia E&P 2A Limited at 42.5%, PETRONAS Carigali 40%, "
                              "Seascape Energy (2A) 10%, PSEP 7.5%) contains the Kertang prospect, a four-way "
                              "closure over 200-220 sq km with gross unrisked mean prospective resources of "
                              "9.1 Tcf gas plus 146 million barrels NGL, chance of success about 20%, at roughly "
                              "1,000 m water depth. Source: partner company public releases and the published "
                              "competent persons report summary. Recorded here as a published claim, not as a "
                              "GEOX estimate.",
    },
    "central_luconia": {
        "name": "Central Luconia",
        "id": "CENTRAL_LUCONIA",
        "location": "Offshore Sarawak, NW Borneo; the classic carbonate build-up province",
        "tectonic": "Late Oligocene to Miocene carbonate build-ups on horst blocks and structural highs, "
                    "drowned and draped by clastic input as the Baram and Rajang systems prograded",
        "framework": "Sarawak Cycles, principally Cycle IV and Cycle V carbonate build-ups",
        "status": "Mature carbonate province with many hundreds of build-up penetrations and several "
                  "producing gas fields",
        "hc": "Gas-dominant in the build-ups; sour gas with variable CO2 is common and is a development "
              "cost driver",
        "aliases": ["central luconia", "central_luconia", "luconia", "luconia central"],
        "reservoir": "Miocene carbonate build-ups. Reservoir quality is diagenetically controlled: karst and "
                     "dolomitisation improve it, tight argillaceous lime mudstone destroys it, within the same "
                     "build-up",
        "source": "Intra-formational and adjacent shales; charge from below and laterally",
        "seal": "Regional clastic drape; seal adequacy varies and is a routine development-phase question",
        "trap": "Build-up geometry with four-way or fault-assisted closure; stratigraphic component common",
        "prospectivity_note": "The province is the analogue set for deepwater carbonate prospectivity elsewhere "
                              "in Sarawak. Reservoir and seal behaviour are not transferable to North Luconia "
                              "at 400 km basinward; treat analogue use explicitly.",
    },
    "balingian": {
        "name": "Balingian",
        "id": "BALINGIAN",
        "location": "Shallow water offshore Sarawak, NW Borneo, roughly central Sarawak coast",
        "tectonic": "Cenozoic basin with significant coaly and paralic section; clastic-dominated with "
                    "structural and stratigraphic trapping",
        "framework": "Sarawak Cycles I to III are the principal described reservoir intervals; coaly source "
                     "rocks within the section",
        "status": "Mature to emerging; shallow water with active exploration and appraisal",
        "hc": "Oil and gas. Coaly source rocks give a mixed kerogen type, and gas-condensate is common",
        "aliases": ["balingian", "balingian province", "sk405b", "sk405"],
        "reservoir": "Cycle I to III shallow marine and deltaic clastics; lateral continuity and net-to-gross "
                     "are the routine risks",
        "source": "Coaly and carbonaceous shales within the Cycle I to III section; kerogen type II-III to III",
        "seal": "Intra-formational shales; seal adequacy is usually better evidenced here than in the "
                "carbonate provinces",
        "trap": "Structural closures with a significant stratigraphic component; fault dependency common",
        "prospectivity_note": "Block SK405B (PTTEP Sarawak Oil operator, with MOECO and PETRONAS Carigali) "
                              "delivered the Sirung-1 oil and gas discovery, announced by PETRONAS on "
                              "30 March 2021, drilled to 2,538 m total depth with an oil and gas column "
                              "exceeding 100 m in Oligocene to Middle Miocene sandstones. Recorded as a "
                              "published claim.",
    },
    "baram": {
        "name": "Baram Delta",
        "id": "BARAM",
        "location": "Offshore and onshore Sarawak, NW Borneo, centred on the Baram Delta and the West Baram Line",
        "tectonic": "Deltaic to deepwater clastic system fed by the Baram river, deformed by gravity tectonics "
                    "and cut by the West Baram Line; growth faults and shale diapirs are characteristic",
        "framework": "Sarawak Cycles, with Miocene deltaic and deepwater clastic reservoirs; Cycle V "
                     "deep-marine intervals are a recognised deepwater target",
        "status": "Mature for shallow deltaics; deepwater distal equivalents are actively explored",
        "hc": "Oil and gas; the delta is one of Malaysia's historic oil provinces, with gas in deeper and "
              "more distal plays",
        "aliases": ["baram", "baram delta", "baram province", "west baram"],
        "reservoir": "Miocene deltaic to deepwater turbidite sandstones; stacking patterns and lateral "
                     "discontinuity control net-to-gross. Authigenic clay (kaolinite, illite) controls "
                     "permeability",
        "source": "Coaly and marine shales in the delta succession; charge is generally well evidenced",
        "seal": "Interbedded shales and growth-fault seals; top seal adequacy varies with fault activity",
        "trap": "Rollover anticlines against growth faults, fault-dependent closures, and stratigraphic traps "
                "in channel and lobe sands",
        "prospectivity_note": "Distal Baram deepwater play has been reassessed using reprocessed 3D and "
                              "spectral decomposition; reservoir thickness, not charge, is the recurring risk "
                              "in published assessments of the stepped-slope play.",
    },
}

TEMPLATE = """\
# GEOX basin registry — {name}
# Created 2026-10-23. Field defect: no Sarawak province existed in the registry, so a working
# geologist asking about Sarawak hit a bare "Basin data not found".
#
# DISCIPLINE: qualitative characterisation only where it is standard published synthesis.
# Any quantitative field that is not backed by a named public source is null with a data_gap note.
# Nothing here is invented to look complete.

basin_name: "{name}"
basin_id: "{bid}"
location: "{location}"
area_sq_km: null            # data_gap: no single citable per-province figure used
tectonic_setting: >-
  {tectonic}
stratigraphic_framework: >-
  {framework}
status: >-
  {status}
primary_hydrocarbon: >-
  {hc}
parent_basin: "sarawak_basin"
aliases:
{aliases}
stratigraphy:
  framework: "Sarawak Cycles I to VIII"
  note: >-
    Cycle boundaries are regional unconformities. Maximum flooding surfaces are both the most
    reliable correlation markers and the most organic-rich intervals — sample them deliberately.
data_gaps:
{gaps}
{extra}"""


def yaml_block(text, indent=2):
    pad = " " * indent
    return "\n".join(pad + line for line in textwrap.wrap(" ".join(text.split()), 92))


def write(entry_key, data):
    d = ROOT / entry_key
    d.mkdir(parents=True, exist_ok=True)
    aliases = "\n".join(f'  - "{a}"' for a in data["aliases"])
    gaps = "\n".join(f'  - "{g}"' for g in COMMON_GAPS)
    extra = ""
    if "reservoir" in data:
        extra += f"""
play_elements:
  reservoir: >-
{yaml_block(data["reservoir"], 4)}
  source: >-
{yaml_block(data["source"], 4)}
  seal: >-
{yaml_block(data["seal"], 4)}
  trap: >-
{yaml_block(data["trap"], 4)}
  seal_is_least_evidenced: {"true" if data["id"] == "NORTH_LUCONIA" else "false"}
"""
    if "provinces" in data:
        extra += "\nprovinces:\n" + "\n".join(f'  - {p}' for p in data["provinces"]) + "\n"
    if "prospectivity_note" in data:
        extra += f"""
published_claims:
  - note: >-
{yaml_block(data["prospectivity_note"], 6)}
    epistemic: "PUBLISHED_CLAIM — recorded from public reporting, not a GEOX computation"
    forbidden_use: "Do not present as a GEOX estimate, reserve, or drilling recommendation."
"""
    content = TEMPLATE.format(
        name=data["name"], bid=data["id"], location=data["location"],
        tectonic=data["tectonic"], framework=data["framework"], status=data["status"],
        hc=data["hc"], aliases=aliases, gaps=gaps, extra=extra,
    )
    (d / "basin_profile.yaml").write_text(content, encoding="utf-8")
    print(f"wrote {d}/basin_profile.yaml ({len(content)} bytes)")


if __name__ == "__main__":
    for key, data in ENTRIES.items():
        write(key, data)
