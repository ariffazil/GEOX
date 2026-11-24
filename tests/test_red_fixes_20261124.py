"""RED-tool fixes 2026-11-24 (FI-002): believable-wrong answers must become loud errors.

Covers geox_source ΔlogR (Passey 1990), geox_temporal decline fit, and
geox_contrast_metabolize input resolution.
"""

from __future__ import annotations

import asyncio
import math

import pytest

from geox_core.source_rock.parameters import estimate_toc_deltalogr

# ── geox_source · ΔlogR ────────────────────────────────────────────────────────


@pytest.mark.parametrize("rt", [0.0, -5.0])
def test_deltalogr_rejects_nonpositive_resistivity(rt):
    with pytest.raises(ValueError, match="resistivity_ohm_m"):
        estimate_toc_deltalogr(depth_m=2500.0, resistivity_ohm_m=rt, sonic_us_ft=100.0)


@pytest.mark.parametrize("kw", [{"baseline_resistivity": 0.0}, {"baseline_sonic": 0.0}])
def test_deltalogr_rejects_nonpositive_baselines(kw):
    with pytest.raises(ValueError, match="baseline"):
        estimate_toc_deltalogr(depth_m=2500.0, resistivity_ohm_m=10.0, sonic_us_ft=100.0, **kw)


def test_deltalogr_density_only_path_refused():
    # Old code converted density -> sonic with a non-Gardner formula (rho=2.4 -> ~1512 us/ft).
    with pytest.raises(ValueError, match="sonic_us_ft"):
        estimate_toc_deltalogr(depth_m=2500.0, resistivity_ohm_m=10.0, density_gcc=2.4)


def test_deltalogr_passey_reference_value():
    # Passey 1990: dlogR = log10(R/Rb) + 0.02(dt - dtb); TOC = dlogR * 10^(2.297 - 0.1688 LOM)
    r = estimate_toc_deltalogr(
        depth_m=2500.0, resistivity_ohm_m=20.0, sonic_us_ft=100.0, lom=9.0,
        baseline_resistivity=2.0, baseline_sonic=90.0,
    )
    dlogr = math.log10(20.0 / 2.0) + 0.02 * (100.0 - 90.0)
    toc = dlogr * 10 ** (2.297 - 0.1688 * 9.0)
    assert r["delta_log_r"] == pytest.approx(dlogr, abs=1e-4)
    assert r["toc_wt_pct"] == pytest.approx(toc, abs=1e-3)


def test_deltalogr_exposes_assumed_inputs_and_lowers_confidence_on_defaults():
    r = estimate_toc_deltalogr(depth_m=2500.0, resistivity_ohm_m=20.0, sonic_us_ft=100.0)
    used = r["inputs_used"]
    assert used["baseline_resistivity_ohm_m"] == 2.0
    assert used["baseline_sonic_us_ft"] == 90.0
    assert used["lom"] == 7.0
    assert set(r["defaults_applied"]) == {"baseline_resistivity", "baseline_sonic", "lom"}
    assert r["confidence"] == "LOW"


def test_deltalogr_picked_baselines_keep_medium_confidence():
    r = estimate_toc_deltalogr(
        depth_m=2500.0, resistivity_ohm_m=20.0, sonic_us_ft=100.0, lom=9.0,
        baseline_resistivity=1.5, baseline_sonic=95.0,
    )
    assert r["defaults_applied"] == []
    assert r["confidence"] == "MEDIUM"


# ── geox_temporal · decline ────────────────────────────────────────────────────


def _decline(rows, **kw):
    from geox.egs.tools.temporal import temporal_decline

    return asyncio.run(temporal_decline(production_data=rows, **kw))


def test_decline_rejects_zero_first_rate():
    r = _decline([{"year": 2020, "bpd": 0}, {"year": 2021, "bpd": 500}])
    assert r["success"] is False
    assert "positive" in r["error"]


def test_decline_uses_all_points_least_squares():
    # Exact exponential through all points except a high middle outlier; endpoint-only
    # method ignores the middle point, a least-squares fit must not.
    d = 0.2
    rows = [{"year": 2020 + i, "bpd": 1000.0 * math.exp(-d * i)} for i in range(5)]
    r = _decline(rows)["results"]
    assert r["fit"]["method"] == "log_linear_least_squares"
    assert r["fit"]["n_points"] == 5
    assert r["fit"]["r_squared"] == pytest.approx(1.0, abs=1e-9)
    assert r["decline_rate_pct_annual"] == pytest.approx((1 - math.exp(-d)) * 100, abs=0.01)

    # Off-centre outlier (a point at mean(t) moves the intercept only, not the slope).
    # Endpoints unchanged, so the old first/last method would report the same decline.
    rows[3]["bpd"] *= 1.5
    r2 = _decline(rows)["results"]
    assert r2["fit"]["r_squared"] < 1.0
    assert r2["decline_rate_pct_annual"] != pytest.approx(r["decline_rate_pct_annual"], abs=0.01)


def test_decline_flat_is_stable():
    r = _decline([{"year": 2020, "bpd": 800}, {"year": 2021, "bpd": 800}, {"year": 2022, "bpd": 800}])
    assert r["results"]["trend"] == "stable"


# ── geox_contrast_metabolize · no silent fixture ───────────────────────────────


def _metabolize(**kw):
    from geox_mcp.tools.contrast_metabolize import geox_contrast_metabolize

    return asyncio.run(geox_contrast_metabolize(**kw))


def test_metabolize_without_input_refuses():
    r = _metabolize()
    assert r["ok"] is False
    assert "impedance_profile" in r["error"]


def test_metabolize_explicit_synthetic_is_labelled():
    r = _metabolize(mode="synthetic")
    assert r["ok"] is True
    assert r["data_source"] == "SYNTHETIC_FIXTURE"


def test_metabolize_arrays_infer_profile_mode():
    imp = [6000.0] * 20 + [9000.0] * 20 + [6000.0] * 20
    dep = [2000.0 + 2.0 * i for i in range(60)]
    r = _metabolize(impedance_profile=imp, depth_profile=dep)
    assert r["ok"] is True
    assert r["mode"] == "profile"
    assert r["data_source"] == "CALLER_PROFILE"
