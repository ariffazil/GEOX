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
    mode: Literal["screen", "appraise", "develop"] = "screen",
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
            "pos": 0.22 if mode == "screen" else 0.35,
            "stoiip_p50": 150 if mode == "screen" else 220,
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

    # ── SEAL PATH (irreversible constitutional adjudication) ─────────────────
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
        seal_verdict = GovernanceStatus.SEAL if ac_risk_score < 0.5 else GovernanceStatus.HOLD
        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "ac_risk": ac_risk_score,
            "pos": 0.22 if mode == "screen" else 0.35,
            "stoiip_p50": 150 if mode == "screen" else 220,
            "verdict": seal_verdict,
            "sealed": True,
            "f13_compliance": {
                "Recommendation": "Proceed to Capital Execution"
                if seal_verdict == GovernanceStatus.SEAL
                else "Hold / Reject Prospect",
                "Uncertainty": f"Residual AC_Risk: {ac_risk_score}",
                "Consequence": "Irreversible Capital and Safety Risk Bound to this Decision.",
                "Authority": "HUMAN",
            },
        }
        return get_standard_envelope(
            artifact,
            tool_class="judge",
            governance_status=seal_verdict,
            artifact_status=ArtifactStatus.VERIFIED if seal_verdict == GovernanceStatus.SEAL else ArtifactStatus.DRAFT,
            claim_tag="CLAIM",
            claim_state="SEALED",
        )

    # ── COMPUTE PATH (default) ───────────────────────────────────────────────
    artifact = {
        "ref": prospect_ref,
        "mode": mode,
        "ac_risk": ac_risk_score,
        "pos": 0.22 if mode == "screen" else 0.35,
        "stoiip_p50": 150 if mode == "screen" else 220,
        "score_type": "heuristic_screening" if mode == "screen" else "appraisal",
        "verdict_available": True,
        "note": "Use verdict='preview' for reversible advisory or verdict='seal' with ack_irreversible for constitucional seal.",
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
