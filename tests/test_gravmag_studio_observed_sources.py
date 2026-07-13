"""
tests/test_gravmag_studio_observed_sources.py — Commit 4 fetch-hook tests.

Five tests covering the observed_source guards in geox_gravmag_studio_screen:

1. EMAG2v3 with survey_type=gravity → HOLD (wrong survey_type for source)
2. ICGEM with survey_type=magnetic → HOLD (wrong survey_type for source)
3. EMAG2v3 with survey_type=magnetic → HOLD (fetcher in offline_stub OR
   grid extraction deferred — both are honest boundary conditions)
4. ICGEM with survey_type=gravity → HOLD (same reason as EMAG2v3)
5. Arbitrary / unrecognised source name → HOLD (whitelist enforcement)

All tests assert HOLD with a specific reason in provenance — no silent fallbacks.

Honest MVP scope: the fetchers are wired in and validated, but actual
bbox→grid_n×grid_n grid extraction is deferred. The HOLD reason names
that limitation so downstream consumers see the boundary, not a silent
fallback. The agent's Commit 4 spec explicitly notes this is operator-side
for now.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ─────────────────────────── HELPERS ──────────────────────────────────────────
SINGLE_PRISM = [{
    "easting": 0.0,
    "northing": 0.0,
    "depth_top": 200.0,
    "depth_bottom": 1200.0,
    "width_e": 3000.0,
    "width_n": 3000.0,
    "density": 500.0,
}]
GRID_EXTENT_M = 4000.0
GRID_N = 12


def _hold_reason(out: dict) -> str:
    """Pull HOLD reason from provenance or governance."""
    prov_reason = (
        out.get("_meta", {}).get("provenance", {}).get("reason")
    )
    gov_reason = out.get("governance", {}).get("hold_reason")
    return (prov_reason or gov_reason or "").lower()


# ─────────────────────────── TESTS ────────────────────────────────────────────
def test_emag2v3_with_gravity_survey_holds():
    """Commit 4 #1: EMAG2v3 requires survey_type=magnetic.

    Using EMAG2v3 with survey_type=gravity is a unit/dimension footgun
    (global magnetic anomaly grid has no business on a gravity survey).
    Must HOLD with reason mentioning emag2v3 + survey_type.
    """
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=[[0.0] * GRID_N for _ in range(GRID_N)],
        observed_units="mGal",
        observed_source="emag2v3",  # wrong — must be magnetic
        backend="mock",
    ))
    assert out["verdict"] == "HOLD"
    reason = _hold_reason(out)
    assert "emag2v3" in reason
    assert "magnetic" in reason
    assert "gravity" in reason  # explicitly names the wrong type


def test_icgem_with_magnetic_survey_holds():
    """Commit 4 #2: ICGEM requires survey_type=gravity."""
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="magnetic",  # wrong — must be gravity
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=[[0.0] * GRID_N for _ in range(GRID_N)],
        observed_units="nT",
        observed_source="icgem",
        backend="mock",
        magnetization_a_m=5.0,
        field_declination_deg=0.0,
        field_inclination_deg=5.0,
    ))
    assert out["verdict"] == "HOLD"
    reason = _hold_reason(out)
    assert "icgem" in reason
    assert "gravity" in reason
    assert "magnetic" in reason  # explicitly names the wrong type


def test_emag2v3_with_magnetic_survey_holds_until_grid_extraction():
    """Commit 4 #3: correct coupling, but fetcher is offline_stub by default
    (GEOX_EMAG2_OFFLINE=1). HOLD reason must explicitly name the limitation.

    Once live HarmonIC + bbox→grid extraction lands, this test's reason
    must be updated to reflect a new boundary condition (not deleted).
    """
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    # Ensure the offline flag is on (CI default).
    assert os.environ.get("GEOX_EMAG2_OFFLINE", "1") == "1"

    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="magnetic",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=[[0.0] * GRID_N for _ in range(GRID_N)],
        observed_units="nT",
        observed_source="emag2v3",
        backend="mock",
        magnetization_a_m=5.0,
        field_declination_deg=0.0,
        field_inclination_deg=5.0,
    ))
    assert out["verdict"] == "HOLD"
    reason = _hold_reason(out)
    # Either offline_stub OR grid-extraction-deferred — both are honest
    # boundary conditions depending on env state.
    assert ("offline_stub" in reason) or ("not yet implemented" in reason)
    assert "emag2v3" in reason


def test_icgem_with_gravity_survey_holds_until_grid_extraction():
    """Commit 4 #4: correct coupling, ICGEM list_models returns empty (no real
    network call), or grid extraction deferred. HOLD reason must surface.
    """
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=[[0.0] * GRID_N for _ in range(GRID_N)],
        observed_units="mGal",
        observed_source="icgem",
        backend="mock",
    ))
    assert out["verdict"] == "HOLD"
    reason = _hold_reason(out)
    # ICGEM list_models returns [] unless populated; we accept either
    # "no models" or "not yet implemented" as honest boundary conditions.
    assert ("no models" in reason) or ("not yet implemented" in reason)
    assert "icgem" in reason


def test_unrecognised_source_name_holds():
    """Commit 4 #5: arbitrary source name → HOLD (whitelist enforcement).

    Prevents users from inventing source names like 'noaa' or 'foo' that
    bypass the governance contract.
    """
    from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen

    out = asyncio.run(geox_gravmag_studio_screen(
        survey_type="gravity",
        prisms=SINGLE_PRISM,
        grid_extent_m=GRID_EXTENT_M,
        grid_n=GRID_N,
        observed_grid=[[0.0] * GRID_N for _ in range(GRID_N)],
        observed_units="mGal",
        observed_source="noaa_arbitrary_v3",  # not in whitelist
        backend="mock",
    ))
    assert out["verdict"] == "HOLD"
    reason = _hold_reason(out)
    assert "whitelist" in reason
    assert "noaa_arbitrary_v3" in reason
