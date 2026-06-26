import json

from geox.core.scar_ledger import ScarLedger


def test_scar_canonisation():
    print("--- TESTING WAJIB F12: SCAR CANONISATION ---")
    
    ledger = ScarLedger()
    
    # 1. Canonize a historical scar
    print("1. Canonizing a historical scar...")
    scar_id = ledger.canonize_scar(
        context_tag="BASIN_ALPHA",
        failed_assumption="Assumed continuous blanket sand based on 2D seismic.",
        consequence="Well Alpha-1 encountered strat-pinchout. Total loss.",
        enforced_rule="Maximum reservoir presence COS capped at 0.6 unless bounded by 3D seismic."
    )
    print(f"   ✅ Scar permanently recorded. (ID: {scar_id})")
    
    # 2. A new team tries to evaluate a prospect in Basin Alpha
    print("\n2. New team evaluating 'Prospect Beta' in BASIN_ALPHA...")
    active_tags = ["BASIN_ALPHA", "DEEPWATER"]
    
    # 3. System audits against Scars
    triggered_scars = ledger.audit_against_scars(active_tags)
    
    if triggered_scars:
        print("   🛑 SCAR ECHO TRIGGERED! The system remembers:")
        print(json.dumps(triggered_scars, indent=2))
        print("\n   => GEOX Enforces: Team must prove 3D seismic exists or risk is capped.")
        print("✅ WAJIB F12 SUCCESS: Institutional memory enforced.")
    else:
        print("❌ WAJIB F12 FAILURE: System forgot the scar.")

if __name__ == "__main__":
    test_scar_canonisation()
