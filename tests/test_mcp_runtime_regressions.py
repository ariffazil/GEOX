from geox.geox_mcp.fastmcp_server import (
    arifos_compute_risk,
    geox_list_skills,
    geox_map_get_context_summary,
    geox_well_compute_petrophysics,
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
        u_ambiguity=0.2,
        transform_stack=[{"kind": "ai_segmentation"}, {"transform": "clahe"}],
        bias_scenario="ai_vision_only",
        evidence_credit=0.5,
    )
    assert "ac_risk" in result
    assert result["verdict"] in {"SEAL", "QUALIFY", "HOLD", "VOID"}
    assert "d_transform_effective" in result["components"]
    assert "evidence_credit" in result["components"]


def test_geox_well_compute_petrophysics_returns_depth_curves():
    result = geox_well_compute_petrophysics("BEK-2", "BEK_VOL")
    assert "curves" in result
    assert len(result["curves"]) > 0
    assert "curve_manifest" in result
    assert "summary" in result
    assert "net_pay_intervals" in result["summary"]
    hc_curves = [c for c in result["curves"] if 2090 <= c["depth_md"] <= 2170]
    assert all(c["net_pay"] for c in hc_curves), "HC zone should be net pay"
    water_curves = [c for c in result["curves"] if c["depth_md"] > 2175]
    assert not any(c["net_pay"] for c in water_curves), "Water zone should not be net pay"


def test_geox_well_load_bundle_returns_curve_manifest():
    result = geox_well_load_bundle("BEK-2")
    assert "curve_manifest" in result
    mnemonics = [c["mnemonic"] for c in result["curve_manifest"]]
    assert "GR" in mnemonics
    assert "RT" in mnemonics
    assert "RHOB" in mnemonics
    assert "NPHI" in mnemonics
