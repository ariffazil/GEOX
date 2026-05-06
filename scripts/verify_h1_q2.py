from geox.skills.subsurface.petro.las_ingest import geox_ingest_las_tool
import json

def test_refusal():
    print("--- TESTING CONSTITUTIONAL REFUSAL: IDENTITY MISMATCH ---")
    # Requesting 'CORRECT_WELL' but file has 'IDENTITY_MISMATCH_TEST'
    result = geox_ingest_las_tool(path="/root/geox/tests/fixtures/bad_identity.las", asset_id="CORRECT_WELL")
    print(json.dumps(result, indent=2))
    
    if result.get("status") == "888_HOLD":
        print("\n✅ SUCCESS: Refusal Triggered as Expected.")
    else:
        print("\n❌ FAILURE: System accepted mismatched identity.")

if __name__ == "__main__":
    test_refusal()
