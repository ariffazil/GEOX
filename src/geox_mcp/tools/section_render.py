"""Deterministic seismic-section renderer — human loop, not agent GUI.

render(section, horizons, faults, annotations) → PNG path + hashes.

- Machine loop stays in coordinates.
- Human loop gets picks on the section with receipt_hash burned in.
- No interactive editor. Matplotlib only. Idempotent for same inputs.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from geox_mcp.tools.structure_gates.geometry_adapt import adapt_framework_geometry


def _sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _points(obj: dict[str, Any]) -> list[tuple[float, float]]:
    pts = obj.get("points") or obj.get("pts") or obj.get("sticks") or obj.get("picks") or []
    out: list[tuple[float, float]] = []
    for i, p in enumerate(pts):
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            out.append((float(p[0]), float(p[1])))
        elif isinstance(p, dict):
            x = p.get("x", p.get("cmp", p.get("trace_index", i)))
            y = p.get("y", p.get("twt_ms", p.get("depth_m", p.get("sample"))))
            if x is not None and y is not None:
                out.append((float(x), float(y)))
    return out


def _load_background(image_path: str | None) -> tuple[Any, str | None]:
    """Return (array or None, input_hash)."""
    if not image_path:
        return None, None
    p = Path(image_path)
    if not p.is_file():
        return None, None
    data = p.read_bytes()
    input_hash = hashlib.sha256(data).hexdigest()
    try:
        from PIL import Image
        import numpy as np

        im = Image.open(p).convert("L")
        arr = np.asarray(im, dtype=float)
        return arr, input_hash
    except Exception:
        return None, input_hash


def render_section_overlay(
    *,
    image_path: str | None = None,
    faults: list[dict[str, Any]] | None = None,
    horizons: list[dict[str, Any]] | None = None,
    framework: dict[str, Any] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    title: str = "GEOX section · QUALIFIED_CANDIDATE",
    receipt_hash: str | None = None,
    hypothesis_id: str | None = None,
    output_path: str | None = None,
    cmp_range: tuple[float, float] | None = None,
    twt_range: tuple[float, float] | None = None,
    dpi: int = 120,
) -> dict[str, Any]:
    """Render section + fault sticks + horizon polylines → PNG.

    Coordinate convention: x = CMP / trace, y = TWT ms (increasing downward).
    If background image is present without axis calibration, geometry is
    plotted in data coordinates on a twin axis extent estimated from picks,
    or overlaid in normalized image space when cmp/twt ranges provided.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fw = adapt_framework_geometry(framework or {})
    flist = list(faults if faults is not None else (fw.get("faults") or []))
    hlist = list(horizons if horizons is not None else (fw.get("horizons") or []))
    # re-adapt standalone lists
    from geox_mcp.tools.structure_gates.geometry_adapt import adapt_fault, adapt_horizon

    flist = [adapt_fault(f) if isinstance(f, dict) else f for f in flist]
    hlist = [adapt_horizon(h) if isinstance(h, dict) else h for h in hlist]

    bg, img_hash = _load_background(image_path)

    # Collect geometry extents
    all_x: list[float] = []
    all_y: list[float] = []
    for f in flist:
        for x, y in _points(f if isinstance(f, dict) else {}):
            all_x.append(x)
            all_y.append(y)
    for h in hlist:
        for x, y in _points(h if isinstance(h, dict) else {}):
            all_x.append(x)
            all_y.append(y)

    if cmp_range:
        xmin, xmax = cmp_range
    elif all_x:
        xmin, xmax = min(all_x), max(all_x)
        pad = max(1.0, (xmax - xmin) * 0.05)
        xmin, xmax = xmin - pad, xmax + pad
    else:
        xmin, xmax = 0.0, 1.0

    if twt_range:
        tmin, tmax = twt_range
    elif all_y:
        tmin, tmax = min(all_y), max(all_y)
        pad = max(1.0, (tmax - tmin) * 0.05)
        tmin, tmax = tmin - pad, tmax + pad
    else:
        tmin, tmax = 0.0, 1000.0

    # Content hash for cache / watermark
    content = {
        "faults": [{"id": f.get("fault_id") if isinstance(f, dict) else None, "pts": _points(f if isinstance(f, dict) else {})} for f in flist],
        "horizons": [
            {"id": h.get("horizon_id") if isinstance(h, dict) else None, "pts": _points(h if isinstance(h, dict) else {})} for h in hlist
        ],
        "image_hash": img_hash,
        "hypothesis_id": hypothesis_id,
        "title": title,
    }
    content_hash = _sha(content)[:16]
    stamp = (receipt_hash or content_hash)[:16]

    fig, ax = plt.subplots(figsize=(11, 7))

    if bg is not None:
        # Show greyscale section; extent maps image to CMP/TWT if we have ranges
        ax.imshow(
            bg,
            cmap="gray",
            aspect="auto",
            extent=[xmin, xmax, tmax, tmin],  # y down
            origin="upper",
            interpolation="bilinear",
        )
    else:
        ax.set_facecolor("#1a1a1a")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(tmax, tmin)

    # Horizon palette
    h_colors = ["#00e5ff", "#76ff03", "#ffea00", "#ff9100", "#e040fb", "#18ffff"]
    for i, h in enumerate(hlist):
        if not isinstance(h, dict):
            continue
        pts = _points(h)
        if len(pts) < 2:
            continue
        xs, ys = zip(*pts, strict=False)
        hid = h.get("horizon_id") or h.get("name") or f"H{i}"
        ax.plot(xs, ys, color=h_colors[i % len(h_colors)], lw=1.4, label=str(hid), alpha=0.95)

    # Faults — red dashed
    for i, f in enumerate(flist):
        if not isinstance(f, dict):
            continue
        pts = _points(f)
        if len(pts) < 2:
            continue
        xs, ys = zip(*pts, strict=False)
        fid = f.get("fault_id") or f.get("name") or f"F{i}"
        art = bool(f.get("artifact") or f.get("artifact_flag"))
        style = ":" if art else "--"
        ax.plot(xs, ys, color="#ff1744", lw=1.8, ls=style, label=str(fid), alpha=0.95)
        # label at midpoint
        mx, my = xs[len(xs) // 2], ys[len(ys) // 2]
        ax.annotate(
            str(fid),
            (mx, my),
            color="#ff8a80",
            fontsize=8,
            fontweight="bold",
            xytext=(4, 4),
            textcoords="offset points",
        )

    # Free annotations
    for a in annotations or []:
        if not isinstance(a, dict):
            continue
        x, y = a.get("x"), a.get("y")
        text = a.get("text") or a.get("label") or ""
        if x is None or y is None:
            continue
        ax.annotate(
            str(text),
            (float(x), float(y)),
            color=a.get("color") or "#ffffff",
            fontsize=float(a.get("fontsize") or 8),
            alpha=0.9,
        )

    ax.set_xlabel("CMP / trace")
    ax.set_ylabel("TWT (ms)")
    hyp = f" · {hypothesis_id}" if hypothesis_id else ""
    ax.set_title(f"{title}{hyp}", fontsize=11, color="#e0e0e0" if bg is None else "#111")
    ax.grid(True, alpha=0.15, ls=":")

    # Legend (cap size)
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        # unique labels preserve order
        seen: set[str] = set()
        uh, ul = [], []
        for hnd, lab in zip(handles, labels, strict=False):
            if lab not in seen:
                seen.add(lab)
                uh.append(hnd)
                ul.append(lab)
        ax.legend(uh[:12], ul[:12], loc="upper right", fontsize=7, framealpha=0.7)

    # Receipt hash burned into corner
    fig.text(
        0.01,
        0.01,
        f"GEOX · receipt={stamp} · content={content_hash} · INT_SEISMIC · not SEAL",
        fontsize=7,
        color="#b0bec5",
        family="monospace",
        transform=fig.transFigure,
    )

    if output_path is None:
        fd, output_path = tempfile.mkstemp(prefix="geox_section_", suffix=".png")
        os.close(fd)
    else:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    png_bytes = Path(output_path).read_bytes()
    png_hash = hashlib.sha256(png_bytes).hexdigest()

    return {
        "ok": True,
        "tool": "geox_section_render",
        "mode": "render",
        "png_path": str(output_path),
        "png_sha256": png_hash,
        "receipt_hash": stamp,
        "content_hash": content_hash,
        "image_input_hash": img_hash,
        "n_faults": len(flist),
        "n_horizons": len(hlist),
        "hypothesis_id": hypothesis_id,
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "epistemic_label": "DER_RENDER",
        "honesty_banner": (
            "Rendered pick overlay for human review. Geometry is INT/SPEC until gated. "
            "PNG is not a SEAL. arifOS seals only."
        ),
    }


async def geox_section_render(
    image_path: str | None = None,
    faults: list[dict[str, Any]] | None = None,
    horizons: list[dict[str, Any]] | None = None,
    framework: dict[str, Any] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    title: str = "GEOX section · QUALIFIED_CANDIDATE",
    receipt_hash: str | None = None,
    hypothesis_id: str | None = None,
    output_path: str | None = None,
    calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Async entry for MCP mode=render."""
    cmp_range = None
    twt_range = None
    if isinstance(calibration, dict):
        if calibration.get("cmp_min") is not None and calibration.get("cmp_max") is not None:
            cmp_range = (float(calibration["cmp_min"]), float(calibration["cmp_max"]))
        if calibration.get("twt_min") is not None and calibration.get("twt_max") is not None:
            twt_range = (float(calibration["twt_min"]), float(calibration["twt_max"]))
    return render_section_overlay(
        image_path=image_path,
        faults=faults,
        horizons=horizons,
        framework=framework,
        annotations=annotations,
        title=title,
        receipt_hash=receipt_hash,
        hypothesis_id=hypothesis_id,
        output_path=output_path,
        cmp_range=cmp_range,
        twt_range=twt_range,
    )


def compact_gate_summary(gates: dict[str, Any] | None) -> dict[str, Any]:
    """Zen output: one line per gate + hashes, not full physics."""
    if not gates:
        return {"gates": {}, "measured": 0, "kills": [], "passes": [], "warns": [], "unmeasured": []}
    summary: dict[str, Any] = {}
    kills: list[str] = []
    passes: list[str] = []
    warns: list[str] = []
    unmeasured: list[str] = []
    for gid, g in gates.items():
        if not isinstance(g, dict):
            continue
        st = g.get("status") or g.get("verdict") or "UNMEASURED"
        line = {
            "status": st,
            "reason": (g.get("reason") or "")[:160],
            "receipt_hash": g.get("receipt_hash"),
        }
        summary[gid] = line
        if st == "KILL":
            kills.append(gid)
        elif st == "PASS":
            passes.append(gid)
        elif st == "WARN":
            warns.append(gid)
        else:
            unmeasured.append(gid)
    return {
        "gates": summary,
        "measured": len(kills) + len(passes) + len(warns),
        "kills": kills,
        "passes": passes,
        "warns": warns,
        "unmeasured": unmeasured,
    }
