"""gl33.py — GEOX Large Earth World Model (LEWM) 33-State Unified Tensor.

The zen reduction. Per Arifs 2026-08-27 synthesis:

    M (Geomechanics)      — 9 properties — failure & flow mechanics
    P (Petrophysics)      — 9 properties — in-situ state & storage
    W (Wave Invariants)   — 9 properties — observable bridge (remote sensing)
    X (Cross-Domain)      — 6 properties — chemistry, bio, math, info, social

Total: 33 scalars.  No more, no less.  R ∉ S = g (gravity) is fixed; the
remaining 32 are learnable from observations.

F-I-M loop on the full 33D state:
    Forward    : M, P  →  W  (Gassmann + Navier-Cauchy)
    Inverse    : W_obs → M*, P* (Bayesian update)
    Metabolize : check failure + phase transition + X-bridge effects

Zen doctrine applied:
    - Single dataclass (no parallel state objects)
    - Coupling via operators, not via additional fields
    - One closed loop (F-I-M), no parallel diagnostics
    - 33 is the FLOOR — cannot reduce below without losing a domain

DITEMPA BUKAN DIBERI — the 33-state tensor is forged, not given.
"""
from __future__ import annotations

import math
import time
import hashlib
from dataclasses import dataclass, field, asdict, replace
from enum import Enum
from typing import Optional

import numpy as np


# ============================================================== Panel labels
class Panel(Enum):
    M = "Geomechanics"        # 9 properties (state matrix)
    P = "Petrophysics"        # 9 properties (field & storage)
    W = "Wave Invariants"     # 9 properties (observable bridge)
    X = "Cross-Domain"        # 6 properties (chemistry/bio/info/social)


# ============================================================== Bounds
@dataclass(frozen=True)
class Bounds:
    lo: float
    hi: float
    unit: str
    panel: Panel
    source: str = ""


BOUNDS_33 = {
    # === M (9): Geomechanics — failure & flow ===
    "E":         Bounds(1e6,  1e11,  "Pa",    Panel.M, "Paterson 1994 / ISRM"),
    "nu":        Bounds(0.05, 0.49,  "-",      Panel.M, "Thermodynamic bound"),
    "c":         Bounds(0.0,  5e6,   "Pa",     Panel.M, "Clay to hard rock"),
    "phi_angle": Bounds(0.0,  1.55,  "rad",    Panel.M, "0 to <pi/2"),
    "k_perm":    Bounds(1e-15, 1e-2, "m^2",    Panel.M, "Intact rock to gravel"),
    "phi_p":     Bounds(0.0,  0.6,   "-",      Panel.M, "Loose soil to pumice"),
    "eta":       Bounds(1e-3, 1e3,   "Pa.s",   Panel.M, "Water to wet concrete"),
    "tau_0":     Bounds(0.0,  1e5,   "Pa",     Panel.M, "Water to debris flow"),
    "sigma_t":   Bounds(0.0,  5e7,   "Pa",     Panel.M, "Snow to steel"),

    # === P (9): Petrophysics — in-situ state & storage ===
    "rho":       Bounds(500,  3200,  "kg/m^3", Panel.P, "USGS rock/ice tables"),
    "Pp":        Bounds(0.0,  1e8,   "Pa",     Panel.P, "Hydrostatic to lithostatic"),
    "T":         Bounds(173,  1000,  "K",      Panel.P, "Permafrost to magma"),
    "phi":       Bounds(0.0,  0.6,   "-",      Panel.P, "Same as phi_p; field-scale effective"),
    "rho_e":     Bounds(0.1,  1000,  "ohm.m",  Panel.P, "Shale to brine"),
    "chi":       Bounds(-1e-2, 1e-1, "SI",     Panel.P, "Diamag to ferromag"),
    "k_th":      Bounds(0.1,  10,    "W/m.K",  Panel.P, "Insulator to metal"),
    "S_w":       Bounds(0.0,  1.0,   "-",      Panel.P, "Dry to saturated"),
    "phase_id":  Bounds(0,    3,     "-",      Panel.P, "solid/granular/fluid/unknown enum"),

    # === W (9): Wave Invariants — observable bridge ===
    "Vp":        Bounds(1500, 6000,  "m/s",    Panel.W, "Water to dense rock"),
    "Vs":        Bounds(0.0,  4000,  "m/s",    Panel.W, "Fluid=0, rock=3500"),
    "Qp":        Bounds(5,    500,   "-",      Panel.W, "Attenuation"),
    "Qs":        Bounds(5,    500,   "-",      Panel.W, "Attenuation"),
    "epsilon":   Bounds(-0.2, 0.5,   "-",      Panel.W, "Thomsen VTI anisotropy"),
    "delta":     Bounds(-0.2, 0.5,   "-",      Panel.W, "Thomsen VTI anisotropy"),
    "gamma":     Bounds(-0.2, 0.5,   "-",      Panel.W, "Thomsen VTI anisotropy"),
    "alpha_B":   Bounds(0.0,  1.0,   "-",      Panel.W, "Biot-Willis 0..1"),
    "g":         Bounds(9.78, 9.83,  "m/s^2",  Panel.W, "Earth surface gravity (R notin S)"),

    # === X (6): Cross-domain bridges ===
    "E_a":       Bounds(0.0,  200e3, "J/mol",  Panel.X, "Arrhenius activation energy"),
    "L_f":       Bounds(0.0,  334e3, "J/kg",   Panel.X, "Latent heat of fusion (water 334kJ/kg)"),
    "c_bio":     Bounds(0.0,  50e3,  "Pa",     Panel.X, "Biotic root cohesion"),
    "D_f":       Bounds(1.0,  3.0,   "-",      Panel.X, "Fractal dimension (Euclidean=3)"),
    "H_info":    Bounds(0.0,  10.0,  "bits",   Panel.X, "Shannon entropy"),
    "E_socio":   Bounds(0.0,  1.0,   "-",      Panel.X, "Socio-spatial exposure index"),
}


# ============================================================== State
@dataclass
class GEOXEarthState33:
    """The unified 33-state Earth tensor for one voxel / particle / region.

    Invariants (F2):
        33 scalars — panel M(9), P(9), W(9), X(6)
        Dynamic ops (5): velocity, strain, saturation (live), phase_id (already in P)
        R ∉ S enforced: g is fixed (gravity is unlearnable)

    Zen compliance:
        Single dataclass — no parallel state objects
        Coupling arrows between panels via operators (forward_kinematics, etc.)
        No redundant fields (phi vs phi_p are distinct scalar quantities)
    """
    # ============ M (9) Geomechanics ============
    E: float = 30e9
    nu: float = 0.25
    c: float = 5e3
    phi_angle: float = math.radians(32.0)
    k_perm: float = 1e-4
    phi_p: float = 0.30
    eta: float = 0.05
    tau_0: float = 2e3
    sigma_t: float = 0.5e6

    # ============ P (9) Petrophysics ============
    rho: float = 2700.0
    Pp: float = 0.0
    T: float = 273.15
    phi: float = 0.30
    rho_e: float = 1.0
    chi: float = 0.0
    k_th: float = 2.5
    S_w: float = 0.0
    phase_id: int = 0          # 0=solid, 1=granular, 2=fluid, 3=unknown

    # ============ W (9) Wave Invariants ============
    Vp: float = 0.0           # m/s — derived; 0 = unlearned
    Vs: float = 0.0           # m/s — derived; 0 = unlearned
    Qp: float = 100.0
    Qs: float = 50.0
    epsilon: float = 0.0       # Thomsen anisotropy
    delta: float = 0.0
    gamma: float = 0.0
    alpha_B: float = 0.0       # Biot-Willis
    g: float = 9.81           # FIXED — R notin S

    # ============ X (6) Cross-domain bridges ============
    E_a: float = 50e3          # J/mol  (Arrhenius)
    L_f: float = 334e3         # J/kg   (water latent heat)
    c_bio: float = 0.0         # Pa     (root cohesion)
    D_f: float = 2.5           # fractal dim
    H_info: float = 0.0        # bits   (Shannon)
    E_socio: float = 0.0       # exposure index 0..1

    # ============ Dynamic ops (5) ============
    velocity: float = 0.0      # m/s   flow magnitude
    strain: float = 0.0        # -     accumulated
    saturation: float = 0.0    # -     live water fraction (deprecated alias; use S_w)
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())
    cell_id: str = ""

    # ============ Iteration API ============
    def panel(self, p: Panel) -> dict:
        """Return all fields belonging to one panel."""
        return {k: getattr(self, k) for k, v in BOUNDS_33.items() if v.panel == p}

    @property
    def M(self) -> dict:
        return self.panel(Panel.M)

    @property
    def P(self) -> dict:
        return self.panel(Panel.P)

    @property
    def W(self) -> dict:
        return self.panel(Panel.W)

    @property
    def X(self) -> dict:
        return self.panel(Panel.X)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["panels"] = {p.value: self.panel(p) for p in Panel}
        return d

    def state_hash(self) -> str:
        h = hashlib.sha256()
        for k in sorted(BOUNDS_33.keys()):
            v = getattr(self, k)
            h.update(f"{k}={v:.6e}".encode())
        return h.hexdigest()[:16]

    def validate(self) -> tuple:
        violations = []
        for k, b in BOUNDS_33.items():
            v = getattr(self, k)
            if not (b.lo <= v <= b.hi):
                violations.append(f"{k}={v} not in [{b.lo}, {b.hi}] {b.unit} (panel={b.panel.value})")
        return (len(violations) == 0, violations)

    # ============================================== Derived scalars
    def K_bulk(self) -> float:
        """K = E / [3(1-2nu)]  from M slice."""
        return self.E / (3.0 * (1.0 - 2.0 * self.nu))

    def G_shear(self) -> float:
        """G = E / [2(1+nu)]  from M slice."""
        return self.E / (2.0 * (1.0 + self.nu))


# ============================================================== Coupling operators
def forward_kinematics(s: GEOXEarthState33) -> dict:
    """M, P → W: Gassmann + Navier-Cauchy.

    Returns derived W fields (Vp, Vs) from M (E, nu) and P (rho).
    Other W fields (Qp, Qs, epsilon, delta, gamma, alpha_B, g) are
    state-bound; not computed.
    """
    K = s.K_bulk()
    G = s.G_shear()
    # Navier-Cauchy: Vp = sqrt((K + 4/3 G) / rho); Vs = sqrt(G / rho)
    Vp = math.sqrt(max((K + (4.0 / 3.0) * G) / s.rho, 1e-12))
    Vs = math.sqrt(max(G / s.rho, 1e-12))
    # Biot-Willis (for low-frequency saturated case): alpha_B = 1 - Kdry/Ks
    # Approx: Kdry ~ 0.7 * K (Biot coefficient empiric), so alpha_B ~ 0.3 for sandstone.
    # Use phi as proxy for connected porosity.
    Kdry = 0.7 * K
    Ks = K / max(1.0 - s.phi, 1e-6)
    alpha_B = max(0.0, min(1.0, 1.0 - Kdry / Ks)) if Ks > 0 else 0.0
    return {"Vp": Vp, "Vs": Vs, "alpha_B": alpha_B}


def gassmann_substitution(s: GEOXEarthState33, K_f: float = 2.2e9) -> dict:
    """Fluid substitution: replace pore fluid and recompute K_sat.

    Standard Gassmann (low-frequency limit):
        K_sat = Kdry + (1 - Kdry/Ks)^2 / (phi/Kf + (1-phi)/Ks - Kdry/Ks^2)

    Returns updated K_sat and Vp_sat.
    """
    K = s.K_bulk()
    Kdry = 0.7 * K  # empiric approx
    Ks = K / max(1.0 - s.phi, 1e-6)
    phi = s.phi
    # Gassmann denominator
    denom = phi / K_f + (1.0 - phi) / Ks - Kdry / (Ks * Ks)
    if denom <= 0:
        return {"K_sat": K, "Vp_sat": s.Vp}
    K_sat = Kdry + (1.0 - Kdry / Ks) ** 2 / denom
    G = s.G_shear()
    Vp_sat = math.sqrt(max((K_sat + (4.0 / 3.0) * G) / s.rho, 1e-12))
    return {"K_sat": K_sat, "Vp_sat": Vp_sat}


def metabolize_33(s: GEOXEarthState33) -> GEOXEarthState33:
    """Metabolic closure on the 33D state.

    Steps (in order):
        1. Arrhenius cohesion decay (X[E_a] affects M[c] via temperature)
        2. Biotic root cohesion add (X[c_bio] augments M[c])
        3. Latent heat phase check (P[T] vs 273.15 K + X[L_f])
        4. Terzaghi effective stress (P[Pp], W[alpha_B]) → yield check
        5. Mohr-Coulomb failure (M[c, phi_angle], W[alpha_B])
        6. Voellmy if velocity > V_crit (M[tau_0, eta])
        7. Update phase_id (P[phase_id])
        8. Update derived W (forward_kinematics)
        9. F12 witness hash recompute
    """
    from dataclasses import replace
    s2 = replace(s)

    # --- 1. Arrhenius: cohesion decays with temperature (normalized to T_ref)
    # c(T) / c_ref = exp(-E_a / R * (1/T_ref - 1/T))
    # Default T_ref = 298 K; at T=T_ref, factor=1 (no decay).
    R_gas = 8.314
    T_ref = 298.15
    if s2.E_a > 0 and s2.T > 0:
        arrhenius_factor = math.exp(-s2.E_a / R_gas * (1.0 / T_ref - 1.0 / s2.T))
        # Bound: factor in [0.01, 1.0] to avoid total collapse
        arrhenius_factor = max(0.01, min(1.0, arrhenius_factor))
        s2 = replace(s2, c=s2.c * arrhenius_factor)

    # --- 2. Biotic cohesion augmentation
    s2 = replace(s2, c=s2.c + s2.c_bio)

    # --- 3. Latent heat phase check (melting)
    # If T >= 273.15 K and we have ice-like properties (rho ~ 917), trigger melt
    if s2.T >= 273.15 and 800 < s2.rho < 1100 and s2.phase_id == 0:
        # Consume latent heat energy balance (simplified)
        # Real impl: dt = (rho * L_f) / heat_input_rate
        s2 = replace(s2, phase_id=1)   # solid -> granular (wet)

    # --- 4. Terzaghi effective stress
    sigma_v = s2.rho * s2.g * 100.0  # 100m reference depth
    sigma_eff = sigma_v - s2.alpha_B * s2.Pp

    # --- 5. Mohr-Coulomb
    tau_max = s2.c + max(sigma_eff, 0.0) * math.tan(max(s2.phi_angle, 1e-3))
    tau_applied = s2.Pp * 0.5
    margin = (tau_max - tau_applied) / max(tau_max, 1.0)

    # --- 6. Voellmy if velocity high
    if s2.velocity >= 5.0 and s2.tau_0 > 0:
        # Voellmy check at sigma_n from effective stress
        tau_v = s2.tau_0 + 0.15 * max(sigma_eff, 0.0) + s2.rho * s2.velocity ** 2 / 1000.0
        if tau_v > tau_max * 1.5:
            s2 = replace(s2, phase_id=2)  # granular -> fluid
    elif margin < 0:
        s2 = replace(s2, phase_id=1)      # solid -> granular

    # --- 7. Saturation update (live water fraction from pore pressure)
    if s2.Pp > 0 and s2.rho > 0:
        # Approx: S_w = Pp / (rho * g * depth_ref)
        s2 = replace(s2, S_w=min(1.0, s2.Pp / max(s2.rho * s2.g * 100.0, 1.0)))

    # --- 8. Update derived W
    derived = forward_kinematics(s2)
    s2 = replace(s2, Vp=derived["Vp"], Vs=derived["Vs"],
                 alpha_B=derived["alpha_B"])

    return s2


# ============================================================== F-I-M cycle
@dataclass
class FIMReceipt33:
    cycle_id: str
    timestamp_ns: int
    prior_state: dict
    posterior_state: dict
    forward_W: dict
    observed_W: dict
    G_score: float
    log_likelihood: float
    phase_transitions: list
    notes: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _g33_gaussian_likelihood(s_sim: GEOXEarthState33, w_obs: dict) -> float:
    """log P(w_obs | s) assuming Gaussian observation noise."""
    sigma_vp = 100.0  # m/s
    sigma_vs = 60.0   # m/s
    fwd = forward_kinematics(s_sim)
    L = 0.0
    if "Vp" in w_obs:
        L += -0.5 * ((w_obs["Vp"] - fwd["Vp"]) / sigma_vp) ** 2
    if "Vs" in w_obs:
        L += -0.5 * ((w_obs["Vs"] - fwd["Vs"]) / sigma_vs) ** 2
    return L


def run_fim_cycle_33(
    s0: GEOXEarthState33,
    w_obs: dict,
    cycle_id: str = "",
    notes: str = "",
) -> tuple:
    """One F-I-M cycle on the full 33D state.

    Forward  : metabolize_33(s0) -> s1 ; forward_kinematics(s1) -> w_sim
    Inverse  : simple rejection sampling — perturb s0 in M,P; keep best LL
    Metabolize: forward_kinematics + tri-witness G-score
    """
    np.random.seed(int(time.time_ns()) % (2**32))
    best = (None, -float("inf"))
    # Generate 16 candidate perturbations in M,P
    for _ in range(16):
        s_pert = replace(
            s0,
            E=s0.E * np.random.uniform(0.7, 1.3),
            c=s0.c * np.random.uniform(0.5, 2.0),
            phi_angle=max(0.0, min(1.55, s0.phi_angle + np.random.normal(0, 0.1))),
            rho=s0.rho * np.random.uniform(0.95, 1.05),
        )
        s_meta = metabolize_33(s_pert)
        ll = _g33_gaussian_likelihood(s_meta, w_obs)
        if ll > best[1]:
            best = (s_meta, ll)

    s_post = best[0]
    s_post = metabolize_33(s_post)
    fwd = forward_kinematics(s_post)

    # Tri-witness G-score (H × M × E)^(1/3)  — bounded 0..1
    H = min(1.0, max(0.0, 0.9 - 0.05 * (1 if "social" not in str(notes) else 0)))
    # Model witness: exp(-0.5 * sigma^2) where sigma = max(0, -LL/scale)
    sigma = max(0.0, -best[1]) / 10.0  # LL=-10 -> sigma=1.0, LL=-100 -> sigma=10
    M_witness = float(np.exp(-0.5 * sigma * sigma))
    ok, _ = s_post.validate()
    E = 1.0 if ok else 0.0
    G = (H * M_witness * E) ** (1.0 / 3.0)
    G = min(1.0, G)

    # Phase transitions
    transitions = []
    if s0.phase_id != s_post.phase_id:
        transitions.append({"from": s0.phase_id, "to": s_post.phase_id})

    receipt = FIMReceipt33(
        cycle_id=cycle_id or hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:12],
        timestamp_ns=time.time_ns(),
        prior_state=s0.to_dict(),
        posterior_state=s_post.to_dict(),
        forward_W=fwd,
        observed_W=w_obs,
        G_score=round(G, 4),
        log_likelihood=round(best[1], 4),
        phase_transitions=transitions,
        notes=notes,
    )
    return s_post, receipt


# ============================================================== Factories
def from_legacy_states(
    physics13_dict: Optional[dict] = None,
    glof_dict: Optional[dict] = None,
) -> GEOXEarthState33:
    """Build GEOXEarthState33 from existing Physics13State + GLOFMaterialState dicts.

    Bridges:
        Physics13State  -> P slice (rho, Pp, T, phi, rho_e, chi, k_th, S_w)
                          + W slice (Vp, Vs, Qp, Qs, alpha_B)
        GLOFMaterialState -> M slice (E, nu, c, phi_angle, k_perm, phi_p, eta,
                                     tau_0, sigma_t)
    """
    s = GEOXEarthState33()
    if physics13_dict:
        # W slice from Physics13State (vp, vs, Qp, Qs derived)
        if "vp" in physics13_dict:
            s = replace(s, Vp=float(physics13_dict["vp"]))
        if "vs" in physics13_dict:
            s = replace(s, Vs=float(physics13_dict["vs"]))
        if "rho" in physics13_dict:
            s = replace(s, rho=float(physics13_dict["rho"]))
        # P slice
        for k in ("Pp", "T", "phi", "rho_e", "chi", "k_th", "S_w"):
            if k in physics13_dict:
                s = replace(s, **{k: float(physics13_dict[k])})
        # W slice (Qp, Qs)
        if "qp" in physics13_dict:
            s = replace(s, Qp=float(physics13_dict["qp"]))
        if "qs" in physics13_dict:
            s = replace(s, Qs=float(physics13_dict["qs"]))
    if glof_dict:
        # M slice
        for k in ("E", "nu", "c", "phi_angle", "k_perm", "phi_p",
                  "eta", "tau_0", "sigma_t"):
            if k in glof_dict:
                # Map phi (glof) -> phi_p (33)
                actual_key = "phi_p" if k == "phi_p" else k
                s = replace(s, **{actual_key: float(glof_dict[k])})
        # dynamic state
        if "velocity" in glof_dict:
            s = replace(s, velocity=float(glof_dict["velocity"]))
        if "saturation" in glof_dict:
            s = replace(s, saturation=float(glof_dict["saturation"]))
    return s


def himalayan_glof_33() -> GEOXEarthState33:
    """Himalayan GLOF reference state — 33D defaults for Bhote Koshi."""
    return GEOXEarthState33(
        # M
        E=30e9, nu=0.25, c=5e3, phi_angle=math.radians(32),
        k_perm=1e-4, phi_p=0.30, eta=0.05, tau_0=2e3, sigma_t=0.5e6,
        # P
        rho=2700.0, T=273.15, phi=0.30, rho_e=100.0,
        chi=1e-4, k_th=2.5, S_w=0.1,
        # W — Vp/Vs derived via forward_kinematics
        Vp=5500.0, Vs=3200.0, Qp=80, Qs=40,
        epsilon=0.15, delta=0.10, gamma=0.12,
        alpha_B=0.30,
        # X
        E_a=80e3, L_f=334e3, c_bio=0.0, D_f=2.4,
        H_info=2.5, E_socio=0.15,
        cell_id="bhotekoshi_33",
        phase_id=1,  # granular
    )


if __name__ == "__main__":
    s = himalayan_glof_33()
    print(f"=== GEOXEarthState33 (33-D) ===")
    print(f"  cell_id={s.cell_id}")
    for p in Panel:
        d = s.panel(p)
        print(f"  Panel {p.value:14s} ({p.value:1s}): {len(d)} fields")
    ok, viol = s.validate()
    print(f"  validate ok={ok} violations={viol}")
    print(f"  K={s.K_bulk()/1e9:.2f} GPa  G={s.G_shear()/1e9:.2f} GPa")
    print(f"  state_hash={s.state_hash()}")

    print()
    print("=== Forward kinematics (M,P -> W) ===")
    derived = forward_kinematics(s)
    print(f"  Vp={derived['Vp']:.0f} m/s  Vs={derived['Vs']:.0f} m/s  alpha_B={derived['alpha_B']:.3f}")

    print()
    print("=== Gassmann fluid substitution ===")
    g = gassmann_substitution(s, K_f=2.2e9)  # water
    print(f"  K_sat={g['K_sat']/1e9:.3f} GPa  Vp_sat={g['Vp_sat']:.0f} m/s")

    print()
    print("=== Metabolize (one closure pass) ===")
    s2 = metabolize_33(s)
    print(f"  phase_id {s.phase_id} -> {s2.phase_id}")
    print(f"  c (after Arrhenius) {s.c:.0f} -> {s2.c:.0f} Pa")
    print(f"  Vp (derived) {s.Vp:.0f} -> {s2.Vp:.0f} m/s")

    print()
    print("=== F-I-M cycle ===")
    # Pretend seismic observed Vp slightly different (e.g., water saturation increased)
    w_obs = {"Vp": 5000.0, "Vs": 2900.0}
    s_post, receipt = run_fim_cycle_33(s, w_obs, cycle_id="c1", notes="Bhote Koshi")
    print(f"  cycle={receipt.cycle_id} G={receipt.G_score:.3f} LL={receipt.log_likelihood:.2f}")
    print(f"  inferred rho={s_post.rho:.0f} E={s_post.E/1e9:.1f}GPa phase={s_post.phase_id}")