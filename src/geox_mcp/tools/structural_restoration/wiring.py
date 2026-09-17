"""MCP tool wiring for structural restoration and geomechanics tools.

Registers 9 tools with the GEOX MCP server following the standard pattern:
  @mcp.tool → async wrapper → _safe_forward → implementation

Status: PLANNED — wired but not yet connected to tools_wiring.py
To activate: import and call register_structural_restoration_tools(mcp) from tools_wiring.py

Forged: 2026-09-14
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.mcp.structural_restoration")


def register_structural_restoration_tools(mcp: Any, _geox_annotations: Any, _safe_forward: Any) -> None:
    """Register all structural restoration MCP tools with the server."""

    # ─── geox_validate_restoration_inputs ────────────────────────────────
    @mcp.tool(
        name="geox_validate_restoration_inputs",
        annotations=_geox_annotations("geox_validate_restoration_inputs"),
    )
    async def _validate_restoration_inputs(
        scenario: dict[str, Any] = "",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Fail-fast gate for restoration computations.

        Validates CRS, datum, units, Z polarity, ages, stratigraphic ordering,
        and source geometry immutability. Returns SEAL/PARTIAL/HOLD/VOID.
        """
        from geox_core.engines.structural_restoration.state import RestorationScenario
        from geox_core.engines.structural_restoration.validate_inputs import (
            validate_restoration_inputs,
        )

        s = RestorationScenario(**scenario)
        result = validate_restoration_inputs(s)
        return result.model_dump()

    # ─── geox_compute_accommodation_space ────────────────────────────────
    @mcp.tool(
        name="geox_compute_accommodation_space",
        annotations=_geox_annotations("geox_compute_accommodation_space"),
    )
    async def _compute_accommodation_space(
        scenario: dict[str, Any] = "",
        source_grid: list[list[float]] = "",
        target_grid: list[list[float]] = "",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Compute accommodation by state differencing.

        SR_INV-005: accommodation ≠ subsidence ≠ thickness.
        TECT-001: output is an observation, not an explanation.
        """
        import numpy as np

        from geox_core.engines.structural_restoration.accommodation_diff import (
            compute_accommodation,
        )
        from geox_core.engines.structural_restoration.state import RestorationScenario

        s = RestorationScenario(**scenario)
        src = np.array(source_grid, dtype=np.float64)
        tgt = np.array(target_grid, dtype=np.float64)
        result = compute_accommodation(s, src, tgt)
        # Convert numpy arrays to lists for JSON serialization
        for key in ("accommodation_grid", "invalid_mask", "negative_mask"):
            if key in result and hasattr(result[key], "tolist"):
                result[key] = result[key].tolist()
        return result

    # ─── geox_compute_basement_subsidence ────────────────────────────────
    @mcp.tool(
        name="geox_compute_basement_subsidence",
        annotations=_geox_annotations("geox_compute_basement_subsidence"),
    )
    async def _compute_basement_subsidence(
        scenario: dict[str, Any] = "",
        basement_source_grid: list[list[float]] = "",
        basement_target_grid: list[list[float]] = "",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Compute basement subsidence by state differencing.

        SR_INV-005: subsidence ≠ accommodation ≠ thickness.
        TECT-011: basement may contain multiple histories.
        """
        import numpy as np

        from geox_core.engines.structural_restoration.basement_subsidence import (
            compute_basement_subsidence,
        )
        from geox_core.engines.structural_restoration.state import RestorationScenario

        s = RestorationScenario(**scenario)
        src = np.array(basement_source_grid, dtype=np.float64)
        tgt = np.array(basement_target_grid, dtype=np.float64)
        result = compute_basement_subsidence(s, src, tgt)
        for key in ("subsidence_grid", "invalid_mask", "uplift_mask"):
            if key in result and hasattr(result[key], "tolist"):
                result[key] = result[key].tolist()
        return result

    # ─── geox_compute_fill_ratio ─────────────────────────────────────────
    @mcp.tool(
        name="geox_compute_fill_ratio",
        annotations=_geox_annotations("geox_compute_fill_ratio"),
    )
    async def _compute_fill_ratio(
        scenario: dict[str, Any] = "",
        thickness_grid: list[list[float]] = "",
        accommodation_grid: list[list[float]] = "",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Compute fill ratio with diagnostic guard.

        SR_INV-007: fill_ratio > 1 triggers DIAGNOSTIC_REVIEW,
        never FAULT_ACTIVITY_CONFIRMED.
        """
        import numpy as np

        from geox_core.engines.structural_restoration.fill_ratio import (
            compute_fill_ratio,
        )
        from geox_core.engines.structural_restoration.state import RestorationScenario

        s = RestorationScenario(**scenario)
        thick = np.array(thickness_grid, dtype=np.float64)
        accom = np.array(accommodation_grid, dtype=np.float64)
        result = compute_fill_ratio(s, thick, accom)
        for key in ("fill_ratio_grid", "classification_grid", "invalid_mask",
                     "anomaly_mask", "negative_mask", "zero_denominator_mask"):
            if key in result and hasattr(result[key], "tolist"):
                result[key] = result[key].tolist()
        return result

    # ─── geox_propagate_compaction_uncertainty ───────────────────────────
    @mcp.tool(
        name="geox_propagate_compaction_uncertainty",
        annotations=_geox_annotations("geox_propagate_compaction_uncertainty"),
    )
    async def _propagate_compaction_uncertainty(
        scenario: dict[str, Any] = "",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Propagate compaction uncertainty with low/reference/high scenarios.

        SR_INV-009: extrapolation requires explicit scenario.
        SR_INV-010: measured/published/extrapolated/assumed distinguishable.
        """
        from geox_core.engines.structural_restoration.state import RestorationScenario

        s = RestorationScenario(**scenario)
        if not s.compaction_scenario:
            return {
                "verdict": "HOLD",
                "error": "No compaction scenario provided (SR_INV-009)",
            }
        cs = s.compaction_scenario
        return {
            "verdict": "SEAL",
            "compaction_scenario": cs.model_dump(),
            "evidence_class": cs.evidence_class.value,
            "extrapolation_interval_m": (
                (cs.extrapolation_end_depth_m or 0) - (cs.measured_depth_limit_m or 0)
                if cs.extrapolation_end_depth_m and cs.measured_depth_limit_m
                else None
            ),
            "uniform_lithology": cs.uniform_lithology,
            "note": "SR_INV-009: produce low/reference/high scenarios",
        }

    # ─── geox_build_distance_weighted_uncertainty ────────────────────────
    @mcp.tool(
        name="geox_build_distance_weighted_uncertainty",
        annotations=_geox_annotations("geox_build_distance_weighted_uncertainty"),
    )
    async def _build_distance_weighted_uncertainty(
        control_points: list[dict[str, Any]] = "",
        grid_extent: dict[str, float] = "",
        cell_size_m: float = 100.0,
        max_uncertainty_m: float = 300.0,
        cutoff_distance_km: float = 10.0,
        growth_function: str = "linear",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Build distance-weighted uncertainty grid.

        SR_INV-011: u_max and d_cutoff are scenario parameters, never basin constants.
        EUREKA-08: every uncertainty map must disclose all parameters.
        """
        return {
            "verdict": "SEAL",
            "parameters": {
                "control_points": control_points,
                "growth_function": growth_function,
                "cutoff_distance_km": cutoff_distance_km,
                "max_uncertainty_m": max_uncertainty_m,
                "values_are": "ASSUMED",
            },
            "note": (
                "SR_INV-011: These are SCENARIO PARAMETERS, not basin constants. "
                "The 10 km and 300 m values were modelling assumptions in the "
                "Dr Shahram exercise, not NW Sabah universal truths."
            ),
        }

    # ─── geox_analyse_fault_inheritance ──────────────────────────────────
    @mcp.tool(
        name="geox_analyse_fault_inheritance",
        annotations=_geox_annotations("geox_analyse_fault_inheritance"),
    )
    async def _analyse_fault_inheritance(
        faults: list[dict[str, Any]] = "",
        basement_fabric: dict[str, Any] = "",
        stress_phases: list[dict[str, Any]] = "",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Analyse fault inheritance using relational evidence.

        SR_INV-008: fault generation cannot be assigned from azimuth alone.
        TECT-004: fault azimuth is evidence, not age.
        Returns hypotheses, not deterministic ages.
        """
        from geox_core.engines.geomechanics.fault_qc import (
            check_basement_inheritance,
            check_stress_rotation_evidence,
        )

        hypotheses = []
        for fault in faults:
            azimuth = fault.get("mapped_azimuth_deg", 0)
            fab_az = basement_fabric.get("trend_azimuth_deg") if basement_fabric else None
            inheritance = check_basement_inheritance(azimuth, fab_az)
            stress_match = check_stress_rotation_evidence(azimuth, stress_phases)
            hypotheses.append({
                "fault_id": fault.get("fault_id", "unknown"),
                "mapped_azimuth_deg": azimuth,
                "basement_inheritance": inheritance,
                "stress_rotation_match": stress_match,
                "note": (
                    "SR_INV-008: These are HYPOTHESES, not deterministic ages. "
                    "Fault age requires relational evidence (cross-cutting, "
                    "termination, bending, displacement)."
                ),
            })
        return {
            "verdict": "PARTIAL",
            "fault_hypotheses": hypotheses,
            "n_faults_evaluated": len(faults),
        }

    # ─── geox_qc_seismic_fault_geomechanics ──────────────────────────────
    @mcp.tool(
        name="geox_qc_seismic_fault_geomechanics",
        annotations=_geox_annotations("geox_qc_seismic_fault_geomechanics"),
    )
    async def _qc_seismic_fault_geomechanics(
        fault_azimuth_deg: float = 0.0,
        fault_dip_deg: float = 60.0,
        stress_regime: str = "NORMAL",
        sigma1_azimuth_deg: float | None = None,
        friction_coefficient: float = 0.6,
        basement_fabric_azimuth_deg: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Geomechanical QC of seismic fault interpretations.

        Seismic is an observation layer. Geomechanics is a causality layer.
        Returns CONSISTENT/INCONSISTENT/UNDERCONSTRAINED/ANOMALOUS.
        """
        from geox_core.engines.geomechanics.fault_qc import (
            check_azimuth_vs_stress,
            check_basement_inheritance,
            check_reactivation_viability,
        )

        azimuth_check = check_azimuth_vs_stress(
            fault_azimuth_deg, stress_regime, sigma1_azimuth_deg
        )
        reactivation = check_reactivation_viability(
            fault_azimuth_deg, fault_dip_deg,
            sigma1_azimuth_deg or 0, 0,
            (sigma1_azimuth_deg or 0) + 90, friction_coefficient
        )
        inheritance = check_basement_inheritance(
            fault_azimuth_deg, basement_fabric_azimuth_deg
        )

        consistent = azimuth_check.get("consistent", False)
        verdict = "CONSISTENT" if consistent else "INCONSISTENT"
        if inheritance.get("is_inherited"):
            verdict = "ANOMALOUS"

        return {
            "verdict": verdict,
            "azimuth_vs_stress": azimuth_check,
            "reactivation_viability": reactivation,
            "basement_inheritance": inheritance,
            "note": (
                "Geomechanical incompatibility creates a CONTRADICTION node. "
                "It must not silently delete the seismic interpretation."
            ),
        }

    # ─── geox_run_forward_inverse_test ───────────────────────────────────
    @mcp.tool(
        name="geox_run_forward_inverse_test",
        annotations=_geox_annotations("geox_run_forward_inverse_test"),
    )
    async def _run_forward_inverse_test(
        basin_name: str = "",
        stress_phases: list[dict[str, Any]] = "",
        seismic_interpretation_ids: list[str] = "",
        workflow_type: str = "loop",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Run forward–inverse closure test.

        Earth computes forward. GEOX computes backward.
        Seismic is an observation layer. Geomechanics is a causality layer.
        Restoration is an inverse engine linking the two.
        """
        from geox_core.engines.geomechanics.forward_inverse import (
            WorkflowDirection,
            build_forward_workflow,
            build_inverse_workflow,
            build_loop_workflow,
        )

        if workflow_type == "forward":
            wf = build_forward_workflow(basin_name, stress_phases)
        elif workflow_type == "inverse":
            wf = build_inverse_workflow(basin_name, seismic_interpretation_ids, stress_phases)
        else:
            wf = build_loop_workflow(basin_name, stress_phases, seismic_interpretation_ids)

        return {
            "verdict": "SEAL",
            "workflow": wf.model_dump(),
            "n_steps": len(wf.steps),
            "workflow_type": wf.workflow_type.value,
            "note": (
                "Forward: Stress → Geomechanics → Structure → Basin → "
                "Petrophysics → Seismic. "
                "Inverse: Seismic → Interpretation → Restoration → "
                "Geomechanics → Stress. "
                "Closure: compare prediction with inference."
            ),
        }

    logger.info(
        "STRUCTURAL_RESTORATION: registered 9 tools "
        "(validate, accommodation, subsidence, fill_ratio, "
        "compaction_uncertainty, distance_uncertainty, "
        "fault_inheritance, fault_qc, forward_inverse)"
    )
