#!/usr/bin/env python3
"""Deterministic base render for the Sabah A-A' cross-section (STAGE 3).

Geometry source of truth: _geometry_raw.json — extracted verbatim from
arif-fazil.com/earth/kinabalu-cross-section.html in-page data (XS + MODELS),
which was hand-plotted from published values (see page REFS). Public sources only.

This script computes NOTHING synthetic: it maps (km along, depth km) polygons
through a declared two-panel vertical scale (upper 0-15 km @ ~17x, lower
15-60 km @ ~3x) and renders flat lithology fills. No text in the base PNG
(text arrives in STAGE 6, by code).

Usage: python3 render_base.py [--model A|B|C|D|all]
"""

import json, math, sys, pathlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle

HERE = pathlib.Path(__file__).resolve().parent
DATA = json.loads((HERE / "_geometry_raw.json").read_text())
XS, MODELS, SUBDRU = DATA["XS"], DATA["MODELS"], DATA["SUBDRU"]
FACIES = XS["facies"]

# ── vertical scale (declared, from the page renderer) ─────────────────────────
W_KM = 833.0
Z_TOP, Z_BRK, Z_BOT = -4.6, 15.0, 60.0
H_TOP, H_LOW = 560.0, 240.0  # px heights → aspect ratio of panels
VE_TOP = (H_TOP / (Z_BRK - Z_TOP)) / (1480.0 / W_KM)  # ≈17x
VE_LOW = (H_LOW / (Z_BOT - Z_BRK)) / (1480.0 / W_KM)  # ≈3x


def split_panel(pts, lo, hi):
    """Clip a polygon to a z-band with vertical rescaling at the boundary."""
    out = []
    for i, (x, z) in enumerate(pts):
        jx, jz = pts[(i + 1) % len(pts)]
        segs = [(x, z), (jx, jz)]
        # simple clip: keep vertices inside band, add crossings
        if lo <= z <= hi:
            out.append((x, z))
        for a, b in ((segs[0], segs[1]),):
            (x1, z1), (x2, z2) = a, b
            if (z1 < lo <= z2) or (z2 < lo < z1):
                t = (lo - z1) / (z2 - z1)
                out.append((x1 + t * (x2 - x1), lo))
            if (z1 > hi >= z2) or (z2 > hi > z1):
                t = (hi - z1) / (z2 - z1)
                out.append((x1 + t * (x2 - x1), hi))
    return out


def draw_body(ax, pts, band, color, hatch=None, alpha=0.96, ec="#0a0e17", lw=0.6):
    clipped = split_panel(pts, band[0], band[1])
    if len(clipped) < 3:
        return
    ax.add_patch(MplPoly(clipped, closed=True, facecolor=color, edgecolor=ec, linewidth=lw, alpha=alpha, hatch=hatch, zorder=2))


def render(model_id, out_prefix, with_masks=False):
    model = next(m for m in MODELS if m["id"] == model_id)
    fig = plt.figure(figsize=(16.5, 9.6), dpi=150)
    fig.patch.set_facecolor("#0a0e17")
    ax_t = fig.add_axes([0.045, 0.415, 0.935, 0.545])  # upper panel
    ax_b = fig.add_axes([0.045, 0.075, 0.935, 0.315])  # lower panel

    mantle = FACIES.get("MANTLE", {}).get("fill", "#1a1420")
    for ax, band, xlab in ((ax_t, (-4.6, 15.0), False), (ax_b, (15.0, 60.0), True)):
        ax.set_facecolor(mantle if band[0] >= 15.0 else "#0d1220")
        ax.set_xlim(0, W_KM)
        ax.set_ylim(band[0], band[1])
        ax.invert_yaxis()
        for s in ax.spines.values():
            s.set_color("#22304a")
        ax.tick_params(colors="#5b6b85", labelsize=7)

    # 1. water column (0 → surface where surface > 0)
    surf = XS["surface"]
    for ax, band in ((ax_t, (-4.6, 15.0)), (ax_b, (15.0, 60.0))):
        wtop = [(x, 0.0) for x, _ in surf]
        wpts = list(surf) + wtop[::-1]
        draw_body(ax, wpts, band, FACIES["WATER"]["fill"], alpha=0.85, lw=0)

    # 2. shared bodies
    masks = {}
    for b in XS["common"]:
        col = FACIES.get(b["f"], {}).get("fill", "#444")
        for ax, band in ((ax_t, (-4.6, 15.0)), (ax_b, (15.0, 60.0))):
            draw_body(ax, b["pts"], band, col)
        masks[b["f"]] = b["pts"]

    # 3. model bodies (deep geometry differs per model)
    for b in model["bodies"]:
        col = FACIES.get(b["f"], {}).get("fill", "#555")
        hatch = "xxx" if b["f"] == "BASALT" else None
        for ax, band in ((ax_t, (-4.6, 15.0)), (ax_b, (15.0, 60.0))):
            draw_body(ax, b["pts"], band, col, hatch=hatch, alpha=0.9)
        masks[b["f"]] = b["pts"]

    # 4. surfaces (MMU/DRU/SRU + Moho/detachment if present)
    for ln in XS["lines"]:
        pts = ln["pts"]
        for ax, band in ((ax_t, (-4.6, 15.0)), (ax_b, (15.0, 60.0))):
            seg = [(x, z) for x, z in pts if band[0] <= z <= band[1]]
            if len(seg) >= 2:
                xs_, zs_ = zip(*seg)
                ax.plot(xs_, zs_, color=ln.get("c", "#e2e8f0"), lw=ln.get("w", 1.4), solid_capstyle="round", zorder=5)

    # 5. faults
    for f in XS["faults"]:
        st = {
            "thrust": ("#f1f5f9", 1.1, None),
            "normal": ("#cbd5e1", 0.9, None),
            "strike": ("#cbd5e1", 0.9, (0, (2, 3))),
            "detach": ("#fb7185", 1.4, (0, (7, 4))),
        }.get(f.get("k", "thrust"), ("#e2e8f0", 1.0, None))
        for ax, band in ((ax_t, (-4.6, 15.0)), (ax_b, (15.0, 60.0))):
            seg = [(x, z) for x, z in f["pts"] if band[0] <= z <= band[1]]
            if len(seg) >= 2:
                xs_, zs_ = zip(*seg)
                ax.plot(xs_, zs_, color=st[0], lw=st[1], ls=st[2] or "-", zorder=6)

    # 6. topography/bathymetry profile (bold)
    for ax, band in ((ax_t, (-4.6, 15.0)), (ax_b, (15.0, 60.0))):
        seg = [(x, z) for x, z in surf if band[0] <= z <= band[1]]
        if len(seg) >= 2:
            xs_, zs_ = zip(*seg)
            ax.plot(xs_, zs_, color="#e8e6e1", lw=2.0, zorder=7)

    fig.savefig(f"{out_prefix}.png", facecolor=fig.get_facecolor())
    plt.close(fig)
    json.dump({"masks": {k: v for k, v in masks.items()}}, open(f"{out_prefix}_masks.json", "w"))
    print(f"rendered {out_prefix}.png (model {model_id})")


if __name__ == "__main__":
    args = sys.argv[1:]
    want = args[args.index("--model") + 1] if "--model" in args else "all"
    ids = ["A", "B", "C", "D"] if want == "all" else [want]
    for mid in ids:
        render(mid, str(HERE / f"base_{mid}"))
