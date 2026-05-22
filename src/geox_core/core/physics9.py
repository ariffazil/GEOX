"""
geox_core.core.physics9 — BACKWARD COMPATIBILITY SHIM

All canonical Physics-9 logic has migrated to geox_core.physics.
This module re-exports the same symbols for code that has not yet updated imports.

DO NOT ADD NEW CODE HERE. Use geox_core.physics instead.
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
)
from geox_core.physics.drivers import (
    build_lithology_model,
    anomaly_contrast_theory,
    inverse_physics9,
    metabolic_loop,
)

__all__ = [
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
    "forward_physics9",
    "bulk_modulus",
    "shear_modulus",
    "young_modulus",
    "poisson_ratio",
    "acoustic_impedance",
    "vp_vs_ratio",
    "thermal_diffusivity",
    "fatigue_proxy",
    "build_lithology_model",
    "anomaly_contrast_theory",
    "inverse_physics9",
    "metabolic_loop",
]
