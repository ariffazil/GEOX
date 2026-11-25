"""Provenance ledger for one structural-reconstruction run.

K-RESTORE is not called. Its throw-sum length fallback stays in the locked
gate and is not a length. This ledger records legacy_k_restore = NOT_USED.

input_hash is SHA-256 of the resolved input. The receipt has no clock and
no calibrated probability.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from geox_core.engines.structural_reconstruction.restoration import EQUATIONS
from geox_core.engines.structural_reconstruction.younger_extension_gate import (
    VERDICT_AXES,
    histories_for_section,
    igneous_axis,
    regional_axis,
    timing_axis,
)

SCHEMA = "structural-reconstruction-1"
ALLOWED_AUTH = {"OPEN_SOURCE_PUBLIC", "SYNTHETIC"}
MODES = {"restore", "depth_sensitivity", "falsify_histories", "receipt", "benchmark"}
BANNED_KEYS = {
    "well_name",
    "seismic_path",
    "segy_path",
    "corporate_pick",
    "uwi",
    "corporate",
    "kl2",
    "latitude",
    "longitude",
    "lat",
    "lon",
    "easting",
    "northing",
}
FORBIDDEN_KEY_PARTS = ("probability", "percent", "confidence", "likelihood")
RATIO_KEYS = {
    "extension",
    "growth_ratio",
    "secant",
    "residual_extension",
    "depth_scale",
    "shale_explain_fraction",
    "growth_ratio_min",
    "heave_extension_min",
}
REQUIRED_FIXTURES = (
    "fault_growth_synthetic",
    "shale_transfer",
    "time_domain",
    "collision_label",
    "post_spreading",
    "sensitivity_shale",
    "moho_anchors_open",
    "moho_gap_anchor_blocked",
    "cornwell_slab_remnant",
    "sabah_trough_open_constraints",
)


def benchmark_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "benchmarks" / "sabah_basin_open"


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _hash(payload: dict) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _all(state: str) -> dict[str, str]:
    return {axis: state for axis in VERDICT_AXES}


def _round_tree(obj, key: str | None = None):
    if isinstance(obj, dict):
        return {str(k): _round_tree(v, str(k)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_tree(item, key) for item in obj]
    if isinstance(obj, float):
        if key in RATIO_KEYS:
            return round(obj, 12)
        if key and (key.endswith("_m") or key.endswith("_m2") or key.endswith("_km") or key.endswith("_nT")):
            return round(obj, 9)
    return obj


def _finite(obj) -> bool:
    if isinstance(obj, float):
        return math.isfinite(obj)
    if isinstance(obj, dict):
        return all(_finite(v) for v in obj.values())
    if isinstance(obj, list):
        return all(_finite(v) for v in obj)
    return True


def _scan(obj, bad: list[str], key: str | None = None) -> None:
    if isinstance(obj, dict):
        for raw_key, value in obj.items():
            name = str(raw_key)
            lowered = name.lower()
            if lowered in BANNED_KEYS or "kl2" in lowered:
                bad.append(name)
                continue
            if isinstance(value, str) and ("/root" in value or "kl2" in value.lower()):
                bad.append(name)
                continue
            _scan(value, bad, name)
        return
    if isinstance(obj, list):
        for item in obj:
            _scan(item, bad, key)
        return
    if isinstance(obj, str) and key is None and ("/root" in obj or "kl2" in obj.lower()):
        bad.append("value")


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    merged.pop("base_fixture", None)
    return merged


def _resolve(payload: dict, depth: int = 0) -> tuple[dict, list[str]]:
    if not isinstance(payload, dict):
        return {}, ["payload_not_object"]
    supplied = dict(payload)
    base_name = supplied.pop("base_fixture", None)
    if base_name is None:
        return supplied, []
    if depth >= 4:
        return supplied, ["base_fixture_too_deep"]
    if (
        not isinstance(base_name, str)
        or "/" in base_name
        or "\\" in base_name
        or ".." in base_name
        or not base_name.endswith(".json")
        or base_name.startswith(".")
    ):
        return supplied, ["base_fixture_rejected"]
    path = (benchmark_dir() / base_name).resolve()
    try:
        path.relative_to(benchmark_dir().resolve())
    except ValueError:
        return supplied, ["base_fixture_rejected"]
    if not path.is_file():
        return supplied, ["base_fixture_missing"]
    try:
        base = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return supplied, ["base_fixture_not_json"]
    resolved_base, nested = _resolve(base, depth + 1)
    if nested:
        return supplied, nested
    return _deep_merge(resolved_base, supplied), []


def _shell(reasons: list[str], fixture_id: str | None, auth: str | None, input_hash: str, rejected: list[str]) -> dict:
    return {
        "schema": SCHEMA,
        "fixture_id": fixture_id,
        "authorization_class": auth,
        "input_hash": input_hash,
        "input_hash_of": "resolved_payload",
        "legacy_k_restore": "NOT_USED",
        "float_round_decimals": {"lengths_m": 9, "ratios": 12},
        "verdicts": _all("BLOCKED"),
        "reasons": reasons,
        "claims_refused": [],
        "measurements": None,
        "missing_inputs": list(reasons),
        "residual_mismatches": [],
        "equations": EQUATIONS,
        "rejected_keys": rejected,
        "parameter_bounds": {},
        "sensitivity": {"cell_count": 0, "cells": []},
    }


def _auth(value: object) -> str | None:
    if not isinstance(value, str) or value not in ALLOWED_AUTH:
        return None
    return value


def _cited(payload: dict) -> dict:
    cited = {}
    for key in ("heat_flow", "tmi"):
        block = payload.get(key)
        if not isinstance(block, dict):
            continue
        copied = {name: item for name, item in block.items() if name != "kinematic_use"}
        copied["kinematic_use"] = False
        cited[key] = copied
    return cited


def _force_kinematic(payload: dict) -> tuple[dict, list[str]]:
    copied = json.loads(_canonical(payload))
    refused: list[str] = []
    for key, claim in (("heat_flow", "heat_flow_kinematic_use_refused"), ("tmi", "tmi_kinematic_use_refused")):
        block = copied.get(key)
        if isinstance(block, dict) and block.get("kinematic_use") is True:
            block["kinematic_use"] = False
            refused.append(claim)
    flex = copied.get("flexural_faults")
    if isinstance(flex, dict) and flex.get("kinematic_use") is True:
        flex["kinematic_use"] = False
        refused.append("flexural_faults_kinematic_use_refused")
    return copied, refused


def _moho(payload: dict) -> dict:
    gap = payload.get("moho_gap_km") or [230, 540]
    lo, hi = float(gap[0]), float(gap[1])
    anchors = list(payload.get("anchors") or [])
    in_gap = [
        anchor
        for anchor in anchors
        if isinstance(anchor, dict) and anchor.get("chainage_km") is not None and lo <= float(anchor["chainage_km"]) <= hi
    ]
    timing, timing_refused = timing_axis(payload)
    regional, regional_refused = regional_axis(payload)
    refused = timing_refused + regional_refused
    outside = []
    for anchor in anchors:
        if not isinstance(anchor, dict):
            continue
        chain = anchor.get("chainage_km")
        if chain is None or lo <= float(chain) <= hi:
            continue
        outside.append(
            {
                "id": anchor.get("id"),
                "chainage_km": anchor.get("chainage_km"),
                "depth_km": anchor.get("depth_km"),
                "attached": anchor.get("attached") is True,
                "source": anchor.get("source"),
            }
        )
    common = {
        "moho_gap_km": [lo, hi],
        "moho_gap_state": "UNCONSTRAINED",
        "interpolated": False,
        "values_inside_gap": [],
        "anchors": outside,
        "cited_constraints": {
            "crustal_thickness_km": payload.get("crustal_thickness_km"),
            "flexural_faults": payload.get("flexural_faults"),
        },
    }
    if in_gap or payload.get("interpolate") is True:
        reason = "moho_anchor_inside_unconstrained_gap" if in_gap else "moho_interpolation_refused"
        common["anchors"] = []
        return {
            "verdicts": _all("BLOCKED"),
            "reasons": [reason],
            "claims_refused": sorted(set(refused)),
            "measurements": None,
            "missing_inputs": [reason],
            "residual_mismatches": [],
            "parameter_bounds": {},
            "sensitivity": {"cell_count": 0, "cells": []},
            "equations": EQUATIONS,
            **common,
        }
    attached = any(isinstance(anchor, dict) and anchor.get("attached") is True for anchor in anchors)
    if not anchors:
        geometry = "UNRESOLVED"
        reasons = ["moho_anchors_missing"]
    elif attached:
        geometry = "BLOCKED"
        reasons = ["moho_anchor_marked_attached"]
    else:
        geometry = "ADMISSIBLE"
        reasons = []
    return {
        "verdicts": {
            "geometry": geometry,
            "timing": timing,
            "driver": "UNRESOLVED",
            "igneous_identity": igneous_axis(payload),
            "regional_link": regional,
        },
        "reasons": reasons,
        "claims_refused": sorted(set(refused)),
        "measurements": None,
        "missing_inputs": [] if anchors else ["moho_anchors"],
        "residual_mismatches": [],
        "parameter_bounds": {},
        "sensitivity": {"cell_count": 0, "cells": []},
        "equations": EQUATIONS,
        **common,
    }


def _mantle(payload: dict) -> dict:
    merged_requested = payload.get("merged_into_crustal_anchors") is True
    timing, timing_refused = timing_axis(payload)
    regional, regional_refused = regional_axis(payload)
    refused = list(timing_refused + regional_refused)
    if merged_requested:
        refused.append("mantle_context_merge_refused")
        verdicts = _all("BLOCKED")
        reasons = ["mantle_context_merge_refused"]
    else:
        verdicts = {
            "geometry": "UNRESOLVED",
            "timing": timing,
            "driver": "UNRESOLVED",
            "igneous_identity": igneous_axis(payload),
            "regional_link": regional,
        }
        reasons = ["cited_range_not_a_measured_body"]
    return {
        "verdicts": verdicts,
        "reasons": reasons,
        "claims_refused": sorted(set(refused)),
        "measurements": None,
        "missing_inputs": ["measured_body"],
        "residual_mismatches": [],
        "parameter_bounds": {},
        "sensitivity": {"cell_count": 0, "cells": []},
        "equations": EQUATIONS,
        "body_id": payload.get("body_id"),
        "depth_km_min": payload.get("depth_km_min"),
        "depth_km_max": payload.get("depth_km_max"),
        "dip": payload.get("dip"),
        "citation_status": payload.get("citation_status"),
        "doi": payload.get("doi"),
        "merged_into_crustal_anchors": False,
        "kinematic_use": False,
    }


def _open_constraints(payload: dict) -> dict:
    timing, timing_refused = timing_axis(payload)
    regional, regional_refused = regional_axis(payload)
    return {
        "verdicts": {
            "geometry": "UNRESOLVED",
            "timing": timing,
            "driver": "UNRESOLVED",
            "igneous_identity": igneous_axis(payload),
            "regional_link": regional,
        },
        "reasons": ["open_constraint_is_not_a_kinematic_section"],
        "claims_refused": sorted(set(timing_refused + regional_refused)),
        "measurements": None,
        "missing_inputs": [],
        "residual_mismatches": [],
        "parameter_bounds": {},
        "sensitivity": {"cell_count": 0, "cells": []},
        "equations": EQUATIONS,
        "kinematic_use": False,
    }


def _finish(payload: dict, body: dict, input_hash: str, extra_refused: list[str]) -> dict:
    auth = _auth(payload.get("authorization_class"))
    receipt = {
        "schema": SCHEMA,
        "fixture_id": payload.get("fixture_id"),
        "kind": payload.get("kind") or "section",
        "authorization_class": auth,
        "input_hash": input_hash,
        "input_hash_of": "resolved_payload",
        "legacy_k_restore": "NOT_USED",
        "float_round_decimals": {"lengths_m": 9, "ratios": 12},
        "verdicts": body["verdicts"],
        "reasons": body.get("reasons") or [],
        "claims_refused": sorted(set(list(body.get("claims_refused") or []) + extra_refused)),
        "measurements": body.get("measurements"),
        "missing_inputs": body.get("missing_inputs") or [],
        "residual_mismatches": body.get("residual_mismatches") or [],
        "equations": body.get("equations") or EQUATIONS,
        "parameter_bounds": body.get("parameter_bounds") or {},
        "parameter_notes": body.get("parameter_notes") or [],
        "sensitivity": body.get("sensitivity") or {"cell_count": 0, "cells": []},
        "rejected_keys": [],
    }
    for field in (
        "moho_gap_km",
        "moho_gap_state",
        "interpolated",
        "values_inside_gap",
        "anchors",
        "body_id",
        "depth_km_min",
        "depth_km_max",
        "dip",
        "citation_status",
        "doi",
        "merged_into_crustal_anchors",
        "kinematic_use",
    ):
        if field in body:
            receipt[field] = body[field]
    cited = _cited(payload)
    if "cited_constraints" in body or cited:
        base = dict(body.get("cited_constraints") or {})
        base.update(cited)
        receipt["cited_constraints"] = base
    receipt = _round_tree(receipt)
    _guard_receipt(receipt)
    return receipt


def _guard_receipt(receipt: dict) -> None:
    bad_keys: list[str] = []

    def walk(obj) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                lowered = str(key).lower()
                if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                    bad_keys.append(str(key))
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(receipt)
    if bad_keys:
        raise RuntimeError("forbidden_receipt_key:" + ",".join(sorted(set(bad_keys))))
    if "/root" in _canonical(receipt):
        raise RuntimeError("receipt_contains_private_path")


def evaluate(payload: dict) -> dict:
    """One fixture in, one gate receipt out. Bad physics returns BLOCKED."""
    if not isinstance(payload, dict):
        return _shell(["payload_not_object"], None, None, "", [])
    resolved, resolve_reasons = _resolve(payload)
    try:
        input_hash = _hash(resolved if not resolve_reasons else payload)
    except (TypeError, ValueError):
        return _shell(["payload_not_canonical"], payload.get("fixture_id") if isinstance(payload, dict) else None, None, "", [])
    if resolve_reasons:
        return _shell(resolve_reasons, payload.get("fixture_id"), _auth(payload.get("authorization_class")), input_hash, [])
    if not _finite(resolved):
        return _shell(["non_finite_number"], resolved.get("fixture_id"), _auth(resolved.get("authorization_class")), input_hash, [])
    rejected: list[str] = []
    _scan(resolved, rejected)
    rejected = sorted(set(rejected))
    auth = _auth(resolved.get("authorization_class"))
    if rejected or auth is None:
        reasons = []
        if auth is None:
            reasons.append("authorization_class_rejected")
        if rejected:
            reasons.append("proprietary_input_rejected")
        return _shell(reasons, resolved.get("fixture_id"), auth, input_hash, rejected)
    forced, extra_refused = _force_kinematic(resolved)
    kind = forced.get("kind") or "section"
    try:
        if kind == "section":
            body = histories_for_section(forced)
        elif kind == "moho":
            body = _moho(forced)
        elif kind == "mantle_context":
            body = _mantle(forced)
        elif kind == "open_constraints":
            body = _open_constraints(forced)
        else:
            body = {
                "verdicts": _all("BLOCKED"),
                "reasons": ["unknown_kind"],
                "claims_refused": [],
                "measurements": None,
                "missing_inputs": ["unknown_kind"],
                "residual_mismatches": [],
                "equations": EQUATIONS,
            }
    except (TypeError, ValueError, ZeroDivisionError, ArithmeticError) as exc:
        body = {
            "verdicts": _all("BLOCKED"),
            "reasons": [type(exc).__name__],
            "claims_refused": [],
            "measurements": None,
            "missing_inputs": [type(exc).__name__],
            "residual_mismatches": [],
            "equations": EQUATIONS,
        }
    return _finish(forced, body, input_hash, extra_refused)


def _material(receipt: dict | None) -> dict:
    if not receipt:
        return {}
    measurements = receipt.get("measurements") or {}
    material = measurements.get("material")
    return material if isinstance(material, dict) else {}


def _verdict(receipt: dict | None, axis: str):
    if not receipt:
        return None
    return (receipt.get("verdicts") or {}).get(axis)


def run_benchmark(out_path: Path | None = None, write: bool = False) -> dict:
    """Run every open fixture. Write gate_receipt.json only when the discipline holds."""
    directory = benchmark_dir()
    paths = sorted(path for path in directory.glob("*.json") if path.name != "gate_receipt.json")
    results: dict[str, dict] = {}
    hashed = []
    classes = set()
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        receipt = evaluate(payload)
        fixture_id = str(receipt.get("fixture_id") or path.stem)
        results[fixture_id] = receipt
        hashed.append({"fixture_id": fixture_id, "input_hash": receipt.get("input_hash")})
        if receipt.get("authorization_class") in ALLOWED_AUTH:
            classes.add(receipt["authorization_class"])
    hashed.sort(key=lambda item: item["fixture_id"])
    primary = results.get("fault_growth_synthetic")
    failures: list[str] = []
    for fixture_id in REQUIRED_FIXTURES:
        if fixture_id not in results:
            failures.append(f"missing_fixture:{fixture_id}")
    shale = _material(results.get("shale_transfer"))
    crustal = shale.get("crustal_extension_area_m2")
    gap = shale.get("gap_area_m2")
    shale_flagged = shale.get("shale_transfer_flagged") is True
    shale_not_full = (
        isinstance(crustal, (int, float)) and isinstance(gap, (int, float)) and crustal != gap and crustal < gap
    )
    moho = results.get("moho_anchors_open") or {}
    gap_case = results.get("moho_gap_anchor_blocked") or {}
    cornwell = results.get("cornwell_slab_remnant") or {}
    discipline = {
        "post_spreading_timing": _verdict(results.get("post_spreading"), "timing"),
        "collision_label_regional": _verdict(results.get("collision_label"), "regional_link"),
        "shale_transfer_flagged": shale_flagged,
        "shale_crustal_not_full_heave": shale_not_full,
        "moho_interpolated": moho.get("interpolated"),
        "moho_gap_state": moho.get("moho_gap_state"),
        "cornwell_merged_into_crustal_anchors": cornwell.get("merged_into_crustal_anchors"),
        "time_domain_geometry": _verdict(results.get("time_domain"), "geometry"),
        "sensitivity_driver": _verdict(results.get("sensitivity_shale"), "driver"),
        "moho_in_gap_blocked": bool(gap_case)
        and all(_verdict(gap_case, axis) == "BLOCKED" for axis in VERDICT_AXES)
        and gap_case.get("values_inside_gap") == []
        and gap_case.get("interpolated") is False,
    }
    expected = {
        "post_spreading_timing": "BLOCKED",
        "collision_label_regional": "BLOCKED",
        "shale_transfer_flagged": True,
        "shale_crustal_not_full_heave": True,
        "moho_interpolated": False,
        "moho_gap_state": "UNCONSTRAINED",
        "cornwell_merged_into_crustal_anchors": False,
        "time_domain_geometry": "BLOCKED",
        "sensitivity_driver": "UNRESOLVED",
        "moho_in_gap_blocked": True,
    }
    for key, value in expected.items():
        if discipline[key] != value:
            failures.append(key)
    if _verdict(primary, "geometry") != "ADMISSIBLE" or _verdict(primary, "timing") != "BLOCKED":
        failures.append("primary_geometry_timing_split")
    if _verdict(primary, "driver") != "REQUIRED_WITHIN_TESTED_SET":
        failures.append("primary_driver")
    if _verdict(results.get("sensitivity_shale"), "geometry") != "ADMISSIBLE":
        failures.append("sensitivity_geometry")
    if _verdict(results.get("shale_transfer"), "driver") != "NOT_REQUIRED_WITHIN_TESTED_SET":
        failures.append("shale_driver")
    if _verdict(results.get("collision_label"), "geometry") != "ADMISSIBLE":
        failures.append("collision_geometry")
    post = results.get("post_spreading") or {}
    if not any("post-spreading" in str(item).lower() for item in post.get("claims_refused") or []):
        failures.append("post_spreading_claim_not_refused")
    collision = results.get("collision_label") or {}
    if "H_unconf_1=collision_onset" not in (collision.get("claims_refused") or []):
        failures.append("collision_claim_not_refused")
    if moho.get("moho_gap_state") != "UNCONSTRAINED" or moho.get("interpolated") is not False:
        failures.append("moho_gap_not_preserved")
    if _verdict(moho, "timing") != "BLOCKED":
        failures.append("moho_timing")
    if cornwell.get("kinematic_use") is not False:
        failures.append("cornwell_kinematic_use")
    open_case = results.get("sabah_trough_open_constraints") or {}
    if open_case.get("kinematic_use") is not False or _verdict(open_case, "timing") != "BLOCKED":
        failures.append("open_constraints_not_kinematic")
    primary_measurements = (primary or {}).get("measurements") or {}
    fixtures = {}
    for fixture_id, receipt in sorted(results.items()):
        material = _material(receipt)
        fixtures[fixture_id] = {
            "input_hash": receipt.get("input_hash"),
            "authorization_class": receipt.get("authorization_class"),
            "kind": receipt.get("kind"),
            "verdicts": receipt.get("verdicts"),
            "claims_refused": receipt.get("claims_refused"),
            "shale_transfer_flagged": material.get("shale_transfer_flagged"),
            "crustal_extension_area_m2": material.get("crustal_extension_area_m2"),
            "gap_area_m2": material.get("gap_area_m2"),
            "moho_gap_state": receipt.get("moho_gap_state"),
            "interpolated": receipt.get("interpolated"),
            "merged_into_crustal_anchors": receipt.get("merged_into_crustal_anchors"),
        }
    aggregate = {
        "schema": SCHEMA,
        "benchmark_id": "sabah_basin_open",
        "authorization_class": "SYNTHETIC",
        "authorization_classes": sorted(classes),
        "primary_fixture": "fault_growth_synthetic",
        "input_hash": _hash({"fixtures": hashed}),
        "input_hash_of": "fixture_ids_and_hashes",
        "legacy_k_restore": "NOT_USED",
        "float_round_decimals": {"lengths_m": 9, "ratios": 12},
        "verdicts": (primary or {}).get("verdicts"),
        "claims_refused": (primary or {}).get("claims_refused"),
        "extension": primary_measurements.get("extension"),
        "equations": (primary or {}).get("equations") or EQUATIONS,
        "material": primary_measurements.get("material"),
        "parameter_bounds": (primary or {}).get("parameter_bounds"),
        "residual_mismatches": (primary or {}).get("residual_mismatches"),
        "missing_inputs": (primary or {}).get("missing_inputs"),
        "fixtures": fixtures,
        "reality_discipline": discipline,
        "reality_discipline_pass": not failures,
        "failures": failures,
    }
    aggregate = _round_tree(aggregate)
    _guard_receipt(aggregate)
    if write and not failures:
        target = Path(out_path) if out_path is not None else directory / "gate_receipt.json"
        target.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return aggregate


def dispatch_mode(mode: str, payload_json: str = "{}") -> dict:
    """MCP entry. Every mode returns the full receipt. Benchmark does not write."""
    if mode not in MODES:
        receipt = _shell(["unknown_mode"], None, None, "", [])
        receipt["mode"] = str(mode)
        return receipt
    if mode == "benchmark":
        receipt = run_benchmark(write=False)
        receipt["mode"] = mode
        return receipt
    try:
        payload = json.loads(payload_json or "{}")
    except json.JSONDecodeError:
        receipt = _shell(["payload_json_not_json"], None, None, "", [])
        receipt["mode"] = mode
        return receipt
    if not isinstance(payload, dict):
        receipt = _shell(["payload_not_object"], None, None, "", [])
        receipt["mode"] = mode
        return receipt
    receipt = evaluate(payload)
    receipt["mode"] = mode
    return receipt
