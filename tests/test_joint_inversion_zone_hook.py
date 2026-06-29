"""
test_joint_inversion_zone_hook.py — Tests for the post-inversion crust-zone hook
═══════════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBEI

Verifies:
  - F4 CLARITY: opt-in flag, default OFF, no breakage for existing callers
  - F2 TRUTH: classification is DER-grade (from inverted state.vp)
  - F7 HUMILITY: confidence hard-capped at 0.90
  - m/s → km/s conversion is correct
  - Sabah-specific scenarios
"""
from __future__ import annotations

import pytest

from geox_core.physics.joint_inversion import (
    InversionRequest,
    ModalityObservation,
    joint_inversion,
)
from geox_core.physics.joint_inversion_zone_hook import (
    PostInversionZoneHook,
    classify_state_post_inversion,
)
from geox_core.physics.state import Physics13State
from geox_core.schemas.crust_vp_grammar import CrustZone


# ═══════════════════════════════════════════════════════════════════════════════
# F4 CLARITY — opt-in behavior (no breakage)
# ═══════════════════════════════════════════════════════════════════════════════


class TestOptInBehavior:
    """F4 CLARITY: default behavior unchanged when classify_crust_zone=False."""

    def test_default_off_no_classification(self) -> None:
        """Existing callers see no change."""
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance", value=7000000.0, depth_m=2000.0
                ),
            ],
        )
        assert req.classify_crust_zone is False  # default
        result = joint_inversion(req)
        assert "crust_zone_classification" not in result

    def test_explicit_off_no_classification(self) -> None:
        """Setting classify_crust_zone=False explicitly still skips."""
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance", value=7000000.0, depth_m=2000.0
                ),
            ],
            classify_crust_zone=False,
        )
        result = joint_inversion(req)
        assert "crust_zone_classification" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# F2 TRUTH — DER-grade classification from inverted state
# ═══════════════════════════════════════════════════════════════════════════════


class TestPostInversionClassification:
    """When ON, classification runs on the inverted Physics13State."""

    def test_classification_present_when_on(self) -> None:
        """Setting classify_crust_zone=True adds the field."""
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance", value=7000000.0, depth_m=5000.0
                ),
            ],
            classify_crust_zone=True,
            crust_thickness_km=12.0,
        )
        result = joint_inversion(req)
        assert "crust_zone_classification" in result
        cz = result["crust_zone_classification"]
        assert "crust_zone" in cz
        assert "vp_km_s" in cz
        assert "confidence" in cz

    def test_vp_m_s_to_km_s_conversion(self) -> None:
        """Verify state.vp (m/s) is correctly converted to km/s."""
        # Prior with known Vp
        prior = Physics13State(
            rho=2700.0, vp=5500.0, vs=3300.0, rho_e=100.0,
            chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05,
        )
        # Observation that anchors the impedance = ρ·Vp = 2700·5500 = 14.85e6
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance", value=14850000.0, depth_m=8000.0
                ),
            ],
            prior=prior,
            classify_crust_zone=True,
            crust_thickness_km=22.0,
        )
        result = joint_inversion(req)
        cz = result["crust_zone_classification"]
        # Vp 5500 m/s → 5.5 km/s
        assert abs(cz["vp_km_s"] - 5.5) < 0.05

    def test_depth_derived_from_observations(self) -> None:
        """Cell depth should be median of observation depths."""
        prior = Physics13State(rho=2700.0, vp=5500.0, vs=3300.0, rho_e=100.0, chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05)
        req = InversionRequest(
            observations=[
                ModalityObservation(modality="seismic_impedance", value=14850000.0, depth_m=4000.0),
                ModalityObservation(modality="seismic_impedance", value=14850000.0, depth_m=8000.0),
                ModalityObservation(modality="seismic_impedance", value=14850000.0, depth_m=12000.0),
            ],
            prior=prior,
            classify_crust_zone=True,
            crust_thickness_km=22.0,
        )
        result = joint_inversion(req)
        cz = result["crust_zone_classification"]
        # Median of (4, 8, 12) = 8 km
        assert abs(cz["depth_km"] - 8.0) < 0.01

    def test_diagnostics_included_when_requested(self) -> None:
        """include_zone_diagnostics=True adds diagnostic_basis."""
        prior = Physics13State(rho=2700.0, vp=6500.0, vs=3700.0, rho_e=100.0, chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05)
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance", value=18850000.0, depth_m=5000.0
                ),
            ],
            prior=prior,
            classify_crust_zone=True,
            crust_thickness_km=6.0,
            heat_flow_mw_m2=55.0,
            include_zone_diagnostics=True,
        )
        result = joint_inversion(req)
        cz = result["crust_zone_classification"]
        assert "diagnostic_basis" in cz
        assert len(cz["diagnostic_basis"]) > 0

    def test_no_diagnostics_by_default(self) -> None:
        """Verbose diagnostics are off by default to keep result compact."""
        prior = Physics13State(rho=2700.0, vp=6500.0, vs=3700.0, rho_e=100.0, chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05)
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance", value=18850000.0, depth_m=5000.0
                ),
            ],
            prior=prior,
            classify_crust_zone=True,
            crust_thickness_km=6.0,
            heat_flow_mw_m2=55.0,
        )
        result = joint_inversion(req)
        cz = result["crust_zone_classification"]
        assert "diagnostic_basis" not in cz


# ═══════════════════════════════════════════════════════════════════════════════
# F7 HUMILITY — confidence cap
# ═══════════════════════════════════════════════════════════════════════════════


class TestHumilityCap:
    """Confidence is hard-capped at 0.90."""

    def test_no_classification_above_0_90(self) -> None:
        # Generate a wide range of priors + observations
        test_vps = [3000.0, 4500.0, 5500.0, 6500.0, 7500.0]
        test_thicks = [5.0, 10.0, 22.0, 30.0]
        for vp_m_s in test_vps:
            for thick in test_thicks:
                rho = 2400.0 + (vp_m_s - 3000.0) / 10.0  # crude ρ-Vp tie
                prior = Physics13State(rho=rho, vp=vp_m_s, vs=vp_m_s / 1.8, rho_e=100.0, chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05)
                req = InversionRequest(
                    observations=[
                        ModalityObservation(
                            modality="seismic_impedance",
                            value=rho * vp_m_s,
                            depth_m=5000.0,
                        ),
                    ],
                    prior=prior,
                    classify_crust_zone=True,
                    crust_thickness_km=thick,
                )
                result = joint_inversion(req)
                cz = result["crust_zone_classification"]
                assert cz["confidence"] <= 0.90, (
                    f"F7 VIOLATION: vp={vp_m_s}, thick={thick}, "
                    f"confidence={cz['confidence']}"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# Sabah-specific scenarios
# ═══════════════════════════════════════════════════════════════════════════════


class TestSabahScenarios:
    """Sabah Basin-specific classification scenarios."""

    def test_kinabalu_inboard_normal_continental(self) -> None:
        """Kinabalu Basin on Dangerous Grounds: thick continental, ~30 km."""
        prior = Physics13State(rho=2750.0, vp=6200.0, vs=3600.0, rho_e=100.0, chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05)
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance",
                    value=2750 * 6200,
                    depth_m=5000.0,
                ),
            ],
            prior=prior,
            classify_crust_zone=True,
            crust_thickness_km=30.0,  # Kinabalu/Dangerous Grounds
        )
        result = joint_inversion(req)
        cz = result["crust_zone_classification"]
        # 6.2 km/s in 30 km crust → normal_continental
        assert cz["crust_zone"] == CrustZone.NORMAL_CONTINENTAL.value

    def test_layang_layang_ductile_signature(self) -> None:
        """Layang-Layang: ductile layer expected at ~9 km depth."""
        prior = Physics13State(rho=2700.0, vp=5900.0, vs=3400.0, rho_e=100.0, chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05)
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance",
                    value=2700 * 5900,
                    depth_m=9000.0,  # mid-crust depth
                ),
            ],
            prior=prior,
            classify_crust_zone=True,
            crust_thickness_km=10.0,
        )
        result = joint_inversion(req)
        cz = result["crust_zone_classification"]
        # Vp 5.9 km/s at 9 km depth → ductile mid-crustal layer
        assert cz["crust_zone"] == CrustZone.DUCTILE_MID_CRUSTAL.value

    def test_nw_sabah_oct(self) -> None:
        """NW Sabah trough → hyperthinned OCT-equivalent."""
        prior = Physics13State(rho=2850.0, vp=6500.0, vs=3700.0, rho_e=100.0, chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05)
        req = InversionRequest(
            observations=[
                ModalityObservation(
                    modality="seismic_impedance",
                    value=2850 * 6500,
                    depth_m=5000.0,
                ),
            ],
            prior=prior,
            classify_crust_zone=True,
            crust_thickness_km=6.0,
        )
        result = joint_inversion(req)
        cz = result["crust_zone_classification"]
        assert cz["crust_zone"] == CrustZone.HYPERTHINNED_OCT.value


# ═══════════════════════════════════════════════════════════════════════════════
# PostInversionZoneHook dataclass
# ═══════════════════════════════════════════════════════════════════════════════


class TestZoneHookDataclass:
    def test_default_hook_values(self) -> None:
        hook = PostInversionZoneHook()
        assert hook.crust_thickness_km is None
        assert hook.heat_flow_mw_m2 is None
        assert hook.include_diagnostics is False

    def test_custom_hook_values(self) -> None:
        hook = PostInversionZoneHook(
            crust_thickness_km=12.0,
            heat_flow_mw_m2=55.0,
            include_diagnostics=True,
        )
        assert hook.crust_thickness_km == 12.0
        assert hook.heat_flow_mw_m2 == 55.0
        assert hook.include_diagnostics is True

    def test_hook_is_frozen(self) -> None:
        """Frozen dataclass — accidental mutation is a programming error."""
        hook = PostInversionZoneHook()
        with pytest.raises(Exception):
            hook.crust_thickness_km = 99.0  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════════════
# Direct function tests (classify_state_post_inversion)
# ═══════════════════════════════════════════════════════════════════════════════


class TestDirectHookFunction:
    def test_classify_state_returns_envelope(self) -> None:
        state = Physics13State(rho=2700.0, vp=5500.0, vs=3300.0, rho_e=100.0, chi=0.001, k=2.5, P=15e6, T=300.0, phi=0.05)
        hook = PostInversionZoneHook(crust_thickness_km=22.0)
        observations = [
            ModalityObservation(modality="seismic_impedance", value=14850000.0, depth_m=8000.0),
        ]
        result = classify_state_post_inversion(state, observations, hook)
        assert "crust_zone" in result
        assert "vp_km_s" in result
        assert abs(result["vp_km_s"] - 5.5) < 1e-6
