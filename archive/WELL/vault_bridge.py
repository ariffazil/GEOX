"""WELL → VAULT999 Bridge
DITEMPA BUKAN DIBERI

Role: Immutable biological anchoring with High-Signal Filtering.
Axiom: WELL informs, arifOS judges, A-FORGE executes.
W0: WELL holds a mirror, not a veto. Operator sovereignty is invariant.

Env vars:
- WELL_STATE_PATH   — path to WELL state.json (default: /root/WELL/state.json)
- VAULT999_HOST     — VAULT999 PostgreSQL host (default: 10.60.231.47)
- VAULT999_WELL_TABLE — table name for WELL events (default: well_events)
- WELL_VAULT_FALLBACK — if set, write local jsonl even when DB unreachable

Status: SCAFFOLD — requires VAULT999 DB to be network-reachable
"""

import json
import hashlib
import datetime
import os
from pathlib import Path

WELL_STATE_PATH = Path(os.environ.get("WELL_STATE_PATH", "/root/WELL/state.json"))
VAULT999_HOST = os.environ.get("VAULT999_HOST", "10.60.231.47")
VAULT999_WELL_TABLE = os.environ.get("VAULT999_WELL_TABLE", "well_events")
WELL_VAULT_FALLBACK = os.environ.get("WELL_VAULT_FALLBACK", "")

def get_last_anchored_score():
    """Read last well_score from VAULT999 via PostgreSQL or local fallback."""
    fallback_path = Path(f"/root/arifOS/core/vault999/well_ledger.jsonl")
    
    # Try PostgreSQL first
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=VAULT999_HOST,
            database="vault999",
            user="vault999_writer",
            password=os.environ.get("VAULT999_PASSWORD", ""),
            timeout=3,
        )
        row = await conn.fetchrow(
            f"SELECT well_score FROM {VAULT999_WELL_TABLE} ORDER BY epoch DESC LIMIT 1"
        )
        await conn.close()
        return row["well_score"] if row else None
    except Exception:
        pass
    
    # Fallback to local jsonl
    if fallback_path.exists():
        try:
            with open(fallback_path, "rb") as f:
                f.seek(-2, 2)
                while f.read(1) != b"\n":
                    f.seek(-2, 1)
                last_line = f.readline().decode()
                return json.loads(last_line).get("well_score")
        except Exception:
            return None
    return None


def bridge_to_vault(force: bool = False) -> dict:
    """Write WELL state to VAULT999 if high-signal change detected."""
    try:
        with open(WELL_STATE_PATH, "r") as f:
            state = json.load(f)
    except Exception as e:
        return {"status": "ERROR", "message": f"READ_FAILED: {str(e)}"}

    current_score = state.get("well_score", 0)
    last_score = get_last_anchored_score()
    violations = state.get("floors_violated", [])

    # High-Signal Filter: only write if meaningful delta or degraded state
    is_degraded = len(violations) > 0
    is_low_capacity = current_score < 70
    is_significant_delta = last_score is None or abs(current_score - last_score) >= 10

    if not (is_degraded or is_low_capacity or is_significant_delta or force):
        return {"status": "SKIPPED", "message": "Signal-to-noise suppressed. Ledger remains clean."}

    payload = {
        "vault_type": "well_event",
        "epoch": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "well_score": current_score,
        "status": "DEGRADED" if is_degraded else "LOW" if is_low_capacity else "STABLE",
        "violations": violations,
        "w0_assertion": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "trigger": "VIOLATION" if is_degraded else "CAPACITY" if is_low_capacity else "DELTA" if is_significant_delta else "MANUAL",
    }
    payload["hash"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    # Try PostgreSQL write first
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=VAULT999_HOST,
            database="vault999",
            user="vault999_writer",
            password=os.environ.get("VAULT999_PASSWORD", ""),
            timeout=5,
        )
        await conn.execute(
            f"""INSERT INTO {VAULT999_WELL_TABLE} 
                (vault_type, epoch, well_score, status, violations, w0_assertion, trigger, hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            payload["vault_type"], payload["epoch"], payload["well_score"],
            payload["status"], payload["violations"], payload["w0_assertion"],
            payload["trigger"], payload["hash"],
        )
        await conn.close()
        return {"status": "SUCCESS", "payload": payload, "write": "vault999_db"}
    except Exception as e:
        pass

    # Fallback: local jsonl
    fallback_path = Path(f"/root/arifOS/core/vault999/well_ledger.jsonl")
    try:
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        with open(fallback_path, "a") as f:
            f.write(json.dumps(payload) + "\n")
        return {"status": "SUCCESS", "payload": payload, "write": "local_fallback"}
    except Exception as e:
        return {"status": "ERROR", "message": f"VAULT_WRITE_FAILED: {str(e)}"}


if __name__ == "__main__":
    import sys
    force_sync = "--force" in sys.argv
    result = bridge_to_vault(force=force_sync)
    print(json.dumps(result, indent=2))
