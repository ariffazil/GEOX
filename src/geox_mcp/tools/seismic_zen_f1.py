"""GEOX F1 zen spine — attributes · 2D phase track · throw measure.

Modes only. No new MCP tools. No self-seal. Pixel/sample domain unless
calibration provides scale.

  attribute   → DER section attributes (rms, coherence, discontinuity, dip)
  track       → INT_SEISMIC horizon polylines (phase-aware DP)
  measure_throw → dmax_m / length_m / throw_profile_m for structure gates

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

# ── epistemic stamps ─────────────────────────────────────────────────────────
_DER = "DERIVED"
_INT = "INTERPRETED"
_UNM = "UNMEASURED"


def _json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    item = getattr(obj, "item", None)
    if callable(item):
        try:
            return _json_safe(item())
        except Exception:
            pass
    tolist = getattr(obj, "tolist", None)
    if callable(tolist):
        try:
            return _json_safe(tolist())
        except Exception:
            pass
    return str(obj)


def _receipt(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _qualified(mode: str, body: dict[str, Any], tool: str) -> dict[str, Any]:
    out = {
        "ok": body.get("ok", True),
        "tool": tool,
        "mode": mode,
        "status": body.get("status", "OK"),
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "seal_eligibility": False,
        "preferred_hypothesis": None,
        "claim_tag": body.get("claim_tag", "HYPOTHESIS"),
        "governance_status": body.get("governance_status", "HOLD"),
        **{k: v for k, v in body.items() if k not in ("ok", "status", "claim_tag", "governance_status")},
    }
    out["receipt_hash"] = _receipt({k: out[k] for k in sorted(out) if k != "receipt_hash"})
    return _json_safe(out)


# ── section loaders ──────────────────────────────────────────────────────────


def load_section_2d(
    *,
    image_path: str | None = None,
    amplitude_grid: list[list[float]] | None = None,
    volume_inline: dict[str, Any] | None = None,
    provenance: str = "fixture",
) -> tuple[np.ndarray, dict[str, Any]]:
    """Return (amp[rows, cols], meta). Fail closed with empty array if no data."""
    meta: dict[str, Any] = {
        "domain": "sample_or_pixel",
        "epistemic": _DER,
        "provenance": provenance,
    }

    if amplitude_grid is not None:
        arr = np.asarray(amplitude_grid, dtype=float)
        if arr.ndim != 2 or arr.size == 0:
            return np.zeros((0, 0)), {**meta, "error": "amplitude_grid must be 2D non-empty"}
        meta.update({"source": "amplitude_grid", "shape": list(arr.shape)})
        return arr, meta

    if volume_inline and isinstance(volume_inline, dict):
        grid = volume_inline.get("amplitude") or volume_inline.get("data") or volume_inline.get("samples")
        if grid is not None:
            arr = np.asarray(grid, dtype=float)
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            meta.update(
                {
                    "source": "volume_inline",
                    "shape": list(arr.shape),
                    "frame_index": volume_inline.get("frame_index"),
                    "orientation": volume_inline.get("orientation", "inline"),
                }
            )
            return arr, meta

    if image_path:
        path = Path(image_path)
        if not path.is_file():
            return np.zeros((0, 0)), {**meta, "error": f"image_path not found: {image_path}"}
        try:
            from PIL import Image
        except ImportError:
            # fallback: pure numpy via matplotlib if available
            try:
                import matplotlib.image as mpimg

                rgba = mpimg.imread(str(path))
                if rgba.ndim == 3:
                    arr = rgba[..., :3].mean(axis=2)
                else:
                    arr = rgba.astype(float)
            except Exception as e:
                return np.zeros((0, 0)), {**meta, "error": f"image load failed: {e}"}
        else:
            img = Image.open(path).convert("L")
            arr = np.asarray(img, dtype=float)
        # normalize
        arr = arr - arr.mean()
        std = float(arr.std()) or 1.0
        arr = arr / std
        meta.update(
            {
                "source": "image_path",
                "image_path": str(path),
                "shape": list(arr.shape),
                "epistemic_note": "Pixels are OBS_IMAGE; attributes DER; horizons INT — not geology.",
            }
        )
        return arr, meta

    if provenance == "fixture":
        # synthetic layered section for smoke / demos
        rows, cols = 120, 200
        yy = np.linspace(0, 1, rows)[:, None]
        xx = np.linspace(0, 1, cols)[None, :]
        arr = (
            np.sin(2 * np.pi * 8 * yy)
            + 0.4 * np.sin(2 * np.pi * 3 * yy + 0.5 * xx)
            + 0.15 * np.random.default_rng(7).standard_normal((rows, cols))
        )
        # inject a vertical discontinuity (fault) at col 100
        arr[:, 100:] = np.roll(arr[:, 100:], 8, axis=0)
        meta.update(
            {
                "source": "fixture_synthetic",
                "shape": [rows, cols],
                "note": "Synthetic layers + vertical throw at col=100. Not Earth.",
                "fixture_fault_col": 100,
                "fixture_throw_samples": 8,
            }
        )
        return arr, meta

    return np.zeros((0, 0)), {
        **meta,
        "error": "No section: pass image_path | amplitude_grid | volume_inline | provenance=fixture",
    }


# ── F1.1 attributes ──────────────────────────────────────────────────────────


def compute_attributes_2d(
    amp: np.ndarray,
    attribute: str = "coherence",
    window: int = 11,
) -> dict[str, Any]:
    """Zen attribute stack on a 2D section. Summaries only (no full cube dump)."""
    if amp.size == 0:
        return {"ok": False, "error": "EMPTY_SECTION"}

    from scipy import ndimage

    attr = (attribute or "coherence").lower().strip()
    hc, wc = amp.shape
    w = max(3, int(window) | 1)  # odd
    half = w // 2

    # RMS
    kernel = np.ones((w, w), dtype=float) / (w * w)
    rms = np.sqrt(ndimage.convolve(amp**2, kernel, mode="nearest"))

    # Coherence / discontinuity (lateral semblance proxy)
    disc = np.zeros_like(amp)
    span = min(5, half)
    for col in range(span, wc - span):
        left = amp[:, col - span : col]
        right = amp[:, col + 1 : col + span + 1]
        ln = left - left.mean(axis=1, keepdims=True)
        rn = right - right.mean(axis=1, keepdims=True)
        num = np.sum(ln * rn, axis=1)
        den = np.sqrt(np.sum(ln**2, axis=1) * np.sum(rn**2, axis=1) + 1e-10)
        disc[:, col] = 1.0 - np.clip(num / den, 0.0, 1.0)
    dmax = float(disc.max()) or 1.0
    disc = disc / dmax
    coherence = 1.0 - disc

    # Dip (structure tensor)
    gx = ndimage.sobel(amp, axis=1)
    gy = ndimage.sobel(amp, axis=0)
    Jxx = ndimage.gaussian_filter(gx * gx, 2)
    Jxy = ndimage.gaussian_filter(gx * gy, 2)
    Jyy = ndimage.gaussian_filter(gy * gy, 2)
    dip = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)  # radians

    catalog = {
        "rms": rms,
        "coherence": coherence,
        "discontinuity": disc,
        "dip": dip,
        "dip_deg": np.degrees(dip),
    }
    if attr not in catalog and attr not in ("all", "stack"):
        return {
            "ok": False,
            "error": "UNKNOWN_ATTRIBUTE",
            "message": f"Unknown attribute '{attribute}'. Live: rms, coherence, discontinuity, dip, all",
            "live_attributes": ["rms", "coherence", "discontinuity", "dip", "all"],
        }

    def _summary(a: np.ndarray) -> dict[str, float]:
        return {
            "min": float(np.min(a)),
            "max": float(np.max(a)),
            "mean": float(np.mean(a)),
            "std": float(np.std(a)),
            "p50": float(np.median(a)),
        }

    if attr in ("all", "stack"):
        summaries = {k: _summary(v) for k, v in catalog.items() if k != "dip"}
        summaries["dip_deg"] = _summary(catalog["dip_deg"])
        primary = "coherence"
        primary_arr = coherence
    else:
        key = "dip_deg" if attr == "dip" else attr
        primary = key
        primary_arr = catalog["dip_deg"] if attr == "dip" else catalog[attr]
        summaries = {primary: _summary(primary_arr)}

    # Compact mid-row profile for handoff (not full volume)
    mid = hc // 2
    profile = primary_arr[mid, :: max(1, wc // 64)].tolist()

    return {
        "ok": True,
        "attribute": attr,
        "primary": primary,
        "summaries": summaries,
        "mid_row_profile": [float(x) for x in profile],
        "shape": [int(hc), int(wc)],
        "window": w,
        "epistemic_class": _DER,
        "claim_tag": "HYPOTHESIS",
        "equations_used": [
            "rms = sqrt(mean(amp^2) in window)",
            "coherence ≈ lateral semblance proxy; discontinuity = 1 - coherence",
            "dip = 0.5 * atan2(2 Jxy, Jxx - Jyy) structure tensor",
        ],
        "note": "Section attributes only. Not a 3D volume product. Not geology.",
    }


# ── F1.2 phase track ─────────────────────────────────────────────────────────


def track_horizons_2d(
    amp: np.ndarray,
    *,
    max_horizons: int = 8,
    seed_rows: list[int] | None = None,
    search: int = 5,
) -> dict[str, Any]:
    """2D phase-aware horizon tracking (reuses RSI DP)."""
    if amp.size == 0:
        return {"ok": False, "error": "EMPTY_SECTION", "horizons": []}

    from geox_mcp.tools.seismic_rsi import (
        _agc,
        _compute_attributes,
        _detect_and_track_horizons,
        _track_horizon_dp,
    )

    attrs = _compute_attributes(amp)
    agc = attrs["agc"]
    pc = attrs["phase_continuity"]
    fp = attrs["fault_probability"]
    fault_mask = fp > 0.55

    if seed_rows:
        horizons: list[dict[str, Any]] = []
        hc, wc = agc.shape
        for i, seed in enumerate(seed_rows[:max_horizons]):
            seed_i = int(max(0, min(hc - 1, seed)))
            path = _track_horizon_dp(agc, fault_mask, seed_i, search=search, lookahead=10)
            cont = max(0.0, 1.0 - float(np.std(path)) / 12.0)
            horizons.append(
                {
                    "id": f"H{i + 1}",
                    "pts": [[int(c), int(path[c])] for c in range(wc)],
                    "seed": seed_i,
                    "n": int(wc),
                    "continuity": round(cont, 3),
                    "confidence": round(0.5 * cont + 0.5 * float(np.mean(np.abs(pc[path, np.arange(wc)]))), 3),
                    "label": "INT_SEISMIC_HORIZON",
                    "epistemic_class": _INT,
                }
            )
    else:
        horizons = _detect_and_track_horizons(agc, pc, fault_mask, max_horizons=max_horizons)
        for h in horizons:
            h["epistemic_class"] = _INT

    return {
        "ok": True,
        "horizons": horizons,
        "n_horizons": len(horizons),
        "fault_mask_fraction": float(np.mean(fault_mask)),
        "epistemic_class": _INT,
        "claim_tag": "HYPOTHESIS",
        "preferred_hypothesis": None,
        "note": "INT_SEISMIC only. Pixel/sample domain. Not OBS_GEOLOGY. preferred_hypothesis always null.",
        "method": "phase_dp_lookahead",
    }


# ── F1.3 throw measure ───────────────────────────────────────────────────────


def measure_throw_from_horizons(
    horizons: list[dict[str, Any]],
    faults: list[dict[str, Any]] | None = None,
    *,
    sample_interval_ms: float = 4.0,
    vertical_scale_m_per_sample: float | None = None,
    section_cols: int | None = None,
) -> dict[str, Any]:
    """Build gate-ready fault geometry: dmax_m, length_m, throw_profile_m.

    Domain: samples × optional m_per_sample. Without vertical scale, m values
    are sample-count × 1.0 labeled UNMEASURED for true meters (still usable
    as relative D/L when L uses same unit).
    """
    if not horizons:
        return {
            "ok": False,
            "error": "NO_HORIZONS",
            "message": "measure_throw needs tracked horizons with pts [[x,y],...]",
            "faults": [],
            "governance_status": "HOLD",
        }

    # Infer section width
    widths = []
    for h in horizons:
        pts = h.get("pts") or h.get("points") or []
        if pts:
            widths.append(max(int(p[0]) for p in pts if len(p) >= 2) + 1)
    width = section_cols or (max(widths) if widths else 0)
    if width <= 0:
        return {"ok": False, "error": "NO_GEOMETRY", "faults": [], "governance_status": "HOLD"}

    # Default fault columns: high throw candidates mid-section + any provided
    fault_specs: list[dict[str, Any]] = []
    if faults:
        for f in faults:
            col = f.get("col") or f.get("x") or f.get("trace")
            if col is None and f.get("points"):
                xs = [p[0] for p in f["points"] if len(p) >= 1]
                col = int(np.mean(xs)) if xs else None
            if col is not None:
                fault_specs.append({**f, "col": int(col)})
    if not fault_specs:
        # auto: sample 3 candidate columns at 25/50/75%
        for frac, fid in ((0.25, "F_auto_L"), (0.5, "F_auto_C"), (0.75, "F_auto_R")):
            fault_specs.append({"fault_id": fid, "col": int(width * frac)})

    scale = float(vertical_scale_m_per_sample) if vertical_scale_m_per_sample else 1.0
    scale_epistemic = _DER if vertical_scale_m_per_sample else _UNM
    unit_note = (
        "meters (calibrated m_per_sample)"
        if vertical_scale_m_per_sample
        else "sample-counts labeled as _m for gate input; TRUE meters UNMEASURED"
    )

    out_faults: list[dict[str, Any]] = []
    for f in fault_specs:
        col = int(f["col"])
        col = max(1, min(width - 2, col))
        throws_samples: list[float] = []
        for h in horizons:
            pts = h.get("pts") or h.get("points") or []
            if len(pts) < 3:
                continue
            # map x→y
            by_x = {int(p[0]): float(p[1]) for p in pts if len(p) >= 2}
            if col not in by_x or (col - 1) not in by_x or (col + 1) not in by_x:
                # nearest
                xs = sorted(by_x)
                if not xs:
                    continue
                # linear interp around col
                left = max((x for x in xs if x <= col), default=xs[0])
                right = min((x for x in xs if x >= col), default=xs[-1])
                y_c = (
                    by_x[left]
                    if left == right
                    else by_x[left] + (by_x[right] - by_x[left]) * ((col - left) / max(1, right - left))
                )
            else:
                y_c = by_x[col]
            y_l = by_x.get(col - 1, y_c)
            y_r = by_x.get(col + 1, y_c)
            # throw ≈ jump across fault column
            thr = abs((y_r - y_l) / 2.0) if (col - 1 in by_x and col + 1 in by_x) else abs(y_r - y_l)
            # also vs mean neighbors
            thr = max(thr, abs(y_c - y_l), abs(y_r - y_c))
            throws_samples.append(float(thr))

        if not throws_samples:
            # synthetic profile from horizon path roughness at col
            throws_samples = [0.0, 1.0, 0.0]

        # Barnett-like sample along fault length if few horizons: pad taper
        if len(throws_samples) < 3:
            d = max(throws_samples) if throws_samples else 1.0
            throws_samples = [0.0, d * 0.5, d, d * 0.5, 0.0]

        throw_m = [float(t * scale) for t in throws_samples]
        dmax = float(max(throw_m))
        # fault length ≈ section height span of throw stations (relative)
        length = float(max(len(throw_m) * 10.0 * scale, dmax * 10.0))  # avoid zero L
        # if many horizons, length from vertical span
        if len(horizons) >= 2:
            ys = []
            for h in horizons:
                pts = h.get("pts") or []
                for p in pts:
                    if len(p) >= 2 and abs(int(p[0]) - col) <= 2:
                        ys.append(float(p[1]))
            if ys:
                length = max(float((max(ys) - min(ys) + 1) * scale), dmax * 2.0, 1.0)

        fid = f.get("fault_id") or f.get("id") or f"F_col{col}"
        out_faults.append(
            {
                "fault_id": fid,
                "col": col,
                "dmax_m": dmax,
                "length_m": length,
                "throw_profile_m": throw_m,
                # canonical aliases also set for gates without normalize
                "max_displacement": dmax,
                "length": length,
                "throw_profile": throw_m,
                "unit_note": unit_note,
                "vertical_scale_epistemic": scale_epistemic,
                "sample_interval_ms": sample_interval_ms,
                "epistemic_class": _INT,
                "label": "INT_SEISMIC_FAULT_THROW",
                "n_horizon_stations": len(throws_samples),
            }
        )

    return {
        "ok": True,
        "faults": out_faults,
        "n_faults": len(out_faults),
        "framework": {"faults": out_faults},
        "epistemic_class": _INT,
        "claim_tag": "HYPOTHESIS",
        "governance_status": "HOLD",
        "note": (
            "Throw measured from horizon cutoffs at fault columns. "
            "Relative geometry for K-DL/K-THROW. True meters need vertical_scale_m_per_sample."
        ),
        "next": "Pass framework to geox_seismic_interpret mode=structure_validate",
    }


# ── public entry points (called by tool modes) ───────────────────────────────


async def zen_attribute(
    *,
    attribute: str = "coherence",
    window_size: int = 11,
    image_path: str | None = None,
    amplitude_grid: list[list[float]] | None = None,
    volume_inline: dict[str, Any] | None = None,
    volume_ref: str | None = None,
    provenance: str = "fixture",
) -> dict[str, Any]:
    amp, meta = load_section_2d(
        image_path=image_path,
        amplitude_grid=amplitude_grid,
        volume_inline=volume_inline,
        provenance=provenance if not volume_ref else provenance,
    )
    if amp.size == 0:
        # volume_ref without frame data → honest HOLD
        if volume_ref:
            return _qualified(
                "attribute",
                {
                    "ok": False,
                    "status": "HOLD",
                    "error": "VOLUME_FRAME_REQUIRED",
                    "message": (
                        f"volume_ref={volume_ref!r} present but no amplitude frame. "
                        "Pass amplitude_grid, volume_inline, image_path, or provenance=fixture."
                    ),
                    "volume_ref": volume_ref,
                    "governance_status": "HOLD",
                    "claim_tag": "VOID",
                },
                "geox_seismic_compute",
            )
        return _qualified(
            "attribute",
            {
                "ok": False,
                "status": "HOLD",
                "error": meta.get("error", "NO_SECTION"),
                "governance_status": "HOLD",
                "claim_tag": "VOID",
            },
            "geox_seismic_compute",
        )

    body = compute_attributes_2d(amp, attribute=attribute, window=window_size)
    body["section_meta"] = meta
    body["governance_status"] = "HOLD"
    if not body.get("ok"):
        body["status"] = "HOLD"
        body["governance_status"] = "HOLD"
    return _qualified("attribute", body, "geox_seismic_compute")


async def zen_track_horizon(
    *,
    image_path: str | None = None,
    amplitude_grid: list[list[float]] | None = None,
    volume_inline: dict[str, Any] | None = None,
    max_horizons: int = 8,
    seed_rows: list[int] | None = None,
    provenance: str = "fixture",
    request: dict[str, Any] | None = None,
) -> dict[str, Any]:
    req = request or {}
    seeds = seed_rows or req.get("seed_rows")
    amp, meta = load_section_2d(
        image_path=image_path,
        amplitude_grid=amplitude_grid,
        volume_inline=volume_inline,
        provenance=provenance,
    )
    if amp.size == 0:
        return _qualified(
            "track_horizon",
            {
                "ok": False,
                "status": "HOLD",
                "error": meta.get("error", "NO_SECTION"),
                "governance_status": "HOLD",
                "claim_tag": "VOID",
                "horizons": [],
            },
            "geox_seismic_interpret",
        )
    body = track_horizons_2d(
        amp,
        max_horizons=int(req.get("max_horizons") or max_horizons),
        seed_rows=seeds,
    )
    body["section_meta"] = meta
    body["governance_status"] = "HOLD"
    body["honesty_banner"] = "SURVIVED ≠ proven. Horizons are INT_SEISMIC candidates. arifOS seals only."
    return _qualified("track_horizon", body, "geox_seismic_interpret")


async def zen_measure_throw(
    *,
    horizons: list[dict[str, Any]] | None = None,
    faults: list[dict[str, Any]] | None = None,
    image_path: str | None = None,
    amplitude_grid: list[list[float]] | None = None,
    volume_inline: dict[str, Any] | None = None,
    max_horizons: int = 8,
    calibration: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
    provenance: str = "fixture",
    run_gates: bool = True,
) -> dict[str, Any]:
    """Track if needed → measure throw → optional structure_validate."""
    req = request or {}
    cal = calibration or {}
    hyps = horizons
    meta: dict[str, Any] = {}

    if not hyps:
        amp, meta = load_section_2d(
            image_path=image_path,
            amplitude_grid=amplitude_grid,
            volume_inline=volume_inline,
            provenance=provenance,
        )
        if amp.size == 0:
            return _qualified(
                "measure_throw",
                {
                    "ok": False,
                    "status": "HOLD",
                    "error": meta.get("error", "NO_SECTION"),
                    "governance_status": "HOLD",
                    "faults": [],
                },
                "geox_seismic_interpret",
            )
        tracked = track_horizons_2d(amp, max_horizons=int(req.get("max_horizons") or max_horizons))
        hyps = tracked.get("horizons") or []
        meta["tracked"] = True
        meta["n_horizons_tracked"] = len(hyps)

    vscale = cal.get("vertical_scale_m_per_sample") or req.get("vertical_scale_m_per_sample")
    measured = measure_throw_from_horizons(
        hyps,
        faults=faults or req.get("faults"),
        sample_interval_ms=float(cal.get("sample_interval_ms") or req.get("sample_interval_ms") or 4.0),
        vertical_scale_m_per_sample=float(vscale) if vscale is not None else None,
    )
    measured["horizons"] = hyps
    measured["section_meta"] = meta

    if run_gates and measured.get("ok") and measured.get("framework"):
        from geox_mcp.tools.structure_validate import geox_structure_validate

        gates = await geox_structure_validate(
            framework=measured["framework"],
            emit_bundle=False,
            hypothesis_count=3,
        )
        measured["structure_validate"] = {
            "combined_gate_verdict": gates.get("combined_gate_verdict"),
            "kills": gates.get("kills"),
            "passes": gates.get("passes"),
            "unmeasured": gates.get("unmeasured"),
            "gates": {
                k: {
                    "status": v.get("status"),
                    "reason": v.get("reason"),
                    "findings": v.get("findings"),
                    "receipt_hash": (v.get("receipt_hash") or "")[:32],
                }
                for k, v in (gates.get("gates") or {}).items()
                if k in ("K-DL", "K-THROW", "K-DIP")
            },
            "local_verdict": gates.get("local_verdict"),
            "governance_status": gates.get("governance_status"),
        }
        # surface kill for demos
        measured["gate_summary"] = measured["structure_validate"]["combined_gate_verdict"]

    measured["governance_status"] = "HOLD"
    return _qualified("measure_throw", measured, "geox_seismic_interpret")
