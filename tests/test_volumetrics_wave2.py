from geox.core.volumetrics import ProbabilisticVolumetrics


def test_probabilistic_volumetrics_returns_percentiles():
    result = ProbabilisticVolumetrics(draws=5000).compute_hcpv(
        grv_dist={"min": 100.0, "ml": 120.0, "max": 150.0},
        ntg_dist={"min": 0.45, "ml": 0.60, "max": 0.72},
        phi_dist={"min": 0.18, "ml": 0.22, "max": 0.28},
        sw_dist={"min": 0.20, "ml": 0.30, "max": 0.42},
        fvf_dist={"min": 1.05, "ml": 1.10, "max": 1.18},
    ).to_dict()
    assert result["p10"] <= result["p50"] <= result["p90"]
    assert result["valid_draws"] > 0
    assert "tornado" in result
