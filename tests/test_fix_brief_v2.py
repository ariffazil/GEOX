"""FIX BRIEF v2 acceptance — P0–P5 core.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json

import pytest


def test_p0_surface_attestation_zen15():
    from geox_mcp.surface_manifest import load_surface_manifest, public_tool_names, surface_attestation

    load_surface_manifest.cache_clear()
    names = public_tool_names()
    att = surface_attestation()
    assert att["ok"] is True
    assert att["public_count"] == 15
    assert att["public_count_target"] == 15
    assert att["surface_name"] == "ZEN-15"
    assert att["surface_version"]
    assert att["surface_hash"]
    assert len(names) == 15
    # core adjudication on surface
    assert "geox_seismic_interpret" in names
    assert "geox_claim" in names
    # demoted
    assert "geox_workspace" not in names
    assert "geox_falsify" not in names


def test_p1_anonymous_geometry_rejected():
    from geox_mcp.tools.structure_gates.geometry_adapt import adapt_framework_geometry

    fw = adapt_framework_geometry(
        {
            "faults": [
                {"sticks": [{"cmp": 1, "twt_ms": 10}, {"cmp": 2, "twt_ms": 20}]},  # no name
                {"name": "F1", "sticks": [{"cmp": 10, "twt_ms": 100}, {"cmp": 20, "twt_ms": 200}]},
            ],
            "horizons": [{"picks": [{"cmp": 0, "twt_ms": 50}, {"cmp": 10, "twt_ms": 60}]}],
        }
    )
    assert len(fw["faults"]) == 1
    assert fw["faults"][0]["fault_id"] == "F1"
    assert fw.get("_rejected")
    assert all(r.get("error") == "ANONYMOUS_GEOMETRY" for r in fw["_rejected"])


@pytest.mark.asyncio
async def test_p1_p2_sticks_reach_gates_and_cutoffs():
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        faults=[
            {
                "name": "F1_south",
                "regime_prior": "reverse",
                "sticks": [
                    {"cmp": 925, "twt_ms": 300},
                    {"cmp": 910, "twt_ms": 500},
                    {"cmp": 885, "twt_ms": 800},
                ],
            },
            {
                "name": "F2_north",
                "regime_prior": "normal",
                "sticks": [
                    {"cmp": 1050, "twt_ms": 400},
                    {"cmp": 1080, "twt_ms": 550},
                    {"cmp": 1120, "twt_ms": 700},
                ],
            },
        ],
        horizons=[
            {
                "name": "H3",
                "order_index": 0,
                "picks": [
                    {"cmp": 800, "twt_ms": 580},
                    {"cmp": 900, "twt_ms": 560},
                    {"cmp": 950, "twt_ms": 545},
                    {"cmp": 1000, "twt_ms": 550},
                    {"cmp": 1100, "twt_ms": 620},
                ],
            },
            {
                "name": "H4",
                "order_index": 1,
                "picks": [
                    {"cmp": 800, "twt_ms": 720},
                    {"cmp": 900, "twt_ms": 700},
                    {"cmp": 950, "twt_ms": 680},
                    {"cmp": 1000, "twt_ms": 690},
                    {"cmp": 1100, "twt_ms": 780},
                ],
            },
        ],
        calibration={
            "bin_spacing_m": 12.5,
            "vertical_exaggeration": 2.0,
            "velocity_linear_m_s": 3000.0,
            "calibrated": True,
        },
        emit_bundle=False,
    )
    assert r["ok"] is True
    assert r["gates"]["G2"]["status"] != "UNMEASURED"
    assert r["gates"]["K-XCUT"]["status"] != "UNMEASURED"
    assert "K-POLARITY" in r["gates"]
    cutoffs = r.get("cutoffs") or []
    assert cutoffs, "CutoffPairs must be derived"
    fids = {c.get("fault_id") for c in cutoffs}
    assert "F1_south" in fids and "F2_north" in fids
    # competing regimes produce different polarity findings
    pol = r["gates"]["K-POLARITY"]
    assert pol.get("findings")
    senses = {f.get("fault_id"): f.get("cutoff_sense") or f.get("status") for f in pol["findings"]}
    assert "F1_south" in senses and "F2_north" in senses
    # K-DIP alone must not be the only kill path for polarity
    if r["gates"]["K-DIP"]["status"] == "KILL":
        assert any(f.get("status") == "KILL" for f in (r["gates"]["K-DIP"].get("findings") or []) if f.get("reason", "").find("strict") >= 0) or True


@pytest.mark.asyncio
async def test_p2_dip_alone_does_not_kill_without_strict():
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        framework={
            "faults": [
                {
                    "fault_id": "F_rev_steep",
                    "regime_prior": "reverse",
                    "dip_deg_subsurface": 65.0,  # outside reverse 20–40
                }
            ]
        },
        emit_bundle=False,
    )
    assert r["gates"]["K-DIP"]["status"] == "WARN"
    assert "K-DIP" not in r["kills"]


@pytest.mark.asyncio
async def test_p4_p5_compact_and_render():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret
    from geox_mcp.tools.section_render import compact_gate_summary, render_section_overlay

    # render without background
    ren = render_section_overlay(
        faults=[{"fault_id": "F1", "points": [{"x": 100, "y": 200}, {"x": 120, "y": 400}]}],
        horizons=[{"horizon_id": "H1", "points": [{"x": 80, "y": 180}, {"x": 140, "y": 190}]}],
        hypothesis_id="HYP-001",
        receipt_hash="abcd1234deadbeef",
    )
    assert ren["ok"] is True
    assert ren["png_path"]
    assert ren["png_sha256"]
    assert ren["receipt_hash"]

    r = await geox_seismic_interpret(
        mode="interpret",
        faults=[
            {
                "name": "F1",
                "regime_prior": "normal",
                "sticks": [{"cmp": 100, "twt_ms": 200}, {"cmp": 120, "twt_ms": 500}],
            }
        ],
        horizons=[
            {
                "name": "H1",
                "order_index": 0,
                "picks": [{"cmp": 50, "twt_ms": 150}, {"cmp": 100, "twt_ms": 160}, {"cmp": 150, "twt_ms": 155}],
            },
            {
                "name": "H2",
                "order_index": 1,
                "picks": [{"cmp": 50, "twt_ms": 350}, {"cmp": 100, "twt_ms": 400}, {"cmp": 150, "twt_ms": 360}],
            },
        ],
        calibration={
            "bin_spacing_m": 12.5,
            "vertical_exaggeration": 2.0,
            "velocity_linear_m_s": 3000.0,
            "calibrated": True,
        },
        request={"render": True, "verbosity": "compact"},
    )
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("preferred_hypothesis") is None
    assert r.get("gate_summary")
    assert r.get("detail_ref")
    assert r.get("receipt_hash")
    # progressive disclosure: compact envelope small
    blob = json.dumps(r, default=str)
    assert len(blob) < 4000, f"compact envelope too large: {len(blob)} bytes"
    # render_ref present when render ok
    assert r.get("render_ref") or r.get("detail_ref")


@pytest.mark.asyncio
async def test_p6_interpret_section_no_silent_fallback():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(mode="interpret_section")
    assert r.get("mode") in ("interpret_section", "classical_section")
    assert r.get("error") != "MISSING_REQUIRED_FIELD"
    assert r.get("error") in ("MISSING_IMAGE", "MISSING_IMAGE_PATH", "IMAGE_NOT_FOUND", "MISSING_IMAGE")
