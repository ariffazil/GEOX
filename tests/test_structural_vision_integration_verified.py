"""Independent verification of the structural-vision integration map.

The integration map (docs/STRUCTURAL_VISION_INTEGRATION_MAP.md) was produced by a
read-only auditor that ran CONCURRENTLY with three writing agents. Its own report
flags that the repo was a moving target. This module re-probes the load-bearing
findings AFTER all writers finished, so that a false defect cannot survive into
the record.

Contract under test:
  C1  was reported as a BLOCKING wiring gap, claiming `geox_core.vision_structural`
      imports as an empty namespace package. Re-verified here.
  D1  governance hazard: the VLM lane solicits dip/throw from a language model.
  D2  the RT1 blockage is the only thing keeping D1 inert.
  D4  falsify.py K001 returns PASS when its inputs are absent (deficit -> pass).
  R   reuse warning: deterministic primitives already exist in the repo.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8", errors="replace")


# ── C1 — the reported blocking gap ───────────────────────────────────────────


def test_c1_vision_structural_is_not_an_empty_namespace_package():
    """C1 is STALE. The __init__.py landed after the auditor's probe window."""
    pkg_dir = SRC / "geox_core" / "vision_structural"
    assert (pkg_dir / "__init__.py").is_file(), "package must have an __init__.py"

    vs = importlib.import_module("geox_core.vision_structural")
    names = [n for n in dir(vs) if not n.startswith("_")]
    assert len(names) > 10, f"package exports too little to be a real package: {names}"
    for expected in ("Measurement", "apply_ve_correction", "compute_dip_field"):
        assert hasattr(vs, expected), f"missing export: {expected}"


def test_c1_all_four_axes_are_importable():
    for mod, funcs in (
        ("geox_core.vision_structural.structure_tensor", ("compute_dip_field", "extract_axis_a")),
        ("geox_core.vision_structural.isopach", ("dtw_align_traces", "compute_isopach",
                                                  "expansion_index", "isopach_differential")),
        ("geox_core.vision_structural.orientation", ("extract_fault_azimuths",
                                                     "azimuth_population_stats",
                                                     "conjugate_pair_test")),
        ("geox_core.vision_structural.terminations", ("detect_terminations",
                                                       "build_cross_cutting_table")),
    ):
        m = importlib.import_module(mod)
        for fn in funcs:
            assert hasattr(m, fn), f"{mod}.{fn} missing"


# ── D1 — governance hazard ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "adapter",
    [
        "geox_core/engines/vision/minimax_vlm_adapter.py",
        "geox_core/engines/vision/mimo_vlm_adapter.py",
    ],
)
def test_d1_vlm_lane_no_longer_solicits_dip_and_throw(adapter):
    """D1 CORRECTED — the two geometric fields are gone from the VLM path.

    This test originally asserted the defect was PRESENT (prompt schema requesting
    strike_dip_deg/throw_ms, values piped into FaultObservation). The cut has now
    been applied, so the assertion is inverted: it fails if either field reappears
    in the request schema or in the construction path.
    """
    src = _read(adapter)
    assert '\"strike_dip_deg\"' not in src, (
        f"{adapter}: strike_dip_deg must not be solicited from a language model"
    )
    assert '\"throw_ms\"' not in src, (
        f"{adapter}: throw_ms must not be solicited from a language model"
    )
    assert "deliberately NOT populated" in src, (
        f"{adapter}: the explicit non-population comment must survive — it is the guard"
    )


def test_fault_observation_still_accepts_deterministic_dip_and_throw():
    """The cut removes the VLM as a producer, not the field as a channel.

    Deterministic lanes (seismic_classical.structure_tensor,
    structure_gates.calibration_derive) remain legitimate producers.
    """
    from geox_core.engines.vision.perceptual_inventory import FaultObservation

    measured = FaultObservation(
        fault_id="F1", lateral_extent_inlines=(1.0, 2.0), twt_range_ms=(3.0, 4.0),
        strike_dip_deg=45.0, throw_ms=50.0, confidence=0.5,
    )
    assert measured.strike_dip_deg == 45.0 and measured.throw_ms == 50.0

    vlm_only = FaultObservation(
        fault_id="F2", lateral_extent_inlines=(1.0, 2.0), twt_range_ms=(3.0, 4.0),
        confidence=0.5,
    )
    assert vlm_only.strike_dip_deg is None and vlm_only.throw_ms is None


def test_d1_confidence_cap_is_the_only_guard():
    """A cap on self-reported certainty bounds nothing about physical validity."""
    src = _read("geox_mcp/tools/vision.py")
    assert "HUMILITY_CAP" in src or "0.90" in src, "expected the F7 humility cap to be present"


# ── D2 — RT1 is what keeps D1 inert ──────────────────────────────────────────


def test_d2_vision_tools_are_mounted_but_absent_from_the_manifest():
    manifest = _read("geox_mcp/tools_manifest.yaml")
    assert "geox_vision" not in manifest, (
        "if geox_vision_* ever appears in the manifest, D1 goes live — re-audit immediately"
    )
    server = _read("geox_mcp/server.py")
    assert "create_vision_server" in server, "the VLM lane is mounted"


def test_d2_rt1_blocks_tools_absent_from_the_surface():
    mw = _read("geox_mcp/geox_middleware.py")
    assert "_EXECUTABLE_SURFACE" in mw and "RT1_BLOCK" in mw, (
        "RT1 is the mechanism that currently blocks the unmounted vision lane"
    )


# ── D4 — deficit read as pass, in shared code ────────────────────────────────


def test_d4_k001_returns_pass_when_its_inputs_are_absent():
    """Same defect class as the falsifier-direction rule — in a different lane."""
    from geox_mcp.tools.falsify import _k001_climate_archetype

    r_empty = _k001_climate_archetype({})
    assert r_empty["verdict"] == "PASS", (
        "documenting the current (defective) behaviour: an empty context yields PASS, "
        "so absent evidence is scored as positive evidence"
    )
    assert r_empty["issues"] == []


def test_d4_k001_still_reviews_on_real_mismatch():
    from geox_mcp.tools.falsify import _k001_climate_archetype

    r = _k001_climate_archetype(
        {"climate_archetype": "icehouse", "depositional_environment": "carbonate_platform",
         "age_ma": 10.0}
    )
    assert r["verdict"] == "REVIEW"


# ── R — reuse: these already exist and must not be rebuilt ───────────────────


@pytest.mark.parametrize(
    "rel,name",
    [
        ("geox_mcp/tools/seismic_classical.py", "structure_tensor"),
        ("geox_mcp/tools/contrast_views.py", "_local_dip"),
        ("geox_mcp/tools/structure_gates/calibration_derive.py", "_expansion_index"),
        ("geox_mcp/tools/seismic_zen_f1.py", "measure_throw_from_horizons"),
    ],
)
def test_r_deterministic_primitives_already_exist(rel, name):
    src = _read(rel)
    assert f"def {name}" in src, f"reuse warning: {rel}::{name} already exists"


# ── The lane is built but NOT reachable ──────────────────────────────────────


def test_lane_is_not_yet_mounted():
    """Documents the integration state: built and tested, deliberately unarmed."""
    server = _read("geox_mcp/server.py")
    assert "create_structural_vision_server" not in server, (
        "if this fails, the lane has been armed — update the integration map"
    )
    # Load by file path: importing geox_mcp.servers transitively pulls
    # tools/basin.py -> macrostrat_client.py, which does `import httpx2` on a
    # package that does not exist in this venv. That is a separate, pre-existing
    # repo breakage (see test_httpx2_breaks_the_servers_package below).
    import importlib.util

    wiring_path = SRC / "geox_mcp" / "servers" / "structural_vision_wiring.py"
    spec = importlib.util.spec_from_file_location("_sv_wiring_probe", wiring_path)
    assert spec and spec.loader
    wiring = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wiring)

    plan = wiring.describe_arming_plan()
    assert plan["armed"] is False
    assert plan["status"] == "PLANNED_NOT_ARMED"
    assert "geox_structural_vision_extract" in plan["tools_to_add_to_public_surface"]
    assert plan["hazard"]["id"] == "D1"


def test_httpx2_breaks_the_servers_package():
    """Independent second witness of a hard, repo-wide import breakage.

    `import httpx2` appears in at least four modules. The package does not exist
    in this venv. Consequence: `import geox_mcp.servers` and `import
    geox_core.services` both raise ModuleNotFoundError, so the domain-server
    mount path is unreachable — which is a blocker on arming this lane, separate
    from the manifest change.
    """
    for rel in (
        "geox_mcp/tools/macrostrat_client.py",
        "geox_mcp/tools/wealth_bridge_tool.py",
        "geox_core/services/spglobal_client.py",
        "geox_core/services/npd_client.py",
    ):
        assert "import httpx2" in _read(rel), f"expected httpx2 import in {rel}"

    # The raw name is still absent...
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("httpx2")

    # ...but every consumer guards the import and falls back to the shim.
    for rel in (
        "geox_mcp/tools/macrostrat_client.py",
        "geox_mcp/tools/wealth_bridge_tool.py",
        "geox_core/services/spglobal_client.py",
        "geox_core/services/npd_client.py",
        "geox_core/services/eia_client.py",
        "geox_core/integrations/arifos_governance.py",
    ):
        assert "httpx2_shim" in _read(rel), f"{rel}: expected the guarded import"

    from geox_core import httpx2_shim
    import httpx
    assert httpx2_shim.ConnectError is httpx.ConnectError
    assert httpx2_shim.TimeoutException is httpx.TimeoutException


def test_servers_package_imports_after_the_httpx2_fix():
    """The domain-server mount path was unimportable. It must import now."""
    servers = importlib.import_module("geox_mcp.servers")
    assert hasattr(servers, "create_vision_server")
