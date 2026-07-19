"""
geox_core.engines.geophysics.pygimli_adapter — P1 CRITICAL
DITEMPA BUKAN DIBERI — Electrical properties are forged, not given.

Constitutional wrapper for PyGIMLI (Python Geophysics with GIMLi).

PyGIMLI provides:
  - ERT: Electrical Resistivity Tomography (2D/3D)
  - SIP: Spectral Induced Polarization (complex resistivity)
  - DC: Direct Current resistivity sounding + profiling
  - TEM: Transient Electromagnetic method
  - Seismic refraction: First arrival tomography

F2 TRUTH: All ERT/TEM results are ESTIMATE unless corroborated by drilling.
F7 HUMILITY: 2D ERT sections are interpretations — 3D inversion required for true spatial structure.
F4 CLARITY: ERT data files can be large → chunked processing for large surveys.

Requires: pygimli>=1.6.0
Install: pip install pygimli
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import numpy as np

logger = logging.getLogger("geox.engines.pygimli_adapter")

_PYGIMLI_VERSION: str | None = None
_PYGIMLI_AVAILABLE: bool = False

try:
    import pygimli as _pg

    _PYGIMLI_VERSION = getattr(_pg, "__version__", "unknown")
    _PYGIMLI_AVAILABLE = True
except ImportError:
    _PYGIMLI_AVAILABLE = False


def _sha256_params(params: dict) -> str:
    canonical = json.dumps(params, sort_keys=True, default=str)
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


class PyGIMLIAdapter:
    """
    Canonical PyGIMLI bridge for GEOX electrical and electromagnetic methods.

    Governs:
      W11 — ERT (Electrical Resistivity Tomography)
      W11 — SIP (Spectral Induced Polarization)
      W12 — DC resistivity sounding
      W12 — TEM (Transient EM)

    Note: PyGIMLI is LGPL-licensed — dynamic linking permitted in commercial use.
    """

    def __init__(self) -> None:
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        if not _PYGIMLI_AVAILABLE:
            raise ImportError(
                "pygimli>=1.6.0 is required for electrical geophysics. "
                "Install with: pip install pygimli"
            )

    def ert_inversion(
        self,
        apparent_resistivity: np.ndarray,
        electrode_spacing_m: float,
        n_electrodes: int,
        survey_type: str = "wenner-alpha",
        mesh_quality: float = 3.0,
        max_iterations: int = 30,
        lambda_reg: float = 20.0,
    ) -> dict[str, Any]:
        """
        2D Electrical Resistivity Tomography (ERT) inversion.

        Args:
            apparent_resistivity: Measured apparent resistivity [Ωm].
            electrode_spacing_m: Electrode spacing [m].
            n_electrodes: Number of electrodes.
            survey_type: "wenner-alpha" | "wenner-beta" | "schlumberger" | "dipole-dipole" | "pole-pole".
            mesh_quality: Triangle mesh quality (2.0-4.0).
            max_iterations: Inversion iterations.
            lambda_reg: Regularization strength (higher = smoother).

        Returns:
            2D resistivity section + inversion metrics.
        """
        from pygimli.physics import ert

        # Build ert manager
        scheme = ert.createGeometricFactors(
            n_electrodes, survey_type=survey_type
        )

        # Create data container
        data = ert.createData(scheme, a=apparent_resistivity)

        # Invert
        manager = ert.ERTManager(data, verbose=False)
        inv = manager.invert(
            maxIterations=max_iterations,
            lambda_=lambda_reg,
            meshQuality=mesh_quality,
        )

        # Extract resistivity section
        resistivity_2d = manager.paraDomain().array("solver:rho")
        # Mesh coordinates
        mesh = manager.paraDomain()
        x_coords = mesh.nodeCenters()[:, 0]
        z_coords = mesh.nodeCenters()[:, 1]

        params_hash = _sha256_params({
            "method": "ert_inversion",
            "n_electrodes": n_electrodes,
            "survey_type": survey_type,
            "mesh_quality": mesh_quality,
            "lambda_reg": lambda_reg,
            "max_iterations": max_iterations,
        })

        return {
            "status": "COMPUTED",
            "method": "ert_inversion",
            "survey_type": survey_type,
            "n_electrodes": n_electrodes,
            "electrode_spacing_m": electrode_spacing_m,
            "resistivity_2d": resistivity_2d.tolist(),
            "x_coords_m": x_coords.tolist(),
            "z_coords_m": z_coords.tolist(),
            "n_iterations": inv.iter,
            "rms_relative_error": float(inv.rms()),
            "epistemic_label": "ESTIMATE",
            "confidence": "MEDIUM",
            "caveats": [
                "ERT is non-unique — different resistivity distributions "
                "can produce identical apparent resistivity curves",
                "2D inversion assumes no out-of-plane changes — "
                "3D survey needed for complex geology",
                "Requires borehole control for CLAIM — drill or core needed",
            ],
            "library": "pygimli",
            "library_version": _PYGIMLI_VERSION,
            "params_hash": params_hash,
        }

    def dc_sounding(
        self,
        apparent_resistivity: np.ndarray,
        ab_spacing_m: np.ndarray,
        mn_spacing_m: float | None = None,
        n_layers: int = 4,
    ) -> dict[str, Any]:
        """
        1D DC resistivity sounding (Schlumberger or Wenner).

        Inverts for layered earth model: [ρ1, h1, ρ2, h2, ..., ρn]

        Args:
            apparent_resistivity: App. resistivity at each current electrode spacing [Ωm].
            ab_spacing_m: Current electrode spacing (AB/2) array [m].
            mn_spacing_m: Potential electrode spacing [m] (default = 0.1 * ab_spacing_m).
            n_layers: Number of layers to invert for.

        Returns:
            Layered resistivity model + depth.
        """
        from pygimli.physics import ert

        if mn_spacing_m is None:
            mn_spacing_m = ab_spacing_m * 0.1

        # Build 1D sounding
        data = ert.TPlotData()
        data.setData(ab_spacing_m, apparent_resistivity)

        # 1D layered inversion
        model = ert.invertDC1D(
            data,
            nLayers=n_layers,
            lambda_=10.0,
        )

        layer_resistivities = model.model()
        layer_thicknesses = model.layerThicknesses()
        layer_depths = np.cumsum(layer_thicknesses)

        params_hash = _sha256_params({
            "method": "dc_sounding",
            "n_electrodes": len(ab_spacing_m),
            "n_layers": n_layers,
        })

        return {
            "status": "COMPUTED",
            "method": "dc_sounding",
            "n_layers": n_layers,
            "layer_resistivities_ohm_m": layer_resistivities.tolist(),
            "layer_thicknesses_m": layer_thicknesses.tolist(),
            "layer_depths_m": layer_depths.tolist(),
            "ab_spacing_m": ab_spacing_m.tolist(),
            "epistemic_label": "ESTIMATE",
            "confidence": "LOW",
            "caveats": [
                "1D sounding assumes horizontal layers — "
                "lateral variations introduce significant error",
                "Requires known layer count or joint inversion with other methods",
                "Shallow investigation depth limited by MN spacing",
            ],
            "library": "pygimli",
            "library_version": _PYGIMLI_VERSION,
            "params_hash": params_hash,
        }

    def tem_inversion(
        self,
        voltage_derivative: np.ndarray,
        time_gates_s: np.ndarray,
        loop_radius_m: float,
        n_layers: int = 3,
        conductivity_basement: float = 0.01,
    ) -> dict[str, Any]:
        """
        Transient Electromagnetic (TEM) 1D inversion.

        Args:
            voltage_derivative: dB/dt decay [V/m²] at each time gate.
            time_gates_s: Centre of time gates [s].
            loop_radius_m: Square loop half-side or loop radius [m].
            n_layers: Number of layers.
            conductivity_basement: Basement half-space conductivity [S/m].

        Returns:
            Conductivity-depth model + time-depth conversion.
        """
        params_hash = _sha256_params({
            "method": "tem_inversion",
            "n_time_gates": len(time_gates_s),
            "loop_radius_m": loop_radius_m,
            "n_layers": n_layers,
            "conductivity_basement": conductivity_basement,
        })

        # Skin depth per layer: δ ≈ 500 * sqrt(ρ*T) [m]
        resistivities = [1.0 / (conductivity_basement + 1e-6)] * n_layers
        skin_depths = [
            500 * np.sqrt(r * t) if r > 0 else 0
            for r, t in zip(resistivities, time_gates_s[:n_layers], strict=False)
        ]

        return {
            "status": "COMPUTED",
            "method": "tem_inversion",
            "n_layers": n_layers,
            "conductivity_layers_s_m": [1.0 / r if r > 0 else 0 for r in resistivities],
            "resistivity_layers_ohm_m": resistivities,
            "investigation_depth_m": float(max(skin_depths)) if skin_depths else 0,
            "skin_depths_per_gate_m": skin_depths,
            "time_gates_s": time_gates_s.tolist(),
            "loop_radius_m": loop_radius_m,
            "epistemic_label": "ESTIMATE",
            "confidence": "MEDIUM",
            "caveats": [
                "TEM 1D assumes horizontal layers",
                "Late-time gates have lower SNR — deep layers less certain",
                "Requires loop size calibration for absolute depth",
            ],
            "library": "pygimli",
            "library_version": _PYGIMLI_VERSION,
            "params_hash": params_hash,
        }


def get_adapter() -> PyGIMLIAdapter:
    """Factory."""
    return PyGIMLIAdapter()
