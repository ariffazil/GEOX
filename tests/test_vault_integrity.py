import os
import json
import hashlib
from datetime import datetime, timezone

VAULT_DIR = "/root/geox/999_vault"

def test_vault_write_and_read():
    if not os.path.exists(VAULT_DIR):
        os.makedirs(VAULT_DIR, exist_ok=True)
    
    # Create a mock sealed Earth claim
    claim = {
        "earth_object_id": "PROSPECT-ALPHA-01",
        "claim_state": "SEALED",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sealed_by": "arifOS-GEOX-Clerk",
        "data": {
            "GCoS": 0.45,
            "dominant_risk": "Charge Timing",
            "decision": "Acquire 3D Seismic"
        }
    }
    
    # Hash the claim for sealing
    claim_str = json.dumps(claim, sort_keys=True)
    seal_hash = hashlib.sha256(claim_str.encode()).hexdigest()
    claim["vault_hash"] = seal_hash
    
    file_path = os.path.join(VAULT_DIR, f"seal_{seal_hash[:12]}.json")
    
    # Write to vault
    try:
        with open(file_path, "w") as f:
            json.dump(claim, f, indent=2)
        print(f"✅ Successfully wrote sealed claim to vault: {file_path}")
    except Exception as e:
        print(f"❌ Failed to write to vault: {e}")
        return False
        
    # Read from vault
    try:
        with open(file_path, "r") as f:
            loaded_claim = json.load(f)
        
        # Verify hash
        loaded_hash = loaded_claim.pop("vault_hash")
        loaded_str = json.dumps(loaded_claim, sort_keys=True)
        verified_hash = hashlib.sha256(loaded_str.encode()).hexdigest()
        
        if loaded_hash == verified_hash:
            print(f"✅ Successfully read and verified sealed claim from vault.")
            return True
        else:
            print(f"❌ Hash mismatch in vault record.")
            return False
    except Exception as e:
        print(f"❌ Failed to read from vault: {e}")
        return False

if __name__ == "__main__":
    print("Testing Vault999 Integrity for GEOX Earth Claims...")
    success = test_vault_write_and_read()
    if success:
        print("Vault999 Integrity Check: PASSED")
        exit(0)
    else:
        print("Vault999 Integrity Check: FAILED")
        exit(1)
