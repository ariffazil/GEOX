import pytest
from geox_mcp.tools.prospect_unified import geox_prospect

@pytest.mark.asyncio
async def test_prospect_falsify_normal():
    # Normal prospect without contradictions
    res = await geox_prospect(
        prospect_ref="Kinabalu_West_Play",
        mode="falsify",
        evidence_refs=["seismic_section_01"]
    )
    assert res["falsified"] is False
    assert res["apex_score"]["G"] == 0.85
    assert not res["results"]["contradictions"]

@pytest.mark.asyncio
async def test_prospect_falsify_invalid_name():
    # Falsified due to invalid naming indicator
    res = await geox_prospect(
        prospect_ref="Prospect_Leak_02",
        mode="falsify"
    )
    assert res["falsified"] is True
    assert res["apex_score"]["G"] == 0.50
    assert any("leak" in c.lower() for c in res["results"]["contradictions"])

@pytest.mark.asyncio
async def test_prospect_falsify_physical_contradiction():
    # Falsified due to column height exceeding seal capacity
    res = await geox_prospect(
        prospect_ref="Prospect_Alpha",
        mode="falsify",
        structural_map_inline={
            "estimated_column_height_m": 150,
            "seal_thickness_m": 50
        }
    )
    assert res["falsified"] is True
    assert res["apex_score"]["G"] == 0.50
    assert any("exceeds" in c.lower() for c in res["results"]["contradictions"])
