"""Base types for deterministic GEOX renderers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from geox.plot_specs.schemas import PlotSpec


class RendererError(RuntimeError):
    """Renderer failed before producing a valid artifact."""


@dataclass
class RenderRequest:
    plot_spec: PlotSpec
    output_dir: str
    output_png: str | None = None
    well_names: list[str] | None = None
    tops: dict | None = None
    basin_hint: str | None = None
    well_ids: list[str] | None = None
    normalize: bool = True


@dataclass
class RenderResult:
    ok: bool
    artifacts: dict[str, str | None] = field(default_factory=dict)
    validation: dict[str, dict[str, Any]] = field(default_factory=dict)
    audit_path: str | None = None
    warnings: list[str] = field(default_factory=list)
    claim_state: str = "EXPLORATORY_VISUALIZATION"
    payload: dict[str, Any] = field(default_factory=dict)
