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
    result = geox_map_get_context_summary({"xmin": 0, "ymin": 0, "xmax": 10, "ymax": 5})
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


# ── L1: geox_map_get_context_summary bounds handling ────────────────────────


def test_geox_map_context_none_bounds_returns_error():
    """L1: None bounds must return error, not crash with AttributeError."""
    result = geox_map_get_context_summary(None)
    assert result["summary"]["claim_tag"] == "UNKNOWN"
    assert result["summary"]["error"] in ("bounds_required", "bounds_must_be_dict")
    assert result["summary"]["area"] == 0.0


def test_geox_map_context_norwegian_shelf_has_positive_area():
    """L1: Norwegian shelf bounds (59-62N, 2-5E) must compute positive area."""
    result = geox_map_get_context_summary({"xmin": 2, "ymin": 59, "xmax": 5, "ymax": 62})
    assert result["summary"]["area"] > 0
    assert result["summary"].get("area_unit") == "degrees_squared"
    assert result["summary"]["spatial_context"] == "bbox[2.0,59.0,5.0,62.0]"


def test_geox_map_context_has_width_and_height():
    """L1: Response should include width_deg and height_deg for transparency."""
    result = geox_map_get_context_summary({"xmin": 0, "ymin": 0, "xmax": 10, "ymax": 5})
    s = result["summary"]
    assert "width_deg" in s
    assert "height_deg" in s
    assert s["width_deg"] * s["height_deg"] == s["area"]


# ── M6: geox_well_compute_petrophysics null-handling ──────────────────────────


def test_geox_well_petrophysics_has_rhob_null_in_curves():
    """M6: Every curve must have explicit rhob=None (nullable RHOB curve)."""
    result = geox_well_compute_petrophysics("BEK-2", "BEK_VOL")
    assert all(c.get("rhob") is None for c in result["curves"]), "RHOB must be null-safe"


def test_geox_well_petrophysics_curve_manifest_has_nullable_rhob():
    """M6: curve_manifest must declare RHOB as nullable."""
    result = geox_well_compute_petrophysics("BEK-2", "BEK_VOL")
    rhob_entry = next((c for c in result["curve_manifest"] if c["mnemonic"] == "RHOB"), None)
    assert rhob_entry is not None, "RHOB must be in curve_manifest"
    assert rhob_entry.get("nullable") is True


def test_geox_well_petrophysics_has_data_origin():
    """M6: result must carry data_origin field (OBSERVED or SYNTHETIC_FIXTURE)."""
    result = geox_well_compute_petrophysics("BEK-2", "BEK_VOL")
    assert "data_origin" in result
    assert result["data_origin"] in ("OBSERVED", "SYNTHETIC_FIXTURE")


# ── L2: uncertainty propagation via p10_p90_spread ──────────────────────────
# (Tested via integrated call; unit via test_npd_eia_structured_errors)
