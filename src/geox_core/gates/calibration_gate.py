"""
Calibration Gate for GEOX Geopressure Analysis
DITEMPA BUKAN DIBERI — Forged, not given

A decorator that enforces calibration requirements for geopressure predictions.
Ensures that predictions without proper calibration emit appropriate epistemic
labels and caveats, preventing false confidence in unvalidated results.
"""

import functools
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Literal


class CalibrationLevel(str, Enum):
    """Calibration level enumeration - ordered from highest to lowest."""

    CALIBRATED = "CALIBRATED"
    PARTIAL = "PARTIAL"
    UNCALIBRATED = "UNCALIBRATED"


# Calibration requirements by level
CALIBRATION_REQUIREMENTS = {
    CalibrationLevel.CALIBRATED: {
        "required": ["sonic_log", "rft_mdt", "lot_xlot"],
        "description": "Full calibration: sonic log + RFT/MDT + LOT/XLOT",
    },
    CalibrationLevel.PARTIAL: {
        "required": ["sonic_log"],
        "description": "Partial calibration: at least sonic log or offset wells",
    },
    CalibrationLevel.UNCALIBRATED: {
        "required": [],
        "description": "No calibration - purely predictive",
    },
}


@dataclass
class CalibrationManifest:
    """
    Calibration manifest for geopressure analysis.

    Attributes:
        sonic_log: Path or SHA256 of sonic log file
        rft_mdt: Path or SHA256 of RFT/MDT data
        lot_xlot: Path or SHA256 of LOT/XLOT data
        offset_wells: List of offset well identifiers
        basin_context_ref: Reference to basin context registry
        literature_grounded: Whether literature-grounded context is loaded
    """

    sonic_log: str | None = None
    rft_mdt: str | None = None
    lot_xlot: str | None = None
    offset_wells: list[str] = field(default_factory=list)
    basin_context_ref: str | None = None
    literature_grounded: bool = False


@dataclass
class GateResult:
    """
    Result of calibration gate check.

    Attributes:
        status: "PASS" or "888_HOLD"
        level: Detected calibration level
        required_level: Minimum required level
        missing_inputs: List of missing required inputs
        reason: Human-readable reason
    """

    status: Literal["PASS", "888_HOLD"]
    level: CalibrationLevel
    required_level: CalibrationLevel
    missing_inputs: list[str] = field(default_factory=list)
    reason: str = ""


def detect_calibration_level(manifest: CalibrationManifest | None) -> CalibrationLevel:
    """
    Detect calibration level from manifest.

    Args:
        manifest: Calibration manifest or None

    Returns:
        Detected calibration level
    """
    if manifest is None:
        return CalibrationLevel.UNCALIBRATED

    # Check CALIBRATED requirements
    if manifest.sonic_log and manifest.rft_mdt and manifest.lot_xlot:
        return CalibrationLevel.CALIBRATED

    # Check PARTIAL requirements (sonic_log OR offset_wells)
    if manifest.sonic_log or manifest.offset_wells:
        return CalibrationLevel.PARTIAL

    # Default to uncalibrated
    return CalibrationLevel.UNCALIBRATED


def check_calibration_gate(
    manifest: CalibrationManifest | None,
    required_level: CalibrationLevel = CalibrationLevel.UNCALIBRATED,
) -> GateResult:
    """
    Check if calibration meets requirements.

    Args:
        manifest: Calibration manifest
        required_level: Minimum required calibration level

    Returns:
        GateResult with status and details
    """
    detected_level = detect_calibration_level(manifest)

    # Define level hierarchy
    level_order = [
        CalibrationLevel.CALIBRATED,
        CalibrationLevel.PARTIAL,
        CalibrationLevel.UNCALIBRATED,
    ]

    required_index = level_order.index(required_level)
    detected_index = level_order.index(detected_level)

    # If detected level is higher or equal to required, pass
    if detected_index <= required_index:
        return GateResult(
            status="PASS",
            level=detected_level,
            required_level=required_level,
            reason=f"Calibration level {detected_level.value} meets requirement {required_level.value}",
        )

    # Missing inputs for the required level
    requirements = CALIBRATION_REQUIREMENTS[required_level]
    missing = []

    if required_level == CalibrationLevel.CALIBRATED:
        if not manifest or not manifest.sonic_log:
            missing.append("sonic_log")
        if not manifest or not manifest.rft_mdt:
            missing.append("rft_mdt")
        if not manifest or not manifest.lot_xlot:
            missing.append("lot_xlot")
    elif required_level == CalibrationLevel.PARTIAL:
        if not manifest or (not manifest.sonic_log and not manifest.offset_wells):
            missing.append("sonic_log or offset_wells")

    return GateResult(
        status="888_HOLD",
        level=detected_level,
        required_level=required_level,
        missing_inputs=missing,
        reason=f"Calibration level {detected_level.value} below required {required_level.value}. Missing: {', '.join(missing) if missing else 'none'}",
    )


def requires_calibration(min_level: CalibrationLevel = CalibrationLevel.UNCALIBRATED):
    """
    Decorator that enforces calibration requirements for geopressure functions.

    The wrapped function must accept a `calibration_manifest` kwarg.
    If calibration is missing or below minimum level, returns a dict with
    888_HOLD status instead of executing the function.

    Args:
        min_level: Minimum required calibration level (default: UNCALIBRATED)

    Returns:
        Decorated function

    Example:
        @requires_calibration(min_level=PARTIAL)
        def predict_eaton(depths, calibration_manifest=None, ...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract calibration_manifest from kwargs
            manifest = kwargs.get("calibration_manifest")

            # Check calibration gate
            result = check_calibration_gate(manifest, min_level)

            if result.status == "888_HOLD":
                return {
                    "status": "888_HOLD",
                    "reason": "calibration_required",
                    "required_level": min_level.value,
                    "current_level": result.level.value,
                    "missing_inputs": result.missing_inputs,
                    "message": result.reason,
                }

            # Add calibration info to kwargs for the function
            kwargs["_calibration_level"] = result.level
            kwargs["_calibration_checked"] = True

            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_confidence_cap(calibration_level: CalibrationLevel) -> float:
    """
    Get confidence cap based on calibration level.

    Args:
        calibration_level: Detected calibration level

    Returns:
        Confidence cap value
    """
    caps = {
        CalibrationLevel.CALIBRATED: 0.85,
        CalibrationLevel.PARTIAL: 0.72,
        CalibrationLevel.UNCALIBRATED: 0.45,
    }
    return caps.get(calibration_level, 0.45)


def get_epistemic_label(calibration_level: CalibrationLevel) -> str:
    """
    Get epistemic label based on calibration level.

    Args:
        calibration_level: Detected calibration level

    Returns:
        Epistemic label string
    """
    labels = {
        CalibrationLevel.CALIBRATED: "CLAIM",
        CalibrationLevel.PARTIAL: "ESTIMATE",
        CalibrationLevel.UNCALIBRATED: "HYPOTHESIS",
    }
    return labels.get(calibration_level, "HYPOTHESIS")
