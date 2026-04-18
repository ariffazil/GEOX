from geox.core.petro_ensemble import PetroEnsemble
from geox.geox_mcp.server import geox_well_compute_petrophysics


def test_petro_ensemble_returns_three_models():
    result = PetroEnsemble().compute_sw_ensemble(rt=25.0, phi=0.22, rw=0.08, vsh=0.12, temp=95.0)
    assert len(result.models) == 3
    assert result.p10 <= result.p50 <= result.p90
    assert result.claim_tag in {"CLAIM", "PLAUSIBLE", "ESTIMATE"}


def test_existing_petrophysics_tool_absorbs_ensemble():
    result = geox_well_compute_petrophysics("BEK-2", "BEK_VOL")
    assert "probabilistic_volume" in result["summary"]
    assert "sensitivity" in result["summary"]
    assert "visualization_payload" in result
    assert "sw_models" in result["curves"][0]
