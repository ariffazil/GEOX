#!/usr/bin/env python3
"""
asas_malam_xs.py — Kinabalu / NW Sabah section, ASAS-MALAM public version (v1.0)
Architecture: THREE BLOCKS · TWO MARGINS
  BLOCK 1  Dangerous Grounds — attenuated continental LOWER PLATE (rifted passive margin = MARGIN 1, dead)
  SUTURE   Sabah Trough — flexural moat over the BENT-DOWN DG edge + lower-plate BENDING EXTENSION (outer-rise analog)
  BLOCK 2  Borneo / Crocker-Rajang — accreted UPPER PLATE (jammed convergent margin = MARGIN 2)
  Layang-Layang basin = Block 1's bent-down margin-edge basin. Kinabalu belt = Block 2's leading-edge wedge-top.
Physics annotations: flexure Te fit, load+downdrag (not sag alone), wedge taper, bending-extension predictions.
Evidence tiers: L0 measured (green line, public well) · L1 calculated/dated (granite, Moho) · L2 interpreted (dashed).
Spine-driven ages. Public sources only. Usage: python3 asas_malam_xs.py dark|light
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
if THEME == "dark":
    BG = "#0b1220"
    FG = "#cbd5e1"
    GRID = "#1e293b"
    WATER = "#0c4a6e"
    MANT = "#3a2f45"
    LC = "#3b3a44"
    BASE = "#4a4038"
    SYN = "#6b5b45"
    POST = "#8a7a5c"
    CARB = "#2e7d6b"
    S3 = "#4e5d55"
    ST4 = "#a08c68"
    CRO = "#5c4a6e"
    OPH = "#2f4f4f"
    MEL = "#4a5d33"
    TANJ = "#7c6a4f"
    SEB = "#96755a"
    GR = "#a87878"
    GRB = "#7a2e2e"
    EDGE = "#94a3b8"
    NOTE = "#64748b"
    FONT = "#e2e8f0"
    L0 = "#39d353"
    FLEX = "#fbbf24"
else:
    BG = "#ffffff"
    FG = "#1e293b"
    GRID = "#e2e8f0"
    WATER = "#7dd3fc"
    MANT = "#d8cfe0"
    LC = "#c9c6cf"
    BASE = "#c9b8a8"
    SYN = "#d9c9a3"
    POST = "#e7dab8"
    CARB = "#8fd6c4"
    S3 = "#c7d2ca"
    ST4 = "#eddfb5"
    CRO = "#cabde0"
    OPH = "#9fc4c4"
    MEL = "#c2d19a"
    TANJ = "#e3d2ac"
    SEB = "#e6c8a8"
    GR = "#e3b8b8"
    GRB = "#7a2e2e"
    EDGE = "#475569"
    NOTE = "#64748b"
    FONT = "#0f172a"
    L0 = "#1b5e20"
    FLEX = "#b45309"

x = np.linspace(0, 600, 3001)


def P(px, py):
    return np.interp(x, np.array(px, float), np.array(py, float))


def sm(v, s=15):
    return gaussian_filter1d(v, s)


def g(c, a, s):
    return a * np.exp(-((x - c) ** 2) / (2 * s * s))


# ---- topography/bathymetry (L0 anchor values: summit 4095 m, trough ~2.9 km) ----
S = sm(
    P(
        [
            0,
            60,
            100,
            140,
            170,
            200,
            218,
            240,
            260,
            285,
            320,
            345,
            352,
            360,
            372,
            390,
            400,
            412,
            424,
            436,
            452,
            470,
            490,
            510,
            530,
            548,
            562,
            580,
            600,
        ],
        [
            -1.5,
            -1.9,
            -1.5,
            -2.3,
            -2.6,
            -2.8,
            -2.9,
            -2.6,
            -2.1,
            -1.6,
            -1.1,
            -0.5,
            -0.15,
            0.05,
            0.25,
            0.7,
            1.1,
            4.095,
            1.3,
            0.8,
            0.45,
            0.3,
            0.5,
            0.35,
            0.15,
            0.0,
            -0.5,
            -1.0,
            -1.6,
        ],
    ),
    6,
)
S = np.where((x >= 104) & (x <= 120), 0.0, S)
S = S + (0.06 * np.sin(x / 3.1) + 0.05 * np.sin(x / 1.7)) * ((x > 352) & (x < 548))
S = np.where((x >= 404) & (x <= 420), np.maximum(S, 4.095 - 0.55 * np.abs(x - 412)), S)

# ---- lower-plate flexure: DG edge bends down under wedge load + underthrust downdrag ----
bend = np.where(x > 170, -(((x - 170) / 160.0) ** 2) * 5.2, 0.0)  # downdrag envelope (L2)
foreb = g(95, 0.35, 30)  # forebulge? (L2 — test on 3D)
BSM = sm(P([0, 80, 150, 220, 280, 330, 360, 380], [-4.6, -5.4, -6.0, -8.2, -9.8, -11.2, -12.6, -13.5]) + bend, 8)  # DG basement
BU = sm(
    P([0, 80, 150, 220, 280, 330, 352, 370], [-4.0, -4.8, -5.5, -7.4, -8.8, -10.2, -11.4, -12.6]) + bend, 8
)  # breakup unconf.
BU = BU - foreb * 0.4
BSM = BSM - foreb * 0.5
saw = np.where(x < 230, 0.8 * np.where((np.floor(x / 32) % 2) == 0, 1, -1) * np.clip(1 - np.abs(((x % 32) - 16)) / 16, 0, 1), 0)
DG = np.minimum(sm(BSM + sm(saw, 4) * 0.7, 2), BU - 0.4)

# ---- wedge / belt surfaces ----
B = g(255, 0.5, 9) + g(280, 0.68, 9) + g(305, 0.5, 9) + g(328, 0.45, 8)
th = np.clip(np.interp(x, [160, 185, 340, 352], [0.0, 1.8, 0.5, 0.0]), 0, 2)
DRU = np.where((x >= 160) & (x <= 358), S - th + 1.45 * B, np.nan)
DRU = np.where(DRU < S - 0.05, DRU, S - 0.05)
st4 = (x >= 160) & (x <= 352) & (DRU < S - 0.05)
SRU = np.where(st4, S - 0.45 * (S - DRU) + 0.35 * B, np.nan)
OP = sm(P([340, 380, 420, 455, 490, 520, 560, 600], [-11.5, -9.5, -8.0, -6.0, -4.2, -5.0, -6.5, -8.0]), 8)
RJ = sm(P([300, 340, 380, 420, 440, 455], [-12.6, -10.5, -7.5, -4.5, -2.0, -0.6]), 8)
SBt = sm(P([535, 560, 600], [-1.0, -2.0, -4.5]), 6)
SBb = sm(P([535, 575, 600], [-2.5, -5.5, -7.5]), 6)

# ---- Panel A lithosphere ----
moho = P([0, 150, 250, 330, 420, 520, 600], [-26, -27, -30, -33, -33, -31, -28])
fig = plt.figure(figsize=(20, 14.5), dpi=200)
fig.patch.set_facecolor(BG)
axA = fig.add_axes((0.045, 0.795, 0.93, 0.115))
axA.set_facecolor(BG)
sedtop = np.where(x < 352, np.minimum(BU, S), np.minimum(S - 0.05, 0.0))
axA.fill_between(x, -45, moho, color=MANT, zorder=1)
axA.fill_between(x, moho, sedtop, color=LC, zorder=2)
axA.fill_between(x, sedtop, S, color=ST4, zorder=3)
axA.fill_between(x, S, 0, where=S < 0, color=WATER, zorder=4, alpha=0.8)
axA.plot(x, moho, color="#f87171", lw=1.0, ls=(0, (6, 3)), zorder=6)
axA.plot(x, S, color=L0, lw=1.6, zorder=6)
axA.text(
    30,
    -23,
    "Moho 26–33 km · gravity/magnetic model, non-unique (Sidek et al. 2016) · L1",
    fontsize=7.5,
    color="#f87171",
    zorder=7,
)
axA.text(30, -6.5, "BLOCK 1 · thinned continental lower plate (Steuer et al. 2012)", fontsize=7.5, color="white", zorder=7)
axA.text(215, -19.5, "SUTURE · underthrust bend", fontsize=7.5, color="white", zorder=7)
axA.text(430, -12, "BLOCK 2 · upper-plate crust + ophiolite", fontsize=7.5, color="white", zorder=7)
axA.text(300, -40, "mantle", fontsize=8, color="white", zorder=7)
axA.annotate("", xy=(168, -12.5), xytext=(120, -6.2), arrowprops=dict(arrowstyle="-|>", color=FLEX, lw=1.6), zorder=8)
axA.text(96, -13.8, "plate bends & jams here (~16–15 Ma)", fontsize=7.2, color=FLEX, zorder=8)
axA.set_xlim(0, 600)
axA.set_ylim(-45, 4)
axA.set_aspect("equal")
axA.set_xticks([])
axA.set_yticks([0, -20, -40])
axA.tick_params(colors=NOTE, labelsize=7)
axA.set_title(
    "A · TRUE SCALE 1:1 — the whole basin system is a thin skin on a ~30 km crust: THREE BLOCKS, TWO MARGINS",
    loc="left",
    fontsize=11.5,
    weight="bold",
    color=FONT,
    pad=6,
)

# ---- Panel B sediment section ----
ax = fig.add_axes((0.045, 0.335, 0.93, 0.44))
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
band(BU - 4, BU, LC, m=x <= 380, z=2)
band(np.maximum(BSM, -13), OP, OPH, m=x >= 335, z=3, hatch="//")
band(DG, np.minimum(BU - 0.9, S), SYN, m=x <= 230, z=3)
band(BU, S, POST, m=x <= 250, z=3)
band(DRU, S, ST4, m=st4, z=4)
band(np.maximum(BU, -13), DRU, S3, m=(x >= 170) & (x <= 358), z=3, hatch="--")
band(np.maximum(BU, -13), np.maximum(BU, -13) + 0.9, "#6e564a", m=(x >= 300) & (x <= 352), z=4, hatch="++")
band(np.maximum(BU, -13), RJ, CRO, m=(x >= 300) & (x <= 455), z=3, hatch="xx")
band(OP, np.minimum(SBt, S), MEL, m=x >= 450, z=4, hatch="..")
for c, w in [(467, 15), (520, 15)]:
    band(OP + g(c, 1.6, w / 2.2), S, TANJ, m=(np.abs(x - c) < w), z=5)
band(SBb, S, SEB, m=x >= 532, z=5)
band(
    pts_a := P([546, 552, 560, 566], [-2.1, -2.2, -2.4, -2.5]),
    P([546, 552, 560, 566], [-2.6, -2.7, -2.9, -3.0]),
    CARB,
    m=(x >= 546) & (x <= 566),
    z=7,
    hatch="o",
)
band(P([100, 108, 116, 124], [-1.2, 0, 0, -1.0]), S, CARB, m=(x >= 100) & (x <= 124), z=6, hatch="o")
band(BU - 1.3, BU - 0.15, CARB, m=(x >= 80) & (x <= 98), z=6, hatch="o")


# granite sheets (L1 age, L2 shape)
def lens(yc, hw, t, xc=413, z=8):
    env = np.sqrt(np.clip(1 - ((x - xc) / hw) ** 2, 0, 1)) ** 0.6
    m = (np.abs(x - xc) <= hw) & (yc + t * env < S + 0.02)
    ax.fill_between(x, yc - t * env, yc + t * env, where=m, facecolor=GR, hatch="..", edgecolor=GRB, lw=0.8, zorder=z)


lens(2.9, 9, 0.9)
lens(1.0, 12, 0.55)
lens(-1.0, 13, 0.5)
lens(-3.0, 14, 0.45)
lens(-5.0, 15, 0.4)
mt = (x >= 403) & (x <= 423)
ts = 4.095 - 0.5 * np.abs(x - 413)
ax.fill_between(x, ts, S + 0.05, where=mt & (S > ts), facecolor=GR, hatch="..", edgecolor=GRB, lw=0.8, zorder=8)
ax.fill_between(x, -9.0, 4.0, where=(x >= 412.3) & (x <= 413.7), facecolor=GR, edgecolor=GRB, lw=0.8, zorder=7)

# unconformities — all L2 dashed
ax.plot(x, BU, color="#f87171", lw=1.6, ls=(0, (7, 3)), zorder=9)
ax.plot(x, DRU, color="#fbbf24", lw=1.6, ls=(0, (7, 3)), zorder=9)
ax.plot(x, SRU, color="#fde047", lw=1.2, ls=(0, (5, 2)), zorder=9)
ax.plot(x, S, color=L0, lw=1.8, zorder=10)

# thrusts
for toe, crest in [(244, 255), (268, 280), (294, 305), (317, 328)]:
    t = np.linspace(0, 1, 40)
    fx = toe + (crest - toe) * t**0.75
    fy = np.interp(toe, x, BU) + (np.interp(crest, x, S) - np.interp(toe, x, BU)) * t**1.7
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
# BENDING EXTENSION on the lower plate, outer edge of the moat (outer-rise analog) — physics core of this version
for xf, dip in [(150, 1.8), (162, 2.4), (178, 2.0)]:
    ytop = np.interp(xf, x, BU)
    ybot = np.interp(xf + 4, x, BSM) - 0.4
    ax.plot([xf, xf + dip], [ytop, ybot], color="#60a5fa", lw=1.5, zorder=9)
    ax.plot([xf, xf - dip * 0.3], [ytop, ybot * 0.985], color="#60a5fa", lw=0.8, zorder=9)
ax.annotate(
    "lower-plate BENDING EXTENSION\n(outer-rise analog) — physics-allowed,\nNO spreading required",
    xy=(158, np.interp(158, x, BU)),
    xytext=(46, -1.85),
    fontsize=7.2,
    color="#60a5fa",
    zorder=12,
    arrowprops=dict(arrowstyle="->", color="#60a5fa", lw=1.0),
)
ax.annotate(
    "forebulge? · L2 untested\n(measure on 3D → fixes Te)",
    xy=(95, np.interp(95, x, BU)),
    xytext=(28, -2.6),
    fontsize=6.8,
    color=FLEX,
    zorder=12,
    arrowprops=dict(arrowstyle="->", color=FLEX, lw=0.9),
)
# underthrust arrow
ax.add_patch(FancyArrowPatch((150, -7.2), (210, -9.4), arrowstyle="-|>", mutation_scale=10, color=FLEX, lw=1.4, zorder=12))
ax.text(168, -7.7, "underthrust DG crust + load → moat", fontsize=6.8, color=FLEX, rotation=-13)

# wells: public only
ax.plot([88, 88], [np.interp(88, x, S), -5.4], color=FG, lw=1.2, zorder=10)
ax.plot(88, np.interp(88, x, S), marker="^", ms=5, color=FG, zorder=10)
ax.text(
    88,
    np.interp(88, x, S) + 1.2,
    "Tepat-1 · L0\n(gas + oil rim · Olig. carbonate — public record)",
    fontsize=6.4,
    color=FG,
    ha="center",
    zorder=12,
)
for cx in (305, 328):
    ax.plot(cx, np.interp(cx, x, S) - 0.5, marker="o", ms=4, mfc="none", mec=NOTE, mew=0.8, zorder=10)
ax.text(317, np.interp(317, x, S) - 1.5, "undrilled closures (schematic) · L2", fontsize=5.5, color=NOTE, ha="center")


# surface labels
def utag(wx, txt, col):
    ax.text(wx, np.interp(wx, x, BU) + 0.35, txt, fontsize=6.4, color=col, style="italic")


utag(18, "BU / BMU ~24 Ma · L2", "#f87171")
ax.text(196, np.nanmin(DRU) - 0.5, "DRU ~13–12 Ma · L2 (composite surface)", fontsize=6.4, color="#fbbf24", style="italic")
ax.text(222, -1.35, "SRU ~8.5–9 Ma · L2", fontsize=6.2, color="#fde047", style="italic", ha="center")
ax.text(
    426,
    -6.9,
    "Kinabalu granite 7.85–7.22 Ma · L1 age, L2 shape\nsheeted laccolith (Cottam et al. 2010)",
    fontsize=6.4,
    color="#fda4af",
    ha="center",
)
ax.text(163, -2.9, "RU (≈DRU?) · L2", fontsize=5.8, color="#fbbf24", style="italic")

# ---- three blocks / two margins band (the organizing architecture) ----
bb = fig.add_axes((0.045, 0.845, 0.93, 0.03))
bb.set_xlim(0, 600)
bb.set_ylim(0, 1)
bb.axis("off")


def block(a, b, txt, col, dashed=False, fs=7.6):
    bb.plot([a, a, b, b], [0.05, 0.95, 0.95, 0.05], color=col, lw=1.4, ls=(0, (4, 2)) if dashed else "-", zorder=3)
    bb.text((a + b) / 2, 0.5, txt, ha="center", va="center", fontsize=fs, color=col, weight="bold", zorder=4)


block(2, 168, "BLOCK 1 · DANGEROUS GROUNDS\nlower plate · rifted passive MARGIN 1 (dead)", "#60a5fa")
block(168, 242, "SUTURE · SABAH TROUGH\nflexural moat · underthrust bend\n· bending extension", FLEX, dashed=True, fs=6.4)
block(240, 600, "BLOCK 2 · BORNEO UPPER PLATE\njammed convergent MARGIN 2 · wedge + fold-thrust belt + Crocker", "#fdba74")
bb.annotate("", xy=(150, 1.25), xytext=(110, 1.25), arrowprops=dict(arrowstyle="<->", color="#60a5fa", lw=1.2))
bb.text(130, 1.42, "Layang-Layang basin = Block 1's bent-down margin-edge", fontsize=6.8, color="#60a5fa", ha="center")
bb.annotate("", xy=(300, 1.25), xytext=(240, 1.25), arrowprops=dict(arrowstyle="<->", color="#fdba74", lw=1.2))
bb.text(270, 1.42, "Kinabalu belt = Block 2 leading edge", fontsize=6.8, color="#fdba74", ha="center")
bb.text(
    300,
    -0.35,
    "NOT three basins — TWO plates and ONE suture. Two margins: passive (M1, died with breakup) and convergent (M2, jammed ~16–15 Ma).",
    fontsize=7.2,
    color=FONT,
    ha="center",
)

# province sub-labels on Panel B
for lx, txt in [
    (85, "platform + trough-fill"),
    (200, "Sabah Trough ~2.9 km"),
    (288, "Kinabalu fold-thrust\nbelt · W-vergent, taper ~4°"),
    (395, "Crocker Range\n· Mt Kinabalu 4,095 m"),
    (492, "Central Sabah mélange\n+ Tanjong basins"),
    (570, "Sandakan → Sulu"),
]:
    ax.text(lx, 3.55, txt, fontsize=6.6, color=FONT, ha="center", weight="bold")
ax.text(
    300,
    2.75,
    "NSPW / mud canopy: N Sabah only (Morley et al. 2023) — not on this transect",
    fontsize=6.8,
    style="italic",
    color="#7dd3fc" if THEME == "dark" else "#0369a1",
    ha="center",
)
ax.set_xlim(0, 600)
ax.set_ylim(-13.5, 4.6)
ax.set_xlabel("distance NW → SE (km, schematic)", fontsize=8, color=FG)
ax.set_ylabel("elevation (km)", fontsize=8, color=FG)
ax.tick_params(colors=FG, labelsize=7)
ax.grid(axis="y", color=GRID, lw=0.4)
for sp in ax.spines.values():
    sp.set_color(GRID)
w_in = 20 * 0.93
h_in = 14.5 * 0.44
ve = round((600 / w_in) / ((13.5 + 4.6) / h_in), 1)
ax.set_title(
    f"B · SEDIMENT SECTION · VE ≈ {ve}× — geometry schematic (L2); horizons placed by published ages, not seismic picks",
    loc="left",
    fontsize=10.5,
    weight="bold",
    color=FONT,
    pad=4,
)

# ---- physics check panel ----
fx = fig.add_axes((0.045, 0.085, 0.27, 0.175))
fx.set_facecolor(BG)
Te = np.linspace(3, 35, 200)
Ey, nu_, g_ = 70e9, 0.25, 9.81
for rf, ls_, lab_ in [(2400, "-", "sediment infill"), (1030, ":", "water infill")]:
    a = (4 * Ey * (Te * 1e3) ** 3 / (12 * (1 - nu_**2)) / ((3300 - rf) * g_)) ** 0.25 / 1e3
    fx.plot(Te, np.pi * a, color=FLEX, ls=ls_, lw=1.5, label=f"continuous · {lab_}")
    fx.plot(Te, 0.75 * np.pi * a, color="#4fa3d9", ls=ls_, lw=1.5, label=f"broken · {lab_}")
fx.axhspan(110, 150, color=NOTE, alpha=0.18)
fx.text(34, 156, "load-front→DG-high distance on THIS sketch ≈110–150 km (L2, not measured)", fontsize=5.8, color=FG, ha="right")
fx.set_xlabel("elastic thickness Te (km)", fontsize=7, color=NOTE)
fx.set_ylabel("forebulge distance (km)", fontsize=7, color=NOTE)
fx.tick_params(labelsize=6, colors=NOTE)
fx.set_ylim(0, 320)
fx.set_xlim(3, 35)
fx.grid(False)
for sp in ["top", "right"]:
    fx.spines[sp].set_visible(False)
fx.legend(fontsize=5.6, frameon=False, labelcolor=FG)
fx.set_title("PHYSICS CHECK · flexure", fontsize=8.5, weight="bold", color=FONT, loc="left")
fig.text(
    0.045,
    0.028,
    "Te ≈ 8–17 km fits a 110–150 km load distance — consistent with weak rifted lower plate.\n"
    "BUT 2.9 km of moat relief needs sediment load PLUS underthrust downdrag — a pure sag cannot do it.\n"
    "Extension at the Trough = lower-plate bending (outer-rise analog) + up-dip gravity collapse — NO spreading (5-vector falsification 2026-09-30).",
    fontsize=6.6,
    color=NOTE,
)

# ---- legend ----
lg = fig.add_axes((0.345, 0.085, 0.28, 0.175))
lg.axis("off")
items = [
    ("post-rift / Stage IV", POST, None),
    ("syn-rift", SYN, None),
    ("Stage III (Setap/Temburong)", S3, "--"),
    ("accreted pre-BMU slices", "#6e564a", "++"),
    ("Rajang/Crocker", CRO, "xx"),
    ("ophiolite", OPH, "//"),
    ("mélange", MEL, ".."),
    ("carbonate", CARB, "o"),
    ("granite sheets", GR, ".."),
    ("lower/upper crust", LC, None),
]
h = [Patch(fc=c, ec=EDGE, lw=0.4, hatch=ht) for _, c, ht in items] + [
    Line2D([], [], color=L0, lw=1.8, label="topography/bathymetry · L0"),
    Line2D([], [], color="#f87171", lw=1.6, ls=(0, (7, 3)), label="BU/BMU ~24 Ma · L2"),
    Line2D([], [], color="#fbbf24", lw=1.6, ls=(0, (7, 3)), label="DRU ~13–12 Ma · L2"),
    Line2D([], [], color="#fde047", lw=1.2, ls=(0, (5, 2)), label="SRU ~8.5–9 Ma · L2"),
    Line2D([], [], color="#60a5fa", lw=1.5, label="bending-extension fault (predicted)"),
    Line2D([], [], color="#fdba74", lw=1.2, label="thrust (W-vergent)"),
]
lg.legend(
    handles=h,
    labels=[n for n, _, _ in items]
    + [
        "topography/bathymetry · L0",
        "BU/BMU ~24 Ma · L2",
        "DRU ~13–12 Ma · L2",
        "SRU ~8.5–9 Ma · L2",
        "bending-extension fault (predicted)",
        "thrust (W-vergent)",
    ],
    loc="upper left",
    ncol=2,
    fontsize=5.9,
    frameon=False,
    labelcolor=FG,
    title="EVIDENCE-TIERED LEGEND · every body = L2",
    title_fontproperties={"weight": "bold", "size": 7.5},
)
lg.get_legend().get_title().set_color(FG)

# ---- what-is-measured panel ----
ev = fig.add_axes((0.655, 0.085, 0.32, 0.175))
ev.axis("off")
ev.text(0, 1.0, "MEASURED vs MODELLED", fontsize=8.5, weight="bold", color=FONT, va="top")
rows = [
    ("L0", "#1b5e20", "Topography, bathymetry, Tepat-1 public result"),
    ("L1", "#c0392b", "Granite U-Pb 7.85–7.22 Ma · Moho 26–33 km (non-unique) · flexure curves (this figure)"),
    ("L2", "#b45309", "Every surface, body, fault, closure — depths uncalibrated (no velocity model)"),
    ("L2", "#b45309", "Bending-extension faults: PREDICTED here — verify soles + strike ∥ trough on 3D"),
    ("L2", "#b45309", "Forebulge position: untested — measuring it fixes Te"),
]
for k, (t, c, d) in enumerate(rows):
    yy = 0.80 - k * 0.155
    ev.text(0, yy, t, fontsize=7.5, weight="bold", color="white", va="top", bbox=dict(boxstyle="round,pad=0.2", fc=c, ec="none"))
    ev.text(0.075, yy, d, fontsize=6.6, color=FG, va="top")

fig.text(0.045, 0.975, "KINABALU — NW SABAH SECTION · ASAS-MALAM PUBLIC v1.0", fontsize=16, weight="bold", color=FONT)
fig.text(
    0.045,
    0.952,
    "Three blocks · two margins · one suture — ages from GEOX event spine v0.1 · public sources only · internal well data excluded",
    fontsize=9.5,
    color=NOTE,
)
fig.text(
    0.985, 0.975, "Φ GEOX · L0 measured · L1 calculated · L2 interpreted", fontsize=9, color="#fbbf24", ha="right", weight="bold"
)
fig.text(0.985, 0.952, "Not seismic picks (F7) · no volumetrics", fontsize=7.5, color=NOTE, ha="right")
fig.text(
    0.045,
    0.008,
    "Sources: Lunt 2022 (BGSM 74) · Morley et al. 2023 · Das et al. 2024 · Cottam et al. 2010 · Sidek et al. 2016 · Steuer et al. 2012 · Tan & Lamy 1990 · S&P 2022 (Tepat-1) · flexure: E=70 GPa, ν=0.25, ρ=3300. arif-fazil.com/earth · DITEMPA BUKAN DIBERI",
    fontsize=6.2,
    color=NOTE,
)

fig.savefig(f"{OUT}/asas_malam_xs_{THEME}.png", facecolor=BG)
if THEME == "dark":
    fig.savefig(f"{OUT}/asas_malam_xs.svg", facecolor=BG)
else:
    fig.savefig(f"{OUT}/asas_malam_xs_print.pdf", facecolor=BG)
print(f"{THEME} done · VE≈{ve}×")
