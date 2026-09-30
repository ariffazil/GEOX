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
from geox_mcp.tools.structure_gates.tectonic_regime import (
    REGIME_CATEGORIES,
    REGIME_FALSIFIERS,
    falsify_regime,
    run_regime_falsification,
)
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
    # Tectonic regime falsification (K-REGIME-*, K-EXT-*, K-COMP-*, K-SS-*, K-INV-*, K-SALT-*)
    "REGIME_CATEGORIES",
    "REGIME_FALSIFIERS",
    "falsify_regime",
    "run_regime_falsification",
]

HYPOTHESIS_STATUS_MAP: dict[str, str] = {
    "KILL": "REJECTED",
    "PASS": "SURVIVES_CURRENT_TESTS",
    "PARTIAL": "SURVIVES_CURRENT_TESTS",
    "UNMEASURED": "UNTESTED",
    "INCONCLUSIVE": "INCONCLUSIVE",
    "PARTIALLY_MEASURED": "SURVIVES_CURRENT_TESTS",
    "COMPUTABLE": "UNTESTED",
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


def _merged_combined_verdict(
    kills: list[str],
    passes: list[str],
    warns: list[str],
    unmeasured: list[str],
    partially_measured: list[str],
    computable: list[str],
) -> str:
    """Combined-gate precedence for the core + K-REGIME merged view.

    Mirrors the precedence applied to the 9 core gates, in the same order, so
    the two views cannot drift. Used ONLY for `combined_verdict_with_regime`;
    the core `combined_verdict` is computed by the original inline block.
    """
    if kills:
        return "KILL"
    if passes or warns:
        return "PASS" if not unmeasured else "PARTIAL"
    if partially_measured:
        return "PARTIALLY_MEASURED"
    if computable:
        return "COMPUTABLE"
    return "UNMEASURED"


def _regime_skipped_block(reason: str) -> dict[str, Any]:
    """Truthful marker when the K-REGIME block is deliberately not executed.

    Never a bare None and never a PASS: skipped == UNTESTED.
    """
    return {
        "ok": False,
        "tool": "geox_regime_falsification",
        "error": "REGIME_FALSIFICATION_SKIPPED",
        "message": reason,
        "universal_gates": {},
        "hypotheses": [],
        "n_hypotheses": 0,
        "surviving": [],
        "rejected": [],
        "untested": [],
        "overall": "INSUFFICIENT_EVIDENCE",
        "governance_status": "HOLD",
        "preferred_hypothesis": None,
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
    }


def _run_regime_falsification_block(framework: dict[str, Any]) -> dict[str, Any]:
    """Execute the K-REGIME engine (tectonic_regime.run_regime_falsification).

    A regime-engine exception must not delete the core gate matrix, and must
    not be swallowed either — it is returned as an explicit error block
    (status UNTESTED / governance HOLD), never as PASS and never as KILL.
    """
    try:
        return run_regime_falsification(framework)
    except Exception as exc:  # noqa: BLE001 — surfaced, never silenced
        return {
            "ok": False,
            "tool": "geox_regime_falsification",
            "error": "REGIME_ENGINE_EXCEPTION",
            "message": f"{type(exc).__name__}: {exc}",
            "universal_gates": {},
            "hypotheses": [],
            "n_hypotheses": 0,
            "surviving": [],
            "rejected": [],
            "untested": [],
            "overall": "INSUFFICIENT_EVIDENCE",
            "governance_status": "HOLD",
            "preferred_hypothesis": None,
            "local_verdict": "QUALIFIED_CANDIDATE",
            "seal_authority": "arifOS_only",
        }


def _regime_gate_receipts(block: dict[str, Any]) -> dict[str, Any]:
    """Flatten regime receipts into one gate_id → receipt map.

    Universal gates (K-REGIME-*) keep their ids; per-regime falsifier receipts
    keep theirs (K-EXT-*, K-COMP-*, K-SS-*, K-INV-*, K-SALT-*, K-GRAV-*,
    K-NULL-*). Ids are unique across regimes today; if a future falsifier
    collides the second occurrence is namespaced as "<regime>:<gate_id>"
    rather than silently overwriting a receipt.
    """
    out: dict[str, Any] = {}
    for gid, r in (block.get("universal_gates") or {}).items():
        if isinstance(r, dict):
            out[str(gid)] = r
    for h in block.get("hypotheses") or []:
        if not isinstance(h, dict):
            continue
        rid = str(h.get("regime") or "regime")
        for gid, r in (h.get("gates") or {}).items():
            if not isinstance(r, dict):
                continue
            key = str(gid)
            if key in out:
                key = f"{rid}:{gid}"
            out[key] = r
    return out


def _classify_receipts(receipts: dict[str, Any]) -> dict[str, list[str]]:
    """Bucket receipt ids by status. UNMEASURED is NOT a pass — it lands in
    `unmeasured`, never in `passes`."""
    buckets: dict[str, list[str]] = {
        "kills": [], "passes": [], "warns": [],
        "unmeasured": [], "not_applicable": [],
        "partially_measured": [], "computable": [],
    }
    for gid, r in receipts.items():
        v = str(r.get("status") or r.get("verdict") or "UNMEASURED")
        if v == "KILL":
            buckets["kills"].append(gid)
        elif v == "PASS":
            buckets["passes"].append(gid)
        elif v == "WARN":
            buckets["warns"].append(gid)
        elif v == "NOT_APPLICABLE":
            buckets["not_applicable"].append(gid)
        elif v == "PARTIALLY_MEASURED":
            buckets["partially_measured"].append(gid)
        elif v == "COMPUTABLE":
            buckets["computable"].append(gid)
        else:
            buckets["unmeasured"].append(gid)
    return buckets


def run_all_structure_gates(
    framework: dict[str, Any],
    *,
    include_regime_gates: bool = True,
) -> dict[str, Any]:
    """Run full structural gate matrix on a StructuralFramework-like dict.

    Discrimination chain (P2): calibration → VE/T–D → true dip (FILTER) →
    cutoff sense (K-POLARITY) → throw taper → growth → restoration (JUDGE).
    K-DIP never sole-sources a polarity kill.

    K-REGIME (additive, 2026-09-18): the tectonic-regime falsification engine
    (tectonic_regime.py) is executed over the SAME calibrated + normalized
    framework. Its receipts merge into `gates` as K-REGIME-*/K-EXT-*/K-COMP-*/
    K-SS-*/K-INV-*/K-SALT-*/K-GRAV-*/K-NULL-*, and its driver output is returned
    as `regime_falsification` / `regime_status` / `regime_kills`. The 9 core
    gates and the core `combined_verdict` / `hypothesis_status` are unchanged:
    the merged view lives only in `combined_verdict_with_regime` and
    `hypothesis_status_with_regime`. `include_regime_gates=False` skips it.
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
    partially_measured: list[str] = []
    computable: list[str] = []

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
        elif v == "PARTIALLY_MEASURED":
            partially_measured.append(name)
        elif v == "COMPUTABLE":
            computable.append(name)
        else:
            unmeasured.append(name)

    if kills:
        combined = "KILL"
    elif passes or warns:
        combined = "PASS" if not unmeasured else "PARTIAL"
    elif partially_measured:
        combined = "PARTIALLY_MEASURED"
    elif computable:
        combined = "COMPUTABLE"
    else:
        combined = "UNMEASURED"

    hypothesis_status = aggregate_hypothesis_status(results, kills, passes, warns, unmeasured)

    # ── K-REGIME — tectonic-regime falsification (ADDITIVE) ──────────────────
    # tectonic_regime.py is an orthogonal falsifier matrix: 7 candidate regimes
    # (incl. the MANDATORY null hypothesis) × their falsifier families, plus 7
    # universal epistemic gates (ceiling / differential / decompaction / display
    # / resolution / xcut / coverage). It was imported here but never invoked —
    # so the doctrine ran nowhere. It runs here.
    #
    # Additive contract, deliberately narrow:
    #   * the 9 core receipts in `results` are untouched; core kills / passes /
    #     warns / unmeasured stay core-only, so `combined_verdict` and
    #     `hypothesis_status` cannot drift from the 9-gate matrix
    #   * regime results are readable: `regime_falsification` (full driver
    #     output), K-REGIME-* receipts inside `gates`, and flat
    #     regime_kills / regime_passes / regime_warns / regime_unmeasured
    #   * a regime KILL is never hidden behind the core verdict — the merged
    #     view is exposed as combined_verdict_with_regime /
    #     hypothesis_status_with_regime (aggregate_hypothesis_status reused
    #     unmodified)
    #   * UNMEASURED is never promoted: an unmeasured regime receipt lands in
    #     `regime_unmeasured`, never in `regime_passes`
    if include_regime_gates:
        regime_block = _run_regime_falsification_block(framework)
    else:
        regime_block = _regime_skipped_block(
            "include_regime_gates=False — K-REGIME matrix not executed"
        )
    regime_receipts = _regime_gate_receipts(regime_block)
    regime_buckets = _classify_receipts(regime_receipts)
    regime_kills = regime_buckets["kills"]
    regime_passes = regime_buckets["passes"]
    regime_warns = regime_buckets["warns"]
    regime_unmeasured = regime_buckets["unmeasured"]
    regime_not_applicable = regime_buckets["not_applicable"]
    # Receipts are merged AFTER core aggregation so core lists cannot change.
    results.update(regime_receipts)

    merged_combined = _merged_combined_verdict(
        kills + regime_kills,
        passes + regime_passes,
        warns + regime_warns,
        unmeasured + regime_unmeasured,
        partially_measured + regime_buckets["partially_measured"],
        computable + regime_buckets["computable"],
    )
    merged_hypothesis_status = aggregate_hypothesis_status(
        results,
        kills + regime_kills,
        passes + regime_passes,
        warns + regime_warns,
        unmeasured + regime_unmeasured,
    )

    return {
        "gates": results,
        "combined_verdict": combined,
        "hypothesis_status": hypothesis_status,
        "kills": kills,
        "passes": passes,
        "warns": warns,
        "unmeasured": unmeasured,
        "not_applicable": not_applicable,
        "partially_measured": partially_measured,
        "computable": computable,
        "inconclusive": unmeasured,  # legacy alias
        # ── K-REGIME (additive) ──────────────────────────────────────────────
        "regime_falsification": regime_block,
        "regime_status": regime_block.get("overall"),
        "regime_governance_status": regime_block.get("governance_status"),
        "regime_surviving": list(regime_block.get("surviving") or []),
        "regime_rejected": list(regime_block.get("rejected") or []),
        "regime_untested": list(regime_block.get("untested") or []),
        "regime_kills": regime_kills,
        "regime_passes": regime_passes,
        "regime_warns": regime_warns,
        "regime_unmeasured": regime_unmeasured,
        "regime_not_applicable": regime_not_applicable,
        "combined_verdict_with_regime": merged_combined,
        "hypothesis_status_with_regime": merged_hypothesis_status,
        "regime_note": (
            "K-REGIME receipts are merged into `gates` additively. Core "
            "combined_verdict/hypothesis_status speak for the 9 core gates only; "
            "the merged verdict is combined_verdict_with_regime. "
            "preferred_hypothesis is always None — GEOX proposes, arifOS seals."
        ),
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "note": (
            "Correlated gates — not blind POS. UNMEASURED ≠ PASS. "
            "K-DIP is filter not sole polarity judge. any hard KILL → REJECTED."
        ),
    }
