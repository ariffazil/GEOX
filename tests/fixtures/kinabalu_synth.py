"""
geox_core.tests.fixtures.kinabalu_synth — synthetic Kinabalu-style T-D data

We do NOT have the real TZ KL2.xlsx on the VPS. We DO have the published
characteristics from the Copilot external analysis (see
docs/eureka_insights/KL2_KINABALU_2026_06_03.md):

  - 8 wells: 6 measured near-vertical, 1 deviated (BUNGA LILI-1), 1 synthetic (BULUH-1)
  - 3 Excel formats: 2 with 2-row headers, 5 with no headers, 1 with 10 cols + "SYNTHETIC" label
  - TVDSS: 0–4000 m
  - TWT: 0–3500 ms
  - V_avg: 1800–3500 m/s
  - V_int: 1500–5000 m/s
  - dV/dZ bound: |dv/dz| ≤ 50 m/s/m (matches PhysicsGuard)
  - BULUH-1: marked "SYNTHETIC" in row 0 col 8

This fixture is the E2E test corpus for Eurekas 1, 2, 4, 6, 7.

DITEMPA BUKAN DIBERI — forges are not fantasies, they run on synthetic-but-faithful data.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np


# ── Synthetic well configs ──────────────────────────────────────────────────


_KINABALU_WELLS: Dict[str, Dict[str, Any]] = {
    "BARTON-2": {
        "type": "measured",
        "deviated": False,
        "z_range": (0, 3000),
        "twt_at_td": 2620,
        "header_rows": 2,
        "n_cols": 8,
        "synthetic": False,
    },
    "ROTAN-1": {
        "type": "measured",
        "deviated": False,
        "z_range": (0, 3200),
        "twt_at_td": 2810,
        "header_rows": 2,
        "n_cols": 8,
        "synthetic": False,
    },
    "BUNGA LILI-1": {
        "type": "measured",
        "deviated": True,
        "max_inclination_deg": 45.0,
        "z_range": (0, 3500),
        "twt_at_td": 3050,
        "header_rows": 0,
        "n_cols": 8,
        "synthetic": False,
    },
    "BULUH-1": {
        "type": "synthetic",
        "deviated": False,
        "z_range": (0, 2800),
        "twt_at_td": 2480,
        "header_rows": 0,
        "n_cols": 10,
        "synthetic": True,  # has SYNTHETIC label
    },
    "MALIGAN-1": {
        "type": "measured",
        "deviated": False,
        "z_range": (0, 2900),
        "twt_at_td": 2540,
        "header_rows": 0,
        "n_cols": 8,
        "synthetic": False,
    },
    "PEKAKA-1": {
        "type": "measured",
        "deviated": False,
        "z_range": (0, 3100),
        "twt_at_td": 2700,
        "header_rows": 0,
        "n_cols": 8,
        "synthetic": False,
    },
    "SUGUT": {
        "type": "measured",
        "deviated": False,
        "z_range": (0, 2700),
        "twt_at_td": 2370,
        "header_rows": 0,
        "n_cols": 8,
        "synthetic": False,
    },
    "SOLISIP-1": {
        "type": "measured",
        "deviated": False,
        "z_range": (0, 3300),
        "twt_at_td": 2900,
        "header_rows": 0,
        "n_cols": 8,
        "synthetic": False,
    },
}


def _synth_checkshot(
    z_min: float,
    z_max: float,
    twt_at_td: float,
    n_pts: int = 12,
    compaction_k: float = 0.0006,
    noise_ms: float = 2.0,
    seed: int = 0,
) -> List[Dict[str, float]]:
    """Build a synthetic checkshot that follows Vo-K compaction with small noise."""
    rng = np.random.default_rng(seed)
    depths = np.linspace(z_min, z_max, n_pts)
    # Vo-K: TWT(z) = (2/k)·ln(1 + k·z/V₀)·1000 ; invert to get TWT at any depth
    V0 = 1800.0
    k = compaction_k
    twts = (2.0 / k) * np.log(1.0 + k * depths / V0) * 1000.0
    # Scale to land at twt_at_td at z_max
    twts *= twt_at_td / twts[-1]
    twts += rng.normal(0, noise_ms, size=len(depths))
    return [{"depth_md": float(d), "twt_ms": float(t)} for d, t in zip(depths, twts)]


def _synth_xlsx_sheet(
    well_name: str,
    cfg: Dict[str, Any],
) -> List[List[Any]]:
    """Build a single sheet's rows in the format Copilot described."""
    cs = _synth_checkshot(cfg["z_range"][0], cfg["z_range"][1], cfg["twt_at_td"])
    rows: List[List[Any]] = []

    # Header rows
    for _ in range(cfg["header_rows"]):
        rows.append([f"{well_name} Time-Depth", "", "", "", "", "", "", ""] + [""] * (cfg["n_cols"] - 8))

    # Data rows
    for d_t in cs:
        d_md = d_t["depth_md"]
        t_ms = d_t["twt_ms"]
        if cfg["deviated"]:
            # Sinusoidal deviation, max ±500 m horizontal offset
            incl = cfg.get("max_inclination_deg", 30.0)
            x = 500.0 * np.sin(np.deg2rad(incl) * d_md / cfg["z_range"][1])
            y = 200.0 * np.cos(np.deg2rad(incl) * d_md / cfg["z_range"][1])
        else:
            x, y = 0.0, 0.0
        row = [
            -d_md,  # TVDSS (positive depth, negative for surface datum)
            d_md,  # MD
            x,  # X
            y,  # Y
            t_ms,  # TWT
            d_md * 0.5,  # TVD below water
            d_md,  # SS_TVD
            t_ms / d_md * 500.0,  # Vint (proxy)
        ]
        # BULUH-1 has 2 extra columns with "SYNTHETIC" label
        if cfg["synthetic"]:
            row = row + ["SYNTHETIC", f"PSEUDO_{well_name}"]
        rows.append(row)

    # Mark first data row's first cell with "SYNTHETIC" if synthetic
    if cfg["synthetic"] and cfg["header_rows"] < len(rows):
        rows[cfg["header_rows"]][0] = "SYNTHETIC"

    return rows


def build_kinabalu_synthetic_xlsx() -> Dict[str, List[List[Any]]]:
    """Build a dict-of-sheets that mirrors TZ KL2.xlsx structure (synthetic).

    Returns:
        {sheet_name: [[row_cells], ...]} ready to be written to .xlsx
    """
    return {name: _synth_xlsx_sheet(name, cfg) for name, cfg in _KINABALU_WELLS.items()}


def get_well_config(well_name: str) -> Dict[str, Any]:
    return dict(_KINABALU_WELLS[well_name])


def list_wells() -> List[str]:
    return list(_KINABALU_WELLS.keys())


def get_synthetic_checkshot(well_name: str) -> List[Dict[str, float]]:
    cfg = _KINABALU_WELLS[well_name]
    return _synth_checkshot(
        cfg["z_range"][0],
        cfg["z_range"][1],
        cfg["twt_at_td"],
        seed=hash(well_name) % (2**31),
    )


# ── Inline self-test (can be run as `python -m tests.fixtures.kinabalu_synth`) ──


if __name__ == "__main__":
    print("=== Kinabalu Synthetic T-D Data ===")
    print(f"Wells: {len(_KINABALU_WELLS)}")
    for name, cfg in _KINABALU_WELLS.items():
        cs = get_synthetic_checkshot(name)
        z_range = f"{cs[0]['depth_md']:.0f}–{cs[-1]['depth_md']:.0f}"
        twt_range = f"{cs[0]['twt_ms']:.0f}–{cs[-1]['twt_ms']:.0f}"
        flags = []
        if cfg["synthetic"]:
            flags.append("SYNTHETIC")
        if cfg["deviated"]:
            flags.append(f"DEVIATED<{cfg.get('max_inclination_deg', 0):.0f}°")
        flag_str = " [" + ", ".join(flags) + "]" if flags else ""
        print(f"  {name:18s} | {len(cs):2d} pts | Z: {z_range:14s} m | TWT: {twt_range:14s} ms{flag_str}")
    print()
    print(f"Sheets in synthetic xlsx: {list(_KINABALU_WELLS.keys())}")
