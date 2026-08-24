"""segy_horizon_bridge — SEGY horizon picks → GemPy 3D model → true-scale 2D section.

The falsification-gated bridge between interpreted seismic (OBS-grade) and
the implicit structural model. When real SEGY horizon picks arrive, they flow:

    horizon picks (CSV/JSON {x,y,z,formation})
        → GemPy implicit 3D (universal cokriging scalar field)
        → vertical section slice at true scale (1:1, no VE)
        → epistemic-tagged artifact (OBS if picks are real, SYNTHETIC if demo)

Epistemic rule (F2): this bridge NEVER upgrades the tag of its input. If the
picks are synthetic, every downstream artifact is tagged SYNTHETIC. Truth
class propagates downward; it can only be set at the source.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("geox.canonical.segy_horizon_bridge")

# Minimum picks per formation for GemPy to interpolate a surface
MIN_POINTS_PER_FORMATION = 3


def parse_horizon_picks(source: str | list[dict] | Path) -> list[dict]:
    """Parse horizon picks from JSON string, CSV string, or list of dicts.

    Accepted record shape: {x, y, z, formation} — z is depth below datum
    (positive down, metres) or elevation (negative down) — caller declares
    via `z_convention` in the bridge call.
    """
    if isinstance(source, list):
        records = source
    else:
        text = str(source)
        stripped = text.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
            records = json.loads(stripped)
        else:
            # CSV with header x,y,z,formation
            reader = csv.DictReader(io.StringIO(stripped))
            records = [
                {"x": float(r["x"]), "y": float(r["y"]),
                 "z": float(r["z"]), "formation": r["formation"].strip()}
                for r in reader
            ]
    out = []
    for r in records:
        out.append({
            "x": float(r["x"]), "y": float(r["y"]),
            "z": float(r["z"]), "formation": str(r["formation"]),
        })
    return out


def picks_to_gempy_inputs(
    picks: list[dict],
    z_convention: str = "depth_positive_down",
    dip_hint_deg: float = 2.0,
    azimuth_hint_deg: float = 90.0,
) -> tuple[list[dict], list[dict]]:
    """Convert horizon picks to GemPy surface_points + orientations.

    Surface points pass straight through (z flipped to elevation for GemPy:
    GemPy expects z-up). Orientations are seeded with a regional dip hint so
    the interpolator has a gradient constraint even with sparse picks.
    """
    if z_convention not in ("depth_positive_down", "elevation"):
        raise ValueError(f"unknown z_convention: {z_convention}")

    surface_points = []
    for p in picks:
        z = p["z"] if z_convention == "elevation" else -p["z"]
        surface_points.append({
            "x": p["x"], "y": p["y"], "z": z,
            "formation": p["formation"],
        })

    # One orientation per formation, at the centroid of its picks
    by_formation: dict[str, list[dict]] = {}
    for sp in surface_points:
        by_formation.setdefault(sp["formation"], []).append(sp)

    orientations = []
    for formation, pts in by_formation.items():
        cx = float(np.mean([p["x"] for p in pts]))
        cy = float(np.mean([p["y"] for p in pts]))
        cz = float(np.mean([p["z"] for p in pts]))
        orientations.append({
            "x": cx, "y": cy, "z": cz,
            "dip": dip_hint_deg, "azimuth": azimuth_hint_deg,
            "formation": formation,
        })
    return surface_points, orientations


def validate_picks(picks: list[dict]) -> dict[str, Any]:
    """Falsification gate — check picks can constrain a model at all."""
    by_formation: dict[str, int] = {}
    for p in picks:
        by_formation[p["formation"]] = by_formation.get(p["formation"], 0) + 1

    deficient = {f: n for f, n in by_formation.items() if n < MIN_POINTS_PER_FORMATION}

    # Duplicate (x, y) WITHIN a formation is degenerate; the same (x, y) across
    # DIFFERENT formations is normal stacked-horizon geometry.
    per_formation_xy: dict[str, set] = {}
    dup_per_formation = 0
    for p in picks:
        key = (p["x"], p["y"])
        seen = per_formation_xy.setdefault(p["formation"], set())
        if key in seen:
            dup_per_formation += 1
        else:
            seen.add(key)

    ok = not deficient and dup_per_formation == 0
    return {
        "ok": ok,
        "formations": by_formation,
        "deficient_formations": deficient,
        "duplicate_xy_within_formation": dup_per_formation,
        "min_points_required": MIN_POINTS_PER_FORMATION,
    }


def extract_section_from_block(
    block: np.ndarray,
    extent: tuple[float, float, float, float, float, float],
    y_slice_frac: float = 0.5,
) -> dict[str, Any]:
    """Slice a 2D section (x–z) out of a 3D lithology block at y = fraction."""
    if block.ndim != 3:
        raise ValueError(f"expected 3D block, got ndim={block.ndim}")
    ny = block.shape[1]
    j = int(np.clip(y_slice_frac, 0.0, 1.0) * (ny - 1))
    section = block[:, j, :]  # (nx, nz)
    return {
        "section": section,
        "shape": list(section.shape),
        "y_index": j,
        "y_world": float(extent[2] + y_slice_frac * (extent[3] - extent[2])),
        "vertical_exaggeration": 1.0,  # hard contract: true scale
    }


def derive_epistemic_tag(picks_tag: str) -> str:
    """Truth class propagates downward — never upgrades."""
    allowed = {"OBS", "DER", "INT", "SYNTHETIC"}
    t = picks_tag.strip().upper()
    if t not in allowed:
        raise ValueError(f"picks_tag must be one of {allowed}, got {picks_tag}")
    if t == "OBS":
        # Even with real picks, the GemPy interpolation is derived from them.
        return "DER"
    return t


async def geox_segy_horizon_bridge(
    horizon_picks: str | list[dict] | None = None,
    picks_tag: str = "SYNTHETIC",
    z_convention: str = "depth_positive_down",
    dip_hint_deg: float = 2.0,
    azimuth_hint_deg: float = 90.0,
    grid_resolution: tuple | list | None = None,
    model_extent: tuple | list | None = None,
    compute_uncertainty: bool = True,
    y_slice_frac: float = 0.5,
    output_format: str = "json",
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Bridge: horizon picks → GemPy implicit 3D → true-scale 2D section.

    Returns an evidence envelope with the model, the section slice, and a
    truth tag derived from the picks (never upgraded).
    """
    from .gempy_implicit_3d import geox_gempy_implicit_3d  # late import

    if horizon_picks is None:
        return {
            "ok": False,
            "error": "horizon_picks required — provide CSV/JSON string or list",
            "picks_tag": picks_tag,
        }

    picks = parse_horizon_picks(horizon_picks)
    gate = validate_picks(picks)
    if not gate["ok"]:
        return {
            "ok": False,
            "error": "PICKS_INSUFFICIENT",
            "gate": gate,
            "picks_tag": picks_tag,
            "remediation": (
                "Each formation needs >= "
                f"{MIN_POINTS_PER_FORMATION} picks at distinct (x, y). "
                "Deficient: " + ", ".join(f"{f} ({n})" for f, n in gate["deficient_formations"].items())
            ),
        }

    # Auto-derive extent from picks if not provided, so the GemPy compute
    # has a z-range that actually contains the input surface points.
    # Without this, the federation tool's auto-extent treats zmin=0,
    # zmax = max(z)+500 — which fails for elevation-mode picks (negative z).
    if model_extent is None:
        xs = [p["x"] for p in picks]
        ys = [p["y"] for p in picks]
        zs = [p["z"] for p in picks]
        # Detect convention: positive z values = depth, negative = elevation
        max_z = max(zs); min_z = min(zs)
        if max_z > 0:
            # depth_positive_down — picks are positive; convert to elevation
            # and build extent covering [min elev - margin, max elev + margin]
            elev_min = -max_z - 1000
            elev_max = -min_z + 1000
            if elev_min > elev_max: elev_min, elev_max = elev_max, elev_min
        else:
            elev_min = min_z - 1000
            elev_max = max_z + 1000
        margin = max(100.0, (max(xs) - min(xs)) * 0.2)
        model_extent = [
            min(xs) - margin, max(xs) + margin,
            min(ys) - margin, max(ys) + margin,
            elev_min, elev_max,
        ]

    surface_points, orientations = picks_to_gempy_inputs(
        picks, z_convention=z_convention,
        dip_hint_deg=dip_hint_deg, azimuth_hint_deg=azimuth_hint_deg,
    )

    result = await geox_gempy_implicit_3d(
        surface_points=surface_points,
        orientations=orientations,
        grid_resolution=grid_resolution,
        model_extent=model_extent,
        compute_uncertainty=compute_uncertainty,
        output_format=output_format,
        session_id=session_id,
        actor_id=actor_id,
        trace_id=trace_id,
    )

    tag = derive_epistemic_tag(picks_tag)

    # If the engine produced a block (3-D post-reshape), slice it
    section_info = None
    block = None
    if isinstance(result, dict):
        payload = result
        # nested envelope? check one level deep (gempy_result.result)
        for candidate_dict in (result, result.get("result") if isinstance(result.get("result"), dict) else None):
            if candidate_dict is None:
                continue
            for key in ("lithology_block", "lith_block", "block", "block_model"):
                candidate = candidate_dict.get(key)
                if isinstance(candidate, np.ndarray) and candidate.ndim == 3:
                    block = candidate
                    break
                if isinstance(candidate, list):
                    try:
                        arr = np.array(candidate)
                        if arr.ndim == 3:
                            block = arr
                            break
                    except Exception:
                        continue
            if block is not None:
                break
    if block is not None and model_extent is not None:
        ext = tuple(float(v) for v in model_extent)
        section_info = extract_section_from_block(block, ext, y_slice_frac)

    return {
        "ok": bool(result.get("ok", True)) if isinstance(result, dict) else True,
        "bridge": "segy_horizon_bridge",
        "picks_tag": picks_tag,
        "derived_tag": tag,
        "tag_rule": "truth class propagates downward; OBS picks → DER model, SYNTHETIC stays SYNTHETIC",
        "pick_count": len(picks),
        "formations": gate["formations"],
        "section": section_info,
        "gempy_result": result,
    }
