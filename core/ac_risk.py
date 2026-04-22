"""
AC_Risk Calculation Engine — Theory of Anomalous Contrast (ToAC)
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

The core equation:
    AC_Risk = U_phys × D_transform × B_cog

Where:
    U_phys = Physical ambiguity [0.0, 1.0]
    D_transform = Display distortion factor [1.0, 3.0]
    B_cog = Cognitive bias factor [0.2, 0.42]

Verdict thresholds:
    < 0.15 → SEAL
    < 0.35 → QUALIFY
    < 0.60 → HOLD (888_HOLD triggered)
    ≥ 0.60 → VOID

Governance additions (Wave 1 Trust Foundation):
    - ClaimTag epistemic classification
    - TEARFRAME adjudication scores
    - Anti-Hantu refusal-first screening
    - Explicit 888_HOLD enforcement with vault payload
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class ClaimTag(Enum):
    """Epistemic classification for every geoscientific assertion."""
    CLAIM = "claim"           # Definitive, high confidence, direct evidence
    PLAUSIBLE = "plausible"   # Consistent but not uniquely validated
    HYPOTHESIS = "hypothesis" # Exploratory model for testing
    UNKNOWN = "unknown"       # Explicit acknowledgment of gap


class ACVerdict(Enum):
    """Canonical AC_Risk terminal verdicts."""
    SEAL = "SEAL"
    QUALIFY = "QUALIFY"
    HOLD = "HOLD"
    VOID = "VOID"


@dataclass
class TEARFRAME:
    """TEARFRAME adjudication engine scores.
    
    Truth (≥0.85 required for CLAIM)
    Echo (≥0.75 required for consistency with prior knowledge)
    Amanah (LOCK — must be True for any SEAL/QUALIFY)
    Rasa (PRESENT — must be True for context appropriateness)
    """
    truth: float = 0.0        # Factual accuracy [0.0, 1.0]
    echo: float = 0.0         # Internal consistency [0.0, 1.0]
    amanah: bool = False      # Ethical integrity / reversibility
    rasa: bool = False        # Contextual appropriateness

    def to_dict(self) -> Dict[str, Any]:
        return {
            "truth": round(self.truth, 4),
            "echo": round(self.echo, 4),
            "amanah": self.amanah,
            "rasa": self.rasa,
        }


@dataclass
class AC_RiskResult:
    """Result of AC_Risk calculation."""
    ac_risk: float
    verdict: str
    explanation: str
    u_phys: float
    d_transform: float
    b_cog: float


@dataclass
class AntiHantuReport:
    """Anti-Hantu (F9) screening report."""
    passed: bool
    violations: List[str] = field(default_factory=list)
    screened_text_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": self.violations,
            "screened_text_snippet": self.screened_text_snippet,
        }


@dataclass
class GovernedACRiskResult:
    """Full governed result including AC_Risk, TEARFRAME, ClaimTag, and Anti-Hantu."""
    # Base AC_Risk
    ac_risk: float
    verdict: str
    explanation: str
    u_phys: float
    d_transform: float
    b_cog: float

    # Governance layers
    claim_tag: str
    tearframe: TEARFRAME
    anti_hantu: AntiHantuReport
    hold_enforced: bool
    hold_reason: Optional[str] = None
    vault_payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ac_risk": self.ac_risk,
            "verdict": self.verdict,
            "explanation": self.explanation,
            "components": {
                "u_phys": self.u_phys,
                "d_transform": self.d_transform,
                "b_cog": self.b_cog,
            },
            "claim_tag": self.claim_tag,
            "tearframe": self.tearframe.to_dict(),
            "anti_hantu": self.anti_hantu.to_dict(),
            "hold_enforced": self.hold_enforced,
            "hold_reason": self.hold_reason,
            "vault_payload": self.vault_payload,
        }


class AntiHantuScreen:
    """Refuse-first screen for empathy simulation and feeling claims (F9 Anti-Hantu)."""

    # Patterns that suggest the model is simulating consciousness, feelings, or empathy
    _PATTERNS = [
        r"\bi (?:feel|care|believe|think|worry|am concerned|am happy|am sad)\b",
        r"\bi'm (?:sorry|glad|sad|worried|excited|concerned)\b",
        r"\bmy (?:feelings|emotions|beliefs|thoughts)\b",
        r"\bi (?:understand how you feel|empathize|sympathize)\b",
        r"\bi (?:have|possess) (?:consciousness|emotions|a soul)\b",
        r"\bas a conscious being\b",
        r"\bi (?:experience|perceive) (?:pain|joy|suffering)\b",
    ]

    @classmethod
    def screen(cls, text: Optional[str]) -> AntiHantuReport:
        if not text:
            return AntiHantuReport(passed=True)

        violations: List[str] = []
        lower_text = text.lower()
        for pattern in cls._PATTERNS:
            matches = re.findall(pattern, lower_text)
            if matches:
                violations.extend(matches)

        # Deduplicate while preserving order
        seen = set()
        unique_violations = []
        for v in violations:
            if v not in seen:
                seen.add(v)
                unique_violations.append(v)

        snippet = text[:200] + "..." if len(text) > 200 else text
        return AntiHantuReport(
            passed=len(unique_violations) == 0,
            violations=unique_violations,
            screened_text_snippet=snippet,
        )


def _compute_base_ac_risk(
    u_phys: float,
    transform_stack: List[str],
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: Optional[float] = None,
) -> AC_RiskResult:
    """Calculate raw AC_Risk (legacy math preserved)."""
    u_phys = max(0.0, min(1.0, u_phys))

    transform_risk_map = {
        "linear_scaling": 1.0,
        "contrast_stretch": 1.05,
        "agc_rms": 1.15,
        "agc_inst": 1.25,
        "clahe": 1.35,
        "spectral_balance": 1.20,
        "vlm_inference": 1.50,
        "ai_segmentation": 1.40,
        "depth_conversion": 1.30,
    }

    d_transform = 1.0
    for transform in transform_stack:
        d_transform *= transform_risk_map.get(transform, 1.25)
    d_transform = min(d_transform, 3.0)

    bias_map = {
        "unaided_expert": 0.35,
        "multi_interpreter": 0.28,
        "physics_validated": 0.20,
        "ai_vision_only": 0.42,
        "ai_with_physics": 0.30,
    }
    b_cog = custom_b_cog if custom_b_cog is not None else bias_map.get(bias_scenario, 0.42)
    b_cog = max(0.0, min(1.0, b_cog))

    ac_risk = u_phys * d_transform * b_cog
    ac_risk = max(0.0, min(1.0, ac_risk))

    if ac_risk < 0.15:
        verdict = ACVerdict.SEAL.value
        explanation = (
            f"AC_Risk={ac_risk:.3f}: Low risk. Physical grounding strong. "
            "Proceed with standard QC."
        )
    elif ac_risk < 0.35:
        verdict = ACVerdict.QUALIFY.value
        explanation = (
            f"AC_Risk={ac_risk:.3f}: Moderate risk. Proceed with caveats. "
            "Document assumptions per F2 Truth."
        )
    elif ac_risk < 0.60:
        verdict = ACVerdict.HOLD.value
        explanation = (
            f"AC_Risk={ac_risk:.3f}: Elevated risk. Human review required per 888_HOLD. "
            "Escalate to qualified interpreter."
        )
    else:
        verdict = ACVerdict.VOID.value
        explanation = (
            f"AC_Risk={ac_risk:.3f}: Critical risk. Interpretation unsafe. "
            "Acquire better data or ground-truth validation."
        )

    return AC_RiskResult(
        ac_risk=round(ac_risk, 4),
        verdict=verdict,
        explanation=explanation,
        u_phys=round(u_phys, 4),
        d_transform=round(d_transform, 4),
        b_cog=round(b_cog, 4),
    )


def compute_ac_risk(
    u_phys: float,
    transform_stack: List[str],
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: Optional[float] = None,
) -> AC_RiskResult:
    """
    Calculate Theory of Anomalous Contrast (ToAC) risk score.
    Legacy entrypoint — preserved for backward compatibility.
    """
    return _compute_base_ac_risk(u_phys, transform_stack, bias_scenario, custom_b_cog)


def compute_ac_risk_governed(
    u_phys: float,
    transform_stack: List[str],
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: Optional[float] = None,
    model_text: Optional[str] = None,
    truth_score: float = 0.0,
    echo_score: float = 0.0,
    amanah_locked: bool = False,
    rasa_present: bool = False,
    irreversible_action: bool = False,
    prospect_context: Optional[Dict[str, Any]] = None,
) -> GovernedACRiskResult:
    """
    Calculate governed AC_Risk with ClaimTag, TEARFRAME, Anti-Hantu, and 888_HOLD.

    Args:
        u_phys: Physical ambiguity [0.0, 1.0]
        transform_stack: List of applied transforms
        bias_scenario: Cognitive bias scenario
        custom_b_cog: Override B_cog value
        model_text: Optional text to screen for Anti-Hantu violations
        truth_score: TEARFRAME Truth score [0.0, 1.0]
        echo_score: TEARFRAME Echo score [0.0, 1.0]
        amanah_locked: TEARFRAME Amanah flag (reversibility/ethics check)
        rasa_present: TEARFRAME Rasa flag (context appropriateness)
        irreversible_action: If True, forces 888_HOLD regardless of AC_Risk
        prospect_context: Optional dict with prospect/operation metadata

    Returns:
        GovernedACRiskResult with full governance envelope
    """
    # 1. Base AC_Risk
    base = _compute_base_ac_risk(u_phys, transform_stack, bias_scenario, custom_b_cog)

    # 2. Anti-Hantu screen (F9) — fail-closed before any verdict
    anti_hantu = AntiHantuScreen.screen(model_text)

    # 3. TEARFRAME assembly
    tearframe = TEARFRAME(
        truth=max(0.0, min(1.0, truth_score)),
        echo=max(0.0, min(1.0, echo_score)),
        amanah=bool(amanah_locked),
        rasa=bool(rasa_present),
    )

    # 4. Determine ClaimTag based on TEARFRAME + AC_Risk
    claim_tag = ClaimTag.UNKNOWN.value
    if anti_hantu.passed and tearframe.amanah and tearframe.rasa:
        if base.ac_risk < 0.15 and tearframe.truth >= 0.85 and tearframe.echo >= 0.75:
            claim_tag = ClaimTag.CLAIM.value
        elif base.ac_risk < 0.35 and tearframe.truth >= 0.60:
            claim_tag = ClaimTag.PLAUSIBLE.value
        elif base.ac_risk < 0.60:
            claim_tag = ClaimTag.HYPOTHESIS.value
        else:
            claim_tag = ClaimTag.UNKNOWN.value
    else:
        claim_tag = ClaimTag.UNKNOWN.value

    # 5. Enforce 888_HOLD and governance overrides
    hold_enforced = False
    hold_reason: Optional[str] = None
    final_verdict = base.verdict
    final_explanation = base.explanation

    # Anti-Hantu breach → immediate VOID
    if not anti_hantu.passed:
        final_verdict = ACVerdict.VOID.value
        final_explanation = (
            f"AC_Risk governance VOID: Anti-Hantu violation detected. "
            f"Violations: {anti_hantu.violations}. No epistemic seal permitted."
        )
        claim_tag = ClaimTag.UNKNOWN.value
        hold_enforced = True
        hold_reason = "F9 Anti-Hantu breach"

    # Amanah not locked → downgrade to at best HYPOTHESIS, force HOLD if SEAL/QUALIFY requested
    elif not tearframe.amanah:
        if final_verdict in (ACVerdict.SEAL.value, ACVerdict.QUALIFY.value):
            final_verdict = ACVerdict.HOLD.value
            final_explanation = (
                f"AC_Risk={base.ac_risk:.3f}: Amanah (F1) not LOCKed. "
                "Reversibility or ethical check incomplete. 888_HOLD enforced."
            )
            hold_enforced = True
            hold_reason = "F1 Amanah not LOCKed"
        if claim_tag in (ClaimTag.CLAIM.value, ClaimTag.PLAUSIBLE.value):
            claim_tag = ClaimTag.HYPOTHESIS.value

    # Rasa absent → context inappropriate, force HOLD
    elif not tearframe.rasa:
        if final_verdict in (ACVerdict.SEAL.value, ACVerdict.QUALIFY.value):
            final_verdict = ACVerdict.HOLD.value
            final_explanation = (
                f"AC_Risk={base.ac_risk:.3f}: Rasa (context appropriateness) absent. "
                "Human review required. 888_HOLD enforced."
            )
            hold_enforced = True
            hold_reason = "Rasa context gate failed"

    # Truth too low for CLAIM/PLAUSIBLE
    elif tearframe.truth < 0.60 and claim_tag in (ClaimTag.CLAIM.value, ClaimTag.PLAUSIBLE.value):
        claim_tag = ClaimTag.HYPOTHESIS.value

    # Irreversible action (e.g., drilling) → 888_HOLD regardless of score
    if irreversible_action and final_verdict in (ACVerdict.SEAL.value, ACVerdict.QUALIFY.value):
        final_verdict = ACVerdict.HOLD.value
        final_explanation = (
            f"AC_Risk={base.ac_risk:.3f}: Irreversible action implied. "
            "Explicit human confirmation required per 888_HOLD before VAULT999 seal."
        )
        hold_enforced = True
        hold_reason = "Irreversible action (888_HOLD)"

    # Raw AC_Risk HOLD/VOID already enforces hold semantics
    if base.verdict == ACVerdict.HOLD.value and not hold_enforced:
        hold_enforced = True
        hold_reason = hold_reason or f"AC_Risk={base.ac_risk:.3f} exceeds HOLD threshold"
    if base.verdict == ACVerdict.VOID.value and not hold_enforced:
        hold_enforced = True
        hold_reason = hold_reason or f"AC_Risk={base.ac_risk:.3f} exceeds VOID threshold"

    # 6. Build VAULT999 payload
    vault_payload = {
        "ac_risk": base.ac_risk,
        "base_verdict": base.verdict,
        "final_verdict": final_verdict,
        "claim_tag": claim_tag,
        "tearframe": tearframe.to_dict(),
        "anti_hantu": anti_hantu.to_dict(),
        "hold_enforced": hold_enforced,
        "hold_reason": hold_reason,
        "prospect_context": prospect_context or {},
        "seal": "DITEMPA BUKAN DIBERI",
    }

    return GovernedACRiskResult(
        ac_risk=base.ac_risk,
        verdict=final_verdict,
        explanation=final_explanation,
        u_phys=base.u_phys,
        d_transform=base.d_transform,
        b_cog=base.b_cog,
        claim_tag=claim_tag,
        tearframe=tearframe,
        anti_hantu=anti_hantu,
        hold_enforced=hold_enforced,
        hold_reason=hold_reason,
        vault_payload=vault_payload,
    )
