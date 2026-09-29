"""
geox_seismic_render_publication.v1 — Deterministic publication-quality rendering.

Per the GEOX Seismic Interpretation Forge Package:
- Consumes artifact refs (Polylines, Polygons, VoxelMasks) + base PNG
- Returns image bytes (PNG) + SHA256 + provenance
- Dash style driven by confidence (high=solid, medium=dashed, low=short-dashed)
- Label collision avoidance via vertical offset + leader lines

This is DISPLAY-ONLY rendering. NO amplitudes, attributes, or quantitative
decisions are made from the rendered image. Per the display-proxy prohibition,
this tool does not lift that gate.

Reference: Copilot forge prompt BUILD step 4 of the section-image slice.
DITEMPA BUKAN DIBERI — Forged, not given.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import math
import os
from datetime import datetime, timezone
from typing import Any, Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from geox.seismic.contracts import PointSet, Polygon, Polyline, SurfaceMesh, VoxelMask

logger = logging.getLogger("geox.seismic_render_publication")

TOOL_NAME = "geox_seismic_render_publication"

DEFAULT_CONVENTIONS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "resources", "section_slice_conventions.json"
)


def _load_conventions(path: str | None = None) -> dict:
    p = path or DEFAULT_CONVENTIONS_PATH
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _font(conv: dict, size_key: str = "medium"):
    sizes = conv["font"]["sizes"]
    return ImageFont.truetype(
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
        sizes.get(size_key, 12),
    )


def _dash_segments(draw: ImageDraw.ImageDraw, points: list, color, width: int, dash_px: int = 12, gap_px: int = 7):
    acc = 0
    on = True
    for a, b in zip(points[:-1], points[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        s = 0
        while s < L and L > 0:
            seg = min((dash_px if on else gap_px) - acc, L - s)
            e = s + seg
            if on:
                draw.line(
                    [
                        (a[0] + (b[0] - a[0]) * s / L, a[1] + (b[1] - a[1]) * s / L),
                        (a[0] + (b[0] - a[0]) * e / L, a[1] + (b[1] - a[1]) * e / L),
                    ],
                    fill=color,
                    width=width,
                )
            acc += seg
            s = e
            if acc >= (dash_px if on else gap_px):
                acc = 0
                on = not on


def _line_with_halo(draw, points, color, width: int, dash=False):
    """Line with dark halo for legibility."""
    halo = (0, 0, 0, 230)
    if dash:
        _dash_segments(draw, points, halo, width=width + 3, dash_px=14, gap_px=6)
        _dash_segments(draw, points, color, width=width, dash_px=14, gap_px=6)
    else:
        draw.line(points, fill=halo, width=width + 3, joint="curve")
        draw.line(points, fill=color, width=width, joint="curve")


def _resolve_horizon_color(label: str | None, conv: dict):
    """Map a horizon label to its color class. Returns (rgb, line_style, line_width)."""
    if not label:
        return (200, 200, 200, 255), "dashed", 2
    label_lc = label.lower()
    if "sru" in label_lc:
        return tuple(conv["color_classes"]["horizon.sru"]["rgb"]) + (255,), "dashed", 4
    if "uiu" in label_lc:
        return tuple(conv["color_classes"]["horizon.uiu"]["rgb"]) + (255,), "solid", 3
    if "dru" in label_lc:
        return tuple(conv["color_classes"]["horizon.dru"]["rgb"]) + (255,), "solid", 5
    return (200, 200, 200, 255), "dashed", 2


def _avoid_label_collision(positions: list[tuple[float, float]], min_sep_px: float = 18) -> list[tuple[float, float]]:
    """Reorder labels vertically to avoid collisions (greedy)."""
    if not positions:
        return positions
    sorted_pos = sorted(enumerate(positions), key=lambda kv: kv[1][1])
    new_positions = list(positions)
    last_y = -math.inf
    for orig_idx, (x, y) in sorted_pos:
        if y < last_y + min_sep_px:
            new_positions[orig_idx] = (x, last_y + min_sep_px)
        last_y = new_positions[orig_idx][1]
    return new_positions


# ────────────────────────────────────────────────────────────────────────────
# Public tool
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_render_publication(
    png_base64: str | None = None,
    png_path: str | None = None,
    overlay_artifacts: list[dict] | None = None,
    output_size_px: tuple[int, int] | None = None,
    title: str | None = None,
    actor_id: str = "kimi-code/FI-008",
    session_id: str | None = None,
    trace_id: str | None = None,
    conventions_path: str | None = None,
    ctx: Any = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Render a deterministic publication-quality image.

    Parameters
    ----------
    png_base64, png_path : str
        Base image (one required).
    overlay_artifacts : list[dict]
        List of artifacts (Polyline/Polygon/VoxelMask). Each must have a
        `label` field (str, optional) and either `points` or `vertices`.
    output_size_px : tuple
        (width, height). Default: source image size.
    title : str
        Optional title rendered top-left.

    Returns
    -------
    dict with:
      - status: OK | HOLD
      - image_base64: rendered PNG
      - image_sha256: SHA256 of rendered PNG
      - provenance: source + overlay hash + parameters
      - claim: null
    """
    conv = _load_conventions(conventions_path)

    # Load base image
    if png_base64 is None and png_path is None:
        return _envelope(
            status="HOLD",
            error="either png_base64 or png_path required",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    try:
        if png_base64 is not None:
            img = Image.open(io.BytesIO(base64.b64decode(png_base64))).convert("RGBA")
        else:
            img = Image.open(png_path).convert("RGBA")
    except Exception as e:
        return _envelope(
            status="HOLD",
            error=f"failed to load image: {type(e).__name__}: {e}",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    src_hash = hashlib.sha256(img.convert("RGB").tobytes()).hexdigest()

    if output_size_px is not None:
        img = img.resize(output_size_px, Image.LANCZOS)

    overlay_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay_layer)
    label_positions: list[tuple[float, float]] = []

    for art in overlay_artifacts or []:
        label = art.get("label", "")
        color, style, width = _resolve_horizon_color(label, conv)
        pts = art.get("points") or art.get("vertices")
        if pts is None:
            continue
        # Polyline / SurfaceMesh path
        if isinstance(pts[0], (list, tuple)) and len(pts[0]) == 2:
            points_2d = [(float(p[0]), float(p[1])) for p in pts]
        elif isinstance(pts[0], (list, tuple)) and len(pts[0]) == 3:
            points_2d = [(float(p[0]), float(p[1])) for p in pts]
        else:
            continue

        if style == "dashed":
            _line_with_halo(draw, points_2d, color, width, dash=True)
        else:
            _line_with_halo(draw, points_2d, color, width, dash=False)

        # Label at midpoint
        if label and points_2d:
            mid = points_2d[len(points_2d) // 2]
            label_positions.append((mid[0], mid[1]))

    # Label collision avoidance
    safe_positions = _avoid_label_collision(label_positions)
    for (x, y), art in zip(safe_positions, overlay_artifacts or []):
        label = art.get("label", "")
        if not label:
            continue
        _, _, _ = _resolve_horizon_color(label, conv)
        draw.text(
            (x, y - 12),
            label,
            fill=(255, 255, 255, 255),
            font=_font(conv, "small"),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
            anchor="ms",
        )

    # Compose
    out = Image.alpha_composite(img, overlay_layer)
    if title:
        title_layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
        td = ImageDraw.Draw(title_layer)
        td.text(
            (10, 10),
            title,
            fill=(255, 255, 255, 255),
            font=_font(conv, "large"),
            stroke_width=4,
            stroke_fill=(0, 0, 0, 255),
        )
        out = Image.alpha_composite(out, title_layer)

    # Encode
    buf = io.BytesIO()
    out.convert("RGB").save(buf, format="PNG", optimize=True)
    rendered_bytes = buf.getvalue()
    rendered_b64 = base64.b64encode(rendered_bytes).decode("ascii")
    rendered_sha = hashlib.sha256(rendered_bytes).hexdigest()

    provenance = {
        "source_sha256": src_hash,
        "rendered_sha256": rendered_sha,
        "n_overlay_artifacts": len(overlay_artifacts or []),
        "image_size_px": list(out.size),
        "conventions_version": conv.get("version"),
        "issued_by": actor_id,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "DISPLAY_PROXY",
        "claim_ceiling": "GEOMETRY",
    }

    return {
        **_envelope(
            status="OK",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        ),
        "image_base64": rendered_b64,
        "image_sha256": rendered_sha,
        "provenance": provenance,
        "claim": None,
    }


def _envelope(
    *,
    status: str,
    error: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    env = {
        "tool_name": TOOL_NAME,
        "actor_id": actor_id or "kimi-code/FI-008",
        "session_id": session_id,
        "trace_id": trace_id,
        "execution_status": "OK" if status == "OK" else "HOLD",
        "artifact_status": "READY" if status == "OK" else "DRAFT",
        "governance_status": "QUALIFIED" if status == "OK" else "HOLD",
    }
    if status == "OK":
        return {**env, "status": "OK", "claim": None}
    return {**env, "status": status, "error": error, "hold_reason": error, "claim": None}


def register_with_mcp(mcp: Any) -> None:
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_render_publication)
    logger.info("Registered %s (deterministic render)", TOOL_NAME)
