"""
Copilot prototype v5 — v4 + DRU/UIU/SRU horizons + thickness plausibility gate.

Original Copilot output: ROTAN1_dipline_DRU_UIU_SRU_v5.png (annotated inline)
Algorithm: PIL ImageDraw with horizon color-mask extraction (red/blue/green)
+ thickness gate (>400 ms TWT → HOLD with intra-IVB explanation).

The thickness gate is what `geox_seismic_age_assign.v1` automates.

PUBLIC SYNTHETIC ONLY.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageDraw


# Color conventions per Morley 2023 (also in geox://conventions/seismic_display)
COLOR_SRU = (255, 140, 0)     # orange
COLOR_UIU = (0, 210, 255)     # cyan
COLOR_DRU = (31, 42, 107)     # navy


def synth_with_horizons(width: int = 600, height: int = 400) -> Image.Image:
    """Synthetic dip line with three colored horizons baked in."""
    rng = np.random.RandomState(13)
    img = Image.new("RGB", (width, height), (240, 240, 230))
    pix = np.asarray(img).copy()
    # Background banding
    for y in range(height):
        intensity = 200 + int(15 * np.sin(y * 0.05))
        for x in range(0, width, 3):
            pix[y, x] = [intensity + int(rng.randint(-15, 15))] * 3
    img = Image.fromarray(pix)
    draw = ImageDraw.Draw(img)
    # Draw three horizons as sinuous lines
    for label, color, base_y in (
        ("SRU", COLOR_SRU, 100),
        ("UIU", COLOR_UIU, 180),
        ("DRU", COLOR_DRU, 300),
    ):
        for x in range(0, width, 2):
            y = int(base_y + 20 * np.sin(x * 0.01))
            draw.line([(x, y), (x + 1, y)], fill=color, width=2)
    return img


def thickness_gate(thickness_px: int, ms_per_pixel: float = 8.27) -> dict:
    """The Copilot v5 + GEOX age_assign thickness gate.

    > 400 ms TWT (= 400 / ms_per_pixel px) → HOLD with intra-IVB / prolonged-subsidence
    Otherwise → PASS.
    """
    thickness_ms = thickness_px * ms_per_pixel
    if thickness_ms > 400:
        return {
            "verdict": "HOLD",
            "thickness_ms": thickness_ms,
            "reason": (
                f"measured thickness {thickness_ms:.0f} ms exceeds published IVC max "
                f"of 400 ms (Morley 2023 §6.2). Either (a) blue horizon is intra-IVB, "
                f"or (b) mini-basin subsidence persisted longer in this area."
            ),
        }
    return {"verdict": "PASS", "thickness_ms": thickness_ms}


def annotate_v5() -> dict:
    img = synth_with_horizons()
    # The thickness gate test case: SRU at y=100, UIU at y=180, IVC thickness = 80 px ~ 662 ms
    sru_y, uiu_y = 100, 180
    thickness_px = abs(uiu_y - sru_y)
    gate = thickness_gate(thickness_px, ms_per_pixel=8.27)
    return {
        "algorithm": "v5_dru_uiu_sru",
        "horizons_drawn": 3,
        "thickness_test": gate,
    }


if __name__ == "__main__":
    print(annotate_v5())
