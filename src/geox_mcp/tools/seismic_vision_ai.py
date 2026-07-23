#!/usr/bin/env python3
"""
GEOX Seismic Vision AI Layer (Model & Platform Agnostic)
===========================================================
v1.0 — Forged 2026-07-06 under F13 SOVEREIGN.

Implements the 4 cognitive visual AI modes decoupled from specific backends:
  1. geox_visual_understand — VLM pattern classification (OBS_IMAGE)
  2. geox_visual_enhance    — Deterministic filtering (DER_RENDER_ENHANCEMENT)
  3. geox_visual_generate_hypotheses — Visual scenario rendering (GEN_HYPOTHESIS)
  4. geox_panel_d_render    — Cognitive interpretation rendering (DER_COGNITIVE_RENDER)

Strict Boundary Enforced:
  Image generation is NOT used as truth. It is bounded to explanation/hypotheses.
  All outputs carry clear provenance, hashes, and warnings.

DITEMPA BUKAN DIBERI.
"""

import hashlib
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

# ═══════════════════════════════════════════════════════════════════════════
# 1. VISUAL UNDERSTAND (OBS_IMAGE)
# ═══════════════════════════════════════════════════════════════════════════


def geox_visual_understand(image_path: str, mode: str = "full", vlm_client_callback=None) -> dict:
    """Extract visual patterns from a seismic image without making geological claims.

    If a vlm_client_callback is provided, it delegates the visual query to the active LLM.
    Without a perception backend: HOLD — never invent discontinuities or terminations.

    P0 2026-07-23 (sovereign): hard-coded CV fallback deleted. False evidence is F2 violation.
    Correct fallback is HOLD, not plausible-looking geological observations.
    """
    if not image_path or not os.path.exists(image_path):
        return {
            "ok": False,
            "status": "HOLD",
            "error": "NO_IMAGE",
            "reason": f"File not found or empty path: {image_path!r}",
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "seal_authority": "arifOS_only",
            "epistemic": "NO_VALID_PERCEPTION",
            "claim_tag": "HYPOTHESIS",
        }

    with open(image_path, "rb") as f:
        img_bytes = f.read()
    sha256 = hashlib.sha256(img_bytes).hexdigest()

    im = Image.open(image_path)
    w, h = im.size

    # If VLM callback is available, use it (platform agnostic)
    if vlm_client_callback:
        try:
            prompt = (
                "Identify and classify visible reflector packages, continuity (parallel vs chaotic), "
                "apparent breaks, termination shapes, and potential imaging artifacts. Do NOT use "
                "interpretive geological names (e.g. reservoir, oil, gas, formation top)."
            )
            out = vlm_client_callback(image_path, prompt)
            if isinstance(out, dict):
                out.setdefault("image_hash", sha256)
                out.setdefault("dimensions", [w, h])
                out.setdefault("input_class", "image_only")
                out.setdefault("epistemic_note", "OBS_IMAGE ≠ OBS_GEOLOGY. Pixels observed; geology requires calibration.")
                out.setdefault("local_verdict", "QUALIFIED_CANDIDATE")
                out.setdefault("seal_authority", "arifOS_only")
            return out
        except Exception as e:
            return {
                "ok": False,
                "status": "HOLD",
                "error": "VLM_BACKEND_FAILED",
                "reason": str(e)[:300],
                "image_hash": sha256,
                "dimensions": [w, h],
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "seal_authority": "arifOS_only",
                "epistemic": "NO_VALID_PERCEPTION",
                "claim_tag": "HYPOTHESIS",
                "hint": "Register a real VLM callback or use SEG-Y attribute pipelines. Do not invent structure.",
            }

    # No perception backend — HOLD (never fabricate discontinuities)
    return {
        "ok": False,
        "status": "HOLD",
        "error": "NO_PERCEPTION_BACKEND",
        "reason": "No VLM callback registered. Hard-coded structure inventory is prohibited (F2 TRUTH).",
        "image_hash": sha256,
        "dimensions": [w, h],
        "input_class": "image_only",
        "governance_status": "HOLD",
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "epistemic": "NO_VALID_PERCEPTION",
        "claim_tag": "HYPOTHESIS",
        "transport_status": "TRANSPORT_OK",
        "hint": (
            "Provide vlm_client_callback, or use geox_seismic_interpret(mode=horizon_contrast) "
            "with attribute_data+depth from SEG-Y — not screenshot fabrication."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. VISUAL ENHANCE (DER_RENDER_ENHANCEMENT)
# ═══════════════════════════════════════════════════════════════════════════


def geox_visual_enhance(image_path: str, output_path: str, enhancement_mode: str = "contrast_normalize") -> dict:
    """Enhance seismic image readability without modifying trace amplitudes.

    Decoupled from VLM/platform — runs locally via PIL/scipy.
    """
    if not os.path.exists(image_path):
        return {"status": "VOID", "reason": f"File not found: {image_path}"}

    with open(image_path, "rb") as f:
        img_bytes = f.read()
    base_sha256 = hashlib.sha256(img_bytes).hexdigest()

    im = Image.open(image_path).convert("L")

    if enhancement_mode == "contrast_normalize":
        im = ImageEnhance.Contrast(im).enhance(1.8)
    elif enhancement_mode == "denoise":
        im = im.filter(ImageFilter.MedianFilter(size=3))
    elif enhancement_mode == "grayscale_standardize":
        im = ImageEnhance.Brightness(im).enhance(1.2)
        im = ImageEnhance.Contrast(im).enhance(1.4)
    else:
        return {"status": "VOID", "reason": f"Unknown enhancement mode: {enhancement_mode}"}

    # Always stamp the warning watermark on the enhanced visual to block synthetic drift
    draw = ImageDraw.Draw(im)
    warning_text = "DER_RENDER_ENHANCEMENT — DO NOT USE FOR PHYSICAL AMPLITUDE"
    draw.text((10, 10), warning_text, fill=128)

    im.save(output_path)

    with open(output_path, "rb") as f:
        out_bytes = f.read()
    out_sha256 = hashlib.sha256(out_bytes).hexdigest()

    return {
        "status": "DER_RENDER_ENHANCEMENT",
        "base_image_hash": base_sha256,
        "enhanced_image_hash": out_sha256,
        "output_path": output_path,
        "enhancement_mode": enhancement_mode,
        "warning": "Readability enhancement only. Do not interpret as physical seismic amplitude.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. VISUAL GENERATE HYPOTHESES (GEN_HYPOTHESIS)
# ═══════════════════════════════════════════════════════════════════════════


def geox_visual_generate_hypotheses(image_path: str, output_dir: str, target_feature_id: str, hypotheses: list[str]) -> dict:
    """Generate visual representations of alternative continuations across gaps.

    Decoupled from VLM/platform — renders dashed scenario paths on the original visual.
    """
    if not os.path.exists(image_path):
        return {"status": "VOID", "reason": f"File not found: {image_path}"}

    with open(image_path, "rb") as f:
        img_bytes = f.read()
    base_sha256 = hashlib.sha256(img_bytes).hexdigest()

    variants = []
    colors = ["#ff5555", "#00ff87", "#00d4ff"]

    for idx, hyp in enumerate(hypotheses[:3]):
        im = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(im)
        w, h = im.size

        # Draw a simulated structural scenario path near the center
        col = colors[idx]
        draw.text((20, 20), f"GEN_HYPOTHESIS: {hyp}", fill=col)
        draw.text((20, 40), f"Base SHA: {base_sha256[:8]}", fill="#888888")

        # Overlay a dashed line representing the proposed continuation
        if "normal" in hyp.lower() or "fault" in hyp.lower():
            # Scenario A: Faulted continuation
            draw.line([(w // 2 - 50, h // 2 - 50), (w // 2 + 50, h // 2 + 50)], fill=col, width=3)
        elif "channel" in hyp.lower() or "truncation" in hyp.lower():
            # Scenario B: Truncation path
            draw.arc([w // 2 - 100, h // 2 - 50, w // 2 + 100, h // 2 + 50], 0, 180, fill=col, width=3)
        else:
            # Scenario C: Conformable sag
            draw.line([(w // 4, h // 2), (3 * w // 4, h // 2)], fill=col, width=3)

        out_path = os.path.join(output_dir, f"scenario_{idx}_{target_feature_id}.png")
        im.save(out_path)

        variants.append(
            {
                "output_path": out_path,
                "hypothesis": hyp,
                "label": "GEN_HYPOTHESIS",
                "warning": "Generated structural scenario candidate, not physical seismic observation.",
            }
        )

    return {"status": "GEN_HYPOTHESIS", "base_image_hash": base_sha256, "feature_id": target_feature_id, "variants": variants}


# ═══════════════════════════════════════════════════════════════════════════
# 4. PANEL D RENDER (DER_COGNITIVE_RENDER)
# ═══════════════════════════════════════════════════════════════════════════


def geox_panel_d_render(base_image_path: str, output_path: str, obs_manifest: dict, cognitive_manifest: dict) -> dict:
    """Render the cognitive geologist interpretation dashboard (Panel D).

    Combines the observations, hypotheses, and warning labels spatially onto the visual.

    Law 7 (GUI before physics): Requires valid provenance chain.
    obs_manifest must contain 'provenance.source_pipeline' indicating
    it came from geox_physical_reality_interpret or geox_rsi_interpret.
    """
    if not os.path.exists(base_image_path):
        return {"status": "VOID", "reason": f"File not found: {base_image_path}"}

    # Law 7 guard: require valid provenance chain
    provenance = obs_manifest.get("provenance", {})
    source_pipeline = provenance.get("source_pipeline", "")
    valid_pipelines = ["geox_physical_reality_interpret", "geox_rsi_interpret", "geox_geological_cognition_run"]
    if source_pipeline not in valid_pipelines:
        return {
            "status": "HOLD",
            "reason": "Law 7 violation: GUI before physics. obs_manifest lacks valid provenance chain.",
            "required": f"provenance.source_pipeline must be one of {valid_pipelines}",
            "got": source_pipeline or "MISSING",
            "hint": "Run geox_physical_reality_interpret or geox_rsi_interpret first.",
        }

    with open(base_image_path, "rb") as f:
        img_bytes = f.read()
    base_sha256 = hashlib.sha256(img_bytes).hexdigest()

    im = Image.open(base_image_path).convert("RGB")
    draw = ImageDraw.Draw(im)
    w, h = im.size

    # 1. Overlay zone bands
    zones = obs_manifest.get("continuity_zones", [])
    zone_colors = [(0, 255, 0, 40), (0, 0, 255, 40)]  # green, blue alpha overlays

    # Create semi-transparent overlay
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for idx, zone in enumerate(zones):
        z_y = zone["depth_px"]
        col = zone_colors[idx % len(zone_colors)]
        overlay_draw.rectangle([0, z_y[0], w, z_y[1]], fill=col)
        draw.text((15, z_y[0] + 10), f"Zone {idx + 1}: {zone['pattern']} (coh={zone['coherence']})", fill="white")

    im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(im)

    # 2. Draw terminations
    terms = obs_manifest.get("terminations", [])
    for t in terms:
        tx, ty = t["x_px"], t["y_px"]
        draw.rectangle([tx - 10, ty - 10, tx + 10, ty + 10], outline="#FFE566", width=2)
        draw.text((tx + 15, ty - 5), f"▲ {t['type']}", fill="#FFE566")

    # 3. Draw faults
    faults = obs_manifest.get("discontinuities", [])
    for idx, f in enumerate(faults):
        fx, fy_range = f["x_px"], f["y_px"]
        draw.line([(fx, fy_range[0]), (fx, fy_range[1])], fill="#FF4444", width=3)
        draw.text((fx + 10, fy_range[0] + 20), f"F{idx + 1}: Normal Fault\n(HOLD: well tie req)", fill="#FF4444")

    # 4. Stamp epistemic ladder
    ladder_text = "EPISTEMIC: OBS_IMAGE -> DER_ATTRIBUTE -> INT_SEISMIC [NOW] -> INT_GEOLOGY (HOLD)"
    draw.rectangle([0, h - 40, w, h], fill="#0a0d14")
    draw.text((15, h - 28), ladder_text, fill="#FFE566")
    draw.text((15, h - 14), f"Base SHA: {base_sha256[:16]}", fill="#888888")

    im.save(output_path)

    with open(output_path, "rb") as f:
        out_bytes = f.read()
    out_sha256 = hashlib.sha256(out_bytes).hexdigest()

    return {
        "status": "DER_COGNITIVE_RENDER",
        "base_image_hash": base_sha256,
        "panel_d_hash": out_sha256,
        "output_path": output_path,
        "epistemic_ladder": {"current": "INT_SEISMIC", "held_prerequisites": ["well_tie", "checkshot", "velocity_model"]},
    }


if __name__ == "__main__":
    # Test suite run
    test_img = "/tmp/seismic_image_test/seismic_greyscale.jpg"
    test_out = "/tmp/geox_vision_ai_test"
    os.makedirs(test_out, exist_ok=True)

    if os.path.exists(test_img):
        print("Testing platform-agnostic GEOX Seismic Vision AI Layer...")
        # 1. understand
        obs = geox_visual_understand(test_img)
        print("  ✅ Understand:", obs["status"])

        # 2. enhance
        enh = geox_visual_enhance(test_img, os.path.join(test_out, "enhanced.png"), "contrast_normalize")
        print("  ✅ Enhance:", enh["status"])

        # 3. hypotheses
        hyp = geox_visual_generate_hypotheses(test_img, test_out, "F1", ["Normal offset fault", "Channel erosional truncation"])
        print("  ✅ Hypotheses:", hyp["status"])

        # 4. panel d
        pd = geox_panel_d_render(test_img, os.path.join(test_out, "panel_d.png"), obs, {})
        print("  ✅ Panel D:", pd["status"])
    else:
        print("Test image not found. Verification skipped.")
