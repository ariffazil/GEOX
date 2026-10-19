#!/usr/bin/env python3
"""
run_evidence_chain.py — Execute the canonical Kinabalu Moho evidence chain.
"""

import json
import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, "/root/GEOX/src")
from geox_core.evidence_chain import EvidenceChainEngine

def run():
    obs = {
        "observation_id": "OBS-SABAH-RF-001",
        "kind": "receiver_function_moho_depth",
        "source": {
            "citation": "Sidek et al. (2016) Crustal thickness beneath North Borneo from receiver function analysis. Bull. Geol. Soc. Malaysia 62, 55-63; Madon et al. (2025) Gravity and crustal structure of Sabah.",
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
            "uncertainty_plus_minus": 2.5,
            "confidence_interval": 0.95
        },
        "temporal": {
            "age_ma": 0.0
        },
        "observed_at_utc": "2016-10-01T00:00:00Z"
    }

    evidence_obj = {
        "evidence_id": "GEOX-EV-000001",
        "observation_ref": "OBS-SABAH-RF-001",
        "epistemic_tier": "L0_MEASURED",
        "processing_lineage": {
            "method": "P-to-S receiver function H-kappa stacking (Zhu & Kanamori 2000)",
            "software_version": "CPS330 / geox_rf_v1",
            "operator_or_author": "Sidek et al.",
            "parameters": {
                "vp_vs_ratio": 1.73,
                "gaussian_filter_a": 2.5
            }
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
            "mantle_density_kg_m3": 3300.0,
            "sediment_density_kg_m3": 2400.0
        },
        "predictions": [
            {
                "prediction_id": "PRED-A-MOHO-CROCKER",
                "target_observable": "receiver_function_moho_depth",
                "expected_window": {
                    "min_value": 30.0,
                    "max_value": 35.0,
                    "units": "km"
                },
                "location_chainage_km": 520.0,
                "kill_condition": "Moho < 28 km or Moho > 38 km without positive gravity anomaly"
            }
        ],
        "kill_criteria": [
            "Moho > 40 km under Crocker axis without mantle downwelling signature",
            "Absence of flexural forebulge in Dangerous Grounds outer-rise"
        ]
    }

    model_d = {
        "model_id": "MODEL-D-DRIP",
        "model_name": "Post-Subduction Lithospheric Drip",
        "family": "mantle_delamination",
        "geometry_hash": "d4408e91f00a34c7b28911cde",
        "assumptions": {
            "reference_crust_thickness_t0_km": 30.0,
            "crust_density_kg_m3": 2800.0,
            "mantle_density_kg_m3": 3300.0,
            "sediment_density_kg_m3": 2400.0
        },
        "predictions": [
            {
                "prediction_id": "PRED-D-MOHO-CROCKER",
                "target_observable": "receiver_function_moho_depth",
                "expected_window": {
                    "min_value": 42.0,
                    "max_value": 55.0,
                    "units": "km"
                },
                "location_chainage_km": 520.0,
                "kill_condition": "Moho <= 35.0 km under Crocker axis kills localized lithospheric drip hypothesis"
            }
        ],
        "kill_criteria": [
            "Moho <= 35 km under Crocker axis (provenance: Cottam 2010 / Sidek 2016)",
            "Lack of anomalous high-velocity mantle blob in upper 150 km tomographic slice"
        ]
    }

    result = EvidenceChainEngine.execute_two_model_discrimination(
        evidence_obj=evidence_obj,
        obs=obs,
        model_a=model_a,
        model_b=model_d
    )

    full_payload = {
        "observation": obs,
        "evidence_object": evidence_obj,
        "model_a": model_a,
        "model_d": model_d,
        "discrimination_run": result
    }

    # Save destinations
    destinations = [
        Path("/root/GEOX/data/evidence/kinabalu_moho_chain.json"),
        Path("/opt/geox/data/evidence/kinabalu_moho_chain.json"),
        Path("/var/www/html/earth/sabah-observatory/evidence_chain.json")
    ]

    for p in destinations:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(full_payload, indent=2))
        print(f"Wrote evidence chain payload to {p}")

    print("\n=== EVIDENCE CHAIN RESULT ===")
    print(f"Evidence ID: {result['evidence_id']}")
    print(f"Artifact Identity: {result['artifact_identity']}")
    print(f"Model A Verdict: {result['decision_test']['test_results']['MODEL-A-UNDERTHRUST']['verdict']}")
    print(f"Model D Verdict: {result['decision_test']['test_results']['MODEL-D-DRIP']['verdict']}")
    print(f"Kill Triggered on Model D: {result['decision_test']['test_results']['MODEL-D-DRIP']['kill_triggered']}")
    print(f"Supports: {result['scientific_warrant']['supports_models']}")
    print(f"Weakens: {result['scientific_warrant']['weakens_models']}")

if __name__ == "__main__":
    run()
