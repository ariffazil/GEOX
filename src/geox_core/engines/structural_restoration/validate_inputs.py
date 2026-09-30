"""validate_inputs — Fail-fast gate for restoration computations.

SR_INV_001: Never overwrite source geometry.
SR_INV_003: Surface subtraction requires matching CRS/units/datum/polarity.
SR_INV_004: Restoration ages and stratigraphing ordering must be explicit.

Blocks all downstream computation if geometry is not admissible.
Returns SEAL, PARTIAL, HOLD, or VOID with detected mismatches.

Forged: 2026-09-14
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from .state import CRSProof, RestorationScenario, SurfaceIdentity, ZConvention


class ValidationVerdict(StrEnum):
    """Validation verdict — maps to arifOS verdict vocabulary."""

    SEAL = "SEAL"  # All checks pass
    PARTIAL = "PARTIAL"  # Some checks pass, some missing
    HOLD = "HOLD"  # Mismatch detected, cannot proceed
    VOID = "VOID"  # Hard violation, computation forbidden


class ValidationResult(BaseModel):
    """Result of restoration input validation."""

    verdict: ValidationVerdict = Field(..., description="Overall validation verdict")
    checks_passed: list[str] = Field(
        default_factory=list, description="Checks that passed"
    )
    checks_failed: list[str] = Field(
        default_factory=list, description="Checks that failed"
    )
    checks_missing: list[str] = Field(
        default_factory=list, description="Checks that could not be run (missing data)"
    )
    mismatches: list[str] = Field(
        default_factory=list, description="Detected mismatches"
    )
    missing_metadata: list[str] = Field(
        default_factory=list, description="Required metadata that is missing"
    )
    permitted_calculations: list[str] = Field(
        default_factory=list,
        description="Calculations permitted given this validation result",
    )
    blocked_calculations: list[str] = Field(
        default_factory=list,
        description="Calculations blocked due to validation failures",
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed validation results"
    )


def validate_restoration_inputs(
    scenario: RestorationScenario,
) -> ValidationResult:
    """Validate restoration inputs before computation.

    SR_INV_001: Source geometry must be immutable.
    SR_INV_003: CRS/units/datum/polarity must match.
    SR_INV_004: Ages and stratigraphic ordering must be explicit.

    Returns ValidationResult with verdict and details.
    """
    checks_passed: list[str] = []
    checks_failed: list[str] = []
    checks_missing: list[str] = []
    mismatches: list[str] = []
    missing_metadata: list[str] = []
    details: dict[str, Any] = {}

    # ─── SR_INV_001: Immutability ────────────────────────────────────────
    if scenario.source_state.is_source_geometry:
        checks_passed.append("SR_INV_001: source_geometry_is_immutable")
    else:
        checks_failed.append("SR_INV_001: source_geometry_not_marked_immutable")
        mismatches.append(
            f"Source surface '{scenario.source_state.surface_id}' "
            f"is not marked as immutable source geometry"
        )

    if scenario.immutable:
        checks_passed.append("SR_INV_001: scenario_marked_immutable")
    else:
        checks_failed.append("SR_INV_001: scenario_not_immutable")
        mismatches.append("Scenario immutable flag is False — this is forbidden")

    # ─── SR_INV_003: CRS Compatibility ───────────────────────────────────
    source_crs = scenario.source_state.crs
    target_crs = scenario.target_state.crs

    crs_mismatches = source_crs.is_compatible_with(target_crs)
    if crs_mismatches:
        for m in crs_mismatches:
            checks_failed.append(f"SR_INV_003: {m}")
            mismatches.append(m)
    else:
        checks_passed.append("SR_INV_003: crs_compatible")

    # Check for missing CRS metadata
    _check_crs_completeness(source_crs, "source", missing_metadata, checks_missing)
    _check_crs_completeness(target_crs, "target", missing_metadata, checks_missing)

    # ─── SR_INV_004: Explicit Ages ───────────────────────────────────────
    if scenario.source_age_ma is not None and scenario.target_age_ma is not None:
        checks_passed.append("SR_INV_004: ages_explicit")
        details["source_age_ma"] = scenario.source_age_ma
        details["target_age_ma"] = scenario.target_age_ma

        # Age ordering check
        if scenario.source_age_ma > scenario.target_age_ma:
            details["age_order"] = "source_older_than_target"
        elif scenario.source_age_ma < scenario.target_age_ma:
            details["age_order"] = "source_younger_than_target"
        else:
            checks_failed.append("SR_INV_004: ages_equal")
            mismatches.append(
                "Source and target ages are equal — no temporal difference to restore"
            )
    else:
        if scenario.source_age_ma is None:
            checks_missing.append("SR_INV_004: source_age_missing")
            missing_metadata.append("source_age_ma")
        if scenario.target_age_ma is None:
            checks_missing.append("SR_INV_004: target_age_missing")
            missing_metadata.append("target_age_ma")

    # ─── SR_INV_004: Stratigraphic Ordering ──────────────────────────────
    if scenario.stratigraphic_order:
        checks_passed.append("SR_INV_004: stratigraphic_order_explicit")
        details["stratigraphic_order"] = scenario.stratigraphic_order
    else:
        checks_missing.append("SR_INV_004: stratigraphic_order_missing")
        missing_metadata.append("stratigraphic_order")

    # ─── Surface Identity Checks ─────────────────────────────────────────
    _validate_surface(scenario.source_state, "source", checks_passed,
                      checks_failed, missing_metadata)
    _validate_surface(scenario.target_state, "target", checks_passed,
                      checks_failed, missing_metadata)

    # ─── Z Convention Check ──────────────────────────────────────────────
    if source_crs.z_convention and target_crs.z_convention:
        if source_crs.z_convention == target_crs.z_convention:
            checks_passed.append("SR_INV_003: z_convention_match")
            details["z_convention"] = source_crs.z_convention.value
        else:
            checks_failed.append("SR_INV_003: z_convention_mismatch")
            mismatches.append(
                f"Z convention mismatch: source={source_crs.z_convention.value}, "
                f"target={target_crs.z_convention.value}"
            )
            details["z_convention_mismatch"] = {
                "source": source_crs.z_convention.value,
                "target": target_crs.z_convention.value,
            }

    # ─── Compaction Scenario (SR_INV_009/010/012) ────────────────────────
    if scenario.compaction_scenario:
        cs = scenario.compaction_scenario
        if cs.evidence_class:
            checks_passed.append("SR_INV_010: compaction_evidence_class_declared")
            details["compaction_evidence_class"] = cs.evidence_class.value
        else:
            checks_missing.append("SR_INV_010: compaction_evidence_class_missing")
            missing_metadata.append("compaction_scenario.evidence_class")

        if cs.uniform_lithology:
            checks_passed.append("SR_INV_012: uniform_lithology_declared")
            details["uniform_lithology"] = True
            details["dominant_lithology"] = cs.dominant_lithology

        if cs.measured_depth_limit_m and cs.extrapolation_end_depth_m:
            if cs.extrapolation_end_depth_m > cs.measured_depth_limit_m:
                details["extrapolation_interval_m"] = (
                    cs.extrapolation_end_depth_m - cs.measured_depth_limit_m
                )
                checks_passed.append(
                    "SR_INV_009: extrapolation_interval_declared"
                )
    else:
        checks_missing.append("compaction_scenario_missing")
        missing_metadata.append("compaction_scenario")

    # ─── Resolve Verdict ─────────────────────────────────────────────────
    if any("VOID" in c for c in checks_failed):
        verdict = ValidationVerdict.VOID
    elif checks_failed:
        verdict = ValidationVerdict.HOLD
    elif checks_missing and not checks_passed:
        verdict = ValidationVerdict.VOID
    elif checks_missing:
        verdict = ValidationVerdict.PARTIAL
    else:
        verdict = ValidationVerdict.SEAL

    # ─── Permitted / Blocked Calculations ────────────────────────────────
    permitted: list[str] = []
    blocked: list[str] = []

    if verdict in (ValidationVerdict.SEAL, ValidationVerdict.PARTIAL):
        permitted.extend(
            [
                "compute_accommodation_space",
                "compute_basement_subsidence",
                "compute_fill_ratio",
                "propagate_compaction_uncertainty",
                "build_distance_weighted_uncertainty",
            ]
        )
        if scenario.faults:
            permitted.append("analyse_fault_inheritance")
        else:
            blocked.append(
                "analyse_fault_inheritance (no faults provided)"
            )
    else:
        blocked.extend(
            [
                "compute_accommodation_space",
                "compute_basement_subsidence",
                "compute_fill_ratio",
                "propagate_compaction_uncertainty",
                "build_distance_weighted_uncertainty",
                "analyse_fault_inheritance",
            ]
        )

    return ValidationResult(
        verdict=verdict,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        checks_missing=checks_missing,
        mismatches=mismatches,
        missing_metadata=missing_metadata,
        permitted_calculations=permitted,
        blocked_calculations=blocked,
        details=details,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _check_crs_completeness(
    crs: CRSProof,
    label: str,
    missing: list[str],
    checks_missing: list[str],
) -> None:
    """Check CRS proof has minimum required fields."""
    if not crs.crs_epsg and not crs.crs_name:
        missing.append(f"{label}_crs")
        checks_missing.append(f"SR_INV_003: {label}_crs_missing")
    if not crs.z_units:
        missing.append(f"{label}_z_units")
        checks_missing.append(f"SR_INV_003: {label}_z_units_missing")
    if not crs.vertical_datum:
        missing.append(f"{label}_vertical_datum")
        checks_missing.append(f"SR_INV_003: {label}_vertical_datum_missing")


def _validate_surface(
    surface: SurfaceIdentity,
    label: str,
    checks_passed: list[str],
    checks_failed: list[str],
    missing: list[str],
) -> None:
    """Validate a surface identity has minimum required metadata."""
    if surface.surface_id:
        checks_passed.append(f"surface_{label}: id_present")
    else:
        checks_failed.append(f"surface_{label}: id_missing")
        missing.append(f"{label}_surface_id")

    if surface.name:
        checks_passed.append(f"surface_{label}: name_present")
    else:
        missing.append(f"{label}_surface_name")

    if surface.hash:
        checks_passed.append(f"surface_{label}: hash_present")
    else:
        missing.append(f"{label}_surface_hash")


__all__ = [
    "ValidationVerdict",
    "ValidationResult",
    "validate_restoration_inputs",
]
