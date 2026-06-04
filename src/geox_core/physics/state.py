"""
geox_core.physics.state — EARTH.CANON_9 Canonical State Vector

The 9 orthogonal physics parameters that describe any Earth material.
Nothing in this file interprets. It only names and bounds.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Physics9State:
    """
    Canonical 9-parameter Earth state vector.

    Derived variables (moduli, ratios) are computed in parameters.py,
    not stored here, per the orthogonality rule.
    """

    rho: float  # kg/m³   density
    vp: float  # m/s     compressional velocity
    vs: float  # m/s     shear velocity
    rho_e: float  # Ω·m     electrical resistivity
    chi: float  # SI      magnetic susceptibility
    k: float  # W/m·K   thermal conductivity
    P: float  # Pa      pore pressure
    T: float  # K       temperature
    phi: float  # 0–1     porosity

    # Anisotropy (Thomsen parameters) — extensions, not core 9
    epsilon: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0

    # Attenuation quality factors
    qp: float = 100.0
    qs: float = 50.0

    def to_vector(self) -> list[float]:
        return [
            self.rho,
            self.vp,
            self.vs,
            self.rho_e,
            self.chi,
            self.k,
            self.P,
            self.T,
            self.phi,
            self.epsilon,
            self.delta,
            self.gamma,
            self.qp,
            self.qs,
        ]

    @classmethod
    def from_vector(cls, v: list[float]) -> Physics9State:
        return cls(
            rho=v[0],
            vp=v[1],
            vs=v[2],
            rho_e=v[3],
            chi=v[4] if len(v) > 4 else 0.0,
            k=v[5] if len(v) > 5 else 2.5,
            P=v[6] if len(v) > 6 else 20e6,
            T=v[7] if len(v) > 7 else 320,
            phi=v[8] if len(v) > 8 else 0.20,
            epsilon=v[9] if len(v) > 9 else 0.0,
            delta=v[10] if len(v) > 10 else 0.0,
            gamma=v[11] if len(v) > 11 else 0.0,
            qp=v[12] if len(v) > 12 else 100.0,
            qs=v[13] if len(v) > 13 else 50.0,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": self.rho,
            "vp": self.vp,
            "vs": self.vs,
            "rho_e": self.rho_e,
            "chi": self.chi,
            "k": self.k,
            "P": self.P,
            "T": self.T,
            "phi": self.phi,
            "epsilon": self.epsilon,
            "delta": self.delta,
            "gamma": self.gamma,
            "qp": self.qp,
            "qs": self.qs,
        }

    def grade(self) -> str:
        """Physical-bounds quality gate. RAW = outside Earth bounds."""
        if not (0.02 <= self.phi <= 0.45):
            return "RAW"
        if not (1500 <= self.vp <= 6000):
            return "RAW"
        if not (1000 <= self.rho <= 5000):
            return "RAW"
        return "AAA"


# ─── Earth Material Catalog ─────────────────────────────────────────────────

SANDSTONE = Physics9State(rho=2350, vp=2950, vs=1680, rho_e=20, chi=0.0001, k=2.8, P=20e6, T=320, phi=0.25)
LIMESTONE = Physics9State(rho=2710, vp=4300, vs=2500, rho_e=200, chi=0.00005, k=3.2, P=30e6, T=340, phi=0.10)
DOLOMITE = Physics9State(rho=2850, vp=5400, vs=2900, rho_e=100, chi=0.00006, k=3.0, P=35e6, T=350, phi=0.08)
SHALE = Physics9State(rho=2350, vp=2450, vs=1050, rho_e=10, chi=0.004, k=1.5, P=25e6, T=330, phi=0.32)
ANHYDRITE = Physics9State(rho=2970, vp=6000, vs=3200, rho_e=2000, chi=0.00002, k=4.1, P=40e6, T=360, phi=0.01)
SALT = Physics9State(rho=2160, vp=4500, vs=2300, rho_e=1e6, chi=0.00001, k=5.5, P=15e6, T=310, phi=0.01)
COAL = Physics9State(rho=1450, vp=2100, vs=1100, rho_e=500, chi=0.005, k=0.3, P=10e6, T=300, phi=0.08)
BASEMENT = Physics9State(rho=2900, vp=5800, vs=3400, rho_e=500, chi=0.01, k=2.5, P=60e6, T=400, phi=0.02)

EARTH_MATERIAL_CATALOG: dict[str, Physics9State] = {
    "Sandstone": SANDSTONE,
    "Limestone": LIMESTONE,
    "Dolomite": DOLOMITE,
    "Shale": SHALE,
    "Anhydrite": ANHYDRITE,
    "Salt": SALT,
    "Coal": COAL,
    "Basement": BASEMENT,
}


def compute_earth_material_catalog() -> dict[str, dict[str, float]]:
    return {name: s.to_dict() for name, s in EARTH_MATERIAL_CATALOG.items()}
