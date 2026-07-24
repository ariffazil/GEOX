"""Build interpretation_bundle from framework gate matrix + optional propose.

preferred_hypothesis is always null from GEOX — human sets acceptance.
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


def _competing_frameworks(
    base: dict[str, Any],
    n: int = 3,
) -> list[tuple[str, str, dict[str, Any]]]:
    """Build ≥3 competing structural hypotheses from one framework.

    H0: as proposed
    H1: relay / segmented (split throw, linkage story)
    H2: artifact-dominant (degrade dips to force challenge / no dip)
    """
    faults = list(base.get("faults") or [])
    horizons = list(base.get("horizons") or [])
    shared = {k: v for k, v in base.items() if k not in ("faults", "horizons")}

    h0 = {**shared, "faults": faults, "horizons": horizons}

    h1_faults = []
    for f in faults:
        nf = dict(f)
        nf["fault_id"] = f"{f.get('fault_id') or f.get('id') or 'F'}_relay"
        nf["linkage_story"] = True
        # split as segmented — keep dip, mark multi-peak throw if present
        prof = nf.get("throw_profile")
        if isinstance(prof, list) and len(prof) >= 3:
            # M-type twin peak suggestion
            mid = len(prof) // 2
            if all(isinstance(x, dict) for x in prof):
                alt = [dict(x) for x in prof]
                if "throw" in alt[0]:
                    alt[0]["throw"] = float(alt[0].get("throw") or 0) * 0.3
                    alt[-1]["throw"] = float(alt[-1].get("throw") or 0) * 0.3
                    if mid < len(alt):
                        alt[mid]["throw"] = float(alt[mid].get("throw") or 0)
                nf["throw_profile"] = alt
            nf["tip_taper"] = nf.get("tip_taper") or "ok"
        h1_faults.append(nf)
    h1 = {**shared, "faults": h1_faults or faults, "horizons": horizons}

    h2_faults = []
    for f in faults:
        nf = dict(f)
        nf["fault_id"] = f"{f.get('fault_id') or f.get('id') or 'F'}_artifact"
        # deliberately challenge: claim image-only uncalibrated dip if was claimed true
        if "dip_deg_subsurface" in nf:
            nf["dip_deg_image"] = nf.pop("dip_deg_subsurface")
            nf.pop("dip_calibrated", None)
        # remove VE so K-DIP becomes UNMEASURED on artifact hyp if only image dip
        h2_faults.append(nf)
    h2_shared = dict(shared)
    # strip calibration for artifact-dominant to force UNMEASURED where appropriate
    if "measurement_context" in h2_shared:
        mc = dict(h2_shared["measurement_context"] or {})
        geom = dict(mc.get("geometry") or {})
        geom.pop("vertical_exaggeration", None)
        mc["geometry"] = geom
        mc["calibrated"] = False
        h2_shared["measurement_context"] = mc
    h2_shared.pop("calibration", None)
    h2 = {**h2_shared, "faults": h2_faults or faults, "horizons": horizons}

    out = [
        ("HYP-001", "as_proposed", h0),
        ("HYP-002", "relay_segmented", h1),
        ("HYP-003", "artifact_dominant", h2),
    ]
    return out[: max(3, n)]


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
) -> dict[str, Any]:
    """Assemble interpretation_bundle. preferred_hypothesis always None from GEOX."""
    from geox_mcp.tools.structure_gates import run_all_structure_gates

    cal = calibration if isinstance(calibration, dict) else (calibration.model_dump() if calibration else {})
    req = request if isinstance(request, dict) else (request.model_dump() if request else InterpretRequestFlags().model_dump())
    hyp_n = int(req.get("hypothesis_count") or 3)

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

    # Multi-hypothesis compete
    pairs = _competing_frameworks(primary, n=hyp_n) if (primary.get("faults") or primary.get("horizons")) else []
    if not pairs and gate_matrix:
        # single gate matrix already computed
        pairs = []

    hypotheses: list[dict[str, Any]] = []
    all_unmeasured: set[str] = set()

    if pairs:
        for hid, style_tag, fw in pairs:
            matrix = run_all_structure_gates(fw)
            gates = matrix.get("gates") or {}
            unmeas = [g for g, v in gates.items() if v.get("status") == "UNMEASURED" or v.get("verdict") == "UNMEASURED"]
            kills = matrix.get("kills") or []
            all_unmeasured.update(unmeas)
            conf = 0.55
            if matrix.get("combined_verdict") == "KILL":
                conf = 0.15
            elif matrix.get("combined_verdict") in ("PASS", "PARTIAL"):
                conf = 0.45
            elif unmeas:
                conf = 0.25
            hyp = HypothesisModel(
                hypothesis_id=hid,
                horizons=list(fw.get("horizons") or []),
                faults=list(fw.get("faults") or []),
                fault_blocks=[],
                structural_style=style_tag if style_tag != "as_proposed" else _style_from_faults(fw.get("faults") or []),
                confidence=conf,
                epistemic_class="INTERPRETATION",
                supporting_evidence=[f"gate_pass:{g}" for g in (matrix.get("passes") or [])],
                contradicting_evidence=[f"gate_kill:{g}" for g in kills],
                physics_gates=list(gates.values()),
                unresolved_questions=[f"unmeasured:{g}" for g in unmeas],
                combined_gate_verdict=matrix.get("combined_verdict"),
            )
            hypotheses.append(hyp.model_dump())
    elif gate_matrix:
        gates = gate_matrix.get("gates") or {}
        unmeas = [g for g, v in gates.items() if v.get("status") == "UNMEASURED" or v.get("verdict") == "UNMEASURED"]
        all_unmeasured.update(unmeas)
        hyp = HypothesisModel(
            hypothesis_id="HYP-001",
            horizons=list(primary.get("horizons") or []),
            faults=list(primary.get("faults") or []),
            structural_style=_style_from_faults(primary.get("faults") or []),
            confidence=0.4,
            physics_gates=list(gates.values()),
            contradicting_evidence=[f"gate_kill:{g}" for g in (gate_matrix.get("kills") or [])],
            unresolved_questions=[f"unmeasured:{g}" for g in unmeas],
            combined_gate_verdict=gate_matrix.get("combined_verdict"),
        )
        hypotheses.append(hyp.model_dump())
        # pad to ≥3 formal alternatives even if only one matrix
        for i, label in enumerate(("relay_segmented", "artifact_dominant"), start=2):
            hypotheses.append(
                HypothesisModel(
                    hypothesis_id=f"HYP-00{i}",
                    structural_style=label,
                    confidence=0.2,
                    epistemic_class="SPECULATION",
                    unresolved_questions=["alternative_not_fully_expanded"],
                    physics_gates=[],
                ).model_dump()
            )

    # Propose-only (RSI) without structure: still ≥3 alts
    if propose_result and not hypotheses:
        alts = propose_result.get("alternatives") or []
        hypotheses.append(
            HypothesisModel(
                hypothesis_id="HYP-001",
                horizons=propose_result.get("horizons") or (propose_result.get("geometry") or {}).get("horizons") or [],
                faults=propose_result.get("faults") or (propose_result.get("geometry") or {}).get("faults") or [],
                structural_style="rsi_primary",
                confidence=0.35,
                epistemic_class="INTERPRETATION",
                supporting_evidence=["rsi_pipeline"],
                unresolved_questions=["physics_gates_not_run_on_image_only_propose"],
            ).model_dump()
        )
        for i, a in enumerate(alts[:2], start=2):
            hypotheses.append(
                HypothesisModel(
                    hypothesis_id=f"HYP-00{i}",
                    structural_style=str(a.get("model_id") if isinstance(a, dict) else a),
                    confidence=0.2,
                    epistemic_class="SPECULATION",
                ).model_dump()
            )
        while len(hypotheses) < 3:
            hypotheses.append(
                HypothesisModel(
                    hypothesis_id=f"HYP-00{len(hypotheses) + 1}",
                    structural_style="unspecified_alternative",
                    confidence=0.15,
                    epistemic_class="SPECULATION",
                ).model_dump()
            )

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
        or (hasattr(earth_constraints, "velocity_model_ref") and earth_constraints.velocity_model_ref)
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

    bundle = InterpretationBundle(
        observations=obs,
        hypotheses=[HypothesisModel.model_validate(h) for h in hypotheses],
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
            algorithm_versions={"structure_gates": "v1", "bundle": "b-final", "calibration_derive": "v1"},
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
    return out
