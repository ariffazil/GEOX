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

import json
import logging
from typing import Any

logger = logging.getLogger("geox_mcp.evidence_postcondition")

# ── Per-tool evidence contracts ──────────────────────────────────────────
# Each entry: {tool_name: list[required_non_empty_keys]}
# A tool with ANY of its required keys containing a non-null, non-empty value
# passes the evidence gate. Only tools where ALL required keys are null/empty
# AND the tool claims success are downgraded.

EVIDENCE_CONTRACTS: dict[str, list[str] | None] = {
    # ── Compute / petrophysics ──────────────────────────────────────
    "geox_petrophysics": ["net_pay", "curves", "curves_available", "vsh", "porosity", "sw"],
    "geox_seismic_compute": ["synthetic_trace", "reflectivity", "amplitude", "attribute", "zoeppritz", "rpp", "shuey", "lmr", "castagna"],
    "geox_seismic_interpret": ["horizons", "faults", "interpretation_bundle", "geometry"],
    "geox_seismic_ingest": ["volume_ref", "headers", "trace_count", "sample_count"],
    "geox_sequence": ["correlation", "zones", "tops", "strat_column"],
    "geox_subsurface_model": ["layers", "prisms", "model", "density_model"],
    "geox_geomechanics": ["moduli", "stress_polygon", "stress_polygon_vertices", "elastic_properties", "pressure", "sv_mpa"],
    "geox_gravmag_studio": ["prisms", "forward_model", "residual", "anomaly"],
    "geox_lem_predict": ["predictions", "porosity", "sw", "lithology"],
    "geox_sediment_mass_balance": ["source_eroded_km3", "preserved_volumes", "bypassed"],
    "geox_thermal_maturity_history": ["maturity", "ro", "tti", "burial_curve"],
    "geox_basin_backstrip": ["subsidence_curve", "tectonic_subsidence", "total_subsidence"],
    # ── Basin / Earth state ─────────────────────────────────────────
    # C1 FIX (2026-08-26): keys must match actual result structure from
    # geox_basin_profile → get_standard_envelope. Data lives inside
    # primary_artifact as observed/derived/interpreted/process_hypotheses.
    # _lookup_evidence_value searches top-level + one nested dict level.
    "geox_basin": ["observed", "derived", "interpreted", "process_hypotheses"],
    "geox_deep_time_state": [
        "variables",
        "data",
        "state_vector",
        "n_variables",
        "primary_artifact",
        "age_resolution",
        "execution_status",
    ],
    "geox_contradiction_scan": ["contradictions", "findings", "severity"],
    "geox_falsify": ["kill_results", "verdict", "kill_matrix"],
    # geox_evidence removed from EVIDENCE_CONTRACTS 2026-08-06 (geo-stable-fix).
    # Rationale: geox_evidence is a multi-mode dispatcher (discover|synthesize|
    # abduct|contradict|spatial_block|ingest_literature) in evidence_unified.py.
    # Each mode returns a DIFFERENT key set; the previous contract
    # (evidence_items/synthesis/sources) was hallucinated — no mode emits those keys.
    # Empty contract (line was "") caused FALSE_SUCCESS downgrade because
    # the postcondition loop iterates over an empty list and never finds evidence.
    # Moving to NON_COMPLIANT until mode-aware contracts land (requires plumbing
    # mode through check_evidence_postcondition call site).
    # "geox_evidence": <placeholder — see NON_COMPLIANT.add() below>,
    "geox_evidence_synthesize": ["evidence_items", "synthesis", "sources"],
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
    # NOTE: do not list claim-only fields (status/ok) — they are success
    # assertions, not evidence. A payload with only status:OK is FALSE SUCCESS.
    "geox_surface_status": [
        "canonical_tools",
        "registry_truth",
        "tool_count",
        "surface_attestation",
        "surface_hash",
        "callable_tools",
        "public_count",
    ],
    "geox_workspace": ["basin", "play", "well_id", "field", "workspace", "context"],
    "geox_to_wealth_bridge": ["prospect_ref", "npv_usd", "score_kernel"],
    "geox_prospect": ["prospect_ref", "volumetrics", "pos", "risk"],
    # ── Geological model ─────────────────────────────────────────────
    "geox_geological_model_generate": ["image_path", "description", "parameters_used"],
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


def coerce_tool_result_to_dict(result: Any) -> dict[str, Any]:
    """Extract a domain dict from FastMCP ToolResult / MCP CallToolResult / dict.

    Runtime fact (2026-08-04): call_next(context) returns ToolResult, not dict.
    Signature used to claim dict[str, Any] while the wire type was ToolResult —
    .get() then AttributeError, silently swallowed → false SUCCESS (G8 variant).

    Order of preference:
      1. plain dict
      2. ToolResult.structured_content (dict)
      3. first text content block parsed as JSON
      4. model_dump() / __dict__ fallback (never empty without record)
    """
    if result is None:
        return {}
    if isinstance(result, dict):
        return result

    # FastMCP ToolResult / pydantic models with structured_content
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict) and structured:
        return structured

    # content: list of ContentBlock with .text
    content = getattr(result, "content", None)
    if content:
        try:
            blocks = list(content)
        except TypeError:
            blocks = []
        for block in blocks:
            text = getattr(block, "text", None)
            if text is None and isinstance(block, dict):
                text = block.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            try:
                parsed = json.loads(text)
            except Exception:
                continue
            if isinstance(parsed, dict):
                return parsed

    # Pydantic v2 model_dump
    if hasattr(result, "model_dump") and callable(result.model_dump):
        try:
            dumped = result.model_dump()
            if isinstance(dumped, dict):
                sc = dumped.get("structured_content")
                if isinstance(sc, dict) and sc:
                    return sc
                return dumped
        except Exception:
            pass

    # Last resort — never pretend we have a domain dict of Nothing
    raw = getattr(result, "__dict__", None)
    if isinstance(raw, dict) and raw:
        return {"_raw_tool_result": True, **{k: v for k, v in raw.items() if not k.startswith("_")}}

    return {"_coerce_failed": True, "_type": type(result).__name__}


def apply_domain_dict_to_result(result: Any, domain: dict[str, Any]) -> Any:
    """Write an updated domain dict back onto a ToolResult (or return dict).

    Preserves ToolResult identity for FastMCP while reflecting evidence
    postcondition mutations (isError, status, _evidence_postcondition).
    """
    if isinstance(result, dict):
        return domain

    # Mutate ToolResult in place when possible
    is_err = bool(domain.get("isError") or domain.get("ok") is False)
    if hasattr(result, "structured_content"):
        try:
            result.structured_content = domain
        except Exception:
            pass
    if hasattr(result, "is_error"):
        try:
            result.is_error = is_err
        except Exception:
            pass
    # Keep text content in sync so clients that only read content[] see the downgrade
    if hasattr(result, "content"):
        try:
            from mcp.types import TextContent

            result.content = [TextContent(type="text", text=json.dumps(domain, default=str))]
        except Exception:
            try:
                # Minimal duck-type block
                result.content = [{"type": "text", "text": json.dumps(domain, default=str)}]
            except Exception:
                pass
    return result


def _lookup_evidence_value(result: dict[str, Any], key: str) -> Any:
    """Top-level key, else first nested dict that carries key (workspace.basin)."""
    if key in result:
        return result.get(key)
    for val in result.values():
        if isinstance(val, dict) and key in val:
            return val.get(key)
    return None


def _is_substantive(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return True
    if isinstance(val, (int, float)):
        return True
    if isinstance(val, (list, tuple, dict, set, str)):
        return len(val) > 0  # type: ignore[arg-type]
    return bool(val)


def ensure_fastmcp_tool_result(result: Any) -> Any:
    """Guarantee FastMCP wire type (must expose to_mcp_result).

    If a pipeline step demoted ToolResult → dict, re-wrap so the MCP
    transport does not raise: 'dict' object has no attribute 'to_mcp_result'.
    """
    if result is None:
        return result
    if callable(getattr(result, "to_mcp_result", None)):
        return result
    if isinstance(result, dict):
        try:
            from fastmcp.tools.base import ToolResult

            is_err = bool(result.get("isError") or result.get("ok") is False)
            return ToolResult(structured_content=result, is_error=is_err)
        except Exception as exc:
            logger.error("ensure_fastmcp_tool_result: wrap failed: %s", exc)
            return result
    return result


def check_evidence_postcondition(
    tool_name: str,
    result: Any,
) -> Any:
    """Apply evidence post-condition check to a tool result.

    Accepts dict **or** FastMCP ToolResult. Returns the same outer type
    with domain fields updated. SUCCESS + null evidence → FAILURE.

    G8: never silently no-op on type mismatch — coerce or mark verification
    failed on the payload.
    """
    required_keys = EVIDENCE_CONTRACTS.get(tool_name)
    original = result
    domain = coerce_tool_result_to_dict(result)

    if required_keys is None:
        if tool_name in NON_COMPLIANT:
            logger.debug(
                "EVIDENCE_POST: tool=%s NON_COMPLIANT (no contract defined)",
                tool_name,
            )
        return original

    if domain.get("_coerce_failed"):
        # Could not extract domain — do not claim evidence verified
        logger.error(
            "EVIDENCE_POST: tool=%s COERCE_FAILED type=%s — cannot verify evidence",
            tool_name,
            domain.get("_type"),
        )
        failed = {
            "ok": False,
            "isError": True,
            "status": "INVALID",
            "execution_status": "ERROR",
            "error": (
                f"EVIDENCE_POST_COERCE_FAILED: cannot read domain payload from "
                f"{domain.get('_type')} for {tool_name}. Evidence verification "
                f"did not run — refusing silent SUCCESS (G8)."
            ),
            "_evidence_postcondition": {
                "applied": True,
                "verdict": "COERCE_FAILED",
                "result_type": domain.get("_type"),
                "spec": "geox-evidence-postcondition-v1",
            },
        }
        return apply_domain_dict_to_result(original, failed)

    # Determine if the tool is claiming success.
    # execution_status missing is NOT an automatic success claim — that
    # previously let empty payloads pass the gate (false SUCCESS / G8).
    # Explicit isError:false is a success claim (workspace and peers).
    exec_st = domain.get("execution_status")
    claims_success = (
        domain.get("ok") is True
        or domain.get("status") in ("OK", "SUCCESS", "healthy", "HEALTHY")
        or exec_st in ("SUCCESS", "COMPLETED")
        or domain.get("isError") is False
    )
    is_already_error = (
        domain.get("isError") is True
        or domain.get("status") in ("INVALID", "ERROR", "FAILURE")
        or bool(domain.get("error"))
    )

    if is_already_error or not claims_success:
        return original  # Already honest about failure, or not claiming success

    # Check if ANY required key has substantive content (incl. one-level nest)
    has_evidence = False
    for key in required_keys:
        val = _lookup_evidence_value(domain, key)
        if _is_substantive(val):
            has_evidence = True
            break

    if has_evidence:
        # Stamp that verification actually ran (anti-silent-bypass)
        domain = dict(domain)
        domain["_evidence_postcondition"] = {
            "applied": True,
            "verdict": "PASS",
            "spec": "geox-evidence-postcondition-v1",
        }
        return apply_domain_dict_to_result(original, domain)

    # FALSE SUCCESS: claims success but has zero evidence
    logger.warning(
        "EVIDENCE_POST: tool=%s FALSE_SUCCESS — claimed ok/SUCCESS but all "
        "required evidence fields (%s) are null/empty. Downgrading to FAILURE.",
        tool_name,
        ", ".join(required_keys[:5]),
    )

    domain = dict(domain)
    domain["ok"] = False
    domain["isError"] = True
    domain["status"] = "INVALID"
    domain["execution_status"] = "ERROR"
    domain["governance_status"] = "HOLD"
    domain["confidence"] = min(float(domain.get("confidence") or 0.10), 0.10)
    domain["authority_claim"] = "ADVISORY"
    domain.setdefault(
        "error",
        f"EVIDENCE_SCHEMA_VIOLATION: {tool_name} returned SUCCESS but produced "
        f"no substantive evidence. All required fields ({', '.join(required_keys[:5])}...)"
        f" are null, empty, or missing. This is a false success per Stage-1 "
        f"outputSchema enforcement (commit 80fc80fd pattern).",
    )
    domain["_evidence_postcondition"] = {
        "applied": True,
        "verdict": "DOWNGRADED",
        "missing_evidence": required_keys,
        "spec": "geox-evidence-postcondition-v1",
    }

    return apply_domain_dict_to_result(original, domain)
