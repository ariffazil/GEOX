from __future__ import annotations

import logging
from typing import Any, Literal

from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    get_standard_envelope,
)

logger = logging.getLogger("geox.canonical.prospect")


async def geox_prospect_evaluate(
    prospect_ref: str,
    mode: Literal["screen", "appraise", "develop", "decompose", "trajectory"] = "screen",
    evidence_refs: list[str] | None = None,
    verdict: Literal["compute", "preview", "seal"] = "compute",
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
    # ── Eureka 8 (2026-06-03): optional StructuralMap as derived input ────
    structural_map_inline: dict[str, Any] | None = None,
    # ── Eureka 11 (2026-06-03): optional statistical-power params ──────────
    # When provided, runs saf_stats.stat_power to solve for missing n
    # or power. Critical for survey design: "how many wells do I need to
    # confirm a play with effect size f and target power 0.8?"
    # Required keys: test (t/f/chi2/z), effect_size, alpha. Provide
    # exactly one of: power (to solve for n) or nobs (to solve for power).
    # For test=f, also set df_num (k-1).
    power_params: dict[str, Any] | None = None,
) -> dict:
    """Integrated prospect evaluation (Volumetrics, POS, EVOI) with optional preview/seal.

    Replaces: geox_prospect_evaluate + geox_prospect_judge_preview + geox_prospect_judge_seal.

    Args:
        prospect_ref: Prospect artifact reference.
        mode: Evaluation mode.
            - "screen": Qualitative/heuristic screening (default). No evidence required.
            - "appraise": Requires QC_VERIFIED evidence_refs (DST, PVT, seismic, etc.).
            - "develop": Requires full evidence package + prior appraisal.
        evidence_refs: List of artifact refs that have passed QC. Required for appraise/develop.
        verdict: "compute" (default) | "preview" (reversible advisory) | "seal" (irreversible).
        ack_irreversible: Required when verdict="seal". F1 Amanah gate.
        judge_pin: Optional constant-time PIN for seal authorization.
        structural_map_inline: E8 — optional inline StructuralMap (output of
                               bootstrap_structure). When provided, the prospect
                               evaluation carries the structural position as
                               additional evidence (Vp-mean, structural-height
                               at the prospect location, etc.).
    """
    # Hardening: validate free-text inputs at boundary.
    from geox_mcp.tools.kernel._validation import validate_tool_inputs

    _err = validate_tool_inputs(
        "geox_prospect_evaluate",
        prospect_ref=prospect_ref,
        evidence_refs=evidence_refs,
        judge_pin=judge_pin,
    )
    if _err is not None:
        return _err
    refs = evidence_refs or []

    # ── NEW MODES (F13-ratified 2026-09-20): chance-factor decomposition + maturation curve
    # These modes do NOT require evidence_refs — they are pure POS mathematics.
    # Inserted before the existing mode dispatch so they short-circuit cleanly.
    # No mutation, no seal, no judgement — just math.
    if mode == "decompose":
        # Extract chance factors from kwargs that may be passed via power_params
        # (since Literal doesn't allow custom keys) or via a dedicated factors dict.
        # For simplicity, we accept them via a single dict in power_params["factors"]
        # OR via dedicated params structural_map_inline["chance_factors"].
        # Cleanest path: structural_map_inline carries the chance factors.
        factors = {}
        if structural_map_inline and isinstance(structural_map_inline, dict):
            factors = structural_map_inline.get("chance_factors", {}) or {}
        if not factors and power_params and isinstance(power_params, dict):
            factors = power_params.get("chance_factors", {}) or {}
        artifact = pos_decompose(
            source=factors.get("source", 1.0),
            migration=factors.get("migration", 1.0),
            reservoir=factors.get("reservoir", 1.0),
            trap=factors.get("trap", 1.0),
            seal=factors.get("seal", 1.0),
        )
        artifact["tool"] = "geox_prospect_evaluate"
        artifact["mode"] = "decompose"
        artifact["prospect_ref"] = prospect_ref
        artifact["note"] = (
            "Rose 2001 chance-factor decomposition. POS = source × migration × reservoir × trap × seal. "
            "Independence assumption: factors do not compensate. "
            "Risk drivers returned as the lowest-2 factors (where uncertainty lives)."
        )
        return get_standard_envelope(
            artifact,
            tool_class="compute",
            governance_status=GovernanceStatus.QUALIFY,
            artifact_status=ArtifactStatus.VERIFIED,
            claim_tag="DERIVED",
            claim_state="COMPUTED",
        )

    if mode == "trajectory":
        # Maturation params via structural_map_inline["maturation_params"]
        mparams = {}
        if structural_map_inline and isinstance(structural_map_inline, dict):
            mparams = structural_map_inline.get("maturation_params", {}) or {}
        artifact = pos_trajectory(
            po_prior=mparams.get("po_prior", 0.95),
            po_asymptote=mparams.get("po_asymptote", 0.70),
            po_decay_rate=mparams.get("po_decay_rate", 5.0),
            ps_max=mparams.get("ps_max", 0.85),
            ps_growth_rate=mparams.get("ps_growth_rate", 6.0),
        )
        artifact["tool"] = "geox_prospect_evaluate"
        artifact["mode"] = "trajectory"
        artifact["prospect_ref"] = prospect_ref
        artifact["note"] = (
            "Rose 2001 bullhorn curve: Po(t) × Ps(t) over execution maturity axis. "
            "Po decays sigmoidally (advertised → residual after wells). "
            "Ps grows logistically (no prospects at frontier → ceiling after delineation). "
            "Combined G(t) = Po × Ps. Frontier scalar POS hides the trajectory."
        )
        return get_standard_envelope(
            artifact,
            tool_class="compute",
            governance_status=GovernanceStatus.QUALIFY,
            artifact_status=ArtifactStatus.VERIFIED,
            claim_tag="DERIVED",
            claim_state="COMPUTED",
        )

    if mode in ("appraise", "develop") and not refs:
        # Agentic recovery (Fix #1, #5 - Arif 2026-05-16)
        # RECOVERABLE_ERROR: failure has an exit path — downgrade or evidence workflow
        return get_standard_envelope(
            {
                "tool": "geox_prospect_evaluate",
                "error_code": "NO_VALID_EVIDENCE",
                "message": f"mode='{mode}' requires evidence_refs. Provide ingested + QC-verified artifacts.",
                "required_evidence": [
                    "DST table",
                    "pressure buildup",
                    "PVT / gas composition",
                    "structure map",
                    "seismic interpretation",
                    "contacts",
                    "net pay / petrophysics",
                ],
                # Downgrade path: allow screen mode without evidence
                "downgrade_available": True,
                "downgrade_mode": "screen",
                "downgrade_note": "Use mode='screen' for qualitative screening without evidence. Results will be HYPOTHESIS-level.",
            },
            tool_class="compute",
            execution_status=ExecutionStatus.RECOVERABLE_ERROR,  # Changed from ERROR
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[],
            # Agentic recovery fields (Fix #1, #4 - Arif 2026-05-16)
            next_best_actions=[
                {
                    "mode": "downgrade",
                    "action": "Use screen mode for qualitative screening without evidence",
                    "tool_hint": "geox.prospect_evaluate",
                    "parameters": {"mode": "screen"},
                    "rank": 0,
                },
                {
                    "mode": "evidence_request",
                    "action": "Ingest DST, PVT, seismic data to unlock appraise/develop modes",
                    "tool_hint": "geox.data.ingest",
                    "evidence_required": [
                        "DST table",
                        "PVT / gas composition",
                        "seismic interpretation",
                    ],
                    "rank": 1,
                },
                {
                    "mode": "evidence_request",
                    "action": "QC verify ingested artifacts before appraisal",
                    "tool_hint": "geox.data.qc",
                    "rank": 2,
                },
            ],
            suggested_tool="geox.data.ingest",
            can_auto_retry=True,
            # Structured missing inputs (Fix #8 - Arif 2026-05-16)
            missing_inputs_schema=[
                {
                    "name": "evidence_refs",
                    "type": "string[]",
                    "acceptable_sources": ["QC_VERIFIED_LAS", "QC_VERIFIED_DST", "QC_VERIFIED_SEISMIC", "QC_VERIFIED_PVT"],
                    "unlock_stage": "appraisal",
                    "description": "QC-verified artifacts required for appraise/develop modes",
                }
            ],
            # Confidence policy (Fix #9 - Arif 2026-05-16)
            confidence_policy={
                "confidence_band": "not_computed",
                "reason": "No QC-verified evidence_refs supplied for appraisal",
                "allowed_claims": ["qualitative screening", "hypothesis framing"],
                "disallowed_claims": ["POS", "STOIIP", "P10/P50/P90", "commercial decision", "prospect ranking"],
            },
        )

    if mode == "screen" and not refs:
        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "pos": None,
            "stoiip_p50": None,
            "score_type": "heuristic_screening",
            "note": "No evidence supplied — screening is qualitative only.",
        }

        # EUREKA FORGE (2026-06-03): prospect survey design via stat_power.
        # Lives in the screen-mode path so the power query works without
        # needing full evidence. When power_params is provided, solves
        # for missing n or power and embeds the result in the artifact.
        if power_params and isinstance(power_params, dict):
            try:
                import math as _math_pw_sm
                import warnings as _w_pw_sm

                _w_pw_sm.filterwarnings("ignore")
                from statsmodels.stats.power import (
                    FTestAnovaPower,
                    GofChisquarePower,
                    NormalIndPower,
                    TTestIndPower,
                )

                _test_sm = str(power_params.get("test", "f")).lower()
                _alpha_sm = float(power_params.get("alpha", 0.05))
                _effect_sm = float(power_params.get("effect_size", 0.25))
                _power_in_sm = power_params.get("power")
                _nobs_in_sm = power_params.get("nobs")
                _df_num_sm = power_params.get("df_num")
                _out_sm: dict[str, Any] = {
                    "test": _test_sm,
                    "alpha": _alpha_sm,
                    "effect_size": _effect_sm,
                }
                if _test_sm == "f":
                    _k_sm = (int(_df_num_sm) + 1) if _df_num_sm is not None else 3
                    _ana_sm = FTestAnovaPower()
                    _out_sm["k_groups"] = _k_sm
                    if _nobs_in_sm is not None:
                        _df_den_sm = max(1, int(_nobs_in_sm) - _k_sm)
                        _out_sm["solved_power"] = float(
                            _ana_sm.solve_power(
                                effect_size=_effect_sm,
                                alpha=_alpha_sm,
                                k_groups=_k_sm,
                                nobs=int(_nobs_in_sm),
                                power=None,
                            )
                        )
                        _out_sm["solved_nobs"] = int(_nobs_in_sm)
                        _out_sm["df_den"] = _df_den_sm
                    elif _power_in_sm is not None:
                        _out_sm["solved_nobs"] = int(
                            _math_pw_sm.ceil(
                                _ana_sm.solve_power(
                                    effect_size=_effect_sm,
                                    alpha=_alpha_sm,
                                    k_groups=_k_sm,
                                    power=float(_power_in_sm),
                                )
                            )
                        )
                    else:
                        _out_sm["error"] = "supply exactly one of power or nobs"
                elif _test_sm == "t":
                    _ana_sm = TTestIndPower()
                    if _nobs_in_sm is not None:
                        _out_sm["solved_power"] = float(
                            _ana_sm.solve_power(
                                effect_size=_effect_sm,
                                alpha=_alpha_sm,
                                nobs1=int(_nobs_in_sm),
                            )
                        )
                        _out_sm["solved_nobs"] = int(_nobs_in_sm)
                    elif _power_in_sm is not None:
                        _out_sm["solved_nobs"] = int(
                            _math_pw_sm.ceil(
                                _ana_sm.solve_power(
                                    effect_size=_effect_sm,
                                    alpha=_alpha_sm,
                                    power=float(_power_in_sm),
                                )
                            )
                        )
                    else:
                        _out_sm["error"] = "supply exactly one of power or nobs"
                elif _test_sm == "chi2":
                    _ana_sm = GofChisquarePower()
                    if _nobs_in_sm is not None:
                        _out_sm["solved_power"] = float(
                            _ana_sm.solve_power(
                                effect_size=_effect_sm,
                                alpha=_alpha_sm,
                                nobs=int(_nobs_in_sm),
                            )
                        )
                        _out_sm["solved_nobs"] = int(_nobs_in_sm)
                    elif _power_in_sm is not None:
                        _out_sm["solved_nobs"] = int(
                            _math_pw_sm.ceil(
                                _ana_sm.solve_power(
                                    effect_size=_effect_sm,
                                    alpha=_alpha_sm,
                                    power=float(_power_in_sm),
                                )
                            )
                        )
                    else:
                        _out_sm["error"] = "supply exactly one of power or nobs"
                elif _test_sm == "z":
                    _ana_sm = NormalIndPower()
                    if _nobs_in_sm is not None:
                        _out_sm["solved_power"] = float(
                            _ana_sm.solve_power(
                                effect_size=_effect_sm,
                                alpha=_alpha_sm,
                                nobs1=int(_nobs_in_sm),
                            )
                        )
                        _out_sm["solved_nobs"] = int(_nobs_in_sm)
                    elif _power_in_sm is not None:
                        _out_sm["solved_nobs"] = int(
                            _math_pw_sm.ceil(
                                _ana_sm.solve_power(
                                    effect_size=_effect_sm,
                                    alpha=_alpha_sm,
                                    power=float(_power_in_sm),
                                )
                            )
                        )
                    else:
                        _out_sm["error"] = "supply exactly one of power or nobs"
                else:
                    _out_sm["error"] = f"unsupported test '{_test_sm}'"
                artifact["_saf_power"] = _out_sm
            except Exception as _pw_exc_sm:
                artifact["_saf_power"] = {"embed_skipped": str(_pw_exc_sm)[:120]}

        return get_standard_envelope(
            artifact,
            tool_class="compute",
            claim_tag="HYPOTHESIS",
            claim_state="INTERPRETED",
            uncertainty="High",
            humility_score=0.5,
            evidence_refs=[],
            # Confidence policy for screen mode (Fix #9 - Arif 2026-05-16)
            confidence_policy={
                "confidence_band": "qualitative",
                "reason": "Screen mode — no quantitative evidence available",
                "allowed_claims": ["qualitative screening", "relative ranking", "hypothesis framing"],
                "disallowed_claims": ["POS", "STOIIP", "P10/P50/P90", "comercial decision"],
            },
            # Agentic: screen mode is the safe downgrade
            suggested_tool=None,
            can_auto_retry=True,
        )

    # Compute AC risk score from evidence quality
    ac_risk_score = 0.22
    if mode == "screen" and not refs:
        ac_risk_score = 0.65
    elif mode == "appraise" and refs:
        ac_risk_score = 0.35
    elif mode == "develop" and refs:
        ac_risk_score = 0.18

    # ── PREVIEW PATH (reversible advisory) ───────────────────────────────────
    if verdict == "preview":
        preview_verdict = GovernanceStatus.SEAL if ac_risk_score < 0.5 else GovernanceStatus.HOLD
        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "ac_risk": ac_risk_score,
            # NOTE: screen-mode default heuristic, NOT a real POS. Flagged so the
            # reversible-advisory consumer does not mistake it for decomposed POS.
            # (555-ASI verify 2026-09-20 found this path missing the flag.)
            "pos": 0.22 if mode == "screen" else 0.35,
            "pos_default_heuristic": True,
            "stoiip_p50": 150 if mode == "screen" else 220,
            "stoiip_p50_default_heuristic": True,
            "preview_verdict": preview_verdict,
            "reversible": True,
            "note": "This is a preview only. Call verdict='seal' with ack_irreversible=True to make irreversible.",
            "f13_compliance": {
                "Recommendation": "Proceed" if preview_verdict == GovernanceStatus.SEAL else "Hold / Rework",
                "Uncertainty": f"AC_Risk Score: {ac_risk_score}",
                "Consequence": "Preview Mode - No physical capital committed.",
                "Authority": "HUMAN",
            },
        }
        return get_standard_envelope(
            artifact,
            tool_class="judge",
            governance_status=GovernanceStatus.QUALIFY,
            artifact_status=ArtifactStatus.DRAFT,
            claim_tag="PLAUSIBLE",
            claim_state="JUDGE_PREVIEW",
        )

    # ── SEAL PATH (2026-09-17 jurisdiction fix — 333-AGI / JURISDICTION-001) ──
    # BEFORE: GEOX minted constitutional verdicts locally
    #   (GovernanceStatus.SEAL if ac_risk_score < 0.5) — domain competence
    #   impersonating sovereign authority. VIOLATES:
    #   Expertise(D) ⇏ Authority(D).
    # AFTER: the PIN + ack_irreversible gates remain (defense in depth), but
    #   the verdict itself is delegated to arifOS 888 via the existing
    #   arifos_governance integration. GEOX outputs a DOMAIN verdict with
    #   recommended_handoff; only arifOS can produce AUTHORIZED_TO_ACT.
    if verdict == "seal":
        import hmac
        import os

        _expected_pin = os.environ.get("GEOX_JUDGE_PIN", "")
        if _expected_pin:
            if not judge_pin or not hmac.compare_digest(str(judge_pin), _expected_pin):
                return get_standard_envelope(
                    {
                        "tool": "geox_prospect_evaluate",
                        "error_code": "F11_AUTH_FAILED",
                        "message": "F11 AUTH: Invalid or missing judge_pin. Constant-time check failed.",
                        "guard": "F11",
                        "floor": "F11_AUTH",
                    },
                    tool_class="judge",
                    execution_status=ExecutionStatus.ERROR,
                    governance_status=GovernanceStatus.HOLD,
                    claim_tag="HYPOTHESIS",
                )
        if not ack_irreversible:
            return get_standard_envelope(
                {
                    "tool": "geox_prospect_evaluate",
                    "error_code": "RT3_GUARD_F1_AMANAH",
                    "message": (
                        "verdict='seal' is a constitutional adjudication (irreversible). "
                        "F1 Amanah requires ack_irreversible=True. "
                        "Provide ack_irreversible=True in the tool call to proceed."
                    ),
                    "guard": "RT3",
                    "floor": "F1_AMANAH",
                },
                tool_class="judge",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                claim_tag="HYPOTHESIS",
            )

        # DOMAIN verdict — GEOX's competence ends at physical evidence.
        domain_verdict = "PHYSICALLY_SUPPORTED" if ac_risk_score < 0.5 else "HYPOTHESIS"

        # Delegate constitutional adjudication to arifOS 888 (graceful
        # degradation: HOLD if judge unreachable — never self-adjudicate).
        try:
            from geox_core.integrations.arifos_governance import (
                build_governed_payload,
                call_judge,
            )
            from geox_core.integrations.arifos_governance import IrreversibilityLevel

            governed = build_governed_payload(
                tool_name="geox_prospect_evaluate[seal]",
                intent=f"Constitutional adjudication of prospect {prospect_ref} "
                f"(GEOX domain verdict: {domain_verdict}, ac_risk={ac_risk_score})",
                parameters={"prospect_ref": prospect_ref, "ac_risk_score": ac_risk_score, "mode": mode},
                evidence_refs=refs,
                uncertainty={"ac_risk_score": ac_risk_score, "confidence": "domain"},
                irreversibility=IrreversibilityLevel.STRUCTURAL,
            )
            judge_result = await call_judge(governed)
            arifos_verdict = str(judge_result.get("verdict", "HOLD")).upper()
            constitutional = {
                "adjudicated_by": "arifOS",
                "verdict_class": "CONSTITUTIONAL",
                "verdict": arifos_verdict,
                "judge_state_hash": judge_result.get("judge_state_hash"),
                "delegation": "JURISDICTION-001: domain organs never self-adjudicate",
            }
        except Exception as exc:  # judge unreachable → HOLD, never mint SEAL locally
            constitutional = {
                "adjudicated_by": "arifOS",
                "verdict_class": "CONSTITUTIONAL",
                "verdict": "HOLD",
                "delegation": "JURISDICTION-001: arifOS judge unreachable — graceful HOLD",
                "delegation_error": str(exc)[:200],
            }

        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "ac_risk": ac_risk_score,
            # NOTE (F13-ratified 2026-09-20): the 0.22/0.35 placeholder values are
            # a *screen-mode default heuristic*, NOT a real POS. For a real POS,
            # call mode="decompose" with chance factors. Same default is used in
            # the compute path below for backward compatibility.
            "pos": 0.22 if mode == "screen" else 0.35,
            "pos_default_heuristic": True,
            "stoiip_p50": 150 if mode == "screen" else 220,
            "stoiip_p50_default_heuristic": True,
            "domain_verdict": domain_verdict,
            "verdict_class": "DOMAIN",
            "recommended_handoff": "arifOS (888 judge)",
            "awaiting_verification": True,
            "sealed": False,
            "constitutional": constitutional,
        }
        return get_standard_envelope(
            artifact,
            tool_class="judge",
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.DRAFT,
            claim_tag="CLAIM",
            claim_state="JUDGE_PENDING",
        )

    # ── COMPUTE PATH (default) ───────────────────────────────────────────────
    artifact = {
        "ref": prospect_ref,
        "mode": mode,
        "ac_risk": ac_risk_score,
        # NOTE (F13-ratified 2026-09-20): the 0.22/0.35 values are a *screen-mode
        # default heuristic*, NOT a real POS. For real POS use mode="decompose".
        "pos": 0.22 if mode == "screen" else 0.35,
        "pos_default_heuristic": True,
        "stoiip_p50": 150 if mode == "screen" else 220,
        "stoiip_p50_default_heuristic": True,
        "score_type": "heuristic_screening" if mode == "screen" else "appraisal",
        "verdict_available": True,
        "note": "Use verdict='preview' for reversible advisory or verdict='seal' with ack_irreversible for constitucional seal. For real POS use mode='decompose' with chance factors.",
    }

    # ── EUREKA 2026-06-05 (Burlamaque Step 4): stratum-confidence ribbon ──
    # Make hidden class imbalance per stratum visible on every prospect eval.
    # Honors the article's lesson: aggregate metrics hide which sub-domain
    # the data is actually strong in.
    artifact["stratum_breakdown"] = _compute_stratum_breakdown(
        mode=mode,
        evidence_refs=refs,
        prospect_ref=prospect_ref,
    )

    # ── Eureka 2026-06-10: Migration shadow + POS ceiling (Zahid Zamanshah, 2026) ──
    # Migration is buoyancy-driven, up-dip along individual carrier beds.
    # Leads in a migration shadow score differently than leads in a fairway.
    # Without carrier-bed refs this is a placeholder — but it must be surfaced
    # so the agent knows what's missing, not silently assumed filled.
    artifact["migration_context"] = {
        "migration_shadow_scored": False,
        "migration_fairway_assumption": "assumed_in_fairway",
        "pos_multiplier_applied": 1.0,
        "shadow_scoring_available": False,
        "upgrade_requires": [
            "carrier_bed_refs (per-layer carrier grid)",
            "structural_dip_map (for buoyancy flow direction)",
            "fill_spill_points (closure spill depth per horizon)",
        ],
        "note": (
            "Per-carrier-bed migration shadow scoring: buoyancy-driven up-dip flowpath "
            "per carrier layer. Leads in a migration shadow should be down-weighted, "
            "not deleted. Provide carrier_bed_refs to unlock scored migration fairway mapping. "
            "Current POS multiplier = 1.0 (fairway assumed — unscored)."
        ),
        "eureka_ref": "MIGRATION_SHADOW_SCORING_2026_06_10",
    }
    # POS ceiling: honest declaration of what QI rung constrains the POS.
    # A screening POS of 0.05 on post-stack is not the same as a calibrated
    # appraisal POS of 0.05 — the ceiling is different.
    _qi_rung_label = "pre-QI-screen" if mode == "screen" else "appraisal"
    artifact["pos_ceiling_declaration"] = {
        "pos_ceiling_basis": _qi_rung_label,
        "fluid_certified": False,
        "fluid_discrimination_note": (
            "No fluid type has been confirmed by prestack QI. Gas, fizz, and CO₂ are "
            "indistinguishable on post-stack data. POS ceiling is constrained by QI rung, "
            "not only by evidence count. A screen-mode POS is a screening probability — "
            "not a certified volumetric risk number."
        ),
        "pos_interpretation": "high-grading probability only — not a certified prospect POS",
        "calibration_status": "UNCALIBRATED",
        "eureka_ref": "POS_CEILING_2026_06_10",
    }

    # EUREKA FORGE (2026-06-03): prospect survey design via stat_power.
    # When the user passes power_params (e.g. for "how many wells do I
    # need to confirm a play with f=0.25 at power=0.8?"), solve for the
    # missing n or power and surface in artifact. Uses statsmodels
    # directly because the federated saf_stats.stat_power wrapper
    # strips the F-test k_groups / df_num params needed for one-way
    # ANOVA power. Embed is best-effort; never break main flow.
    if power_params and isinstance(power_params, dict):
        try:
            import math as _math_pw
            import warnings as _w_pw

            _w_pw.filterwarnings("ignore")
            from statsmodels.stats.power import (
                FTestAnovaPower,
                GofChisquarePower,
                NormalIndPower,
                TTestIndPower,
            )

            _test = str(power_params.get("test", "f")).lower()
            _alpha = float(power_params.get("alpha", 0.05))
            _effect = float(power_params.get("effect_size", 0.25))
            _power_in = power_params.get("power")
            _nobs_in = power_params.get("nobs")
            _df_num = power_params.get("df_num")
            _out: dict[str, Any] = {
                "test": _test,
                "alpha": _alpha,
                "effect_size": _effect,
            }
            if _test == "f":
                _k = (int(_df_num) + 1) if _df_num is not None else 3
                _ana = FTestAnovaPower()
                _out["k_groups"] = _k
                if _nobs_in is not None:
                    _df_den = max(1, int(_nobs_in) - _k)
                    _solved_power = float(
                        _ana.solve_power(
                            effect_size=_effect,
                            alpha=_alpha,
                            k_groups=_k,
                            nobs=None,
                            df_num=int(_df_num) if _df_num is not None else _k - 1,
                            df_den=_df_den,
                            power=None,
                        )
                    )
                    _out["solved_power"] = _solved_power
                    _out["solved_nobs"] = int(_nobs_in)
                    _out["df_den"] = _df_den
                elif _power_in is not None:
                    _solved_n = int(
                        _math_pw.ceil(
                            _ana.solve_power(
                                effect_size=_effect,
                                alpha=_alpha,
                                k_groups=_k,
                                nobs=None,
                                df_num=_k - 1,
                                power=float(_power_in),
                            )
                        )
                    )
                    _out["solved_nobs"] = _solved_n
                else:
                    _out["error"] = "supply exactly one of power or nobs"
            elif _test == "t":
                _ana = TTestIndPower()
                if _nobs_in is not None:
                    _out["solved_power"] = float(_ana.solve_power(effect_size=_effect, alpha=_alpha, nobs1=int(_nobs_in)))
                    _out["solved_nobs"] = int(_nobs_in)
                elif _power_in is not None:
                    _out["solved_nobs"] = int(
                        _math_pw.ceil(
                            _ana.solve_power(
                                effect_size=_effect,
                                alpha=_alpha,
                                power=float(_power_in),
                            )
                        )
                    )
                else:
                    _out["error"] = "supply exactly one of power or nobs"
            elif _test == "chi2":
                _ana = GofChisquarePower()
                if _nobs_in is not None:
                    _out["solved_power"] = float(_ana.solve_power(effect_size=_effect, alpha=_alpha, nobs=int(_nobs_in)))
                    _out["solved_nobs"] = int(_nobs_in)
                elif _power_in is not None:
                    _out["solved_nobs"] = int(
                        _math_pw.ceil(
                            _ana.solve_power(
                                effect_size=_effect,
                                alpha=_alpha,
                                power=float(_power_in),
                            )
                        )
                    )
                else:
                    _out["error"] = "supply exactly one of power or nobs"
            elif _test == "z":
                _ana = NormalIndPower()
                if _nobs_in is not None:
                    _out["solved_power"] = float(_ana.solve_power(effect_size=_effect, alpha=_alpha, nobs1=int(_nobs_in)))
                    _out["solved_nobs"] = int(_nobs_in)
                elif _power_in is not None:
                    _out["solved_nobs"] = int(
                        _math_pw.ceil(
                            _ana.solve_power(
                                effect_size=_effect,
                                alpha=_alpha,
                                power=float(_power_in),
                            )
                        )
                    )
                else:
                    _out["error"] = "supply exactly one of power or nobs"
            else:
                _out["error"] = f"unsupported test '{_test}'"
            artifact["_saf_power"] = _out
        except Exception as _pw_exc:
            artifact["_saf_power"] = {"embed_skipped": str(_pw_exc)[:120]}

    return get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="PLAUSIBLE",
        claim_state="COMPUTED",
        confidence_band={"p10": 80, "p50": 150, "p90": 280},
        humility_score=round((280 - 80) / 150, 4) if 150 else 0.0,
        evidence_refs=refs,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# EUREKA 2026-06-05 — Stratum-Confidence Ribbon (Burlamaque 2026-06-04 Step 4)
# Surface the hidden class imbalance across the three evaluation strata.
# ═══════════════════════════════════════════════════════════════════════════════


def _compute_stratum_breakdown(
    mode: str,
    evidence_refs: list[str],
    prospect_ref: str,
) -> dict[str, Any]:
    """Compute the stratum-confidence ribbon for a prospect evaluation.

    Returns per-stratum (screen/appraise/develop) sample counts, confidence,
    and missing strata, plus a Gini-based balance verdict.
    """
    # Strata are the three evaluation tiers. Each represents a different
    # evidence bar; "balanced" coverage means data exists at each tier.
    strata = {
        "screen": _stratum_screen(evidence_refs, prospect_ref),
        "appraise": _stratum_appraise(evidence_refs),
        "develop": _stratum_develop(evidence_refs),
    }

    # Gini coefficient of sample counts (0 = perfect balance, 1 = monoculture)
    counts = [s["n_samples"] for s in strata.values()]
    gini = _gini_coefficient(counts)

    if gini > 0.7 or any(s["n_samples"] == 0 for s in strata.values()):
        ribbon_verdict = "CRITICAL"
    elif gini > 0.4:
        ribbon_verdict = "UNBALANCED"
    else:
        ribbon_verdict = "BALANCED"

    return {
        "screen": strata["screen"],
        "appraise": strata["appraise"],
        "develop": strata["develop"],
        "balance_gini": round(gini, 4),
        "ribbon_verdict": ribbon_verdict,
        "active_mode": mode,
        "eureka_ref": "BURLAMAQUE_2026_STEP4_STRATUM",
        "note": (
            "Aggregate prospect metrics can hide which evaluation tier your "
            "data actually supports. The ribbon shows effective sample size "
            "per stratum. CRITICAL = at least one stratum is empty; "
            "UNBALANCED = Gini > 0.4; BALANCED = even coverage across tiers."
        ),
    }


def _stratum_screen(evidence_refs: list[str], prospect_ref: str) -> dict[str, Any]:
    """Screen mode: qualitative, no evidence required. Always has >= 1 sample (the prospect)."""
    return {
        "n_samples": max(1, len(evidence_refs) if evidence_refs else 1),
        "confidence": 0.40,  # qualitative-only — low
        "missing_strata": [],
        "evidence_bar": "qualitative heuristic",
    }


def _stratum_appraise(evidence_refs: list[str]) -> dict[str, Any]:
    """Appraise mode: requires QC-verified DST/PVT/seismic. Threshold = 3+."""
    n = len(evidence_refs) if evidence_refs else 0
    if n >= 3:
        confidence = min(0.85, 0.40 + 0.15 * n)
        missing: list[str] = []
    else:
        confidence = 0.20 + 0.10 * n
        missing = [
            "DST table (QC-verified)",
            "PVT / gas composition (QC-verified)",
            "seismic interpretation (QC-verified)",
        ]
    return {
        "n_samples": n,
        "confidence": round(confidence, 3),
        "missing_strata": missing,
        "evidence_bar": "QC-verified DST/PVT/seismic",
    }


def _stratum_develop(evidence_refs: list[str]) -> dict[str, Any]:
    """Develop mode: full evidence package + prior appraisal. Threshold = 5+."""
    n = len(evidence_refs) if evidence_refs else 0
    if n >= 5:
        confidence = min(0.95, 0.50 + 0.10 * (n - 5))
        missing: list[str] = []
    else:
        confidence = 0.10 + 0.05 * n
        missing = [
            "net pay / petrophysics",
            "structure map (depth-converted)",
            "fluid contacts",
            "production analog data",
            "reservoir simulation (history-matched)",
        ]
    return {
        "n_samples": n,
        "confidence": round(confidence, 3),
        "missing_strata": missing,
        "evidence_bar": "full package + prior appraisal",
    }


def _gini_coefficient(values: list[int | float]) -> float:
    """Standard Gini coefficient. 0 = perfect equality, 1 = max inequality."""
    if not values or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cum = 0.0
    for i, v in enumerate(sorted_vals, start=1):
        cum += (2 * i - n - 1) * v
    return cum / (n * sum(sorted_vals))


# ═══════════════════════════════════════════════════════════════════════════════
# POS CHANCE-FACTOR DECOMPOSITION (Rose 2001 — Risk and Reliance in Exploration)
# ═══════════════════════════════════════════════════════════════════════════════
# eureka_ref: GEOX_PROSPECT_DECOMPOSE_2026_09_20
# Doctrine:
#   POS = P(source) × P(migration) × P(reservoir) × P(trap) × P(seal)
#   Each factor ∈ [0, 1]. Independence assumption: factors do not compensate.
#   Honest reporting: surface the LOWEST factors as risk drivers, not the product.
# Reference: Rose, P.R., 2001, "Risk and Reliance in Exploration"
#            AAPG Hedberg Research Conference Proceedings.


def pos_decompose(
    source: float = 1.0,
    migration: float = 1.0,
    reservoir: float = 1.0,
    trap: float = 1.0,
    seal: float = 1.0,
) -> dict:
    """Compute POS via Rose 2001 chance-factor decomposition.

    Returns dict with:
      - pos: scalar product of all factors
      - factors: {factor_name: value} each rounded
      - risk_drivers: top-2 lowest factors (where uncertainty lives)
      - independence_assumption: True (Rose 2001)
    """
    factors_raw = {
        "source": float(source),
        "migration": float(migration),
        "reservoir": float(reservoir),
        "trap": float(trap),
        "seal": float(seal),
    }

    # Validate bounds — factors must be probabilities ∈ [0, 1]
    invalid = {k: v for k, v in factors_raw.items() if not (0.0 <= v <= 1.0)}
    if invalid:
        return {
            "error": "INVALID_FACTOR_BOUNDS",
            "message": "Each chance factor must be in [0, 1]",
            "invalid": invalid,
            "factors_supplied": factors_raw,
        }

    pos = 1.0
    for v in factors_raw.values():
        pos *= v

    # Charge = source × migration (composite). F13-accepted term order:
    # source, migration, reservoir, trap, seal. Charge rides AFTER migration —
    # it never replaces the explicit source/migration factors.
    charge = factors_raw["source"] * factors_raw["migration"]

    # Risk drivers: the 2 LOWEST factors (the ones dragging POS down).
    # This is the key teaching from Rose: scalar POS hides which factor kills it.
    sorted_factors = sorted(factors_raw.items(), key=lambda x: x[1])
    risk_drivers = [{"factor": k, "value": round(v, 3), "delta_to_1": round(1.0 - v, 3)} for k, v in sorted_factors[:2]]

    return {
        "pos": round(pos, 4),
        "factors": {k: round(v, 3) for k, v in factors_raw.items()},
        "charge": round(charge, 3),
        "charge_definition": "source × migration",
        "factor_order": ["source", "migration", "reservoir", "trap", "seal"],
        "risk_drivers": risk_drivers,
        "independence_assumption": True,
        "doctrine_ref": "ROSE_2001_RISK_AND_RELIANCE",
        "eureka_ref": "GEOX_PROSPECT_DECOMPOSE_2026_09_20",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# POS MATURATION TRAJECTORY (Rose 2001 — Bullhorn Diagram)
# ═══════════════════════════════════════════════════════════════════════════════
# eureka_ref: GEOX_PROSPECT_TRAJECTORY_2026_09_20
# Doctrine:
#   The bullhorn is the missing primitive. Scalar POS collapses a trajectory.
#   Po (play chance) decays sigmoidally: high at frontier, asymptotes after wells.
#   Ps (prospect chance) grows logistically: 0 at frontier, ceiling after delineation.
#   Combined G(t) = Po(t) × Ps(t). Peak in mid-maturity is where decision is sharpest.
# Reference: Rose, P.R., 2001, AAPG Hedberg.
#            Binns & Adams, 2003, "Risk, Reliability and Confidence".


def pos_trajectory(
    po_prior: float = 0.95,
    po_asymptote: float = 0.70,
    po_decay_rate: float = 5.0,
    ps_max: float = 0.85,
    ps_growth_rate: float = 6.0,
    maturity_points: int = 11,
) -> dict:
    """Compute Po(t), Ps(t), G(t) = Po×Ps over execution maturity axis ∈ [0, 1].

    Parameters:
      po_prior:       advertised Po at frontier (m=0). Usually high (geological optimism).
      po_asymptote:   residual Po after wells. Lower means wells bit down hard.
      po_decay_rate:  how fast Po bites down. Higher = faster correction.
      ps_max:         ceiling of prospect-specific chance. Typically 0.7-0.9.
      ps_growth_rate: logistic steepness. Higher = faster prospect delineation.
      maturity_points: number of samples on the X axis.

    Returns dict with three curves + peak location.
    """
    import math

    if maturity_points < 2:
        return {
            "error": "INVALID_MATURITY_POINTS",
            "message": "maturity_points must be >= 2",
        }

    maturities = [i / (maturity_points - 1) for i in range(maturity_points)]
    po_curve = []
    ps_curve = []
    combined = []

    for m in maturities:
        # Sigmoidal decay: Po(m) = asymptote + (prior - asymptote) * exp(-decay_rate * m)
        po = po_asymptote + (po_prior - po_asymptote) * math.exp(-po_decay_rate * m)
        # Logistic growth: Ps(m) = max / (1 + exp(-growth_rate * (m - 0.5)))
        ps = ps_max / (1.0 + math.exp(-ps_growth_rate * (m - 0.5)))
        po_curve.append({"m": round(m, 3), "Po": round(po, 4)})
        ps_curve.append({"m": round(m, 3), "Ps": round(ps, 4)})
        combined.append(
            {
                "m": round(m, 3),
                "Po": round(po, 4),
                "Ps": round(ps, 4),
                "G_t": round(po * ps, 4),
            }
        )

    peak_idx = max(range(len(combined)), key=lambda i: combined[i]["G_t"])

    # The maturity where G_t first exceeds 0.5 — proxy for "decision is sharp"
    decision_sharp_idx = next(
        (i for i, c in enumerate(combined) if c["G_t"] >= 0.5),
        None,
    )

    return {
        "parameters": {
            "po_prior": po_prior,
            "po_asymptote": po_asymptote,
            "po_decay_rate": po_decay_rate,
            "ps_max": ps_max,
            "ps_growth_rate": ps_growth_rate,
            "maturity_points": maturity_points,
        },
        "maturation_axis": "maturity ∈ [0, 1] — 0 = frontier (no wells), 1 = fully appraised",
        "po_curve": po_curve,
        "ps_curve": ps_curve,
        "combined": combined,
        "peak": {"m": combined[peak_idx]["m"], "G_t": combined[peak_idx]["G_t"]},
        "decision_sharp_at": (combined[decision_sharp_idx]["m"] if decision_sharp_idx is not None else None),
        "doctrine_ref": "ROSE_2001_BULLHORN",
        "eureka_ref": "GEOX_PROSPECT_TRAJECTORY_2026_09_20",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DEPRECATED: Preview / Seal / Verdict — energy absorbed into geox_prospect_evaluate
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_prospect_judge_preview(
    prospect_ref: str,
    ac_risk_score: float,
) -> dict:
    """[DEPRECATED] Use geox_prospect_evaluate with verdict='preview'."""
    return await geox_prospect_evaluate(
        prospect_ref=prospect_ref,
        mode="screen",
        verdict="preview",
    )


async def geox_prospect_judge_seal(
    prospect_ref: str,
    ac_risk_score: float,
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
) -> dict:
    """[DEPRECATED] Use geox_prospect_evaluate with verdict='seal'."""
    return await geox_prospect_evaluate(
        prospect_ref=prospect_ref,
        mode="screen",
        verdict="seal",
        ack_irreversible=ack_irreversible,
        judge_pin=judge_pin,
    )


async def geox_prospect_judge_verdict(
    prospect_ref: str,
    ac_risk_score: float,
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
) -> dict:
    """[DEPRECATED] Use geox_prospect_evaluate with verdict='seal'."""
    return await geox_prospect_evaluate(
        prospect_ref=prospect_ref,
        mode="screen",
        verdict="seal",
        ack_irreversible=ack_irreversible,
        judge_pin=judge_pin,
    )
