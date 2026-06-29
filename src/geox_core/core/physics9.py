"""
geox_core.core.physics9 — BACKWARD COMPATIBILITY SHIM

All canonical Physics-9 logic has migrated to geox_core.physics.
This module re-exports the same symbols for code that has not yet updated imports.

DO NOT ADD NEW CODE HERE. Use geox_core.physics instead.
"""

from geox_core.physics.drivers import (
    anomaly_contrast_theory,
    build_lithology_model,
    inverse_physics9,
    metabolic_loop,
)
from geox_core.physics.parameters import (
    acoustic_impedance,
    bulk_modulus,
    fatigue_proxy,
    forward_physics9,
    poisson_ratio,
    shear_modulus,
    thermal_diffusivity,
    vp_vs_ratio,
    young_modulus,
)
from geox_core.physics.state import (
    ANHYDRITE,
    BASEMENT,
    COAL,
    DOLOMITE,
    EARTH_MATERIAL_CATALOG,
    LIMESTONE,
    SALT,
    SANDSTONE,
    SHALE,
    Physics13State,
    compute_earth_material_catalog,
)

__all__ = [
    "Physics13State",
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
