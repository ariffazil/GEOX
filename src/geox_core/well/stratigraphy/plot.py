"""
GEOX Well Stratigraphy — Generalized Plot Panels
═══════════════════════════════════════════════════════════════════════════════

Per-well 6-track panel and multi-well correlation panel.
Config-driven via ProjectConfig — no hardcoded colors, labels, or well order.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from .config import (
    MOTIF_COLORS,
    TRACT_COLORS,
    ProjectConfig,
    default_depo_eod,
    default_depo_rank,
    default_nn_ages,
)

logger = logging.getLogger("geox.stratigraphy.plot")

SHORT_MOTIF = {
    "Fining Upward": "↑ FU",
    "Coarsening Upward": "↓ CU",
    "Blocky": "▬ BLK",
    "Serrated / Irregular Pattern": "≋ SER",
    "Crecentric": "◉ CRE",
    "Heterolithic": "≈ HET",
}

# Default well colors for correlation panel
WELL_COLORS = [
    "#C5D9F1",
    "#E2EFDA",
    "#FCE4D6",
    "#FFF2CC",
    "#FFE0E0",
    "#EAD1DC",
    "#D9D2E9",
    "#CFE2F3",
]
IVL_COLORS = plt.cm.Dark2.colors


def _plot_gr_conventional(ax, depth, gr, gr_min, gr_max, gr_cut, sand_color, shale_color, curve_color, alpha=0.70):
    """Conventional GR shading: fill from right edge (gr_max) to GR curve."""
    d = np.asarray(depth, dtype=float)
    g = np.asarray(gr, dtype=float)
    gc = np.clip(g, gr_min, gr_max)
    mask = ~np.isnan(d) & ~np.isnan(gc)
    if mask.sum() < 2:
        return
    dd, gg = d[mask], gc[mask]

    ax.fill_betweenx(dd, gg, gr_max, where=(gg <= gr_cut), color=sand_color, alpha=alpha, linewidth=0, zorder=2)
    ax.fill_betweenx(dd, gg, gr_max, where=(gg > gr_cut), color=shale_color, alpha=alpha, linewidth=0, zorder=2)
    ax.plot(gg, dd, color=curve_color, lw=0.70, zorder=3)
    ax.axvline(gr_min, color="#9E9E9E", lw=0.7, zorder=1)
    ax.axvline(gr_cut, color="#616161", lw=0.7, ls="--", zorder=1)
    ax.axvline(gr_max, color="#9E9E9E", lw=0.7, zorder=1)
    ax.set_xlim(gr_min, gr_max)


def _draw_motif_schematic(ax, motif, color, top_d, base_d, x0=0.02, x1=0.40, alpha_override=None):
    """Symbolic GR-motif shape in ax normalized x-space."""
    n = max(30, int((base_d - top_d) / 3))
    y = np.linspace(top_d, base_d, n)
    span = x1 - x0
    alp = alpha_override if alpha_override is not None else 0.70

    if motif == "Fining Upward":
        xr = np.linspace(x0 + span * 0.08, x1, n)
        ax.fill_betweenx(y, x0, xr, color=color, alpha=alp, zorder=4, lw=0)
    elif motif == "Coarsening Upward":
        xr = np.linspace(x1, x0 + span * 0.08, n)
        ax.fill_betweenx(y, x0, xr, color=color, alpha=alp, zorder=4, lw=0)
    elif motif == "Blocky":
        ax.fill_betweenx([top_d, base_d], x0, x0 + span * 0.62, color=color, alpha=alp, zorder=4, lw=0)
    elif motif == "Serrated / Irregular Pattern":
        n_t = max(4, int((base_d - top_d) / 12))
        xr = (x0 + span * 0.46 * (1 + np.sin(np.linspace(0, n_t * np.pi, n)))).clip(x0, x1)
        ax.fill_betweenx(y, x0, xr, color=color, alpha=max(0.08, alp - 0.15), zorder=4, lw=0)
    elif motif == "Crecentric":
        xr = x0 + span * 0.55 * np.abs(np.sin(np.linspace(0, np.pi, n)))
        ax.fill_betweenx(y, x0, xr + x0, color=color, alpha=alp, zorder=4, lw=0)
    else:
        ax.fill_betweenx([top_d, base_d], x0, x0 + span * 0.50, facecolor="none", edgecolor=color, hatch="////", lw=0.6, zorder=4)
        ax.fill_betweenx([top_d, base_d], x0, x0 + span * 0.50, color=color, alpha=min(alp * 0.26, 0.18), zorder=3, lw=0)


def generate_well_panel(
    well_id: str,
    wdata: dict | None,
    packages: list[dict],
    intervals: list,
    config: ProjectConfig,
    output_dir: str = "output",
    dpi: int = 200,
    sensing_bins: list | None = None,
    now_ts: str = "",
) -> str | None:
    """
    Generate per-well 6-track panel.

    Tracks: GR Log | Litho | Package + Motif + Seq Strat | Depo Env | Sea Level | Age/NN
    """
    if not packages:
        return None

    d_min = float(min(p["TOP"] for p in packages))
    d_max = float(max(p["BASE"] for p in packages))
    d_rng = d_max - d_min
    pad = max(20, d_rng * 0.03)

    depo_eod = default_depo_eod()
    depo_rank = default_depo_rank()
    nn_ages = default_nn_ages()

    # GR data
    dep = gr = None
    if wdata:
        dep = wdata.get("depth")
        gr = wdata.get("gr")

    mask = None
    if dep is not None and gr is not None:
        mask = (~np.isnan(dep)) & (~np.isnan(gr)) & (dep >= d_min - 5) & (dep <= d_max + 5)
        dep_f = dep[mask]
        gr_f = gr[mask]
        if len(dep_f) > 12000:
            s = len(dep_f) // 12000 + 1
            dep_f = dep_f[::s]
            gr_f = gr_f[::s]
    else:
        dep_f = gr_f = None

    # Depth -> age interpolator
    d_pts, a_pts = [], []
    for ivl in intervals:
        age = _parse_zone_age(str(ivl.zone if hasattr(ivl, "zone") else ivl.get("Z", "")), nn_ages)
        if age:
            t = float(ivl.top if hasattr(ivl, "top") else ivl.get("T", 0))
            b = float(ivl.base if hasattr(ivl, "base") else ivl.get("B", 0))
            d_pts += [t, b]
            a_pts += [age[0], age[1]]

    age_fn = None
    if len(d_pts) >= 2:
        da = np.array(d_pts)
        aa = np.array(a_pts)
        si = np.argsort(da)
        from scipy.interpolate import interp1d

        try:
            age_fn = interp1d(da[si], aa[si], bounds_error=False, fill_value=(aa[si][0], aa[si][-1]))
        except Exception:
            pass

    # Sea level data
    sl_d = sl_v = None
    if age_fn is not None:
        sl_d = np.linspace(d_min, d_max, 600)
        _haq_ogg = _get_haq_ogg()
        sl_v = np.array([float(np.interp(float(age_fn(dd)), _haq_ogg[:, 0], _haq_ogg[:, 1])) for dd in sl_d])

    # Figure
    fig = plt.figure(figsize=(26, 22), facecolor="white")
    gs = gridspec.GridSpec(
        1,
        6,
        figure=fig,
        width_ratios=[5.5, 0.65, 3.2, 2.1, 2.4, 1.7],
        wspace=0.03,
        left=0.065,
        right=0.985,
        top=0.905,
        bottom=0.055,
    )

    ax_gr = fig.add_subplot(gs[0, 0])
    ax_lt = fig.add_subplot(gs[0, 1], sharey=ax_gr)
    ax_pkg = fig.add_subplot(gs[0, 2], sharey=ax_gr)
    ax_dep = fig.add_subplot(gs[0, 3], sharey=ax_gr)
    ax_sl = fig.add_subplot(gs[0, 4], sharey=ax_gr)
    ax_age = fig.add_subplot(gs[0, 5], sharey=ax_gr)

    for ax in [ax_gr, ax_lt, ax_pkg, ax_dep, ax_sl, ax_age]:
        ax.set_ylim(d_max + pad, d_min - pad)
        ax.set_facecolor("#FAFAFA")
        for sp in ax.spines.values():
            sp.set_color("#BDBDBD")
            sp.set_linewidth(0.5)

    # Track 0: GR Log
    ax_gr.set_facecolor("white")
    if dep_f is not None and gr_f is not None:
        _plot_gr_conventional(
            ax_gr,
            dep_f,
            gr_f,
            config.gr_min_api,
            config.gr_max_api,
            config.gr_cut_api,
            config.sand_color,
            config.shale_color,
            config.curve_color,
            alpha=0.58,
        )

    for gv in range(0, int(config.gr_max_api) + 1, 25):
        lc = "#BDBDBD" if gv == config.gr_cut_api else "#EEEEEE"
        lw = 0.9 if gv == config.gr_cut_api else 0.5
        ax_gr.axvline(gv, color=lc, lw=lw, zorder=0)

    ax_gr.set_xticks(range(0, int(config.gr_max_api) + 1, 25))
    ax_gr.tick_params(axis="x", labelsize=8, pad=2)
    ax_gr.set_xlabel("GR  (API)", fontsize=9, labelpad=3)
    ax_gr.set_ylabel("Depth  MD (m)", fontsize=10, labelpad=5)
    d_ticks = np.arange(np.ceil(d_min / 50) * 50, d_max + 50, 50)
    ax_gr.set_yticks(d_ticks)
    ax_gr.tick_params(axis="y", labelsize=8.5, length=4)
    ax_gr.yaxis.grid(color="#EEEEEE", lw=0.4, zorder=0)

    # Interval zone labels
    for ii, ivl in enumerate(intervals):
        ic = IVL_COLORS[ii % len(IVL_COLORS)]
        t = float(ivl.top if hasattr(ivl, "top") else ivl.get("T", 0))
        b = float(ivl.base if hasattr(ivl, "base") else ivl.get("B", 0))
        zn = str(ivl.zone if hasattr(ivl, "zone") else ivl.get("Z", ""))
        for md in (t, b):
            if d_min - 5 <= md <= d_max + 5:
                ax_gr.axhline(md, color=ic, lw=1.6, alpha=0.85, zorder=5)
        mid = (t + b) / 2
        if d_min <= mid <= d_max:
            age = _parse_zone_age(zn, nn_ages)
            a_s = f"{age[0]:.1f}–{age[1]:.1f} Ma" if age else ""
            ax_gr.text(
                3,
                mid,
                f"{zn}\n{a_s}",
                fontsize=6,
                va="center",
                ha="left",
                zorder=6,
                color=ic,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=ic, alpha=0.88, lw=0.9),
            )

    ax_gr.set_title(
        f"GR Log  (API)\n0 ← Sand  |  {int(config.gr_cut_api)} cut  |  Shale → {int(config.gr_max_api)}",
        fontsize=10,
        fontweight="bold",
        pad=6,
    )
    ax_gr.legend(
        handles=[
            mpatches.Patch(color=config.sand_color, label=f"Sand  (<{int(config.gr_cut_api)} API)"),
            mpatches.Patch(color=config.shale_color, label=f"Shale (>{int(config.gr_cut_api)} API)"),
        ],
        loc="lower right",
        fontsize=7,
        framealpha=0.95,
        handlelength=1.2,
    )

    # Track 1: Lithology
    lit_colors = {
        "Clean Sand": config.sand_color,
        "Silty Sand": "#FFB300",
        "Shaly Sand": "#A1887F",
        "Shale": "#5D4037",
        "Heterolithic": "#90A4AE",
    }
    ax_lt.set_xlim(0, 1)
    ax_lt.set_xticks([])
    ax_lt.tick_params(axis="y", left=False, labelleft=False)
    ax_lt.set_title("Litho\n(GR)", fontsize=8.5, fontweight="bold", pad=6)

    if sensing_bins:
        for b in sensing_bins:
            tc = max(b["TOP"], d_min)
            bc = min(b["BASE"], d_max)
            if tc >= bc:
                continue
            from .seqstrat import litho_classify

            lc = lit_colors.get(
                litho_classify(b.get("MEAN"), config.gr_sand_api, config.gr_silt_api, config.gr_shaly_api),
                "#BDBDBD",
            )
            ax_lt.axhspan(tc, bc, color=lc, alpha=1.0, lw=0)
            if b.get("N", 0) < 3:
                ax_lt.axhspan(tc, bc, facecolor="none", edgecolor="white", hatch="xxx", lw=0, alpha=0.55)

    ax_lt.legend(
        handles=[mpatches.Patch(color=c, label=k) for k, c in lit_colors.items()],
        loc="lower center",
        fontsize=4.5,
        framealpha=0.95,
        bbox_to_anchor=(0.5, -0.01),
        ncol=1,
        handlelength=1.0,
    )

    # Track 2: Geological Package + Motif + Seq Strat
    ax_pkg.set_xlim(0, 1)
    ax_pkg.set_xticks([])
    ax_pkg.tick_params(axis="y", left=False, labelleft=False)
    ax_pkg.set_title("Geological Package\nMotif Schematic  |  Systems Tract", fontsize=10, fontweight="bold", pad=6)

    for pkg in packages:
        top_c = max(pkg["TOP"], d_min)
        base_c = min(pkg["BASE"], d_max)
        if top_c >= base_c:
            continue
        tract = pkg.get("SEQ_STRAT", "UNCERTAIN")
        motif = pkg.get("HUMAN_MOTIF", "Heterolithic")
        em = pkg.get("EXTRAP_MOTIF")
        tc = TRACT_COLORS.get(tract, "#BDBDBD")
        mc = MOTIF_COLORS.get(motif, "#90A4AE")
        mid = (top_c + base_c) / 2

        # Systems tract background
        ax_pkg.axhspan(top_c, base_c, xmin=0.43, xmax=1.0, color=tc, alpha=0.38, lw=0, zorder=2)

        # Motif schematic
        if motif == "Heterolithic" and em:
            ec = MOTIF_COLORS.get(em, "#90A4AE")
            _draw_motif_schematic(ax_pkg, em, ec, top_c, base_c, alpha_override=0.28)
            _draw_motif_schematic(ax_pkg, "Heterolithic", mc, top_c, base_c)
        else:
            _draw_motif_schematic(ax_pkg, motif, mc, top_c, base_c)

        ax_pkg.axhline(top_c, color="#455A64", lw=1.5, zorder=7)

        # Label
        thick_d = base_c - top_c
        if motif == "Heterolithic" and em:
            txt = (
                f"~{SHORT_MOTIF.get(em, em[:6])}\n"
                f"[extrap·{pkg.get('EXTRAP_CONF', '?')[:1]}]\n"
                f"≈HET\n{int(pkg['TOP'])}–{int(pkg['BASE'])} m"
            )
        else:
            txt = (
                f"{tract}\n{SHORT_MOTIF.get(motif, motif[:8])}\n"
                f"{int(pkg['TOP'])}–{int(pkg['BASE'])} m\n"
                f"{pkg.get('GR_MEAN', '?'):.0f} API"
                if pkg.get("GR_MEAN")
                else f"{tract}\n{SHORT_MOTIF.get(motif, motif[:8])}\n{int(pkg['TOP'])}–{int(pkg['BASE'])} m"
            )

        if thick_d >= 20:
            ax_pkg.text(
                0.71,
                mid,
                txt,
                ha="center",
                va="center",
                fontsize=6.5,
                fontweight="bold",
                color="#1A1A2E",
                zorder=8,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", alpha=0.72, lw=0),
            )

    ax_pkg.legend(
        handles=[
            mpatches.Patch(color=TRACT_COLORS[k], alpha=0.55, label=k) for k in ("LST", "TST", "HST", "FSST", "CS", "UNCERTAIN")
        ],
        loc="lower right",
        fontsize=6.5,
        framealpha=0.95,
        handlelength=1.0,
        ncol=2,
    )

    # Track 3: Depositional Environment
    ax_dep.set_xlim(0, 1)
    ax_dep.set_xticks([])
    ax_dep.tick_params(axis="y", left=False, labelleft=False)
    ax_dep.set_title("Depositional\nEnvironment (EOD)", fontsize=10, fontweight="bold", pad=6, color="#006064")

    for ivl in intervals:
        t = float(ivl.top if hasattr(ivl, "top") else ivl.get("T", 0))
        b = float(ivl.base if hasattr(ivl, "base") else ivl.get("B", 0))
        top_c, base_c = max(t, d_min), min(b, d_max)
        if top_c >= base_c:
            continue
        de = str(ivl.depo_env if hasattr(ivl, "depo_env") else ivl.get("D", ""))
        lbl, col = depo_eod.get(de, (de, (0.8, 0.8, 0.8)))
        rank = depo_rank.get(de, 0)
        ax_dep.axhspan(top_c, base_c, color=col, alpha=0.92)
        ax_dep.axhline(top_c, color="white", lw=1.2)
        brt = 0.299 * col[0] + 0.587 * col[1] + 0.114 * col[2]
        fc = "white" if brt < 0.55 else "#1A1A2E"
        if base_c - top_c >= 40:
            ax_dep.text(
                0.5,
                (top_c + base_c) / 2,
                f"{lbl}\n[Rank {rank}]\n{int(t)}–{int(b)} m",
                ha="center",
                va="center",
                fontsize=7,
                color=fc,
                fontweight="bold",
                zorder=5,
            )
        elif base_c - top_c >= 15:
            ax_dep.text(
                0.5, (top_c + base_c) / 2, lbl, ha="center", va="center", fontsize=6.5, color=fc, fontweight="bold", zorder=5
            )

    # Track 4: Sea Level
    ax_sl.tick_params(axis="y", left=False, labelleft=False)
    ax_sl.set_facecolor("#F0F7FF")
    ax_sl.set_title("Sea Level\n(Haq & Ogg 2024)", fontsize=9, fontweight="bold", pad=6, color="#0277BD")

    if sl_v is not None:
        sl_mn, sl_mx = float(np.nanmin(sl_v)), float(np.nanmax(sl_v))
        ax_sl.set_xlim(sl_mn - 20, sl_mx + 30)
        for gv in range(-100, 200, 25):
            ax_sl.axvline(gv, color="#BBDEFB", lw=0.4, zorder=0)
        ax_sl.axvline(0, color="#546E7A", lw=1.0, ls="--", alpha=0.85, zorder=2)
        ax_sl.fill_betweenx(sl_d, 0, sl_v, where=(sl_v >= 0), color="#90CAF9", alpha=0.82)
        ax_sl.fill_betweenx(sl_d, 0, sl_v, where=(sl_v < 0), color="#FFCC80", alpha=0.82)
        ax_sl.plot(sl_v, sl_d, color="#1565C0", lw=2.0, zorder=3)
        ax_sl.set_xlabel("ΔSL (m)", fontsize=8)
        ax_sl.tick_params(axis="x", labelsize=7)

    # Track 5: Age
    ax_age.set_xlim(0, 1)
    ax_age.set_xticks([])
    ax_age.tick_params(axis="y", left=False, labelleft=False)
    ax_age.set_title("Age\n(Ma + NN Zone)", fontsize=9, fontweight="bold", pad=6)

    NN_BG = {
        "NN4": "#FFF3E0",
        "NN5": "#FFF9C4",
        "NN6": "#F0F4C3",
        "NN7": "#DCEDC8",
        "NN8": "#C8E6C9",
        "NN9": "#B2DFDB",
        "NN10": "#B3E5FC",
        "NN11": "#BBDEFB",
        "NN11A": "#C5CAE9",
        "NN11B": "#D1C4E9",
        "NN11C": "#E8EAF6",
    }
    for ivl in intervals:
        t = float(ivl.top if hasattr(ivl, "top") else ivl.get("T", 0))
        b = float(ivl.base if hasattr(ivl, "base") else ivl.get("B", 0))
        top_c, base_c = max(t, d_min), min(b, d_max)
        if top_c >= base_c:
            continue
        zn = str(ivl.zone if hasattr(ivl, "zone") else ivl.get("Z", ""))
        age = _parse_zone_age(zn, nn_ages)
        nn_key = next((k for k in NN_BG if k.upper() in zn.upper()), None)
        if nn_key:
            ax_age.axhspan(top_c, base_c, color=NN_BG[nn_key], alpha=0.85)
        ax_age.axhline(top_c, color="#9E9E9E", lw=0.7)
        mid_a = (top_c + base_c) / 2
        if age and base_c - top_c >= 20:
            ax_age.text(0.5, top_c + 2, f"{age[0]:.1f} Ma", ha="center", va="top", fontsize=7, color="#1A237E", fontweight="bold")
            ax_age.text(0.5, mid_a, zn, ha="center", va="center", fontsize=5.5, color="#37474F", style="italic")
            ax_age.text(0.5, base_c - 2, f"{age[1]:.1f} Ma", ha="center", va="bottom", fontsize=6, color="#546E7A")
        elif age:
            ax_age.text(0.5, mid_a, f"{age[0]:.1f}", ha="center", va="center", fontsize=6, color="#1A237E", fontweight="bold")

    # Title
    fig.suptitle(
        f"{config.project} — {well_id}   |   GR Log · Litho · Geological Package · "
        f"Seq Strat · Depo Env · Sea Level\n"
        f"Conv. GR shading (right-fill): sand=yellow (<{int(config.gr_cut_api)} API)  "
        f"|  shale=brown (>{int(config.gr_cut_api)} API)  "
        f"|  {len(packages)} packages  |  net sand cut = {int(config.gr_cut_api)} API",
        fontsize=11,
        fontweight="bold",
        color="#1A1A2E",
        y=0.978,
    )

    # Save
    safe = well_id.replace(" ", "_").replace("-", "")
    out = os.path.join(output_dir, f"{config.project}_well_{safe}.png")
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info(f"  PNG: {out}")
    return out


def generate_correlation_panel(
    well_data: dict[str, dict],
    all_packages: list[dict],
    config: ProjectConfig,
    output_dir: str = "output",
    dpi: int = 180,
    now_ts: str = "",
) -> str | None:
    """Generate multi-well correlation panel with GR shading and systems tract stripe."""
    well_order = config.well_order or list(well_data.keys())
    n = len(well_order)
    if n == 0:
        return None

    fig, axes = plt.subplots(1, n, figsize=(max(38, n * 4.5), 24), facecolor="white")
    fig.subplots_adjust(wspace=0.10, left=0.04, right=0.97, top=0.915, bottom=0.07)

    if n == 1:
        axes = [axes]

    ax_info = {}
    default_depo_rank()
    default_nn_ages()

    for col_i, well_id in enumerate(well_order):
        ax = axes[col_i]
        ax.set_facecolor("#FAFAFA")
        for sp in ax.spines.values():
            sp.set_color("#BDBDBD")
            sp.set_linewidth(0.5)

        wdata = well_data.get(well_id)
        pkgs = [p for p in all_packages if p["WELL"] == well_id]
        config.intervals.get(well_id, [])

        WELL_COLORS[col_i % len(WELL_COLORS)]
        if wdata is None or not pkgs:
            ax.text(0.5, 0.5, "NO DATA", transform=ax.transAxes, ha="center", va="center", fontsize=9, color="#9E9E9E")
            ax.set_title(well_id, fontsize=8, fontweight="bold", pad=4)
            ax_info[well_id] = (ax, 0, 1)
            continue

        d_min = float(min(p["TOP"] for p in pkgs))
        d_max = float(max(p["BASE"] for p in pkgs))
        d_rng = d_max - d_min
        ax.set_ylim(d_max + d_rng * 0.05, d_min - d_rng * 0.05)
        ax_info[well_id] = (ax, d_min, d_max)

        dep = wdata.get("depth")
        gr = wdata.get("gr")
        if dep is not None and gr is not None:
            mask = (~np.isnan(dep)) & (~np.isnan(gr)) & (dep >= d_min - 5) & (dep <= d_max + 5)
            dep_f, gr_f = dep[mask], gr[mask]
            if len(dep_f) > 6000:
                s = len(dep_f) // 6000 + 1
                dep_f = dep_f[::s]
                gr_f = gr_f[::s]
            _plot_gr_conventional(
                ax,
                dep_f,
                gr_f,
                config.gr_min_api,
                config.gr_max_api,
                config.gr_cut_api,
                config.sand_color,
                config.shale_color,
                config.curve_color,
                alpha=0.62,
            )

        for gv in range(0, int(config.gr_max_api) + 1, 25):
            ax.axvline(gv, color="#EEEEEE", lw=0.4, zorder=0)

        # Systems tract stripe
        for pkg in pkgs:
            top_c = max(pkg["TOP"], d_min)
            base_c = min(pkg["BASE"], d_max)
            if top_c >= base_c:
                continue
            tract = pkg.get("SEQ_STRAT", "UNCERTAIN")
            tc = TRACT_COLORS.get(tract, "#BDBDBD")
            ax.barh(
                y=(top_c + base_c) / 2,
                width=config.gr_max_api * 0.20,
                height=base_c - top_c,
                left=config.gr_max_api * 0.80,
                color=tc,
                alpha=0.80,
                zorder=5,
                lw=0,
            )
            ax.axhline(top_c, color="#B0BEC5", lw=0.6, ls="--", zorder=4)
            if base_c - top_c >= 30:
                motif = pkg.get("HUMAN_MOTIF", "?")
                ax.text(
                    config.gr_max_api * 0.90,
                    (top_c + base_c) / 2,
                    f"{tract}\n{SHORT_MOTIF.get(motif, '?')}",
                    fontsize=4.5,
                    va="center",
                    ha="center",
                    color="white",
                    fontweight="bold",
                    zorder=6,
                )

        d_ticks = np.arange(np.ceil(d_min / 100) * 100, d_max + 100, 100)
        ax.set_yticks(d_ticks)
        ax.tick_params(axis="y", labelsize=7 if col_i == 0 else 0, left=(col_i == 0), length=3)
        ax.tick_params(axis="x", labelsize=6)
        ax.set_xticks([0, 50, 100, 150])
        ax.set_xlabel("GR (API)", fontsize=6.5)
        if col_i == 0:
            ax.set_ylabel("Depth MD (m)", fontsize=8)
        ax.yaxis.grid(color="#EEEEEE", lw=0.3, zorder=0)
        ax.set_title(well_id, fontsize=7.5, fontweight="bold", pad=4, color="#1A237E")

    fig.suptitle(
        f"{config.project}  —  Correlation Panel ({n} wells)\n"
        f"GR conv. shading: right-fill (sand=yellow / shale=brown)  "
        f"|  Net sand cut = {int(config.gr_cut_api)} API  |  "
        f"Seq Strat: LST / TST / HST / FSST / CS",
        fontsize=11,
        fontweight="bold",
        color="#1A1A2E",
        y=0.998,
    )

    fig.legend(
        handles=[
            mpatches.Patch(color=TRACT_COLORS[k], alpha=0.75, label=k) for k in ("LST", "TST", "HST", "FSST", "CS", "UNCERTAIN")
        ],
        loc="lower center",
        ncol=6,
        fontsize=7.5,
        framealpha=0.95,
        bbox_to_anchor=(0.5, 0.01),
    )

    out = os.path.join(output_dir, f"{config.project}_CORRELATION.png")
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info(f"  PNG: {out}")
    return out


def _parse_zone_age(zone: str, nn_ages: dict):
    """Parse NN zone age from zone string."""
    z = zone.upper().replace(" ", "_")
    if z in nn_ages:
        return nn_ages[z]
    parts = [p for p in z.replace("-", "_").split("_") if p in nn_ages]
    if parts:
        return (min(nn_ages[p][0] for p in parts), max(nn_ages[p][1] for p in parts))
    return None


def _get_haq_ogg():
    """Return interpolated Haq & Ogg 2024 sea level curve."""
    return np.array(
        [
            [0, 0],
            [0.12, -120],
            [0.40, 10],
            [0.80, -60],
            [1.20, 20],
            [1.80, -20],
            [2.50, 30],
            [3.00, 50],
            [3.60, 35],
            [4.20, 45],
            [5.00, -80],
            [5.40, 60],
            [5.90, 40],
            [6.40, 25],
            [7.00, 35],
            [7.50, 20],
            [8.00, 45],
            [8.60, 30],
            [9.00, 55],
            [9.50, 40],
            [10.00, 25],
            [10.50, 35],
            [11.00, 50],
            [11.50, 55],
            [12.00, 65],
            [12.50, 50],
            [13.00, 30],
            [13.50, 20],
            [14.00, 55],
            [14.50, 70],
            [15.00, 60],
            [16.00, 50],
            [17.00, 40],
            [18.00, 30],
            [20.00, 35],
            [22.00, 20],
            [25.00, 15],
        ]
    )
