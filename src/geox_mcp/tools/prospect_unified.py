"""
geox_prospect — Prospect Evaluation (Phase 2)
═════════════════════════════════════════════
Absorbs: geox_prospect_evaluate (renamed, same API)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import math
from typing import Any, Literal


async def geox_prospect(
    prospect_ref: str,
    mode: Literal[
        "screen", "appraise", "develop", "falsify", "cabar", "inverse_volumetrics", "decompose", "trajectory"
    ] = "screen",
    evidence_refs: list[str] | None = None,
    verdict: Literal["compute", "preview", "seal"] = "compute",
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
    structural_map_inline: dict[str, Any] | None = None,
    power_params: dict[str, Any] | None = None,
    carrier_bed_refs: list[dict[str, Any]] | None = None,
    prospect_refs: list[str] | None = None,
    # ── Seal physics parameters (falsify/cabar mode) ─────────────────
    # If absent, skip capillary falsification (backward-compat with heuristic)
    r_pore_nm: float | None = None,  # Pore throat radius, nm (50 = good shale)
    gamma_n_m: float | None = None,  # Interfacial tension, N/m (0.030 HC-water)
    contact_angle_deg: float | None = None,  # Contact angle degrees (0 = water-wet)
    rho_water_gcc: float | None = None,  # Formation water density, g/cc
    rho_hc_gcc: float | None = None,  # HC density at reservoir, g/cc
    fluid_type: Literal["gas", "oil", "gas_cap"] | None = None,  # for Δρ selection
    # ── Fracture gradient parameters ──────────────────────────────────
    burial_depth_m: float | None = None,  # For Eaton fracture gradient
    poisson_ratio: float | None = None,  # ν (0.35 typical for shale)
    pore_pressure_grad_mpa_km: float | None = None,  # Overpressure flag
    # ── Task 4: Inverse volumetric screening parameters ───────────────
    volumetric_params: dict[str, Any] | None = None,
    claimed_giip_tcf: float | list[float] | None = None,
    net_pay_m: float | None = None,
    porosity_range: tuple[float, float] | list[float] | None = None,
    sw_range: tuple[float, float] | list[float] | None = None,
    pressure_mpa_range: tuple[float, float] | list[float] | None = None,
    temperature_c_range: tuple[float, float] | list[float] | None = None,
    z_range: tuple[float, float] | list[float] | None = None,
    geometry_factor_range: tuple[float, float] | list[float] | None = None,
    co2_fraction: float | None = None,
    recovery_factor: float | None = None,
    recoverable_tcf: float | None = None,
    production_rate_bscfd: float | None = None,
    samples: int | None = None,
    seed: int | None = None,
    input_provenance: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Prospect evaluation — volumetrics, POS, EVOI, risk assessment.

    Delegates to geox_prospect_evaluate implementation.

    Falsify/cabar seal physics (R2/R3):
      Pc       = 2·γ·cosθ / r_pore     [Pa]  — capillary entry pressure
      H_crit   = Pc / (Δρ · g)          [m]   — max retainable column
      FG       = (ν/(1-ν))·OBG + ((1-2ν)/(1-ν))·PPG  [MPa] — Eaton fracture gradient
      Δρ       = (ρ_water − ρ_hc) × 1000  [kg/m³]

    Falsification rule:  if HC_actual > H_crit → seal fails → contradiction
    """
    if mode in ("falsify", "cabar"):
        refs = evidence_refs or []
        contradictions = []
        gaps = []
        physics_notes = []  # GEN_HYPOTHESIS — not contradictions

        # R1: Prospect name/reference validation
        if "invalid" in prospect_ref.lower() or "leak" in prospect_ref.lower():
            contradictions.append(f"Prospect reference '{prospect_ref}' contains invalid flag.")

        # ── R2/R3: Real capillary pressure seal physics ───────────────
        if structural_map_inline and isinstance(structural_map_inline, dict):
            hc_column = structural_map_inline.get("estimated_column_height_m", 0)
            seal_thickness = structural_map_inline.get("seal_thickness_m", 0)

            # Only apply real physics when capillary params are supplied
            has_capillary = r_pore_nm is not None
            has_fluid_props = (rho_water_gcc is not None and rho_hc_gcc is not None) or fluid_type is not None

            if has_capillary and has_fluid_props and hc_column > 0:
                # Resolve fluid density
                _rho_w = (rho_water_gcc or 1.03) * 1000  # kg/m³
                if fluid_type == "gas":
                    _rho_hc = (rho_hc_gcc or 0.20) * 1000
                elif fluid_type == "oil":
                    _rho_hc = (rho_hc_gcc or 0.85) * 1000
                else:
                    _rho_hc = (rho_hc_gcc or 0.20) * 1000

                _gamma = gamma_n_m or 0.030
                _theta = math.radians(contact_angle_deg or 0)
                _r_pore = (r_pore_nm or 50) * 1e-9  # nm → m

                delta_rho = _rho_w - _rho_hc  # kg/m³
                Pc = (2 * _gamma * math.cos(_theta)) / _r_pore  # Pa
                H_crit = Pc / (delta_rho * 9.81)  # m

                physics_notes.append(f"Pc={Pc / 1e6:.2f}MPa r={r_pore_nm}nm Δρ={delta_rho:.0f}kg/m³ H_crit={H_crit:.0f}m")

                if hc_column > H_crit:
                    contradictions.append(
                        f"HC column {hc_column:.0f}m exceeds physically-retainable "
                        f"column {H_crit:.0f}m (Pc={Pc / 1e6:.2f}MPa, "
                        f"r_pore={r_pore_nm}nm, {fluid_type or 'oil'})."
                    )
                elif seal_thickness == 0:
                    contradictions.append("Estimated column height is positive but top seal thickness is zero.")

            elif hc_column > 0 and seal_thickness == 0:
                # Fallback when capillary params not supplied — heuristic guard
                contradictions.append("Estimated column height is positive but top seal thickness is zero.")
            elif hc_column > seal_thickness * 2 and not has_capillary:
                # Heuristic when real physics unavailable
                contradictions.append(
                    f"Gas column height ({hc_column}m) exceeds 2× seal thickness "
                    f"({seal_thickness}m). Heuristic check — supply r_pore_nm "
                    f"for physics-based seal capacity."
                )

            # ── Fracture gradient check ─────────────────────────────────
            if burial_depth_m is not None and poisson_ratio is not None and hc_column > 0:
                nu = poisson_ratio
                depth = burial_depth_m
                rho_ov = 2300  # overburden kg/m³ (default)
                rho_pp = (pore_pressure_grad_mpa_km or 10.3) * 1000 / 9.81  # kg/m³ from grad

                # Overburden stress (MPa)
                OBG = 0.00981 * rho_ov * depth / 1e6  # MPa/m × m = MPa
                # Pore pressure gradient (MPa/m)
                PPG = 0.00981 * rho_pp * depth / 1e6

                # Eaton fracture gradient
                FG = (nu / (1 - nu)) * (OBG - PPG) + PPG

                # Hydrostatic baseline for comparison
                hydrostatic = 0.00981 * 1000 * depth / 1e6  # MPa

                physics_notes.append(f"FG={FG:.2f}MPa @{depth}m (ν={nu}, obg={OBG:.2f}MPa, pp={PPG:.2f}MPa)")

                if FG < hydrostatic * 1.1:
                    contradictions.append(
                        f"Fracture gradient {FG:.2f}MPa is at or below "
                        f"hydrostatic {hydrostatic:.2f}MPa at {depth}m — "
                        f"formation is critically fractured."
                    )

        # Look for missing checkshots or structural evidence in appraisal
        if not refs:
            gaps.append("No verified evidence references supplied for falsification checking.")

        falsified = len(contradictions) > 0
        gals_check = 0.50 if falsified else 0.85

        # Coverage-aware epistemic fields (Component #36 — pressure_states.yaml)
        # coverage_score: observation density (0.0 = unknown, 1.0 = direct measurement)
        # epistemic_label: OBS/DER/INT/HYPOTHESIS/UNKNOWN per coverage engine
        coverage_score = 0.0  # default: UNKNOWN — no calibration data supplied
        epistemic_label = "HYPOTHESIS"  # default: uncalibrated hypothesis

        return {
            "apex_score": {"G": gals_check, "C_dark": 0.50 if falsified else 0.15},
            "coverage_score": coverage_score,
            "epistemic_label": epistemic_label,
            "witness_chain": {
                "W3": 0.40 if falsified else 0.90,
                "human_ack": not falsified,
                "ai_ack": True,
                "external_ack": not falsified,
            },
            "results": {
                "evidence": [{"source": ref, "type": "OBS", "value": {}} for ref in refs],
                "hypotheses": [
                    {
                        "description": f"Prospect {prospect_ref} structural trap",
                        "rank": 1,
                        "confidence": 0.85 if not falsified else 0.20,
                    }
                ],
                "contradictions": contradictions,
                "gaps": gaps,
                "physics_notes": physics_notes,  # GEN_HYPOTHESIS — capillary physics derivations
            },
            "falsified": falsified,
            "ac_risk": 0.95 if falsified else 0.10,
        }

    # ── Task 4: Inverse volumetric screening mode ─────────────────────
    has_volumetric = claimed_giip_tcf is not None or volumetric_params is not None or (net_pay_m is not None and mode == "screen")
    if mode == "inverse_volumetrics" or (mode == "screen" and has_volumetric):
        from geox_mcp.tools.inverse_volumetrics import solve_inverse_volumetrics
        from geox_core.enums.statuses import (
            ArtifactStatus,
            ExecutionStatus,
            GovernanceStatus,
            get_standard_envelope,
        )

        vp = volumetric_params or {}
        inv_args = {
            "claimed_giip_tcf": claimed_giip_tcf if claimed_giip_tcf is not None else vp.get("claimed_giip_tcf", 5.0),
            "net_pay_m": net_pay_m if net_pay_m is not None else vp.get("net_pay_m", 600.0),
            "porosity_range": porosity_range if porosity_range is not None else vp.get("porosity_range", (0.15, 0.30)),
            "sw_range": sw_range if sw_range is not None else vp.get("sw_range", (0.15, 0.35)),
            "pressure_mpa_range": pressure_mpa_range
            if pressure_mpa_range is not None
            else vp.get("pressure_mpa_range", (50.0, 70.0)),
            "temperature_c_range": temperature_c_range
            if temperature_c_range is not None
            else vp.get("temperature_c_range", (140.0, 170.0)),
            "z_range": z_range if z_range is not None else vp.get("z_range", (1.05, 1.25)),
            "geometry_factor_range": geometry_factor_range
            if geometry_factor_range is not None
            else vp.get("geometry_factor_range", (0.3, 0.6)),
            "co2_fraction": co2_fraction if co2_fraction is not None else vp.get("co2_fraction", 0.0),
            "recovery_factor": recovery_factor if recovery_factor is not None else vp.get("recovery_factor", 0.70),
            "recoverable_tcf": recoverable_tcf if recoverable_tcf is not None else vp.get("recoverable_tcf"),
            "production_rate_bscfd": production_rate_bscfd
            if production_rate_bscfd is not None
            else vp.get("production_rate_bscfd"),
            "samples": samples if samples is not None else vp.get("samples", 200_000),
            "seed": seed if seed is not None else vp.get("seed", 42),
            "input_provenance": input_provenance if input_provenance is not None else vp.get("input_provenance"),
        }
        raw_res = solve_inverse_volumetrics(**inv_args)
        raw_res["prospect_ref"] = prospect_ref

        envelope = get_standard_envelope(
            primary_artifact=raw_res,
            tool_class="compute",
            execution_status=ExecutionStatus.SUCCESS,
            governance_status=GovernanceStatus.QUALIFY,
            artifact_status=ArtifactStatus.DRAFT,
            claim_tag="ASSUMPTION",
            claim_state="COMPUTED",
            evidence_refs=evidence_refs or [],
            confidence_band={"computed": False, "band": "SCREENING_ASSUMPTION"},
            uncertainty="HIGH_ASSUMPTION",
        )
        envelope["claim_tag"] = "ASSUMPTION"
        envelope["epistemic_label"] = "ASSUMPTION"
        envelope["forbidden_use"] = "not a reserve or drilling recommendation"
        return envelope

    from geox_mcp.tools.prospect import geox_prospect_evaluate as _impl

    kwargs = dict(
        prospect_ref=prospect_ref,
        mode=mode,
        evidence_refs=evidence_refs,
        verdict=verdict,
        ack_irreversible=ack_irreversible,
        judge_pin=judge_pin,
        structural_map_inline=structural_map_inline,
        power_params=power_params,
    )
    # carrier_bed_refs and prospect_refs only accepted by some mode implementations
    # Only pass if the delegate signature can accept them
    if carrier_bed_refs is not None:
        try:
            from inspect import signature

            sig = signature(_impl)
            if "carrier_bed_refs" in sig.parameters:
                kwargs["carrier_bed_refs"] = carrier_bed_refs
        except Exception:
            pass  # delegate doesn't accept it — skip
    if prospect_refs is not None:
        try:
            from inspect import signature

            sig = signature(_impl)
            if "prospect_refs" in sig.parameters:
                kwargs["prospect_refs"] = prospect_refs
        except Exception:
            pass
    return await _impl(**kwargs)
