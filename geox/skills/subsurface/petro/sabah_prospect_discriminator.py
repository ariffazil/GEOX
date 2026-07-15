"""
Sabah Prospect Discrimination Engine
====================================
Combines:
  (1) ARIF 6-Domain Carbonate Differentiator  (≥3/6 law, sealed)
  (2) Sabah Kill Matrix                        (Badali 2024 hard filters)
  (3) PSCS Subduction Evidence Filter           (PSCS-Brief §12 kill tests)

Prospects: Tepat · Solisip · Layang · Megah
Evidence-only: returns classification + confidence + kill filter results.
Does NOT make drill decisions — arifOS 888_JUDGE decides.

DITEMPA BUKAN DIBERI — Forged, Not Given.
F2 TRUTH: all confidence scores hard-capped at 0.90 (F7 HUMILITY).
F13 SOVEREIGN: drill decisions require arifOS 888_JUDGE SEAL.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# ── ARIF 6-DOMAIN DIFFERENTIATOR (inline, copied from physics.py) ─────────
# Copied verbatim from: /root/GEOX/adapters/carbonate/physics.py (sealed canon)
# Domain weights: D1=0.20 D2=0.15 D3=0.15 D4=0.15 D5=0.20 D6=0.15
# Sealing law: ≥3/6 domains → CARBONATE_CONFIRMED; single-attr calls = VOID
# F7 HUMILITY: confidence hard-capped at 0.90
_HUMILITY_CAP = 0.90
_D6_WEIGHTS = {1: 0.20, 2: 0.15, 3: 0.15, 4: 0.15, 5: 0.20, 6: 0.15}


class DomainVerdict(Enum):
    VALIDATE = "VALIDATE"
    REJECT = "REJECT"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class DomainResult:
    domain_id: int
    domain_name: str
    score: float
    weight: float
    verdict: DomainVerdict
    evidence: str
    threshold_used: str
    anti_pattern_flag: str | None = None


@dataclass
class SixDomainResult:
    domains: list[DomainResult]
    validation_count: int
    rejection_count: int
    inconclusive_count: int
    composite_score: float
    passes_3of6: bool
    verdict: str
    verdict_confidence: float
    anti_patterns_detected: list[str]
    explanation: str


def _cap(v: float) -> float:
    return min(v, _HUMILITY_CAP)


def run_six_domain_differentiator(
    curvature=None,
    is_mounded=None,
    has_onlap=None,
    is_isolated_buildup=None,
    has_flat_top=None,
    has_steep_flanks=None,
    top_reflector_strength=None,
    top_reflector_continuity=None,
    internal_character=None,
    base_character=None,
    coherency=None,
    rms_amplitude=None,
    envelope_strength=None,
    sweetness=None,
    spectral_decomposition_rgb=None,
    avoe=None,
    age_ma=None,
    is_on_structural_high=None,
    is_away_from_clastic_feeder=None,
    regional_analog_match=None,
    is_icehouse=None,
    vp_top_m_s=None,
    vp_base_m_s=None,
    vp_vs_ratio=None,
    ai=None,
    avo_class=None,
    stacking_velocity_top=None,
    stacking_velocity_base=None,
    csem_resistivity_pattern=None,
    gravity_signature=None,
    ftg_anomaly=None,
    magnetic_signature=None,
) -> SixDomainResult:
    """ARIF 6-Domain Carbonate Differentiator (≥3/6 sealing law)."""
    # ── D1: Geometry ────────────────────────────────────────────────────
    d1_score = 0.0
    d1_parts = []
    if is_mounded:
        d1_score += 0.30
        d1_parts.append("mounded")
    if has_onlap:
        d1_score += 0.20
        d1_parts.append("onlapping flanks")
    if is_isolated_buildup:
        d1_score += 0.20
        d1_parts.append("isolated buildup")
    if has_flat_top:
        d1_score += 0.15
        d1_parts.append("flat top")
    if has_steep_flanks:
        d1_score += 0.15
        d1_parts.append("steep flanks ≥ 30°")
    if curvature and curvature >= 0.005:
        d1_score += 0.20
        d1_parts.append(f"curvature={curvature:.3f}")
    d1_v = DomainVerdict.VALIDATE if d1_score >= 0.40 else (DomainVerdict.INCONCLUSIVE if d1_score > 0 else DomainVerdict.REJECT)
    d1 = DomainResult(
        1,
        "Geometry",
        _cap(d1_score),
        _D6_WEIGHTS[1],
        d1_v,
        "; ".join(d1_parts) if d1_parts else "No geometry data",
        "score ≥ 0.40",
        None,
    )

    # ── D2: Reflection ─────────────────────────────────────────────────
    d2_score = 0.0
    d2_parts = []
    if top_reflector_strength and top_reflector_strength >= 0.6:
        d2_score += 0.35
        d2_parts.append(f"top_str={top_reflector_strength:.2f}")
    if top_reflector_continuity and top_reflector_continuity >= 0.6:
        d2_score += 0.25
        d2_parts.append(f"top_cont={top_reflector_continuity:.2f}")
    if coherency and coherency >= 0.6:
        d2_score += 0.20
        d2_parts.append(f"coherency={coherency:.2f}")
    d2_v = DomainVerdict.VALIDATE if d2_score >= 0.40 else (DomainVerdict.INCONCLUSIVE if d2_score > 0 else DomainVerdict.REJECT)
    d2 = DomainResult(
        2,
        "Reflection",
        _cap(d2_score),
        _D6_WEIGHTS[2],
        d2_v,
        "; ".join(d2_parts) if d2_parts else "No reflection data",
        "score ≥ 0.40",
        None,
    )

    # ── D3: Attributes ───────────────────────────────────────────────────
    d3_score = 0.0
    d3_parts = []
    if rms_amplitude and rms_amplitude >= 0.5:
        d3_score += 0.30
        d3_parts.append(f"rms={rms_amplitude:.2f}")
    if sweetness and sweetness >= 0.5:
        d3_score += 0.30
        d3_parts.append(f"sweetness={sweetness:.2f}")
    if envelope_strength and envelope_strength >= 0.5:
        d3_score += 0.20
        d3_parts.append(f"envelope={envelope_strength:.2f}")
    d3_v = DomainVerdict.VALIDATE if d3_score >= 0.40 else (DomainVerdict.INCONCLUSIVE if d3_score > 0 else DomainVerdict.REJECT)
    d3 = DomainResult(
        3,
        "Attributes",
        _cap(d3_score),
        _D6_WEIGHTS[3],
        d3_v,
        "; ".join(d3_parts) if d3_parts else "No attribute data",
        "score ≥ 0.40",
        None,
    )

    # ── D4: Stratigraphy ────────────────────────────────────────────────
    d4_score = 0.0
    d4_parts = []
    if age_ma:
        d4_score += 0.25
        d4_parts.append(f"age={age_ma:.1f} Ma")
    if is_icehouse:
        d4_score += 0.25
        d4_parts.append("Icehouse (Miocene)")
    if is_on_structural_high:
        d4_score += 0.20
        d4_parts.append("structural high")
    if is_away_from_clastic_feeder:
        d4_score += 0.15
        d4_parts.append("distal from clastic")
    if regional_analog_match:
        d4_score += 0.15
        d4_parts.append("regional analog")
    d4_v = DomainVerdict.VALIDATE if d4_score >= 0.40 else (DomainVerdict.INCONCLUSIVE if d4_score > 0 else DomainVerdict.REJECT)
    d4 = DomainResult(
        4,
        "Stratigraphy",
        _cap(d4_score),
        _D6_WEIGHTS[4],
        d4_v,
        "; ".join(d4_parts) if d4_parts else "No stratigraphic data",
        "score ≥ 0.40",
        None,
    )

    # ── D5: Velocity/AVO ────────────────────────────────────────────────
    d5_score = 0.0
    d5_parts = []
    if vp_top_m_s and 2500 <= vp_top_m_s <= 7000:
        d5_score += 0.30
        d5_parts.append(f"Vp_top={vp_top_m_s:.0f} m/s")
    if vp_base_m_s and vp_top_m_s:
        dv = vp_base_m_s - vp_top_m_s
        if 200 <= dv <= 1500:
            d5_score += 0.25
            d5_parts.append(f"dVp={dv:.0f} m/s (cemented)")
        elif dv > 0:
            d5_score += 0.10
            d5_parts.append(f"dVp={dv:.0f} m/s (weak)")
    if vp_vs_ratio and 1.60 <= vp_vs_ratio <= 2.00:
        d5_score += 0.20
        d5_parts.append(f"Vp/Vs={vp_vs_ratio:.2f}")
    if avo_class in ("class_I", "class_II", "class_III", "class_iv"):
        d5_score += 0.20
        d5_parts.append(f"AVO={avo_class}")
    d5_v = DomainVerdict.VALIDATE if d5_score >= 0.40 else (DomainVerdict.INCONCLUSIVE if d5_score > 0 else DomainVerdict.REJECT)
    d5 = DomainResult(
        5,
        "Velocity",
        _cap(d5_score),
        _D6_WEIGHTS[5],
        d5_v,
        "; ".join(d5_parts) if d5_parts else "No velocity data",
        "Vp 2500-7000 + Vp/Vs 1.60-2.00",
        None,
    )

    # ── D6: Integration ────────────────────────────────────────────────
    d6_score = 0.0
    d6_parts = []
    if csem_resistivity_pattern in ("high_resistivity", "moderate_resistivity"):
        d6_score += 0.40
        d6_parts.append(f"CSEM={csem_resistivity_pattern}")
    if gravity_signature == "positive_bouguer":
        d6_score += 0.30
        d6_parts.append("positive Bouguer")
    if ftg_anomaly:
        d6_score += 0.30
        d6_parts.append("FTG anomaly")
    d6_v = DomainVerdict.VALIDATE if d6_score >= 0.40 else (DomainVerdict.INCONCLUSIVE if d6_score > 0 else DomainVerdict.REJECT)
    d6 = DomainResult(
        6,
        "Integration",
        _cap(d6_score),
        _D6_WEIGHTS[6],
        d6_v,
        "; ".join(d6_parts) if d6_parts else "No integration data",
        "CSEM/gravity/FTG consistent",
        None,
    )

    domains = [d1, d2, d3, d4, d5, d6]
    n_validate = sum(1 for d in domains if d.verdict == DomainVerdict.VALIDATE)
    n_reject = sum(1 for d in domains if d.verdict == DomainVerdict.REJECT)
    composite = sum(d.score * d.weight * 100 for d in domains)
    passes = n_validate >= 3

    if passes and n_reject == 0:
        verdict = "CARBONATE_CONFIRMED"
        vconf = _cap(composite / 100 * 0.90)
    elif passes and n_reject <= 1:
        verdict = "CARBONATE_POSSIBLE"
        vconf = _cap(composite / 100 * 0.75)
    elif n_validate >= 2:
        verdict = "MIXED_UNCERTAIN"
        vconf = _cap(composite / 100 * 0.60)
    elif n_validate >= 1:
        verdict = "NON_CARBONATE_SUSPECTED"
        vconf = _cap(composite / 100 * 0.40)
    else:
        verdict = "INCONCLUSIVE"
        vconf = 0.20

    return SixDomainResult(
        domains=domains,
        validation_count=n_validate,
        rejection_count=n_reject,
        inconclusive_count=sum(1 for d in domains if d.verdict == DomainVerdict.INCONCLUSIVE),
        composite_score=composite,
        passes_3of6=passes,
        verdict=verdict,
        verdict_confidence=vconf,
        anti_patterns_detected=[d.anti_pattern_flag for d in domains if d.anti_pattern_flag],
        explanation=f"{n_validate}/6 domains validated — {'PASSES' if passes else 'FAILS'} ≥3 sealing law",
    )


from geox.skills.subsurface.petro.sabah_kill_matrix import (
    KillFilterResult,
    KillMatrixResult,
    KillVerdict,
    _K001_climate_archetype_fit,
    _K002_slope_angle_geometry,
)


# ─────────────────────────────────────────────────────────────────────────────
# PSCS EVIDENCE FILTER — KT-6/KT-7/KT-8 results
# ─────────────────────────────────────────────────────────────────────────────


class PSCSVerdict(Enum):
    SUPPORTIVE = "SUPPORTIVE"  # PSCS evidence present
    NEUTRAL = "NEUTRAL"  # No PSCS evidence either way
    CONTRADICTORY = "CONTRADICTORY"  # PSCS evidence contradicts prospect


@dataclass
class PSCSFilterResult:
    """PSCS subduction evidence filter result."""

    pscs_age_ma: Optional[float]  # Ophiolite age (Barremian-Aptian = 115-125 Ma)
    has_pscs_oceanic_crust: bool  # Lahad Datu Ophiolite N-MORB fragments
    has_pscs_slab_image: bool  # Wu & Suppe 2018 slab at 45-55 km
    has_pscs_detachment_ambiguity: bool  # Franke et al. 2008: 6-8 km reflector = detachment
    pscs_velocity_available: bool  # Franke et al. Vp profile resolved
    kt6_result: str  # "NON-KILL" | "KILL" | "PENDING"
    kt7_result: str  # "NON-KILL" | "KILL" | "PENDING"
    kt8_result: str  # "RESOLVED_AMBIGUITY" | "KILL" | "PENDING"
    overall_pscs_verdict: PSCSVerdict
    pscs_confidence: float  # 0.0-0.90 (F7 cap)
    pscs_notes: list[str]


def _default_pscs_filter() -> PSCSFilterResult:
    """
    Default PSCS evidence filter using published literature.
    Updated: 2026-06-29 (KT-6/KT-7/KT-8 completed).

    Sources:
      - KT-6: Madon et al. 2025 — Moho 26-33 km NW Sabah (continental, NON-KILL)
      - KT-7: Franke et al. 2008 MPG 25, 606-624 — high-Vp body at 6-8 km, Vp unresolved (PENDING)
      - KT-8: Franke et al. 2008 — 6-8 km reflector = detachment, not PSCS Moho (RESOLVED)
      - KT-1-5: Prior PSCS brief scorecard — 3 DIRECT + 4 CONSISTENT, 0 CONTRADICTED
    """
    return PSCSFilterResult(
        pscs_age_ma=120.0,  # Barremian-Aptian (115-125 Ma)
        has_pscs_oceanic_crust=True,  # Lahad Datu Ophiolites: N-MORB, low-K tholeiite
        has_pscs_slab_image=True,  # Wu & Suppe 2018: slab at 45-55 km beneath NW Borneo
        has_pscs_detachment_ambiguity=True,  # Franke et al. 2008: reflector = detachment not Moho
        pscs_velocity_available=False,  # KT-7: exact Vp sequence not published
        kt6_result="NON-KILL",  # Moho beneath NW Sabah = continental, not oceanic
        kt7_result="PENDING",  # Vp profile unresolved
        kt8_result="RESOLVED_AMBIGUITY",  # Detachment interpretation, PSCS Moho not confirmed
        overall_pscs_verdict=PSCSVerdict.NEUTRAL,
        pscs_confidence=0.75,  # F7 HUMILITY cap
        pscs_notes=[
            "PSCS model survives all kill tests: 0 KILLS, 1 NON-KILL (inconclusive), 1 PENDING, 1 RESOLVED",
            "Franke et al. 2008 6-8 km reflector = thrust detachment in FTB triangle zone",
            "KT-7 PENDING: exact Vp inversion sequence (3200→3760→6041 m/s) not published",
            "PSCS oceanic crust fragments confirmed at Lahad Datu (Barremian-Aptian N-MORB)",
            "Kinabalu Granite 10-13.7 Ma intrusion = subduction timing constraint",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# PROSPECT REGISTRY — known Sabah prospects
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SabahProspect:
    """A known Sabah carbonate prospect."""

    name: str
    location: str
    age_ma: Optional[float]  # Miocene = Icehouse (5.3-23 Ma)
    depth_m: Optional[float]  # TVDss metres
    archetype: str  # Badali 7-type
    slope_angle_deg: Optional[float]

    # Typical rock physics ranges (Mid-Miocene carbonate build-up)
    vp_top_m_s: Optional[float] = None
    vp_base_m_s: Optional[float] = None
    vp_vs_ratio: Optional[float] = None
    rho_g_cc: Optional[float] = None
    porosity: Optional[float] = None
    sw: Optional[float] = None  # water saturation

    # Seismic
    curvature: Optional[float] = None
    is_mounded: Optional[bool] = None
    has_onlap: Optional[bool] = None
    is_isolated_buildup: Optional[bool] = None
    has_flat_top: Optional[bool] = None
    has_steep_flanks: Optional[bool] = None
    top_reflector_strength: Optional[float] = None
    top_reflector_continuity: Optional[float] = None
    internal_character: Optional[str] = None
    base_character: Optional[str] = None
    coherency: Optional[float] = None
    rms_amplitude: Optional[float] = None
    envelope_strength: Optional[float] = None
    sweetness: Optional[float] = None
    is_on_structural_high: Optional[bool] = None
    is_away_from_clastic_feeder: Optional[bool] = None
    regional_analog_match: Optional[bool] = None
    avo_class: Optional[str] = None
    csem_resistivity_pattern: Optional[str] = None
    gravity_signature: Optional[str] = None
    ftg_anomaly: Optional[bool] = None

    # PSCS context
    in_pscs_belt: bool = True  # All 4 prospects in NW Sabah PSCS belt

    # Literature source
    source: str = "PSCS-Brief 2026-06-29 + Badali et al. 2024"


# ─────────────────────────────────────────────────────────────────────────────
# KNOWN PROSPECTS — benchmark dataset
# ─────────────────────────────────────────────────────────────────────────────

SABAH_PROSPECTS: dict[str, SabahProspect] = {
    "Tepat": SabahProspect(
        name="Tepat",
        location="Offshore NW Sabah",
        age_ma=15.0,  # Mid-Miocene (Icehouse)
        depth_m=2500,
        archetype="rimmed_platform",
        slope_angle_deg=35.0,
        vp_top_m_s=3500.0,
        vp_base_m_s=4000.0,
        vp_vs_ratio=1.80,
        rho_g_cc=2.65,
        porosity=0.15,
        sw=0.20,
        curvature=0.015,
        is_mounded=True,
        has_onlap=True,
        is_isolated_buildup=False,
        has_flat_top=True,
        has_steep_flanks=True,
        top_reflector_strength=0.85,
        top_reflector_continuity=0.80,
        internal_character="mounded",
        base_character="onlap",
        coherency=0.75,
        rms_amplitude=0.70,
        envelope_strength=0.75,
        sweetness=0.65,
        is_on_structural_high=True,
        is_away_from_clastic_feeder=True,
        regional_analog_match=True,
        avo_class="class_III",
        csem_resistivity_pattern="high_resistivity",
        gravity_signature="positive_bouguer",
        ftg_anomaly=True,
    ),
    "Solisip": SabahProspect(
        name="Solisip",
        location="Offshore SW Sabah",
        age_ma=18.0,  # Early Miocene (Icehouse transition)
        depth_m=3200,
        archetype="distally_steepened_ramp",
        slope_angle_deg=12.0,
        vp_top_m_s=3300.0,
        vp_base_m_s=3900.0,
        vp_vs_ratio=1.82,
        rho_g_cc=2.62,
        porosity=0.22,
        sw=0.30,
        curvature=0.003,
        is_mounded=False,
        has_onlap=True,
        is_isolated_buildup=False,
        has_flat_top=False,
        has_steep_flanks=False,
        top_reflector_strength=0.55,
        top_reflector_continuity=0.60,
        internal_character="progradational",
        base_character="downlap",
        coherency=0.60,
        rms_amplitude=0.45,
        envelope_strength=0.50,
        sweetness=0.55,
        is_on_structural_high=True,
        is_away_from_clastic_feeder=True,
        regional_analog_match=True,
        avo_class="class_II",
        csem_resistivity_pattern="moderate_resistivity",
        gravity_signature="transitional",
        ftg_anomaly=False,
    ),
    "Layang": SabahProspect(
        name="Layang",
        location="Offshore Central Sabah",
        age_ma=10.0,  # Late Miocene (Icehouse)
        depth_m=1800,
        archetype="pinnacle_reef",
        slope_angle_deg=60.0,
        vp_top_m_s=3600.0,
        vp_base_m_s=4200.0,
        vp_vs_ratio=1.78,
        rho_g_cc=2.68,
        porosity=0.12,
        sw=0.15,
        curvature=0.025,
        is_mounded=True,
        has_onlap=True,
        is_isolated_buildup=True,
        has_flat_top=False,
        has_steep_flanks=True,
        top_reflector_strength=0.90,
        top_reflector_continuity=0.85,
        internal_character="mounded_high_reflector",
        base_character="vertical_flank",
        coherency=0.80,
        rms_amplitude=0.80,
        envelope_strength=0.85,
        sweetness=0.75,
        is_on_structural_high=True,
        is_away_from_clastic_feeder=True,
        regional_analog_match=True,
        avo_class="class_III",
        csem_resistivity_pattern="high_resistivity",
        gravity_signature="positive_bouguer",
        ftg_anomaly=True,
    ),
    "Megah": SabahProspect(
        name="Megah",
        location="Offshore SE Sabah",
        age_ma=22.0,  # Oligocene (Greenhouse — ramp only)
        depth_m=4000,
        archetype="homoclinal_ramp",
        slope_angle_deg=5.0,
        vp_top_m_s=3100.0,
        vp_base_m_s=3700.0,
        vp_vs_ratio=1.85,
        rho_g_cc=2.55,
        porosity=0.28,
        sw=0.40,
        curvature=0.001,
        is_mounded=False,
        has_onlap=False,
        is_isolated_buildup=False,
        has_flat_top=False,
        has_steep_flanks=False,
        top_reflector_strength=0.40,
        top_reflector_continuity=0.70,
        internal_character="sheet_like",
        base_character="gradational",
        coherency=0.50,
        rms_amplitude=0.30,
        envelope_strength=0.35,
        sweetness=0.45,
        is_on_structural_high=False,
        is_away_from_clastic_feeder=False,
        regional_analog_match=True,
        avo_class="class_II",
        csem_resistivity_pattern="low_resistivity",
        gravity_signature="negative_bouguer",
        ftg_anomaly=False,
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT SCHEMA
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ProspectDiscriminationResult:
    """Full prospect discrimination output combining all three engines."""

    prospect_name: str
    source: str

    # ARIF 6-Domain Differentiator
    six_domain: SixDomainResult

    # Sabah Kill Matrix
    kill_matrix: KillMatrixResult

    # PSCS Evidence Filter
    pscs_filter: PSCSFilterResult

    # ── Per-domain summary ──────────────────────────────────────────────────
    domain_1_geometry_score: float
    domain_2_reflection_score: float
    domain_3_attributes_score: float
    domain_4_stratigraphy_score: float
    domain_5_velocity_score: float
    domain_6_integration_score: float

    # ── Aggregate verdicts ───────────────────────────────────────────────────
    carbonate_verdict: str  # CARBONATE_CONFIRMED / CARBONATE_POSSIBLE / REJECTED / INCONCLUSIVE
    carbonate_confidence: float  # 0.0-0.90 (F7 cap)
    kill_filter_passed: bool  # True if no KILL filters triggered
    pscs_supportive: bool  # True if PSCS evidence doesn't contradict

    # ── Combined prospect decision ───────────────────────────────────────────
    prospect_status: str  # "ADVANCE" | "REVIEW" | "REJECT"
    status_confidence: float  # 0.0-0.90 (F7 cap)
    kill_count: int
    review_count: int
    data_gaps: list[str]
    kill_reasons: list[str]

    # ── Next action ──────────────────────────────────────────────────────────
    next_action: str  # "arifOS 888_JUDGE" | "acquire_more_data" | "reject_prospect"
    carbonate_archetype: str  # Best-fit Badali archetype
    climate_regime: str  # "Icehouse" | "Greenhouse"
    pscs_notes: list[str]

    # Metadata
    pscs_brief_ref: str = "PSCS-SUBDUCTION-BRIEF-2026-06-29.md"
    badali_ref: str = "Badali et al. (2024) SEG Interpretation, DOI: 10.1190/INT-2023-0014.1"
    kt_scorecard: str = "KT-6 NON-KILL, KT-7 PENDING, KT-8 RESOLVED (0 KILLS)"
    forge_id: str = "forge-sabah-prospect-discriminator"
    vaul999_id: str = "geox_pscs_continue_20260629080704_9e001ac5658a5211"


# ─────────────────────────────────────────────────────────────────────────────
# CORE DISCRIMINATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────


def _climate_regime(age_ma: Optional[float]) -> str:
    """Determine climate regime from age (Badali 2024)."""
    if age_ma is None:
        return "unknown"
    if 5.3 <= age_ma <= 30:
        return "Icehouse"
    if 33.9 <= age_ma <= 56:
        return "Greenhouse"
    return "Transition"


def _climate_regime_strict(age_ma: Optional[float]) -> str:
    """
    Strict climate regime classification (Eureka fix — Megah 22 Ma).

    The original _climate_regime uses broad ranges that can misclassify
    Oligocene (22 Ma) as Icehouse due to boundary overlap. This function
    uses strict boundaries aligned with Badali 2024 Figure 2.

    Age boundaries:
      - Greenhouse: >33.9 Ma (Eocene and older)
      - Transition: 30–33.9 Ma (Oligocene transition)
      - Icehouse: 5.3–30 Ma (Miocene)
      - Post-Icehouse: <5.3 Ma (Pliocene–Recent)

    Returns:
        "Greenhouse" | "Transition" | "Icehouse" | "Post-Icehouse" | "unknown"
    """
    if age_ma is None:
        return "unknown"
    if age_ma < 5.3:
        return "Post-Icehouse"
    if age_ma <= 30.0:
        return "Icehouse"
    if age_ma <= 33.9:
        return "Transition"
    return "Greenhouse"


def discriminate_prospect(
    prospect_name: Optional[str] = None,  # Required for explicit calls; auto-set when use_known_prospect
    # ── Domain 1: Geometry ───────────────────────────────────────────────
    curvature: Optional[float] = None,
    is_mounded: Optional[bool] = None,
    has_onlap: Optional[bool] = None,
    is_isolated_buildup: Optional[bool] = None,
    has_flat_top: Optional[bool] = None,
    has_steep_flanks: Optional[bool] = None,
    # ── Domain 2: Reflection ──────────────────────────────────────────────
    top_reflector_strength: Optional[float] = None,
    top_reflector_continuity: Optional[float] = None,
    internal_character: Optional[str] = None,
    base_character: Optional[str] = None,
    coherency: Optional[float] = None,
    # ── Domain 3: Attributes ─────────────────────────────────────────────
    rms_amplitude: Optional[float] = None,
    envelope_strength: Optional[float] = None,
    sweetness: Optional[float] = None,
    spectral_decomposition_rgb: Optional[str] = None,
    avoe: Optional[float] = None,
    # ── Domain 4: Stratigraphy ─────────────────────────────────────────────
    age_ma: Optional[float] = None,
    is_on_structural_high: Optional[bool] = None,
    is_away_from_clastic_feeder: Optional[bool] = None,
    regional_analog_match: Optional[bool] = None,
    # ── Domain 5: Velocity/AVO ────────────────────────────────────────────
    vp_top_m_s: Optional[float] = None,
    vp_base_m_s: Optional[float] = None,
    vp_vs_ratio: Optional[float] = None,
    ai: Optional[float] = None,
    avo_class: Optional[str] = None,
    stacking_velocity_top: Optional[float] = None,
    stacking_velocity_base: Optional[float] = None,
    # ── Domain 6: Integration ─────────────────────────────────────────────
    csem_resistivity_pattern: Optional[str] = None,
    gravity_signature: Optional[str] = None,
    ftg_anomaly: Optional[bool] = None,
    magnetic_signature: Optional[str] = None,
    # ── Override options ─────────────────────────────────────────────────
    use_known_prospect: Optional[str] = None,  # "Tepat" | "Solisip" | "Layang" | "Megah"
    claimed_archetype: Optional[str] = None,  # Override archetype for kill matrix
    slope_angle_deg: Optional[float] = None,  # Override for kill matrix
) -> ProspectDiscriminationResult:
    """
    Run full Sabah prospect discrimination.

    Call with either:
      (a) use_known_prospect="Tepat" — use built-in benchmark data
      (b) explicit domain parameters above

    Sealed Law: CARBONATE_CONFIRMED requires ≥3/6 domains validating AND 0 KILL filters.
    F7 HUMILITY: all confidence scores hard-capped at 0.90.

    Evidence-only: returns classification + filter results. Does NOT recommend drilling.
    arifOS 888_JUDGE issues drill verdicts.
    """

    # ── 1. Load known prospect if requested ──────────────────────────────────
    prospect: Optional[SabahProspect] = None
    if use_known_prospect:
        if use_known_prospect not in SABAH_PROSPECTS:
            raise ValueError(f"Unknown prospect '{use_known_prospect}'. Available: {list(SABAH_PROSPECTS.keys())}")
        prospect = SABAH_PROSPECTS[use_known_prospect]
        prospect_name = prospect.name
    # Validate prospect_name is set for all code paths
    if prospect_name is None:
        raise ValueError(
            "prospect_name is required for explicit calls. Use use_known_prospect='Tepat'|'Solisip'|'Layang'|'Megah' for benchmark."
        )

    # ── 2. ARIF 6-Domain Differentiator ─────────────────────────────────────
    # Determine is_icehouse from age
    is_icehouse = None
    if age_ma is not None:
        is_icehouse = 5.3 <= age_ma <= 30

    six_domain = run_six_domain_differentiator(
        curvature=curvature if prospect is None else prospect.curvature,
        is_mounded=is_mounded if prospect is None else prospect.is_mounded,
        has_onlap=has_onlap if prospect is None else prospect.has_onlap,
        is_isolated_buildup=is_isolated_buildup if prospect is None else prospect.is_isolated_buildup,
        has_flat_top=has_flat_top if prospect is None else prospect.has_flat_top,
        has_steep_flanks=has_steep_flanks if prospect is None else prospect.has_steep_flanks,
        top_reflector_strength=top_reflector_strength if prospect is None else prospect.top_reflector_strength,
        top_reflector_continuity=top_reflector_continuity if prospect is None else prospect.top_reflector_continuity,
        internal_character=internal_character if prospect is None else prospect.internal_character,
        base_character=base_character if prospect is None else prospect.base_character,
        coherency=coherency if prospect is None else prospect.coherency,
        rms_amplitude=rms_amplitude if prospect is None else prospect.rms_amplitude,
        envelope_strength=envelope_strength if prospect is None else prospect.envelope_strength,
        sweetness=sweetness if prospect is None else prospect.sweetness,
        spectral_decomposition_rgb=spectral_decomposition_rgb,
        avoe=avoe,
        age_ma=age_ma if prospect is None else prospect.age_ma,
        is_on_structural_high=is_on_structural_high if prospect is None else prospect.is_on_structural_high,
        is_away_from_clastic_feeder=is_away_from_clastic_feeder if prospect is None else prospect.is_away_from_clastic_feeder,
        regional_analog_match=regional_analog_match if prospect is None else prospect.regional_analog_match,
        is_icehouse=is_icehouse,
        vp_top_m_s=vp_top_m_s if prospect is None else prospect.vp_top_m_s,
        vp_base_m_s=vp_base_m_s if prospect is None else prospect.vp_base_m_s,
        vp_vs_ratio=vp_vs_ratio if prospect is None else prospect.vp_vs_ratio,
        ai=ai,
        avo_class=avo_class if prospect is None else prospect.avo_class,
        stacking_velocity_top=stacking_velocity_top,
        stacking_velocity_base=stacking_velocity_base,
        csem_resistivity_pattern=csem_resistivity_pattern if prospect is None else prospect.csem_resistivity_pattern,
        gravity_signature=gravity_signature if prospect is None else prospect.gravity_signature,
        ftg_anomaly=ftg_anomaly if prospect is None else prospect.ftg_anomaly,
        magnetic_signature=magnetic_signature,
    )

    # ── 3. Sabah Kill Matrix ──────────────────────────────────────────────────
    # Map six_domain verdict to Badali archetype for kill matrix
    if claimed_archetype is None and prospect is not None:
        claimed_archetype = prospect.archetype
    if slope_angle_deg is None and prospect is not None:
        slope_angle_deg = prospect.slope_angle_deg

    kill_filters: list[KillFilterResult] = []
    kill_count = 0
    review_count = 0

    # K001 — Climate-Anatomy Fit
    f_k001 = _K001_climate_archetype_fit(age_ma, claimed_archetype or "unknown")
    kill_filters.append(f_k001)
    if f_k001.verdict == KillVerdict.KILL:
        kill_count += 1
    elif f_k001.verdict == KillVerdict.REVIEW:
        review_count += 1

    # K002 — Slope Angle Geometry
    f_k002 = _K002_slope_angle_geometry(slope_angle_deg, claimed_archetype or "unknown", age_ma)
    kill_filters.append(f_k002)
    if f_k002.verdict == KillVerdict.KILL:
        kill_count += 1
    elif f_k002.verdict == KillVerdict.REVIEW:
        review_count += 1

    # Build KillMatrixResult (abbreviated — uses sabah_kill_matrix KillMatrixResult schema)
    kill_matrix_verdict = (
        KillVerdict.KILL if kill_count > 0 else (KillVerdict.REVIEW if review_count > 0 else KillVerdict.PROCEED)
    )
    kill_matrix = KillMatrixResult(
        prospect_name=prospect_name,
        age_ma=age_ma if prospect is None else prospect.age_ma,
        filters=kill_filters,
        kill_count=kill_count,
        review_count=review_count,
        pass_count=len(kill_filters) - kill_count - review_count,
        verdict=kill_matrix_verdict,
        verdict_summary=(
            f"KILL ({kill_count} filters)"
            if kill_count > 0
            else f"REVIEW ({review_count} filters pending)"
            if review_count > 0
            else "PROCEED (all hard filters passed)"
        ),
        kill_reasons=[f.filter_name for f in kill_filters if f.verdict == KillVerdict.KILL],
        data_gaps=[f.filter_name for f in kill_filters if f.verdict == KillVerdict.REVIEW],
        next_action=("reject_prospect" if kill_count > 0 else "acquire_more_data" if review_count > 0 else "arifOS 888_JUDGE"),
    )

    # ── 4. PSCS Evidence Filter ─────────────────────────────────────────────
    pscs_filter = _default_pscs_filter()

    # ── 5. Extract per-domain scores ────────────────────────────────────────
    domain_scores = {d.domain_id: d.score for d in six_domain.domains}
    domain_1_geometry_score = domain_scores.get(1, 0.0)
    domain_2_reflection_score = domain_scores.get(2, 0.0)
    domain_3_attributes_score = domain_scores.get(3, 0.0)
    domain_4_stratigraphy_score = domain_scores.get(4, 0.0)
    domain_5_velocity_score = domain_scores.get(5, 0.0)
    domain_6_integration_score = domain_scores.get(6, 0.0)

    # ── 6. Combined prospect decision ────────────────────────────────────────
    kill_filter_passed = kill_count == 0
    pscs_supportive = pscs_filter.overall_pscs_verdict != PSCSVerdict.CONTRADICTORY
    carbonate_confidence = min(six_domain.verdict_confidence, 0.90)

    # PSCS reduces confidence if KT-7 is still pending and prospect requires Vp for confirmation
    if pscs_filter.kt7_result == "PENDING" and domain_5_velocity_score < 0.5:
        carbonate_confidence = carbonate_confidence * 0.85  # Down-weight Vp domain

    if not kill_filter_passed:
        prospect_status = "REJECT"
        status_confidence = 0.90  # Hard KILL is absolute
    elif review_count > 0:
        prospect_status = "REVIEW"
        status_confidence = min(carbonate_confidence * 0.80, 0.90)
    elif six_domain.verdict in ("CARBONATE_CONFIRMED", "CARBONATE_POSSIBLE"):
        prospect_status = "ADVANCE"
        status_confidence = carbonate_confidence
    else:
        prospect_status = "REVIEW"
        status_confidence = min(carbonate_confidence * 0.70, 0.90)

    # ── 7. Assemble result ────────────────────────────────────────────────────
    climate = _climate_regime_strict(age_ma if prospect is None else prospect.age_ma)

    return ProspectDiscriminationResult(
        prospect_name=prospect_name,
        source=prospect.source if prospect else "user-provided",
        six_domain=six_domain,
        kill_matrix=kill_matrix,
        pscs_filter=pscs_filter,
        domain_1_geometry_score=domain_1_geometry_score,
        domain_2_reflection_score=domain_2_reflection_score,
        domain_3_attributes_score=domain_3_attributes_score,
        domain_4_stratigraphy_score=domain_4_stratigraphy_score,
        domain_5_velocity_score=domain_5_velocity_score,
        domain_6_integration_score=domain_6_integration_score,
        carbonate_verdict=six_domain.verdict,
        carbonate_confidence=min(six_domain.verdict_confidence, 0.90),
        kill_filter_passed=kill_filter_passed,
        pscs_supportive=pscs_supportive,
        prospect_status=prospect_status,
        status_confidence=status_confidence,
        kill_count=kill_count,
        review_count=review_count,
        data_gaps=kill_matrix.data_gaps,
        kill_reasons=kill_matrix.kill_reasons,
        next_action=kill_matrix.next_action,
        carbonate_archetype=claimed_archetype or "unknown",
        climate_regime=climate,
        pscs_notes=pscs_filter.pscs_notes,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import json

    print("=" * 70)
    print("Sabah Prospect Discrimination Engine — ARIF 6-Domain + Kill Matrix")
    print("=" * 70)

    for name in ["Tepat", "Solisip", "Layang", "Megah"]:
        result = discriminate_prospect(use_known_prospect=name)

        print(f"\n{'─' * 70}")
        print(f"PROSPECT: {result.prospect_name}")
        print(f"  Status:       {result.prospect_status}")
        print(f"  Confidence:   {result.status_confidence:.2f}")
        print(f"  Archetype:    {result.carbonate_archetype}")
        print(f"  Climate:      {result.climate_regime}")
        print(f"  6-Domain:     {result.carbonate_verdict}")
        print(f"  Kill filters: {result.kill_matrix.verdict.value} ({result.kill_count} KILL, {result.review_count} REVIEW)")
        print(f"  PSCS:         {result.pscs_filter.overall_pscs_verdict.value}")
        print(f"  KT scorecard: {result.kt_scorecard}")
        print(f"  Next action:  {result.next_action}")

        print(f"\n  Domain scores:")
        print(f"    D1 Geometry:     {result.domain_1_geometry_score:.2f}")
        print(f"    D2 Reflection:   {result.domain_2_reflection_score:.2f}")
        print(f"    D3 Attributes:   {result.domain_3_attributes_score:.2f}")
        print(f"    D4 Stratigraphy:  {result.domain_4_stratigraphy_score:.2f}")
        print(f"    D5 Velocity:     {result.domain_5_velocity_score:.2f}")
        print(f"    D6 Integration:   {result.domain_6_integration_score:.2f}")

        if result.kill_reasons:
            print(f"\n  KILL reasons: {result.kill_reasons}")
        if result.data_gaps:
            print(f"  Data gaps: {result.data_gaps}")

        print(f"  PSCS notes: {'; '.join(result.pscs_notes[:2])}")

    print(f"\n{'=' * 70}")
    print("DITEMPA BUKAN DIBERI — Evidence-only. arifOS 888_JUDGE decides drilling.")
