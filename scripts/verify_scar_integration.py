from geox.core.ac_risk import compute_ac_risk_governed
import json

def test_ac_risk_scar_enforcement():
    print("--- TESTING WAJIB F12 ENFORCEMENT IN AC_RISK ---")
    
    # Normally this would be a low-risk, PROCEED calculation.
    # We provide perfect evidence and truth scores.
    result = compute_ac_risk_governed(
        u_ambiguity=0.1,
        transform_stack=["test"],
        evidence_credit=0.9,
        echo_score=0.9,
        truth_score=0.9,
        amanah_locked=True,
        prospect_context={"context_tags": ["BASIN_ALPHA"]} # This should hit the scar we just canonized!
    )
    
    print("\nResult Verdict: ", result.verdict)
    print("Explanation: ", result.explanation)
    print("Floor Violations: ", result.floor_violations)
    
    if result.verdict == "HOLD" and any("F12_SCAR" in v for v in result.floor_violations):
        print("\n✅ SUCCESS: AC_Risk engine successfully caught the F12_SCAR and enforced an 888_HOLD despite mathematically low risk.")
    else:
        print("\n❌ FAILURE: Engine bypassed the scar.")

if __name__ == "__main__":
    test_ac_risk_scar_enforcement()
