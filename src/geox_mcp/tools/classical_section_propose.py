"""Classical seismic-section propose baseline (image-first).

Structure tensor · semblance-proxy coherence · edge/ridge · DP horizons ·
discontinuity faults. Outputs CANDIDATE_GEOMETRY only (INT_SEISMIC).

Mandatory comparator for any future ONNX/SAM propose layer.
Does not SEAL. Does not claim OBS_GEOLOGY.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np

# Reuse RSI measurement + attribute stack (already structure-tensor based)
from geox_mcp.tools.seismic_rsi import (
    _agc,
    _compute_attributes,
    _compute_provenance,
    _detect_and_track_horizons,
    _detect_faults,
    _detect_seismic_panel,
    _input_reality_gate,
    _segment_fault_blocks,
)


def _sha_params(d: dict[str, Any]) -> str:
    raw = repr(sorted(d.items())).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def _estimate_apparent_dip_deg(pts: list[list[int]] | list[tuple[int, int]]) -> float | None:
    """Image-space dip from fault stick (row=depth-down, col=lateral).

    apparent dip from vertical: atan(|dc|/|dr|) in degrees from horizontal
    if depth is vertical axis. Seismic sections: dip from horizontal ≈
    atan(d_lateral / d_vertical) with vertical in samples.
    """
    if not pts or len(pts) < 4:
        return None
    arr = np.asarray(pts, dtype=float)
    # pts may be [row, col] (RSI) or [x,y]
    if arr.shape[1] < 2:
        return None
    # RSI faults use pts as [r, c] in detect; geometry export uses [c,r] sometimes
    # Prefer first two columns as (a,b); use linear fit col vs row
    a, b = arr[:, 0], arr[:, 1]
    # Assume larger variance axis is length along fault
    if np.std(a) >= np.std(b):
        # a is along-fault major; slope db/da
        if np.std(a) < 1e-6:
            return 90.0
        slope = np.polyfit(a, b, 1)[0]  # db/da
        # if a=row (depth), b=col (x): dip from horizontal = atan(|dx/dz|)
        dip = math.degrees(math.atan(abs(slope)))
    else:
        if np.std(b) < 1e-6:
            return 90.0
        slope = np.polyfit(b, a, 1)[0]
        dip = math.degrees(math.atan(abs(1.0 / (slope + 1e-12))))
    # Clamp to (0, 90)
    dip = max(1.0, min(89.0, dip))
    return round(dip, 1)


def _faults_to_framework(faults: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for f in faults:
        pts = f.get("pts") or []
        # Normalize to {x,y} with x=lateral col, y=depth row
        points = []
        for p in pts:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                # RSI fault pts are [r,c]
                r, c = int(p[0]), int(p[1])
                points.append({"x": c, "y": r})
            elif isinstance(p, dict):
                points.append(p)
        dip_img = _estimate_apparent_dip_deg([[p["y"], p["x"]] for p in points] if points else [])
        # length proxy in pixels
        length_px = float(len(points)) if points else None
        out.append(
            {
                "fault_id": f.get("id") or f.get("fault_id") or "F?",
                "domain": "pixel",
                "points": points,
                "n_points": len(points),
                "dip_deg_image": dip_img,
                # image-only: NOT subsurface — gates will UNMEASURED true dip without VE
                "regime_prior": "unknown",
                "tip_taper": "unknown",
                "confidence": f.get("confidence"),
                "dip_direction_deg": f.get("dip_direction_deg"),
                "length_px": length_px,
                "epistemic_label": "INT_SEISMIC_FAULT",
                "tracker_method": "classical_discontinuity_nms",
                "alternatives": f.get("alternatives")
                or [
                    "structural_fault",
                    "acquisition_footprint",
                    "migration_smile",
                    "noise_corridor",
                ],
            }
        )
    return out


def _horizons_to_framework(horizons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for i, h in enumerate(horizons):
        pts = h.get("pts") or []
        points = []
        for p in pts:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                # DP path stores [c, path[c]] in RSI
                c, r = int(p[0]), int(p[1])
                points.append({"x": c, "y": r})
            elif isinstance(p, dict):
                points.append(p)
        mean_y = float(np.mean([p["y"] for p in points])) if points else float(i)
        out.append(
            {
                "horizon_id": h.get("id") or f"H{i + 1}",
                "domain": "pixel",
                "points": points,
                "order_index": i,
                "mean_y_px": mean_y,
                "confidence": h.get("confidence"),
                "continuity": h.get("continuity"),
                "tracker_method": "dynamic_programming",
                "epistemic_label": "INT_SEISMIC_HORIZON",
                "phase": "unknown",
                "alternatives": h.get("alternatives")
                or [
                    "stratigraphic_boundary",
                    "sidelobe",
                    "facies_transition",
                    "processing_artifact",
                ],
            }
        )
    # order by mean depth (y)
    out.sort(key=lambda z: z.get("mean_y_px", 0))
    for i, h in enumerate(out):
        h["order_index"] = i
    return out


def _ridge_enhance(agc: np.ndarray) -> np.ndarray:
    """Optional Sato vesselness for subvertical discontinuities (fault-like)."""
    try:
        from skimage.filters import sato

        # Invert so dark/light discontinuities both get energy via abs grad proxy
        rid = sato(agc, sigmas=range(1, 4), black_ridges=False)
        rid = rid / (rid.max() + 1e-10)
        return rid.astype(np.float64)
    except Exception:
        return np.zeros_like(agc, dtype=np.float64)


async def geox_classical_section_propose(
    image_path: str,
    max_faults: int = 15,
    max_horizons: int = 10,
    fault_percentile: float = 96.0,
    fault_min_length: int = 40,
    include_attribute_stats: bool = True,
    run_gates: bool = False,
    calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Propose horizons + faults from a seismic section image (classical CV).

    All geometry is pixel-domain INT_SEISMIC. True dip/throw/V remain UNMEASURED
    unless calibration supplies VE / true axes.
    """
    params = {
        "max_faults": max_faults,
        "max_horizons": max_horizons,
        "fault_percentile": fault_percentile,
        "fault_min_length": fault_min_length,
    }
    out: dict[str, Any] = {
        "tool": "geox_classical_section_propose",
        "mode": "classical_section",
        "ok": False,
        "input_class": "image_only",
        "epistemic_label": "INT_SEISMIC",
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "seal_eligibility": False,
        "preferred_hypothesis": None,
        "algorithm": {
            "name": "classical_section_v1",
            "stack": [
                "agc",
                "structure_tensor",
                "semblance_proxy_discontinuity",
                "sobel_edge",
                "sato_ridge",
                "nms_faults",
                "dp_horizons",
            ],
            "parameter_hash": _sha_params(params),
        },
    }

    gate = _input_reality_gate(image_path)
    out["reality_gate"] = gate
    if gate.get("verdict") != "PASS":
        out["governance_status"] = "HOLD"
        out["reason"] = f"Reality gate: {gate.get('reason')}"
        return out

    try:
        from PIL import Image
    except ImportError:
        out["error"] = "PIL_MISSING"
        out["governance_status"] = "HOLD"
        return out

    img = Image.open(image_path)
    arr = np.array(img)
    if arr.ndim == 3:
        gray = np.mean(arr, axis=2)
    else:
        gray = arr.astype(float)

    panel = _detect_seismic_panel(arr)
    out["panel"] = {k: v for k, v in panel.items() if k != "panel_bbox"}
    if panel.get("verdict") == "PASS" and panel.get("panel_bbox"):
        x0, y0, x1, y1 = panel["panel_bbox"]
        amp = 255.0 - gray[y0:y1, x0:x1].astype(float)
    else:
        amp = 255.0 - gray.astype(float)

    # Downsample for MCP latency — image-first product must stay under tool timeout
    max_side = 512
    hc0, wc0 = amp.shape
    scale = 1.0
    if max(hc0, wc0) > max_side:
        scale = max_side / float(max(hc0, wc0))
        new_h = max(32, int(hc0 * scale))
        new_w = max(32, int(wc0 * scale))
        ys = np.linspace(0, hc0 - 1, new_h).astype(int)
        xs = np.linspace(0, wc0 - 1, new_w).astype(int)
        amp = amp[np.ix_(ys, xs)].astype(float)
        out["downsample"] = {"scale": scale, "shape": [int(amp.shape[0]), int(amp.shape[1])]}

    attrs = _compute_attributes(amp)
    # Sato ridge is optional / expensive — skip by default for product path latency
    ridge = np.zeros_like(attrs["agc"], dtype=np.float64)
    fp = attrs["fault_probability"]
    attrs["sato_ridge"] = ridge

    # Scale min_length with downsampled height
    min_len = max(15, min(fault_min_length, amp.shape[0] // 8))
    faults_raw = _detect_faults(
        fp,
        attrs["orientation"],
        min_length=min_len,
        percentile=fault_percentile,
        max_faults=max_faults,
    )
    # Fault mask for horizon DP
    hc, wc = amp.shape
    fault_mask = np.zeros((hc, wc), dtype=bool)
    for f in faults_raw:
        for pt in f.get("pts") or []:
            r, c = int(pt[0]), int(pt[1])
            for dr in range(-2, 3):
                for dc in range(-1, 2):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < hc and 0 <= cc < wc:
                        fault_mask[rr, cc] = True

    horizons_raw = _detect_and_track_horizons(
        attrs["agc"],
        attrs["phase_continuity"],
        fault_mask,
        max_horizons=max_horizons,
    )
    n_blocks = int(_segment_fault_blocks(faults_raw, (hc, wc)).max()) if faults_raw else 0

    fw_faults = _faults_to_framework(faults_raw)
    fw_horizons = _horizons_to_framework(horizons_raw)

    prov = _compute_provenance(image_path, str(Path(__file__).resolve()))
    cal = dict(calibration or {})
    cal.setdefault("input_class", "image_only")
    cal.setdefault("calibrated", bool(cal.get("vertical_exaggeration") is not None))
    cal.setdefault("sha256", prov.get("image_sha256"))

    framework = {
        "faults": fw_faults,
        "horizons": fw_horizons,
        "measurement_context": {
            "input_class": "image_only",
            "sha256": prov.get("image_sha256"),
            "calibrated": cal.get("calibrated", False),
            "geometry": {
                "vertical_exaggeration": cal.get("vertical_exaggeration"),
                "domain": "pixel",
                "panel_shape": [int(hc), int(wc)],
            },
        },
        "calibration": cal,
        "fault_blocks_count": n_blocks,
    }

    observations = {
        "reflector_continuity": [{"horizon_id": h["horizon_id"], "continuity": h.get("continuity")} for h in fw_horizons],
        "discontinuities": [{"fault_id": f["fault_id"], "n_points": f.get("n_points")} for f in fw_faults],
        "image_quality_flags": [],
        "attribute_summary": {},
    }
    if include_attribute_stats:
        for key in ("discontinuity", "edge", "coherence_st", "fault_probability"):
            a = attrs.get(key)
            if isinstance(a, np.ndarray):
                observations["attribute_summary"][key] = {
                    "mean": float(np.nanmean(a)),
                    "p95": float(np.nanpercentile(a, 95)),
                    "label": "DER_RENDER_CONTRAST",
                }

    alternatives = [
        {"model_id": "through_going", "prior": "primary classical pick set"},
        {"model_id": "relay_segmented", "prior": "faults as relays / segments"},
        {"model_id": "artifact_dominant", "prior": "processing/noise dominant"},
    ]

    out.update(
        {
            "ok": True,
            "governance_status": "QUALIFY",
            "n_faults": len(fw_faults),
            "n_horizons": len(fw_horizons),
            "faults": fw_faults,
            "horizons": fw_horizons,
            "framework": framework,
            "observations": observations,
            "alternatives": alternatives,
            "provenance": prov,
            "capability_note": (
                "Classical image propose only. Pixel domain. "
                "Not OBS_GEOLOGY. Run structure_validate / mode=interpret for gates. "
                "True dip/throw UNMEASURED without calibration."
            ),
            "honesty_banner": (
                "CANDIDATE_GEOMETRY from structure tensor + DP. Always physics-gated before any claim. Human adjudicates."
            ),
        }
    )

    if run_gates and (fw_faults or fw_horizons):
        from geox_mcp.tools.structure_validate import geox_structure_validate

        sv = await geox_structure_validate(
            framework=framework,
            calibration=cal,
            emit_bundle=True,
            hypothesis_count=3,
        )
        out["structure_validate"] = {
            "combined_gate_verdict": sv.get("combined_gate_verdict"),
            "kills": sv.get("kills"),
            "unmeasured": sv.get("unmeasured"),
            "passes": sv.get("passes"),
        }
        out["interpretation_bundle"] = sv.get("interpretation_bundle")
        out["preferred_hypothesis"] = None
    else:
        # Light bundle without full re-gate multi-hyp expand if no gates
        from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle

        out["interpretation_bundle"] = build_interpretation_bundle(
            frameworks_or_primary=framework,
            observations=observations,
            calibration=cal,
            propose_result={
                "horizons": fw_horizons,
                "faults": fw_faults,
                "alternatives": alternatives,
            },
            request={"hypothesis_count": 3},
            model_revision="classical_section_v1",
        )
        # If we have geometry, re-run gates inside bundle builder via frameworks
        if fw_faults or fw_horizons:
            # rebuild with gate matrix for real multi-hyp
            out["interpretation_bundle"] = build_interpretation_bundle(
                frameworks_or_primary=framework,
                observations=observations,
                calibration=cal,
                request={"hypothesis_count": 3},
                model_revision="classical_section_v1",
            )

    return out
