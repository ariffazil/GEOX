"""
geox_core.spatial.velocity_slice — Eureka 8 (FINAL, 2026-06-03 17:55 MYT)

The velocity-as-structure eureka. Three primitives + a synthetic test cube.

Theory reference: docs/eureka_insights/E8_VELOCITY_AS_STRUCTURE_2026_06_03.md

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

import numpy as np

VP_MIN = 1500.0
VP_MAX = 6000.0


# ── Data carriers ────────────────────────────────────────────────────────────


@dataclass
class VpCube:
    """3D P-wave velocity field V(x, y, z).

    Convention: data.shape == (nx, ny, nz); data[ix, iy, iz] is Vp at (x[ix], y[iy], z[iz]).
    """

    data: np.ndarray
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    units: str = "m/s"
    source: str = "unknown"
    provenance: str = "synthetic"
    construction: str = "unknown"
    dix_horizontal_layering_assumed: bool = True
    cube_id: str = ""

    def __post_init__(self) -> None:
        if self.data.ndim != 3:
            raise ValueError(f"VpCube data must be 3D, got shape {self.data.shape}")
        if not self.cube_id:
            self.cube_id = "cube_" + hashlib.sha256(self.data.tobytes()).hexdigest()[:16]
        self.data = np.clip(self.data, VP_MIN, VP_MAX)

    @property
    def shape(self) -> tuple[int, int, int]:
        return tuple(self.data.shape)  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cube_id": self.cube_id,
            "shape": list(self.shape),
            "x_range": [float(self.x.min()), float(self.x.max())],
            "y_range": [float(self.y.min()), float(self.y.max())],
            "z_range": [float(self.z.min()), float(self.z.max())],
            "vp_min": float(self.data.min()),
            "vp_max": float(self.data.max()),
            "vp_mean": float(self.data.mean()),
            "construction": self.construction,
            "dix_horizontal_layering_assumed": self.dix_horizontal_layering_assumed,
            "physics_guard": "F2_PHYSICS_GUARD",
        }


@dataclass
class VpSlice:
    """2D Vp map at constant depth. THIS IS A STRUCTURE MAP (E8 keystone)."""

    data: np.ndarray
    x: np.ndarray
    y: np.ndarray
    depth: float
    cube_id: str = ""
    slice_id: str = ""
    smoothing_window_m: float = 0.0
    envelope: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.data.ndim != 2:
            raise ValueError(f"VpSlice data must be 2D, got shape {self.data.shape}")
        if not self.slice_id:
            self.slice_id = f"slice_z{int(self.depth)}_" + hashlib.sha256(self.data.tobytes()).hexdigest()[:12]
        self.data = np.clip(self.data, VP_MIN, VP_MAX)

    @property
    def shape(self) -> tuple[int, int]:
        return tuple(self.data.shape)  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "depth_m": float(self.depth),
            "shape": list(self.shape),
            "vp_min": float(self.data.min()),
            "vp_max": float(self.data.max()),
            "vp_mean": float(self.data.mean()),
            "vp_std": float(self.data.std()),
            "smoothing_window_m": float(self.smoothing_window_m),
            "cube_id": self.cube_id,
            "envelope": self.envelope,
            "interpretation": "Velocity slice = 2D structure map at this depth",
            "physics_guard": "F2_PHYSICS_GUARD",
        }


@dataclass
class StructuralMap:
    """The attributed Vp slice: 5 geological signals + provenance."""

    slice_data: VpSlice
    signals: dict[str, np.ndarray] = field(default_factory=dict)
    attribution_confidence: dict[str, float] = field(default_factory=dict)
    envelope: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "slice_id": self.slice_data.slice_id,
            "depth_m": self.slice_data.depth,
            "shape": list(self.slice_data.data.shape),
            "signals": {k: float(v.mean()) for k, v in self.signals.items()},
            "signal_shapes": {k: list(v.shape) for k, v in self.signals.items()},
            "attribution_confidence": self.attribution_confidence,
            "envelope": self.envelope,
            "eureka": "E8_velocity_as_structure_2026_06_03",
        }
        for sig, arr in self.signals.items():
            out[f"{sig}_min"] = float(arr.min())
            out[f"{sig}_max"] = float(arr.max())
            out[f"{sig}_std"] = float(arr.std())
        return out


# ── Primitive 1: slice_velocity_cube ────────────────────────────────────────


def slice_velocity_cube(
    cube: VpCube,
    depth: float,
    window_m: float = 0.0,
) -> VpSlice:
    """Extract a horizontal Vp slice at constant depth. Keystone primitive."""
    z_arr = cube.z
    if depth < z_arr.min() or depth > z_arr.max():
        depth = float(np.clip(depth, z_arr.min(), z_arr.max()))
        clamped = True
    else:
        clamped = False

    z_idx = int(np.argmin(np.abs(z_arr - depth)))
    actual_depth = float(z_arr[z_idx])

    if window_m > 0:
        dz = float(z_arr[1] - z_arr[0]) if len(z_arr) > 1 else 1.0
        half = max(1, int(round(window_m / (2 * dz))))
        z_lo = max(0, z_idx - half)
        z_hi = min(len(z_arr) - 1, z_idx + half)
        slice_2d = np.mean(cube.data[:, :, z_lo : z_hi + 1], axis=2)
    else:
        slice_2d = cube.data[:, :, z_idx].copy()

    envelope = {
        "requested_depth_m": float(depth),
        "actual_depth_m": actual_depth,
        "clamped": clamped,
        "vp_at_depth_mean": float(slice_2d.mean()),
        "vp_at_depth_std": float(slice_2d.std()),
        "vp_at_depth_min": float(slice_2d.min()),
        "vp_at_depth_max": float(slice_2d.max()),
        "dix_horizontal_layering_assumed": cube.dix_horizontal_layering_assumed,
        "bootstrap_risk": ("PLAUSIBLE_NOT_CLAIM" if cube.dix_horizontal_layering_assumed else "CLAIM"),
        "interpretation": "VpSlice is a 2D structure map at this depth (E8 keystone)",
        "authority": "F2_PHYSICS_GUARD",
    }

    return VpSlice(
        data=slice_2d,
        x=cube.x.copy(),
        y=cube.y.copy(),
        depth=actual_depth,
        cube_id=cube.cube_id,
        smoothing_window_m=window_m,
        envelope=envelope,
    )


# ── Primitive 2: structural_attribution ─────────────────────────────────────


_DEFAULT_LITHOLOGY_CATALOG: dict[str, dict[str, float]] = {
    "Sandstone": {"vp": 3500.0, "rho": 2300.0, "phi_typical": 0.20},
    "Limestone": {"vp": 4500.0, "rho": 2600.0, "phi_typical": 0.10},
    "Dolomite": {"vp": 5500.0, "rho": 2800.0, "phi_typical": 0.08},
    "Shale": {"vp": 2400.0, "rho": 2200.0, "phi_typical": 0.15},
    "Anhydrite": {"vp": 5000.0, "rho": 2900.0, "phi_typical": 0.05},
    "Salt": {"vp": 4500.0, "rho": 2160.0, "phi_typical": 0.00},
    "Coal": {"vp": 1800.0, "rho": 1500.0, "phi_typical": 0.10},
    "Basement": {"vp": 5800.0, "rho": 2900.0, "phi_typical": 0.02},
}


def structural_attribution(
    slice_data: VpSlice,
    physics9_catalog: dict[str, dict[str, float]] | None = None,
    matrix_vp: float = 5500.0,
    fluid_vp_brine: float = 1700.0,
    fluid_vp_gas: float = 500.0,
) -> StructuralMap:
    """Decompose Vp variation into 5 geological signals (L5 multi-channel attribution)."""
    if physics9_catalog is None:
        physics9_catalog = _DEFAULT_LITHOLOGY_CATALOG

    vp = slice_data.data
    vp_mean = float(vp.mean())
    vp_std = float(vp.std()) if vp.std() > 0 else 1.0

    sig_vp = vp.copy()

    litho_names = list(physics9_catalog.keys())
    litho_vp = np.array([physics9_catalog[n].get("vp", 3000.0) for n in litho_names])
    distances = np.abs(vp[..., None] - litho_vp)
    litho_id = np.argmin(distances, axis=-1)

    safe_vp = np.where(vp > 0, vp, 1e-9)
    phi_brine = (1.0 / safe_vp - 1.0 / matrix_vp) / (1.0 / fluid_vp_brine - 1.0 / matrix_vp)
    phi = np.clip(phi_brine, 0.0, 0.45)

    vp_normal = vp_mean
    if vp_normal > 0:
        ratio = np.clip(safe_vp / vp_normal, 0.1, 2.0)
        p_pore_norm = 1.0 - np.power(ratio, 3.0)
        p_pore_norm = np.clip(p_pore_norm, 0.0, 1.0)
    else:
        p_pore_norm = np.zeros_like(vp)

    expected_vp_brine = 1.0 / ((1.0 - phi) / matrix_vp + phi / fluid_vp_brine)
    gas_prob = np.clip(
        1.0 - (safe_vp / np.maximum(expected_vp_brine, 1.0)),
        0.0,
        1.0,
    )
    gas_prob = gas_prob * np.clip(phi / 0.05, 0.0, 1.0)

    struct_height = np.clip((vp - vp_mean) / vp_std, -3.0, 3.0)

    signals = {
        "vp": sig_vp,
        "lithology_id": litho_id.astype(float),
        "porosity": phi,
        "pore_pressure_normalized": p_pore_norm,
        "fluid_indicator_gas_probability": gas_prob,
        "structural_height_normalized": struct_height,
    }

    confidence = {
        "vp": 1.0,
        "lithology_id": 0.85,
        "porosity": 0.7,
        "pore_pressure_normalized": 0.6,
        "fluid_indicator_gas_probability": 0.5,
        "structural_height_normalized": 0.7,
    }

    litho_legend = {i: name for i, name in enumerate(litho_names)}
    envelope = {
        "vp_mean": vp_mean,
        "vp_std": float(vp_std),
        "vp_range": [float(vp.min()), float(vp.max())],
        "matrix_vp_used": matrix_vp,
        "fluid_vp_brine_used": fluid_vp_brine,
        "fluid_vp_gas_used": fluid_vp_gas,
        "lithology_catalog_size": len(litho_names),
        "lithology_legend": litho_legend,
        "honest_flags": [
            "Porosity is Wyllie-derived (PLAUSIBLE for clastics, less reliable for carbonates)",
            "Pore pressure is Eaton-derived (PLAUSIBLE in normal compaction, unreliable in geopressured zones)",
            "Fluid indicator is Vp-only proxy (full Biot-Gassmann needs Vp AND Vs)",
            "Lithology attribution is most-likely catalog match (confidence capped at 0.85)",
            "Structural height inverts in overpressure/gas zones (cross-check fluid_indicator)",
        ],
        "authority": "F2_PHYSICS_GUARD",
        "eureka": "E8_velocity_as_structure_2026_06_03",
    }

    return StructuralMap(
        slice_data=slice_data,
        signals=signals,
        attribution_confidence=confidence,
        envelope=envelope,
    )


# ── Primitive 3: bootstrap_structure ────────────────────────────────────────


def bootstrap_structure(
    checkshots: list[dict[str, Any]],
    cube: VpCube,
    target_depth: float,
    target_twt: float | None = None,
    tie_tolerance_m: float = 50.0,
) -> StructuralMap:
    """Sparse 1D well anchors + dense 2.5D Vp field -> 2D structure map.

    The keystone forge of E8. Anchors: well checkshots (1D, sparse, high
    quality) calibrate the cube's Vp scale. Extrapolation: the cube's
    2.5D field carries the anchors laterally. The slice is the structure map.
    """
    well_vp_obs: list[dict[str, float]] = []
    for cs in checkshots:
        if "depths" in cs and "twts" in cs:
            for d, t in zip(cs["depths"], cs["twts"]):
                if t > 0 and d > 0:
                    v_well = 2.0 * d / (t / 1000.0)
                    v_well = float(np.clip(v_well, VP_MIN, VP_MAX))
                    if not well_vp_obs or d > well_vp_obs[-1]["depth"]:
                        well_vp_obs.append({"depth": float(d), "vp": v_well})
        elif "depth_md" in cs and "twt_ms" in cs:
            d, t = float(cs["depth_md"]), float(cs["twt_ms"])
            if t > 0 and d > 0:
                v_well = 2.0 * d / (t / 1000.0)
                v_well = float(np.clip(v_well, VP_MIN, VP_MAX))
                well_vp_obs.append({"depth": d, "vp": v_well})

    if target_twt is not None and well_vp_obs:
        depths = [w["depth"] for w in well_vp_obs]
        twts_proxy = [w["depth"] / max(w["vp"], 1.0) * 2000.0 for w in well_vp_obs]
        target_depth = float(np.interp(target_twt, sorted(twts_proxy), sorted(depths)))

    slice_data = slice_velocity_cube(cube, target_depth, window_m=0.0)

    bulk_shift_applied = 1.0
    if well_vp_obs:
        well_vp_at_target = float(
            np.interp(
                target_depth,
                [w["depth"] for w in well_vp_obs],
                [w["vp"] for w in well_vp_obs],
            )
        )
        if well_vp_at_target > 0:
            cube_vp_at_target = float(np.mean(slice_data.data))
            shift = well_vp_at_target / cube_vp_at_target
            if abs(shift - 1.0) > 0.05:
                slice_data.data = slice_data.data * shift
                bulk_shift_applied = float(shift)
                slice_data.envelope["local_bulk_shift_applied"] = bulk_shift_applied
                slice_data.envelope["bulk_shift_evidence"] = (
                    f"well_vp_at_target={well_vp_at_target:.1f}, cube_vp_at_target={cube_vp_at_target:.1f}"
                )

    smap = structural_attribution(slice_data)

    smap.envelope["bootstrap"] = {
        "n_well_anchors": len(well_vp_obs),
        "target_depth_m": float(target_depth),
        "target_twt_ms": float(target_twt) if target_twt is not None else None,
        "tie_tolerance_m": tie_tolerance_m,
        "bulk_shift_applied": bulk_shift_applied,
        "well_anchors_preview": well_vp_obs[:5],
        "n_well_anchors_total": len(well_vp_obs),
        "eureka": "E8_bootstrap_structure_2026_06_03",
        "physics_status": (
            "PLAUSIBLE_NOT_CLAIM (2.5D Dix has known limitations)"
            if cube.dix_horizontal_layering_assumed
            else "CLAIM (synth cube; no horizontal-layer assumption)"
        ),
        "falsifiable": True,
        "falsification_test": (
            "If a new well at (x_new, y_new) drills through, the cube at that "
            "location MUST match the well's Vp within tie_tolerance_m. Otherwise "
            "the cube is wrong, not the well."
        ),
        "authority": "F2_PHYSICS_GUARD",
    }

    return smap


# ── Synthetic test cube generator ───────────────────────────────────────────


def synth_cube_with_structure(
    x_min: float = 0.0,
    x_max: float = 10000.0,
    y_min: float = 0.0,
    y_max: float = 10000.0,
    z_min: float = 0.0,
    z_max: float = 3000.0,
    nx: int = 41,
    ny: int = 41,
    nz: int = 31,
    include_anticline: bool = True,
    include_fault: bool = True,
    include_gas_pocket: bool = True,
    compaction_v0: float = 1800.0,
    compaction_k: float = 0.5,
    seed: int = 0,
) -> VpCube:
    """Build a synthetic 3D Vp cube with embedded geological structure.

    3 structures deliberately distinct in (x, y, z) so structural_attribution
    can be tested independently for each:
      - Anticline: Gaussian Vp high centred at (5000, 5000, 2000)
      - Fault: step in Vp east of x=4000, z in [1500, 2500]
      - Gas pocket: Vp low at (7000, 3000), z in [1000, 1500]
    """
    rng = np.random.default_rng(seed)
    x = np.linspace(x_min, x_max, nx)
    y = np.linspace(y_min, y_max, ny)
    z = np.linspace(z_min, z_max, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

    vp = compaction_v0 + compaction_k * Z

    if include_anticline:
        xc, yc, zc = 5000.0, 5000.0, 2000.0
        sigma_xy = 2000.0
        sigma_z = 500.0
        d2 = ((X - xc) / sigma_xy) ** 2 + ((Y - yc) / sigma_xy) ** 2 + ((Z - zc) / sigma_z) ** 2
        vp = vp + 200.0 * np.exp(-d2)

    if include_fault:
        fault_mask = (X > 4000.0) & (Z > 1500.0) & (Z < 2500.0)
        vp = np.where(fault_mask, vp + 300.0, vp)

    if include_gas_pocket:
        xc, yc, zc = 7000.0, 3000.0, 1250.0
        sigma_xy = 800.0
        sigma_z = 250.0
        d2 = ((X - xc) / sigma_xy) ** 2 + ((Y - yc) / sigma_xy) ** 2 + ((Z - zc) / sigma_z) ** 2
        vp = vp - 300.0 * np.exp(-d2)

    vp = vp + rng.normal(0.0, 15.0, size=vp.shape)

    return VpCube(
        data=vp,
        x=x,
        y=y,
        z=z,
        units="m/s",
        source="synth_cube_with_structure",
        provenance="synth_with_5_signals (compaction + anticline + fault + gas + noise)",
        construction="synthetic_with_5_signals",
        dix_horizontal_layering_assumed=False,
    )
