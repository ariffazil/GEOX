"""
GEOX Well Stratigraphy — L3: Generalized Sequence Stratigraphy Inference
═══════════════════════════════════════════════════════════════════════════════

Assigns systems tract per geological package based on:
  - GR motif (observational)
  - Depositional environment rank (water depth proxy)
  - GR mean value
  - Package thickness
  - Variability

Returns (tract_code, process_description).
UNCERTAIN is allowed for interpretive tracks — UNKNOWN is not (per BPSSB governance).

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any, Optional

from .config import default_depo_rank


def infer_seq_strat(
    pkg: dict[str, Any],
    depo_code: str,
    depo_rank: Optional[dict[str, int]] = None,
) -> tuple[str, str]:
    """
    Assign systems tract per package based on motif + depo env + GR.

    Parameters
    ----------
    pkg : dict
        Geological package from build_packages().
    depo_code : str
        Depositional environment code (e.g. "HIN", "UBT", "COL").
    depo_rank : dict, optional
        Rank mapping for depo codes. Defaults to DEFAULT_DEPO_RANK.

    Returns
    -------
    tuple[str, str]: (tract_code, process_description)
    """
    rank_map = depo_rank or default_depo_rank()
    motif = pkg.get("HUMAN_MOTIF", "Heterolithic")
    gr = pkg.get("GR_MEAN") or 80.0
    thick = pkg.get("THICKNESS", 0)
    rank = rank_map.get(str(depo_code).strip(), 5)
    pkg.get("VARIABILITY", "Moderate")

    # Condensed section: thin, high-GR, deep water
    if gr > 95 and thick < 70 and rank >= 8:
        return ("CS", "Condensed section — MFS candidate; hemipelagic drape above maximum flooding surface")

    # LST: clean blocky sand in bathyal = turbidite fan / lowstand
    if motif == "Blocky" and gr < 60 and rank >= 7:
        return ("LST", "Lowstand turbidite fan/lobe — clean blocky sand in deep-water; sand deliverer during sea-level fall")

    # TST: Fining Upward in marine = retrogradational flooding
    if motif == "Fining Upward" and rank >= 3:
        return ("TST", "Transgressive systems tract — retrograding succession; accommodation creation exceeds sediment supply")

    # HST: Coarsening Upward in shallow = prograding highstand
    if motif == "Coarsening Upward" and rank <= 7:
        return ("HST", "Highstand systems tract — prograding shallowing-upward succession; sediment supply exceeds accommodation")

    # FSST: Coarsening Upward in deep setting = falling-stage turbidite lobe
    if motif == "Coarsening Upward" and rank >= 8:
        return ("FSST", "Falling stage systems tract — prograding turbidite lobe; forced regression into deep water")

    # Blocky in shallow = aggradational HST or TST
    if motif == "Blocky" and rank <= 5:
        return ("HST", "Aggradational highstand — constant accommodation; shoreface or shelf amalgamated sand")

    # Serrated in deep water = slope apron / condensed
    if motif == "Serrated / Irregular Pattern" and rank >= 8:
        if gr > 90:
            return ("CS", "Hemipelagic/pelagic drape — condensed; minimal clastic supply to deep water")
        return ("UNCERTAIN", "Heterolithic slope apron — systems tract uncertain; mixed turbidite and hemipelagic signal")

    # Serrated in proximal = heterolithic coastal / tidal
    if motif == "Serrated / Irregular Pattern" and rank <= 4:
        return ("UNCERTAIN", "Heterolithic coastal/tidal plain — high-frequency cyclicity; possibly transgressive lagoonal")

    # Heterolithic fallback: assign by depth of water only
    if motif == "Heterolithic":
        if rank >= 8:
            return (
                "UNCERTAIN",
                "Heterolithic interval in deep water — mixed turbidite/hemipelagic; "
                "insufficient GR geometry to determine systems tract",
            )
        return ("UNCERTAIN", "Heterolithic interval — high-frequency GR oscillation; tidal/coastal cyclicity or data gap")

    return ("UNCERTAIN", "GR geometry does not uniquely satisfy any single systems tract rule")


def geo_rule_check(
    pkg: dict[str, Any],
    depo_code: str,
    depo_rank: Optional[dict[str, int]] = None,
) -> str:
    """Check for geological anomalies. Returns flag string or PASS."""
    rank_map = depo_rank or default_depo_rank()
    pkg.get("HUMAN_MOTIF", "")
    rider = pkg.get("RIDER_MOTIF", "")
    gr_mean = pkg.get("GR_MEAN") or 80.0
    rank = rank_map.get(str(depo_code).strip(), 5)

    flags = []
    if rider == "Cylindrical" and gr_mean < 55 and rank >= 8:
        flags.append("TURBIDITE_CANDIDATE")
    if rider in ("Serrated", "High_GR_Shale") and gr_mean > 90 and rank <= 3:
        flags.append("FLOODING_SURFACE_CANDIDATE")
    if rider == "Funnel" and rank >= 8:
        flags.append("TURBIDITE_LOBE_PROGRADING")
    return ";".join(flags) if flags else "PASS"


def litho_classify(gr_mean: Optional[float], cut_sand=35, cut_silt=65, cut_shaly=90) -> str:
    """Classify lithology from GR mean."""
    if gr_mean is None:
        return "Heterolithic"
    g = float(gr_mean)
    if g < cut_sand:
        return "Clean Sand"
    if g < cut_silt:
        return "Silty Sand"
    if g < cut_shaly:
        return "Shaly Sand"
    return "Shale"
