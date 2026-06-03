from geox_core.skills.subsurface.reservoir_dynamics import (
    compute_mobility_index,
    probabilistic_hcpv_lite,
    estimate_permeability_from_phi,
)
from geox_core.skills.subsurface.volumes.volumetrics import geox_compute_volume_probabilistic_tool
from geox_core.skills.subsurface.sensitivity_tool import geox_run_sensitivity_sweep_tool
from geox_core.skills.subsurface.petro.petro_ensemble import geox_compute_sw_ensemble_tool


def test_reservoir_dynamics_functions():
    # compute_mobility_index
    assert compute_mobility_index(100.0, 2.0, 10.0) == 500.0
    assert compute_mobility_index(100.0, 0.0, 10.0) == 0.0
    assert compute_mobility_index(100.0, -1.0, 10.0) == 0.0

    # probabilistic_hcpv_lite
    res = probabilistic_hcpv_lite(1000.0, 10.0, 0.6, 0.2, 0.3, 1.1)
    assert res > 0.0
    assert probabilistic_hcpv_lite(1000.0, 10.0, 0.6, 0.2, 0.3, 0.0) > 0.0

    # estimate_permeability_from_phi
    assert estimate_permeability_from_phi(0.0) == 0.0
    assert estimate_permeability_from_phi(-0.1) == 0.0
    assert estimate_permeability_from_phi(0.2, "sand") == 10 ** (3 * 0.2 + 1)
    assert estimate_permeability_from_phi(0.2, "clay") == 10 ** (2 * 0.2 - 1)


def test_volumetrics_wrapper():
    res = geox_compute_volume_probabilistic_tool(
        grv_dist={"min": 100.0, "ml": 120.0, "max": 150.0},
        ntg_dist={"min": 0.45, "ml": 0.60, "max": 0.72},
        phi_dist={"min": 0.18, "ml": 0.22, "max": 0.28},
        sw_dist={"min": 0.20, "ml": 0.30, "max": 0.42},
        fvf_dist={"min": 1.05, "ml": 1.10, "max": 1.18},
        draws=100,
    )
    assert "p50" in res


def test_sensitivity_wrapper():
    inputs = {
        "u_ambiguity": 0.35,
        "evidence_credit": 0.75,
        "echo_score": 0.10,
        "truth_score": 0.99,
        "amanah_locked": False,
        "irreversible_action": False,
        "transform_stack": ["normalize", "ac_risk"],
    }
    res = geox_run_sensitivity_sweep_tool(inputs, percent_delta=0.1)
    assert "cases" in res


def test_petro_ensemble_wrapper():
    res = geox_compute_sw_ensemble_tool(rt=25.0, phi=0.22, rw=0.08, vsh=0.12, temp=95.0)
    assert "p50" in res
