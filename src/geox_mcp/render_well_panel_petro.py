"""Well-panel render with petrophysical interpretation + earth meaning.

Uses open LAS (lasio) + geox_1d / compute_las_physics transforms.
Evidence: input curves OBSERVED; Vsh/φ/Sw DERIVED with stated assumptions.
"""

from __future__ import annotations

import base64
import fcntl
import hashlib
import io
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

# Open LAS registry (local copies)
OPEN_LAS_REGISTRY: dict[str, Path] = {
    "15/9-19": Path("/root/GEOX/data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las"),
    "15-9-19": Path("/root/GEOX/data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las"),
    "volve-15-9-19": Path("/root/GEOX/data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las"),
    "volve": Path("/root/GEOX/data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las"),
    "q15_15_9_19": Path("/root/GEOX/data/real_wells/q15_15_9_19/q15_15_9_19.las"),
    "f02-1": Path("/root/GEOX/data/wells/marmousi-F02-1.las"),
    "f03-2": Path("/root/GEOX/data/wells/marmousi-F03-2.las"),
    "f06-1": Path("/root/GEOX/data/wells/marmousi-F06-1.las"),
    "marmousi-f02-1": Path("/root/GEOX/data/wells/marmousi-F02-1.las"),
}

_ALIAS = {
    "depth": ("DEPT", "DEPTH", "MD", "TVD"),
    "gr": ("GR", "GR_EDTC", "SGR", "CGR", "GAMMA"),
    "rt": ("RDEP", "RT", "ILD", "LLD", "RD", "AT90", "RMED", "ILM"),
    "rhob": ("RHOB", "DEN", "RHOZ", "ZDEN", "DENS"),
    "nphi": ("NPHI", "NEU", "TNPH", "NPOR", "PHIN"),
    "dt": ("DT", "AC", "DTCO", "DTC", "SONIC"),
}


def resolve_las(well_id: str, las_path: str | None = None) -> Path | None:
    if las_path:
        p = Path(las_path).expanduser()
        if p.is_file():
            return p
    key = (well_id or "").strip().lower().replace("_", "-")
    compact = key.replace("/", "-").replace(" ", "")
    for k, path in OPEN_LAS_REGISTRY.items():
        kk = k.replace("/", "-")
        if compact == kk or compact in kk or kk in compact:
            if path.is_file():
                return path
    for root in (
        Path("/root/GEOX/data/geox_las"),
        Path("/root/GEOX/data/real_wells"),
        Path("/root/GEOX/data/wells"),
    ):
        if not root.exists():
            continue
        for p in root.rglob("*.las"):
            if compact in p.stem.lower().replace("_", "-"):
                return p
    return None


def _pick(las_obj, role: str) -> tuple[str | None, np.ndarray | None]:
    keys = {str(k).upper(): k for k in las_obj.keys()}
    for alias in _ALIAS[role]:
        if alias.upper() in keys:
            return alias, np.asarray(las_obj[keys[alias.upper()]], dtype=float)
    return None, None


def _pct(a: np.ndarray, q: float) -> float | None:
    f = a[np.isfinite(a)]
    if f.size == 0:
        return None
    return float(np.percentile(f, q))


def _mean(a: np.ndarray) -> float | None:
    f = a[np.isfinite(a)]
    if f.size == 0:
        return None
    return float(np.mean(f))


def gr_motif(depth: np.ndarray, gr: np.ndarray) -> dict[str, Any]:
    """Coarse GR shape → depositional motif (INTERPRETED, low confidence)."""
    m = np.isfinite(depth) & np.isfinite(gr)
    if m.sum() < 20:
        return {"motif": "unknown", "confidence": 0.2, "note": "insufficient GR samples"}
    d, g = depth[m], gr[m]
    # normalize depth 0..1 for regression
    x = (d - d.min()) / max(d.max() - d.min(), 1e-9)
    # linear trend of GR vs depth
    coef = np.polyfit(x, g, 1)
    slope = float(coef[0])
    g_p10, g_p90 = float(np.percentile(g, 10)), float(np.percentile(g, 90))
    amp = g_p90 - g_p10
    # blockiness: rolling variance ratio
    if g.size > 40:
        w = max(5, g.size // 20)
        kernel = np.ones(w) / w
        smooth = np.convolve(g, kernel, mode="same")
        residual = np.nanstd(g - smooth)
    else:
        residual = float(np.nanstd(g))

    if abs(slope) < amp * 0.15 and residual < amp * 0.35:
        motif, meaning = "blocky", "Sharp-ish GR block — possible clean sand body or thick shale package"
    elif slope > amp * 0.25:
        motif, meaning = "fining-up", "GR increases upward — fining-upward package (channel-fill / abandonment?)"
    elif slope < -amp * 0.25:
        motif, meaning = "coarsening-up", "GR decreases upward — coarsening-upward (prograding shoreline / mouth bar?)"
    elif residual > amp * 0.5:
        motif, meaning = "serrated", "Highly serrated GR — heterolithic / thin-bedded mixed lithology"
    else:
        motif, meaning = "transitional", "Mixed GR character — no single strong stacking pattern in window"

    return {
        "motif": motif,
        "meaning": meaning,
        "gr_slope_api_per_norm_depth": round(slope, 2),
        "gr_p10": round(g_p10, 1),
        "gr_p90": round(g_p90, 1),
        "confidence": 0.45,
        "epistemic": "INTERPRETED",
    }


def earth_meaning_decode(
    *,
    well_id: str,
    depth_top: float,
    depth_base: float,
    vsh: np.ndarray,
    phi_e: np.ndarray,
    sw: np.ndarray | None,
    gr: np.ndarray | None,
    depth: np.ndarray,
    curve_map: dict[str, str],
    license_note: str | None,
    net_frac: float,
    stats: dict[str, Any],
) -> dict[str, Any]:
    """Human-readable earth meaning from DERIVED petro + INTERPRETED motif."""
    motif = gr_motif(depth, gr) if gr is not None else {"motif": "unknown", "meaning": "no GR"}

    vsh_m = _mean(vsh)
    phi_m = _mean(phi_e)
    sw_m = _mean(sw) if sw is not None else None

    # Reservoir quality class (rules of thumb — INTERPRETED)
    if vsh_m is not None and phi_m is not None:
        if vsh_m < 0.3 and phi_m >= 0.12 and net_frac >= 0.25:
            rq = "fair–good reservoir potential in window (DER→INT)"
        elif vsh_m < 0.5 and phi_m >= 0.08:
            rq = "marginal reservoir quality — silty / mixed net"
        elif vsh_m >= 0.5:
            rq = "shale-dominated window — seal / non-reservoir character"
        else:
            rq = "tight / low-φ window — limited conventional storage"
    else:
        rq = "insufficient curves for reservoir quality call"

    fluid = "unknown — need Rw calibration + pressure for fluid certainty"
    if sw_m is not None and phi_m is not None:
        if sw_m <= 0.55 and phi_m >= 0.10 and (vsh_m or 1) < 0.45:
            fluid = (
                "possible hydrocarbon-bearing interval (Archie Sw low) — "
                "HYPOTHESIS until Rw/m/n calibrated and MDT/DST confirm"
            )
        elif sw_m >= 0.75:
            fluid = "water-wet / high Sw character (Archie) — brine-filled more likely"
        else:
            fluid = "mixed / intermediate Sw — transition or shaly sand; do not force fluid call"

    bullets = [
        f"Window {depth_top:.1f}–{depth_base:.1f} m MD on well {well_id}.",
        f"GR motif: {motif.get('motif')} — {motif.get('meaning')}",
        f"Vsh mean≈{_fmt(vsh_m)} (Larionov/linear GR), φe mean≈{_fmt(phi_m)} (density–neutron composite, clay-corrected).",
        f"Net flag (φe≥0.08 & Vsh≤0.5" + (" & Sw≤0.7" if sw is not None else "") + f"): N/G≈{net_frac:.0%}.",
        f"Reservoir read: {rq}",
        f"Fluid read: {fluid}",
        "Assumptions: ρma=2.65 g/cc, ρf=1.0, Archie a=1 m=2 n=2, Rw=0.03 Ω·m (North Sea-ish default — NOT measured).",
        "Epistemic: curves OBSERVED · Vsh/φ/Sw DERIVED · motif/fluid INTERPRETED–HYPOTHESIS.",
    ]
    if license_note:
        bullets.append(f"Data: {license_note}")

    return {
        "title": f"Earth meaning — {well_id}",
        "motif": motif,
        "reservoir_quality": rq,
        "fluid_hypothesis": fluid,
        "stats": stats,
        "bullets": bullets,
        "curve_map": curve_map,
        "epistemic_stack": {
            "curves": "OBSERVED",
            "vsh_phi_sw": "DERIVED",
            "motif_fluid": "INTERPRETED/HYPOTHESIS",
        },
    }


def _fmt(v: float | None) -> str:
    if v is None:
        return "n/a"
    if abs(v) < 1:
        return f"{v:.3f}"
    return f"{v:.2f}"


def _style(ax) -> None:
    ax.grid(True, color="#333", ls="--", alpha=0.7)
    ax.set_facecolor("#0f0f1a")
    ax.tick_params(colors="white", labelsize=8)
    for s in ("bottom", "top", "left", "right"):
        ax.spines[s].set_color("#555")


def render_interpreted_panel(
    *,
    well_id: str,
    depth_top: float | None = None,
    depth_base: float | None = None,
    las_path: str | None = None,
    rw: float = 0.03,
    matrix_density: float = 2.65,
    fluid_density: float = 1.0,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image as PILImage
    from PIL.PngImagePlugin import PngInfo

    _wid = (well_id or "").strip()
    if not _wid:
        return {"ok": False, "isError": True, "message": "well_id is required"}

    resolved = resolve_las(_wid, las_path)
    if resolved is None:
        return {
            "ok": False,
            "isError": True,
            "message": f"No open LAS resolved for well_id={_wid}. Pass las_path= or use volve / 15/9-19.",
        }

    import lasio
    from geox_core.benchmarks.geox_001_las_physics import compute_las_physics

    las = lasio.read(str(resolved), ignore_header_errors=True)
    dname, depth_raw = _pick(las, "depth")
    if depth_raw is None:
        return {"ok": False, "isError": True, "message": "LAS has no depth curve"}

    curve_map: dict[str, str] = {"depth": dname or "DEPT"}
    series: dict[str, np.ndarray] = {"DEPT": depth_raw}
    for role in ("gr", "rt", "rhob", "nphi", "dt"):
        name, arr = _pick(las, role)
        if name is not None and arr is not None:
            # map to canonical keys for compute_las_physics
            canon = {"gr": "GR", "rt": "RDEP", "rhob": "RHOB", "nphi": "NPHI", "dt": "DT"}[role]
            # also keep aliases
            series[canon] = arr
            if role == "rt":
                series["RT"] = arr
            if role == "rhob":
                series["DEN"] = arr
            if role == "nphi":
                series["NEU"] = arr
            if role == "dt":
                series["AC"] = arr
            curve_map[role] = name

    d_min, d_max = float(np.nanmin(depth_raw)), float(np.nanmax(depth_raw))
    if depth_top is None or depth_base is None:
        # Prefer densest RHOB window
        if "RHOB" in series:
            finite_d = depth_raw[np.isfinite(series["RHOB"]) & np.isfinite(depth_raw)]
            if finite_d.size > 50:
                lo, hi = float(finite_d.min()), float(finite_d.max())
                mid = 0.5 * (lo + hi)
                half = min(100.0, 0.5 * (hi - lo))
                depth_top = mid - half if depth_top is None else depth_top
                depth_base = mid + half if depth_base is None else depth_base
        if depth_top is None:
            depth_top = d_min + 0.35 * (d_max - d_min)
        if depth_base is None:
            depth_base = min(d_max, float(depth_top) + 200.0)
    depth_top = float(depth_top)
    depth_base = float(depth_base)
    if depth_base <= depth_top:
        depth_base = depth_top + 50.0

    mask = np.isfinite(depth_raw) & (depth_raw >= depth_top) & (depth_raw <= depth_base)
    if mask.sum() < 10:
        return {
            "ok": False,
            "isError": True,
            "message": f"Too few samples in {depth_top}-{depth_base} m",
        }

    windowed: dict[str, np.ndarray] = {}
    for k, v in series.items():
        windowed[k] = np.asarray(v, dtype=float)[mask]
    depth = windowed["DEPT"]

    # Need DT for compute_las_physics — if missing, inject synthetic mild DT from Gardner inverse skip
    if "DT" not in windowed and "AC" not in windowed:
        # approximate DT from density if possible else constant 90 us/ft
        if "RHOB" in windowed:
            rh = windowed["RHOB"].copy()
            if np.nanmedian(rh) > 10:
                rh = rh / 1000.0
            # rough: higher density → lower DT
            windowed["DT"] = np.clip(200 - 50 * (rh - 2.0), 50, 140)
            curve_map["dt"] = "DT_proxy_from_RHOB"
        else:
            windowed["DT"] = np.full_like(depth, 90.0)
            curve_map["dt"] = "DT_default_90"

    physics = compute_las_physics(
        windowed,
        matrix_density=matrix_density,
        fluid_density=fluid_density,
        rw=rw,
    )
    series_p = physics.get("series") or {}
    vsh = np.asarray(series_p["vsh"], dtype=float)
    phi_e = np.asarray(series_p["phi_effective"], dtype=float)
    phi_d = np.asarray(series_p.get("phi_density") or phi_e, dtype=float)
    phi_n = np.asarray(series_p.get("phi_neutron") or phi_e, dtype=float)
    sw = np.asarray(series_p["sw"], dtype=float) if series_p.get("sw") is not None else None

    # Local GR clean/shale (p5/p95) — fixed 15/150 API collapses Vsh on clean NS sands
    from geox_core.core.geox_1d import compute_sw_archie, compute_vsh_gr

    gr_w = windowed.get("GR")
    vsh_method = "larionov_default_GR_15_150"
    if gr_w is not None and np.isfinite(gr_w).sum() > 20:
        g5 = float(np.nanpercentile(gr_w, 5))
        g95 = float(np.nanpercentile(gr_w, 95))
        if (g95 - g5) >= 5.0:
            vsh = compute_vsh_gr(gr_w, gr_clean=g5, gr_shale=g95)
            vsh_method = f"larionov_local_GR_p5={g5:.1f}_p95={g95:.1f}"
            phi_t = np.clip(0.5 * (phi_d + phi_n), 0.0, 0.45)
            phi_e = np.clip(phi_t * (1.0 - vsh), 0.0, 0.4)
            rt_w = windowed.get("RDEP", windowed.get("RT"))
            if rt_w is not None:
                sw = compute_sw_archie(rt_w, phi_n, phi_e, rw=rw)

    net = (phi_e >= 0.08) & (vsh <= 0.5)
    if sw is not None:
        net = net & np.isfinite(sw) & (sw <= 0.70)
    net = net & np.isfinite(phi_e) & np.isfinite(vsh)
    net_frac = float(np.mean(net)) if net.size else 0.0

    stats = {
        "vsh_p50": _pct(vsh, 50),
        "vsh_mean": _mean(vsh),
        "phi_e_p10": _pct(phi_e, 10),
        "phi_e_p50": _pct(phi_e, 50),
        "phi_e_p90": _pct(phi_e, 90),
        "sw_p50": _pct(sw, 50) if sw is not None else None,
        "sw_mean": _mean(sw) if sw is not None else None,
        "net_to_gross": round(net_frac, 3),
        "n_samples": int(mask.sum()),
        "phi_stats_engine": physics.get("stats"),
        "vsh_method": vsh_method,
        "equations": physics.get("equations"),
        "anti_hantu": physics.get("anti_hantu"),
    }

    license_note = None
    src = str(resolved)
    if "volve" in src.lower() or "15_9_19" in src or "15/9-19" in _wid:
        license_note = "Equinor Volve open dataset (CC BY 4.0)"
    elif "marmousi" in src.lower():
        license_note = "Marmousi public demo LAS"

    meaning = earth_meaning_decode(
        well_id=_wid,
        depth_top=depth_top,
        depth_base=depth_base,
        vsh=vsh,
        phi_e=phi_e,
        sw=sw,
        gr=windowed.get("GR"),
        depth=depth,
        curve_map=curve_map,
        license_note=license_note,
        net_frac=net_frac,
        stats=stats,
    )

    # ── plot: 6 log tracks + meaning panel ──
    fig = plt.figure(figsize=(16, 9), facecolor="#0f0f1a")
    gs = fig.add_gridspec(1, 7, width_ratios=[1, 1, 1.1, 0.9, 0.9, 0.9, 1.6], wspace=0.18)
    axes = [fig.add_subplot(gs[0, i]) for i in range(6)]
    ax_txt = fig.add_subplot(gs[0, 6])
    fig.suptitle(
        f"GEOX Interpreted Well Panel — {_wid}  [{depth_top:.0f}–{depth_base:.0f} m]  ·  LAS+DER+INT",
        color="white",
        fontsize=13,
        weight="bold",
        y=0.98,
    )

    gr = windowed.get("GR")
    rt = windowed.get("RDEP", windowed.get("RT"))
    rhob = windowed.get("RHOB")
    nphi = windowed.get("NPHI")
    dt = windowed.get("DT", windowed.get("AC"))

    # Track 0 GR + net fill
    if gr is not None:
        axes[0].plot(gr, depth, color="#f1c40f", lw=0.9)
        if net.any():
            axes[0].fill_betweenx(depth, 0, gr, where=net, color="#27ae60", alpha=0.25, label="net")
        axes[0].set_xlim(0, max(150, float(np.nanpercentile(gr[np.isfinite(gr)], 98)) + 10))
    axes[0].set_title(f"GR ({curve_map.get('gr', '?')})", color="white", fontsize=9)
    _style(axes[0])
    axes[0].set_ylabel("Depth (m)", color="white")

    # Track 1 RT
    if rt is not None:
        pos = rt[np.isfinite(rt) & (rt > 0)]
        axes[1].semilogx(rt, depth, color="#2ecc71", lw=0.9)
        if pos.size:
            axes[1].set_xlim(max(0.05, float(np.percentile(pos, 1)) * 0.5), float(np.percentile(pos, 99)) * 2)
    axes[1].set_title(f"RT ({curve_map.get('rt', '?')})", color="white", fontsize=9)
    axes[1].grid(True, which="both", color="#333", ls="--", alpha=0.7)
    axes[1].set_facecolor("#0f0f1a")
    axes[1].tick_params(colors="white", labelsize=8)

    # Track 2 RHOB / NPHI
    axn = axes[2].twiny()
    if rhob is not None:
        rh = rhob.copy()
        if np.nanmedian(rh[np.isfinite(rh)]) > 10:
            rh = rh / 1000.0
        axes[2].plot(rh, depth, color="#e74c3c", lw=0.9)
        rf = rh[np.isfinite(rh)]
        if rf.size:
            axes[2].set_xlim(float(np.percentile(rf, 1)) - 0.05, float(np.percentile(rf, 99)) + 0.05)
    if nphi is not None:
        n = nphi.copy()
        if np.nanmedian(np.abs(n[np.isfinite(n)])) > 1.0:
            n = n / 100.0
        axn.plot(n, depth, color="#3498db", lw=0.9, ls="--")
        nf = n[np.isfinite(n)]
        if nf.size:
            lo, hi = float(np.percentile(nf, 1)), float(np.percentile(nf, 99))
            axn.set_xlim(hi + 0.02, lo - 0.02)
    axes[2].set_title("RHOB / NPHI", color="white", fontsize=9)
    _style(axes[2])
    axn.tick_params(colors="white", labelsize=7)

    # Track 3 Vsh
    axes[3].plot(vsh, depth, color="#e67e22", lw=0.9)
    axes[3].axvline(0.5, color="#888", ls=":", lw=0.8)
    axes[3].fill_betweenx(depth, 0, vsh, where=vsh <= 0.5, color="#e67e22", alpha=0.2)
    axes[3].set_xlim(0, 1)
    axes[3].set_title("Vsh DER", color="white", fontsize=9)
    _style(axes[3])

    # Track 4 PhiE
    axes[4].plot(phi_e, depth, color="#1abc9c", lw=0.9)
    axes[4].axvline(0.08, color="#888", ls=":", lw=0.8)
    axes[4].fill_betweenx(depth, 0, phi_e, where=net, color="#1abc9c", alpha=0.25)
    axes[4].set_xlim(0, min(0.45, max(0.2, float(np.nanpercentile(phi_e[np.isfinite(phi_e)], 99)) * 1.2)))
    axes[4].set_title("φe DER", color="white", fontsize=9)
    _style(axes[4])

    # Track 5 Sw or DT
    if sw is not None and np.isfinite(sw).any():
        axes[5].plot(sw, depth, color="#9b59b6", lw=0.9)
        axes[5].axvline(0.7, color="#888", ls=":", lw=0.8)
        axes[5].set_xlim(0, 1)
        axes[5].set_title("Sw Archie DER", color="white", fontsize=9)
    elif dt is not None:
        axes[5].plot(dt, depth, color="#9b59b6", lw=0.9)
        df = dt[np.isfinite(dt)]
        if df.size:
            axes[5].set_xlim(float(np.percentile(df, 99)) + 5, max(0, float(np.percentile(df, 1)) - 5))
        axes[5].set_title(f"DT ({curve_map.get('dt', '?')})", color="white", fontsize=9)
    _style(axes[5])

    for ax in axes:
        ax.set_ylim(depth_base, depth_top)  # depth down
        ax.tick_params(labelleft=False)
    axes[0].tick_params(labelleft=True)

    # Meaning panel
    ax_txt.set_facecolor("#12121f")
    ax_txt.set_xlim(0, 1)
    ax_txt.set_ylim(0, 1)
    ax_txt.axis("off")
    text_lines = [
        meaning["title"],
        "",
        f"Vsh p50={_fmt(stats['vsh_p50'])}  φe p50={_fmt(stats['phi_e_p50'])}",
        f"Sw p50={_fmt(stats['sw_p50'])}  N/G={stats['net_to_gross']:.0%}",
        f"n={stats['n_samples']}  motif={meaning['motif'].get('motif')}",
        "",
    ]
    for b in meaning["bullets"]:
        # wrap roughly
        words = b.split()
        line = ""
        for w in words:
            if len(line) + len(w) + 1 > 42:
                text_lines.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            text_lines.append(line)
        text_lines.append("")

    y = 0.98
    for i, line in enumerate(text_lines[:48]):
        weight = "bold" if i == 0 else "normal"
        color = "#f1c40f" if i == 0 else "#dfe6e9"
        ax_txt.text(0.02, y, line, transform=ax_txt.transAxes, fontsize=7.2, color=color, va="top", fontweight=weight, family="DejaVu Sans")
        y -= 0.028
        if y < 0.02:
            break

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, facecolor="#0f0f1a")
    plt.close()
    img_bytes = buf.getvalue()

    renders_dir = Path("/root/GEOX/data/renders")
    renders_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    safe_wid = _wid.replace("/", "-").replace(" ", "_")
    filename = f"well-panel-petro-{safe_wid}-{timestamp}.png"
    filepath = renders_dir / filename

    metadata = {
        "well_id": _wid,
        "depth_top": depth_top,
        "depth_base": depth_base,
        "generated_at": datetime.now(UTC).isoformat() + "Z",
        "actor": actor_id or "ARIF",
        "session_id": session_id or "geox_session",
        "tool": "geox_render_well_panel",
        "provenance": "OBSERVED:lasio+DERIVED:geox_1d+INTERPRETED:earth_meaning",
        "source_uri": src,
        "curve_map": json.dumps(curve_map),
        "n_samples": str(stats["n_samples"]),
        "license": license_note or "",
        "evidence_class": "OBSERVED+DERIVED+INTERPRETED",
        "rw": str(rw),
        "matrix_density": str(matrix_density),
        "phi_e_p50": str(stats["phi_e_p50"]),
        "vsh_p50": str(stats["vsh_p50"]),
        "sw_p50": str(stats["sw_p50"]),
        "net_to_gross": str(stats["net_to_gross"]),
        "motif": meaning["motif"].get("motif", ""),
    }

    pil_img = PILImage.open(io.BytesIO(img_bytes))
    meta = PngInfo()
    for k, v in metadata.items():
        meta.add_text(k, str(v))
    pil_img.save(filepath, "PNG", pnginfo=meta)
    final_bytes = filepath.read_bytes()
    image_sha = f"sha256:{hashlib.sha256(final_bytes).hexdigest()}"
    seal_token = f"SEAL-IMG-{hashlib.sha256(final_bytes).hexdigest()[:16].upper()}"

    seal_entry = {
        "entry_type": "IMAGE_SEAL",
        "token": seal_token,
        "well_id": _wid,
        "image_sha256": image_sha,
        "filename": filename,
        "filepath": str(filepath),
        "issued_at": datetime.now(UTC).isoformat() + "Z",
        "actor": actor_id or "ARIF",
        "session_id": session_id or "geox_session",
        "metadata": metadata,
        "earth_meaning": meaning,
        "epoch": datetime.now(UTC).isoformat() + "Z",
    }

    vault_dir = Path("/root/.local/share/arifos/vault999")
    vault_dir.mkdir(parents=True, exist_ok=True)
    lock_path = vault_dir / ".image_seal.lock"
    with open(lock_path, "a") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            with open(vault_dir / "image_seal_chain.jsonl", "a") as f:
                f.write(json.dumps(seal_entry) + "\n")
                f.flush()
            with open(vault_dir / "image_seal_head.json", "w") as f:
                json.dump(seal_entry, f)
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

    return {
        "ok": True,
        "tool": "geox_render_well_panel",
        "well_id": _wid,
        "seal_token": seal_token,
        "image_sha256": image_sha,
        "filepath": str(filepath),
        "metadata": metadata,
        "curve_map": curve_map,
        "provenance": metadata["provenance"],
        "source_uri": src,
        "n_samples": stats["n_samples"],
        "depth_top": depth_top,
        "depth_base": depth_base,
        "petrophysics": stats,
        "earth_meaning": meaning,
        "assumptions": {
            "matrix_density": matrix_density,
            "fluid_density": fluid_density,
            "rw": rw,
            "archie": {"a": 1.0, "m": 2.0, "n": 2.0},
            "net_cutoffs": {"phi_e_min": 0.08, "vsh_max": 0.5, "sw_max": 0.7},
        },
        "content_text": (
            f"Interpreted panel {_wid}: φe_p50={_fmt(stats['phi_e_p50'])}, "
            f"Vsh_p50={_fmt(stats['vsh_p50'])}, Sw_p50={_fmt(stats['sw_p50'])}, "
            f"N/G={stats['net_to_gross']:.0%}, motif={meaning['motif'].get('motif')}. "
            f"Seal {seal_token}. File {filepath}"
        ),
        "image_base64_len": len(base64.b64encode(final_bytes)),
    }
