"""
crust_provenance_map.py — Hasterok 40-row → GEOX CrustZone vocabulary map
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given
Forged: 2026-08-11 by 333-AGI Δ MIND under F13 SOVEREIGN directive
Purpose: All GEOX agents use CrustZone as the standard vocabulary for describing
         earth crust types. This file provides the canonical 40→7 mapping from
         the Hasterok et al. (2022) provenance taxonomy to the GEOX CrustZone
         physical-state taxonomy.

AXIS CONFLICT (know this before using):
  ── Hasterok taxonomy (your 40 rows) = provenance / tectonic-history axis
    CV = Continental-Volcanic arc suite
    OV = Oceanic-Volcanic arc suite
    PM = Passive Margin suite
    Relic / Inverted / Accreted / Preserved = what happened to the suite
  ── GEOX CrustZone = physical-state axis
    Vp (km/s) + crustal thickness (km) = what the crust IS now
  ── When Hasterok says "Relic CV Suite" it means "this was a volcanic arc once"
    GEOX CrustZone says what it looks like NOW (Vp + thickness)
  ── The mapping below assigns the PHYSICAL (CrustZone) interpretation
    as the operational output. Provenance is annotation, not classification.

WILSON CYCLE STAGE:
  1 = Rift / Extension       → STRETCHED_CONTINENTAL / HYPERTHINNED_OCT
  2 = Drift / Passive Margin → NORMAL_CONTINENTAL (stable)
  3 = Convergence / Arc     → LOWER_CRUST_MAGMATIC / OCEANIC_CRUST
  4 = Collision / Orogeny  → DUCTILE_MID_CRUSTAL / LOWER_CRUST_MAGMATIC
  5 = Post-Orogenic         → NORMAL_CONTINENTAL (re-equilibrated)
  R → Rift again (cycle restarts)

LITERATURE:
  ── Hasterok et al. (2022) — global_tectonics — the Hasterok CV/OV/PM grammar source
  ── Huang et al. (2021) — Tectonics — the GEOX CrustZone Vp grammar source
  ── Wilson (1966) — Nature — the Wilson Cycle idea
  ── Rudnick & Gao (2003) — Treatise on Geochemistry — two crusts axiom
  ── Taylor & McLennan (1985) — andesitic bulk continental crust
  ── Péron-Pinvidic & Manatschal — hyperextended margins / OCT
  ── Doré & Lundin (2015) — Geology — hyperextended margins knowns & unknowns
  ── Welford (2024) — magma-poor COTZ / OCT Vp

USE THIS FILE to:
  1. Translate any Hasterok provenance label → CrustZone operational label
  2. Annotate a CrustZone with its likely provenance history
  3. Mark the 4 reversible calls that have two defensible mappings
  4. Make GEOX output consistent across all agents

REVERSIBLE CALLS (marked ⚠️ — two defensible interpretations):
  ── Arc suites (Relic CV/OV) → CrustZone 3 or 2? (arc PHYSICALLY vs reworked?)
  ── Continental Fragments → CrustZone 1 or 4? (buoyant block vs mobile terrain?)
  ── Back/fore-arc attenuation → CrustZone 4 or 3? (extension vs arc magmatism?)
  ── O-C Collisional CV Arc → CrustZone 3 or 4? (active arc vs thickened orogen?)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from geox_core.schemas.crust_vp_grammar import CrustZone


# ════════════════════════════════════════════════════════════════════════════════
# Dataclass for provenance entry — defined BEFORE the map that uses it
# ════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class ProvenanceEntry:
    """One row of the Hasterok → CrustZone mapping."""

    crust_zone: CrustZone
    wilson_stage: int  # 1=Rift, 2=Drift, 3=Arc/Convergence, 4=Collision, 5=Post-orogenic
    hasterok_axis: str  # "P" = provenance/history, "S" = physical/state
    provenance: str  # What this Hasterok label means tectonically
    notes: str = ""
    reversible_call: bool = False  # ⚠️ True = two defensible mappings

    def wilson_stage_name(self) -> str:
        names = {
            1: "Rift / Extension",
            2: "Drift / Passive Margin",
            3: "Arc / Convergence",
            4: "Collision / Orogeny",
            5: "Post-Orogenic",
        }
        return names.get(self.wilson_stage, "Unknown")


# ════════════════════════════════════════════════════════════════════════════════
# Canonical 40 → 7 mapping
# ════════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════════

# Each entry: (Hasterok label → CrustZone, Wilson stage, axis_conflict_note)
# axis: P = provenance-history axis (Hasterok) | S = physical-state axis (CrustZone)
# Provenance annotation is P-axis; CrustZone output is S-axis.
# ⚠️ = reversible call (two defensible interpretations)

CRUST_PROVENANCE_MAP: dict[str, ProvenanceEntry] = {
    # ── CRATON ──────────────────────────────────────────────────────────────
    "Craton: Shield": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,
        wilson_stage=2,  # stable / post-orogenic
        hasterok_axis="P",
        provenance="Oldest stable continental nucleus. Shield = exposure of cratonic root.",
        notes="Thick (~40 km), felsic, cold, buoyantly stable for >2 Gyr.",
    ),
    "Craton: Platform": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,
        wilson_stage=2,
        hasterok_axis="P",
        provenance="Craton covered by flat-lying sedimentary platform strata.",
        notes="Same physical signature as shield — normal continental Vp + thickness.",
    ),
    "Craton: Undifferentiated": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,
        wilson_stage=2,
        hasterok_axis="P",
        provenance="Craton but细分 not specified.",
        notes="Mapped to NORMAL_CONTINENTAL unless seismic says otherwise.",
    ),
    # ── MOBILE BELT ─────────────────────────────────────────────────────────
    "Mobile Belt: Relic CV Suite": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,  # ⚠️ reversible → could be 2 (reworked orogen)
        wilson_stage=3,
        hasterok_axis="P",
        provenance="Continental volcanic arc that has been accreted/deformed.",
        notes="CV arc material added to orogenic root. Vp → lower crust magmatic. ⚠️ Could also "
        "be DUCTILE_MID_CRUSTAL if orogenic thickening dominant. Prefer LOWER_CRUST_MAGMATIC "
        "when magmatic underplate signature present.",
        reversible_call=True,
    ),
    "Mobile Belt: Relic OV Suite": ProvenanceEntry(
        crust_zone=CrustZone.OCEANIC_CRUST,  # ⚠️ reversible → could be 2 (accreted, now thickened)
        wilson_stage=3,
        hasterok_axis="P",
        provenance="Oceanic volcanic arc accreted onto continental margin.",
        notes="Accreted OV material has mafic Vp signature. ⚠️ If heavily thickened/inverted, "
        "could map to LOWER_CRUST_MAGMATIC or DUCTILE_MID_CRUSTAL.",
        reversible_call=True,
    ),
    "Mobile Belt: Relic PM Suite": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,  # ⚠️ reversible → could be STRETCHED if rifted
        wilson_stage=2,
        hasterok_axis="P",
        provenance="Relic passive margin — extended continental margin now incorporated.",
        notes="PM = rifted continent. ⚠️ If extension was extreme, could be HYPERTHINNED_OCT "
        "or STRETCHED_CONTINENTAL. NORMAL_CONTINENTAL only if fully re-equilibrated.",
        reversible_call=True,
    ),
    "Mobile Belt: Continental Fragment": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,  # ⚠️ reversible → could be 4 (mobile terrain)
        wilson_stage=2,
        hasterok_axis="P",
        provenance="Exotic continental block accreted into mobile belt.",
        notes="Buoyant felsic block = NORMAL_CONTINENTAL Vp. ⚠️ If the block is thin/attenuated "
        "from transport, could be STRETCHED_CONTINENTAL.",
        reversible_call=True,
    ),
    "Mobile Belt: Preserved Intra-Continental Rift": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Failed rift preserved within continental interior.",
        notes="Rift valley fill + thinned flanks = STRETCHED_CONTINENTAL. β ≈ 2–3.",
    ),
    "Mobile Belt: Preserved Foreland": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,  # foreland = load-induced flexure, thinned
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Foreland basin + flexed foreland crust beneath orogenic load.",
        notes="Foreland crust is typically STRETCHED by flexural subsidence. Thick sediment fill.",
    ),
    "Mobile Belt: Preserved Orogenic Wedge": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Thickened orogenic wedge — accretionary/prism material.",
        notes="Orogenic wedge = thickened crust, often with DUCTILE_MID_CRUSTAL lower layer. "
        "LOWER_CRUST_MAGMATIC when magmatic addition present.",
    ),
    "Mobile Belt: Undifferentiated": ProvenanceEntry(
        crust_zone=CrustZone.DUCTILE_MID_CRUSTAL,  # undiff MB = complex, favor ductile
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Mobile belt but tectonic history unspecified.",
        notes="Default to DUCTILE_MID_CRUSTAL when MB is undifferentiated. "
        "Ductile mid-crustal is the most common MB present-state signature.",
    ),
    # ── C-C COLLISION ────────────────────────────────────────────────────────
    "C-C Collision: Undifferentiated": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Continent-continent collision belt, full orogen.",
        notes="Thickened orogen = LOWER_CRUST_MAGMATIC + DUCTILE_MID_CRUSTAL stack.",
    ),
    "C-C: Relic CV Suite": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Continental volcanic arc caught in C-C collision.",
        notes="Arc material underplated/thickened during collision.",
    ),
    "C-C: Relic OV Suite": ProvenanceEntry(
        crust_zone=CrustZone.OCEANIC_CRUST,  # ⚠️ reversible → could be LOWER_CRUST_MAGMATIC if thickened
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Oceanic arc caught in C-C collision.",
        notes="Accreted OV now at depth. ⚠️ If collision thickened it significantly, could be LOWER_CRUST_MAGMATIC.",
        reversible_call=True,
    ),
    "C-C: Inverted PM Suite": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Inverted passive margin — former rifted margin now under compression.",
        notes="PM inverted = THICKENED crust. But the Vp signature of thickened PM is "
        "indistinguishable from STRETCHED if no magmatic addition. "
        "Prefer STRETCHED_CONTINENTAL for inverted PM lacking magmatic Vp.",
    ),
    "C-C: Continental Fragment": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Continental fragment caught in C-C suture.",
        notes="Thin continental sliver. NORMAL_CONTINENTAL Vp if preserved; STRETCHED_CONTINENTAL if thinned by transport.",
    ),
    "C-C: Local Attenuation": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Local crustal attenuation within collisional belt.",
        notes="Core complex or local extension within orogen.",
    ),
    "C-C: Foreland": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="C-C collision foreland basin system.",
        notes="Foreland = flexural subsidence → THIN crust. STRETCHED_CONTINENTAL.",
    ),
    "C-C: Orogenic Wedge": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Accretionary orogenic wedge in C-C setting.",
        notes="Thickened, often with magmatic addition.",
    ),
    # ── O-C COLLISION ────────────────────────────────────────────────────────
    "O-C Collision: Undifferentiated": ProvenanceEntry(
        crust_zone=CrustZone.OCEANIC_CRUST,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Ocean-continent collision. Subduction of oceanic beneath continent.",
        notes="Oceanic slab + continental margin = complex. Default to OCEANIC_CRUST for "
        "the oceanic component unless thickened by arc addition.",
    ),
    "O-C: CV Arc": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,  # ⚠️ reversible → could be OCEANIC_CRUST (arc = mafic)
        wilson_stage=3,
        hasterok_axis="P",
        provenance="Continental volcanic arc built on oceanic or transitional basement.",
        notes="CV arc = andesitic-dacitic crust. ⚠️ PHYSICALLY similar to thickened oceanic. "
        "LOWER_CRUST_MAGMATIC when arc Vp signatures present (>6.8 km/s lower layer). "
        "OCEANIC_CRUST if purely mafic arc crust.",
        reversible_call=True,
    ),
    "O-C: Accreted OV Suite": ProvenanceEntry(
        crust_zone=CrustZone.OCEANIC_CRUST,
        wilson_stage=3,
        hasterok_axis="P",
        provenance="Accreted oceanic volcanic arc terrane welded to continent.",
        notes="OV arc material = mafic. Accreted = at surface. OCEANIC_CRUST Vp signature.",
    ),
    "O-C: Inverted PM Suite": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Inverted passive margin in O-C collision zone.",
        notes="Former rifted margin now shortened.",
    ),
    "O-C: Continental Fragment": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Exotic continental block in O-C collision zone.",
        notes="Microcontinent or ribbon continent.",
    ),
    "O-C: Back/Fore Arc Attenuation": ProvenanceEntry(
        crust_zone=CrustZone.HYPERTHINNED_OCT,  # ⚠️ reversible → back-arc could be STRETCHED
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Extension behind arc (back-arc) or in front (fore-arc) of O-C collision.",
        notes="Back-arc extension = extreme thinning → HYPERTHINNED_OCT or STRETCHED_CONTINENTAL. "
        "⚠️ Fore-arc attenuation is narrower zone — STRETCHED_CONTINENTAL may be more apt.",
        reversible_call=True,
    ),
    "O-C: Foreland": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="O-C collision foreland basin.",
        notes="Thin crust from flexural loading.",
    ),
    "O-C: Subduction-Accretion Complex": ProvenanceEntry(
        crust_zone=CrustZone.OCEANIC_CRUST,
        wilson_stage=3,
        hasterok_axis="P",
        provenance="Accreted oceanic sediment + crustal slices in subduction channel.",
        notes="Chaotic mixture. OCEANIC_CRUST Vp for mafic component.",
    ),
    # ── O-O COLLISION ────────────────────────────────────────────────────────
    "O-O Collision: Undifferentiated": ProvenanceEntry(
        crust_zone=CrustZone.OCEANIC_CRUST,
        wilson_stage=4,
        hasterok_axis="P",
        provenance="Ocean-ocean convergence. Two oceanic plates colliding.",
        notes="Typically produces intra-oceanic arc. OCEANIC_CRUST Vp for the basement.",
    ),
    "O-O: OV Arc": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,  # arc root = thickened mafic
        wilson_stage=3,
        hasterok_axis="P",
        provenance="Intra-oceanic volcanic arc in O-O setting.",
        notes="Arc root = lower crust Vp with magmatic underplate. LOWER_CRUST_MAGMATIC.",
    ),
    "O-O: Fore Arc Attenuation": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Fore-arc extension in intra-oceanic setting.",
        notes="Fore-arc spreading centre / trench rollback extension. STRETCHED_CONTINENTAL.",
    ),
    "O-O: Subduction-Accretion Complex": ProvenanceEntry(
        crust_zone=CrustZone.OCEANIC_CRUST,
        wilson_stage=3,
        hasterok_axis="P",
        provenance="Accretionary prism in O-O setting.",
        notes="Same logic as O-C subduction-accretion complex.",
    ),
    # ── CONTINENTAL FRAGMENT ───────────────────────────────────────────────
    "Continental Fragment": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,  # ⚠️ reversible → could be STRETCHED if thin
        wilson_stage=2,
        hasterok_axis="P",
        provenance="Displaced continental block (microcontinent / ribbon continent).",
        notes="Buoyant felsic block = NORMAL_CONTINENTAL Vp if thickness preserved. "
        "⚠️ If thinned during transport, STRETCHED_CONTINENTAL.",
        reversible_call=True,
    ),
    # ── CONTINENTAL CRUST ────────────────────────────────────────────────────
    "Continental Crust: Undifferentiated": ProvenanceEntry(
        crust_zone=CrustZone.NORMAL_CONTINENTAL,
        wilson_stage=2,
        hasterok_axis="P",
        provenance="Generic continental crust — composition unspecified.",
        notes="NORMAL_CONTINENTAL unless seismic shows thinning.",
    ),
    "Attenuated Continental Crust": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Continental crust stretched/thinned by extension.",
        notes="β > 2. STRETCHED_CONTINENTAL. If β > 4, HYPERTHINNED_OCT.",
    ),
    # ── OCEANIC CRUST ───────────────────────────────────────────────────────
    "Oceanic Crust": ProvenanceEntry(
        crust_zone=CrustZone.OCEANIC_CRUST,
        wilson_stage=3,
        hasterok_axis="S",
        provenance="Mature oceanic crust formed at mid-ocean ridge. Layer 2 + 3.",
        notes="~7 km thick. Vp ~5.0–7.0 km/s (layer 2) / ~7.0 km/s (layer 3).",
    ),
    "Thickened Oceanic Crust": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,  # thickened oceanic = underplate + magmatic thickening
        wilson_stage=3,
        hasterok_axis="P",
        provenance="Oceanic crust thickened by plume/arc addition or obduction.",
        notes="Thickened oceanic Vp → lower crust magmatic range (6.8–7.1 km/s). "
        "Mapped to LOWER_CRUST_MAGMATIC for operational use.",
    ),
    # ── TRANSITIONAL CRUST ──────────────────────────────────────────────────
    "Transitional: Undifferentiated": ProvenanceEntry(
        crust_zone=CrustZone.HYPERTHINNED_OCT,  # transitional = between cont and ocean = OCT
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Neither typical continental nor typical oceanic — ambiguous affinity.",
        notes="OCT territory. HYPERTHINNED_OCT or STRETCHED_CONTINENTAL depending on Vp.",
    ),
    "Transitional Crust: Strike-Slip": ProvenanceEntry(
        crust_zone=CrustZone.STRETCHED_CONTINENTAL,
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Transitional crust modified by strike-slip transfer.",
        notes="Strike-slip creates localized thinning. STRETCHED_CONTINENTAL geometry.",
    ),
    "Transitional Magma Rich": ProvenanceEntry(
        crust_zone=CrustZone.LOWER_CRUST_MAGMATIC,
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Transitional / OCT crust with significant magmatic addition.",
        notes="Magma-rich OCT = magmatic underplating. LOWER_CRUST_MAGMATIC signature.",
    ),
    "Transitional Magma Poor": ProvenanceEntry(
        crust_zone=CrustZone.HYPERTHINNED_OCT,
        wilson_stage=1,
        hasterok_axis="P",
        provenance="Hyperextended OCT with minimal magmatic addition.",
        notes="Serpentinized mantle exhaled. HYPERTHINNED_OCT. Vp ~2.5–5.0 km/s upper, ~7.7 km/s exhumed mantle.",
    ),
}


# ════════════════════════════════════════════════════════════════════════════════
# Dataclass for provenance entry
# ════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class ProvenanceEntry:
    """One row of the Hasterok → CrustZone mapping."""

    crust_zone: CrustZone
    wilson_stage: int  # 1=Rift, 2=Drift, 3=Arc/Convergence, 4=Collision, 5=Post-orogenic
    hasterok_axis: str  # "P" = provenance/history, "S" = physical/state (only Oceanic/Transitional)
    provenance: str  # What this Hasterok label means tectonically
    notes: str = ""
    reversible_call: bool = False  # ⚠️ True = two defensible mappings

    def wilson_stage_name(self) -> str:
        names = {
            1: "Rift / Extension",
            2: "Drift / Passive Margin",
            3: "Arc / Convergence",
            4: "Collision / Orogeny",
            5: "Post-Orogenic",
        }
        return names.get(self.wilson_stage, "Unknown")


# ════════════════════════════════════════════════════════════════════════════════
# Lookup helper
# ════════════════════════════════════════════════════════════════════════════════


def lookup(hasterok_label: str) -> ProvenanceEntry:
    """Look up a Hasterok label → CrustZone + provenance.

    Raises KeyError if label not in map. Use in all GEOX tool outputs
    that reference tectonic provenance.

    Usage:
        entry = lookup("Mobile Belt: Relic CV Suite")
        print(entry.crust_zone.value)       # → "lower_crust_magmatic"
        print(entry.wilson_stage_name())    # → "Arc / Convergence"
        print(entry.reversible_call)        # → True
    """
    if hasterok_label not in CRUST_PROVENANCE_MAP:
        raise KeyError(
            f"Unknown Hasterok label: {hasterok_label!r}. "
            f"Ran from mapping at 2026-08-11. "
            f"Available keys: {len(CRUST_PROVENANCE_MAP)}"
        )
    return CRUST_PROVENANCE_MAP[hasterok_label]


def all_labels() -> list[str]:
    """Return all 40 Hasterok provenance labels."""
    return list(CRUST_PROVENANCE_MAP.keys())


def reversible_calls() -> list[tuple[str, ProvenanceEntry]]:
    """Return all ⚠️ reversible mapping entries."""
    return [(k, v) for k, v in CRUST_PROVENANCE_MAP.items() if v.reversible_call]


def crust_zone_map() -> dict[CrustZone, list[str]]:
    """Invert the map: CrustZone → list of Hasterok labels that map to it."""
    from collections import defaultdict

    inv: dict[CrustZone, list[str]] = defaultdict(list)
    for label, entry in CRUST_PROVENANCE_MAP.items():
        inv[entry.crust_zone].append(label)
    return dict(inv)


# ════════════════════════════════════════════════════════════════════════════════
# 5-TYPE WILSON CYCLE COLLAPSE (ARIF's question)
# For GEOX agents: use CrustZone (7-type) as operational. Use this only
# when a 5-type Wilson-cycle classification is explicitly requested.
# ════════════════════════════════════════════════════════════════════════════════

WILSON_FIVE_COLLAPSE: dict[int, list[CrustZone]] = {
    1: [CrustZone.STRETCHED_CONTINENTAL, CrustZone.HYPERTHINNED_OCT],
    2: [CrustZone.NORMAL_CONTINENTAL],
    3: [CrustZone.LOWER_CRUST_MAGMATIC, CrustZone.OCEANIC_CRUST],
    4: [CrustZone.DUCTILE_MID_CRUSTAL, CrustZone.LOWER_CRUST_MAGMATIC],
    5: [CrustZone.NORMAL_CONTINENTAL, CrustZone.STRETCHED_CONTINENTAL],
}
"""Wilson cycle 5-stage → CrustZone mapping.

Stage 1 Rift/Extension        → STRETCHED_CONTINENTAL, HYPERTHINNED_OCT
Stage 2 Drift/Passive Margin   → NORMAL_CONTINENTAL
Stage 3 Arc/Convergence       → LOWER_CRUST_MAGMATIC, OCEANIC_CRUST
Stage 4 Collision/Orogeny     → DUCTILE_MID_CRUSTAL, LOWER_CRUST_MAGMATIC
Stage 5 Post-Orogenic         → NORMAL_CONTINENTAL (re-equilibrated)
"""


# ════════════════════════════════════════════════════════════════════════════════
# Exports
# ════════════════════════════════════════════════════════════════════════════════

__all__ = [
    "CRUST_PROVENANCE_MAP",
    "ProvenanceEntry",
    "lookup",
    "all_labels",
    "reversible_calls",
    "crust_zone_map",
    "WILSON_FIVE_COLLAPSE",
]
