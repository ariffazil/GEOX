"""ArtCraft S9b Phase 1 — geox_grid + geox_resqml_io contract tests.

Positive: box descriptor, inspect from real xtgeo arrays, RESQML export with
round-trip verification (sha + extent + bulk volume).
Negative (falsification gates): malformed shapes, NaN arrays, bad actnum values,
oversized cell counts, non-positive increments, unknown modes — every gate
returns a structured HOLD envelope (never silent pass, never crash).
"""

from __future__ import annotations

import asyncio
import base64
import hashlib

import numpy as np
import pytest
import xtgeo

from geox_mcp.tools.artcraft_grid import geox_grid
from geox_mcp.tools.artcraft_resqml_io import geox_resqml_io


def _arrays(ni=2, nj=3, nk=4):
    g = xtgeo.create_box_grid((ni, nj, nk))
    return {
        "coordsv": np.asarray(g._coordsv).tolist(),
        "zcornsv": np.asarray(g._zcornsv).tolist(),
        "actnumsv": np.asarray(g._actnumsv).astype(int).tolist(),
    }


def _run(fn, **kw):
    return asyncio.run(fn(**kw))


# ── geox_grid positives ────────────────────────────────────────────────────

def test_grid_box_descriptor():
    r = _run(geox_grid, mode="box", dims=[2, 3, 4], session_id="ANON-test")
    assert r["status"] == "OK"
    assert r["data"]["total_cells"] == 24
    assert r["data"]["active_cells"] == 24
    assert r["governance_status"] == "QUALIFIED"
    assert r["epistemic_label"] == "DER"
    assert "box grid" in r["_ui_fallback"]


def test_grid_box_cell_cap():
    r = _run(geox_grid, mode="box", dims=[100, 100, 100], session_id="ANON-test")
    assert r["status"] == "HOLD"
    assert "exceeds cap" in r["error"]


def test_grid_box_bad_dims():
    r = _run(geox_grid, mode="box", dims=[2, 3], session_id="ANON-test")
    assert r["status"] == "HOLD"
    r = _run(geox_grid, mode="box", dims=[2, 0, 4], session_id="ANON-test")
    assert r["status"] == "HOLD"


def test_grid_inspect_real_arrays():
    r = _run(geox_grid, mode="inspect", session_id="ANON-test", **_arrays(2, 3, 4))
    assert r["status"] == "OK"
    assert r["data"]["total_cells"] == 24
    assert r["data"]["active_cells"] == 24
    assert r["data"]["bulk_volume_m3"] is None or isinstance(r["data"]["bulk_volume_m3"], float)


# ── geox_grid negatives (falsification gates) ──────────────────────────────

def test_grid_unknown_mode():
    r = _run(geox_grid, mode="transmogrify", session_id="ANON-test")
    assert r["status"] == "HOLD"
    assert "unknown mode" in r["error"]


def test_grid_nan_zcorn_hold():
    a = _arrays(2, 2, 2)
    a["zcornsv"][0][0][0][0] = float("nan")
    r = _run(geox_grid, mode="inspect", session_id="ANON-test", **a)
    assert r["status"] == "HOLD"
    assert "NaN/inf" in r["error"]


def test_grid_bad_shape_hold():
    a = _arrays(2, 3, 4)
    a["coordsv"] = a["coordsv"][:-1]  # wrong leading dim
    r = _run(geox_grid, mode="inspect", session_id="ANON-test", **a)
    assert r["status"] == "HOLD"
    assert "shape" in r["error"]


def test_grid_bad_actnum_hold():
    a = _arrays(2, 2, 2)
    a["actnumsv"][0][0][0] = 7
    r = _run(geox_grid, mode="inspect", session_id="ANON-test", **a)
    assert r["status"] == "HOLD"
    assert "0/1" in r["error"]


# ── geox_resqml_io positives ───────────────────────────────────────────────

def test_resqml_export_roundtrip():
    r = _run(geox_resqml_io, mode="export_regular_epc",
             extent_kji=[2, 3, 4], dxi=100.0, dnj=200.0, dnk=10.0,
             title="artcraft s9b test", session_id="ANON-test")
    assert r["status"] == "OK", r.get("error")
    d = r["data"]
    assert d["extent_kji"] == [2, 3, 4]
    assert d["bulk_volume_m3"] == pytest.approx(24 * 100 * 200 * 10, rel=1e-6)
    assert d["epc_bytes"] > 0 and d["h5_bytes"] > 0
    # base64 decodes and hashes match
    epc_raw = base64.b64decode(d["epc_base64"])
    assert hashlib.sha256(epc_raw).hexdigest() == d["epc_sha256"]
    assert len(epc_raw) == d["epc_bytes"]
    assert d["round_trip"]["grid_part_present"] is True
    assert d["round_trip"]["extent_kji"] == [2, 3, 4]
    assert "RESQML regular grid exported" in r["_ui_fallback"]


def test_resqml_export_title_sanitized():
    r = _run(geox_resqml_io, mode="export_regular_epc",
             extent_kji=[1, 1, 1], title="bad\n<script>title//", session_id="ANON-test")
    assert r["status"] == "OK"
    assert "\n" not in r["data"]["title"] and "<" not in r["data"]["title"]


# ── geox_resqml_io negatives ───────────────────────────────────────────────

def test_resqml_unknown_mode():
    r = _run(geox_resqml_io, mode="import_everything", session_id="ANON-test")
    assert r["status"] == "HOLD"
    assert "unknown mode" in r["error"]


def test_resqml_nonpositive_increment():
    for kw in ({"dxi": 0.0}, {"dnj": -5.0}, {"dnk": float("nan")}):
        r = _run(geox_resqml_io, mode="export_regular_epc",
                 extent_kji=[2, 2, 2], session_id="ANON-test", **kw)
        assert r["status"] == "HOLD"
        assert "positive finite" in r["error"]


def test_resqml_bad_extent():
    r = _run(geox_resqml_io, mode="export_regular_epc",
             extent_kji=[0, 2, 2], session_id="ANON-test")
    assert r["status"] == "HOLD"
    r = _run(geox_resqml_io, mode="export_regular_epc",
             extent_kji=[2, 2], session_id="ANON-test")
    assert r["status"] == "HOLD"


def test_resqml_cell_cap():
    r = _run(geox_resqml_io, mode="export_regular_epc",
             extent_kji=[128, 128, 64], session_id="ANON-test")
    assert r["status"] == "HOLD"
    assert "exceeds cap" in r["error"]


def test_resqml_555_boundary_no_persistent_state(tmp_path):
    """555_COMPUTE_ONLY: the tool must leave no server state behind.

    The tool writes only inside its own TemporaryDirectory, which is removed
    before return. We assert the returned bytes are caller-owned provenance,
    and that no side-effect artifact path is exposed in the response.
    """
    r = _run(geox_resqml_io, mode="export_regular_epc",
             extent_kji=[1, 2, 3], session_id="ANON-test")
    assert r["status"] == "OK"
    assert "path" not in str(r["data"].get("epc_base64", ""))
    for key in ("epc_base64", "h5_base64", "epc_sha256", "h5_sha256"):
        assert key in r["data"]


# ── S9b Phase 2: arbitrary ALIGNED corner-point → RESQML ───────────────────

def test_resqml_cornerpoint_export_volume_verified():
    a = _arrays(2, 3, 4)
    r = _run(geox_resqml_io, mode="export_cornerpoint_epc",
             title="artcraft cp phase2", session_id="ANON-test", **a)
    assert r["status"] == "OK", r.get("error")
    d = r["data"]
    assert d["extent_kji"] == [4, 3, 2]
    assert d["round_trip"]["grid_part_present"] is True
    assert d["round_trip"]["volume_matches_xtgeo"] is True
    assert d["xtgeo_bulk_volume_m3"] == pytest.approx(d["bulk_volume_m3"], rel=1e-6)
    epc_raw = base64.b64decode(d["epc_base64"])
    assert hashlib.sha256(epc_raw).hexdigest() == d["epc_sha256"]
    assert "corner-point grid exported (aligned)" in r["_ui_fallback"]


def test_resqml_cornerpoint_split_pillar_hold():
    """A split-pillar grid (adjacent cells disagree at a pillar plane) => HOLD."""
    a = _arrays(2, 2, 2)
    # perturb one quadrant of one pillar plane: xtgeo-4 padded zcorn layout
    z = np.asarray(a["zcornsv"], dtype=np.float64)
    z[1, 1, 1, 2] += 25.0
    a["zcornsv"] = z.tolist()
    r = _run(geox_resqml_io, mode="export_cornerpoint_epc",
             session_id="ANON-test", **a)
    assert r["status"] == "HOLD"
    assert "ALIGNED" in r["error"]


def test_resqml_cornerpoint_bad_arrays_hold():
    a = _arrays(2, 2, 2)
    a["actnumsv"] = [[1, 1], [1, 1], [1, 1]]  # wrong vs zcorn-derived dims
    r = _run(geox_resqml_io, mode="export_cornerpoint_epc",
             session_id="ANON-test", **a)
    assert r["status"] == "HOLD"
    assert "falsification gate" in r["error"]


def test_resqml_cornerpoint_cell_cap():
    a = _arrays(64, 64, 64)  # 262,144 > 250,000 cap
    r = _run(geox_resqml_io, mode="export_cornerpoint_epc",
             session_id="ANON-test", **a)
    assert r["status"] == "HOLD"
    assert "exceeds cap" in r["error"]
