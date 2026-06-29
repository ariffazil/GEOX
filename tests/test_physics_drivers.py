"""
Tests for geox_core.physics.drivers — Dynamic Physics: Forward, Inverse, Contrast, Metabolic
Covers build_lithology_model, anomaly_contrast_theory, inverse_physics9, and metabolic_loop.
DITEMPA BUKAN DIBERI
"""

import pytest
import math
from typing import Dict, Any

from geox_core.physics.state import Physics13State
from geox_core.physics.parameters import forward_physics9
from geox_core.physics.drivers import (
    build_lithology_model,
    anomaly_contrast_theory,
    inverse_physics9,
    metabolic_loop,
)


@pytest.fixture
def base_state():
    """Default state with sandstone-like baseline properties."""
    return Physics13State(
        rho=2350.0,
        vp=2950.0,
        vs=1680.0,
        rho_e=20.0,
        chi=0.0001,
        k=2.8,
        P=20e6,
        T=320.0,
        phi=0.25,
    )


# ─── Lithology Discrimination ─────────────────────────────────────────────────

def test_build_lithology_model_dolomite():
    # Vp > 5500
    state = Physics13State(rho=2850, vp=5600, vs=3000, rho_e=100, chi=0, k=3, P=0, T=0, phi=0.05)
    litho, conf, derived = build_lithology_model(state)
    assert litho == "Dolomite"
    assert conf == 0.85
    assert "K_GPa" in derived


def test_build_lithology_model_limestone():
    # Vp > 4000 (and <= 5500)
    state = Physics13State(rho=2710, vp=4500, vs=2400, rho_e=200, chi=0, k=3, P=0, T=0, phi=0.08)
    litho, conf, derived = build_lithology_model(state)
    assert litho == "Limestone"
    assert conf == 0.80


def test_build_lithology_model_anhydrite():
    # Vp > 3000 (and <= 4000) and vp/vs > 1.75
    state = Physics13State(rho=2900, vp=3500, vs=1800, rho_e=2000, chi=0, k=4, P=0, T=0, phi=0.01)
    litho, conf, derived = build_lithology_model(state)
    assert litho == "Anhydrite"
    assert conf == 0.75


def test_build_lithology_model_sandstone():
    # Vp > 2800 (and <= 3000) and phi > 0.20
    state = Physics13State(rho=2300, vp=2900, vs=1600, rho_e=20, chi=0, k=2, P=0, T=0, phi=0.22)
    litho, conf, derived = build_lithology_model(state)
    assert litho == "Sandstone"
    assert conf == 0.78


def test_build_lithology_model_shale():
    # Vp < 2500 and Vs < 1200
    state = Physics13State(rho=2350, vp=2400, vs=1100, rho_e=10, chi=0, k=1.5, P=0, T=0, phi=0.32)
    litho, conf, derived = build_lithology_model(state)
    assert litho == "Shale"
    assert conf == 0.82


def test_build_lithology_model_coal():
    # Vp < 2200 and rho < 1700 (and not matching previous)
    state = Physics13State(rho=1400, vp=2000, vs=1250, rho_e=500, chi=0, k=0.3, P=0, T=0, phi=0.08)
    litho, conf, derived = build_lithology_model(state)
    assert litho == "Coal"
    assert conf == 0.70


def test_build_lithology_model_mixed():
    # Default case
    state = Physics13State(rho=2500, vp=2700, vs=1500, rho_e=50, chi=0, k=2, P=0, T=0, phi=0.15)
    litho, conf, derived = build_lithology_model(state)
    assert litho == "Mixed"
    assert conf == 0.50


# ─── Theory of Anomalous Contrast ───────────────────────────────────────────

def test_anomaly_contrast_theory_identical(base_state):
    result = anomaly_contrast_theory(base_state, base_state)
    assert result["AC_Risk"] == 0.0
    assert result["u_ambiguity"] == 0.0
    assert result["D_transform"] == 0.0
    assert result["B_cog"] == 1.0
    assert result["verdict"] == "SEAL"


def test_anomaly_contrast_theory_low_risk(base_state):
    # Small modification
    observed = Physics13State(
        rho=base_state.rho + 10,
        vp=base_state.vp + 50,
        vs=base_state.vs,
        rho_e=base_state.rho_e + 10,
        chi=base_state.chi,
        k=base_state.k,
        P=base_state.P,
        T=base_state.T,
        phi=base_state.phi + 0.01,
    )
    result = anomaly_contrast_theory(base_state, observed)
    assert result["AC_Risk"] > 0
    assert result["verdict"] in ("SEAL", "HOLD", "VOID")


def test_anomaly_contrast_theory_high_risk(base_state):
    # Significant deviation
    observed = Physics13State(
        rho=base_state.rho + 400,
        vp=base_state.vp + 1500,
        vs=base_state.vs,
        rho_e=base_state.rho_e + 300,
        chi=base_state.chi,
        k=base_state.k,
        P=base_state.P,
        T=base_state.T,
        phi=base_state.phi + 0.25,
    )
    result = anomaly_contrast_theory(base_state, observed)
    # AC_Risk should be higher, check boundaries for verdict
    assert result["AC_Risk"] > 0
    risk = result["AC_Risk"]
    if risk < 0.5:
        assert result["verdict"] == "SEAL"
    elif risk < 1.5:
        assert result["verdict"] == "HOLD"
    else:
        assert result["verdict"] == "VOID"


# ─── Inverse Physics ────────────────────────────────────────────────────────

def test_inverse_physics9_default_prior():
    measurements = {
        "density_ratio": 1.05,
        "vp_ratio": 0.95,
        "vs_ratio": 0.90,
        "resistivity_ratio": 1.20,
        "pressure_pa": 25e6,
        "temperature_k": 340.0,
        "porosity": 0.18,
    }
    result = inverse_physics9(measurements)
    assert "inferred_state" in result
    inferred = result["inferred_state"]
    # Check default prior is used and updated
    assert inferred["rho"] == pytest.approx(2350 * 1.05)
    assert inferred["vp"] == pytest.approx(2950 * 0.95)
    assert inferred["vs"] == pytest.approx(1680 * 0.90)
    assert inferred["rho_e"] == pytest.approx(20 * 1.20)
    assert inferred["P"] == 25e6
    assert inferred["T"] == 340.0
    assert inferred["phi"] == 0.18


def test_inverse_physics9_custom_prior(base_state):
    measurements = {
        "density_ratio": 1.10,
        "vp_ratio": 1.05,
    }
    result = inverse_physics9(measurements, prior_state=base_state)
    inferred = result["inferred_state"]
    assert inferred["rho"] == pytest.approx(base_state.rho * 1.10)
    assert inferred["vp"] == pytest.approx(base_state.vp * 1.05)
    # Keep others
    assert inferred["vs"] == pytest.approx(base_state.vs)
    assert inferred["phi"] == pytest.approx(base_state.phi)


# ─── Metabolic Loop ──────────────────────────────────────────────────────────

def test_metabolic_loop_immediate_convergence(base_state):
    # Predict values from base state first
    pred = forward_physics9(base_state)
    measurements = {
        "ai_kg_ms2": pred["ai_kg_ms2"],
        "thermal_diff": pred["thermal_diff"],
        "pressure_pa": base_state.P,
        "temperature_k": base_state.T,
    }
    result = metabolic_loop(base_state, measurements)
    assert result["converged"] is True
    assert result["loop_cycles"] == 1
    assert result["converged_state"].rho == base_state.rho


def test_metabolic_loop_slow_convergence(base_state):
    # Set measurements to something slightly different to trigger loop cycles
    pred = forward_physics9(base_state)
    measurements = {
        "ai_kg_ms2": pred["ai_kg_ms2"] - 100000.0,
        "thermal_diff": pred["thermal_diff"] * 0.95,
        "pressure_pa": base_state.P,
        "temperature_k": base_state.T,
    }
    result = metabolic_loop(base_state, measurements, max_iterations=20)
    # Verify metadata and loop output structure
    assert "converged" in result
    assert "loop_cycles" in result
    assert "final_lithology" in result
    assert result["metadata"]["loop_type"] == "forward_inverse_metabolic"
