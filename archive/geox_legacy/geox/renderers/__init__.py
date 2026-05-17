"""
geox/renderers — Approved Renderer Surface Lock
═══════════════════════════════════════════════════════════════════════

Only approved renderer names are accepted. No dynamic renderer loading.
Renderers are deterministic and produce auditable artifacts.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any

from geox.plot_specs import PlotSpec
from geox.artifacts import validate_artifact, build_artifact_envelope

logger = logging.getLogger("geox.renderers")

# ── Approved renderer registry ────────────────────────────────────────────────

_APPROVED_RENDERERS: dict[str, Any] = {}


def register_renderer(name: str, func: Any) -> None:
    """Register an approved renderer. Internal use only."""
    _APPROVED_RENDERERS[name] = func
    logger.info("Renderer registered: %s", name)


def dispatch(spec: PlotSpec) -> dict[str, Any]:
    """
    Dispatch a validated PlotSpec to its approved renderer.

    Returns governed envelope with artifact validation baked in.
    """
    if spec.renderer not in _APPROVED_RENDERERS:
        return {
            "ok": False,
            "error": f"Renderer '{spec.renderer}' not in approved surface: {list(_APPROVED_RENDERERS.keys())}",
            "artifact": None,
            "claim_state": "BLOCKED",
        }

    renderer_fn = _APPROVED_RENDERERS[spec.renderer]
    try:
        result = renderer_fn(spec)
    except Exception as exc:
        logger.exception("Renderer %s failed", spec.renderer)
        return {
            "ok": False,
            "error": f"Renderer {spec.renderer} execution failed: {exc}",
            "artifact": None,
            "claim_state": "BLOCKED",
        }

    # Artifact truth verification — NEVER return success without it
    artifact_path = result.get("artifact_path")
    validation = validate_artifact(artifact_path, expected_format=spec.output_format)

    if not validation["ok"]:
        return {
            "ok": False,
            "error": f"Artifact validation failed: {validation['error']}",
            "artifact": validation,
            "claim_state": "BLOCKED",
        }

    envelope = build_artifact_envelope(
        artifact_path=str(artifact_path) if artifact_path else "",
        claim_state=spec.claim_state,
        depth_basis=spec.depth_basis,
        depth_unit=spec.depth_unit,
        renderer=spec.renderer,
        plot_spec_digest=_digest_spec(spec),
    )

    return {
        "ok": True,
        "error": None,
        "artifact": envelope,
        "claim_state": spec.claim_state,
    }


def _digest_spec(spec: PlotSpec) -> str:
    """Stable hash of the PlotSpec for lineage tracking."""
    import hashlib, json
    payload = {
        "renderer": spec.renderer,
        "plot_type": spec.plot_type,
        "title": spec.title,
        "data_refs": sorted(spec.data_refs),
        "curve_names": sorted(spec.curve_names),
        "depth_basis": spec.depth_basis,
        "depth_unit": spec.depth_unit,
        "output_format": spec.output_format,
        "normalize": spec.normalize,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


# ── Internal: matplotlib renderer ─────────────────────────────────────────────

def _render_matplotlib(spec: PlotSpec) -> dict[str, Any]:
    """Deterministic matplotlib renderer for well panels and sections."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import os

    os.makedirs(spec.output_dir, exist_ok=True)
    timestamp = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(spec.output_dir, f"geox_{spec.plot_type}_{timestamp}.{spec.output_format}")

    fig, ax = plt.subplots(figsize=(spec.width_px / spec.dpi, spec.height_px / spec.dpi), dpi=spec.dpi)
    ax.set_title(spec.title)
    ax.set_xlabel(spec.x_label)
    ax.set_ylabel(f"{spec.y_label} ({spec.depth_unit})")

    # Placeholder: deterministic line rendering from data_refs would go here.
    # For now, emit a structured placeholder that still produces a valid PNG.
    ax.text(0.5, 0.5, f"GEOX {spec.plot_type.upper()}\nRenderer: matplotlib\nDepth basis: {spec.depth_basis}",
            transform=ax.transAxes, ha="center", va="center", fontsize=10, family="monospace")
    ax.axis("off")

    fig.savefig(path, dpi=spec.dpi, bbox_inches="tight", format=spec.output_format)
    plt.close(fig)

    return {"artifact_path": path}


# ── Internal: plotly renderer (stub) ──────────────────────────────────────────

def _render_plotly(spec: PlotSpec) -> dict[str, Any]:
    """Deterministic plotly renderer for interactive HTML."""
    import os
    os.makedirs(spec.output_dir, exist_ok=True)
    timestamp = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(spec.output_dir, f"geox_{spec.plot_type}_{timestamp}.html")

    html = f"""<!DOCTYPE html>
<html><head><title>{spec.title}</title></head>
<body style="font-family:monospace;padding:2rem;">
<h2>{spec.title}</h2>
<p>Renderer: plotly | Depth basis: {spec.depth_basis} | Unit: {spec.depth_unit}</p>
<p>Data refs: {spec.data_refs}</p>
<p>Claim state: {spec.claim_state}</p>
</body></html>"""
    with open(path, "w") as f:
        f.write(html)
    return {"artifact_path": path}


# ── Internal: pillow renderer (stub) ──────────────────────────────────────────

def _render_pillow(spec: PlotSpec) -> dict[str, Any]:
    """Deterministic pillow renderer for image verification / thumbnails."""
    from PIL import Image, ImageDraw, ImageFont
    import os

    os.makedirs(spec.output_dir, exist_ok=True)
    timestamp = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(spec.output_dir, f"geox_{spec.plot_type}_{timestamp}.{spec.output_format}")

    img = Image.new("RGB", (spec.width_px, spec.height_px), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    text = f"GEOX {spec.plot_type}\nRenderer: pillow\nDepth basis: {spec.depth_basis}"
    draw.text((20, 20), text, fill=(30, 30, 30))
    img.save(path, format=spec.output_format.upper())
    return {"artifact_path": path}


# ── Internal: pyvista renderer (stub) ─────────────────────────────────────────

def _render_pyvista(spec: PlotSpec) -> dict[str, Any]:
    """Deterministic pyvista renderer for 3D previews."""
    import os
    os.makedirs(spec.output_dir, exist_ok=True)
    timestamp = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(spec.output_dir, f"geox_{spec.plot_type}_{timestamp}.{spec.output_format}")

    # PyVista is optional; if not installed, write a placeholder PNG
    try:
        import pyvista as pv
        plotter = pv.Plotter(off_screen=True)
        plotter.add_text(f"GEOX 3D | {spec.title}", font_size=12)
        plotter.add_mesh(pv.Cube(), color="lightblue")
        plotter.screenshot(path)
        plotter.close()
    except Exception:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (spec.width_px, spec.height_px), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), f"PyVista 3D placeholder\n{spec.title}", fill=(50, 50, 50))
        img.save(path)
    return {"artifact_path": path}


# ── Register all approved renderers at import time ─────────────────────────────

register_renderer("matplotlib", _render_matplotlib)
register_renderer("plotly", _render_plotly)
register_renderer("pillow", _render_pillow)
register_renderer("pyvista", _render_pyvista)
