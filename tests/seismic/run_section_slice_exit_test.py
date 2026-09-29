"""
Section-image interpretation slice — EXIT TEST.

Runs the full GEOX section-image pipeline on a synthetic NW-SE Sabah
profile that emulates the structural style of Vijayan et al. (modified
from Madon) Figure 4: NW-SE seismic profile across Sabah Shelf to
Dangerous Grounds.

INPUT GATING (per spec):
- Public data only (no Block H 3D, no PETRONAS confidential)
- Synthetic PNG generated from published Morley 2023 stratigraphy
  (DRU/UIU/SRU/H-III ages + IVC thickness max)
- Real ResearchGate URL was blocked (HTTP 403), so we emulate the
  figure structure from published descriptions

PIPELINE (per spec):
  display_trace → age_assign → alternative_interpret → render_publication

OUTPUT:
- Source SHA256 + axis calibration (PNG bytes hashed)
- Polylines with provenance
- Age assignments with plausibility gates fired
- 3 hypothesis cards (all HOLD, no auto-verdict)
- Rendered image with legend, deterministic SHA256

Writes outputs to /root/AAA/specs/mcp-2026-07-28/ for sovereign inspection.
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import sys
from datetime import datetime, timezone

import numpy as np
from PIL import Image, ImageDraw

# Add GEOX to path so the test runs from anywhere
sys.path.insert(0, "/root/GEOX")

from src.geox_mcp.tools.seismic_display_trace import geox_seismic_display_trace
from src.geox_mcp.tools.seismic_age_assign import geox_seismic_age_assign
from src.geox_mcp.tools.seismic_alternative_interpret import geox_seismic_alternative_interpret
from src.geox_mcp.tools.seismic_render_publication import geox_seismic_render_publication

OUTPUT_DIR = "/root/AAA/specs/mcp-2026-07-28"


# ────────────────────────────────────────────────────────────────────────────
# Synthetic NW-SE Sabah profile (emulating Vijayan/Madon Fig 4)
# ────────────────────────────────────────────────────────────────────────────


def synthesize_nw_se_sabah_profile(
    width: int = 1200, height: int = 600, seed: int = 7
) -> bytes:
    """Synthetic NW-SE Sabah profile mimicking Vijayan/Madon Fig 4.

    Structural model (per Morley 2023 §6 + Vijayan):
    - NW (left): shallow Sabah Shelf, thin sediments over acoustic basement
    - Middle: deep Dangerous Grounds, mobile-shale deformation, mini-basins
    - SE (right): uplift, fold-thrust belt
    - Color-coded horizons: SRU orange, UIU cyan, DRU navy
    - Diapirs and mini-basins in the middle section
    """
    img = Image.new("RGB", (width, height), (240, 240, 230))
    draw = ImageDraw.Draw(img)
    rng = np.random.RandomState(seed)

    # Draw seismic "wiggle" background (gray-scale noise + dim reflectors)
    pix = np.asarray(img).copy()
    for y in range(height):
        # Subtle vertical banding (representing geological layering)
        intensity = 200 + int(20 * np.sin(y * 0.05))
        intensity = max(180, min(220, intensity))
        for x in range(0, width, 3):
            noise = int(rng.randint(-15, 15))
            pix[y, x] = [intensity + noise, intensity + noise, intensity + noise]
    img = Image.fromarray(pix)
    draw = ImageDraw.Draw(img)

    # SRU — orange dashed style (synthetic stroke)
    sru_points = []
    for x in range(0, width, 5):
        # SRU: rises to SE (uplift) and dips into mini-basins
        y_base = 100 + 80 * np.sin(x * 0.004)  # wavy
        # Mini-basin deepening near x=600-800
        if 500 < x < 900:
            y_base += 30
        sru_points.append((x, int(y_base)))
    for i in range(len(sru_points) - 1):
        draw.line([sru_points[i], sru_points[i + 1]], fill=(255, 140, 0), width=3)

    # UIU — cyan solid
    uiu_points = []
    for x in range(0, width, 5):
        y_base = 250 + 50 * np.sin(x * 0.004 + 1.0)
        if 500 < x < 900:
            y_base += 30
        uiu_points.append((x, int(y_base)))
    for i in range(len(uiu_points) - 1):
        draw.line([uiu_points[i], uiu_points[i + 1]], fill=(0, 210, 255), width=3)

    # DRU — navy thick solid
    dru_points = []
    for x in range(0, width, 5):
        y_base = 450 + 30 * np.sin(x * 0.004 + 2.0)
        if 500 < x < 900:
            y_base += 20
        dru_points.append((x, int(y_base)))
    for i in range(len(dru_points) - 1):
        draw.line([dru_points[i], dru_points[i + 1]], fill=(31, 42, 107), width=4)

    # Add H-III (intra-IVD) for north-west shelf area
    h3_points = [(x, int(60 + 20 * np.sin(x * 0.005))) for x in range(0, 400, 5)]
    for i in range(len(h3_points) - 1):
        draw.line([h3_points[i], h3_points[i + 1]], fill=(230, 230, 230), width=2)

    # Mark mini-basin region (highlighting the SE-of-D3 anomaly zone)
    mb_box = (500, 200, 900, 550)
    mb_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    mb_draw = ImageDraw.Draw(mb_layer)
    mb_draw.rectangle(mb_box, outline=(200, 0, 0, 200), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), mb_layer).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.text(
        (mb_box[0] + 10, mb_box[3] + 5),
        "mini-basin zone",
        fill=(200, 0, 0),
    )

    # Save
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ────────────────────────────────────────────────────────────────────────────
# Pipeline runner
# ────────────────────────────────────────────────────────────────────────────


async def run_exit_test() -> dict:
    print("=" * 70)
    print("SECTION-IMAGE INTERPRETATION SLICE — EXIT TEST")
    print("=" * 70)
    print()
    print("INPUT:")
    print("  Source: ResearchGate URL was blocked (HTTP 403).")
    print("  Substitute: synthetic NW-SE Sabah profile emulating Vijayan/Madon")
    print("  Fig 4 structural style (Morley 2023 stratigraphy).")
    print()
    print("PIPELINE:  display_trace → age_assign → alternative_interpret → render_publication")
    print()

    # Step 0: Generate synthetic PNG (the public-data substitute)
    png_bytes = synthesize_nw_se_sabah_profile()
    png_b64 = base64.b64encode(png_bytes).decode("ascii")
    src_hash = __import__("hashlib").sha256(png_bytes).hexdigest()
    print(f"[Step 0] Generated synthetic PNG")
    print(f"          source_sha256 = {src_hash}")
    print(f"          size_bytes = {len(png_bytes)}")
    print()

    # Save the source PNG for sovereign inspection
    src_path = os.path.join(OUTPUT_DIR, "exit_test_synthetic_input.png")
    with open(src_path, "wb") as f:
        f.write(png_bytes)
    print(f"          saved: {src_path}")
    print()

    # ── Step 2: display_trace × 3 (SRU, UIU, DRU) ──
    color_targets = [
        ("horizon.sru", [255, 140, 0], "SRU"),
        ("horizon.uiu", [0, 210, 255], "UIU"),
        ("horizon.dru", [31, 42, 107], "DRU"),
    ]
    horizon_artifacts = []
    for color_class, rgb, label in color_targets:
        print(f"[Step 2] display_trace({label})")
        result = await geox_seismic_display_trace(
            png_base64=png_b64,
            color_class=color_class,
            rgb=rgb,
            tolerance=30,
        )
        print(f"          status = {result['status']}")
        if result["status"] == "OK":
            n_segments = result["provenance"]["n_segments"]
            print(f"          n_segments = {n_segments}")
            for i, poly in enumerate(result["data"]):
                pid = poly["polyline_id"]
                n_points = len(poly["points"])
                print(f"          segment[{i}]: {pid} ({n_points} pts)")
                horizon_artifacts.append(
                    {"polyline_id": pid, "label": label, "payload": poly}
                )
        else:
            print(f"          error = {result.get('error')}")
        print()

    # ── Step 3: age_assign per horizon ──
    print(f"[Step 3] age_assign per horizon (with plausibility gate)")
    age_results = {}
    for h in horizon_artifacts:
        ref_surface = h["label"]
        print(f"          age_assign({ref_surface})")
        result = await geox_seismic_age_assign(
            horizon_artifact_id=h["polyline_id"],
            horizon_payload=h["payload"],
            reference_surface=ref_surface,
        )
        print(f"          status = {result['status']}")
        if result["status"] == "OK":
            d = result["data"]
            print(
                f"          age = {d['age_ma_min']}-{d['age_ma_max']} Ma "
                f"(typical {d['typical_age_ma']} Ma)"
            )
        else:
            print(f"          error = {result.get('error')}")
        age_results[ref_surface] = result
    print()

    # Plausibility gate test: SRU vs UIU thickness (real morphology, expect OK)
    if "SRU" in {h["label"] for h in horizon_artifacts} and "UIU" in {h["label"] for h in horizon_artifacts}:
        sru = next(h["payload"] for h in horizon_artifacts if h["label"] == "SRU")
        uiu = next(h["payload"] for h in horizon_artifacts if h["label"] == "UIU")
        print("[Step 3+] Plausibility gate: SRU vs UIU interval (real morphology)")
        result = await geox_seismic_age_assign(
            horizon_artifact_id=sru["polyline_id"],
            horizon_payload=sru,
            reference_surface="SRU",
            twt_ms_per_pixel=1.0,
            pair_horizon_payload=uiu,
        )
        print(f"          status = {result['status']}")
        if result["status"] == "HOLD":
            print(f"          hold_reason = {result['data'].get('hold_reason')}")
        else:
            print(f"          thickness_ms = {result['data']['plausibility']['measured_thickness_ms']:.0f}")
        print()

    # Plausibility gate test: OVERTHICK synthetic
    print("[Step 3+] Plausibility gate: DELIBERATE OVER-THICK synthetic (adversarial)")
    from geox.seismic.contracts import Polyline
    upper = Polyline(
        polyline_id="geox://artifact/upper-overthick-test",
        coordinate_frame="INLINE_XLINE_SAMPLE",
        points=[(x, 100, 0.0) for x in range(0, 600, 10)],
        created_by="exit-test-fixture",
    )
    lower = Polyline(
        polyline_id="geox://artifact/lower-overthick-test",
        coordinate_frame="INLINE_XLINE_SAMPLE",
        points=[(x, 700, 0.0) for x in range(0, 600, 10)],  # 600 ms apart — over-thick
        created_by="exit-test-fixture",
    )
    result = await geox_seismic_age_assign(
        horizon_artifact_id="geox://artifact/upper-overthick-test",
        horizon_payload=upper.model_dump(mode="json"),
        reference_surface="SRU",
        twt_ms_per_pixel=1.0,
        pair_horizon_payload=lower.model_dump(mode="json"),
    )
    print(f"          status = {result['status']}")
    if result["status"] == "HOLD":
        print(f"          hold_reason = {result['data'].get('hold_reason')[:80]}...")
    print()

    # ── Step 5: alternative_interpret (3 hypotheses, all HOLD) ──
    print("[Step 5] alternative_interpret (3 hypotheses from discriminator)")
    horizon_ids = [h["polyline_id"] for h in horizon_artifacts]
    horizon_payloads = [h["payload"] for h in horizon_artifacts]
    result = await geox_seismic_alternative_interpret(
        horizon_artifact_ids=horizon_ids,
        horizon_payloads=horizon_payloads,
        survey_id="synthetic_nw_se_sabah",
    )
    print(f"          status = {result['status']}")
    if result["status"] == "OK":
        for h in result["hypotheses"]:
            print(f"          [{h['id']}] state={h['state']}")
            print(f"              falsifiers: {len(h['falsifiers'])}")
            print(f"              observations: {len(h['required_observations'])}")
            print(f"              best_test: {h['best_test'][:60]}...")
    print()

    # ── Step 4: render_publication (deterministic) ──
    print("[Step 4] render_publication (deterministic)")
    overlay_artifacts = [
        {"label": h["label"], "points": h["payload"]["points"]} for h in horizon_artifacts
    ]
    title = "GEOX Exit Test — NW-SE Sabah (synthetic, Morley 2023)"
    render1 = await geox_seismic_render_publication(
        png_base64=png_b64,
        overlay_artifacts=overlay_artifacts,
        title=title,
    )
    render2 = await geox_seismic_render_publication(
        png_base64=png_b64,
        overlay_artifacts=overlay_artifacts,
        title=title,
    )
    print(f"          status = {render1['status']}")
    if render1["status"] == "OK":
        sha1 = render1["image_sha256"]
        sha2 = render2["image_sha256"]
        print(f"          image_sha256 (run 1) = {sha1}")
        print(f"          image_sha256 (run 2) = {sha2}")
        print(f"          deterministic? {sha1 == sha2}")
        print(f"          image_base64 length = {len(render1['image_base64'])}")
        # Save rendered image for sovereign inspection
        rendered_bytes = base64.b64decode(render1["image_base64"])
        rendered_path = os.path.join(OUTPUT_DIR, "exit_test_rendered_output.png")
        with open(rendered_path, "wb") as f:
            f.write(rendered_bytes)
        print(f"          saved: {rendered_path}")

    print()
    print("=" * 70)
    print("EXIT TEST COMPLETE")
    print("=" * 70)

    return {
        "source_sha256": src_hash,
        "horizon_artifacts": horizon_artifacts,
        "age_results": {k: v.get("status") for k, v in age_results.items()},
        "alternative_interpret_hypotheses": (
            len(result["hypotheses"]) if result["status"] == "OK" else 0
        ),
        "render_deterministic": (
            render1.get("image_sha256") == render2.get("image_sha256")
            if render1["status"] == "OK"
            else None
        ),
    }


if __name__ == "__main__":
    summary = asyncio.run(run_exit_test())
    # Also save summary
    summary_path = os.path.join(OUTPUT_DIR, "exit_test_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSummary: {summary_path}")
