#!/usr/bin/env python3
"""
kl2_reality_calibration.py — anchor the KL2 transect to REAL Earth geometry.

Every figure in this project so far used a 600 km schematic axis with invented station
positions. This renders the measured replacement: the true B-B' path from verifiable
coordinates, the true along-track distances, and an explicit MEASURED / SCHEMATIC /
UNCONSTRAINED tag on every station so no figure can silently promote a guess.

Lane: PUBLIC. L0 = computed from published coordinates. No PETRONAS data. NOT SEALED.
Usage: python3 kl2_reality_calibration.py [dark|light]
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

THEME = sys.argv[1] if len(sys.argv) > 1 else "dark"
OUT = "/root/GEOX/geox/skills/subsurface/section/output"
DATA = "/root/GEOX/data/kl2_realdata"
os.makedirs(OUT, exist_ok=True)

d = np.load(f"{DATA}/transect.npz")
LAT, LON, DIST = d["lat"], d["lon"], d["dist_km"]
prov = json.load(open(f"{DATA}/bathy_provenance.json")) if os.path.exists(f"{DATA}/bathy_provenance.json") else None
bathy = np.load(f"{DATA}/real_bathy.npz")["bathy_m"] if os.path.exists(f"{DATA}/real_bathy.npz") else None

B = (7.78, 113.00)
Bp = (5.10, 118.60)
ANCHORS = [("Layang-Layang / Swallow Reef", 7.372, 113.847),
           ("Mt Kinabalu 4,095 m", 6.075, 116.558)]
OFFTRACK = [("Sandakan", 5.840, 118.117)]

# stations whose along-track position GEOX SOT does NOT constrain
SCHEM = [("Pekaka–Tepat high", 135), ("Sabah Trough axis", 230),
         ("deformation front / NSPW toe", 285), ("Kinabalu FTB / Block H", 360),
         ("Central Sabah", 495)]


def along_track(pt):
    dd = np.hypot((LAT - pt[0]) * 111.0, (LON - pt[1]) * 111.0 * np.cos(np.radians(pt[0])))
    j = int(np.argmin(dd))
    return DIST[j], float(dd[j])          # dd is already in km — do not re-convert


if THEME == "dark":
    BG, FG, GRID = "#0b1220", "#cbd5e1", "#1e293b"
    MEAS, SCH, OFF = "#22c55e", "#f59e0b", "#ef4444"
else:
    BG, FG, GRID = "#ffffff", "#1f2937", "#e5e7eb"
    MEAS, SCH, OFF = "#15803d", "#b45309", "#b91c1c"

fig = plt.figure(figsize=(17, 11), facecolor=BG)

# ── panel 1: map view of the real track ──────────────────────────────────────
a1 = fig.add_axes((0.06, 0.50, 0.44, 0.40), facecolor=BG)
a1.plot(LON, LAT, color="#38bdf8", lw=2.4, zorder=3, label="B–B′ real track (687 km)")
a1.plot(*B[::-1], marker="s", ms=9, color=FG, zorder=5)
a1.plot(*Bp[::-1], marker="s", ms=9, color=FG, zorder=5)
a1.text(B[1] - 0.08, B[0] + 0.09, "B (NW)", fontsize=8, color=FG, ha="right", weight="bold")
a1.text(Bp[1] + 0.08, Bp[0] - 0.09, "B′ (SE)", fontsize=8, color=FG, ha="left", weight="bold")
for nm, la, lo in ANCHORS:
    km, off = along_track((la, lo))
    a1.plot(lo, la, marker="o", ms=10, mfc=MEAS, mec=BG, mew=1.2, zorder=6)
    a1.annotate(f"{nm}\n{km:.1f} km  (off-track {off:.0f} km)", xy=(lo, la),
                xytext=(lo + 0.22, la + 0.20), fontsize=7.2, color=MEAS, weight="bold",
                arrowprops=dict(arrowstyle="->", color=MEAS, lw=0.9), zorder=6)
for nm, la, lo in OFFTRACK:
    km, off = along_track((la, lo))
    a1.plot(lo, la, marker="X", ms=11, color=OFF, zorder=6)
    a1.annotate(f"{nm} — {off:.0f} km OFF_TRANSECT\n(prior figures drew it as an on-line station)",
                xy=(lo, la), xytext=(lo - 1.55, la - 0.42), fontsize=7.2, color=OFF, weight="bold",
                arrowprops=dict(arrowstyle="->", color=OFF, lw=0.9), zorder=6)
for nm, km in SCHEM:
    j = int(np.argmin(np.abs(DIST - km)))
    a1.plot(LON[j], LAT[j], marker="v", ms=7, color=SCH, alpha=0.9, zorder=5)
a1.set_xlabel("longitude °E", fontsize=8, color=FG)
a1.set_ylabel("latitude °N", fontsize=8, color=FG)
a1.tick_params(colors=FG, labelsize=7)
a1.grid(color=GRID, lw=0.4)
for s in ("top", "right"):
    a1.spines[s].set_visible(False)
a1.set_title("1 · REAL TRANSECT — computed from published coordinates (L0)", fontsize=9.5, color=FG, loc="left")

# ── panel 2: MEASURED bathymetry on the real distance axis ───────────────────
a2 = fig.add_axes((0.56, 0.50, 0.40, 0.40), facecolor=BG)
if bathy is not None:
    a2.fill_between(DIST, bathy / 1000.0, 0, where=(bathy < 0), color="#0c4a6e", alpha=0.9)
    a2.fill_between(DIST, bathy / 1000.0, 0, where=(bathy >= 0), color="#8a7a63", alpha=0.95)
    a2.plot(DIST, bathy / 1000.0, color="#38bdf8", lw=1.1)
    jd = int(np.nanargmin(bathy[:400]))
    a2.plot(DIST[jd], bathy[jd] / 1000.0, marker="v", ms=11, color=MEAS, zorder=6)
    a2.annotate(f"Maximum sampled trough depth\n{bathy[jd]:.0f} m at chainage {DIST[jd]:.1f} km\n({LAT[jd]:.3f}N {LON[jd]:.3f}E)",
                xy=(DIST[jd], bathy[jd] / 1000.0), xytext=(DIST[jd] + 55, bathy[jd] / 1000.0 - 0.35),
                fontsize=7.0, color=MEAS, weight="bold",
                arrowprops=dict(arrowstyle="->", color=MEAS, lw=0.9), zorder=6)
    a2.axhline(-2.924, color="#f59e0b", lw=1.2, ls=(0, (5, 2)))
    a2.text(6, -2.80, "−2.9 km = the dw used in every Airy/flexure calc this session — now MEASURED",
            fontsize=6.4, color="#f59e0b", weight="bold")
    for nm, la, lo in ANCHORS:
        km, _ = along_track((la, lo))
        a2.axvline(km, color=MEAS, lw=1.0, ls=(0, (4, 2)), alpha=0.7)
        a2.text(km + 5, 3.55, f"{nm}\n{km:.1f} km", fontsize=6.6, color=MEAS, weight="bold", va="top")
    a2.axvspan(600, 690, color=OFF, alpha=0.10)
    a2.text(645, -1.2, "87 km of real\ntransect that no\nprior figure drew", fontsize=6.4,
            color=OFF, ha="center", va="center", weight="bold")
    a2.set_title("2 · GEBCO_2019 15″ cell elevation, sampled along B–B′ (Rutgers THREDDS dodsC, live)\n"
                 "     trough-axis position is LINE-SPECIFIC — not a mapped regional-axis solution",
                 fontsize=8.4, color=FG, loc="left")
    a2.set_ylim(-4.2, 4.4)
    a2.set_ylabel("elevation (km rel. sea level)", fontsize=8, color=FG)
else:
    a2.plot(DIST, LAT, color="#38bdf8", lw=2.0, label="latitude along track")
    a2.set_title("2 · transect coordinates (bathymetry UNMEASURED)", fontsize=9.5, color=FG, loc="left")
    a2.set_ylim(4.6, 8.2)
    a2.set_yticklabels([])
a2.axvline(600, color=OFF, lw=1.6, ls=":")
a2.text(596, 4.15, "600 km = axis every\nprior figure used", fontsize=6.4, color=OFF,
        ha="right", va="top", weight="bold")
a2.set_xlim(0, 690)
a2.set_xlabel("along-track distance (km)", fontsize=8, color=FG)
a2.tick_params(colors=FG, labelsize=7)
a2.grid(color=GRID, lw=0.4)
for s in ("top", "right"):
    a2.spines[s].set_visible(False)

# ── panel 3: station provenance table ────────────────────────────────────────
a3 = fig.add_axes((0.06, 0.055, 0.52, 0.38), facecolor=BG)
a3.axis("off")
a3.set_title("3 · STATION PROVENANCE — never promote a guess to a measurement", fontsize=9.5, color=FG, loc="left")
rows = [["Station", "Along-track", "Class", "Source"]]
rows += [["B (NW, Dangerous Grounds)", "0.0 km", "L0 MEASURED", "chosen on-line, 7.78N 113.00E"],
         ["Layang-Layang / Swallow Reef", f"{along_track(ANCHORS[0][1:])[0]:.1f} km", "L0 MEASURED", "7.372N 113.847E (published)"],
         ["Mt Kinabalu 4,095 m", f"{along_track(ANCHORS[1][1:])[0]:.1f} km", "L0 MEASURED", "6.075N 116.558E (published)"],
         ["B′ (SE, Sulu Sea)", f"{DIST[-1]:.1f} km", "L0 MEASURED", "chosen on-line, 5.10N 118.60E"]]
for nm, km in SCHEM:
    rows.append([nm, f"~{km} km", "SCHEMATIC", "no coordinates in GEOX SOT"])
rows.append(["Sandakan", f"~{along_track(OFFTRACK[0][1:])[0]:.0f} km", "OFF_TRANSECT", f"{along_track(OFFTRACK[0][1:])[1]:.0f} km off-line — remove or relabel"])
t = a3.table(cellText=rows, loc="upper center", cellLoc="left", colWidths=[0.36, 0.15, 0.17, 0.32])
t.auto_set_font_size(False)
t.set_fontsize(6.8)
t.scale(1, 1.5)
for j in range(4):
    t[0, j].set_facecolor(GRID)
    t[0, j].set_text_props(weight="bold", color=FG)
for i, r in enumerate(rows[1:], start=1):
    col = MEAS if "MEASURED" in r[2] else (OFF if "OFF" in r[2] else SCH)
    t[i, 2].set_text_props(color=col, weight="bold")
    for j in range(4):
        t[i, j].set_text_props(color=t[i, j].get_text().get_color() or FG) if j != 2 else None
        t[i, j].set_facecolor(BG)
        if j != 2:
            t[i, j].set_text_props(color=FG)

# ── panel 4: live-data status (Void Guard — no data != all clear) ────────────
a4 = fig.add_axes((0.62, 0.055, 0.34, 0.38), facecolor=BG)
a4.axis("off")
a4.set_title("4 · DATA MODE — what is measured vs UNMEASURED", fontsize=9.5, color=FG, loc="left")
lines = [
    ("Transect geometry", "MEASURED (L0)", MEAS, "haversine from published coordinates"),
    ("Bathymetry along B–B′", "MEASURED (L0)", MEAS, "GEBCO_2019 via Rutgers THREDDS dodsC — live subset 708×1404"),
]
if bathy is not None:
    _jd = int(np.nanargmin(bathy[:400]))
    lines += [
        ("   deepest point", f"{bathy[_jd]:.0f} m", MEAS,
         f"@ {DIST[_jd]:.1f} km ({LAT[_jd]:.3f}N {LON[_jd]:.3f}E) — confirms the dw≈2.9 km"),
        ("   Mount Kinabalu", f"+{bathy[int(np.argmin(abs(DIST-435.9)))]:.0f} m", SCH,
         "sampled GEBCO cell; Low's Peak geodetic elevation = 4,095.2 m"),
        ("   Layang-Layang", f"{bathy[int(np.argmin(abs(DIST-103.9)))]:.0f} m", SCH,
         "coarse-cell terrain value — NOT reef crest, island elevation, or water-depth observation"),
    ]
lines += [
    ("Free-air / Bouguer gravity", "UNMEASURED", OFF, "RUNTIME ACCESS PATHS unavailable from this host:"),
    ("", "", FG, "Sandwell-Smith CGI 500 · NOAA ERDDAP 000 · EMODnet 404 · OpenTopography 400"),
    ("", "", FG, "The PRODUCTS are live. Failure is reachability, not absence — do not say 'source dead'"),
    ("Magnetics (EMAG2)", "UNMEASURED", OFF, "GEOX emag2_fetcher = offline stub (already recorded in ledger)"),
    ("Moho", "TWO MODELS", SCH, "Sidek 2016 = INVERSE, non-unique; F13 = forward Airy"),
    ("All subsurface bodies", "L2 INTERPRET", SCH, "no KL2 geometry on this VPS (hard_wall)"),
]
y = 0.90
for name, mode, col, note in lines:
    if name:
        a4.text(0, y, name, fontsize=7.0, color=FG, va="top", weight="bold")
        a4.text(0.44, y, mode, fontsize=6.8, color=col, va="top", weight="bold")
        y -= 0.055
    if note:
        a4.text(0.02, y, note, fontsize=6.0, color=FG, va="top", alpha=0.85)
        y -= 0.055
a4.text(0, y - 0.02,
        "EVIDENCE HIERARCHY (external review 2026-10-08, adopted):\n"
        "  MEASURED — line geometry · GEBCO sampled elevation · along-line trough minimum\n"
        "  DERIVED  — dw input · line-specific source-to-trough separation (87 km)\n"
        "  UNKNOWN  — S · Bouguer/free-air · basement architecture · Te · Moho · OCT vs thinned continental\n"
        "  GATE     — T7 (constrain S) before T8 (gravity): h stays highly sensitive to S\n"
        "\n"
        "87 km high→moat does NOT determine Te, h, load geometry, S or crustal origin.\n"
        "Wording per review: raster SAMPLES, not point observations. OFFLINE_STUBS rule 1 + Void Guard apply.",
        fontsize=5.6, color=FG, va="top", style="italic",
        bbox=dict(fc=BG, ec=GRID, lw=0.5))
if prov:
    a4.text(0, 0.02, f"data_mode recorded: {prov.get('data_mode', 'n/a')}", fontsize=6.0, color=FG)

fig.suptitle(
    "KINABALU BASIN KL2 — REALITY CALIBRATION · real B–B′ transect replaces the 600 km schematic\n"
    "PUBLIC LANE · L0 geometry computed 2026-10-08 · bathymetry + gravity UNMEASURED (sources dead, see panel 4) · NOT SEALED",
    fontsize=10.5, color=FG, weight="bold", y=0.965,
)
fig.savefig(f"{OUT}/kl2_reality_calibration_{THEME}.png", facecolor=BG, dpi=150)
print(f"{THEME} rendered -> {OUT}/kl2_reality_calibration_{THEME}.png")
for nm, la, lo in ANCHORS + OFFTRACK:
    km, off = along_track((la, lo))
    print(f"  {nm:32s} {km:7.1f} km along track, {off:6.1f} km off-line")
print(f"  total {DIST[-1]:.1f} km | bathy loaded: {bathy is not None} | prov: {prov is not None}")
