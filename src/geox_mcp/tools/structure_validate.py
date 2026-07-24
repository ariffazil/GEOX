"""geox_structure_validate — structural framework falsification (G2–G9 + K-*).

Returns gate matrix + optional interpretation_bundle (multi-hypothesis).
UNMEASURED when scale/V missing. Never local SEAL.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.structure_gates import run_all_structure_gates


async def geox_structure_validate(
    framework: dict[str, Any] | None = None,
    faults: list[dict[str, Any]] | None = None,
    horizons: list[dict[str, Any]] | None = None,
    measurement_context: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    earth_constraints: dict[str, Any] | None = None,
    gates: list[str] | None = None,
    claim_text: str = "",
    emit_bundle: bool = False,
    hypothesis_count: int = 3,
) -> dict[str, Any]:
    fw: dict[str, Any] = dict(framework or {})
    if faults is not None:
        fw["faults"] = faults
    if horizons is not None:
        fw["horizons"] = horizons
    if measurement_context is not None:
        fw["measurement_context"] = measurement_context
    if calibration is not None:
        fw["calibration"] = calibration
        mc = dict(fw.get("measurement_context") or {})
        if calibration.get("vertical_exaggeration") is not None:
            geom = dict(mc.get("geometry") or {})
            geom["vertical_exaggeration"] = calibration["vertical_exaggeration"]
            mc["geometry"] = geom
        # Chat calibration keys → measurement_context.geometry
        for src_k, dst_k in (
            ("bin_spacing_m", "bin_spacing_m"),
            ("sample_rate_ms", "sample_rate_ms"),
            ("sample_interval_ms", "sample_rate_ms"),
            ("ve", "vertical_exaggeration"),
        ):
            if calibration.get(src_k) is not None:
                geom = dict(mc.get("geometry") or {})
                geom[dst_k] = calibration[src_k]
                mc["geometry"] = geom
        if calibration.get("calibrated") or any(
            calibration.get(k) is not None
            for k in ("bin_spacing_m", "vertical_exaggeration", "velocity_td", "velocity_linear_m_s")
        ):
            mc["calibrated"] = True
        if calibration.get("input_class"):
            mc["input_class"] = calibration["input_class"]
        fw["measurement_context"] = mc

    if not fw.get("faults") and not fw.get("horizons") and not fw.get("velocity") and not fw.get("restore"):
        return {
            "ok": False,
            "tool": "geox_structure_validate",
            "error": "EMPTY_FRAMEWORK",
            "message": "Provide framework with faults[] and/or horizons[] (or velocity/restore metrics).",
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "seal_authority": "arifOS_only",
        }

    # Geometry adapt + calibration derive happen inside run_all_structure_gates
    matrix = run_all_structure_gates(fw)

    if gates:
        want = {g.upper() for g in gates}
        filtered = {k: v for k, v in matrix["gates"].items() if k.upper() in want or k in want}
        kills = [k for k, v in filtered.items() if (v.get("status") or v.get("verdict")) == "KILL"]
        passes = [k for k, v in filtered.items() if (v.get("status") or v.get("verdict")) == "PASS"]
        unmeasured = [k for k, v in filtered.items() if (v.get("status") or v.get("verdict")) in ("UNMEASURED", "INCONCLUSIVE")]
        if kills:
            combined = "KILL"
        elif passes:
            combined = "PASS" if not unmeasured else "PARTIAL"
        else:
            combined = "UNMEASURED"
        matrix = {
            **matrix,
            "gates": filtered,
            "combined_verdict": combined,
            "kills": kills,
            "passes": passes,
            "unmeasured": unmeasured,
            "inconclusive": unmeasured,
        }

    mc = fw.get("measurement_context") or {}
    input_class = mc.get("input_class") or fw.get("input_class") or "unknown"
    combined = matrix["combined_verdict"]
    if combined == "KILL":
        gov, overall = "HOLD", "FALSIFIED"
    elif combined in ("PASS", "PARTIAL"):
        gov, overall = "QUALIFY", "SURVIVED"
    else:
        gov, overall = "HOLD", "UNMEASURED"

    # Ensure every gate has receipt_hash
    for gname, gval in (matrix.get("gates") or {}).items():
        if isinstance(gval, dict) and not gval.get("receipt_hash"):
            from geox_mcp.domain.seismic_physics.receipts import receipt_hash

            gval["receipt_hash"] = receipt_hash(gval)

    # Compact gate_summary counts for progressive disclosure (P4)
    from geox_mcp.tools.section_render import compact_gate_summary

    gsum = compact_gate_summary(matrix.get("gates") or {})
    # Re-run is not needed — cutoffs live on framework after gates
    # matrix path stores cutoffs only if we re-derive; pull from a fresh normalize
    from geox_mcp.tools.structure_gates import derive_cutoff_pairs, normalize_framework

    fw_n = normalize_framework(fw)
    cutoffs = fw_n.get("cutoffs") or derive_cutoff_pairs(fw_n.get("faults") or [], fw_n.get("horizons") or [])

    out: dict[str, Any] = {
        "ok": True,
        "tool": "geox_structure_validate",
        "overall_verdict": overall,
        "combined_gate_verdict": combined,
        "gates": matrix["gates"],
        "gate_summary": {
            "pass": len(gsum.get("passes") or []),
            "warn": len(gsum.get("warns") or []),
            "kill": len(gsum.get("kills") or []),
            "unmeasured": len(gsum.get("unmeasured") or []),
        },
        "kills": matrix["kills"],
        "passes": matrix["passes"],
        "warns": matrix.get("warns") or [],
        "unmeasured": matrix.get("unmeasured") or matrix.get("inconclusive") or [],
        "inconclusive": matrix.get("unmeasured") or matrix.get("inconclusive") or [],
        "cutoffs": cutoffs,
        "rejected_geometry": fw_n.get("_rejected") or fw.get("_rejected") or [],
        "input_class": input_class,
        "measurement_context": mc or None,
        "claim_text": (claim_text or "")[:500],
        "n_faults": len(fw_n.get("faults") or fw.get("faults") or []),
        "n_horizons": len(fw_n.get("horizons") or fw.get("horizons") or []),
        "governance_status": gov,
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "seal_eligibility": False,
        "preferred_hypothesis": None,
        "epistemic_label": "DER",
        "honesty_banner": (
            "Structure gates falsify impossible geometry. "
            "K-DIP is a filter not sole polarity judge (use K-POLARITY cutoffs). "
            "UNMEASURED when scale/velocity missing — never invent. "
            "SURVIVED ≠ proven. arifOS SEAL only."
        ),
    }

    if emit_bundle or hypothesis_count:
        from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle

        bundle = build_interpretation_bundle(
            frameworks_or_primary=fw,
            calibration=calibration or mc,
            earth_constraints=earth_constraints,
            request={"hypothesis_count": max(3, hypothesis_count or 3)},
        )
        out["interpretation_bundle"] = bundle
        out["hypotheses"] = bundle.get("hypotheses")
        out["preferred_hypothesis"] = None
        out["limitations"] = bundle.get("limitations")

    # P7 multi-witness: external geometry bundles under same section
    witnesses = None
    if isinstance(earth_constraints, dict):
        witnesses = earth_constraints.get("witnesses")
    if not witnesses and isinstance(fw.get("witnesses"), list):
        witnesses = fw["witnesses"]
    if witnesses:
        from geox_mcp.tools.structure_gates.witness import gate_all_witnesses, register_witnesses

        reg = register_witnesses(fw, witnesses)
        out["multi_witness"] = {
            "n": len(reg),
            "results": gate_all_witnesses(reg, calibration=calibration),
            "note": "Symmetric gates on all witnesses — no preferred hypothesis from GEOX",
        }
        out["preferred_hypothesis"] = None

    return out
