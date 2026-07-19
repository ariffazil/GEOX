"""
GEOX Tie Preflight — 25-Point Pre-Interpretation Gate
═══════════════════════════════════════════════════════════════════════════════════

Before interpreting a seismic-to-well tie, an agent must answer 25 questions.
This engine validates those answers and returns a GO / HOLD / VOID verdict.

The checklist is not bureaucracy. It is the metabolizer's intake valve.
If you don't know the polarity, you can't trust the tie.
If you don't know the wavelet, you can't trust the synthetic.
If you don't know the decision being supported, you can't set the burden of proof.

Schema:   TiePreflight
Version:  1.0.0
Domain:   NATURAL_LAW
Organ:    GEOX
Floor:    F2 (truth), F4 (clarity), F7 (humility), F9 (anti-hantu)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────────────────────
# ENUMS
# ──────────────────────────────────────────────────────────────────────────────


class CheckStatus(StrEnum):
    """Status of a single preflight check."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class PreflightVerdict(StrEnum):
    """Overall preflight verdict."""

    GO = "GO"  # All critical checks pass; proceed with tie
    HOLD = "HOLD"  # Some checks fail or are unknown; fix before proceeding
    VOID = "VOID"  # Critical failures; tie is unreliable


class DecisionContext(StrEnum):
    """What decision is the tie supporting?

    Same data, different burden of proof.
    """

    HORIZON_CALIBRATION = "horizon_calibration"  # Tie for seismic horizon picking
    HYDROCARBON_PREDICTION = "hydrocarbon_prediction"  # Tie for fluid/lithology prediction
    APPRAISAL = "appraisal"  # Tie for well appraisal decisions
    RESERVES_BOOKING = "reserves_booking"  # Tie for reserves classification
    DRILLING_HAZARD = "drilling_hazard"  # Tie for drilling hazard assessment
    DEVELOPMENT_PLANNING = "development_planning"  # Tie for field development
    FRONTIER_EXPLORATION = "frontier_exploration"  # Tie in frontier/low-data setting


# ──────────────────────────────────────────────────────────────────────────────
# SINGLE CHECK
# ──────────────────────────────────────────────────────────────────────────────


class PreflightCheck(BaseModel):
    """A single preflight check item."""

    check_id: int = Field(description="Check number (1-25)")
    category: str = Field(
        description="Category: convention | data | calibration | signal | processing | geology | rock_physics | resolution | decision"
    )
    question: str = Field(description="The question being answered")
    answer: str = Field(default="", description="Agent-provided answer")
    status: CheckStatus = Field(default=CheckStatus.UNKNOWN, description="PASS/WARN/FAIL/UNKNOWN")
    critical: bool = Field(default=False, description="Is this check critical? FAIL on critical → HOLD or VOID")
    notes: str = Field(default="", description="Caveats or explanation")


# ──────────────────────────────────────────────────────────────────────────────
# PREFLIGHT RESULT
# ──────────────────────────────────────────────────────────────────────────────


class TiePreflightResult(BaseModel):
    """Result of the 25-point pre-interpretation gate."""

    # ── Identity ──────────────────────────────────────────────────────────────
    well_name: str = Field(description="Well identifier")
    session_id: str | None = Field(default=None)

    # ── Decision context ─────────────────────────────────────────────────────
    decision_context: DecisionContext = Field(description="What decision is the tie supporting?")

    # ── Checks ───────────────────────────────────────────────────────────────
    checks: list[PreflightCheck] = Field(description="All 25 preflight checks")

    # ── Summary ──────────────────────────────────────────────────────────────
    total_pass: int = Field(default=0)
    total_warn: int = Field(default=0)
    total_fail: int = Field(default=0)
    total_unknown: int = Field(default=0)
    critical_failures: int = Field(default=0)

    # ── Verdict ──────────────────────────────────────────────────────────────
    verdict: PreflightVerdict = Field(description="GO / HOLD / VOID")
    verdict_reason: str = Field(default="", description="Plain-language verdict explanation")

    # ── Blocking issues ──────────────────────────────────────────────────────
    blockers: list[str] = Field(
        default_factory=list,
        description="Specific issues that block the tie",
    )

    # ── Provenance ──────────────────────────────────────────────────────────
    timestamp_utc: str = Field(description="UTC timestamp")
    domain_law: str = Field(default="NATURAL_LAW")

    class Config:
        json_schema_extra = {
            "description": (
                "25-point pre-interpretation gate — "
                "The checklist is not bureaucracy. It is the metabolizer's intake valve. "
                "DITEMPA BUKAN DIBERI"
            )
        }


# ──────────────────────────────────────────────────────────────────────────────
# THE 25 CHECKS — Canonical definition
# ──────────────────────────────────────────────────────────────────────────────

_CHECKS_TEMPLATE: list[dict[str, Any]] = [
    # ── CONVENTION (1-2) ──
    {"id": 1, "cat": "convention", "q": "Polarity convention (SEG_NORMAL or SEG_REVERSE)?", "critical": True},
    {"id": 2, "cat": "convention", "q": "Phase convention (zero-phase, minimum-phase, mixed)?", "critical": True},
    # ── DATUM (3-4) ──
    {"id": 3, "cat": "convention", "q": "Seismic datum declared (MSL, KB, LAT)?", "critical": True},
    {"id": 4, "cat": "convention", "q": "Well datum declared (KB, MSL)?", "critical": True},
    # ── CALIBRATION (5-7) ──
    {"id": 5, "cat": "calibration", "q": "Checkshot data available?", "critical": True},
    {"id": 6, "cat": "calibration", "q": "VSP data available?", "critical": False},
    {"id": 7, "cat": "calibration", "q": "Sonic log quality acceptable (no major washout/invasion)?", "critical": True},
    # ── DATA QUALITY (8-11) ──
    {"id": 8, "cat": "data", "q": "Density log quality acceptable?", "critical": True},
    {"id": 9, "cat": "data", "q": "Environmental corrections documented?", "critical": False},
    {"id": 10, "cat": "data", "q": "Borehole condition assessed?", "critical": False},
    {"id": 11, "cat": "data", "q": "Log sampling rate compatible with seismic sample rate?", "critical": False},
    # ── SIGNAL (12-13) ──
    {"id": 12, "cat": "signal", "q": "Wavelet extraction method declared (extracted/statistical/assumed)?", "critical": True},
    {"id": 13, "cat": "signal", "q": "Phase confidence assessed (low/medium/high)?", "critical": True},
    # ── PROCESSING (14-15) ──
    {"id": 14, "cat": "processing", "q": "Seismic processing sequence known?", "critical": False},
    {"id": 15, "cat": "processing", "q": "Migration type and quality assessed?", "critical": False},
    # ── FREQUENCY (16) ──
    {"id": 16, "cat": "signal", "q": "Frequency bandwidth of seismic data declared?", "critical": False},
    # ── GEOLOGY (17-19) ──
    {"id": 17, "cat": "geology", "q": "Target interval identified?", "critical": True},
    {"id": 18, "cat": "geology", "q": "Marker depths established from well data?", "critical": True},
    {"id": 19, "cat": "geology", "q": "Stratigraphic framework defined?", "critical": False},
    # ── ROCK PHYSICS (20-22) ──
    {"id": 20, "cat": "rock_physics", "q": "Expected lithology at target interval known?", "critical": True},
    {"id": 21, "cat": "rock_physics", "q": "Fluid/pressure regime at target known?", "critical": False},
    {"id": 22, "cat": "rock_physics", "q": "Rock physics model assessed (elastic-fluid separability)?", "critical": False},
    # ── RESOLUTION (23) ──
    {"id": 23, "cat": "resolution", "q": "Tuning thickness estimated or modeled?", "critical": False},
    # ── ANALOG (24) ──
    {"id": 24, "cat": "data", "q": "Nearby well analogs available for cross-validation?", "critical": False},
    # ── DECISION (25) ──
    {"id": 25, "cat": "decision", "q": "Decision being supported by this tie declared?", "critical": True},
]


# ──────────────────────────────────────────────────────────────────────────────
# BURDEN OF PROOF — Decision context → required check strictness
# ──────────────────────────────────────────────────────────────────────────────

_DECISION_BURDEN: dict[str, dict[str, Any]] = {
    "horizon_calibration": {
        "min_pass_pct": 0.60,
        "critical_must_pass": [1, 2, 3, 4, 5, 7, 12, 17, 18, 25],
        "description": "Tie for seismic horizon picking. Moderate burden.",
    },
    "hydrocarbon_prediction": {
        "min_pass_pct": 0.75,
        "critical_must_pass": [1, 2, 3, 4, 5, 7, 8, 12, 13, 17, 18, 20, 21, 22, 25],
        "description": "Tie for fluid/lithology prediction. High burden.",
    },
    "appraisal": {
        "min_pass_pct": 0.70,
        "critical_must_pass": [1, 2, 3, 4, 5, 7, 8, 12, 17, 18, 20, 25],
        "description": "Tie for well appraisal. High burden.",
    },
    "reserves_booking": {
        "min_pass_pct": 0.80,
        "critical_must_pass": [1, 2, 3, 4, 5, 7, 8, 12, 13, 17, 18, 20, 21, 22, 23, 25],
        "description": "Tie for reserves classification. Highest burden.",
    },
    "drilling_hazard": {
        "min_pass_pct": 0.65,
        "critical_must_pass": [1, 2, 3, 4, 5, 7, 12, 17, 18, 25],
        "description": "Tie for drilling hazard assessment. Moderate-high burden.",
    },
    "development_planning": {
        "min_pass_pct": 0.70,
        "critical_must_pass": [1, 2, 3, 4, 5, 7, 8, 12, 17, 18, 20, 22, 25],
        "description": "Tie for field development. High burden.",
    },
    "frontier_exploration": {
        "min_pass_pct": 0.50,
        "critical_must_pass": [1, 2, 3, 4, 17, 25],
        "description": "Tie in frontier/low-data setting. Lower burden but still needs basics.",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# ENGINE — Run the preflight
# ──────────────────────────────────────────────────────────────────────────────


def run_tie_preflight(
    well_name: str,
    decision_context: str,
    answers: dict[int, str] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Run the 25-point pre-interpretation gate.

    Parameters
    ----------
    well_name : str
        Well identifier.
    decision_context : str
        One of the DecisionContext values (e.g. "horizon_calibration", "hydrocarbon_prediction").
    answers : dict[int, str], optional
        Map of check_id → answer text. Checks without answers get status UNKNOWN.
    session_id : str, optional
        Governed session ID.

    Returns
    -------
    dict
        TiePreflightResult as dict.
    """
    from datetime import UTC, datetime

    now = datetime.now(UTC).isoformat()
    answers = answers or {}

    # Build checks
    checks: list[PreflightCheck] = []
    for t in _CHECKS_TEMPLATE:
        answer = answers.get(t["id"], "")
        # Auto-determine status from answer
        if not answer:
            status = CheckStatus.UNKNOWN
        elif answer.upper() in (
            "YES",
            "PRESENT",
            "GOOD",
            "HIGH",
            "NORMAL",
            "DECLARED",
            "KNOWN",
            "AVAILABLE",
            "ASSESSED",
            "DEFINED",
            "ESTIMATED",
            "DOCUMENTED",
            "ACCEPTABLE",
            "COMPATIBLE",
        ):
            status = CheckStatus.PASS
        elif answer.upper() in (
            "NO",
            "ABSENT",
            "POOR",
            "LOW",
            "MISSING",
            "UNKNOWN",
            "NOT AVAILABLE",
            "NOT DECLARED",
            "NOT KNOWN",
            "NOT ASSESSED",
        ):
            status = CheckStatus.FAIL if t["critical"] else CheckStatus.WARN
        elif answer.upper() in ("DEGRADED", "PARTIAL", "MEDIUM", "PARTIALLY", "SOME"):
            status = CheckStatus.WARN
        else:
            status = CheckStatus.PASS  # Non-empty, non-obvious → treat as provided

        checks.append(
            PreflightCheck(
                check_id=t["id"],
                category=t["cat"],
                question=t["q"],
                answer=answer,
                status=status,
                critical=t["critical"],
            )
        )

    # Summary
    total_pass = sum(1 for c in checks if c.status == CheckStatus.PASS)
    total_warn = sum(1 for c in checks if c.status == CheckStatus.WARN)
    total_fail = sum(1 for c in checks if c.status == CheckStatus.FAIL)
    total_unknown = sum(1 for c in checks if c.status == CheckStatus.UNKNOWN)

    # Get burden for this decision context
    burden = _DECISION_BURDEN.get(decision_context, _DECISION_BURDEN["horizon_calibration"])
    critical_must_pass = burden["critical_must_pass"]
    min_pass_pct = burden["min_pass_pct"]

    # Count critical failures
    critical_failures = 0
    blockers: list[str] = []
    for c in checks:
        if c.check_id in critical_must_pass and c.status in (CheckStatus.FAIL, CheckStatus.UNKNOWN):
            critical_failures += 1
            blockers.append(f"Check {c.check_id}: {c.question} — {c.status.value}")

    # Compute verdict
    pass_pct = total_pass / len(checks) if checks else 0.0

    if critical_failures > 0:
        verdict = PreflightVerdict.HOLD
        verdict_reason = f"{critical_failures} critical check(s) failed or unknown. Fix before proceeding."
    elif pass_pct < min_pass_pct:
        verdict = PreflightVerdict.HOLD
        verdict_reason = f"Pass rate {pass_pct:.0%} below minimum {min_pass_pct:.0%} for {decision_context}."
    elif total_fail > 3:
        verdict = PreflightVerdict.HOLD
        verdict_reason = f"{total_fail} checks failed. Review non-critical failures."
    else:
        verdict = PreflightVerdict.GO
        verdict_reason = f"All critical checks pass. Pass rate {pass_pct:.0%}. Proceed with tie."

    # Check for VOID conditions
    if critical_failures >= 5:
        verdict = PreflightVerdict.VOID
        verdict_reason = f"{critical_failures} critical failures — tie is unreliable. VOID."

    result = TiePreflightResult(
        well_name=well_name,
        session_id=session_id,
        decision_context=DecisionContext(decision_context)
        if decision_context in [e.value for e in DecisionContext]
        else DecisionContext.HORIZON_CALIBRATION,
        checks=checks,
        total_pass=total_pass,
        total_warn=total_warn,
        total_fail=total_fail,
        total_unknown=total_unknown,
        critical_failures=critical_failures,
        verdict=verdict,
        verdict_reason=verdict_reason,
        blockers=blockers,
        timestamp_utc=now,
        domain_law="NATURAL_LAW",
    )

    return result.model_dump()
