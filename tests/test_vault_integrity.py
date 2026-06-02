import os
import json
import hashlib
from datetime import datetime, timezone


def test_vault_write_and_read(tmp_path):
    """Test vault write+read+verify using pytest's tmp_path (no repo pollution).

    Previous version hardcoded /root/geox/999_vault which:
      1. Polluted git status with seal_*.json artifacts every run
      2. Failed in CI where the runner user can't write to /root/geox
    """
    vault_dir = tmp_path / "999_vault"
    vault_dir.mkdir(exist_ok=True)

    # Create a mock sealed Earth claim
    claim = {
        "earth_object_id": "PROSPECT-ALPHA-01",
        "claim_state": "SEALED",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sealed_by": "arifOS-GEOX-Clerk",
        "data": {
            "GCoS": 0.45,
            "dominant_risk": "Charge Timing",
            "decision": "Acquire 3D Seismic",
        },
    }

    # Hash the claim for sealing
    claim_str = json.dumps(claim, sort_keys=True)
    seal_hash = hashlib.sha256(claim_str.encode()).hexdigest()
    claim["vault_hash"] = seal_hash

    file_path = vault_dir / f"seal_{seal_hash[:12]}.json"

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
    # Allow standalone run with a temp vault dir
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        ok = test_vault_write_and_read(Path(td))
        print("Vault999 Integrity Check:", "PASSED" if ok else "FAILED")
