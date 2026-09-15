"""Display-derived proxy extraction from raster seismic images.

Extracts pixel-column amplitude proxies for visual and morphological
interpretation assistance. NEVER claims amplitude preservation.

BOUNDARY: This is DISPLAY_DERIVED_PROXY, not NATIVE_TRACE.
- Permitted: visual event tracking, morphology, discontinuity, overlay support
- Prohibited: AVO, amplitude preservation, phase certification, native well-tie

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
from typing import Any, Optional

import numpy as np


def _detect_seismic_panel(image_array: np.ndarray) -> tuple[int, int, int, int]:
    """Detect seismic panel bounding box from image array.

    Finds the bounding box of non-white pixels (gray < 235).
    Returns (x_min, y_min, x_max, y_max).
    """
    if image_array.ndim == 3:
        gray = np.mean(image_array[:, :, :3], axis=2)
    else:
        gray = image_array.astype(float)

    mask = gray < 235
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    if not rows.any() or not cols.any():
        return 0, 0, image_array.shape[1], image_array.shape[0]

    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    return int(x_min), int(y_min), int(x_max), int(y_max)


def _column_amplitude_proxy(image_array: np.ndarray, x_min: int, y_min: int, x_max: int, y_max: int) -> np.ndarray:
    """Extract amplitude proxy from pixel columns in the seismic panel.

    Uses luminance as proxy — NOT reflection amplitude.
    Returns array of shape (n_traces, n_samples) normalized to [-1, 1].
    """
    panel = image_array[y_min:y_max + 1, x_min:x_max + 1]
    if panel.ndim == 3:
        # Convert to grayscale using R-B channel (seismic convention)
        gray = panel[:, :, 0].astype(float) - panel[:, :, 2].astype(float)
    else:
        gray = panel.astype(float)

    # Normalize to [-1, 1]
    abs_max = np.abs(gray).max()
    if abs_max > 0:
        gray = gray / abs_max

    # Transpose: rows=samples, cols=traces → traces x samples
    return gray.T


async def geox_extract_display_proxy(
    *,
    image_path: Optional[str] = None,
    image_data: Optional[str] = None,
    calibration_witness_ref: Optional[dict[str, Any]] = None,
    panel_bounds: Optional[dict[str, int]] = None,
    extraction_method: str = "column_luminance_r_minus_b",
    session_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Extract a display-derived proxy from a raster seismic image.

    This function produces pixel-derived proxy arrays for visual and
    morphological interpretation assistance. The output is explicitly
    labeled DISPLAY_DERIVED_PROXY and cannot be used for:
    - amplitude preservation validation
    - AVO classification
    - phase certification
    - native seismic-to-well tie acceptance
    - quantitative prospect/fault-seal decisions

    Inputs:
        image_path: Path to seismic image file
        image_data: Base64-encoded image (alternative to path)
        calibration_witness_ref: Validated CalibrationWitness reference
        panel_bounds: Override panel detection {x_min, y_min, x_max, y_max}
        extraction_method: Algorithm identifier for provenance
        session_id, actor_id, trace_id: Transport metadata

    Returns:
        dict with proxy arrays, provenance, permitted/prohibited uses, and status
    """
    from PIL import Image

    # Require calibration witness
    if not calibration_witness_ref:
        return {
            "status": "HOLD",
            "reason": "CALIBRATION_REQUIRED",
            "detail": "Display-derived proxy extraction requires a valid CalibrationWitness",
            "tool_name": "geox_extract_display_proxy",
        }

    # Verify witness is not HOLD
    witness_status = str(calibration_witness_ref.get("status", "")).upper()
    if witness_status == "HOLD":
        return {
            "status": "HOLD",
            "reason": "WITNESS_HOLD",
            "detail": "CalibrationWitness status is HOLD — resolve blockers first",
            "tool_name": "geox_extract_display_proxy",
        }

    # Load image
    try:
        if image_path:
            img = Image.open(image_path)
        else:
            return {
                "status": "VOID",
                "reason": "NO_IMAGE",
                "detail": "Either image_path or image_data required",
                "tool_name": "geox_extract_display_proxy",
            }
    except Exception as e:
        return {
            "status": "VOID",
            "reason": f"IMAGE_LOAD_ERROR: {e}",
            "tool_name": "geox_extract_display_proxy",
        }

    # SHA256 provenance
    with open(image_path, "rb") as f:
        image_hash = hashlib.sha256(f.read()).hexdigest()

    image_array = np.array(img)

    # Detect or use provided panel bounds
    if panel_bounds:
        x_min = panel_bounds.get("x_min", 0)
        y_min = panel_bounds.get("y_min", 0)
        x_max = panel_bounds.get("x_max", image_array.shape[1] - 1)
        y_max = panel_bounds.get("y_max", image_array.shape[0] - 1)
    else:
        x_min, y_min, x_max, y_max = _detect_seismic_panel(image_array)

    # Extract proxy
    proxy = _column_amplitude_proxy(image_array, x_min, y_min, x_max, y_max)

    return {
        "tool_name": "geox_extract_display_proxy",
        "status": "OK",
        "representation": "DISPLAY_DERIVED_PROXY",
        "data_representation": "DISPLAY_DERIVED_PROXY",
        "amplitude_integrity": "DISPLAY_TRANSFORMED",
        "phase_integrity": "DISPLAY_TRANSFORMED",
        "epistemic_tag": "DER",
        "calibration_witness_ref": calibration_witness_ref.get("witness_id") or calibration_witness_ref.get("calibration_witness_id", "unknown"),
        "panel_bounds": {
            "x_min": x_min, "y_min": y_min,
            "x_max": x_max, "y_max": y_max,
            "width": x_max - x_min + 1,
            "height": y_max - y_min + 1,
        },
        "proxy_shape": {"n_traces": proxy.shape[0], "n_samples": proxy.shape[1]},
        "extraction_method": extraction_method,
        "image_provenance": {
            "path": image_path,
            "sha256": image_hash,
            "dimensions": list(image_array.shape),
        },
        "permitted_uses": [
            "visual_interpretation",
            "event_tracking",
            "structural_pick_assist",
            "candidate_discontinuity_indication",
            "candidate_horizon_fault_overlay",
            "proxy_labeled_exploratory_indicators",
        ],
        "prohibited_uses": [
            "quantitative_amplitude_analysis",
            "avo_classification",
            "phase_certification",
            "amplitude_preservation_validation",
            "native_trace_substitution",
            "native_well_tie_acceptance",
            "prospect_decision_evidence",
            "fault_seal_decision_evidence",
        ],
        "limitations": [
            "Pixel luminance is NOT reflection amplitude",
            "Display transforms (AGC, gain, clipping, compression) unknown",
            "Phase rotation unknown",
            "Polarity convention unknown",
            "Color mapping may be non-linear",
        ],
        "provenance": {
            "tool": "geox_extract_display_proxy",
            "tool_version": "v0.1.0",
            "actor_id": actor_id,
            "session_id": session_id,
            "trace_id": trace_id,
        },
        "warning": "DISPLAY_DERIVED_PROXY — not suitable for quantitative seismic analysis",
    }
