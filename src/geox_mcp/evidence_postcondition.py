"""
evidence_postcondition — Stage-1 outputSchema enforcement (2026-07-25).

Applies the petrophysics pattern (commit 80fc80fd) across all 32 canonical
public tools: SUCCESS with null evidence = FAILURE.

Per-tool evidence contracts define which fields constitute substantive output.
A tool that returns ok:true / status:OK / SUCCESS but has all evidence fields
null/empty/missing is a FALSE SUCCESS and is downgraded to:

    isError: true, status: INVALID, confidence: 0.10, authority_claim: ADVISORY

The compliance matrix at module bottom shows which tools have post-conditions
and which are still NON-COMPLIANT (evidence contract not yet defined).

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox_mcp.evidence_postcondition")

# ── Per-tool evidence contracts ──────────────────────────────────────────
# Each entry: {tool_name: list[required_non_empty_keys]}
# A tool with ANY of its required keys containing a non-null, non-empty value
# passes the evidence gate. Only tools where ALL required keys are null/empty
# AND the tool claims success are downgraded.

EVIDENCE_CONTRACTS: dict[str, list[str]] = {
    # ── Compute / petrophysics ──────────────────────────────────────
    "geox_petrophysics": ["net_pay", "curves", "curves_available", "vsh", "porosity", "sw"],
    "geox_seismic_compute": ["synthetic_trace", "reflectivity", "amplitude", "attribute"],
    "geox_seismic_interpret": ["horizons", "faults", "interpretation_bundle", "geometry"],
    "geox_seismic_ingest": ["volume_ref", "headers", "trace_count", "sample_count"],
    "geox_sequence": ["correlation", "zones", "tops", "strat_column"],
    "geox_subsurface_model": ["layers", "prisms", "model", "density_model"],
    "geox_geomechanics": ["moduli", "stress_polygon", "elastic_properties", "pressure"],
    "geox_gravmag_studio": ["prisms", "forward_model", "residual", "anomaly"],
    "geox_lem_predict": ["predictions", "porosity", "sw", "lithology"],
    "geox_sediment_mass_balance": ["source_eroded_km3", "preserved_volumes", "bypassed"],
    "geox_thermal_maturity_history": ["maturity", "ro", "tti", "burial_curve"],
    "geox_basin_backstrip": ["subsidence_curve", "tectonic_subsidence", "total_subsidence"],
    # ── Basin / Earth state ─────────────────────────────────────────
    "geox_basin": ["basin_profile", "tectonic_summary", "stratigraphy", "macrostrat_units"],
    "geox_deep_time_state": ["variables", "data", "state_vector", "n_variables"],
    "geox_contradiction_scan": ["contradictions", "findings", "severity"],
    "geox_falsify": ["kill_results", "verdict", "kill_matrix"],
    "geox_evidence": ["evidence_items", "synthesis", "sources"],
    "geox_claim": ["claim_id", "claim_text", "verdict", "evidence_ids"],
    "geox_claim_graph_evaluate": ["claims", "edges", "verdicts", "propagation"],
    # ── Visual / map ────────────────────────────────────────────────
    "geox_visual_understand": ["patterns", "features", "classification"],
    "geox_visual_generate_hypotheses": ["hypotheses", "candidates", "geometry"],
    "geox_map_layers_list": ["layers", "layer_ids", "bbox"],
    "geox_map_scene_plan": ["scene_id", "layer_ids", "bbox"],
    "geox_map_render_preview": ["scene_id", "image", "preview_url"],
    "geox_map_export_package": ["scene_plan_id", "formats", "output"],
    # ── Well ────────────────────────────────────────────────────────
    "geox_well_ingest": ["well_id", "curves", "las_metadata", "artifact_ref"],
    "geox_well_view": ["well_id", "curves", "depths"],
    "geox_well_qc": ["artifact_ref", "qc_results", "issues", "grade"],
    "geox_well_desk": ["well_id", "curves", "panels", "tracks"],
    # ── Registry / bridge ───────────────────────────────────────────
    "geox_surface_status": ["canonical_tools", "registry_truth", "tool_count"],
    "geox_workspace": ["basin", "play", "well_id", "field"],
    "geox_to_wealth_bridge": ["prospect_ref", "npv_usd", "score_kernel"],
    "geox_prospect": ["prospect_ref", "volumetrics", "pos", "risk"],
}

# Tools without an evidence contract yet (NON-COMPLIANT).
# These will pass through without post-condition checking.
NON_COMPLIANT: set[str] = set()

# ── Build the compliance matrix ──────────────────────────────────────────


def _build_compliance_matrix() -> None:
    """Populate NON_COMPLIANT from CANONICAL_PUBLIC_TOOLS minus EVIDENCE_CONTRACTS."""
    global NON_COMPLIANT
    try:
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

        contracted = set(EVIDENCE_CONTRACTS.keys())
        all_canonical = set(CANONICAL_PUBLIC_TOOLS)
        NON_COMPLIANT = all_canonical - contracted
    except Exception:
        NON_COMPLIANT = set()


_build_compliance_matrix()


def compliance_matrix() -> dict[str, Any]:
    """Return the compliance matrix: which tools have evidence contracts."""
    contracted = set(EVIDENCE_CONTRACTS.keys())
    all_tools = contracted | NON_COMPLIANT
    return {
        "total_tools": len(all_tools),
        "compliant": sorted(contracted),
        "compliant_count": len(contracted),
        "non_compliant": sorted(NON_COMPLIANT),
        "non_compliant_count": len(NON_COMPLIANT),
        "compliance_pct": round(len(contracted) / max(1, len(all_tools)) * 100),
        "spec": "geox-evidence-postcondition-v1",
        "rule": "SUCCESS with null evidence → FAILURE (isError:true, confidence:0.10)",
    }


def check_evidence_postcondition(
    tool_name: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Apply evidence post-condition check to a tool result.

    Returns modified result (or original if tool is non-compliant or passes).
    """
    required_keys = EVIDENCE_CONTRACTS.get(tool_name)
    if required_keys is None:
        # Non-compliant tool — pass through, logged at debug
        if tool_name in NON_COMPLIANT:
            logger.debug(
                "EVIDENCE_POST: tool=%s NON_COMPLIANT (no contract defined)",
                tool_name,
            )
        return result

    # Determine if the tool is claiming success
    claims_success = (
        result.get("ok") is True
        or result.get("status") in ("OK", "SUCCESS")
        or result.get("execution_status") in ("SUCCESS", "COMPLETED", None)
    )
    is_already_error = (
        result.get("isError") is True or result.get("status") in ("INVALID", "ERROR", "FAILURE") or bool(result.get("error"))
    )

    if is_already_error or not claims_success:
        return result  # Already honest about failure, or not claiming success

    # Check if ANY required key has substantive content
    has_evidence = False
    for key in required_keys:
        val = result.get(key)
        if val is None:
            continue
        if isinstance(val, bool):
            has_evidence = True
            break
        if isinstance(val, (int, float)):
            has_evidence = True
            break
        if isinstance(val, (list, tuple, dict, set, str)):
            if len(val) > 0:  # type: ignore[arg-type]
                has_evidence = True
                break
        # Non-empty-ish
        if val:
            has_evidence = True
            break

    if has_evidence:
        return result  # Evidence present — honest success

    # FALSE SUCCESS: claims success but has zero evidence
    logger.warning(
        "EVIDENCE_POST: tool=%s FALSE_SUCCESS — claimed ok/SUCCESS but all "
        "required evidence fields (%s) are null/empty. Downgrading to FAILURE.",
        tool_name,
        ", ".join(required_keys[:5]),
    )

    result["ok"] = False
    result["isError"] = True
    result["status"] = "INVALID"
    result["execution_status"] = "ERROR"
    result["governance_status"] = "HOLD"
    result["confidence"] = min(result.get("confidence", 0.10), 0.10)
    result["authority_claim"] = "ADVISORY"
    result.setdefault(
        "error",
        f"EVIDENCE_SCHEMA_VIOLATION: {tool_name} returned SUCCESS but produced "
        f"no substantive evidence. All required fields ({', '.join(required_keys[:5])}...)"
        f" are null, empty, or missing. This is a false success per Stage-1 "
        f"outputSchema enforcement (commit 80fc80fd pattern).",
    )
    result["_evidence_postcondition"] = {
        "applied": True,
        "verdict": "DOWNGRADED",
        "missing_evidence": required_keys,
        "spec": "geox-evidence-postcondition-v1",
    }

    return result
