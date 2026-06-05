"""
GEOX Volume Frame I/O — Frame-by-Frame Seismic Volume Operations
══════════════════════════════════════════════════════════════════
Forged from paleoscan_python Volume.getFrame / writeFrame patterns.

Provides orientation-aware frame extraction and writing for 3D seismic volumes.
All read operations return canonical Image2d schemas.
Write operations are explicitly marked for 888_HOLD gating at the MCP layer.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import numpy as np

from geox_core.core.geox_image import Image2d, Image3d, ScanOrientation

logger = logging.getLogger("geox.volume_frames")

# ─────────────────── FRAME EXTRACTION ───────────────────


def extract_frame_from_image3d(
    volume: Image3d,
    frame_index: int,
    orientation: ScanOrientation,
) -> Image2d:
    """
    Extract a 2D frame from an in-memory Image3d volume.

    Args:
        volume: Source Image3d volume.
        frame_index: Index of the frame to extract.
        orientation: Inline, Crossline, TimeSlice, or DepthSlice.

    Returns:
        Canonical Image2d (deep copy).
    """
    return volume.get_image(orientation, frame_index)


def extract_frame_from_segy(
    segy_path: str,
    frame_index: int,
    orientation: Literal["inline", "crossline", "time"] = "inline",
) -> Image2d | None:
    """
    Extract a single frame from a SEG-Y file using segyio.

    Args:
        segy_path: Path to SEG-Y file.
        frame_index: Frame index to extract.
        orientation: "inline", "crossline", or "time".

    Returns:
        Image2d on success, None on failure.
    """
    try:
        import segyio
    except ImportError:
        logger.error("segyio not available — cannot extract frame from SEG-Y")
        return None

    try:
        with segyio.open(segy_path, "r") as segy:
            if orientation == "inline":
                if not hasattr(segy, "iline") or frame_index >= len(segy.iline):
                    logger.error(f"Inline index {frame_index} out of range")
                    return None
                data = segy.iline[segy.ilines[frame_index]]
                img = Image2d(data.shape[1], data.shape[0], name=f"inline_{frame_index}")
                img._data = data.astype(np.float32)
                return img
            elif orientation == "crossline":
                if not hasattr(segy, "xline") or frame_index >= len(segy.xline):
                    logger.error(f"Crossline index {frame_index} out of range")
                    return None
                data = segy.xline[segy.xlines[frame_index]]
                img = Image2d(data.shape[1], data.shape[0], name=f"crossline_{frame_index}")
                img._data = data.astype(np.float32)
                return img
            else:
                # Time slice: extract from all traces at sample index
                data = segy.trace.raw[:]  # (n_traces, n_samples)
                if frame_index >= data.shape[1]:
                    logger.error(f"Time index {frame_index} out of range")
                    return None
                # Reshape to inline × crossline if possible
                n_il = len(segy.ilines) if hasattr(segy, "ilines") else 1
                n_xl = len(segy.xlines) if hasattr(segy, "xlines") else data.shape[0]
                if n_il * n_xl == data.shape[0]:
                    slice_data = data[:, frame_index].reshape(n_il, n_xl)
                else:
                    slice_data = data[:, frame_index].reshape(1, -1)
                img = Image2d(slice_data.shape[1], slice_data.shape[0], name=f"time_{frame_index}")
                img._data = slice_data.astype(np.float32)
                return img
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
        return None


# ─────────────────── FRAME WRITING ───────────────────


def write_frame_to_image3d(
    volume: Image3d,
    frame_index: int,
    orientation: ScanOrientation,
    image: Image2d,
) -> bool:
    """
    Write a 2D frame into an in-memory Image3d volume.

    Args:
        volume: Target Image3d volume.
        frame_index: Index where the frame will be written.
        orientation: Inline, Crossline, TimeSlice, or DepthSlice.
        image: Image2d to write.

    Returns:
        True on success.
    """
    try:
        volume.set_image(orientation, frame_index, image)
        return True
    except Exception as e:
        logger.error(f"Frame write failed: {e}")
        return False


# ─────────────────── VOLUME FILE CREATION ───────────────────


def create_segy_file(
    output_path: str,
    inline_range: tuple[int, int, int],
    crossline_range: tuple[int, int, int],
    sample_interval_ms: float,
    n_samples: int,
) -> bool:
    """
    Create a new SEG-Y file with the specified geometry and zero-filled traces.

    WARNING: This is an irreversible file write. MCP layer must 888_HOLD gate.

    Args:
        output_path: Path for new SEG-Y file.
        inline_range: (start, stop, step) for inline numbers.
        crossline_range: (start, stop, step) for crossline numbers.
        sample_interval_ms: Sample interval in milliseconds.
        n_samples: Number of samples per trace.

    Returns:
        True on success.
    """
    try:
        import segyio
    except ImportError:
        logger.error("segyio not available — cannot create SEG-Y file")
        return False

    try:
        ilines = np.arange(inline_range[0], inline_range[1] + 1, inline_range[2])
        xlines = np.arange(crossline_range[0], crossline_range[1] + 1, crossline_range[2])

        spec = segyio.spec()
        spec.sorting = 2
        spec.format = 1
        spec.samples = np.arange(n_samples) * sample_interval_ms
        spec.ilines = ilines
        spec.xlines = xlines

        with segyio.create(output_path, spec) as f:
            for il in ilines:
                for xl in xlines:
                    segyio.Trace(f, segyio.traceheader(field=segyio.su.iline) == il)
                    # segyio create handles trace allocation; we just ensure zeros
        return True
    except Exception as e:
        logger.error(f"SEGY file creation failed: {e}")
        return False


# ─────────────────── CANONICAL TOOL WRAPPERS ───────────────────


def geox_volume_get_frame(
    volume_ref: str,
    frame_index: int,
    orientation: str = "inline",
    provenance: str = "fixture",
) -> dict[str, Any]:
    """
    Skill-level wrapper: extract a frame and return canonical envelope.
    """
    from geox_core.skills.earth_science.seismic_wrappers import (
        ClaimTag,
        _admissibility_gate,
        make_vault_receipt,
    )

    gate = _admissibility_gate(provenance)
    claim_state = ClaimTag.OBSERVED.value if gate["claim_state"] != ClaimTag.HYPOTHESIS.value else ClaimTag.HYPOTHESIS.value

    result: dict[str, Any] = {
        "tool": "geox_volume_get_frame",
        "volume_ref": volume_ref,
        "frame_index": frame_index,
        "orientation": orientation,
        "claim_state": claim_state,
        "provenance": provenance,
    }

    # Attempt extraction
    img = extract_frame_from_segy(volume_ref, frame_index, orientation)  # type: ignore[arg-type]
    if img is None:
        result.update({
            "status": "error",
            "error": "Frame extraction failed — file not found or segyio unavailable",
            "verdict": "VOID",
        })
        result["vault_receipt"] = make_vault_receipt("geox_volume_get_frame", result, "VOID")
        return result

    result.update({
        "status": "extracted",
        "image": img.to_dict(),
        "width": img.width,
        "height": img.height,
        "verdict": "SEAL" if claim_state != ClaimTag.HYPOTHESIS.value else "HOLD",
    })
    result["vault_receipt"] = make_vault_receipt("geox_volume_get_frame", result, result["verdict"])
    return result


def geox_volume_set_frame(
    volume_ref: str,
    frame_index: int,
    orientation: str,
    image_data: list[list[float]],
) -> dict[str, Any]:
    """
    Skill-level wrapper: write a frame into a volume file.
    NOTE: This function is a SCHEMATIC — true frame writing into existing SEG-Y
    requires careful trace header preservation. Full implementation deferred to
    engine layer. Returns HOLD envelope to enforce 888_HOLD at MCP layer.
    """
    from geox_core.skills.earth_science.seismic_wrappers import (
        ClaimTag,
        make_vault_receipt,
    )

    result: dict[str, Any] = {
        "tool": "geox_volume_set_frame",
        "volume_ref": volume_ref,
        "frame_index": frame_index,
        "orientation": orientation,
        "claim_state": ClaimTag.COMPUTED.value,
        "status": "PENDING_ENGINE",
        "note": (
            "Frame write requires trace-header-aware SEG-Y rewriting. "
            "Schematic only — full engine pending. Use 888_HOLD."
        ),
        "verdict": "HOLD",
    }
    result["vault_receipt"] = make_vault_receipt("geox_volume_set_frame", result, "HOLD")
    return result
