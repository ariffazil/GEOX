"""
geox_prospect — Prospect Evaluation (Phase 2)
═════════════════════════════════════════════
Absorbs: geox_prospect_evaluate (renamed, same API)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations
from typing import Any, Literal

async def geox_prospect(
    prospect_ref: str,
    mode: Literal["screen", "appraise", "develop"] = "screen",
    evidence_refs: list[str] | None = None,
    verdict: Literal["compute", "preview", "seal"] = "compute",
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
    structural_map_inline: dict[str, Any] | None = None,
    power_params: dict[str, Any] | None = None,
    carrier_bed_refs: list[dict[str, Any]] | None = None,
    prospect_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Prospect evaluation — volumetrics, POS, EVOI, risk assessment.

    Delegates to geox_prospect_evaluate implementation.
    """
    from geox_mcp.tools.prospect import geox_prospect_evaluate as _impl
    return await _impl(
        prospect_ref=prospect_ref,
        mode=mode,
        evidence_refs=evidence_refs,
        verdict=verdict,
        ack_irreversible=ack_irreversible,
        judge_pin=judge_pin,
        structural_map_inline=structural_map_inline,
        power_params=power_params,
        carrier_bed_refs=carrier_bed_refs,
        prospect_refs=prospect_refs,
    )
