"""Monte Carlo & MCMC audit hardening tests (2026-11-16).

Phase 1: Percentile convention parity + hard MC receipt + known-distribution P90.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from geox_core.core.volumetrics import ProbabilisticVolumetrics
from geox_core.physics.guards import PhysicsGuard
from geox_core.wealth.volumetric_mc import emv_from_stoiip_mc, stoiip_monte_carlo
from geox_mcp.tools.inverse_volumetrics import solve_inverse_volumetrics


class TestPhase1ConventionAndReceipt:
    def test_known_normal_p90_matches_analytic_quantile(self):
        """Known N(100, 10) scaled by phi=0.25 -> N(25.0, 2.5); P90 = 25 + 1.28155*2.5."""
        vol = ProbabilisticVolumetrics(draws=50_000, seed=123)
        res = vol.compute_hcpv(
            grv_dist={"mean": 100.0, "stddev": 10.0},
            ntg_dist=1.0,
            phi_dist=0.25,
            sw_dist=0.0,
            fvf=1.0,
        )
        expected_p10 = 25.0 - 1.2815515655 * 2.5
        expected_p90 = 25.0 + 1.2815515655 * 2.5
        assert res.percentile_convention == "statistical_ascending"
        assert abs(res.p10 - expected_p10) < 0.1
        assert abs(res.p90 - expected_p90) < 0.1
        assert res.p10 < res.p50 < res.p90
        assert res.mc_receipt["seed"] == 123
        assert res.mc_receipt["n_sims"] == 50_000
        assert res.mc_receipt["standard_error"] > 0

    def test_guard_rejects_untagged_inverted_petroleum_percentiles(self):
        """Unmarked p10 > p90 must HOLD INVALID instead of passing inverted ratio < 1."""
        guard = PhysicsGuard(max_posterior_ratio=5.0)
        res = guard.check_volumetric_output({"p10": 500.0, "p50": 100.0, "p90": 10.0})
        assert res.status == "INVALID"
        assert res.hold is True

    def test_guard_evaluates_petroleum_descending_breadth_correctly(self):
        """With explicit petroleum_descending, 500/10=50 triggers POSTERIOR_TOO_BROAD."""
        guard = PhysicsGuard(max_posterior_ratio=5.0)
        res = guard.check_volumetric_output(
            {
                "p10": 500.0,
                "p50": 100.0,
                "p90": 10.0,
                "percentile_convention": "petroleum_descending",
            }
        )
        assert res.status == "POSTERIOR_TOO_BROAD"
        assert res.hold is True
        assert res.posterior_breadth_ratio == pytest.approx(50.0)

    def test_stoiip_mc_and_emv_preserve_convention_and_receipt(self):
        mc = stoiip_monte_carlo(
            area_km2_p10=12.0,
            area_km2_p50=8.0,
            area_km2_p90=5.0,
            h_m_p10=80.0,
            h_m_p50=50.0,
            h_m_p90=30.0,
            ntg_p10=0.8,
            ntg_p50=0.65,
            ntg_p90=0.5,
            phi_p10=0.25,
            phi_p50=0.20,
            phi_p90=0.15,
            n_sims=10_000,
            seed=42,
        )
        assert mc["percentile_convention"] == "petroleum_descending"
        assert mc["stoiip_mmstb"]["p10"] > mc["stoiip_mmstb"]["p50"] > mc["stoiip_mmstb"]["p90"]
        guard = PhysicsGuard(max_posterior_ratio=20.0)
        assert guard.validate_mc_receipt(mc["mc_receipt"]).status == "PASS"

        emv = emv_from_stoiip_mc(mc, pos=0.3)
        assert emv["percentile_convention"] == "petroleum_descending"
        assert emv["mc_receipt"] == mc["mc_receipt"]

    def test_emv_from_stoiip_mc_handles_statistical_ascending_input(self):
        """Passing statistical_ascending percentiles must not invert low/high branches."""
        stat_input = {
            "percentile_convention": "statistical_ascending",
            "stoiip_mmstb": {"p10": 10.0, "p50": 50.0, "p90": 100.0},
            "mc_receipt": {
                "seed": 1,
                "n_sims": 1000,
                "standard_error": 0.5,
                "percentile_convention": "statistical_ascending",
            },
        }
        emv = emv_from_stoiip_mc(stat_input, pos=0.4)
        assert emv["recoverable_mmstb"]["p10"] < emv["recoverable_mmstb"]["p90"]
        assert emv["scenarios"][0]["outcome"] < emv["scenarios"][2]["outcome"]

    def test_validate_mc_receipt_fails_closed_when_incomplete(self):
        guard = PhysicsGuard()
        assert guard.validate_mc_receipt(None).hold is True
        assert guard.validate_mc_receipt({"seed": 42, "n_sims": 1000}).hold is True
        assert guard.validate_mc_receipt(
            {"seed": None, "n_sims": 1000, "standard_error": 0.1, "percentile_convention": "statistical_ascending"}
        ).hold is True
        assert guard.validate_mc_receipt(
            {"seed": 42, "n_sims": 1000, "standard_error": math.nan, "percentile_convention": "statistical_ascending"}
        ).hold is True

    def test_inverse_volumetrics_emits_receipt(self):
        res = solve_inverse_volumetrics(samples=2000, seed=7)
        # 2026-11-24: SPE-PRMS ordering (P90 = low), data flipped to match the label
        assert res["percentile_convention"] == "petroleum_descending"
        assert PhysicsGuard().validate_mc_receipt(res["mc_receipt"]).status == "PASS"


class TestPhase2RNGIsolation:
    def test_inverse_volumetrics_bit_identical_and_global_rng_untouched(self):
        import numpy as np

        np.random.seed(777)
        before = float(np.random.random())
        np.random.seed(777)
        r1 = solve_inverse_volumetrics(samples=3000, seed=42)
        after_call_1 = float(np.random.random())
        assert after_call_1 == before  # global np.random untouched

        np.random.seed(999)  # scramble global state
        r2 = solve_inverse_volumetrics(samples=3000, seed=42)
        assert r1["required_effective_area_km2"] == r2["required_effective_area_km2"]
        assert r1["expansion_factor_scf_per_rcf"] == r2["expansion_factor_scf_per_rcf"]
        assert r1["mc_receipt"] == r2["mc_receipt"]

    def test_stoiip_mc_bit_identical_same_seed(self):
        kwargs = dict(
            area_km2_p10=12.0,
            area_km2_p50=8.0,
            area_km2_p90=5.0,
            h_m_p10=80.0,
            h_m_p50=50.0,
            h_m_p90=30.0,
            ntg_p10=0.8,
            ntg_p50=0.65,
            ntg_p90=0.5,
            phi_p10=0.25,
            phi_p50=0.20,
            phi_p90=0.15,
            n_sims=5000,
            seed=2026,
        )
        r1 = stoiip_monte_carlo(**kwargs)
        r2 = stoiip_monte_carlo(**kwargs)
        assert r1["stoiip_mmstb"] == r2["stoiip_mmstb"]
        assert r1["mc_receipt"] == r2["mc_receipt"]


class TestPhase3MCMCFalsifiers:
    def test_rejects_frozen_zero_acceptance_chain(self):
        import numpy as np
        from geox_core.physics.gl_mcmc import diagnose_chains

        frozen = [np.ones((200, 6)), np.ones((200, 6))]
        diag = diagnose_chains(frozen, n_accept=0, n_proposals=400)
        assert diag.ess == 0.0
        assert diag.accept_rate == 0.0
        assert diag.converged is False

    def test_rejects_divergent_unmixed_chains(self):
        import numpy as np
        from geox_core.physics.gl_mcmc import diagnose_chains

        rng = np.random.default_rng(7)
        c1 = rng.normal(loc=0.0, scale=0.1, size=(200, 6))
        c2 = rng.normal(loc=5.0, scale=0.1, size=(200, 6))
        diag = diagnose_chains([c1, c2], n_accept=200, n_proposals=400)
        assert diag.r_hat > 1.1
        assert diag.converged is False

    def test_rejects_single_parameter_diverging_hidden_by_others(self):
        import numpy as np
        from geox_core.physics.gl_mcmc import diagnose_chains

        rng = np.random.default_rng(11)
        c1 = rng.normal(0.0, 1.0, size=(200, 6))
        c2 = rng.normal(0.0, 1.0, size=(200, 6))
        # Corrupt only parameter 3 so mean(r_hats) might stay near 1.1 while max(r_hat) explodes
        c1[:, 3] = rng.normal(-4.0, 0.05, size=200)
        c2[:, 3] = rng.normal(+4.0, 0.05, size=200)
        diag = diagnose_chains([c1, c2], n_accept=300, n_proposals=400)
        assert diag.r_hat > 5.0
        assert diag.converged is False

    def test_autocorrelated_chain_reduces_ess_below_n_iter(self):
        import numpy as np
        from geox_core.physics.gl_mcmc import diagnose_chains

        rng = np.random.default_rng(21)
        chains = []
        for _ in range(2):
            arr = np.zeros((400, 6))
            for t in range(1, 400):
                arr[t] = 0.95 * arr[t - 1] + rng.normal(0.0, 0.2, size=6)
            chains.append(arr)
        diag = diagnose_chains(chains, n_accept=600, n_proposals=800)
        assert diag.ess < 150.0  # total nominal draws = 800; AR(1) 0.95 must shrink ESS sharply

    def test_metropolis_hastings_runs_per_chain_and_reproduces(self):
        import numpy as np
        from geox_core.physics.gl_forward_inverse_loop import GLOFObservation
        from geox_core.physics.gl_mcmc import metropolis_hastings
        from geox_core.physics.glgeomaterial import himalayan_defaults

        obs = GLOFObservation(
            label="test_obs",
            water_head_m=110.0,
            breach_width_m=150.0,
            peak_discharge_m3s=3000.0,
            time_to_peak_min=12.0,
            downstream_surge_m=9.0,
            source="gauge",
        )
        np.random.seed(999)
        chains1, diag1 = metropolis_hastings(
            himalayan_defaults(), obs, n_warmup=20, n_iter=30, n_chains=2, seed=42
        )
        np.random.seed(111)
        chains2, diag2 = metropolis_hastings(
            himalayan_defaults(), obs, n_warmup=20, n_iter=30, n_chains=2, seed=42
        )
        assert len(chains1[0]) == 1 + 20 + 30
        assert diag1.n_iter == 30
        assert diag1.n_accept == diag2.n_accept
        assert diag1.ess == diag2.ess
        assert diag1.mean == diag2.mean


class TestPhase4CopulaAndFullVectorEMV:
    def test_correlated_lognormal_pair_spearman_rank_invariant_across_sigmas(self):
        import numpy as np
        from scipy.stats import spearmanr
        from geox_core.wealth.volumetric_mc import correlated_lognormal_pair

        rng = np.random.default_rng(2026)
        # Low-sigma vs high-sigma spreads: raw Pearson decays as sigma grows, Spearman stays ~0.582
        a_lo, b_lo = correlated_lognormal_pair(
            (400.0, 372.5, 347.0), (0.40, 0.375, 0.35), 20_000, rho=0.60, rng=rng
        )
        a_hi, b_hi = correlated_lognormal_pair(
            (2000.0, 200.0, 20.0), (0.80, 0.20, 0.05), 20_000, rho=0.60, rng=rng
        )
        assert 0.55 < float(np.corrcoef(np.log(a_lo), np.log(b_lo))[0, 1]) < 0.65
        rho_s_lo = float(spearmanr(a_lo, b_lo).statistic)
        rho_s_hi = float(spearmanr(a_hi, b_hi).statistic)
        assert 0.55 < rho_s_lo < 0.62
        assert 0.55 < rho_s_hi < 0.62

    def test_no_silent_default_for_percentile_convention(self):
        from geox_core.core.volumetrics import VolumeDistribution

        with pytest.raises(ValueError, match="silent inference is forbidden"):
            emv_from_stoiip_mc({"stoiip_mmstb": {"p10": 100.0, "p50": 50.0, "p90": 10.0}}, pos=0.3)

        with pytest.raises(TypeError):
            VolumeDistribution(
                p10=10.0,
                p50=20.0,
                p90=30.0,
                mean=20.0,
                stdev=5.0,
                valid_draws=100,
                rejected_draws=0,
                hold_enforced=False,
                claim_tag="DER",
                tornado={},
                vault_receipt={},
                physics_validation={},
            )  # type: ignore[call-arg]

        guard = PhysicsGuard()
        assert guard.check_mc_output_strict({"p10": 10.0, "p50": 20.0, "p90": 30.0}).hold is True
        assert guard.check_mc_output_strict(
            {"p10": 10.0, "p50": 20.0, "p90": 30.0, "percentile_convention": "statistical_ascending"}
        ).hold is True

    def test_full_vector_emv_propagates_samples(self):
        mc = stoiip_monte_carlo(
            area_km2_p10=12.0,
            area_km2_p50=8.0,
            area_km2_p90=5.0,
            h_m_p10=80.0,
            h_m_p50=50.0,
            h_m_p90=30.0,
            ntg_p10=0.8,
            ntg_p50=0.65,
            ntg_p90=0.5,
            phi_p10=0.25,
            phi_p50=0.20,
            phi_p90=0.15,
            n_sims=5000,
            seed=42,
            corr_ntg_phi=0.60,
            return_samples=True,
        )
        assert "_samples_mmstb" in mc and len(mc["_samples_mmstb"]) == 5000
        emv = emv_from_stoiip_mc(mc, pos=0.35)
        dist = emv["emv_distribution"]
        assert dist["method"] == "full_vector_mc"
        assert dist["n_samples"] == 5000
        assert dist["emv_standard_error_usd_mm"] > 0
        assert dist["success_value_usd_mm"]["p10"] > dist["success_value_usd_mm"]["p90"]
