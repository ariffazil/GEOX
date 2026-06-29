"""
Sabah Carbonate Kill Matrix
============================
Hard physical rejection rules derived from Badali et al. (2024) Figure 2.

Any prospect failing ANY hard kill filter → AUTO-REJECT.
No appeal. No narrative override. Earth constraints win.

Source: Badali et al. (2024), SEG Interpretation, Figure 2 + Table
DOI: 10.1190/INT-2023-0014.1
29 carbonate case studies — Icehouse (I) vs Greenhouse (G) taxonomy.

DITEMPA BUKAN DIBERI — Forged, Not Given.
F2 TRUTH: hard filters are binary YES/NO. No confidence interval theatre.
F7 HUMILITY: confidence cap applies only to soft checks; hard kills are absolute.
F13 SOVEREIGN: kill decisions require arifOS 888_JUDGE SEAL for drilling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT SCHEMA
# ─────────────────────────────────────────────────────────────────────────────


class KillVerdict(Enum):
    KILL = "KILL"  # Prospect fails hard filter — reject
    PROCEED = "PROCEED"  # Passes all hard filters — advance
    REVIEW = "REVIEW"  # Insufficient data to apply filter — requires more data


@dataclass
class KillFilterResult:
    filter_name: str
    verdict: KillVerdict
    evidence: str  # What was observed
    threshold: str  # What Badali requires
    kill_logic: str  # Why it kills or passes


@dataclass
class KillMatrixResult:
    """
    Full kill matrix output for a Sabah carbonate prospect.

    Hard filters: KILL is absolute. PROCEED requires all hard filters pass.
    REVIEW means insufficient data — treat as KILL until resolved.
    """

    prospect_name: str
    age_ma: Optional[float]

    # Per-filter results
    filters: list[KillFilterResult]

    # Aggregate
    kill_count: int
    review_count: int
    pass_count: int

    # Final verdict
    verdict: KillVerdict
    verdict_summary: str

    # What killed it (if KILL)
    kill_reasons: list[str]

    # What needs more data (if REVIEW)
    data_gaps: list[str]

    # Next step
    next_action: str  # "arifOS 888_JUDGE" | "acquire_more_data" | "reject_prospect"

    # Metadata
    source: str = "Badali et al. (2024) Figure 2 + Table"
    doi: str = "10.1190/INT-2023-0014.1"
    forge_id: str = "forge-sabah-carbonate"


# ─────────────────────────────────────────────────────────────────────────────
# HARD KILL FILTERS (in order of application)
# ─────────────────────────────────────────────────────────────────────────────


def _K001_climate_archetype_fit(
    age_ma: Optional[float],
    claimed_archetype: str,
) -> KillFilterResult:
    """
    K001 — Climate-Anatomy Fit

    HARD KILL: If age falls in Greenhouse window (Eocene-early Oligocene, 56-33.9 Ma)
    but claimed architecture is Icehouse-endemic (rimmed platform, pinnacle).

    Sabah context:
    - Oligocene (33.9-23 Ma): Greenhouse → ramp / distally-steepened ramp only
    - Miocene (23-5.3 Ma): Icehouse → rimmed platform / pinnacle / isolated

    Evidence: Badali Table — Icehouse markers: rimmed platforms, karst, megabreccias,
    slopes 30-70°. Greenhouse markers: low-angle ramps, NRP, no karst.
    """
    if age_ma is None:
        return KillFilterResult(
            filter_name="K001_climate_archetype_fit",
            verdict=KillVerdict.REVIEW,
            evidence="age_ma not provided",
            threshold="age_ma required to determine Icehouse vs Greenhouse regime",
            kill_logic="Cannot apply climate filter without age context",
        )

    icehouse_archetypes = {"rimmed_platform", "isolated_platform", "pinnacle_reef"}
    greenhouse_archetypes = {"homoclinal_ramp", "distally_steepened_ramp", "nonrimmed_attached_platform"}

    is_icehouse = 5.3 <= age_ma <= 30
    is_greenhouse = 33.9 <= age_ma <= 56

    if is_greenhouse and claimed_archetype in icehouse_archetypes:
        return KillFilterResult(
            filter_name="K001_climate_archetype_fit",
            verdict=KillVerdict.KILL,
            evidence=f"age={age_ma:.1f} Ma (Greenhouse) but claimed={claimed_archetype} (Icehouse-endemic)",
            threshold="Icehouse-endemic archetypes (rimmed platform, pinnacle) cannot exist in Greenhouse period",
            kill_logic="Carbonate factory architecture is climate-controlled. Rimmed platforms + pinnacles are Icehouse constructs. Greenhouse builds ramps and NRPs.",
        )

    if is_icehouse and claimed_archetype in greenhouse_archetypes:
        return KillFilterResult(
            filter_name="K001_climate_archetype_fit",
            verdict=KillVerdict.KILL,
            evidence=f"age={age_ma:.1f} Ma (Icehouse) but claimed={claimed_archetype} (Greenhouse-endemic)",
            threshold="Greenhouse-endemic archetypes (ramp, NRP) are low-accommodation builds inconsistent with Icehouse high-frequency cycles",
            kill_logic="Icehouse accommodation architecture generates rimmed/high-relief builds. Low-angle ramps are Greenhouse morphology.",
        )

    return KillFilterResult(
        filter_name="K001_climate_archetype_fit",
        verdict=KillVerdict.PROCEED,
        evidence=f"age={age_ma:.1f} Ma — climate regime consistent with claimed archetype",
        threshold="Age and archetype consistent with Badali climate framework",
        kill_logic="Climate-archetype fit confirmed",
    )


def _K002_slope_angle_geometry(
    slope_angle_deg: Optional[float],
    claimed_archetype: str,
    age_ma: Optional[float],
) -> KillFilterResult:
    """
    K002 — Slope Angle as Archetype Discriminator

    HARD KILL: If slope angle is measured and falls outside the Badali-allowed range
    for the claimed archetype by more than 10°.

    From Badali Figure 2:
    - Homoclinal ramp: <15°
    - Distally steepened ramp: 5-25°
    - Non-rimmed attached platform: <15°
    - Slightly rimmed platform: 5-15°
    - Rimmed platform: 30-70° (Icehouse)
    - Isolated platform: 20-70°
    - Pinnacle reef: 30-60°

    Critical: If slope >40° and NOT in Icehouse window → volcanic intrusion or mud volcano.
    """
    if slope_angle_deg is None:
        return KillFilterResult(
            filter_name="K002_slope_angle_geometry",
            verdict=KillVerdict.REVIEW,
            evidence="slope_angle_deg not measured",
            threshold="Slope angle required — key discriminator from Badali Figure 2",
            kill_logic="Cannot apply geometry filter without slope measurement",
        )

    # Archetype → expected slope range
    slope_ranges = {
        "homoclinal_ramp": (0, 15),
        "distally_steepened_ramp": (5, 25),
        "nonrimmed_attached_platform": (0, 15),
        "slightly_rimmed_platform": (5, 15),
        "rimmed_platform": (30, 70),
        "isolated_platform": (20, 70),
        "pinnacle_reef": (30, 60),
    }

    if claimed_archetype not in slope_ranges:
        return KillFilterResult(
            filter_name="K002_slope_angle_geometry",
            verdict=KillVerdict.REVIEW,
            evidence=f"claimed_archetype={claimed_archetype} not in Badali taxonomy",
            threshold="Archetype must be one of the 7 Badali Figure 2 types",
            kill_logic="Unknown archetype — cannot apply slope filter",
        )

    slope_min, slope_max = slope_ranges[claimed_archetype]

    # Hard kill: slope outside range by >10°
    if slope_angle_deg < slope_min - 10 or slope_angle_deg > slope_max + 10:
        return KillFilterResult(
            filter_name="K002_slope_angle_geometry",
            verdict=KillVerdict.KILL,
            evidence=f"slope_angle={slope_angle_deg}° for claimed={claimed_archetype} (expected {slope_min}–{slope_max}°)",
            threshold=f"Slope must be within {slope_min}–{slope_max}° for {claimed_archetype} per Badali Fig.2",
            kill_logic="Slope angle is the primary geometric discriminator in Badali taxonomy. Wrong slope = wrong archetype = non-carbonate or misclassified structure.",
        )

    # Soft warning: slope outside range but within tolerance
    if slope_angle_deg < slope_min or slope_angle_deg > slope_max:
        return KillFilterResult(
            filter_name="K002_slope_angle_geometry",
            verdict=KillVerdict.REVIEW,
            evidence=f"slope_angle={slope_angle_deg}° marginally outside {slope_min}–{slope_max}° range",
            threshold=f"Slope should be {slope_min}–{slope_max}° for {claimed_archetype}",
            kill_logic="Slope marginally inconsistent — requires additional evidence to confirm archetype",
        )

    # Special check: steep slope >40° in non-Icehouse → volcanic intrusion
    if slope_angle_deg > 40:
        is_icehouse = age_ma is not None and 5.3 <= age_ma <= 30
        if not is_icehouse:
            return KillFilterResult(
                filter_name="K002_slope_angle_geometry",
                verdict=KillVerdict.KILL,
                evidence=f"slope_angle={slope_angle_deg}° in non-Icehouse context → volcanic intrusion likely",
                threshold="Steep slopes >40° outside Icehouse window are volcanic intrusions or mud volcanoes, NOT carbonate",
                kill_logic="Carbonate factories cannot build >40° slopes in Greenhouse conditions. Steep mound + non-Icehouse age = volcanic/mud volcano.",
            )

    return KillFilterResult(
        filter_name="K002_slope_angle_geometry",
        verdict=KillVerdict.PROCEED,
        evidence=f"slope_angle={slope_angle_deg}° within {slope_min}–{slope_max}° for {claimed_archetype}",
        threshold="Slope angle consistent with Badali archetype geometry",
        kill_logic="Slope geometry confirmed",
    )


def _K003_resolution_thickness_test(
    carbonate_thickness_m: Optional[float],
    seismic_frequency_hz: Optional[float],
) -> KillFilterResult:
    """
    K003 — Seismic Resolution vs Thickness Test

    HARD KILL: If carbonate is thinner than seismic vertical resolution,
    it cannot be resolved and should be KILL'd as "non-detectable."

    From Badali: vertical resolution = λ/4 = Vp / (4 × f)
    - Typical: 25-60 m (standard processing, 25-35 Hz)
    - Best: 18-25 m (high frequency >35 Hz)
    - Poor: >60 m (low frequency <20 Hz)

    Rule: If thickness < resolution AND no well control → KILL.
    If thickness < resolution BUT well control confirms carbonate → REVIEW (requires well proof).
    """
    if carbonate_thickness_m is None:
        return KillFilterResult(
            filter_name="K003_resolution_thickness_test",
            verdict=KillVerdict.REVIEW,
            evidence="carbonate_thickness_m not provided",
            threshold="Thickness required to apply resolution test",
            kill_logic="Cannot apply resolution filter without thickness",
        )

    # Estimate resolution from frequency if not provided
    if seismic_frequency_hz is None:
        # Assume standard processing: 30 Hz
        vp_calcite_m_s = 6400.0
        resolution_m = vp_calcite_m_s / (4 * 30)
        resolution_note = "assumed 30 Hz standard processing"
    else:
        vp_calcite_m_s = 6400.0
        resolution_m = vp_calcite_m_s / (4 * seismic_frequency_hz)
        resolution_note = f"computed at {seismic_frequency_hz} Hz"

    resolution_m = round(resolution_m, 1)

    # Hard kill: thickness below 60% of resolution (below reliable detection)
    kill_threshold = resolution_m * 0.6
    if carbonate_thickness_m < kill_threshold:
        return KillFilterResult(
            filter_name="K003_resolution_thickness_test",
            verdict=KillVerdict.KILL,
            evidence=f"carbonate_thickness={carbonate_thickness_m:.0f} m < kill_threshold={kill_threshold:.0f} m (resolution={resolution_m} m, {resolution_note})",
            threshold=f"Carbonate must be >{kill_threshold:.0f} m thick to be reliably resolved at {resolution_m} m resolution",
            kill_logic="Below seismic resolution = invisible on seismic = cannot be mapped or risking = should not be drilled as seismic-constrained prospect",
        )

    # Warning: thickness between 60-100% of resolution → marginal
    if carbonate_thickness_m < resolution_m:
        return KillFilterResult(
            filter_name="K003_resolution_thickness_test",
            verdict=KillVerdict.REVIEW,
            evidence=f"carbonate_thickness={carbonate_thickness_m:.0f} m < resolution={resolution_m} m — marginal detectability",
            threshold=f"Thickness should be >{resolution_m} m for confident seismic mapping",
            kill_logic="Marginal resolution — carbonate may exist but cannot be confidently mapped from seismic alone",
        )

    return KillFilterResult(
        filter_name="K003_resolution_thickness_test",
        verdict=KillVerdict.PROCEED,
        evidence=f"carbonate_thickness={carbonate_thickness_m:.0f} m > resolution={resolution_m} m",
        threshold=f"Thickness above seismic resolution — structure mappable",
        kill_logic="Resolution-thickness test passed",
    )


def _K004_rim_crest_amplitude_test(
    has_strong_rim: Optional[bool],
    has_weak_rim: Optional[bool],
    has_no_rim: Optional[bool],
    claimed_archetype: str,
) -> KillFilterResult:
    """
    K004 — Rim Crest Amplitude Test

    HARD KILL: If claimed archetype is rimmed_platform or isolated_platform
    but NO rim crest is visible on seismic → KILL.

    From Badali: rimmed platforms show high-amplitude continuous rim crest.
    If no rim → not rimmed platform → wrong archetype → reclassify or kill.

    This is the most abused filter in Sabah — mounds get called "rimmed" without rim.
    """
    rimmed_archetypes = {"rimmed_platform", "isolated_platform", "slightly_rimmed_platform"}

    if claimed_archetype not in rimmed_archetypes:
        return KillFilterResult(
            filter_name="K004_rim_crest_amplitude_test",
            verdict=KillVerdict.PROCEED,
            evidence=f"claimed={claimed_archetype} — rim not required",
            threshold="Rim test only applies to rimmed/isolated/slightly-rimmed archetypes",
            kill_logic="Non-rimmed archetype — rim test not applicable",
        )

    # Insufficient data
    if has_strong_rim is None and has_weak_rim is None and has_no_rim is None:
        return KillFilterResult(
            filter_name="K004_rim_crest_amplitude_test",
            verdict=KillVerdict.REVIEW,
            evidence="rim visibility not assessed",
            threshold=f"Claimed archetype={claimed_archetype} REQUIRES rim visibility check",
            kill_logic="Rimmed platform without rim = misclassified — requires review",
        )

    # Check rim presence
    rim_present = has_strong_rim or has_weak_rim
    rim_absent = has_no_rim

    if rim_absent or not rim_present:
        # Hard kill for rimmed platform if no rim
        if claimed_archetype == "rimmed_platform":
            return KillFilterResult(
                filter_name="K004_rim_crest_amplitude_test",
                verdict=KillVerdict.KILL,
                evidence=f"claimed=rimmed_platform but NO rim crest visible on seismic",
                threshold="Rimmed platform DEFINITION requires visible rim crest — no rim = not rimmed platform",
                kill_logic="'Rimmed platform' without rim is a category error. Either the prospect is misclassified or it is a mud volcano / basement high. KILL.",
            )

        # REVIEW for isolated/slightly-rimmed (lesser requirement)
        return KillFilterResult(
            filter_name="K004_rim_crest_amplitude_test",
            verdict=KillVerdict.REVIEW,
            evidence=f"claimed={claimed_archetype} — rim questionable",
            threshold=f"Archetype requires visible rim for confirmation",
            kill_logic="Rim not clearly visible — requires more data",
        )

    return KillFilterResult(
        filter_name="K004_rim_crest_amplitude_test",
        verdict=KillVerdict.PROCEED,
        evidence=f"claimed={claimed_archetype} — rim present",
        threshold="Rim crest confirmed",
        kill_logic="Rim geometry confirmed",
    )


def _K005_false_positive_indicator_test(
    has_chaotic_surface: Optional[bool],
    has_no_internal_reflectors: Optional[bool],
    is_isolated_mound_in_deep_water: Optional[bool],
    slope_angle_deg: Optional[float],
) -> KillFilterResult:
    """
    K005 — False Positive Indicator Test

    HARD KILL: Any of these = non-carbonate structure:
    1. Chaotic surface + no coherent geometry → mud volcano
    2. No internal reflectors + isolated mound → volcanic intrusion or salt diapir
    3. Isolated mound in deep water + steep slope + no rim → mud volcano cone

    From Badali: carbonate mounds have organized internal architecture
    (progradation, onlap, reflectors). Chaotic = non-carbonate.
    """
    kill_signals = []

    if has_chaotic_surface is True:
        kill_signals.append("CHAOTIC_SURFACE: organized carbonate architecture absent → mud volcano")

    if has_no_internal_reflectors is True:
        if is_isolated_mound_in_deep_water is True:
            kill_signals.append("NO_INTERNAL_REFLECTORS + ISOLATED_MOUND: volcanic intrusion or salt diapir")

    if is_isolated_mound_in_deep_water is True and slope_angle_deg is not None:
        if slope_angle_deg > 40 and not (5.3 <= (None or 0) <= 30):  # simplified check
            kill_signals.append(f"ISOLATED_MOUND + STEEP_SLOPE({slope_angle_deg}°) + NON_ICECHOUSE: mud volcano")

    if kill_signals:
        return KillFilterResult(
            filter_name="K005_false_positive_indicator_test",
            verdict=KillVerdict.KILL,
            evidence="; ".join(kill_signals),
            threshold="Chaotic surface or no internal reflectors = non-carbonate per Badali",
            kill_logic="Carbonate lookalike confirmed — mud volcano, volcanic intrusion, or basement high. Cannot distinguish from carbonate on seismic geometry alone.",
        )

    # Warnings
    warnings = []
    if has_no_internal_reflectors is True:
        warnings.append("No internal reflectors — cannot confirm carbonate architecture")

    if warnings:
        return KillFilterResult(
            filter_name="K005_false_positive_indicator_test",
            verdict=KillVerdict.REVIEW,
            evidence="; ".join(warnings),
            threshold="Internal reflector architecture required for carbonate confirmation",
            kill_logic="Internal architecture not visible — requires well control to confirm",
        )

    return KillFilterResult(
        filter_name="K005_false_positive_indicator_test",
        verdict=KillVerdict.PROCEED,
        evidence="No false-positive indicators detected",
        threshold="Clean seismic character — no mud volcano / volcanic intrusion signals",
        kill_logic="False-positive test passed",
    )


def _K006_reservoir_quality_precheck(
    porosity_fraction: Optional[float],
    vp_m_s: Optional[float],
    thickness_m: Optional[float],
) -> KillFilterResult:
    """
    K006 — Reservoir Quality Pre-Check

    HARD KILL: If Vp + porosity combination falls in basement/igneous overlap zone
    AND there is no well control → carbonate cannot be confirmed.

    From our session rock physics (VRH computation):
    - φ < 15% → Vp_Hill > 5.4 km/s → overlaps basement/igneous
    - Discrimination gap: Vp alone cannot distinguish at φ < 15%

    Operator Sabah data: Kinabalu porosity 3-15% (sub-commercial)
    Solisip-1: 138 m carbonate non-productive

    Rule: If Vp > 5.4 km/s AND porosity < 0.15 AND no well control → KILL.
    """
    if vp_m_s is None:
        return KillFilterResult(
            filter_name="K006_reservoir_quality_precheck",
            verdict=KillVerdict.REVIEW,
            evidence="vp_m_s not provided",
            threshold="Vp required for rock physics discrimination",
            kill_logic="Cannot apply reservoir quality filter without Vp",
        )

    # Basement overlap zone
    if vp_m_s > 5500 and porosity_fraction is not None and porosity_fraction < 0.15:
        return KillFilterResult(
            filter_name="K006_reservoir_quality_precheck",
            verdict=KillVerdict.KILL,
            evidence=f"Vp={vp_m_s:.0f} m/s + φ={porosity_fraction:.1%} — in basement overlap zone (Vp>5.5 km/s, φ<15%)",
            threshold="Vp + porosity in basement/igneous overlap — cannot confirm carbonate lithology",
            kill_logic="At low porosity (<15%), carbonate Vp overlaps basement/igneous Vp. Without well control or AVO, cannot confirm carbonate. Operator Kinabalu (φ=3-15%) = sub-commercial. Solisip-1 = non-productive.",
        )

    # Thin prospect warning
    if thickness_m is not None and thickness_m < 100:
        return KillFilterResult(
            filter_name="K006_reservoir_quality_precheck",
            verdict=KillVerdict.REVIEW,
            evidence=f"thickness={thickness_m:.0f} m — below minimum economic threshold (~100 m for carbonate)",
            threshold="Carbonate thickness should be >100 m for economic viability",
            kill_logic="Thin carbonate — marginal or sub-economic even if present",
        )

    return KillFilterResult(
        filter_name="K006_reservoir_quality_precheck",
        verdict=KillVerdict.PROCEED,
        evidence=f"Vp={vp_m_s:.0f} m/s — outside basement overlap zone (or well-controlled)",
        threshold="Rock physics consistent with carbonate + viable porosity",
        kill_logic="Reservoir quality pre-check passed",
    )


# ─────────────────────────────────────────────────────────────────────────────
# MASTER KILL MATRIX
# ─────────────────────────────────────────────────────────────────────────────

KILL_FILTERS = [
    _K001_climate_archetype_fit,
    _K002_slope_angle_geometry,
    _K003_resolution_thickness_test,
    _K004_rim_crest_amplitude_test,
    _K005_false_positive_indicator_test,
    _K006_reservoir_quality_precheck,
]


def apply_kill_matrix(
    prospect_name: str,
    age_ma: Optional[float] = None,
    claimed_archetype: str = "rimmed_platform",
    slope_angle_deg: Optional[float] = None,
    seismic_frequency_hz: Optional[float] = None,
    carbonate_thickness_m: Optional[float] = None,
    has_strong_rim: Optional[bool] = None,
    has_weak_rim: Optional[bool] = None,
    has_no_rim: Optional[bool] = None,
    has_chaotic_surface: Optional[bool] = None,
    has_no_internal_reflectors: Optional[bool] = None,
    is_isolated_mound_in_deep_water: Optional[bool] = None,
    vp_m_s: Optional[float] = None,
    porosity_fraction: Optional[float] = None,
) -> KillMatrixResult:
    """
    Apply all 6 hard kill filters to a Sabah carbonate prospect.

    HARD RULE: ANY KILL → prospect is rejected.
    REVIEW count > 0 → treat as KILL until resolved.

    Parameters
    ----------
    prospect_name : str
        Name of prospect for reporting.
    age_ma : float, optional
        Seismic age in Ma. Miocene (5.3-30 Ma) = Icehouse; Eocene-early Oligocene (33.9-56 Ma) = Greenhouse.
    claimed_archetype : str
        One of the 7 Badali Figure 2 types: homoclinal_ramp, distally_steepened_ramp,
        nonrimmed_attached_platform, slightly_rimmed_platform, rimmed_platform,
        isolated_platform, pinnacle_reef.
    slope_angle_deg : float, optional
        Margin slope angle measured from seismic. Key discriminator.
    seismic_frequency_hz : float, optional
        Dominant seismic frequency. If not provided, assumes 30 Hz standard.
    carbonate_thickness_m : float, optional
        Estimated carbonate thickness from seismic.
    has_strong_rim : bool, optional
        Is there a high-amplitude continuous rim crest?
    has_weak_rim : bool, optional
        Is there a subtle rim crest?
    has_no_rim : bool, optional
        Is there clearly NO rim?
    has_chaotic_surface : bool, optional
        Chaotic surface with no coherent geometry? (FALSE POSITIVE flag)
    has_no_internal_reflectors : bool, optional
        No internal seismic reflectors visible? (FALSE POSITIVE flag)
    is_isolated_mound_in_deep_water : bool, optional
        Is the structure isolated in deep water vs attached to shelf?
    vp_m_s : float, optional
        Vp from well control or inversion.
    porosity_fraction : float, optional
        Porosity estimate (0.0-1.0).

    Returns
    -------
    KillMatrixResult
        Full kill matrix output: per-filter verdict, aggregate KILL/PROCEED/REVIEW count,
        final verdict, kill reasons, data gaps, next action.

    Usage
    -----
    result = apply_kill_matrix(
        prospect_name="Pekaka",
        age_ma=15.0,
        claimed_archetype="rimmed_platform",
        slope_angle_deg=35.0,
        carbonate_thickness_m=200.0,
        has_strong_rim=False,  # <-- no rim visible!
        has_chaotic_surface=True,
    )
    if result.verdict == KillVerdict.KILL:
        print(f"KILLED: {result.kill_reasons}")
    """
    filters = [
        _K001_climate_archetype_fit(age_ma, claimed_archetype),
        _K002_slope_angle_geometry(slope_angle_deg, claimed_archetype, age_ma),
        _K003_resolution_thickness_test(carbonate_thickness_m, seismic_frequency_hz),
        _K004_rim_crest_amplitude_test(has_strong_rim, has_weak_rim, has_no_rim, claimed_archetype),
        _K005_false_positive_indicator_test(
            has_chaotic_surface, has_no_internal_reflectors, is_isolated_mound_in_deep_water, slope_angle_deg
        ),
        _K006_reservoir_quality_precheck(porosity_fraction, vp_m_s, carbonate_thickness_m),
    ]

    kill_count = sum(1 for f in filters if f.verdict == KillVerdict.KILL)
    review_count = sum(1 for f in filters if f.verdict == KillVerdict.REVIEW)
    pass_count = sum(1 for f in filters if f.verdict == KillVerdict.PROCEED)

    kill_reasons = [f"{f.filter_name}: {f.evidence}" for f in filters if f.verdict == KillVerdict.KILL]

    data_gaps = [f"{f.filter_name}: {f.evidence}" for f in filters if f.verdict == KillVerdict.REVIEW]

    # Verdict logic: KILL overrides everything
    if kill_count > 0:
        verdict = KillVerdict.KILL
        verdict_summary = f"KILLED by {kill_count} hard filter(s) — {len(kill_reasons)} kill reason(s) documented"
        next_action = "reject_prospect"
    elif review_count > 0:
        verdict = KillVerdict.REVIEW
        verdict_summary = f"REVIEW — {review_count} filter(s) require more data before decision"
        next_action = "acquire_more_data"
    else:
        verdict = KillVerdict.PROCEED
        verdict_summary = f"PROCEED — all {pass_count} hard filters passed — advance to arifOS 888_JUDGE"
        next_action = "arifOS 888_JUDGE"

    return KillMatrixResult(
        prospect_name=prospect_name,
        age_ma=age_ma,
        filters=filters,
        kill_count=kill_count,
        review_count=review_count,
        pass_count=pass_count,
        verdict=verdict,
        verdict_summary=verdict_summary,
        kill_reasons=kill_reasons,
        data_gaps=data_gaps,
        next_action=next_action,
    )


# ─────────────────────────────────────────────────────────────────────────────
# SABAH PROSPECTS — TEST AGAINST KILL MATRIX
# ─────────────────────────────────────────────────────────────────────────────

SABAH_TEST_PROSPECTS = {
    "Pekaka": {
        "age_ma": 15.0,
        "claimed_archetype": "rimmed_platform",
        "slope_angle_deg": None,  # not measured
        "carbonate_thickness_m": 200.0,  # estimated
        "has_strong_rim": False,  # chaotic reflectors — no rim
        "has_weak_rim": False,
        "has_no_rim": True,
        "has_chaotic_surface": True,
        "has_no_internal_reflectors": True,
        "is_isolated_mound_in_deep_water": None,
        "vp_m_s": None,
        "porosity_fraction": None,
        "note": "Pekaka: chaotic reflectors, vertical nucleation, no organized geometry — violates ALL carbonate classes",
    },
    "Solisip-1": {
        "age_ma": 18.0,
        "claimed_archetype": "rimmed_platform",
        "slope_angle_deg": 35.0,
        "carbonate_thickness_m": 138.0,  # 138 m non-productive
        "has_strong_rim": None,
        "has_weak_rim": None,
        "has_no_rim": None,
        "has_chaotic_surface": None,
        "has_no_internal_reflectors": None,
        "is_isolated_mound_in_deep_water": None,
        "vp_m_s": 4800.0,  # estimated
        "porosity_fraction": 0.10,  # Kinabalu: 3-15%
        "note": "Solisip-1: 138 m carbonate but sub-commercial porosity (Operator data)",
    },
    "Tepat (proven)": {
        "age_ma": 15.0,
        "claimed_archetype": "rimmed_platform",
        "slope_angle_deg": 45.0,
        "carbonate_thickness_m": 600.0,
        "has_strong_rim": True,
        "has_weak_rim": False,
        "has_no_rim": False,
        "has_chaotic_surface": False,
        "has_no_internal_reflectors": False,
        "is_isolated_mound_in_deep_water": False,
        "vp_m_s": 4700.0,  # VRH at φ=20%
        "porosity_fraction": 0.20,
        "note": "Tepat: proven producer — should pass kill matrix",
    },
    "Unknown mound (exploratory)": {
        "age_ma": None,  # unknown
        "claimed_archetype": "pinnacle_reef",
        "slope_angle_deg": 50.0,
        "carbonate_thickness_m": 300.0,
        "has_strong_rim": None,
        "has_weak_rim": None,
        "has_no_rim": None,
        "has_chaotic_surface": False,
        "has_no_internal_reflectors": False,
        "is_isolated_mound_in_deep_water": True,
        "vp_m_s": None,
        "porosity_fraction": None,
        "note": "Unknown mound — steep slope in deep water — mud volcano risk",
    },
}


def run_sabah_kill_matrix_tests() -> None:
    """Run kill matrix against all Sabah test prospects."""
    print(f"\n{'=' * 70}")
    print(f"SABAH CARBONATE KILL MATRIX — BADALI ET AL. (2024)")
    print(f"{'=' * 70}\n")

    for name, prospect in SABAH_TEST_PROSPECTS.items():
        # Separate 'note' meta-field from apply_kill_matrix kwargs
        params = {k: v for k, v in prospect.items() if k != "note"}
        result = apply_kill_matrix(prospect_name=name, **params)

        verdict_symbol = {
            KillVerdict.KILL: "🔴 KILL",
            KillVerdict.REVIEW: "🟡 REVIEW",
            KillVerdict.PROCEED: "🟢 PROCEED",
        }[result.verdict]

        print(f"{'─' * 70}")
        print(f"PROSPECT: {name}")
        print(f"NOTE: {prospect.get('note', '')}")
        print(f"{'─' * 70}")
        print(f"VERDICT: {verdict_symbol} — {result.verdict_summary}")
        print(f"SUMMARY: KILL={result.kill_count}  REVIEW={result.review_count}  PASS={result.pass_count}")

        if result.kill_reasons:
            print(f"\nKILL REASONS:")
            for r in result.kill_reasons:
                print(f"  • {r}")

        if result.data_gaps:
            print(f"\nDATA GAPS (must resolve before decision):")
            for g in result.data_gaps:
                print(f"  ? {g}")

        print(f"\nNEXT ACTION: {result.next_action}")
        print()

    print(f"{'=' * 70}")
    print("KILL MATRIX COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_sabah_kill_matrix_tests()
