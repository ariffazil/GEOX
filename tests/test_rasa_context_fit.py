"""RASA context-fit score tests.

RASA = evidence_credit × (1 − u_ambiguity), F7-humility capped at 0.90.
"""

from geox_core.core.ac_risk import compute_ac_risk_governed

BASE_KWARGS = {
    "transform_stack": [],
    "echo_score": 0.8,
    "truth_score": 0.9,
    "amanah_locked": True,
}


def test_rasa_disabled_when_not_present():
    result = compute_ac_risk_governed(
        u_ambiguity=0.2,
        evidence_credit=0.9,
        rasa_present=False,
        **BASE_KWARGS,
    )
    assert result.rasa_present is False
    assert result.rasa_context_fit == 0.0
    assert result.to_dict()["rasa_present"] is False
    assert result.to_dict()["rasa_context_fit"] == 0.0


def test_rasa_basic_computation():
    result = compute_ac_risk_governed(
        u_ambiguity=0.2,
        evidence_credit=0.9,
        rasa_present=True,
        **BASE_KWARGS,
    )
    assert result.rasa_present is True
    # 0.9 * (1 - 0.2) = 0.72
    assert round(result.rasa_context_fit, 4) == 0.72


def test_rasa_f7_humility_cap():
    """F7 HUMILITY: rasa_context_fit must never exceed 0.90."""
    result = compute_ac_risk_governed(
        u_ambiguity=0.0,
        evidence_credit=1.0,
        rasa_present=True,
        **BASE_KWARGS,
    )
    assert result.rasa_context_fit == 0.90


def test_rasa_zero_evidence():
    result = compute_ac_risk_governed(
        u_ambiguity=0.1,
        evidence_credit=0.0,
        rasa_present=True,
        **BASE_KWARGS,
    )
    assert result.rasa_context_fit == 0.0


def test_rasa_full_ambiguity():
    result = compute_ac_risk_governed(
        u_ambiguity=1.0,
        evidence_credit=0.9,
        rasa_present=True,
        **BASE_KWARGS,
    )
    assert result.rasa_context_fit == 0.0


def test_rasa_to_dict_rounding():
    result = compute_ac_risk_governed(
        u_ambiguity=0.3333,
        evidence_credit=0.7777,
        rasa_present=True,
        **BASE_KWARGS,
    )
    d = result.to_dict()
    assert "rasa_present" in d
    assert "rasa_context_fit" in d
    assert isinstance(d["rasa_context_fit"], float)
    assert 0.0 <= d["rasa_context_fit"] <= 0.90
