"""
Phase C structure gates — UNMEASURED + receipts + multi-KILL pack.
B-final interpretation_bundle. DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_kill_reverse_75_tip_growth():
    """Impossible reverse@75° (true dip) + throw increasing at tip → ≥1 KILL."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    framework = {
        "faults": [
            {
                "fault_id": "F_bad",
                "regime_prior": "reverse",
                "dip_deg_subsurface": 75.0,  # true claim
                "throw_profile": [
                    {"station": 0, "throw": 10},
                    {"station": 1, "throw": 20},
                    {"station": 2, "throw": 50},
                ],
            }
        ],
        "measurement_context": {"input_class": "image_only", "calibrated": True},
    }
    r = await geox_structure_validate(framework=framework, emit_bundle=False)
    assert r["ok"] is True
    assert r["gates"]["K-DIP"]["status"] == "KILL"
    assert r["gates"]["K-THROW"]["status"] == "KILL"
    assert r["gates"]["K-DIP"].get("receipt_hash")
    assert r["gates"]["K-DIP"].get("equation")
    assert r["combined_gate_verdict"] == "KILL"
    assert r["overall_verdict"] == "FALSIFIED"
    assert r["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert r.get("governance_status") != "SEAL"


@pytest.mark.asyncio
async def test_unmeasured_image_dip_without_calibration():
    """Image dip without VE/calibration → K-DIP UNMEASURED (never guess true dip)."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        framework={
            "faults": [
                {
                    "fault_id": "F1",
                    "regime_prior": "normal",
                    "dip_deg_image": 60.0,
                }
            ]
        },
        emit_bundle=False,
    )
    assert r["gates"]["K-DIP"]["status"] == "UNMEASURED"
    assert "K-DIP" in r["unmeasured"] or r["gates"]["K-DIP"]["status"] == "UNMEASURED"
    assert r["gates"]["K-DIP"].get("receipt_hash")


@pytest.mark.asyncio
async def test_pass_clean_normal_taper():
    from geox_mcp.tools.structure_validate import geox_structure_validate

    framework = {
        "faults": [
            {
                "fault_id": "F_ok",
                "regime_prior": "normal",
                "dip_deg_subsurface": 62.0,
                "throw_profile": [
                    {"station": 0, "throw": 5},
                    {"station": 1, "throw": 45},
                    {"station": 2, "throw": 8},
                ],
                "tip_taper": "ok",
                "max_displacement": 45,
                "length": 1000,
            }
        ],
        "horizons": [
            {
                "horizon_id": "H1",
                "order_index": 0,
                "points": [{"x": 0, "y": 100}, {"x": 10, "y": 105}, {"x": 20, "y": 110}],
            },
            {
                "horizon_id": "H2",
                "order_index": 1,
                "points": [{"x": 0, "y": 200}, {"x": 10, "y": 205}, {"x": 20, "y": 210}],
            },
        ],
    }
    r = await geox_structure_validate(framework=framework, emit_bundle=False)
    assert r["ok"] is True
    assert r["gates"]["K-DIP"]["status"] == "PASS"
    assert r["gates"]["K-THROW"]["status"] == "PASS"
    assert "K-DIP" not in r["kills"]
    assert "K-THROW" not in r["kills"]


@pytest.mark.asyncio
async def test_topology_cross_kill():
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        framework={
            "horizons": [
                {
                    "horizon_id": "A",
                    "order_index": 0,
                    "points": [{"x": 0, "y": 0}, {"x": 10, "y": 10}],
                },
                {
                    "horizon_id": "B",
                    "order_index": 1,
                    "points": [{"x": 0, "y": 10}, {"x": 10, "y": 0}],
                },
            ]
        },
        emit_bundle=False,
    )
    assert r["gates"]["G2"]["status"] == "KILL"


@pytest.mark.asyncio
async def test_growth_kill_and_restore_stub():
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        framework={
            "faults": [{"fault_id": "F1", "regime_prior": "unknown"}],
            "growth_claimed": True,
            "expansion_index": 0.8,
            "restore_residual": 0.2,
            "restore_tolerance": 0.05,
        },
        emit_bundle=False,
    )
    assert r["gates"]["K-GROWTH"]["status"] == "KILL"
    assert r["gates"]["K-RESTORE"]["status"] == "KILL"


@pytest.mark.asyncio
async def test_impossible_multi_kill_pack():
    """Doctrine pack: 15° 'normal', D/L=0.5, no taper, polarity reverse → multi KILL."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        framework={
            "faults": [
                {
                    "fault_id": "F_imp",
                    "regime_prior": "normal",
                    "dip_deg_subsurface": 15.0,
                    "max_displacement": 500,
                    "length": 1000,  # D/L = 0.5
                    "throw_profile": [40, 40, 40],  # no taper
                }
            ],
            "throw_polarity_reversal": True,
            "relay_zone": False,
            "horizons": [
                {
                    "horizon_id": "H1",
                    "order_index": 0,
                    "points": [{"x": 0, "y": 0}, {"x": 10, "y": 10}],
                },
                {
                    "horizon_id": "H2",
                    "order_index": 1,
                    "points": [{"x": 0, "y": 10}, {"x": 10, "y": 0}],
                },
            ],
        },
        emit_bundle=False,
    )
    kills = set(r["kills"])
    assert "K-DIP" in kills
    assert "K-THROW" in kills
    assert "K-DL" in kills or r["gates"]["K-DL"]["status"] in ("KILL", "WARN")
    assert "G2" in kills or "K-XCUT" in kills
    assert len([k for k in kills if k in ("K-DIP", "K-THROW", "K-DL", "G2", "K-XCUT")]) >= 3
    assert r["combined_gate_verdict"] == "KILL"


@pytest.mark.asyncio
async def test_interpretation_bundle_multi_hypothesis():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(
        mode="structure_validate",
        framework={
            "faults": [
                {
                    "fault_id": "F1",
                    "regime_prior": "normal",
                    "dip_deg_subsurface": 60.0,
                    "tip_taper": "ok",
                    "throw_profile": [5, 40, 6],
                    "max_displacement": 40,
                    "length": 2000,
                }
            ]
        },
        emit_bundle=True,
        request={"hypothesis_count": 3},
    )
    assert r.get("preferred_hypothesis") is None
    bundle = r.get("interpretation_bundle") or r
    hyps = bundle.get("hypotheses") or r.get("hypotheses")
    assert hyps and len(hyps) >= 3
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("seal_authority") == "arifOS_only"


@pytest.mark.asyncio
async def test_falsify_structural_claim_type():
    from geox_mcp.tools.claim_unified import geox_falsify

    r = await geox_falsify(
        claim_text="Reverse fault at 75 deg with tip growth",
        claim_type="structural_fault",
        context={
            "faults": [
                {
                    "fault_id": "F1",
                    "regime_prior": "reverse",
                    "dip_deg_subsurface": 75.0,
                    "throw_profile": [10, 20, 60],
                }
            ]
        },
    )
    assert r["execution_status"] == "SUCCESS"
    assert r["verdict"] == "FALSIFIED"
    assert r["filters_failed"] >= 1
    assert r["local_verdict"] == "QUALIFIED_CANDIDATE"


@pytest.mark.asyncio
async def test_k_dip_ve_correction_kills_apparent_normal():
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        framework={
            "faults": [
                {
                    "fault_id": "F_ve",
                    "regime_prior": "normal",
                    "dip_deg_image": 60.0,
                }
            ],
            "measurement_context": {"geometry": {"vertical_exaggeration": 3.0}},
        },
        emit_bundle=False,
    )
    assert r["gates"]["K-DIP"]["status"] == "KILL"
    finding = r["gates"]["K-DIP"]["findings"][0]
    assert finding.get("dip_meta", {}).get("ve_corrected") is True
    assert finding["dip_deg"] < 40


@pytest.mark.asyncio
async def test_k_vel_unmeasured_without_velocity():
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        framework={"faults": [{"fault_id": "F1", "regime_prior": "unknown"}]},
        emit_bundle=False,
    )
    assert r["gates"]["K-VEL"]["status"] == "UNMEASURED"
