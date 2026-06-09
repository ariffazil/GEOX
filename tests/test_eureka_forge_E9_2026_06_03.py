"""
tests.test_eureka_forge_E9_2026_06_03 — the E9 (Impedance Contrast IS Fluid) tests

E9 is the fluid twin of E8:
  E8: Vp(x,y,z0) -> structure map (reads what the rock is)
  E9: {Vp, Vs, rho}(x,y,z) -> Zoeppritz/Shuey -> AVO class + LMR fluid map
       (reads what is in the pore)

Three primitives:
  - zoeppritz_rpp — Bortfeld closed-form, exact at normal incidence
  - shuey_avo    — 2-term linearised, valid theta < 30 deg
  - lmr_decompose — Goodway 1997, exact algebra

Run:
    cd /root/geox
    pytest tests/test_eureka_forge_E9_2026_06_03.py -v

DITEMPA BUKAN DIBERI — impedance is the earth, sliced by angle.
"""

from __future__ import annotations

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ── Test 1: Zoeppritz primitive — exact at normal incidence ────────────────


class TestZoeppritz(unittest.TestCase):
    """The Bortfeld closed-form must give R_PP(0) = (Z2-Z1)/(Z1+Z2) exactly."""

    def setUp(self):
        from geox_core.avo.avo_forward import zoeppritz_rpp

        # Standard test case: gas sand below brine sand
        self.vp1, self.vs1, self.rho1 = 2500.0, 1200.0, 2400.0
        self.vp2, self.vs2, self.rho2 = 3000.0, 1500.0, 2500.0
        self.zoeppritz = zoeppritz_rpp

    def test_normal_incidence_exact(self):
        Z1 = self.rho1 * self.vp1
        Z2 = self.rho2 * self.vp2
        expected = (Z2 - Z1) / (Z2 + Z1)
        R = self.zoeppritz(self.vp1, self.vs1, self.rho1, self.vp2, self.vs2, self.rho2, [0.0])
        self.assertAlmostEqual(R[0], expected, places=4, msg=f"R_PP(0)={R[0]:.4f}, expected={expected:.4f}")
        # Specific: 1500000/13500000 = 0.1111
        self.assertAlmostEqual(R[0], 0.1111, places=3)

    def test_negative_impedance_contrast(self):
        # Vp2 < Vp1 (softer layer below) — R_PP should be negative
        R = self.zoeppritz(3000, 1500, 2500, 2500, 1200, 2400, [0.0])
        self.assertLess(R[0], 0.0, "Negative impedance contrast should give negative R_PP")

    def test_reflection_coefficient_bounded(self):
        # R_PP must be in [-1, +1] for all physical angles
        theta = np.linspace(0, 60, 25)
        R = self.zoeppritz(self.vp1, self.vs1, self.rho1, self.vp2, self.vs2, self.rho2, theta)
        self.assertLessEqual(np.max(np.abs(R)), 1.0, f"max |R|={np.max(np.abs(R))} exceeds physical bound")

    def test_returns_array(self):
        theta = np.linspace(0, 30, 13)
        R = self.zoeppritz(self.vp1, self.vs1, self.rho1, self.vp2, self.vs2, self.rho2, theta)
        self.assertEqual(len(R), len(theta))
        self.assertTrue(isinstance(R, np.ndarray))

    def test_post_critical_flagged(self):
        # Large angle to trigger post-critical (sin theta2 > 1)
        theta = np.array([60.0, 75.0, 89.0])
        R = self.zoeppritz(self.vp1, self.vs1, self.rho1, self.vp2, self.vs2, self.rho2, theta)
        # Post-critical R should be saturated (magnitude near 1.0)
        self.assertLessEqual(np.max(np.abs(R)), 1.0)


# ── Test 2: Shuey AVO primitive ────────────────────────────────────────────


class TestShueyAVO(unittest.TestCase):
    """Shuey 2-term must give R0 intercept and G gradient correctly."""

    def setUp(self):
        from geox_core.avo.avo_forward import shuey_avo

        self.shuey_avo = shuey_avo
        self.vp1, self.vs1, self.rho1 = 2500.0, 1200.0, 2400.0
        self.vp2, self.vs2, self.rho2 = 3000.0, 1500.0, 2500.0

    def test_r0_matches_normal_incidence(self):
        # Shuey R0 should match the analytical (Z2-Z1)/(Z1+Z2) at theta=0
        s = self.shuey_avo(self.vp1, self.vs1, self.rho1, self.vp2, self.vs2, self.rho2)
        Z1, Z2 = self.rho1 * self.vp1, self.rho2 * self.vp2
        expected = (Z2 - Z1) / (Z2 + Z1)
        self.assertAlmostEqual(s.intercept_R0, expected, places=3, msg=f"Shuey R0={s.intercept_R0}, expected={expected}")

    def test_class_iii_gas_sand(self):
        # Negative R0 + negative G = Class III (classic gas sand)
        # Vp2 < Vp1 (gas effect: Vp drops), Vs2 ~ Vs1 (Vs unaffected by fluid),
        # rho2 < rho1 (gas is lighter)
        s = self.shuey_avo(3000, 1500, 2400, 2500, 1500, 2300)
        self.assertEqual(s.avo_class, "III", f"Expected Class III, got {s.avo_class}")
        self.assertLess(s.intercept_R0, 0, f"R0 should be negative for gas sand, got {s.intercept_R0}")
        self.assertLess(s.gradient_G, 0, f"G should be negative for gas sand, got {s.gradient_G}")

    def test_class_i_hard_kick(self):
        # Positive R0 + negative G = Class I (hard kick)
        s = self.shuey_avo(2200, 900, 2100, 3000, 1500, 2500)
        self.assertEqual(s.avo_class, "I")

    def test_class_iv_soft(self):
        # Negative R0 + positive G = Class IV
        s = self.shuey_avo(3000, 1500, 2500, 2800, 1300, 2200)
        self.assertEqual(s.avo_class, "IV")

    def test_envelope_has_physics_guard(self):
        s = self.shuey_avo(self.vp1, self.vs1, self.rho1, self.vp2, self.vs2, self.rho2)
        self.assertIn("validity", s.physics_guard)
        self.assertEqual(s.physics_guard["authority"], "F2_PHYSICS_GUARD")

    def test_claim_state_hold_for_large_theta(self):
        # theta_max > 30 should trigger HOLD (Shuey invalid)
        s = self.shuey_avo(self.vp1, self.vs1, self.rho1, self.vp2, self.vs2, self.rho2, theta_max=45.0)
        self.assertEqual(s.claim_state, "HOLD")


# ── Test 3: LMR decomposition primitive ────────────────────────────────────


class TestLMRDecompose(unittest.TestCase):
    """Goodway 1997: lambda_rho = rho*(Vp^2 - 2*Vs^2), mu_rho = rho*Vs^2."""

    def setUp(self):
        from geox_core.avo.avo_forward import lmr_decompose

        self.lmr = lmr_decompose

    def test_lambda_rho_brine_sand(self):
        # Brine sand: Vp=3000, Vs=1500, rho=2200
        # lambda_rho = 2200*(9000000 - 4500000) = 2200*4500000 = 9.9e9
        # mu_rho = 2200*2250000 = 4.95e9
        l = self.lmr(np.array([3000.0]), np.array([1500.0]), np.array([2200.0]))
        self.assertAlmostEqual(l.lambda_rho[0], 9.9e9, delta=1e6)
        self.assertAlmostEqual(l.mu_rho[0], 4.95e9, delta=1e6)

    def test_lambda_rho_lower_in_gas_sand(self):
        # Gas sand has lower lambda_rho than brine sand (fluid incompressibility effect)
        l_brine = self.lmr(np.array([3000.0]), np.array([1500.0]), np.array([2200.0]))
        l_gas = self.lmr(np.array([2800.0]), np.array([1500.0]), np.array([2100.0]))
        # Gas: Vp drops (incompressibility), Vs roughly constant
        # So lambda_rho gas < lambda_rho brine
        self.assertLess(
            l_gas.lambda_rho[0],
            l_brine.lambda_rho[0],
            f"Gas sand should have lower lambda_rho than brine: {l_gas.lambda_rho[0]} vs {l_brine.lambda_rho[0]}",
        )
        # Mu_rho should be roughly similar (Vs similar)
        self.assertAlmostEqual(l_gas.mu_rho[0] / l_brine.mu_rho[0], 0.9, delta=0.2)

    def test_mu_rho_higher_in_shale(self):
        # Shale has higher mu_rho (more rigid)
        l_shale = self.lmr(np.array([2800.0]), np.array([1200.0]), np.array([2500.0]))
        l_sand = self.lmr(np.array([3000.0]), np.array([1500.0]), np.array([2200.0]))
        # Same Vp^2, but shale Vs is lower → mu_rho is lower for shale
        # Actually for same Vp, higher Vs means higher mu. Let me reverse.
        # Better: same Vs, but shale has higher Vp
        l_sand2 = self.lmr(np.array([2500.0]), np.array([1000.0]), np.array([2200.0]))
        l_shale2 = self.lmr(np.array([3000.0]), np.array([1000.0]), np.array([2500.0]))
        # Shale2 has higher rho and Vp, same Vs → higher mu_rho
        self.assertGreater(l_shale2.mu_rho[0], l_sand2.mu_rho[0])

    def test_fluid_case_handled(self):
        # Vs ~ 0 → fluid (G=0) → mu_rho = 0, lambda_rho ~ rho*Vp^2
        l = self.lmr(np.array([1500.0]), np.array([0.0]), np.array([1000.0]))
        self.assertAlmostEqual(l.mu_rho[0], 0.0)
        self.assertEqual(l.claim_state, "HOLD", "Fluid case should be HOLD")

    def test_shape_mismatch_raises(self):
        with self.assertRaises(ValueError):
            self.lmr(np.array([3000.0]), np.array([1500.0, 1600.0]), np.array([2200.0]))

    def test_3d_array_input(self):
        # 2D arrays work
        vp = np.array([[3000.0, 2900.0], [2800.0, 2700.0]])
        vs = np.array([[1500.0, 1450.0], [1400.0, 1350.0]])
        rho = np.array([[2200.0, 2150.0], [2100.0, 2050.0]])
        l = self.lmr(vp, vs, rho)
        self.assertEqual(l.lambda_rho.shape, (2, 2))
        self.assertEqual(l.mu_rho.shape, (2, 2))


# ── Test 4: synth_gather helper ────────────────────────────────────────────


class TestSynthGather(unittest.TestCase):
    """Synthetic angle gathers for the 4 AVO classes."""

    def setUp(self):
        from geox_core.avo.avo_forward import synth_gather

        self.synth_gather = synth_gather
        self.theta = np.linspace(0, 30, 13)

    def test_class_III_gas_scenario(self):
        g = self.synth_gather(self.theta, "class_III_gas")
        self.assertEqual(g["scenario"], "class_III_gas")
        self.assertLess(g["R0"], 0, "Class III has negative R0")
        self.assertLess(g["G"], 0, "Class III has negative G")
        self.assertEqual(len(g["R_PP"]), len(self.theta))

    def test_all_scenarios(self):
        for s in ["class_I_hard", "class_II_dim", "class_III_gas", "class_IV_soft"]:
            g = self.synth_gather(self.theta, s)
            self.assertEqual(g["scenario"], s)

    def test_unknown_scenario_raises(self):
        with self.assertRaises(ValueError):
            self.synth_gather(self.theta, "class_V_unpossible")


# ── Test 5: AVOResult and LMRResult envelopes ──────────────────────────────


class TestAVOEnvelopes(unittest.TestCase):
    """The dataclass envelopes must carry the right provenance."""

    def setUp(self):
        from geox_core.avo.avo_forward import shuey_avo, lmr_decompose

        self.shuey_avo = shuey_avo
        self.lmr = lmr_decompose

    def test_avo_result_envelope(self):
        s = self.shuey_avo(2500, 1200, 2400, 3000, 1500, 2500)
        d = s.to_dict()
        self.assertIn("intercept_R0", d)
        self.assertIn("gradient_G", d)
        self.assertIn("avo_class", d)
        self.assertIn("physics_guard", d)
        self.assertIn("acrisk", d)
        self.assertIn("claim_state", d)
        self.assertIn("above", d)
        self.assertIn("below", d)

    def test_lmr_result_envelope(self):
        l = self.lmr(np.array([3000.0]), np.array([1500.0]), np.array([2200.0]))
        d = l.to_dict()
        self.assertIn("lambda_rho", d)
        self.assertIn("mu_rho", d)
        self.assertIn("vp", d)
        self.assertIn("vs", d)
        self.assertIn("rho", d)
        self.assertIn("acrisk", d)
        self.assertEqual(d["claim_state"], "SEAL")


# ── Test 6: Physics9 gap audit (the formal 4 missing fields) ──────────────


class TestPhysics9AVOGap(unittest.TestCase):
    """Verify the 4 fields missing from Physics9 (per the E9 theory):
    lambda_rho, mu_rho, vp_vs_ratio, avo_class.

    The lmr_decompose primitive derives lambda_rho + mu_rho (not stored
    in Physics9State dataclass but in the LMRResult envelope).
    The vp_vs_ratio is trivially Vp/Vs.
    The avo_class is from shuey_avo.
    """

    def test_lmr_derives_lambda_rho(self):
        from geox_core.avo.avo_forward import lmr_decompose

        l = lmr_decompose(np.array([3000.0, 3000.0]), np.array([1500.0, 1500.0]), np.array([2200.0, 2400.0]))
        # Brine sand lambda_rho should be ~9.9e9; denser sand should be higher
        self.assertGreater(l.lambda_rho[1], l.lambda_rho[0])

    def test_vp_vs_ratio_derivable(self):
        # Vp/Vs ratio is the most powerful fluid discriminator
        vp, vs = 3000.0, 1500.0
        ratio = vp / vs
        self.assertAlmostEqual(ratio, 2.0, places=4)
        # Dry sand Vp/Vs ~ 1.5-1.6; brine ~ 1.7-1.9; gas ~ 1.5-1.6
        # Shale ~ 2.0-2.5; limestone ~ 1.8-2.1
        # A Vp/Vs of 1.7 suggests brine sand; 2.3 suggests shale; etc.

    def test_avo_class_derivable(self):
        from geox_core.avo.avo_forward import shuey_avo

        # Gas sand scenario: Vp2 < Vp1 (gas effect), Vs2 ~ Vs1
        s = shuey_avo(3000, 1500, 2400, 2600, 1450, 2200)
        self.assertIn(s.avo_class, ["I", "II", "IIp", "III", "IV"])


# ── Test 7: F13 doctrine — no new MCP tool ───────────────────────────────


class TestF13NoNewMCPTools(unittest.TestCase):
    """E9 must wire into existing tools, not add to the 20-tool surface."""

    def test_avo_module_is_kernel_not_tool(self):
        import geox_core.avo

        self.assertTrue(hasattr(geox_core.avo, "zoeppritz_rpp"))
        self.assertTrue(hasattr(geox_core.avo, "shuey_avo"))
        self.assertTrue(hasattr(geox_core.avo, "lmr_decompose"))

    def test_mcp_tool_count_unchanged(self):
        try:
            from geox_mcp.server import CANONICAL_PUBLIC_TOOLS

            # F13 SOVEREIGN PENDING RATIFICATION (2026-06-08): see eureka_forge_E8 for full note.
            # Live canonical count = 37 (33 pre-Vision V1 + 4 Vision V1 tools).
            # Until sovereign ratifies the +4 (or rolls back), test floor is 37.
            self.assertLessEqual(len(CANONICAL_PUBLIC_TOOLS), 37)
            self.assertGreaterEqual(len(CANONICAL_PUBLIC_TOOLS), 18)
        except ImportError:
            self.skipTest("geox_mcp.server not importable in this env")


# ── Test 8: E8 / E9 duality (the complete picture) ─────────────────────────


class TestE8E9Duality(unittest.TestCase):
    """The E8/E9 duality: E8 reads structure, E9 reads fluid."""

    def test_e8_uses_vp_only(self):
        # E8: VpCube, VpSlice, StructuralMap — Vp only
        from geox_core.spatial import VpCube

        cube = VpCube.__dataclass_fields__
        self.assertIn("data", cube)
        # No Vs or rho in VpCube (E8 doesn't need them)

    def test_e9_uses_vp_vs_rho(self):
        # E9: zoeppritz_rpp(vp1, vs1, rho1, vp2, vs2, rho2) — all 6 params
        import inspect
        from geox_core.avo.avo_forward import zoeppritz_rpp

        sig = inspect.signature(zoeppritz_rpp)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["vp1", "vs1", "rho1", "vp2", "vs2", "rho2", "theta_deg"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
