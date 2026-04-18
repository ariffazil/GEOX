from geox.core.sensitivity import SensitivitySweep
from geox.geox_mcp.server import geox_prospect_evaluate


def test_sensitivity_sweep_returns_ranked_cases():
    result = SensitivitySweep().run(
        {
            "u_ambiguity": 0.35,
            "evidence_credit": 0.75,
            "echo_score": 0.10,
            "truth_score": 0.99,
            "amanah_locked": False,
            "irreversible_action": False,
            "transform_stack": ["normalize", "ac_risk"],
        }
    ).to_dict()
    assert result["cases"]
    assert result["cases"][0]["sensitivity_index"] >= 0.0


def test_existing_prospect_tool_runs_sensitivity():
    result = geox_prospect_evaluate(
        "BEK-2-PROSPECT",
        u_ambiguity=0.3,
        transform_stack=["normalize", "ac_risk"],
        evidence_credit=0.8,
        truth_score=0.99,
        echo_score=0.1,
    )
    assert "sensitivity" in result
