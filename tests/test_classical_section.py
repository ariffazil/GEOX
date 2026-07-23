"""
Classical image-first section propose baseline.
F13 product path: PNG/JPG section → CANDIDATE_GEOMETRY → gates.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import os

import pytest

_TEST_IMAGE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "geox", "seismic", "rsi", "seismic_greyscale.jpg")
)
_ALT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "geox", "seismic", "rsi", "seismic_section.jpg")
)


def _img() -> str | None:
    if os.path.exists(_TEST_IMAGE):
        return _TEST_IMAGE
    if os.path.exists(_ALT):
        return _ALT
    return None


@pytest.mark.asyncio
async def test_classical_section_proposes_geometry():
    from geox_mcp.tools.classical_section_propose import geox_classical_section_propose

    path = _img()
    if not path:
        pytest.skip("demo section image missing")
    r = await geox_classical_section_propose(
        image_path=path,
        max_faults=5,
        max_horizons=4,
        fault_min_length=20,
        run_gates=False,
    )
    assert r.get("ok") is True
    assert r.get("input_class") == "image_only"
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("seal_eligibility") is False
    assert r.get("preferred_hypothesis") is None
    assert "classical" in (r.get("algorithm") or {}).get("name", "")
    # At least some geometry or honest empty
    assert "faults" in r and "horizons" in r
    assert r.get("framework")
    assert r["framework"]["measurement_context"]["input_class"] == "image_only"
    # Never SEAL
    assert r.get("governance_status") != "SEAL"


@pytest.mark.asyncio
async def test_classical_via_seismic_interpret_mode():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    path = _img()
    if not path:
        pytest.skip("demo section image missing")
    r = await geox_seismic_interpret(
        mode="classical_section",
        image_path=path,
        emit_bundle=False,
        max_faults=5,
        max_horizons=4,
    )
    assert r.get("mode") == "classical_section"
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("preferred_hypothesis") is None
    # Bundle or framework present
    assert r.get("interpretation_bundle") or r.get("framework") or r.get("faults") is not None


@pytest.mark.asyncio
async def test_interpret_section_aliases_classical():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    path = _img()
    if not path:
        pytest.skip("demo section image missing")
    r = await geox_seismic_interpret(mode="interpret_section", image_path=path, emit_bundle=False)
    # Routed to classical product path
    assert r.get("mode") == "classical_section"
    assert r.get("ok") is True
    assert r.get("input_class") == "image_only"


@pytest.mark.asyncio
async def test_interpret_image_uses_classical_then_gates():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    path = _img()
    if not path:
        pytest.skip("demo section image missing")
    r = await geox_seismic_interpret(
        mode="interpret",
        image_path=path,
        max_faults=4,
        max_horizons=3,
        emit_bundle=True,
    )
    assert r.get("mode") == "interpret"
    assert r.get("preferred_hypothesis") is None
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    # propose method classical
    prop = r.get("propose") or {}
    if prop.get("ran"):
        assert prop.get("method") == "classical_section"
    hyps = r.get("hypotheses") or (r.get("interpretation_bundle") or {}).get("hypotheses")
    if hyps:
        assert len(hyps) >= 3


@pytest.mark.asyncio
async def test_classical_no_guess_true_dip_without_ve():
    """Image dips stay image domain; gates UNMEASURED for true dip without calib."""
    from geox_mcp.tools.classical_section_propose import geox_classical_section_propose
    from geox_mcp.tools.structure_validate import geox_structure_validate

    path = _img()
    if not path:
        pytest.skip("demo section image missing")
    r = await geox_classical_section_propose(
        image_path=path, max_faults=4, max_horizons=3, fault_min_length=20, run_gates=False
    )
    fw = r.get("framework") or {}
    if not fw.get("faults"):
        pytest.skip("no faults extracted on this image")
    # Ensure no subsurface dip invented
    for f in fw["faults"]:
        assert f.get("dip_deg_subsurface") is None
        assert f.get("domain") == "pixel"
    sv = await geox_structure_validate(framework=fw, emit_bundle=False)
    # K-DIP should be UNMEASURED (image dip, no VE) not fake PASS
    assert sv["gates"]["K-DIP"]["status"] in ("UNMEASURED", "PASS", "WARN", "KILL")
    # If any fault only has image dip without VE → UNMEASURED expected
    if all(f.get("dip_deg_image") and not f.get("dip_deg_subsurface") for f in fw["faults"]):
        assert sv["gates"]["K-DIP"]["status"] == "UNMEASURED"
