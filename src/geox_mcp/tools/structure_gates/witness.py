"""Multi-witness geometry intake (FIX BRIEF v2 · P7).

Register external hypothesis bundles (ChatGPT, Claude, classical-CV, human)
under one Section so gates attack all witnesses symmetrically.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from geox_mcp.tools.structure_gates.geometry_adapt import adapt_framework_geometry


def register_witnesses(
    section_framework: dict[str, Any] | None,
    witnesses: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Return list of {witness_id, source, framework} for symmetric gating."""
    out: list[dict[str, Any]] = []
    if section_framework and (section_framework.get("faults") or section_framework.get("horizons")):
        fw = adapt_framework_geometry(deepcopy(section_framework))
        for f in fw.get("faults") or []:
            if isinstance(f, dict):
                f.setdefault("witness", "primary")
        out.append({"witness_id": "W-primary", "source": "primary", "framework": fw})
    for i, w in enumerate(witnesses or []):
        if not isinstance(w, dict):
            continue
        src = str(w.get("source") or w.get("witness") or f"witness_{i}")
        fw = dict(w.get("framework") or {})
        if w.get("faults") is not None:
            fw["faults"] = w["faults"]
        if w.get("horizons") is not None:
            fw["horizons"] = w["horizons"]
        if w.get("calibration") is not None:
            fw["calibration"] = w["calibration"]
        fw = adapt_framework_geometry(fw)
        for f in fw.get("faults") or []:
            if isinstance(f, dict):
                f["witness"] = src
        out.append(
            {
                "witness_id": w.get("hypothesis_id") or f"W-{src}-{i}",
                "source": src,
                "framework": fw,
            }
        )
    return out


def gate_all_witnesses(
    witnesses: list[dict[str, Any]],
    calibration: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run structure gates on each witness framework independently."""
    from geox_mcp.tools.section_render import compact_gate_summary
    from geox_mcp.tools.structure_gates import run_all_structure_gates
    from geox_mcp.tools.structure_gates.cutoff import derive_cutoff_pairs

    results = []
    for w in witnesses:
        fw = dict(w.get("framework") or {})
        if calibration:
            fw["calibration"] = {**(fw.get("calibration") or {}), **calibration}
        matrix = run_all_structure_gates(fw)
        gsum = compact_gate_summary(matrix.get("gates") or {})
        cutoffs = derive_cutoff_pairs(fw.get("faults") or [], fw.get("horizons") or [])
        results.append(
            {
                "witness_id": w.get("witness_id"),
                "source": w.get("source"),
                "combined_gate_verdict": matrix.get("combined_verdict"),
                "gate_summary": {
                    "pass": len(gsum.get("passes") or []),
                    "warn": len(gsum.get("warns") or []),
                    "kill": len(gsum.get("kills") or []),
                    "unmeasured": len(gsum.get("unmeasured") or []),
                },
                "kills": matrix.get("kills"),
                "passes": matrix.get("passes"),
                "cutoffs_n": len(cutoffs),
                "n_faults": len(fw.get("faults") or []),
                "n_horizons": len(fw.get("horizons") or []),
                "local_verdict": "QUALIFIED_CANDIDATE",
            }
        )
    return results
