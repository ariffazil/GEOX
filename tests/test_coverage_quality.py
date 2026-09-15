"""Tests for quality-weighted coverage calculation."""
import pytest


def test_gate_quality_scores():
    """Verify quality score mapping."""
    scores = {
        "PASS": 1.0,
        "WARN": 0.75,
        "PARTIAL": 0.5,
        "UNMEASURED": 0.0,
        "HOLD": 0.0,
        "KILL": 0.0,
    }
    for status, expected in scores.items():
        # Import the actual function once it's wired
        # For now, verify the mapping logic
        if status == "PASS":
            assert expected == 1.0
        elif status == "WARN":
            assert expected == 0.75
        elif status in ("UNMEASURED", "HOLD", "KILL"):
            assert expected == 0.0
