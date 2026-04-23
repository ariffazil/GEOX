"""
Verification Script: Sovereign Governance Sync (Harness v2)
Testing the 9-Harness Constraint Architecture in GEOX.
"""
import asyncio
from geox.wealth.wealth_score_kernel import geox_to_wealth_score

async def test_harness_governance():
    print("🜂 Starting Sovereign Harness Verification...")
    
    # Mock Evidence: High Entropy + High Carbon
    dirty_evidence = {
        "well_id": "STRESS_WELL_001",
        "claim_tag": "ESTIMATE",
        "entropy": 0.45,  # Threshold typically 0.3
        "carbon_intensity": 0.08, # Threshold 0.04
        "flags": ["HIGH_ENTROPY_SIGNAL"],
        "primary_result": {"hcpv_m3": 500000}
    }
    
    print("\n[SCENARIO 1] Auditing High-Entropy/High-Carbon Evidence...")
    result = await geox_to_wealth_score(dirty_evidence)
    
    print(f"Verdict: {result['verdict']}")
    print(f"Reason: {result.get('reason')}")
    print(f"Violations: {result.get('violations')}")
    print(f"Systemic Stress: {result.get('systemic_stress')}")
    
    if result['verdict'] == "VOID" and "CIVILIZATION_HARNESS_FAILURE" in result['violations']:
        print("✅ SUCCESS: Civilization Harness correctly blocked dirty capital.")
    else:
        print("❌ FAILURE: Harness failed to block.")

    # Mock Evidence: Chain violation
    print("\n[SCENARIO 2] Auditing Identity Chain Violation...")
    identity_violation = {
        "well_id": "WELL_002",
        "claim_tag": "OBSERVED",
        "entropy": 0.1,
        "primary_result": {"hcpv_m3": 100000}
    }
    result_identity = await geox_to_wealth_score(identity_violation, parent_chain_hash="INVALID_HASH")
    
    print(f"Verdict: {result_identity['verdict']}")
    print(f"Violations: {result_identity.get('violations')}")
    
    if "IDENTITY_CHAIN_VIOLATION" in result_identity.get("violations", []):
        print("✅ SUCCESS: Identity Harness correctly blocked broken chain.")
    else:
        print("❌ FAILURE: Identity Harness failed to block.")

if __name__ == "__main__":
    asyncio.run(test_harness_governance())
