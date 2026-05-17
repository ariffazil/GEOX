from geox.skills.subsurface.maps.visualization import (
    geox_render_log_track_tool,
    geox_render_volume_slice_tool,
)

def _normalise(values: list[float]) -> list[float]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    span = hi - lo or 1.0
    return [(value - lo) / span for value in values]


def geox_render_log_track(
    depth: list[float],
    gr: list[float] | None = None,
    rhob: list[float] | None = None,
    nphi: list[float] | None = None,
    rt: list[float] | None = None,
    title: str = "Log Track Viewer",
) -> dict:
    from geox.core.governed_output import make_vault_receipt

    tracks = []
    for mnemonic, values in [("GR", gr), ("RHOB", rhob), ("NPHI", nphi), ("RT", rt)]:
        if values is None:
            continue
        float_values = [float(v) for v in values]
        tracks.append(
            {
                "mnemonic": mnemonic,
                "depths": depth,
                "values": float_values,
                "normalised": _normalise(float_values),
            }
        )
    payload = {
        "render_type": "log_track",
        "title": title,
        "n_samples": len(depth),
        "tracks": tracks,
    }
    payload["vault_receipt"] = make_vault_receipt("geox_render_log_track", payload)
    return payload


def geox_render_volume_slice(
    volume_data: list[list[float]] | list[list[list[float]]],
    nx: int | None = None,
    ny: int | None = None,
    **_: object,
) -> dict:
    import numpy as np
    from geox.core.governed_output import make_vault_receipt

    array = np.asarray(volume_data, dtype=float)
    if array.ndim == 3:
        array = array[0]
    lo = float(np.min(array))
    hi = float(np.max(array))
    span = hi - lo or 1.0
    payload = {
        "render_type": "volume_slice",
        "nx": int(nx or array.shape[-1]),
        "ny": int(ny or array.shape[0]),
        "flat_data": [float((value - lo) / span) for value in array.flatten()],
    }
    payload["vault_receipt"] = make_vault_receipt("geox_render_volume_slice", payload)
    return payload

__all__ = [
    "geox_render_log_track_tool",
    "geox_render_volume_slice_tool",
    "geox_render_log_track",
    "geox_render_volume_slice",
]
