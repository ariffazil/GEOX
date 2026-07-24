"""Build interpretation_bundle from framework gate matrix + optional propose.

preferred_hypothesis is always null from GEOX — human sets acceptance.
Each hypothesis is an INDEPENDENT witness, not a copy-modify derivative.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from geox_mcp.domain.seismic_interpret.models import (
    Calibration,
    EarthConstraints,
    HypothesisModel,
    InterpretationBundle,
    InterpretRequestFlags,
    LimitationsModel,
    ProvenanceModel,
)


def _param_hash(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _style_from_faults(faults: list[dict[str, Any]]) -> str:
    regimes = {str(f.get("regime_prior") or f.get("regime") or "unknown").lower() for f in faults}
    regimes.discard("unknown")
    if not regimes:
        return "unknown"
    if regimes <= {"normal"}:
        return "extensional_normal"
    if regimes & {"reverse", "thrust"}:
        return "contractional"
    if regimes & {"strike_slip", "strike-slip"}:
        return "strike_slip"
    return "mixed"


def _build_hypothesis_from_framework(
    hypothesis_id: str,
    witness_id: str,
    witness_type: str,
    framework: dict[str, Any],
    model_or_method: str = "",
    derivation: str = "",
) -> dict[str, Any]:
    """Build ONE hypothesis, never copy geometry and relabel."""
    faults = list(framework.get("faults") or [])
    horizons = list(framework.get("horizons") or [])
    structural_style = _style_from_faults(faults)
    return {
        "hypothesis_id": hypothesis_id,
        "witness_id": witness_id,
        "witness_type": witness_type,
        "model_or_method": model_or_method,
        "faults": faults,
        "horizons": horizons,
        "structural_style": structural_style,
        "derivation": derivation,
        "kinematic_claims": [],
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "unresolved_measurements": [],
    }


def build_interpretation_bundle(
    *,
    frameworks_or_primary: dict[str, Any] | None = None,
    gate_matrix: dict[str, Any] | None = None,
    observations: dict[str, Any] | None = None,
    calibration: Calibration | dict[str, Any] | None = None,
    earth_constraints: EarthConstraints | dict[str, Any] | None = None,
    request: InterpretRequestFlags | dict[str, Any] | None = None,
    propose_result: dict[str, Any] | None = None,
    model_revision: str = "geox-seismic-interpret-b-final",
    independent_witnesses: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble interpretation_bundle. preferred_hypothesis always None from GEOX.

    W3: never manufacture fake alternatives by mutating one base framework.
    Legitimate hyps: primary geometry, independent_witnesses, classical propose,
    or empty conceptual alternatives that state required measurements.
    """
    from geox_mcp.tools.structure_gates import HYPOTHESIS_STATUS_MAP, run_all_structure_gates

    cal = calibration if isinstance(calibration, dict) else (calibration.model_dump() if calibration else {})
    req = request if isinstance(request, dict) else (request.model_dump() if request else InterpretRequestFlags().model_dump())
    hyp_n = int(req.get("hypothesis_count") or 3)
    ec = earth_constraints if isinstance(earth_constraints, dict) else {}

    primary = dict(frameworks_or_primary or {})
    if cal:
        primary.setdefault("measurement_context", {})
        if isinstance(primary["measurement_context"], dict):
            mc = dict(primary["measurement_context"])
            if cal.get("vertical_exaggeration") is not None:
                geom = dict(mc.get("geometry") or {})
                geom["vertical_exaggeration"] = cal["vertical_exaggeration"]
                mc["geometry"] = geom
            if cal.get("calibrated"):
                mc["calibrated"] = True
            if cal.get("input_class"):
                mc["input_class"] = cal["input_class"]
            if cal.get("sha256"):
                mc["sha256"] = cal["sha256"]
            primary["measurement_context"] = mc
        primary["calibration"] = cal

    has_geometry = bool(primary.get("faults") or primary.get("horizons"))
    hypotheses: list[dict[str, Any]] = []
    all_unmeasured: set[str] = set()

    if has_geometry:
        base_hyp = _build_hypothesis_from_framework(
            hypothesis_id="HYP-001",
            witness_id="W-primary",
            witness_type="primary",
            framework=primary,
            model_or_method="structural_interpretation",
            derivation="Primary framework — gates run on live geometry",
        )
        matrix = run_all_structure_gates(primary)
        gates = matrix.get("gates") or {}
        unmeas = [g for g, v in gates.items() if v.get("status") in ("UNMEASURED",) or v.get("verdict") in ("UNMEASURED",)]
        kills = matrix.get("kills") or []
        all_unmeasured.update(unmeas)

        combined_verdict = matrix.get("combined_verdict", "")
        hypothesis_status_map = {
            "KILL": "REJECTED",
            "PASS": "SURVIVES_CURRENT_TESTS",
            "PARTIAL": "SURVIVES_CURRENT_TESTS",
            "UNMEASURED": "UNTESTED",
            "INCONCLUSIVE": "INCONCLUSIVE",
        }
        status = hypothesis_status_map.get(combined_verdict, "UNTESTED")

        applicable = len(gates)
        measured = applicable - len(unmeas)
        evidence_coverage = measured / max(applicable, 1)

        if cal.get("calibrated"):
            cal_status = "CALIBRATED"
        elif cal.get("vertical_exaggeration") or cal.get("bin_spacing_m"):
            cal_status = "PARTIAL"
        else:
            cal_status = "UNCALIBRATED"

        hyp = HypothesisModel(
            hypothesis_id=base_hyp["hypothesis_id"],
            witness_id=base_hyp["witness_id"],
            witness_type=base_hyp["witness_type"],
            model_or_method=base_hyp["model_or_method"],
            derivation=base_hyp["derivation"],
            horizons=list(primary.get("horizons") or []),
            faults=list(primary.get("faults") or []),
            fault_blocks=[],
            structural_style=base_hyp["structural_style"],
            kinematic_claims=[],
            confidence=0.0,
            status=status,
            hypothesis_status=status,
            evidence_coverage=evidence_coverage,
            calibration_status=cal_status,
            confidence_value=None,
            confidence_basis=None,
            epistemic_class="INTERPRETATION",
            supporting_evidence=[f"gate_pass:{g}" for g in (matrix.get("passes") or [])],
            contradicting_evidence=[f"gate_kill:{g}" for g in kills],
            physics_gates=list(gates.values()),
            unresolved_questions=[f"unmeasured:{g}" for g in unmeas],
            unresolved_measurements=list(unmeas),
            combined_gate_verdict=combined_verdict,
        )
        hypotheses.append(hyp.model_dump())

        # Empty conceptual alternatives (explicitly NOT copy-derived geometry clones)
        for i in range(2):
            hypotheses.append({
                "hypothesis_id": f"HYP-CONCEPTUAL-00{i+1}",
                "witness_id": f"W-conceptual-{i+1}",
                "witness_type": "empty_conceptual",
                "model_or_method": "requires_measurements",
                "structural_style": "unspecified",
                "status": "UNTESTED",
                "hypothesis_status": "UNTESTED",
                "evidence_coverage": 0.0,
                "calibration_status": "UNCALIBRATED",
                "confidence_value": None,
                "confidence_basis": None,
                "confidence": 0.0,
                "derivation": "empty_conceptual — geometry not supplied; states required measurements only",
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "unresolved_measurements": ["axis_calibration", "velocity_model", "independent_geometry"],
            })

    # Independent witnesses (ChatGPT / Claude / classical-CV / human) — never averaged
    wit_list = list(independent_witnesses or [])
    if isinstance(ec.get("witnesses"), list):
        wit_list.extend(ec["witnesses"])
    for i, w in enumerate(wit_list):
        if not isinstance(w, dict):
            continue
        src = str(w.get("source") or w.get("witness_type") or f"witness_{i}")
        fw = dict(w.get("framework") or {})
        if w.get("faults") is not None:
            fw["faults"] = w["faults"]
        if w.get("horizons") is not None:
            fw["horizons"] = w["horizons"]
        if not (fw.get("faults") or fw.get("horizons")):
            continue
        if cal and not fw.get("calibration"):
            fw["calibration"] = cal
        matrix_w = run_all_structure_gates(fw)
        gates_w = matrix_w.get("gates") or {}
        unmeas_w = [g for g, v in gates_w.items() if (v.get("status") or "") == "UNMEASURED"]
        all_unmeasured.update(unmeas_w)
        combined_w = matrix_w.get("combined_verdict", "")
        status_w = {
            "KILL": "REJECTED",
            "PASS": "SURVIVES_CURRENT_TESTS",
            "PARTIAL": "SURVIVES_CURRENT_TESTS",
            "UNMEASURED": "UNTESTED",
        }.get(combined_w, "UNTESTED")
        applicable_w = len(gates_w)
        measured_w = applicable_w - len(unmeas_w)
        hypotheses.append(
            HypothesisModel(
                hypothesis_id=w.get("hypothesis_id") or f"HYP-W-{i+2:03d}",
                witness_id=w.get("witness_id") or f"W-{src}",
                witness_type=str(w.get("witness_type") or "independent_model"),
                model_or_method=str(w.get("model_or_method") or src),
                derivation=str(w.get("derivation") or f"independent_witness:{src}"),
                horizons=list(fw.get("horizons") or []),
                faults=list(fw.get("faults") or []),
                structural_style=_style_from_faults(fw.get("faults") or []),
                confidence=0.0,
                status=status_w,
                hypothesis_status=status_w,
                evidence_coverage=measured_w / max(applicable_w, 1),
                calibration_status="PARTIAL" if cal.get("calibrated") else "UNCALIBRATED",
                confidence_value=None,
                confidence_basis=None,
                supporting_evidence=[f"gate_pass:{g}" for g in (matrix_w.get("passes") or [])],
                contradicting_evidence=[f"gate_kill:{g}" for g in (matrix_w.get("kills") or [])],
                physics_gates=list(gates_w.values()),
                unresolved_measurements=list(unmeas_w),
                combined_gate_verdict=combined_w,
            ).model_dump()
        )

    if not has_geometry and gate_matrix:
        # Pre-computed gate matrix, single hypothesis
        gates = gate_matrix.get("gates") or {}
        unmeas = [g for g, v in gates.items() if v.get("status") in ("UNMEASURED",) or v.get("verdict") in ("UNMEASURED",)]
        all_unmeasured.update(unmeas)
        kills = gate_matrix.get("kills") or []
        combined = gate_matrix.get("combined_verdict", "")
        status = HYPOTHESIS_STATUS_MAP.get(combined, "UNTESTED")
        applicable = len(gates)
        measured = applicable - len(unmeas)
        evidence_coverage = measured / max(applicable, 1)

        hyp = HypothesisModel(
            hypothesis_id="HYP-001",
            horizons=list(primary.get("horizons") or []),
            faults=list(primary.get("faults") or []),
            structural_style=_style_from_faults(primary.get("faults") or []),
            confidence=0.0,
            status=status,
            hypothesis_status=status,
            evidence_coverage=evidence_coverage,
            calibration_status="UNCALIBRATED",
            confidence_value=None,
            confidence_basis=None,
            physics_gates=list(gates.values()),
            contradicting_evidence=[f"gate_kill:{g}" for g in kills],
            unresolved_questions=[f"unmeasured:{g}" for g in unmeas],
            unresolved_measurements=list(unmeas),
            combined_gate_verdict=combined,
        )
        hypotheses.append(hyp.model_dump())

        for i, label in enumerate(("through_going_fold", "artifact_vs_structure"), start=2):
            hypotheses.append(
                HypothesisModel(
                    hypothesis_id=f"HYP-CONCEPTUAL-00{i}",
                    witness_id=f"W-conceptual-{label}",
                    witness_type="empty_conceptual",
                    structural_style=label,
                    confidence=0.0,
                    status="UNTESTED",
                    hypothesis_status="UNTESTED",
                    evidence_coverage=0.0,
                    calibration_status="UNCALIBRATED",
                    confidence_value=None,
                    confidence_basis=None,
                    epistemic_class="SPECULATION",
                    derivation=f"empty_conceptual:{label}",
                    unresolved_measurements=["geometry required for this alternative"],
                    physics_gates=[],
                ).model_dump()
            )

    # Propose-only (RSI / image-only) — one hypothesis from propose + empty conceptuals
    if propose_result and not hypotheses:
        geom = propose_result.get("geometry") or {}
        hypotheses.append(
            HypothesisModel(
                hypothesis_id="HYP-001",
                horizons=propose_result.get("horizons") or geom.get("horizons") or [],
                faults=propose_result.get("faults") or geom.get("faults") or [],
                structural_style="rsi_primary",
                confidence=0.0,
                status="UNTESTED",
                hypothesis_status="UNTESTED",
                evidence_coverage=0.0,
                calibration_status="UNCALIBRATED",
                confidence_value=None,
                confidence_basis=None,
                epistemic_class="INTERPRETATION",
                supporting_evidence=["rsi_pipeline"],
                unresolved_questions=["physics_gates_not_run_on_image_only_propose"],
                unresolved_measurements=["axis_calibration", "velocity_model", "independent_geometry"],
            ).model_dump()
        )
        for i in range(2):
            hypotheses.append({
                "hypothesis_id": f"HYP-CONCEPTUAL-00{i+1}",
                "witness_id": "empty_conceptual",
                "witness_type": "empty_conceptual",
                "model_or_method": "requires_measurements",
                "structural_style": "",
                "status": "UNTESTED",
                "hypothesis_status": "UNTESTED",
                "evidence_coverage": 0.0,
                "calibration_status": "UNCALIBRATED",
                "confidence_value": None,
                "confidence_basis": None,
                "derivation": "No geometry proposed — requires axis calibration, velocity model, and independent witness geometry",
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "unresolved_measurements": ["axis_calibration", "velocity_model", "independent_geometry"],
            })

    missing_scale = not (
        cal.get("calibrated")
        or cal.get("vertical_exaggeration") is not None
        or (primary.get("measurement_context") or {}).get("calibrated")
    )
    input_class = cal.get("input_class") or (primary.get("measurement_context") or {}).get("input_class") or "unknown"
    image_only = input_class == "image_only"
    missing_velocity = not (
        primary.get("velocity")
        or primary.get("interval_v_m_s")
        or (isinstance(earth_constraints, dict) and earth_constraints.get("velocity_model_ref"))
        or (hasattr(earth_constraints, "velocity_model_ref") and getattr(earth_constraints, "velocity_model_ref", None))
    )

    obs = observations or {}
    if propose_result:
        obs = {
            **obs,
            "rsi_stages": propose_result.get("stages"),
            "image_quality_flags": (propose_result.get("render_audit") or {}).get("flags")
            if isinstance(propose_result.get("render_audit"), dict)
            else [],
        }

    # Coerce free-dict hyps through HypothesisModel where possible
    validated_hyps: list[dict[str, Any]] = []
    for h in hypotheses:
        try:
            validated_hyps.append(HypothesisModel.model_validate(h).model_dump())
        except Exception:
            validated_hyps.append(h if isinstance(h, dict) else {"hypothesis_id": "HYP-unknown"})

    bundle = InterpretationBundle(
        observations=obs,
        hypotheses=[HypothesisModel.model_validate(h) for h in validated_hyps],
        preferred_hypothesis=None,  # human only
        limitations=LimitationsModel(
            missing_scale=bool(missing_scale),
            missing_velocity=bool(missing_velocity),
            image_only=bool(image_only),
            unmeasured_gates=sorted(all_unmeasured),
        ),
        provenance=ProvenanceModel(
            input_hash=cal.get("sha256")
            or cal.get("calibration_hash")
            or (primary.get("measurement_context") or {}).get("sha256")
            or (primary.get("measurement_context") or {}).get("calibration_hash"),
            model_revision=model_revision,
            algorithm_versions={"structure_gates": "v2", "bundle": "truth-loop-w3", "calibration_derive": "v1"},
            parameter_hash=_param_hash({"cal": cal, "req": req}),
        ),
        local_verdict="QUALIFIED_CANDIDATE",
        seal_authority="arifOS_only",
        seal_eligibility=False,
        governance_status="HOLD" if (all_unmeasured or image_only) else "QUALIFY",
    )
    out = bundle.model_dump()
    out["ok"] = True
    out["tool"] = "geox_seismic_interpret"
    out["interpretation_bundle"] = True
    # W3/W4 flags (LimitationsModel is strict — attach outside)
    lim = out.setdefault("limitations", {})
    if isinstance(lim, dict):
        lim["no_fabricated_alternatives"] = True
        lim["no_confidence_theatre"] = True
    return out
