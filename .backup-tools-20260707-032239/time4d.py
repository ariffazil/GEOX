from __future__ import annotations

import logging

from geox_core.enums.statuses import (
    get_standard_envelope,
)

logger = logging.getLogger("geox.canonical.time4d")


async def geox_time4d_analyze_system(
    prospect_ref: str,
    mode: str = "burial",
    time_ma: float = 10.0,
    T_C: float = 100.0,
    TOC_wt: float = 0.05,
    initial_smectite_frac: float = 0.5,
    evidence_refs: list[str] | None = None,
) -> dict:
    """Burial history, maturity modeling, and regime shift analysis.

    Wired directly to the GeoChemState causal base layer. Computes kerogen
    maturation and smectite-illite diagenesis dynamically rather than assuming
    a static Oil_Window.
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

    # 1. Engage the Causal Base Layer
    from geox_mcp.tools.geochemistry import GeochemRequest, geox_geochem_kinetics
    
    geochem_req = GeochemRequest(
        initial_smectite_frac=initial_smectite_frac,
        T_C=T_C,
        time_ma=time_ma,
        TOC_wt=TOC_wt,
        kerogen_type="II"
    )
    # Since geox_geochem_kinetics is async, await it
    base_state = await geox_geochem_kinetics(geochem_req)
    
    # 2. Derive Maturity from Hydrocarbon Generation
    if base_state.hydrocarbon_generated > (TOC_wt * 0.8):
        maturity = "Late_Gas_Window"
    elif base_state.hydrocarbon_generated > (TOC_wt * 0.1):
        maturity = "Oil_Window"
    else:
        maturity = "Immature"

    artifact = {
        "ref": prospect_ref,
        "mode": mode,
        "maturity": maturity,
        "geochem_state": {
            "illite_frac": round(base_state.illite_frac, 3),
            "water_released_frac": round(base_state.water_released_frac, 3),
            "hydrocarbon_generated": round(base_state.hydrocarbon_generated, 4),
            "porosity_change": round(base_state.porosity_change, 4),
            "status": base_state.geochem_status
        },
        "basis": "GEOCHEM_KINETICS",
        "evidence_refs": refs,
    }
    return get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="PLAUSIBLE",
        claim_state="DERIVED",
        evidence_refs=refs,
    )
