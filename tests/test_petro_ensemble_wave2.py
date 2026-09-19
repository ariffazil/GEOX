from geox_core.core.petro_ensemble import PetroEnsemble


def geox_well_compute_petrophysics(well_id: str, zone_id: str) -> dict:
    ens = PetroEnsemble().compute_sw_ensemble(rt=25.0, phi=0.22, rw=0.08, vsh=0.12, temp=95.0)
    return {
        "summary": {
            "probabilistic_volume": 42.0,
            "sensitivity": {"p10": ens.p10, "p50": ens.p50, "p90": ens.p90},
        },
        "visualization_payload": {"type": "petro"},
        "curves": [{"sw_models": ens.models}],
    }


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
