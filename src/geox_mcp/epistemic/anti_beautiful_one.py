"""
epistemic/anti_beautiful_one.py — GEOX Anti-Beautiful One Detector
=============================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Detects when GEOX outputs are becoming "too beautiful" —
rhetorically smooth, syntactically complete, emotionally satisfying
— but epistemically hollow.

The Anti-Beautiful One Law:
  certainty_gradient ≤ grounding_gradient

Where:
  certainty_gradient = increase in claim strength language
  grounding_gradient = increase in lower-rung evidence

Beauty overreach score = rhetorical_coherence / evidentiary_density

If beauty_overreach > 1.5 → FLAG as BEAUTIFUL_ONE_RISK
If beauty_overreach > 3.0 → FORCE_DECOMPOSITION

This is GEOX's primary immune system against elegant hallucination.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ─── Certainty language markers ────────────────────────────────────────────────

STRENGTH_MARKERS: list[str] = [
    # Absolute certainty (highest gradient)
    "definitively",
    "certainly",
    "undoubtedly",
    "confirms",
    "confirmed",
    "proven",
    "demonstrates",
    "demonstrated",
    # High certainty
    "clearly",
    "obviously",
    "clearly indicates",
    "clearly shows",
    "confidently",
    "confident",
    "high confidence",
    "establishes",
    "validates",
    "validates that",
    "confirms that",
    "confirms the presence of",
    "robustly indicates",
    "robust indication",
    # Moderate certainty (these are borderline)
    "suggests",
    "indicates",
    "consistent with",
    "appears to",
    "appears to indicate",
    "most likely",
    "likely",
    "probable",
    # Weak certainty
    "may",
    "might",
    "could indicate",
    "possible",
    "suggests possible",
    "admits ambiguity",
]

# Words that signal narrative compression / rhetorical polish
NARRATIVE_POLISH_MARKERS: list[str] = [
    "in conclusion",
    "to summarize",
    "overall",
    "the evidence clearly demonstrates",
    "it is therefore",
    "this clearly shows",
    "the data overwhelmingly supports",
    "comprehensive analysis reveals",
    "a thorough examination confirms",
    "the weight of evidence suggests",
]

# Falsifiability drainers — language that makes claims seem more certain
CERTAINTY_AMPLIFIERS: list[str] = [
    "excellent",
    "outstanding",
    "world-class",
    "exceptional",
    "remarkable",
    "significant",
    "substantial",
    "major",
    "critical",
    "key",
    "essential",
    "fundamental",
]


@dataclass
class BeautyMetrics:
    """
    Metrics computed by the Anti-Beautiful One detector.
    """

    rhetorical_coherence: float  # 0-10: how linguistically smooth the output is
    evidentiary_density: float  # 0-10: how much grounded evidence it cites
    beauty_overreach_score: float  # coherence / density
    certainty_gradient: float  # How fast certainty language accumulates
    grounding_gradient: float  # How fast evidence accumulates
    polish_marker_count: int  # Number of narrative polish phrases
    strength_marker_count: int  # Number of certainty strength markers
    evidence_citations: int  # Number of direct evidence citations (refs)
    missing_grounding_count: int  # Claims without lower-rung support
    overreach_verdict: str  # CLEAN | SUSPICIOUS | BEAUTIFUL_ONE_RISK | FORCE_DECOMPOSITION

    def to_dict(self) -> dict:
        return {
            "rhetorical_coherence": round(self.rhetorical_coherence, 3),
            "evidentiary_density": round(self.evidentiary_density, 3),
            "beauty_overreach_score": round(self.beauty_overreach_score, 3),
            "certainty_gradient": round(self.certainty_gradient, 3),
            "grounding_gradient": round(self.grounding_gradient, 3),
            "polish_marker_count": self.polish_marker_count,
            "strength_marker_count": self.strength_marker_count,
            "evidence_citations": self.evidence_citations,
            "missing_grounding_count": self.missing_grounding_count,
            "overreach_verdict": self.overreach_verdict,
        }


class AntiBeautifulOne:
    """
    Detects Beautiful One drift in GEOX outputs.

    Compares rhetorical coherence (smooth, certain language)
    against evidentiary density (grounded evidence citations,
    lower-rung support, assumption disclosure).

    Law: certainty_gradient ≤ grounding_gradient

    Verdict levels:
      CLEAN: score ≤ 1.0 — output is proportionate
      SUSPICIOUS: 1.0 < score ≤ 2.0 — mild overreach, note
      BEAUTIFUL_ONE_RISK: 2.0 < score ≤ 3.0 — flag, surface discrepancy
      FORCE_DECOMPOSITION: score > 3.0 — force explicit claim decomposition
    """

    STRENGTH_THRESHOLD = 1.5  # beauty_overreach above this = SUSPICIOUS
    RISK_THRESHOLD = 2.0  # above this = BEAUTIFUL_ONE_RISK
    DECOMPOSE_THRESHOLD = 3.0  # above this = FORCE_DECOMPOSITION

    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self._text_lower = output_text.lower()
        self._words = output_text.split()

    def analyze(self, evidence_ref_count: int = 0, assumption_count: int = 0) -> BeautyMetrics:
        """
        Analyze the output text for Beautiful One drift.

        Args:
            evidence_ref_count: Number of evidence citations in the output
            assumption_count: Number of assumptions declared in the output

        Returns:
            BeautyMetrics with all computed scores and verdict
        """
        rhetorical_coherence = self._rhetorical_coherence_score()
        evidentiary_density = self._evidentiary_density_score(evidence_ref_count, assumption_count)

        # beauty_overreach = coherence / density
        # If density is 0, use 0.1 to avoid division by zero
        density = max(evidentiary_density, 0.1)
        beauty_overreach = rhetorical_coherence / density

        certainty_gradient = self._certainty_gradient_score()
        grounding_gradient = self._grounding_gradient_score(evidence_ref_count, assumption_count)

        verdict = self._compute_verdict(beauty_overreach, evidence_ref_count)

        return BeautyMetrics(
            rhetorical_coherence=rhetorical_coherence,
            evidentiary_density=evidentiary_density,
            beauty_overreach_score=beauty_overreach,
            certainty_gradient=certainty_gradient,
            grounding_gradient=grounding_gradient,
            polish_marker_count=self._count_polish_markers(),
            strength_marker_count=self._count_strength_markers(),
            evidence_citations=evidence_ref_count,
            missing_grounding_count=self._count_missing_grounding(),
            overreach_verdict=verdict,
        )

    def _rhetorical_coherence_score(self) -> float:
        """
        Compute rhetorical coherence: how smooth, complete, and polished
        the text sounds. Higher = more rhetorically complete.
        Scale 0-10.
        """
        score = 5.0  # Baseline

        # Polish markers add coherence (this is the trap)
        polish_count = self._count_polish_markers()
        polish_contribution = min(polish_count * 0.5, 2.0)
        score += polish_contribution

        # Strong certainty markers add perceived coherence
        strength_count = self._count_strength_markers()
        strength_contribution = min(strength_count * 0.3, 1.5)
        score += strength_contribution

        # Sentence completeness (ends with periods, not question marks)
        sentences = re.split(r"[.!?]", self._text_lower)
        complete_sentences = sum(1 for s in sentences if len(s.strip()) > 10)
        total_sentences = len([s for s in sentences if len(s.strip()) > 0])
        completeness_ratio = complete_sentences / max(total_sentences, 1)
        score += completeness_ratio * 1.0

        return min(score, 10.0)

    def _evidentiary_density_score(self, evidence_ref_count: int, assumption_count: int) -> float:
        """
        Compute evidentiary density: how much grounded evidence
        backs the claims. Higher = more grounded.
        Scale 0-10.
        """
        score = 2.0  # Baseline minimum

        # Direct evidence citations are the strongest grounding
        ref_contribution = min(evidence_ref_count * 0.8, 4.0)
        score += ref_contribution

        # Assumptions declared = awareness of epistemic cost
        assumption_contribution = min(assumption_count * 0.5, 2.0)
        score += assumption_contribution

        # Uncertainty language indicates epistemic awareness
        uncertainty_markers = self._count_uncertainty_markers()
        uncertainty_contribution = min(uncertainty_markers * 0.3, 1.5)
        score += uncertainty_contribution

        # Evidence of rung disclosure (mentioning "Rung N" or epistemic ladder)
        rung_disclosure = self._text_lower.count("rung")
        rung_contribution = min(rung_disclosure * 0.3, 1.0)
        score += rung_contribution

        return min(score, 10.0)

    def _certainty_gradient_score(self) -> float:
        """
        How fast certainty language accumulates in the text.
        High certainty_gradient without corresponding grounding_gradient
        is the Beautiful One signature.
        """
        strength_count = self._count_strength_markers()
        polish_count = self._count_polish_markers()
        total_markers = strength_count + (polish_count * 2)  # Polish doubled
        return min(total_markers / max(len(self._words), 1) * 100, 10.0)

    def _grounding_gradient_score(self, evidence_ref_count: int, assumption_count: int) -> float:
        """
        How fast evidence accumulates relative to text length.
        """
        grounding_signals = (
            evidence_ref_count
            + assumption_count
            + self._text_lower.count("measured")
            + self._text_lower.count("observed")
            + self._text_lower.count("recorded")
            + self._text_lower.count("calculated")
        )
        return min(grounding_signals / max(len(self._words), 1) * 100, 10.0)

    def _count_polish_markers(self) -> int:
        count = 0
        for marker in NARRATIVE_POLISH_MARKERS:
            count += self._text_lower.count(marker)
        return count

    def _count_strength_markers(self) -> int:
        count = 0
        text = self._text_lower
        for marker in STRENGTH_MARKERS:
            count += text.count(marker)
        return count

    def _count_uncertainty_markers(self) -> int:
        uncertainty_markers = [
            "uncertain",
            "unknown",
            "ambiguous",
            "may",
            "might",
            "possible",
            "probable",
            "possibly",
            "unclear",
            "requires further",
            "needs more data",
            "incomplete",
            "caveat",
            "limitation",
            "approximate",
        ]
        count = 0
        text = self._text_lower
        for marker in uncertainty_markers:
            count += text.count(marker)
        return count

    def _count_missing_grounding(self) -> int:
        """
        Count claims that sound definitive but lack grounding markers.
        Simple heuristic: sentences with strong certainty but no evidence refs.
        """
        sentences = re.split(r"[.!?]", self.output_text)
        missing = 0
        for sentence in sentences:
            sl = sentence.lower()
            has_strength = any(m in sl for m in STRENGTH_MARKERS[:10])  # Only strong markers
            has_evidence = any(m in sl for m in ["measured", "observed", "recorded", "cited", "ref"])
            if has_strength and not has_evidence:
                missing += 1
        return missing

    def _compute_verdict(self, beauty_overreach: float, evidence_ref_count: int) -> str:
        if beauty_overreach <= 1.0 and evidence_ref_count > 0:
            return "CLEAN"
        elif beauty_overreach <= self.STRENGTH_THRESHOLD:
            return "CLEAN"
        elif beauty_overreach <= self.RISK_THRESHOLD:
            return "SUSPICIOUS"
        elif beauty_overreach <= self.DECOMPOSE_THRESHOLD:
            return "BEAUTIFUL_ONE_RISK"
        else:
            return "FORCE_DECOMPOSITION"

    def force_decomposition_triggered(self, metrics: BeautyMetrics | None = None) -> bool:
        """True if the output should be force-decomposed."""
        if metrics is None:
            metrics = self.analyze()
        return metrics.overreach_verdict == "FORCE_DECOMPOSITION"

    def suspicious(self, metrics: BeautyMetrics | None = None) -> bool:
        """True if the output is suspicious or worse."""
        if metrics is None:
            metrics = self.analyze()
        return metrics.overreach_verdict in (
            "BEAUTIFUL_ONE_RISK",
            "FORCE_DECOMPOSITION",
        )
