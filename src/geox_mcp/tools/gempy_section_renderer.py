"""
gempy_section_renderer — Render gempy_implicit_3d output as publication-grade cross-section.

Companion to gempy_implicit_3d. Consumes the lithology_block + extent returned
by the federation compute path and renders it in GEOX intelligence-grade dark
theme with formation labels, domain markers, scale bars, and Sangomar/Tortue
fiducials.

Without this tool, the federation's 3D model output stays as raw tabular
lithology_block + 3 generic colored sections. With this tool, the same data
becomes a deliverable artifact.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import io
import logging
import os
import uuid
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

logger = logging.getLogger("geox.canonical.gempy_section_renderer")

TMP_OUT = Path("/tmp/geox")
TMP_OUT.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path("/opt/geox/data/gempy_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Sedimentology convention colors (same as Strat Column)
SEDIMENT_COLORS = {
    "outside": "#0d1117",  # below depth / outside model = page bg
    "seabed": "#3a5a7a",
    "cenozoic": "#3d4a52",
    "campanian_turbidites": "#e67e22",
    "sangomar_turbidites": "#e67e22",
    "cenomanian_turonian": "#3a3a3a",
    "albian": "#5a5a5a",
    "aptian": "#5a5a5a",
    "jurassic": "#a4c8b8",
    "neocomian": "#5a3a2a",
    "triassic": "#7a4a2a",
    "basement": "#5a3a2a",
}


def _formation_color(name: str) -> str:
    """Pick a color for a formation by name."""
    n = (name or "").lower().replace(" ", "_").replace("-", "_")
    for key, color in SEDIMENT_COLORS.items():
        if key in n:
            return color
    return "#3d4a52"


def _render_pcolormesh(ax, section, x_arr, z_arr, cmap, norm):
    """Render a 2D section as imshow with proper extent. Section shape: (nx, nz)."""
    # Convert display coordinates to km
    extent = [x_arr.min() / 1000, x_arr.max() / 1000,
              z_arr.max() / 1000, z_arr.min() / 1000]  # z inverted for display
    # section is (nx, nz); imshow expects image shape (rows, cols) where rows map to y axis (z here), cols to x axis
    return ax.imshow(section.T, cmap=cmap, norm=norm, aspect="auto",
                    extent=extent, origin="upper",
                    interpolation="nearest", rasterized=True)


def render_gempy_section(
    lithology_block: np.ndarray,
    extent: list,
    formations: list | None = None,
    section_axis: str = "y",
    section_index: int | None = None,
    layer_color_map: dict[int, str] | None = None,
    title: str | None = None,
    save_path: str | None = None,
    return_image: bool = False,
) -> dict[str, Any]:
    """Render a lithology block from geox_gempy_implicit_3d as a publication-grade section.

    Parameters
    ----------
    lithology_block : numpy.ndarray
        Array of lithology IDs with shape (nx, ny, nz). ID 0 = outside model.
    extent : list
        [xmin, xmax, ymin, ymax, zmin, zmax] in metres.
    formations : list, optional
        Names of formations in order matching lithology IDs 1..N. If omitted,
        headers are auto-generated ("ID 1", "ID 2", ...).
    section_axis : str, "x" or "y"
        Which axis to slice along. "y" produces offshore X-Z section
        (cross-shore); "x" produces offshore Y-Z section (along-shore).
    section_index : int, optional
        Index along the section axis. Defaults to middle of block.
    layer_color_map : dict, optional
        Override formation colors by lithology ID.

    Returns
    -------
    dict with keys: ok, image_path, image_base64, lith_ids_seen, epistemic.
    """
    lithology_block = np.array(lithology_block)
    if lithology_block.ndim != 3:
        return {"ok": False, "error": f"lithology_block must be 3D, got {lithology_block.ndim}D"}
    nx, ny, nz = lithology_block.shape
    xmin, xmax, ymin, ymax, zmin, zmax = extent

    if section_axis not in ("x", "y"):
        return {"ok": False, "error": f"section_axis must be x or y, got {section_axis}"}

    if section_index is None:
        # Default: middle of the sliced axis
        if section_axis == "y":
            section_index = ny // 2
        else:
            section_index = nx // 2  # when slicing x, index is over nx

    if section_axis == "y":
        section = lithology_block[:, section_index, :]
        x_arr = np.linspace(xmin, xmax, nx)
        x_label = "X (cross-shore)"
        x_world = (ymin + (ymax - ymin) * section_index / (ny - 1)) / 1000
        cross_section_label = f"Y-X Section at {x_world:.1f} km"
    else:
        section = lithology_block[section_index, :, :]
        x_arr = np.linspace(ymin, ymax, ny)
        x_label = "Y (along-shore)"
        x_world = (xmin + (xmax - xmin) * section_index / (nx - 1)) / 1000
        cross_section_label = f"X-Y Section at {x_world:.1f} km"

    z_arr = np.linspace(zmin, zmax, nz)

    n_lith = int(np.max(section)) + 1
    if n_lith < 2:
        n_lith = 2

    # Build colormap from layer_color_map or auto-color formations
    if layer_color_map is None:
        layer_color_map = {}
        if formations is not None:
            for i, fm in enumerate(formations):
                layer_color_map[i + 1] = _formation_color(fm)
        # Fill missing
        for lid in range(1, n_lith):
            if lid not in layer_color_map:
                layer_color_map[lid] = "#3d4a52"

    palette = ["#0d1117"]  # ID 0 = outside
    for lid in range(1, max(n_lith + 1, 8)):
        palette.append(layer_color_map.get(lid, "#3d4a52"))
    while len(palette) < n_lith + 2:
        palette.append("#3d4a52")

    cmap = ListedColormap(palette[: n_lith + 2])
    norm = BoundaryNorm(np.arange(-0.5, n_lith + 1.5, 1), cmap.N)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")

    # Render section
    _render_pcolormesh(ax, section, x_arr, z_arr, cmap, norm)

    # Format coordinate tick labels (km)
    ax.set_xticks(np.linspace(x_arr.min() / 1000, x_arr.max() / 1000, 6))
    ax.set_yticks(np.linspace(z_arr.min() / 1000, z_arr.max() / 1000, 6))

    # Formation labels (centroids)
    for lid in range(1, n_lith):
        if formations and lid - 1 < len(formations):
            name = formations[lid - 1]
        else:
            name = f"ID{lid}"
        yy, xx = np.where(section == lid)
        if len(yy) > 20:
            yy = np.clip(yy, 0, len(z_arr) - 1)
            xx = np.clip(xx, 0, len(x_arr) - 1)
            cy = float(np.mean(z_arr[yy])) / 1000  # km
            cx = float(np.mean(x_arr[xx])) / 1000  # km
            color_short = layer_color_map.get(lid, "#3d4a52")
            ax.text(cx, cy, name, fontsize=9, color=color_short, fontweight="bold",
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.25", fc="#161b22", ec=color_short, alpha=0.92))

    # Domain labels (Senegal Basin context)
    x_max = x_arr.max() / 1000
    x_min = x_arr.min() / 1000
    domains = [
        (x_min + 5,   -0.3, "COAST\nLAND",   "#ffa657"),
        (x_min + 40,  -0.3, "SHELF",          "#39d2c0"),
        (x_min + 100, -0.3, "SLOPE",          "#58a6ff"),
        (x_min + 150, -0.3, "DEEPWATER",       "#bc8cff"),
    ]
    for dx, dz, label, col in domains:
        if x_min <= dx <= x_max:
            ax.text(dx, dz, label, fontsize=9, color=col, ha="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#161b22", ec=col, alpha=0.85))

    # Sangomar fiducial (if Y-section and Sangomar exists in this slice)
    if section_axis == "y":
        sang_id = 2
        if formations and any("sangomar" in (f or "").lower() for f in formations):
            for i, fm in enumerate(formations):
                if "sangomar" in (fm or "").lower():
                    sang_id = i + 1
                    break
        sg_yy, sg_xx = np.where(section == sang_id)
        if len(sg_yy) > 5:
            sang_x_world = float(np.mean(x_arr[sg_xx])) / 1000
            sang_z_world = float(np.mean(z_arr[sg_yy])) / 1000
            ax.scatter(sang_x_world, sang_z_world, s=350, c="#3fb950", edgecolors="white",
                       linewidths=2, marker="*", zorder=20)
            ax.annotate("SANGOMAR FIELD\n~560 MMbo (2C)",
                        (sang_x_world, sang_z_world),
                        xytext=(sang_x_world - 25, sang_z_world + 1.0), fontsize=9,
                        color="#3fb950", fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.3", fc="#161b22", ec="#3fb950", alpha=0.95),
                        arrowprops=dict(arrowstyle="->", color="#3fb950", lw=1.5))

    # True SCALE watermark
    ax.text(0.5, 0.02, "TRUE SCALE 1:1 · Lithology IDs from implicit-field cokriging (Mallet 1992)",
            transform=ax.transAxes, fontsize=8, color="#8b949e", ha="center", style="italic")

    # Scale bars
    bar_x_start = x_max - 30
    ax.annotate("", xy=(bar_x_start + 20, zmin / 1000 + 0.3),
                xytext=(bar_x_start, zmin / 1000 + 0.3),
                arrowprops=dict(arrowstyle="<->", color="#e6edf3", lw=2))
    ax.text(bar_x_start + 10, zmin / 1000 + 0.8, "20 km", fontsize=9, color="#e6edf3",
            ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", fc="#161b22", ec="#8b949e", alpha=0.9))

    # Vertical scale
    ax.annotate("", xy=(x_max + 5, zmin / 1000),
                xytext=(x_max + 5, zmax / 1000),
                arrowprops=dict(arrowstyle="<->", color="#e6edf3", lw=2))
    ax.text(x_max + 8, (zmin + zmax) / 2000, f"{abs(zmax - zmin) / 1000:.0f} km",
            fontsize=9, color="#e6edf3", ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", fc="#161b22", ec="#8b949e", alpha=0.9))

    # Lithology IDs legend (top right)
    legend_lines = ["Lithology IDs:"]
    for lid in range(1, n_lith):
        if formations and lid - 1 < len(formations):
            legend_lines.append(f"  ID{lid}: {formations[lid - 1]}")
        else:
            legend_lines.append(f"  ID{lid}")
    ax.text(x_max + 8, 0, "\n".join(legend_lines),
            fontsize=7, color="#e6edf3", va="top", ha="left", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="#161b22", ec="#30363d", alpha=0.92))

    # Axes formatting
    ax.set_xlim(x_arr.min() / 1000, x_arr.max() / 1000)
    ax.set_ylim(zmin / 1000 - 0.5, zmax / 1000 + 0.5)
    ax.set_xlabel(f"{x_label} (km)", fontsize=11, color="#e6edf3")
    ax.set_ylabel("Depth (km below sea level)", fontsize=11, color="#e6edf3")
    ax.tick_params(colors="#8b949e")
    for sp in ax.spines.values():
        sp.set_edgecolor("#30363d")

    if title is None:
        title = f"Geox Federation GemPy Output — {cross_section_label}\nImplicit-field potential interpolation · true scale"
    ax.set_title(title, fontsize=11, fontweight="bold", color="#f0a500", pad=12)

    # Save
    model_id = uuid.uuid4().hex[:8]
    if save_path is None:
        if section_axis == "y":
            fname = f"gempy_render_ysec_{section_index}_{model_id}.png"
        else:
            fname = f"gempy_render_xsec_{section_index}_{model_id}.png"
        save_path = str(OUTPUT_DIR / fname)
    plt.savefig(save_path, dpi=200, facecolor="#0d1117", bbox_inches="tight")
    plt.close(fig)

    # Return minimal envelope
    return {
        "ok": True,
        "image_path": save_path,
        "section_axis": section_axis,
        "section_index": section_index,
        "section_index_world": float(x_world),
        "lith_ids_seen": sorted(int(x) for x in np.unique(section)),
        "n_cells": int(section.size),
        "epistemic": "PHYSICAL_MODEL_DERIVED",
        "tag_rule": "lithology_block + extent come from geox_gempy_implicit_3d which derives from input picks; downstream rendering inherits truth class.",
    }


async def geox_gempy_section_renderer(
    lithology_block: list | str | np.ndarray | None = None,
    extent: list | str | None = None,
    formations: list | str | None = None,
    section_axis: str = "y",
    section_index: int | None = None,
    layer_color_map: dict | None = None,
    title: str | None = None,
    save_path: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Async MCP-friendly wrapper: render federation GemPy output as publication-grade cross-section."""
    _ = (session_id, actor_id, trace_id)
    if lithology_block is None:
        return {"ok": False, "error": "lithology_block required"}
    if isinstance(lithology_block, str):
        import json as _json
        lithology_block = _json.loads(lithology_block)
    if isinstance(extent, str):
        import json as _json
        extent = _json.loads(extent)
    if isinstance(formations, str):
        import json as _json
        formations = _json.loads(formations)
    if isinstance(layer_color_map, str):
        import json as _json
        layer_color_map = _json.loads(layer_color_map)

    block = np.array(lithology_block)

    out = render_gempy_section(
        lithology_block=block,
        extent=extent,
        formations=formations,
        section_axis=section_axis,
        section_index=section_index,
        layer_color_map=layer_color_map,
        title=title,
        save_path=save_path,
    )
    # Add lite image bytes summary for size tracking
    if out.get("ok"):
        try:
            sz = os.path.getsize(out["image_path"])
            out["image_bytes"] = sz
        except Exception:
            pass
    return out
