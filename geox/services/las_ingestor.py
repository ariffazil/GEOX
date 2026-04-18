"""
LAS ingestion pipeline for GEOX Wave 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from geox.core.physics_guard import PhysicsGuard

try:
    import lasio
except ImportError:  # pragma: no cover - exercised after dependency install
    lasio = None

try:
    from welly import Well
except ImportError:  # pragma: no cover - exercised after dependency install
    Well = None


@dataclass
class LASCurveManifest:
    mnemonic: str
    unit: str
    sample_count: int
    null_count: int
    qc_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mnemonic": self.mnemonic,
            "unit": self.unit,
            "sample_count": self.sample_count,
            "null_count": self.null_count,
            "qc_flags": self.qc_flags,
        }


@dataclass
class LASManifest:
    asset_id: str
    source_path: str
    uwi: str | None
    well_name: str | None
    depth_range: tuple[float, float]
    curves: list[LASCurveManifest]
    chunk_count: int
    qcfail_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "source_path": self.source_path,
            "uwi": self.uwi,
            "well_name": self.well_name,
            "depth_range": [round(self.depth_range[0], 4), round(self.depth_range[1], 4)],
            "curves": [curve.to_dict() for curve in self.curves],
            "chunk_count": self.chunk_count,
            "qcfail_count": self.qcfail_count,
        }


class LASIngestor:
    """Read LAS 2.0/3.0 files and produce a JSON-safe manifest."""

    CURVE_MAP = {
        "NPHI": "porosity",
        "PHI": "porosity",
        "SW": "sw",
        "VSH": "vsh",
    }

    def __init__(self, guard: PhysicsGuard | None = None) -> None:
        self.guard = guard or PhysicsGuard()

    def _require_deps(self) -> None:
        if lasio is None:
            raise RuntimeError("lasio is required for LAS ingestion")

    def _curve_qc(self, mnemonic: str, values: np.ndarray) -> list[str]:
        flags: list[str] = []
        clean = values[~np.isnan(values)]
        if clean.size == 0:
            return ["ALL_NULL"]
        diffs = np.abs(np.diff(clean))
        if diffs.size and float(diffs.max()) > max(float(np.nanstd(clean)) * 5.0, 1.0):
            flags.append("SPIKE_DETECTED")
        guard_key = self.CURVE_MAP.get(mnemonic.upper())
        if guard_key:
            for value in clean[: min(50, clean.size)]:
                validation = self.guard.validate({guard_key: float(value)})
                if validation.hold:
                    flags.append(validation.status)
                    break
        return flags

    def ingest(self, path: str, asset_id: str | None = None, chunk_size: int = 200) -> LASManifest:
        self._require_deps()
        source = Path(path)
        las = lasio.read(source)
        well = Well.from_las(str(source)) if Well is not None else None
        depth_curve = np.asarray(las.index, dtype=float)
        curves: list[LASCurveManifest] = []
        qcfail_count = 0
        for curve in las.curves:
            mnemonic = curve.mnemonic.strip()
            if mnemonic.upper() in {"DEPT", "DEPTH"}:
                continue
            values = np.asarray(las[curve.mnemonic], dtype=float)
            flags = self._curve_qc(mnemonic, values)
            if flags:
                qcfail_count += 1
            curves.append(
                LASCurveManifest(
                    mnemonic=mnemonic,
                    unit=str(curve.unit or ""),
                    sample_count=int(values.size),
                    null_count=int(np.isnan(values).sum()),
                    qc_flags=flags,
                )
            )

        uwi = None
        if "UWI" in las.well:
            uwi = str(las.well["UWI"].value)
        well_name = None
        if "WELL" in las.well:
            well_name = str(las.well["WELL"].value)
        elif well is not None:
            well_name = getattr(well, "name", None)
        return LASManifest(
            asset_id=asset_id or (uwi or source.stem),
            source_path=str(source),
            uwi=uwi,
            well_name=well_name,
            depth_range=(float(np.nanmin(depth_curve)), float(np.nanmax(depth_curve))),
            curves=curves,
            chunk_count=max(1, int(np.ceil(max(depth_curve.size, 1) / chunk_size))),
            qcfail_count=qcfail_count,
        )
