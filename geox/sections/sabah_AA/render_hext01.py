#!/usr/bin/env python3
"""Three-panel H-EXT-01 figure — inherited architecture / extension overprint / competing drivers.

All geometry is code-drawn and CONCEPTUAL where marked. Nothing here is styled as a
seismic pick. Output: tri_panel_hext01.png (desktop) + tri_panel_hext01_mobile.png.
"""

import json, pathlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D

HERE = pathlib.Path(__file__).resolve().parent
XS = json.loads((HERE / "_geometry_raw.json").read_text())["XS"]
F = XS["facies"]
BG, INK, GOLD, DIM = "#0a0e17", "#e8e6e1", "#c9a227", "#8b98ab"


def poly(ax, pts, color, alpha=1.0, ec=BG, lw=0.8, hatch=None, z=2):
    ax.add_patch(MplPoly(pts, closed=True, facecolor=color, edgecolor=ec, lw=lw, alpha=alpha, hatch=hatch, zorder=z))


def arrow(ax, xy1, xy2, color=GOLD, lw=2.2, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(xy1, xy2, arrowstyle=style, color=color, lw=lw, linestyle=ls, mutation_scale=14, zorder=8))


def shared(ax, names, alpha=1.0):
    for b in XS["common"]:
        if b["f"] in names:
            poly(ax, b["pts"], F.get(b["f"], {}).get("fill", "#444"), alpha=alpha)


def frame(ax, title, sub):
    ax.set_xlim(0, 833)
    ax.set_ylim(60, -5)
    ax.set_facecolor("#0d1220")
    for s in ax.spines.values():
        s.set_color("#22304a")
    ax.set_xticks([])
    ax.set_yticks([0, 15, 30, 45, 60])
    ax.tick_params(colors=DIM, labelsize=8)
    ax.set_title(title, color=GOLD, fontsize=12, fontweight="bold", loc="left", pad=6)
    ax.text(0.005, -0.10, sub, transform=ax.transAxes, color=DIM, fontsize=8.5, va="top")


def ledger(ax, rows):
    ax.text(
        0.03,
        0.60,
        "WHAT IS WHAT",
        transform=ax.transAxes,
        color=GOLD,
        fontsize=8,
        ha="left",
        va="top",
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", fc="#0a0e17", ec="#22304a"),
    )
    for i, (tag, txt, col) in enumerate(rows):
        ax.text(
            0.03,
            0.535 - i * 0.075,
            f"{tag}: {txt}",
            transform=ax.transAxes,
            color=col,
            fontsize=7.5,
            ha="left",
            va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="#0a0e17", ec="none"),
        )


def draw_inherited(ax, alpha=1.0):
    shared(
        ax,
        {
            "WATER",
            "DRAPE",
            "CARB",
            "SYNRIFT",
            "TOE",
            "STAGE4",
            "CCRUST",
            "PRISM",
            "MELANGE",
            "CIRC",
            "SANDK",
            "GRANITE",
            "OCEAN",
            "SABCRUST",
            "MOBSH",
        },
        alpha=alpha,
    )
    for ln in XS["lines"]:
        xs, zs = zip(*ln["pts"])
        ax.plot(xs, zs, color=ln.get("c", "#ddd"), lw=1.3, alpha=alpha, zorder=6)


def build(rows_spec, figtitle, out, w, h):
    fig = plt.figure(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(BG)
    fig.suptitle(figtitle, color=GOLD, fontsize=15 if w > 14 else 12.5, fontweight="bold", x=0.02, ha="left", y=0.99)
    fig.text(
        0.02,
        0.962,
        "Sabah A–A′ · theory H-EXT-01 (GEOX/Arif synthesis, TESTABLE) · preferred_hypothesis = null · schematic — not a seismic section",
        color=DIM,
        fontsize=8.5 if w > 14 else 7.5,
    )
    n = len(rows_spec)
    for i, (ax_kind, title, sub) in enumerate(rows_spec):
        if w > 14:
            ax = fig.add_axes([0.035 + i * 0.322, 0.09, 0.285, 0.77])
        else:
            ax = fig.add_axes([0.06, 0.80 - i * 0.262, 0.88, 0.20])
        ax_kind(ax, title, sub)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)
    print("wrote", out)


# ── panel builders ───────────────────────────────────────────────────────────
def p1(ax, title, sub):
    frame(ax, "1 · INHERITED ARCHITECTURE", "PSCS subduction → DG underthrusting + accretionary orogen + shallow NSPW system")
    draw_inherited(ax)
    # slab = off-panel mantle annotation
    ax.plot([430, 600], [52, 57], color="#7dd3fc", lw=2, ls=(0, (6, 4)), zorder=7)
    ax.text(
        515,
        58.5,
        "PSCS slab remnant? — OFF-PANEL MANTLE ANNOTATION (published imaging, not fitted)",
        color="#7dd3fc",
        fontsize=7,
        ha="center",
    )
    arrow(ax, (250, 20), (330, 20), "#93c5fd", 2.0)
    ax.text(290, 18, "underthrusting (classic model C)", color="#93c5fd", fontsize=7, ha="center")
    ledger(
        ax,
        [
            ("OBS", "topo/bathy · granite 7.85–7.22 Ma · RF Moho 32.8±2.5 (KMY)", "#7ee787"),
            ("INT", "underthrust geometry · prism architecture", "#79c0ff"),
            ("SPEC", "—", DIM),
            ("UNKNOWN", "crustal suture (Vijayan 2013: none found)", "#ffa657"),
        ],
    )


def p2(ax, title, sub):
    frame(
        ax, "2 \u00b7 H-EXT-01 \u00b7 EXTENSION OVERPRINT (SPEC)", "post-subduction extension across NORTH-CENTRAL Sabah \u2014 the missing link"
    )
    draw_inherited(ax, alpha=0.45)
    z1 = [[430, 2], [560, 2], [560, 38], [430, 38]]
    z2 = [[560, 2], [700, 2], [700, 38], [560, 38]]
    poly(ax, z1, "#c9a227", alpha=0.16, ec=GOLD, lw=2.0, z=7)
    poly(ax, z2, "#c9a227", alpha=0.06, ec="none", z=7)
    ax.plot([430, 430, 560, 560, 430], [2, 38, 38, 2, 2], color=GOLD, lw=2.0, ls=(0, (6, 3)), zorder=8)
    ax.plot([560, 560, 700, 700, 560], [2, 38, 38, 2, 2], color=GOLD, lw=1.4, ls=(0, (2, 3)), alpha=0.65, zorder=8)
    ax.text(495, 4, "SOURCE-CONSTRAINED\nthinning / extension\n(Crocker-Ranau)", color=GOLD, fontsize=7, ha="center", va="top", zorder=9)
    ax.text(648, 4, "H-EXT-01 POSSIBLE\nCONTINUATION\nTEST REQUIRED ?", color=GOLD, fontsize=7, ha="center", va="top", alpha=0.85, zorder=9)
    ax.text(290, 4, "MORLEY 2023: shallow\nmobile-shale - NOT deep\nextension evidence", color="#94a3b8", fontsize=6.8, ha="center", va="top", zorder=9)
    ax.text(555, 27, "H-EXT-01 \u00b7 EXTENSION STRAIN FIELD (hypothesized)\ncontinuity = TESTABLE, not observed", color=GOLD, fontsize=8, ha="center", va="center", fontweight="bold", zorder=9)
    ax.text(505, 19, "granite + exhumation\n(melting consequence)", color=INK, fontsize=7, ha="left")
    arrow(ax, (455, -1), (415, -1), GOLD, 2.4)
    arrow(ax, (625, -1), (665, -1), GOLD, 2.4)
    ax.text(540, 47, "continental thinning (\u03b2 ~1.2\u20131.3, Greenfield 2022)\noceanic breakup = UNMEASURED \u00b7 strain field \u2260 fault geometry", color=GOLD, fontsize=7.5, ha="center")
    arrow(ax, (500, 33), (500, 29), "#fca5a5", 2.0)
    arrow(ax, (590, 33), (590, 29), "#fca5a5", 2.0)
    ax.text(545, 33.5, "thinning / Moho pull-up?", color="#fca5a5", fontsize=7, ha="center")
    arrow(ax, (780, 52), (640, 42), "#a78bfa", 1.6, ls=(0, (4, 3)))
    ax.text(782, 55, "SE mantle context: lithospheric thinning / drip (Bacon 2022)\ncausal link? - dashed hypothesis, NOT an imaged conduit", color="#a78bfa", fontsize=6.8, ha="right")
    ledger(
        ax,
        [
            ("OBS", "granite 7.85\u20137.22 Ma \u00b7 rapid exhumation \u00b7 Moho variations", "#7ee787"),
            ("INT", "regional extension phase (Hall 2013)", "#79c0ff"),
            ("SPEC", "corridor continuity \u00b7 dip/width", "#d2a8ff"),
            ("UNKNOWN", "oceanic vs continental (thinning < breakup)", "#ffa657"),
        ],
    )



def p3(ax, title, sub):
    frame(ax, "3 · COMPETING DRIVERS — ALL LIVE (none preferred)", "same crustal expression, four causal alternatives")
    bands = {"A": (-5, 15), "B": (15, 30), "C": (30, 45), "D": (45, 60)}
    for k, (z0, z1) in bands.items():
        ax.axhline(z1, color="#22304a", lw=0.8, ls=":")
    # A rollback (z -5..15)
    ax.plot([280, 480], [12, -2], color="#7dd3fc", lw=2.2, ls=(0, (6, 4)))
    arrow(ax, (470, 1), (415, -3), "#7dd3fc", 1.8)
    arrow(ax, (330, 3), (385, 3), GOLD, 1.8)
    ax.text(30, 2, "H-EXT-01A  ROLLBACK", color="#93c5fd", fontsize=9, fontweight="bold")
    ax.text(30, 5.5, "slab rollback drives trench-parallel extension (Hall 2013)", color=DIM, fontsize=7)
    # B drip (z 15..30)
    ax.plot([240, 600], [20, 20], color="#8b98ab", lw=1.6)
    poly(ax, [[395, 20], [435, 20], [425, 29], [405, 29]], "#7c2d12", alpha=0.9, hatch="xx", z=5)
    arrow(ax, (415, 21), (415, 27), "#f0abfc", 1.8)
    arrow(ax, (300, 17), (360, 17), GOLD, 1.6)
    arrow(ax, (530, 17), (470, 17), GOLD, 1.6)
    ax.text(30, 17, "H-EXT-01B  LITHOSPHERIC DRIP", color="#f0abfc", fontsize=9, fontweight="bold")
    ax.text(
        30,
        20.5,
        "drip drives extension + melting + exhumation (Pilia 2023) \u00b7 drip interpreted SE of Kinabalu (Bacon 2022)",
        color=DIM,
        fontsize=7,
    )
    # C collapse (z 30..45)
    poly(ax, [[330, 42], [420, 33], [510, 42], [510, 45], [330, 45]], "#4c3d63", alpha=0.85, z=5)
    arrow(ax, (355, 39), (315, 39), "#86efac", 1.8)
    arrow(ax, (485, 39), (525, 39), "#86efac", 1.8)
    ax.text(30, 32, "H-EXT-01C  GRAVITATIONAL COLLAPSE", color="#86efac", fontsize=9, fontweight="bold")
    ax.text(30, 35.5, "orogenic load spreads on detachments (King 2010)", color=DIM, fontsize=7)
    # D reactivation (z 45..60)
    for x0 in (300, 365, 430, 495, 560):
        ax.plot([x0, x0 + 10], [52, 46], color="#fdba74", lw=1.5, ls=(0, (3, 2)))
        arrow(ax, (x0 + 5, 45), (x0 + 5, 48.5), "#fdba74", 1.2)
    ax.text(30, 47, "H-EXT-01D  INHERITED REACTIVATION", color="#fdba74", fontsize=9, fontweight="bold")
    ax.text(30, 50.5, "distributed fault-localised extension — no single corridor", color=DIM, fontsize=7)
    ax.text(
        416,
        58,
        "preferred_hypothesis = null — chosen only after discriminating observations + sealed human decision",
        color=GOLD,
        fontsize=7.5,
        ha="center",
    )


# ── desktop (3 across) + mobile (3 stacked) ──────────────────────────────────
build(
    [(p1, "", ""), (p2, "", ""), (p3, "", "")],
    "SABAH — THE MISSING LINK · post-SCS extension (H-EXT-01)",
    str(HERE / "tri_panel_hext01.png"),
    19.5,
    8.2,
)
build(
    [(p1, "", ""), (p2, "", ""), (p3, "", "")],
    "SABAH — THE MISSING LINK · H-EXT-01",
    str(HERE / "tri_panel_hext01_mobile.png"),
    9.0,
    16.5,
)
