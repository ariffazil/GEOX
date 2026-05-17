"""
GEOX Well Stratigraphy — LAS/CSV Loader with GR Detection
═══════════════════════════════════════════════════════════════════════════════

Generalized loader that detects depth and GR columns across LAS and CSV formats.
Supports PETRONAS naming conventions for GR curves.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("geox.stratigraphy.loader")

NULL_VALUES = {-999.25, -999, 999.25, -9999}

GR_ALIASES = [
    "GR", "GRC", "GR:1", "GR:2", "GR:3", "SGR", "CGR", "CGRC", "CGRC:1",
    "GAPI", "GAMMA", "GAMMA_RAY", "GRMA_RT_FULL_PKK",
    "GR_EDITED", "GR_COMPUTED",
]

DEPTH_ALIASES = ["DEPT", "DEPTH", "MD", "TD", "DEPT_M", "DEPT_FT", "INDEX"]


def load_well_data(
    path: str,
    gr_override: Optional[str] = None,
    depth_override: Optional[str] = None,
) -> dict:
    """
    Load well data from LAS or CSV file.

    Parameters
    ----------
    path : str
        Path to LAS or CSV file.
    gr_override : str, optional
        Force GR column name.
    depth_override : str, optional
        Force depth column name.

    Returns
    -------
    dict with keys: depth, gr, meta (well name, source, format, n_samples, etc.)
    """
    filepath = Path(path)
    ext = filepath.suffix.lower()

    if ext in (".las", ".LAS"):
        return _load_las(filepath, gr_override, depth_override)
    elif ext == ".las":
        return _load_las(filepath, gr_override, depth_override)
    elif ext in (".csv", ".CSV", ".txt"):
        return _load_csv(filepath, gr_override, depth_override)
    else:
        raise ValueError(f"Unsupported format: {ext}. Use LAS or CSV.")


def _load_las(
    path: Path,
    gr_override: Optional[str] = None,
    depth_override: Optional[str] = None,
) -> dict:
    """Load LAS file, detect depth and GR columns."""
    import lasio
    las = lasio.read(str(path), ignore_header_errors=True, engine="normal")

    null_val = -999.25
    try:
        null_val = float(las.well.NULL.value)
    except Exception:
        pass

    df = las.df().reset_index()
    df.columns = [c.upper().strip() for c in df.columns]

    for nv in NULL_VALUES:
        df.replace(nv, np.nan, inplace=True)
    df.replace(null_val, np.nan, inplace=True)

    # Detect depth column
    if depth_override and depth_override.upper() in df.columns:
        depth_col = depth_override.upper()
    else:
        depth_col = "DEPT" if "DEPT" in df.columns else df.columns[0]

    # Convert feet to metres if needed
    try:
        unit = las.curves[0].unit.upper().strip()
        if unit in ("F", "FT", "FEET"):
            df[depth_col] = df[depth_col].astype(float) * 0.3048
    except Exception:
        pass

    # Detect GR column
    gr_col = _detect_gr_column(df, gr_override)

    well_name = str(getattr(las.well, "WELL", path.stem))

    depth_raw = df[depth_col].dropna().values.astype(float)
    gr_raw = df[gr_col].dropna().values.astype(float) if gr_col else None

    return {
        "well": well_name,
        "source": str(path),
        "format": "LAS",
        "n_samples": len(depth_raw),
        "depth": depth_raw,
        "gr": gr_raw,
        "gr_col": gr_col,
        "depth_col": depth_col,
        "start_depth": float(depth_raw[0]),
        "end_depth": float(depth_raw[-1]),
        "curves": list(df.columns),
        "df": df,
    }


def _load_csv(
    path: Path,
    gr_override: Optional[str] = None,
    depth_override: Optional[str] = None,
) -> dict:
    """Load CSV file, detect depth and GR columns."""
    df = pd.read_csv(path)
    df.columns = [c.upper().strip() for c in df.columns]

    for nv in NULL_VALUES:
        df.replace(nv, np.nan, inplace=True)

    # Detect depth column
    if depth_override and depth_override.upper() in df.columns:
        depth_col = depth_override.upper()
    else:
        depth_col = next((c for c in df.columns if c in DEPTH_ALIASES), df.columns[0])

    # Detect GR column
    gr_col = _detect_gr_column(df, gr_override)

    depth_raw = df[depth_col].dropna().values.astype(float)
    gr_raw = df[gr_col].dropna().values.astype(float) if gr_col else None

    return {
        "well": path.stem,
        "source": str(path),
        "format": "CSV",
        "n_samples": len(depth_raw),
        "depth": depth_raw,
        "gr": gr_raw,
        "gr_col": gr_col,
        "depth_col": depth_col,
        "columns": list(df.columns),
        "df": df,
    }


def _detect_gr_column(df: pd.DataFrame, override: Optional[str] = None) -> Optional[str]:
    """Detect GR column from common aliases."""
    if override and override.upper() in df.columns:
        return override.upper()

    for alias in GR_ALIASES:
        if alias in df.columns:
            v = df[alias].dropna()
            if len(v) > 10 and 0 < float(v.mean()) < 300:
                return alias

    # Fallback: scan for any column with GR in name
    for c in df.columns:
        if "GR" in c.upper():
            v = df[c].dropna()
            if len(v) > 5 and 0 < float(v.mean()) < 300:
                return c

    return None
