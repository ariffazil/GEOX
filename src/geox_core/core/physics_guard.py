"""
geox_core.core.physics_guard — BACKWARD COMPATIBILITY SHIM

All canonical PhysicsGuard logic has migrated to geox_core.physics.guards.
This module re-exports the same symbols for code that has not yet updated imports.

DO NOT ADD NEW CODE HERE. Use geox_core.physics.guards instead.
"""

from geox_core.physics.guards import (
    PhysicsGuard,
    PhysicsViolation,
    ValidationResult,
)

__all__ = [
    "PhysicsGuard",
    "PhysicsViolation",
    "ValidationResult",
]
