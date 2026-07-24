"""F1 zen spine — attribute · track_horizon · measure_throw."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_f1_attribute_fixture_coherence():
    from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute

    r = await geox_seismic_compute(mode="attribute", attribute="coherence", provenance="fixture")
    assert r.get("ok") is True
    assert r.get("mode") == "attribute"
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("preferred_hypothesis") is None
    assert "summaries" in r
    assert "coherence" in r["summaries"] or r.get("primary")
    assert r.get("receipt_hash")


@pytest.mark.asyncio
async def test_f1_track_horizon_fixture():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(mode="track_horizon", provenance="fixture", max_horizons=5)
    assert r.get("ok") is True
    assert r.get("mode") == "track_horizon"
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("preferred_hypothesis") is None
    hyps = r.get("horizons") or []
    assert len(hyps) >= 1
    assert "pts" in hyps[0]
    assert hyps[0].get("label") == "INT_SEISMIC_HORIZON" or hyps[0].get("epistemic_class")


@pytest.mark.asyncio
async def test_f1_measure_throw_feeds_gates():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(
        mode="measure_throw",
        provenance="fixture",
        max_horizons=6,
        request={"run_gates": True},
    )
    assert r.get("ok") is True
    assert r.get("mode") == "measure_throw"
    faults = r.get("faults") or []
    assert len(faults) >= 1
    f0 = faults[0]
    assert "dmax_m" in f0 and "length_m" in f0 and "throw_profile_m" in f0
    assert f0["dmax_m"] >= 0
    assert f0["length_m"] > 0
    # gates ran
    sv = r.get("structure_validate") or {}
    assert "gates" in sv or r.get("gate_summary")
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("preferred_hypothesis") is None


@pytest.mark.asyncio
async def test_f1_image_path_track():
    from pathlib import Path
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    img = Path("/root/GEOX/geox/seismic/rsi/seismic_section.jpg")
    if not img.is_file():
        pytest.skip("no section image")
    r = await geox_seismic_interpret(
        mode="track_horizon",
        image_path=str(img),
        max_horizons=4,
        provenance="live_section",
    )
    assert r.get("ok") is True
    assert (r.get("horizons") or r.get("n_horizons", 0))
