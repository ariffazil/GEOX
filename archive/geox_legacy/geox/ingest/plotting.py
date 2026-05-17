"""
geox/ingest/plotting.py — Well Correlation Panel Engine
═══════════════════════════════════════════════════════════════════════

Generates multi-well log correlation panels as PNG images.
Thin engine layer — testable without MCP.

DITEMPA BUKAN DIBERI — Forged, Not Given

Curve alias groups:
  GR   → GR, GAMMA, CGR, SGR
  RT   → RT, ILD, LLD, RDEP, RESD, AT90
  RHOB → RHOB, DEN, DENS, ZDEN
  NPHI → NPHI, NEUT, TNPH, CNCF
  DT   → DT, DTC, AC
  CAL  → CAL, CALI
  SP   → SP
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("geox.plotting")

# ── Alias maps ────────────────────────────────────────────────────────────────

CURVE_ALIASES: dict[str, list[str]] = {
    "GR":   ["GR", "GAMMA", "CGR", "SGR", "GAM"],
    "RT":   ["RT", "ILD", "LLD", "LLS", "RDEP", "RESD", "RES", "AT90", "MSFL"],
    "RHOB": ["RHOB", "DEN", "DENS", "ZDEN", "RHO", "BDC"],
    "NPHI": ["NPHI", "NEUT", "TNPH", "CNCF", "PHI", "NPL"],
    "DT":   ["DT", "DTC", "AC"],
    "CAL":  ["CAL", "CALI", "CALM"],
    "SP":   ["SP"],
}

# ── Claim state constants ─────────────────────────────────────────────────────

CLAIM_EXPLORATORY  = "EXPLORATORY_VISUALIZATION"
CLAIM_COMPUTED     = "COMPUTED_AUTOPICK"
CLAIM_OBSERVED     = "OBSERVED_CURVE_PATTERN"


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class WellBundle:
    """Loaded well data for correlation."""
    well_id: str
    source_path: str
    depth_md: np.ndarray
    curves: dict[str, np.ndarray]          # canonical name → array
    depth_unit: str = "M"
    null_pct: dict[str, float] = field(default_factory=dict)
    depth_range: tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    qc_warnings: list[str] = field(default_factory=list)
    claim_state: str = CLAIM_EXPLORATORY

    @property
    def n_samples(self) -> int:
        return len(self.depth_md)


@dataclass
class PanelConfig:
    """Configuration for a correlation panel."""
    tracks: list[str]            # e.g. ["GR", "RT"]
    depth_basis: str = "MD"      # always stated explicitly
    depth_unit: str = "m"
    depth_range: Optional[tuple[float, float]] = None  # None = auto
    tops: Optional[dict[str, float]] = None  # well_id → {marker_name: depth}
    normalize: bool = True
    output_format: str = "png"
    output_formats: list[str] = field(default_factory=lambda: ["png", "csv_summary"])
    basin_hint: Optional[str] = None  # for cross-basin guardrail
    well_names: Optional[list[str]] = None  # display names per well


@dataclass
class PanelResult:
    """Output of a panel render."""
    ok: bool
    png_path: Optional[str] = None
    svg_path: Optional[str] = None
    pdf_path: Optional[str] = None
    csv_summary_path: Optional[str] = None
    wells_loaded: int = 0
    wells_failed: list[str] = field(default_factory=list)
    tracks_rendered: list[str] = field(default_factory=list)
    curve_summary: list[dict] = field(default_factory=list)
    qc_warnings: list[str] = field(default_factory=list)
    claim_state: str = CLAIM_EXPLORATORY
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        out: dict[str, Any] = {
            "ok": self.ok,
            "claim_state": self.claim_state,
            "wells_loaded": self.wells_loaded,
            "tracks_rendered": self.tracks_rendered,
            "qc_warnings": self.qc_warnings,
        }
        if self.ok:
            out["artifact"] = {
                "png_path": self.png_path,
                "svg_path": self.svg_path,
                "pdf_path": self.pdf_path,
                "csv_summary_path": self.csv_summary_path,
            }
            out["artifact"] = {k: v for k, v in out["artifact"].items() if v}
            out["curve_summary"] = self.curve_summary
        else:
            out["error_code"] = self.error_code
            out["error_message"] = self.error_message
            out["wells_failed"] = self.wells_failed
        return out


# ── LAS loading (thin wrapper around las_reader) ───────────────────────────────

def _canonicalise(arr: np.ndarray) -> np.ndarray:
    """Replace LAS null values with np.nan."""
    arr = np.array(arr, dtype=np.float64)
    for nv in (-999.25, -999.0, -999.00, -9999.0, -9999.25, 0.0):
        arr[arr == nv] = np.nan
    return arr


def _safe_curve(las_curves, *keys: str) -> Optional[np.ndarray]:
    """Try each alias key; return first non-empty match."""
    for key in keys:
        for curve in las_curves:
            if curve.mnemonic.strip().upper() == key:
                raw = np.asarray(curve.data, dtype=float)
                if len(raw) > 0:
                    return _canonicalise(raw)
    return None


def load_well_bundle(filepath: str, well_id: Optional[str] = None) -> WellBundle:
    """
    Load a LAS file and return a WellBundle.

    Args:
        filepath: Path to .las file.
        well_id: Optional identifier; derived from filename if omitted.

    Returns:
        WellBundle with depth + canonical curves.

    Raises:
        FileNotFoundError: File not found.
        ValueError: No depth curve in LAS.
    """
    import lasio

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"LAS file not found: {filepath}")

    las = lasio.read(str(path))
    derived_well_id = well_id or path.stem.replace(".las", "").replace(".LAS", "")

    # Depth curve
    depth = _safe_curve(las.curves, "DEPT", "DEPTH", "MD", "MEAS")
    if depth is None or len(depth) == 0:
        raise ValueError(f"No depth curve in {filepath}. Tried: DEPT, DEPTH, MD, MEAS.")

    # Load each alias group
    curves: dict[str, np.ndarray] = {}
    null_pct: dict[str, float] = {}
    warnings: list[str] = []

    for canon, aliases in CURVE_ALIASES.items():
        arr = _safe_curve(las.curves, *aliases)
        if arr is not None:
            curves[canon] = arr
            pct = float(np.sum(np.isnan(arr)) / max(len(arr), 1))
            null_pct[canon] = round(pct, 4)
            if pct > 0.5:
                warnings.append(f"{canon}: {round(pct*100,1)}% null — interpret with caution.")
        else:
            warnings.append(f"{canon}: not found — substituted null array.")

    return WellBundle(
        well_id=derived_well_id,
        source_path=str(path),
        depth_md=depth,
        curves=curves,
        null_pct=null_pct,
        depth_range=(float(np.nanmin(depth)), float(np.nanmax(depth))),
        qc_warnings=warnings,
    )


# ── Correlation panel plotting ─────────────────────────────────────────────────

def _render_panel(
    bundles: list[WellBundle],
    config: PanelConfig,
    output_dir: str,
) -> PanelResult:
    """
    Render a multi-well correlation panel using matplotlib.

    Args:
        bundles: List of loaded well data.
        config: Panel configuration.
        output_dir: Directory to write PNG + CSV.

    Returns:
        PanelResult with artifact paths and QC state.
    """
    import matplotlib
    matplotlib.use("Agg")  # headless — no display required
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from matplotlib.colors import Normalize

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    png_path = os.path.join(output_dir, f"geox_panel_{timestamp}.png")
    csv_path = os.path.join(output_dir, f"geox_panel_{timestamp}.csv")

    n_wells = len(bundles)
    n_tracks = len(config.tracks)

    fig_width = n_wells * 2.5 + 0.5
    fig_height = 12.0
    fig, axes = plt.subplots(
        nrows=1,
        ncols=n_wells,
        figsize=(fig_width, fig_height),
        sharey=True,
        squeeze=False,
    )

    all_warnings: list[str] = []
    curve_summary: list[dict] = []

    # Cross-basin guardrail
    if config.basin_hint:
        all_warnings.append(
            f"Basin hint: {config.basin_hint} — "
            "correlation is exploratory; do not use for stratigraphic interpretation "
            "across different basins."
        )

    # Depth limits
    all_depths = np.concatenate([b.depth_md for b in bundles])
    dmin = float(np.nanmin(all_depths)) if len(all_depths) > 0 else 0.0
    dmax = float(np.nanmax(all_depths)) if len(all_depths) > 0 else 1000.0

    for col_idx, bundle in enumerate(bundles):
        ax = axes[0, col_idx]

        for w in bundle.qc_warnings:
            all_warnings.append(f"[{bundle.well_id}] {w}")

        # Title
        display_name = (config.well_names[col_idx]
                        if config.well_names and col_idx < len(config.well_names)
                        else bundle.well_id)
        ax.set_title(display_name, fontsize=9, pad=6)

        for track_idx, track_name in enumerate(config.tracks):
            if col_idx == 0:
                ax.set_ylabel(f"Depth ({config.depth_unit})", fontsize=8)

            arr = bundle.curves.get(track_name)
            if arr is None:
                ax.text(0.5, 0.5, f"{track_name}\n(NOT FOUND)",
                        transform=ax.transAxes, ha="center", va="center",
                        fontsize=8, color="red", alpha=0.7)
                ax.set_xticks([])
                continue

            valid = ~np.isnan(arr)
            if not np.any(valid):
                ax.text(0.5, 0.5, f"{track_name}\n(all null)",
                        transform=ax.transAxes, ha="center", va="center",
                        fontsize=8, color="orange")
                continue

            x_plot = arr.copy()
            x_plot[~valid] = np.nan

            # Normalise to 0-1 range for display if requested
            if config.normalize:
                v_valid = x_plot[valid]
                v_min, v_max = np.nanmin(v_valid), np.nanmax(v_valid)
                if v_max - v_min > 1e-9:
                    x_plot = (x_plot - v_min) / (v_max - v_min)
                else:
                    x_plot = x_plot * 0.0

            depth = bundle.depth_md
            ax.plot(x_plot, depth, linewidth=0.6, color="black", alpha=0.8)
            ax.fill_betweenx(depth, 0, x_plot, linewidth=0, color=_track_color(track_name), alpha=0.35)
            ax.set_xlim(-0.05, 1.05)
            ax.set_xticks([])
            ax.invert_yaxis()

            # Depth ticks
            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=8))
            ax.tick_params(axis="y", labelsize=7)

            # Tops
            if config.tops and bundle.well_id in config.tops:
                for marker, mdepth in config.tops[bundle.well_id].items():
                    ax.axhline(y=mdepth, color="brown", linewidth=0.8, linestyle="--", alpha=0.6)
                    ax.text(1.02, mdepth, f"◆ {marker}", transform=ax.get_yaxis_transform(),
                            fontsize=6, va="center", color="brown")

            # Null pct in corner
            np_pct = bundle.null_pct.get(track_name, 0.0)
            if np_pct > 0.1:
                ax.text(0.97, 0.03, f"null: {np_pct*100:.0f}%",
                        transform=ax.transAxes, ha="right", va="bottom",
                        fontsize=6, color="gray")

            # Curve summary
            curve_summary.append({
                "well_id": bundle.well_id,
                "track": track_name,
                "n_samples": int(np.sum(valid)),
                "null_pct": round(np_pct, 4),
                "min": round(float(np.nanmin(x_plot)), 4),
                "max": round(float(np.nanmax(x_plot)), 4),
                "unit": _track_unit(track_name),
            })

        # Grid
        ax.grid(True, axis="y", linewidth=0.3, alpha=0.4)
        ax.set_axisbelow(True)

    # Shared depth label
    fig.text(0.5, 0.01, f"Depth basis: {config.depth_basis} | Datum correction: not applied | TVDSS: unavailable",
             ha="center", fontsize=7, color="gray", style="italic")

    # Claim state banner
    claim_text = f"Claim state: {config.basin_hint} — {CLAIM_EXPLORATORY}" if config.basin_hint else f"Claim state: {CLAIM_EXPLORATORY}"
    fig.text(0.5, 0.985, claim_text,
             ha="center", fontsize=7, color="darkorange",
             style="italic",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7))

    # Warning list
    if all_warnings:
        warn_text = " | ".join(all_warnings[:3])
        fig.text(0.5, 0.015, f"WARNINGS: {warn_text}",
                 ha="center", fontsize=6, color="red")

    fig.suptitle("GEOX Well Correlation Panel — Exploratory Visualization",
                 fontsize=11, y=0.99)
    plt.tight_layout(rect=[0, 0.02, 1, 0.97])
    fig.savefig(png_path, dpi=150, bbox_inches="tight", format="png")
    svg_path = None
    pdf_path = None
    if "svg" in config.output_formats:
        svg_path = os.path.splitext(png_path)[0] + ".svg"
        fig.savefig(svg_path, bbox_inches="tight", format="svg")
    if "pdf" in config.output_formats:
        pdf_path = os.path.splitext(png_path)[0] + ".pdf"
        fig.savefig(pdf_path, bbox_inches="tight", format="pdf")
    plt.close(fig)

    # Write CSV summary
    _write_csv_summary(csv_path, curve_summary)

    return PanelResult(
        ok=True,
        png_path=png_path,
        svg_path=svg_path,
        pdf_path=pdf_path,
        csv_summary_path=csv_path,
        wells_loaded=n_wells,
        tracks_rendered=config.tracks,
        curve_summary=curve_summary,
        qc_warnings=all_warnings,
        claim_state=CLAIM_EXPLORATORY,
    )


def _track_color(track: str) -> str:
    return {
        "GR":   "green",
        "RT":   "red",
        "RHOB": "blue",
        "NPHI": "orange",
        "DT":   "purple",
        "CAL":  "brown",
        "SP":   "gray",
    }.get(track, "black")


def _track_unit(track: str) -> str:
    return {
        "GR":   "gAPI",
        "RT":   "ohm.m",
        "RHOB": "g/cc",
        "NPHI": "v/v",
        "DT":   "us/ft",
        "CAL":  "in",
        "SP":   "mV",
    }.get(track, "")


def _write_csv_summary(csv_path: str, curve_summary: list[dict]) -> None:
    import csv
    if not curve_summary:
        return
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(curve_summary[0].keys()))
        writer.writeheader()
        writer.writerows(curve_summary)


# ── Public entry point ─────────────────────────────────────────────────────────

def render_correlation_panel(
    las_paths: list[str],
    well_names: Optional[list[str]] = None,
    tracks: Optional[list[str]] = None,
    output_dir: str = "/tmp/geox_panels",
    depth_range: Optional[list[float]] = None,
    tops: Optional[dict[str, dict[str, float]]] = None,
    normalize: bool = True,
    basin_hint: Optional[str] = None,
    well_ids: Optional[list[str]] = None,
    output_formats: Optional[list[str]] = None,
) -> PanelResult:
    """
    Generate a multi-well correlation panel PNG.

    Args:
        las_paths:       List of .las file paths.
        well_names:      Display names for each well (optional).
        tracks:          Track curve names to display (default: ["GR", "RT"]).
        output_dir:      Directory to write output files.
        depth_range:     [min, max] depth filter (optional).
        tops:            {well_id: {marker_name: depth}} (optional).
        normalize:       Normalise each track to 0–1 for display.
        basin_hint:      Basin name for cross-basin guardrail warning.
        well_ids:        Internal IDs for each well (optional, derived from paths if None).

    Returns:
        PanelResult with artifact paths or error state.
    """
    tracks = tracks or ["GR", "RT"]
    well_ids = well_ids or [Path(p).stem.replace(".las", "").replace(".LAS", "") for p in las_paths]

    bundles: list[WellBundle] = []
    wells_failed: list[str] = []

    for path, wid in zip(las_paths, well_ids):
        try:
            bundle = load_well_bundle(path, well_id=wid)

            # Apply depth filter if specified
            if depth_range:
                dmin, dmax = depth_range
                mask = (bundle.depth_md >= dmin) & (bundle.depth_md <= dmax)
                bundle.depth_md = bundle.depth_md[mask]
                for cname, carray in bundle.curves.items():
                    bundle.curves[cname] = carray[mask]
                bundle.qc_warnings.append(f"Depth filtered to {dmin}–{dmax} m")

            # Cross-basin guardrail
            if basin_hint:
                bundle.claim_state = CLAIM_EXPLORATORY
                bundle.qc_warnings.append(
                    f"Cross-basin guardrail active: basin='{basin_hint}' — "
                    "this panel is for visual/testing purposes only."
                )

            bundles.append(bundle)
        except Exception as exc:
            wells_failed.append(f"{wid}: {exc}")
            logger.warning(f"Failed to load LAS {path}: {exc}")

    if not bundles:
        return PanelResult(
            ok=False,
            error_code="NO_WELLS_LOADED",
            error_message="Could not load any wells. Check LAS file paths.",
            wells_failed=wells_failed,
            claim_state=CLAIM_EXPLORATORY,
        )

    config = PanelConfig(
        tracks=tracks,
        depth_basis="MD",
        depth_unit="m",
        depth_range=tuple(depth_range) if depth_range else None,
        tops=tops,
        normalize=normalize,
        basin_hint=basin_hint,
        well_names=well_names,
        output_formats=output_formats or ["png", "csv_summary"],
    )

    result = _render_panel(bundles, config, output_dir)
    result.wells_failed = wells_failed

    # Write vault receipt
    _write_vault_receipt(result)

    return result


def _write_vault_receipt(result: PanelResult) -> None:
    """Write a VAULT999-compatible receipt for the panel artifact."""
    receipt = {
        "vault": "VAULT999",
        "tool": "geox_well_correlation_panel",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ok": result.ok,
        "wells_loaded": result.wells_loaded,
        "tracks_rendered": result.tracks_rendered,
        "claim_state": result.claim_state,
        "png_path": result.png_path,
        "sha256": _sha256_file(result.png_path) if result.png_path else None,
    }
    receipt_path = os.path.join(os.path.dirname(result.png_path or "/tmp"), "panel_receipt.json")
    if result.png_path:
        import json
        with open(receipt_path, "w") as f:
            json.dump(receipt, f, indent=2, default=str)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
