from geox.geox_mcp.fastmcp_server import (
    arifos_compute_risk,
    geox_list_skills,
    geox_map_get_context_summary,
    geox_well_load_bundle,
)


def test_geox_list_skills_returns_registry_entries():
    result = geox_list_skills()
    assert result["count"] > 0
    assert result["skills"]


def test_geox_map_context_summary_is_not_empty():
    result = geox_map_get_context_summary(
        {"xmin": 0, "ymin": 0, "xmax": 10, "ymax": 5}
    )
    assert result["summary"]["area"] == 50
    assert result["summary"]["spatial_context"]


def test_geox_well_load_bundle_rejects_unknown_well():
    result = geox_well_load_bundle("FAKE-WELL-999")
    assert result["status"] == "not_found"
    assert result["claim_tag"] == "VOID"


def test_arifos_compute_risk_accepts_structured_transform_stack():
    result = arifos_compute_risk(
        u_phys=0.2,
        transform_stack=[{"kind": "ai_segmentation"}, {"transform": "clahe"}],
        bias_scenario="ai_vision_only",
    )
    assert "ac_risk" in result
    assert result["verdict"] in {"SEAL", "QUALIFY", "HOLD", "VOID"}
