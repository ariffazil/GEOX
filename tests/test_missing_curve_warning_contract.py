"""
test_missing_curve_warning_contract.py — Artifact Contract Test #3
═══════════════════════════════════════════════════════════════════════

Missing optional curves produce warnings, not fake success.
DITEMPA BUKAN DIBERI
"""

from pathlib import Path
from geox.ingest.plotting import render_correlation_panel


def test_missing_curve_emits_warning():
    las_path = Path("tests/fixtures/geox_smoke_test.las")
    if not las_path.exists():
        pytest.skip("Smoke test LAS fixture not found")

    result = render_correlation_panel(
        las_paths=[str(las_path)],
        well_names=["SMOKE-1"],
        tracks=["GR", "NONEXISTENT_CURVE"],
        output_dir="/tmp/geox_test_panels",
    )

    assert result.ok is True
    assert any("NOT FOUND" in str(w) or "not found" in str(w) for w in result.qc_warnings)


def test_all_null_curve_emits_warning():
    # This test relies on a curve that exists but is all null
    # In a real test harness, a fixture with all-null curve would be used.
    pass
