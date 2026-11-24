"""Curve origin classification — Law L5 (raw vs computed) and Law L10 (a name is
a hypothesis, not a provenance).

A mnemonic is *screening evidence* about where a curve came from, never proof of
it. ``RHOB_INTERP`` is probably interpreted; ``VSH`` might be vendor-derived or
locally computed; ``DT`` may be measured, patched or reconstructed. Every result
therefore carries ``origin_basis`` and ``origin_confidence``, and a mnemonic
match can never return better than LOW confidence. A consumer that needs real
provenance must read source metadata, not this function.

The two completeness measures are deliberately separate:

* inventory completeness  — every present curve counts; nothing disappears
* physical completeness   — only ``origin == measured`` counts

A recomputed curve satisfies the first and must never satisfy the second. That
is the whole point of L5: prior to this module the QC path treated one dict of
"raw_curves" as raw, so a computed RHOB could satisfy a requirement meant for a
measured one.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class CurveOrigin(str, Enum):
    MEASURED = "measured"
    COMPUTED = "computed"
    SPLICED = "spliced"
    INTERPRETED = "interpreted"
    RECONSTRUCTED = "reconstructed"
    UNKNOWN = "unknown"


# Direct physical measurements. Depth is only measured along the borehole axis;
# TVD/TVDSS are derived from deviation, so they are NOT in this set.
_MEASURED = frozenset(
    {
        "GR", "RHOB", "RHOZ", "NPHI", "TNPH", "DT", "DTC", "DTS", "AC",
        "RT", "ILD", "LLD", "LLS", "MSFL", "SP", "CALI", "HCAL", "PE", "PEF", "BS",
        "MD", "DEPT", "DEPTH",
    }
)

# Deterministic transforms of measured curves — reproducible, but not evidence.
_COMPUTED = frozenset(
    {"VSH", "VSHALE", "PHIE", "PHIT", "PHID", "SW", "SWT", "SWE", "PERM", "NTG", "BVW", "TVD", "TVDSS"}
)

# Ordered: a token match wins over an exact mnemonic match, so RHOB_INTERP is
# interpreted rather than measured.
_KEYWORD_RULES: tuple[tuple[tuple[str, ...], CurveOrigin], ...] = (
    (("SPLC", "SPLICE", "COMPOSITE", "_COMP", "MRG", "MERGE"), CurveOrigin.SPLICED),
    (("SYNTH", "PSEUDO", "PATCH", "RECON"), CurveOrigin.RECONSTRUCTED),
    (("INTERP", "FACIES", "LITH", "_PAY", "PAYFLAG", "NETFLAG"), CurveOrigin.INTERPRETED),
)

_UNKNOWN: dict[str, Any] = {
    "origin": CurveOrigin.UNKNOWN.value,
    "origin_basis": "unknown",
    "origin_confidence": "unknown",
}


def classify_curve_origin(mnemonic: str) -> dict[str, Any]:
    """Classify ``mnemonic`` into an origin, with its basis and confidence.

    Always returns all three keys. ``origin_confidence`` is ``"low"`` for any
    mnemonic-derived answer and ``"unknown"`` when nothing matched.
    """
    name = (mnemonic or "").strip().upper()
    if not name:
        return dict(_UNKNOWN)

    for tokens, origin in _KEYWORD_RULES:
        if any(token in name for token in tokens):
            return {
                "origin": origin.value,
                "origin_basis": "mnemonic_pattern",
                "origin_confidence": "low",
            }

    if name in _MEASURED:
        return {
            "origin": CurveOrigin.MEASURED.value,
            "origin_basis": "mnemonic_pattern",
            "origin_confidence": "low",
        }

    if name in _COMPUTED:
        return {
            "origin": CurveOrigin.COMPUTED.value,
            "origin_basis": "mnemonic_pattern",
            "origin_confidence": "low",
        }

    return dict(_UNKNOWN)


def measure_completeness(present_origins: dict[str, str], total_canonical: int) -> dict[str, Any]:
    """Two completeness measures over the canonical curves that were resolved.

    ``present_origins`` maps canonical curve name -> origin value.
    """
    measured = sorted(name for name, origin in present_origins.items() if origin == CurveOrigin.MEASURED.value)
    inventory_only = sorted(name for name, origin in present_origins.items() if origin != CurveOrigin.MEASURED.value)
    denominator = max(int(total_canonical or 0), 1)

    return {
        "inventory_count": len(present_origins),
        "measured_count": len(measured),
        "measured_curves": measured,
        "inventory_only_curves": inventory_only,
        "completeness_inventory_score": round(len(present_origins) / denominator, 2),
        "completeness_measured_score": round(len(measured) / denominator, 2),
    }
