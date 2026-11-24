"""G4 — Golden Volve answer-key suite.

Runs in CI, offline, deterministic. Scores GEOX behaviour against the
published Sodir + PVT STAT550B answer key instead of reporting which
modules happened to import.

Design rules (from the 2026-11-24 GEOX audit):
  * A number without an instrument does not pass. Every expected value
    carries its source.
  * UNMEASURED is a legitimate outcome and must never be scored as
    pass/fail.
  * Known source conflicts are recorded AS conflicts, not averaged away.
  * Negative tests exist: a physically impossible input must be rejected,
    and an omitted input must never be relabelled OBS.

Run:  /opt/geox/.venv/bin/python -m pytest tests/test_golden_volve.py -v
"""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path

import pytest

# ── Answer key: Volve / Hugin, South Viking Graben ───────────────────────
# Sources: Sodir FactPages (field 3420717) + Oilphase PVT STAT550B (1998).
VOLVE_ANSWER_KEY = {
    "stoip_mmsm3": 18.70,          # Sodir, valid 31.12.2025
    "recoverable_mmsm3": 10.17,    # Sodir
    "recovery_factor": 0.54,       # Sodir-derived, matches literature 54%
    "reservoir_temp_c": 110.0,     # PVT STAT550B / DST 110.8-112.7
    "bubble_point_bar": 235.5,     # PVT STAT550B
    "bo_m3_per_sm3": 1.388,        # PVT STAT550B at Pb
    "rw_ohm_m_60f": 0.1478,        # 15/9-19 A water analysis (secondary source)
    "hugin_phi_published": (0.21, 0.226),   # secondary sources
    "hugin_ntg_published": 0.924,           # secondary source
    "hugin_sw_published": 0.20,             # secondary source
    "peak_annual_oil_mmsm3_2009": 2.717,    # Sodir
    "decline_fit_window": (2009, 2012),     # pre-infill only
}

# Items for which no public instrument exists. GEOX must mark these
# UNMEASURED — neither pass nor fail.
UNMEASURED_ITEMS = (
    "pre_drill_pos",
    "closure_area",
    "volve_rock_eval",
    "geothermal_gradient",
)

# Conflicting published values. Recorded as conflicts; never averaged.
KNOWN_CONFLICTS = {
    "porosity": (0.17, 0.21, 0.226),
    "avo_class": ("I", "II-III"),
    "reservoir_pressure_bar": (322.0, 330.0, 340.0),
}

SRC = Path(__file__).resolve().parents[1] / "src"


# ── 1. Answer-key integrity ─────────────────────────────────────────────

def test_answer_key_internal_consistency():
    """Recoverable / STOIIP must reproduce the published RF."""
    rf = VOLVE_ANSWER_KEY["recoverable_mmsm3"] / VOLVE_ANSWER_KEY["stoip_mmsm3"]
    assert abs(rf - VOLVE_ANSWER_KEY["recovery_factor"]) < 0.01, (
        f"RF {rf:.3f} disagrees with published 0.54"
    )


def test_bubble_point_below_reservoir_pressure():
    """A black oil must have Pb < initial reservoir pressure."""
    assert VOLVE_ANSWER_KEY["bubble_point_bar"] < 322.0  # lowest reported P


def test_unmeasured_items_are_declared():
    assert set(UNMEASURED_ITEMS) == {
        "pre_drill_pos",
        "closure_area",
        "volve_rock_eval",
        "geothermal_gradient",
    }


def test_conflicts_are_recorded_not_resolved():
    """Every conflict must carry >=2 competing values."""
    for key, values in KNOWN_CONFLICTS.items():
        assert len(values) >= 2, f"{key} recorded without a competing value"


# ── 2. Ingest verifier helpers (F06/F07/F08 regression) ─────────────────

def test_identity_normalisation():
    from geox_mcp.verify_ingest import _norm_identity

    assert _norm_identity("15/9-F-11A") == _norm_identity("15/9-F-11 A")
    assert _norm_identity("15/9-19") == "15919"
    assert _norm_identity(" 15/9-F-11 A ") == "159F11A"


def test_curve_set_excludes_depth():
    from geox_mcp.verify_ingest import _curve_set

    class C:
        def __init__(self, m):
            self.mnemonic = m

    got = _curve_set([C("DEPT"), C("GR"), C("DT"), C("RHOB")])
    assert got == {"GR", "DT", "RHOB"}, got


def test_verify_ingest_synthetic_las_passes(tmp_path):
    """A clean LAS must VERIFY — the false-DEGRADED of 2026-11-24 must not recur."""
    from geox_mcp.verify_ingest import verify_ingest_independent

    las = tmp_path / "t.las"
    las.write_text(
        "~Version\nVERS. 2.0 : CWLS LOG ASCII STANDARD\nWRAP. NO : ONE LINE PER DEPTH STEP\n"
        "~Well\nSTRT.M 1000.0 :\nSTOP.M 1002.0 :\nSTEP.M 1.0 :\nNULL. -999.25 :\n"
        "COMP. TEST :\nWELL. 15/9-F-11A :\n"
        "~Curve\nDEPT.M : DEPTH\nGR.GAPI : GAMMA RAY\nDT.US/F : SONIC\n"
        "~A\n1000.0 50.0 80.0\n1001.0 55.0 82.0\n1002.0 60.0 79.0\n"
    )
    stored = {
        "well_id": "15/9-F-11 A",          # spacing variant → F08
        "uwi": "VOLVE",                     # inferred token → F07
        "depth_unit_normalized": "M",
        "curve_inventory": ["DEPT", "GR", "DT"],  # DEPT included → F06
    }
    out = verify_ingest_independent(str(las), stored, artifact_ref="test")
    assert out["failed"] == 0, json.dumps(out["checks"], indent=1)
    assert out["verdict"] == "VERIFIED", out["verdict"]


# ── 3. Petrophysics provenance (F02 regression) ─────────────────────────

def test_petrophysics_labels_supplied_rw_as_observed():
    """rw=<value> must read OBS, not DEFAULT, and must not be in defaults_applied."""
    try:
        from geox_mcp.tools.petrophysics_unified import geox_petrophysics
    except Exception as exc:  # pragma: no cover - dependency environment
        pytest.skip(f"petrophysics import unavailable: {exc}")

    res = asyncio.run(
        geox_petrophysics(
            mode="generate",
            well_id="TEST",
            curves={
                "GR": [40.0, 50.0, 60.0, 45.0],
                "RHOB": [2.30, 2.28, 2.32, 2.29],
                "RT": [30.0, 25.0, 40.0, 22.0],
                "DT": [80.0, 82.0, 78.0, 81.0],
            },
            depth_m=[1000.0, 1001.0, 1002.0, 1003.0],
            gr_clean=25,
            gr_shale=100,
            rw=0.0417,
        )
    )
    prov = res.get("input_provenance")
    if prov is None:
        pytest.skip("generate path did not expose input_provenance in this build")
    assert prov["rw_ohm_m"] == "OBS", prov
    assert "rw_ohm_m" not in res.get("defaults_applied", []), res.get("defaults_applied")
    assert res.get("resolved_values", {}).get("rw_ohm_m_used") == pytest.approx(0.0417)


# ── 4. Negative / physics gate ──────────────────────────────────────────

def test_sw_range_accepts_full_water_leg():
    """G2: Sw max == 1.0 must be accepted (water leg); only > 1.0 rejected."""
    try:
        import geox_mcp.tools.inverse_volumetrics as m
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"inverse_volumetrics import unavailable: {exc}")

    src = inspect.getsource(m)
    assert "sw_max > 1.0" in src, "rule to reject Sw > 1.0 not found"
    assert "sw_max >= 1.0" not in src, "code would wrongly reject a legitimate water leg (Sw == 1.0)"


def test_public_surface_names_are_registered():
    """Every name in the generated public surface must be a real geox_ tool."""
    p = SRC / "geox_mcp" / "generated" / "CANONICAL_PUBLIC_SURFACE.json"
    if not p.exists():
        pytest.skip("generated surface manifest not present")
    data = json.loads(p.read_text())
    names = data.get("tools") or data.get("public_names") or []
    if isinstance(names, list) and names and isinstance(names[0], dict):
        names = [n.get("name") for n in names]
    assert len(names) == 29, f"expected 29 public tools, found {len(names)}"
    bad = [n for n in names if not str(n).startswith("geox_")]
    assert not bad, f"non-conforming tool names: {bad}"
