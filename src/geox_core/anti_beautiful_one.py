"""
anti_beautiful_one.py — Gap 3 (WAJIB, elevated priority)

GEOX_FOUNDATIONAL_GAPS_AND_GODEL_LOCK.md Part IV Gap 3:

  certainty_gradient ≤ grounding_gradient

If certainty language outruns grounding evidence, the answer is
"too beautiful to be true" — it must be decomposed before seal.

Anti-Beautiful-One Law (formal):
  beauty_overreach_score = certainty_gradient / grounding_gradient

  if beauty_overreach_score > threshold:
      verdict = BEAUTIFUL_ONE_DRIFT
      action  = FORCE_DECOMPOSITION

DITEMPA BUKAN DIBERI — Beauty must come after falsification, never before.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

# ───────────────────────────── CERTAINTY VOCABULARY ──────────────────────────────
# Higher weight = stronger certainty claim. Calibrated from real subsurface rhetoric.
_CERTAINTY_LEXICON: dict[str, float] = {
    # Strong / narrative-compression language
    "clearly": 0.85,
    "definitely": 0.90,
    "certainly": 0.90,
    "obviously": 0.85,
    "undoubtedly": 0.95,
    "unquestionably": 0.95,
    "without doubt": 0.95,
    "absolutely": 0.95,
    "proven": 0.85,
    "confirmed": 0.80,
    "robust": 0.70,
    "strong": 0.60,
    "significant": 0.55,
    "substantial": 0.55,
    "conclusive": 0.85,
    "compelling": 0.75,
    "convincing": 0.70,
    "decisive": 0.85,
    "definitive": 0.90,
    "reliable": 0.50,
    "valid": 0.45,
    "excellent": 0.70,
    "perfect": 0.95,
    "ideal": 0.75,
    "superb": 0.80,
}

_GROUNDING_LEXICON: dict[str, float] = {
    # Evidence / measurement language
    "measured": 0.50,
    "observed": 0.45,
    "calibrated": 0.55,
    "qc-passed": 0.55,
    "qc_passed": 0.55,
    "validated": 0.50,
    "verified": 0.55,
    "reproducible": 0.60,
    "replicated": 0.60,
    "sampled": 0.40,
    "tested": 0.45,
    "logged": 0.50,
    "documented": 0.40,
    "traceable": 0.55,
    "anchored": 0.55,
    "witnessed": 0.55,
    "stamped": 0.50,
    "sealed": 0.65,
    "hashed": 0.45,
    "checksummed": 0.40,
}


# Sentences that "soften" without grounding are demoted to baseline 0.0.
_HEDGE_PHRASES = {"maybe", "perhaps", "possibly", "might", "could", "appears to", "seems to"}


@dataclass(frozen=True)
class BeautyAudit:
    """The output of an Anti-Beautiful-One audit."""

    certainty_gradient: float
    grounding_gradient: float
    beauty_overreach_score: float
    threshold: float
    verdict: Literal["PASS", "BEAUTIFUL_ONE_DRIFT"]
    action: Literal["PROCEED", "FORCE_DECOMPOSITION"]
    matched_certainty: tuple[str, ...]
    matched_grounding: tuple[str, ...]
    explanation: str


def _scan(text: str, lexicon: dict[str, float]) -> tuple[float, tuple[str, ...]]:
    """Return (weighted_score, matches) for a lexicon scan over `text`."""
    if not text:
        return 0.0, ()
    low = text.lower()
    score = 0.0
    matches: list[str] = []
    for phrase, weight in lexicon.items():
        # Word-boundary scan, case-insensitive. Allow underscores.
        pattern = r"\b" + re.escape(phrase) + r"\b"
        n = len(re.findall(pattern, low))
        if n > 0:
            matches.extend([phrase] * n)
            score += weight * n
    # Normalize by token count to keep gradients bounded across text lengths.
    tokens = max(len(low.split()), 1)
    return score / tokens, tuple(matches)


def audit(
    text: str,
    *,
    grounding_evidence_count: int = 0,
    grounding_evidence_rungs: Iterable[int] = (),
    threshold: float = 1.5,
) -> BeautyAudit:
    """Run an Anti-Beautiful-One audit.

    Parameters
    ----------
    text:
        The candidate claim / response text.
    grounding_evidence_count:
        Number of distinct grounding evidence items attached.
    grounding_evidence_rungs:
        Rung numbers (1-7) for each grounding evidence item. Lower rungs
        count more (Rung 1 = signal, Rung 2 = measurement, Rung 7 = narrative).
    threshold:
        The beauty_overreach_score above which we declare drift.
        Default 1.5 means certainty must be 50% cheaper than grounding.

    Returns
    -------
    BeautyAudit — verdict + matched terms + explanation.
    """
    certainty_score, certainty_matches = _scan(text, _CERTAINTY_LEXICON)

    # Lower rung = stronger grounding. Map rung n to weight 1/n.
    rung_weights = [max(0.05, 1.0 / max(1, r)) for r in grounding_evidence_rungs]
    grounding_from_rungs = sum(rung_weights) if rung_weights else 0.0
    grounding_from_count = float(max(0, grounding_evidence_count)) * 0.10  # cheap bonus per item
    grounding_score = grounding_from_rungs + grounding_from_count
    grounding_score += _scan(text, _GROUNDING_LEXICON)[0]  # in-text grounding language

    # Anti-Beautiful-One Law
    if grounding_score <= 0:
        # No grounding at all → infinity / forced drift
        beauty = float("inf")
    else:
        beauty = certainty_score / grounding_score

    if beauty == float("inf") or beauty > threshold:
        verdict: Literal["PASS", "BEAUTIFUL_ONE_DRIFT"] = "BEAUTIFUL_ONE_DRIFT"
        action: Literal["PROCEED", "FORCE_DECOMPOSITION"] = "FORCE_DECOMPOSITION"
    else:
        verdict = "PASS"
        action = "PROCEED"

    if beauty == float("inf"):
        explanation = (
            f"No grounding evidence found (count={grounding_evidence_count}, "
            f"rungs={list(grounding_evidence_rungs)}); certainty has no floor. "
            f"Drift forced."
        )
    else:
        explanation = (
            f"certainty_gradient={certainty_score:.4f}, "
            f"grounding_gradient={grounding_score:.4f}, "
            f"beauty_overreach_score={beauty:.3f} "
            f"{'>' if verdict == 'BEAUTIFUL_ONE_DRIFT' else '<='} threshold={threshold}."
        )

    return BeautyAudit(
        certainty_gradient=certainty_score,
        grounding_gradient=grounding_score,
        beauty_overreach_score=beauty,
        threshold=threshold,
        verdict=verdict,
        action=action,
        matched_certainty=certainty_matches,
        matched_grounding=(),
        explanation=explanation,
    )


def decompose(
    text: str,
    *,
    grounding_evidence_count: int = 0,
    grounding_evidence_rungs: Iterable[int] = (),
    threshold: float = 1.5,
) -> dict:
    """Audit and (if drift) return a decomposition prompt for the claim.

    Returns a dict that can be appended to GEOX tool output:
        {
          "audit": BeautyAudit(...),
          "decomposition_required": bool,
          "decomposition_prompt": str  (only if required)
        }
    """
    a = audit(
        text,
        grounding_evidence_count=grounding_evidence_count,
        grounding_evidence_rungs=grounding_evidence_rungs,
        threshold=threshold,
    )
    out: dict = {
        "audit": {
            "verdict": a.verdict,
            "action": a.action,
            "beauty_overreach_score": (None if a.beauty_overreach_score == float("inf") else a.beauty_overreach_score),
            "certainty_gradient": a.certainty_gradient,
            "grounding_gradient": a.grounding_gradient,
            "matched_certainty": list(a.matched_certainty),
            "explanation": a.explanation,
        },
        "decomposition_required": a.verdict == "BEAUTIFUL_ONE_DRIFT",
    }
    if a.verdict == "BEAUTIFUL_ONE_DRIFT":
        out["decomposition_prompt"] = (
            "FORCE_DECOMPOSITION: certainty language exceeds grounding evidence. "
            "Break the claim into atomic sub-claims, attach Rung 1-3 evidence "
            "to each, and re-submit. Do not seal until beauty_overreach_score <= "
            f"{threshold}."
        )
    return out


__all__ = ["BeautyAudit", "audit", "decompose"]
