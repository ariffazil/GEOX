"""
Carbonate Intelligence Adapters — GEOX
DITEMPA BUKAN DIBERI
"""

from .physics import (
    run_six_domain_differentiator,
    run_tepat_calibration,
    check_vp_consistency,
    check_basement_discrimination,
    bridge_classification_to_physics,
    compute_archetype_vp,
    generate_all_profiles,
    SixDomainResult,
    PhysicsBridgeResult,
    ARCHETYPE_RECIPES,
    TEPAT_BENCHMARK,
)

__all__ = [
    "run_six_domain_differentiator",
    "run_tepat_calibration",
    "check_vp_consistency",
    "check_basement_discrimination",
    "bridge_classification_to_physics",
    "compute_archetype_vp",
    "generate_all_profiles",
    "SixDomainResult",
    "PhysicsBridgeResult",
    "ARCHETYPE_RECIPES",
    "TEPAT_BENCHMARK",
]
