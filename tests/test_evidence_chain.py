"""
test_evidence_chain.py — CI Verification for Evidence-to-Decision Chain.

Tests the five mandatory constitutional rejection criteria:
1. Rejects comparison if model geometry hashes are identical.
2. Rejects observation if datum, CRS, or uncertainty is absent.
3. Successfully discriminates Model A (PASS) vs Model D (KILL).
4. Enforces separation between Artifact Identity, Execution Witness, and Scientific Warrant.
"""

import copy
import pytest
from geox_core.evidence_chain import EvidenceChainEngine


@pytest.fixture
def base_fixtures():
    obs = {
        "observation_id": "OBS-SABAH-RF-001",
        "kind": "receiver_function_moho_depth",
        "source": {
            "citation": "Sidek et al. (2016)",
            "doi": "10.7186/bgsm62201607",
            "file_hash": "4a7d0e9c8f2b1a3e5d7c9f0b2a4e6d8c0b2a4e6d8c0b2a4e6d8c0b2a4e6d8c0b",
            "access_classification": "public"
        },
        "spatial": {
            "crs": "EPSG:4326",
            "latitude": 5.98,
            "longitude": 116.07,
            "station_name": "KMY_BROADBAND"
        },
        "vertical_datum": "sea_level",
        "measurement": {
            "value": 32.8,
            "units": "km",
            "uncertainty_plus_minus": 2.5
        },
        "observed_at_utc": "2016-10-01T00:00:00Z"
    }

    evidence_obj = {
        "evidence_id": "GEOX-EV-000001",
        "observation_ref": "OBS-SABAH-RF-001",
        "epistemic_tier": "L0_MEASURED",
        "processing_lineage": {
            "method": "P-to-S receiver function H-kappa stacking",
            "software_version": "CPS330",
            "operator_or_author": "Sidek et al."
        },
        "warrant_state": "WARRANTED"
    }

    model_a = {
        "model_id": "MODEL-A-UNDERTHRUST",
        "model_name": "Underthrust Attenuated Continental Margin",
        "family": "underthrust_continent",
        "geometry_hash": "a1104e79b90c12e8d35687abf",
        "assumptions": {
            "reference_crust_thickness_t0_km": 30.0,
            "crust_density_kg_m3": 2800.0,
            "mantle_density_kg_m3": 3300.0
        },
        "predictions": [
            {
                "prediction_id": "PRED-A-MOHO-CROCKER",
                "target_observable": "receiver_function_moho_depth",
                "expected_window": { "min_value": 30.0, "max_value": 35.0, "units": "km" },
                "location_chainage_km": 520.0,
                "kill_condition": "Moho > 40 km"
            }
        ],
        "kill_criteria": ["Moho > 40 km under Crocker axis"]
    }

    model_d = {
        "model_id": "MODEL-D-DRIP",
        "model_name": "Post-Subduction Lithospheric Drip",
        "family": "mantle_delamination",
        "geometry_hash": "d4408e91f00a34c7b28911cde",
        "assumptions": {
            "reference_crust_thickness_t0_km": 30.0,
            "crust_density_kg_m3": 2800.0,
            "mantle_density_kg_m3": 3300.0
        },
        "predictions": [
            {
                "prediction_id": "PRED-D-MOHO-CROCKER",
                "target_observable": "receiver_function_moho_depth",
                "expected_window": { "min_value": 42.0, "max_value": 55.0, "units": "km" },
                "location_chainage_km": 520.0,
                "kill_condition": "Moho <= 35.0 km kills drip"
            }
        ],
        "kill_criteria": ["Moho <= 35 km under Crocker axis"]
    }

    return evidence_obj, obs, model_a, model_d


def test_successful_model_discrimination(base_fixtures):
    evidence_obj, obs, model_a, model_d = base_fixtures
    res = EvidenceChainEngine.execute_two_model_discrimination(evidence_obj, obs, model_a, model_d)

    assert res["status"] == "COMPLETED"
    assert res["evidence_id"] == "GEOX-EV-000001"
    assert res["decision_test"]["test_results"]["MODEL-A-UNDERTHRUST"]["verdict"] == "PASS"
    assert res["decision_test"]["test_results"]["MODEL-D-DRIP"]["verdict"] == "FAIL"
    assert res["decision_test"]["test_results"]["MODEL-D-DRIP"]["kill_triggered"] is True
    assert "MODEL-A-UNDERTHRUST" in res["scientific_warrant"]["supports_models"]
    assert "MODEL-D-DRIP" in res["scientific_warrant"]["weakens_models"]


def test_rejects_identical_geometry_hashes(base_fixtures):
    evidence_obj, obs, model_a, model_d = base_fixtures
    bad_model_d = copy.deepcopy(model_d)
    bad_model_d["geometry_hash"] = model_a["geometry_hash"]  # Artificial duplicate

    with pytest.raises(ValueError, match="share identical geometry hash"):
        EvidenceChainEngine.execute_two_model_discrimination(evidence_obj, obs, model_a, bad_model_d)


def test_rejects_missing_vertical_datum(base_fixtures):
    evidence_obj, obs, model_a, model_d = base_fixtures
    bad_obs = copy.deepcopy(obs)
    bad_obs["vertical_datum"] = None

    with pytest.raises(ValueError, match="lacks vertical_datum or CRS"):
        EvidenceChainEngine.execute_two_model_discrimination(evidence_obj, bad_obs, model_a, model_d)


def test_rejects_missing_crs(base_fixtures):
    evidence_obj, obs, model_a, model_d = base_fixtures
    bad_obs = copy.deepcopy(obs)
    bad_obs["spatial"]["crs"] = None

    with pytest.raises(ValueError, match="lacks vertical_datum or CRS"):
        EvidenceChainEngine.execute_two_model_discrimination(evidence_obj, bad_obs, model_a, model_d)


def test_rejects_missing_uncertainty(base_fixtures):
    evidence_obj, obs, model_a, model_d = base_fixtures
    bad_obs = copy.deepcopy(obs)
    bad_obs["measurement"]["uncertainty_plus_minus"] = None

    with pytest.raises(ValueError, match="lacks explicit uncertainty"):
        EvidenceChainEngine.execute_two_model_discrimination(evidence_obj, bad_obs, model_a, model_d)


def test_tri_witness_independence(base_fixtures):
    evidence_obj, obs, model_a, model_d = base_fixtures
    res = EvidenceChainEngine.execute_two_model_discrimination(evidence_obj, obs, model_a, model_d)

    # Verify tri-witness independence
    artifact_id = res["artifact_identity"]
    witness = res["execution_witness"]
    warrant = res["scientific_warrant"]

    assert len(artifact_id) == 64  # SHA-256
    assert witness["execution_status"] == "SUCCESS"
    assert witness["exit_code"] == 0
    assert warrant["warrant_id"].startswith("WARRANT-")
    assert warrant["epistemic_split"]["observed"]
    assert warrant["epistemic_split"]["contradicted"]
