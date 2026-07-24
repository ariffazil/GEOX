"""Structural physics / topology gates (G2–G9 + K-*).

Status: PASS | WARN | KILL | UNMEASURED | NOT_APPLICABLE + receipt_hash.
Any KILL → model REJECTED. Correlated — not blind POS multiply.

Hypothesis aggregation:
  any KILL → REJECTED
  no KILL + at least one measured gate → SURVIVES_CURRENT_TESTS
  no measurable gates → UNTESTED
  conflicting measured gates → INCONCLUSIVE

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.structure_gates.cutoff import derive_cutoff_pairs, gate_k_polarity
from geox_mcp.tools.structure_gates.growth import gate_k_growth
from geox_mcp.tools.structure_gates.k_dip import gate_k_dip
from geox_mcp.tools.structure_gates.k_dl import gate_k_dl
from geox_mcp.tools.structure_gates.k_throw import gate_k_throw
from geox_mcp.tools.structure_gates.normalize import normalize_fault, normalize_framework
from geox_mcp.tools.structure_gates.restore import gate_k_restore
from geox_mcp.tools.structure_gates.topology import gate_g2_topology
from geox_mcp.tools.structure_gates.velocity import gate_k_vel

__all__ = [
    "gate_k_dip",
    "gate_k_throw",
    "gate_k_dl",
    "gate_g2_topology",
    "gate_k_restore",
    "gate_k_vel",
    "gate_k_growth",
    "gate_k_polarity",
    "derive_cutoff_pairs",
    "normalize_fault",
    "normalize_framework",
    "run_all_structure_gates",
    "aggregate_hypothesis_status",
    "HYPOTHESIS_STATUS_MAP",
]

HYPOTHESIS_STATUS_MAP: dict[str, str] = {
    "KILL": "REJECTED",
    "PASS": "SURVIVES_CURRENT_TESTS",
    "PARTIAL": "SURVIVES_CURRENT_TESTS",
    "UNMEASURED": "UNTESTED",
    "INCONCLUSIVE": "INCONCLUSIVE",
}


def aggregate_hypothesis_status(
    gates: dict[str, Any],
    kills: list[str],
    passes: list[str],
    warns: list[str],
    unmeasured: list[str],
) -> str:
    """Hypothesis-level status from gate matrix.

    any KILL → REJECTED
    no KILL + at least one measured gate → SURVIVES_CURRENT_TESTS
    no measurable gates → UNTESTED
    conflicting measured gates → INCONCLUSIVE
    """
    if kills:
        return "REJECTED"
    measured = len(passes) + len(warns) + len(kills)
    if measured == 0:
        return "UNTESTED"
    return "SURVIVES_CURRENT_TESTS"


def run_all_structure_gates(framework: dict[str, Any]) -> dict[str, Any]:
    """Run full structural gate matrix on a StructuralFramework-like dict.

    Discrimination chain (P2): calibration → VE/T–D → true dip (FILTER) →
    cutoff sense (K-POLARITY) → throw taper → growth → restoration (JUDGE).
    K-DIP never sole-sources a polarity kill.
    """
    from geox_mcp.tools.structure_gates.calibration_derive import apply_calibration
    from geox_mcp.tools.structure_gates.normalize import normalize_framework

    # Calibration derive (sticks+bin+T–D → dips/throws/lengths) THEN normalize
    cal = None
    if isinstance(framework, dict):
        cal = framework.get("calibration")
        if not cal and isinstance(framework.get("measurement_context"), dict):
            # pull VE/bin from measurement_context.geometry if present
            geom = (framework["measurement_context"] or {}).get("geometry") or {}
            if geom or framework.get("measurement_context", {}).get("calibrated"):
                cal = {
                    "vertical_exaggeration": geom.get("vertical_exaggeration"),
                    "bin_spacing_m": geom.get("bin_spacing_m"),
                    "sample_rate_ms": geom.get("sample_rate_ms"),
                    "calibrated": framework["measurement_context"].get("calibrated"),
                    "input_class": framework["measurement_context"].get("input_class"),
                    "velocity_td": (framework.get("calibration") or {}).get("velocity_td")
                    if isinstance(framework.get("calibration"), dict)
                    else None,
                }
        if cal:
            framework = apply_calibration(framework, cal if isinstance(cal, dict) else {})
    # Alias metric-suffixed demo keys (dmax_m, throw_profile_m, …) → canonical
    # so K-DL/K-THROW can kill rather than silently UNMEASURED.
    framework = normalize_framework(framework)
    # P2: CutoffPairs before polarity / throw consumers
    if not framework.get("cutoffs") and (framework.get("faults") or framework.get("horizons")):
        framework["cutoffs"] = derive_cutoff_pairs(
            framework.get("faults") or [],
            framework.get("horizons") or [],
        )
    gates_spec = [
        ("K-DIP", gate_k_dip),
        ("K-POLARITY", gate_k_polarity),
        ("K-THROW", gate_k_throw),
        ("K-DL", gate_k_dl),
        ("G2", gate_g2_topology),
        ("K-XCUT", gate_g2_topology),
        ("K-RESTORE", gate_k_restore),
        ("K-VEL", gate_k_vel),
        ("K-GROWTH", gate_k_growth),
    ]
    results: dict[str, Any] = {}
    kills: list[str] = []
    passes: list[str] = []
    warns: list[str] = []
    unmeasured: list[str] = []
    not_applicable: list[str] = []

    topology_result: dict[str, Any] | None = None
    for name, fn in gates_spec:
        if fn is gate_g2_topology:
            if topology_result is None:
                topology_result = fn(framework)
            r = dict(topology_result)
            if name == "K-XCUT":
                r = {**r, "gate": "K-XCUT", "gate_id": "K-XCUT", "alias_of": "G2"}
        else:
            r = fn(framework)
        results[name] = r
        v = r.get("status") or r.get("verdict") or "UNMEASURED"
        if v == "KILL":
            kills.append(name)
        elif v == "PASS":
            passes.append(name)
        elif v == "WARN":
            warns.append(name)
        elif v == "NOT_APPLICABLE":
            not_applicable.append(name)
        else:
            unmeasured.append(name)

    if kills:
        combined = "KILL"
    elif passes or warns:
        combined = "PASS" if not unmeasured else "PARTIAL"
    else:
        combined = "UNMEASURED"

    hypothesis_status = aggregate_hypothesis_status(results, kills, passes, warns, unmeasured)

    return {
        "gates": results,
        "combined_verdict": combined,
        "hypothesis_status": hypothesis_status,
        "kills": kills,
        "passes": passes,
        "warns": warns,
        "unmeasured": unmeasured,
        "not_applicable": not_applicable,
        "inconclusive": unmeasured,  # legacy alias
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "note": (
            "Correlated gates — not blind POS. UNMEASURED ≠ PASS. "
            "K-DIP is filter not sole polarity judge. any hard KILL → REJECTED."
        ),
    }
