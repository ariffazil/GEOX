from geox.geox_mcp.fastmcp_server import arifos_compute_risk


def test_advisory_mode():
    print("--- TESTING SUNNAH: ADVISORY MODE ---")
    
    # We deliberately trigger an F9 Anti-Hantu block by using "I feel"
    result = arifos_compute_risk(
        u_ambiguity=0.5,
        transform_stack=[],
        model_text="I feel that this reservoir is very good.",
        advisory_mode=True
    )
    
    print("Verdict:", result["verdict"])
    print("Explanation:", result["explanation"])
    
    if result["verdict"] == "ADVISORY_BLOCK":
        print("✅ SUCCESS: Advisory Mode downgraded the hard BLOCK to an ADVISORY_BLOCK.")
    else:
        print("❌ FAILURE: Advisory Mode failed to bypass the hold.")

if __name__ == "__main__":
    test_advisory_mode()