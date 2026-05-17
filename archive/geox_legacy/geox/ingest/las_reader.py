"""
LAS File Reader — Seal C Phase 2
DITEMPA BUKAN DIBERI

Parses real .las (Log ASCII Standard) files into depth-indexed curve arrays.
Used by geox_well_load_bundle when a real LAS file path is provided.

Supports LAS 1.2 and 2.0.
Curve mapping:
  DEPT / DEPTH → depth_md
  GR / GAM → gamma_ray
  RT / RES / RESIST → resistivity (ohm.m)
  RHOB / RHO → bulk density (g/cc)
  NPHI / PHI → neutron porosity (v/v)
  CAL / CALI → caliper
  SP → spontaneous potential
"""

from __future__ import annotations

import lasio
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CurveBundle:
    """Container for loaded LAS curve data."""
    well_id: str
    depth_md: np.ndarray
    gr: Optional[np.ndarray] = None
    rt: Optional[np.ndarray] = None
    rhob: Optional[np.ndarray] = None
    nphi: Optional[np.ndarray] = None
    cal: Optional[np.ndarray] = None
    sp: Optional[np.ndarray] = None
    null_pct: dict = field(default_factory=dict)
    depth_range: tuple = field(default_factory=lambda: (0.0, 0.0))
    provenance: str = "las_file"


@dataclass
class CurveManifestEntry:
    """Single curve metadata for QC reporting."""
    mnemonic: str
    unit: str
    null_pct: float
    range_min: float
    range_max: float


def _canonicalise(arr: Optional[np.ndarray]) -> Optional[np.ndarray]:
    """Replace LAS null value (-999.25 etc.) with np.nan."""
    if arr is None:
        return None
    arr = np.array(arr, dtype=np.float64)
    null_values = {-999.25, -999.0, -999.00, -9999.0, -9999.25, 0.0}
    for nv in null_values:
        arr[arr == nv] = np.nan
    return arr


def _safe_curve(las: lasio.LasFile, *keys: str) -> Optional[np.ndarray]:
    """Try each key alias until one has data."""
    for key in keys:
        if key in las.curves:
            raw = las[key].data
            if raw is not None and len(raw) > 0:
                return _canonicalise(raw)
    return None


def _null_pct(arr: Optional[np.ndarray]) -> float:
    if arr is None:
        return 1.0
    return float(np.sum(np.isnan(arr)) / max(len(arr), 1))


def load_las(filepath: str, well_id: str) -> CurveBundle:
    """Load a .las file and return depth-indexed curve bundle.

    Args:
        filepath: Path to .las file on disk.
        well_id: Well identifier (used in provenance).

    Returns:
        CurveBundle with depth array and available curves.

    Raises:
        FileNotFoundError: If filepath does not exist.
        ValueError: If no depth curve found in LAS file.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"LAS file not found: {filepath}")

    las = lasio.read(str(path))

    # Depth — check common mnemonics
    depth = _safe_curve(las, "DEPT", "DEPTH", "MD", "MEAS")
    if depth is None or len(depth) == 0:
        raise ValueError(f"No depth curve found in {filepath}. Tried: DEPT, DEPTH, MD, MEAS.")

    # Map curves by alias groups
    gr   = _safe_curve(las, "GR", "GAM", "GRC", "SGR")
    rt   = _safe_curve(las, "RT", "RES", "RESIST", "LLD", "LLS", "MSFL")
    rhob = _safe_curve(las, "RHOB", "RHO", "BDC", "DEN")
    nphi = _safe_curve(las, "NPHI", "PHI", "NPL", "CNC")
    cal  = _safe_curve(las, "CAL", "CALI", "CALM")
    sp   = _safe_curve(las, "SP")

    null_pct = {
        "GR": round(_null_pct(gr), 4),
        "RT": round(_null_pct(rt), 4),
        "RHOB": round(_null_pct(rhob), 4),
        "NPHI": round(_null_pct(nphi), 4),
        "CAL": round(_null_pct(cal), 4),
        "SP": round(_null_pct(sp), 4),
    }

    return CurveBundle(
        well_id=well_id,
        depth_md=depth,
        gr=gr,
        rt=rt,
        rhob=rhob,
        nphi=nphi,
        cal=cal,
        sp=sp,
        null_pct=null_pct,
        depth_range=(float(np.nanmin(depth)), float(np.nanmax(depth))),
        provenance=f"las_file:{path.name}",
    )


def curve_manifest_from_bundle(bundle: CurveBundle) -> list[CurveManifestEntry]:
    """Build curve_manifest from a CurveBundle for geox_well_load_bundle response."""
    entries = []
    curve_map = [
        ("DEPTH_MD", "m", bundle.depth_md),
        ("GR", "gAPI", bundle.gr),
        ("RT", "ohm.m", bundle.rt),
        ("RHOB", "g/cc", bundle.rhob),
        ("NPHI", "v/v", bundle.nphi),
        ("CAL", "in", bundle.cal),
        ("SP", "mV", bundle.sp),
    ]
    for mnemonic, unit, arr in curve_map:
        if arr is not None:
            valid = arr[~np.isnan(arr)]
            range_min = float(np.min(valid)) if len(valid) > 0 else 0.0
            range_max = float(np.max(valid)) if len(valid) > 0 else 0.0
            entries.append(CurveManifestEntry(
                mnemonic=mnemonic,
                unit=unit,
                null_pct=bundle.null_pct.get(mnemonic.split("_")[0], _null_pct(arr)),
                range_min=range_min,
                range_max=range_max,
            ))
    return entries
