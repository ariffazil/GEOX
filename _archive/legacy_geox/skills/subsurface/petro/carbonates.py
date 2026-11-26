"""
Carbonate Archetype Discrimination Engine
==========================================
Applies Badali et al. (2024) 7-type carbonate taxonomy (Figure 2) to seismic
interpretation, VLM inference, and rock physics data.

Evidence-only: returns archetype classification + confidence + false-positive
warnings. Does NOT make drill decisions.

Source: Badali et al. (2024), SEG Interpretation, Figure 2
DOI: 10.1190/INT-2023-0014.1
29 carbonate case studies across Icehouse/Greenhouse climates.

DITEMPA BUKAN DIBERI — Forged, Not Given.
F2 TRUTH: all confidence scores hard-capped at 0.90 (F7 HUMILITY).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# DATA PATH — archetypes JSON lives alongside this module
# ─────────────────────────────────────────────────────────────────────────────
_ARCHETYPES_JSON = Path(__file__).parent / "carbonate_archetypes.json"

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────


class ClimateRegime(Enum):
    ICEHOUSE = "Icehouse (I)"
    GREENHOUSE = "Greenhouse (G)"
    UNKNOWN = "unknown"


class ArchetypeID(Enum):
    HOMOCLINAL_RAMP = "homoclinal_ramp"
    DISTRALLY_STEEPENED_RAMP = "distally_steepened_ramp"
    NONRIMMED_ATTACHED_PLATFORM = "nonrimmed_attached_platform"
    SLIGHTLY_RIMMED_PLATFORM = "slightly_rimmed_platform"
    RIMMED_PLATFORM = "rimmed_platform"
    ISOLATED_PLATFORM = "isolated_platform"
    PINNACLE_REEF = "pinnacle_reef"
    UNKNOWN = "unknown"


@dataclass
class ArchetypeMatch:
    archetype_id: str
    label: str
    confidence: float  # 0.0–0.90 (F7 HUMILITY cap)
    rimmed_score: float
    isolation_score: float
    slope_angle_deg: str
    key_features: list[str]
    false_positive_warnings: list[str]
    sabah_relevance: str
    is_sabah_relevant: bool


@dataclass
class DiscriminationResult:
    """Full discrimination output for a carbonate seismic interpretation."""

    # Input summary
    input_summary: dict[str, Any]

    # Climate
    climate_regime: ClimateRegime
    climate_confidence: float

    # Top match
    best_match: ArchetypeMatch

    # All candidates (sorted by confidence descending)
    all_candidates: list[ArchetypeMatch]

    # False-positive check
    false_positive_risks: dict[str, float]  # lookalike → risk score 0–1
    top_false_positive: str | None

    # Decision
    verdict: str  # "CARBONATE_CONFIRMED" / "CARBONATE_POSSIBLE" / "EXPLORATORY" / "NON_CARBONATE_SUSPECTED"
    verdict_confidence: float  # 0.0–0.90
    discrimination_confidence: float  # how confident we are in the discrimination
    next_steps: list[str]

    # Metadata
    archetypes_source: str = "Badali et al. (2024) Figure 2"
    forge_id: str = "forge-sabah-carbonate"
    vaul999_id: str = "8b0c7a711dee4f7f"


# ─────────────────────────────────────────────────────────────────────────────
# ARCHETYPE LIBRARY (lazy-loaded from JSON)
# ─────────────────────────────────────────────────────────────────────────────

_library: dict[str, Any] | None = None


def _load_library() -> dict[str, Any]:
    global _library
    if _library is None:
        with open(_ARCHETYPES_JSON) as f:
            _library = json.load(f)
    # F7 HUMILITY: assert non-None after load
    assert _library is not None, "Failed to load archetype library"
    return _library


# ─────────────────────────────────────────────────────────────────────────────
# SCORING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_HUMILITY_CAP = 0.90  # F7 HUMILITY hard cap


def _cap(value: float) -> float:
    """Apply F7 HUMILITY cap."""
    return min(value, _HUMILITY_CAP)


def _slope_score(input_angle: float, expected_min: float, expected_max: float) -> float:
    """How well does the observed slope angle match the expected range."""
    if expected_min <= input_angle <= expected_max:
        return 1.0
    # Linear decay outside range
    if input_angle < expected_min:
        gap = expected_min - input_angle
        return max(0.0, 1.0 - gap / expected_min)
    else:
        gap = input_angle - expected_max
        return max(0.0, 1.0 - gap / expected_max)


def _rim_score(input_rim_score: float, expected_rim_score: float) -> float:
    """How well does the rim score match."""
    diff = abs(input_rim_score - expected_rim_score)
    return max(0.0, 1.0 - diff)


def _isolation_score(input_isolated: bool, expected_isolated: bool) -> float:
    """Perfect match if both agree on isolation."""
    return 1.0 if input_isolated == expected_isolated else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MAIN DISCRIMINATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────


def classify_carbonate_structure(
    # ── Seismic / structural inputs ──────────────────────────────────────────
    age_ma: float | None = None,
    climate_regime: ClimateRegime | None = None,
    is_attached: bool | None = None,
    is_isolated: bool | None = None,
    has_strong_rim: bool | None = None,
    has_weak_rim: bool | None = None,
    slope_angle_deg: float | None = None,
    has_megabreccias: bool = False,
    has_karst: bool = False,
    has_progradation: bool = False,
    has_chaotic_surface: bool = False,
    thickness_m: float | None = None,
    # ── Physics inputs ──────────────────────────────────────────────────────
    vp_m_s: float | None = None,
    porosity_fraction: float | None = None,
    # ── Context ─────────────────────────────────────────────────────────────
    sabah_mode: bool = True,  # apply Sabah-specific guidance
    source: str = "seismic_interpretation",  # "seismic_interpretation" | "vlm" | "well_control"
) -> DiscriminationResult:
    """
    Classify a seismic feature as a carbonate archetype using Badali (2024).

    Parameters
    ----------
    age_ma : float, optional
        Seismic age context in Ma. Miocene (>5.3) → Icehouse; Eocene-early Oligocene
        (56–30 Ma) → Greenhouse; Oligocene transitional.
    climate_regime : ClimateRegime, optional
        Explicit climate regime if known from biostratigraphy or sequence stratigraphy.
    is_attached : bool, optional
        Is the carbonate build-up attached to hinterland (vs isolated in deep water)?
    is_isolated : bool, optional
        Is it isolated in deep water? (mutually exclusive with is_attached)
    has_strong_rim : bool, optional
        Is there a well-developed high-amplitude rim crest?
    has_weak_rim : bool, optional
        Is there a subtle rim crest?
    slope_angle_deg : float, optional
        Margin slope angle measured from seismic. Key discriminator.
    has_megabreccias : bool
        Are there megabreccia packages on the slope? (Icehouse indicator)
    has_karst : bool
        Are there karst collapse features? (Icehouse / exposure indicator)
    has_progradation : bool
        Are there progradation packages? (platform growth indicator)
    has_chaotic_surface : bool
        Is there a chaotic surface with no coherent geometry? (FALSE POSITIVE flag)
    thickness_m : float, optional
        Estimated carbonate thickness from seismic.
    vp_m_s : float, optional
        Measured or inferred Vp in m/s from well control or inversion.
    porosity_fraction : float, optional
        Estimated porosity (0.0–1.0) from rock physics or well control.
    sabah_mode : bool
        Apply Sabah-specific discrimination guidance (Operator overrides).
    source : str
        Source of interpretation for provenance tracking.

    Returns
    -------
    DiscriminationResult
        Full discrimination output: archetype match, false-positive risks,
        verdict, next steps. All confidence scores capped at 0.90 (F7 HUMILITY).

    Notes
    -----
    F2 TRUTH: confidence scores hard-capped at 0.90 via F7 HUMILITY.
    F9 ANTI-HANTU: this is a classification tool, not a geological intuition.
    Evidence-only: always pair with rock physics + well control for confirmation.
    """

    lib = _load_library()
    archetypes = lib["archetypes"]

    # ── Step 1: Climate regime ──────────────────────────────────────────────
    if climate_regime is None and age_ma is not None:
        if age_ma <= 5.3 or (13 <= age_ma <= 30):
            # Miocene (5.3–23 Ma) + Oligocene (23–33.9 Ma) → Icehouse dominant
            climate_regime = ClimateRegime.ICEHOUSE
            climate_confidence = _cap(0.80)
        elif 33.9 <= age_ma <= 56:
            # Eocene-early Oligocene → Greenhouse
            climate_regime = ClimateRegime.GREENHOUSE
            climate_confidence = _cap(0.75)
        else:
            climate_regime = ClimateRegime.UNKNOWN
            climate_confidence = 0.30
    elif climate_regime is None:
        climate_regime = ClimateRegime.UNKNOWN
        climate_confidence = 0.20
    else:
        climate_confidence = _cap(0.85)

    # ── Step 2: Score each archetype ────────────────────────────────────────
    candidates: list[tuple[str, float, ArchetypeMatch]] = []

    for arch in archetypes:
        score = 0.0
        feature_matches: list[str] = []
        warnings: list[str] = []
        factors: list[str] = []

        # ── Climate filter ─────────────────────────────────────────────────
        if climate_regime == ClimateRegime.ICEHOUSE:
            icehouse_archetypes = ["rimmed_platform", "isolated_platform", "pinnacle_reef"]
            if arch["id"] in icehouse_archetypes:
                score += 0.30
                factors.append("climate_icehouse_match")
            else:
                score += 0.05
                factors.append("climate_mismatch")
        elif climate_regime == ClimateRegime.GREENHOUSE:
            greenhouse_archetypes = [
                "homoclinal_ramp",
                "distally_steepened_ramp",
                "nonrimmed_attached_platform",
            ]
            if arch["id"] in greenhouse_archetypes:
                score += 0.30
                factors.append("climate_greenhouse_match")
            else:
                score += 0.05
                factors.append("climate_mismatch")
        else:
            score += 0.10  # unknown climate — no penalty

        # ── Attachment filter ──────────────────────────────────────────────
        if is_attached is not None and is_isolated is not None:
            if is_attached and arch["attached_score"] >= 0.5:
                score += 0.15
                factors.append("attached_match")
            elif is_isolated and arch["isolation_score"] >= 0.5:
                score += 0.15
                factors.append("isolated_match")
            elif is_attached and arch["attached_score"] < 0.5:
                score -= 0.10
                factors.append("attached_mismatch")
            elif is_isolated and arch["isolation_score"] < 0.5:
                score -= 0.10
                factors.append("isolated_mismatch")

        # ── Rim filter ─────────────────────────────────────────────────────
        if has_strong_rim and arch["rimmed_score"] >= 0.7:
            score += 0.20
            factors.append("strong_rim_match")
        elif has_weak_rim and 0.2 <= arch["rimmed_score"] <= 0.4:
            score += 0.15
            factors.append("weak_rim_match")
        elif has_strong_rim and arch["rimmed_score"] < 0.3:
            score -= 0.15
            factors.append("strong_rim_mismatch")

        # ── Slope angle ────────────────────────────────────────────────────
        if slope_angle_deg is not None:
            try:
                min_angle = float(arch["slope_angle_deg"].split("-")[0].replace(">", ""))
                max_angle = float(arch["slope_angle_deg"].split("-")[1]) if "-" in arch["slope_angle_deg"] else min_angle + 30
                slope_s = _slope_score(slope_angle_deg, min_angle, max_angle)
                score += slope_s * 0.25
                if slope_s > 0.8:
                    factors.append(f"slope_match_{arch['slope_angle_deg']}")
            except (ValueError, IndexError):
                pass

        # ── Feature checklist ──────────────────────────────────────────────
        if has_megabreccias:
            if arch["id"] in ["rimmed_platform", "isolated_platform", "distally_steepened_ramp"]:
                score += 0.10
                feature_matches.append("megabreccias_present")
            else:
                score -= 0.05

        if has_karst:
            if arch["id"] in ["rimmed_platform", "isolated_platform", "pinnacle_reef"]:
                score += 0.08
                feature_matches.append("karst_present")
            else:
                score -= 0.05

        if has_progradation:
            if arch["id"] in ["rimmed_platform", "distally_steepened_ramp", "nonrimmed_attached_platform"]:
                score += 0.05
                feature_matches.append("progradation_present")

        if has_chaotic_surface:
            # Negative signal — this is a non-carbonate indicator
            score -= 0.25
            warnings.append(f"CHAOTIC_SURFACE: {arch['id']} unlikely; check mud volcano / volcanic intrusion")
            factors.append("chaotic_surface_negative")

        # ── Vp-porosity physics filter ─────────────────────────────────────
        if vp_m_s is not None and porosity_fraction is not None:
            # Simple VRH-inspired check: carbonate at given porosity should be in a range
            # Vp for calcite = 6400 m/s, brine = 1600 m/s
            # At 20% porosity: ~4720 m/s (our earlier computation)
            # Basement/igneous: >5500 m/s regardless of porosity
            expected_vp = 6400 * (1 - porosity_fraction) + 1600 * porosity_fraction
            vp_diff = abs(vp_m_s - expected_vp)
            if vp_diff < 400:  # within 400 m/s
                score += 0.15
                factors.append("vp_porosity_match")
            elif vp_m_s > 5500 and porosity_fraction < 0.15:
                warnings.append(f"Vp={vp_m_s:.0f} m/s + φ={porosity_fraction:.1%} — overlaps basement; cannot confirm carbonate")
                score -= 0.20
                factors.append("vp_basement_overlap")

        # ── Thickness filter ───────────────────────────────────────────────
        if thickness_m is not None:
            try:
                thick_parts = arch["typical_thickness_m"].split("-")
                thick_min = float(thick_parts[0].replace(">", ""))
                thick_max = float(thick_parts[1]) if len(thick_parts) > 1 else thick_min + 1000
                if thick_min <= thickness_m <= thick_max:
                    score += 0.05
                    factors.append("thickness_in_range")
            except (ValueError, IndexError):
                pass

        # ── Normalize score to 0–1 ─────────────────────────────────────────
        max_possible = 0.30 + 0.15 + 0.20 + 0.25 + 0.10 + 0.08 + 0.05 + 0.15 + 0.05  # = 1.33
        normalized = max(0.0, min(1.0, score / max_possible))

        # Apply F7 HUMILITY cap
        confidence = _cap(normalized * 0.90 / 0.75)  # scale so good matches hit ~0.85

        # ── False-positive warnings ────────────────────────────────────────
        if arch["mud_volcano_risk"] == "HIGH":
            warnings.append("HIGH mud volcano false-positive risk — requires AVO or well control")
        if arch.get("volcanic_intrusion_risk") == "HIGH":
            warnings.append("HIGH volcanic intrusion false-positive risk — requires Vp or magnetic data")
        if arch["discrimination_confidence"].startswith("LOW"):
            warnings.append(f"LOW discrimination confidence for {arch['id']} — confirm with well control")

        # ── Sabah relevance ────────────────────────────────────────────────
        sabah_relevant = sabah_mode and arch.get("sabah_relevance") not in [None, "", "Oligocene pre-collision; broad shelf ramp"]

        match = ArchetypeMatch(
            archetype_id=arch["id"],
            label=arch["label"],
            confidence=confidence,
            rimmed_score=arch["rimmed_score"],
            isolation_score=arch["isolation_score"],
            slope_angle_deg=arch["slope_angle_deg"],
            key_features=feature_matches,
            false_positive_warnings=warnings,
            sabah_relevance=arch.get("sabah_relevance", ""),
            is_sabah_relevant=sabah_relevant,
        )
        candidates.append((arch["id"], normalized, match))

    # ── Sort by score ────────────────────────────────────────────────────────
    candidates.sort(key=lambda x: x[1], reverse=True)

    top_id, top_score, top_match = candidates[0]
    all_matches = [m for _, _, m in candidates]

    # ── False-positive risk summary ─────────────────────────────────────────
    false_positive_risks: dict[str, float] = {}
    lookalikes = lib["false_positive_risk_matrix"]["carbonat_lookalikes"]

    # Evaluate each lookalike
    for lookalike_name, lookalike_data in lookalikes.items():
        risk = 0.0
        if lookalike_data["risk_level"] == "HIGH":
            risk = 0.7
        elif lookalike_data["risk_level"] == "MODERATE":
            risk = 0.4
        else:
            risk = 0.1

        # Adjust based on archetype match
        if top_id in lookalike_data["mimics"]:
            # SABAH MODE: Steep slopes (30-70°) are EXPECTED for icehouse Rimmed Platform,
            # Isolated Platform, and Pinnacle Reef — mimic penalty only fires if slope is
            # OUTSIDE the archetype's expected range (i.e., > 70° for RP/IP, > 60° for pinnacle).
            if lookalike_name == "volcanic_intrusion" and sabah_mode:
                expected_top = top_id in ("rimmed_platform", "isolated_platform", "pinnacle_reef")
                slope_upper = {"rimmed_platform": 70, "isolated_platform": 70, "pinnacle_reef": 60}.get(top_id, 40)
                if expected_top and slope_angle_deg is not None and slope_angle_deg <= slope_upper:
                    pass  # expected geometry — no mimic penalty
                elif expected_top and slope_angle_deg is not None and slope_angle_deg > slope_upper:
                    risk = min(1.0, risk + 0.2)  # outside expected range
                else:
                    risk = min(1.0, risk + 0.2)  # unknown slope, apply mimic penalty
            else:
                risk = min(1.0, risk + 0.2)

        # Adjust based on input signals
        if lookalike_name == "mud_volcano":
            if has_chaotic_surface and not sabah_mode:
                risk = min(1.0, risk + 0.3)
            # SABAH MODE: megabreccias + strong rim + karst = carbonate factory signals.
            # In sabah_mode, do NOT inflate mud volcano risk from these — they are carbonate evidence.
            if sabah_mode and has_megabreccias:
                risk = max(0.0, risk - 0.2)
            if sabah_mode and has_strong_rim:
                risk = max(0.0, risk - 0.15)
            if sabah_mode and has_karst:
                risk = max(0.0, risk - 0.15)

        # SABAH MODE: Steep slopes (30-70°) are EXPECTED for icehouse Rimmed Platform,
        # Isolated Platform, and Pinnacle Reef — do NOT add volcanic intrusion penalty.
        if lookalike_name == "volcanic_intrusion" and sabah_mode:
            expected_steep = top_id in ("rimmed_platform", "isolated_platform", "pinnacle_reef")
            slope_upper = {"rimmed_platform": 70, "isolated_platform": 70, "pinnacle_reef": 60}.get(top_id, 40)
            if expected_steep and slope_angle_deg is not None and slope_angle_deg <= slope_upper:
                risk = 0.0  # expected geometry — no volcanic intrusion risk in sabah_mode
            elif expected_steep and slope_angle_deg is not None and slope_angle_deg > slope_upper:
                risk = min(1.0, risk + 0.2)  # outside expected range

        false_positive_risks[lookalike_name] = risk

    top_fp = max(false_positive_risks.items(), key=lambda kv: kv[1])[0] if false_positive_risks else None

    # ── Verdict ──────────────────────────────────────────────────────────────
    # F7 HUMILITY: confidence capped at 0.90, never above.
    # Decision tree: high confidence + low FP risk → confirm/possible;
    #                chaotic surface OR very high mud volcano risk → reject;
    #                everything else → exploratory.
    top_fp_risk = false_positive_risks.get(top_fp or "", 0.0)
    if top_match.confidence >= 0.70 and top_fp_risk < 0.5:
        verdict = "CARBONATE_CONFIRMED"
        verdict_confidence = _cap(top_match.confidence)
    elif top_match.confidence >= 0.50 and top_fp_risk < 0.6:
        verdict = "CARBONATE_POSSIBLE"
        verdict_confidence = _cap(top_match.confidence * 0.80)
    elif has_chaotic_surface or false_positive_risks.get("mud_volcano", 0.0) > 0.7:
        verdict = "NON_CARBONATE_SUSPECTED"
        verdict_confidence = _cap(0.70)
    else:
        verdict = "EXPLORATORY"
        verdict_confidence = _cap(0.40)

    # ── Next steps ───────────────────────────────────────────────────────────
    next_steps = []
    if vp_m_s is None:
        next_steps.append("Acquire Vp or sonic data to confirm carbonate vs basement")
    if porosity_fraction is None:
        next_steps.append("Run rock physics modeling (VRH) to estimate porosity range")
    if not has_megabreccias and not has_karst:
        next_steps.append("Check for megabreccias / karst features to differentiate Icehouse vs Greenhouse")
    if slope_angle_deg is None:
        next_steps.append("Measure margin slope angle from seismic to apply Badali discrimination tree")
    if false_positive_risks.get("mud_volcano", 0.0) > 0.5:
        next_steps.append("Run AVO analysis to rule out mud volcano")
    if false_positive_risks.get("volcanic_intrusion", 0.0) > 0.5:
        next_steps.append("Check magnetic anomaly data to rule out volcanic intrusion")
    if verdict in ("CARBONATE_CONFIRMED", "CARBONATE_POSSIBLE") and thickness_m is None:
        next_steps.append("Estimate carbonate thickness from seismic to size the play")
    if not next_steps:
        next_steps.append("Interpretations consistent — recommend drill decision via arifOS 888_JUDGE")

    # ── Assemble result ──────────────────────────────────────────────────────
    discrimination_confidence = _cap(top_match.confidence * (1.0 - false_positive_risks.get(top_fp or "", 0.0)))

    return DiscriminationResult(
        input_summary={
            "age_ma": age_ma,
            "climate_regime": climate_regime.value if climate_regime else None,
            "is_attached": is_attached,
            "is_isolated": is_isolated,
            "has_strong_rim": has_strong_rim,
            "slope_angle_deg": slope_angle_deg,
            "has_megabreccias": has_megabreccias,
            "has_karst": has_karst,
            "has_chaotic_surface": has_chaotic_surface,
            "vp_m_s": vp_m_s,
            "porosity_fraction": porosity_fraction,
            "thickness_m": thickness_m,
            "source": source,
        },
        climate_regime=climate_regime,
        climate_confidence=climate_confidence,
        best_match=top_match,
        all_candidates=all_matches,
        false_positive_risks=false_positive_risks,
        top_false_positive=top_fp,
        verdict=verdict,
        verdict_confidence=verdict_confidence,
        discrimination_confidence=discrimination_confidence,
        next_steps=next_steps,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE DISPATCHER (mirrors geox_petrophysics_unified pattern)
# ─────────────────────────────────────────────────────────────────────────────


def carbonate_discriminate(**kwargs) -> DiscriminationResult:
    """
    Alias for classify_carbonate_structure() — mirrors geox_petrophysics_unified
    naming convention for consistency across GEOX skill modules.
    """
    return classify_carbonate_structure(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# SABAH PLAY TEST (uses our session evidence)
# ─────────────────────────────────────────────────────────────────────────────


def sabah_play_test() -> DiscriminationResult:
    """
    Apply Badali discrimination to our Sabah session evidence:
    - Miocene (Icehouse, ~15 Ma peak)
    - Rimmed platform geometry expected (Operator proven producers: Tepat, Megah)
    - Slope 30-70° (Badali icehouse)
    - Solisip-1 failure noted (reservoir quality issue)
    - Vp-porosity from our rock physics: φ=20% → Vp=4720 m/s

    Returns DiscriminationResult for Sabah Miocene rimmed platform play.
    """
    return classify_carbonate_structure(
        age_ma=15.0,
        climate_regime=ClimateRegime.ICEHOUSE,
        is_attached=True,
        has_strong_rim=True,
        slope_angle_deg=45.0,  # Badali icehouse: 30-70°, take mid-range
        has_megabreccias=True,  # Badali icehouse indicator
        has_karst=True,  # exposure surfaces likely
        thickness_m=800.0,  # Solisip-1 had 138 m; Operator notes 3-15% porosity
        vp_m_s=4720.0,  # our VRH computation at φ=20%
        porosity_fraction=0.20,
        sabah_mode=True,
        source="geox_egs_rock_physics + Operator_overrides",
    )


if __name__ == "__main__":
    # CLI test
    result = sabah_play_test()
    print(f"\n{'=' * 60}")
    print("SABAH PLAY DISCRIMINATION TEST")
    print(f"{'=' * 60}")
    print(f"Climate: {result.climate_regime.value} (conf={result.climate_confidence:.2f})")
    print(f"Best match: {result.best_match.label}")
    print(f"Confidence: {result.best_match.confidence:.2f} [F7 cap {_HUMILITY_CAP}]")
    print(f"Verdict: {result.verdict} (conf={result.verdict_confidence:.2f})")
    print(f"Discrimination confidence: {result.discrimination_confidence:.2f}")
    print(f"Top false positive risk: {result.top_false_positive}")
    print("\nAll candidates:")
    for m in result.all_candidates[:4]:
        print(f"  {m.label:40s} conf={m.confidence:.2f}  sabah={'YES' if m.is_sabah_relevant else 'no'}")
    print("\nNext steps:")
    for s in result.next_steps:
        print(f"  → {s}")
