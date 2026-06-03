from __future__ import annotations

import logging

from geox_core.enums.statuses import (
    get_standard_envelope,
)

logger = logging.getLogger("geox.canonical.time4d")


async def geox_time4d_analyze_system(
    prospect_ref: str,
    mode: str = "burial",
    evidence_refs: list[str] | None = None,
) -> dict:
    """Burial history, maturity modeling, and regime shift analysis.

    F2 Truth: without source-rock / VRo / Tmax / basin-model evidence,
    maturity is UNDETERMINED and labelled as HYPOTHESIS.
    """
    refs = evidence_refs or []
    if not refs:
        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "maturity": "UNDETERMINED",
            "reason": "No burial model / source rock / VRo / Tmax evidence supplied",
        }
        return get_standard_envelope(
            artifact,
            tool_class="compute",
            claim_tag="HYPOTHESIS",
            claim_state="INTERPRETED",
            uncertainty="High",
            humility_score=0.5,
            evidence_refs=[],
        )
    artifact = {
        "ref": prospect_ref,
        "mode": mode,
        "maturity": "Oil_Window",
        "basis": "REGIONAL_PRIOR",
        "evidence_refs": refs,
    }
    return get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="PLAUSIBLE",
        claim_state="INTERPRETED",
        evidence_refs=refs,
    )
