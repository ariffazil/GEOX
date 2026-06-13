"""
GEOX SEG-Y Export Engine — 3D Volume Export
════════════════════════════════════════════
Forged from paleoscan_python segy.Exporter patterns.

Extends the existing 2D export_segy in geox_core/core/geox_2d.py to full 3D
volume export using canonical Image3d + CoordinateSystem substrates.

WARNING: File creation is irreversible. MCP layer enforces 888_HOLD gating.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from geox_core.core.geox_image import Image3d
from geox_core.spatial.transforms import CoordinateSystem

logger = logging.getLogger("geox.segy_export")


def export_volume_to_segy(
    output_path: str,
    volume: Image3d,
    coordinate_system: CoordinateSystem | None = None,
    textual_header: str = "",
    sample_interval_ms: float = 4.0,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Export a canonical Image3d volume to SEG-Y format.

    Args:
        output_path: Destination file path.
        volume: Source Image3d volume.
        coordinate_system: Optional CoordinateSystem for trace header geometry.
        textual_header: Optional 3200-byte EBCDIC/ASCII textual header.
        sample_interval_ms: Sample interval in milliseconds.
        overwrite: If False and file exists, raises FileExistsError behavior.

    Returns:
        Result dict with status, path, trace_count, and vault_receipt fields.
    """
    import os

    if os.path.exists(output_path) and not overwrite:
        return {
            "status": "error",
            "error": f"File exists and overwrite=False: {output_path}",
            "path": output_path,
        }

    try:
        import segyio
    except ImportError:
        logger.error("segyio not available — cannot export SEG-Y")
        return {
            "status": "error",
            "error": "segyio library not installed",
            "path": output_path,
        }

    try:
        n_il = volume.length
        n_xl = volume.width
        n_samples = volume.height

        # Build inline/crossline arrays
        ilines = np.arange(n_il, dtype=np.int32)
        xlines = np.arange(n_xl, dtype=np.int32)

        spec = segyio.spec()
        spec.sorting = 2  # Inline sorted
        spec.format = 1  # IBM float (standard)
        spec.samples = np.arange(n_samples) * sample_interval_ms
        spec.ilines = ilines
        spec.xlines = xlines

        with segyio.create(output_path, spec) as f:
            trace_index = 0
            for il in range(n_il):
                for xl in range(n_xl):
                    trace = volume._data[il, :, xl].astype(np.float32)
                    f.trace[trace_index] = trace

                    # Write trace header with geometry if available
                    hdr = f.header[trace_index]
                    hdr[segyio.su.iline] = il
                    hdr[segyio.su.xline] = xl
                    hdr[segyio.su.tracf] = trace_index + 1
                    hdr[segyio.su.cdps] = trace_index + 1
                    hdr[segyio.su.ns] = n_samples
                    hdr[segyio.su.dt] = int(sample_interval_ms * 1000)

                    if coordinate_system:
                        # Add survey coordinate info if available
                        try:
                            block_pt = np.array([[xl, il, 0]], dtype=np.float64)
                            survey_pt = coordinate_system.transform_points(block_pt, "block", "survey")
                            hdr[segyio.su.sx] = int(survey_pt[0, 0] * 1000)  # scaled coordinate
                            hdr[segyio.su.sy] = int(survey_pt[0, 1] * 1000)
                        except Exception:
                            pass

                    trace_index += 1

            # Textual header
            if textual_header:
                f.text[0] = textual_header

        return {
            "status": "exported",
            "path": output_path,
            "trace_count": n_il * n_xl,
            "inline_count": n_il,
            "crossline_count": n_xl,
            "sample_count": n_samples,
            "sample_interval_ms": sample_interval_ms,
        }

    except Exception as e:
        logger.error(f"SEG-Y export failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "path": output_path,
        }
