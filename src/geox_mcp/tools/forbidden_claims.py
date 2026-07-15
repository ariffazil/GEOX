"""
GEOX Forbidden Claims Classifier — Civilizational Safety Gate
==============================================================
Phase 2.5 (2026-07-02): Every tool output is scanned against a
canonical forbidden-claims list before returning to the caller.

Any output claiming certainty about:
  - proven reserves, commercial discovery
  - hydrocarbon pay, safe drilling, mineable resource
  - environmental safety, low-risk investment
  - any capital/land/drilling/mining decision without supporting evidence

...will be flagged with a WARNING or downgraded to candidate status.

Architecture:
  geox_forbidden_claims_scan(output_text) → list of flagged claims
  Applied as middleware in every tool return via _envelope.forbidden_claims

F2 TRUTH: Never fabricate evidence. Never overclaim certainty.
F13 SOVEREIGN: This list is not modifiable by agents. Edit via 888_HOLD.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import re
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# FORBIDDEN CLAIMS — Patterns that MUST be flagged/downgraded
# ═══════════════════════════════════════════════════════════════════════════════
#
# Structure: (compiled_regex, severity, replacement_suggestion)
# severity: BLOCK | WARN | DOWNGRADE
# BLOCK = should never appear in GEOX output
# WARN = appears but with caveats
# DOWNGRADE = change "confirmed X" to "candidate X"
#
FORBIDDEN_CLAIMS: list[tuple[re.Pattern, str, str]] = [
    # ── Proven/commercial certainty ────────────────────────────────────────────
    (re.compile(r"(?i)\bproven\s+reserves?\b"), "BLOCK", "Use 'estimated resources' or 'candidate volume'"),
    (re.compile(r"(?i)\bcommercial\s+discovery\b"), "BLOCK", "Use 'indicated accumulation' or 'candidate prospect'"),
    (
        re.compile(r"(?i)\bhydrocarbon\s+pay\b(?!\s*candidate)"),
        "WARN",
        "Use 'hydrocarbon candidate interval' unless core/test confirmed",
    ),
    (re.compile(r"(?i)\bproven\s+pay\b"), "BLOCK", "Use 'candidate pay interval'"),
    (re.compile(r"(?i)\bcommercial\s+accumulation\b(?!\s*candidate)"), "WARN", "Downgrade to 'candidate accumulation'"),
    (re.compile(r"(?i)\bproductive\s+reservoir\b(?!\s*candidate)"), "WARN", "Use 'candidate reservoir' unless production tested"),
    # ── Drilling/mining certainty ──────────────────────────────────────────────
    (re.compile(r"(?i)\bsafe\s+drilling?\s+target\b"), "BLOCK", "Use 'drilling candidate — requires further evaluation'"),
    (re.compile(r"(?i)\bmineable\s+resource\b"), "WARN", "Use 'mineralized zone — requires feasibility study'"),
    (re.compile(r"(?i)\bdrill[--]?ready\b"), "WARN", "Use 'drill candidate subject to technical review'"),
    # ── Environmental certainty ────────────────────────────────────────────────
    (re.compile(r"(?i)\benvironmentally\s+safe\b"), "BLOCK", "Cannot assert environmental safety from earth data alone"),
    (re.compile(r"(?i)\bno\s+environmental\s+impact\b"), "BLOCK", "Environmental impact requires site-specific EIA"),
    (re.compile(r"(?i)\bzero\s+risk\b"), "BLOCK", "No earth science claim can assert zero risk"),
    # ── Investment/capital certainty ───────────────────────────────────────────
    (
        re.compile(r"(?i)\blow[-\s]risk\s+investment\b"),
        "WARN",
        "Risk assessment requires WEALTH organ — GEOX provides evidence only",
    ),
    (re.compile(r"(?i)\bguaranteed\s+production\b"), "BLOCK", "No production guarantee from subsurface data alone"),
    # ── False precision ────────────────────────────────────────────────────────
    (
        re.compile(r"\b\d{4,}\.?\d*\s*(bbl|mmscf|boe|tonnes?)\b(?![^.]*uncertainty)"),
        "WARN",
        "High-precision resource numbers require uncertainty bounds",
    ),
    (re.compile(r"\bexact\s+(depth|thickness|porosity|saturation)\b"), "WARN", "All subsurface measurements carry uncertainty"),
]


def scan_forbidden_claims(text: str) -> list[dict[str, Any]]:
    """Scan a text output for forbidden claim patterns.

    Args:
        text: Tool output text to scan (stringified if dict).

    Returns:
        List of flagged claims with severity, matched pattern, and suggestion.
        Empty list = clean.
    """
    if not text:
        return []

    flags: list[dict[str, Any]] = []
    for pattern, severity, suggestion in FORBIDDEN_CLAIMS:
        matches = pattern.findall(text)
        if matches:
            flags.append(
                {
                    "severity": severity,
                    "match": matches[0] if isinstance(matches[0], str) else "matched",
                    "suggestion": suggestion,
                }
            )

    return flags


def scan_output_envelope(output: dict[str, Any]) -> dict[str, Any]:
    """Inject forbidden-claims scan result into an output envelope.

    Modifies output in-place by adding _envelope.forbidden_claims.
    Returns the modified output dict.

    This is the main entry point for tool middleware.
    """
    # Convert output to text for scanning
    import json

    text = json.dumps(output, default=str)

    flags = scan_forbidden_claims(text)

    if "_envelope" not in output:
        output["_envelope"] = {}

    output["_envelope"]["forbidden_claims"] = flags
    output["_envelope"]["forbidden_claims_count"] = len(flags)

    # Auto-downgrade if BLOCK-level claims detected
    block_flags = [f for f in flags if f["severity"] == "BLOCK"]
    if block_flags:
        output["_envelope"]["auto_downgraded"] = True
        output["_envelope"]["downgrade_reason"] = (
            f"{len(block_flags)} BLOCK-level forbidden claim(s) detected. "
            "GEOX cannot assert commercial/drilling/environmental certainty "
            "from earth evidence alone. Review warnings before use."
        )

    return output


def forbidden_claims_summary() -> dict[str, Any]:
    """Return summary of the forbidden-claims registry for governance audit."""
    block_count = sum(1 for _, s, _ in FORBIDDEN_CLAIMS if s == "BLOCK")
    warn_count = sum(1 for _, s, _ in FORBIDDEN_CLAIMS if s == "WARN")
    downgrade_count = sum(1 for _, s, _ in FORBIDDEN_CLAIMS if s == "DOWNGRADE")

    return {
        "total_patterns": len(FORBIDDEN_CLAIMS),
        "block_patterns": block_count,
        "warn_patterns": warn_count,
        "downgrade_patterns": downgrade_count,
        "classification": "CIVILIZATIONAL_SAFETY_GATE",
        "authority": "F13 SOVEREIGN — not modifiable by agents",
    }
