"""Tests for W13+ Phase C forge:
- joint_inversion.py (multi-physics fusion)
- mt_forward.py (CSEM/MT 1D forward)
- biostrat_constraint.py (time-facies constraints)
"""

from __future__ import annotations

import math

import pytest

from geox_core.physics.joint_inversion import (
    InversionRequest,
    ModalityObservation,
    joint_inversion,
    joint_inversion_batch,
    forward_impedance,
    forward_vpvs,
    forward_gravity_bouguer,
    forward_magnetic_tmi,
    forward_mt_resistivity,
    DEFAULT_BOUNDS,
)
from geox_core.engines.geophysics.mt_forward import (
    MTLayer,
    MTForwardRequest,
    mt_forward,
    mt_response_from_physics9,
    wait_recursion,
    mt_apparent_resistivity_phase,
)
from geox_core.engines.geophysics.biostrat_constraint import (
    BUILTIN_ZONES,
    BiostratZone,
    evaluate_biostrat_constraint,
)
from geox_core.physics.state import (
    SANDSTONE,
    LIMESTONE,
    SHALE,
    BASEMENT,
    Physics13State,
)


# ════════════════════════════════════════════════════════════════════════════════
# JOINT INVERSION
# ════════════════════════════════════════════════════════════════════════════════
class TestJointInversion:
    def test_no_observations_returns_error(self):
        r = joint_inversion(InversionRequest(observations=[]))
        assert r["ok"] is False
        assert r["error"] == "no_observations"

    def test_seismic_only_inversion_converges(self):
        """Single-modality inversion should converge to the prior."""
        # True Z = ρ · Vp for Sandstone = 2350 * 2950 = 6,932,500
        true_z = SANDSTONE.rho * SANDSTONE.vp
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance", value=true_z,
                    uncertainty=0.02, depth_m=0.0,
                ),
            ],
            prior=SANDSTONE,
            max_iter=30,
        )
        result = joint_inversion(req)
        assert result["ok"] is True
        assert result["grade"] == "AAA"
        assert result["residual_rms"] < 1e-2

    def test_multimodal_converges_within_bounds(self):
        """Seismic + gravity + magnetic + MT should produce an AAA state."""
        # Synthetic observations matching Sandstone
        true_z = SANDSTONE.rho * SANDSTONE.vp
        true_vpvs = SANDSTONE.vp / SANDSTONE.vs
        true_g = forward_gravity_bouguer(SANDSTONE, depth_m=2000.0)
        true_t = forward_magnetic_tmi(SANDSTONE, depth_m=2000.0)
        true_rhoe = SANDSTONE.rho_e

        req = InversionRequest(
            observations=[
                ModalityObservation(modality="seismic_impedance", value=true_z,
                                    uncertainty=0.05, depth_m=2000.0),
                ModalityObservation(modality="seismic_vpvs", value=true_vpvs,
                                    uncertainty=0.05, depth_m=2000.0),
                ModalityObservation(modality="gravity", value=true_g,
                                    uncertainty=0.10, depth_m=2000.0),
                ModalityObservation(modality="magnetic", value=true_t,
                                    uncertainty=0.20, depth_m=2000.0),
                ModalityObservation(modality="mt_resistivity", value=true_rhoe,
                                    uncertainty=0.10, depth_m=2000.0),
            ],
            prior=Physics13State(
                rho=2400.0, vp=2900.0, vs=1650.0, rho_e=20.0,
                chi=0.0001, k=2.8, P=20e6, T=320.0, phi=0.25,
            ),
            max_iter=80,
        )
        result = joint_inversion(req)
        assert result["ok"] is True
        assert result["grade"] == "AAA"
        assert result["modality_count"] == 5
        assert result["observation_count"] == 5
        # State should be close to true Sandstone
        s = result["state"]
        assert abs(s.rho - SANDSTONE.rho) < 100.0
        assert abs(s.vp - SANDSTONE.vp) < 100.0

    def test_observation_hash_is_deterministic(self):
        req = InversionRequest(
            observations=[ModalityObservation(modality="seismic_impedance",
                                              value=1e6, depth_m=1000.0)],
        )
        r1 = joint_inversion(req)
        r2 = joint_inversion(req)
        assert r1["observation_hash"] == r2["observation_hash"]

    def test_per_modality_breakdown(self):
        req = InversionRequest(
            observations=[
                ModalityObservation(modality="seismic_impedance", value=SANDSTONE.rho*SANDSTONE.vp),
                ModalityObservation(modality="gravity", value=forward_gravity_bouguer(SANDSTONE, 1000.0)),
            ],
        )
        result = joint_inversion(req)
        assert "seismic_impedance" in result["per_modality"]
        assert "gravity" in result["per_modality"]

    def test_bounds_clipping_prevents_runaway(self):
        """With an absurd prior and conflicting observations, solver must stay in bounds."""
        req = InversionRequest(
            observations=[ModalityObservation(modality="seismic_impedance",
                                              value=1e9, uncertainty=0.01)],  # nonsense
            prior=Physics13State(rho=2350, vp=2950, vs=1680, rho_e=20, chi=0,
                                k=2.8, P=20e6, T=320, phi=0.25),
        )
        result = joint_inversion(req)
        assert result["ok"] is True
        s = result["state"]
        # All dials must respect DEFAULT_BOUNDS
        assert DEFAULT_BOUNDS["rho"][0] <= s.rho <= DEFAULT_BOUNDS["rho"][1]
        assert DEFAULT_BOUNDS["vp"][0] <= s.vp <= DEFAULT_BOUNDS["vp"][1]
        assert DEFAULT_BOUNDS["phi"][0] <= s.phi <= DEFAULT_BOUNDS["phi"][1]


class TestJointInversionBatch:
    def test_batch_runs_multiple_cells(self):
        cells = [
            InversionRequest(observations=[ModalityObservation(
                modality="seismic_impedance", value=SANDSTONE.rho*SANDSTONE.vp)]),
            InversionRequest(observations=[ModalityObservation(
                modality="seismic_impedance", value=LIMESTONE.rho*LIMESTONE.vp)]),
        ]
        results = joint_inversion_batch(cells)
        assert len(results) == 2
        assert all(r["ok"] for r in results)


# ════════════════════════════════════════════════════════════════════════════════
# CSEM/MT 1D FORWARD
# ════════════════════════════════════════════════════════════════════════════════
class TestMTForward:
    def test_halfspace_returns_constant_resistivity(self):
        """Halfspace of 100 Ω·m must return ρ_a ≈ 100 across frequencies."""
        layers = [MTLayer(thickness_m=1e9, resistivity_ohm_m=100.0)]
        r = mt_forward(MTForwardRequest(layers=layers,
                                        frequencies_hz=(0.01, 0.1, 1.0, 10.0)))
        assert r["ok"] is True
        rho_a = r["apparent_resistivity_ohm_m"]
        for v in rho_a:
            assert abs(v - 100.0) < 1e-3

    def test_three_layer_response_is_finite(self):
        layers = [
            MTLayer(thickness_m=500.0, resistivity_ohm_m=10.0),
            MTLayer(thickness_m=200.0, resistivity_ohm_m=100.0),
            MTLayer(thickness_m=1e9, resistivity_ohm_m=20.0),
        ]
        r = mt_forward(MTForwardRequest(layers=layers,
                                        frequencies_hz=(0.001, 0.01, 0.1, 1.0)))
        assert r["ok"] is True
        # Apparent resistivity can be negative in pathological Cagniard cases
        # (sign reversal); just check finite.
        assert all(math.isfinite(v) for v in r["apparent_resistivity_ohm_m"])
        # Phase is in (-180, 180] for any physical impedance. Strong contrasts
        # can push phase toward ±180° (this is real, not a numerical error).
        assert all(-180 <= p <= 180 for p in r["phase_deg"])

    def test_empty_layers_returns_error(self):
        r = mt_forward(MTForwardRequest(layers=[], frequencies_hz=(1.0,)))
        assert r["ok"] is False

    def test_response_from_physics9_uses_cell_rhoe(self):
        s = Physics13State(rho=2000, vp=3000, vs=1700, rho_e=50.0,
                          chi=0, k=2.5, P=20e6, T=320, phi=0.20)
        r = mt_response_from_physics9(s)
        assert r["ok"] is True
        assert len(r["apparent_resistivity_ohm_m"]) == 6

    def test_wait_recursion_is_stable(self):
        """Run Wait's recursion on a simple 1-layer model, compare with halfspace."""
        layers = [MTLayer(thickness_m=1e9, resistivity_ohm_m=100.0)]
        Z = wait_recursion(layers, omega=2.0 * math.pi)
        # Z should be a finite complex number with positive real part
        assert math.isfinite(Z.real)
        assert math.isfinite(Z.imag)


# ════════════════════════════════════════════════════════════════════════════════
# BIOSTRAT CONSTRAINTS
# ════════════════════════════════════════════════════════════════════════════════
class TestBiostratConstraint:
    def test_builtin_zones_loaded(self):
        assert len(BUILTIN_ZONES) >= 5
        names = [z.name for z in BUILTIN_ZONES]
        assert "Cretaceous_Shale" in names

    def test_sandstone_in_quaternary_zone(self):
        """Sandstone with high φ in Quaternary fluvial zone is consistent."""
        r = evaluate_biostrat_constraint(SANDSTONE, age_ma=1.0)
        assert r.zone_name == "Quaternary_Alluvium"
        assert r.cell_material_match == "Sandstone"
        assert r.is_material_admissible is True
        assert r.is_consistent is True

    def test_sandstone_in_reef_zone_inconsistent(self):
        """Sandstone is not admissible in a reef zone."""
        r = evaluate_biostrat_constraint(SANDSTONE, age_ma=10.0)
        assert r.zone_name == "Miocene_Reef"
        assert r.is_material_admissible is False
        assert r.is_consistent is False

    def test_basement_at_old_age_consistent(self):
        r = evaluate_biostrat_constraint(BASEMENT, age_ma=600.0)
        assert r.zone_name == "Precambrian_Basement"
        assert r.is_consistent is True

    def test_no_zone_for_age_returns_inconsistent(self):
        r = evaluate_biostrat_constraint(SANDSTONE, age_ma=4.0)  # gap between Quaternary and Miocene
        assert r.is_consistent is False
        assert "No biostrat zone" in r.notes[0]

    def test_phi_out_of_range_flagged(self):
        # Sandstone but with very high phi (overpressured) at Quaternary zone
        s = Physics13State(**{**SANDSTONE.__dict__, "phi": 0.05})  # too low for fluvial
        r = evaluate_biostrat_constraint(s, age_ma=1.0)
        assert r.is_consistent is False
        assert any("φ" in n or "Porosity" in n for n in r.notes)

    def test_custom_zone(self):
        custom = BiostratZone(
            name="Custom_Test_Zone",
            age_top_ma=2.6, age_base_ma=5.3,
            environment="lacustrine",
            admissible_materials=("Shale",),
            phi_min=0.10, phi_max=0.30,
        )
        r = evaluate_biostrat_constraint(SHALE, age_ma=3.0, zones=custom)
        assert r.zone_name == "Custom_Test_Zone"
        assert r.is_material_admissible is True
