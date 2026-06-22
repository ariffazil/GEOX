"""
GEOX Golden Tests — Regression Anchor for Abduction + PINN
═══════════════════════════════════════════════════════════════════════════════
Captures expected outputs from geox_process_abduction and PINN predict()
on Danum-1 baseline data. Fails if output drifts from golden baseline.

Update golden files:
    GEOX_UPDATE_GOLDEN=1 PYTHONPATH=src python -m pytest tests/test_golden.py -v

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"
UPDATE_GOLDEN = os.environ.get("GEOX_UPDATE_GOLDEN", "0") == "1"


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _load_golden(name: str) -> dict[str, Any]:
    path = GOLDEN_DIR / name
    with open(path, "r") as f:
        return json.load(f)


def _save_golden(name: str, data: dict[str, Any]) -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    path = GOLDEN_DIR / name
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════════════════════
# Golden Test 1 — Abduction on Danum-1 Shoreface Evidence
# ═══════════════════════════════════════════════════════════════════════════════

def test_golden_abduction_danum1_shoreface():
    """geox_process_abduction grammar rules must produce stable hypotheses."""
    from geox_mcp.tools.abduction import _match_rules

    golden = _load_golden("abduction_danum1_shoreface.json")
    evidence = golden["evidence"]

    hypotheses = _match_rules(evidence)

    # Count check
    assert len(hypotheses) == golden["expected_hypothesis_count"], (
        f"Expected {golden['expected_hypothesis_count']} hypotheses, got {len(hypotheses)}"
    )

    # Process names check
    actual_processes = [h["process"] for h in hypotheses]
    for expected in golden["expected_processes"]:
        assert expected in actual_processes, (
            f"Expected process '{expected}' not found in {actual_processes}"
        )

    # Top process check (highest confidence wins)
    confidence_rank = {"high": 5, "moderate-high": 4, "moderate": 3, "low-moderate": 2, "low": 1}
    hypotheses_sorted = sorted(
        hypotheses,
        key=lambda h: confidence_rank.get(h["confidence"], 0),
        reverse=True,
    )
    top_process = hypotheses_sorted[0]["process"]
    assert top_process == golden["expected_top_process"], (
        f"Expected top process '{golden['expected_top_process']}', got '{top_process}'"
    )

    # Confidence range check
    confidences = [h["confidence"] for h in hypotheses]
    min_conf = golden["expected_confidence_range"]["min"]
    max_conf = golden["expected_confidence_range"]["max"]
    assert min_conf in confidences, f"Expected at least one '{min_conf}' confidence"
    assert max_conf in confidences, f"Expected at least one '{max_conf}' confidence"

    # Claim state check
    for h in hypotheses:
        assert h["claim_state"] == golden["expected_claim_state"]

    # Evidence-for patterns check
    for h in hypotheses:
        evidence_for = h.get("evidence_for", [])
        for pattern in golden["expected_evidence_for_patterns"]:
            assert any(pattern in ef for ef in evidence_for), (
                f"Pattern '{pattern}' not found in evidence_for for {h['process']}"
            )

    # Update golden if requested
    if UPDATE_GOLDEN:
        updated = {
            **golden,
            "_last_updated": "2026-05-17",
            "captured_processes": actual_processes,
            "captured_confidences": confidences,
        }
        _save_golden("abduction_danum1_shoreface.json", updated)


# ═══════════════════════════════════════════════════════════════════════════════
# Golden Test 2 — PINN on Synthetic Well Log Data
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(
    not pytest.importorskip("torch", reason="PyTorch not installed"),
    reason="PINN golden test requires PyTorch",
)
@pytest.mark.skipif(
    # Skip on CPU-only — 2000 epochs is GPU-bound, CPU runtime exceeds test budget.
    # Re-enable when GPU acceleration is available in CI / dev environment.
    not __import__("torch").cuda.is_available(),
    reason="PINN golden test requires CUDA GPU acceleration (CPU-only runtimes exceed test budget)",
)
def test_golden_pinn_danum1_prediction():
    """PINN must learn and predict within golden ranges on a learnable dataset."""
    from geox_core.engines.petrophysics.pinn import PINNPetrophysics

    golden = _load_golden("pinn_danum1_prediction.json")
    train_cfg = golden["training"]

    # Build synthetic well log data with direct input→target mappings
    np.random.seed(42)
    n = golden["inputs_shape"][0]

    gr = np.random.uniform(30, 140, n)
    nphi = np.random.uniform(0.1, 0.4, n)
    rt = np.random.uniform(1, 50, n)
    rhob = 2.65 - nphi * 0.8 + np.random.normal(0, 0.02, n)
    dt = 100 - nphi * 100 + np.random.normal(0, 5, n)

    inputs = np.column_stack([gr, rhob, nphi, rt, dt]).astype(np.float32)
    targets = np.column_stack([
        gr / 150.0,
        nphi * 0.7,
        np.clip(1.0 / np.sqrt(rt) * 2.5, 0.1, 0.9),
    ]).astype(np.float32)

    # Train PINN
    pinn = PINNPetrophysics(
        input_dim=5,
        hidden_dims=tuple(train_cfg["hidden_dims"]),
        lambda_archie=train_cfg["lambda_archie"],
        lambda_density=train_cfg["lambda_density"],
        lambda_phys=train_cfg["lambda_phys"],
    )
    pinn.fit(inputs, targets, epochs=train_cfg["epochs"], lr=train_cfg["lr"], log_interval=0)

    # Predict
    result = pinn.predict(inputs, violation_threshold=0.05)

    # Structure checks
    struct = golden["expected_structure"]
    assert struct["has_vsh"] == ("vsh" in result)
    assert struct["has_phi"] == ("phi" in result)
    assert struct["has_sw"] == ("sw" in result)
    assert struct["has_physics_violation"] == ("physics_violation" in result)
    assert struct["has_confidence"] == ("confidence" in result)
    assert struct["has_canon9_profile"] == ("canon9_profile" in result)
    assert struct["has_violation_details"] == ("violation_details" in result)

    # CANON-9 profile keys check
    profile = result.get("canon9_profile", {})
    for key in golden["expected_canon9_profile_keys"]:
        assert key in profile, f"Missing CANON-9 profile key: {key}"

    # Confidence check
    assert result["confidence"] == golden["expected_confidence"], (
        f"Expected confidence '{golden['expected_confidence']}', got '{result['confidence']}'"
    )

    # Range checks against golden baseline
    ranges = golden["expected_ranges"]
    for key, bounds in ranges.items():
        actual = float(np.mean(result[key.replace("_mean", "")]))
        assert bounds["min"] <= actual <= bounds["max"], (
            f"{key} = {actual:.4f} outside golden range [{bounds['min']}, {bounds['max']}]"
        )

    # MSE sanity check — predictions should be close to targets
    mse_vsh = float(np.mean((result["vsh"] - targets[:, 0]) ** 2))
    mse_phi = float(np.mean((result["phi"] - targets[:, 1]) ** 2))
    mse_sw = float(np.mean((result["sw"] - targets[:, 2]) ** 2))
    max_mse = golden["expected_mse_max"]
    assert mse_vsh < max_mse, f"Vsh MSE {mse_vsh:.6f} >= {max_mse}"
    assert mse_phi < max_mse, f"Phi MSE {mse_phi:.6f} >= {max_mse}"
    assert mse_sw < max_mse, f"Sw MSE {mse_sw:.6f} >= {max_mse}"

    # Update golden if requested
    if UPDATE_GOLDEN:
        updated = {
            **golden,
            "_last_updated": "2026-05-17",
            "captured_values": {
                "vsh_mean": float(np.mean(result["vsh"])),
                "phi_mean": float(np.mean(result["phi"])),
                "sw_mean": float(np.mean(result["sw"])),
                "mse_vsh": mse_vsh,
                "mse_phi": mse_phi,
                "mse_sw": mse_sw,
                "physics_violation": result["physics_violation"],
                "confidence": result["confidence"],
                "physics_loss": result["violation_details"]["physics_loss"],
            },
        }
        _save_golden("pinn_danum1_prediction.json", updated)
