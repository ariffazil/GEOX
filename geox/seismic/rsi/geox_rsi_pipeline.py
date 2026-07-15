"""
GEOX RSI Pipeline — Real Seismic Image Processing
==================================================
v1.0 — Forged from SCAR_GEOX_RSI_001 failure analysis.

Implements:
  P0: INPUT_REALITY_GATE
  P0: REAL_CONTRAST_EXTRACTOR
  P0: NO_SYNTHETIC_DRIFT_GUARD
  P0: ARTIFACT_SUCCESS_VALIDATOR
  P1: IMAGE_CROP_AND_AXIS_DETECTOR
  P1: Full provenance manifest (full SHA256)
  P1: OBS_IMAGE / DER_IMAGE / INT_GEOLOGY grammar

Pipeline:
  RSI-0 FETCH/LOAD → RSI-1 HASH → RSI-2 CROP → RSI-3 EXTRACT →
  RSI-4 DETECT → RSI-5 OVERLAY → RSI-6 GOVERN → RSI-7 DELIVER

DITEMPA BUKAN DIBERI.
"""
import numpy as np
from PIL import Image
import hashlib, json, os
from datetime import datetime, UTC
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# P0: INPUT REALITY GATE
# ═══════════════════════════════════════════════════════════════
def input_reality_gate(image_path: str) -> dict:
    """Verify the image is real, decodable, and loaded before any processing.
    
    Returns gate_result with verdict: PASS | HOLD | VOID.
    If HOLD/VOID, no further processing allowed.
    """
    gate = {
        "image_path": image_path,
        "file_exists": False,
        "file_size_bytes": 0,
        "decodable": False,
        "dimensions": None,
        "mime_type": None,
        "pixel_array_loaded": False,
        "verdict": "VOID",
        "reason": "",
    }
    
    # Step 1: File exists?
    if not os.path.exists(image_path):
        gate["reason"] = "FILE_NOT_FOUND"
        return gate
    gate["file_exists"] = True
    gate["file_size_bytes"] = os.path.getsize(image_path)
    
    # Step 2: Decodable?
    try:
        img = Image.open(image_path)
        img.verify()  # Verify integrity
        img = Image.open(image_path)  # Re-open after verify
        gate["decodable"] = True
        gate["dimensions"] = {"width": img.size[0], "height": img.size[1]}
        gate["mime_type"] = Image.MIME.get(img.format, "unknown")
    except Exception as e:
        gate["reason"] = f"IMAGE_NOT_DECODABLE: {e}"
        return gate
    
    # Step 3: Pixel array loaded?
    try:
        arr = np.array(img)
        if arr.ndim < 2 or arr.ndim > 3:
            gate["reason"] = f"INVALID_DIMENSIONS: {arr.ndim}D"
            return gate
        gate["pixel_array_loaded"] = True
    except Exception as e:
        gate["reason"] = f"PIXEL_LOAD_FAILED: {e}"
        return gate
    
    # Step 4: Minimum size check (reject tiny images)
    w, h = gate["dimensions"]["width"], gate["dimensions"]["height"]
    if w < 100 or h < 100:
        gate["reason"] = f"IMAGE_TOO_SMALL: {w}x{h}"
        return gate
    
    gate["verdict"] = "PASS"
    gate["reason"] = "Real image loaded successfully"
    return gate


# ═══════════════════════════════════════════════════════════════
# P0: NO SYNTHETIC DRIFT GUARD
# ═══════════════════════════════════════════════════════════════
def synthetic_drift_guard(code_path: str, mode: str = "real_image_interpretation") -> dict:
    """Scan generator code for synthetic data patterns.
    
    If mode is real_image_interpretation, blocks code that generates
    synthetic seismic data instead of using real pixels.
    """
    guard = {
        "code_path": code_path,
        "mode": mode,
        "synthetic_patterns_found": [],
        "verdict": "PASS",
        "reason": "",
    }
    
    if mode != "real_image_interpretation":
        guard["reason"] = "Mode allows synthetic data"
        return guard
    
    if not os.path.exists(code_path):
        guard["verdict"] = "HOLD"
        guard["reason"] = "Code file not found — cannot verify"
        return guard
    
    with open(code_path) as f:
        code = f.read()
    
    forbidden_patterns = [
        ("np.random.seed", "Random seed — may generate synthetic data"),
        ("synthetic seismic", "Explicit synthetic data generation"),
        ("simulated section", "Simulated section — not real"),
        ("proxy artifact", "Proxy artifact — not real interpretation"),
        ("random reflectors", "Random reflectors — synthetic"),
        ("dummy data", "Dummy data — not real"),
        ("fake_", "Fake data prefix"),
    ]
    
    for pattern, reason in forbidden_patterns:
        if pattern.lower() in code.lower():
            guard["synthetic_patterns_found"].append({"pattern": pattern, "reason": reason})
    
    if guard["synthetic_patterns_found"]:
        guard["verdict"] = "VOID"
        guard["reason"] = f"Synthetic patterns found: {[p['pattern'] for p in guard['synthetic_patterns_found']]}"
    
    return guard


# ═══════════════════════════════════════════════════════════════
# P1: IMAGE CROP AND AXIS DETECTOR
# ═══════════════════════════════════════════════════════════════
def detect_seismic_panel(arr: np.ndarray) -> dict:
    """Find the actual seismic panel within the image.
    
    Removes white margins, labels, axes, and annotations.
    Returns the bounding box of the seismic data region.
    """
    h, w = arr.shape[:2]
    
    # Convert to grayscale
    if arr.ndim == 3:
        gray = np.mean(arr, axis=2)
    else:
        gray = arr
    
    # Find non-white/non-background regions
    # Background is typically white (255) or very light
    threshold = 240
    mask = gray < threshold
    
    # Find bounding box of non-background
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        return {"panel_bbox": None, "verdict": "HOLD", "reason": "No seismic panel detected"}
    
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    
    # Add small margin
    margin = 5
    rmin = max(0, rmin - margin)
    rmax = min(h - 1, rmax + margin)
    cmin = max(0, cmin - margin)
    cmax = min(w - 1, cmax + margin)
    
    return {
        "panel_bbox": [int(cmin), int(rmin), int(cmax), int(rmax)],
        "panel_size": [int(cmax - cmin), int(rmax - rmin)],
        "original_size": [w, h],
        "crop_pct": round((cmax - cmin) * (rmax - rmin) / (w * h) * 100, 1),
        "verdict": "PASS",
    }


# ═══════════════════════════════════════════════════════════════
# P0: REAL CONTRAST EXTRACTOR
# ═══════════════════════════════════════════════════════════════
def extract_real_contrast(arr: np.ndarray, polarity: str = "auto") -> dict:
    """Extract real seismic amplitude from image pixels.
    
    For colour seismic: amplitude = R - B (or B - R depending on convention).
    Returns normalized amplitude, coherence, and discontinuity maps.
    
    Labels all outputs as OBS_IMAGE_PIXEL or DER_IMAGE_CONTRAST.
    """
    h, w = arr.shape[:2]
    
    if arr.ndim != 3 or arr.shape[2] < 3:
        return {"verdict": "VOID", "reason": "Image must be RGB"}
    
    r = arr[:, :, 0].astype(float)
    g = arr[:, :, 1].astype(float)
    b = arr[:, :, 2].astype(float)
    
    # Auto-detect polarity: if mean R > mean B, then red = positive
    if polarity == "auto":
        polarity = "R_POS" if r.mean() > b.mean() else "B_POS"
    
    if polarity == "R_POS":
        amplitude = r - b  # Red = positive, Blue = negative
    else:
        amplitude = b - r  # Blue = positive, Red = negative
    
    # Normalize to [-1, 1]
    amp_max = np.max(np.abs(amplitude))
    if amp_max > 0:
        amplitude_norm = amplitude / amp_max
    else:
        amplitude_norm = amplitude
    
    # Lateral coherence (horizon continuity)
    coherence = np.zeros_like(amplitude_norm)
    for row in range(1, h - 1):
        grad = np.abs(np.diff(amplitude_norm[row, :]))
        coherence[row, 1:] = grad
    
    # Lateral discontinuity (fault detection)
    discontinuity = np.zeros_like(amplitude_norm)
    for col in range(5, w - 5):
        left = amplitude_norm[:, col - 5:col].mean(axis=1)
        right = amplitude_norm[:, col + 1:col + 6].mean(axis=1)
        discontinuity[:, col] = np.abs(left - right)
    
    # Bright spots (high amplitude anomalies)
    amp_abs = np.abs(amplitude_norm)
    bright_threshold = np.percentile(amp_abs, 95)
    bright_spots = amp_abs > bright_threshold
    
    return {
        "verdict": "PASS",
        "polarity_detected": polarity,
        "amplitude_range": [float(amplitude.min()), float(amplitude.max())],
        "amplitude_norm": amplitude_norm,
        "coherence": coherence,
        "discontinuity": discontinuity,
        "bright_spots": bright_spots,
        "labels": {
            "amplitude": "OBS_IMAGE_PIXEL",
            "coherence": "DER_IMAGE_CONTRAST",
            "discontinuity": "DER_IMAGE_CONTRAST",
            "bright_spots": "OBS_IMAGE_PIXEL",
        },
        "epistemic_note": "These are IMAGE PIXEL observations, NOT geological measurements. Real amplitude requires calibrated seismic data.",
    }


# ═══════════════════════════════════════════════════════════════
# P1: FULL PROVENANCE MANIFEST
# ═══════════════════════════════════════════════════════════════
def compute_full_provenance(image_path: str, code_path: str, prompt_path: str = None) -> dict:
    """Compute full SHA256 hashes for complete reproducibility chain."""
    
    def sha256_full(path: str) -> str:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    manifest = {
        "run_tag": f"GEOX_RSI_{datetime.now(UTC).strftime('%Y%m%dT%H%MZ')}",
        "generated_at": datetime.now(UTC).isoformat(),
        "input": {
            "image_sha256": sha256_full(image_path),
            "image_sha256_short": sha256_full(image_path)[:16],
            "image_path": image_path,
            "image_size_bytes": os.path.getsize(image_path),
        },
        "code": {
            "code_sha256": sha256_full(code_path),
            "code_sha256_short": sha256_full(code_path)[:16],
            "code_path": code_path,
        },
        "model": {
            "vlm_model": "minimax-M3-vision",
            "vlm_backend": "mmx vision describe",
        },
        "reproduce": f"python3 {os.path.basename(code_path)}",
        "input_class": "image_only",
        "coordinate_domain": "pixel",
        "epistemic_note": "All outputs are OBS_IMAGE/DER_IMAGE. No geology claimed without calibration.",
    }
    
    if prompt_path and os.path.exists(prompt_path):
        manifest["prompt"] = {
            "prompt_sha256": sha256_full(prompt_path),
            "prompt_sha256_short": sha256_full(prompt_path)[:16],
            "prompt_path": prompt_path,
        }
    
    return manifest


# ═══════════════════════════════════════════════════════════════
# P0: ARTIFACT SUCCESS VALIDATOR
# ═══════════════════════════════════════════════════════════════
def validate_artifact_delivery(artifact_path: str, delivery_result: dict) -> dict:
    """Verify artifact was actually created and delivery was confirmed.
    
    Courier response ≠ delivery proof.
    """
    validator = {
        "artifact_path": artifact_path,
        "artifact_exists": False,
        "artifact_size_bytes": 0,
        "artifact_sha256": None,
        "delivery_result": delivery_result,
        "telegram_confirmed": False,
        "verdict": "UNKNOWN",
    }
    
    if os.path.exists(artifact_path):
        validator["artifact_exists"] = True
        validator["artifact_size_bytes"] = os.path.getsize(artifact_path)
        with open(artifact_path, "rb") as f:
            validator["artifact_sha256"] = hashlib.sha256(f.read()).hexdigest()
    
    # Check if courier returned success indicators
    if isinstance(delivery_result, dict):
        if delivery_result.get("telegram_message_id"):
            validator["telegram_confirmed"] = True
            validator["verdict"] = "CONFIRMED"
        elif delivery_result.get("sovereign") or delivery_result.get("status") == "ok":
            validator["verdict"] = "PROBABLE_BUT_UNCONFIRMED"
        else:
            validator["verdict"] = "FAILED"
    
    if not validator["artifact_exists"]:
        validator["verdict"] = "VOID"
    
    return validator


# ═══════════════════════════════════════════════════════════════
# RSI PIPELINE — Full chain
# ═══════════════════════════════════════════════════════════════
def run_rsi_pipeline(image_path: str, output_dir: str, code_path: str = None, prompt_path: str = None) -> dict:
    """Run the full RSI pipeline: gate → crop → extract → detect → govern."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    result = {
        "pipeline": "GEOX_RSI_v1.0",
        "stages": {},
        "verdict": "VOID",
        "outputs": [],
    }
    
    # RSI-0: INPUT REALITY GATE
    gate = input_reality_gate(image_path)
    result["stages"]["RSI-0_reality_gate"] = gate
    if gate["verdict"] != "PASS":
        result["verdict"] = "HOLD"
        result["reason"] = f"Reality gate failed: {gate['reason']}"
        return result
    
    # Load image
    img = Image.open(image_path)
    arr = np.array(img)
    
    # RSI-1: FULL PROVENANCE
    if code_path:
        prov = compute_full_provenance(image_path, code_path, prompt_path)
        result["stages"]["RSI-1_provenance"] = prov
        prov_path = os.path.join(output_dir, "manifest.json")
        with open(prov_path, "w") as f:
            json.dump(prov, f, indent=2)
        result["outputs"].append(prov_path)
    
    # RSI-2: CROP SEISMIC PANEL
    panel = detect_seismic_panel(arr)
    result["stages"]["RSI-2_panel_detect"] = panel
    
    if panel["verdict"] == "PASS" and panel["panel_bbox"]:
        x0, y0, x1, y1 = panel["panel_bbox"]
        arr_cropped = arr[y0:y1, x0:x1]
    else:
        arr_cropped = arr  # Use full image if crop fails
    
    # RSI-3: EXTRACT REAL CONTRAST
    contrast = extract_real_contrast(arr_cropped)
    result["stages"]["RSI-3_contrast"] = {k: v for k, v in contrast.items() 
                                           if k not in ("amplitude_norm", "coherence", "discontinuity", "bright_spots")}
    
    if contrast["verdict"] != "PASS":
        result["verdict"] = "HOLD"
        result["reason"] = f"Contrast extraction failed: {contrast.get('reason', 'unknown')}"
        return result
    
    # RSI-4: DETECT FEATURES FROM REAL PIXELS
    amp_norm = contrast["amplitude_norm"]
    coherence = contrast["coherence"]
    discontinuity = contrast["discontinuity"]
    bright_spots = contrast["bright_spots"]
    
    # Detect strong horizons (high-coherence rows)
    h, w = amp_norm.shape
    row_coherence = np.mean(coherence, axis=1)
    horizon_threshold = np.percentile(row_coherence, 90)
    strong_horizons = np.where(row_coherence > horizon_threshold)[0]
    
    # Detect fault candidates (high-discontinuity columns)
    col_discontinuity = np.mean(discontinuity, axis=0)
    fault_threshold = np.percentile(col_discontinuity, 95)
    fault_candidates = np.where(col_discontinuity > fault_threshold)[0]
    
    detection = {
        "n_strong_horizons": len(strong_horizons),
        "n_fault_candidates": len(fault_candidates),
        "n_bright_spots": int(bright_spots.sum()),
        "horizon_rows": strong_horizons.tolist()[:20],
        "fault_cols": fault_candidates.tolist()[:20],
        "labels": {
            "horizons": "DER_IMAGE_CONTRAST",
            "faults": "DER_IMAGE_CONTRAST",
            "bright_spots": "OBS_IMAGE_PIXEL",
        },
    }
    result["stages"]["RSI-4_detection"] = detection
    
    # RSI-5: GOVERN — Epistemic labels
    govern = {
        "OBS_IMAGE": ["Pixel amplitude (R-B)", "Coherence pattern", "Discontinuity pattern", "Bright spot locations"],
        "DER_IMAGE": ["Horizon candidates (from coherence)", "Fault candidates (from discontinuity)"],
        "INT_GEOLOGY": [],  # NONE without calibration
        "SPEC": [],
        "UNKNOWN": ["True depth", "Lithology", "Fluid type", "Age", "Formation names"],
        "HOLD": ["Petrophysics", "Reserves", "Commerciality"],
        "forbidden_claims": [
            "Lithology from pixel color",
            "Fluid type from amplitude",
            "Depth in meters",
            "Formation names",
            "Reserves or commerciality",
        ],
        "epistemic_grammar": "OBS_IMAGE ≠ OBS_GEOLOGY. Pixels are observed. Geology requires calibration.",
    }
    result["stages"]["RSI-5_govern"] = govern
    
    result["verdict"] = "PARTIAL"
    result["reason"] = "Real image processed. All outputs are OBS_IMAGE/DER_IMAGE. No geology claimed."
    
    return result


# ═══════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    
    image_path = "/tmp/seismic_image_test/seismic_section.jpg"
    output_dir = "/tmp/seismic_image_test/rsi_output"
    code_path = "/tmp/seismic_image_test/geox_rsi_pipeline.py"
    prompt_path = "/tmp/seismic_image_test/vlm_v2_prompt.txt"
    
    print("=" * 60)
    print("GEOX RSI PIPELINE v1.0")
    print("=" * 60)
    
    result = run_rsi_pipeline(image_path, output_dir, code_path, prompt_path)
    
    # Save result
    result_path = os.path.join(output_dir, "rsi_result.json")
    # Remove non-serializable arrays
    serializable = json.loads(json.dumps(result, default=str))
    with open(result_path, "w") as f:
        json.dump(serializable, f, indent=2)
    
    # Print summary
    print(f"\nVerdict: {result['verdict']}")
    print(f"Reason: {result.get('reason', 'N/A')}")
    print(f"\nStages:")
    for stage, data in result["stages"].items():
        v = data.get("verdict", "?")
        print(f"  {stage}: {v}")
    
    print(f"\nOutputs: {result['outputs']}")
    print(f"\nFull result: {result_path}")
    
    # Print key detections
    det = result["stages"].get("RSI-4_detection", {})
    print(f"\nDetection (from REAL pixels):")
    print(f"  Strong horizons: {det.get('n_strong_horizons', 0)}")
    print(f"  Fault candidates: {det.get('n_fault_candidates', 0)}")
    print(f"  Bright spots: {det.get('n_bright_spots', 0)}")
    
    gov = result["stages"].get("RSI-5_govern", {})
    print(f"\nEpistemic labels:")
    for label, items in gov.items():
        if isinstance(items, list) and items:
            print(f"  {label}: {len(items)} items")

