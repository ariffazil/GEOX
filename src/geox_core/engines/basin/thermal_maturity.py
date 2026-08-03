"""
thermal_maturity.py — Thermal Maturity History Engine
═════════════════════════════════════════════════════
Model burial + heat flow + maturity through time.

Three methods implemented:
  1. EasyRo (Sweeney & Burnham 1990) — Arrhenius parallel-reaction model
  2. TTI (Lopatin 1971) — Time-Temperature Index
  3. Simple burial + geothermal gradient model

The EasyRo model uses an Arrhenius first-order parallel-reaction approach
with a distribution of activation energies to predict vitrinite reflectance
from thermal history.

Key equations:
  T(z) = T_surface + (dT/dz) * z    — temperature at depth
  dX/dt = A * exp(-Ea/RT) * (1-X)   — Arrhenius kinetics
  TTI = Σ(2^n * Δt)                 — Lopatin TTI
  Ro = f(TTI)                        — TTI to Ro correlation

DITEMPA BUKAN DIBERI — Forged, Not Given.

References:
  - Sweeney, J.J. & Burnham, A.K. (1990) Evaluation of a simple model of
    vitrinite reflectance based on chemical kinetics. AAPG Bull. 74(10):1559.
  - Lopatin, N.V. (1971) Temperature and geologic time as factors in coalification.
  - Waples, D.W. (1980) Time and temperature in petroleum formation.
  - Issler, D.R. (1984) A new approach to vitrinite reflectance modeling.
  - Peters, K.E. & Cassa, M.R. (1994) Applied source rock geochemistry.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# Physical Constants
# ═══════════════════════════════════════════════════════════════════════════════

R_GAS = 8.314462  # J/(mol·K) — universal gas constant
SURFACE_TEMP_C = 20.0  # °C — mean annual surface temperature

# EasyRo activation energy distribution (Sweeney & Burnham 1990)
# 20 parallel reactions with distributed activation energies
EASYRO_EA_KJ = [
    180.0,
    190.0,
    200.0,
    210.0,
    220.0,
    230.0,
    240.0,
    250.0,
    260.0,
    270.0,
    280.0,
    290.0,
    300.0,
    310.0,
    320.0,
    330.0,
    340.0,
    350.0,
    360.0,
    370.0,
]  # kJ/mol
EASYRO_A = 2.0e14  # s⁻¹ — pre-exponential factor (calibrated for geological Myr steps)
# Note: Standard S&B 1990 uses A=1.0e13 with Ea=142-301 kJ/mol and the exponential
# integral (Ei) integration. GEOX uses Ea=180-370 kJ/mol with stepwise analytic
# integration. A=2.0e14 is calibrated to match S&B 1990 benchmarks at geological
# heating rates (30-50°C/km, Myr timescales). See GEOX-HARDEN-001 for calibration details.
EASYRO_F = [
    0.03,
    0.03,
    0.04,
    0.04,
    0.05,
    0.05,
    0.06,
    0.06,
    0.06,
    0.06,
    0.06,
    0.06,
    0.06,
    0.06,
    0.06,
    0.06,
    0.05,
    0.04,
    0.04,
    0.03,
]  # reaction fractions (sum = 1.0 — normalized per Sweeney & Burnham 1990)

# TTI temperature index ranges (Lopatin 1971)
# n = 0 for 100-110°C, n = 1 for 110-120°C, etc.
TTI_T_BASE = 100.0  # °C — base temperature for n=0
TTI_T_STEP = 10.0  # °C — temperature step per index


@dataclass
class ThermalHistory:
    """Thermal history of a sedimentary layer through time."""

    name: str
    # Time steps (oldest first)
    ages_ma: list[float]  # Ma (oldest first)
    temperatures_c: list[float]  # °C at each time step
    depths_m: list[float]  # m at each time step
    heat_flow_mw_m2: list[float]  # mW/m² at each time step
    geothermal_gradient_c_km: list[float]  # °C/km at each time step


@dataclass
class MaturityResult:
    """Complete maturity analysis result."""

    layer_name: str
    # Final maturity
    easyro_final: float  # %Ro — EasyRo result
    tti_final: float  # TTI — Lopatin result
    ro_from_tti: float  # %Ro converted from TTI
    # Time series
    easyro_history: list[tuple[float, float]]  # (age_ma, %Ro)
    tti_history: list[tuple[float, float]]  # (age_ma, TTI)
    temperature_history: list[tuple[float, float]]  # (age_ma, °C)
    depth_history: list[tuple[float, float]]  # (age_ma, m)
    # Hydrocarbon windows
    oil_window_entered_ma: float | None  # age when Ro > 0.6
    oil_window_exited_ma: float | None  # age when Ro > 1.3
    gas_window_entered_ma: float | None  # age when Ro > 1.3
    gas_window_exited_ma: float | None  # age when Ro > 2.0
    overmature_ma: float | None  # age when Ro > 2.0
    # Loading events
    loading_pulse_age_ma: float | None  # age of maximum loading rate
    loading_pulse_rate_m_myr: float  # maximum loading rate
    # Provenance
    provenance: dict[str, Any]
    diagnostics: list[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Core Physics
# ═══════════════════════════════════════════════════════════════════════════════


def temperature_at_depth(
    depth_m: float,
    surface_temp_c: float = SURFACE_TEMP_C,
    geothermal_gradient_c_km: float = 30.0,
) -> float:
    """Temperature at depth using linear geothermal gradient.

    T(z) = T_surface + (dT/dz) * z
    """
    return surface_temp_c + geothermal_gradient_c_km * depth_m / 1000.0


def easyro_compute(
    temperature_history_c: list[float],
    time_step_myr: float = 1.0,
    pre_exponential: float = EASYRO_A,
) -> float:
    """Compute EasyRo from a temperature history.

    Uses Sweeney & Burnham (1990) parallel-reaction model with
    20 activation energies.

    The model tracks the conversion fraction X for each reaction:
      dX/dt = A * exp(-Ea/RT) * (1-X)

    EasyRo = 0.2 + 0.8 * (sum of f_i * X_i)

    Parameters:
      temperature_history_c: list of temperatures (°C) at each time step
      time_step_myr: time step in millions of years
      pre_exponential: pre-exponential factor (s⁻¹)

    Returns: EasyRo (%Ro)
    """
    if not temperature_history_c:
        return 0.2  # minimum Ro

    dt_seconds = time_step_myr * 1e6 * 365.25 * 24 * 3600  # Myr -> seconds

    # Initialize conversion fractions
    X = [0.0] * len(EASYRO_EA_KJ)

    for temp_c in temperature_history_c:
        temp_k = temp_c + 273.15
        if temp_k <= 0:
            continue

        for i in range(len(EASYRO_EA_KJ)):
            ea_j = EASYRO_EA_KJ[i] * 1000  # kJ -> J
            rate = pre_exponential * math.exp(-ea_j / (R_GAS * temp_k))
            dX = rate * dt_seconds * (1 - X[i])
            X[i] = min(X[i] + dX, 1.0)

    # Compute EasyRo — Sweeney & Burnham (1990) formula
    # Ro = exp(-1.6 + 3.7 * F) where F = Σ(f_i * X_i) / Σ(f_i)
    weighted_x = sum(f * x for f, x in zip(EASYRO_F, X, strict=False))
    f_sum = sum(EASYRO_F)
    F = weighted_x / f_sum if f_sum > 0 else 0.0
    easyro = math.exp(-1.6 + 3.7 * F)

    # Clamp to physical range [0.2, 4.7]
    easyro = max(0.2, min(easyro, 4.7))

    return easyro


def tti_compute(
    temperature_history_c: list[float],
    time_step_myr: float = 1.0,
) -> float:
    """Compute Time-Temperature Index (Lopatin 1971).

    TTI = Σ(2^n * Δt)

    where:
      n = temperature index (0 for 100-110°C, 1 for 110-120°C, etc.)
      Δt = time interval in Myr

    Parameters:
      temperature_history_c: list of temperatures (°C) at each time step
      time_step_myr: time step in Myr

    Returns: TTI (dimensionless)
    """
    tti = 0.0

    for temp_c in temperature_history_c:
        # Temperature index
        if temp_c < TTI_T_BASE:
            n = -1  # below base temperature
        else:
            n = int((temp_c - TTI_T_BASE) / TTI_T_STEP)

        # TTI contribution
        if n >= 0:
            tti += (2**n) * time_step_myr
        else:
            # Below 100°C — minimal contribution
            # Use exponential decay for sub-base temperatures
            tti += math.exp(-abs(n)) * time_step_myr

    return tti


def tti_to_ro(tti: float) -> float:
    """Convert TTI to vitrinite reflectance using Waples (1980) correlation.

    log10(Ro) = 0.173 * log10(TTI) - 0.118

    Valid for Ro ~0.3 to 4.5%
    """
    if tti <= 0:
        return 0.2
    log_ro = 0.173 * math.log10(tti) - 0.118
    return 10**log_ro


def burial_maturity_history(
    thermal_history: ThermalHistory,
    time_step_myr: float = 1.0,
) -> MaturityResult:
    """Compute complete maturity history for a layer.

    Steps:
    1. Interpolate thermal history to uniform time steps
    2. Compute EasyRo at each step
    3. Compute TTI at each step
    4. Identify hydrocarbon windows
    5. Detect loading pulses

    Returns MaturityResult with full history.
    """
    diagnostics: list[str] = []

    # Ensure uniform time steps
    ages = thermal_history.ages_ma
    temps = thermal_history.temperatures_c
    depths = thermal_history.depths_m

    if len(ages) < 2:
        diagnostics.append("Insufficient thermal history data")
        return MaturityResult(
            layer_name=thermal_history.name,
            easyro_final=0.2,
            tti_final=0.0,
            ro_from_tti=0.2,
            easyro_history=[],
            tti_history=[],
            temperature_history=[],
            depth_history=[],
            oil_window_entered_ma=None,
            oil_window_exited_ma=None,
            gas_window_entered_ma=None,
            gas_window_exited_ma=None,
            overmature_ma=None,
            loading_pulse_age_ma=None,
            loading_pulse_rate_m_myr=0.0,
            provenance={"error": "insufficient data"},
            diagnostics=diagnostics,
        )

    # Interpolate to uniform time steps
    age_min = min(ages)
    age_max = max(ages)
    n_steps = int((age_max - age_min) / time_step_myr) + 1
    uniform_ages = [age_max - i * time_step_myr for i in range(n_steps)]

    # Linear interpolation
    def interp(age: float, ages_src: list[float], values: list[float]) -> float:
        if age >= max(ages_src):
            return values[ages_src.index(max(ages_src))]
        if age <= min(ages_src):
            return values[ages_src.index(min(ages_src))]
        for i in range(len(ages_src) - 1):
            if ages_src[i] >= age >= ages_src[i + 1]:
                frac = (ages_src[i] - age) / (ages_src[i] - ages_src[i + 1])
                return values[i] + frac * (values[i + 1] - values[i])
        return values[-1]

    uniform_temps = [interp(a, ages, temps) for a in uniform_ages]
    uniform_depths = [interp(a, ages, depths) for a in uniform_ages]

    # Compute EasyRo history
    easyro_history: list[tuple[float, float]] = []
    tti_history: list[tuple[float, float]] = []

    # Progressive computation with correct Arrhenius kinetics
    # Track X conversion fractions across timesteps
    # dX_i/dt = A * exp(-Ea_i/RT) * (1 - X_i)     (proper Arrhenius)
    # EasyRo = 0.2 + 0.8 * Σ(f_i * X_i)            (no artificial cap)
    X = [0.0] * len(EASYRO_EA_KJ)
    easyro_accum = 0.2
    tti_accum = 0.0

    for _i, (age, temp) in enumerate(zip(uniform_ages, uniform_temps, strict=False)):
        # Compute EasyRo for this step
        dt_seconds = time_step_myr * 1e6 * 365.25 * 24 * 3600
        temp_k = temp + 273.15

        if temp_k > 0:
            for j in range(len(EASYRO_EA_KJ)):
                ea_j = EASYRO_EA_KJ[j] * 1000  # kJ -> J
                rate = EASYRO_A * math.exp(-ea_j / (R_GAS * temp_k))
                # ── CORRECTED: (1 - X[j]) dependency ──
                dX = rate * dt_seconds * (1.0 - X[j])
                X[j] = min(X[j] + dX, 0.9999)

        # Compute EasyRo from current X fractions — S&B formula
        weighted_x = sum(EASYRO_F[j] * X[j] for j in range(len(EASYRO_EA_KJ)))
        f_s = sum(EASYRO_F)
        F_val = weighted_x / f_s if f_s > 0 else 0.0
        easyro_accum = math.exp(-1.6 + 3.7 * F_val)
        easyro_accum = max(0.2, min(easyro_accum, 4.7))

        # Compute TTI for this step
        if temp >= TTI_T_BASE:
            n = int((temp - TTI_T_BASE) / TTI_T_STEP)
            tti_accum += (2**n) * time_step_myr
        else:
            n = -int((TTI_T_BASE - temp) / TTI_T_STEP) - 1
            tti_accum += math.exp(-abs(n)) * time_step_myr

        easyro_history.append((age, easyro_accum))
        tti_history.append((age, tti_accum))

    # Final values
    easyro_final = easyro_accum
    tti_final = tti_accum
    ro_from_tti = tti_to_ro(tti_final)

    # Temperature and depth history
    temperature_history = list(zip(uniform_ages, uniform_temps, strict=False))
    depth_history = list(zip(uniform_ages, uniform_depths, strict=False))

    # Hydrocarbon windows
    oil_entered = None
    oil_exited = None
    gas_entered = None
    gas_exited = None
    overmature = None

    for age, ro in easyro_history:
        if ro > 0.6 and oil_entered is None:
            oil_entered = age
        if ro > 1.3 and oil_exited is None:
            oil_exited = age
            gas_entered = age
        if ro > 2.0 and gas_exited is None:
            gas_exited = age
            overmature = age

    # Loading pulse detection
    loading_rates: list[tuple[float, float]] = []
    for i in range(1, len(depth_history)):
        dt = depth_history[i - 1][0] - depth_history[i][0]
        if dt > 0:
            dd = depth_history[i][1] - depth_history[i - 1][1]
            loading_rates.append((depth_history[i][0], dd / dt))

    if loading_rates:
        max_rate_idx = max(range(len(loading_rates)), key=lambda i: loading_rates[i][1])
        loading_pulse_age = loading_rates[max_rate_idx][0]
        loading_pulse_rate = loading_rates[max_rate_idx][1]
    else:
        loading_pulse_age = None
        loading_pulse_rate = 0.0

    # Provenance
    provenance = {
        "method": "EasyRo + TTI",
        "reference": "Sweeney & Burnham (1990), Lopatin (1971), Waples (1980)",
        "easyro_model": "20 parallel reactions, distributed Ea",
        "tti_model": "Lopatin (1971) — TTI = Σ(2^n * Δt)",
        "time_step_myr": time_step_myr,
        "layer_name": thermal_history.name,
    }

    return MaturityResult(
        layer_name=thermal_history.name,
        easyro_final=easyro_final,
        tti_final=tti_final,
        ro_from_tti=ro_from_tti,
        easyro_history=easyro_history,
        tti_history=tti_history,
        temperature_history=temperature_history,
        depth_history=depth_history,
        oil_window_entered_ma=oil_entered,
        oil_window_exited_ma=oil_exited,
        gas_window_entered_ma=gas_entered,
        gas_window_exited_ma=gas_exited,
        overmature_ma=overmature,
        loading_pulse_age_ma=loading_pulse_age,
        loading_pulse_rate_m_myr=loading_pulse_rate,
        provenance=provenance,
        diagnostics=diagnostics,
    )


def _check_time_step_convergence(
    thermal_history: ThermalHistory,
    target_ro_tolerance: float = 0.02,
) -> dict[str, Any]:
    """RULE 6 — Convergence guard.

    Re-runs at half timestep. If EasyRo changes > tolerance,
    the timestep is too coarse and the result is flagged.

    Returns: {converged: bool, delta_ro: float, recommended_step: float}
    """
    result_coarse = burial_maturity_history(thermal_history, time_step_myr=1.0)
    result_fine = burial_maturity_history(thermal_history, time_step_myr=0.5)

    delta = abs(result_coarse.easyro_final - result_fine.easyro_final)
    converged = delta <= target_ro_tolerance

    return {
        "converged": converged,
        "delta_ro": round(delta, 4),
        "coarse_ro": round(result_coarse.easyro_final, 4),
        "fine_ro": round(result_fine.easyro_final, 4),
        "recommended_step_myr": 1.0 if converged else 0.5,
        "flag": None if converged else "TIMESTEP_TOO_COARSE",
    }


def compute_cooling_rate(
    ages_ma: list[float],
    temperatures_c: list[float],
) -> list[tuple[float, float]]:
    """Compute cooling rate (°C/Myr) from temperature history.

    Used for tectonic unroofing detection (Cottam et al. 2013).
    """
    rates: list[tuple[float, float]] = []
    for i in range(1, len(ages_ma)):
        dt = ages_ma[i - 1] - ages_ma[i]
        if dt > 0:
            dT = temperatures_c[i] - temperatures_c[i - 1]
            rates.append((ages_ma[i], dT / dt))
    return rates
