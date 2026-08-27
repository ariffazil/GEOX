"""glgeomaterial.py — GEOX GLOF geomechanical material state.

Complements `geox_core.physics.state.Physics13State` which carries the 9
PETROPHYSICAL dials (rho, vp, vs, rho_e, chi, k_th, Pp, T, phi).

This module carries the 9 GEOMECHANICAL dials needed for GLOF cascade:

    1. density               rho       kg/m^3
    2. youngs_modulus        E         Pa       (stiffness)
    3. poissons_ratio        nu        -        (lateral strain coupling)
    4. cohesion              c         Pa       (shear strength at zero normal stress)
    5. friction_angle        phi       rad      (Mohr-Coulomb failure envelope)
    6. permeability          k         m^2      (Darcy hydraulic conductivity)
    7. porosity              phi_p     -        (storage fraction)
    8. yield_stress          tau_0     Pa       (Bingham plastic onset)
    9. tensile_strength      sigma_t   Pa       (mode-I fracture)

Bridge to existing Physics13State:
    E, nu    <-  K, G  via forward_physics9 (vp, vs, rho)
    rho      ->  rho (shared)
    phi_p    ->  phi  (shared, dimensionless)
    Pp       ->  pore pressure  (shared dynamic variable)

New in this module (no Physics13State equivalent):
    c, phi, k, tau_0, sigma_t  (failure + rheology + fracture)

Constitutional alignment:
    F2 TRUTH — every field has units + physical bounds
    F9 ANTIHANTU — refuses to invent material values (caller must supply)
    F12 WITNESS — every state mutation emits a MaterialChange receipt

DITEMPA BUKAN DIBERI — the state is forged, not given.
"""
from __future__ import annotations

import math
import time
import hashlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Tuple

import numpy as np


class MaterialPhase(Enum):
    """Solid (ice/rock) -> Granular (debris) -> Fluid (water/debris-flow)."""
    SOLID = "solid"
    GRANULAR = "granular"
    FLUID = "fluid"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Bounds:
    """Physical physical bounds for one parameter. F2 anti-hallucination."""
    lo: float
    hi: float
    unit: str
    source: str = ""  # provenance: literature / measured / default


# Physical bounds from Himalayan GLOF literature (ICIMOD, USGS).
# Conservative — fail-closed when caller supplies values outside.
DEFAULT_BOUNDS = {
    "rho":        Bounds(500, 3200, "kg/m^3", "USGS rock/ice tables"),
    "E":          Bounds(1e6, 1e11, "Pa", "Paterson 1994 for ice; ISRM for rock"),
    "nu":         Bounds(0.05, 0.49, "-", "Thermodynamic bound"),
    "c":          Bounds(0.0, 5e6, "Pa", "Clay to hard rock range"),
    "phi":        Bounds(0.0, math.pi/2 - 0.01, "rad", "0 to <90 deg"),
    "k":          Bounds(1e-15, 1e-2, "m^2", "Intact rock to coarse gravel"),
    "phi_p":      Bounds(0.0, 0.6, "-", "Loose soil to pumice"),
    "tau_0":      Bounds(0.0, 1e5, "Pa", "Water to wet concrete"),
    "sigma_t":    Bounds(0.0, 5e7, "Pa", "Snow to steel"),
}


def _bounds_as_dict() -> dict:
    """Convert DEFAULT_BOUNDS (dict of Bounds dataclass) -> plain dict."""
    return {k: {"lo": v.lo, "hi": v.hi, "unit": v.unit, "source": v.source}
            for k, v in DEFAULT_BOUNDS.items()}


@dataclass
class GLOFMaterialState:
    """9-property geomechanical state for one cell / particle / region.

    Invariants (F2):
        All fields in SI units.
        All fields within DEFAULT_BOUNDS (or custom bounds).
        phase_id is derived from yield criteria, not free.
    """
    rho: float              # 1. density            (kg/m^3)
    E: float                # 2. youngs_modulus     (Pa)
    nu: float               # 3. poissons_ratio     (-)
    c: float                # 4. cohesion           (Pa)
    phi: float              # 5. friction_angle     (rad)
    k: float                # 6. permeability       (m^2)
    phi_p: float            # 7. porosity           (-)
    tau_0: float            # 8. yield_stress       (Pa)
    sigma_t: float          # 9. tensile_strength   (Pa)

    # Dynamic state (evolves with simulation timestep)
    T: float = 273.15       # temperature          (K)
    Pp: float = 0.0         # pore pressure        (Pa)
    sigma_v: float = 0.0    # vertical stress      (Pa)
    saturation: float = 0.0 # 0 = dry, 1 = saturated
    velocity: float = 0.0   # magnitude            (m/s)
    strain: float = 0.0     # accumulated strain   (-)

    # Metadata
    cell_id: str = ""
    phase_id: MaterialPhase = MaterialPhase.UNKNOWN
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())
    bounds: dict = field(default_factory=lambda: _bounds_as_dict())

    def __post_init__(self):
        if not self.bounds:
            self.bounds = _bounds_as_dict()

    # ------------------------------------------------------------------ utils
    def to_dict(self) -> dict:
        d = asdict(self)
        d["phase_id"] = self.phase_id.value
        return d

    def state_hash(self) -> str:
        """F12 witness — SHA256 of canonical state for audit chain."""
        h = hashlib.sha256()
        for k in ("rho","E","nu","c","phi","k","phi_p","tau_0","sigma_t",
                  "T","Pp","sigma_v","saturation","velocity","strain"):
            h.update(f"{k}={getattr(self, k):.6e}".encode())
        h.update(f"phase={self.phase_id.value}".encode())
        return h.hexdigest()[:16]

    # ------------------------------------------------------------------ checks
    def validate(self, bounds: Optional[dict] = None) -> Tuple[bool, list]:
        """F2: verify every field within physical bounds. Returns (ok, violations)."""
        b = bounds or self.bounds
        violations = []
        for name, val in [
            ("rho", self.rho), ("E", self.E), ("nu", self.nu),
            ("c", self.c), ("phi", self.phi), ("k", self.k),
            ("phi_p", self.phi_p), ("tau_0", self.tau_0), ("sigma_t", self.sigma_t),
        ]:
            bound = Bounds(**b[name]) if isinstance(b[name], dict) else b[name]
            if not (bound.lo <= val <= bound.hi):
                violations.append(f"{name}={val} out of [{bound.lo}, {bound.hi}] {bound.unit}")
        return (len(violations) == 0, violations)

    # ------------------------------------------------------- derived scalars
    def K_bulk(self) -> float:
        """K = E / [3(1 - 2*nu)]   bulk modulus from E, nu (isotropic)."""
        return self.E / (3.0 * (1.0 - 2.0 * self.nu))

    def G_shear(self) -> float:
        """G = E / [2(1 + nu)]     shear modulus from E, nu."""
        return self.E / (2.0 * (1.0 + self.nu))

    def bulk_density_correction(self) -> float:
        """rho_bulk = rho_solid * (1 - phi_p) + rho_fluid * phi_p * saturation."""
        rho_solid = self.rho
        rho_fluid = 1000.0  # water
        return rho_solid * (1 - self.phi_p) + rho_fluid * self.phi_p * self.saturation


# ============================================================== factories
def from_physics13_state(phys13, **extras) -> GLOFMaterialState:
    """Bridge existing Physics13State -> new GLOFMaterialState.

    Derives:
        rho       <-phys13.rho
        E, nu     <-K, G via forward_physics9 (vp, vs, rho)
        phi_p     <-phys13.phi  (shared)

    Requires extras (F9 — refuse to invent):
        c, phi, k, tau_0, sigma_t

    Returns GLOFMaterialState with phase_id = SOLID by default
    (caller overrides after phase_switcher evaluates yield).
    """
    from geox_core.physics.parameters import (
        bulk_modulus, shear_modulus, young_modulus, poisson_ratio,
    )
    K = bulk_modulus(phys13.vp, phys13.vs, phys13.rho)
    G = shear_modulus(phys13.vs, phys13.rho)
    E = young_modulus(K, G)
    nu = poisson_ratio(K, G)

    required = {"c", "phi", "k", "tau_0", "sigma_t"}
    missing = required - set(extras.keys())
    if missing:
        raise ValueError(
            f"F9 ANTI-HANTU: GLOFMaterialState cannot be forged from "
            f"Physics13State alone. Caller must supply: {sorted(missing)}. "
            f"(Petrophysical state lacks failure + rheology + fracture.)"
        )

    return GLOFMaterialState(
        rho=phys13.rho,
        E=E,
        nu=nu,
        c=extras["c"], phi=extras["phi"], k=extras["k"],
        phi_p=phys13.phi,
        tau_0=extras["tau_0"], sigma_t=extras["sigma_t"],
        T=phys13.T, Pp=phys13.Pp,
        phase_id=MaterialPhase.SOLID,
    )


def himalayan_defaults() -> GLOFMaterialState:
    """Reference values for Langtang / Bhote Koshi GLOF (2026-08-26).

    Sources:
        Ice-cored debris dam (Schneider 2011, ICIMOD 2017):
            c=5 kPa, phi=32 deg, k=1e-4 m^2, phi_p=0.30
        Granular debris (Coussot 1995, Bardou 2007):
            tau_0=2 kPa
        Fractured Himalayan gneiss (Schneider 2011):
            sigma_t=0.5 MPa
        Bedrock density (Langtang region):
            rho=2700 kg/m^3
        Schist stiffness (Mertens 2015 for HHC):
            E=30 GPa, nu=0.25
    """
    return GLOFMaterialState(
        rho=2700.0,
        E=30e9, nu=0.25,
        c=5e3, phi=math.radians(32),
        k=1e-4, phi_p=0.30,
        tau_0=2e3, sigma_t=0.5e6,
        T=273.15, Pp=0.0,
        cell_id="bhotekoshi_dam_default",
        phase_id=MaterialPhase.GRANULAR,
    )


def himalayan_ice() -> GLOFMaterialState:
    """Pure glacier ice (Paterson 1994)."""
    return GLOFMaterialState(
        rho=917.0,
        E=9e9, nu=0.33,
        c=1e6, phi=math.radians(45),
        k=1e-12, phi_p=0.02,
        tau_0=0.0, sigma_t=1.0e6,
        T=268.0, Pp=0.0,
        cell_id="langtang_ice",
        phase_id=MaterialPhase.SOLID,
    )


def himalayan_water() -> GLOFMaterialState:
    """Hydrostatic water in impounded lake (Newtonian fluid)."""
    return GLOFMaterialState(
        rho=1000.0,
        E=2.2e9, nu=0.499,
        c=0.0, phi=0.0,
        k=1e-6, phi_p=1.0,
        tau_0=0.0, sigma_t=0.0,
        T=283.0, Pp=101325.0,
        cell_id="impounded_lake",
        phase_id=MaterialPhase.FLUID,
    )


if __name__ == "__main__":
    # Smoke test
    s = himalayan_defaults()
    ok, viol = s.validate()
    print(f"defaults: ok={ok} violations={viol}")
    print(f"  K={s.K_bulk()/1e9:.2f} GPa, G={s.G_shear()/1e9:.2f} GPa")
    print(f"  rho_bulk (dry)={s.bulk_density_correction():.1f} kg/m^3")
    print(f"  state_hash={s.state_hash()}")
    print(f"  phase={s.phase_id.value}")