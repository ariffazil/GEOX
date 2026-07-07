"""deep_time/epistemic.py — F2/F7/F9 tagging rules.

Single source of truth for assigning epistemic levels and capping
confidence per arifOS doctrine.

F2 TRUTH: never claim certainty without evidence.
F7 HUMILITY: cap confidence at 0.90 (default), or per the variable's
             source-specific ceiling (some sources can't exceed 0.99).
F9 ANTI-HANTU: never claim consciousness / "what it was like to live".

DITEMPA BUKAN DIBEI — Forged, Not Given.
"""

from __future__ import annotations

from .schemas import EPISTEMIC_CONFIDENCE_CAP, EpistemicLevel


def tag_epistemic_level(
    age_ma: float,
    source_type: str,
    has_external_evidence: bool = False,
) -> EpistemicLevel:
    """Assign the canonical epistemic level for a variable.

    Args:
        age_ma:              the deep time at which the variable is queried
        source_type:         one of 'observation' | 'proxy_high_res' |
                             'proxy_low_res' | 'model' | 'formula' | 'consensus'
        has_external_evidence: True if external dataset was successfully loaded

    Returns:
        The EpistemicLevel string.

    Rules:
      - Formula → DERIVED (regardless of age)
      - Consensus qualitative (supercontinent, biotic) → OBSERVED
      - No external evidence loaded → NO_DATA
      - Cenozoic (< 66 Ma) + observation/proxy_high_res → INTERPRETED
      - Phanerozoic (66-541 Ma) + observation/proxy → INTERPRETED
      - Deep-time (> 541 Ma) + proxy → PROCESS_HYPOTHESIS
      - UNKNOWN is set by data_loaders._is_unknown_at_age (F9 fabrication guard)
        and never by this function — caller must check the guard first.
    """
    if not has_external_evidence:
        return "NO_DATA"
    if source_type == "formula":
        return "DERIVED"
    if source_type == "consensus":
        return "OBSERVED"
    if source_type == "observation":
        return "OBSERVED"
    # proxy or model
    if age_ma > 541.0:
        return "PROCESS_HYPOTHESIS"
    return "INTERPRETED"


def cap_confidence(epistemic: EpistemicLevel, claimed: float) -> float:
    """Apply the F7 HUMILITY cap on a claimed confidence.

    Args:
        epistemic: the assigned epistemic level
        claimed:   the tool's raw claimed confidence (0.0-1.0)

    Returns:
        min(claimed, EPISTEMIC_CONFIDENCE_CAP[epistemic], 0.90)
    """
    cap = min(EPISTEMIC_CONFIDENCE_CAP.get(epistemic, 0.10), 0.90)
    return min(max(claimed, 0.0), cap)
