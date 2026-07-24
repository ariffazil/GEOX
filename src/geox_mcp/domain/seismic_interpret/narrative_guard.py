"""Block probability theatre and drilling advice from image-only narratives (T1).

Vision may propose geometry. It must not convert lines into depth, closure
probability, economic ranking, or drilling advice without measurements.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import re
from typing import Any

# Patterns that must never become measured geology from image alone
_BLOCKED = [
    (
        re.compile(r"\b\d+\s*%\s*(probability|chance|POS|likelihood)\b", re.I),
        "PROBABILITY_THEATRE",
        "Percentage chance / POS without benchmark-calibrated model is rejected",
    ),
    (
        re.compile(r"\b(four[- ]way|4[- ]way)\s+closure\b", re.I),
        "FOUR_WAY_UNMEASURED",
        "Four-way closure requires maps or crossing lines — not a single 2D image",
    ),
    (
        re.compile(r"\b(drill|drilling|spud|high[- ]grade)\b", re.I),
        "DRILLING_BLOCKED",
        "Drilling / high-grade recommendations are constitutionally blocked from GEOX local verdicts",
    ),
    (
        re.compile(r"\b(\d+)\s*ms\s*(equals?|=|≈|~)\s*(\d+)\s*m\b", re.I),
        "DEPTH_FROM_TWT_UNMEASURED",
        "TWT→depth conversion requires checkshot/VSP/velocity model — not image pixels",
    ),
    (
        re.compile(r"\b(fault[- ]seal\s+probability|trap\s+validity\s+\d+%|prospect\s+rank)", re.I),
        "ECONOMIC_RANKING_BLOCKED",
        "Fault-seal probability / prospect ranking requires WEALTH+calibration path, not image narrative",
    ),
]


def scan_narrative_claims(
    text: str,
    *,
    input_class: str = "image_only",
    has_velocity: bool = False,
    has_3d: bool = False,
) -> dict[str, Any]:
    """Return blocked claims and required measurements."""
    blocked: list[dict[str, Any]] = []
    if not text:
        return {"ok": True, "blocked": [], "missing_measurements": []}

    for rx, code, reason in _BLOCKED:
        if rx.search(text):
            # Allow depth conversion phrasing only if velocity present (still not auto-pass)
            if code == "DEPTH_FROM_TWT_UNMEASURED" and has_velocity:
                blocked.append(
                    {
                        "code": code,
                        "status": "UNMEASURED",
                        "reason": reason + " (velocity present but conversion not executed in this guard)",
                        "match": rx.findall(text)[:3],
                    }
                )
                continue
            if code == "FOUR_WAY_UNMEASURED" and has_3d:
                continue
            blocked.append(
                {
                    "code": code,
                    "status": "BLOCKED" if code in ("DRILLING_BLOCKED", "ECONOMIC_RANKING_BLOCKED", "PROBABILITY_THEATRE") else "UNMEASURED",
                    "reason": reason,
                    "match": rx.findall(text)[:3] if rx.groups else [rx.search(text).group(0)],  # type: ignore[union-attr]
                }
            )

    missing = []
    if input_class == "image_only":
        missing = [
            "bin_spacing_m + sample_interval_ms (or pixel scale)",
            "vertical_exaggeration or velocity_td / checkshot",
            "section_azimuth_deg + fault_strike_deg for true dip",
            "intersecting lines or 3D volume for four-way closure",
            "benchmark-calibrated model for any probability / POS",
        ]

    hard_block = any(b["status"] == "BLOCKED" for b in blocked)
    return {
        "ok": not hard_block,
        "blocked": blocked,
        "missing_measurements": missing,
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_eligibility": False,
        "drilling_recommendation": None,
        "note": "Vision proposes; measurements validate. Narrative is not a SEAL.",
    }
