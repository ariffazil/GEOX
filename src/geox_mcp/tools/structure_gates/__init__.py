"""Structural physics / topology gates (G2–G9 + K-*).

Each gate returns PASS | KILL | INCONCLUSIVE + receipt.
Any KILL → model rejected for that gate; correlated gates are not blind POS multiply.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.structure_gates.growth import gate_k_growth
from geox_mcp.tools.structure_gates.k_dip import gate_k_dip
from geox_mcp.tools.structure_gates.k_dl import gate_k_dl
from geox_mcp.tools.structure_gates.k_throw import gate_k_throw
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
    "run_all_structure_gates",
]


def run_all_structure_gates(framework: dict[str, Any]) -> dict[str, Any]:
    """Run full structural gate matrix on a StructuralFramework-like dict."""
    gates = [
        ("K-DIP", gate_k_dip),
        ("K-THROW", gate_k_throw),
        ("K-DL", gate_k_dl),
        ("G2", gate_g2_topology),
        ("K-XCUT", gate_g2_topology),  # topology covers cross/cut; alias receipt
        ("K-RESTORE", gate_k_restore),
        ("K-VEL", gate_k_vel),
        ("K-GROWTH", gate_k_growth),
    ]
    results: dict[str, Any] = {}
    kills: list[str] = []
    passes: list[str] = []
    inconclusive: list[str] = []

    # Run unique callables once; alias G2/K-XCUT share topology
    seen_fn: set[int] = set()
    topology_result: dict[str, Any] | None = None
    for name, fn in gates:
        if fn is gate_g2_topology:
            if id(fn) not in seen_fn:
                topology_result = fn(framework)
                seen_fn.add(id(fn))
            r = topology_result or {"verdict": "INCONCLUSIVE", "reason": "topology not run"}
            if name == "K-XCUT":
                r = {**r, "gate": "K-XCUT", "alias_of": "G2"}
        else:
            r = fn(framework)
        results[name] = r
        v = r.get("verdict", "INCONCLUSIVE")
        if v == "KILL":
            kills.append(name)
        elif v == "PASS":
            passes.append(name)
        else:
            inconclusive.append(name)

    if kills:
        combined = "KILL"
    elif not passes and inconclusive:
        combined = "INCONCLUSIVE"
    elif passes and not kills:
        # Partial PASS: hard gates that ran may pass while soft stay inconclusive
        hard_names = {"K-DIP", "K-THROW", "G2", "K-RESTORE", "K-VEL"}
        hard_kills = [k for k in kills if k in hard_names]
        if hard_kills:
            combined = "KILL"
        elif any(results.get(h, {}).get("verdict") == "PASS" for h in ("K-DIP", "K-THROW")):
            combined = "PASS" if not inconclusive else "PARTIAL"
        else:
            combined = "INCONCLUSIVE"
    else:
        combined = "INCONCLUSIVE"

    return {
        "gates": results,
        "combined_verdict": combined,
        "kills": kills,
        "passes": passes,
        "inconclusive": inconclusive,
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "note": "Correlated gates — not blind POS product. KILL on any hard physics gate rejects model.",
    }
