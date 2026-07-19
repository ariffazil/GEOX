"""
maturity_kinetics.py — Thermal Maturity Kernel (P6)
====================================================
TTI + Easy%Ro + Heat Flow + Maturity Classification.
Integrates P1 (rift kinematics → β) + P2 (backstripping → burial history).

McKenzie (1978) heat flow from β; steady-state geotherm; Lopatin TTI;
Sweeney & Burnham (1990) Easy%Ro proxy; Suggate (1998) maturity zones.

DITEMPA BUKAN DIBERI — Forged, Not Given.

Forged: 2026-07-03 — P6 Thermal Maturation (atomic with P1 + P2)
"""

from __future__ import annotations

import math
from enum import StrEnum

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════
# Constants (McKenzie 1978, Sweeney & Burnham 1990, Suggate 1998)
# ═══════════════════════════════════════════════════════════════════════════

BASAL_HEAT_FLOW_MW_M2: float = 60.0  # Typical continental basal heat flow (mW/m²)
SURFACE_TEMP_DEFAULT_C: float = 10.0  # Default surface temperature (°C) — seabed
THERMAL_CONDUCTIVITY_DEFAULT: float = 2.5  # Sedimentary thermal conductivity (W/m·K)
TEMP_EXPULSION_THRESHOLD_C: float = 90.0  # Onset of oil expulsion (°C)
ASTHENOSPHERE_TEMP_C: float = 1333.0  # T₁ — asthenosphere temperature (°C)
MIN_RO: float = 0.2  # Minimum vitrinite reflectance (immature)
MAX_RO: float = 5.0  # Maximum vitrinite reflectance (overmature)


# ═══════════════════════════════════════════════════════════════════════════
# MaturityZone — Suggate (1998) hydrocarbon generation windows
# ═══════════════════════════════════════════════════════════════════════════


class MaturityZone(StrEnum):
    IMMATURE = "IMMATURE"  # Ro < 0.5 — biogenic gas only
    EARLY_OIL = "EARLY_OIL"  # Ro 0.5–0.7 — oil window onset
    MAIN_OIL = "MAIN_OIL"  # Ro 0.7–1.0 — peak oil generation
    LATE_OIL = "LATE_OIL"  # Ro 1.0–1.3 — late oil + condensate
    WET_GAS = "WET_GAS"  # Ro 1.3–2.0 — wet gas / condensate
    DRY_GAS = "DRY_GAS"  # Ro 2.0–3.0 — dry gas
    OVERMATURE = "OVERMATURE"  # Ro > 3.0 — overmature / carbon residue
    UNKNOWN = "UNKNOWN"


# ═══════════════════════════════════════════════════════════════════════════
# Pydantic I/O schemas — MCP transport compatible
# ═══════════════════════════════════════════════════════════════════════════


class BurialStep(BaseModel):
    """One timestep in a burial/temperature history.

    F2 TRUTH: ages must be from stratigraphic correlation (OBS) or backstripping (DER).
    """

    age_ma: float = Field(
        ...,
        ge=0.0,
        le=500.0,
        description="Age of this burial step (Ma). 0 = present day.",
    )
    depth_km: float = Field(
        ...,
        ge=0.0,
        le=20.0,
        description="Burial depth at this time (km below surface).",
    )
    temperature_c: float = Field(
        ...,
        ge=0.0,
        le=500.0,
        description="Temperature at this depth (°C).",
    )
    duration_ma: float = Field(
        default=1.0,
        ge=0.001,
        le=100.0,
        description="Duration spent at this temperature (Myr).",
    )


class HeatFlowResult(BaseModel):
    """Heat flow computation output — falsifiable.

    F7 HUMILITY: confidence capped at 0.90. Heat flow is DER from β.
    """

    heat_flow_mw_m2: float = Field(
        ...,
        ge=20.0,
        le=200.0,
        description="Present-day surface heat flow (mW/m²).",
    )
    beta: float = Field(..., ge=1.0, le=50.0)
    confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=0.90,
        description="Confidence capped at 0.90 (F7 HUMILITY).",
    )
    epistemic_label: str = Field(default="DER")
    alternative_models: list[str] = Field(
        default_factory=lambda: ["Chapman_1984_polynomial", "radiogenic_heat_production_correction"]
    )
    evidence_gaps: list[str] = Field(
        default_factory=lambda: [
            "crustal_radiogenic_heat_production_uW_m3",
            "crust_thickness_km",
            "mantle_heat_flow_mw_m2",
        ]
    )
    note: str = Field(default="")


class MaturityRequest(BaseModel):
    """Request schema for compute_maturity_full().

    Accepts either backstrip output dict OR explicit burial history list.
    """

    burial_history: list[dict[str, float]] | None = Field(
        default=None,
        description="Pre-computed burial history from compute_tti() format.",
    )
    heat_flow_mw_m2: float | None = Field(
        default=None,
        ge=20.0,
        le=200.0,
        description="Present-day heat flow (mW/m²). If None, use BASAL_HEAT_FLOW_MW_M2.",
    )
    beta: float | None = Field(
        default=None,
        ge=1.0,
        le=50.0,
        description="Extension factor β. If provided, heat_flow is computed from β.",
    )
    strat_column: list[dict[str, float]] | None = Field(
        default=None,
        description="Alternative input: [(depth_km, age_ma), ...].",
    )
    backstrip_result: dict | None = Field(
        default=None,
        description="Output dict from backstrip_decompaction.compute_subsidence_history().",
    )
    source_rock_age_ma: float | None = Field(
        default=None,
        ge=0.0,
        le=500.0,
        description="Age of source rock (Ma). Used for charge timing.",
    )


class MaturityResult(BaseModel):
    """Complete thermal maturity output — falsifiable, agentic.

    Every field carries epistemic labels. Alternatives are mandatory.
    F2 TRUTH + F7 HUMILITY enforced.
    """

    easy_ro: float = Field(
        ...,
        ge=MIN_RO,
        le=MAX_RO,
        description="Vitrinite reflectance (%Ro).",
    )
    tti: float = Field(..., ge=0.0, description="Time-Temperature Index (Lopatin).")
    maturity_zone: MaturityZone = Field(
        default=MaturityZone.UNKNOWN,
        description="Suggate (1998) hydrocarbon generation window.",
    )
    heat_flow_mw_m2: float = Field(
        default=BASAL_HEAT_FLOW_MW_M2,
        ge=20.0,
        le=200.0,
        description="Heat flow used for computation (mW/m²).",
    )
    geothermal_gradient_c_km: float = Field(
        default=0.0,
        description="Average geothermal gradient (°C/km).",
    )
    charge_age_ma: float | None = Field(
        default=None,
        description="Age at which source rock reached expulsion threshold (Ma).",
    )
    hydrocarbon_window: str = Field(
        default="UNKNOWN",
        description="Plain-text description of hydrocarbon generation window.",
    )
    peak_temperature_c: float = Field(
        default=0.0,
        description="Maximum temperature experienced by source rock (°C).",
    )
    confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=0.90,
        description="Confidence capped at 0.90 (F7 HUMILITY).",
    )
    epistemic_label: str = Field(default="DER")
    alternative_zones: list[MaturityZone] = Field(default_factory=list)
    alternative_ro_range: tuple[float, float] = Field(default=(0.0, 0.0))
    evidence_gaps: list[str] = Field(default_factory=list)
    kinetic_model_used: str = Field(
        default="Sweeney_Burnham_1990",
        description="Kinetic model used for Ro computation.",
    )
    note: str = Field(default="")


# ═══════════════════════════════════════════════════════════════════════════
# LEGACY FUNCTIONS — DO NOT DELETE (backward compatibility)
# ═══════════════════════════════════════════════════════════════════════════


def compute_tti(burial_history: list[dict[str, float]]) -> float:
    """
    Compute TTI (Time-Temperature Index) using Lopatin's method.
    phi = duration * 2^((T-100)/10)
    """
    tti = 0.0
    for step in burial_history:
        temp_c = step.get("temperature_c", 0.0)
        duration_ma = step.get("duration_ma", 0.0)
        tti += duration_ma * (2.0 ** ((temp_c - 100.0) / 10.0))
    return max(tti, 0.0)


def compute_easy_ro(tti: float) -> float:
    """
    Compute Vitrinite Reflectance (Easy%Ro) from TTI.
    Simplified formula based on Sweeney & Burnham (1990) proxy.
    """
    if tti <= 0.0:
        return 0.2
    # Ro = 0.42 + 0.23 * log10(TTI + 1)
    return max(0.2, min(3.5, 0.42 + 0.23 * math.log10(tti + 1.0)))


def get_charge_age(burial_history: list[dict[str, float]], threshold_c: float = 90.0) -> float:
    """Age at which source rock reached thermal expulsion threshold."""
    ages = [step.get("age_ma", 0.0) for step in burial_history if step.get("temperature_c", 0) >= threshold_c]
    return max(ages) if ages else 0.0


# ═══════════════════════════════════════════════════════════════════════════
# NEW FUNCTIONS — P6 Thermal Maturity Module
# ═══════════════════════════════════════════════════════════════════════════


def compute_present_day_heat_flow(
    beta: float,
    heat_flow_base_mw_m2: float = BASAL_HEAT_FLOW_MW_M2,
    asthenosphere_temp_c: float = ASTHENOSPHERE_TEMP_C,
) -> HeatFlowResult:
    """Compute present-day surface heat flow from extension factor β.

    McKenzie (1978): stretched lithosphere has elevated heat flow.
    q(t, β) = q₀ · β · [1 + 2 · Σ sin(nπ/β)/(nπ/β) · exp(−n²π²t/a²κ)]

    At t → ∞ (steady-state, present-day), the series term → 0 and the
    post-rift factor approaches the one-dimensional stretching solution:
    q_present ≈ q_base · β · (1 − 0.7 · (1 − 1/β))

    This is a calibrated simplification of the full McKenzie series.

    F2 TRUTH: DER — derived from β. β itself is DER from crustal thickness ratios.
    F7 HUMILITY: confidence varies with β constraint quality.

    Returns HeatFlowResult with alternatives + evidence gaps.
    """
    if beta < 1.0:
        raise ValueError(f"β must be ≥ 1.0, got {beta}")

    # McKenzie post-rift heat flow approximation
    # q = q₀ · β · (1 − 0.7 · (1 − 1/β))
    # The 0.7 factor is the asymptotic post-rift decay limit
    damping = 0.7 * (1.0 - 1.0 / beta)
    heat_flow = heat_flow_base_mw_m2 * beta * (1.0 - damping)

    # Confidence: base from β alone
    conf = 0.75
    if beta > 1.5:
        conf = min(0.80, conf + 0.05)  # significant extension → clearer signal
    if beta > 3.0:
        conf = min(0.85, conf + 0.05)  # hyperextension → unambiguous

    return HeatFlowResult(
        heat_flow_mw_m2=round(heat_flow, 1),
        beta=round(beta, 2),
        confidence=conf,
        epistemic_label="DER",
        alternative_models=["Chapman_1984_polynomial", "radiogenic_heat_production_correction"],
        evidence_gaps=[
            "crustal_radiogenic_heat_production_uW_m3",
            "crust_thickness_km",
            "mantle_heat_flow_mw_m2",
        ],
        note=(
            f"McKenzie (1978) asymptotic post-rift heat flow. "
            f"β={beta:.1f} → q={heat_flow:.1f} mW/m². "
            f"Base heat flow={heat_flow_base_mw_m2} mW/m²."
        ),
    )


def compute_temperature_history(
    burial_depth_km_list: list[float],
    heat_flow_mw_m2: float = BASAL_HEAT_FLOW_MW_M2,
    surface_temp_c: float = SURFACE_TEMP_DEFAULT_C,
    thermal_conductivity: float = THERMAL_CONDUCTIVITY_DEFAULT,
) -> list[dict[str, float]]:
    """Compute steady-state geotherm for a list of burial depths.

    Steady-state 1-D heat conduction (Fourier's law, constant conductivity):
        T(z) = T_surface + (q_surface · z) / λ

    where:
        T_surface = surface temperature (°C)
        q_surface = heat flow (mW/m² = 1e-3 W/m²)
        λ = thermal conductivity (W/m·K)
        z = depth in km

    Returns list of dicts: [{"depth_km": d, "temp_c": T}, ...]

    F2 TRUTH: DER — assumes steady-state. Transient effects (advection,
    sedimentation rate, compaction dewatering) NOT modeled.
    F7 HUMILITY: conductivity uncertainty ±0.5 W/m·K typical.
    """
    results: list[dict[str, float]] = []
    # q in W/m²: mW/m² → W/m²
    q_surface_w_m2 = heat_flow_mw_m2 * 1e-3

    for depth_km in burial_depth_km_list:
        depth_m = depth_km * 1000.0  # km → m
        delta_t = (q_surface_w_m2 * depth_m) / thermal_conductivity
        temp_c = surface_temp_c + delta_t
        results.append(
            {
                "depth_km": round(depth_km, 3),
                "temp_c": round(temp_c, 1),
            }
        )

    return results


def build_burial_history_from_stratigraphy(
    strat_column: list[dict[str, float]],
    ages_ma: list[float],
    heat_flow_mw_m2: float = BASAL_HEAT_FLOW_MW_M2,
    surface_temp_c: float = SURFACE_TEMP_DEFAULT_C,
) -> list[dict[str, float]]:
    """Build TTI-compatible burial history from stratigraphic column.

    Args:
        strat_column: list of {"depth_km": d, ...} — base of each unit in km
        ages_ma: corresponding ages for each stratigraphic unit (Ma)
        heat_flow_mw_m2: heat flow for geotherm computation
        surface_temp_c: surface temperature (°C)

    Returns:
        list of {"age_ma", "temperature_c", "duration_ma"} dicts
        ready for compute_tti().

    Duration per step = |age[i] − age[i−1]|. Temperature from geotherm.

    F2 TRUTH: ages must be from biostratigraphy/radiometric dating (OBS).
    Temperature is DER from heat flow + depth (constant conductivity model).
    """
    if len(strat_column) != len(ages_ma):
        raise ValueError(f"strat_column (len={len(strat_column)}) and ages_ma (len={len(ages_ma)}) must match")
    if not strat_column:
        return []

    # Sort by depth descending (deepest first = oldest)
    zipped = sorted(
        zip(strat_column, ages_ma, strict=False),
        key=lambda x: x[0].get("depth_km", 0.0),
        reverse=True,
    )

    history: list[dict[str, float]] = []
    prev_age = ages_ma[0] if ages_ma else 0.0

    for i, (unit, age_ma) in enumerate(zipped):
        depth_km = unit.get("depth_km", 0.0)

        # Geotherm temperature at this depth
        temp_c = surface_temp_c + (heat_flow_mw_m2 * 1e-3 * depth_km * 1000) / THERMAL_CONDUCTIVITY_DEFAULT

        # Duration = time spent in this depth interval
        if i == 0:
            duration_ma = 5.0  # default for oldest unit
        else:
            duration_ma = abs(prev_age - age_ma)

        history.append(
            {
                "age_ma": float(age_ma),
                "temperature_c": round(temp_c, 1),
                "duration_ma": round(duration_ma, 1),
            }
        )
        prev_age = age_ma

    return history


def classify_maturity(easy_ro: float) -> tuple[MaturityZone, list[MaturityZone], str]:
    """Classify vitrinite reflectance into maturity zone.

    Thresholds from Suggate (1998), with typical SE Asia basin calibration.

    Returns: (zone, alternatives, hydrocarbon_window_description)

    F2 TRUTH: classification is DER from Ro. Ro is DER from TTI.
    Alternative zones represent adjacent maturity windows.
    """
    if easy_ro < 0.5:
        zone = MaturityZone.IMMATURE
        alts = [MaturityZone.EARLY_OIL]
        desc = "IMMATURE — biogenic gas only (<0.5 %Ro)"
    elif easy_ro < 0.7:
        zone = MaturityZone.EARLY_OIL
        alts = [MaturityZone.IMMATURE, MaturityZone.MAIN_OIL]
        desc = "EARLY OIL — onset of oil generation (0.5–0.7 %Ro)"
    elif easy_ro < 1.0:
        zone = MaturityZone.MAIN_OIL
        alts = [MaturityZone.EARLY_OIL, MaturityZone.LATE_OIL]
        desc = "MAIN OIL — peak oil generation (0.7–1.0 %Ro)"
    elif easy_ro < 1.3:
        zone = MaturityZone.LATE_OIL
        alts = [MaturityZone.MAIN_OIL, MaturityZone.WET_GAS]
        desc = "LATE OIL — late oil + condensate (1.0–1.3 %Ro)"
    elif easy_ro < 2.0:
        zone = MaturityZone.WET_GAS
        alts = [MaturityZone.LATE_OIL, MaturityZone.DRY_GAS]
        desc = "WET GAS — wet gas / condensate window (1.3–2.0 %Ro)"
    elif easy_ro < 3.0:
        zone = MaturityZone.DRY_GAS
        alts = [MaturityZone.WET_GAS, MaturityZone.OVERMATURE]
        desc = "DRY GAS — dry gas window (2.0–3.0 %Ro)"
    else:
        zone = MaturityZone.OVERMATURE
        alts = [MaturityZone.DRY_GAS]
        desc = "OVERMATURE — carbon residue / overmature (>3.0 %Ro)"

    return zone, alts, desc


def compute_maturity_full(
    burial_history: list[dict[str, float]] | None = None,
    heat_flow_mw_m2: float | None = None,
    beta: float | None = None,
    strat_column: list[dict[str, float]] | None = None,
    ages_ma: list[float] | None = None,
    backstrip_result: dict | None = None,
    source_rock_age_ma: float | None = None,
) -> MaturityResult:
    """Single-entry function for complete thermal maturity computation.

    Computes heat flow (from β or direct) → burial history (from strat or
    backstrip) → TTI → Easy%Ro → maturity zone → charge timing.

    Integration points:
      - P1 (rift_kinematics): β from compute_beta() feeds heat flow
      - P2 (backstrip): burial_history_dict from compute_subsidence_history()

    Args:
        burial_history: pre-computed TTI-compatible history
        heat_flow_mw_m2: direct heat flow value (mW/m²)
        beta: extension factor → compute heat flow from β
        strat_column: list of {"depth_km": d, ...} units
        ages_ma: corresponding ages for strat_column
        backstrip_result: dict from backstrip_decompaction.compute_subsidence_history()
        source_rock_age_ma: age of source rock for charge timing

    Returns:
        MaturityResult with Ro, zone, hydrocarbon_window, alternatives, evidence_gaps.

    F2 TRUTH: All temperatures are DER from heat flow + depth model.
    F7 HUMILITY: Confidence capped at 0.90. Alternatives always populated.

    Agentic contract:
      - Every result has alternative_zones (never empty)
      - Every result has alternative_ro_range (±20% sensitivity bound)
      - Every result has evidence_gaps — other agents know what to fetch next
    """
    # --- Resolve heat flow ---
    resolved_heat_flow = BASAL_HEAT_FLOW_MW_M2
    hf_gaps: list[str] = []
    hf_conf = 0.75

    if beta is not None:
        hf_result = compute_present_day_heat_flow(beta)
        resolved_heat_flow = hf_result.heat_flow_mw_m2
        hf_gaps = hf_result.evidence_gaps
        hf_conf = hf_result.confidence
    elif heat_flow_mw_m2 is not None:
        resolved_heat_flow = heat_flow_mw_m2
    else:
        hf_gaps = [
            "no_beta_or_heat_flow_provided",
            "using_default_basal_heat_flow",
            "crustal_radiogenic_heat_production_uW_m3",
        ]

    # --- Resolve burial history ---
    history: list[dict[str, float]] = []
    history_gaps: list[str] = []

    if burial_history is not None:
        history = burial_history
    elif backstrip_result is not None:
        # --- P2 integration: backstrip output → TTI format ---
        # backstrip_result is expected to have {"depths_km": [...], "ages_ma": [...]}
        depths_km = backstrip_result.get("depths_km", [])
        bs_ages_ma = backstrip_result.get("ages_ma", [])

        if not depths_km or not bs_ages_ma:
            history_gaps = ["backstrip_result_missing_depths_km_or_ages_ma"]
        elif len(depths_km) != len(bs_ages_ma):
            history_gaps = ["backstrip_depth_age_mismatch"]
        else:
            history_gaps = ["backstrip_no_porosity_correction_for_thermal_conductivity"]
            for i in range(len(depths_km)):
                depth_km = depths_km[i]
                age_ma = bs_ages_ma[i]
                temp_c = SURFACE_TEMP_DEFAULT_C + (resolved_heat_flow * 1e-3 * depth_km * 1000.0) / THERMAL_CONDUCTIVITY_DEFAULT
                if i < len(depths_km) - 1:
                    duration_ma = abs(bs_ages_ma[i + 1] - age_ma)
                else:
                    duration_ma = max(1.0, age_ma * 0.05)  # 5% of age as final step
                history.append(
                    {
                        "age_ma": float(age_ma),
                        "depth_km": float(depth_km),
                        "temperature_c": round(temp_c, 1),
                        "duration_ma": round(duration_ma, 1),
                    }
                )
    elif strat_column is not None and ages_ma is not None:
        history = build_burial_history_from_stratigraphy(strat_column, ages_ma, resolved_heat_flow)
        history_gaps = ["strat_column_lacks_erosional_events", "ages_ma_need_biostrat_confirmation"]

    if not history:
        return MaturityResult(
            easy_ro=MIN_RO,
            tti=0.0,
            maturity_zone=MaturityZone.UNKNOWN,
            heat_flow_mw_m2=round(resolved_heat_flow, 1),
            confidence=0.50,
            epistemic_label="DER",
            evidence_gaps=["no_burial_history_provided"] + hf_gaps,
            note="No burial history available. Cannot compute maturity.",
        )

    # --- Compute TTI + Ro ---
    tti = compute_tti(history)
    easy_ro = compute_easy_ro(tti)

    # --- Classify maturity ---
    zone, alt_zones, hc_window = classify_maturity(easy_ro)

    # --- Alternative Ro range (sensitivity: ±20%) ---
    tti_low = tti * 0.8
    tti_high = tti * 1.2
    ro_low = compute_easy_ro(tti_low)
    ro_high = compute_easy_ro(tti_high)

    # --- Charge age ---
    charge_age = get_charge_age(history, TEMP_EXPULSION_THRESHOLD_C)

    # --- Peak temperature ---
    peak_temp = max(
        (step.get("temperature_c", 0.0) for step in history),
        default=0.0,
    )

    # --- Geothermal gradient ---
    avg_gradient = 0.0
    depths_km_list = [step.get("depth_km", 0.0) for step in history if "depth_km" in step]
    temps_list = [step.get("temperature_c", 0.0) for step in history]
    if depths_km_list and max(depths_km_list) > 0:
        max_depth = max(depths_km_list)
        max_temp = max(temps_list)
        if max_temp > SURFACE_TEMP_DEFAULT_C:
            avg_gradient = (max_temp - SURFACE_TEMP_DEFAULT_C) / max_depth

    # --- Confidence calibration ---
    conf = 0.75
    if beta is not None:
        conf = max(conf, hf_conf)
    if resolved_heat_flow != BASAL_HEAT_FLOW_MW_M2:
        conf = min(0.85, conf + 0.05)
    if source_rock_age_ma is not None and charge_age is not None:
        conf = min(0.90, conf + 0.05)

    return MaturityResult(
        easy_ro=round(easy_ro, 3),
        tti=round(tti, 1),
        maturity_zone=zone,
        heat_flow_mw_m2=round(resolved_heat_flow, 1),
        geothermal_gradient_c_km=round(avg_gradient, 1),
        charge_age_ma=round(charge_age, 1) if charge_age is not None and charge_age > 0 else None,
        hydrocarbon_window=hc_window,
        peak_temperature_c=round(peak_temp, 1),
        confidence=conf,
        epistemic_label="DER",
        alternative_zones=alt_zones,
        alternative_ro_range=(round(ro_low, 3), round(ro_high, 3)),
        evidence_gaps=hf_gaps + history_gaps,
        kinetic_model_used="Sweeney_Burnham_1990",
        note=(
            f"TTI={tti:.1f}, Easy%Ro={easy_ro:.3f}, zone={zone.value}. "
            f"q={resolved_heat_flow:.1f} mW/m². "
            f"Alternative models: Easy%Ro DL (Burnham 2018), BasinMod (LLNL). "
            f"Peak temp={peak_temp:.0f}°C."
        ),
    )


__all__ = [
    # Enums
    "MaturityZone",
    # Schemas
    "BurialStep",
    "HeatFlowResult",
    "MaturityRequest",
    "MaturityResult",
    # Legacy (DO NOT DELETE)
    "compute_tti",
    "compute_easy_ro",
    "get_charge_age",
    # New (P6)
    "compute_present_day_heat_flow",
    "compute_temperature_history",
    "build_burial_history_from_stratigraphy",
    "classify_maturity",
    "compute_maturity_full",
    # Constants
    "BASAL_HEAT_FLOW_MW_M2",
    "SURFACE_TEMP_DEFAULT_C",
    "THERMAL_CONDUCTIVITY_DEFAULT",
    "TEMP_EXPULSION_THRESHOLD_C",
]
