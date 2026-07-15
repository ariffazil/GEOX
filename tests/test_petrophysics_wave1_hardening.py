from __future__ import annotations

import pytest

from geox_mcp.tools._helpers import _registry
from geox_mcp.tools.petrophysics import geox_subsurface_generate_candidates


def _write_las(path, rows: list[tuple[float, float, float, float, float]]) -> None:
    body = "\n".join(f" {depth:.1f} {gr:.1f} {rt:.2f} {rhob:.2f} {nphi:.2f}" for depth, gr, rt, rhob, nphi in rows)
    path.write_text(
        "\n".join(
            [
                "~Version Information",
                " VERS. 2.0 : CWLS LOG ASCII STANDARD",
                " WRAP. NO",
                "~Well Information",
                " STRT.M 100.0 : START DEPTH",
                " STOP.M 104.0 : STOP DEPTH",
                " STEP.M 1.0 : STEP",
                " NULL. -999.25 : NULL VALUE",
                " WELL. WAVE1_TEST : WELL NAME",
                "~Curve Information",
                " DEPT.M : Measured Depth",
                " GR.API : Gamma Ray",
                " RT.OHMM : True Resistivity",
                " RHOB.G/C3 : Bulk Density",
                " NPHI.V/V : Neutron Porosity",
                "~ASCII Log Data",
                body,
            ]
        )
    )


@pytest.fixture(autouse=True)
def _clear_registry():
    _registry._artifact_registry.clear()
    _registry._artifact_store.clear()
    _registry._well_curves_registry.clear()
    yield
    _registry._artifact_registry.clear()
    _registry._artifact_store.clear()
    _registry._well_curves_registry.clear()


def _register_las(path, artifact_ref: str = "well_las:WAVE1_TEST") -> str:
    return _registry._register_artifact(
        artifact_ref,
        curves=["DEPT", "GR", "RT", "RHOB", "NPHI"],
        las_path=str(path),
        claim_state="INGESTED",
    )


def _record_passed_qc(ref: str) -> None:
    _registry._record_latest_qc(
        ref,
        {
            "qc_passed": True,
            "qc_overall": "PASS",
            "flags": [],
            "limitations": [],
            "claim_state": "QC_VERIFIED",
        },
    )


@pytest.mark.asyncio
async def test_petrophysics_target_requires_passed_qc(tmp_path):
    path = tmp_path / "valid.las"
    _write_las(path, [(100, 45, 40, 2.35, 0.20), (101, 50, 45, 2.34, 0.21), (102, 55, 50, 2.33, 0.22)])
    ref = _register_las(path)

    result = await geox_subsurface_generate_candidates(
        target_class="saturation",
        evidence_refs=[ref],
    )

    assert result["governance_status"] == "HOLD"
    assert result["claim_state"] == "DECISION_SENSITIVE"
    assert result["primary_artifact"]["error_code"] == "QC_REQUIRED_BEFORE_PETROPHYSICS"


@pytest.mark.asyncio
async def test_porosity_success_carries_unit_contract_and_physics_guard(tmp_path):
    path = tmp_path / "valid.las"
    _write_las(path, [(100, 45, 40, 2.35, 0.20), (101, 50, 45, 2.34, 0.21), (102, 55, 50, 2.33, 0.22)])
    ref = _register_las(path)
    _record_passed_qc(ref)

    result = await geox_subsurface_generate_candidates(
        target_class="porosity",
        evidence_refs=[ref],
    )

    assert result["execution_status"] == "SUCCESS"
    artifact = result["primary_artifact"]
    assert artifact["value_contract"]["property"] == "PHI"
    assert artifact["value_contract"]["unit"] == "v/v"
    assert artifact["value_contract"]["RATLAS_ref"].startswith("RATLAS:")
    assert artifact["physics_guard"]["guard_passed"] is True


@pytest.mark.asyncio
async def test_porosity_rejects_rhob_outside_matrix_fluid_window(tmp_path):
    path = tmp_path / "bad_density.las"
    _write_las(path, [(100, 45, 40, 2.80, 0.20), (101, 50, 45, 2.81, 0.21), (102, 55, 50, 2.82, 0.22)])
    ref = _register_las(path)
    _record_passed_qc(ref)

    result = await geox_subsurface_generate_candidates(
        target_class="porosity",
        evidence_refs=[ref],
        matrix_density=2.65,
        fluid_density=1.0,
    )

    assert result["governance_status"] == "HOLD"
    assert result["primary_artifact"]["error_code"] == "RHOB_INCONSISTENT_WITH_DENSITY_ENDPOINTS"
    assert result["physics_guard"]["guard_passed"] is False


@pytest.mark.asyncio
async def test_saturation_rejects_non_positive_archie_parameters(tmp_path):
    path = tmp_path / "valid.las"
    _write_las(path, [(100, 45, 40, 2.35, 0.20), (101, 50, 45, 2.34, 0.21), (102, 55, 50, 2.33, 0.22)])
    ref = _register_las(path)
    _record_passed_qc(ref)

    result = await geox_subsurface_generate_candidates(
        target_class="saturation",
        evidence_refs=[ref],
        rw=0.0,
    )

    assert result["governance_status"] == "HOLD"
    assert result["primary_artifact"]["error_code"] == "INVALID_ARCHIE_PARAMETERS"
    assert "RW_A_M_N_MUST_BE_POSITIVE" in result["physics_guard"]["violations"]
