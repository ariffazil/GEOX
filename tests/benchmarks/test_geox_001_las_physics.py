"""LAS physics + volumetric MC — F2 curve math, not table citations."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from geox_core.benchmarks.geox_001_las_physics import compute_las_physics
from geox_core.benchmarks.geox_001_well_seismic_truth import run_geox_001_real_las
from geox_core.wealth.volumetric_mc import emv_from_stoiip_mc, stoiip_monte_carlo


def test_compute_las_physics_from_synthetic_curves():
    n = 100
    depth = np.linspace(2000, 2100, n)
    curves = {
        "DEPT": depth,
        "DT": np.full(n, 90.0),  # us/ft
        "RHOB": np.full(n, 2.30),
        "GR": np.full(n, 50.0),
        "NPHI": np.full(n, 0.22),
        "RT": np.full(n, 20.0),
    }
    r = compute_las_physics(curves)
    assert r["epistemic"]["porosity"] == "DER"
    assert r["stats"]["phi_e"]["p50"] is not None
    assert 0.05 < r["stats"]["phi_e"]["p50"] < 0.35
    assert len(r["series"]["ai"]) == n
    assert len(r["series"]["rc"]) == n - 1


def test_stoiip_mc_p10_gt_p50_gt_p90():
    mc = stoiip_monte_carlo(
        area_km2_p10=30,
        area_km2_p50=20,
        area_km2_p90=12,
        h_m_p10=40,
        h_m_p50=25,
        h_m_p90=15,
        ntg_p10=0.7,
        ntg_p50=0.5,
        ntg_p90=0.3,
        phi_p10=0.22,
        phi_p50=0.18,
        phi_p90=0.12,
        n_sims=2000,
        seed=1,
    )
    s = mc["stoiip_mmstb"]
    assert s["p10"] >= s["p50"] >= s["p90"]
    emv = emv_from_stoiip_mc(mc, pos=0.35, dry_hole_cost_usd_mm=40)
    assert "emv_usd_mm" in emv
    assert emv["recoverable_mmstb"]["p50"] > 0


@pytest.mark.skipif(
    not Path("/root/geox/data/real_wells/q15_15_9_19/q15_15_9_19.las").exists(),
    reason="Q15 LAS not staged",
)
def test_real_las_path_includes_las_physics():
    r = run_geox_001_real_las(scenario="mistie_hold")
    assert r["real_las"]["status"] == "INGESTED"
    assert "las_physics" in r
    assert r["las_physics"]["epistemic"]["porosity"] == "DER"
    assert r["las_physics"]["stats"]["phi_e"]["p50"] is not None
