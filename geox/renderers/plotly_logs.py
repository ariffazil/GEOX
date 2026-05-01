"""Optional Plotly HTML renderer adapter.

Plotly is intentionally optional. GEOX never requires it for static PNG/PDF
well-log evidence because the production spine is matplotlib.
"""

from __future__ import annotations

from pathlib import Path

from geox.artifacts.writer import validate_output_path
from geox.plot_specs.schemas import PlotSpec


def render_plotly_html_placeholder(spec: PlotSpec, output_html: str) -> str:
    """Write a deterministic HTML audit view without executing arbitrary code."""
    path = validate_output_path(output_html, must_have_suffix=".html")
    Path(path).write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>GEOX PlotSpec</title></head>"
        "<body><h1>GEOX PlotSpec Review</h1>"
        "<p>Interactive Plotly rendering is optional in this runtime.</p>"
        f"<pre>{spec.model_dump_json(indent=2)}</pre></body></html>"
    )
    return path
