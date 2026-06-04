"""
GEOX Well Stratigraphy — Config Schema & Defaults
═══════════════════════════════════════════════════════════════════════════════

project.yaml schema for the generalized stratigraphy pipeline.

All constants, colors, motifs, depo env codes, and NN ages are configurable.
The KL2 Kinabalu Basin defaults are provided as the reference implementation.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WellSource(BaseModel):
    name: str = Field(..., description="Well identifier")
    path: str = Field(..., description="Path to LAS or CSV file")
    format: str = Field("LAS", description="File format: LAS or CSV_LAS")
    lon: float | None = Field(None, description="Longitude for spatial ordering")


class ProjectInterval(BaseModel):
    zone: str = Field(..., description="Zone identifier (e.g. NN11, Stage_IVC)")
    top: float = Field(..., description="Top depth in metres MD")
    base: float = Field(..., description="Base depth in metres MD")
    depo_env: str = Field(..., description="Depositional environment code")


class ProjectConfig(BaseModel):
    project: str = Field(..., description="Project name (e.g. KL2, SABAH_2026)")
    bin_size_m: float = Field(10.0, description="Sensing layer bin size")
    min_package_thickness_m: float = Field(20.0, description="Minimum package thickness")
    p50_shift_thresh_gapi: float = Field(15.0, description="P50 shift triggers package boundary")
    gr_cut_api: float = Field(75.0, description="Net sand cutoff (50% shale concept)")
    gr_min_api: float = Field(0.0, description="GR display minimum")
    gr_max_api: float = Field(150.0, description="GR display maximum")
    gr_sand_api: float = Field(35.0, description="Clean sand / silt boundary")
    gr_silt_api: float = Field(65.0, description="Silt / shaly sand boundary")
    gr_shaly_api: float = Field(90.0, description="Shaly sand / shale boundary")
    sand_color: str = Field("#FFD54F", description="Sand fill hex color")
    shale_color: str = Field("#8D6E63", description="Shale fill hex color")
    curve_color: str = Field("#1A1A1A", description="GR curve line color")

    well_order: list[str] = Field(default_factory=list, description="Well order for correlation panel presentation")
    wells: list[WellSource] = Field(default_factory=list, description="Well data sources")
    intervals: dict[str, list[ProjectInterval]] = Field(default_factory=dict, description="Well ID -> list of intervals")

    regional_surfaces: list[dict[str, Any]] = Field(
        default_factory=list, description="Regional surfaces for tie lines: [{name, age_ma, type, color}]"
    )

    output_dir: str = Field("output", description="Output directory for PNGs and XLSX")
    dpi: int = Field(200, description="PNG resolution")
    dpi_correlation: int = Field(180, description="Correlation panel PNG resolution")


# ── Motif vocabulary (corrected 2026-05-22) ──────────────────────────────────
HUMAN_LABELS: dict[str, str] = {
    "Bell": "Fining Upward",
    "Funnel": "Coarsening Upward",  # typo: Coaserning
    "Cylindrical": "Blocky",
    "Serrated": "Serrated / Irregular Pattern",  # typo: Serated
    "High_GR_Shale": "Serrated / Irregular Pattern",
    "Symmetrical": "Crecentric",  # typo: Crecentric
    "Heterolithic": "Heterolithic",
}

MOTIF_COLORS: dict[str, str] = {
    "Fining Upward": "#1565C0",
    "Coarsening Upward": "#2E7D32",
    "Blocky": "#F9A825",
    "Serrated / Irregular Pattern": "#546E7A",
    "Crecentric": "#FF8C00",
    "Heterolithic": "#90A4AE",
}

TRACT_COLORS: dict[str, str] = {
    "LST": "#FF8F00",
    "TST": "#1565C0",
    "HST": "#2E7D32",
    "FSST": "#E65100",
    "CS": "#6A1B9A",
    "UNCERTAIN": "#78909C",
    "UNKNOWN": "#BDBDBD",
}

TRACT_ALPHA = 0.45

# ── Depositional environment codes (GDE) ────────────────────────────────────
# Format: code -> (label, (R, G, B) normalized 0-1)
DEFAULT_DEPO_EOD: dict[str, tuple[str, tuple[float, float, float]]] = {
    "COL": ("Alluvial Plain", (1.0, 0.647, 0.0)),
    "COL-HIN": ("Alluvial->Inn.N.", (0.757, 0.694, 0.455)),
    "HIN": ("Inner Neritic", (0.514, 0.737, 0.906)),
    "HIN-HMN": ("Inn.->Mid.N.", (0.333, 0.627, 0.847)),
    "HMN": ("Middle Neritic", (0.153, 0.518, 0.788)),
    "HMN-HON": ("Mid.->Out.N.", (0.078, 0.259, 0.710)),
    "HON": ("Outer Neritic", (0.0, 0.0, 0.627)),
    "HON-UBT": ("Out.N->Up.Bath.", (0.216, 0.341, 0.816)),
    "UBT": ("Upper Bathyal", (0.824, 0.682, 1.0)),
    "UBT-MBT": ("Up.->Mid.Bath.", (0.769, 0.584, 0.996)),
    "MBT": ("Middle Bathyal", (0.714, 0.482, 0.992)),
    "MBT-LBT": ("Mid.->Lo.Bath.", (0.584, 0.243, 0.996)),
    "LBT": ("Lower Bathyal", (0.451, 0.004, 0.996)),
}

DEFAULT_DEPO_RANK: dict[str, int] = {
    "COL": 0,
    "COL-HIN": 1,
    "HIN": 2,
    "HIN-HMN": 3,
    "HMN": 4,
    "HMN-HON": 5,
    "HON": 6,
    "HON-UBT": 7,
    "UBT": 8,
    "UBT-MBT": 9,
    "MBT": 10,
    "MBT-LBT": 11,
    "LBT": 12,
}

# ── Default NN ages (GPTS2020) ──────────────────────────────────────────────
DEFAULT_NN_AGES: dict[str, tuple[float, float]] = {
    "NN11C": (6.91, 7.42),
    "NN11B": (7.42, 7.67),
    "NN11A": (7.67, 8.59),
    "NN11": (6.91, 8.59),
    "NN10B": (8.59, 9.53),
    "NN10A": (9.53, 10.41),
    "NN10": (8.59, 10.41),
    "NN9": (10.41, 11.79),
    "NN8": (11.79, 12.12),
    "NN7": (12.12, 13.12),
    "NN6": (13.12, 13.65),
    "NN5": (13.65, 14.91),
    "NN4": (14.91, 17.95),
}


def default_motif_colors() -> dict[str, str]:
    return dict(MOTIF_COLORS)


def default_tract_colors() -> dict[str, str]:
    return dict(TRACT_COLORS)


def default_depo_eod() -> dict[str, tuple[str, tuple[float, float, float]]]:
    return dict(DEFAULT_DEPO_EOD)


def default_depo_rank() -> dict[str, int]:
    return dict(DEFAULT_DEPO_RANK)


def default_nn_ages() -> dict[str, tuple[float, float]]:
    return dict(DEFAULT_NN_AGES)
