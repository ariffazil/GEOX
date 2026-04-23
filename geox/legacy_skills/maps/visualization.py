"""
JSON-serializable visualization payload builders for GEOX Wave 2.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from geox.core.governed_output import classify_claim_tag, make_vault_receipt


def geox_render_log_track_tool(curves: list[dict[str, Any]], title: str = "Log Track Viewer") -> dict[str, Any]:
    tracks = []
    for curve in curves:
        samples = curve.get("samples", [])
        values = [float(sample["value"]) for sample in samples]
        depths = [float(sample["depth"]) for sample in samples]
        tracks.append(
            {
                "mnemonic": curve["mnemonic"],
                "color": curve.get("color", "#3b82f6"),
                "depths": depths,
                "values": values,
            }
        )
    payload = {
        "title": title,
        "tracks": tracks,
        "depth_range": [
            min((min(track["depths"]) for track in tracks if track["depths"]), default=0.0),
            max((max(track["depths"]) for track in tracks if track["depths"]), default=0.0),
        ],
        "claim_tag": classify_claim_tag(0.75),
    }
    payload["vault_receipt"] = make_vault_receipt("geox_render_log_track", payload)
    return payload


def geox_render_volume_slice_tool(
    volume: list[list[float]] | list[list[list[float]]],
    orientation: str = "inline",
    slice_index: int = 0,
) -> dict[str, Any]:
    array = np.asarray(volume, dtype=float)
    if array.ndim == 3:
        if orientation == "inline":
            slice_data = array[slice_index]
        elif orientation == "crossline":
            slice_data = array[:, slice_index, :]
        else:
            slice_data = array[:, :, slice_index]
    else:
        slice_data = array
    payload = {
        "orientation": orientation,
        "slice_index": slice_index,
        "width": int(slice_data.shape[-1]),
        "height": int(slice_data.shape[0]),
        "values": slice_data.tolist(),
        "min_value": float(np.min(slice_data)),
        "max_value": float(np.max(slice_data)),
        "claim_tag": classify_claim_tag(0.75),
    }
    payload["vault_receipt"] = make_vault_receipt("geox_render_volume_slice", payload)
    return payload
