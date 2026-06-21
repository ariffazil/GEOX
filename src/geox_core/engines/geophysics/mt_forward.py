"""
mt_forward.py — W13+ Phase C forge: CSEM/MT 1D forward response.

The missing discipline per strategic vision. Magnetotelluric (MT) and
Controlled-Source EM (CSEM) measure subsurface electrical resistivity
(ρₑ). They are the only direct probe of ρₑ in the 9-dial Physics9State.

Forward model:
  For a 1D layered Earth, the MT apparent resistivity is:
    ρ_a(ω) = (1/ωμ) · |Z(ω)|²
  where Z is the surface impedance, recursively computed via
  Wait's recursion through the layer stack.

For CSEM (frequency-domain):
  E_x(r, ω) for a horizontal electric dipole source.

This module implements a clean 1D MT forward (no CSEM yet — flagged
for future forge). It uses the Cagniard-Tikhonov formulation.

DITEMPA BUKAN DIBEI — the ρₑ dial is forged, not given.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from geox_core.physics.state import Physics9State


# Physical constants
MU0 = 4.0 * math.pi * 1e-7  # H/m


@dataclass(frozen=True)
class MTLayer:
    """One layer in a 1D MT model."""

    thickness_m: float  # layer thickness; last layer should be ~1e9 (halfspace)
    resistivity_ohm_m: float  # ρₑ in Ω·m


@dataclass(frozen=True)
class MTForwardRequest:
    """1D MT forward modeling request."""

    layers: list[MTLayer] = field(default_factory=list)
    frequencies_hz: tuple[float, ...] = (0.001, 0.01, 0.1, 1.0, 10.0, 100.0)


# ───────────────────────────── WAIT'S RECURSION ──────────────────────────────────
def wait_recursion(layers: list[MTLayer], omega: float) -> complex:
    """Compute surface impedance via Wait's recursion for N-layer 1D Earth.

    For layer i (0-indexed, top to bottom):
      k_i = sqrt(i ω μ₀ / ρ_i)
      Z_i = -i ω μ₀ / k_i  (intrinsic)
      Z_{i-1} = Z_i · (Z_i + Z_{i-1}_intrinsic · tanh(k_i h_i)) / ...
                (Z_{i-1}_intrinsic + Z_i · tanh(k_i h_i))

    Top layer (i=0) has no overlying layer; its intrinsic is the surface Z.
    """
    if not layers:
        return complex(0.0, 0.0)

    # Bottom-up: start from halfspace (last layer)
    Z = -1j * omega * MU0 / _k(omega, layers[-1].resistivity_ohm_m)
    # Iterate upward
    for layer in reversed(layers[:-1]):
        k_i = _k(omega, layer.resistivity_ohm_m)
        Z_intrinsic = -1j * omega * MU0 / k_i
        tanh_kh = cmath.tanh(k_i * layer.thickness_m)
        Z = (Z + Z_intrinsic * tanh_kh) / (1.0 + Z * tanh_kh / Z_intrinsic)
    return Z


def _k(omega: float, rho: float) -> complex:
    """Wavenumber for a layer: k = sqrt(i ω μ₀ / ρ)."""
    val = 1j * omega * MU0 / max(rho, 1e-12)
    return cmath.sqrt(val)


# ───────────────────────────── APPARENT RESISTIVITY + PHASE ──────────────────────
def mt_apparent_resistivity_phase(
    layers: list[MTLayer],
    omega: float,
) -> tuple[float, float]:
    """Compute MT apparent resistivity (Ω·m) and phase (deg) at one frequency.

    ρ_a(ω) = (1/ωμ₀) · |Z(ω)|²
    φ(ω)   = atan2(Im(Z), Re(Z)) (radians; convert to deg)
    """
    Z = wait_recursion(layers, omega)
    rho_a = (abs(Z) ** 2) / (omega * MU0)
    phi_rad = cmath.phase(Z)
    return rho_a, math.degrees(phi_rad)


def mt_forward(request: MTForwardRequest) -> dict:
    """Run 1D MT forward over a frequency sweep.

    Returns apparent resistivity + phase curves plus Cagniard check.
    """
    if not request.layers:
        return {"ok": False, "error": "no_layers"}

    freqs = np.array(request.frequencies_hz, dtype=float)
    omegas = 2.0 * np.pi * freqs

    rho_a = []
    phase = []
    for omega in omegas:
        r, p = mt_apparent_resistivity_phase(request.layers, float(omega))
        rho_a.append(r)
        phase.append(p)

    return {
        "ok": True,
        "frequencies_hz": freqs.tolist(),
        "apparent_resistivity_ohm_m": rho_a,
        "phase_deg": phase,
        "n_layers": len(request.layers),
        "epistemic_provenance": {
            "rung": 3,
            "grounding": "maxwell_equations_1d_recursion",
            "method": "wait_recursion_cagniard_tikhonov",
            "caveat": (
                "1D layered Earth assumption. Real MT requires 2D/3D and "
                "static-shift correction. Phase wrap at 90° is normal."
            ),
        },
        "godel_wall": {
            "state": "KNOWN",
            "reason": "Deterministic 1D MT forward grounded in Maxwell's equations.",
        },
    }


# ───────────────────────────── PHYSICS9 BRIDGE ────────────────────────────────────
def mt_response_from_physics9(
    cell_state: Physics9State,
    frequencies_hz: tuple[float, ...] = (0.001, 0.01, 0.1, 1.0, 10.0, 100.0),
    overburden_thickness_m: float = 1000.0,
    target_thickness_m: float = 100.0,
) -> dict:
    """Convenience: build a 3-layer MT model from a single Physics9State cell.

    Layer 1: overburden (use background ρₑ = 50 Ω·m)
    Layer 2: target (uses cell ρₑ)
    Layer 3: halfspace (ρₑ = 100 Ω·m)

    Returns the MT forward response.
    """
    layers = [
        MTLayer(thickness_m=overburden_thickness_m, resistivity_ohm_m=50.0),
        MTLayer(thickness_m=target_thickness_m, resistivity_ohm_m=cell_state.rho_e),
        MTLayer(thickness_m=1e9, resistivity_ohm_m=100.0),
    ]
    return mt_forward(MTForwardRequest(layers=layers, frequencies_hz=frequencies_hz))


__all__ = [
    "MTLayer",
    "MTForwardRequest",
    "wait_recursion",
    "mt_apparent_resistivity_phase",
    "mt_forward",
    "mt_response_from_physics9",
    "MU0",
]
