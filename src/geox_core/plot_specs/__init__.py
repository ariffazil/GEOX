"""
geox/plot_specs — Deterministic Visualization Specification
═══════════════════════════════════════════════════════════════════════

Declarative PlotSpec validation. Rejects ALL executable fields.
Only geometry, styling, and data-reference descriptors are permitted.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("geox.plot_specs")

# ── Forbidden fields (executable / arbitrary code vectors) ────────────────────

_FORBIDDEN_KEYS: set[str] = {
    "exec", "eval", "code", "script", "shell", "command", "subprocess",
    "import", "__import__", "compile", "open", "os.system", "os.popen",
    "eval_expression", "lambda", "fn", "function", "callback", "hook",
    "javascript", "js", "wasm", "bytecode", "pickle", "marshal",
}

# ── Approved renderer surface ─────────────────────────────────────────────────

_APPROVED_RENDERERS: set[str] = {
    "matplotlib",
    "plotly",
    "pillow",
    "pyvista",
}


# ── PlotSpec dataclass ────────────────────────────────────────────────────────

@dataclass
class PlotSpec:
    """Deterministic, declarative plot specification."""

    renderer: str = "matplotlib"
    plot_type: str = "line"  # line, scatter, histogram, image, surface, section
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    z_label: str = ""
    width_px: int = 1200
    height_px: int = 800
    dpi: int = 150
    output_format: str = "png"  # png, svg, pdf, html
    output_dir: str = "/tmp/geox_artifacts"
    depth_basis: str = "MD"  # MD, TVD, TVDSS
    depth_unit: str = "m"
    claim_state: str = "INGESTED"

    # Data references (artifact handles, not raw arrays)
    data_refs: list[str] = field(default_factory=list)
    curve_names: list[str] = field(default_factory=list)
    tops_refs: list[str] = field(default_factory=list)

    # Styling (deterministic, no dynamic evaluation)
    colors: list[str] = field(default_factory=list)
    line_styles: list[str] = field(default_factory=list)
    markers: list[str] = field(default_factory=list)
    normalize: bool = True

    # Optional annotation text (plain string only)
    annotations: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    basin_hint: str = ""
    tags: list[str] = field(default_factory=list)

    def validate(self) -> dict[str, Any]:
        """
        Fail-closed validation.
        Returns {"ok": True} or {"ok": False, "error": ..., "blocked_fields": [...]}
        """
        # 1. Renderer approval
        if self.renderer not in _APPROVED_RENDERERS:
            return {
                "ok": False,
                "error": f"Renderer '{self.renderer}' is not approved. Allowed: {_APPROVED_RENDERERS}",
                "blocked_fields": ["renderer"],
            }

        # 2. Output format approval
        if self.output_format not in {"png", "svg", "pdf", "html", "csv"}:
            return {
                "ok": False,
                "error": f"Output format '{self.output_format}' is not approved.",
                "blocked_fields": ["output_format"],
            }

        # 3. Forbidden-key scan (deep, recursive)
        blocked = _scan_forbidden(self.__dict__)
        if blocked:
            return {
                "ok": False,
                "error": f"PlotSpec contains forbidden executable fields: {blocked}",
                "blocked_fields": blocked,
            }

        # 4. Depth basis
        if self.depth_basis not in {"MD", "TVD", "TVDSS", "KB", "DF", "WS"}:
            return {
                "ok": False,
                "error": f"Depth basis '{self.depth_basis}' is not recognized.",
                "blocked_fields": ["depth_basis"],
            }

        return {"ok": True}


def _scan_forbidden(obj: Any, path: str = "") -> list[str]:
    """Recursively scan a dict/list for forbidden keys."""
    found: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            k_str = str(k).lower()
            if k_str in _FORBIDDEN_KEYS or any(f in k_str for f in _FORBIDDEN_KEYS):
                found.append(f"{path}.{k}" if path else k)
            found.extend(_scan_forbidden(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(_scan_forbidden(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        lowered = obj.lower()
        if any(f"{f}(" in lowered or f" {f} " in lowered for f in _FORBIDDEN_KEYS):
            found.append(f"{path}: suspicious string content")
    return found


def from_dict(payload: dict[str, Any]) -> PlotSpec:
    """Construct a PlotSpec from a raw dict, rejecting extra fields silently."""
    allowed = {f.name for f in PlotSpec.__dataclass_fields__.values()}
    filtered = {k: v for k, v in payload.items() if k in allowed}
    return PlotSpec(**filtered)
