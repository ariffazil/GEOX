#!/usr/bin/env python3
"""
kinabalu_xs.py — Kinabalu Basin regional cross-section renderer (GEOX section skill v0.3)
Spine-driven labels (kinabalu_event_spine.yaml) so figure and framework cannot drift.
v0.3: legend handles fixed (no add_patch on Patch), valid hatch chars, computed VE formula fixed,
granite = sheeted laccolith w/ exposed summit sheet + feeder dyke (Cottam et al. 2010, JGS 167),
SRU "~8.5 Ma (Morley: 8.5–9)", footer "no volumetrics shown", Megah-1 neutral, unnamed transpression.
Usage: python3 kinabalu_xs.py dark|light
"""

import sys, os, numpy as np, matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Ellipse, FancyArrowPatch
from matplotlib.lines import Line2D
from scipy.ndimage import gaussian_filter1d

THEME = sys.argv[1] if len(sys.argv) > 1 else "dark"
OUT = "/root/GEOX/geox/skills/subsurface/section/output"
os.makedirs(OUT, exist_ok=True)
L_BMU, L_DRU, L_SRU, L_GR = "~24 Ma", "~13–12 Ma", "~8.5 Ma (Morley: 8.5–9)", "~7.85–7.22 Ma"

if THEME == "dark":
    BG = "#0b1220"
    FG = "#cbd5e1"
    GRID = "#1e293b"
    WATER = "#0c4a6e"
    CRUST = "#3b2f2a"
    SYN = "#6b5b45"
    POST = "#8a7a5c"
    ST4 = "#a08c68"
    WEDGE = "#6e564a"
    RAJ = "#5c4a6e"
    OPH = "#2f4f4f"
    MEL = "#4a5d33"
    TANJ = "#7c6a4f"
    SEB = "#96755a"
    CARB = "#2e7d6b"
    GR = "#a87878"
    SLAB = "#241c19"
    EDGE = "#94a3b8"
    HC_G = "#f87171"
    HC_O = "#4ade80"
    NOTE = "#64748b"
    FONT = "#e2e8f0"
    GRB = "#7a2e2e"
else:
    BG = "#ffffff"
    FG = "#1e293b"
    GRID = "#e2e8f0"
    WATER = "#7dd3fc"
    CRUST = "#c9b8a8"
    SYN = "#d9c9a3"
    POST = "#e7dab8"
    ST4 = "#eddfb5"
    WEDGE = "#d4b39c"
    RAJ = "#cabde0"
    OPH = "#9fc4c4"
    MEL = "#c2d19a"
    TANJ = "#e3d2ac"
    SEB = "#e6c8a8"
    CARB = "#8fd6c4"
    GR = "#e3b8b8"
    SLAB = "#b8a894"
    EDGE = "#475569"
    HC_G = "#dc2626"
    HC_O = "#16a34a"
    NOTE = "#64748b"
    FONT = "#0f172f" if False else "#0f172a"
    GRB = "#7a2e2e"

ST3 = "#4e5d55" if THEME == "dark" else "#c7d2ca"  # Stage III color
x = np.linspace(0, 600, 3001)


def pts(px, py):
    py = np.array(py, dtype=float)
    good = ~np.isnan(py)
    return np.interp(x, np.array(px)[good], py[good])


def smooth(v, s=15):
    return gaussian_filter1d(v, s)


def gauss(c, a, s):
    return a * np.exp(-((x - c) ** 2) / (2 * s * s))


def below(u, v):
    return np.minimum(u, v)


S = smooth(
    pts(
        [
            0, 60, 100, 140, 170, 191, 200, 218, 240, 260, 285, 320, 345, 352,
            360, 372, 390, 400, 412, 424, 436, 452, 470, 490, 510, 530, 548,
            562, 580, 600,
        ],
        [
            -1.5, -1.9, -1.5, -2.3, -2.7, -2.924,  # KL2 measured trough -2,924 m @ chainage 191.3 km of 523.7 km geodesic (≈ 219 of 600 schematic)
            -2.8, -2.9, -2.6, -2.1, -1.6, -1.1, -0.5, -0.15, 0.05, 0.25, 0.7,
            1.1, 4.095, 1.3, 0.8, 0.45, 0.3, 0.5, 0.35, 0.15, 0.0, -0.5, -1.0, -1.6,
        ],
    ),
    6,
)
S = np.where((x >= 104) & (x <= 120), 0.0, S)
S = S + (0.06 * np.sin(x / 3.1) + 0.05 * np.sin(x / 1.7)) * ((x > 352) & (x < 548))  # onshore only (QA D3)
S = np.where((x >= 404) & (x <= 420), np.maximum(S, 4.095 - 0.55 * np.abs(x - 412)), S)

BMU = pts([0, 80, 150, 220, 280, 330, 360, 380], [-4.0, -4.8, -5.6, -7.0, -8.8, -10.0, -11.6, -13.0])
DGt = pts([0, 80, 150, 220, 230], [-4.6, -5.5, -6.4, -7.9, -8.1])
saw = np.where(x < 230, 0.9 * np.where((np.floor(x / 32) % 2) == 0, 1, -1) * np.clip(1 - np.abs(((x % 32) - 16)) / 16, 0, 1), 0)
DG = below(smooth(DGt + smooth(saw, 4) * 0.8, 2), BMU - 0.5)
B = gauss(255, 0.5, 9) + gauss(280, 0.68, 9) + gauss(305, 0.5, 9) + gauss(328, 0.45, 8)
th = np.clip(np.interp(x, [160, 185, 340, 352], [0.0, 1.8, 0.5, 0.0]), 0, 2)
DRU = np.where((x >= 160) & (x <= 358), S - th + 1.45 * B, np.nan)
DRU = np.where(DRU < S - 0.05, DRU, S - 0.05)
st4 = (x >= 160) & (x <= 352) & (DRU < S - 0.05)
SRU = np.where(st4, S - 0.45 * (S - DRU) + 0.35 * B, np.nan)
OP = pts([340, 380, 420, 455, 490, 520, 560, 600], [-11.5, -9.5, -8.0, -6.0, -4.2, -5.0, -6.5, -8.0])
RJ = pts([300, 340, 380, 420, 440, 455], [-12.6, -10.5, -7.5, -4.5, -2.0, -0.6])
SBt = pts([535, 560, 600], [-1.0, -2.0, -4.5])
SBb = pts([535, 575, 600], [-2.5, -5.5, -7.5])

fig = plt.figure(figsize=(14.4, 9.2), dpi=300)
ax = fig.add_axes([0.035, 0.14, 0.93, 0.67])
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)


def band(lo, hi, color, m=None, hatch=None, z=3, ec=None):
    ax.fill_between(
        x,
        lo,
        hi,
        where=(~np.isnan(hi)) if m is None else m,
        color=color,
        hatch=hatch,
        lw=0,
        zorder=z,
        edgecolor=ec or EDGE,
        alpha=0.95 if hatch else 1.0,
    )


ax.fill_between(x, S, 0, where=S < 0, color=WATER, zorder=2, alpha=0.75)
band(BMU - 4, BMU, SLAB, m=x <= 380, z=2)
band(np.maximum(BMU, -13), OP, OPH, m=x >= 335, z=3, hatch="//")
band(DG, below(BMU - 0.9, S), SYN, m=x <= 230, z=3)
band(BMU, S, POST, m=x <= 250, z=3)
band(DRU, S, ST4, m=st4, z=4)
band(np.maximum(BMU, -13), DRU, ST3, m=(x >= 170) & (x <= 358), z=3, hatch="--")  # Stage III Setap/Temburong equiv.
band(np.maximum(BMU, -13), np.maximum(BMU, -13) + 0.9, WEDGE, m=(x >= 300) & (x <= 352), z=4, hatch="++")  # accreted pre-BMU slices
band(np.maximum(BMU, -13), RJ, RAJ, m=(x >= 300) & (x <= 455), z=3, hatch="xx")
band(OP, np.minimum(SBt, S), MEL, m=x >= 450, z=4, hatch="..")
for c, w in [(467, 15), (520, 15)]:
    floor = OP + gauss(c, 1.6, w / 2.2)
    band(floor, S, TANJ, m=(np.abs(x - c) < w), z=5)
band(SBb, S, SEB, m=x >= 532, z=5)
for k in range(1, 5):
    cf = S - (SBb - S) * 0.25 * k - gauss(600 - 18 * k, 0.4, 10)
    ax.plot(x[x >= 540], cf[x >= 540], color=EDGE, lw=0.4, zorder=6, alpha=0.6)
band(
    pts([546, 552, 560, 566], [-2.1, -2.2, -2.4, -2.5]),
    pts([546, 552, 560, 566], [-2.6, -2.7, -2.9, -3.0]),
    CARB,
    m=(x >= 546) & (x <= 566),
    z=7,
    hatch="o",
)
band(pts([100, 108, 116, 124], [-1.2, 0, 0, -1.0]), S, CARB, m=(x >= 100) & (x <= 124), z=6, hatch="o")


# ---- Kinabalu granite: sheeted laccolith (Cottam et al. 2010) — top sheet EXPOSED at summit, sheets young DOWNWARD
def lens(yc, hw, t, xc=413, z=8):
    env = np.sqrt(np.clip(1 - ((x - xc) / hw) ** 2, 0, 1)) ** 0.6
    m = (np.abs(x - xc) <= hw) & (yc + t * env < S + 0.02)
    ax.fill_between(x, yc - t * env, yc + t * env, where=m, facecolor=GR, hatch="..", edgecolor=GRB, lw=0.8, zorder=z)


lens(2.9, 9, 0.9)
lens(1.0, 12, 0.55)
lens(-1.0, 13, 0.5)
lens(-3.0, 14, 0.45)
lens(-5.0, 15, 0.4)
mtop = (x >= 403) & (x <= 423)
topsheet = 4.095 - 0.5 * np.abs(x - 413)
ax.fill_between(x, topsheet, S + 0.05, where=mtop & (S > topsheet), facecolor=GR, hatch="..", edgecolor=GRB, lw=0.8, zorder=8)
ax.fill_between(x, -9.0, 4.0, where=(x >= 412.3) & (x <= 413.7), facecolor=GR, edgecolor=GRB, lw=0.8, zorder=7)  # feeder dyke
ax.annotate("", xy=(429, -1.2), xytext=(429, -3.2), arrowprops=dict(arrowstyle="-|>", color=GRB, lw=1.0), zorder=12)
ax.text(430, -2.2, "sheets young\ndownward", fontsize=5.6, color=GRB, va="center", zorder=12)

ax.plot(x, BMU, color="#fbbf24", lw=1.3, ls=(0, (6, 2)), zorder=9)
ax.plot(x, DRU, color="#fbbf24", lw=1.3, zorder=9)
ax.plot(x, SRU, color="#f87171", lw=1.1, ls=(0, (4, 2)), zorder=9)

for toe, crest in [(244, 255), (268, 280), (294, 305), (317, 328)]:
    t = np.linspace(0, 1, 40)
    fx = toe + (crest - toe) * t**0.75
    fy = np.interp(toe, x, BMU) + (np.interp(crest, x, S) - np.interp(toe, x, BMU)) * t**1.7
    ax.plot(fx, fy, color="#fdba74", lw=1.0, zorder=9)
for fx0, fx1 in [(300, 312), (322, 334), (342, 352)]:
    t = np.linspace(0, 1, 30)
    ax.plot(
        fx0 + (fx1 - fx0) * t**0.75,
        np.interp(fx0, x, S) - 3.5 * t + (np.interp(fx1, x, S) - np.interp(fx0, x, S) + 3.5) * t**1.7,
        color="#fdba74",
        lw=0.8,
        zorder=9,
    )
for fx0 in (330, 344):
    t = np.linspace(0, 1, 30)
    ax.plot(
        fx0 + 2.5 * t,
        np.interp(fx0, x, S) + (np.interp(fx0 + 6, x, BMU) - np.interp(fx0, x, S)) * t**1.5,
        color="#93c5fd",
        lw=0.7,
        zorder=9,
    )

band(BMU - 1.3, BMU - 0.15, CARB, m=(x >= 84) & (x <= 98), z=6, hatch="o")  # Tepat-1 Olig. carbonate buildup
for cx, cy, c in [(90, -5.45, HC_G), (90, -5.05, HC_O)]: ax.add_patch(Ellipse((cx, cy), 4.5, 0.4, facecolor=c, alpha=0.85, zorder=11, edgecolor="none"))
wells = [("Tepat-1", 90, -5.6, 1.1), ("Well B", 255, -4.6, 1.1), ("Well A", 280, -5.2, 1.0), ("Well D", 288, -8.8, 2.3)]  # dossier v2 convention; staggered labels (QA D2)
for name, wx, td, yoff in wells:
    ax.plot([wx, wx], [np.interp(wx, x, S), td], color=FG, lw=1.1, zorder=10)
    ax.plot(wx, np.interp(wx, x, S), marker="^", ms=5, color=FG, zorder=10)
    ax.annotate(name, (wx, np.interp(wx, x, S)), xytext=(wx, np.interp(wx, x, S) + yoff), fontsize=6.5, color=FG, ha="center")
for cx in (305, 328):
    ax.plot(cx, np.interp(cx, x, S) - 0.5, marker="o", ms=4, mfc="none", mec=NOTE, mew=0.8, ls="dashed", zorder=10)
ax.text(317, np.interp(317, x, S) - 1.4, "undrilled closures (schematic)", fontsize=5.5, color=NOTE, ha="center")
ax.text(90, np.interp(90, x, S) + 1.85, "gas + oil rim - Olig. carbonate", fontsize=5.2, color=NOTE, ha="center")
for cx, cy, c in [(280, -4.4, HC_G), (280, -4.0, HC_O), (255, -4.2, HC_G)]:
    ax.add_patch(Ellipse((cx, cy), 5, 0.45, facecolor=c, alpha=0.85, zorder=11, edgecolor="none"))

ax.add_patch(FancyArrowPatch((150, -6.0), (210, -7.6), arrowstyle="-|>", mutation_scale=9, color="#fbbf24", lw=1.2, zorder=12))
ax.text(178, -6.35, "underthrust Dangerous Grounds crust", fontsize=6, color="#fbbf24", rotation=-14)
ax.add_patch(FancyArrowPatch((330, -0.8), (360, -0.8), arrowstyle="-|>", mutation_scale=8, color=EDGE, lw=0.9, zorder=12))
ax.text(345, -1.15, "sediment supply →", fontsize=5.5, color=EDGE, ha="center")
ax.plot([452, 452], [-9, np.interp(452, x, S)], color=EDGE, lw=1.1, ls=(0, (5, 3)), zorder=8.5)
ax.text(452, 1.0, "Late Pliocene–Recent\ntranspression", fontsize=5.6, color=EDGE, ha="center")


def utag(wx, txt, col):
    ax.text(wx, np.interp(wx, x, BMU) + 0.35, txt, fontsize=6.2, color=col, style="italic")


utag(40, f"BMU {L_BMU}", "#fbbf24")
ax.text(163, -2.5, "RU (approx DRU?)", fontsize=5.6, color="#fbbf24", style="italic")
ax.text(166, np.nanmin(DRU) - 0.5, f"DRU {L_DRU} · composite surface", fontsize=6.2, color="#fbbf24", style="italic")
ax.text(196, -1.55, f"SRU {L_SRU}", fontsize=5.8, color="#f87171", style="italic", ha="center")  # moved: was colliding w/ Well B (QA D1)
ax.text(
    424,
    -6.6,
    f"Kinabalu granite {L_GR}\nsheeted laccolith (Cottam et al. 2010, JGS 167)",
    fontsize=5.8,
    color="#fda4af",
    ha="center",
)
for lx, txt in [
    (80, "Dangerous Grounds"),
    (185, "Sabah Trough"),
    (290, "Kinabalu fold-thrust\nbelt (W-vergent)"),
    (395, "Crocker Range\n· Mt Kinabalu 4,095 m"),
    (490, "Central Sabah\nmélange + Tanjong basins"),
    (570, "Sandakan →\nSulu Sea"),
]:
    ax.text(lx, 3.6, txt, fontsize=6.4, color=FONT, ha="center", weight="bold")

ax.set_xlim(0, 600)
ax.set_ylim(-12.5, 4.6)
ax.set_xlabel("distance along transect, NW → SE (km, schematic)", fontsize=7, color=FG)
ax.set_ylabel("elevation (km)", fontsize=7, color=FG)
ax.tick_params(colors=FG, labelsize=6)
ax.grid(axis="y", color=GRID, lw=0.4)
for sp in ax.spines.values():
    sp.set_color(GRID)
ax.plot([500, 550], [-11.8, -11.8], color=FG, lw=1.2)
ax.text(525, -11.45, "50 km", fontsize=6, color=FG, ha="center")

w_in = fig.get_size_inches()[0] * 0.93
h_in = fig.get_size_inches()[1] * 0.67
ve = round((600 / w_in) / ((12.5 + 4.6) / h_in), 1)  # (km per inch H)/(km per inch V)
fig.text(0.035, 0.965, "KINABALU BASIN — NW→SE REGIONAL CROSS-SECTION · NW BORNEO", fontsize=11, color=FONT, weight="bold")
fig.text(
    0.035,
    0.935,
    f"Schematic — not seismic picks · no volumetrics shown · ages from GEOX event spine v0.1 · BMU {L_BMU} (Lunt 2022, BGSM 74) · DRU {L_DRU} · SRU {L_SRU} · vertical exaggeration ≈ {ve}× · seafloor: KL2 measured (GEBCO_2019 15″ Rutgers THREDDS) · Tepat-1 + Wells A/B/D per dossier v2",
    fontsize=6.3,
    color=NOTE,
)

leg_items = [
    ("post-rift / Stage IV", POST, None),
    ("syn-rift", SYN, None),
    ("Stage III (Setap/Temburong)", ST3, "--"), ("accreted pre-BMU slices", WEDGE, "++"),
    ("Rajang/Crocker", RAJ, "xx"),
    ("ophiolite", OPH, "//"),
    ("mélange", MEL, ".."),
    ("carbonate", CARB, "o"),
    ("granite sheets", GR, ".."),
]
handles = [Patch(fc=c, ec=EDGE, lw=0.4, hatch=h) for _, c, h in leg_items]
handles += [Line2D([], [], color="#fbbf24", lw=1.3, ls=(0, (6, 2))), Line2D([], [], color="#f87171", lw=1.1, ls=(0, (4, 2)))]
labels = [n for n, _, _ in leg_items] + [f"BMU/DRU (BMU {L_BMU}, DRU {L_DRU})", f"SRU {L_SRU}"]
axl = fig.add_axes((0.035, 0.015, 0.55, 0.105))
axl.axis("off")
axl.legend(handles=handles, labels=labels, loc="center", ncol=3, fontsize=5.6, frameon=False, labelcolor=FG)
axr = fig.add_axes((0.62, 0.015, 0.35, 0.105))
axr.axis("off")
axr.text(
    0,
    0.5,
    "EVENTS (spine v0.1): BMU ~24 Ma collision onset · DRU ~13–12 Ma composite surface (Morley et al. 2023) · "
    "SRU ~8.5 Ma canopy-basin fill top (N Sabah only) · granite ~7.85–7.22 Ma, <800 ka, post-SRU · "
    "Plio–Recent transpression (unnamed) · NSPW phases apply to N Sabah only · "
    "DRU = SABAR provisional (per-well DRU dating test T12 = falsifier)",
    fontsize=5.0,
    color=FG,
    va="center",
    wrap=True,
)

fig.savefig(f"{OUT}/kinabalu_xs_{THEME}.png", facecolor=BG)
fig.savefig(f"{OUT}/kinabalu_xs_{THEME}.svg", facecolor=BG)
if THEME == "light":
    fig.savefig(f"{OUT}/kinabalu_xs_light.pdf", facecolor=BG)
print(f"{THEME} rendered · VE≈{ve}×")
