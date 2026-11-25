"""Young-to-old restoration on neutral horizon and fault ids.

Porosity reuses the Athy / Sclater-Christie functions already in
backstrip_decompaction. Lengths are never invented from a throw list.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import root_scalar

from geox_core.skills.subsurface.backstrip_decompaction import (
    GEOS_POROSITY_DEPTH,
    average_porosity,
    decompact_thickness,
)

EQUATIONS = {
    "porosity": "phi(z) = phi0 * exp(-c * z)",
    "solid": "T_solid = T_present * (1 - phi_bar)",
    "depositional_thickness": "T0 = T_solid / (1 - phi0)",
    "extension": "(L_deformed - L_restored) / L_restored",
}


def lithology_params(name: str) -> tuple[float, float]:
    entry = GEOS_POROSITY_DEPTH.get(str(name).lower(), GEOS_POROSITY_DEPTH["generic"])
    return float(entry["phi0"]), float(entry["c_per_km"])


def solid_thickness_m(thickness_m: float, z_top_m: float, phi0: float, c_per_km: float) -> float:
    if thickness_m <= 0:
        raise ValueError("thickness_m must be > 0")
    if z_top_m < 0:
        raise ValueError("z_top_m must be >= 0")
    z_top_km = z_top_m / 1000.0
    z_base_km = (z_top_m + thickness_m) / 1000.0
    phi_bar = average_porosity(z_top_km, z_base_km, phi0, c_per_km)
    return float(thickness_m * (1.0 - phi_bar))


def thickness_at_burial_m(solid_m: float, z_top_m: float, phi0: float, c_per_km: float) -> float:
    """Thickness at sediment burial z_top whose conserved solid equals solid_m."""
    if solid_m <= 0:
        raise ValueError("solid_m must be > 0")
    if z_top_m < 0:
        raise ValueError("z_top_m must be >= 0")

    def residual(thickness: float) -> float:
        return solid_thickness_m(thickness, z_top_m, phi0, c_per_km) - solid_m

    lo = max(float(solid_m), 1e-6)
    hi = float(solid_m) / max(1e-6, (1.0 - phi0)) * 2.0
    if residual(hi) < 0.0:
        hi = max(hi * 4.0, lo + 1.0)
    root = root_scalar(residual, bracket=[lo, hi], xtol=1e-9)
    return float(root.root)


def depositional_thickness_m(
    present_thickness_m: float,
    present_base_depth_m: float,
    phi0: float,
    c_per_km: float,
) -> float:
    """Fully unloaded thickness. Same code path as decompact_thickness."""
    return float(
        decompact_thickness(
            present_thickness_m,
            present_base_depth_m,
            phi0=phi0,
            c_per_km=c_per_km,
        )
    )


def sequential_decompaction(layers: list[dict]) -> dict:
    """Strip youngest first.

    z is depth below the remaining sediment top. Paleobathymetry is not added.
    Solid thickness is conserved. A layer moved to the surface uses the
    Sclater-Christie depositional thickness; a layer that stays buried is
    solved by bisection at the new z_top.
    """
    column: list[dict] = []
    z_top = 0.0
    for layer in layers:
        thickness = float(layer["thickness_m"])
        phi0, c_per_km = lithology_params(str(layer.get("lithology", "generic")))
        solid = solid_thickness_m(thickness, z_top, phi0, c_per_km)
        identity = thickness_at_burial_m(solid, z_top, phi0, c_per_km)
        column.append(
            {
                "id": str(layer["id"]),
                "lithology": str(layer.get("lithology", "generic")),
                "phi0": phi0,
                "c_per_km": c_per_km,
                "solid_m": solid,
                "present_z_top_m": z_top,
                "present_thickness_m": thickness,
                "identity_thickness_m": identity,
                "current_z_top_m": z_top,
                "current_thickness_m": thickness,
            }
        )
        z_top += thickness

    steps: list[dict] = []
    active = column
    while len(active) > 1:
        removed = active[0]
        shift = float(removed["current_thickness_m"])
        updated: list[dict] = []
        reported: list[dict] = []
        for rec in active[1:]:
            new_top = max(0.0, float(rec["current_z_top_m"]) - shift)
            phi0 = float(rec["phi0"])
            c_per_km = float(rec["c_per_km"])
            solid = float(rec["solid_m"])
            if new_top <= 1e-9:
                present_base = float(rec["present_z_top_m"]) + float(rec["present_thickness_m"])
                new_thickness = depositional_thickness_m(
                    float(rec["present_thickness_m"]),
                    present_base,
                    phi0,
                    c_per_km,
                )
                method = "sclater_christie_surface"
            else:
                new_thickness = thickness_at_burial_m(solid, new_top, phi0, c_per_km)
                method = "burial_bisection"
            nxt = dict(rec)
            nxt["current_z_top_m"] = new_top
            nxt["current_thickness_m"] = new_thickness
            updated.append(nxt)
            reported.append(
                {
                    "id": rec["id"],
                    "z_top_m": round(new_top, 9),
                    "thickness_m": round(new_thickness, 9),
                    "method": method,
                }
            )
        steps.append({"stripped_id": removed["id"], "remaining": reported})
        active = updated

    present = [
        {
            "id": rec["id"],
            "lithology": rec["lithology"],
            "z_top_m": round(float(rec["present_z_top_m"]), 9),
            "present_thickness_m": round(float(rec["present_thickness_m"]), 9),
            "solid_m": round(float(rec["solid_m"]), 9),
            "identity_thickness_m": round(float(rec["identity_thickness_m"]), 9),
            "depth_datum": "remaining_sediment_top",
        }
        for rec in column
    ]
    return {
        "compaction_reference": "shallowest_supplied_horizon",
        "paleobathymetry_added_to_burial": False,
        "layers": present,
        "steps": steps,
        "equations": EQUATIONS,
    }


def shear_to_paleoslope(
    points: list[dict],
    *,
    slope: float,
    z0: float,
    datum_id: str,
    force_flatten: bool,
) -> dict:
    """Vertical shear onto z = z0 + slope * x.

    A nonzero slope with force_flatten is refused and the coordinates are
    returned unchanged. Points that already lie on the datum do not move.
    """
    original = [
        {"id": str(p["id"]), "x_m": float(p["x_m"]), "z_m": float(p["z_m"])}
        for p in points
    ]
    if force_flatten and abs(slope) > 1e-12:
        return {
            "status": "BLOCKED",
            "reason": "force_flatten_nonzero_paleoslope",
            "points": original,
            "max_abs_shift_m": 0.0,
            "coordinates_changed": False,
        }
    use_slope = 0.0 if force_flatten else float(slope)
    datum_z: dict[float, float] = {}
    for point in original:
        if point["id"] == datum_id:
            datum_z[round(point["x_m"], 6)] = point["z_m"]
    shifted: list[dict] = []
    max_abs = 0.0
    for point in original:
        key = round(point["x_m"], 6)
        z_datum = datum_z.get(key)
        moved = dict(point)
        if z_datum is None:
            shifted.append(moved)
            continue
        dz = (z0 + use_slope * point["x_m"]) - z_datum
        max_abs = max(max_abs, abs(dz))
        moved["z_m"] = point["z_m"] + dz
        shifted.append(moved)
    return {
        "status": "ADMISSIBLE",
        "reason": "zero_slope_flatten" if force_flatten else "paleoslope_datum_preserved",
        "points": shifted,
        "max_abs_shift_m": float(max_abs),
        "coordinates_changed": bool(max_abs > 1e-6),
    }


def extension_from_heave(
    x_min_m: float,
    x_max_m: float,
    heave_m: float,
    paleoslope: float,
) -> dict:
    """Pin-to-pin extension. Bed length is reported separately.

    A constant paleoslope scales deformed and restored lengths by the same
    secant, so the ratio does not depend on slope. The slope*heave vertical
    mismatch of a rigid close is reported and is not called extension.
    """
    width = float(x_max_m) - float(x_min_m)
    restored_horizontal = width - float(heave_m)
    if width <= 0 or restored_horizontal <= 0 or heave_m < 0:
        return {"ok": False, "reason": "restored_length_non_positive"}
    secant = float(np.hypot(1.0, paleoslope))
    deformed = width * secant
    restored = restored_horizontal * secant
    extension = (deformed - restored) / restored
    return {
        "ok": True,
        "L_deformed_m": deformed,
        "L_restored_m": restored,
        "bed_length_horizontal_m": restored_horizontal,
        "extension": float(extension),
        "secant": secant,
        "rigid_close_vertical_mismatch_m": abs(float(paleoslope) * float(heave_m)),
    }


def restore_fault_points(points: list[dict], fault: dict) -> list[dict]:
    """Close one fault by a rigid hanging-wall shift. Footwall stays put."""
    trace = float(fault["trace_x_m"])
    heave = float(fault["heave_m"])
    throw = float(fault["throw_m"])
    hanging = str(fault.get("hanging_wall", "x_greater"))
    sense = str(fault.get("sense", "normal"))
    dx = -heave if hanging == "x_greater" else heave
    dz = -throw if sense == "normal" else throw
    restored: list[dict] = []
    for point in points:
        moved = {"id": str(point["id"]), "x_m": float(point["x_m"]), "z_m": float(point["z_m"])}
        on_hanging_wall = moved["x_m"] > trace + 1e-6 if hanging == "x_greater" else moved["x_m"] < trace - 1e-6
        if on_hanging_wall:
            moved["x_m"] = moved["x_m"] + dx
            moved["z_m"] = moved["z_m"] + dz
        restored.append(moved)
    return restored


def unfaulted_datum_points(x_min_m: float, x_max_m: float, trace_x_m: float, slope: float, z0: float, datum_id: str) -> list[dict]:
    xs = (float(x_min_m), float(trace_x_m), float(x_max_m))
    return [{"id": datum_id, "x_m": x, "z_m": float(z0) + float(slope) * x} for x in xs]


def faulted_datum_points(
    x_min_m: float,
    x_max_m: float,
    trace_x_m: float,
    heave_m: float,
    throw_m: float,
    slope: float,
    z0: float,
    datum_id: str,
) -> list[dict]:
    """Footwall on the datum. Hanging wall is down by throw and offset by heave."""
    fw_end = float(trace_x_m)
    hw_start = float(trace_x_m) + float(heave_m)
    samples = (
        (float(x_min_m), 0.0),
        (fw_end, 0.0),
        (hw_start, float(throw_m)),
        (float(x_max_m), float(throw_m)),
    )
    return [
        {"id": datum_id, "x_m": x, "z_m": float(z0) + float(slope) * x + extra}
        for x, extra in samples
    ]


def shale_account(
    heave_m: float,
    fw_thickness_m: float,
    hw_thickness_m: float,
    in_plane_m2: float | None,
    out_of_plane_m2: float | None,
    explain_fraction: float,
) -> dict:
    """Gap area is heave times mean present-day vertical thickness.

    Missing shale is not zero. Out-of-plane area is subtracted before any
    remainder is called crustal. The full heave area is never relabelled as
    crustal extension.
    """
    mean_thickness = float(np.mean(np.array([fw_thickness_m, hw_thickness_m], dtype=float)))
    gap = float(heave_m) * mean_thickness
    base = {
        "gap_area_m2": gap,
        "mean_growth_thickness_m": mean_thickness,
        "area_domain": "present_day_depth",
        "in_plane_m2": in_plane_m2,
        "out_of_plane_m2": out_of_plane_m2,
    }
    if in_plane_m2 is None or out_of_plane_m2 is None:
        base.update(
            {
                "shale_missing": True,
                "accounted_m2": None,
                "explains_gap": None,
                "shale_transfer_flagged": False,
                "crustal_extension_area_m2": None,
            }
        )
        return base
    accounted = float(in_plane_m2) + float(out_of_plane_m2)
    threshold = float(explain_fraction) * gap
    explains = accounted + 1e-6 >= threshold
    base.update(
        {
            "shale_missing": False,
            "accounted_m2": accounted,
            "explain_threshold_m2": threshold,
            "explains_gap": bool(explains),
            "shale_transfer_flagged": bool(float(out_of_plane_m2) > 0.0),
            "crustal_extension_area_m2": max(0.0, gap - accounted),
        }
    )
    return base


def growth_observation(intervals: list[dict]) -> dict | None:
    """The growth interval is the one whose thickness changes across the fault.

    The ratio is computed. No syn-rift label is applied. Equal thicknesses are
    a drape observation and are not selected as growth.
    """
    chosen: dict | None = None
    for interval in intervals:
        fw = interval.get("fw_thickness_m")
        hw = interval.get("hw_thickness_m")
        if fw is None or hw is None:
            continue
        fw_f = float(fw)
        hw_f = float(hw)
        if fw_f <= 0 or hw_f <= 0:
            continue
        ratio = hw_f / fw_f
        if abs(ratio - 1.0) <= 1e-9:
            continue
        if chosen is None or abs(ratio - 1.0) > abs(float(chosen["growth_ratio"]) - 1.0):
            chosen = {
                "id": str(interval.get("id", "")),
                "top_id": interval.get("top_id"),
                "base_id": interval.get("base_id"),
                "fw_thickness_m": fw_f,
                "hw_thickness_m": hw_f,
                "growth_ratio": ratio,
                "lithology": str(interval.get("lithology", "generic")),
            }
    return chosen
