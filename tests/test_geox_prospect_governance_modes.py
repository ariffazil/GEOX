"""
tests/test_geox_prospect_governance_modes.py
Test Task 2 & Task 4:
Task 2: Authority & lane split for geox_prospect:
  - mode=screen (arithmetic, no state change) -> ANALYZE lane, OBSERVE_ONLY allowed.
  - mode=evaluate / appraise / develop -> requires OPERATOR (held on OBSERVE_ONLY).
  - verdict=seal -> requires seal authority (held on OBSERVE_ONLY).
  - output carries claim_tag="ASSUMPTION", forbidden_use="not a reserve or drilling recommendation".

Task 4: Inverse volumetrics mode:
  - Solves required area P10/P50/P90 for stated GIIP.
  - Sensitivity table across CO2 0-60%.
  - Plateau years at given rate.
  - Reference check within 2% of prompt specification:
    E P50 ≈ 347 scf/rcf, 5 Tcf -> ≈ 9.3 km² P50, 10 Tcf -> ≈ 18.6 km² P50.
"""

from unittest.mock import patch
import pytest
from geox_mcp.organ_governance import check_governance, _get_effective_lane
from geox_mcp.session_enforcement import ValidationResult
from geox_mcp.tools.prospect_unified import geox_prospect


@pytest.mark.asyncio
async def test_geox_prospect_governance_lane_split():
    """OBSERVE_ONLY session must be allowed to run screen, but blocked from evaluate/appraise/seal."""
    mock_auth = ValidationResult(
        ok=True,
        actor="test_agent",
        authority="OBSERVE_ONLY",
        session={"type": "session", "session_id": "SEAL-123456789012"},
    )
    with patch("geox_mcp.organ_governance.validate_session", return_value=mock_auth):
        # 1. mode=screen allowed for OBSERVE_ONLY
        verdict, err, _ = await check_governance(
            tool_name="geox_prospect",
            arguments={"mode": "screen", "verdict": "compute"},
            session_authority="OBSERVE_ONLY",
            actor_id="test_agent",
            session_id="SEAL-123456789012",
        )
        assert verdict == "TRANSPORT_OK", f"mode=screen should pass for OBSERVE_ONLY, got {verdict}: {err}"

        # 2. mode=inverse_volumetrics allowed for OBSERVE_ONLY
        verdict, err, _ = await check_governance(
            tool_name="geox_prospect",
            arguments={"mode": "inverse_volumetrics"},
            session_authority="OBSERVE_ONLY",
            actor_id="test_agent",
            session_id="SEAL-123456789012",
        )
        assert verdict == "TRANSPORT_OK", f"mode=inverse_volumetrics should pass for OBSERVE_ONLY, got {verdict}: {err}"

        # 3. mode=evaluate BLOCKED for OBSERVE_ONLY (requires OPERATOR)
        verdict, err, _ = await check_governance(
            tool_name="geox_prospect",
            arguments={"mode": "evaluate"},
            session_authority="OBSERVE_ONLY",
            actor_id="test_agent",
            session_id="SEAL-123456789012",
        )
        assert verdict == "HOLD", f"mode=evaluate must be blocked for OBSERVE_ONLY, got {verdict}"

        # 4. mode=appraise BLOCKED for OBSERVE_ONLY
        verdict, err, _ = await check_governance(
            tool_name="geox_prospect",
            arguments={"mode": "appraise"},
            session_authority="OBSERVE_ONLY",
            actor_id="test_agent",
            session_id="SEAL-123456789012",
        )
        assert verdict == "HOLD", f"mode=appraise must be blocked for OBSERVE_ONLY, got {verdict}"

        # 5. verdict=seal BLOCKED for OBSERVE_ONLY even in screen mode
        verdict, err, _ = await check_governance(
            tool_name="geox_prospect",
            arguments={"mode": "screen", "verdict": "seal"},
            session_authority="OBSERVE_ONLY",
            actor_id="test_agent",
            session_id="SEAL-123456789012",
        )
        assert verdict == "HOLD", f"verdict=seal must be blocked for OBSERVE_ONLY, got {verdict}"


@pytest.mark.asyncio
async def test_geox_prospect_screen_labels_and_forbidden_use():
    """mode=screen outputs must carry ASSUMPTION label and forbidden_use disclaimer."""
    res = await geox_prospect(
        prospect_ref="Lang-Lebah-1",
        mode="screen",
    )
    # Check top-level or primary artifact fields
    claim_tag = res.get("claim_tag") or res.get("epistemic_label")
    forbidden = res.get("forbidden_use") or res.get("primary_artifact", {}).get("forbidden_use", "")
    if not forbidden:
        forbidden = res.get("geox_advisory", {}).get("disclaimer", "")

    assert "ASSUMPTION" in str(claim_tag) or res.get("epistemic_label") == "ASSUMPTION"
    assert "not a reserve or drilling recommendation" in forbidden.lower() or "not authorize" in forbidden.lower()


@pytest.mark.asyncio
async def test_geox_prospect_inverse_volumetrics_reference_match():
    """Inverse volumetrics must match reference numbers within 2%."""
    # Reference check parameters:
    # P: 50-70 MPa, T: 140-170 C, z: 1.05-1.25, phi: 0.15-0.30, Sw: 0.15-0.35, net: 600m, geom: 0.3-0.6
    # Seed 42, 200k samples
    # Target: E P50 ≈ 347 scf/rcf, 5 Tcf -> ≈ 9.3 km² P50, 10 Tcf -> ≈ 18.6 km² P50
    res = await geox_prospect(
        prospect_ref="Lang-Lebah-Discovery",
        mode="screen",
        claimed_giip_tcf=[5.0, 10.0],
        net_pay_m=600.0,
        porosity_range=[0.15, 0.30],
        sw_range=[0.15, 0.35],
        pressure_mpa_range=[50.0, 70.0],
        temperature_c_range=[140.0, 170.0],
        z_range=[1.05, 1.25],
        geometry_factor_range=[0.3, 0.6],
        co2_fraction=0.18,
        recovery_factor=0.70,
        production_rate_bscfd=1.0,
        samples=200_000,
        seed=42,
    )

    art = res.get("primary_artifact") if "primary_artifact" in res else res
    assert art.get("sub_mode") == "inverse_volumetrics" or "required_effective_area_km2" in art

    # Check E P50 ≈ 347 (within 2%)
    e_p50 = art["expansion_factor_scf_per_rcf"]["p50"]
    assert abs(e_p50 - 347.0) / 347.0 < 0.02, f"E P50={e_p50} not within 2% of 347"

    # Check 5 Tcf P50 ≈ 9.3 km² (within 2%)
    area_5 = art["all_targets_area_km2"]["5.0_tcf"]["p50_km2"]
    assert abs(area_5 - 9.3) / 9.3 < 0.02, f"5 Tcf area P50={area_5} not within 2% of 9.3 km²"

    # Check 10 Tcf P50 ≈ 18.6 km² (within 2%)
    area_10 = art["all_targets_area_km2"]["10.0_tcf"]["p50_km2"]
    assert abs(area_10 - 18.6) / 18.6 < 0.02, f"10 Tcf area P50={area_10} not within 2% of 18.6 km²"

    # Check CO2 sensitivity table
    co2_table = art.get("co2_sensitivity_table", [])
    assert len(co2_table) >= 7
    co2_percentages = [row["co2_percent"] for row in co2_table]
    assert "0%" in co2_percentages and "60%" in co2_percentages

    # Check plateau years at 1 Bscfd
    assert art.get("plateau_years") is not None
    assert art["plateau_years"] > 0

    # Check provenance
    provenance = art.get("input_provenance", {})
    assert provenance.get("net_pay_m") == "OBS"
    assert provenance.get("porosity_range") == "ASSUMPTION"

    # Check forbidden use
    assert "not a reserve or drilling recommendation" in art.get("forbidden_use", "").lower()
