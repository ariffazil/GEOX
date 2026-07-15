"""
test_uncertainty.py — EGS Uncertainty Algebra Tests

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import pytest

from geox.egs.models.uncertainty import (
    ConfidenceGrade,
    DistributionType,
    DistributionUncertainty,
    IntervalUncertainty,
    ScenarioMember,
    ScenarioSet,
    UncertainValue,
    UncertaintyBudget,
    UncertaintyKind,
    UncertaintyNature,
)


class TestIntervalUncertainty:
    def test_create_interval(self):
        u = IntervalUncertainty(
            value=25.0,
            lower_bound=20.0,
            upper_bound=30.0,
            unit="percent",
        )
        assert u.value == 25.0
        assert u.range == 10.0
        assert u.kind == UncertaintyKind.INTERVAL

    def test_relative_uncertainty(self):
        u = IntervalUncertainty(value=100, lower_bound=80, upper_bound=120)
        assert u.relative_uncertainty == pytest.approx(0.2)

    def test_invalid_bounds(self):
        with pytest.raises(ValueError):
            IntervalUncertainty(value=25, lower_bound=30, upper_bound=20)

    def test_value_outside_bounds(self):
        with pytest.raises(ValueError):
            IntervalUncertainty(value=35, lower_bound=20, upper_bound=30)


class TestDistributionUncertainty:
    def test_normal_distribution(self):
        d = DistributionUncertainty(
            dist_type=DistributionType.NORMAL,
            mean=100.0,
            std=15.0,
            unit="percent",
        )
        assert d.kind == UncertaintyKind.DISTRIBUTION

    def test_normal_missing_params(self):
        with pytest.raises(ValueError, match="Normal requires mean and std"):
            DistributionUncertainty(dist_type=DistributionType.NORMAL, mean=100.0)

    def test_uniform_distribution(self):
        d = DistributionUncertainty(
            dist_type=DistributionType.UNIFORM,
            min_val=0.0,
            max_val=1.0,
        )
        assert d.min_val == 0.0
        assert d.max_val == 1.0

    def test_uniform_invalid_bounds(self):
        with pytest.raises(ValueError):
            DistributionUncertainty(dist_type=DistributionType.UNIFORM, min_val=10, max_val=5)

    def test_triangular(self):
        d = DistributionUncertainty(
            dist_type=DistributionType.TRIANGULAR,
            low_val=0.0,
            mode_val=0.5,
            high_val=1.0,
        )
        assert d.mode_val == 0.5

    def test_p10_p50_p90(self):
        d = DistributionUncertainty(
            dist_type=DistributionType.NORMAL,
            mean=100,
            std=15,
            p10=80.8,
            p50=100.0,
            p90=119.2,
        )
        assert d.p10_p50_p90 == (80.8, 100.0, 119.2)


class TestScenarioSet:
    def test_create_scenario_set(self):
        s1 = ScenarioMember(name="High case", probability=0.3, parameters={"porosity": 0.25})
        s2 = ScenarioMember(name="Base case", probability=0.5, parameters={"porosity": 0.20})
        s3 = ScenarioMember(name="Low case", probability=0.2, parameters={"porosity": 0.15})
        ss = ScenarioSet(scenarios=[s1, s2, s3], description="Porosity scenarios")
        assert len(ss.scenarios) == 3
        assert ss.scenarios[1].name == "Base case"

    def test_probability_sum_must_be_one(self):
        s1 = ScenarioMember(name="A", probability=0.5)
        s2 = ScenarioMember(name="B", probability=0.3)
        with pytest.raises(ValueError, match="probabilities must sum to 1.0"):
            ScenarioSet(scenarios=[s1, s2])

    def test_empty_scenarios(self):
        with pytest.raises(ValueError):
            ScenarioSet(scenarios=[])


class TestUncertainValue:
    def test_interval_uncertain_value(self):
        uv = UncertainValue(
            label="Porosity",
            value=0.20,
            uncertainty=IntervalUncertainty(value=0.20, lower_bound=0.15, upper_bound=0.25),
            grade=ConfidenceGrade.B,
            source="log analysis",
        )
        assert uv.nature == UncertaintyNature.EPISTEMIC
        assert uv.p50 == 0.20

    def test_distribution_uncertain_value(self):
        uv = UncertainValue(
            label="Permeability",
            value=100.0,
            uncertainty=DistributionUncertainty(
                dist_type=DistributionType.LOGNORMAL,
                mean=4.6,
                std=0.5,
                p50=100.0,
            ),
        )
        assert uv.p50 == 100.0

    def test_no_grade(self):
        uv = UncertainValue(
            label="Test",
            uncertainty=IntervalUncertainty(value=0, lower_bound=-1, upper_bound=1),
        )
        assert uv.grade == ConfidenceGrade.NOT_GRADED


class TestUncertaintyBudget:
    def test_budget(self):
        b = UncertaintyBudget(description="Volume uncertainty budget")
        uv = UncertainValue(
            label="Area",
            uncertainty=IntervalUncertainty(value=100, lower_bound=80, upper_bound=120),
        )
        b.add("area", uv)
        assert b.get("area") is not None
        assert b.get("nonexistent") is None
