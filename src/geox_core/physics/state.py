
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class RockPhysics13State:
    rho_b: float    # Bulk density [g/cc]
    rho_ma: float   # Grain (matrix) density [g/cc]
    rho_f: float    # Fluid density [g/cc]
    phi: float      # Porosity [v/v]
    Sw: float       # Water saturation [v/v]
    k: float        # Permeability [mD]
    vp: float       # P-wave velocity [m/s]
    vs: float       # S-wave velocity [m/s]
    K: float        # Bulk modulus [GPa]
    mu: float       # Shear modulus [GPa]
    Rt: float       # Electrical resistivity [Ω·m]
    T: float        # Temperature [°C]
    Pp: float       # Pore pressure [MPa]

@dataclass(frozen=True)
class Physics13State:
    rho: float       # kg/m³ density
    vp: float        # m/s compressional velocity
    vs: float        # m/s shear velocity
    rho_e: float     # Ω·m electrical resistivity
    chi: float       # SI magnetic susceptibility
    k_th: float      # W/m·K thermal conductivity (legacy named k)
    Pp: float        # Pa pore pressure (legacy named P)
    T: float         # K temperature
    phi: float       # 0–1 porosity
    epsilon: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    sigma_eff: float = 30e6
    qp: float = 100.0
    qs: float = 50.0

    @property
    def k(self): return self.k_th
    @property
    def P(self): return self.Pp

    def __init__(
        self,
        rho: float,
        vp: float,
        vs: float,
        rho_e: float,
        chi: float,
        k_th: float | None = None,
        Pp: float | None = None,
        T: float | None = None,
        phi: float | None = None,
        epsilon: float = 0.0,
        delta: float = 0.0,
        gamma: float = 0.0,
        sigma_eff: float = 30e6,
        qp: float = 100.0,
        qs: float = 50.0,
        *,
        k: float | None = None,
        P: float | None = None,
    ) -> None:
        """Init with backward-compat aliases k → k_th and P → Pp."""
        if k is not None:
            k_th = k
        if P is not None:
            Pp = P
        if k_th is None:
            raise TypeError("Physics13State missing required thermal conductivity (k_th or k)")
        if Pp is None:
            raise TypeError("Physics13State missing required pore pressure (Pp or P)")
        if T is None:
            raise TypeError("Physics13State missing required temperature (T)")
        if phi is None:
            raise TypeError("Physics13State missing required porosity (phi)")
        object.__setattr__(self, "rho", rho)
        object.__setattr__(self, "vp", vp)
        object.__setattr__(self, "vs", vs)
        object.__setattr__(self, "rho_e", rho_e)
        object.__setattr__(self, "chi", chi)
        object.__setattr__(self, "k_th", k_th)
        object.__setattr__(self, "Pp", Pp)
        object.__setattr__(self, "T", T)
        object.__setattr__(self, "phi", phi)
        object.__setattr__(self, "epsilon", epsilon)
        object.__setattr__(self, "delta", delta)
        object.__setattr__(self, "gamma", gamma)
        object.__setattr__(self, "sigma_eff", sigma_eff)
        object.__setattr__(self, "qp", qp)
        object.__setattr__(self, "qs", qs)

    def to_vector(self) -> list[float]:
        return [self.rho, self.vp, self.vs, self.rho_e, self.chi, self.k_th, self.Pp, self.T, self.phi, self.epsilon, self.delta, self.gamma, self.qp, self.qs]

    @classmethod
    def from_vector(cls, v: list[float]) -> Physics13State:
        return cls(
            rho=v[0], vp=v[1], vs=v[2], rho_e=v[3],
            chi=v[4] if len(v)>4 else 0.0,
            k_th=v[5] if len(v)>5 else 2.5,
            Pp=v[6] if len(v)>6 else 20e6,
            T=v[7] if len(v)>7 else 320,
            phi=v[8] if len(v)>8 else 0.2,
            epsilon=v[9] if len(v)>9 else 0.0,
            delta=v[10] if len(v)>10 else 0.0,
            gamma=v[11] if len(v)>11 else 0.0,
            qp=v[12] if len(v)>12 else 100.0,
            qs=v[13] if len(v)>13 else 50.0
        )

    def to_dict(self) -> dict[str, Any]:
        return {"rho": self.rho, "vp": self.vp, "vs": self.vs, "rho_e": self.rho_e, "chi": self.chi, "k": self.k_th, "P": self.Pp, "T": self.T, "phi": self.phi, "epsilon": self.epsilon, "delta": self.delta, "gamma": self.gamma, "qp": self.qp, "qs": self.qs}

    @classmethod
    def from_raw_dict(cls, raw: dict[str, Any]) -> Physics13State:
        return cls(
            rho=float(raw.get("rho", 2500.0)),
            vp=float(raw.get("vp", 3000.0)),
            vs=float(raw.get("vs", 1500.0)),
            rho_e=float(raw.get("rho_e", 20.0)),
            chi=float(raw.get("chi", 0.0)),
            k_th=float(raw.get("k", 2.5)),
            Pp=float(raw.get("P", 20e6)),
            T=float(raw.get("T", 320.0)),
            phi=float(raw.get("phi", 0.2)),
            epsilon=float(raw.get("epsilon", 0.0)),
            delta=float(raw.get("delta", 0.0)),
            gamma=float(raw.get("gamma", 0.0))
        )
    
    def grade(self) -> str:
        if not (0.02 <= self.phi <= 0.45):
            return "RAW"
        if not (1500 <= self.vp <= 6000):
            return "RAW"
        if not (1000 <= self.rho <= 5000):
            return "RAW"
        return "AAA"

SANDSTONE = Physics13State(rho=2350, vp=2950, vs=1680, rho_e=20, chi=0.0001, k_th=2.8, Pp=20e6, T=320, phi=0.25)
LIMESTONE = Physics13State(rho=2710, vp=4300, vs=2500, rho_e=200, chi=0.00005, k_th=3.2, Pp=30e6, T=340, phi=0.10)
DOLOMITE = Physics13State(rho=2850, vp=5400, vs=2900, rho_e=100, chi=0.00006, k_th=3.0, Pp=35e6, T=350, phi=0.08)
SHALE = Physics13State(rho=2350, vp=2450, vs=1050, rho_e=10, chi=0.004, k_th=1.5, Pp=25e6, T=330, phi=0.32)
ANHYDRITE = Physics13State(rho=2970, vp=6000, vs=3200, rho_e=2000, chi=0.00002, k_th=4.1, Pp=40e6, T=360, phi=0.01)
SALT = Physics13State(rho=2160, vp=4500, vs=2300, rho_e=1e6, chi=0.00001, k_th=5.5, Pp=15e6, T=310, phi=0.01)
COAL = Physics13State(rho=1450, vp=2100, vs=1100, rho_e=500, chi=0.005, k_th=0.3, Pp=10e6, T=300, phi=0.08)
BASEMENT = Physics13State(rho=2900, vp=5800, vs=3400, rho_e=500, chi=0.01, k_th=2.5, Pp=60e6, T=400, phi=0.02)

EARTH_MATERIAL_CATALOG = {
    "Sandstone": SANDSTONE, "Limestone": LIMESTONE, "Dolomite": DOLOMITE,
    "Shale": SHALE, "Anhydrite": ANHYDRITE, "Salt": SALT, "Coal": COAL, "Basement": BASEMENT,
}
def compute_earth_material_catalog():
    return {name: s.to_dict() for name, s in EARTH_MATERIAL_CATALOG.items()}
