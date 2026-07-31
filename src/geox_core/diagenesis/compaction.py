"""compaction.py — Mechanical compaction models. Athy (1930), Sclater & Christie (1980)."""
from __future__ import annotations
import math

def athy_porosity(depth_m: float, surface_porosity: float = 0.45, compaction_coeff: float = 0.0004) -> float:
    return surface_porosity * math.exp(-compaction_coeff * depth_m)

def sclater_christie_porosity(lithology: str, depth_m: float) -> float:
    params = {"sandstone": (0.49, 0.00027), "shale": (0.63, 0.00051), "carbonate": (0.70, 0.00055), "limestone": (0.70, 0.00055), "dolomite": (0.40, 0.00022)}
    phi0, c = params.get(lithology.lower(), (0.50, 0.00035))
    return phi0 * math.exp(-c * depth_m)

def compaction_correction(measured_porosity: float, depth_m: float, lithology: str = "sandstone") -> dict:
    expected = sclater_christie_porosity(lithology, depth_m)
    residual = measured_porosity - expected
    flag = "NORMAL_COMPACTION" if abs(residual) < 0.02 else ("UNDERCOMPACTED" if residual > 0.03 else "OVERCOMPACTED")
    return {"measured_phi": round(measured_porosity, 3), "expected_phi": round(expected, 3), "residual": round(residual, 3), "lithology": lithology, "depth_m": depth_m, "flag": flag, "model": "Sclater-Christie-1980"}
