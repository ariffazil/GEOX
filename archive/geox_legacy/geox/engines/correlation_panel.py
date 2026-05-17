"""
GEOX Well Correlation Panel Renderer
====================================
Produces a multi-well, multi-track PNG/SVG correlation panel from LAS files.

Domain guardrails enforced:
  - Cross-basin warning if wells from different sources
  - Depth basis always stated (MD, no TVDSS claim unless corrected)
  - Claim state labels on all interpretations

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import os
import json
import hashlib
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

try:
    import lasio
except ImportError:
    lasio = None

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Rectangle


# ─── Curve alias map (Arif's canonical spec) ───────────────────────────────────

CURVE_ALIASES: dict[str, list[str]] = {
    "GR":  ["GR", "GAMMA", "CGR", "SGR"],
    "RT":  ["RT", "ILD", "LLD", "RDEP", "RES_DEEP", "AT90", "RESD"],
    "RHOB": ["RHOB", "DEN", "DENS", "ZDEN"],
    "NPHI": ["NPHI", "NEUT", "TNPH", "CNCF"],
    "DT":  ["DT", "DTC", "AC"],
    "PEF": ["PEF", "PE"],
}


# ─── Claim state labels ────────────────────────────────────────────────────────

class ClaimState:
    OBSERVATION  = "OBSERVED"
    COMPUTED     = "COMPUTED"
    CANDIDATE    = "AUTO_PICK_CANDIDATE"
    EXPLORATORY  = "EXPLORATORY_VISUALIZATION"
    UNKNOWN      = "UNKNOWN"


@dataclass
class CurveManifest:
    mnemonic: str
    unit: str
    depth_min: float
    depth_max: float
    null_pct: float
    loaded: bool = True


@dataclass
class WellManifest:
    well_id: str
    las_path: str
    depth_unit: str
    depth_min: float
    depth_max: float
    curves: dict[str, CurveManifest] = field(default_factory=dict)
    basin_hints: list[str] = field(default_factory=list)
    loaded: bool = False
    error: str | None = None


@dataclass
class TrackConfig:
    mnemonic: str          # canonical name (GR, RT, RHOB, NPHI)
    aliases: list[str]     # which LAS mnemonics map to this track
    color: str = "#222222"
    fill_color: str | None = None
    log_scale: bool = False
    min_val: float | None = None
    max_val: float | None = None


DEFAULT_TRACKS: list[TrackConfig] = [
    TrackConfig("GR",   CURVE_ALIASES["GR"],   color="#4CAF50", fill_color="#A5D6A7"),
    TrackConfig("RT",   CURVE_ALIASES["RT"],   color="#F44336", log_scale=True,  min_val=0.1, max_val=1000),
    TrackConfig("RHOB", CURVE_ALIASES["RHOB"], color="#FF9800", min_val=1.9, max_val=2.9),
    TrackConfig("NPHI", CURVE_ALIASES["NPHI"], color="#2196F3", min_val=-0.05, max_val=0.6),
]


# ─── LAS Reader ────────────────────────────────────────────────────────────────

def read_las_with_aliases(path: str) -> tuple[dict[str, np.ndarray], np.ndarray, str, list[str]]:
    """Read LAS file and return {canonical_name: values}, depth_array, depth_unit, loaded_mnemonics.

    Raises ValueError if file unreadable.
    """
    if lasio is None:
        raise RuntimeError("lasio not installed")
    las = lasio.read(path)

    # Detect depth curve
    depth_arr = np.asarray(las.index, dtype=float)
    depth_unit = "M"
    if hasattr(las, "params"):
        for key in ["DX", "DXC", "DLL", "LENGTH", "UNIT"]:
            if key in las.params:
                depth_unit = str(las.params[key].value)
                break

    # Load all curves
    raw: dict[str, np.ndarray] = {}
    for curve in las.curves:
        mn = curve.mnemonic.strip().upper()
        vals = np.asarray(las[curve.mnemonic], dtype=float)
        raw[mn] = vals

    # Find depth curve name
    depth_mn = "DEPT"
    for candidate in ["DEPT", "DEPTH", "MD", "TVD"]:
        if candidate in raw:
            depth_mn = candidate
            break

    depth_arr = raw.pop(depth_mn, depth_arr)

    # Resolve aliases → canonical
    resolved: dict[str, np.ndarray] = {}
    loaded_mnemonics: list[str] = []
    for canonical, aliases in CURVE_ALIASES.items():
        for alias in aliases:
            if alias in raw:
                resolved[canonical] = np.asarray(raw[alias], dtype=float)
                loaded_mnemonics.append(alias)
                break

    return resolved, depth_arr, depth_unit, loaded_mnemonics


# ─── Domain guardrails ─────────────────────────────────────────────────────────

def check_cross_basin(wells: list[WellManifest]) -> list[str]:
    """Warn if wells appear to be from different basins/sources."""
    basins = set()
    for w in wells:
        # Use UWI/well_id prefix heuristic
        if w.basin_hints:
            basins.update(w.basin_hints)
        elif "_" in w.well_id:
            prefix = w.well_id.split("_")[0]
            if prefix.startswith(("L0", "L1", "15", "30", "31", "55")):
                basins.add("NL")  # North Sea / Netherlands
            elif prefix.isdigit() and len(prefix) >= 4:
                basins.add("GENERIC")
    return list(basins)


# ─── Panel renderer ───────────────────────────────────────────────────────────

def render_correlation_panel(
    wells: list[WellManifest],
    tracks: list[TrackConfig],
    output_path: str,
    depth_range: tuple[float, float] | None = None,
    tops: dict[str, dict[str, float]] | None = None,  # well_id → marker → depth
    normalize: bool = True,
    figsize: tuple[float, float] = (12.0, 16.0),
) -> dict[str, Any]:
    """Render a multi-well correlation panel PNG.

    Args:
        wells: List of loaded WellManifest objects.
        tracks: Track configurations.
        output_path: Output PNG path.
        depth_range: (min, max) depth to display. Auto if None.
        tops: Optional {well_id: {marker_name: depth}} dict.
        normalize: Normalize tracks to shared depth range.

    Returns:
        Summary dict with status, wells_loaded, tracks_rendered, warnings.
    """
    n_wells = len(wells)
    n_tracks = len(tracks)

    fig, axes = plt.subplots(
        1, n_wells * n_tracks,
        figsize=(figsize[0] * n_wells, figsize[1]),
        squeeze=False,
    )
    fig.patch.set_facecolor("#FAFAFA")

    warnings: list[str] = []
    depth_basis = "MD (measured depth)"
    depth_unit = wells[0].depth_unit if wells else "M"

    # Auto depth range
    if depth_range is None:
        d_mins, d_maxs = [], []
        for w in wells:
            if w.loaded:
                d_mins.append(w.depth_min)
                d_maxs.append(w.depth_max)
        if d_mins:
            d_min = min(d_mins)
            d_max = max(d_maxs)
        else:
            d_min, d_max = 0.0, 5000.0
    else:
        d_min, d_max = depth_range

    col_idx = 0
    for w_idx, well in enumerate(wells):
        for t_idx, track in enumerate(tracks):
            ax = axes[0, col_idx]

            if not well.loaded:
                ax.text(0.5, 0.5, f"ERROR:\n{well.error}",
                        ha="center", va="center", color="red", fontsize=8,
                        transform=ax.transAxes)
                ax.set_title(well.well_id[:12], fontsize=8, color="gray")
                col_idx += 1
                continue

            # Get curve data
            curve_data = well.curves.get(track.mnemonic)
            if curve_data is None:
                # Try to find from loaded curves
                for alias in track.aliases:
                    for cname, cdata in well.curves.items():
                        if cname == alias:
                            curve_data = cdata
                            break

            ax.set_facecolor("#FFFFFF")

            if curve_data is not None and curve_data.loaded:
                vals = _get_curve_values(well, track.mnemonic, track.aliases)
                if vals is not None:
                    depths = np.linspace(d_min, d_max, len(vals))
                    _plot_track(ax, depths, vals, track, d_min, d_max)
                    warnings.append(f"Well {well.well_id} loaded {track.mnemonic}")
                else:
                    ax.text(0.5, 0.5, f"[{track.mnemonic}\nmissing]",
                            ha="center", va="center", color="#999",
                            fontsize=7, transform=ax.transAxes)
            else:
                ax.text(0.5, 0.5, f"[{track.mnemonic}\nnot loaded]",
                        ha="center", va="center", color="#CCC",
                        fontsize=7, transform=ax.transAxes)

            # Tops
            if tops and well.well_id in tops:
                for marker, depth in tops[well.well_id].items():
                    if d_min <= depth <= d_max:
                        ax.axhline(y=depth, color="#9C27B0", linestyle="--",
                                   linewidth=0.8, alpha=0.7)
                        ax.text(1.02, depth, f"◆ {marker}", fontsize=6,
                                va="center", color="#9C27B0",
                                transform=ax.get_yaxis_transform())

            ax.set_xlim(track.min_val or 0, track.max_val or 100)
            ax.invert_yaxis()
            ax.set_ylim(d_max, d_min)
            ax.yaxis.set_major_locator(mticker.MaxNLocator(8))
            ax.tick_params(labelsize=7)
            ax.set_xlabel(f"{track.mnemonic}", fontsize=7, color="#555")
            ax.xaxis.label.set_fontsize(7)

            # Column headers
            if t_idx == 0:
                ax.set_title(well.well_id[:14], fontsize=9, fontweight="bold",
                             color="#1A1A1A")
            if w_idx == 0:
                ax.text(0.5, 1.03, track.mnemonic,
                        ha="center", va="bottom", fontsize=9, fontweight="bold",
                        color=track.color, transform=ax.transAxes)

            col_idx += 1

    # Disclaimer
    fig.text(0.5, 0.01,
             f"Depth basis: {depth_basis} | Datum correction: not applied | "
             f"TVDSS: unavailable | Claim: {ClaimState.EXPLORATORY} | "
             f"GEOX Sovereign 13 | DITEMPA BUKAN DIBERI",
             ha="center", va="bottom", fontsize=6, color="#888",
             style="italic")

    plt.subplots_adjust(left=0.06, right=0.97, top=0.95, bottom=0.06,
                       wspace=0.4)
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)

    return {
        "status": "OK",
        "artifact": {
            "png_path": output_path,
        },
        "wells_loaded": sum(1 for w in wells if w.loaded),
        "tracks_rendered": [t.mnemonic for t in tracks],
        "warnings": warnings[:10],  # cap at 10
        "claim_state": ClaimState.EXPLORATORY,
        "depth_datum": {"basis": depth_basis, "datum_corrected": False, "tvd_available": False},
    }


def _get_curve_values(well: WellManifest, canonical: str, aliases: list[str]) -> np.ndarray | None:
    """Get curve array from well manifest by canonical name or alias."""
    for cname, cdata in well.curves.items():
        if cname == canonical:
            return np.asarray(cdata, dtype=float) if isinstance(cdata, (list, np.ndarray)) else None
    for alias in aliases:
        if alias in well.curves:
            return np.asarray(well.curves[alias], dtype=float) if isinstance(well.curves[alias], (list, np.ndarray)) else None
    return None


def _plot_track(ax, depths: np.ndarray, values: np.ndarray,
                track: TrackConfig, d_min: float, d_max: float) -> None:
    """Plot a single track curve with fill."""
    mask = ~(np.isnan(values) | np.isnan(depths))
    d_plot = depths[mask]
    v_plot = values[mask]

    if len(d_plot) < 2:
        return

    ax.plot(v_plot, d_plot, color=track.color, linewidth=0.8, alpha=0.9)

    if track.fill_color and not track.log_scale:
        ax.fill_betweenx(d_plot, v_plot, color=track.fill_color, alpha=0.3)


# ─── High-level pipeline ───────────────────────────────────────────────────────

def build_correlation_panel(
    las_paths: list[str],
    well_names: list[str] | None,
    tracks: list[str] | None,
    output_png: str,
    depth_range: tuple[float, float] | None = None,
    tops: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Full pipeline: LAS → parse → render PNG.

    Args:
        las_paths: List of LAS file paths.
        well_names: Optional display names per well.
        tracks: List of canonical track names (GR, RT, RHOB, NPHI). All if None.
        output_png: Output PNG path.
        depth_range: Optional (min, max) depth.
        tops: Optional {well_name: {marker: depth}}.

    Returns:
        Status dict with artifact paths, curve summaries, warnings, claim_state.
    """
    if lasio is None:
        return {
            "status": "ERROR",
            "error_code": "LASIO_MISSING",
            "message": "lasio not installed in runtime.",
        }

    track_configs = [t for t in DEFAULT_TRACKS if tracks is None or t.mnemonic in tracks]
    names = well_names or [Path(p).stem for p in las_paths]

    wells: list[WellManifest] = []
    all_warnings: list[str] = []

    for las_path, wname in zip(las_paths, names):
        well = WellManifest(
            well_id=wname,
            las_path=las_path,
            depth_unit="M",
            depth_min=0.0,
            depth_max=0.0,
        )

        if not os.path.exists(las_path):
            well.error = f"File not found: {las_path}"
            wells.append(well)
            all_warnings.append(f"Well {wname}: FILE_NOT_FOUND")
            continue

        try:
            curves, depths, depth_unit, loaded = read_las_with_aliases(las_path)
            well.depth_unit = depth_unit
            well.depth_min = float(np.nanmin(depths))
            well.depth_max = float(np.nanmax(depths))
            well.loaded = True

            for canonical, vals in curves.items():
                null_pct = float(np.isnan(vals).sum() / max(len(vals), 1)) * 100
                well.curves[canonical] = CurveManifest(
                    mnemonic=canonical,
                    unit="",
                    depth_min=well.depth_min,
                    depth_max=well.depth_max,
                    null_pct=null_pct,
                    loaded=True,
                )

        except Exception as exc:
            well.error = str(exc)[:120]
            all_warnings.append(f"Well {wname}: LAS_PARSE_FAILED — {exc}")

        wells.append(well)

    # Cross-basin check
    basins = check_cross_basin(wells)
    if len(basins) > 1:
        all_warnings.append(
            f"Wells appear from different basins/sources: {basins}. "
            f"Correlation is visual/testing only."
        )

    # Pre-render guard: fail if no wells loaded
    wells_loaded_count = sum(1 for w in wells if w.loaded)
    if wells_loaded_count == 0:
        return {
            "status": "ERROR",
            "error_code": "NO_WELLS_LOADED",
            "message": "Correlation panel could not be generated — no LAS files were loaded.",
            "recoverable": True,
            "warnings": all_warnings,
            "artifact": None,
            "wells_loaded": 0,
            "claim_state": ClaimState.UNKNOWN,
        }

    # Render
    result = render_correlation_panel(
        wells=wells,
        tracks=track_configs,
        output_path=output_png,
        depth_range=depth_range,
        tops=tops,
    )

    # Curve summary
    curve_summary = []
    for w in wells:
        if w.loaded:
            for mn, cdata in w.curves.items():
                curve_summary.append({
                    "well_id": w.well_id,
                    "mnemonic": mn,
                    "depth_min": round(cdata.depth_min, 1),
                    "depth_max": round(cdata.depth_max, 1),
                    "null_pct": round(cdata.null_pct, 1),
                })

    result["curve_summary"] = curve_summary
    result["warnings"] = all_warnings + result.get("warnings", [])
    result["claim_state"] = ClaimState.EXPLORATORY

    return result
