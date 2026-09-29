"""
Copilot prototype v4 — v3 + diapir interpretation (purple polygons).

Original Copilot output: ROTAN1_dipline_DRU_SRU_diapirs_v4.png
Algorithm: PIL ImageDraw with semi-transparent purple overlays on diapir cores.

This is the first INTERPRETATION step (vs geometry-only v3).
What `geox_seismic_alternative_interpret.v1` automates (with discriminator set).

PUBLIC SYNTHETIC ONLY.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageDraw


def synth_with_diapirs(width: int = 600, height: int = 400) -> Image.Image:
    """Synthetic dip line with diapir-shaped anomalies baked into base."""
    rng = np.random.RandomState(11)
    img = Image.new("RGB", (width, height), (255, 255, 255))
    pix = np.asarray(img).copy()
    for y in range(height):
        intensity = 200 + int(20 * np.sin(y * 0.05))
        for x in range(0, width, 3):
            pix[y, x] = [intensity + int(rng.randint(-15, 15))] * 3
    return Image.fromarray(pix)


def diapir_polygon(center_x: int, height_y: int, width: int = 50, height: int = 200) -> list:
    """Tall narrow polygon for diapir core."""
    return [
        (center_x - width // 2, height_y),
        (center_x + width // 2, height_y),
        (center_x + width // 3, height_y - height),
        (center_x - width // 3, height_y - height),
    ]


def annotate_v4() -> dict:
    img = synth_with_diapirs().convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    purple = (123, 63, 160, 130)
    d1 = diapir_polygon(150, 380, width=60, height=250)
    d2 = diapir_polygon(280, 380, width=40, height=300)
    d3 = diapir_polygon(450, 380, width=70, height=200)
    d4 = diapir_polygon(550, 380, width=50, height=220)
    for poly in (d1, d2, d3, d4):
        draw.polygon(poly, fill=purple, outline=(80, 30, 120, 255))
    buf = io.BytesIO()
    Image.alpha_composite(img, overlay).convert("RGB").save(buf, format="PNG")
    return {"algorithm": "v4_diapirs", "n_diapirs": 4, "size_bytes": buf.tell()}


if __name__ == "__main__":
    print(annotate_v4())
