from typing import Any, Dict, List
# ─── kernel/_evidence.py ─── F6 Maruah + F7 Humility + ensemble injection ─────
# Extracted from _helpers.py (lines 193–311)
# NO FastMCP imports. Pure business logic.

# F6 Maruah-first: Community / Indigenous Territory Guard
# ═══════════════════════════════════════════════════════════════════════════════

# Simplified basin-to-territory overlap map (global key basins).
# Production should query authoritative indigenous land registries.
_MARUAH_BASIN_POLYGONS: dict[str, list[tuple[float, float]]] = {
    "north_sea": [(0, 50), (10, 50), (10, 62), (0, 62)],
    "gulf_of_mexico": [(-98, 18), (-80, 18), (-80, 31), (-98, 31)],
    "south_china_sea": [(105, 5), (125, 5), (125, 25), (105, 25)],
    "bay_of_bengal": [(80, 5), (95, 5), (95, 25), (80, 25)],
    "north_slope_alaska": [(-160, 68), (-140, 68), (-140, 72), (-160, 72)],
    "amazon_basin": [(-75, -10), (-45, -10), (-45, 5), (-75, 5)],
    "congo_basin": [(12, -10), (30, -10), (30, 5), (12, 5)],
}


def _bbox_intersects(bbox: list[float], poly: list[tuple[float, float]]) -> bool:
    """Simple AABB overlap test between bbox [min_lon, min_lat, max_lon, max_lat]
    and polygon bounding box."""
    min_lon, min_lat, max_lon, max_lat = bbox
    p_min_lon = min(p[0] for p in poly)
    p_max_lon = max(p[0] for p in poly)
    p_min_lat = min(p[1] for p in poly)
    p_max_lat = max(p[1] for p in poly)
    return not (max_lon < p_min_lon or min_lon > p_max_lon or max_lat < p_min_lat or min_lat > p_max_lat)


def _inject_ensemble_residual_evidence(
    result: dict[str, Any],
    realizations: int = 3,
    assumptions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inject ensemble, residual, evidence_density, and assumptions into SUCCESS outputs.

    F7 Humility: computes humility_score = (p90 - p10) / p50
    and attaches ensemble realizations + residual maps.
    """
    if result.get("execution_status") != "SUCCESS":
        return result

    # Try to extract p10/p50/p90 for humility computation
    p10 = result.get("phit_p10") or result.get("sw_p10") or result.get("k_p10_md") or 0.0
    p50 = result.get("phit_p50") or result.get("sw_p50") or result.get("k_p50_md") or result.get("k_mean_md") or 1.0
    p90 = result.get("phit_p90") or result.get("sw_p90") or result.get("k_p90_md") or 0.0

    humility_score = 0.0
    if p50 and p50 != 0:
        humility_score = round(abs(float(p90) - float(p10)) / abs(float(p50)), 4)

    # Synthetic ensemble (realizations) based on available data
    ensemble = []
    for i in range(realizations):
        noise_factor = 0.9 + (i * 0.1)  # 0.9, 1.0, 1.1
        _scenario_tags = {1: "MIN", 2: "MID", 3: "MAX"}
        realization = {"realization_id": i + 1, "noise_factor": noise_factor, "scenario_tag": _scenario_tags.get(i + 1, f"R{i + 1}")}
        if "phit_p50" in result:
            realization["phit"] = round(float(result["phit_p50"]) * noise_factor, 4)
        if "sw_p50" in result:
            realization["sw"] = round(float(result["sw_p50"]) * noise_factor, 4)
        if "k_mean_md" in result:
            realization["k_md"] = round(float(result["k_mean_md"]) * noise_factor, 2)
        ensemble.append(realization)

    # Residual: difference from realization mean
    residual = {"mean_offset": 0.0, "max_deviation": 0.0}
    if ensemble:
        vals = [r.get("phit", r.get("k_md", 0.0)) for r in ensemble]
        if vals:
            mean_v = sum(vals) / len(vals)
            residual["mean_offset"] = round(mean_v - vals[1], 6)  # offset from central realization
            residual["max_deviation"] = round(max(abs(v - mean_v) for v in vals), 6)

    # Evidence density: how much data supported the computation
    evidence_density = {
        "n_samples": result.get("n_samples", 0),
        "null_pct": result.get("uncertainty", {}).get("input_null_pct", {}),
        "data_quality": "HIGH" if result.get("n_samples", 0) > 1000 else "MEDIUM" if result.get("n_samples", 0) > 100 else "LOW",
    }

    result["ensemble"] = ensemble
    result["residual"] = residual
    result["evidence_density"] = evidence_density
    result["humility_score"] = humility_score
    result["realizations"] = realizations
    result["assumptions"] = assumptions if assumptions is not None else {}
    return result


def _check_maruah_territory(bbox: list[float], crs: str) -> dict[str, Any]:
    """Check if bounding box intersects basins with community/indigenous territory.
    Returns F6 Maruah flag + uncertainty + recommended next action."""
    intersected_basins = []
    for basin_name, poly in _MARUAH_BASIN_POLYGONS.items():
        if _bbox_intersects(bbox, poly):
            intersected_basins.append(basin_name)

    if not intersected_basins:
        return {
            "maruah_flag": "CLEAR",
            "territory_risk": "none",
            "intersected_basins": [],
            "recommended_action": "Proceed with standard consent protocols.",
            "confidence": "HIGH",
        }

    return {
        "maruah_flag": "MARUAH_REQUIRED",
        "territory_risk": "high" if len(intersected_basins) >= 2 else "medium",
        "intersected_basins": intersected_basins,
        "recommended_action": (
            "F6 MARUAH: Bounding box intersects basin(s) with community/indigenous territory. "
            "Require Free, Prior, and Informed Consent (FPIC) before proceeding. "
            "Consult local authorities and indigenous representatives."
        ),
        "confidence": "MEDIUM",
        "floors_triggered": ["F5", "F6"],
    }

