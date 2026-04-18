"""
AC_Risk Calculation Engine — Theory of Anomalous Contrast (ToAC)
══════════════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

REPAIRED: arifos-judge-repair-001

Canonical formula (ARIF-OS REPAIR MISSION):
    b_cog = custom_b_cog ?? (u_ambiguity * 0.7 + (1 - evidence_credit) * 0.3)
    ac_risk = b_cog * (1 - truth_score) * (1 + echo_score * 0.5)
    ac_risk = clamp(ac_risk, 0.0, 1.0)

Verdict thresholds:
    < 0.15 → PROCEED (SEAL)
    < 0.75 → HOLD (888_HOLD triggered)
    ≥ 0.75 → BLOCK (VOID)

Governance additions (Wave 1 Trust Foundation):
    - ClaimTag epistemic classification (CLAIM, PLAUSIBLE, HYPOTHESIS, ESTIMATE, UNKNOWN)
    - TEARFRAME adjudication scores (u_ambiguity, evidence_credit, echo_score, truth_score, bias_scenario, b_cog)
    - Anti-Hantu refusal-first screening (F9)
    - Explicit 888_HOLD enforcement with VAULT999 seal
    - Floor violations tracking (F1, F2, F5, F6, F9, F13)
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ClaimTag(Enum):
    """Epistemic classification for every geoscientific assertion."""
    CLAIM = "CLAIM"
    PLAUSIBLE = "PLAUSIBLE"
    HYPOTHESIS = "HYPOTHESIS"
    ESTIMATE = "ESTIMATE"
    UNKNOWN = "UNKNOWN"


class ACVerdict(Enum):
    """Canonical AC_Risk terminal verdicts."""
    PROCEED = "PROCEED"
    HOLD = "HOLD"
    BLOCK = "BLOCK"


@dataclass
class TEARFRAME:
    """TEARFRAME adjudication engine scores.

    Required fields per ARIF-OS REPAIR MISSION:
    - u_ambiguity: Physical ambiguity score
    - evidence_credit: Evidence grounding score
    - echo_score: Consistency with prior knowledge
    - truth_score: Factual accuracy
    - bias_scenario: Cognitive bias scenario
    - b_cog: Computed cognitive bias factor
    """
    u_ambiguity: float = 0.0
    evidence_credit: float = 0.0
    echo_score: float = 0.0
    truth_score: float = 0.0
    bias_scenario: str = "ai_vision_only"
    b_cog: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "u_ambiguity": round(self.u_ambiguity, 4),
            "evidence_credit": round(self.evidence_credit, 4),
            "echo_score": round(self.echo_score, 4),
            "truth_score": round(self.truth_score, 4),
            "bias_scenario": self.bias_scenario,
            "b_cog": round(self.b_cog, 4),
        }


@dataclass
class AC_RiskResult:
    """Result of AC_Risk calculation."""
    ac_risk: float
    verdict: str
    explanation: str
    u_ambiguity: float
    evidence_credit: float
    b_cog: float
    transform_stack: list[str] = field(default_factory=list)


@dataclass
class AntiHantuReport:
    """Anti-Hantu (F9) screening report."""
    passed: bool
    violations: list[str] = field(default_factory=list)
    screened_text_snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": self.violations,
            "screened_text_snippet": self.screened_text_snippet,
        }


@dataclass
class VaultSeal:
    """VAULT999 seal emitted on PROCEED verdict only."""
    epoch: int
    session_id: str
    hash: str
    verdict: str
    ac_risk_score: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch": self.epoch,
            "session_id": self.session_id,
            "hash": self.hash,
            "verdict": self.verdict,
            "ac_risk_score": round(self.ac_risk_score, 4),
            "timestamp": self.timestamp,
        }


@dataclass
class GovernedACRiskResult:
    """Full governed result including AC_Risk, TEARFRAME, ClaimTag, Anti-Hantu, 888_HOLD, VAULT999."""
    ac_risk_score: float
    verdict: str
    explanation: str
    u_ambiguity: float
    evidence_credit: float
    echo_score: float
    truth_score: float
    bias_scenario: str
    b_cog: float

    claim_tag: str
    tearframe: TEARFRAME
    anti_hantu_check: bool
    hold_triggered: bool
    vault_seal: Optional[VaultSeal]
    floor_violations: List[str]
    audit_trace: str
    physics_validation: Optional[ValidationResult] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "ac_risk_score": round(self.ac_risk_score, 4),
            "claim_tag": self.claim_tag,
            "tearframe": self.tearframe.to_dict(),
            "anti_hantu_check": self.anti_hantu_check,
            "hold_triggered": self.hold_triggered,
            "vault_seal": self.vault_seal.to_dict() if self.vault_seal else None,
            "floor_violations": self.floor_violations,
            "audit_trace": self.audit_trace,
        }


class AntiHantuScreen:
    """Refuse-first screen for empathy simulation and feeling claims (F9 Anti-Hantu)."""

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


def _clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def _compute_b_cog(
    u_ambiguity: float,
    evidence_credit: float,
    custom_b_cog: Optional[float],
    bias_scenario: str,
) -> float:
    """Compute B_cog using canonical formula per ARIF-OS REPAIR MISSION."""
    if custom_b_cog is not None:
        return _clamp(custom_b_cog, 0.0, 1.0)

    b_cog = u_ambiguity * 0.7 + (1 - evidence_credit) * 0.3
    return _clamp(b_cog, 0.0, 1.0)


def _compute_governed_ac_risk(
    u_ambiguity: float,
    evidence_credit: float,
    echo_score: float,
    truth_score: float,
    b_cog: float,
) -> float:
    """Compute AC_Risk using canonical formula per ARIF-OS REPAIR MISSION."""
    ac_risk = b_cog * (1 - truth_score) * (1 + echo_score * 0.5)
    return _clamp(ac_risk, 0.0, 1.0)


def _run_floor_checks(
    irreversible_action: bool,
    truth_score: float,
    evidence_credit: float,
    anti_hantu_passed: bool,
    amanah_locked: bool,
) -> List[str]:
    """Run F1-F13 floor checks. Returns list of violated floors.

    NOTE: Floor violations are tracked for audit but do NOT automatically
    override verdict. The 888_HOLD gate is controlled by:
    1. irreversible_action flag
    2. ac_risk_score >= 0.75
    Per ARIF-OS REPAIR MISSION specification.
    """
    violations = []

    if not amanah_locked:
        violations.append("F1")

    if truth_score < 0.99:
        violations.append("F2")

    if not anti_hantu_passed:
        violations.append("F9")

    return violations


def _generate_audit_trace(
    u_ambiguity: float,
    evidence_credit: float,
    echo_score: float,
    truth_score: float,
    b_cog: float,
    ac_risk_score: float,
    verdict: str,
    claim_tag: str,
    hold_triggered: bool,
    floor_violations: List[str],
) -> str:
    """Generate human-readable audit trace."""
    parts = [
        f"u_ambiguity={u_ambiguity:.2f}, evidence_credit={evidence_credit:.2f}",
        f"truth_score={truth_score:.2f}, echo_score={echo_score:.2f}",
        f"b_cog={b_cog:.3f}",
        f"ac_risk={ac_risk_score:.3f}",
        f"verdict={verdict}",
        f"claim_tag={claim_tag}",
    ]
    if hold_triggered:
        parts.append("888_HOLD=ACTIVE")
    if floor_violations:
        parts.append(f"floor_violations={','.join(floor_violations)}")
    return " | ".join(parts)


def _generate_vault_seal(
    verdict: str,
    ac_risk_score: float,
    session_id: str,
) -> Optional[VaultSeal]:
    """Generate VAULT999 seal only on PROCEED verdict."""
    if verdict != "PROCEED":
        return None

    epoch = int(time.time())
    timestamp = datetime.now(timezone.utc).isoformat()
    hash_input = f"{verdict}{ac_risk_score}{timestamp}"
    hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    return VaultSeal(
        epoch=epoch,
        session_id=session_id or "N/A",
        hash=hash_digest,
        verdict=verdict,
        ac_risk_score=ac_risk_score,
        timestamp=timestamp,
    )


def compute_ac_risk(
    u_ambiguity: float,
    transform_stack: List[str],
    evidence_credit: float = 0.0,
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: Optional[float] = None,
) -> AC_RiskResult:
    """
    Calculate Theory of Anomalous Contrast (ToAC) risk score.
    Legacy entrypoint for backward compatibility.
    """
    u_ambiguity = _clamp(u_ambiguity, 0.0, 1.0)
    evidence_credit = _clamp(evidence_credit, 0.0, 1.0)

    b_cog = _compute_b_cog(u_ambiguity, evidence_credit, custom_b_cog, bias_scenario)
    ac_risk = _compute_governed_ac_risk(u_ambiguity, evidence_credit, 0.0, 0.0, b_cog)

    if ac_risk < 0.15:
        verdict = ACVerdict.PROCEED.value
        explanation = f"AC_Risk={ac_risk:.3f}: Low risk. Physical grounding strong. Proceed with standard QC."
    elif ac_risk < 0.75:
        verdict = ACVerdict.HOLD.value
        explanation = f"AC_Risk={ac_risk:.3f}: Elevated risk. Human review required per 888_HOLD."
    else:
        verdict = ACVerdict.BLOCK.value
        explanation = f"AC_Risk={ac_risk:.3f}: Critical risk. Interpretation unsafe. BLOCKED."

    return AC_RiskResult(
        ac_risk=round(ac_risk, 4),
        verdict=verdict,
        explanation=explanation,
        u_ambiguity=round(u_ambiguity, 4),
        evidence_credit=round(evidence_credit, 4),
        b_cog=round(b_cog, 4),
        transform_stack=transform_stack,
    )


def compute_ac_risk_governed(
    u_ambiguity: float,
    transform_stack: List[str],
    evidence_credit: float = 0.0,
    echo_score: float = 0.0,
    truth_score: float = 0.0,
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: Optional[float] = None,
    rasa_present: bool = False,
    amanah_locked: bool = False,
    irreversible_action: bool = False,
    model_text: Optional[str] = None,
    prospect_context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> GovernedACRiskResult:
    """
    Calculate governed AC_Risk with ClaimTag, TEARFRAME, Anti-Hantu, 888_HOLD, VAULT999.

    Args:
        u_ambiguity: Physical ambiguity [0.0, 1.0] - REQUIRED
        transform_stack: List of applied transforms - REQUIRED
        evidence_credit: Evidence grounding score [0.0, 1.0], default 0.0
        echo_score: Consistency with prior knowledge [0.0, 1.0], default 0.0
        truth_score: Factual accuracy [0.0, 1.0], default 0.0
        bias_scenario: Cognitive bias scenario, default "ai_vision_only"
        custom_b_cog: Override B_cog value, default None
        rasa_present: Context appropriateness flag, default False
        amanah_locked: Ethical integrity/reversibility flag, default False
        irreversible_action: If True, forces 888_HOLD, default False
        model_text: Optional text to screen for Anti-Hantu violations
        prospect_context: Optional dict with prospect/operation metadata
        session_id: Optional session ID for VAULT999 seal

    Returns:
        GovernedACRiskResult with full governance envelope per ARIF-OS REPAIR MISSION
    """
    u_ambiguity = _clamp(u_ambiguity, 0.0, 1.0)
    evidence_credit = _clamp(evidence_credit, 0.0, 1.0)
    echo_score = _clamp(echo_score, 0.0, 1.0)
    truth_score = _clamp(truth_score, 0.0, 1.0)

    b_cog = _compute_b_cog(u_ambiguity, evidence_credit, custom_b_cog, bias_scenario)
    ac_risk_score = _compute_governed_ac_risk(u_ambiguity, evidence_credit, echo_score, truth_score, b_cog)

    anti_hantu = AntiHantuScreen.screen(model_text)
    anti_hantu_check = anti_hantu.passed

    tearframe = TEARFRAME(
        u_ambiguity=u_ambiguity,
        evidence_credit=evidence_credit,
        echo_score=echo_score,
        truth_score=truth_score,
        bias_scenario=bias_scenario,
        b_cog=b_cog,
    )

    physics_validation = None
    if prospect_context:
        guard = PhysicsGuard()
        physics_validation = guard.validate_prospect_input(prospect_context)
        if physics_validation.hold:
            hold_triggered = True
            floor_violations.append(f"PHYSICS_EPISTEMIC_VIOLATION: {physics_validation.reason}")

    floor_violations = _run_floor_checks(
        irreversible_action=irreversible_action,
        truth_score=truth_score,
        evidence_credit=evidence_credit,
        anti_hantu_passed=anti_hantu_check,
        amanah_locked=amanah_locked,
    )

    hold_triggered = False
    verdict = ACVerdict.PROCEED.value
    explanation = ""

    if ac_risk_score < 0.15 and anti_hantu_check and amanah_locked and truth_score >= 0.85 and echo_score >= 0.75:
        verdict = ACVerdict.PROCEED.value
        claim_tag = ClaimTag.CLAIM.value
        explanation = f"AC_Risk={ac_risk_score:.3f}: Low risk. Strong evidence. CLAIM tag warranted."
    elif ac_risk_score < 0.35 and anti_hantu_check and truth_score >= 0.60:
        verdict = ACVerdict.PROCEED.value
        claim_tag = ClaimTag.PLAUSIBLE.value
        explanation = f"AC_Risk={ac_risk_score:.3f}: Moderate risk. Evidence supports PLAUSIBLE tag."
    elif ac_risk_score < 0.75:
        verdict = ACVerdict.HOLD.value
        if truth_score < 0.60:
            claim_tag = ClaimTag.ESTIMATE.value
        else:
            claim_tag = ClaimTag.HYPOTHESIS.value
        explanation = f"AC_Risk={ac_risk_score:.3f}: Elevated risk. Human review required per 888_HOLD."
        hold_triggered = True
    else:
        verdict = ACVerdict.BLOCK.value
        claim_tag = ClaimTag.UNKNOWN.value
        explanation = f"AC_Risk={ac_risk_score:.3f}: Critical risk. Interpretation unsafe. BLOCKED."
        hold_triggered = True

    if irreversible_action and verdict == ACVerdict.PROCEED.value:
        verdict = ACVerdict.HOLD.value
        explanation = f"AC_Risk={ac_risk_score:.3f}: Irreversible action. 888_HOLD required before VAULT999 seal."
        hold_triggered = True

    if not anti_hantu_check:
        verdict = ACVerdict.BLOCK.value
        claim_tag = ClaimTag.UNKNOWN.value
        explanation = f"AC_Risk governance BLOCK: Anti-Hantu violation. {anti_hantu.violations}"
        hold_triggered = True

    vault_seal = _generate_vault_seal(verdict, ac_risk_score, session_id or "N/A")

    audit_trace = _generate_audit_trace(
        u_ambiguity=u_ambiguity,
        evidence_credit=evidence_credit,
        echo_score=echo_score,
        truth_score=truth_score,
        b_cog=b_cog,
        ac_risk_score=ac_risk_score,
        verdict=verdict,
        claim_tag=claim_tag,
        hold_triggered=hold_triggered,
        floor_violations=floor_violations,
    )

    return GovernedACRiskResult(
        ac_risk_score=ac_risk_score,
        verdict=verdict,
        explanation=explanation,
        u_ambiguity=u_ambiguity,
        evidence_credit=evidence_credit,
        echo_score=echo_score,
        truth_score=truth_score,
        bias_scenario=bias_scenario,
        b_cog=b_cog,
        claim_tag=claim_tag,
        tearframe=tearframe,
        anti_hantu_check=anti_hantu_check,
        hold_triggered=hold_triggered,
        vault_seal=vault_seal,
        floor_violations=floor_violations,
        audit_trace=audit_trace,
    )