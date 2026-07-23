"""geox_structure_validate — structural framework falsification (G2–G9 + K-*).

Internal/product path. Prefer calling via:
  - geox_seismic_interpret(mode=structure_validate, framework=...)
  - geox_falsify(claim_type=structural_fault|structural_horizon|structural_framework, context=framework)

Never emits local SEAL. Max local_verdict = QUALIFIED_CANDIDATE.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.structure_gates import run_all_structure_gates


async def geox_structure_validate(
    framework: dict[str, Any] | None = None,
    faults: list[dict[str, Any]] | None = None,
    horizons: list[dict[str, Any]] | None = None,
    measurement_context: dict[str, Any] | None = None,
    gates: list[str] | None = None,
    claim_text: str = "",
) -> dict[str, Any]:
    """Validate a structural framework against physics/topology gates.

    Args:
        framework: StructuralFramework-like dict (faults, horizons, claims, velocity, restore)
        faults / horizons: optional top-level convenience (merged into framework)
        measurement_context: G0 identity (input_class, sha256, VE, ...)
        gates: optional subset filter by gate name (default all)
        claim_text: free text for receipt only
    """
    fw: dict[str, Any] = dict(framework or {})
    if faults is not None:
        fw["faults"] = faults
    if horizons is not None:
        fw["horizons"] = horizons
    if measurement_context is not None:
        fw["measurement_context"] = measurement_context

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

    matrix = run_all_structure_gates(fw)

    if gates:
        want = {g.upper() for g in gates}
        filtered = {k: v for k, v in matrix["gates"].items() if k.upper() in want or k in want}
        kills = [k for k, v in filtered.items() if v.get("verdict") == "KILL"]
        passes = [k for k, v in filtered.items() if v.get("verdict") == "PASS"]
        inconclusive = [k for k, v in filtered.items() if v.get("verdict") == "INCONCLUSIVE"]
        if kills:
            combined = "KILL"
        elif passes and not kills:
            combined = "PASS" if not inconclusive else "PARTIAL"
        else:
            combined = "INCONCLUSIVE"
        matrix = {
            **matrix,
            "gates": filtered,
            "combined_verdict": combined,
            "kills": kills,
            "passes": passes,
            "inconclusive": inconclusive,
        }

    mc = fw.get("measurement_context") or {}
    input_class = mc.get("input_class") or fw.get("input_class") or "unknown"

    combined = matrix["combined_verdict"]
    if combined == "KILL":
        gov = "HOLD"
        overall = "FALSIFIED"
    elif combined in ("PASS", "PARTIAL"):
        gov = "QUALIFY"
        overall = "SURVIVED"
    else:
        gov = "HOLD"
        overall = "INCONCLUSIVE"

    return {
        "ok": True,
        "tool": "geox_structure_validate",
        "overall_verdict": overall,
        "combined_gate_verdict": combined,
        "gates": matrix["gates"],
        "kills": matrix["kills"],
        "passes": matrix["passes"],
        "inconclusive": matrix["inconclusive"],
        "input_class": input_class,
        "measurement_context": mc or None,
        "claim_text": (claim_text or "")[:500],
        "n_faults": len(fw.get("faults") or []),
        "n_horizons": len(fw.get("horizons") or []),
        "governance_status": gov,
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "epistemic_label": "DER",
        "honesty_banner": (
            "Structure gates falsify impossible geometry. "
            "SURVIVED ≠ proven Earth model. arifOS SEAL only. "
            "image_only remains INT_SEISMIC."
        ),
    }
