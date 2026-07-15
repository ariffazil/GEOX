"""
Tests for geox_core.physics.parameters — Pure Physics Equations
Covers all functions: elastic moduli, rock physics, anisotropy,
attenuation, well-tie primitives, and forward_physics9.

These are pure functions — no mocking required.
DITEMPA BUKAN DIBERI
"""

import math
import pytest
import numpy as np

from geox_core.physics.parameters import (
    bulk_modulus,
    shear_modulus,
    young_modulus,
    poisson_ratio,
    acoustic_impedance,
    vp_vs_ratio,
    thermal_diffusivity,
    fatigue_proxy,
    gardner_density,
    bellotti_velocity_from_density,
    faust_velocity,
    estimate_thomsen_parameters,
    apply_anisotropic_velocity_correction,
    spectral_decay,
    time_variant_wavelet_params,
    impedance_array,
    reflectivity_array,
    ricker_wavelet,
    convolve_trace,
    forward_physics9,
)
from geox_core.physics.state import Physics13State


# ── Canonical test state ──────────────────────────────────────────────────


@pytest.fixture
def sandstone_state():
    """Typical shallow marine sandstone parameters."""
    return Physics13State(
        rho=2200.0,  # kg/m³
        vp=2800.0,  # m/s
        vs=1500.0,  # m/s
        rho_e=10.0,  # Ω·m
        chi=1e-4,  # SI
        k=2.5,  # W/m·K
        P=20e6,  # 20 MPa pore pressure
        T=320.0,  # K
        phi=0.22,  # 22% porosity
    )


# ── Elastic Moduli ────────────────────────────────────────────────────────


def test_bulk_modulus_positive(sandstone_state):
    """K = ρ(Vp² − 4/3 Vs²) should be positive for real rock."""
    K = bulk_modulus(sandstone_state.vp, sandstone_state.vs, sandstone_state.rho)
    assert K > 0


def test_shear_modulus_positive(sandstone_state):
    G = shear_modulus(sandstone_state.vs, sandstone_state.rho)
    expected = sandstone_state.rho * sandstone_state.vs**2
    assert G == pytest.approx(expected)
    assert G > 0


def test_young_modulus_isotropic_identity():
    """E = 9KG/(3K+G) — three-way cross-check against isotropic elastic identity.

    Four convicted regression vectors from sovereign probe (2026-07-10).
    Each: E must match both E=2G(1+ν) and E=3K(1-2ν) to machine epsilon.
    """
    vectors = [
        # (rho, Vp, Vs, E_correct_GPa)
        (2400, 3000, 1500, 14.4000),  # sovereign's primary kill vector
        (2500, 4500, 2000, 27.5385),  # higher velocity band
        (2200, 2000, 1400, 8.7931),  # lower density band
        (2400, 3000, 1000, 6.9000),  # high Vp/Vs (shale regime)
    ]
    for rho, vp, vs, expected_e_gpa in vectors:
        K = bulk_modulus(vp, vs, rho)
        G = shear_modulus(vs, rho)
        E = young_modulus(K, G)
        nu = poisson_ratio(K, G)

        # Three-way cross-check
        E_from_G_nu = 2.0 * G * (1.0 + nu)
        E_from_K_nu = 3.0 * K * (1.0 - 2.0 * nu)

        assert E == pytest.approx(E_from_G_nu, rel=1e-12), f"ρ={rho} Vp={vp} Vs={vs}: E={E} ≠ 2G(1+ν)={E_from_G_nu}"
        assert E == pytest.approx(E_from_K_nu, rel=1e-12), f"ρ={rho} Vp={vp} Vs={vs}: E={E} ≠ 3K(1-2ν)={E_from_K_nu}"
        assert E == pytest.approx(expected_e_gpa * 1e9, rel=1e-4), (
            f"ρ={rho} Vp={vp} Vs={vs}: expected {expected_e_gpa} GPa, got {E / 1e9:.4f} GPa"
        )


def test_poisson_ratio_physical_range():
    """ν must be in (-1, 0.5) for real materials."""
    K, G = 10e9, 5e9
    nu = poisson_ratio(K, G)
    assert -1.0 < nu < 0.5


def test_acoustic_impedance():
    Z = acoustic_impedance(2800.0, 2200.0)
    assert Z == pytest.approx(2800.0 * 2200.0)


def test_vp_vs_ratio_normal():
    ratio = vp_vs_ratio(2800.0, 1500.0)
    assert ratio == pytest.approx(2800.0 / 1500.0)


def test_vp_vs_ratio_zero_vs():
    """Division by zero guard — min vs clamped to 0.001."""
    ratio = vp_vs_ratio(2000.0, 0.0)
    assert ratio == pytest.approx(2000.0 / 0.001)


def test_thermal_diffusivity():
    """κ = k/(ρ·Cp)"""
    kappa = thermal_diffusivity(2.5, 2200.0, 850.0)
    assert kappa == pytest.approx(2.5 / (2200.0 * 850.0))


def test_thermal_diffusivity_default_cp():
    kappa = thermal_diffusivity(2.5, 2200.0)
    assert kappa == pytest.approx(2.5 / (2200.0 * 850.0))


def test_fatigue_proxy():
    """Empirical: φ · (ΔP/1MPa) · ln(cycles)."""
    result = fatigue_proxy(0.2, 10e6, cycles=1000)
    expected = 0.2 * (10e6 / 1e6) * math.log(1000)
    assert result == pytest.approx(expected)


def test_fatigue_proxy_min_cycles():
    """cycles=0 should not raise — clamped to 1."""
    result = fatigue_proxy(0.2, 5e6, cycles=0)
    assert result == pytest.approx(0.2 * 5.0 * math.log(1))  # log(1)=0
    assert result == 0.0


# ── Rock Physics ──────────────────────────────────────────────────────────


def test_gardner_density():
    """ρ = α·Vp^β — default α=310, β=0.25."""
    vp = np.array([2000.0, 3000.0, 4000.0])
    rho = gardner_density(vp)
    expected = 310.0 * (vp**0.25)
    np.testing.assert_allclose(rho, expected)


def test_gardner_density_custom_params():
    vp = np.array([3000.0])
    rho = gardner_density(vp, alpha=320.0, beta=0.26)
    expected = 320.0 * (3000.0**0.26)
    np.testing.assert_allclose(rho, expected)


def test_bellotti_velocity_from_density():
    """Vp ≈ (ρ/310)^4 — inverse Gardner."""
    rho = np.array([2000.0, 2200.0])
    vp = bellotti_velocity_from_density(rho)
    expected = (rho / 310.0) ** 4
    np.testing.assert_allclose(vp, expected)


def test_faust_velocity():
    """Vp = k·(Z·Rt)^(1/6)."""
    depth = np.array([1000.0, 2000.0, 3000.0])
    resistivity = np.array([5.0, 10.0, 15.0])
    vp = faust_velocity(depth, resistivity)
    expected = 2.288 * (depth * resistivity) ** (1.0 / 6.0)
    np.testing.assert_allclose(vp, expected)


# ── Anisotropy (Thomsen) ──────────────────────────────────────────────────


def test_thomsen_parameters():
    vp = np.array([3000.0, 4000.0])
    vsh = np.array([0.3, 0.5])
    result = estimate_thomsen_parameters(vp, vsh)
    np.testing.assert_allclose(result["epsilon"], 0.2 * vsh)
    np.testing.assert_allclose(result["delta"], 0.1 * vsh)
    np.testing.assert_allclose(result["gamma"], 0.15 * vsh)


def test_anisotropic_correction_zero_angle():
    """At θ=0°, correction should return vp_vertical unchanged."""
    vp = np.array([3000.0])
    eps = np.array([0.1])
    delta = np.array([0.05])
    corrected = apply_anisotropic_velocity_correction(vp, 0.0, eps, delta)
    np.testing.assert_allclose(corrected, vp)


def test_anisotropic_correction_45_degrees():
    """At 45°, sin²=cos²=0.5, so correction is well-defined."""
    vp = np.array([3000.0])
    eps = np.array([0.1])
    delta = np.array([0.05])
    corrected = apply_anisotropic_velocity_correction(vp, 45.0, eps, delta)
    theta_rad = np.deg2rad(45.0)
    sin2 = np.sin(theta_rad) ** 2
    cos2 = np.cos(theta_rad) ** 2
    sin4 = np.sin(theta_rad) ** 4
    expected = vp * (1.0 + delta * sin2 * cos2 + eps * sin4)
    np.testing.assert_allclose(corrected, expected)


# ── Attenuation ───────────────────────────────────────────────────────────


def test_spectral_decay_normal():
    """f_decayed = f_initial / (1 + π·f·t/Q)."""
    f_in = 40.0
    t = 1.0  # 1 second TWT
    Q = 50.0
    result = spectral_decay(f_in, t, Q)
    expected = f_in / (1.0 + (np.pi * f_in * t) / Q)
    assert result == pytest.approx(max(5.0, expected))


def test_spectral_decay_floor():
    """Result clamped to minimum 5 Hz."""
    result = spectral_decay(40.0, 100.0, 1.0)  # Very long TWT → huge decay
    assert result >= 5.0


def test_spectral_decay_zero_q():
    """Q=0 guard — returns f_initial."""
    result = spectral_decay(40.0, 1.0, 0.0)
    assert result == pytest.approx(40.0)


def test_time_variant_wavelet_params():
    t_vec = np.array([0.0, 0.5, 1.0, 2.0])
    result = time_variant_wavelet_params(40.0, t_vec, 50.0)
    assert result.shape == (4,)
    assert all(r >= 5.0 for r in result)
    # Should be monotonically decreasing (more attenuation at deeper TWT)
    assert result[0] >= result[-1]


# ── Well-Tie Primitives ───────────────────────────────────────────────────


def test_impedance_array():
    rho = np.array([2000.0, 2200.0, 2400.0])
    vp = np.array([2500.0, 2800.0, 3200.0])
    Z = impedance_array(rho, vp)
    np.testing.assert_allclose(Z, rho * vp)


def test_impedance_array_shape_mismatch():
    rho = np.array([2000.0, 2200.0])
    vp = np.array([2500.0, 2800.0, 3200.0])
    with pytest.raises(ValueError, match="HOLD"):
        impedance_array(rho, vp)


def test_reflectivity_array():
    Z = np.array([5e6, 6e6, 5.5e6, 7e6])
    R = reflectivity_array(Z)
    assert R.shape == Z.shape
    assert R[-1] == 0.0  # Last sample is always 0 (no z[n+1])
    # Check first coefficient manually
    expected_r0 = (6e6 - 5e6) / (6e6 + 5e6)
    assert R[0] == pytest.approx(expected_r0)


def test_ricker_wavelet_shape():
    w = ricker_wavelet(freq=30.0, dt=0.002)
    assert w.ndim == 1
    assert len(w) > 0
    # Peak should be near zero-time (centre)
    mid = len(w) // 2
    assert abs(w[mid]) > 0.5  # Peak amplitude near 1


def test_ricker_wavelet_zero_phase():
    """Ricker wavelet should be symmetric (zero-phase)."""
    w = ricker_wavelet(freq=30.0, dt=0.002, length=0.2)
    # Symmetric check
    assert np.allclose(w, w[::-1], atol=1e-10)


def test_convolve_trace():
    R = np.zeros(100)
    R[50] = 1.0  # Single spike
    w = ricker_wavelet(30.0, 0.002)
    trace = convolve_trace(R, w)
    assert trace.shape == R.shape
    # Peak should be near the spike location
    peak_idx = np.argmax(np.abs(trace))
    assert abs(peak_idx - 50) <= 5


# ── Forward Physics9 ──────────────────────────────────────────────────────


def test_forward_physics9_keys(sandstone_state):
    result = forward_physics9(sandstone_state)
    expected_keys = {
        "K_GPa",
        "G_GPa",
        "E_GPa",
        "nu",
        "ai_kg_ms2",
        "vp_vs_ratio",
        "thermal_diff",
        "fatigue_proxy",
        "acoustic_impedance",
    }
    assert set(result.keys()) == expected_keys


def test_forward_physics9_values_physical(sandstone_state):
    result = forward_physics9(sandstone_state)
    # Poisson's ratio must be in physical range
    assert -1.0 < result["nu"] < 0.5
    # Moduli must be positive
    assert result["K_GPa"] > 0
    assert result["G_GPa"] > 0
    assert result["E_GPa"] > 0
    # Acoustic impedance must be positive
    assert result["ai_kg_ms2"] > 0


def test_forward_physics9_consistency(sandstone_state):
    """acoustic_impedance and ai_kg_ms2 should match."""
    result = forward_physics9(sandstone_state)
    assert result["acoustic_impedance"] == result["ai_kg_ms2"]


# ── Physics13State ─────────────────────────────────────────────────────────


def test_physics9state_to_vector(sandstone_state):
    v = sandstone_state.to_vector()
    assert len(v) == 14
    assert v[0] == sandstone_state.rho
    assert v[1] == sandstone_state.vp
    assert v[2] == sandstone_state.vs
    assert v[8] == sandstone_state.phi


def test_physics9state_frozen():
    """State is immutable — modification raises AttributeError."""
    state = Physics13State(rho=2000.0, vp=2500.0, vs=1200.0, rho_e=5.0, chi=1e-5, k=2.0, P=10e6, T=300.0, phi=0.2)
    with pytest.raises((AttributeError, TypeError)):
        state.rho = 9999.0  # type: ignore


def test_physics9state_defaults():
    """Extension params default correctly."""
    state = Physics13State(rho=2000.0, vp=2500.0, vs=1200.0, rho_e=5.0, chi=1e-5, k=2.0, P=10e6, T=300.0, phi=0.2)
    assert state.epsilon == 0.0
    assert state.delta == 0.0
    assert state.gamma == 0.0
    assert state.qp == 100.0
    assert state.qs == 50.0


def test_physics9state_from_vector():
    v = [2350, 2950, 1680, 20, 0.0001, 2.8, 20e6, 320, 0.25, 0.0, 0.0, 0.0, 100.0, 50.0]
    state = Physics13State.from_vector(v)
    assert state.rho == 2350
    assert state.vp == 2950
    assert state.vs == 1680
    assert state.phi == 0.25

    # Short vector
    v_short = [2350, 2950, 1680, 20]
    state_short = Physics13State.from_vector(v_short)
    assert state_short.rho == 2350
    assert state_short.chi == 0.0
    assert state_short.phi == 0.20


def test_physics9state_grade():
    # Valid
    state_aaa = Physics13State(rho=2350, vp=2950, vs=1680, rho_e=20, chi=0, k=2, P=0, T=0, phi=0.25)
    assert state_aaa.grade() == "AAA"

    # Out of bounds porosity
    state_raw1 = Physics13State(rho=2350, vp=2950, vs=1680, rho_e=20, chi=0, k=2, P=0, T=0, phi=0.50)
    assert state_raw1.grade() == "RAW"

    # Out of bounds velocity
    state_raw2 = Physics13State(rho=2350, vp=7000, vs=1680, rho_e=20, chi=0, k=2, P=0, T=0, phi=0.25)
    assert state_raw2.grade() == "RAW"

    # Out of bounds density
    state_raw3 = Physics13State(rho=6000, vp=2950, vs=1680, rho_e=20, chi=0, k=2, P=0, T=0, phi=0.25)
    assert state_raw3.grade() == "RAW"


def test_compute_earth_material_catalog():
    from geox_core.physics.state import compute_earth_material_catalog

    catalog = compute_earth_material_catalog()
    assert "Sandstone" in catalog
    assert catalog["Sandstone"]["rho"] == 2350
