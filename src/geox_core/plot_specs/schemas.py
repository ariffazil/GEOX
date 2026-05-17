"""Pydantic PlotSpec schemas used by governed GEOX plotting execution."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

FORBIDDEN_PLOT_SPEC_FIELDS = {
    "code",
    "python",
    "python_code",
    "script",
    "shell",
    "command",
    "commands",
    "eval",
    "exec",
    "subprocess",
    "os.system",
    "import",
    "imports",
    "__import__",
    "network_fetch",
    "urlopen",
}


class PlotSpecValidationError(ValueError):
    """Raised when a PlotSpec violates GEOX plotting governance."""


class DepthSpec(BaseModel):
    basis: Literal["MD", "TVD", "TVDSS", "UNKNOWN"] = "MD"
    unit: Literal["m", "ft", "M", "FT", "UNKNOWN"] = "m"
    range: list[float] | None = None
    increasing_down: bool = True

    @field_validator("range")
    @classmethod
    def validate_range(cls, value: list[float] | None) -> list[float] | None:
        if value is None:
            return None
        if len(value) != 2:
            raise ValueError("depth.range must contain exactly [min, max]")
        if value[0] >= value[1]:
            raise ValueError("depth.range min must be smaller than max")
        return value


class TrackSpec(BaseModel):
    name: str
    curves: list[str]
    scale: Literal["linear", "log"] = "linear"
    xlim: list[float] | None = None
    unit: str | None = None
    overlay: bool = False

    @field_validator("curves")
    @classmethod
    def validate_curves(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("track.curves cannot be empty")
        return [str(curve).strip().upper() for curve in value if str(curve).strip()]

    @model_validator(mode="after")
    def default_resistivity_log_scale(self) -> TrackSpec:
        curve_names = {curve.upper() for curve in self.curves}
        if curve_names.intersection({"RT", "RDEP", "RESD", "ILD", "LLD", "RES"}):
            self.scale = "log"
        return self


class RendererSpec(BaseModel):
    primary: Literal["matplotlib"] = "matplotlib"
    secondary: Literal["plotly_html", "none"] = "none"


class PlotSpec(BaseModel):
    plot_type: Literal["well_log_panel", "well_correlation_panel", "curve_qc_dashboard"]
    artifact_refs: list[str] = Field(default_factory=list)
    las_paths: list[str] = Field(default_factory=list)
    depth: DepthSpec = Field(default_factory=DepthSpec)
    tracks: list[TrackSpec]
    curve_aliases: dict[str, list[str]] = Field(default_factory=dict)
    annotations: dict[str, Any] = Field(default_factory=dict)
    renderer: RendererSpec = Field(default_factory=RendererSpec)
    outputs: list[Literal["png", "svg", "pdf", "html", "csv_summary", "json_audit"]] = Field(
        default_factory=lambda: ["png", "csv_summary", "json_audit"]
    )
    claim_state: Literal[
        "RAW_OBSERVATION",
        "EXPLORATORY_VISUALIZATION",
        "INTERPRETIVE_SUMMARY",
        "DECISION_SENSITIVE",
        "NO_VALID_EVIDENCE",
    ] = "EXPLORATORY_VISUALIZATION"

    @model_validator(mode="before")
    @classmethod
    def reject_executable_fields(cls, data: Any) -> Any:
        _reject_forbidden_fields(data)
        return data

    @model_validator(mode="after")
    def validate_evidence(self) -> PlotSpec:
        if not self.artifact_refs and not self.las_paths:
            raise ValueError("PlotSpec requires artifact_refs or las_paths")
        if not self.tracks:
            raise ValueError("PlotSpec requires at least one track")
        if "html" in self.outputs and self.renderer.secondary == "none":
            self.renderer.secondary = "plotly_html"
        return self

    @property
    def canonical_tracks(self) -> list[str]:
        tracks: list[str] = []
        for track in self.tracks:
            for curve in track.curves:
                if curve not in tracks:
                    tracks.append(curve)
        return tracks


def _reject_forbidden_fields(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            executable_tokens = ("python_code", "os.system", "subprocess")
            if lowered in FORBIDDEN_PLOT_SPEC_FIELDS or any(
                token in lowered for token in executable_tokens
            ):
                location = f"{path}.{key_text}" if path else key_text
                raise PlotSpecValidationError(f"Executable PlotSpec field rejected: {location}")
            _reject_forbidden_fields(child, f"{path}.{key_text}" if path else key_text)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_fields(child, f"{path}[{index}]")
