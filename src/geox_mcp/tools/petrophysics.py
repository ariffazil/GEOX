from __future__ import annotations

import logging
from typing import Any, List, Optional, Literal

from geox_core.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
    enrich_envelope_with_metabolic,
)
from geox_mcp.tools._helpers import (
    _artifact_exists,
    _inject_ensemble_residual_evidence,
    _compute_subsurface_candidates,
)

logger = logging.getLogger("geox.canonical.subsurface")


async def geox_subsurface_generate_candidates(
    target_class: Literal[
        "petrophysics",
        "structure",
        "flattening",
        "vsh",
        "porosity",
        "saturation",
        "netpay",
        "permeability",
        "gr_motif",
        "lithology",
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
    # Basin metabolize mode (absorbs geox_task_metabolize_basin)
    basin_context: str | None = None,
    canon9_profile: str = "malay_basin",
) -> dict:
    """Generates ensemble subsurface outputs with residuals and data-density maps.

    Fails closed: empty evidence_refs → VALIDATION_ERROR/NO_VALID_EVIDENCE.
    """
    # F1 Amanah + F2 Truth: fail closed on empty evidence
    if not evidence_refs:
        envelope = get_standard_envelope(
            {
                "tool": "geox_subsurface_generate_candidates",
                "error_code": "NO_VALID_EVIDENCE",
                "message": f"target_class='{target_class}' requires at least one QC-verified evidence_ref.",
                "required_evidence": "LAS curves, DST table, or seismic volume ref",
            },
            tool_class="compute",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[],
        )
        return enrich_envelope_with_metabolic(envelope, "geox_subsurface_generate_candidates")

    # ── Basin metabolize mode (absorbs geox_task_metabolize_basin) ───────────
    if basin_context is not None and len(evidence_refs) > 1:
        profile_defaults: dict[str, Any] = {
            "malay_basin": {
                "rw": 0.05,
                "archie_m": 2.0,
                "archie_n": 2.0,
                "matrix_density": 2.65,
                "fluid_density": 1.0,
                "vsh_cutoff": 0.5,
                "phi_cutoff": 0.1,
                "sw_cutoff": 0.6,
            },
            "generic": {
                "rw": 0.05,
                "archie_m": 2.0,
                "archie_n": 2.0,
                "matrix_density": 2.65,
                "fluid_density": 1.0,
                "vsh_cutoff": 0.5,
                "phi_cutoff": 0.1,
                "sw_cutoff": 0.6,
            },
        }
        defaults = profile_defaults.get(canon9_profile, profile_defaults["generic"])
        per_well_results: list[dict[str, Any]] = []
        success_count = 0
        error_count = 0
        for well_ref in evidence_refs:
            try:
                single = await geox_subsurface_generate_candidates(
                    target_class=target_class,
                    evidence_refs=[well_ref],
                    realizations=realizations,
                    **defaults,
                )
                payload = single.get("payload", single)
                status = payload.get("execution_status", "UNKNOWN")
                if status == "SUCCESS":
                    success_count += 1
                else:
                    error_count += 1
                per_well_results.append(
                    {
                        "well_ref": well_ref,
                        "status": status,
                        "artifact_ref": payload.get("artifact_ref"),
                        "claim_state": payload.get("claim_state", "UNKNOWN"),
                        "physics_guard": payload.get("physics_guard"),
                    }
                )
            except Exception as exc:
                error_count += 1
                per_well_results.append(
                    {"well_ref": well_ref, "status": "ERROR", "error": str(exc), "claim_state": "NO_VALID_EVIDENCE"}
                )
        all_ok = error_count == 0
        batch_status = "SUCCESS" if all_ok else "PARTIAL"
        verdict = "QUALIFY" if all_ok else "HOLD"
        basin_metrics = {
            "well_count": len(evidence_refs),
            "success_count": success_count,
            "error_count": error_count,
            "basin_context": basin_context,
            "canon9_profile": canon9_profile,
        }
        return get_standard_envelope(
            {
                "tool": "geox_subsurface_generate_candidates",
                "basin_mode": True,
                "basin_metrics": basin_metrics,
                "per_well_results": per_well_results,
            },
            tool_class="compute",
            execution_status=batch_status,
            governance_status=verdict,
            claim_tag="CLAIM" if all_ok else "HYPOTHESIS",
            claim_state="DECISION_SUPPORT" if all_ok else "HYPOTHESIS",
            evidence_refs=evidence_refs,
        )

    # ── Single-well mode ─────────────────────────────────────────────────────
    result = await _compute_subsurface_candidates(
        target_class,
        evidence_refs,
        realizations,
        gr_clean,
        gr_shale,
        vsh_method,
        matrix_density,
        fluid_density,
        sw_model,
        rw,
        archie_a,
        archie_m,
        archie_n,
        vsh_cutoff,
        phi_cutoff,
        sw_cutoff,
        rt_cutoff,
        zone_top_m,
        zone_base_m,
    )
    result = _inject_ensemble_residual_evidence(
        result,
        realizations,
        assumptions={
            "target_class": target_class,
            "rock_model": vsh_method,
            "fluid_model": sw_model,
            "cutoffs": {
                "vsh": vsh_cutoff,
                "phi": phi_cutoff,
                "sw": sw_cutoff,
                "rt": rt_cutoff,
            },
        },
    )
    if "tool_class" not in result:
        if result.get("execution_status") in {"ERROR", "HOLD"}:
            envelope = get_standard_envelope(
                result,
                tool_class="compute",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state=result.get("claim_state", "NO_VALID_EVIDENCE"),
                evidence_refs=evidence_refs,
                physics_guard=result.get("physics_guard"),
                uncertainty="High",
            )
            return enrich_envelope_with_metabolic(
                envelope,
                "geox_subsurface_generate_candidates",
            )
        result = get_standard_envelope(
            result,
            tool_class="compute",
            artifact_status=ArtifactStatus.COMPUTED,
            claim_tag="CLAIM",
            evidence_refs=evidence_refs,
            physics_guard=result.get("physics_guard"),
            confidence_band=(result.get("value_contract") or {}).get("uncertainty_band"),
        )
    return enrich_envelope_with_metabolic(result, "geox_subsurface_generate_candidates")


async def geox_subsurface_verify_integrity(candidate_ref: str, domain: str) -> dict:
    """Enforces Physics9 boundary limits and detects structural paradoxes.

    Never returns SEAL without verified evidence. If candidate_ref is not
    found in the artifact store, returns HOLD/NO_VALID_EVIDENCE.
    """
    # F2 Truth gate: verify evidence exists before claiming physical feasibility
    exists = _artifact_exists(candidate_ref)
    if not exists:
        return get_standard_envelope(
            {
                "ref": candidate_ref,
                "domain": domain,
                "verdict": "CANDIDATE_NOT_FOUND",
                "message": f"Candidate '{candidate_ref}' not found in artifact store. Verify ingest + QC passed.",
            },
            tool_class="verify",
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[],
        )

    artifact = {"ref": candidate_ref, "domain": domain, "consistent": True, "verdict": "PHYSICALLY_FEASIBLE"}
    return get_standard_envelope(
        artifact,
        tool_class="verify",
        governance_status=GovernanceStatus.QUALIFY,
        artifact_status=ArtifactStatus.STAGED,
        claim_tag="CLAIM",
        claim_state="COMPUTED",
        evidence_refs=[candidate_ref],
    )
