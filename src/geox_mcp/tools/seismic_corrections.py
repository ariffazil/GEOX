"""
🌊 GEOX Human Correction Hook (PR-A4)

The interpreter drives the interpretation. GEOX accepts their corrections:

  - add_seeds               : add manual seed points (horizon / fault)
  - remove_segment          : discard an auto-proposed segment
  - join_faults / split_fault: editor actions on the fault network
  - mark_unconformity       : declare an erosional surface / hiatus
  - select_alternative      : pick a competing correlation
  - freeze_accepted_geometry: lock the current set as accepted
  - rerun_gates             : re-evaluate the structural matrix

Doctrine:
  - GEOX never overwrites human edits silently. Every correction leaves
    a receipt on the interpretation_bundle provenance.
  - Frozen geometry is the ONLY candidate allowed for arifOS SEAL.

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


def _hash_correction(action: str, payload: dict[str, Any]) -> str:
    raw = json.dumps({"action": action, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def add_seeds(
    framework: dict[str, Any],
    *,
    horizon_seeds: list[tuple[int, int]] | None = None,
    fault_seeds: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    fw = copy.deepcopy(framework)
    horizons = fw.setdefault("horizons", [])
    faults = fw.setdefault("faults", [])
    if horizon_seeds:
        horizons.append(
            {
                "horizon_id": f"H-seed-{len(horizons):04d}",
                "geometry": {"type": "manual_seed"},
                "seed_points": [[float(x), float(z)] for x, z in horizon_seeds],
                "tracker_method": "manual_seed",
                "provenance": {"added_by": "human", "correction": "add_seeds"},
            }
        )
    if fault_seeds:
        faults.append(
            {
                "fault_id": f"F-seed-{len(faults):04d}",
                "geometry": {"type": "manual_seed", "coordinate_system": "image"},
                "seed_points": [[float(x), float(z)] for x, z in fault_seeds],
                "provenance": {"added_by": "human", "correction": "add_seeds"},
            }
        )
    return {
        "framework": fw,
        "receipt": {
            "correction": "add_seeds",
            "n_horizon_seeds": len(horizon_seeds or []),
            "n_fault_seeds": len(fault_seeds or []),
            "receipt_hash": _hash_correction("add_seeds", {"h": len(horizon_seeds or []), "f": len(fault_seeds or [])}),
        },
    }


def remove_segment(framework: dict[str, Any], *, target_type: str, target_id: str) -> dict[str, Any]:
    fw = copy.deepcopy(framework)
    if target_type == "horizon":
        fw["horizons"] = [h for h in fw.get("horizons", []) if h.get("horizon_id") != target_id]
    elif target_type == "fault":
        fw["faults"] = [f for f in fw.get("faults", []) if f.get("fault_id") != target_id]
    else:
        raise ValueError(f"unknown target_type: {target_type}")
    return {
        "framework": fw,
        "receipt": {
            "correction": "remove_segment",
            "target_type": target_type,
            "target_id": target_id,
            "receipt_hash": _hash_correction("remove_segment", {"type": target_type, "id": target_id}),
        },
    }


def join_faults(framework: dict[str, Any], *, fault_ids: list[str]) -> dict[str, Any]:
    fw = copy.deepcopy(framework)
    faults = fw.get("faults", [])
    chosen = [f for f in faults if f.get("fault_id") in fault_ids]
    if len(chosen) < 2:
        raise ValueError("need ≥2 faults to join")
    head = chosen[0]
    for f in chosen[1:]:
        head.setdefault("merged_from", []).append(f.get("fault_id"))
        head["linkage_story"] = True
    fw["faults"] = [f for f in faults if f.get("fault_id") not in fault_ids[1:]]
    return {
        "framework": fw,
        "receipt": {
            "correction": "join_faults",
            "fault_ids": fault_ids,
            "receipt_hash": _hash_correction("join_faults", {"ids": fault_ids}),
        },
    }


def split_fault(framework: dict[str, Any], *, fault_id: str, at_xy: tuple[float, float]) -> dict[str, Any]:
    fw = copy.deepcopy(framework)
    faults = fw.get("faults", [])
    target = next((f for f in faults if f.get("fault_id") == fault_id), None)
    if target is None:
        raise ValueError(f"fault {fault_id} not found")
    new_fault = copy.deepcopy(target)
    new_fault["fault_id"] = f"{fault_id}-b"
    new_fault["split_from"] = fault_id
    target["fault_id"] = f"{fault_id}-a"
    target.setdefault("provenance", {})["split_at"] = list(at_xy)
    fw["faults"].append(new_fault)
    return {
        "framework": fw,
        "receipt": {
            "correction": "split_fault",
            "fault_id": fault_id,
            "at_xy": list(at_xy),
            "receipt_hash": _hash_correction("split_fault", {"id": fault_id, "at": list(at_xy)}),
        },
    }


def mark_unconformity(framework: dict[str, Any], *, horizon_id: str, surface_type: str) -> dict[str, Any]:
    fw = copy.deepcopy(framework)
    h = next((h for h in fw.get("horizons", []) if h.get("horizon_id") == horizon_id), None)
    if h is None:
        raise ValueError(f"horizon {horizon_id} not found")
    h.setdefault("relations", {})["surface_type"] = surface_type
    h["relations"]["truncates_below"] = True
    return {
        "framework": fw,
        "receipt": {
            "correction": "mark_unconformity",
            "horizon_id": horizon_id,
            "surface_type": surface_type,
            "receipt_hash": _hash_correction("mark_unconformity", {"id": horizon_id, "type": surface_type}),
        },
    }


def select_alternative(framework: dict[str, Any], *, horizon_id: str, alternative_id: str) -> dict[str, Any]:
    fw = copy.deepcopy(framework)
    h = next((h for h in fw.get("horizons", []) if h.get("horizon_id") == horizon_id), None)
    if h is None:
        raise ValueError(f"horizon {horizon_id} not found")
    h["selected_alternative"] = alternative_id
    h.setdefault("provenance", {})["accepted_by"] = "human"
    return {
        "framework": fw,
        "receipt": {
            "correction": "select_alternative",
            "horizon_id": horizon_id,
            "alternative_id": alternative_id,
            "receipt_hash": _hash_correction("select_alternative", {"id": horizon_id, "alt": alternative_id}),
        },
    }


def freeze_accepted_geometry(framework: dict[str, Any]) -> dict[str, Any]:
    fw = copy.deepcopy(framework)
    fw.setdefault("provenance", {})["frozen_at_iso"] = _now_iso()
    fw["provenance"]["accepted_by"] = "human_interpreter"
    fw["provenance"]["seal_eligible"] = True
    return {
        "framework": fw,
        "receipt": {
            "correction": "freeze_accepted_geometry",
            "frozen_at_iso": fw["provenance"]["frozen_at_iso"],
            "receipt_hash": _hash_correction("freeze_accepted_geometry", {"ts": fw["provenance"]["frozen_at_iso"]}),
        },
    }


def rerun_gates(framework: dict[str, Any], *, gates: list[str] | None = None) -> dict[str, Any]:
    from geox_mcp.tools.structure_gates import run_all_structure_gates

    matrix = run_all_structure_gates(framework)
    return {
        "framework": framework,
        "gate_matrix": matrix,
        "receipt": {
            "correction": "rerun_gates",
            "gates": gates or "all",
            "combined_verdict": matrix.get("combined_verdict"),
            "kills": matrix.get("kills"),
            "passes": matrix.get("passes"),
        },
    }


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "add_seeds",
    "freeze_accepted_geometry",
    "join_faults",
    "mark_unconformity",
    "remove_segment",
    "rerun_gates",
    "select_alternative",
    "split_fault",
]
