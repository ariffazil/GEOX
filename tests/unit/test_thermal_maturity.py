"""
test_thermal_maturity.py — Thermal Maturity Correctness Tests
=============================================================
Validates: EasyRo convergence, gradient sensitivity,
          Arrhenius (1-X) dependency, TTI monotonicity.

GEOX-HARDEN-001 :: Fix 0.4 — Calibrated for geological Myr timescales
A=2.0e14, Ea=180-370 kJ/mol, exp(-1.6+3.7F) formula
DITEMPA BUKAN DIBERI
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from geox_core.engines.basin.thermal_maturity import (
    ThermalHistory,
    easyro_compute,
    tti_compute,
    burial_maturity_history,
    SURFACE_TEMP_C,
)

SURFACE_TEMP = SURFACE_TEMP_C  # 20.0


def _make_thermal(
    name: str,
    ages: list[float],
    depths: list[float],
    gradient: float,
) -> ThermalHistory:
    """Helper: build ThermalHistory from ages, depths, gradient."""
    temps = [SURFACE_TEMP + gradient * d / 1000.0 for d in depths]
    n = len(ages)
    return ThermalHistory(
        name=name,
        ages_ma=ages,
        temperatures_c=temps,
        depths_m=depths,
        heat_flow_mw_m2=[gradient * 2.5] * n,
        geothermal_gradient_c_km=[gradient] * n,
    )


# ── TEST 1: Low gradient → immature ────────────────────────────────────
def test_easyro_immature_at_30_gradient():
    """30°C/km, 4000m, 15 Ma → immature (Ro < 0.55)."""
    th = _make_thermal("test", [15, 10, 5, 0], [0, 1200, 2800, 4000], 30.0)
    result = burial_maturity_history(th)
    assert result.easyro_final < 0.55, f"Expected immature (<0.55), got Ro={result.easyro_final:.3f}%"


# ── TEST 2: Elevated gradient → early oil ──────────────────────────────
def test_easyro_oil_window_at_38_gradient():
    """38°C/km → early oil window (Ro > 0.45)."""
    th = _make_thermal("test", [15, 10, 5, 0], [0, 1200, 2800, 4000], 38.0)
    result = burial_maturity_history(th)
    assert result.easyro_final > 0.45, f"Expected early oil (>0.45), got Ro={result.easyro_final:.3f}%"


# ── TEST 3: High gradient → oil window ─────────────────────────────────
def test_easyro_gas_window_at_50_gradient():
    """50°C/km → oil window (Ro > 0.80)."""
    th = _make_thermal("test", [15, 10, 5, 0], [0, 1200, 2800, 4000], 50.0)
    result = burial_maturity_history(th)
    assert result.easyro_final > 0.80, f"Expected oil window (>0.8), got Ro={result.easyro_final:.3f}%"


# ── TEST 4: Gradient separation ────────────────────────────────────────
def test_gradient_separation():
    """38°C/km and 50°C/km must produce DISTINCT Ro (Δ > 0.30)."""
    r38 = burial_maturity_history(_make_thermal("a", [15, 10, 5, 0], [0, 1200, 2800, 4000], 38.0)).easyro_final
    r50 = burial_maturity_history(_make_thermal("b", [15, 10, 5, 0], [0, 1200, 2800, 4000], 50.0)).easyro_final
    delta = abs(r50 - r38)
    assert delta > 0.30, f"Gradients 38 vs 50°C/km too similar: Δ={delta:.3f}%"


# ── TEST 5: (1-X) dependency ──────────────────────────────────────────
def test_arrhenius_one_minus_x_dependency():
    """200°C for 10 Myr — (1-X) prevents runaway but produces significant Ro."""
    temps = [200.0] * 10
    ro = easyro_compute(temps, time_step_myr=1.0)
    assert ro < 5.0, f"Ro={ro:.3f}% — physics should prevent runaway"
    assert ro > 0.70, f"Ro={ro:.3f}% — 10 Myr at 200°C should produce significant maturity"


# ── TEST 6: TTI monotonicity ────────────────────────────────────────────
def test_tti_increases_with_temperature():
    """TTI must be higher for higher temperatures at same duration."""
    tti_cold = tti_compute([100.0] * 5, time_step_myr=1.0)
    tti_hot = tti_compute([150.0] * 5, time_step_myr=1.0)
    assert tti_hot > tti_cold * 5, "TTI should increase with temperature"


# ── TEST 7: Hydrocarbon windows ────────────────────────────────────────
def test_hydrocarbon_windows_tracked():
    """Oil/gas window entry/exit must be physically ordered."""
    th = _make_thermal("test", [15, 10, 5, 0], [0, 1200, 2800, 4000], 42.0)
    result = burial_maturity_history(th)
    oe = result.oil_window_entered_ma
    ox = result.oil_window_exited_ma
    gx = result.gas_window_exited_ma
    if oe is not None and ox is not None:
        assert oe >= ox, f"Oil entry {oe} should be >= oil exit {ox}"
    if ox is not None and gx is not None:
        assert ox >= gx, f"Oil exit {ox} should be >= gas exit {gx}"


# ── TEST 8: Surface temperature → minimal maturity ─────────────────────
def test_easyro_minimum_at_surface():
    """At surface temperature only, Ro should be ~0.2 (immature)."""
    ro = easyro_compute([SURFACE_TEMP] * 10, time_step_myr=1.0)
    assert ro < 0.25, f"At surface temp, Ro should be ~0.2, got {ro:.3f}%"


# ── TEST 9: Convergence check ──────────────────────────────────────────
def test_timestep_convergence():
    """Half-timestep should not change EasyRo by more than 0.15."""
    th = _make_thermal("test", [15, 10, 5, 0], [0, 1200, 2800, 4000], 40.0)
    r1 = burial_maturity_history(th, time_step_myr=1.0)
    r2 = burial_maturity_history(th, time_step_myr=0.5)
    delta = abs(r1.easyro_final - r2.easyro_final)
    assert delta < 0.15, f"Timestep sensitivity too high: ΔRo={delta:.3f}%"
