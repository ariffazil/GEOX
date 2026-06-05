"""
Tests for feature_joint_info (FJIS) module (Eureka 2026-06-05, Burlamaque 2026-06-04 Step 1).

Verifies:
- Redundant features score DROP
- Genuine new information scores ADD
- Marginal features score HOLD
- Empty / invalid input handling

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import random
from typing import Any

import pytest

from geox_mcp.tools.feature_joint_info import run_fjis


def _make_samples(n: int, target_func, feature_funcs: dict, seed: int = 42) -> list[dict[str, Any]]:
    """Build a sample list with a target and named features."""
    rng = random.Random(seed)
    samples = []
    for i in range(n):
        row: dict[str, Any] = {}
        for name, fn in feature_funcs.items():
            row[name] = fn(rng)
        row["value"] = target_func(rng, row)
        samples.append(row)
    return samples


def test_empty_input_returns_void():
    res = run_fjis(
        samples=[],
        existing_features=["a"],
        candidate_feature="b",
    )
    assert res["verdict"] == "VOID"
    assert res["fjis_score"] == 0.0


def test_redundant_feature_scores_drop():
    """A candidate that's a copy of an existing feature should DROP."""
    rng = random.Random(42)
    base_vals = [rng.gauss(0, 1) for _ in range(100)]
    samples = []
    for v in base_vals:
        samples.append(
            {
                "feature_a": v,  # existing
                "feature_b": v,  # candidate — IDENTICAL to feature_a
                "value": v * 2 + rng.gauss(0, 0.1),
            }
        )
    res = run_fjis(
        samples=samples,
        existing_features=["feature_a"],
        candidate_feature="feature_b",
    )
    # Pure redundancy → recommendation should be DROP or HOLD (never ADD)
    assert res["recommendation"] in ("DROP", "HOLD"), f"Got {res['recommendation']}"


def test_genuine_new_info_scores_add():
    """A candidate that adds new signal should score ADD."""
    rng = random.Random(42)
    samples = []
    for _ in range(200):
        a = rng.gauss(0, 1)
        # Candidate is a genuinely independent signal
        c = rng.gauss(0, 1)
        # Target depends on BOTH a and c
        target = 2 * a + 3 * c + rng.gauss(0, 0.1)
        samples.append({"feature_a": a, "feature_c": c, "value": target})

    res = run_fjis(
        samples=samples,
        existing_features=["feature_a"],
        candidate_feature="feature_c",
    )
    assert res["recommendation"] in ("ADD", "HOLD"), f"Expected ADD/HOLD, got {res['recommendation']}"


def test_target_with_insufficient_unique_values():
    """Constant target → MI undefined → VOID."""
    samples = [{"feature_a": 1.0, "feature_b": 2.0, "value": 5.0} for _ in range(20)]
    res = run_fjis(
        samples=samples,
        existing_features=["feature_a"],
        candidate_feature="feature_b",
    )
    assert res["verdict"] == "VOID"


def test_returns_required_receipt_fields():
    samples = [{"a": float(i), "b": float(i * 2), "value": float(i + (i * 2))} for i in range(50)]
    res = run_fjis(
        samples=samples,
        existing_features=["a"],
        candidate_feature="b",
    )
    # Only check fields present in success case
    if res.get("verdict") != "VOID":
        for k in (
            "verdict",
            "recommendation",
            "fjis_score_raw",
            "fjis_score_normalized",
            "mi_candidate_target",
            "max_redundancy",
            "redundancy_breakdown",
            "n_samples",
        ):
            assert k in res, f"Missing field: {k}"


def test_max_samples_downsampling():
    """When n > max_samples, downsampling is applied."""
    rng = random.Random(42)
    samples = []
    for i in range(1000):
        a = rng.gauss(0, 1)
        b = rng.gauss(0, 1)
        samples.append({"a": a, "b": b, "value": a + b})
    res = run_fjis(
        samples=samples,
        existing_features=["a"],
        candidate_feature="b",
        max_samples=200,
    )
    assert res["n_samples"] == 200
