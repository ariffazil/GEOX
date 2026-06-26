"""
GEOX Vision V1 — Synthetic Forward-Inverse Test Harness
═══════════════════════════════════════════════════════════════════════════
Forged 2026-06-07 — DITEMPA BUKAN DIBERI

This is the **calibration** mechanism for the vision layer. Per Bond
et al. (2007) "What do you think this is?" — 79% first-interpretation
error rate means vision outputs need ground-truth validation before
they earn trust. The synthetic forward-inverse loop provides that
ground truth:

1. **Forward pass** (GEOX existing): well logs → acoustic impedance
   → reflection coefficients → wavelet convolution → synthetic
   seismogram (1D). Then replicate as 2D with **known perturbations**
   (faults, bright spots, sequence boundaries at exact known positions).

2. **Render to PNG** (variable-density display, real TWT/inline axes).

3. **Vision pass** (the layer under test): VLM reads the PNG, returns
   PerceptualInventory.

4. **Inverse pass** (ground-truth comparison): for each observation,
   check whether it falls within ε of the known feature. Compute
   precision/recall per feature class.

5. **AC_Risk calibration**: per Bond 2007, the unaided VLM is the
   baseline. The synthetic loop lets us measure how much better (or
   worse) the VLM is than a random interpretation, and how the
   AC_Risk components (U_phys, D_transform, B_cog) actually distribute
   on this controlled data.

Outputs (per run):
- `synthetic_test_report_<timestamp>.json` — full structured report
- Print summary to stdout

This is the **calibration artifact** for the GEOX Vision V1 forge.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# GEOX physics — production-grade
from geox_core.physics import (
    convolve_trace,
    ricker_wavelet,
)

# Vision module
from .minimax_vlm_adapter import MiniMaxVLMAdapter
from .perceptual_inventory import (
    PerceptualInventory,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Ground truth schema
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class SyntheticGroundTruth:
    """The known features in the synthetic section, with tolerance for
    matching against VLM-detected observations."""

    n_inlines: int
    n_twt_samples: int
    twt_range_ms: tuple[float, float]  # (min, max) TWT
    inline_range: tuple[float, float]  # (min, max) inline

    # Each reflector: (twt_center_ms, amplitude_sign, width_ms)
    # For matching: VLM reflector must overlap in twt_range_ms
    reflectors: list[dict[str, Any]] = field(default_factory=list)

    # Each fault: (inline_center, twt_top, twt_bot, type, throw_ms)
    faults: list[dict[str, Any]] = field(default_factory=list)

    # Each bright zone: (twt_center, twt_width, lateral_inlines, character)
    bright_zones: list[dict[str, Any]] = field(default_factory=list)

    def reflector_tolerance_ms(self) -> float:
        """A VLM-detected reflector is a match if its twt_range overlaps
        a true reflector's twt_range by at least this much."""
        return 50.0  # ms

    def fault_tolerance_inlines(self) -> float:
        return 20.0  # inlines

    def zone_tolerance_ms(self) -> float:
        return 100.0  # ms

    def zone_tolerance_inlines(self) -> float:
        return 30.0  # inlines


# ═══════════════════════════════════════════════════════════════════════════════
# Forward model — synthetic 2D section
# ═══════════════════════════════════════════════════════════════════════════════


def build_synthetic_2d_section(
    n_inlines: int = 200,
    n_twt_samples: int = 300,
    twt_range_ms: tuple[float, float] = (0.0, 2000.0),
    dt_ms: float = 4.0,
    wavelet_freq: float = 25.0,
    noise_db: float = -22.0,
    seed: int | None = 42,
    reflectors: list[tuple[float, float, float]] | None = None,
    faults: list[tuple[int, float, float, str, float]] | None = None,
    bright_zones: list[tuple[float, float, int, int, str]] | None = None,
) -> tuple[np.ndarray, SyntheticGroundTruth]:
    """Build a synthetic 2D seismic section with known features.

    Args:
        n_inlines: number of CDP/inline traces
        n_twt_samples: number of TWT samples
        twt_range_ms: (min, max) TWT
        dt_ms: time sample interval
        wavelet_freq: Ricker wavelet dominant frequency
        noise_db: noise level in dB (0 = none, -∞ = clean)
        reflectors: list of (twt_center_ms, amplitude, width_ms)
        faults: list of (inline_center, twt_top_ms, twt_bot_ms, type, throw_ms)
        bright_zones: list of (twt_center, twt_width_ms, inline_start, inline_end, character)

    Returns:
        (section_2d, ground_truth)
    """
    if reflectors is None:
        reflectors = [(400, 0.6, 30), (800, 0.8, 25), (1200, -0.7, 20), (1500, 0.4, 15)]
    if faults is None:
        faults = [(130, 0, 2000, "normal", 80)]
    if bright_zones is None:
        bright_zones = [(1150, 140, 75, 155, "bright")]

    if seed is not None:
        np.random.seed(seed)

    twt_axis = np.linspace(twt_range_ms[0], twt_range_ms[1], n_twt_samples)

    # 1. Build 1D reflectivity from reflector list
    rc_1d = np.zeros(n_twt_samples)
    for twt_c, amp, width in reflectors:
        rc_1d += amp * np.exp(-0.5 * ((twt_axis - twt_c) / width) ** 2)

    # 2. Convolve with Ricker wavelet to get 1D synthetic
    wavelet = ricker_wavelet(freq=wavelet_freq, dt=dt_ms, length=0.1)
    synth_1d = convolve_trace(rc_1d, wavelet)

    # 3. Replicate as 2D
    section_2d = np.tile(synth_1d[:, None], (1, n_inlines))

    # 4. Apply fault throws
    for inline_c, twt_top, twt_bot, ftype, throw in faults:
        if ftype == "normal":
            # Right side goes down (later TWT)
            for i in range(inline_c, n_inlines):
                # Shift down by `throw` ms below twt_top
                mask = (twt_axis >= twt_top) & (twt_axis <= twt_bot)
                section_2d[mask, i] = np.interp(twt_axis[mask] - throw, twt_axis, section_2d[:, i])
        # (Other fault types would be more complex; this is sandbox-scope)

    # 5. Apply bright zones
    for twt_c, width, inl_start, inl_end, char in bright_zones:
        mask = (twt_axis >= twt_c - width / 2) & (twt_axis <= twt_c + width / 2)
        if char == "bright":
            section_2d[np.ix_(mask, np.arange(inl_start, min(inl_end, n_inlines)))] += 0.5

    # 6. Add noise
    if noise_db < 0:
        snr_linear = 10 ** (noise_db / 20.0)
        noise_amp = np.std(section_2d) * snr_linear
        section_2d += noise_amp * np.random.randn(n_twt_samples, n_inlines)

    # 7. Build ground truth
    gt = SyntheticGroundTruth(
        n_inlines=n_inlines,
        n_twt_samples=n_twt_samples,
        twt_range_ms=twt_range_ms,
        inline_range=(0, n_inlines),
        reflectors=[
            {
                "id": f"GT_R{i + 1}",
                "twt_center_ms": twt_c,
                "twt_range_ms": (twt_c - width, twt_c + width),
                "amplitude_sign": 1 if amp > 0 else -1,
                "width_ms": width,
            }
            for i, (twt_c, amp, width) in enumerate(reflectors)
        ],
        faults=[
            {
                "id": f"GT_F{i + 1}",
                "inline_center": inline_c,
                "twt_range_ms": (twt_top, twt_bot),
                "type": ftype,
                "throw_ms": throw,
            }
            for i, (inline_c, twt_top, twt_bot, ftype, throw) in enumerate(faults)
        ],
        bright_zones=[
            {
                "id": f"GT_A{i + 1}",
                "twt_center_ms": twt_c,
                "twt_range_ms": (twt_c - width / 2, twt_c + width / 2),
                "lateral_extent_inlines": (inl_start, inl_end),
                "character": char,
            }
            for i, (twt_c, width, inl_start, inl_end, char) in enumerate(bright_zones)
        ],
    )
    return section_2d, gt


def render_section_to_png(
    section_2d: np.ndarray,
    gt: SyntheticGroundTruth,
    output_path: str,
    title: str = "Synthetic Test Section",
) -> str:
    """Render a 2D seismic section to a PNG with proper axes."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    n_twt, n_inl = section_2d.shape
    extent = [
        gt.inline_range[0],
        gt.inline_range[1],
        gt.twt_range_ms[1],
        gt.twt_range_ms[0],  # top-down
    ]
    vmax = max(1.5, np.percentile(np.abs(section_2d), 98))
    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(
        section_2d,
        aspect="auto",
        cmap="seismic",
        vmin=-vmax,
        vmax=vmax,
        extent=extent,
    )
    ax.set_xlabel("Inline")
    ax.set_ylabel("Two-Way Time (ms)")
    ax.set_title(title)
    plt.colorbar(im, ax=ax, label="Amplitude (arbitrary)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# Ground-truth comparison
# ═══════════════════════════════════════════════════════════════════════════════


def _ranges_overlap(a: tuple[float, float], b: tuple[float, float], tolerance: float = 0.0) -> float:
    """Return the size of the intersection of two ranges (with tolerance)."""
    a_lo, a_hi = a[0] - tolerance, a[1] + tolerance
    b_lo, b_hi = b[0] - tolerance, b[1] + tolerance
    lo = max(a_lo, b_lo)
    hi = min(a_hi, b_hi)
    return max(0.0, hi - lo)


def compare_to_ground_truth(
    inventory: PerceptualInventory,
    gt: SyntheticGroundTruth,
) -> dict[str, Any]:
    """Compare VLM output to known ground truth. Returns precision,
    recall, and per-feature match breakdown."""
    # Reflectors
    tp_r, fp_r, fn_r = [], [], []
    matched_gt_r = set()
    for _i, vlm_r in enumerate(inventory.reflectors):
        vlm_twt = vlm_r.twt_range_ms
        matched_idx = None
        for j, gt_r in enumerate(gt.reflectors):
            if j in matched_gt_r:
                continue
            overlap = _ranges_overlap(vlm_twt, gt_r["twt_range_ms"], gt.reflector_tolerance_ms())
            if overlap > 0:
                matched_idx = j
                break
        if matched_idx is not None:
            tp_r.append(
                {
                    "vlm_id": vlm_r.reflector_id,
                    "gt_id": gt.reflectors[matched_idx]["id"],
                    "overlap_ms": overlap,
                    "vlm_confidence": vlm_r.confidence,
                }
            )
            matched_gt_r.add(matched_idx)
        else:
            fp_r.append({"vlm_id": vlm_r.reflector_id, "vlm_twt_range": vlm_twt})
    for j, gt_r in enumerate(gt.reflectors):
        if j not in matched_gt_r:
            fn_r.append({"gt_id": gt_r["id"], "gt_twt_range": gt_r["twt_range_ms"]})

    # Faults
    tp_f, fp_f, fn_f = [], [], []
    matched_gt_f = set()
    for vlm_f in inventory.faults:
        vlm_inline_c = (vlm_f.lateral_extent_inlines[0] + vlm_f.lateral_extent_inlines[1]) / 2
        matched_idx = None
        for j, gt_f in enumerate(gt.faults):
            if j in matched_gt_f:
                continue
            dist_inl = abs(vlm_inline_c - gt_f["inline_center"])
            if dist_inl <= gt.fault_tolerance_inlines():
                matched_idx = j
                break
        if matched_idx is not None:
            tp_f.append({"vlm_id": vlm_f.fault_id, "gt_id": gt.faults[matched_idx]["id"], "dist_inl": dist_inl})
            matched_gt_f.add(matched_idx)
        else:
            fp_f.append({"vlm_id": vlm_f.fault_id, "vlm_inline": vlm_inline_c})
    for j, gt_f in enumerate(gt.faults):
        if j not in matched_gt_f:
            fn_f.append({"gt_id": gt_f["id"], "gt_inline": gt_f["inline_center"]})

    # Bright zones
    tp_a, fp_a, fn_a = [], [], []
    matched_gt_a = set()
    for vlm_a in inventory.amplitude_zones:
        matched_idx = None
        for j, gt_a in enumerate(gt.bright_zones):
            if j in matched_gt_a:
                continue
            twt_overlap = _ranges_overlap(vlm_a.twt_range_ms, gt_a["twt_range_ms"], gt.zone_tolerance_ms())
            inl_overlap = _ranges_overlap(
                vlm_a.lateral_extent_inlines, gt_a["lateral_extent_inlines"], gt.zone_tolerance_inlines()
            )
            if twt_overlap > 0 and inl_overlap > 0:
                matched_idx = j
                break
        if matched_idx is not None:
            tp_a.append({"vlm_id": vlm_a.zone_id, "gt_id": gt.bright_zones[matched_idx]["id"]})
            matched_gt_a.add(matched_idx)
        else:
            fp_a.append({"vlm_id": vlm_a.zone_id})
    for j, gt_a in enumerate(gt.bright_zones):
        if j not in matched_gt_a:
            fn_a.append({"gt_id": gt_a["id"]})

    def _pr(tp, fp, fn):
        prec = len(tp) / max(1, len(tp) + len(fp))
        rec = len(tp) / max(1, len(tp) + len(fn))
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        return {"precision": prec, "recall": rec, "f1": f1, "tp": len(tp), "fp": len(fp), "fn": len(fn)}

    return {
        "reflectors": {"matches": tp_r, "false_positives": fp_r, "false_negatives": fn_r, **_pr(tp_r, fp_r, fn_r)},
        "faults": {"matches": tp_f, "false_positives": fp_f, "false_negatives": fn_f, **_pr(tp_f, fp_f, fn_f)},
        "zones": {"matches": tp_a, "false_positives": fp_a, "false_negatives": fn_a, **_pr(tp_a, fp_a, fn_a)},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level run
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class HarnessReport:
    """Output of one synthetic forward-inverse run."""

    test_id: str
    timestamp_unix: float
    image_path: str
    image_sha256: str
    ground_truth_summary: dict[str, int]
    vision_verdict: str
    vision_human_review_required: bool
    vision_ac_risk: float
    vision_ac_risk_verdict: str
    n_vlm_reflectors: int
    n_vlm_faults: int
    n_vlm_zones: int
    precision_recall: dict[str, Any]
    pass_fail: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


async def run_synthetic_forward_inverse(
    backend: Any,
    output_png: str = "/tmp/opencode/geox-vision-v1/pngs/synthetic_test_section.png",
    output_report: str = "/tmp/opencode/geox-vision-v1/reports/synthetic_forward_inverse_report.json",
    basin_context: str = "Synthetic test (sandbox, Malay Basin-style progradational)",
    seed: int = 42,
) -> HarnessReport:
    """One full forward-inverse run.

    1. Build synthetic 2D section
    2. Render to PNG
    3. Call VLM (via injected backend)
    4. Compare to ground truth
    5. Write report to disk + return HarnessReport

    Returns HarnessReport with full provenance (image SHA256, test_id, etc.)
    """
    np.random.seed(seed)
    t0 = time.time()

    section_2d, gt = build_synthetic_2d_section(seed=seed)
    render_section_to_png(section_2d, gt, output_png)
    image_sha = hashlib.sha256(open(output_png, "rb").read()).hexdigest()

    adapter = MiniMaxVLMAdapter(backend=backend)
    result = await adapter.interpret(
        image_path=output_png,
        basin_context=basin_context,
        interpretation_goal="Identify all reflectors, faults, and amplitude anomalies",
    )

    test_id = f"synth_test_{int(t0)}"
    if not result.success:
        report = HarnessReport(
            test_id=test_id,
            timestamp_unix=t0,
            image_path=output_png,
            image_sha256=image_sha,
            ground_truth_summary={"reflectors": len(gt.reflectors), "faults": len(gt.faults), "zones": len(gt.bright_zones)},
            vision_verdict="VOID",
            vision_human_review_required=True,
            vision_ac_risk=1.0,
            vision_ac_risk_verdict="VOID",
            n_vlm_reflectors=0,
            n_vlm_faults=0,
            n_vlm_zones=0,
            precision_recall={},
            pass_fail={"vision_succeeded": False, "any_f1_above_0.5": False},
        )
        _write_report(report, output_report)
        return report

    inv = result.inventory
    pr = compare_to_ground_truth(inv, gt)
    pass_fail = {
        "vision_succeeded": True,
        "reflector_f1_above_0.5": pr["reflectors"]["f1"] > 0.5,
        "fault_recall_above_0.5": pr["faults"]["recall"] > 0.5,
        "zone_recall_above_0.5": pr["zones"]["recall"] > 0.5,
    }
    report = HarnessReport(
        test_id=test_id,
        timestamp_unix=t0,
        image_path=output_png,
        image_sha256=image_sha,
        ground_truth_summary={
            "reflectors": len(gt.reflectors),
            "faults": len(gt.faults),
            "zones": len(gt.bright_zones),
        },
        vision_verdict=inv.verdict.value,
        vision_human_review_required=inv.human_review_required,
        vision_ac_risk=inv.ac_risk.compute(),
        vision_ac_risk_verdict=inv.ac_risk.to_verdict().value,
        n_vlm_reflectors=len(inv.reflectors),
        n_vlm_faults=len(inv.faults),
        n_vlm_zones=len(inv.amplitude_zones),
        precision_recall=pr,
        pass_fail=pass_fail,
    )
    _write_report(report, output_report)
    return report


def _write_report(report: HarnessReport, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)
