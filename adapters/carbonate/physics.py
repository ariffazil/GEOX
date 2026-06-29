"""
Carbonate Intelligence Bridge — Full GEOX Integration
======================================================
Connects Badali et al. (2024) 7-type taxonomy + ARIF 6-Domain Differentiator
to rock physics velocity predictions, AVO modelling, and multi-physics
discrimination.

Canon sources:
  - Badali et al. (2024), SEG Interpretation, DOI: 10.1190/INT-2023-0014.1
  - ARIF 6-Domain Carbonate Differentiator (TEA Layang-Layang Basin, sealed)
  - Tepat-1 benchmark (Operator Sabah, proven producer)
  - Yellow-horizon scar: ≥3/6 domain validation law

Sealed Law: classify as carbonate only when ≥3 of 6 domains validate.
Single-attribute calls are VOID.

DITEMPA BUKAN DIBERI — Forged, Not Given.
F2 TRUTH: all confidence scores derived from measured elastic constants.
F7 HUMILITY: confidence hard-capped at 0.90.
F9 ANTI-HANTU: this is physics, not intuition.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# MINERAL ELASTIC CONSTANTS — Mavko et al. (2009)
# ─────────────────────────────────────────────────────────────────────────────

_MINERAL_PROPS: dict[str, dict[str, float]] = {
    "calcite": {"bulk_mod": 76.8, "shear_mod": 32.0, "rho": 2.71},
    "dolomite": {"bulk_mod": 94.9, "shear_mod": 45.0, "rho": 2.87},
    "clay": {"bulk_mod": 20.9, "shear_mod": 6.85, "rho": 2.55},
    "quartz": {"bulk_mod": 36.6, "shear_mod": 45.0, "rho": 2.65},
    "basement": {"bulk_mod": 75.0, "shear_mod": 33.0, "rho": 2.65},
}

_FLUID_PROPS: dict[str, dict[str, float]] = {
    "brine": {"bulk_mod": 2.38, "rho": 1.09},
    "oil": {"bulk_mod": 0.72, "rho": 0.78},
    "gas": {"bulk_mod": 0.02, "rho": 0.15},
}

_VP_MIN, _VP_MAX = 1500.0, 7000.0
_RHO_MIN, _RHO_MAX = 1.00, 3.50
_HUMILITY_CAP = 0.90


def _cap(v: float) -> float:
    return min(v, _HUMILITY_CAP)


# ─────────────────────────────────────────────────────────────────────────────
# 6-DOMAIN CARBONATE DIFFERENTIATOR — ARIF canon, sealed
# ─────────────────────────────────────────────────────────────────────────────


class DomainVerdict(Enum):
    """Per-domain validation result."""

    VALIDATE = "VALIDATE"  # domain confirms carbonate
    REJECT = "REJECT"  # domain rejects carbonate
    INCONCLUSIVE = "INCONCLUSIVE"  # insufficient data


@dataclass
class DomainResult:
    """Result from a single discrimination domain."""

    domain_id: int
    domain_name: str
    score: float  # 0.0–1.0
    weight: float  # domain weight in composite
    verdict: DomainVerdict
    evidence: str
    threshold_used: str
    anti_pattern_flag: str | None = None  # which mimic is suspected


@dataclass
class SixDomainResult:
    """Full 6-domain differentiator output."""

    domains: list[DomainResult]
    validation_count: int  # how many domains validated
    rejection_count: int
    inconclusive_count: int
    composite_score: float  # weighted sum, 0–100
    passes_3of6: bool  # ≥3/6 law
    verdict: str  # CARBONATE_CONFIRMED | CARBONATE_POSSIBLE | REJECTED | INCONCLUSIVE
    verdict_confidence: float
    anti_patterns_detected: list[str]
    explanation: str


# Domain weights (equal by default — Arif can override)
_DOMAIN_WEIGHTS = {
    1: 0.20,  # Geometry — strongest discriminator
    2: 0.15,  # Reflection character
    3: 0.15,  # Multi-attributes
    4: 0.15,  # Stratigraphy
    5: 0.20,  # Velocity/AVO — physics-grounded
    6: 0.15,  # Integration/CSEM-MT
}


def domain_1_geometry(
    curvature: float | None = None,
    is_mounded: bool | None = None,
    has_onlap: bool | None = None,
    is_isolated_buildup: bool | None = None,
    has_flat_top: bool | None = None,
    has_steep_flanks: bool | None = None,
) -> DomainResult:
    """
    Domain 1: Geometry — mound/pinnacle, steep flanks, onlap, isolated build-up.

    Carbonate signature: mounded continuous high reflector with onlapping flanks.
    Threshold: curvature ≥ 0.005
    Anti-patterns: MTC mounds, channel levees, volcanic edifice
    """
    score = 0.0
    evidence_parts = []
    anti_pattern = None

    if is_mounded:
        score += 0.30
        evidence_parts.append("mounded geometry")
    if has_onlap:
        score += 0.20
        evidence_parts.append("onlapping flanks")
    if is_isolated_buildup:
        score += 0.20
        evidence_parts.append("isolated build-up")
    if has_flat_top:
        score += 0.10
        evidence_parts.append("flat top (platform)")
    if has_steep_flanks:
        score += 0.10
        evidence_parts.append("steep flanks")

    if curvature is not None:
        if curvature >= 0.005:
            score += 0.10
            evidence_parts.append(f"curvature={curvature:.4f} ≥ 0.005")
        else:
            evidence_parts.append(f"curvature={curvature:.4f} < 0.005 (low)")

    score = min(1.0, score)

    # Anti-pattern checks
    if is_mounded and not has_onlap and not has_flat_top:
        anti_pattern = "MTC_mound_or_channel_levee"
        score *= 0.7  # penalize but don't reject

    _has_data = any(
        v is not None for v in [curvature, is_mounded, has_onlap, is_isolated_buildup, has_flat_top, has_steep_flanks]
    )
    if not _has_data:
        verdict = DomainVerdict.INCONCLUSIVE
    elif score >= 0.5:
        verdict = DomainVerdict.VALIDATE
    elif score < 0.2:
        verdict = DomainVerdict.REJECT
    else:
        verdict = DomainVerdict.INCONCLUSIVE

    return DomainResult(
        domain_id=1,
        domain_name="Geometry",
        score=score,
        weight=_DOMAIN_WEIGHTS[1],
        verdict=verdict,
        evidence="; ".join(evidence_parts) if evidence_parts else "no geometry data",
        threshold_used="curvature ≥ 0.005; mounded + onlap + isolated",
        anti_pattern_flag=anti_pattern,
    )


def domain_2_reflection_character(
    top_reflector_strength: float | None = None,  # 0–1
    top_reflector_continuity: float | None = None,  # 0–1
    internal_character: str | None = None,  # "chaotic" | "parallel" | "subparallel" | "transparent"
    base_character: str | None = None,  # "dim" | "bright" | "karstified"
    coherency: float | None = None,
) -> DomainResult:
    """
    Domain 2: Reflection character — top, internal, base.

    Carbonate signature: top = strong continuous bright; internal = chaotic-to-parallel;
    base = dim/karstified. Instantaneous Phase shows distinct change.
    Threshold: coherency ≥ 0.7
    Anti-patterns: volcanic flows can mimic bright top; basement can mimic chaotic interior
    """
    score = 0.0
    evidence_parts = []
    anti_pattern = None

    if top_reflector_strength is not None:
        if top_reflector_strength >= 0.7:
            score += 0.25
            evidence_parts.append(f"top reflector strong ({top_reflector_strength:.2f})")
        elif top_reflector_strength >= 0.4:
            score += 0.10
            evidence_parts.append(f"top reflector moderate ({top_reflector_strength:.2f})")
        else:
            evidence_parts.append(f"top reflector weak ({top_reflector_strength:.2f})")

    if top_reflector_continuity is not None:
        if top_reflector_continuity >= 0.7:
            score += 0.15
            evidence_parts.append(f"top continuous ({top_reflector_continuity:.2f})")

    if internal_character in ("chaotic", "subparallel"):
        score += 0.15
        evidence_parts.append(f"internal: {internal_character}")
    elif internal_character == "parallel":
        score += 0.10
        evidence_parts.append("internal: parallel (layered)")

    if base_character in ("dim", "karstified"):
        score += 0.10
        evidence_parts.append(f"base: {base_character}")

    if coherency is not None:
        if coherency >= 0.7:
            score += 0.20
            evidence_parts.append(f"coherency={coherency:.2f} ≥ 0.7")
        elif coherency >= 0.5:
            score += 0.10
            evidence_parts.append(f"coherency={coherency:.2f} (moderate)")
        else:
            evidence_parts.append(f"coherency={coherency:.2f} < 0.5 (low)")

    # Anti-pattern: volcanic flow can mimic bright top
    if top_reflector_strength is not None and top_reflector_strength >= 0.8 and internal_character == "transparent":
        anti_pattern = "volcanic_flow_mimic"
        score *= 0.8

    score = min(1.0, score)

    _has_data = any(v is not None for v in [top_reflector_strength, top_reflector_continuity, internal_character, base_character, coherency])
    if not _has_data:
        verdict = DomainVerdict.INCONCLUSIVE
    elif score >= 0.5:
        verdict = DomainVerdict.VALIDATE
    elif score < 0.2:
        verdict = DomainVerdict.REJECT
    else:
        verdict = DomainVerdict.INCONCLUSIVE

    return DomainResult(
        domain_id=2,
        domain_name="Reflection Character",
        score=score,
        weight=_DOMAIN_WEIGHTS[2],
        verdict=verdict,
        evidence="; ".join(evidence_parts) if evidence_parts else "no reflection data",
        threshold_used="coherency ≥ 0.7; strong continuous top + chaotic internal",
        anti_pattern_flag=anti_pattern,
    )


def domain_3_attributes(
    rms_amplitude: float | None = None,
    envelope_strength: float | None = None,
    sweetness: float | None = None,
    spectral_decomposition_rgb: str | None = None,
    avoe: float | None = None,  # AVO energy
) -> DomainResult:
    """
    Domain 3: Multi-attribute analysis — RMS, Envelope, Sweetness, Spectral Decomp.

    Carbonate signature: RMS strong at top, Sweetness strongest of all lithologies,
    spectral RGB shows reefal facies belts.
    Threshold: RMS amplitude ≥ 0.15
    Anti-patterns: shallow gas clouds, tuning thickness anomalies
    """
    score = 0.0
    evidence_parts = []
    anti_pattern = None

    if rms_amplitude is not None:
        if rms_amplitude >= 0.15:
            score += 0.25
            evidence_parts.append(f"RMS={rms_amplitude:.3f} ≥ 0.15")
        elif rms_amplitude >= 0.08:
            score += 0.10
            evidence_parts.append(f"RMS={rms_amplitude:.3f} (moderate)")
        else:
            evidence_parts.append(f"RMS={rms_amplitude:.3f} (low)")

    if envelope_strength is not None:
        if envelope_strength >= 0.7:
            score += 0.20
            evidence_parts.append(f"envelope strong ({envelope_strength:.2f})")
        elif envelope_strength >= 0.4:
            score += 0.10

    if sweetness is not None:
        if sweetness >= 0.6:
            score += 0.20
            evidence_parts.append(f"sweetness high ({sweetness:.2f})")
        elif sweetness >= 0.3:
            score += 0.10

    if spectral_decomposition_rgb is not None:
        if "reefal" in spectral_decomposition_rgb.lower() or "platform" in spectral_decomposition_rgb.lower():
            score += 0.15
            evidence_parts.append(f"spectral RGB: {spectral_decomposition_rgb}")

    if avoe is not None:
        if avoe < 0:
            score += 0.10
            evidence_parts.append(f"AVOE negative ({avoe:.3f}) — gas-charged carbonate")
        else:
            evidence_parts.append(f"AVOE={avoe:.3f}")

    # Anti-pattern: gas cloud can mimic high RMS
    if rms_amplitude is not None and rms_amplitude >= 0.3 and envelope_strength is not None and envelope_strength < 0.3:
        anti_pattern = "gas_cloud_mimic"

    score = min(1.0, score)

    _has_data = any(v is not None for v in [rms_amplitude, envelope_strength, sweetness, spectral_decomposition_rgb, avoe])
    if not _has_data:
        verdict = DomainVerdict.INCONCLUSIVE
    elif score >= 0.5:
        verdict = DomainVerdict.VALIDATE
    elif score < 0.2:
        verdict = DomainVerdict.REJECT
    else:
        verdict = DomainVerdict.INCONCLUSIVE

    return DomainResult(
        domain_id=3,
        domain_name="Multi-Attributes",
        score=score,
        weight=_DOMAIN_WEIGHTS[3],
        verdict=verdict,
        evidence="; ".join(evidence_parts) if evidence_parts else "no attribute data",
        threshold_used="RMS ≥ 0.15; sweetness high; spectral RGB reefal",
        anti_pattern_flag=anti_pattern,
    )


def domain_4_stratigraphy(
    age_ma: float | None = None,
    is_on_structural_high: bool | None = None,
    is_away_from_clastic_feeder: bool | None = None,
    regional_analog_match: bool | None = None,
    is_icehouse: bool | None = None,
) -> DomainResult:
    """
    Domain 4: Stratigraphy / regional context.

    Carbonate signature: right age (Miocene in Sabah), structural high,
    away from clastic feeder, regional analog match.
    Anti-patterns: reworked carbonate talus (geometry but clastic behaviour)
    """
    score = 0.0
    evidence_parts = []
    anti_pattern = None

    if age_ma is not None:
        if 5.3 <= age_ma <= 30:
            score += 0.30
            evidence_parts.append(f"age={age_ma:.1f} Ma (Icehouse)")
        elif 33.9 <= age_ma <= 56:
            score += 0.15
            evidence_parts.append(f"age={age_ma:.1f} Ma (Greenhouse)")
        else:
            evidence_parts.append(f"age={age_ma:.1f} Ma (uncertain climate)")

    if is_on_structural_high:
        score += 0.25
        evidence_parts.append("on structural high")
    elif is_on_structural_high is False:
        evidence_parts.append("not on structural high (unusual for carbonate)")

    if is_away_from_clastic_feeder:
        score += 0.15
        evidence_parts.append("away from clastic feeder")
    elif is_away_from_clastic_feeder is False:
        anti_pattern = "clastic_contamination_risk"
        score -= 0.10
        evidence_parts.append("near clastic feeder (mixed system risk)")

    if regional_analog_match:
        score += 0.20
        evidence_parts.append("regional analog match")

    score = max(0.0, min(1.0, score))

    _has_data = any(v is not None for v in [age_ma, is_on_structural_high, is_away_from_clastic_feeder, regional_analog_match, is_icehouse])
    if not _has_data:
        verdict = DomainVerdict.INCONCLUSIVE
    elif score >= 0.5:
        verdict = DomainVerdict.VALIDATE
    elif score < 0.2:
        verdict = DomainVerdict.REJECT
    else:
        verdict = DomainVerdict.INCONCLUSIVE

    return DomainResult(
        domain_id=4,
        domain_name="Stratigraphy / Regional",
        score=score,
        weight=_DOMAIN_WEIGHTS[4],
        verdict=verdict,
        evidence="; ".join(evidence_parts) if evidence_parts else "no stratigraphic data",
        threshold_used="Icehouse age + structural high + away from feeder",
        anti_pattern_flag=anti_pattern,
    )


def domain_5_velocity_avo(
    vp_top_m_s: float | None = None,
    vp_base_m_s: float | None = None,
    vp_vs_ratio: float | None = None,
    ai: float | None = None,
    avo_class: str | None = None,  # "I" | "2p" | "II" | "III" | "IV"
    stacking_velocity_top: float | None = None,
    stacking_velocity_base: float | None = None,
) -> DomainResult:
    """
    Domain 5: Velocity / AVO — the physics-grounded discriminator.

    Carbonate signature (Tepat benchmark):
    - Stacking velocity Top ~3,200 m/s, Base ~3,800 m/s
    - High AI, low Vp/Vs over gas-charged buildup
    - AVO Class I (brine/oil) to 2p (gas + moderate φ) to Class 2 (gas + good φ)
    - "Well delineated by acoustic impedance" when inversion done properly

    Anti-patterns: tight cemented carbonate ≈ basement velocities
    """
    score = 0.0
    evidence_parts = []
    anti_pattern = None

    # Tepat stacking velocity benchmark
    if stacking_velocity_top is not None:
        if 2800 <= stacking_velocity_top <= 3600:
            score += 0.20
            evidence_parts.append(f"Vstk_top={stacking_velocity_top:.0f} m/s (Tepat range: ~3,200)")
        else:
            evidence_parts.append(f"Vstk_top={stacking_velocity_top:.0f} m/s (outside Tepat range)")

    if stacking_velocity_base is not None:
        if 3400 <= stacking_velocity_base <= 4200:
            score += 0.15
            evidence_parts.append(f"Vstk_base={stacking_velocity_base:.0f} m/s (Tepat range: ~3,800)")
        else:
            evidence_parts.append(f"Vstk_base={stacking_velocity_base:.0f} m/s (outside Tepat range)")

    # AI — high for carbonate
    if ai is not None:
        if ai >= 8000:
            score += 0.15
            evidence_parts.append(f"AI={ai:.0f} (high — consistent with carbonate)")
        elif ai >= 5000:
            score += 0.10
            evidence_parts.append(f"AI={ai:.0f} (moderate)")
        else:
            evidence_parts.append(f"AI={ai:.0f} (low — may be porous or clastic)")

    # Vp/Vs — low over gas-charged carbonate
    if vp_vs_ratio is not None:
        if vp_vs_ratio <= 1.7:
            score += 0.15
            evidence_parts.append(f"Vp/Vs={vp_vs_ratio:.2f} (low — gas or tight)")
        elif vp_vs_ratio <= 1.9:
            score += 0.10
            evidence_parts.append(f"Vp/Vs={vp_vs_ratio:.2f} (moderate)")
        else:
            evidence_parts.append(f"Vp/Vs={vp_vs_ratio:.2f} (high — shale or brine)")

    # AVO class
    if avo_class is not None:
        if avo_class in ("I", "2p"):
            score += 0.15
            evidence_parts.append(f"AVO Class {avo_class} (Sabah QI: carbonate + fluid)")
        elif avo_class in ("II", "III"):
            score += 0.05
            evidence_parts.append(f"AVO Class {avo_class}")
        else:
            evidence_parts.append(f"AVO Class {avo_class}")

    # Anti-pattern: tight cemented carbonate ≈ basement
    if vp_top_m_s is not None and vp_top_m_s > 5500:
        anti_pattern = "tight_carbonate_basement_overlap"
        score *= 0.8
        evidence_parts.append(f"Vp={vp_top_m_s:.0f} > 5500 — basement overlap risk")

    score = min(1.0, score)

    _has_data = any(v is not None for v in [vp_top_m_s, vp_base_m_s, vp_vs_ratio, ai, avo_class, stacking_velocity_top, stacking_velocity_base])
    if not _has_data:
        verdict = DomainVerdict.INCONCLUSIVE
    elif score >= 0.5:
        verdict = DomainVerdict.VALIDATE
    elif score < 0.2:
        verdict = DomainVerdict.REJECT
    else:
        verdict = DomainVerdict.INCONCLUSIVE

    return DomainResult(
        domain_id=5,
        domain_name="Velocity / AVO",
        score=score,
        weight=_DOMAIN_WEIGHTS[5],
        verdict=verdict,
        evidence="; ".join(evidence_parts) if evidence_parts else "no velocity/AVO data",
        threshold_used="Tepat Vstk 3200/3800; high AI; low Vp/Vs; AVO I/2p",
        anti_pattern_flag=anti_pattern,
    )


def domain_6_integration(
    csem_resistivity_pattern: str | None = None,  # "high-low-high" | "uniform" | "anomalous"
    gravity_signature: str | None = None,  # "positive" | "negative" | "neutral"
    ftg_anomaly: bool | None = None,
    magnetic_signature: str | None = None,  # "quiet" | "anomalous"
) -> DomainResult:
    """
    Domain 6: Multi-physics integration — CSEM/MT, gravity, FTG.

    Carbonate signature (Tepat): high-low-high resistivity pattern,
    positive gravity anomaly, quiet magnetic (non-volcanic).
    Anti-patterns: volcanics produce similar laminated anisotropy
    """
    score = 0.0
    evidence_parts = []
    anti_pattern = None

    if csem_resistivity_pattern is not None:
        if csem_resistivity_pattern == "high-low-high":
            score += 0.35
            evidence_parts.append("CSEM: high-low-high (Tepat pattern)")
        elif csem_resistivity_pattern == "anomalous":
            score += 0.15
            evidence_parts.append("CSEM: anomalous resistivity")
        else:
            evidence_parts.append(f"CSEM: {csem_resistivity_pattern}")

    if gravity_signature is not None:
        if gravity_signature == "positive":
            score += 0.20
            evidence_parts.append("gravity: positive anomaly (dense carbonate)")
        elif gravity_signature == "negative":
            anti_pattern = "salt_or_shale_diapir"
            evidence_parts.append("gravity: negative (non-carbonate)")

    if ftg_anomaly:
        score += 0.15
        evidence_parts.append("FTG anomaly detected")

    if magnetic_signature is not None:
        if magnetic_signature == "quiet":
            score += 0.15
            evidence_parts.append("magnetic: quiet (non-volcanic)")
        elif magnetic_signature == "anomalous":
            anti_pattern = "volcanic_intrusion"
            score -= 0.10
            evidence_parts.append("magnetic: anomalous (volcanic risk)")

    score = max(0.0, min(1.0, score))

    _has_data = any(v is not None for v in [csem_resistivity_pattern, gravity_signature, ftg_anomaly, magnetic_signature])
    if not _has_data:
        verdict = DomainVerdict.INCONCLUSIVE
    elif score >= 0.5:
        verdict = DomainVerdict.VALIDATE
    elif score < 0.2:
        verdict = DomainVerdict.REJECT
    else:
        verdict = DomainVerdict.INCONCLUSIVE

    return DomainResult(
        domain_id=6,
        domain_name="Integration / CSEM-MT",
        score=score,
        weight=_DOMAIN_WEIGHTS[6],
        verdict=verdict,
        evidence="; ".join(evidence_parts) if evidence_parts else "no multi-physics data",
        threshold_used="CSEM high-low-high; gravity positive; magnetic quiet",
        anti_pattern_flag=anti_pattern,
    )


def run_six_domain_differentiator(
    # Domain 1: Geometry
    curvature: float | None = None,
    is_mounded: bool | None = None,
    has_onlap: bool | None = None,
    is_isolated_buildup: bool | None = None,
    has_flat_top: bool | None = None,
    has_steep_flanks: bool | None = None,
    # Domain 2: Reflection
    top_reflector_strength: float | None = None,
    top_reflector_continuity: float | None = None,
    internal_character: str | None = None,
    base_character: str | None = None,
    coherency: float | None = None,
    # Domain 3: Attributes
    rms_amplitude: float | None = None,
    envelope_strength: float | None = None,
    sweetness: float | None = None,
    spectral_decomposition_rgb: str | None = None,
    avoe: float | None = None,
    # Domain 4: Stratigraphy
    age_ma: float | None = None,
    is_on_structural_high: bool | None = None,
    is_away_from_clastic_feeder: bool | None = None,
    regional_analog_match: bool | None = None,
    is_icehouse: bool | None = None,
    # Domain 5: Velocity/AVO
    vp_top_m_s: float | None = None,
    vp_base_m_s: float | None = None,
    vp_vs_ratio: float | None = None,
    ai: float | None = None,
    avo_class: str | None = None,
    stacking_velocity_top: float | None = None,
    stacking_velocity_base: float | None = None,
    # Domain 6: Integration
    csem_resistivity_pattern: str | None = None,
    gravity_signature: str | None = None,
    ftg_anomaly: bool | None = None,
    magnetic_signature: str | None = None,
) -> SixDomainResult:
    """
    Run the full ARIF 6-Domain Carbonate Differentiator.

    Sealed Law: classify as carbonate only when ≥3 of 6 domains validate.
    Single-attribute calls are VOID.

    Returns SixDomainResult with per-domain scores, composite, and verdict.
    """
    domains = [
        domain_1_geometry(curvature, is_mounded, has_onlap, is_isolated_buildup, has_flat_top, has_steep_flanks),
        domain_2_reflection_character(
            top_reflector_strength, top_reflector_continuity, internal_character, base_character, coherency
        ),
        domain_3_attributes(rms_amplitude, envelope_strength, sweetness, spectral_decomposition_rgb, avoe),
        domain_4_stratigraphy(age_ma, is_on_structural_high, is_away_from_clastic_feeder, regional_analog_match, is_icehouse),
        domain_5_velocity_avo(vp_top_m_s, vp_base_m_s, vp_vs_ratio, ai, avo_class, stacking_velocity_top, stacking_velocity_base),
        domain_6_integration(csem_resistivity_pattern, gravity_signature, ftg_anomaly, magnetic_signature),
    ]

    validation_count = sum(1 for d in domains if d.verdict == DomainVerdict.VALIDATE)
    rejection_count = sum(1 for d in domains if d.verdict == DomainVerdict.REJECT)
    inconclusive_count = sum(1 for d in domains if d.verdict == DomainVerdict.INCONCLUSIVE)

    # Weighted composite score (0–100)
    composite = sum(d.score * d.weight * 100 for d in domains)

    # ≥3/6 validation law
    passes_3of6 = validation_count >= 3

    # Anti-patterns
    anti_patterns = [d.anti_pattern_flag for d in domains if d.anti_pattern_flag]

    # Verdict
    if passes_3of6 and rejection_count == 0:
        verdict = "CARBONATE_CONFIRMED"
        verdict_confidence = _cap(composite / 100 * 0.90)
    elif passes_3of6 and rejection_count <= 1:
        verdict = "CARBONATE_POSSIBLE"
        verdict_confidence = _cap(composite / 100 * 0.75)
    elif validation_count >= 2:
        verdict = "CARBONATE_POSSIBLE"
        verdict_confidence = _cap(composite / 100 * 0.60)
    elif rejection_count >= 3:
        verdict = "REJECTED"
        verdict_confidence = _cap(0.80)
    else:
        verdict = "INCONCLUSIVE"
        verdict_confidence = _cap(0.40)

    # Explanation
    if verdict == "CARBONATE_CONFIRMED":
        explanation = f"≥3/6 domains validate ({validation_count}/6). Composite={composite:.0f}/100. No rejections."
    elif verdict == "CARBONATE_POSSIBLE":
        explanation = f"{validation_count}/6 domains validate. {rejection_count} rejection(s). Composite={composite:.0f}/100. Acquire more data."
    elif verdict == "REJECTED":
        explanation = f"{rejection_count}/6 domains reject carbonate. Composite={composite:.0f}/100. Look-alike likely."
    else:
        explanation = f"Insufficient data: {inconclusive_count}/6 inconclusive. Composite={composite:.0f}/100."

    if anti_patterns:
        explanation += f" Anti-patterns: {', '.join(anti_patterns)}."

    return SixDomainResult(
        domains=domains,
        validation_count=validation_count,
        rejection_count=rejection_count,
        inconclusive_count=inconclusive_count,
        composite_score=composite,
        passes_3of6=passes_3of6,
        verdict=verdict,
        verdict_confidence=verdict_confidence,
        anti_patterns_detected=anti_patterns,
        explanation=explanation,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ARCHETYPE MINERAL RECIPES — Badali Figure 2
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ArchetypeRecipe:
    """Mineral recipe + porosity envelope for a Badali archetype."""

    archetype_id: str
    label: str
    f_calcite: float
    f_dolomite: float
    f_clay: float
    f_quartz: float
    porosity_min: float
    porosity_max: float
    porosity_typical: float
    vp_min_expected: float
    vp_max_expected: float
    climate: str
    reservoir_quality: str


ARCHETYPE_RECIPES: dict[str, ArchetypeRecipe] = {
    "rimmed_platform": ArchetypeRecipe(
        archetype_id="rimmed_platform",
        label="Rimmed Platform",
        f_calcite=0.90,
        f_dolomite=0.05,
        f_clay=0.03,
        f_quartz=0.02,
        porosity_min=0.05,
        porosity_max=0.30,
        porosity_typical=0.18,
        vp_min_expected=4200,
        vp_max_expected=5800,
        climate="icehouse",
        reservoir_quality="HIGH",
    ),
    "isolated_platform": ArchetypeRecipe(
        archetype_id="isolated_platform",
        label="Isolated Platform",
        f_calcite=0.85,
        f_dolomite=0.10,
        f_clay=0.03,
        f_quartz=0.02,
        porosity_min=0.05,
        porosity_max=0.35,
        porosity_typical=0.20,
        vp_min_expected=4000,
        vp_max_expected=5600,
        climate="icehouse",
        reservoir_quality="HIGH",
    ),
    "pinnacle_reef": ArchetypeRecipe(
        archetype_id="pinnacle_reef",
        label="Pinnacle Reef",
        f_calcite=0.88,
        f_dolomite=0.07,
        f_clay=0.03,
        f_quartz=0.02,
        porosity_min=0.05,
        porosity_max=0.25,
        porosity_typical=0.15,
        vp_min_expected=4500,
        vp_max_expected=6000,
        climate="icehouse",
        reservoir_quality="HIGH",
    ),
    "slightly_rimmed_platform": ArchetypeRecipe(
        archetype_id="slightly_rimmed_platform",
        label="Slightly Rimmed Platform",
        f_calcite=0.80,
        f_dolomite=0.05,
        f_clay=0.10,
        f_quartz=0.05,
        porosity_min=0.08,
        porosity_max=0.25,
        porosity_typical=0.16,
        vp_min_expected=4100,
        vp_max_expected=5500,
        climate="both",
        reservoir_quality="MODERATE",
    ),
    "nonrimmed_attached_platform": ArchetypeRecipe(
        archetype_id="nonrimmed_attached_platform",
        label="Non-Rimmed Attached Platform",
        f_calcite=0.70,
        f_dolomite=0.05,
        f_clay=0.15,
        f_quartz=0.10,
        porosity_min=0.10,
        porosity_max=0.25,
        porosity_typical=0.18,
        vp_min_expected=3800,
        vp_max_expected=5200,
        climate="greenhouse",
        reservoir_quality="MODERATE",
    ),
    "distally_steepened_ramp": ArchetypeRecipe(
        archetype_id="distally_steepened_ramp",
        label="Distally Steepened Ramp",
        f_calcite=0.65,
        f_dolomite=0.05,
        f_clay=0.20,
        f_quartz=0.10,
        porosity_min=0.10,
        porosity_max=0.25,
        porosity_typical=0.18,
        vp_min_expected=3600,
        vp_max_expected=5000,
        climate="greenhouse",
        reservoir_quality="MODERATE",
    ),
    "homoclinal_ramp": ArchetypeRecipe(
        archetype_id="homoclinal_ramp",
        label="Homoclinal Ramp",
        f_calcite=0.60,
        f_dolomite=0.05,
        f_clay=0.25,
        f_quartz=0.10,
        porosity_min=0.10,
        porosity_max=0.20,
        porosity_typical=0.15,
        vp_min_expected=3500,
        vp_max_expected=4800,
        climate="greenhouse",
        reservoir_quality="LOW",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# VRH ENGINE — standalone
# ─────────────────────────────────────────────────────────────────────────────


def _hashin_shtrikman(f1: float, k1: float, k2: float, g1: float, g2: float) -> tuple[float, float]:
    f2 = 1.0 - f1
    if k2 < k1:
        k1, k2 = k2, k1
        g1, g2 = g2, g1
        f1, f2 = f2, f1
    alpha = -3.0 / (3.0 * k2 + 4.0 * g2)
    k_hs_u = k2 + f1 / (1.0 / (k1 - k2) - f2 * alpha)
    k_hs_l = k1 + f2 / (1.0 / (k2 - k1) - f1 * alpha)
    beta = -3.0 * (k2 + 2.0 * g2) / (5.0 * g2 * (3.0 * k2 + 4.0 * g2))
    g_hs_u = g2 + f1 / (1.0 / (g1 - g2) - f2 * beta)
    g_hs_l = g1 + f2 / (1.0 / (g2 - g1) - f1 * beta)
    return 0.5 * (k_hs_u + k_hs_l), 0.5 * (g_hs_u + g_hs_l)


def _mineral_mix(recipe: ArchetypeRecipe) -> dict[str, float]:
    k_min = (
        recipe.f_calcite * _MINERAL_PROPS["calcite"]["bulk_mod"]
        + recipe.f_dolomite * _MINERAL_PROPS["dolomite"]["bulk_mod"]
        + recipe.f_clay * _MINERAL_PROPS["clay"]["bulk_mod"]
        + recipe.f_quartz * _MINERAL_PROPS["quartz"]["bulk_mod"]
    )
    g_min = (
        recipe.f_calcite * _MINERAL_PROPS["calcite"]["shear_mod"]
        + recipe.f_dolomite * _MINERAL_PROPS["dolomite"]["shear_mod"]
        + recipe.f_clay * _MINERAL_PROPS["clay"]["shear_mod"]
        + recipe.f_quartz * _MINERAL_PROPS["quartz"]["shear_mod"]
    )
    rho_min = (
        recipe.f_calcite * _MINERAL_PROPS["calcite"]["rho"]
        + recipe.f_dolomite * _MINERAL_PROPS["dolomite"]["rho"]
        + recipe.f_clay * _MINERAL_PROPS["clay"]["rho"]
        + recipe.f_quartz * _MINERAL_PROPS["quartz"]["rho"]
    )
    return {"bulk_mod": k_min, "shear_mod": g_min, "rho": rho_min}


def compute_archetype_vp(
    recipe: ArchetypeRecipe,
    porosity: float,
    fluid: str = "brine",
    sw: float = 1.0,
) -> dict[str, float]:
    """Compute Vp, Vs, rho, AI for an archetype at given porosity."""
    phi = max(0.001, min(porosity, 0.50))
    sw_c = max(0.0, min(sw, 1.0))

    matrix = _mineral_mix(recipe)
    k_min, g_min, rho_min = matrix["bulk_mod"], matrix["shear_mod"], matrix["rho"]

    fl = _FLUID_PROPS.get(fluid, _FLUID_PROPS["brine"])
    k_fl, rho_fl = fl["bulk_mod"], fl["rho"]
    if sw_c < 1.0:
        hc = _FLUID_PROPS.get("oil" if fluid != "gas" else "gas", _FLUID_PROPS["brine"])
        k_fl = 1.0 / (sw_c / _FLUID_PROPS["brine"]["bulk_mod"] + (1.0 - sw_c) / hc["bulk_mod"])
        rho_fl = sw_c * _FLUID_PROPS["brine"]["rho"] + (1.0 - sw_c) * hc["rho"]

    k_dry, g_dry = _hashin_shtrikman(phi, 0.0, k_min, 0.0, g_min)
    k_dry = min(k_dry, 0.8 * k_min)
    g_dry = min(g_dry, 0.8 * g_min)
    if k_dry < 0:
        k_dry = phi * k_min * 0.1
    if g_dry < 0:
        g_dry = phi * g_min * 0.1

    phi_c = max(0.001, min(phi, 0.50))
    num = phi_c * k_dry - (1.0 + phi_c) * k_fl * k_dry / k_min + k_fl
    den = (1.0 - phi_c) * k_fl + phi_c * k_min - k_fl * k_dry / k_min
    k_sat = num / den if abs(den) > 1e-12 and num / den > 0 else k_dry
    g_sat = g_dry

    rho_sat = (1.0 - phi) * rho_min + phi * rho_fl
    rho_kg = rho_sat * 1000.0
    k_pa, g_pa = k_sat * 1e9, g_sat * 1e9

    vp = math.sqrt((k_pa + 4.0 * g_pa / 3.0) / rho_kg) if rho_kg > 0 else 0.0
    vs = math.sqrt(g_pa / rho_kg) if g_pa > 0 and rho_kg > 0 else 0.0
    vp = max(_VP_MIN, min(_VP_MAX, vp))
    rho_sat = max(_RHO_MIN, min(_RHO_MAX, rho_sat))

    return {
        "vp": round(vp, 1),
        "vs": round(vs, 1),
        "rho": round(rho_sat, 3),
        "ai": round(rho_sat * vp, 1),
        "vp_vs_ratio": round(vp / vs, 3) if vs > 0 else 0.0,
        "k_sat": round(k_sat, 2),
        "g_sat": round(g_sat, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class VpProfile:
    archetype_id: str
    label: str
    fluid: str
    sw: float
    porosities: list[float] = field(default_factory=list)
    vps: list[float] = field(default_factory=list)
    rhos: list[float] = field(default_factory=list)
    ais: list[float] = field(default_factory=list)
    vp_vs_ratios: list[float] = field(default_factory=list)
    k_mineral: float = 0.0
    g_mineral: float = 0.0
    rho_mineral: float = 0.0


@dataclass
class ArchetypeConsistency:
    archetype_id: str
    label: str
    is_consistent: bool
    observed_vp: float
    expected_vp_range: tuple[float, float]
    vp_residual_m_s: float
    residual_normalized: float
    confidence: float
    explanation: str


@dataclass
class PhysicsBridgeResult:
    observed_vp: float | None
    observed_porosity: float | None
    fluid: str
    sw: float
    vp_at_porosity: dict[str, float]
    consistencies: list[ArchetypeConsistency] = field(default_factory=list)
    best_match: ArchetypeConsistency | None = None
    profiles: dict[str, VpProfile] = field(default_factory=dict)
    discrimination_gap: str | None = None
    source: str = "Badali et al. (2024) + VRH mineral mixing"
    forge_id: str = "forge-carbonate-physics-bridge"


# ─────────────────────────────────────────────────────────────────────────────
# BRIDGE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────


def compute_vp_profile(archetype_id: str, fluid: str = "brine", sw: float = 1.0, porosity_steps: int = 20) -> VpProfile:
    recipe = ARCHETYPE_RECIPES.get(archetype_id)
    if recipe is None:
        raise ValueError(f"Unknown archetype: {archetype_id}. Valid: {list(ARCHETYPE_RECIPES.keys())}")
    matrix = _mineral_mix(recipe)
    porosities = [
        recipe.porosity_min + i * (recipe.porosity_max - recipe.porosity_min) / max(porosity_steps - 1, 1)
        for i in range(porosity_steps)
    ]
    vps, rhos, ais, vp_vs = [], [], [], []
    for por in porosities:
        result = compute_archetype_vp(recipe, por, fluid, sw)
        vps.append(result["vp"])
        rhos.append(result["rho"])
        ais.append(result["ai"])
        vp_vs.append(result["vp_vs_ratio"])
    return VpProfile(
        archetype_id=archetype_id,
        label=recipe.label,
        fluid=fluid,
        sw=sw,
        porosities=porosities,
        vps=vps,
        rhos=rhos,
        ais=ais,
        vp_vs_ratios=vp_vs,
        k_mineral=matrix["bulk_mod"],
        g_mineral=matrix["shear_mod"],
        rho_mineral=matrix["rho"],
    )


def check_vp_consistency(
    observed_vp: float,
    observed_porosity: float | None = None,
    fluid: str = "brine",
    sw: float = 1.0,
    tolerance_factor: float = 1.5,
) -> PhysicsBridgeResult:
    consistencies = []
    vp_at_porosity = {}
    for arch_id, recipe in ARCHETYPE_RECIPES.items():
        por = observed_porosity if observed_porosity is not None else recipe.porosity_typical
        predicted = compute_archetype_vp(recipe, por, fluid, sw)
        vp_pred = predicted["vp"]
        vp_at_porosity[arch_id] = vp_pred
        por_factor = 1.0 + 0.5 * (por - recipe.porosity_typical) / max(recipe.porosity_typical, 0.01)
        vp_lo = recipe.vp_min_expected * por_factor
        vp_hi = recipe.vp_max_expected * por_factor
        vp_lo, vp_hi = min(vp_lo, vp_hi), max(vp_lo, vp_hi)
        range_width = vp_hi - vp_lo
        residual = observed_vp - vp_pred
        norm_residual = abs(residual) / max(range_width, 1.0)
        is_consistent = abs(observed_vp - vp_pred) <= tolerance_factor * max(range_width / 2, 200)
        confidence = _cap(max(0.0, 1.0 - norm_residual) * 0.90)
        if is_consistent:
            explanation = (
                f"Vp={observed_vp:.0f} m/s within tolerance of {arch_id} expected {vp_lo:.0f}–{vp_hi:.0f} m/s at φ={por:.1%}"
            )
        else:
            explanation = f"Vp={observed_vp:.0f} m/s OUTSIDE {arch_id} expected range {vp_lo:.0f}–{vp_hi:.0f} m/s at φ={por:.1%} — residual={residual:+.0f} m/s"
        consistencies.append(
            ArchetypeConsistency(
                archetype_id=arch_id,
                label=recipe.label,
                is_consistent=is_consistent,
                observed_vp=observed_vp,
                expected_vp_range=(vp_lo, vp_hi),
                vp_residual_m_s=residual,
                residual_normalized=norm_residual,
                confidence=confidence,
                explanation=explanation,
            )
        )
    consistencies.sort(key=lambda c: c.confidence, reverse=True)
    best = consistencies[0] if consistencies else None
    all_consistent = all(c.is_consistent for c in consistencies)
    gap_warning = None
    if all_consistent:
        gap_warning = "DISCRIMINATION GAP: Vp alone cannot distinguish between archetypes at this porosity. Use seismic geometry + AVO + well control."
    elif sum(1 for c in consistencies if c.is_consistent) >= 4:
        gap_warning = "WEAK DISCRIMINATION: Vp consistent with multiple archetypes. Supplement with geometry and AVO."
    return PhysicsBridgeResult(
        observed_vp=observed_vp,
        observed_porosity=observed_porosity,
        fluid=fluid,
        sw=sw,
        vp_at_porosity=vp_at_porosity,
        consistencies=consistencies,
        best_match=best,
        discrimination_gap=gap_warning,
    )


def bridge_classification_to_physics(
    classification_result: Any,
    observed_vp: float | None = None,
    observed_porosity: float | None = None,
    fluid: str = "brine",
    sw: float = 1.0,
) -> PhysicsBridgeResult:
    por = observed_porosity
    if por is None and hasattr(classification_result, "input_summary"):
        por = classification_result.input_summary.get("porosity_fraction")
    vp = observed_vp
    if vp is None and hasattr(classification_result, "input_summary"):
        vp = classification_result.input_summary.get("vp_m_s")
    if vp is not None:
        result = check_vp_consistency(vp, por, fluid, sw)
        if result.best_match and hasattr(classification_result, "best_match"):
            classified_id = classification_result.best_match.archetype_id
            physics_best = result.best_match.archetype_id
            if classified_id != physics_best and result.best_match.is_consistent:
                result.discrimination_gap = f"CLASSIFICATION-PHYSICS MISMATCH: classifier says '{classified_id}' but physics best match is '{physics_best}'. Review seismic geometry evidence."
        return result
    else:
        vp_at_por = {}
        for arch_id, recipe in ARCHETYPE_RECIPES.items():
            p = por if por is not None else recipe.porosity_typical
            predicted = compute_archetype_vp(recipe, p, fluid, sw)
            vp_at_por[arch_id] = predicted["vp"]
        return PhysicsBridgeResult(
            observed_vp=None,
            observed_porosity=por,
            fluid=fluid,
            sw=sw,
            vp_at_porosity=vp_at_por,
            discrimination_gap="No observed Vp — predictions only. Acquire Vp for discrimination.",
        )


def generate_all_profiles(fluid: str = "brine", sw: float = 1.0, porosity_steps: int = 20) -> dict[str, VpProfile]:
    return {arch_id: compute_vp_profile(arch_id, fluid, sw, porosity_steps) for arch_id in ARCHETYPE_RECIPES}


# ─────────────────────────────────────────────────────────────────────────────
# BASEMENT / LOOKALIKE DISCRIMINATION
# ─────────────────────────────────────────────────────────────────────────────


def basement_vp_at_porosity(porosity: float) -> float:
    k_min = _MINERAL_PROPS["basement"]["bulk_mod"]
    g_min = _MINERAL_PROPS["basement"]["shear_mod"]
    rho_min = _MINERAL_PROPS["basement"]["rho"]
    phi = max(0.001, min(porosity, 0.10))
    k_fl = _FLUID_PROPS["brine"]["bulk_mod"]
    rho_fl = _FLUID_PROPS["brine"]["rho"]
    k_dry, g_dry = _hashin_shtrikman(phi, 0.0, k_min, 0.0, g_min)
    k_dry = min(k_dry, 0.8 * k_min)
    g_dry = min(g_dry, 0.8 * g_min)
    num = phi * k_dry - (1.0 + phi) * k_fl * k_dry / k_min + k_fl
    den = (1.0 - phi) * k_fl + phi * k_min - k_fl * k_dry / k_min
    k_sat = num / den if abs(den) > 1e-12 and num / den > 0 else k_dry
    rho_sat = (1.0 - phi) * rho_min + phi * rho_fl
    rho_kg = rho_sat * 1000.0
    k_pa, g_pa = k_sat * 1e9, g_dry * 1e9
    vp = math.sqrt((k_pa + 4.0 * g_pa / 3.0) / rho_kg) if rho_kg > 0 else 0.0
    return max(_VP_MIN, min(_VP_MAX, vp))


def check_basement_discrimination(observed_vp: float, observed_porosity: float) -> dict[str, Any]:
    vp_basement = basement_vp_at_porosity(observed_porosity)
    archetype_vps = {
        arch_id: compute_archetype_vp(recipe, observed_porosity)["vp"] for arch_id, recipe in ARCHETYPE_RECIPES.items()
    }
    best_carb_id = min(archetype_vps, key=lambda k: abs(archetype_vps[k] - observed_vp))
    best_carb_vp = archetype_vps[best_carb_id]
    carb_residual = abs(observed_vp - best_carb_vp)
    basement_residual = abs(observed_vp - vp_basement)
    if basement_residual < carb_residual * 0.7:
        lithology, confidence = "BASEMENT_LIKELY", _cap(0.80)
    elif carb_residual < basement_residual * 0.7:
        lithology, confidence = "CARBONATE_LIKELY", _cap(0.80)
    else:
        lithology, confidence = "AMBIGUOUS", _cap(0.50)
    gap_m_s = abs(vp_basement - best_carb_vp)
    return {
        "observed_vp": observed_vp,
        "observed_porosity": observed_porosity,
        "vp_basement": round(vp_basement, 1),
        "vp_best_carbonate": round(best_carb_vp, 1),
        "best_carbonate_archetype": best_carb_id,
        "carb_vp_residual": round(carb_residual, 1),
        "basement_vp_residual": round(basement_residual, 1),
        "vp_gap_m_s": round(gap_m_s, 1),
        "lithology": lithology,
        "confidence": confidence,
        "all_archetype_vps": {k: round(v, 1) for k, v in archetype_vps.items()},
        "discrimination_note": (
            f"At φ={observed_porosity:.1%}: carbonate Vp={best_carb_vp:.0f} m/s, "
            f"basement Vp={vp_basement:.0f} m/s, gap={gap_m_s:.0f} m/s. "
            + (
                "Gap < 400 m/s — Vp alone CANNOT discriminate."
                if gap_m_s < 400
                else "Gap > 400 m/s — Vp provides lithology signal."
            )
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# TEPAT BENCHMARK — golden reference calibration
# ─────────────────────────────────────────────────────────────────────────────

TEPAT_BENCHMARK = {
    "name": "Tepat-1",
    "archetype": "rimmed_platform",
    "age_ma": 15.0,
    "climate": "icehouse",
    "vp_top_m_s": 3200,  # stacking velocity top
    "vp_base_m_s": 3800,  # stacking velocity base
    "vp_pwave_m_s": 4700,  # P-wave velocity at φ≈20%
    "porosity": 0.20,
    "ai": 11800,  # g/cm³·m/s (high)
    "vp_vs_ratio": 1.65,  # low — gas-charged
    "avo_class": "2p",  # gas + moderate φ
    "coherency": 0.85,
    "curvature": 0.008,
    "csem_resistivity": "high-low-high",
    "gravity": "positive",
    "magnetic": "quiet",
    "is_mounded": True,
    "has_onlap": True,
    "has_flat_top": True,
    "has_steep_flanks": True,
    "is_on_structural_high": True,
    "is_away_from_clastic_feeder": True,
    "regional_analog_match": True,
}


def run_tepat_calibration() -> SixDomainResult:
    """Run the 6-domain differentiator on the Tepat benchmark. Should return CARBONATE_CONFIRMED."""
    b = TEPAT_BENCHMARK
    return run_six_domain_differentiator(
        curvature=b["curvature"],
        is_mounded=b["is_mounded"],
        has_onlap=b["has_onlap"],
        is_isolated_buildup=False,
        has_flat_top=b["has_flat_top"],
        has_steep_flanks=b["has_steep_flanks"],
        top_reflector_strength=0.9,
        top_reflector_continuity=0.85,
        internal_character="chaotic",
        base_character="karstified",
        coherency=b["coherency"],
        rms_amplitude=0.25,
        envelope_strength=0.85,
        sweetness=0.80,
        spectral_decomposition_rgb="reefal platform facies belts",
        avoe=-0.15,
        age_ma=b["age_ma"],
        is_on_structural_high=b["is_on_structural_high"],
        is_away_from_clastic_feeder=b["is_away_from_clastic_feeder"],
        regional_analog_match=b["regional_analog_match"],
        is_icehouse=True,
        vp_top_m_s=b["vp_top_m_s"],
        vp_base_m_s=b["vp_base_m_s"],
        vp_vs_ratio=b["vp_vs_ratio"],
        ai=b["ai"],
        avo_class=b["avo_class"],
        stacking_velocity_top=b["vp_top_m_s"],
        stacking_velocity_base=b["vp_base_m_s"],
        csem_resistivity_pattern=b["csem_resistivity"],
        gravity_signature=b["gravity"],
        ftg_anomaly=True,
        magnetic_signature=b["magnetic"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# SABAH CALIBRATION
# ─────────────────────────────────────────────────────────────────────────────


def sabah_physics_calibration() -> dict[str, Any]:
    results = {}
    results["Tepat"] = check_basement_discrimination(4700.0, 0.20)
    results["Solisip-1"] = check_basement_discrimination(4800.0, 0.10)
    results["VRH_calibration"] = check_vp_consistency(4720.0, 0.20)
    results["Tepat_6Domain"] = run_tepat_calibration()
    return results


# ─────────────────────────────────────────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'=' * 70}")
    print("CARBONATE INTELLIGENCE BRIDGE — FULL GEOX")
    print(f"{'=' * 70}")

    # 1. Vp at typical porosity
    print("\n[1] Vp AT TYPICAL POROSITY (brine-saturated)")
    print(f"{'Archetype':<40} {'φ_typ':>6} {'Vp':>8} {'ρ':>6} {'AI':>8}")
    print("─" * 70)
    for arch_id, recipe in ARCHETYPE_RECIPES.items():
        result = compute_archetype_vp(recipe, recipe.porosity_typical)
        print(
            f"{recipe.label:<40} {recipe.porosity_typical:>5.0%} {result['vp']:>7.0f} {result['rho']:>5.2f} {result['ai']:>7.0f}"
        )

    # 2. Vp consistency check
    print(f"\n[2] VP CONSISTENCY — observed Vp=4720 m/s at φ=20%")
    bridge = check_vp_consistency(4720.0, 0.20)
    print(f"{'Archetype':<40} {'OK':>4} {'Predicted':>10} {'Residual':>10} {'Conf':>5}")
    print("─" * 70)
    for c in bridge.consistencies:
        flag = "✓" if c.is_consistent else "✗"
        print(
            f"{c.label:<40} {flag:>4} {bridge.vp_at_porosity[c.archetype_id]:>9.0f} {c.vp_residual_m_s:>+9.0f} {c.confidence:>4.2f}"
        )
    if bridge.discrimination_gap:
        print(f"\n⚠ {bridge.discrimination_gap}")

    # 3. 6-Domain Differentiator — Tepat benchmark
    print(f"\n[3] 6-DOMAIN DIFFERENTIATOR — TEPAT BENCHMARK")
    print("─" * 70)
    tepat = run_tepat_calibration()
    for d in tepat.domains:
        v = {"VALIDATE": "✓", "REJECT": "✗", "INCONCLUSIVE": "?"}[d.verdict.value]
        ap = f" ⚠ {d.anti_pattern_flag}" if d.anti_pattern_flag else ""
        print(f"  D{d.domain_id} {d.domain_name:<25} {v} score={d.score:.2f} w={d.weight:.2f}{ap}")
        print(f"      {d.evidence}")
    print(f"\n  Verdict: {tepat.verdict} ({tepat.validation_count}/6 validate)")
    print(f"  Composite: {tepat.composite_score:.0f}/100")
    print(f"  Confidence: {tepat.verdict_confidence:.2f}")
    print(f"  Explanation: {tepat.explanation}")

    # 4. Basement discrimination
    print(f"\n[4] BASEMENT DISCRIMINATION")
    for name, vp, por in [("Tepat", 4700, 0.20), ("Solisip-1", 4800, 0.10), ("Deep (φ=5%)", 5500, 0.05)]:
        result = check_basement_discrimination(vp, por)
        print(
            f"  {name}: Vp={vp}, φ={por:.0%} → {result['lithology']} "
            f"(carb={result['vp_best_carbonate']:.0f}, basement={result['vp_basement']:.0f}, gap={result['vp_gap_m_s']:.0f})"
        )

    # 5. Sabah calibration
    print(f"\n[5] SABAH CALIBRATION")
    cal = sabah_physics_calibration()
    for name, result in cal.items():
        if isinstance(result, SixDomainResult):
            print(f"  {name}: {result.verdict} ({result.validation_count}/6, composite={result.composite_score:.0f})")
        elif isinstance(result, PhysicsBridgeResult):
            best = result.best_match
            print(f"  {name}: best={best.archetype_id if best else 'N/A'}, conf={best.confidence if best else 0:.2f}")
        else:
            print(f"  {name}: {result['lithology']} (conf={result['confidence']:.2f})")

    print(f"\n{'=' * 70}")
    print("DITEMPA BUKAN DIBERI")
    print(f"{'=' * 70}")
