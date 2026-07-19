"""
geox_core.engines.potential_fields — Gravity & Magnetic Forward Modeling
═══════════════════════════════════════════════════════════════════════
Physics9 bridge: ρ → Δg (gravity), χ → ΔT (magnetics)

Implements:
  - Bouguer anomaly computation (Free-Air, Bouguer, terrain corrections)
  - Gravity forward modeling (voxel superposition)
  - Magnetic forward modeling (dipole field from susceptibility)
  - Joint gravity-magnetic interpretation

Physics:
    Δg = G · ∫∫∫ ρ(r) / |r - r_obs|² dV          [Bouguer slab: Δg = 2πGρh]
    ΔT = μ₀/4π · ∫∫∫ M(r) · ∇(1/|r-r_obs|) dV   [Magnetic dipole]
    G = 6.674e-11 m³/(kg·s²)                       [Gravitational constant]
    μ₀ = 4π × 10⁻⁷ T·m/A                           [Vacuum permeability]

Constitutional: F2 (evidence-labeled), F4 (reduce entropy), F9 (physics-only).
Author: FORGE (000Ω) | DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any, Literal

import numpy as np

logger = logging.getLogger("geox.potential_fields")

# ─── Constants ───────────────────────────────────────────────────────────────

G_CONST = 6.674e-11       # m³/(kg·s²) — gravitational constant
MU_0 = 4 * np.pi * 1e-7  # T·m/A — vacuum permeability
EARTH_RADIUS_M = 6371000  # m
BOUGUER_DENSITY = 2670    # kg/m³ — standard reduction density
MGAL_PER_MS2 = 1e5 / 1e2  # conversion: m/s² → mGal (1 mGal = 1e-5 m/s²)


# ─── Enums ───────────────────────────────────────────────────────────────────


class AnomalyType(StrEnum):
    FREE_AIR = "free_air"
    BOUGUER = "bouguer"
    COMPLETE_BOUGUER = "complete_bouguer"
    RESIDUAL_BOUUGUER = "residual_bouguer"
    TOTAL_FIELD_MAGNETIC = "total_field_magnetic"


class CorrectionMethod(StrEnum):
    SLAB = "slab"           # infinite slab approximation
    VOXEL = "voxel"         # discrete voxel superposition
    TESSEROID = "tesseroid"  # spherical (regional)


# ─── Data Classes ────────────────────────────────────────────────────────────


@dataclass
class GravityAnomaly:
    """Result of gravity forward modeling."""
    anomaly_type: AnomalyType
    values_mgal: np.ndarray
    x_coords: np.ndarray
    y_coords: np.ndarray
    density_contrast: float  # kg/m³
    method: CorrectionMethod
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "values_mgal": self.values_mgal.tolist(),
            "x_coords": self.x_coords.tolist(),
            "y_coords": self.y_coords.tolist(),
            "density_contrast_kg_m3": self.density_contrast,
            "method": self.method.value,
            "min_mgal": float(np.min(self.values_mgal)),
            "max_mgal": float(np.max(self.values_mgal)),
            "mean_mgal": float(np.mean(self.values_mgal)),
            "metadata": self.metadata,
        }


@dataclass
class MagneticAnomaly:
    """Result of magnetic forward modeling."""
    anomaly_type: AnomalyType
    values_nt: np.ndarray
    x_coords: np.ndarray
    y_coords: np.ndarray
    susceptibility_si: float
    inclination_deg: float
    declination_deg: float
    method: CorrectionMethod
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "values_nt": self.values_nt.tolist(),
            "x_coords": self.x_coords.tolist(),
            "y_coords": self.y_coords.tolist(),
            "susceptibility_si": self.susceptibility_si,
            "inclination_deg": self.inclination_deg,
            "declination_deg": self.declination_deg,
            "method": self.method.value,
            "min_nt": float(np.min(self.values_nt)),
            "max_nt": float(np.max(self.values_nt)),
            "mean_nt": float(np.mean(self.values_nt)),
            "metadata": self.metadata,
        }


@dataclass
class BouguerCorrections:
    """Complete Bouguer anomaly corrections."""
    observed_gravity_mgal: np.ndarray
    latitude_correction_mgal: np.ndarray
    free_air_correction_mgal: np.ndarray
    bouguer_correction_mgal: np.ndarray
    terrain_correction_mgal: np.ndarray
    complete_bouguer_mgal: np.ndarray
    x_coords: np.ndarray
    y_coords: np.ndarray
    elevations_m: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        return {
            "station_count": len(self.observed_gravity_mgal),
            "complete_bouguer_range": [
                float(np.min(self.complete_bouguer_mgal)),
                float(np.max(self.complete_bouguer_mgal)),
            ],
            "mean_free_air_correction_mgal": float(np.mean(self.free_air_correction_mgal)),
            "mean_bouguer_correction_mgal": float(np.mean(self.bouguer_correction_mgal)),
        }


# ─── Free-Air Correction ────────────────────────────────────────────────────


def free_air_correction(elevation_m: np.ndarray) -> np.ndarray:
    """
    Free-Air Correction (FAC): accounts for elevation above geoid.

    FAC = 0.3086 × h [mGal], where h = elevation in meters.
    """
    return 0.3086 * elevation_m


# ─── Bouguer Slab Correction ────────────────────────────────────────────────


def bouguer_slab_correction(
    elevation_m: np.ndarray,
    density_kg_m3: float = BOUGUER_DENSITY,
) -> np.ndarray:
    """
    Bouguer Slab Correction: removes gravitational effect of infinite slab.

    BSC = 2πGρh = 0.04193 × ρ × h [mGal]
    where ρ in g/cm³, h in meters.
    """
    rho_gcc = density_kg_m3 / 1000.0
    return 0.04193 * rho_gcc * elevation_m


# ─── Latitude Correction ────────────────────────────────────────────────────


def latitude_correction(latitude_deg: np.ndarray) -> np.ndarray:
    """
    Theoretical gravity at latitude using WGS84 normal gravity formula.

    γ(φ) = 978032.67715 × (1 + 0.0052790414 sin²φ + 0.0000232718 sin⁴φ) [mGal]
    """
    lat_rad = np.deg2rad(latitude_deg)
    sin2 = np.sin(lat_rad) ** 2
    sin4 = sin2 ** 2
    return 978032.67715 * (1.0 + 0.0052790414 * sin2 + 0.0000232718 * sin4)


# ─── Gravity Forward: Voxel Superposition ───────────────────────────────────


def gravity_forward_voxel(
    x_obs: np.ndarray,
    y_obs: np.ndarray,
    z_obs: np.ndarray,
    x_nodes: np.ndarray,
    y_nodes: np.ndarray,
    z_nodes: np.ndarray,
    density_contrast: np.ndarray,
    voxel_size_m: tuple[float, float, float] = (100.0, 100.0, 100.0),
) -> np.ndarray:
    """
    Gravity forward model using voxel superposition.

    Δg_z(r_obs) = G · Σ [Δρ_i · V_i · (z_obs - z_i) / |r_obs - r_i|³]

    Each voxel contributes as a point mass at its centre.
    V_i = dx × dy × dz

    Args:
        x_obs, y_obs, z_obs: Observation points (1D arrays)
        x_nodes, y_nodes, z_nodes: Voxel centres (1D arrays)
        density_contrast: Δρ at each voxel [kg/m³]
        voxel_size_m: (dx, dy, dz) in meters

    Returns:
        Δg_z at each observation point [mGal]
    """
    G = G_CONST
    dx, dy, dz = voxel_size_m
    volume = dx * dy * dz

    n_obs = len(x_obs)
    n_vox = len(x_nodes)
    dg = np.zeros(n_obs)

    for i in range(n_obs):
        for j in range(n_vox):
            rx = x_obs[i] - x_nodes[j]
            ry = y_obs[i] - y_nodes[j]
            rz = z_obs[i] - z_nodes[j]
            r = math.sqrt(rx ** 2 + ry ** 2 + rz ** 2)
            if r < 1.0:
                r = 1.0  # singularity guard

            # Vertical component of gravitational attraction
            dg[i] += G * density_contrast[j] * volume * rz / (r ** 3)

    # Convert to mGal
    return dg * 1e5


# ─── Gravity Forward: Bouguer Slab (Fast Screening) ─────────────────────────


def gravity_forward_slab(
    x_obs: np.ndarray,
    y_obs: np.ndarray,
    thickness_m: float,
    density_contrast_kg_m3: float,
) -> np.ndarray:
    """
    Infinite Bouguer slab approximation — fast screening grade.

    Δg = 2πGΔρh [mGal] = 0.04193 × Δρ(g/cm³) × h(m)

    Returns constant anomaly (slab is infinite).
    """
    delta_rho_gcc = density_contrast_kg_m3 / 1000.0
    dg_mgal = 0.04193 * delta_rho_gcc * thickness_m
    return np.full_like(x_obs, dg_mgal, dtype=float)


# ─── Magnetic Forward: Voxel Dipole ─────────────────────────────────────────


def magnetic_forward_voxel(
    x_obs: np.ndarray,
    y_obs: np.ndarray,
    z_obs: np.ndarray,
    x_nodes: np.ndarray,
    y_nodes: np.ndarray,
    z_nodes: np.ndarray,
    susceptibility: np.ndarray,
    inclination_deg: float = 0.0,
    declination_deg: float = 0.0,
    voxel_size_m: tuple[float, float, float] = (100.0, 100.0, 100.0),
) -> np.ndarray:
    """
    Magnetic forward model using voxel dipole superposition.

    ΔT(r_obs) = μ₀/4π · Σ [M_i · (3(m̂·r̂)r̂ - m̂) / |r|³] · V_i · B̂₀

    where:
        M_i = χ_i · B₀/μ₀  (magnetisation)
        m̂ = direction of magnetisation
        r̂ = unit vector from source to observer
        B̂₀ = direction of ambient field

    Simplified: total field anomaly in direction of inducing field.

    Args:
        x_obs, y_obs, z_obs: Observation points
        x_nodes, y_nodes, z_nodes: Voxel centres
        susceptibility: χ at each voxel [SI]
        inclination_deg: Geomagnetic inclination
        declination_deg: Geomagnetic declination
        voxel_size_m: (dx, dy, dz)

    Returns:
        ΔT at each observation point [nT]
    """
    B0 = 50000e-9  # T — typical Earth's field ~50,000 nT
    mu0 = MU_0
    dx, dy, dz = voxel_size_m
    volume = dx * dy * dz

    # Ambient field direction
    inc = np.deg2rad(inclination_deg)
    dec = np.deg2rad(declination_deg)
    F0_x = B0 * np.cos(inc) * np.cos(dec)
    F0_y = B0 * np.cos(inc) * np.sin(dec)
    F0_z = B0 * np.sin(inc)
    F0_mag = B0

    n_obs = len(x_obs)
    n_vox = len(x_nodes)
    dt = np.zeros(n_obs)

    for i in range(n_obs):
        for j in range(n_vox):
            rx = x_obs[i] - x_nodes[j]
            ry = y_obs[i] - y_nodes[j]
            rz = z_obs[i] - z_nodes[j]
            r = math.sqrt(rx ** 2 + ry ** 2 + rz ** 2)
            if r < 1.0:
                r = 1.0

            # Unit vector
            rhat_x, rhat_y, rhat_z = rx / r, ry / r, rz / r

            # Magnetisation direction ≈ ambient field direction (induced only)
            mhat_x, mhat_y, mhat_z = F0_x / F0_mag, F0_y / F0_mag, F0_z / F0_mag

            # Dot product m̂ · r̂
            m_dot_r = mhat_x * rhat_x + mhat_y * rhat_y + mhat_z * rhat_z

            # Dipole field: B = μ₀/4π · M · V · (3(m̂·r̂)r̂ - m̂) / r³
            factor = mu0 / (4.0 * np.pi) * susceptibility[j] * B0 / mu0 * volume / (r ** 3)

            Bx = factor * (3.0 * m_dot_r * rhat_x - mhat_x)
            By = factor * (3.0 * m_dot_r * rhat_y - mhat_y)
            Bz = factor * (3.0 * m_dot_r * rhat_z - mhat_z)

            # Total field anomaly (projection onto ambient field direction)
            dt[i] += (Bx * F0_x + By * F0_y + Bz * F0_z) / F0_mag

    # Convert to nT
    return dt * 1e9


# ─── Magnetic Forward: Prism (Fast Screening) ───────────────────────────────


def magnetic_forward_prism(
    x_obs: np.ndarray,
    susceptibility_si: float,
    depth_top_m: float,
    depth_bottom_m: float,
    width_m: float = 1000.0,
    inclination_deg: float = 0.0,
    declination_deg: float = 0.0,
) -> np.ndarray:
    """
    Simplified magnetic anomaly from a 2D prism (horizontal cylinder approximation).

    For screening-grade assessment of magnetic response.
    """
    B0 = 50000e-9  # T
    mu0 = MU_0
    M = susceptibility_si * B0 / mu0  # magnetisation

    inc = np.deg2rad(inclination_deg)
    np.deg2rad(declination_deg)

    # Effective depth to centre
    z_c = (depth_top_m + depth_bottom_m) / 2.0
    thickness = depth_bottom_m - depth_top_m

    # Horizontal cylinder approximation
    # ΔT ≈ 2π · μ₀ · M · R² · sin(I) / (x² + z²)
    n_obs = len(x_obs)
    dt = np.zeros(n_obs)

    for i in range(n_obs):
        x = x_obs[i]
        r2 = x ** 2 + z_c ** 2
        if r2 < 1.0:
            r2 = 1.0

        # Simplified total field anomaly
        dt[i] = (mu0 / (4.0 * np.pi)) * M * thickness * width_m * z_c * np.sin(inc) / (r2 ** 1.5)

    return dt * 1e9  # nT


# ─── Complete Bouguer Anomaly Pipeline ──────────────────────────────────────


def compute_complete_bouguer(
    observed_gravity_mgal: np.ndarray,
    elevations_m: np.ndarray,
    latitudes_deg: np.ndarray,
    longitudes_deg: np.ndarray,
    reduction_density_kg_m3: float = BOUGUER_DENSITY,
    terrain_correction_mgal: np.ndarray | None = None,
) -> BouguerCorrections:
    """
    Complete Bouguer Anomaly computation pipeline.

    CBA = g_obs - γ(lat) + FAC - BSC + TC

    where:
        γ(lat) = theoretical gravity at latitude
        FAC = Free-Air Correction = 0.3086 × h
        BSC = Bouguer Slab Correction = 0.04193 × ρ × h
        TC = Terrain Correction (optional)
    """
    n = len(observed_gravity_mgal)

    # Latitude correction (theoretical gravity)
    lat_corr = latitude_correction(latitudes_deg)

    # Free-Air Correction
    fac = free_air_correction(elevations_m)

    # Bouguer Slab Correction
    bsc = bouguer_slab_correction(elevations_m, reduction_density_kg_m3)

    # Terrain correction (if not provided, set to zero)
    tc = terrain_correction_mgal if terrain_correction_mgal is not None else np.zeros(n)

    # Complete Bouguer Anomaly
    cba = observed_gravity_mgal - lat_corr + fac - bsc + tc

    x = longitudes_deg
    y = latitudes_deg

    return BouguerCorrections(
        observed_gravity_mgal=observed_gravity_mgal,
        latitude_correction_mgal=lat_corr,
        free_air_correction_mgal=fac,
        bouguer_correction_mgal=bsc,
        terrain_correction_mgal=tc,
        complete_bouguer_mgal=cba,
        x_coords=x,
        y_coords=y,
        elevations_m=elevations_m,
    )


# ─── Screening-Grade Bouguer Anomaly Map ────────────────────────────────────


def bouguer_anomaly_map(
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    elevation_grid: np.ndarray,
    density_contrast_kg_m3: float = -400.0,
    latitude_deg: float = 4.0,
    method: Literal["slab", "voxel"] = "slab",
) -> GravityAnomaly:
    """
    Generate a screening-grade Bouguer anomaly map.

    For rapid basin screening — not full geodetic precision.
    """
    n_x, n_y = x_grid.shape if x_grid.ndim == 2 else (len(x_grid), 1)

    if x_grid.ndim == 1:
        xx, yy = np.meshgrid(x_grid, y_grid)
    else:
        xx, yy = x_grid, y_grid

    if method == "slab":
        # Fast: Bouguer slab + free-air
        fac = free_air_correction(elevation_grid)
        bsc = bouguer_slab_correction(elevation_grid, BOUGUER_DENSITY + density_contrast_kg_m3)
        values = fac - bsc
    else:
        # Voxel: requires 3D model — placeholder
        values = np.zeros_like(elevation_grid)

    return GravityAnomaly(
        anomaly_type=AnomalyType.COMPLETE_BOUGUER,
        values_mgal=values.flatten(),
        x_coords=xx.flatten(),
        y_coords=yy.flatten(),
        density_contrast=density_contrast_kg_m3,
        method=CorrectionMethod.SLAB if method == "slab" else CorrectionMethod.VOXEL,
        metadata={
            "epistemic_rung": 2 if method == "slab" else 3,
            "note": "Screening-grade. Full inversion requires voxel model.",
        },
    )


# ─── Joint Gravity-Magnetic Interpretation ──────────────────────────────────


def joint_gravity_magnetic_model(
    gravity_anomaly: GravityAnomaly,
    magnetic_anomaly: MagneticAnomaly,
    density_susceptibility_ratio: float = 0.0001,
) -> dict[str, Any]:
    """
    Joint interpretation of gravity and magnetic anomalies.

    Cross-plots density contrast vs susceptibility to identify:
      - Sedimentary basins (low ρ, low χ)
      - Igneous intrusions (high ρ, high χ)
      - Salt bodies (low ρ, very low χ)
      - Basement highs (high ρ, moderate χ)
    """
    # Normalize anomalies
    g_norm = (gravity_anomaly.values_mgal - np.mean(gravity_anomaly.values_mgal))
    g_norm = g_norm / (np.std(g_norm) + 1e-6)

    m_norm = (magnetic_anomaly.values_nt - np.mean(magnetic_anomaly.values_nt))
    m_norm = m_norm / (np.std(m_norm) + 1e-6)

    # Cross-correlation
    n = min(len(g_norm), len(m_norm))
    r_gm = float(np.corrcoef(g_norm[:n], m_norm[:n])[0, 1])

    # Classification
    if r_gm > 0.7:
        interpretation = "CORRELATED — density and susceptibility vary together (igneous basement control)"
    elif r_gm < -0.3:
        interpretation = "ANTI-CORRELATED — possible salt or evaporite (low density, low susceptibility)"
    elif abs(r_gm) < 0.3:
        interpretation = "UNCORRELATED — independent sources (sedimentary + basement mix)"
    else:
        interpretation = "WEAK_CORRELATION — ambiguous, requires 3D modeling"

    return {
        "cross_correlation": round(r_gm, 4),
        "interpretation": interpretation,
        "gravity_mean_mgal": float(np.mean(gravity_anomaly.values_mgal)),
        "magnetic_mean_nt": float(np.mean(magnetic_anomaly.values_nt)),
        "density_susceptibility_ratio": density_susceptibility_ratio,
        "governance": {
            "epistemic_rung": 3,
            "note": "Joint interpretation is INTERPRETED_LOCAL, not EARTHMODEL.",
        },
    }
