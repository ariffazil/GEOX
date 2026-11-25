"""Three kinematic histories, five decoupled verdicts.

A geometry pass does not write the timing, driver, igneous, or regional axis.
No axis emits a calibrated probability.
"""

from __future__ import annotations

from geox_core.engines.structural_reconstruction.depth_sensitivity import (
    domain_precheck,
    grid_axes,
    scaled_section,
)
from geox_core.engines.structural_reconstruction.restoration import (
    EQUATIONS,
    extension_from_heave,
    faulted_datum_points,
    growth_observation,
    restore_fault_points,
    sequential_decompaction,
    shale_account,
    shear_to_paleoslope,
    unfaulted_datum_points,
)

VERDICT_AXES = ("geometry", "timing", "driver", "igneous_identity", "regional_link")
ASSUMED_DEFAULTS = {
    "growth_ratio_min": 1.15,
    "heave_extension_min": 0.02,
    "shale_explain_fraction": 0.8,
}
LABEL_ONLY = {"volcano", "rift", "collision", "dru"}


def assumed_parameters(payload: dict) -> tuple[dict, list[str]]:
    """Caller numbers are allowed. Their class is forced to ASSUMED."""
    supplied = payload.get("parameters") if isinstance(payload.get("parameters"), dict) else {}
    notes: list[str] = []
    if str(supplied.get("parameter_class", "")).upper() == "NW_SABAH_CONSTANT":
        notes.append("parameter_class_forced_assumed")
    bounds = {}
    for key, default in ASSUMED_DEFAULTS.items():
        value = supplied.get(key, default)
        bounds[key] = {"value": float(value), "parameter_class": "ASSUMED"}
    return bounds, notes


def _all(state: str) -> dict[str, str]:
    return {axis: state for axis in VERDICT_AXES}


def _brackets_complete(brackets: object) -> bool:
    if not isinstance(brackets, dict):
        return False
    return (
        brackets.get("age_min_ma") is not None
        and brackets.get("age_max_ma") is not None
        and bool(brackets.get("source"))
    )


def timing_axis(payload: dict) -> tuple[str, list[str]]:
    """Missing well-tied brackets are BLOCKED. A bracket is not a process age.

    The string post-spreading is refused even when a bracket is present.
    """
    refused: list[str] = []
    claim = payload.get("timing_claim")
    if isinstance(claim, str) and "post-spreading" in claim.lower():
        refused.append(claim)
    well_tied = payload.get("well_tied") is True
    if not well_tied or not _brackets_complete(payload.get("age_brackets")):
        return "BLOCKED", refused
    return "ADMISSIBLE", refused


def igneous_axis(payload: dict) -> str:
    body = payload.get("igneous")
    if body is None:
        return "UNRESOLVED"
    if not isinstance(body, dict):
        return "BLOCKED"
    label = str(body.get("label", "")).lower()
    composition = body.get("composition")
    age = body.get("age_ma")
    has_observables = bool(composition) and age is not None
    if label in LABEL_ONLY and not has_observables:
        return "BLOCKED"
    if has_observables:
        return "ADMISSIBLE"
    return "UNRESOLVED"


def regional_axis(payload: dict) -> tuple[str, list[str]]:
    claims = payload.get("regional_claims") or []
    if not isinstance(claims, list) or len(claims) == 0:
        return "UNRESOLVED", []
    refused: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            return "BLOCKED", ["regional_claim_not_object"]
        equated = str(claim.get("equated_to", ""))
        horizon = str(claim.get("horizon_id", ""))
        proof = claim.get("structural_proof") is True
        independent = claim.get("independent_structural_observation") is True
        if equated == "collision_onset" and not (proof and independent):
            refused.append(f"{horizon}=collision_onset")
    if refused:
        return "BLOCKED", refused
    return "ADMISSIBLE", []


def _numbers(payload: dict) -> dict | None:
    pins = payload.get("pins_m")
    fault = payload.get("fault")
    if not isinstance(pins, dict) or not isinstance(fault, dict):
        return None
    needed = ("x_min", "x_max")
    fault_needed = ("trace_x_m", "heave_m", "throw_m")
    if any(pins.get(key) is None for key in needed):
        return None
    if any(fault.get(key) is None for key in fault_needed):
        return None
    return {
        "x_min": float(pins["x_min"]),
        "x_max": float(pins["x_max"]),
        "trace": float(fault["trace_x_m"]),
        "heave": float(fault["heave_m"]),
        "throw": float(fault["throw_m"]),
    }


def evaluate_cell(payload: dict, bounds: dict) -> dict:
    """One grid cell. Domain admission is the caller's job."""
    growth_min = float(bounds["growth_ratio_min"]["value"])
    extension_min = float(bounds["heave_extension_min"]["value"])
    explain_fraction = float(bounds["shale_explain_fraction"]["value"])
    depth_scale = float(payload.get("_depth_scale", 1.0))
    missing: list[str] = []
    residuals: list[dict] = []

    if depth_scale <= 0:
        return {
            "verdicts": _all("BLOCKED"),
            "reasons": ["invalid_depth_scale"],
            "measurements": None,
            "missing_inputs": missing,
            "residual_mismatches": residuals,
            "claims_refused": [],
        }

    timing, timing_refused = timing_axis(payload)
    igneous = igneous_axis(payload)
    regional, regional_refused = regional_axis(payload)
    claims_refused = timing_refused + regional_refused

    slope = payload.get("paleoslope")
    datum = payload.get("datum_z0_m")
    datum_id = payload.get("datum_horizon_id")
    if slope is None:
        missing.append("paleoslope")
    if datum is None:
        missing.append("datum_z0_m")
    if not datum_id:
        missing.append("datum_horizon_id")

    geometry = "ADMISSIBLE"
    reasons: list[str] = []
    if payload.get("force_flatten") is True and slope not in (None, 0, 0.0):
        geometry = "BLOCKED"
        reasons.append("force_flatten_nonzero_paleoslope")

    nums = _numbers(payload)
    growth = growth_observation(list(payload.get("intervals") or []))
    intervals = list(payload.get("intervals") or [])
    if growth is None and not intervals:
        missing.append("growth_interval")
    elif growth is None and intervals:
        # Thicknesses were supplied and none of them change across the fault.
        drape = intervals[0]
        growth = {
            "id": str(drape.get("id", "")),
            "fw_thickness_m": float(drape["fw_thickness_m"]),
            "hw_thickness_m": float(drape["hw_thickness_m"]),
            "growth_ratio": 1.0,
            "lithology": str(drape.get("lithology", "generic")),
            "differential": False,
        }
    if isinstance(growth, dict) and "differential" not in growth:
        growth["differential"] = True

    if nums is None or growth is None:
        if geometry != "BLOCKED":
            geometry = "BLOCKED" if nums is None else "UNRESOLVED"
        if nums is None:
            reasons.append("fault_or_pins_missing")
            missing.append("fault_or_pins")
        driver = "UNRESOLVED"
        return {
            "verdicts": {
                "geometry": geometry,
                "timing": timing,
                "driver": driver,
                "igneous_identity": igneous,
                "regional_link": regional,
            },
            "reasons": reasons,
            "measurements": None,
            "missing_inputs": missing,
            "residual_mismatches": residuals,
            "claims_refused": claims_refused,
        }

    lateral = payload.get("lateral_uncertainty_m")
    pick_unresolved = lateral is not None and float(lateral) > nums["heave"]
    if slope is None or datum is None or not datum_id:
        geometry = "UNRESOLVED"
        reasons.append("datum_incomplete")

    extension = None
    guard = None
    fault_slip = None
    decompaction = None
    material = None
    if slope is not None and geometry != "BLOCKED":
        extension = extension_from_heave(nums["x_min"], nums["x_max"], nums["heave"], float(slope))
        if not extension["ok"]:
            geometry = "BLOCKED"
            reasons.append(extension["reason"])
            extension = None
        else:
            residuals.append(
                {
                    "id": "rigid_close_vertical_mismatch",
                    "value_m": extension["rigid_close_vertical_mismatch_m"],
                    "meaning": "slope * heave after a rigid hanging-wall translation",
                }
            )
            guard = shear_to_paleoslope(
                unfaulted_datum_points(
                    nums["x_min"], nums["x_max"], nums["trace"], float(slope), float(datum or 0.0), str(datum_id)
                ),
                slope=float(slope),
                z0=float(datum or 0.0),
                datum_id=str(datum_id),
                force_flatten=bool(payload.get("force_flatten") is True),
            )
            if guard["status"] == "BLOCKED":
                geometry = "BLOCKED"
                reasons.append(guard["reason"])
            faulted = faulted_datum_points(
                nums["x_min"],
                nums["x_max"],
                nums["trace"],
                nums["heave"],
                nums["throw"],
                float(slope),
                float(datum or 0.0),
                str(datum_id),
            )
            fault_slip = {
                "dx_m": -nums["heave"] if str(payload["fault"].get("hanging_wall", "x_greater")) == "x_greater" else nums["heave"],
                "dz_m": -nums["throw"] if str(payload["fault"].get("sense", "normal")) == "normal" else nums["throw"],
                "points": restore_fault_points(faulted, payload["fault"]),
            }
    if pick_unresolved and geometry == "ADMISSIBLE":
        geometry = "UNRESOLVED"
        reasons.append("lateral_uncertainty_exceeds_heave")

    shale = payload.get("mobile_shale") if isinstance(payload.get("mobile_shale"), dict) else {}
    in_plane = shale.get("in_plane_m2") if isinstance(shale, dict) else None
    out_plane = shale.get("out_of_plane_m2") if isinstance(shale, dict) else None
    material = shale_account(
        nums["heave"],
        float(growth["fw_thickness_m"]),
        float(growth["hw_thickness_m"]),
        None if in_plane is None else float(in_plane),
        None if out_plane is None else float(out_plane),
        explain_fraction,
    )
    if material["shale_missing"]:
        missing.append("mobile_shale")

    decompaction = _relative_decompaction(payload, growth)
    if decompaction.get("overburden_above_shallowest_horizon_m") is None:
        missing.append("overburden_above_shallowest_horizon")

    extension_value = None if extension is None else float(extension["extension"])
    flexural_removes = (
        extension_value is not None
        and slope not in (None, 0, 0.0)
        and abs(extension_value) < extension_min
    )
    growth_ratio = float(growth["growth_ratio"])
    large_growth = growth_ratio >= growth_min
    large_extension = extension_value is not None and extension_value > extension_min
    shale_explains = material["explains_gap"] is True
    both_below = (not large_growth) and extension_value is not None and abs(extension_value) <= extension_min

    if geometry == "BLOCKED":
        driver = "BLOCKED"
    elif growth is None or nums is None:
        driver = "UNRESOLVED"
    elif material["shale_missing"] and large_growth and large_extension:
        driver = "UNRESOLVED"
        reasons.append("shale_not_declared")
    elif shale_explains or flexural_removes or both_below:
        driver = "NOT_REQUIRED_WITHIN_TESTED_SET"
    elif large_growth and large_extension and not material["shale_missing"] and not shale_explains and not flexural_removes:
        driver = "REQUIRED_WITHIN_TESTED_SET"
    elif pick_unresolved:
        driver = "UNRESOLVED"
    else:
        driver = "ADMISSIBLE"

    if pick_unresolved and driver not in {"BLOCKED", "UNRESOLVED"}:
        driver = "UNRESOLVED"

    histories = {
        "inherited_flexural": {
            "removes_heave": bool(flexural_removes),
            "residual_extension": extension_value,
        },
        "mobile_shale": {
            "explains_gap": material["explains_gap"],
            "shale_transfer_flagged": material["shale_transfer_flagged"],
            "accounted_m2": material["accounted_m2"],
            "gap_area_m2": material["gap_area_m2"],
        },
        "younger_extension": {
            "growth_ratio": growth_ratio,
            "extension": extension_value,
            "thresholds_passed": bool(
                large_growth and large_extension and not material["shale_missing"] and not shale_explains and not flexural_removes
            ),
        },
    }
    return {
        "verdicts": {
            "geometry": geometry,
            "timing": timing,
            "driver": driver,
            "igneous_identity": igneous,
            "regional_link": regional,
        },
        "reasons": reasons,
        "measurements": {
            "extension": extension,
            "growth": growth,
            "material": material,
            "paleoslope_guard": _public_guard(guard),
            "fault_slip": _public_slip(fault_slip),
            "decompaction": decompaction,
            "histories": histories,
        },
        "missing_inputs": missing,
        "residual_mismatches": residuals,
        "claims_refused": claims_refused,
    }


def _public_guard(guard: dict | None) -> dict | None:
    if guard is None:
        return None
    points = [
        {"id": point["id"], "x_m": round(point["x_m"], 9), "z_m": round(point["z_m"], 9)}
        for point in guard["points"]
    ]
    return {
        "status": guard["status"],
        "reason": guard["reason"],
        "max_abs_shift_m": round(float(guard["max_abs_shift_m"]), 9),
        "coordinates_changed": guard["coordinates_changed"],
        "points": points,
    }


def _public_slip(slip: dict | None) -> dict | None:
    if slip is None:
        return None
    return {
        "dx_m": round(float(slip["dx_m"]), 9),
        "dz_m": round(float(slip["dz_m"]), 9),
        "points": [
            {"id": point["id"], "x_m": round(point["x_m"], 9), "z_m": round(point["z_m"], 9)}
            for point in slip["points"]
        ],
    }


def _relative_decompaction(payload: dict, growth: dict) -> dict:
    """Stack supplied intervals from the shallowest horizon downward.

    Depths of the paleoslope datum are not treated as sedimentary burial.
    """
    layers = []
    for interval in payload.get("intervals") or []:
        layers.append(
            {
                "id": str(interval.get("id")),
                "thickness_m": float(interval["fw_thickness_m"]),
                "lithology": str(interval.get("lithology", growth.get("lithology", "generic"))),
            }
        )
    # Youngest last in the payload is not guaranteed. The list is top to base
    # when the caller ordered it that way (H3-H2 then H2-H1). Keep caller order.
    try:
        result = sequential_decompaction(layers)
    except (ValueError, ZeroDivisionError) as exc:
        return {"status": "UNRESOLVED", "reason": str(exc), "overburden_above_shallowest_horizon_m": None}
    result["status"] = "COMPUTED_RELATIVE_TO_SHALLOWEST_HORIZON"
    result["overburden_above_shallowest_horizon_m"] = None
    result["growth_interval_id"] = growth.get("id")
    return result


def aggregate_cells(cells: list[dict]) -> dict[str, str]:
    verdicts: dict[str, str] = {}
    for axis in VERDICT_AXES:
        values = [cell["verdicts"][axis] for cell in cells]
        if all(value == "BLOCKED" for value in values):
            verdicts[axis] = "BLOCKED"
            continue
        live = [value for value in values if value != "BLOCKED"]
        verdicts[axis] = live[0] if len(set(live)) == 1 else "UNRESOLVED"
    return verdicts


def histories_for_section(payload: dict) -> dict:
    """Full five-axis receipt body for one section payload. No hash yet."""
    status, reasons = domain_precheck(payload)
    bounds, class_notes = assumed_parameters(payload)
    if status == "BLOCKED":
        timing, timing_refused = timing_axis(payload)
        # A domain block refuses metric balancing on every axis. Timing's own
        # reason is kept in claims_refused, and the axis itself is BLOCKED.
        del timing
        regional, regional_refused = regional_axis(payload)
        del regional
        return {
            "verdicts": _all("BLOCKED"),
            "reasons": reasons,
            "parameter_bounds": bounds,
            "parameter_notes": class_notes,
            "measurements": None,
            "missing_inputs": reasons,
            "residual_mismatches": [],
            "claims_refused": sorted(set(timing_refused + regional_refused)),
            "sensitivity": {"cell_count": 0, "cells": []},
            "equations": EQUATIONS,
        }
    axes = grid_axes(payload)
    if isinstance(axes, str):
        return {
            "verdicts": _all("BLOCKED"),
            "reasons": [axes],
            "parameter_bounds": bounds,
            "parameter_notes": class_notes,
            "measurements": None,
            "missing_inputs": [axes],
            "residual_mismatches": [],
            "claims_refused": [],
            "sensitivity": {"cell_count": 0, "cells": []},
            "equations": EQUATIONS,
        }
    scales, slopes, shale_outs, laterals = axes
    cells = []
    for scale in scales:
        for slope in slopes:
            for shale_out in shale_outs:
                for lateral in laterals:
                    if scale <= 0:
                        cell = {
                            "verdicts": _all("BLOCKED"),
                            "reasons": ["invalid_depth_scale"],
                            "measurements": None,
                            "missing_inputs": [],
                            "residual_mismatches": [],
                            "claims_refused": [],
                        }
                    else:
                        section = scaled_section(payload, scale, slope, shale_out, lateral)
                        cell = evaluate_cell(section, bounds)
                    cells.append(
                        {
                            "depth_scale": scale,
                            "paleoslope": slope,
                            "mobile_shale_out_of_plane_m2": shale_out,
                            "lateral_uncertainty_m": lateral,
                            "body": cell,
                        }
                    )
    official = aggregate_cells([item["body"] for item in cells])
    # The stated payload, not an extreme grid corner, supplies the measurements.
    stated_scale = float(payload["velocity_realizations"][0]["depth_scale"])
    stated = scaled_section(
        payload,
        stated_scale,
        None if payload.get("paleoslope") is None else float(payload["paleoslope"]),
        _stated_shale_out(payload),
        None if payload.get("lateral_uncertainty_m") is None else float(payload["lateral_uncertainty_m"]),
    )
    if stated_scale <= 0:
        stated_body = cells[0]["body"]
    else:
        stated_body = evaluate_cell(stated, bounds)
    missing = sorted(set(stated_body["missing_inputs"] + class_notes))
    compact_cells = [
        {
            "depth_scale": item["depth_scale"],
            "paleoslope": item["paleoslope"],
            "mobile_shale_out_of_plane_m2": item["mobile_shale_out_of_plane_m2"],
            "lateral_uncertainty_m": item["lateral_uncertainty_m"],
            "verdicts": item["body"]["verdicts"],
        }
        for item in cells
    ]
    return {
        "verdicts": official,
        "reasons": stated_body["reasons"],
        "parameter_bounds": bounds,
        "parameter_notes": class_notes,
        "measurements": stated_body["measurements"],
        "missing_inputs": missing,
        "residual_mismatches": stated_body["residual_mismatches"],
        "claims_refused": sorted(set(stated_body["claims_refused"])),
        "sensitivity": {"cell_count": len(cells), "cells": compact_cells},
        "equations": EQUATIONS,
    }


def _stated_shale_out(payload: dict) -> float | None:
    shale = payload.get("mobile_shale")
    if not isinstance(shale, dict) or shale.get("out_of_plane_m2") is None:
        return None
    return float(shale["out_of_plane_m2"])
