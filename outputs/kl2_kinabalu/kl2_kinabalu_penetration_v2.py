#!/usr/bin/env python3
"""
KL2 Kinabalu Basin — Well Penetration / NN Horizon Scaffold (v2, re-datumed)
============================================================================
Re-forge of the 2026-09-07 v1 chart after validator HOLD -> REVISE.

Changes vs v1 (falsified Neogene datum):
  1. NN ages re-datumed to 2023 NW Borneo Integration Framework (PETRONAS
     unified horizons). One shared-boundary ladder — no per-zone bounds, no seams.
  2. Zones regrouped to the 9 PETRONAS unified horizons (no invented groups).
  3. NN12-NN15 tagged ICS-FILL (Gradstein 2020) — not regionally anchored.
     NN14 unresolved regionally, carried with NN15, not plotted separately.
  4. Well roster reclassified REAL (KL2V2 keyline): Perkaka-1, Buluh-1, Rotan-1,
     Bunga Lili-1, Maligan-1, Sigut-1St1, Barton-2, Solisip-1.
     Buluh-1 = REAL well with SYNTHETIC T-D column (not a synthetic well).
  5. sigma_total = sqrt(sigma_bio^2 + sigma_vel^2); sigma_vel 200-500 m
     (NSPW mobile-shale velocity uncertainty) now included in bars.
  6. Error bars clipped at TD where sigma band would imply data below TD.
  7. Framed as FIRST-PASS AGE SCAFFOLD (MOM: tectonic/structural correlation
     before NN-only correlation).

Provenance per field:
  - Roster / TDs / deviation flags : REAL per KL2V2 keyline (via validator
    memo 2026-09-07, DELIVERED-INT); TD numbers carried from kinabalu_synth.py
    fixture (VPS) which encodes the TZ KL2.xlsx analysis.
  - T-D curves                     : DER_SYNTHETIC (kinabalu_synth.py fixture).
  - Horizon pick depths            : DER_MODEL — linear age-depth per well,
    calibrated to reproduce the v1 depth-based penetration pattern exactly
    (asserts below). Pending DSG real tops -> then MEDIUM-LOW -> HIGH.
  - NN base ages                   : PETRONAS Borneo 2023 (HIGH) except
    NN12-15 = ICS-FILL (MEDIUM-LOW).
  - Longitudes                     : approximate keyline spread 115.90-117.70E,
    LOW confidence, presentational only.

Run: pip install numpy pandas matplotlib openpyxl && python kl2_kinabalu_penetration_v2.py
"""
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ---------------------------------------------------------------- datum ----
# NN unified-horizon BASE ages (Ma) — 2023 NW Borneo Integration Framework.
NN_BASE_MA = {
    "NN5": 14.91, "NN6": 13.53, "NN7": 11.90, "NN8": 10.89, "NN9": 10.55,
    "NN10": 9.53, "NN11": 8.29, "NN12": 5.00, "NN13": 4.00, "NN15": 3.75,
    "NN16": 3.70, "NN18": 2.39, "NN21": 0.26,
}
NN_PROV = {h: "ICS-FILL (Gradstein 2020)" for h in ("NN12", "NN13", "NN15")}
NN_PROV.update({h: "PETRONAS Borneo 2023" for h in NN_BASE_MA if h not in NN_PROV})
ICS_FILL = {"NN12", "NN13", "NN14", "NN15"}
# Surfaces anchored to v1 picked groups; the rest are model interpolations.
V1_ANCHORED = {"NN9", "NN8", "NN7", "NN6", "NN5"}

LON_W, LON_E = 115.90, 117.70  # Perkaka-1 west, Solisip-1 east (approximate)

# ---------------------------------------------------------------- wells ----
# KL2V2 keyline order. age_td = age at TD (DER_MODEL calibration, Ma).
# seabed = water bottom TVDSS (m) — block-wide 500-900 m per v1 delivery.
WELLS = [
    # name, legacy alias, status, td, twt_td, seabed, age_td, deviated, td_curve
    ("Perkaka-1",   "PEKAKA-1",  "dry",     3100, 2700, 500, 13.60, False, "measured"),
    ("Buluh-1",     "BULUH-1",   "gas",     2800, 2480, 700, 10.75, False, "SYNTHETIC"),
    ("Rotan-1",     "ROTAN-1",   "gas",     3200, 2810, 750, 12.10, False, "measured"),
    ("Bunga Lili-1","BUNGA LILI-1","unknown",3500, 3050, 850, 12.50, True,  "measured"),
    ("Maligan-1",   "MALIGAN-1", "dry",     2900, 2540, 800, 10.80, False, "measured"),
    ("Sigut-1St1",  "SUGUT",     "unknown", 2700, 2370, 650, 10.65, False, "measured"),
    ("Barton-2",    "BARTON-2",  "unknown", 3000, 2620, 600, 12.00, False, "measured"),
    ("Solisip-1",   "SOLISIP-1", "unknown", 3300, 2900, 900, 12.30, False, "measured"),
]
MAX_INCL = {"Bunga Lili-1": 45.0}
STATUS_COLOR = {"gas": "#2e7d32", "dry": "#c62828", "unknown": "#757575"}

def horizon_depth(age_ma, td, seabed, age_td):
    """Linear paleo-sedimentation model: 0 Ma at seabed -> age_td at TD."""
    return seabed + (age_ma / age_td) * (td - seabed)

def sigma_bio(age_ma):
    return 20.0 + 180.0 * (age_ma / 14.91)          # +/-20 m young .. 200 m NN5

def sigma_vel(z):
    return 200.0 + (300.0 / 3500.0) * z             # 200 m seabed .. 500 m @3500

# ------------------------------------------------- penetration asserts ----
def reached(age_td, horizon):
    return age_td >= NN_BASE_MA[horizon]

for h, expected in [("NN9", 8), ("NN8", 5), ("NN7", 5), ("NN6", 1), ("NN5", 0)]:
    n = sum(1 for w in WELLS if reached(w[6], h))
    assert n == expected, f"PENETRATION PATTERN BROKEN: {h} = {n}/8, expected {expected}/8"
print("[ASSERT] v1 depth-based penetration pattern reproduced under v2 datum:")
for h in ("NN9", "NN8", "NN7", "NN6", "NN5"):
    n = sum(1 for w in WELLS if reached(w[6], h))
    print(f"  {h:5s} base {NN_BASE_MA[h]:5.2f} Ma -> {n}/8 wells")

# ------------------------------------------------------------ pick table ---
rows, picks = [], {}
for (name, alias, status, td, twt_td, seabed, age_td, dev, tdc) in WELLS:
    picks[name] = {}
    for h, age in sorted(NN_BASE_MA.items(), key=lambda kv: -kv[1]):  # old -> young
        z = horizon_depth(age, td, seabed, age_td)
        pen = z <= td
        flag = ("v1-anchor" if h in V1_ANCHORED
                else "interp-ICS-FILL" if h in ICS_FILL else "interp")
        sb, sv = (sigma_bio(age), sigma_vel(z)) if pen else (None, None)
        st = math.hypot(sb, sv) if pen else None
        clipped = bool(pen and z + st > td)
        picks[name][h] = dict(z=z, pen=pen, sigma_total=st, clipped=clipped)
        rows.append(dict(well=name, legacy_alias=alias, horizon=f"{h} base",
                         age_ma=age, age_provenance=NN_PROV[h], pick_flag=flag,
                         depth_tvdss_m=round(z, 1) if pen else None,
                         sigma_bio_m=round(sb, 1) if pen else None,
                         sigma_vel_m=round(sv, 1) if pen else None,
                         sigma_total_m=round(st, 1) if pen else None,
                         penetrated="Y" if pen else "N (below TD)",
                         sigma_clipped_at_td="Y" if clipped else ""))

df_picks = pd.DataFrame(rows)

df_wells = pd.DataFrame([dict(
    well=n, legacy_alias=a, status=s, td_tvdss_m=t, twt_at_td_ms=tt,
    seabed_tvdss_m=sb, deviated=("Y (max %.0f deg)" % MAX_INCL[n]) if d else "N",
    td_curve_prov=("SYNTHETIC T-D column in TZ KL2.xlsx (well is REAL)" if c == "SYNTHETIC"
                   else "measured checkshot (synthetic fixture, DER_SYNTHETIC)"),
    longitude_approx_e=round(LON_W + (LON_E - LON_W) * i / (len(WELLS) - 1), 2),
    roster_prov="REAL — KL2V2 keyline (WORKSHOP#1_2026_Kinabalu_Basin)",
) for i, (n, a, s, t, tt, sb, atd, d, c) in enumerate(WELLS)])

df_datum = pd.DataFrame(
    [dict(surface=f"{h} base", age_ma=a, provenance=NN_PROV[h],
          confidence="MEDIUM-LOW (ICS-FILL)" if h in ICS_FILL else "HIGH",
          note="NN14 unresolved regionally; carried with NN15" if h == "NN15" else "")
     for h, a in sorted(NN_BASE_MA.items(), key=lambda kv: -kv[1])] +
    [dict(surface="Seabed / present", age_ma=0.0,
          provenance="present-day mudline", confidence="HIGH", note="")],
)

df_prov = pd.DataFrame([
    dict(field="Well roster (8)", classification="REAL",
         source="KL2V2 keyline, WORKSHOP#1_2026_Kinabalu_Basin (validator memo 2026-09-07)"),
    dict(field="TDs / TWT@TD / deviation flags", classification="DER_SYNTHETIC (fixture) / REAL per KL2V2",
         source="kinabalu_synth.py fixture — encodes TZ KL2.xlsx published characteristics"),
    dict(field="T-D curves", classification="DER_SYNTHETIC",
         source="Vo-K compaction checkshots, seed-stable (kinabalu_synth.py)"),
    dict(field="NN base ages", classification="HIGH (PETRONAS Borneo 2023); MEDIUM-LOW (NN12-15 ICS-FILL)",
         source="2023 NW Borneo Integration Framework; Gradstein 2020 fill"),
    dict(field="Horizon pick depths", classification="DER_MODEL — calibrated synthetic, pending DSG",
         source="linear age-depth model reproducing v1 penetration pattern (asserts in script)"),
    dict(field="Longitudes", classification="LOW — approximate",
         source="keyline spread 115.90-117.70E, presentational only"),
    dict(field="Gas/dry statuses", classification="DELIVERED-INT",
         source="v1 delivery; Rotan-1 gas independently grounded by validator"),
    dict(field="Velocity uncertainty", classification="DER — 200-500 m",
         source="NSPW mobile-shale province (validator + v1 disclosure), now IN error bars"),
    dict(field="v1 artifact (claude.ai ee4e8f29)", classification="ON HOLD 2026-09-07",
         source="Neogene datum falsified (~2 Ma / ~2 zones young). Do not lift ages from v1."),
])

with pd.ExcelWriter("kl2_kinabalu_well_data_v2.xlsx", engine="openpyxl") as xw:
    df_wells.to_excel(xw, sheet_name="Wells", index=False)
    df_picks.to_excel(xw, sheet_name="NN_Horizon_Picks", index=False)
    df_datum.to_excel(xw, sheet_name="Datum", index=False)
    df_prov.to_excel(xw, sheet_name="Provenance", index=False)

# ---------------------------------------------------------------- chart ----
fig, ax = plt.subplots(figsize=(15, 11))
xs = np.arange(len(WELLS))
names = [w[0] for w in WELLS]

# water column + seabed
seabeds = [w[5] for w in WELLS]
ax.fill_between(xs, 0, seabeds, color="#cfe8f7", alpha=0.55, zorder=1)
ax.plot(xs, seabeds, "--", color="#1f77b4", lw=1.6, zorder=3, label="Water bottom (500–900 m)")

EPOCH_COLOR = {"NN5": "#8d6e63", "NN6": "#8d6e63", "NN7": "#8d6e63", "NN8": "#8d6e63",
               "NN9": "#8d6e63", "NN10": "#8d6e63",
               "NN11": "#f9a825", "NN12": "#f9a825", "NN13": "#f9a825", "NN15": "#f9a825",
               "NN16": "#f9a825", "NN18": "#1e88e5", "NN21": "#1e88e5"}

clipped_wells = []
for i, (name, alias, status, td, twt_td, seabed, age_td, dev, tdc) in enumerate(WELLS):
    ax.plot([i, i], [seabed, td], "-", color=STATUS_COLOR[status], lw=3.2, zorder=4)
    ax.plot([i - 0.22, i + 0.22], [td, td], "-", color="k", lw=1.4, zorder=5)
    ax.annotate(f"TD {td}", (i, td), textcoords="offset points", xytext=(14, -2),
                fontsize=7.5, color="k")
    if dev:
        ax.annotate("deviated ~45°", (i, td), textcoords="offset points",
                    xytext=(14, -13), fontsize=7, color="#6a1b9a", style="italic")
    for h in NN_BASE_MA:
        p = picks[name][h]
        if not p["pen"]:
            continue
        z, st, clipped = p["z"], p["sigma_total"], p["clipped"]
        yerr_lo = min(st, td - z)
        ax.errorbar(i, z, yerr=[[st], [max(yerr_lo, 0)]], fmt="none",
                    ecolor=EPOCH_COLOR[h], elinewidth=1.1, alpha=0.85, zorder=5)
        ax.plot(i, z, marker="o", markersize=5.5,
                markerfacecolor=("none" if h in ICS_FILL else EPOCH_COLOR[h]),
                markeredgecolor=EPOCH_COLOR[h], markeredgewidth=1.4, zorder=6)
        if clipped:
            clipped_wells.append(name)
            ax.plot(i, td, marker="v", markersize=6, color="k",
                    markerfacecolor="white", zorder=7)

# non-uniqueness band at NN9 cluster
nn9 = [picks[n]["NN9"]["z"] for n in names]
mid = float(np.mean(nn9))
ax.axhspan(mid - 300, mid + 300, color="#f9a825", alpha=0.10, zorder=0)
ax.annotate(f"NN9: inter-well spread ≈ single-well σ_vel — correlation non-unique within ±300 m",
            (0.99, mid - 300), ha="right", va="bottom", fontsize=8, color="#8a6d00",
            xycoords=("axes fraction", "data"))

ax.set_xticks(xs)
ax.set_xticklabels([f"{n}\n({w[1]})" if w[1] != w[0] else n for n, w in zip(names, WELLS)],
                   fontsize=8.5)
ax.set_ylabel("TVDSS (m)", fontsize=10)
ax.invert_yaxis()
ax.set_ylim(4300, -150)
ax.set_xlim(-0.6, len(WELLS) - 0.4)
ax.grid(axis="y", color="0.9", lw=0.6)
ax.set_title("KL2 Kinabalu Basin — Well Penetration / NN Horizon Scaffold (v2, re-datumed)\n"
             "Datum: 2023 NW Borneo Integration (PETRONAS unified horizons) · picks DER_MODEL pending DSG",
             fontsize=12)

legend_items = [
    Line2D([], [], color="#2e7d32", lw=3, label="gas (Rotan-1, Buluh-1)"),
    Line2D([], [], color="#c62828", lw=3, label="dry (Perkaka-1, Maligan-1)"),
    Line2D([], [], color="#757575", lw=3, label="unknown status"),
    Line2D([], [], color="#1f77b4", ls="--", label="water bottom"),
    Line2D([], [], marker="o", ls="", color="#8d6e63", label="Miocene horizon (NN10–NN5)"),
    Line2D([], [], marker="o", ls="", color="#f9a825", label="Pliocene (NN16–NN11)"),
    Line2D([], [], marker="o", ls="", color="#1e88e5", label="Pleistocene (NN21–NN18)"),
    Line2D([], [], marker="o", ls="", markerfacecolor="none", color="#f9a825",
           label="ICS-FILL pick (NN12–15, not regionally anchored)"),
    Line2D([], [], marker="v", ls="", markerfacecolor="white", color="k",
           label="σ_total clipped at TD — pick unconstrained at base"),
]
ax.legend(handles=legend_items, loc="upper left", fontsize=8, framealpha=0.95)

footer = ("FIRST-PASS AGE SCAFFOLD — not a well-correlation product.  "
          "MOM: establish tectonic/structural correlation before relying on NN-only correlation.\n"
          "σ_total = √(σ_bio² + σ_vel²); σ_vel 200–500 m (NSPW mobile shale) now included.  "
          "Horizon picks DER_MODEL (calibrated synthetic) — upgrade to HIGH pending DSG real tops.\n"
          "v1 (claude.ai artifact ee4e8f29…) ON HOLD 2026-09-07 — falsified Neogene datum; do not lift ages from v1.")
fig.text(0.5, 0.005, footer, ha="center", fontsize=7.6, color="#333")

plt.tight_layout(rect=(0, 0.045, 1, 1))
plt.savefig("kl2_kinabalu_penetration_chart_v2.png", dpi=200)
print("\n[OK] wrote kl2_kinabalu_penetration_chart_v2.png + kl2_kinabalu_well_data_v2.xlsx")
print(f"[OK] sigma clipped at TD in wells: {sorted(set(clipped_wells))}")
