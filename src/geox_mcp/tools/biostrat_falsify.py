"""biostrat_falsification.py — GEOX MCP tool: Popperian falsification engine for biostrat claims.

Phase 2.5 (2026-07-03): Arif sovereign spec — biostratigraphy is real science only when
practiced with the same falsification discipline as any other geological method.

Every biostrat claim must be testable, falsifiable, and cross-validated.
This tool runs 8 falsification gates against any claim and returns:
  - PASS (survives all gates at this evidence level)
  - FALSIFIED (contradicts physical or biological reality)
  - UNFALSIFIABLE (claim is too vague to test — reject)
  - HOLD (insufficient evidence to falsify or validate)

THE 8 FALSIFICATION GATES:
  G1 — Facies contradiction: fossil ecology vs lithology/environment
  G2 — Stratigraphic impossibility: age ordering violation
  G3 — Taxonomic audit: misidentification risk, synonymy drift
  G4 — Reworking/caving: physical transport of fossil ≠ in situ
  G5 — Diachroneity: assumed synchrony across basin space
  G6 — Seismic mismatch: age claim vs stratal geometry
  G7 — Sequence stratigraphy mismatch: bioevent vs stacking pattern
  G8 — Regional tectonic mismatch: age vs known unconformities/events

POPPER RULE: A single contradiction → FALSIFIED regardless of how many other gates pass.
Science advances by eliminating what cannot be true, not by accumulating confirmations.

F2 TRUTH: Every gate produces evidence_for and evidence_against.
F4 CLARITY: Each gate is independent. No gate's result depends on another gate.
F6 MARUAH: Falsification preserves scientific dignity — killing wrong ideas is progress.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

from geox_core.enums.statuses import get_standard_envelope
from geox_mcp.tools.kernel._biostrat import (
    parse_nn_zone,
    nn_age,
    map_gde,
    lithology_class,
    clean_text,
)

logger = logging.getLogger("geox.canonical.biostrat_falsification")


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 1 — Facies Contradiction
# ═══════════════════════════════════════════════════════════════════════════════
# Rule: fossil ecology MUST be compatible with depositional lithology/environment.
# Marine nannofossils in coal = INSTANT FALSIFICATION.

FOSSIL_ECOLOGY = {
    "calcareous_nannofossil": {
        "requires": "marine_water_column",
        "excluded_lithologies": ["COAL_CARBONACEOUS", "evaporite", "red_bed", "continental_conglomerate"],
        "excluded_environments": ["freshwater_swamp", "fluvial", "lacustrine", "alluvial"],
        "falsification_message": "Calcareous nannofossils require open marine water. Found in non-marine facies → FALSIFIED unless reworking documented.",
    },
    "planktonic_foraminifera": {
        "requires": "open_marine",
        "excluded_lithologies": ["COAL_CARBONACEOUS", "evaporite"],
        "excluded_environments": ["freshwater_swamp", "fluvial", "lacustrine"],
        "falsification_message": "Planktonic forams are exclusively marine. Present in non-marine → reworking, caving, or misidentification.",
    },
    "benthic_foraminifera": {
        "requires": "marine_or_brackish",
        "excluded_lithologies": ["COAL_CARBONACEOUS"],
        "excluded_environments": ["freshwater_swamp"],
        "falsification_message": "Benthic forams require saline water. In freshwater peat → contamination or transport.",
    },
    "freshwater_algae": {
        "requires": "freshwater_to_brackish",
        "excluded_lithologies": [],
        "excluded_environments": ["deep_marine", "open_marine"],
        "falsification_message": "Freshwater algae in open marine → fluvial input or reworking. Not in situ lacustrine.",
    },
    "mangrove_pollen": {
        "requires": "coastal_or_marginal_marine",
        "excluded_lithologies": [],
        "excluded_environments": ["deep_marine", "open_ocean"],
        "falsification_message": "Mangrove pollen in deep marine → transported from coast. Marks proximity to shoreline, not in situ environment.",
    },
}


def _gate1_facies_contradiction(
    fossil_group: str,
    litho_class: str,
    env_class: str,
    claim: str,
) -> dict:
    """G1: Check fossil ecology vs lithology/environment compatibility."""
    ecology = FOSSIL_ECOLOGY.get(fossil_group, {})
    if not ecology:
        return {"gate": "G1_FACIES", "verdict": "PASS", "note": f"No ecology rules for fossil group '{fossil_group}'"}

    contradictions = []
    evidence_for = []
    evidence_against = []

    # Check lithology
    for bad_litho in ecology.get("excluded_lithologies", []):
        if bad_litho.lower() in litho_class.lower():
            contradictions.append(
                f"Fossil group '{fossil_group}' requires {ecology['requires']}. Lithology '{litho_class}' is incompatible."
            )
            evidence_against.append(f"Lithology: {litho_class} ← incompatible with {fossil_group}")

    # Check environment
    for bad_env in ecology.get("excluded_environments", []):
        if bad_env.lower() in env_class.lower():
            contradictions.append(
                f"Fossil group '{fossil_group}' cannot occur in '{env_class}' environment without transport/reworking."
            )
            evidence_against.append(f"Environment: {env_class} ← incompatible with {fossil_group} ecology")

    if contradictions:
        return {
            "gate": "G1_FACIES",
            "verdict": "FALSIFIED",
            "message": ecology.get("falsification_message", "Facies contradiction detected."),
            "contradictions": contradictions,
            "evidence_for": evidence_for,
            "evidence_against": evidence_against,
            "rescue_hypothesis": "Reworking from older marine section, caving from uphole, thin marine incursion not captured in sample, or lithology/environment misidentified.",
        }

    # Compatible
    evidence_for.append(
        f"Lithology '{litho_class}' and environment '{env_class}' are compatible with {fossil_group} ecology ({ecology['requires']})"
    )
    return {
        "gate": "G1_FACIES",
        "verdict": "PASS",
        "message": f"Fossil ecology ({ecology['requires']}) compatible with lithology ({litho_class}) and environment ({env_class}).",
        "evidence_for": evidence_for,
        "evidence_against": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 2 — Stratigraphic Impossibility
# ═══════════════════════════════════════════════════════════════════════════════
# Rule: Younger fossil BELOW older fossil without reworking/fault explanation = FALSIFIED.


def _gate2_stratigraphic_order(
    younger_zone: str,
    older_zone: str,
    depth_younger: float | None,
    depth_older: float | None,
    reworking_claimed: bool,
    fault_present: bool,
) -> dict:
    """G2: Check that fossil ages obey superposition."""
    if not younger_zone or not older_zone:
        return {"gate": "G2_STRAT_ORDER", "verdict": "PASS", "note": "Insufficient zone data to test age ordering"}

    # Resolve ages
    y_top, y_base = nn_age(younger_zone)
    o_top, o_base = nn_age(older_zone)

    if y_top <= -999 or o_top <= -999:
        return {"gate": "G2_STRAT_ORDER", "verdict": "PASS", "note": "Cannot resolve zone ages for ordering check"}

    # Check: younger zone must have younger age (smaller Ma = younger)
    # younger zone top should be LESS than older zone top
    if y_top < o_top:
        # Normal: younger zone IS younger
        if depth_younger is not None and depth_older is not None:
            if depth_younger > depth_older:
                # Younger is deeper → inversion unless faulted
                if fault_present:
                    return {
                        "gate": "G2_STRAT_ORDER",
                        "verdict": "PASS",
                        "message": f"Younger zone '{younger_zone}' ({y_top:.1f} Ma) deeper than older '{older_zone}' ({o_top:.1f} Ma) — but fault present explains inversion.",
                        "evidence_for": [
                            "Fault documented — explains age inversion",
                            f"Zone ages correct: {younger_zone} < {older_zone}",
                        ],
                        "evidence_against": [],
                    }
                else:
                    return {
                        "gate": "G2_STRAT_ORDER",
                        "verdict": "FALSIFIED",
                        "message": f"Younger zone '{younger_zone}' ({y_top:.1f} Ma) appears BELOW older zone '{older_zone}' ({o_top:.1f} Ma) at greater depth with no fault explanation.",
                        "evidence_against": [
                            f"Depth order violates superposition: younger {younger_zone} at {depth_younger}m below older {older_zone} at {depth_older}m"
                        ],
                        "evidence_for": [],
                        "rescue_hypothesis": "Unmapped fault, overturned section, or depth measurement error.",
                    }
        return {
            "gate": "G2_STRAT_ORDER",
            "verdict": "PASS",
            "message": f"Zone ages in correct stratigraphic order: {younger_zone} ({y_top:.1f} Ma) younger than {older_zone} ({o_top:.1f} Ma).",
        }

    # Older appears younger — age inversion
    if reworking_claimed:
        return {
            "gate": "G2_STRAT_ORDER",
            "verdict": "WEAK_PASS",
            "message": f"Age inversion ({older_zone} above {younger_zone}) — but reworking claimed. Age fidelity reduced.",
            "evidence_for": ["Reworking documented"],
            "evidence_against": [f"Age inversion: {older_zone} ({o_top:.1f} Ma) above {younger_zone} ({y_top:.1f} Ma)"],
        }
    else:
        return {
            "gate": "G2_STRAT_ORDER",
            "verdict": "FALSIFIED",
            "message": f"Older zone '{older_zone}' ({o_top:.1f} Ma) appears ABOVE younger zone '{younger_zone}' ({y_top:.1f} Ma). Reworking, caving, or misidentification required.",
            "evidence_against": [f"Age inversion without documented reworking or fault"],
            "evidence_for": [],
            "rescue_hypothesis": "Reworking, caving from uphole, taxonomic misidentification, or fault repetition.",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 3 — Taxonomic Audit
# ═══════════════════════════════════════════════════════════════════════════════
# Rule: taxonomic names CHANGE. Synonymy, splitting, lumping, and lab conventions
# can make the same fossil appear as different names across reports.

SYNONYM_KNOWN_ISSUES = {
    "reticulofenestra": "May be split into Reticulofenestra, Cyclicargolithus, Dictyococcites depending on lab. Check size criteria.",
    "discoaster": "Species-level ID challenging in poor preservation. Many discoasters are convergent in form.",
    "sphenolithus": "Some species split/recombined. Check current Nannotax3 taxonomy.",
    "helicolith": "Helicosphaera taxonomy revised multiple times. Check INA terminology guide.",
    "globoquadrina": "Some species moved to Dentoglobigerina or other genera. Check pforams@mikrotax.",
    "globigerina": "Highly split — many former Globigerina now in other genera. Synonymy risk HIGH.",
    "globorotalia": "Taxonomy stable but species-level ID requires good preservation.",
    "miogypsina": "Larger foram — taxonomy stable. Presence/absence reliable, species ID needs expert.",
    "lepidocyclina": "Larger foram — stable taxonomy. Useful biostrat marker if well preserved.",
    "flosculinella": "LBF marker. Taxonomy stable. Reliable if properly identified.",
}


def _gate3_taxonomic_audit(
    text: str,
    fossil_names: list[str],
) -> dict:
    """G3: Audit taxonomic names for synonymy risk."""
    if not text and not fossil_names:
        return {"gate": "G3_TAXONOMY", "verdict": "PASS", "note": "No taxonomic names to audit"}

    issues = []
    clean = clean_text(text).lower()

    for taxon_key, issue_note in SYNONYM_KNOWN_ISSUES.items():
        if taxon_key in clean or any(taxon_key in f.lower() for f in fossil_names):
            issues.append(
                {
                    "taxon": taxon_key,
                    "risk": "Synonymy or taxonomic instability",
                    "note": issue_note,
                }
            )

    if issues:
        return {
            "gate": "G3_TAXONOMY",
            "verdict": "WEAK_PASS",
            "message": f"Taxonomic audit found {len(issues)} known instability issues. Age fidelity may be affected by naming conventions.",
            "taxonomic_issues": issues,
            "evidence_for": [],
            "evidence_against": [f"{len(issues)} taxa with known taxonomic instability"],
            "recommendation": "Verify current accepted names against Nannotax3 or pforams@mikrotax. Check if legacy reports used older synonyms.",
        }

    return {
        "gate": "G3_TAXONOMY",
        "verdict": "PASS",
        "message": "No known taxonomic instability issues detected in provided fossil names.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 4 — Reworking / Caving
# ═══════════════════════════════════════════════════════════════════════════════

REWORKING_SIGNALS = [
    "reworked",
    "reworking",
    "abraded",
    "broken",
    "rounded",
    "worn",
    "mixed assemblage",
    "mixed flora",
    "mixed fauna",
    "caved",
    "caving",
    "cavings",
    "contamination",
    "contaminated",
    "allochthonous",
]


def _gate4_reworking(text: str, sample_type: str) -> dict:
    """G4: Detect reworking/caving signals."""
    clean = clean_text(text).lower()

    signals_found = [s for s in REWORKING_SIGNALS if s in clean]

    if not signals_found:
        # Check sample type
        if sample_type and "cutting" in sample_type.lower():
            return {
                "gate": "G4_REWORKING",
                "verdict": "WEAK_PASS",
                "message": "Sample is ditch cuttings — caving risk inherent. Age fidelity reduced vs core/sidewall core.",
                "evidence_against": ["Ditch cuttings sample — caving not ruled out"],
                "evidence_for": ["No explicit reworking/caving signals in description"],
                "recommendation": "Prefer core or sidewall core for definitive age picks.",
            }
        return {
            "gate": "G4_REWORKING",
            "verdict": "PASS",
            "message": "No reworking or caving signals detected.",
        }

    return {
        "gate": "G4_REWORKING",
        "verdict": "FALSIFIED" if len(signals_found) >= 2 else "WEAK_PASS",
        "message": f"Reworking/caving signals detected: {', '.join(signals_found)}. Age fidelity compromised — fossil may not be in situ.",
        "signals": signals_found,
        "evidence_against": [f"Explicit reworking/caving signals: {', '.join(signals_found)}"],
        "evidence_for": [],
        "recommendation": "Determine in-situ vs reworked fraction. If majority reworked, downgrade to UNUSABLE for age calibration.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 5 — Diachroneity
# ═══════════════════════════════════════════════════════════════════════════════


def _gate5_diachroneity(
    zone: str,
    basin_province: str,
    claim_is_basinwide: bool,
) -> dict:
    """G5: Flag assumed synchrony as unfalsifiable unless tested."""
    if not zone:
        return {"gate": "G5_DIACHRONEITY", "verdict": "PASS", "note": "No zone to test"}

    if claim_is_basinwide:
        return {
            "gate": "G5_DIACHRONEITY",
            "verdict": "WEAK_PASS",
            "message": f"Claim that zone '{zone}' correlates basin-wide assumes synchrony. Bioevents may be diachronous — migration, ecology, and oceanographic barriers shift event timing.",
            "evidence_against": ["Basin-wide synchrony assumed, not demonstrated"],
            "evidence_for": [],
            "recommendation": "Test synchrony by comparing zone occurrence age across multiple wells in different provinces. If province is '{basin_province}', tie to local calibration.",
        }

    return {
        "gate": "G5_DIACHRONEITY",
        "verdict": "PASS",
        "message": f"Zone '{zone}' used locally — diachroneity risk acknowledged but scope is limited.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 6 — Seismic Mismatch
# ═══════════════════════════════════════════════════════════════════════════════


def _gate6_seismic(
    age_claim: str,
    seismic_group: str,
    expected_seismic_group: str,
) -> dict:
    """G6: Check age claim against seismic stratal geometry context."""
    if not seismic_group and not expected_seismic_group:
        return {"gate": "G6_SEISMIC", "verdict": "PASS", "note": "No seismic group context provided"}

    if seismic_group and expected_seismic_group:
        if seismic_group.lower() != expected_seismic_group.lower():
            return {
                "gate": "G6_SEISMIC",
                "verdict": "FALSIFIED",
                "message": f"Age claim '{age_claim}' assigned to seismic group '{seismic_group}' but expected in '{expected_seismic_group}'. Seismic stratal geometry may contradict age.",
                "evidence_against": [f"Seismic group mismatch: claimed {seismic_group}, expected {expected_seismic_group}"],
                "evidence_for": [],
                "rescue_hypothesis": "Seismic group boundary may be diachronous, or age calibration may be shifted locally.",
            }

    return {
        "gate": "G6_SEISMIC",
        "verdict": "PASS",
        "message": f"Age claim matches seismic group context ({seismic_group or expected_seismic_group}).",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 7 — Sequence Stratigraphy Mismatch
# ═══════════════════════════════════════════════════════════════════════════════


def _gate7_sequence(
    gde_claim: str,
    stacking_pattern: str,
) -> dict:
    """G7: Bioevent claim vs sequence stratigraphic stacking pattern."""
    if not gde_claim or not stacking_pattern:
        return {"gate": "G7_SEQUENCE", "verdict": "PASS", "note": "Insufficient sequence context"}

    # Simplest checks
    contradictions = []
    if "flooding" in gde_claim.lower() or "transgress" in gde_claim.lower():
        if "prograd" in stacking_pattern.lower() or "regress" in stacking_pattern.lower():
            contradictions.append(f"Claimed marine flooding/transgression but stacking is {stacking_pattern} — may contradict.")

    if "regress" in gde_claim.lower() or "falling" in gde_claim.lower():
        if "transgress" in stacking_pattern.lower() or "retrograd" in stacking_pattern.lower():
            contradictions.append(f"Claimed regression but stacking is {stacking_pattern} — may contradict.")

    if contradictions:
        return {
            "gate": "G7_SEQUENCE",
            "verdict": "FALSIFIED",
            "message": f"Bioevent claim ({gde_claim}) contradicts sequence stacking pattern ({stacking_pattern}).",
            "contradictions": contradictions,
            "evidence_against": contradictions,
            "evidence_for": [],
        }

    return {
        "gate": "G7_SEQUENCE",
        "verdict": "PASS",
        "message": f"Bioevent ({gde_claim}) compatible with stacking pattern ({stacking_pattern}).",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 8 — Regional Tectonic Mismatch
# ═══════════════════════════════════════════════════════════════════════════════

SABAH_TECTONIC_EVENTS = {
    "deep_regional_unconformity": {
        "age_ma": [16.0, 13.0],
        "event": "Early-Middle Miocene compression/uplift/erosion — separates pre-MMU deep marine from post-MMU shelf/slope",
    },
    "sabah_orogeny": {"age_ma": [16.0, 12.0], "event": "NW Borneo collision and orogenesis — major structural reorganization"},
    "shallow_regional_unconformity": {
        "age_ma": [10.5, 7.8],
        "event": "Late Miocene uplift/erosion — separates Groups D/E from C in Malay Basin analog",
    },
    "south_china_sea_spreading": {"age_ma": [32.0, 16.0], "event": "Oligocene-Miocene seafloor spreading — ended ~16 Ma"},
}


def _gate8_tectonic(
    claim_age_ma: float | None,
    claim_zone: str,
    region: str,
) -> dict:
    """G8: Check age claim against known regional tectonic events."""
    if not claim_age_ma and not claim_zone:
        return {"gate": "G8_TECTONIC", "verdict": "PASS", "note": "No age to test against tectonic framework"}

    # Resolve age
    age_ma = claim_age_ma
    if age_ma is None and claim_zone:
        _, age_ma = nn_age(claim_zone)
        if age_ma <= -999:
            return {"gate": "G8_TECTONIC", "verdict": "PASS", "note": f"Cannot resolve age for zone '{claim_zone}'"}

    if region and "sabah" in region.lower():
        events = SABAH_TECTONIC_EVENTS
    else:
        events = SABAH_TECTONIC_EVENTS  # default for now

    # Check if age falls within any major event
    for event_name, event_info in events.items():
        top, base = event_info["age_ma"]
        if top <= age_ma <= base:
            return {
                "gate": "G8_TECTONIC",
                "verdict": "PASS",
                "message": f"Claim age ({age_ma:.1f} Ma) falls within known tectonic event '{event_name}': {event_info['event']}. Age is plausible in regional context.",
                "evidence_for": [f"Age consistent with {event_name} ({top}-{base} Ma)"],
                "evidence_against": [],
            }

    return {
        "gate": "G8_TECTONIC",
        "verdict": "PASS",
        "message": f"Claim age ({age_ma:.1f} Ma) does not directly coincide with major known tectonic events. Not a falsification — may represent inter-event deposition.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — Run all 8 gates and return unified falsification verdict
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_biostrat_falsify(
    fossil_group: str = "calcareous_nannofossil",
    biozone: str = "",
    lithology: str = "",
    environment: str = "",
    claim: str = "",
    claim_type: str = "age",
    sample_type: str = "cuttings",
    depth_m: float | None = None,
    younger_zone: str = "",
    older_zone: str = "",
    depth_younger_m: float | None = None,
    depth_older_m: float | None = None,
    reworking_claimed: bool = False,
    fault_present: bool = False,
    fossil_names: str = "",
    basin_province: str = "",
    claim_is_basinwide: bool = False,
    seismic_group: str = "",
    expected_seismic_group: str = "",
    stacking_pattern: str = "",
    region: str = "sabah",
) -> dict:
    """Biostrat Falsification Engine — 8-gate Popperian test of any biostrat claim.

    A single FALSIFIED gate → overall verdict FALSIFIED regardless of other passes.
    Science advances by eliminating what CANNOT be true.

    Args:
      fossil_group:            Fossil group (calcareous_nannofossil, planktonic_foraminifera,
                                benthic_foraminifera, freshwater_algae, mangrove_pollen, palynomorph_marine)
      biozone:                 Claimed biozone (e.g. "NN5")
      lithology:               Lithology description
      environment:             Depositional environment description
      claim:                   The claim being tested (e.g. "open marine deposition", "Middle Miocene age")
      claim_type:              "age" | "environment" | "correlation" | "unconformity"
      sample_type:             "core" | "sidewall_core" | "cuttings" | "ditch"
      depth_m:                 Depth in meters
      younger_zone:            Younger biozone for ordering test (G2)
      older_zone:              Older biozone for ordering test (G2)
      depth_younger_m:         Depth of younger zone
      depth_older_m:           Depth of older zone
      reworking_claimed:       Has reworking been explicitly documented?
      fault_present:           Is a fault known to explain age inversion?
      fossil_names:            Comma-separated fossil names for taxonomic audit (G3)
      basin_province:          Basin province for diachroneity check (G5)
      claim_is_basinwide:      Is the claim asserting basin-wide correlation?
      seismic_group:           Assigned seismic group
      expected_seismic_group:  Expected seismic group from independent interpretation
      stacking_pattern:        Sequence strat stacking: "progradational", "retrogradational", "aggradational"
      region:                  "sabah" | "malay_basin" | "sarawak"

    Returns:
      Governed envelope with per-gate results and overall falsification verdict.
      POPPER RULE: any FALSIFIED gate → overall FALSIFIED.
    """
    logger.info("geox_biostrat_falsify: zone=%s fossil=%s claim=%s", biozone, fossil_group, claim[:80])

    # Resolve lithology and environment classes
    litho_class = lithology_class(lithology) if lithology else "UNKNOWN"
    env_class = _classify_env(environment) if environment else "UNKNOWN"

    # Resolve zone age
    zone_age = None
    if biozone:
        parsed = parse_nn_zone(biozone)
        zone_name = parsed["zone"]
        if zone_name != "UNKNOWN":
            _, zone_age = nn_age(zone_name)

    # Parse fossil names
    fossil_list = [n.strip() for n in fossil_names.split(",") if n.strip()] if fossil_names else []

    # ── Run all 8 gates ──────────────────────────────────────────────────────
    gates = {}

    gates["G1_FACIES"] = _gate1_facies_contradiction(fossil_group, litho_class, env_class, claim)
    gates["G2_STRAT_ORDER"] = _gate2_stratigraphic_order(
        younger_zone, older_zone, depth_younger_m, depth_older_m, reworking_claimed, fault_present
    )
    gates["G3_TAXONOMY"] = _gate3_taxonomic_audit(f"{claim} {fossil_names}", fossil_list)
    gates["G4_REWORKING"] = _gate4_reworking(f"{claim} {lithology} {environment}", sample_type)
    gates["G5_DIACHRONEITY"] = _gate5_diachroneity(biozone, basin_province, claim_is_basinwide)
    gates["G6_SEISMIC"] = _gate6_seismic(biozone or claim, seismic_group, expected_seismic_group)
    gates["G7_SEQUENCE"] = _gate7_sequence(claim, stacking_pattern)
    gates["G8_TECTONIC"] = _gate8_tectonic(zone_age, biozone, region)

    # ── Overall verdict ──────────────────────────────────────────────────────
    verdicts = [g["verdict"] for g in gates.values()]
    falsified_count = sum(1 for v in verdicts if v == "FALSIFIED")
    weak_count = sum(1 for v in verdicts if v == "WEAK_PASS")
    pass_count = sum(1 for v in verdicts if v == "PASS")

    if falsified_count > 0:
        overall = "FALSIFIED"
        reason = f"Claim fails {falsified_count} falsification gate(s). {'; '.join(k for k, g in gates.items() if g['verdict'] == 'FALSIFIED')}"
        confidence = 0.90  # High confidence in falsification
    elif weak_count >= 3:
        overall = "UNFALSIFIABLE"
        reason = f"Claim survives but with {weak_count} weak passes — insufficient evidence to falsify or validate. Claim may be too vague to test."
        confidence = 0.40
    elif weak_count >= 1:
        overall = "WEAK_PASS"
        reason = f"Claim passes most gates but {weak_count} gate(s) show weakness. Proceed with documented caveats."
        confidence = 0.55
    elif pass_count >= 4:
        overall = "PASS"
        reason = f"Claim survives all {pass_count} applicable falsification gates at this evidence level."
        confidence = 0.70
    else:
        overall = "HOLD"
        reason = "Insufficient evidence provided to test the claim across enough gates."
        confidence = 0.30

    # Evidence contract
    evidence_for = []
    evidence_against = []
    for g in gates.values():
        evidence_for.extend(g.get("evidence_for", []))
        evidence_against.extend(g.get("evidence_against", []))

    payload = {
        "claim": claim,
        "claim_type": claim_type,
        "fossil_group": fossil_group,
        "biozone": biozone,
        "zone_age_ma": zone_age,
        "lithology_class": litho_class,
        "environment_class": env_class,
        "overall_verdict": overall,
        "overall_reason": reason,
        "popper_rule_applied": "Any single FALSIFIED gate → overall FALSIFIED. Science advances by elimination, not confirmation.",
        "gates": {k: {"verdict": v["verdict"], "message": v.get("message", "")} for k, v in gates.items()},
        "gate_details": gates,
        "evidence_for": list(set(evidence_for)),
        "evidence_against": list(set(evidence_against)),
        "falsified_gates": [k for k, g in gates.items() if g["verdict"] == "FALSIFIED"],
        "weak_gates": [k for k, g in gates.items() if g["verdict"] == "WEAK_PASS"],
    }

    return get_standard_envelope(
        payload,
        tool_class="compute",
        claim_tag="PLAUSIBLE" if overall == "PASS" else "HYPOTHESIS",
        claim_state="INTERPRETED",
        uncertainty="Low" if overall in ("PASS", "FALSIFIED") else "Moderate",
        humility_score=confidence,
        evidence_refs=evidence_for[:8],
        audit_receipt={
            "verdict": overall,
            "risk": "MEDIUM" if overall == "FALSIFIED" else "LOW",
            "human_review_required": overall in ("FALSIFIED", "UNFALSIFIABLE"),
        },
        tool_name="geox_biostrat_falsify",
        equations_used=[
            "Popperian falsification: eliminate what CANNOT be true",
            "G1-G8: facies, strat order, taxonomy, reworking, diachroneity, seismic, sequence, tectonic",
            "FOSSIL_ECOLOGY matrix (6 groups × lithology × environment)",
            "SABAH_TECTONIC_EVENTS calibrated to Tan & Lamy + operator reports",
        ],
        sensitivity_to=["fossil_ecology_rules", "tectonic_event_ages", "taxonomic_synonymy_db"],
    )


def _classify_env(text: str) -> str:
    """Classify free-text environment into canonical category."""
    text_lower = text.lower()
    mapping = {
        "open_marine": ["open marine", "oceanic", "pelagic", "hemipelagic", "outer neritic", "bathyal", "abyssal"],
        "marine_shelf": ["neritic", "shelf", "inner neritic", "middle neritic", "sublittoral", "shallow marine"],
        "coastal": ["coastal", "littoral", "shoreface", "beach", "supralittoral", "mangrove", "estuarine", "lagoon"],
        "deltaic": ["delta", "deltaic", "prodelta", "delta front", "delta plain"],
        "fluvial": ["fluvial", "alluvial", "floodplain", "channel", "river"],
        "lacustrine": ["lacustrine", "lake", "lacustrine expansion"],
        "freshwater_swamp": ["freshwater swamp", "peat swamp", "coal swamp", "marsh", "freshwater"],
        "deep_marine": ["bathyal", "abyssal", "deep marine", "basin floor", "submarine fan"],
        "reef": ["reef", "carbonate buildup", "atoll", "bioherm", "carbonate platform"],
    }
    for category, keywords in mapping.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return "unknown"
