"""Structural reconstruction: physics, five-axis verdicts, open Sabah fixtures.

The synthetic section is not a real line. Open fixtures carry published bounds
only. A BLOCKED timing axis is a successful refusal.
"""

from __future__ import annotations

import asyncio
import json
import math
from copy import deepcopy

import pytest

from geox_core.engines.structural_reconstruction.ledger import (
    benchmark_dir,
    dispatch_mode,
    evaluate,
    run_benchmark,
)
from geox_core.engines.structural_reconstruction.mcp_tool import register_structural_reconstruction
from geox_core.engines.structural_reconstruction.restoration import (
    depositional_thickness_m,
    extension_from_heave,
    lithology_params,
    sequential_decompaction,
    shear_to_paleoslope,
    solid_thickness_m,
    thickness_at_burial_m,
    unfaulted_datum_points,
)
from geox_mcp.surface_manifest import internal_tool_names, load_surface_manifest, public_tool_names

BENCH = benchmark_dir()
AXES = ("geometry", "timing", "driver", "igneous_identity", "regional_link")
FORBIDDEN_KEY_PARTS = ("probability", "percent", "confidence", "likelihood")


def _load(name: str) -> dict:
    return json.loads((BENCH / name).read_text(encoding="utf-8"))


def _primary() -> dict:
    return _load("fault_growth_synthetic.json")


def _keys(obj, found: list[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            found.append(str(key))
            _keys(value, found)
    elif isinstance(obj, list):
        for item in obj:
            _keys(item, found)


def test_decompaction_identity_and_unload() -> None:
    phi0, coeff = lithology_params("shale")
    present = 200.0
    z_top = 500.0
    solid = solid_thickness_m(present, z_top, phi0, coeff)
    recovered = thickness_at_burial_m(solid, z_top, phi0, coeff)
    assert abs(recovered - present) < 0.001
    unloaded = depositional_thickness_m(present, z_top + present, phi0, coeff)
    assert unloaded > present
    column = sequential_decompaction(
        [
            {"id": "H3_H2", "thickness_m": 180.0, "lithology": "shale"},
            {"id": "H2_H1", "thickness_m": 200.0, "lithology": "shale"},
        ]
    )
    buried = column["layers"][1]
    assert abs(buried["identity_thickness_m"] - buried["present_thickness_m"]) < 0.001
    assert column["paleobathymetry_added_to_burial"] is False
    assert column["steps"][0]["remaining"][0]["thickness_m"] > 200.0


def test_paleoslope_guard_refuses_flatten() -> None:
    points = unfaulted_datum_points(0, 10000, 5000, 0.03, 3000, "H1")
    guarded = shear_to_paleoslope(points, slope=0.03, z0=3000, datum_id="H1", force_flatten=True)
    assert guarded["status"] == "BLOCKED"
    assert guarded["coordinates_changed"] is False
    assert guarded["max_abs_shift_m"] == 0.0
    assert guarded["reason"] == "force_flatten_nonzero_paleoslope"


def test_extension_ratio_is_heave_over_restored_length() -> None:
    result = extension_from_heave(0, 10000, 800, 0.03)
    assert result["ok"] is True
    assert math.isclose(round(result["extension"], 12), 800 / 9200, rel_tol=1e-9)
    assert math.isclose(result["rigid_close_vertical_mismatch_m"], 24.0, abs_tol=1e-9)


def test_primary_splits_geometry_from_timing_and_requires_driver() -> None:
    receipt = evaluate(_primary())
    assert receipt["schema"] == "structural-reconstruction-1"
    assert receipt["legacy_k_restore"] == "NOT_USED"
    assert receipt["authorization_class"] == "SYNTHETIC"
    assert receipt["verdicts"]["geometry"] == "ADMISSIBLE"
    assert receipt["verdicts"]["timing"] == "BLOCKED"
    assert receipt["verdicts"]["driver"] == "REQUIRED_WITHIN_TESTED_SET"
    assert receipt["verdicts"]["igneous_identity"] == "UNRESOLVED"
    assert receipt["verdicts"]["regional_link"] == "UNRESOLVED"
    extension = receipt["measurements"]["extension"]["extension"]
    assert math.isclose(extension, 800 / 9200, rel_tol=1e-9)
    assert "overburden_above_shallowest_horizon" in receipt["missing_inputs"]
    assert receipt["measurements"]["paleoslope_guard"]["coordinates_changed"] is False


def test_missing_shale_does_not_become_crustal_extension() -> None:
    payload = _primary()
    payload["fixture_id"] = "unit_shale_missing"
    payload["mobile_shale"] = {"in_plane_m2": None, "out_of_plane_m2": None}
    receipt = evaluate(payload)
    material = receipt["measurements"]["material"]
    assert material["crustal_extension_area_m2"] is None
    assert material["shale_transfer_flagged"] is False
    assert receipt["verdicts"]["driver"] == "UNRESOLVED"
    assert "shale_not_declared" in receipt["reasons"]


def test_out_of_plane_shale_is_not_called_crustal_extension() -> None:
    receipt = evaluate(_load("shale_transfer.json"))
    material = receipt["measurements"]["material"]
    assert material["shale_transfer_flagged"] is True
    assert material["gap_area_m2"] == 280000
    assert material["crustal_extension_area_m2"] == 56000
    assert receipt["verdicts"]["driver"] == "NOT_REQUIRED_WITHIN_TESTED_SET"
    assert receipt["verdicts"]["geometry"] == "ADMISSIBLE"


def test_time_domain_blocks_metric_balance() -> None:
    receipt = evaluate(_load("time_domain.json"))
    assert receipt["verdicts"] == {axis: "BLOCKED" for axis in AXES}
    assert "time_domain_rejected_for_metric_balance" in receipt["reasons"]
    assert receipt["measurements"] is None


def test_labels_do_not_pass_timing_or_regional_meaning() -> None:
    collision = evaluate(_load("collision_label.json"))
    assert collision["verdicts"]["geometry"] == "ADMISSIBLE"
    assert collision["verdicts"]["regional_link"] == "BLOCKED"
    assert collision["verdicts"]["timing"] == "BLOCKED"
    assert "H_unconf_1=collision_onset" in collision["claims_refused"]
    spreading = evaluate(_load("post_spreading.json"))
    assert spreading["verdicts"]["timing"] == "BLOCKED"
    assert any("post-spreading" in item.lower() for item in spreading["claims_refused"])
    assert spreading["verdicts"]["geometry"] == "ADMISSIBLE"


def test_sensitivity_disagreement_does_not_use_the_grid_corner() -> None:
    receipt = evaluate(_load("sensitivity_shale.json"))
    assert receipt["verdicts"]["geometry"] == "ADMISSIBLE"
    assert receipt["verdicts"]["driver"] == "UNRESOLVED"
    assert receipt["measurements"]["material"]["out_of_plane_m2"] == 0
    assert receipt["sensitivity"]["cell_count"] == 2


def test_moho_gap_stays_unconstrained() -> None:
    receipt = evaluate(_load("moho_anchors_open.json"))
    assert receipt["verdicts"]["geometry"] == "ADMISSIBLE"
    assert receipt["verdicts"]["timing"] == "BLOCKED"
    assert receipt["moho_gap_state"] == "UNCONSTRAINED"
    assert receipt["interpolated"] is False
    assert receipt["values_inside_gap"] == []
    assert {anchor["id"] for anchor in receipt["anchors"]} == {"A_crocker", "A_central_sabah"}
    blocked = evaluate(_load("moho_gap_anchor_blocked.json"))
    assert blocked["verdicts"] == {axis: "BLOCKED" for axis in AXES}
    assert blocked["anchors"] == []
    assert blocked["values_inside_gap"] == []
    assert "A_gap_probe" not in json.dumps(blocked)
    refused = deepcopy(_load("moho_anchors_open.json"))
    refused["interpolate"] = True
    refused["fixture_id"] = "unit_moho_interpolate"
    refused_receipt = evaluate(refused)
    assert refused_receipt["verdicts"] == {axis: "BLOCKED" for axis in AXES}
    assert refused_receipt["interpolated"] is False
    assert "moho_interpolation_refused" in refused_receipt["reasons"]


def test_cornwell_and_open_constraints_are_not_kinematic_passes() -> None:
    cornwell = evaluate(_load("cornwell_slab_remnant.json"))
    assert cornwell["merged_into_crustal_anchors"] is False
    assert cornwell["kinematic_use"] is False
    assert cornwell["verdicts"]["geometry"] == "UNRESOLVED"
    assert cornwell["verdicts"]["igneous_identity"] == "UNRESOLVED"
    assert cornwell["verdicts"]["timing"] == "BLOCKED"
    opened = evaluate(_load("sabah_trough_open_constraints.json"))
    assert opened["kinematic_use"] is False
    assert opened["verdicts"]["geometry"] == "UNRESOLVED"
    assert opened["verdicts"]["timing"] == "BLOCKED"
    assert opened["cited_constraints"]["heat_flow"]["kinematic_use"] is False
    assert opened["cited_constraints"]["tmi"]["kinematic_use"] is False


def test_heat_flow_cannot_change_timing() -> None:
    plain = evaluate(_primary())
    payload = _primary()
    payload["fixture_id"] = "unit_heat_flow"
    payload["heat_flow"] = {
        "min_mW_m2": 54.4,
        "max_mW_m2": 89.3,
        "kinematic_use": True,
        "citation_status": "RANGE_SUPPLIED_AS_OPEN_CONSTRAINT",
        "doi": None,
    }
    heated = evaluate(payload)
    assert heated["verdicts"]["timing"] == plain["verdicts"]["timing"] == "BLOCKED"
    assert "heat_flow_kinematic_use_refused" in heated["claims_refused"]
    assert heated["cited_constraints"]["heat_flow"]["kinematic_use"] is False


def test_well_tied_bracket_is_admissible_and_still_refuses_the_label() -> None:
    payload = _primary()
    payload["fixture_id"] = "unit_bracket"
    payload["well_tied"] = True
    payload["timing_claim"] = "post-spreading"
    payload["age_brackets"] = {"age_min_ma": 10.0, "age_max_ma": 12.0, "source": "synthetic_bracket"}
    receipt = evaluate(payload)
    assert receipt["verdicts"]["timing"] == "ADMISSIBLE"
    assert any("post-spreading" in item.lower() for item in receipt["claims_refused"])


def test_igneous_label_needs_observables() -> None:
    label_only = _primary()
    label_only["fixture_id"] = "unit_igneous_label"
    label_only["igneous"] = {"label": "volcano"}
    blocked = evaluate(label_only)
    assert blocked["verdicts"]["igneous_identity"] == "BLOCKED"
    observed = _primary()
    observed["fixture_id"] = "unit_igneous_observed"
    observed["igneous"] = {"label": "volcano", "composition": "basalt", "age_ma": 12.0}
    admitted = evaluate(observed)
    assert admitted["verdicts"]["igneous_identity"] == "ADMISSIBLE"
    assert admitted["verdicts"]["timing"] == "BLOCKED"


def test_assumed_parameters_cannot_be_renamed_as_sabah_constants() -> None:
    payload = _primary()
    payload["fixture_id"] = "unit_assumed"
    payload["parameters"] = {"parameter_class": "NW_SABAH_CONSTANT", "growth_ratio_min": 1.2}
    receipt = evaluate(payload)
    assert "parameter_class_forced_assumed" in receipt["parameter_notes"]
    assert receipt["parameter_bounds"]["growth_ratio_min"]["parameter_class"] == "ASSUMED"
    assert receipt["parameter_bounds"]["growth_ratio_min"]["value"] == 1.2


def test_proprietary_payload_is_blocked_and_not_echoed() -> None:
    payload = _primary()
    payload["fixture_id"] = "unit_proprietary"
    payload["well_name"] = "SECRET-WELL-ALPHA"
    payload["line"] = "/root/private/line.sgy"
    receipt = evaluate(payload)
    assert receipt["verdicts"] == {axis: "BLOCKED" for axis in AXES}
    assert receipt["authorization_class"] == "SYNTHETIC"
    assert "well_name" in receipt["rejected_keys"]
    assert "line" in receipt["rejected_keys"]
    dumped = json.dumps(receipt)
    assert "SECRET-WELL-ALPHA" not in dumped
    assert "/root" not in dumped


def test_public_surface_stays_at_29() -> None:
    load_surface_manifest.cache_clear()
    public = public_tool_names()
    internal = internal_tool_names()
    assert len(public) == 29
    assert "geox_structural_reconstruction" not in public
    assert "geox_structural_reconstruction" in internal


def test_mcp_receipt_mode_returns_the_gate() -> None:
    class Fake:
        def __init__(self) -> None:
            self.tools = {}

        def tool(self, name, annotations=None):
            def decorate(fn):
                self.tools[name] = fn
                return fn

            return decorate

    fake = Fake()
    register_structural_reconstruction(fake)
    receipt = asyncio.run(
        fake.tools["geox_structural_reconstruction"](
            "receipt",
            json.dumps(_primary()),
        )
    )
    assert receipt["mode"] == "receipt"
    assert receipt["verdicts"]["geometry"] == "ADMISSIBLE"
    assert receipt["verdicts"]["timing"] == "BLOCKED"


def test_benchmark_is_deterministic_and_discipline_passes() -> None:
    first = run_benchmark(write=False)
    second = run_benchmark(write=False)
    assert first == second
    assert first["reality_discipline_pass"] is True
    assert first["failures"] == []
    assert first["authorization_classes"] == ["OPEN_SOURCE_PUBLIC", "SYNTHETIC"]
    assert first["verdicts"]["timing"] == "BLOCKED"
    assert first["verdicts"]["driver"] == "REQUIRED_WITHIN_TESTED_SET"
    keys: list[str] = []
    _keys(first, keys)
    assert not any(part in key.lower() for key in keys for part in FORBIDDEN_KEY_PARTS)
    dumped = json.dumps(first)
    assert "/root" not in dumped
    assert "kl2" not in dumped.lower()
    target = BENCH / "gate_receipt.json"
    written = run_benchmark(out_path=target, write=True)
    assert written["reality_discipline_pass"] is True
    on_disk = json.loads(target.read_text(encoding="utf-8"))
    assert on_disk == written


def test_dispatch_rejects_unknown_mode() -> None:
    receipt = dispatch_mode("seal")
    assert receipt["verdicts"]["geometry"] == "BLOCKED"
    assert "unknown_mode" in receipt["reasons"]


@pytest.mark.parametrize("name", ["fault_growth_synthetic.json", "moho_anchors_open.json"])
def test_fixture_files_have_no_private_path(name: str) -> None:
    text = (BENCH / name).read_text(encoding="utf-8")
    assert "/root" not in text
    assert "kl2" not in text.lower()
