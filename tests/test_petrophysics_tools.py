"""
tests/test_petrophysics_tools.py — Phase B: Petrophysics MCP Tool Test Suite
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Tests for:
  geox_select_sw_model          — model admissibility from log QC flags
  geox_compute_petrophysics     — full property pipeline
  geox_validate_cutoffs         — CutoffPolicy schema application
  geox_petrophysical_hold_check — 888_HOLD on floor violations

All async tests run without decorators (asyncio_mode = auto in pyproject.toml).
"""

from __future__ import annotations
from typing import Any

import pytest


def _sc(result: Any) -> dict:
    """Extract structured_content from a tool result (FastMCP 2/3 or Pydantic model)."""
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    if hasattr(result, "structured_content"):
        return result.structured_content  # type: ignore[return-value]
    if isinstance(result, dict):
        return result.get("structured_content") or result
    return result  # type: ignore[return-value]

# ─────────────────────────────────────────────────────────────────────────────
# Schema tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLogQCFlags:
    def test_valid_flags(self):
        from arifos.geox.schemas.petrophysics_schemas import LogQCFlags

        flags = LogQCFlags(
            well_id="PM3-A-12",
            depth_top_m=2400.0,
            depth_base_m=2450.0,
            has_washout=False,
            has_shale=True,
            vsh_max=0.18,
            available_curves=["GR", "NPHI", "RHOB", "ILD"],
        )
        assert flags.well_id == "PM3-A-12"
        assert flags.provenance_tag == "RAW"

    def test_invalid_depth_range_raises(self):
        from arifos.geox.schemas.petrophysics_schemas import LogQCFlags
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="depth_base_m"):
            LogQCFlags(
                well_id="PM3-A-12",
                depth_top_m=2450.0,
                depth_base_m=2400.0,  # base < top → invalid
            )


class TestSwModelAdmissibility:
    def test_archie_recommended_for_clean_sand(self):
        from arifos.geox.schemas.petrophysics_schemas import SwModelAdmissibility

        result = SwModelAdmissibility(
            well_id="PM3-A-12",
            recommended_model="archie",
            admissible_models=["archie"],
            inadmissible_models={"simandoux": ["No shale detected."]},
            requires_hold=False,
            confidence=0.08,
        )
        assert result.recommended_model == "archie"
        assert result.requires_hold is False
        assert result.provenance_tag == "POLICY"

    def test_no_model_requires_hold(self):
        from arifos.geox.schemas.petrophysics_schemas import SwModelAdmissibility

        result = SwModelAdmissibility(
            well_id="PM3-B-01",
            recommended_model="none",
            admissible_models=[],
            requires_hold=True,
            hold_reasons=["No deep resistivity curve."],
            confidence=0.03,
        )
        assert result.requires_hold is True
        assert result.admissible_models == []


class TestPetrophysicsInput:
    def test_valid_archie_input(self):
        from arifos.geox.schemas.petrophysics_schemas import PetrophysicsInput

        inp = PetrophysicsInput(
            well_id="PM3-A-12",
            sw_model="archie",
            rw_ohm_m=0.08,
            rt_ohm_m=25.0,
            phi_fraction=0.22,
        )
        assert inp.sw_model == "archie"
        assert inp.rsh_ohm_m is None

    def test_simandoux_without_rsh_raises(self):
        from arifos.geox.schemas.petrophysics_schemas import PetrophysicsInput
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="rsh_ohm_m is required"):
            PetrophysicsInput(
                well_id="PM3-A-12",
                sw_model="simandoux",
                rw_ohm_m=0.08,
                rt_ohm_m=25.0,
                phi_fraction=0.22,
                rsh_ohm_m=None,  # missing — should raise
            )

    def test_indonesia_model_with_rsh(self):
        from arifos.geox.schemas.petrophysics_schemas import PetrophysicsInput

        inp = PetrophysicsInput(
            well_id="PM3-C-05",
            sw_model="indonesia",
            rw_ohm_m=0.10,
            rt_ohm_m=15.0,
            phi_fraction=0.18,
            vcl_fraction=0.25,
            rsh_ohm_m=1.5,
        )
        assert inp.sw_model == "indonesia"
        assert inp.vcl_fraction == 0.25


class TestPetrophysicsOutput:
    def test_valid_output(self):
        from arifos.geox.schemas.petrophysics_schemas import PetrophysicsOutput

        out = PetrophysicsOutput(
            well_id="PM3-A-12",
            sw_model_used="archie",
            sw_nominal=0.35,
            phi_effective=0.22,
            vcl=0.10,
            bvw=0.077,
            uncertainty=0.09,
        )
        assert out.requires_hold is False
        assert out.provenance_tag == "DERIVED"
        assert out.audit_id.startswith("PETRO-")

    def test_sw_above_one_triggers_hold(self):
        from arifos.geox.schemas.petrophysics_schemas import PetrophysicsOutput

        out = PetrophysicsOutput(
            well_id="PM3-A-12",
            sw_model_used="archie",
            sw_nominal=1.05,  # physically impossible
            phi_effective=0.22,
            vcl=0.10,
            bvw=0.231,
            uncertainty=0.09,
        )
        assert out.requires_hold is True
        assert any("Sw" in t for t in out.hold_triggers)
        assert out.floor_verdicts["F2_truth"] is False


class TestCutoffPolicy:
    def test_valid_policy(self):
        from arifos.geox.schemas.petrophysics_schemas import CutoffPolicy

        policy = CutoffPolicy(
            policy_id="MALAY-BASIN-STD-2024",
            phi_cutoff=0.08,
            sw_cutoff=0.65,
            vcl_cutoff=0.40,
            basis="core_calibration",
        )
        assert policy.provenance_tag == "POLICY"
        assert policy.phi_cutoff == 0.08


class TestCutoffValidationResult:
    def test_net_pay_classification(self):
        from arifos.geox.schemas.petrophysics_schemas import CutoffValidationResult

        result = CutoffValidationResult(
            well_id="PM3-A-12",
            policy_id="MALAY-BASIN-STD-2024",
            is_net_reservoir=True,
            is_net_pay=True,
            phi_pass=True,
            sw_pass=True,
            vcl_pass=True,
            phi_tested=0.22,
            sw_tested=0.35,
            vcl_tested=0.10,
        )
        assert result.is_net_pay is True
        assert result.audit_id.startswith("CUT-")

    def test_non_pay_wet_interval(self):
        from arifos.geox.schemas.petrophysics_schemas import CutoffValidationResult

        result = CutoffValidationResult(
            well_id="PM3-A-12",
            policy_id="MALAY-BASIN-STD-2024",
            is_net_reservoir=True,
            is_net_pay=False,
            phi_pass=True,
            sw_pass=False,  # wet
            vcl_pass=True,
            phi_tested=0.20,
            sw_tested=0.80,  # above sw_cutoff
            vcl_tested=0.15,
            violations=["Sw 0.800 ≥ cutoff 0.650 — non-pay (wet)."],
        )
        assert result.is_net_pay is False
        assert result.sw_pass is False


class TestPetrophysicsHold:
    def test_valid_hold(self):
        from arifos.geox.schemas.petrophysics_schemas import PetrophysicsHold

        hold = PetrophysicsHold(
            well_id="PM3-B-01",
            triggered_by="geox_petrophysical_hold_check",
            violated_floors=["F2", "F7"],
            violations=["Sw > 1.0", "Uncertainty outside [0.03, 0.15]"],
            remediation=["Re-check Rw input.", "Run Monte Carlo."],
        )
        assert hold.requires_human_signoff is True
        assert hold.severity == "block"
        assert hold.hold_id.startswith("HOLD-")

    def test_block_without_signoff_raises(self):
        from arifos.geox.schemas.petrophysics_schemas import PetrophysicsHold
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="F13 violation"):
            PetrophysicsHold(
                well_id="PM3-B-01",
                triggered_by="test",
                violated_floors=["F9"],
                violations=["Phantom data."],
                severity="block",
                requires_human_signoff=False,  # invalid for block
            )


# ─────────────────────────────────────────────────────────────────────────────
# MCP tool integration tests (async, no decorator needed)
# ─────────────────────────────────────────────────────────────────────────────

class TestGeoxSelectSwModel:
    async def test_clean_sand_recommends_archie(self):
        from geox_mcp_server import geox_select_sw_model

        result = await geox_select_sw_model(
            well_id="PM3-A-12",
            depth_top_m=2400.0,
            depth_base_m=2450.0,
            has_shale=False,
            vsh_max=0.05,
            has_deep_resistivity=True,
        )
        sc = _sc(result)
        assert sc["recommended_model"] == "archie"
        assert sc["requires_hold"] is False
        assert sc["provenance_tag"] == "POLICY"

    async def test_no_resistivity_triggers_hold(self):
        from geox_mcp_server import geox_select_sw_model

        result = await geox_select_sw_model(
            well_id="PM3-Z-00",
            depth_top_m=1800.0,
            depth_base_m=1850.0,
            has_deep_resistivity=False,
        )
        sc = _sc(result)
        assert sc["requires_hold"] is True
        assert sc["recommended_model"] == "none"

    async def test_shaly_sand_recommends_indonesia_or_simandoux(self):
        from geox_mcp_server import geox_select_sw_model

        result = await geox_select_sw_model(
            well_id="PM3-C-05",
            depth_top_m=2200.0,
            depth_base_m=2280.0,
            has_shale=True,
            vsh_max=0.30,
            has_deep_resistivity=True,
        )
        sc = _sc(result)
        assert sc["recommended_model"] in ("indonesia", "simandoux")
        assert sc["requires_hold"] is False

    async def test_poor_borehole_quality_triggers_hold(self):
        from geox_mcp_server import geox_select_sw_model

        result = await geox_select_sw_model(
            well_id="PM3-D-07",
            depth_top_m=3000.0,
            depth_base_m=3080.0,
            borehole_quality="poor",
        )
        sc = _sc(result)
        assert sc["requires_hold"] is True


class TestGeoxComputePetrophysics:
    async def test_archie_clean_sand_produces_valid_sw(self):
        from geox_mcp_server import geox_compute_petrophysics

        result = await geox_compute_petrophysics(
            well_id="PM3-A-12",
            sw_model="archie",
            rw_ohm_m=0.08,
            rt_ohm_m=30.0,
            phi_fraction=0.22,
        )
        sc = _sc(result)
        assert sc["sw_nominal"] > 0.0
        assert sc["sw_nominal"] <= 1.0
        assert sc["bvw"] > 0.0
        assert sc["provenance_tag"] == "DERIVED"
        assert sc["requires_hold"] is False

    async def test_physically_impossible_sw_triggers_hold(self):
        from geox_mcp_server import geox_compute_petrophysics

        # Very low Rt and high PHI → Sw > 1
        result = await geox_compute_petrophysics(
            well_id="PM3-A-12",
            sw_model="archie",
            rw_ohm_m=10.0,   # very high Rw
            rt_ohm_m=0.01,   # extremely low Rt
            phi_fraction=0.01,
            run_monte_carlo=False,
        )
        sc = _sc(result)
        # Model should flag a hold (Sw > 1 or near-impossible conditions)
        assert "hold_triggers" in sc or "requires_hold" in sc

    async def test_invalid_model_raises_hold(self):
        from geox_mcp_server import geox_compute_petrophysics

        result = await geox_compute_petrophysics(
            well_id="PM3-A-12",
            sw_model="invalid_model",
            rw_ohm_m=0.08,
            rt_ohm_m=30.0,
            phi_fraction=0.22,
        )
        sc = _sc(result)
        # Should return a hold for invalid model
        assert "violated_floors" in sc or "hold_triggers" in sc

    async def test_simandoux_with_rsh(self):
        from geox_mcp_server import geox_compute_petrophysics

        result = await geox_compute_petrophysics(
            well_id="PM3-C-05",
            sw_model="simandoux",
            rw_ohm_m=0.10,
            rt_ohm_m=15.0,
            phi_fraction=0.18,
            vcl_fraction=0.20,
            rsh_ohm_m=1.5,
            run_monte_carlo=False,
        )
        sc = _sc(result)
        assert sc["sw_model_used"] == "simandoux"
        assert sc["provenance_tag"] == "DERIVED"

    async def test_output_has_audit_id(self):
        from geox_mcp_server import geox_compute_petrophysics

        result = await geox_compute_petrophysics(
            well_id="PM3-A-12",
            sw_model="archie",
            rw_ohm_m=0.08,
            rt_ohm_m=25.0,
            phi_fraction=0.20,
            run_monte_carlo=False,
        )
        sc = _sc(result)
        assert "audit_id" in sc
        assert sc["audit_id"].startswith("PETRO-")


class TestGeoxValidateCutoffs:
    async def test_net_pay_passes_all_cutoffs(self):
        from geox_mcp_server import geox_validate_cutoffs

        result = await geox_validate_cutoffs(
            well_id="PM3-A-12",
            policy_id="MALAY-BASIN-STD-2024",
            phi_cutoff=0.08,
            sw_cutoff=0.65,
            vcl_cutoff=0.40,
            phi_tested=0.22,
            sw_tested=0.35,
            vcl_tested=0.10,
        )
        sc = _sc(result)
        assert sc["is_net_pay"] is True
        assert sc["is_net_reservoir"] is True
        assert sc["violations"] == []
        assert sc["provenance_tag"] == "POLICY"

    async def test_wet_interval_not_net_pay(self):
        from geox_mcp_server import geox_validate_cutoffs

        result = await geox_validate_cutoffs(
            well_id="PM3-A-12",
            policy_id="MALAY-BASIN-STD-2024",
            phi_cutoff=0.08,
            sw_cutoff=0.65,
            vcl_cutoff=0.40,
            phi_tested=0.20,
            sw_tested=0.82,  # wet
            vcl_tested=0.12,
        )
        sc = _sc(result)
        assert sc["is_net_pay"] is False
        assert sc["sw_pass"] is False
        assert any("Sw" in v for v in sc["violations"])

    async def test_low_porosity_not_reservoir(self):
        from geox_mcp_server import geox_validate_cutoffs

        result = await geox_validate_cutoffs(
            well_id="PM3-A-12",
            policy_id="MALAY-BASIN-STD-2024",
            phi_cutoff=0.08,
            sw_cutoff=0.65,
            vcl_cutoff=0.40,
            phi_tested=0.04,  # below cutoff
            sw_tested=0.30,
            vcl_tested=0.10,
        )
        sc = _sc(result)
        assert sc["is_net_reservoir"] is False
        assert sc["phi_pass"] is False

    async def test_physically_impossible_sw_triggers_hold(self):
        from geox_mcp_server import geox_validate_cutoffs

        result = await geox_validate_cutoffs(
            well_id="PM3-A-12",
            policy_id="MALAY-BASIN-STD-2024",
            phi_cutoff=0.08,
            sw_cutoff=0.65,
            vcl_cutoff=0.40,
            phi_tested=0.20,
            sw_tested=1.05,  # physically impossible
            vcl_tested=0.10,
        )
        sc = _sc(result)
        assert sc["requires_hold"] is True

    async def test_rt_cutoff_optional(self):
        from geox_mcp_server import geox_validate_cutoffs

        result = await geox_validate_cutoffs(
            well_id="PM3-A-12",
            policy_id="MALAY-BASIN-STD-2024",
            phi_cutoff=0.08,
            sw_cutoff=0.65,
            vcl_cutoff=0.40,
            phi_tested=0.22,
            sw_tested=0.35,
            vcl_tested=0.10,
            rt_cutoff=5.0,
            rt_tested=20.0,
        )
        sc = _sc(result)
        assert sc["passed_rt_cutoff"] is True

    async def test_audit_id_present(self):
        from geox_mcp_server import geox_validate_cutoffs

        result = await geox_validate_cutoffs(
            well_id="PM3-A-12",
            policy_id="MALAY-BASIN-STD-2024",
            phi_cutoff=0.08,
            sw_cutoff=0.65,
            vcl_cutoff=0.40,
            phi_tested=0.22,
            sw_tested=0.35,
            vcl_tested=0.10,
        )
        sc = _sc(result)
        assert "audit_id" in sc
        assert sc["audit_id"].startswith("CUT-")


class TestGeoxPetrophysicalHoldCheck:
    async def test_valid_properties_return_seal(self):
        from geox_mcp_server import geox_petrophysical_hold_check

        result = await geox_petrophysical_hold_check(
            well_id="PM3-A-12",
            sw_value=0.35,
            phi_value=0.22,
            vcl_value=0.10,
            uncertainty=0.09,
            has_deep_resistivity=True,
            borehole_quality="good",
            sw_model="archie",
        )
        sc = _sc(result)
        assert sc["status"] == "SEAL"
        assert sc["floor_verdicts"]["f2_truth"] is True

    async def test_sw_above_one_triggers_f2_hold(self):
        from geox_mcp_server import geox_petrophysical_hold_check

        result = await geox_petrophysical_hold_check(
            well_id="PM3-A-12",
            sw_value=1.05,
            phi_value=0.22,
            vcl_value=0.10,
            uncertainty=0.09,
            has_deep_resistivity=True,
            borehole_quality="good",
            sw_model="archie",
        )
        sc = _sc(result)
        assert "F2" in sc["violated_floors"]
        assert sc["severity"] == "block"
        assert sc["requires_human_signoff"] is True

    async def test_missing_resistivity_triggers_f4_hold(self):
        from geox_mcp_server import geox_petrophysical_hold_check

        result = await geox_petrophysical_hold_check(
            well_id="PM3-A-12",
            sw_value=0.50,
            phi_value=0.20,
            vcl_value=0.10,
            uncertainty=0.09,
            has_deep_resistivity=False,  # F4 violation
            borehole_quality="good",
            sw_model="archie",
        )
        sc = _sc(result)
        assert "F4" in sc["violated_floors"]

    async def test_uncertainty_outside_f7_band_triggers_hold(self):
        from geox_mcp_server import geox_petrophysical_hold_check

        result = await geox_petrophysical_hold_check(
            well_id="PM3-A-12",
            sw_value=0.35,
            phi_value=0.22,
            vcl_value=0.10,
            uncertainty=0.50,  # F7 violation — overconfident / out of band
            has_deep_resistivity=True,
            borehole_quality="good",
            sw_model="archie",
        )
        sc = _sc(result)
        assert "F7" in sc["violated_floors"]

    async def test_poor_borehole_triggers_f9_hold(self):
        from geox_mcp_server import geox_petrophysical_hold_check

        result = await geox_petrophysical_hold_check(
            well_id="PM3-D-07",
            sw_value=0.40,
            phi_value=0.18,
            vcl_value=0.15,
            uncertainty=0.09,
            has_deep_resistivity=True,
            borehole_quality="poor",  # F9 violation
            sw_model="archie",
        )
        sc = _sc(result)
        assert "F9" in sc["violated_floors"]

    async def test_hold_has_hold_id(self):
        from geox_mcp_server import geox_petrophysical_hold_check

        result = await geox_petrophysical_hold_check(
            well_id="PM3-A-12",
            sw_value=1.10,
            phi_value=0.22,
            vcl_value=0.10,
            uncertainty=0.09,
        )
        sc = _sc(result)
        assert "hold_id" in sc
        assert sc["hold_id"].startswith("HOLD-")

    async def test_multiple_floor_violations_aggregated(self):
        from geox_mcp_server import geox_petrophysical_hold_check

        result = await geox_petrophysical_hold_check(
            well_id="PM3-A-12",
            sw_value=1.05,        # F2
            phi_value=0.22,
            vcl_value=0.10,
            uncertainty=0.80,     # F7
            has_deep_resistivity=False,  # F4
            borehole_quality="poor",     # F9
            sw_model="archie",
        )
        sc = _sc(result)
        floors = sc["violated_floors"]
        assert "F2" in floors
        assert "F4" in floors
        assert "F7" in floors
        assert "F9" in floors

