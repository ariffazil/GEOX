#!/usr/bin/env python3
"""
KL2 Kinabalu Basin — Well Penetration / NN Horizon Scaffold (v3, Rotan-1 corrected)
===================================================================================
Supersedes v2 (2026-09-07). Changes per F13 enterprise resolution 2026-09-30:
  1. Rotan-1 header CORRECTED. Public values only in this repo:
     water depth 3,773 ft (~1150 m) · TD 7,024 ft (~2141 m MD) — OGJ, 5 Feb 2007.
     v2's 3200 m / 2810 ms / 750 m row was a DATA-LINEAGE FAULT (fixture-encoded).
  2. Rotan-1 picks UPGRADED DER_MODEL -> REAL [RELAY-ENT]: NN12/NN11 base penetrated,
     NN10 base below TD; Landmark IVD Kamunsu / IVC Kinarut tops; top reservoir; GWC.
REDACTED 2026-10-15 (ARIF, AMANAH): exact pick depths, TWT@TD, pay/contact depths,
VSP parameters and the MD->TVDSS factor are held outside this repo. Git history
was intentionally NOT rewritten.
  3. Penetration asserts RECOMPUTED for v3 (v1 pattern was built on the faulty
     row; forcing v1 would launder the fault). Diff printed, not hidden.
  4. Other 7 wells UNCHANGED — remain DER_SYNTHETIC fixture rows. No new fiction.
Provenance discipline: [RELAY-ENT] enterprise files not locally readable on KVM8.
"""

import math
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

NN_BASE_MA = {
    "NN5": 14.91,
    "NN6": 13.53,
    "NN7": 11.90,
    "NN8": 10.89,
    "NN9": 10.55,
    "NN10": 9.53,
    "NN11": 8.29,
    "NN12": 5.00,
    "NN13": 4.00,
    "NN15": 3.75,
    "NN16": 3.70,
    "NN18": 2.39,
    "NN21": 0.26,
}
NN_PROV = {h: "ICS-FILL (Gradstein 2020)" for h in ("NN12", "NN13", "NN15")}
NN_PROV.update({h: "PETRONAS Borneo 2023" for h in NN_BASE_MA if h not in NN_PROV})
ICS_FILL = {"NN12", "NN13", "NN14", "NN15"}
V1_ANCHORED = {"NN9", "NN8", "NN7", "NN6", "NN5"}
LON_W, LON_E = 115.90, 117.70

# name, alias, status, td_tvdss, twt_td, seabed, age_td, deviated, td_curve, header_prov
WELLS = [
    ("Perkaka-1", "PEKAKA-1", "dry", 3100.0, 2700, 500.0, 13.60, False, "measured", "DER_SYNTHETIC fixture"),
    ("Buluh-1", "BULUH-1", "gas", 2800.0, 2480, 700.0, 10.75, False, "SYNTHETIC", "DER_SYNTHETIC fixture"),
    # TD/seabed public (OGJ 2007, MD ~ TVD for a near-vertical well); TWT@TD REDACTED
    ("Rotan-1", "ROTAN-1", "gas", 2141.0, None, 1150.0, 9.51, False, "measured", "PUBLIC [OGJ 2007]"),
    ("Bunga Lili-1", "BUNGA LILI-1", "unknown", 3500.0, 3050, 850.0, 12.50, True, "measured", "DER_SYNTHETIC fixture"),
    ("Maligan-1", "MALIGAN-1", "dry", 2900.0, 2540, 800.0, 10.80, False, "measured", "DER_SYNTHETIC fixture"),
    ("Sigut-1St1", "SUGUT", "unknown", 2700.0, 2370, 650.0, 10.65, False, "measured", "DER_SYNTHETIC fixture"),
    ("Barton-2", "BARTON-2", "unknown", 3000.0, 2620, 600.0, 12.00, False, "measured", "DER_SYNTHETIC fixture"),
    ("Solisip-1", "SOLISIP-1", "unknown", 3300.0, 2900, 900.0, 12.30, False, "measured", "DER_SYNTHETIC fixture"),
]
MAX_INCL = {"Bunga Lili-1": 45.0}
STATUS_COLOR = {"gas": "#2e7d32", "dry": "#c62828", "unknown": "#757575"}

# Rotan-1 REAL picks [RELAY-ENT kin_clm_7] — depths REDACTED 2026-10-15
ROTAN_REAL = {  # horizon: (flag, penetrated)
    "NN12": ("REAL-BIO", True),
    "NN11": ("REAL-BIO", True),
    "NN10": ("REAL-BIO", False),  # below TD -> not penetrated
}


def horizon_depth(age_ma, td, seabed, age_td):
    return seabed + (age_ma / age_td) * (td - seabed)


def sigma_bio(age_ma):
    return 20.0 + 180.0 * (age_ma / 14.91)


def sigma_vel(z):
    return 200.0 + (300.0 / 3500.0) * z


# ------------------------------------------------- penetration asserts v3 --
def reached(age_td, h):
    return age_td >= NN_BASE_MA[h]


EXPECT_V3 = {"NN9": 7, "NN8": 4, "NN7": 4, "NN6": 1, "NN5": 0}  # recomputed after Rotan fix
V2_EXPECT = {"NN9": 8, "NN8": 5, "NN7": 5, "NN6": 1, "NN5": 0}  # what v2 asserted (faulty row)
for h, expected in EXPECT_V3.items():
    n = sum(1 for w in WELLS if reached(w[6], h))
    assert n == expected, f"PENETRATION PATTERN v3 BROKEN: {h} = {n}/8, expected {expected}/8"
print("[ASSERT v3] recomputed penetration pattern (v2 faulty-row pattern in brackets):")
for h in ("NN9", "NN8", "NN7", "NN6", "NN5"):
    n = sum(1 for w in WELLS if reached(w[6], h))
    print(f"  {h:5s} base {NN_BASE_MA[h]:5.2f} Ma -> {n}/8 wells   (v2 said {V2_EXPECT[h]}/8)")

# ------------------------------------------------------------ pick table ---
rows, picks = [], {}
for name, alias, status, td, twt_td, seabed, age_td, dev, tdc, hp in WELLS:
    picks[name] = {}
    for h, age in sorted(NN_BASE_MA.items(), key=lambda kv: -kv[1]):
        if name == "Rotan-1" and h in ROTAN_REAL:
            flag, pen = ROTAN_REAL[h]
            # depth redacted -> not plotted (pen=False in the plot dict only)
            picks[name][h] = dict(z=None, pen=False, sigma_total=None, clipped=False, real=True)
            rows.append(
                dict(
                    well=name,
                    legacy_alias=alias,
                    horizon=f"{h} base",
                    age_ma=age,
                    age_provenance=NN_PROV[h],
                    pick_flag=f"{flag} (depth REDACTED)",
                    depth_tvdss_m=None,
                    sigma_bio_m=None,
                    sigma_vel_m=None,
                    sigma_total_m=None,
                    penetrated="Y" if pen else "N (below TD)",
                    sigma_clipped_at_td="",
                )
            )
            continue
        z = horizon_depth(age, td, seabed, age_td)
        pen = z <= td
        flag = "v1-anchor" if h in V1_ANCHORED else "interp-ICS-FILL" if h in ICS_FILL else "interp"
        if name == "Rotan-1":
            flag = "N/A-superseded" if not pen else "DER_MODEL-superseded"
        sb, sv = (sigma_bio(age), sigma_vel(z)) if pen else (None, None)
        st = math.hypot(sb, sv) if pen else None
        clipped = bool(pen and z + st > td)
        picks[name][h] = dict(z=z, pen=pen, sigma_total=st, clipped=clipped, real=False)
        rows.append(
            dict(
                well=name,
                legacy_alias=alias,
                horizon=f"{h} base",
                age_ma=age,
                age_provenance=NN_PROV[h],
                pick_flag=flag,
                depth_tvdss_m=round(z, 1) if pen else None,
                sigma_bio_m=round(sb, 1) if pen else None,
                sigma_vel_m=round(sv, 1) if pen else None,
                sigma_total_m=round(st, 1) if pen else None,
                penetrated="Y" if pen else "N (below TD)",
                sigma_clipped_at_td="Y" if clipped else "",
            )
        )
df_picks = pd.DataFrame(rows)
df_wells = pd.DataFrame(
    [
        dict(
            well=n,
            legacy_alias=a,
            status=s,
            td_tvdss_m=t,
            twt_at_td_ms=tt,
            seabed_tvdss_m=sb,
            deviated=(f"Y (max {MAX_INCL[n]:.0f} deg)") if d else "N",
            td_curve_prov=(
                "SYNTHETIC T-D column in TZ KL2.xlsx (well is REAL)"
                if c == "SYNTHETIC"
                else "measured checkshot (synthetic fixture, DER_SYNTHETIC)"
            ),
            header_prov=hp,
            longitude_approx_e=round(LON_W + (LON_E - LON_W) * i / (len(WELLS) - 1), 2),
            roster_prov="REAL — KL2V2 keyline (WORKSHOP#1_2026_Kinabalu_Basin); Rotan-1 header corrected per WCR 2026-09-30",
        )
        for i, (n, a, s, t, tt, sb, atd, d, c, hp) in enumerate(WELLS)
    ]
)
df_datum = pd.DataFrame(
    [
        dict(
            surface=f"{h} base",
            age_ma=aa,
            provenance=NN_PROV[h],
            confidence="MEDIUM-LOW (ICS-FILL)" if h in ICS_FILL else "HIGH",
            note="NN14 unresolved regionally; carried with NN15" if h == "NN15" else "",
        )
        for h, aa in sorted(NN_BASE_MA.items(), key=lambda kv: -kv[1])
    ]
    + [dict(surface="Seabed / present", age_ma=0.0, provenance="present-day mudline", confidence="HIGH", note="")]
)
df_prov = pd.DataFrame(
    [
        dict(field="Well roster (8)", classification="REAL", source="KL2V2 keyline (validator memo 2026-09-07)"),
        dict(
            field="Rotan-1 header (seabed/TD)",
            classification="PUBLIC",
            source="Oil & Gas Journal, 5 Feb 2007 (Murphy Oil): TD 7,024 ft in 3,773 ft of water; TWT@TD REDACTED",
        ),
        dict(
            field="Rotan-1 NN picks / tops / pay / GWC",
            classification="REAL [RELAY-ENT] — depths REDACTED 2026-10-15",
            source="enterprise relay (WCR + biostrat + Landmark); exact values held outside repo",
        ),
        dict(
            field="v2 Rotan-1 row (3200 m)",
            classification="DATA-LINEAGE FAULT — SUPERSEDED 2026-09-30",
            source="fixture-encoded value, not the well header; retained for lineage (kin_clm_6)",
        ),
        dict(
            field="Other 7 wells TDs/T-D",
            classification="DER_SYNTHETIC (fixture)",
            source="kinabalu_synth.py — UNCHANGED in v3; no new fiction added",
        ),
        dict(
            field="NN base ages",
            classification="HIGH (PETRONAS Borneo 2023); MEDIUM-LOW (NN12-15 ICS-FILL)",
            source="2023 NW Borneo Integration Framework; Gradstein 2020 fill",
        ),
        dict(
            field="Horizon picks (7 wells)",
            classification="DER_MODEL — linear age-depth",
            source="unchanged model; v3 asserts recomputed after Rotan correction",
        ),
        dict(
            field="Velocity uncertainty",
            classification="DER — 200-500 m",
            source="NSPW mobile-shale province; Rotan VSP details REDACTED",
        ),
        dict(field="v1 artifact", classification="ON HOLD 2026-09-07", source="falsified Neogene datum"),
    ]
)

with pd.ExcelWriter("kl2_kinabalu_well_data_v3.xlsx", engine="openpyxl") as xw:
    df_wells.to_excel(xw, sheet_name="Wells", index=False)
    df_picks.to_excel(xw, sheet_name="NN_Horizon_Picks", index=False)
    df_datum.to_excel(xw, sheet_name="Datum", index=False)
    df_prov.to_excel(xw, sheet_name="Provenance", index=False)

# ---------------------------------------------------------------- chart ----
fig, ax = plt.subplots(figsize=(15, 11))
xs = np.arange(len(WELLS))
names = [w[0] for w in WELLS]
seabeds = [w[5] for w in WELLS]
ax.fill_between(xs, 0, seabeds, color="#cfe8f7", alpha=0.55, zorder=1)
ax.plot(xs, seabeds, "--", color="#1f77b4", lw=1.6, zorder=3, label="water bottom (500–1150 m)")
EPOCH_COLOR = {h: ("#8d6e63" if NN_BASE_MA[h] > 5.33 else "#f9a825" if NN_BASE_MA[h] > 2.58 else "#1e88e5") for h in NN_BASE_MA}
clipped_wells = []
for i, (name, alias, status, td, twt_td, seabed, age_td, dev, tdc, hp) in enumerate(WELLS):
    ax.plot([i, i], [seabed, td], "-", color=STATUS_COLOR[status], lw=3.2, zorder=4)
    ax.plot([i - 0.22, i + 0.22], [td, td], "-", color="k", lw=1.4, zorder=5)
    ax.annotate(
        f"TD {td:.0f}" + ("  PUBLIC" if "PUBLIC" in hp else ""),
        (i, td),
        textcoords="offset points",
        xytext=(14, -2),
        fontsize=7.5,
        color="#2e7d32" if "PUBLIC" in hp else "k",
    )
    if dev:
        ax.annotate(
            "deviated ~45°", (i, td), textcoords="offset points", xytext=(14, -13), fontsize=7, color="#6a1b9a", style="italic"
        )
    for h in NN_BASE_MA:
        p = picks[name][h]
        if not p["pen"]:
            continue
        z, st = p["z"], p["sigma_total"]
        yerr_lo = min(st, td - z)
        ax.errorbar(i, z, yerr=[[st], [max(yerr_lo, 0)]], fmt="none", ecolor=EPOCH_COLOR[h], elinewidth=1.1, alpha=0.85, zorder=5)
        if p.get("real"):
            ax.plot(i, z, marker="D", markersize=7, markerfacecolor="#2e7d32", markeredgecolor="#1b5e20", zorder=7)
        else:
            ax.plot(
                i,
                z,
                marker="o",
                markersize=5.5,
                markerfacecolor=("none" if h in ICS_FILL else EPOCH_COLOR[h]),
                markeredgecolor=EPOCH_COLOR[h],
                markeredgewidth=1.4,
                zorder=6,
            )
        if p["clipped"]:
            clipped_wells.append(name)
            ax.plot(i, td, marker="v", markersize=6, color="k", markerfacecolor="white", zorder=7)
# Rotan: pay, tops and REAL picks exist but their depths are redacted (not drawn)
ri = names.index("Rotan-1")
ax.annotate(
    "single-zone gas pay (OGJ 2007)\nREAL picks / pay / GWC:\ndepths REDACTED",
    (ri, seabeds[ri]),
    textcoords="offset points",
    xytext=(14, 40),
    fontsize=7.6,
    color="#1b5e20",
    fontweight="bold",
)

nn9 = [picks[n]["NN9"]["z"] for n in names if picks[n]["NN9"]["pen"]]
mid = float(np.mean(nn9))
ax.axhspan(mid - 300, mid + 300, color="#f9a825", alpha=0.10, zorder=0)
ax.annotate(
    "NN9 cluster: inter-well spread ≈ single-well σ_vel — correlation non-unique within ±300 m (7 wells; Rotan no longer reaches)",
    (0.99, mid - 300),
    ha="right",
    va="bottom",
    fontsize=8,
    color="#8a6d00",
    xycoords=("axes fraction", "data"),
)
ax.set_xticks(xs)
ax.set_xticklabels([f"{n}\n({w[1]})" if w[1] != w[0] else n for n, w in zip(names, WELLS, strict=False)], fontsize=8.5)
ax.set_ylabel("TVDSS (m)", fontsize=10)
ax.invert_yaxis()
ax.set_ylim(4300, -150)
ax.set_xlim(-0.6, len(WELLS) - 0.4)
ax.grid(axis="y", color="0.9", lw=0.6)
ax.set_title(
    "KL2 Kinabalu Basin — Well Penetration / NN Horizon Scaffold (v3, Rotan-1 corrected)\n"
    "Datum: 2023 NW Borneo Integration · Rotan-1 public header; exact picks & TWT redacted · others DER_SYNTHETIC (unchanged)",
    fontsize=12,
)
legend_items = [
    Line2D([], [], color="#2e7d32", lw=3, label="gas (Rotan-1, Buluh-1)"),
    Line2D([], [], color="#c62828", lw=3, label="dry (Perkaka-1, Maligan-1)"),
    Line2D([], [], color="#757575", lw=3, label="unknown status"),
    Line2D([], [], color="#1f77b4", ls="--", label="water bottom"),
    Line2D([], [], marker="o", ls="", color="#8d6e63", label="DER_MODEL pick (Miocene)"),
    Line2D([], [], marker="o", ls="", color="#f9a825", label="DER_MODEL pick (Pliocene)"),
    Line2D([], [], marker="o", ls="", markerfacecolor="none", color="#f9a825", label="ICS-FILL (NN12–15)"),
    Line2D([], [], marker="v", ls="", markerfacecolor="white", color="k", label="σ clipped at TD"),
]
ax.legend(handles=legend_items, loc="upper left", fontsize=8, framealpha=0.95)
footer = (
    "v3 CHANGES: Rotan-1 TD 3200→~2141 m (public; v2 row = DATA-LINEAGE FAULT, kin_clm_6) · Rotan picks REAL, depths redacted · "
    "asserts recomputed (NN9 8→7, NN8 5→4, NN7 5→4) — v1 pattern NOT preserved because it was built on the fault.\n"
    "FIRST-PASS AGE SCAFFOLD — not a well-correlation product. MOM: tectonic/structural correlation before NN-only.  "
    "σ_total = √(σ_bio²+σ_vel²). v1 ON HOLD 2026-09-07. [RELAY-ENT] = enterprise files, not locally readable on KVM8."
)
fig.text(0.5, 0.005, footer, ha="center", fontsize=7.4, color="#333")
plt.tight_layout(rect=(0, 0.05, 1, 1))
plt.savefig("kl2_kinabalu_penetration_chart_v3.png", dpi=200)
print("[OK] v3 wrote kl2_kinabalu_penetration_chart_v3.png + kl2_kinabalu_well_data_v3.xlsx")
print(f"[OK] sigma clipped at TD: {sorted(set(clipped_wells))}")
