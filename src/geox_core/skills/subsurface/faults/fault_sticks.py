"""
GEOX Fault Stick Data Model & Ingestion
════════════════════════════════════════
Forged from paleoscan_python Fault3d / FaultSet3d patterns.

A fault is a list of fault sticks. A fault stick is a list of 3D points (vec3).
This module provides the data model, ingestion from CSV/JSON, and export to
GeoJSON for interoperability.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger("geox.fault_sticks")

# ─────────────────── DATA MODEL ───────────────────


@dataclass
class FaultStick:
    """A single fault stick: an ordered list of 3D points."""

    points: list[np.ndarray] = field(default_factory=list)
    name: str = ""

    def add_point(self, x: float, y: float, z: float) -> None:
        self.points.append(np.array([x, y, z], dtype=np.float64))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "points": [p.tolist() for p in self.points],
            "n_points": len(self.points),
        }


@dataclass
class Fault3d:
    """
    A 3D fault composed of multiple fault sticks.
    PaleoScan equivalent: paleoscan_python.Fault3d
    """

    name: str = ""
    crs: str = ""  # Coordinate Reference System identifier
    domain_in_time: bool = True
    sticks: list[FaultStick] = field(default_factory=list)

    def add_stick(self, stick: FaultStick) -> None:
        self.sticks.append(stick)

    def insert_stick(self, position: int, stick: FaultStick) -> None:
        if not (0 <= position <= len(self.sticks)):
            raise IndexError(f"Stick position {position} out of range [0..{len(self.sticks)}]")
        self.sticks.insert(position, stick)

    def __len__(self) -> int:
        return len(self.sticks)

    def __iter__(self):
        return iter(self.sticks)

    def __getitem__(self, index: int) -> FaultStick:
        return self.sticks[index]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "crs": self.crs,
            "domain_in_time": self.domain_in_time,
            "n_sticks": len(self.sticks),
            "sticks": [s.to_dict() for s in self.sticks],
        }

    def to_geojson(self) -> dict[str, Any]:
        """Export fault as GeoJSON MultiLineString."""
        coordinates = []
        for stick in self.sticks:
            coords = [p.tolist() for p in stick.points]
            if coords:
                coordinates.append(coords)
        return {
            "type": "Feature",
            "properties": {
                "name": self.name,
                "crs": self.crs,
                "domain_in_time": self.domain_in_time,
            },
            "geometry": {
                "type": "MultiLineString",
                "coordinates": coordinates,
            },
        }


@dataclass
class FaultSet3d:
    """
    A set of 3D faults.
    PaleoScan equivalent: paleoscan_python.FaultSet3d
    """

    filename: str = ""
    faults: list[Fault3d] = field(default_factory=list)

    def add_fault(self, fault: Fault3d) -> None:
        self.faults.append(fault)

    def insert_fault(self, position: int, fault: Fault3d) -> None:
        if not (0 <= position <= len(self.faults)):
            raise IndexError(f"Fault position {position} out of range [0..{len(self.faults)}]")
        self.faults.insert(position, fault)

    def __len__(self) -> int:
        return len(self.faults)

    def __iter__(self):
        return iter(self.faults)

    def __getitem__(self, index: int) -> Fault3d:
        return self.faults[index]

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "n_faults": len(self.faults),
            "faults": [f.to_dict() for f in self.faults],
        }

    def save(self, filepath: str | None = None, overwrite: bool = False) -> bool:
        """Save fault set as GeoJSON FeatureCollection."""
        path = filepath or self.filename
        if not path:
            logger.error("No filename specified for fault set save")
            return False
        try:
            import os
            if os.path.exists(path) and not overwrite:
                logger.error(f"File exists and overwrite=False: {path}")
                return False
            geojson = {
                "type": "FeatureCollection",
                "features": [f.to_geojson() for f in self.faults],
            }
            with open(path, "w") as f:
                json.dump(geojson, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Fault set save failed: {e}")
            return False


# ─────────────────── INGESTION ───────────────────


def ingest_fault_sticks_from_csv(csv_path: str) -> FaultSet3d | None:
    """
    Ingest fault sticks from a CSV with columns:
      fault_name, stick_id, x, y, z
    """
    try:
        import csv
        fault_set = FaultSet3d(filename=csv_path)
        current_fault_name = None
        current_stick_id = None
        current_stick: FaultStick | None = None
        current_fault: Fault3d | None = None

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fname = row.get("fault_name", "unknown")
                sid = row.get("stick_id", "0")
                x = float(row.get("x", 0))
                y = float(row.get("y", 0))
                z = float(row.get("z", 0))

                if fname != current_fault_name:
                    if current_fault is not None:
                        if current_stick is not None:
                            current_fault.add_stick(current_stick)
                        fault_set.add_fault(current_fault)
                    current_fault = Fault3d(name=fname)
                    current_fault_name = fname
                    current_stick = None
                    current_stick_id = None

                if sid != current_stick_id:
                    if current_stick is not None and current_fault is not None:
                        current_fault.add_stick(current_stick)
                    current_stick = FaultStick(name=f"{fname}_stick_{sid}")
                    current_stick_id = sid

                if current_stick is not None:
                    current_stick.add_point(x, y, z)

            # Finalize last stick/fault
            if current_stick is not None and current_fault is not None:
                current_fault.add_stick(current_stick)
            if current_fault is not None:
                fault_set.add_fault(current_fault)

        return fault_set
    except Exception as e:
        logger.error(f"CSV ingestion failed: {e}")
        return None


def ingest_fault_sticks_from_json(json_path: str) -> FaultSet3d | None:
    """Ingest fault sticks from GeoJSON FeatureCollection."""
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        fault_set = FaultSet3d(filename=json_path)
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            fault = Fault3d(
                name=props.get("name", "unknown"),
                crs=props.get("crs", ""),
                domain_in_time=props.get("domain_in_time", True),
            )
            geom = feature.get("geometry", {})
            if geom.get("type") == "MultiLineString":
                for line in geom.get("coordinates", []):
                    stick = FaultStick()
                    for pt in line:
                        stick.add_point(float(pt[0]), float(pt[1]), float(pt[2]) if len(pt) > 2 else 0.0)
                    fault.add_stick(stick)
            elif geom.get("type") == "LineString":
                stick = FaultStick()
                for pt in geom.get("coordinates", []):
                    stick.add_point(float(pt[0]), float(pt[1]), float(pt[2]) if len(pt) > 2 else 0.0)
                fault.add_stick(stick)
            fault_set.add_fault(fault)

        return fault_set
    except Exception as e:
        logger.error(f"JSON ingestion failed: {e}")
        return None
