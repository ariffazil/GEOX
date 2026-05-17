from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from contracts.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)

logger = logging.getLogger("geox.canonical.dst")


async def geox_dst_ingest_test(
    well_id: str,
    field: str | None = None,
    reservoir_name: str | None = None,
    test_name: str | None = None,
    test_duration_hr: float | None = None,
    main_flow_hr: float | None = None,
    main_buildup_hr: float | None = None,
    choke_size_64ths: float | None = None,
    bhp_psi: float | None = None,
    bht_c: float | None = None,
    whp_psi: float | None = None,
    wht_c: float | None = None,
    gas_rate_mmscfd: float | None = None,
    condensate_rate_stbd: float | None = None,
    water_rate_stbd: float | None = None,
    co2_mol_pct: float | None = None,
    h2s_ppm: float | None = None,
    bsw_pct: float | None = None,
    chloride_ppm: float | None = None,
    wgr_stb_per_mmscf: float | None = None,
    permeability_md_min: float | None = None,
    permeability_md_max: float | None = None,
    skin_min: float | None = None,
    skin_max: float | None = None,
) -> dict:
    """Structured DST (Drill-Stem Test) ingestion with derived metrics and flags.

    F2 Truth: all outputs are OBSERVED from supplied parameters; no geological
    interpretation is performed here. claim_state = INGESTED.
    """
    derived: Dict[str, Any] = {}
    flags: List[str] = []

    # ── Derived metrics ──────────────────────────────────────────────────────
    if gas_rate_mmscfd and condensate_rate_stbd is not None:
        derived["cgr_stb_per_mmscf"] = round(condensate_rate_stbd / gas_rate_mmscfd, 2)
    if gas_rate_mmscfd and water_rate_stbd is not None:
        derived["wgr_stb_per_mmscf"] = round(water_rate_stbd / gas_rate_mmscfd, 2)
    if gas_rate_mmscfd and co2_mol_pct is not None:
        derived["hydrocarbon_gas_mmscfd"] = round(gas_rate_mmscfd * (1 - co2_mol_pct / 100), 2)
    if bhp_psi and whp_psi is not None:
        derived["drawdown_proxy_psi"] = round(bhp_psi - whp_psi, 2)

    # ── Flags (observed thresholds, not interpretation) ──────────────────────
    if co2_mol_pct is not None and co2_mol_pct > 10:
        flags.append("HIGH_CO2")
    if h2s_ppm is not None and h2s_ppm > 0:
        flags.append("H2S_PRESENT")
    if permeability_md_min is not None and permeability_md_min > 100:
        flags.append("GOOD_PERM")
    if skin_min is not None and skin_min < 5:
        flags.append("LOW_SKIN")
    if condensate_rate_stbd is not None and condensate_rate_stbd > 0:
        flags.append("CONDENSATE_PRESENT")
    if water_rate_stbd is not None and water_rate_stbd > 0:
        flags.append("WATER_PRESENT")
    if bhp_psi and whp_psi is not None and derived.get("drawdown_proxy_psi", 0) > 1000:
        flags.append("HIGH_DRAWDOWN")
    if main_buildup_hr is not None and main_buildup_hr > 1:
        flags.append("VALID_BUILDUP_PRESENT")

    artifact = {
        "well_id": well_id,
        "field": field,
        "reservoir_name": reservoir_name,
        "test_name": test_name,
        "derived_metrics": derived,
        "flags": flags,
        "raw_inputs": {
            k: v for k, v in {
                "gas_rate_mmscfd": gas_rate_mmscfd,
                "condensate_rate_stbd": condensate_rate_stbd,
                "water_rate_stbd": water_rate_stbd,
                "co2_mol_pct": co2_mol_pct,
                "h2s_ppm": h2s_ppm,
                "bhp_psi": bhp_psi,
                "whp_psi": whp_psi,
            }.items() if v is not None
        },
    }

    return get_standard_envelope(
        artifact,
        tool_class="ingest",
        claim_tag="OBSERVED",
        claim_state="INGESTED",
        evidence_refs=[f"dst://{well_id}/{test_name or 'unknown'}"],
    )
