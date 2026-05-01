"""Validation helpers for GEOX declarative PlotSpecs."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from geox.plot_specs.schemas import PlotSpec, PlotSpecValidationError

DEFAULT_TRACK_UNITS = {
    "GR": "gAPI",
    "RT": "ohm.m",
    "RDEP": "ohm.m",
    "RESD": "ohm.m",
    "RHOB": "g/cc",
    "NPHI": "v/v",
    "DT": "us/ft",
    "CAL": "in",
    "SP": "mV",
}


def validate_plot_spec(raw_spec: dict[str, Any]) -> PlotSpec:
    try:
        return PlotSpec.model_validate(raw_spec)
    except PlotSpecValidationError:
        raise
    except ValidationError as exc:
        raise PlotSpecValidationError(str(exc)) from exc


def build_well_panel_plot_spec(
    *,
    las_paths: list[str],
    tracks: list[str],
    depth_range: list[float] | None = None,
    output_formats: list[str] | None = None,
    raw_plot_spec: dict[str, Any] | None = None,
) -> PlotSpec:
    if raw_plot_spec:
        merged = dict(raw_plot_spec)
        merged.setdefault("las_paths", las_paths)
        merged.setdefault("plot_type", "well_correlation_panel")
        merged.setdefault("claim_state", "EXPLORATORY_VISUALIZATION")
        if tracks:
            merged.setdefault("tracks", [_track_to_spec(track) for track in tracks])
        if depth_range:
            depth = dict(merged.get("depth") or {})
            depth.setdefault("range", depth_range)
            merged["depth"] = depth
        if output_formats:
            merged.setdefault("outputs", output_formats)
        return validate_plot_spec(merged)

    return validate_plot_spec(
        {
            "plot_type": "well_correlation_panel",
            "las_paths": las_paths,
            "depth": {
                "basis": "MD",
                "unit": "m",
                "range": depth_range,
                "increasing_down": True,
            },
            "tracks": [_track_to_spec(track) for track in tracks],
            "renderer": {"primary": "matplotlib", "secondary": "none"},
            "outputs": output_formats or ["png", "csv_summary", "json_audit"],
            "claim_state": "EXPLORATORY_VISUALIZATION",
        }
    )


def _track_to_spec(track: str) -> dict[str, Any]:
    curve = str(track).strip().upper()
    scale = "log" if curve in {"RT", "RDEP", "RESD", "ILD", "LLD", "RES"} else "linear"
    return {
        "name": curve,
        "curves": [curve],
        "scale": scale,
        "unit": DEFAULT_TRACK_UNITS.get(curve),
    }
