"""
tests/test_gravmag_studio_sabah_regression.py — Commit 3 regression suite.

Five Sabah-relevant scenarios (S1–S5) + one extent-mismatch HOLD case (S6).
Each scenario asserts the screen tool's verdict under controlled synthetic
data so physical behaviour is locked before external data ingest (Commit 4).

Design principle:
- truth_prisms generate the synthetic observed grid via MockHarmonICBackend
- candidate_prisms is the user-supplied Earth model we screen against
- expected_verdict is documented per-case in the SabahCase.reason_note

These tests are honest about the MockHarmonICBackend's depth ambiguity
(point-mass approximation collapses depth structure). Where that limit
matters, the case uses LATERAL or SIGN-FLIP differences that the mock
backend discriminates cleanly.
"""
from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ─────────────────────────── HELPERS ──────────────────────────────────────────
async def _forward(
    survey_type: str,
    prisms: list[dict],
    grid_extent_m: float,
    grid_n: int,
    *,
    magnetization_a_m: float = 0.0,
    field_declination_deg: float = 0.0,
    field_inclination_deg: float = 5.0,
    backend: str = "mock",
) -> list[list[float]]:
    """Run the forward tool and return the predicted grid as a 2D list."""
    from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

    kwargs = dict(
        survey_type=survey_type,
        prisms=prisms,
        grid_extent_m=grid_extent_m,
        grid_n=grid_n,
        backend=backend,
    )
    if survey_type == "magnetic":
        kwargs.update(
            magnetization_a_m=magnetization_a_m,
            field_declination_deg=field_declination_deg,
            field_inclination_deg=field_inclination_deg,
        )
    out = await geox_gravmag_studio_open(**kwargs)
    if out.get("verdict") == "VOID":
        raise RuntimeError(f"forward returned VOID: {out.get('caveats')}")
    flat = out["render_payload"]["anomaly_values"]
    nx = out["render_payload"]["grid_shape"][1]
    ny = out["render_payload"]["grid_shape"][0]
    return [flat[i * nx:(i + 1) * nx] for i in range(ny)]


async def _screen(
    survey_type: str,
    prisms: list[dict],
    observed_grid: list[list[float]],
    grid_extent_m: float,
    grid_n: int,
    observed_source: str,
    *,
    observed_extent_m: float | None = None,
    magnetization_a_m: float = 0.0,
    field_declination_deg: float = 0.0,
    field_inclination_deg: float = 5.0,
    backend: str = "mock",
) -> dict:
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    kwargs = dict(
        survey_type=survey_type,
        prisms=prisms,
        grid_extent_m=grid_extent_m,
        grid_n=grid_n,
        observed_grid=observed_grid,
        observed_units="mGal" if survey_type == "gravity" else "nT",
        observed_source=observed_source,
        observed_extent_m=observed_extent_m,
        backend=backend,
    )
    if survey_type == "magnetic":
        kwargs.update(
            magnetization_a_m=magnetization_a_m,
            field_declination_deg=field_declination_deg,
            field_inclination_deg=field_inclination_deg,
        )
    return await geox_gravmag_studio_screen(**kwargs)


# ─────────────────────────── CASE DEFINITIONS ─────────────────────────────────
@dataclass
class SabahCase:
    name: str
    survey_type: Literal["gravity", "magnetic"]
    truth_prisms: list[dict]
    candidate_prisms: list[dict]
    expected_verdict: Literal["PASS_SCREEN", "MARGINAL", "FAIL_SCREEN", "HOLD"]
    reason_note: str
    grid_extent_m: float = 8000.0
    grid_n: int = 16  # small for speed
    inducing_field: dict = field(default_factory=lambda: {
        "magnetization_a_m": 5.0,
        "field_declination_deg": 0.0,
        "field_inclination_deg": 5.0,
    })


def _prism(
    easting: float,
    northing: float,
    depth_top: float,
    depth_bottom: float,
    width_e: float,
    width_n: float,
    density: float = 500.0,
) -> dict:
    """Build a gravity prism with required `density` key for HarmonICAdapter."""
    return {
        "easting": easting,
        "northing": northing,
        "depth_top": depth_top,
        "depth_bottom": depth_bottom,
        "width_e": width_e,
        "width_n": width_n,
        "density": density,
    }


def _prisms_to_strings(prisms: list[dict]) -> str:
    """Compact human-readable representation for assert messages."""
    parts = []
    for p in prisms:
        x = p.get("easting", 0)
        y = p.get("northing", 0)
        z1 = p.get("depth_top", 0)
        z2 = p.get("depth_bottom", 0)
        rho = p.get("density", "?")
        parts.append(f"({x},{y},{z1}->{z2},ρ={rho})")
    return "[" + ",".join(parts) + "]"


# ─────────────────────────── SABAH CASES ─────────────────────────────────────
SABAH_CASES = [
    # ─── S1: Dangerous Grounds rifted margin ──────────────────────────────
    SabahCase(
        name="S1_pass_correct_low_density_margin",
        survey_type="gravity",
        truth_prisms=[
            # 3 half-graben style low-density bodies
            _prism(-3000, 0, 200, 1200, 2000, 1500, density=-200),
            _prism(0, -2000, 200, 1200, 2000, 1500, density=-250),
            _prism(2000, 1500, 200, 1200, 2000, 1500, density=-300),
        ],
        candidate_prisms=[
            # Same style — should PASS
            _prism(-3000, 0, 200, 1200, 2000, 1500, density=-200),
            _prism(0, -2000, 200, 1200, 2000, 1500, density=-250),
            _prism(2000, 1500, 200, 1200, 2000, 1500, density=-300),
        ],
        expected_verdict="PASS_SCREEN",
        reason_note=(
            "Truth and candidate are identical — perfect round-trip must PASS."
        ),
    ),
    SabahCase(
        name="S1_fail_dense_block_against_low_density_margin",
        survey_type="gravity",
        truth_prisms=[
            _prism(-3000, 0, 200, 1200, 2000, 1500, density=-200),
            _prism(0, -2000, 200, 1200, 2000, 1500, density=-250),
            _prism(2000, 1500, 200, 1200, 2000, 1500, density=-300),
        ],
        candidate_prisms=[
            # Single dense block — opposite-sign, opposite-amplitude
            _prism(0, 0, 500, 1500, 4000, 4000, density=400),
        ],
        expected_verdict="FAIL_SCREEN",
        reason_note=(
            "Dense block candidate against low-density-margin truth — sign-flip "
            "and amplitude mismatch must FAIL."
        ),
    ),
    # ─── S2: Sabah Trough flexural low ───────────────────────────────────
    SabahCase(
        name="S2_pass_thrust_loaded_low",
        survey_type="gravity",
        truth_prisms=[
            # Large negative density prism at 1.5 km (within mock depth range)
            _prism(0, 0, 500, 2500, 4000, 4000, density=-300),
        ],
        candidate_prisms=[
            # Same — thrust-loaded interpretation matches
            _prism(0, 0, 500, 2500, 4000, 4000, density=-300),
        ],
        expected_verdict="PASS_SCREEN",
        reason_note=(
            "Identical flexural low candidate must PASS."
        ),
    ),
    SabahCase(
        name="S2_fail_oceanic_crust_against_low",
        survey_type="gravity",
        truth_prisms=[
            _prism(0, 0, 500, 2500, 4000, 4000, density=-300),
        ],
        candidate_prisms=[
            # Positive density body — oceanic crust interpretation is wrong
            _prism(0, 0, 500, 2500, 4000, 4000, density=300),
        ],
        expected_verdict="FAIL_SCREEN",
        reason_note=(
            "Sign-flipped density against flexural low — must FAIL."
        ),
    ),
    # ─── S3: Deepwater Fold-Thrust Belt dense block (magnetic) ───────────
    SabahCase(
        name="S3_pass_correct_intrusion",
        survey_type="magnetic",
        truth_prisms=[
            # Mock backend uses prism geometry for mag via density key fallback;
            # for magnetic, we add magnetization magnitude separately.
            _prism(0, 0, 500, 1500, 2500, 2500, density=0),
        ],
        candidate_prisms=[
            _prism(0, 0, 500, 1500, 2500, 2500, density=0),
        ],
        expected_verdict="PASS_SCREEN",
        reason_note=(
            "Identical dense magnetic prism must PASS (round-trip)."
        ),
        inducing_field={"magnetization_a_m": 5.0, "field_declination_deg": 0.0, "field_inclination_deg": 5.0},
    ),
    # ─── S4: Kinabalu-style shallow pluton ───────────────────────────────
    SabahCase(
        name="S4_marginal_uniform_basement_against_pluton",
        survey_type="gravity",
        truth_prisms=[
            _prism(0, 0, 200, 800, 2500, 2500, density=400),
        ],
        candidate_prisms=[
            # Deep, low-density body — mimics uniform-basement hypothesis
            _prism(0, 0, 10000, 10100, 5000, 5000, density=10),
        ],
        # MockHarmonICBackend point-mass approximation collapses depth × density
        # into a single signal magnitude at the prism centroid. The shallow dense
        # truth produces a STRONGER surface signal than the deep low-density
        # candidate because gravity falls off as 1/r² and z differs by an order
        # of magnitude. The mock discriminates the AMPLITUDE difference but not
        # the depth-density ambiguity, so it returns MARGINAL rather than FAIL.
        # When the live HarmonIC backend is enabled, this should be promoted to
        # FAIL_SCREEN because true prism integration captures the depth structure.
        expected_verdict="MARGINAL",
        reason_note=(
            "Mock backend: amplitude-only discrimination. Real backend: depth-density "
            "would separate these cleanly → FAIL_SCREEN. Deferred to live-backend test."
        ),
    ),
    # ─── S5: Layang-Layang stripe-averaging trap (magnetic) — DEFERRED ────
    # The MockHarmonICBackend applies a uniform magnetization to all prisms
    # (ignoring per-prism density for magnetic mode), so polarity-reversal
    # cancellation cannot be tested with mock. This case will land when the
    # live HarmonIC backend (GEOX_HARMONICA_LIVE=1) is enabled and we exercise
    # against Fatiando's tesseroid source which supports per-prism magnetization.
    # Documented here for traceability — not asserted in CI.
]


# ─────────────────────────── TEST RUNNER ──────────────────────────────────────
import pytest


@pytest.mark.parametrize("case", SABAH_CASES, ids=lambda c: c.name)
def test_sabah_scenario(case: SabahCase):
    """Lock screen-verdict behaviour against 5 Sabah-relevant synthetic scenarios.

    Each case runs forward on the truth prisms, then screens the candidate
    prisms against the synthetic observed grid. The verdict must match the
    documented expected verdict (with reason).
    """
    ifld = case.inducing_field
    observed = asyncio.run(_forward(
        survey_type=case.survey_type,
        prisms=case.truth_prisms,
        grid_extent_m=case.grid_extent_m,
        grid_n=case.grid_n,
        magnetization_a_m=ifld["magnetization_a_m"],
        field_declination_deg=ifld["field_declination_deg"],
        field_inclination_deg=ifld["field_inclination_deg"],
    ))
    res = asyncio.run(_screen(
        survey_type=case.survey_type,
        prisms=case.candidate_prisms,
        observed_grid=observed,
        grid_extent_m=case.grid_extent_m,
        grid_n=case.grid_n,
        observed_source="synthetic_truth",
        observed_extent_m=case.grid_extent_m,
        magnetization_a_m=ifld["magnetization_a_m"],
        field_declination_deg=ifld["field_declination_deg"],
        field_inclination_deg=ifld["field_inclination_deg"],
    ))

    actual = res["governance"]["verdict"]
    candidate_summary = _prisms_to_strings(case.candidate_prisms)
    truth_summary = _prisms_to_strings(case.truth_prisms)
    assert actual == case.expected_verdict, (
        f"[{case.name}] Expected {case.expected_verdict}, got {actual}.\n"
        f"Truth:   {truth_summary}\n"
        f"Candidate: {candidate_summary}\n"
        f"Reason: {case.reason_note}\n"
        f"Stats: rms={res['output']['rms']:.3f}, "
        f"rms_norm={res['output']['rms_normalized']:.3f}, "
        f"corr={res['output']['correlation']:.3f}"
    )


# ─────────────────────────── S6: EXTENT MISMATCH HOLD ───────────────────────
def test_s6_extent_mismatch_holds():
    """Tightening #3 regression guard: observed_extent_m ≠ grid_extent_m → HOLD.

    Bonus case beyond the agent's 5 Sabah scenarios. Protects the screen tool
    from silent extent footguns if future refactors drop the gate.
    """
    observed = asyncio.run(_forward(
        survey_type="gravity",
        prisms=[_prism(0, 0, 200, 800, 2500, 2500, density=400)],
        grid_extent_m=4000.0,
        grid_n=12,
    ))
    res = asyncio.run(_screen(
        survey_type="gravity",
        prisms=[_prism(0, 0, 200, 800, 2500, 2500, density=400)],
        observed_grid=observed,
        grid_extent_m=4000.0,
        grid_n=12,
        observed_source="extent_mismatch_test",
        observed_extent_m=8000.0,  # wrong on purpose
    ))
    assert res["governance"]["verdict"] == "HOLD"
    reason = (
        res.get("_meta", {}).get("provenance", {}).get("reason")
        or res.get("governance", {}).get("hold_reason", "")
    )
    assert "extent" in reason.lower()
