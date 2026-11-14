"""
Copilot prototype v3 — dip line + mini-basin polygons (geometry only).

Original Copilot output: ROTAN1_dipline_diapirs_minibasins_v3.png
Algorithm preserved: PIL ImageDraw + color-based region marking.

This is the geometry-only baseline — no interpretation, no stratigraphy.
What `geox_seismic_display_trace.v1` automates.

PUBLIC SYNTHETIC ONLY — no real Morley data.
"""
from __future__ import annotations

import io
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def synth_dip_line(width: int = 600, height: int = 400) -> bytes:
    """Synthetic dip line mimicking Morley Fig 6 structural style."""
    rng = np.random.RandomState(7)
    img = Image.new("RGB", (width, height), (255, 255, 255))
    pix = np.asarray(img).copy()
    for y in range(height):
        intensity = 200 + int(20 * np.sin(y * 0.05))
        for x in range(0, width, 3):
            pix[y, x] = [intensity + int(rng.randint(-15, 15))] * 3
    return Image.fromarray(pix)


def mini_basin_polygon(
    center_x: int, center_y: int, radius_x: int = 40, radius_y: int = 30
) -> List[Tuple[int, int]]:
    """Compute polygon vertices approximating a mini-basin cross-section."""
    return [
        (center_x - radius_x, center_y + radius_y),
        (center_x + radius_x, center_y + radius_y),
        (center_x + int(radius_x * 0.6), center_y - radius_y),
        (center_x - int(radius_x * 0.6), center_y - radius_y),
    ]


def annotate_v3(width: int = 600, height: int = 400) -> dict:
    """Run v3 algorithm: synthetic dip line + mini-basin polygons."""
    img = synth_dip_line(width, height).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    mb_a = mini_basin_polygon(200, 280)
    mb_b = mini_basin_polygon(380, 260)
    mb_c = mini_basin_polygon(540, 290)
    for poly in (mb_a, mb_b, mb_c):
        draw.polygon(poly, fill=(200, 220, 255, 100), outline=(50, 50, 200, 255))
    buf = io.BytesIO()
    Image.alpha_composite(img, overlay).convert("RGB").save(buf, format="PNG")
    return {
        "algorithm": "v3_minibasins",
        "n_mini_basins": 3,
        "size_bytes": buf.tell(),
        "image_png_sha256_unavailable_due_to_no_external_save": True,
    }


if __name__ == "__main__":
    print(annotate_v3())
