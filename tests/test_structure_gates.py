"""
Phase C structure gates — K-DIP / K-THROW kill suite + falsify wire.
Sovereign blueprint 2026-07-23. DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_kill_reverse_75_tip_growth():
    """Impossible reverse@75° + throw increasing at tip → ≥1 KILL."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    framework = {
        "faults": [
            {
                "fault_id": "F_bad",
                "regime_prior": "reverse",
                "dip_deg_image": 75.0,
                "throw_profile": [
                    {"station": 0, "throw": 10},
                    {"station": 1, "throw": 20},
                    {"station": 2, "throw": 50},  # tip growth
                ],
            }
        ],
        "measurement_context": {"input_class": "image_only"},
    }
    r = await geox_structure_validate(framework=framework)
    assert r["ok"] is True
    assert "K-DIP" in r["kills"] or r["gates"]["K-DIP"]["verdict"] == "KILL"
    assert "K-THROW" in r["kills"] or r["gates"]["K-THROW"]["verdict"] == "KILL"
    assert r["combined_gate_verdict"] == "KILL"
    assert r["overall_verdict"] == "FALSIFIED"
    assert r["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert r["seal_authority"] == "arifOS_only"
    assert r.get("governance_status") != "SEAL"


@pytest.mark.asyncio
async def test_pass_clean_normal_taper():
    """Clean Andersonian normal + tip taper → K-DIP/K-THROW not double INCONCLUSIVE."""
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
    r = await geox_structure_validate(framework=framework)
    assert r["ok"] is True
    assert r["gates"]["K-DIP"]["verdict"] == "PASS"
    assert r["gates"]["K-THROW"]["verdict"] == "PASS"
    # Must not be double INCONCLUSIVE on the two hard gates we care about
    assert r["gates"]["K-DIP"]["verdict"] != "INCONCLUSIVE"
    assert r["gates"]["K-THROW"]["verdict"] != "INCONCLUSIVE"
    assert "K-DIP" not in r["kills"]
    assert "K-THROW" not in r["kills"]
    assert r["local_verdict"] == "QUALIFIED_CANDIDATE"


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
        }
    )
    assert r["gates"]["G2"]["verdict"] == "KILL"


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
        }
    )
    assert r["gates"]["K-GROWTH"]["verdict"] == "KILL"
    assert r["gates"]["K-RESTORE"]["verdict"] == "KILL"


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
                    "dip_deg_image": 75.0,
                    "throw_profile": [10, 20, 60],
                }
            ]
        },
    )
    assert r["execution_status"] == "SUCCESS"
    assert r["verdict"] == "FALSIFIED"
    assert r["filters_failed"] >= 1
    assert r["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert "structure_validate" in r


@pytest.mark.asyncio
async def test_interpret_mode_structure_validate():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(
        mode="structure_validate",
        framework={
            "faults": [
                {
                    "fault_id": "F1",
                    "regime_prior": "normal",
                    "dip_deg_image": 60.0,
                    "tip_taper": "ok",
                    "throw_profile": [5, 40, 6],
                }
            ]
        },
    )
    assert r.get("mode") == "structure_validate"
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("gates", {}).get("K-DIP", {}).get("verdict") == "PASS"

@pytest.mark.asyncio
async def test_k_dip_ve_correction_kills_apparent_normal():
    """Apparent steep dip under high VE may be shallow true reverse — and vice versa.
    High VE makes apparent dips look steeper: true = atan(tan(app)/VE).
    60° apparent at VE=3 → true ~26.6° → fails normal prior → KILL without reactivation.
    """
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
        }
    )
    assert r["gates"]["K-DIP"]["verdict"] == "KILL"
    finding = r["gates"]["K-DIP"]["findings"][0]
    assert finding.get("dip_meta", {}).get("ve_corrected") is True
    assert finding["dip_deg"] < 40  # true dip collapsed under VE=3
