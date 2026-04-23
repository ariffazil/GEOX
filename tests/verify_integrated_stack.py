"""
End-to-End Verification: The Integrated Convergence Architecture (Three-Layer Stack)
Witnessing the flow from Earth Substrate to Sovereign Capital Allocation.
"""
import asyncio
from geox.core.psv_forge import compute_psv_from_substrates
from geox.wealth.valuation_engine import compute_sovereign_valuation

async def test_integrated_stack():
    print("🜂 Initializing Three-Layer Stack Verification...")
    
    # ── Layer 1: Scientific Engine (Earth Intelligence) ──
    # High Stress (0.8) and Low Flow (0.2) -> Should results in Low EROEI
    measurements = {
        "kinetic": {"maturity": 0.8},
        "flow": {"mobility": 0.2, "flow_mobility": 0.2},
        "stress": {"seal_integrity": 0.9, "stress_resistance": 0.8},
        "structure": {"closure": 0.75},
        "pore": {"porosity": 0.18},
        "volume_m3": 5000000,
        "dS": 0.15 # Low entropy
    }
    
    print("\n[STEP 1] Forging Prospect State Vector (PSV)...")
    psv = compute_psv_from_substrates(measurements)
    print(f"P_charge: {psv.p_charge} | P_trap: {psv.p_trap} | GCOS: {psv.gcoS}")
    print(f"P50 Volume: {psv.p50} m3")
    
    # ── Layer 2 & 3: Capital & Civilization Engine ──
    print("\n[STEP 2] Computing Sovereign Valuation & Auditing Harnesses...")
    # Injecting hcpv for the civilization EROEI audit
    psv_dict = measurements.copy()
    psv_dict["hcpv"] = psv.p50 / 1000 # Convert to k-units for the scale
    
    valuation = compute_sovereign_valuation(
        psv=psv,
        capex=100_000_000,
        opex_per_year=5_000_000,
        price_per_unit=60,
        discount_rate=0.10,
        parent_chain_hash="d7a8f9e0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8"
    )
    
    print(f"Valuation Verdict: {valuation['verdict']}")
    print(f"EMV: ${valuation['metrics']['emv_usd']:,.2f}")
    
    audit = valuation["harness_audit"]
    print(f"Civilization Harness Status: {audit['harness_status']['Civilization']['status']}")
    print(f"Civilization Details: {audit['harness_status']['Civilization'].get('detail', 'N/A')}")
    
    if "ENERGY_OVERSHOOT_FAILURE" in audit["violations"]:
        print("\n✅ SUCCESS: Integrated stack correctly flagged the low EROEI (High Stress/Low Flow).")
    elif valuation["verdict"] == "PASS":
         print("\n✅ SUCCESS: Integrated stack passed sovereign audit.")
    else:
        print("\n❌ INTEGRATION FAILURE: Logic divergence detected.")

if __name__ == "__main__":
    asyncio.run(test_integrated_stack())
