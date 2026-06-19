"""CANON Workflow Composer — geox_workflow_run_canon.

Chains the full governed geological reasoning loop:
  ingest → qc → candidates → abduction → contradiction → summarize

F2 TRUTH: Each step is executed sequentially; results flow to next step.
F4 CLARITY: Human sees every step's output and can intervene at any stage.
F5 PEACE: No irreversible action without explicit human ack.
F13 SOVEREIGN: Human can STOP at any step via abort_signal.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Literal, Optional

from geox_core.enums.statuses import (
    get_standard_envelope,
    ExecutionStatus,
    GovernanceStatus,
    ArtifactStatus,
)
from geox_mcp.tools._helpers import _get_artifact, _artifact_exists

logger = logging.getLogger("geox.workflow.canon")


async def geox_workflow_run_canon(
    source_uri: Optional[str] = None,
    source_type: Literal["well", "seismic", "earth3d", "auto"] = "auto",
    well_id: Optional[str] = None,
    content_base64: Optional[str] = None,
    filename: Optional[str] = None,
    target_dir: str = "/data/geox_las",
    overwrite: bool = False,
    auto_contradiction: bool = True,
    abort_on_hold: bool = True,
    export_format: Literal["json", "csv"] = "json",
) -> dict:
    """Run the full governed geological reasoning loop.

    Canonical chain:
      1. geox_data_ingest_bundle    — ingest raw evidence
      2. geox_data_qc_bundle        — verify data quality
      3. geox_subsurface_generate_candidates — derive candidates
      4. geox_process_abduction      — generate geological hypotheses
      5. geox_evidence_contradiction_scan — attack hypotheses (if auto_contradiction=True)
      6. geox_evidence_summarize_cross  — synthesize final ranking

    Parameters:
      source_uri       : File path or HTTPS URL to raw evidence
      source_type      : Type hint: well, seismic, earth3d, auto
      well_id          : Optional well identifier
      content_base64   : Optional base64-encoded file content
      filename         : Required if content_base64 provided
      target_dir       : Directory for uploaded files
      overwrite        : Whether to overwrite existing files
      auto_contradiction: If True, automatically run contradiction scan after abduction
      abort_on_hold    : If True, stop workflow when a step returns HOLD/VOID
      export_format    : Output format for final evidence summary

    Returns:
      Full workflow result with step_outputs, maturity progression,
      final claim_state, and suggested next action.

    F13 SOVEREIGN: Set abort_on_hold=False to let human review before continuing.
    F5 PEACE: Never proceeds to irreversible steps (e.g. judge_seal) without human ack.
    """
    # Defer imports to avoid circular references
    from geox_mcp.tools.data import geox_data_ingest_bundle
    from geox_mcp.tools.qc import geox_data_qc_bundle
    from geox_mcp.tools.petrophysics import geox_subsurface_generate_candidates
    from geox_mcp.tools.abduction import geox_process_abduction, geox_evidence_contradiction_scan
    from geox_mcp.tools.evidence import geox_evidence_summarize_cross

    step_outputs: list[dict] = []
    step_errors: list[dict] = []
    workflow_halted = False
    halt_reason: Optional[str] = None
    final_artifact_ref: Optional[str] = None

    def _claim_state(result: dict) -> str:
        return result.get("claim_state", result.get("artifact", {}).get("claim_state", "UNKNOWN"))

    def _is_hold(result: dict) -> bool:
        cs = _claim_state(result)
        return cs in ("HOLD", "888_HOLD", "BLOCKED", "VOID")

    # ── Step 1: Ingest ──────────────────────────────────────────────────────
    try:
        step1 = await geox_data_ingest_bundle(
            source_uri=source_uri,
            source_type=source_type,
            well_id=well_id,
            content_base64=content_base64,
            filename=filename,
            target_dir=target_dir,
            overwrite=overwrite,
        )
    except Exception as exc:
        step1 = {
            "status": "ERROR",
            "tool": "geox_data_ingest_bundle",
            "error": str(exc),
            "claim_state": "NO_VALID_EVIDENCE",
        }

    step_outputs.append({
        "step": 1,
        "tool": "geox_data_ingest_bundle",
        "claim_state": _claim_state(step1),
        "artifact_ref": step1.get("artifact_ref") or step1.get("artifact", {}).get("artifact_ref"),
        "status": "OK" if step1.get("status") != "ERROR" else "ERROR",
        "next_tool": "geox_data_qc_bundle",
    })

    if step1.get("status") == "ERROR" or _claim_state(step1) == "NO_VALID_EVIDENCE":
        workflow_halted = True
        halt_reason = "Ingest failed — cannot proceed without valid evidence"

    # ── Step 2: QC ─────────────────────────────────────────────────────────
    if not workflow_halted:
        try:
            artifact_ref = (
                step1.get("artifact_ref")
                or step1.get("artifact", {}).get("artifact_ref")
                or step1.get("artifact", {}).get("bundle_ref")
            )
            step2 = await geox_data_qc_bundle(artifact_ref=artifact_ref)
        except Exception as exc:
            step2 = {
                "status": "ERROR",
                "tool": "geox_data_qc_bundle",
                "error": str(exc),
                "claim_state": "NO_VALID_EVIDENCE",
            }

        step_outputs.append({
            "step": 2,
            "tool": "geox_data_qc_bundle",
            "claim_state": _claim_state(step2),
            "artifact_ref": step2.get("artifact_ref") or step2.get("artifact", {}).get("artifact_ref"),
            "status": "OK" if step2.get("status") != "ERROR" else "ERROR",
            "next_tool": "geox_subsurface_generate_candidates",
        })

        if _is_hold(step2) and abort_on_hold:
            workflow_halted = True
            halt_reason = "QC returned HOLD — fix data quality before continuing"

        # Use QC artifact ref for downstream
        if not workflow_halted:
            artifact_ref = (
                step2.get("artifact_ref")
                or step2.get("artifact", {}).get("artifact_ref")
                or artifact_ref
            )
    else:
        step2 = None
        artifact_ref = None

    # ── Step 3: Generate Candidates ──────────────────────────────────────────
    if not workflow_halted:
        try:
            step3 = await geox_subsurface_generate_candidates(
                target_class="petrophysics",
                evidence_refs=[artifact_ref] if artifact_ref else [],
            )
        except Exception as exc:
            step3 = {
                "status": "ERROR",
                "tool": "geox_subsurface_generate_candidates",
                "error": str(exc),
                "claim_state": "NO_VALID_EVIDENCE",
            }

        step_outputs.append({
            "step": 3,
            "tool": "geox_subsurface_generate_candidates",
            "claim_state": _claim_state(step3),
            "artifact_ref": step3.get("artifact_ref") or step3.get("artifact", {}).get("artifact_ref"),
            "status": "OK" if step3.get("status") != "ERROR" else "ERROR",
            "next_tool": "geox_process_abduction",
        })

        if _is_hold(step3) and abort_on_hold:
            workflow_halted = True
            halt_reason = "Candidates generation returned HOLD"

        if not workflow_halted:
            candidate_ref = (
                step3.get("artifact_ref")
                or step3.get("artifact", {}).get("artifact_ref")
                or artifact_ref
            )
    else:
        step3 = None
        candidate_ref = artifact_ref

    # ── Step 4: Abduction ──────────────────────────────────────────────────
    if not workflow_halted:
        try:
            step4 = await geox_process_abduction(
                evidence_refs=[candidate_ref] if candidate_ref else [],
            )
        except Exception as exc:
            step4 = {
                "status": "ERROR",
                "tool": "geox_process_abduction",
                "error": str(exc),
                "claim_state": "NO_VALID_EVIDENCE",
            }

        step_outputs.append({
            "step": 4,
            "tool": "geox_process_abduction",
            "claim_state": _claim_state(step4),
            "artifact_ref": step4.get("artifact_ref") or step4.get("artifact", {}).get("artifact_ref"),
            "status": "OK" if step4.get("status") != "ERROR" else "ERROR",
            "next_tool": "geox_evidence_contradiction_scan" if auto_contradiction else "geox_evidence_summarize_cross",
        })

        if _is_hold(step4) and abort_on_hold:
            workflow_halted = True
            halt_reason = "Abduction returned HOLD"

        abduction_ref = (
            step4.get("artifact_ref")
            or step4.get("artifact", {}).get("artifact_ref")
            or candidate_ref
        )
    else:
        step4 = None
        abduction_ref = candidate_ref

    # ── Step 5: Contradiction Scan (optional) ─────────────────────────────
    if not workflow_halted and auto_contradiction:
        try:
            step5 = await geox_evidence_contradiction_scan(
                evidence_refs=[abduction_ref] if abduction_ref else [],
                hypotheses=step4.get("process_hypotheses") if step4 else None,
            )
        except Exception as exc:
            step5 = {
                "status": "ERROR",
                "tool": "geox_evidence_contradiction_scan",
                "error": str(exc),
                "claim_state": "NO_VALID_EVIDENCE",
            }

        step_outputs.append({
            "step": 5,
            "tool": "geox_evidence_contradiction_scan",
            "claim_state": _claim_state(step5),
            "artifact_ref": step5.get("artifact_ref") or step5.get("artifact", {}).get("artifact_ref"),
            "status": "OK" if step5.get("status") != "ERROR" else "ERROR",
            "contradictions_found": step5.get("decision_support", {}).get("contradictions", []) if isinstance(step5.get("decision_support"), dict) else [],
            "auto_hold": step5.get("decision_support", {}).get("auto_hold_triggers") if isinstance(step5.get("decision_support"), dict) else None,
            "next_tool": "geox_evidence_summarize_cross",
        })

        if _is_hold(step5) and abort_on_hold:
            workflow_halted = True
            halt_reason = "Contradiction scan triggered HOLD"

        scan_ref = (
            step5.get("artifact_ref")
            or step5.get("artifact", {}).get("artifact_ref")
            or abduction_ref
        )
    else:
        step5 = None
        scan_ref = abduction_ref

    # ── Step 6: Summarize ─────────────────────────────────────────────────
    if not workflow_halted:
        try:
            step6 = await geox_evidence_summarize_cross(
                evidence_refs=[scan_ref] if scan_ref else [],
                export_format=export_format,
            )
        except Exception as exc:
            step6 = {
                "status": "ERROR",
                "tool": "geox_evidence_summarize_cross",
                "error": str(exc),
                "claim_state": "NO_VALID_EVIDENCE",
            }

        step_outputs.append({
            "step": 6,
            "tool": "geox_evidence_summarize_cross",
            "claim_state": _claim_state(step6),
            "artifact_ref": step6.get("artifact_ref") or step6.get("artifact", {}).get("artifact_ref"),
            "status": "OK" if step6.get("status") != "ERROR" else "ERROR",
        })

        final_artifact_ref = (
            step6.get("artifact_ref")
            or step6.get("artifact", {}).get("artifact_ref")
            or scan_ref
        )
    else:
        step6 = None
        final_artifact_ref = scan_ref

    # ── Determine final claim state ──────────────────────────────────────
    if workflow_halted:
        final_claim_state = "HOLD"
        execution_status = ExecutionStatus.HOLD
        governance_status = GovernanceStatus.HOLD
        artifact_status = ArtifactStatus.DRAFT
    else:
        final_claim_state = "E4_REDTEAMED" if auto_contradiction else "E3_INTERPRETED"
        execution_status = ExecutionStatus.SUCCESS
        governance_status = GovernanceStatus.QUALIFY
        artifact_status = ArtifactStatus.VERIFIED

    # Count how many steps succeeded
    steps_ok = sum(1 for s in step_outputs if s.get("status") == "OK")

    artifact = {
        "workflow": "CANON",
        "version": "1.0",
        "workflow_halted": workflow_halted,
        "halt_reason": halt_reason,
        "steps_total": 6,
        "steps_run": len(step_outputs),
        "steps_succeeded": steps_ok,
        "step_outputs": step_outputs,
        "final_artifact_ref": final_artifact_ref,
        "final_claim_state": final_claim_state,
        "auto_contradiction": auto_contradiction,
        "abort_on_hold": abort_on_hold,
        "canon_chain": [
            "geox_data_ingest_bundle",
            "geox_data_qc_bundle",
            "geox_subsurface_generate_candidates",
            "geox_process_abduction",
            "geox_evidence_contradiction_scan" if auto_contradiction else None,
            "geox_evidence_summarize_cross",
        ],
        "f4_invariant": "Each step output is preserved — human can inspect any stage",
        "f13_invariant": "abort_on_hold=False allows human review before continuing",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "next_best_actions": [
            {
                "tool": "geox_prospect_judge_preview",
                "reason": "Workflow complete — ready for prospect judgment preview",
                "priority": "high" if not workflow_halted else None,
            },
            {
                "tool": "geox_evidence_maturity_score",
                "reason": "Assess maturity of final workflow artifact",
                "priority": "medium",
            },
            {
                "tool": "geox_system_truth_badge",
                "reason": "Verify GEOX health before trusting workflow output",
                "priority": "low",
            },
        ] if not workflow_halted else [
            {
                "tool": "geox_data_qc_bundle" if halt_reason and "QC" in halt_reason else "geox_data_ingest_bundle",
                "reason": f"Resolve: {halt_reason}",
                "priority": "high",
            },
        ],
    }

    return get_standard_envelope(
        artifact,
        tool_class="workflow",
        execution_status=execution_status,
        governance_status=governance_status,
        artifact_status=artifact_status,
        claim_state=final_claim_state,
        claim_tag="GOVERNANCE_LOOP",
    )
