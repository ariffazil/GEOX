"""P1 Marmousi MC STOIIP — volumes from LAS-derived φ/NTG."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from geox_core.benchmarks.geox_001_las_physics import compute_las_physics
from geox_core.wealth.volumetric_mc import emv_from_stoiip_mc, stoiip_monte_carlo

LAS = Path("/root/geox/data/marmousi-well-x1500.las")


def _curves_from_marmousi(path: Path) -> dict:
    lines = path.read_text().splitlines()
    in_a = False
    depth, vp, rhob = [], [], []
    for line in lines:
        if line.startswith("~A"):
            in_a = True
            continue
        if not in_a or not line.strip():
            continue
        p = line.split()
        if len(p) < 4:
            continue
        d, v, _s, r = map(float, p[:4])
        if v > 0:
            depth.append(d)
            vp.append(v)
            rhob.append(r)
    d_a = np.asarray(depth)
    v_a = np.asarray(vp)
    r_a = np.asarray(rhob)
    dt = 304800.0 / np.clip(v_a, 100.0, 8000.0)
    return {"DEPT": d_a, "DT": dt, "RHOB": r_a}


@pytest.mark.skipif(not LAS.exists(), reason="Marmousi LAS missing")
def test_marmousi_phi_feeds_stoiip_mc():
    phys = compute_las_physics(_curves_from_marmousi(LAS), dt_unit="usft")
    pe = phys["stats"]["phi_e"]
    ntg = float(phys["stats"]["net_to_gross"])
    assert pe["p50"] is not None and pe["p50"] > 0.05
    assert 0.0 < ntg <= 1.0

    phi = float(pe["p50"])
    mc = stoiip_monte_carlo(
        area_km2_p10=12,
        area_km2_p50=8,
        area_km2_p90=5,
        h_m_p10=80,
        h_m_p50=50,
        h_m_p90=30,
        ntg_p10=min(0.99, ntg * 1.05),
        ntg_p50=ntg,
        ntg_p90=max(0.05, ntg * 0.85),
        phi_p10=min(0.4, phi * 1.1),
        phi_p50=phi,
        phi_p90=max(0.02, phi * 0.85),
        n_sims=2000,
        seed=7,
    )
    s = mc["stoiip_mmstb"]
    assert s["p10"] >= s["p50"] >= s["p90"]
    emv = emv_from_stoiip_mc(mc, pos=0.3)
    assert "emv_usd_mm" in emv
    assert emv["epistemic"].startswith("DER")
