"""SEG-Y slice extraction → MeasurementContext + amplitude grid (Phase D).

Preferred over image_only. Uses segyio when available.
Returns float32 grid samples — not greyscale proxy.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


async def geox_segy_slice(
    segy_path: str,
    frame_index: int = 0,
    orientation: str = "inline",
    max_traces: int = 512,
    max_samples: int = 1024,
) -> dict[str, Any]:
    """Extract a 2D amplitude slice from SEG-Y with G0 measurement context."""
    path = Path(segy_path)
    if not path.is_file():
        return {
            "ok": False,
            "tool": "geox_segy_slice",
            "error": "FILE_NOT_FOUND",
            "message": f"SEG-Y not found: {segy_path}",
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
        }

    try:
        import segyio
        import numpy as np
    except ImportError as e:
        return {
            "ok": False,
            "tool": "geox_segy_slice",
            "error": "SEGYIO_MISSING",
            "message": f"segyio/numpy required: {e}",
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
        }

    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        with segyio.open(str(path), "r", ignore_geometry=False) as f:
            sample_interval_us = int(f.bin[segyio.BinField.Interval])
            n_samples = int(f.bin[segyio.BinField.Samples])
            data = None
            label = orientation
            try:
                if orientation == "inline" and hasattr(f, "iline") and len(f.ilines):
                    idx = min(frame_index, len(f.ilines) - 1)
                    data = np.asarray(f.iline[f.ilines[idx]], dtype=np.float32)
                    label = f"inline_{int(f.ilines[idx])}"
                elif orientation == "crossline" and hasattr(f, "xline") and len(f.xlines):
                    idx = min(frame_index, len(f.xlines) - 1)
                    data = np.asarray(f.xline[f.xlines[idx]], dtype=np.float32)
                    label = f"crossline_{int(f.xlines[idx])}"
            except Exception:
                data = None

            if data is None:
                # Fallback: first N traces as pseudo-section
                ntr = min(len(f.trace), max_traces)
                rows = []
                for i in range(ntr):
                    tr = np.asarray(f.trace[i], dtype=np.float32)
                    rows.append(tr[:max_samples])
                data = np.stack(rows, axis=0)
                label = f"trace_section_0_{ntr}"

            # Cap size for MCP payload safety
            if data.ndim == 2:
                data = data[:max_traces, :max_samples]
            else:
                data = np.asarray(data, dtype=np.float32).reshape(1, -1)[:, :max_samples]

            sample_interval_ms = sample_interval_us / 1000.0 if sample_interval_us else None
            depth = None
            if sample_interval_ms:
                depth = [float(i * sample_interval_ms) for i in range(data.shape[1])]

            # 1D mean amplitude along traces for horizon_contrast handoff
            mean_trace = data.mean(axis=0).tolist()

            measurement_context = {
                "input_class": "segy_slice",
                "sha256": sha,
                "geometry": {
                    "sample_interval_ms": sample_interval_ms,
                    "n_samples_bin": n_samples,
                    "slice_shape": [int(data.shape[0]), int(data.shape[1])],
                    "orientation": orientation,
                    "frame_index": frame_index,
                    "label": label,
                    "polarity": "unknown",
                    "vertical_exaggeration": None,
                },
                "processing": {
                    "migration_type": None,
                    "amplitude_scaling": "native_segy_samples",
                },
                "source_path": str(path),
            }

            return {
                "ok": True,
                "tool": "geox_segy_slice",
                "input_class": "segy_slice",
                "measurement_context": measurement_context,
                "amplitude_grid_shape": [int(data.shape[0]), int(data.shape[1])],
                # Compact: mean 1D + corner stats (not full grid in MCP by default)
                "mean_amplitude_trace": mean_trace,
                "depth_ms": depth,
                "amplitude_stats": {
                    "min": float(np.nanmin(data)),
                    "max": float(np.nanmax(data)),
                    "mean": float(np.nanmean(data)),
                    "std": float(np.nanstd(data)),
                },
                "attribute_data": {
                    "seismic_amplitude": mean_trace,
                },
                "epistemic_label": "OBS",
                "governance_status": "QUALIFY",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "seal_authority": "arifOS_only",
                "honesty_banner": (
                    "SEG-Y samples are observations of a processed wavefield, "
                    "not direct geology. Structural picks still require gates + human ratification."
                ),
            }
    except Exception as e:
        return {
            "ok": False,
            "tool": "geox_segy_slice",
            "error": "SEGY_READ_FAILED",
            "message": str(e)[:500],
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
        }
