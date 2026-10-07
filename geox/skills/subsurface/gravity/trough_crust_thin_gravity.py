#!/usr/bin/env python3
"""
trough_crust_thin_gravity.py — forward Bouguer model for the TROUGH-CRUST-THIN hypothesis
(GEOX subsurface/gravity skill v0.1 · PUBLIC LANE · F13 sovereign hypothesis 2026-10-07)

Purpose: answer the ONE question that decides whether falsifier F1 is worth running —
   how thin must the Sabah Trough crust be for free satellite gravity to detect it?

Why this exists: geophysics_studio_screen.py:44 registers "oceanic crust / density
inversion not modelled" as a GEOX capability gap. This is the forward half of that gap.
It does NOT invert; it predicts, so the prediction can be compared to a public grid
(Sandwell-Smith / WGM2012) along B-B' without touching any internal data.

Method: 2D line-mass (Talwani-style) forward model, +/-300 km padding, layered density.
Corrections carried from the Copilot exchange that F13 corrected (2026-10-07):
  * water depth + seabed topography ARE in the load (F13's correction was right —
    a Bouguer anomaly without the water column is meaningless over a 2.9 km trough);
  * sediment overburden IS in the load, at a stated density;
  * observation points OFFSHORE ONLY. Onshore is excluded, not faked: the near-field
    cell singularity produced a spurious +385 mGal at Mt Kinabalu in the v1 attempt;
  * the Layang-Layang atoll is flagged as a 2D ARTIFACT (an infinite-strike ridge in a
    line-mass model; a real atoll is ~1-2 km across). It must not be read as a signal.

Deliberate departure from the Copilot figure: crustal thickness h under the trough axis
is SWEPT, not drawn once. An Airy back-of-envelope has two free parameters (fill S and
reference crust) and spans h = -2 to 19 km, so it cannot pin h. Gravity measures h
directly. This script converts the hypothesis into a detection threshold.

Usage: python3 trough_crust_thin_gravity.py [dark|light]
"""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

THEME = sys.argv[1] if len(sys.argv) > 1 else "dark"
OUT = "/root/GEOX/geox/skills/subsurface/gravity/output"
os.makedirs(OUT, exist_ok=True)

# ── constants + stated assumptions (all public-lane) ─────────────────────────
G = 6.674e-11
SI2MGAL = 1e5
RHO_AIR, RHO_W, RHO_S, RHO_C = 0.0, 1030.0, 2350.0, 2800.0
RHO_M, RHO_CROCKER, RHO_OPH = 3300.0, 2600.0, 2900.0
RHO_BOUGUER_PLATE = 2670.0          # conventional Bouguer slab density
REF_CRUST_BASE = -30.0              # reference column: crust 0..-30 km, mantle below
TROUGH_X = 215.0                    # trough axis along B-B' (km)
DW_TROUGH = 2.9                     # km water depth, the one L0<->L0 tie (3850 ms @1500 m/s)

# ── geometry: seabed / topography and top-of-crust (schematic, published magnitudes) ──
x = np.arange(-300.0, 901.0, 2.0)


def prof(ctrl):
    c = np.array(ctrl, dtype=float)
    return np.interp(x, c[:, 0], c[:, 1])


TOPO = prof([(0, -1.7), (100, -1.8), (104, -1.2), (108, 0.0), (114, 0.0), (118, -1.3),
             (122, -1.85), (160, -2.05), (195, -2.65), (215, -2.9), (246, -2.85),
             (250, -2.45), (285, -1.75), (310, -1.05), (340, -0.12), (356, 0.0),
             (395, 1.0), (410, 3.2), (413, 4.095), (416, 3.0), (422, 1.4), (470, 0.5),
             (540, 0.15), (556, -0.1), (600, -2.0)])
BASE = prof([(0, -2.9), (100, -2.8), (150, -3.3), (185, -5.0), (215, -6.6), (246, -7.4),
             (290, -9.0), (340, -11.5), (372, -13.5), (420, -14.0), (600, -12.0)])

# Published/inversion Moho (Sidek et al. 2016, gravity, non-unique, smoothing-regularised)
MOHO_PUB = prof([(0, -26), (150, -28), (215, -30), (300, -31), (420, -33), (600, -31)])


def moho_for_h(h_axis):
    """Moho profile whose crustal thickness at the trough axis equals h_axis (km).
    Anchored to ~26 km at the NW end and ~33 km under Crocker (Gilligan 2026: 24-60 km)."""
    t_ctrl = [(0, 26.0), (130, 24.0), (185, h_axis * 1.30), (215, h_axis),
              (250, h_axis * 1.10), (300, h_axis * 1.60), (350, h_axis * 2.20),
              (420, 33.0), (600, 30.0)]
    thick = prof(t_ctrl)
    return BASE - thick


# ── forward engine ───────────────────────────────────────────────────────────
dz = 0.5
z = np.arange(5.0 - dz / 2, -50.0, -dz)
X, Z = np.meshgrid(x, z)
cell_area_m2 = (2.0 * 1e3) * (dz * 1e3)

REF = np.where(Z > 0, RHO_AIR, np.where(Z > REF_CRUST_BASE, RHO_C, RHO_M))


def density_model(moho):
    M = moho[None, :]
    T = TOPO[None, :]
    B = BASE[None, :]
    rho = np.full(X.shape, np.nan)
    rho[Z > T] = RHO_AIR
    rho[(Z <= 0) & (Z > T)] = RHO_W                       # water column
    rock = Z <= T
    sed = rock & (Z > B) & (X < 355)             # sediment overburden
    rho[sed] = RHO_S
    cro = rock & (X >= 355) & (X < 455) & (Z > B)
    rho[cro] = RHO_CROCKER
    oph = rock & (X >= 455) & (Z > -12.0)
    rho[oph] = RHO_OPH
    crust = rock & np.isnan(rho) & (Z > M)
    rho[crust] = RHO_C
    rho[np.isnan(rho)] = RHO_M
    return rho - REF


XO = np.arange(0.0, 601.0, 5.0)
TO = np.interp(XO, x, TOPO)
ZO = np.where(TO < 0, 0.01, np.nan)          # OFFSHORE ONLY — onshore excluded, not faked
VALID = ~np.isnan(ZO)


def gravity_2d(drho):
    out = np.full(len(XO), np.nan)
    for i in np.flatnonzero(VALID):
        dxk = (X - XO[i]) * 1e3
        dzk = (ZO[i] - Z) * 1e3
        out[i] = np.nansum(2.0 * G * drho * cell_area_m2 * dzk / (dxk ** 2 + dzk ** 2))
    return out * SI2MGAL


def bouguer(fa):
    corr = np.where(TO < 0,
                    2 * math.pi * G * (RHO_BOUGUER_PLATE - RHO_W) * (-TO * 1e3),
                    -2 * math.pi * G * RHO_BOUGUER_PLATE * (TO * 1e3)) * SI2MGAL
    return fa + corr


def axis_value(arr):
    j = int(np.argmin(np.abs(XO - TROUGH_X)))
    return arr[j], XO[j]


# published baseline
fa_pub = gravity_2d(density_model(MOHO_PUB))
fa_pub = fa_pub - np.nanmean(fa_pub[VALID][:3])           # tie at NW end
bg_pub = bouguer(fa_pub)
BG_PUB_AXIS, _ = axis_value(bg_pub)

H_SWEEP = [5, 7, 9, 11, 13, 15, 18, 21, 24]
results = []
for h in H_SWEEP:
    fa = gravity_2d(density_model(moho_for_h(h)))
    fa = fa - np.nanmean(fa[VALID][:3])
    bg = bouguer(fa)
    bg_axis, _ = axis_value(bg)
    results.append((h, bg_axis, bg_axis - BG_PUB_AXIS, bg))
    print(f"  h={h:>2} km  Bouguer(axis)={bg_axis:7.1f} mGal   dBG vs published={bg_axis - BG_PUB_AXIS:7.1f} mGal")

print(f"\npublished Moho baseline: Bouguer(axis) = {BG_PUB_AXIS:.1f} mGal")
print("Airy h(S,ref) sensitivity — S=3.7 km (as drawn) ref=35 -> h=14.8 km;"
      " S=8 km ref=30 -> h=1.6 km.  Airy spans ~-2 to 19 km: NOT discriminating.")

# ── figure ───────────────────────────────────────────────────────────────────
if THEME == "dark":
    BG, FG, GRID, ACC = "#0b1220", "#cbd5e1", "#1e293b", "#f472b6"
else:
    BG, FG, GRID, ACC = "#ffffff", "#1f2937", "#e5e7eb", "#be185d"

fig = plt.figure(figsize=(16, 12), facecolor=BG)

# Panel A — input load
aA = fig.add_axes((0.08, 0.70, 0.88, 0.20), facecolor=BG)
aA.fill_between(XO, np.minimum(TO, 0), 0, color="#0c4a6e", alpha=0.85)
aA.fill_between(XO, TO, -3.6, color="#8a7a63", alpha=0.9)
aA.plot(XO, TO, color="#38bdf8", lw=1.8)
aA.axvline(TROUGH_X, color=ACC, lw=1.2, ls=(0, (4, 3)))
aA.annotate(f"trough axis\nwater depth {DW_TROUGH} km", xy=(TROUGH_X, -2.9),
            xytext=(TROUGH_X - 92, -3.4), fontsize=7.5, color=ACC,
            arrowprops=dict(arrowstyle="->", color=ACC, lw=0.8))
aA.annotate("atoll: 2D ARTIFACT\n(infinite-strike ridge —\ndo NOT read as signal)",
            xy=(111, 0.0), xytext=(30, 2.6), fontsize=7.0, color="#fbbf24",
            arrowprops=dict(arrowstyle="->", color="#fbbf24", lw=0.8))
aA.axvspan(356, 600, color=FG, alpha=0.10)
aA.text(478, 2.6, "ONSHORE — excluded, not modelled\n(needs terrain correction + land stations)",
        ha="center", fontsize=7.0, color=FG)
aA.set_xlim(0, 600); aA.set_ylim(-3.6, 4.6)
aA.set_ylabel("km rel. MSL", fontsize=8, color=FG)
aA.tick_params(colors=FG, labelsize=7); aA.grid(color=GRID, lw=0.4)
for s in ("top", "right"):
    aA.spines[s].set_visible(False)
aA.set_title("A · INPUT LOAD — seabed/topography + water column + sediment overburden "
             "(F13's correction: all three must be in the Bouguer model)", fontsize=9, color=FG, loc="left")

# Panel B — Bouguer profiles
aB = fig.add_axes((0.08, 0.40, 0.88, 0.24), facecolor=BG)
cmap = plt.get_cmap("coolwarm")
for k, (h, _, dbg, bg) in enumerate(results):
    aB.plot(XO, bg, color=cmap(k / (len(results) - 1)), lw=1.5,
            label=f"thin-crust h={h} km")
aB.plot(XO, bg_pub, color=FG, lw=2.2, ls="--", label="published Moho 26–33 km (Sidek 2016)")
aB.axvline(TROUGH_X, color=ACC, lw=1.0, ls=(0, (4, 3)))
aB.axvspan(356, 600, color=FG, alpha=0.10)
aB.axhline(0, color=GRID, lw=0.6)
aB.set_xlim(0, 360)
aB.set_ylabel("Bouguer anomaly (mGal)", fontsize=8, color=FG)
aB.set_xlabel("distance along B–B′, NW → SE (km)", fontsize=8, color=FG)
aB.tick_params(colors=FG, labelsize=7); aB.grid(color=GRID, lw=0.4)
for s in ("top", "right"):
    aB.spines[s].set_visible(False)
aB.legend(fontsize=6.4, ncol=3, loc="lower left", frameon=False, labelcolor=FG)
aB.set_title("B · PREDICTED BOUGUER — forward-modelled, relative to the NW tie point. "
             "Predictions, NOT data.", fontsize=9, color=FG, loc="left")

# Panel C — detection threshold
aC = fig.add_axes((0.08, 0.075, 0.40, 0.26), facecolor=BG)
hs = [r[0] for r in results]
dbg = [r[2] for r in results]
aC.plot(hs, dbg, color=ACC, lw=2.4, marker="o", ms=4)
aC.axhspan(-5, 5, color="#22c55e", alpha=0.18)
aC.axhline(0, color=GRID, lw=0.8)
aC.set_xlabel("crustal thickness h under trough axis (km)", fontsize=8, color=FG)
aC.set_ylabel("ΔBouguer vs published Moho (mGal)", fontsize=8, color=FG)
aC.tick_params(colors=FG, labelsize=7); aC.grid(color=GRID, lw=0.4)
for s in ("top", "right"):
    aC.spines[s].set_visible(False)
aC.set_title("C · DETECTION THRESHOLD — is F1 resolvable?", fontsize=9, color=FG, loc="left")
aC.text(0.97, 0.06, "green band = ±5 mGal, ~the practical resolution of\n"
                    "satellite gravity at 20–50 km wavelength.\n"
                    "Right of the band: NOT distinguishable from published.\n"
                    "Left of it: F1 decides the hypothesis from free data.",
        transform=aC.transAxes, ha="right", va="bottom", fontsize=6.6, color=FG,
        bbox=dict(fc=BG, ec=GRID, lw=0.5, alpha=0.9))

# Panel D — why Airy cannot pin h
aD = fig.add_axes((0.545, 0.075, 0.415, 0.26), facecolor=BG)
aD.axis("off")
aD.set_title("D · WHY h IS SWEPT, NOT DRAWN — the Airy check does not discriminate",
             fontsize=9, color=FG, loc="left")
rm, rc, rw, rs = RHO_M, RHO_C, RHO_W, RHO_S
f_sed, f_crust = (rm - rs) / (rm - rw), (rm - rc) / (rm - rw)
rows = ["h = REF − (dw + %.3f·S) / %.3f      (dw = %.1f km)" % (f_sed, f_crust, DW_TROUGH), "",
        "      S (km fill) │ ref=30 │ ref=32 │ ref=35 │ ref=38",
        "      ────────────┼────────┼────────┼────────┼───────"]
for S in (3.0, 3.7, 5.0, 6.0, 8.0, 10.0):
    zu = DW_TROUGH + f_sed * S
    rows.append("      %11.1f │ %6.1f │ %6.1f │ %6.1f │ %6.1f"
                % (S, *[R - zu / f_crust for R in (30, 32, 35, 38)]))
rows += ["",
         "Airy spans h ≈ −2 → 19 km over plausible inputs. It is a",
         "plausibility screen, NOT evidence: it can be made to 'fit'",
         "almost any crustal thickness by choosing S and REF.",
         "",
         "Copilot's figure carried THREE inconsistent values of h:",
         "  drawn geometry at axis ......... 6.9 km",
         "  Airy with its own S = 3.71 km .. 14.8 km",
         "  panel label .................... \"7–13 km\"",
         "The label was fitted to the drawing, not computed from the model.",
         "",
         "⇒ Gravity and deep seismic MEASURE h. Airy only guesses it.",
         "⇒ Constrain S (total fill to acoustic basement) independently;",
         "   it is the input that actually moves h.",
         ]
aD.text(0, 1.0, "\n".join(rows), fontsize=6.3, color=FG, va="top", family="monospace")

fig.suptitle(
    "TROUGH-CRUST-THIN — forward Bouguer model with h SWEPT · PUBLIC LANE · predictions not data · NOT SEALED\n"
    "2D line-mass (Talwani-style), 2 × 0.5 km cells, ±300 km padding, offshore observation only · "
    f"ρ: water {RHO_W:.0f} sediment {RHO_S:.0f} crust {RHO_C:.0f} Crocker {RHO_CROCKER:.0f} "
    f"ophiolite {RHO_OPH:.0f} mantle {RHO_M:.0f} kg/m³",
    fontsize=9.5, color=FG, y=0.975,
)
fig.savefig(f"{OUT}/trough_crust_thin_gravity_{THEME}.png", facecolor=BG, dpi=150)
fig.savefig(f"{OUT}/trough_crust_thin_gravity_{THEME}.svg", facecolor=BG)
print(f"\n{THEME} rendered -> {OUT}/trough_crust_thin_gravity_{THEME}.png")
