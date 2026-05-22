"""
geox_core.physics — Unified Physics-9 Core

Orthogonal layers:
  state      → canonical state vector + material catalog
  parameters → static equations (moduli, rock physics, anisotropy, attenuation, well-tie)
  drivers    → forward / inverse / contrast / metabolic loop
  guards     → upstream physics constraint checker

Rule: Nothing outside this module defines new physics parameters.
All engines read from and write back to this layer.
"""
from geox_core.physics.state import (
    Physics9State,
    EARTH_MATERIAL_CATALOG,
    SANDSTONE,
    LIMESTONE,
    DOLOMITE,
    SHALE,
    ANHYDRITE,
    SALT,
    COAL,
    BASEMENT,
    compute_earth_material_catalog,
)
from geox_core.physics.parameters import (
    forward_physics9,
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
)
from geox_core.physics.drivers import (
    build_lithology_model,
    anomaly_contrast_theory,
    inverse_physics9,
    metabolic_loop,
)
from geox_core.physics.guards import (
    PhysicsGuard,
    PhysicsViolation,
    ValidationResult,
)

__all__ = [
    # state
    "Physics9State",
    "EARTH_MATERIAL_CATALOG",
    "SANDSTONE",
    "LIMESTONE",
    "DOLOMITE",
    "SHALE",
    "ANHYDRITE",
    "SALT",
    "COAL",
    "BASEMENT",
    "compute_earth_material_catalog",
    # parameters
    "forward_physics9",
    "bulk_modulus",
    "shear_modulus",
    "young_modulus",
    "poisson_ratio",
    "acoustic_impedance",
    "vp_vs_ratio",
    "thermal_diffusivity",
    "fatigue_proxy",
    "gardner_density",
    "bellotti_velocity_from_density",
    "faust_velocity",
    "estimate_thomsen_parameters",
    "apply_anisotropic_velocity_correction",
    "spectral_decay",
    "time_variant_wavelet_params",
    "impedance_array",
    "reflectivity_array",
    "ricker_wavelet",
    "convolve_trace",
    # drivers
    "build_lithology_model",
    "anomaly_contrast_theory",
    "inverse_physics9",
    "metabolic_loop",
    # guards
    "PhysicsGuard",
    "PhysicsViolation",
    "ValidationResult",
]
