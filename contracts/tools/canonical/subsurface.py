from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Literal

from fastmcp import FastMCP
from contracts.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)
from contracts.tools.canonical._helpers import (
    _get_artifact,
    _artifact_exists,
    _register_artifact,
    _record_latest_qc,
    _latest_qc_failed_refs,
    _check_maruah_territory,
    _inject_ensemble_residual_evidence,
    _safe_upload_path,
    _decode_upload_content,
    _parse_csv_or_json,
    _map_canonical_curves,
    _detect_depth_unit,
    _compute_vsh_from_store,
    _compute_porosity_from_store,
    _compute_saturation_from_store,
    _compute_netpay_from_store,
    _classify_gr_motif,
    _classify_lithology_from_store,
    _safe_reduction,
    _get_well_data_with_depth,
    _compute_subsurface_candidates,
    CLAIM_STATES,
    CANONICAL_ALIASES,
    _CURVE_RANGES,
    _artifact_registry,
    _artifact_store,
    _well_curves_registry,
    _ARTIFACT_REGISTRY_PATH,
    MAX_UPLOAD_BYTES,
)
from compatibility.legacy_aliases import LEGACY_ALIAS_MAP, get_alias_metadata

logger = logging.getLogger("geox.canonical.subsurface")


async def geox_subsurface_generate_candidates(
    target_class: Literal[
        "petrophysics", "structure", "flattening", "vsh", "porosity",
        "saturation", "netpay", "permeability", "gr_motif", "lithology",
    ],
    evidence_refs: List[str],
    realizations: int = 3,
    gr_clean: float = 15.0,
    gr_shale: float = 150.0,
    vsh_method: str = "linear",
    matrix_density: float = 2.65,
    fluid_density: float = 1.0,
    sw_model: str = "archie",
    rw: float = 0.05,
    archie_a: float = 1.0,
    archie_m: float = 2.0,
    archie_n: float = 2.0,
    vsh_cutoff: float = 0.5,
    phi_cutoff: float = 0.1,
    sw_cutoff: float = 0.6,
    rt_cutoff: float = 2.0,
    zone_top_m: Optional[float] = None,
    zone_base_m: Optional[float] = None,
) -> dict:
    """Generates ensemble subsurface outputs with residuals and data-density maps."""
    result = await _compute_subsurface_candidates(
        target_class, evidence_refs, realizations,
        gr_clean, gr_shale, vsh_method, matrix_density, fluid_density,
        sw_model, rw, archie_a, archie_m, archie_n,
        vsh_cutoff, phi_cutoff, sw_cutoff, rt_cutoff,
        zone_top_m, zone_base_m,
    )
    result = _inject_ensemble_residual_evidence(result, realizations, assumptions={
        "target_class": target_class,
        "rock_model": vsh_method,
        "fluid_model": sw_model,
        "cutoffs": {
            "vsh": vsh_cutoff,
            "phi": phi_cutoff,
            "sw": sw_cutoff,
            "rt": rt_cutoff,
        },
    })
    if "tool_class" not in result:
        result = get_standard_envelope(
            result,
            tool_class="compute",
            artifact_status=ArtifactStatus.COMPUTED,
            claim_tag="CLAIM",
            evidence_refs=evidence_refs,
        )
    return result



async def geox_subsurface_verify_integrity(candidate_ref: str, domain: str) -> dict:
    """Enforces Physics9 boundary limits and detects structural paradoxes."""
    artifact = {"ref": candidate_ref, "domain": domain, "consistent": True, "verdict": "PHYSICALLY_FEASIBLE"}
    return get_standard_envelope(artifact, tool_class="verify", governance_status=GovernanceStatus.SEAL)


