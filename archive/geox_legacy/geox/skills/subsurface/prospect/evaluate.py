"""
MCP tool: geox_prospect_evaluate — v2
DITEMPA BUKAN DIBERI

Spec applied:
  - geology_summary: structure, reservoir, charge, seal summary
  - ambiguity_summary: key unknowns and their impact
  - governance_flags: F1-F13 enforcement state
  - hold_status: 888_HOLD conditions
  - human_decision_point: where sovereign approval required
  - ac_risk_score: TEARFRAME composite score (ΔS, Ω₀, κᵣ, Ψ)
  - claim_state: OBSERVED/COMPUTED/HYPOTHESIS/VOID
  - evidence_chain_complete: boolean

geox_prospect_evaluate combines:
  - basin charge timing (geox_time4d_verify_timing)
  - probabilistic volumetrics (geox_compute_volume_probabilistic)
  - TEARFRAME ac_risk scoring
  - 888 HOLD logic
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from geox.core.ac_risk import TEARFRAME
from geox.core.basin_charge import BasinChargeSimulator
from geox.core.volumetrics import ProbabilisticVolumetrics
from geox.core.governed_output import classify_claim_tag, make_vault_receipt


def _make_receipt(tool: str, payload: dict, verdict: str) -> dict:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{tool}:{canonical}".encode("utf-8")).hexdigest()
    return {
        "vault": "VAULT999",
        "tool": tool,
        "verdict": verdict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": digest[:16],
    }


def geox_prospect_evaluate(
    prospect_name: str,
    # Basin charge
    burial_history: list[dict],
    trap_age_ma: float,
    carrier_permeability_md: float,
    buoyancy_pressure_mpa: float,
    seal_capacity_mpa: float,
    fault_density: float = 0.1,
    # Volumetrics
    grv_dist: float | dict | None = None,
    ntg_dist: float | dict | None = None,
    phi_dist: float | dict | None = None,
    sw_dist: float | dict | None = None,
    fvf_dist: float | dict | None = None,
    # TEARFRAME overrides
    u_ambiguity: float | None = None,
    echo_score: float | None = None,
    evidence_credit: float | None = None,
    truth_score: float | None = None,
    # Execution
    execute_888: bool = False,
) -> dict:
    """
    Governed prospect evaluation — v2 full spec.

    Args:
        prospect_name: identifier
        burial_history: [{age_ma, temperature_c, duration_ma}, ...]
        trap_age_ma: trap formation age (Ma)
        carrier_permeability_md: migration pathway permeability (mD)
        buoyancy_pressure_mpa: buoyancy pressure (MPa)
        seal_capacity_mpa: seal capacity (MPa)
        fault_density: 0.0-1.0
        grv_dist, ntg_dist, phi_dist, sw_dist, fvf_dist: volumetrics inputs
        u_ambiguity: override TEARFRAME ambiguity score (0.0-1.0)
        echo_score: override TEARFRAME echo score (0.0-1.0)
        evidence_credit: override TEARFRAME evidence credit (0.0-1.0)
        truth_score: override TEARFRAME truth score (0.0-1.0)
        execute_888: if True, skip 888 HOLD (for automation); else enforce hold

    Returns:
        Full governed prospect evaluation with:
        - verdict: SEAL | QUALIFY | HOLD | VOID
        - geology_summary
        - ambiguity_summary
        - governance_flags
        - hold_status
        - human_decision_point
        - ac_risk_score (TEARFRAME)
        - claim_state
        - evidence_chain_complete
        - vault_receipt
    """
    verdict = "HOLD"
    claim_state = "UNKNOWN"
    hold_status = "CLEAN"
    governance_flags: dict[str, Any] = {}
    human_decision_point = ""
    evidence_chain_complete = False

    # ── Stage 1: Basin charge timing ──────────────────────────────
    bc_sim = BasinChargeSimulator()
    timing = bc_sim.verify_timing(
        burial_history=burial_history,
        trap_age_ma=trap_age_ma,
        carrier_permeability_md=carrier_permeability_md,
        buoyancy_pressure_mpa=buoyancy_pressure_mpa,
        seal_capacity_mpa=seal_capacity_mpa,
        fault_density=fault_density,
    )
    timing_dict = timing.to_dict()

    # ── Stage 2: Volumetrics (optional — pass None to skip) ───────
    volume_result: dict = {}
    if all(v is not None for v in [grv_dist, ntg_dist, phi_dist, sw_dist, fvf_dist]):
        try:
            vol = ProbabilisticVolumetrics(draws=10_000, seed=42).compute_hcpv(
                grv_dist=grv_dist,
                ntg_dist=ntg_dist,
                phi_dist=phi_dist,
                sw_dist=sw_dist,
                fvf_dist=fvf_dist,
            )
            volume_result = vol.to_dict()
            evidence_chain_complete = True
        except Exception as e:
            volume_result = {"error": str(e)}
    else:
        volume_result = {"skipped": "one or more distributions not provided"}

    # ── Stage 3: TEARFRAME AC risk score ─────────────────────────
    tf = TEARFRAME(
        u_ambiguity=u_ambiguity if u_ambiguity is not None else 0.5,
        echo_score=echo_score if echo_score is not None else 0.5,
        evidence_credit=evidence_credit if evidence_credit is not None else 0.5,
        truth_score=truth_score if truth_score is not None else 0.5,
    )

    # Merge volumetrics and timing into TEARFRAME
    risk_input = tf.to_dict()
    if volume_result and "p50" in volume_result:
        risk_input["hcpv_median"] = volume_result["p50"]
    if timing_dict.get("charge_probability"):
        risk_input["charge_probability"] = timing_dict["charge_probability"]

    # Compute composite AC risk score from TEARFRAME fields
    b_cog = tf.u_ambiguity * 0.7 + (1 - tf.evidence_credit) * 0.3
    raw_ac_risk = b_cog * (1 - tf.truth_score) * (1 + tf.echo_score * 0.5)
    ac_risk_score = max(0.0, min(1.0, raw_ac_risk))

    if ac_risk_score < 0.15:
        risk_verdict = "SEAL"
    elif ac_risk_score < 0.75:
        risk_verdict = "HOLD"
    else:
        risk_verdict = "VOID"

    # ── Stage 4: Governed verdict assembly ────────────────────────

    # Build geology summary
    geology_summary = {
        "structure": {
            "trap_age_ma": trap_age_ma,
            "fault_density": fault_density,
        },
        "reservoir": volume_result.get("p50") is not None,
        "charge": {
            "verdict": timing_dict.get("verdict"),
            "charge_age_ma": timing_dict.get("charge_age_ma"),
            "charge_probability": timing_dict.get("charge_probability", 0.0),
            "migration_window_my": timing_dict.get("migration_window_my"),
        },
        "seal": {
            "buoyancy_pressure_mpa": buoyancy_pressure_mpa,
            "seal_capacity_mpa": seal_capacity_mpa,
            "seal_integrity_estimate": timing_dict.get("basin_charge_result", {}).get("seal_integrity_estimate", 0.0),
        },
    }

    # Build ambiguity summary
    ambiguity_summary: list[str] = []
    if timing_dict.get("verdict") in ("improbable", "void"):
        ambiguity_summary.append("Charge timing is improbable or void")
    if volume_result.get("skipped"):
        ambiguity_summary.append("Volumetrics not run — evidence chain incomplete")
    if timing_dict.get("reversal_conditions"):
        ambiguity_summary.append(f"Reversal conditions: {timing_dict['reversal_conditions']}")

    # Build governance flags
    governance_flags = {
        "F1_human_sovereign": True,   # always sovereign
        "F3_tri_witness": True,        # vault_receipt present on both tools
        "F7_no_speculation": timing_dict.get("verdict") != "void",
        "F13_irreversible": False,     # prospect eval is read-only
        "timing_hold": timing_dict.get("verdict") in ("improbable", "void"),
        "volume_hold": volume_result.get("hold_enforced", False),
        "risk_verdict": risk_verdict,
        "ac_risk_score": round(ac_risk_score, 4),
        "Delta_S": tf.Delta_S,
        "Omega_0": tf.Omega_0,
        "Kappa_r": tf.Kappa_r,
        "Psi": tf.Psi_field,
    }

    # 888 HOLD logic
    hold_triggers: list[str] = []
    if timing_dict.get("verdict") in ("improbable", "void"):
        hold_triggers.append("timing_improbable_or_void")
    if volume_result.get("hold_enforced"):
        hold_triggers.append("volume_physics_guard_hold")
    if ac_risk_score > 0.7:
        hold_triggers.append(f"high_risk_score_{round(ac_risk_score,2)}")
    if not evidence_chain_complete:
        hold_triggers.append("evidence_chain_incomplete")

    if hold_triggers:
        hold_status = f"888_HOLD: {', '.join(hold_triggers)}"
        verdict = "HOLD"
        claim_state = "HYPOTHESIS"
        human_decision_point = (
            f"888_HOLD active on prospect {prospect_name}. "
            f"Triggers: {hold_triggers}. "
            f"Do not proceed to drilling decision without sovereign review. "
            f"Refer to reversibility doctrine before any irreversible action."
        )
    else:
        hold_status = "CLEAN"
        verdict = "SEAL"
        claim_state = "COMPUTED"
        human_decision_point = (
            f"Prospect {prospect_name} evaluated. Verdict SEAL. "
            f"Claim state COMPUTED. "
            f"Composite risk score {round(ac_risk_score,4)}. "
            f"Proceed to next workflow stage."
        )

    # Build evidence chain
    evidence_chain = {
        "timing_result": timing_dict.get("verdict"),
        "charge_probability": timing_dict.get("charge_probability", 0.0),
        "volumetrics_run": evidence_chain_complete,
        "hcpv_p50": volume_result.get("p50"),
        "hcpv_p10": volume_result.get("p10"),
        "hcpv_p90": volume_result.get("p90"),
        "ac_risk_score": round(ac_risk_score, 4),
        "Delta_S": tf.Delta_S,
        "Omega_0": tf.Omega_0,
        "Kappa_r": tf.Kappa_r,
        "Psi": tf.Psi_field,
        "seal_integrity": timing_dict.get("basin_charge_result", {}).get("seal_integrity_estimate", 0.0),
        "claim_state": claim_state,
        "verdict": verdict,
    }

    payload = {
        "prospect_name": prospect_name,
        "verdict": verdict,
        "claim_state": claim_state,
        "ac_risk_score": round(ac_risk_score, 4),
    }

    return {
        "tool": "geox_prospect_evaluate",
        "prospect_name": prospect_name,
        "verdict": verdict,
        "claim_state": claim_state,
        "geology_summary": geology_summary,
        "ambiguity_summary": ambiguity_summary,
        "governance_flags": governance_flags,
        "hold_status": hold_status,
        "human_decision_point": human_decision_point,
        "ac_risk_score": round(ac_risk_score, 4),
        "tearframe_state": {
            "Delta_S": tf.Delta_S,
            "Peace2": tf.Peace2,
            "Omega_0": tf.Omega_0,
            "Kappa_r": tf.Kappa_r,
            "Psi": tf.Psi_field,
        },
        "evidence_chain": evidence_chain,
        "evidence_chain_complete": evidence_chain_complete,
        "timing_result": timing_dict,
        "volume_result": volume_result,
        "limitations": timing_dict.get("limitations", []) + ([] if evidence_chain_complete else ["volumetrics not computed"]),
        "vault_receipt": _make_receipt("geox_prospect_evaluate", payload, verdict),
    }
