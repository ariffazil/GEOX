"""
geox_core.engines.em — CSEM/MT 1D Forward Modeling Engine
═══════════════════════════════════════════════════════════
Physics9 bridge: ρ_e → E,H (electromagnetic response)

Implements:
  - 1D layered-earth CSEM forward model (frequency domain)
  - 1D magnetotelluric (MT) impedance tensor computation
  - Recursive matrix method (Wait's algorithm /传播矩阵法)
  - Apparent resistivity and phase from MT impedance

Physics:
    Maxwell's equations (quasi-static, 1D layered earth):
        ∇×E = iωμH
        ∇×H = σE
    where σ = 1/ρ_e (conductivity from resistivity)

    MT impedance: Z(f) = E_x / H_y [Ω]
    Apparent resistivity: ρ_a = |Z|² / (ωμ₀)
    Phase: φ = arctan(Im(Z)/Re(Z))

Constitutional: F2 (evidence-labeled), F9 (physics-only).
Author: FORGE (000Ω) | DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

logger = logging.getLogger("geox.em")

# ─── Constants ───────────────────────────────────────────────────────────────

MU_0 = 4.0 * np.pi * 1e-7   # T·m/A — vacuum permeability
OMEGA_0 = 1.0 / MU_0         # convenience
EPSILON_0 = 8.854e-12         # F/m — vacuum permittivity (negligible at exploration freqs)


# ─── Data Classes ────────────────────────────────────────────────────────────


@dataclass
class LayerModel:
    """1D layered earth model."""
    thicknesses_m: np.ndarray   # layer thicknesses (last layer = half-space, thickness = inf)
    resistivities_ohmm: np.ndarray  # layer resistivities

    @property
    def n_layers(self) -> int:
        return len(self.resistivities_ohmm)

    @property
    def conductivities_sm(self) -> np.ndarray:
        return 1.0 / np.maximum(self.resistivities_ohmm, 1e-10)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_layers": self.n_layers,
            "thicknesses_m": self.thicknesses_m.tolist(),
            "resistivities_ohmm": self.resistivities_ohmm.tolist(),
        }


@dataclass
class CSEMResult:
    """Result of CSEM forward modeling."""
    frequencies_hz: np.ndarray
    ex_amplitude: np.ndarray       # |E_x| at receiver [V/m]
    ey_amplitude: np.ndarray       # |E_y| at receiver [V/m]
    hx_amplitude: np.ndarray       # |H_x| at receiver [A/m]
    hy_amplitude: np.ndarray       # |H_y| at receiver [A/m]
    offset_m: float                # source-receiver offset
    source_depth_m: float
    receiver_depth_m: float
    layer_model: LayerModel
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequencies_hz": self.frequencies_hz.tolist(),
            "ex_amplitude": self.ex_amplitude.tolist(),
            "hy_amplitude": self.hy_amplitude.tolist(),
            "offset_m": self.offset_m,
            "source_depth_m": self.source_depth_m,
            "receiver_depth_m": self.receiver_depth_m,
            "layer_model": self.layer_model.to_dict(),
            "metadata": self.metadata,
        }


@dataclass
class MTResult:
    """Result of MT forward modeling."""
    frequencies_hz: np.ndarray
    impedance_complex: np.ndarray  # Z(f) [Ω] — complex
    apparent_resistivity: np.ndarray  # ρ_a [Ω·m]
    phase_deg: np.ndarray          # phase [degrees]
    tipper: np.ndarray | None      # T(f) — vertical field transfer function
    layer_model: LayerModel
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequencies_hz": self.frequencies_hz.tolist(),
            "apparent_resistivity_ohmm": self.apparent_resistivity.tolist(),
            "phase_deg": self.phase_deg.tolist(),
            "impedance_real": np.real(self.impedance_complex).tolist(),
            "impedance_imag": np.imag(self.impedance_complex).tolist(),
            "layer_model": self.layer_model.to_dict(),
            "metadata": self.metadata,
        }


# ─── 1D MT Forward: Recursive Matrix Method ────────────────────────────────


def mt_forward_1d(
    layer_model: LayerModel,
    frequencies_hz: np.ndarray,
) -> MTResult:
    """
    1D Magnetotelluric forward model using the recursive impedance method.

    Computes the surface impedance Z(f) for a 1D layered earth:
        Z_n = ωμ₀ / k_n  (impedance at bottom of layer n)
        Z_i = Z_{i+1} · (Z_i^0 + Z_{i+1} · tanh(k_i d_i)) / (Z_{i+1} + Z_i^0 · tanh(k_i d_i))

    where:
        k_i = sqrt(iωμ₀σ_i)  — wave number in layer i
        Z_i^0 = ωμ₀ / k_i    — intrinsic impedance of layer i
        d_i = thickness of layer i

    Args:
        layer_model: 1D resistivity/thickness model
        frequencies_hz: frequencies to compute [Hz]

    Returns:
        MTResult with impedance, apparent resistivity, phase
    """
    n_freq = len(frequencies_hz)
    n_layers = layer_model.n_layers
    resistivities = layer_model.resistivities_ohmm
    thicknesses = layer_model.thicknesses_m

    impedance = np.zeros(n_freq, dtype=complex)
    apparent_resistivity = np.zeros(n_freq)
    phase = np.zeros(n_freq)

    for fi in range(n_freq):
        omega = 2.0 * np.pi * frequencies_hz[fi]

        # Start from the bottom layer (half-space)
        # Z_n = ωμ₀ / k_n where k_n = sqrt(iωμ₀σ_n)
        sigma_bottom = 1.0 / max(resistivities[-1], 1e-10)
        k_bottom = np.sqrt(1j * omega * MU_0 * sigma_bottom)
        Z = omega * MU_0 / k_bottom

        # Recurse upward through layers
        for layer in range(n_layers - 2, -1, -1):
            sigma = 1.0 / max(resistivities[layer], 1e-10)
            k = np.sqrt(1j * omega * MU_0 * sigma)
            Z0 = omega * MU_0 / k  # intrinsic impedance
            d = thicknesses[layer]

            # Propagator: tanh(k·d)
            tanh_kd = np.tanh(k * d)

            # Impedance transformation
            numerator = Z0 + Z * tanh_kd
            denominator = Z + Z0 * tanh_kd
            if abs(denominator) < 1e-30:
                denominator = 1e-30
            Z = Z0 * numerator / denominator

        impedance[fi] = Z

        # Apparent resistivity: ρ_a = |Z|² / (ωμ₀)
        abs_Z = abs(Z)
        apparent_resistivity[fi] = abs_Z ** 2 / (omega * MU_0)

        # Phase: φ = arctan(Im(Z)/Re(Z))
        phase[fi] = np.degrees(np.arctan2(Z.imag, Z.real))

    return MTResult(
        frequencies_hz=frequencies_hz,
        impedance_complex=impedance,
        apparent_resistivity=apparent_resistivity,
        phase_deg=phase,
        tipper=None,  # 1D has no tipper (no horizontal conductivity gradients)
        layer_model=layer_model,
        metadata={
            "method": "recursive_impedance_1d",
            "n_layers": n_layers,
            "epistemic_rung": 3,
        },
    )


# ─── CSEM Forward: Horizontal Electric Dipole ──────────────────────────────


def csem_forward_1d(
    layer_model: LayerModel,
    frequencies_hz: np.ndarray,
    offset_m: float,
    source_depth_m: float,
    receiver_depth_m: float,
    source_moment_am: float = 1.0,
) -> CSEMResult:
    """
    1D CSEM forward model for a horizontal electric dipole source.

    Computes E_x and H_y at the receiver for a horizontal electric dipole
    at the seafloor (or in a borehole), using the Sommerfeld integral
    decomposition and the recursive impedance method.

    Simplified: uses the dominant TE mode for a horizontal electric dipole
    at long offsets (far-field approximation).

    Args:
        layer_model: 1D resistivity/thickness model
        frequencies_hz: frequencies [Hz]
        offset_m: horizontal source-receiver offset [m]
        source_depth_m: depth of source below surface [m]
        receiver_depth_m: depth of receiver below surface [m]
        source_moment_am: source dipole moment [A·m]

    Returns:
        CSEMResult with E and H field amplitudes
    """
    n_freq = len(frequencies_hz)
    n_layers = layer_model.n_layers
    resistivities = layer_model.resistivities_ohmm
    thicknesses = layer_model.thicknesses_m

    ex = np.zeros(n_freq)
    ey = np.zeros(n_freq)
    hx = np.zeros(n_freq)
    hy = np.zeros(n_freq)

    for fi in range(n_freq):
        omega = 2.0 * np.pi * frequencies_hz[fi]

        # Compute the TE mode impedance at the surface
        # (same recursive method as MT, but evaluated at source/receiver depths)
        sigma_bottom = 1.0 / max(resistivities[-1], 1e-10)
        k_bottom = np.sqrt(1j * omega * MU_0 * sigma_bottom)
        Z_surface = omega * MU_0 / k_bottom

        for layer in range(n_layers - 2, -1, -1):
            sigma = 1.0 / max(resistivities[layer], 1e-10)
            k = np.sqrt(1j * omega * MU_0 * sigma)
            Z0 = omega * MU_0 / k
            d = thicknesses[layer]

            tanh_kd = np.tanh(k * d)
            numerator = Z0 + Z_surface * tanh_kd
            denominator = Z_surface + Z0 * tanh_kd
            if abs(denominator) < 1e-30:
                denominator = 1e-30
            Z_surface = Z0 * numerator / denominator

        # Wavenumber in air (for the TE mode)
        np.sqrt(1j * omega * MU_0 * 1e-12)  # σ_air ≈ 0
        np.sqrt(omega * MU_0 * omega * EPSILON_0)  # free-space wavenumber

        # Skin depth in the first layer
        sigma_first = 1.0 / max(resistivities[0], 1e-10)
        skin_depth = math.sqrt(2.0 / (omega * MU_0 * sigma_first))

        # Far-field approximation for horizontal electric dipole
        # E_x ∝ (source_moment / r²) · exp(-r/δ) · cos(φ)
        # where r = sqrt(offset² + vertical_sep²), δ = skin depth
        r = math.sqrt(offset_m ** 2 + (source_depth_m - receiver_depth_m) ** 2)
        if r < 1.0:
            r = 1.0

        # Attenuation factor
        attenuation = math.exp(-r / max(skin_depth, 1.0))

        # Geometric spreading (1/r² for near-field, 1/r for far-field)
        lambda_ratio = r / max(skin_depth, 1.0)
        if lambda_ratio < 1.0:
            spreading = 1.0 / (r ** 2)  # near-field
        else:
            spreading = 1.0 / (r * skin_depth)  # far-field

        # E-field amplitude
        E_amplitude = source_moment_am * abs(Z_surface) * spreading * attenuation

        # For horizontal electric dipole: E_x dominant, E_y small
        ex[fi] = E_amplitude
        ey[fi] = E_amplitude * 0.1  # cross-line component (simplified)

        # H-field from impedance: H = E / Z
        if abs(Z_surface) > 1e-30:
            H_amplitude = E_amplitude / abs(Z_surface)
        else:
            H_amplitude = 0.0

        hx[fi] = H_amplitude * 0.1  # cross-line
        hy[fi] = H_amplitude  # in-line

    return CSEMResult(
        frequencies_hz=frequencies_hz,
        ex_amplitude=ex,
        ey_amplitude=ey,
        hx_amplitude=hx,
        hy_amplitude=hy,
        offset_m=offset_m,
        source_depth_m=source_depth_m,
        receiver_depth_m=receiver_depth_m,
        layer_model=layer_model,
        metadata={
            "method": "far_field_approximation_1d",
            "source_moment_am": source_moment_am,
            "skin_depth_first_layer_m": skin_depth,
            "epistemic_rung": 3,
            "note": "Simplified 1D CSEM. Full 3D requires integral equation or finite difference.",
        },
    )


# ─── Apparent Resistivity and Phase from CSEM ──────────────────────────────


def csem_apparent_resistivity(
    csem_result: CSEMResult,
) -> dict[str, np.ndarray]:
    """
    Compute apparent resistivity and phase from CSEM E/H ratio.

    ρ_a = |E_x / H_y|² / (ωμ₀)
    φ = arctan(Im(E/H) / Re(E/H))
    """
    omega = 2.0 * np.pi * csem_result.frequencies_hz
    Z_ratio = csem_result.ex_amplitude / np.maximum(csem_result.hy_amplitude, 1e-30)

    rho_a = Z_ratio ** 2 / (omega * MU_0)
    phase = np.degrees(np.arctan2(
        np.imag(csem_result.ex_amplitude + 1j * csem_result.hy_amplitude),
        np.real(csem_result.ex_amplitude + 1j * csem_result.hy_amplitude),
    ))

    return {
        "apparent_resistivity_ohmm": rho_a,
        "phase_deg": phase,
    }


# ─── Sensitivity Analysis ──────────────────────────────────────────────────


def mt_sensitivity_1d(
    layer_model: LayerModel,
    frequencies_hz: np.ndarray,
    parameter: Literal["resistivity", "thickness"] = "resistivity",
    perturbation_pct: float = 1.0,
) -> dict[str, Any]:
    """
    Sensitivity analysis for 1D MT: ∂Z/∂ρ_i or ∂Z/∂d_i at each layer.

    Uses finite difference approximation.
    """
    base_result = mt_forward_1d(layer_model, frequencies_hz)
    base_rho_a = base_result.apparent_resistivity

    n_layers = layer_model.n_layers
    sensitivity = np.zeros((len(frequencies_hz), n_layers))

    for layer_idx in range(n_layers):
        # Perturb
        if parameter == "resistivity":
            delta = layer_model.resistivities_ohmm[layer_idx] * perturbation_pct / 100.0
            perturbed_resistivities = layer_model.resistivities_ohmm.copy()
            perturbed_resistivities[layer_idx] += delta
            perturbed_model = LayerModel(
                thicknesses_m=layer_model.thicknesses_m.copy(),
                resistivities_ohmm=perturbed_resistivities,
            )
        else:
            if layer_idx == n_layers - 1:
                continue  # half-space has no thickness
            delta = layer_model.thicknesses_m[layer_idx] * perturbation_pct / 100.0
            perturbed_thicknesses = layer_model.thicknesses_m.copy()
            perturbed_thicknesses[layer_idx] += delta
            perturbed_model = LayerModel(
                thicknesses_m=perturbed_thicknesses,
                resistivities_ohmm=layer_model.resistivities_ohmm.copy(),
            )

        perturbed_result = mt_forward_1d(perturbed_model, frequencies_hz)
        perturbed_rho_a = perturbed_result.apparent_resistivity

        # Sensitivity: ∂(log ρ_a) / ∂(log param)
        for fi in range(len(frequencies_hz)):
            if base_rho_a[fi] > 0 and abs(delta) > 0:
                param_val = (
                    layer_model.resistivities_ohmm[layer_idx]
                    if parameter == "resistivity"
                    else layer_model.thicknesses_m[layer_idx]
                )
                sensitivity[fi, layer_idx] = (
                    (perturbed_rho_a[fi] - base_rho_a[fi])
                    / base_rho_a[fi]
                    / (delta / param_val)
                )

    return {
        "frequencies_hz": frequencies_hz.tolist(),
        "parameter": parameter,
        "sensitivity": sensitivity.tolist(),
        "layer_model": layer_model.to_dict(),
    }
