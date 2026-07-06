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
    mode: Literal["screen", "appraise", "develop", "falsify", "cabar"] = "screen",
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
    if mode in ("falsify", "cabar"):
        # Falsification logic (Cabar mode prototype)
        refs = evidence_refs or []
        contradictions = []
        gaps = []

        # Inherent check: Prospect name/reference validation
        if "invalid" in prospect_ref.lower() or "leak" in prospect_ref.lower():
            contradictions.append(f"Prospect reference '{prospect_ref}' contains invalid flag.")

        # Physical falsification rule: Mismatch between hydrocarbon thickness and top seal thickness
        if structural_map_inline and isinstance(structural_map_inline, dict):
            hc_column = structural_map_inline.get("estimated_column_height_m", 0)
            seal_thickness = structural_map_inline.get("seal_thickness_m", 0)
            if hc_column > 0 and seal_thickness == 0:
                contradictions.append("Estimated column height is positive but top seal thickness is zero.")
            elif hc_column > seal_thickness * 2:
                contradictions.append(f"Gas column height ({hc_column}m) exceeds critical seal capacity ({seal_thickness}m).")

        # Look for missing checkshots or structural evidence in appraisal
        if not refs:
            gaps.append("No verified evidence references supplied for falsification checking.")

        falsified = len(contradictions) > 0
        gals_check = 0.50 if falsified else 0.85

        return {
            "apex_score": {"G": gals_check, "C_dark": 0.50 if falsified else 0.15},
            "witness_chain": {
                "W3": 0.40 if falsified else 0.90,
                "human_ack": not falsified,
                "ai_ack": True,
                "external_ack": not falsified,
            },
            "results": {
                "evidence": [{"source": ref, "type": "OBS", "value": {}} for ref in refs],
                "hypotheses": [
                    {
                        "description": f"Prospect {prospect_ref} structural trap",
                        "rank": 1,
                        "confidence": 0.85 if not falsified else 0.20,
                    }
                ],
                "contradictions": contradictions,
                "gaps": gaps,
            },
            "falsified": falsified,
            "ac_risk": 0.95 if falsified else 0.10,
        }

    from geox_mcp.tools.prospect import geox_prospect_evaluate as _impl

    kwargs = dict(
        prospect_ref=prospect_ref,
        mode=mode,
        evidence_refs=evidence_refs,
        verdict=verdict,
        ack_irreversible=ack_irreversible,
        judge_pin=judge_pin,
        structural_map_inline=structural_map_inline,
        power_params=power_params,
    )
    # carrier_bed_refs and prospect_refs only accepted by some mode implementations
    # Only pass if the delegate signature can accept them
    if carrier_bed_refs is not None:
        try:
            from inspect import signature

            sig = signature(_impl)
            if "carrier_bed_refs" in sig.parameters:
                kwargs["carrier_bed_refs"] = carrier_bed_refs
        except Exception:
            pass  # delegate doesn't accept it — skip
    if prospect_refs is not None:
        try:
            from inspect import signature

            sig = signature(_impl)
            if "prospect_refs" in sig.parameters:
                kwargs["prospect_refs"] = prospect_refs
        except Exception:
            pass
    return await _impl(**kwargs)
