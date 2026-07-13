"""
tests/test_gravmag_studio_screen.py — Stage B tests for GEOX GravMag Studio screen.

7 targeted tests per Stage B plan:
  1. perfect-model       → PASS_SCREEN, rms ≈ 0, correlation ≈ 1
  2. wrong-depth         → MARGINAL or FAIL_SCREEN
  3. sign-flipped        → strong negative correlation, FAIL_SCREEN
  4. unit mismatch       → HOLD
  5. grid mismatch       → HOLD
  6. confidence cap      → emitted confidence ≤ 0.70 even for perfect fit
  7. abduction discipline → alternatives + missing_tests non-empty
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ─────────────────────────── HELPERS ─────────────────────────────────────────
SINGLE_PRISM = [{
    "easting": 0.0,
    "northing": 0.0,
    "depth_top": 200.0,
    "depth_bottom": 1200.0,
    "width_e": 3000.0,
    "width_n": 3000.0,
    "density": 500.0,  # kg/m^3 contrast — required key for HarmonICAdapter
}]

GRID_EXTENT_M = 4000.0  # tight enough that mock prism produces visible signal at 12×12
GRID_N = 12  # small for speed


def _run(coro):
    """Helper to run async coroutine in sync test."""
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def _forward_grid(prism_overrides: dict | None = None, **top_level_overrides) -> list[list[float]]:
    """Run the forward tool once and return the grid as 2D list.

    Args:
        prism_overrides: dict of fields to override on the SINGLE_PRISM template.
            e.g. {"depth_top": 1000.0, "width_e": 4000.0}
        **top_level_overrides: kwargs passed straight to geox_gravmag_studio_open,
            e.g. survey_type="magnetic"
    """
    from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

    prisms = [dict(SINGLE_PRISM[0])]
    if prism_overrides:
        prisms[0].update(prism_overrides)

    kwargs = dict(
        survey_type="gravity",
        prisms=prisms,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        backend="mock",
    )
    kwargs.update(top_level_overrides)
    out = asyncio.run(geox_gravmag_studio_open(**kwargs))
    if out.get("verdict") == "VOID":
        raise RuntimeError(f"forward returned VOID: {out.get('caveats')}")
    flat = out["render_payload"]["anomaly_values"]
    nx = out["render_payload"]["grid_shape"][1]
    ny = out["render_payload"]["grid_shape"][0]
    return [flat[i * nx:(i + 1) * nx] for i in range(ny)]


# ─────────────────────────── TESTS ────────────────────────────────────────────
def test_perfect_model_passes_screen():
    """Forward once, feed same grid back as observed → PASS_SCREEN, rms ≈ 0."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    predicted = _forward_grid()
    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="mGal",
        observed_source="synthetic_roundtrip",
        backend="mock",
    ))
    assert out["verdict"] == "PASS_SCREEN"
    assert out["_meta"]["epistemic"]["grade"] == "HYPOTHESIS_SCREEN"
    assert out["output"]["rms"] < 1e-6
    assert out["output"]["correlation"] > 0.999


def test_lateral_offset_fails_screen():
    """Candidate prism offset horizontally — must not PASS the screen.

    Note: we deliberately test *lateral* offset rather than *depth* offset because
    the MockHarmonICBackend point-mass approximation is genuinely depth-ambiguous
    (deep dense body ≈ shallow less-dense body). A horizontal shift, however, moves
    the anomaly peak location and the mock backend's point-mass formula discriminates
    that cleanly. Real geophysics has the same depth ambiguity — that is why
    grav/mag inversion is non-unique.
    """
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    observed = _forward_grid(prism_overrides={"easting": 0.0, "northing": 0.0})
    # Shift candidate 2 km east — anomaly peak must move
    wrong_prisms = [{**SINGLE_PRISM[0], "easting": 2000.0, "northing": 0.0}]

    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=wrong_prisms,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=observed,
        observed_units="mGal",
        observed_source="synthetic_lateral_offset",
        backend="mock",
    ))
    # Lateral shift of 2 km on a 4 km extent grid moves the anomaly peak
    # by ~6 cells, which the mock backend captures via point-mass formula.
    # Correlation should drop substantially; verdict should not be PASS_SCREEN.
    assert out["output"]["correlation"] < 0.7
    assert out["verdict"] in ("MARGINAL", "FAIL_SCREEN")
    assert out["output"]["rms"] > 0.0


def test_sign_flipped_density_fails_screen():
    """A candidate with negative-density contrast must NOT pass against a positive observed."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    # Forward with positive-density body
    observed = _forward_grid(prism_overrides={"density": 500.0})
    # Candidate with sign-flipped (negative) density — strong anti-correlation
    wrong_prisms = [{**SINGLE_PRISM[0], "density": -500.0}]
    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=wrong_prisms,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=observed,
        observed_units="mGal",
        observed_source="synthetic_sign_flip",
        backend="mock",
    ))
    # Sign-flipped density must produce strongly anti-correlated anomaly
    assert out["output"]["correlation"] < 0.0
    assert out["verdict"] == "FAIL_SCREEN"


def test_unit_mismatch_holds():
    """survey_type=gravity but observed.units=nT → HOLD, no comparison attempted."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=[[0.0] * GRID_N for _ in range(GRID_N)],
        observed_units="nT",  # wrong units
        observed_source="user_upload_csv",
        backend="mock",
    ))
    assert out["verdict"] == "HOLD"
    assert "observed.units=nT" in out["_meta"]["provenance"]["reason"]
    assert "expected mGal" in out["_meta"]["provenance"]["reason"]


def test_grid_mismatch_holds():
    """observed_grid shape ≠ grid_n² → HOLD."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=[[0.0] * (GRID_N - 4) for _ in range(GRID_N - 4)],  # wrong shape
        observed_units="mGal",
        observed_source="user_upload_csv",
        backend="mock",
    ))
    assert out["verdict"] == "HOLD"
    assert "shape" in out["_meta"]["provenance"]["reason"]


def test_confidence_cap_even_on_perfect_fit():
    """Even when rms ≈ 0, emitted confidence must be ≤ 0.70 (F7 HUMILITY)."""
    from geox_mcp.tools.geophysics_studio_screen import (
        SCREEN_CONFIDENCE_CAP,
        geox_gravmag_studio_screen,
    )

    predicted = _forward_grid()
    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="mGal",
        observed_source="synthetic_roundtrip",
        backend="mock",
    ))
    assert out["_meta"]["epistemic"]["confidence"] <= SCREEN_CONFIDENCE_CAP
    assert out["_meta"]["epistemic"]["confidence"] <= 0.70


def test_abduction_discipline_always_populated():
    """alternatives and missing_tests must always be non-empty."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    # Perfect case
    predicted = _forward_grid()
    out_pass = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="mGal",
        observed_source="synthetic_truth",
        backend="mock",
    ))
    assert len(out_pass["abduction"]["alternatives"]) > 0
    assert len(out_pass["abduction"]["missing_tests"]) > 0
    assert out_pass["abduction"]["primary_hypothesis"]
    assert out_pass["abduction"]["evidence_for"]
    assert out_pass["abduction"]["evidence_against"]

    # Magnetic case uses magnetic-specific default alternatives
    mag_pred = _forward_grid(
        survey_type="magnetic",
        magnetization_a_m=5.0,
        field_declination_deg=0.0,
        field_inclination_deg=5.0,
    )
    out_mag = asyncio.run(geox_gravmag_studio_screen(
        survey_type="magnetic",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=mag_pred,
        observed_units="nT",
        observed_source="synthetic_truth",
        backend="mock",
        magnetization_a_m=5.0,
        field_declination_deg=0.0,
        field_inclination_deg=5.0,
    ))
    assert any("remanence" in a.lower() for a in out_mag["abduction"]["alternatives"])

    # Explicit alternatives_declared wins
    explicit = ["my custom alt 1", "my custom alt 2"]
    out_explicit = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="mGal",
        observed_source="synthetic_truth",
        backend="mock",
        alternatives_declared=explicit,
    ))
    assert out_explicit["abduction"]["alternatives"] == explicit


def test_observed_source_recorded_in_provenance():
    """observed_source must appear in provenance for auditability.

    Uses synthetic_truth (skips fetcher probe). A separate test verifies
    that emag2v3 source triggers a fetcher-availability HOLD.
    """
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    predicted = _forward_grid()
    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="mGal",
        observed_source="synthetic_truth",
        backend="mock",
    ))
    assert out["_meta"]["provenance"]["observed_source"] == "synthetic_truth"
    assert out["governance"]["requires_888_hold"] is True
    assert "seal_claim" in out["governance"]["not_allowed_actions"]
    assert "issue_drilling_recommendation" in out["governance"]["not_allowed_actions"]


def test_extent_mismatch_holds():
    """Tightening #3: observed_extent_m ≠ grid_extent_m → HOLD."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    predicted = _forward_grid()
    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="mGal",
        observed_source="synthetic_truth",
        backend="mock",
        observed_extent_m=GRID_EXTENT_M * 2,  # wrong extent on purpose
    ))
    assert out["verdict"] == "HOLD"
    reason = out["_meta"]["provenance"].get("reason") or out["governance"].get("hold_reason", "")
    assert "extent" in reason.lower()

    # Within 1 m tolerance — should not HOLD
    out_ok = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="mGal",
        observed_source="synthetic_truth",
        backend="mock",
        observed_extent_m=GRID_EXTENT_M + 0.5,
    ))
    assert out_ok["verdict"] != "HOLD"


def test_zero_variance_observed_grid_holds():
    """Constant-valued observed grid → correlation undefined → HOLD."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    flat = [[1.5] * GRID_N for _ in range(GRID_N)]  # all-constant
    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=flat,
        observed_units="mGal",
        observed_source="user_upload_csv",
        backend="mock",
    ))
    assert out["verdict"] == "HOLD"
    reason = out["_meta"]["provenance"].get("reason") or out["governance"].get("hold_reason", "")
    assert "variance" in reason.lower() or "range" in reason.lower() or "rms" in reason.lower()


def test_declared_alternatives_preserved():
    """Tightening: alternatives_declared wins over default library, byte-for-byte."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    predicted = _forward_grid()
    explicit = ["remanence flip", "sediment loading", "unmodelled acquisition height"]
    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="magnetic",  # would normally inject magnetic defaults
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="nT",
        observed_source="synthetic_truth",
        backend="mock",
        magnetization_a_m=5.0,
        field_declination_deg=0.0,
        field_inclination_deg=5.0,
        alternatives_declared=explicit,
    ))
    assert out["abduction"]["alternatives"] == explicit

    # Empty list — still non-empty output (default library injected)
    out_empty = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=predicted,
        observed_units="mGal",
        observed_source="synthetic_truth",
        backend="mock",
        alternatives_declared=[],
    ))
    assert len(out_empty["abduction"]["alternatives"]) > 0
    assert out_empty["abduction"]["alternatives"] != []  # default library injected

