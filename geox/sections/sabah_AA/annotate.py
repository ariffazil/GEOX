#!/usr/bin/env python3
"""STAGE 6 (v2) — annotation by code on an EXPANDED canvas.

Pastes styl_D_c2.png into a larger dark canvas (real margins), redraws the
spec geometry the image model dropped (computed, not generated), then labels.
"""

import json, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
XS = json.loads((HERE / "_geometry_raw.json").read_text())["XS"]

SRC = Image.open(HERE / "styl_D_c2.png").convert("RGB")
sw, sh = SRC.size
ML, MR, MT, MB = 150, 60, 150, 120  # margins
W, H = sw + ML + MR, sh + MT + MB
BG = (10, 14, 23)
CAN = Image.new("RGB", (W, H), BG)
CAN.paste(SRC, (ML, MT))
draw = ImageDraw.Draw(CAN, "RGBA")

# panel bounds within the pasted image
arr = np.asarray(SRC.convert("L"))
row_dark = arr.max(axis=1) < 40
rows = np.where(~row_dark)[0]
col_dark = arr.max(axis=0) < 40
cols = np.where(~col_dark)[0]
top, bot = MT + rows.min(), MT + rows.max()
mid = [r for r in range(MT + rows.min(), MT + rows.max()) if row_dark[r - MT]]
split = int(np.median(mid)) if mid else int(top + 0.56 * (bot - top))
L, R = ML + cols.min(), ML + cols.max()
UP_T, UP_B, LO_T, LO_B = top, split - 4, split + 4, bot


def xpx(km):
    return L + km / 833.0 * (R - L)


def yu(z):
    return UP_T + (z - (-4.6)) / (15.0 - (-4.6)) * (UP_B - UP_T)


def yl(z):
    return LO_T + (z - 15.0) / (60.0 - 15.0) * (LO_B - LO_T)


def line(pts, color, width=3, dash=False):
    for panel, fy in (("u", yu), ("l", yl)):
        seg = [(xpx(x), fy(z)) for x, z in pts if (panel == "u" and -4.6 <= z <= 15.0) or (panel == "l" and 15.0 <= z <= 60.0)]
        if len(seg) >= 2:
            if dash:
                for i in range(0, len(seg) - 1, 2):
                    draw.line([seg[i], seg[min(i + 1, len(seg) - 1)]], fill=color, width=width)
            else:
                draw.line(seg, fill=color, width=width, joint="curve")


LINES = {ln["id"]: ln for ln in XS["lines"]}
if "MMU" in LINES:
    line(LINES["MMU"]["pts"], (45, 212, 191, 255), 3)
for ln in XS["lines"]:
    if ln["id"] not in ("MMU", "DRU", "SRU"):
        line(ln["pts"], (251, 113, 133, 235), 3)
for f in XS["faults"]:
    if f.get("k") == "detach":
        line(f["pts"], (251, 113, 133, 220), 3, dash=True)


def font(sz, bold=False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()


F_S, F_M, F_L, F_XL = font(13), font(16), font(22, True), font(27, True)
GOLD, INK, DIM = (201, 162, 39), (232, 230, 225), (148, 163, 184)


def text(x, y, s, f, fill=INK, anchor="la"):
    draw.text((x + 1, y + 1), s, font=f, fill=(10, 14, 23, 235), anchor=anchor)
    draw.text((x, y), s, font=f, fill=fill, anchor=anchor)


# ── title block (top margin) ─────────────────────────────────────────────────
text(ML, 28, "SABAH A–A′  ·  DANGEROUS GROUNDS → SULU SEA  ·  ~830 km", F_XL, GOLD)
text(ML, 74, "Model D · slab remnant + gravity tectonics (published) — one of four competing working models", F_M, INK)
text(W - MR, 84, "Vertical exaggeration: upper ~17× · lower ~3× · read shapes, not angles", F_S, DIM, anchor="ra")

# ── province band ────────────────────────────────────────────────────────────
by = 112
for k0, k1, name in XS["provinces"]:
    x0, x1 = xpx(k0), xpx(k1)
    draw.line([(x0, by), (x1, by)], fill=GOLD + (170,), width=2)
    draw.line([(x0, by - 5), (x0, by + 5)], fill=GOLD + (170,), width=2)
    draw.line([(x1, by - 5), (x1, by + 5)], fill=GOLD + (170,), width=2)
    text((x0 + x1) / 2, by + 8, name, F_S, GOLD, anchor="ma")

# ── feature labels near their own lines ──────────────────────────────────────
text(xpx(30), yu(2.7) - 30, "RU/MMU ~16 Ma", F_S, (45, 212, 191))
text(xpx(296), yu(5.3) + 16, "DRU · surface ~14.2 Ma (NN5)", F_S, GOLD)
text(xpx(296), yu(5.3) + 38, "published charts ~15.5 Ma", F_S, DIM)
text(xpx(352), yu(2.6) - 26, "SRU ~8–9.5 Ma", F_S, (248, 113, 113))
text(xpx(268), yu(3.2) + 26, "Sabah Trough ~2.9 km", F_S, DIM)
text(xpx(487) + 44, yu(-3.6), "Mt Kinabalu 4,095 m", F_S, GOLD, anchor="la")
text(xpx(432), yu(7.6), "Kinabalu granite  7.85–7.22 Ma\n(Cottam et al. 2010)", F_S, INK, anchor="ra")
text(xpx(470), yl(46) - 4, "detached slab remnant?\n45–55 km (Cornwell et al. 2025)", F_S, INK, anchor="la")

# ── axes ─────────────────────────────────────────────────────────────────────
for km in range(0, 834, 100):
    x = xpx(km)
    draw.line([(x, LO_B), (x, LO_B + 6)], fill=DIM + (190,), width=2)
    text(x, LO_B + 10, f"{km}", F_S, DIM, anchor="ma")
text((L + R) / 2, LO_B + 34, "DISTANCE ALONG A–A′  (km)", F_M, GOLD, anchor="ma")
for z in (0, 5, 10):
    draw.line([(L - 6, yu(z)), (L, yu(z))], fill=DIM + (190,), width=2)
    text(L - 12, yu(z) - 8, f"{z}", F_S, DIM, anchor="ra")
for z in (20, 30, 40, 50, 60):
    draw.line([(L - 6, yl(z)), (L, yl(z))], fill=DIM + (190,), width=2)
    text(L - 12, yl(z) - 8, f"{z}", F_S, DIM, anchor="ra")
text(L - 12, UP_T - 30, "DEPTH (km)", F_M, GOLD, anchor="ra")

# ── provenance footer ────────────────────────────────────────────────────────
text(
    ML,
    H - 64,
    "Schematic. Geometry from section_spec.json (public sources only) · textures stylised with Google Gemini "
    "gemini-3-pro-image (Nano Banana Pro, 2026-10-20) · geometry QC: boundary recall 0.947, 21/21 bodies preserved; "
    "MMU/detachment lines re-drawn by code (image model dropped them) · qc_report.json",
    F_S,
    DIM,
)
text(ML, H - 32, "DITEMPA BUKAN DIBERI · arifOS GEOX", F_S, GOLD)

OUT = CAN.resize((W * 2, H * 2), Image.LANCZOS)
OUT.save(HERE / "final_D.png")
print("final_D.png:", OUT.size)
