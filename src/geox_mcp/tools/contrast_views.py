"""
GEOX Contrast Views — Band A Raster-Only Seismic Attribute Pipeline
════════════════════════════════════════════════════════════════════
Eureka: the 9 Contrast Visual Attributes (2026-06-08) — image-only
interpretation pipeline that lets an LLM reason about seismic
sections WITHOUT raw SEG-Y access.

This module is the raster-side of the contrast primitive. Each mode
returns a 2D attribute image of the same shape as the input. The
composition is the PerceptualInventory that feeds the LLM via
geox_vision_perceptual_inventory.

MVP scope (Phase 1 — 2026-06-08):
  - amplitude_envelope  (Attribute 1)
  - edge_map           (Attribute 2)
  - texture_energy     (Attribute 3)

The remaining 6 attributes (horizontal_gradient, vertical_gradient,
local_dip, phase_symmetry, frequency_content, AC_Risk heatmap) are
phased road-map items. They share the same `geox_contrast_views`
entry point so callers can compose freely.

Constitutional binding (F1-F13):
  F1 AMANAH     — read-only computation, no I/O
  F2 TRUTH      — output is a measured signal, never an interpretation
  F4 CLARITY    — every output carries axis metadata + provenance
  F7 HUMILITY   — outputs are HYPOTHESIS-grade (CLAIM at most)
  F9 ANTIHANTU  — no "this IS a fault" — only "this is a gradient signal"

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from scipy import ndimage

from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    get_standard_envelope,
)

logger = logging.getLogger("geox.canonical.contrast_views")

ContrastMode = Literal[
    "amplitude_envelope",  # Phase 1
    "edge_map",  # Phase 1
    "texture_energy",  # Phase 1
    # Phase 2 (planned):
    # "horizontal_gradient",
    # "vertical_gradient",
    # "local_dip",
    # "phase_symmetry",
    # "frequency_content",
    # "ac_risk_heatmap",  (Attribute 9 — governance, lives in contrast_ac_risk.py)
]

PHASE1_MODES: tuple[str, ...] = ("amplitude_envelope", "edge_map", "texture_energy")
PHASE2_MODES: tuple[str, ...] = (
    "horizontal_gradient",
    "vertical_gradient",
    "local_dip",
    "phase_symmetry",
    "frequency_content",
)


# ═══════════════════════════════════════════════════════════════════════════════
# Input loading (raster-only — no SEG-Y, this is the Band A pipeline)
# ═══════════════════════════════════════════════════════════════════════════════


def _load_raster(source: str | np.ndarray) -> np.ndarray:
    """Load a raster from path or accept an in-memory array. Returns a
    2D float64 grayscale array normalized to [0, 1].

    For multi-channel input (RGB/RGBA), averages to luminance via
    Rec. 709 weights — the standard for seismic image export pipelines.
    """
    if isinstance(source, np.ndarray):
        arr = source
    else:
        # Lazy import so tests don't need PIL
        from PIL import Image

        img = Image.open(source)
        arr = np.asarray(img)
    if arr.ndim == 3:
        # RGB or RGBA → luminance via Rec. 709
        if arr.shape[2] == 4:
            arr = arr[..., :3]
        # weights per Rec. 709
        w = np.array([0.2126, 0.7152, 0.0722])
        arr = (arr[..., :3].astype(np.float64) * w).sum(axis=-1)
    elif arr.ndim != 2:
        raise ValueError(f"contrast_views expects a 2D grayscale or HxWx3/RGBA image; got shape {arr.shape}")
    arr = arr.astype(np.float64)
    lo, hi = float(arr.min()), float(arr.max())
    if hi > lo:
        arr = (arr - lo) / (hi - lo)
    return arr


# ═══════════════════════════════════════════════════════════════════════════════
# Per-mode attribute kernels
# ═══════════════════════════════════════════════════════════════════════════════


def _amplitude_envelope(img: np.ndarray, **kwargs: Any) -> np.ndarray:
    """Attribute 1: Amplitude Envelope (Normalized Intensity).

    Physical proxy: reflection strength / acoustic impedance contrast.
    Output is the input normalized to [0, 1] — this is the identity
    attribute, but the wrapper is needed so all 9 attributes can be
    composed uniformly.
    """
    return img.copy()


def _edge_map(img: np.ndarray, sigma: float = 1.0, **kwargs: Any) -> np.ndarray:
    """Attribute 2: Edge/Discontinuity Map (Sobel Gradient Magnitude).

    Physical proxy: faults, unconformities, lateral facies boundaries.
    Returns the magnitude of the image gradient after Gaussian
    smoothing (sigma=1.0 is the seismic-interpretation default).
    """
    smoothed = ndimage.gaussian_filter(img, sigma=sigma)
    sx = ndimage.sobel(smoothed, axis=1, mode="reflect")
    sy = ndimage.sobel(smoothed, axis=0, mode="reflect")
    return np.hypot(sx, sy)


def _texture_energy(img: np.ndarray, window: int = 7, **kwargs: Any) -> np.ndarray:
    """Attribute 3: Local Variance / Texture Energy.

    Physical proxy: seismic facies character.
    Returns the per-pixel local variance in a `window x window`
    neighborhood. High variance = chaotic; near-zero = transparent.
    """
    if window < 3 or window % 2 == 0:
        raise ValueError(f"window must be odd and >= 3; got {window}")
    mu = ndimage.uniform_filter(img, size=window, mode="reflect")
    mu_sq = ndimage.uniform_filter(img * img, size=window, mode="reflect")
    var = np.maximum(mu_sq - mu * mu, 0.0)
    return var


_MODE_REGISTRY: dict[str, Any] = {
    "amplitude_envelope": _amplitude_envelope,
    "edge_map": _edge_map,
    "texture_energy": _texture_energy,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Main tool
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class AttributeImage:
    """One computed attribute (2D, same shape as input)."""

    mode: str
    axis: str  # physical axis name
    data: np.ndarray
    normalization: str  # how the values are scaled ("[0,1]", "raw", etc.)
    computation: str  # short description of the math

    def to_dict(self) -> dict[str, Any]:
        # For JSON-safety we serialize data as a list. For large images
        # the caller should chunk / downsample before serializing.
        return {
            "mode": self.mode,
            "axis": self.axis,
            "shape": list(self.data.shape),
            "normalization": self.normalization,
            "computation": self.computation,
            # Store a small summary so the LLM can reason without the full grid.
            "summary": {
                "min": float(self.data.min()),
                "max": float(self.data.max()),
                "mean": float(self.data.mean()),
                "p50": float(np.percentile(self.data, 50)),
                "p95": float(np.percentile(self.data, 95)),
                "p99": float(np.percentile(self.data, 99)),
            },
            # Downsample the full array to a thumbnail for the LLM
            "thumbnail": _downsample_for_thumbnail(self.data).tolist(),
        }


def _downsample_for_thumbnail(arr: np.ndarray, max_dim: int = 64) -> np.ndarray:
    """Downsample a 2D array to a thumbnail (max_dim x max_dim) for LLM
    consumption. Uses simple striding — sufficient for shape/edge
    detection by a VLM.
    """
    h, w = arr.shape
    stride_h = max(1, h // max_dim)
    stride_w = max(1, w // max_dim)
    return arr[::stride_h, ::stride_w]


async def geox_contrast_views(
    source: str | list[str] | np.ndarray,  # path / list / in-memory array
    modes: list[str] | None = None,
    # Per-mode params
    edge_sigma: float = 1.0,
    texture_window: int = 7,
    # Provenance
    image_provenance: dict[str, Any] | None = None,
    basin_context: str | None = None,
) -> dict:
    """Compute Band A contrast attributes from one or more raster images.

    Parameters
    ----------
    source : str | list[str]
        Path(s) to PNG/JPG seismic image(s). Multi-image support is
        reserved for the future — current MVP accepts a single path.
    modes : list[str], optional
        Which attributes to compute. Default = all Phase 1 modes
        (amplitude_envelope, edge_map, texture_energy). Valid modes
        see `ContrastMode` type alias.
    edge_sigma : float
        Gaussian smoothing sigma before Sobel (Attribute 2).
    texture_window : int
        Odd >=3 window for local variance (Attribute 3).
    image_provenance : dict, optional
        Provenance metadata (CRS, scale, source, scale_bar_TWT, etc.).
        Per F4 CLARITY: scale is mandatory, CRS is mandatory.
    basin_context : str, optional
        Free-text basin/region context (e.g. "Malay Basin", "Sabah").
    """
    # ── Input validation ──────────────────────────────────────────────
    if isinstance(source, list) and len(source) > 1:
        return get_standard_envelope(
            {
                "tool": "geox_contrast_views",
                "error_code": "MULTI_IMAGE_NOT_YET_SUPPORTED",
                "message": "MVP scope is single-image only. Pass source as a string path.",
            },
            tool_class="compute",
            execution_status=ExecutionStatus.RECOVERABLE_ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )
    if not modes:
        modes = list(PHASE1_MODES)
    invalid = [m for m in modes if m not in _MODE_REGISTRY]
    if invalid:
        valid = sorted(_MODE_REGISTRY.keys())
        return get_standard_envelope(
            {
                "tool": "geox_contrast_views",
                "error_code": "INVALID_MODE",
                "message": f"Unknown modes: {invalid}. Valid: {valid}. "
                "Phase 2 modes (horizontal_gradient, vertical_gradient, "
                "local_dip, phase_symmetry, frequency_content) are planned.",
                "valid_modes": valid,
            },
            tool_class="compute",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )

    # ── Load raster ───────────────────────────────────────────────────
    try:
        if isinstance(source, str):
            img = _load_raster(source)
        elif isinstance(source, np.ndarray):
            img = _load_raster(source)
        elif isinstance(source, list):
            if len(source) == 0:
                raise ValueError("source list is empty")
            img = _load_raster(source[0])
        else:
            raise ValueError(f"source must be str, list[str], or np.ndarray; got {type(source).__name__}")
    except Exception as exc:
        return get_standard_envelope(
            {
                "tool": "geox_contrast_views",
                "error_code": "RASTER_LOAD_FAIL",
                "message": f"Could not load raster: {exc}",
            },
            tool_class="compute",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )

    if img.ndim != 2 or img.size == 0:
        return get_standard_envelope(
            {
                "tool": "geox_contrast_views",
                "error_code": "EMPTY_IMAGE",
                "message": f"Loaded image has no usable 2D data (shape={img.shape}).",
            },
            tool_class="compute",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )

    # ── Per-attribute axis map (physical axis, F2 TRUTH attribution) ─
    AXIS_MAP: dict[str, tuple[str, str, str]] = {
        # mode: (axis, normalization, computation)
        "amplitude_envelope": (
            "reflection_strength",
            "[0,1]",
            "grayscale normalization (Rec.709 for RGB input)",
        ),
        "edge_map": (
            "structural_discontinuity",
            "raw (gradient magnitude)",
            "Sobel gradient magnitude after Gaussian(sigma=1.0) smoothing",
        ),
        "texture_energy": (
            "seismic_facies_character",
            "variance (>=0)",
            f"local variance in {texture_window}x{texture_window} window (uniform_filter)",
        ),
    }

    # ── Compute ───────────────────────────────────────────────────────
    attributes: list[dict[str, Any]] = []
    for mode in modes:
        try:
            if mode == "edge_map":
                data = _edge_map(img, sigma=edge_sigma)
            elif mode == "texture_energy":
                data = _texture_energy(img, window=texture_window)
            elif mode == "amplitude_envelope":
                data = _amplitude_envelope(img)
            else:
                # Should not reach here (validated above) but fail closed
                continue
            axis, norm, comp = AXIS_MAP[mode]
            attributes.append(
                AttributeImage(
                    mode=mode,
                    axis=axis,
                    data=data,
                    normalization=norm,
                    computation=comp,
                ).to_dict()
            )
        except Exception as exc:
            # Per-mode failure doesn't kill the whole computation.
            # The other attributes still surface — that's the audit
            # primitive (you can see what worked and what didn't).
            attributes.append(
                {
                    "mode": mode,
                    "axis": AXIS_MAP.get(mode, ("unknown",))[0],
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    # ── Aggregate + verdict ───────────────────────────────────────────
    n_success = sum(1 for a in attributes if "summary" in a)
    n_failed = len(attributes) - n_success
    if n_failed > 0 and n_success == 0:
        verdict = "HOLD"
        verdict_reason = f"All {n_failed} attribute(s) failed to compute."
        claim_state = "NO_VALID_EVIDENCE"
    elif n_failed > 0:
        verdict = "QUALIFY"
        verdict_reason = f"{n_success}/{len(attributes)} attributes computed; {n_failed} failed."
        claim_state = "PLAUSIBLE"
    else:
        verdict = "QUALIFY"
        verdict_reason = f"All {n_success} attributes computed cleanly."
        claim_state = "PLAUSIBLE"

    result = {
        "tool": "geox_contrast_views",
        "phase": "Phase 1 (3 of 9 attributes)",
        "image_shape": list(img.shape),
        "basin_context": basin_context,
        "image_provenance": image_provenance or {},
        "attributes": attributes,
        "summary": {
            "n_attributes_requested": len(modes),
            "n_attributes_computed": n_success,
            "n_attributes_failed": n_failed,
            "verdict": verdict,
            "verdict_reason": verdict_reason,
            "primary_hypothesis": (
                "Each computed attribute isolates a different contrast primitive. "
                "The 8 physical attributes are independent physical channels; "
                "an LLM receiving all 8 simultaneously can reason about "
                "geological structure without knowing geology a priori."
            ),
            "alternative_explanations": [
                "Some attributes may be degenerate for images with very low contrast.",
                "Phase 2 attributes (gradients, dip, phase, frequency) carry additional signal not yet extracted.",
                "AC_Risk heatmap (Attribute 9) is the governance layer that audits all 8 — not yet implemented in Phase 1.",
            ],
            "missing_evidence": [
                "image_provenance with CRS + scale_bar_TWT (per F4 CLARITY)",
                "basin_context for grounded interpretation",
            ],
            "caveat": (
                "This is a HYPOTHESIS-grade tool. Attribute images are PHYSICAL "
                "SIGNALS, not interpretations. The LLM downstream (via "
                "geox_vision_perceptual_inventory) is responsible for translating "
                "signal → geology, and that translation is gated by F2/F7/F9. "
                "GEOX computes; the LLM interprets; arifOS judges."
            ),
        },
        "phase2_roadmap": {
            "status": "planned",
            "remaining_attributes": [
                "horizontal_gradient (Attribute 4)",
                "vertical_gradient (Attribute 5)",
                "local_dip (Attribute 6)",
                "phase_symmetry (Attribute 7)",
                "frequency_content (Attribute 8)",
                "ac_risk_heatmap (Attribute 9 — governance)",
            ],
            "depends_on": "F13 ratification of Phase 1 + user feedback on Phase 1 output.",
        },
    }

    return get_standard_envelope(
        result,
        tool_class="compute",
        execution_status=ExecutionStatus.SUCCESS,
        governance_status=GovernanceStatus[verdict] if verdict in ("HOLD", "QUALIFY") else GovernanceStatus.QUALIFY,
        claim_tag=("HYPOTHESIS" if verdict == "HOLD" else "PLAUSIBLE"),
        claim_state=claim_state,
        evidence_refs=[],
    )
