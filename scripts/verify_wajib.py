import os
import sqlite3

from geox.skills.subsurface.petro.las_ingest import geox_ingest_las_tool


def test_wajib_forge():
    print("--- TESTING WAJIB #1 (Ledger) and WAJIB #5 (Artefact) ---")
    
    # Ingest a known good LAS file (using one from fixtures if it exists, or smoke test)
    las_path = "/root/geox/tests/fixtures/geox_smoke_test.las"
    
    result = geox_ingest_las_tool(path=las_path)
    
    # 1. Check Artefact
    artefact_path = result.get("vault_receipt", {}).get("artefact_path")
    if artefact_path and os.path.exists(artefact_path):
        print(f"✅ WAJIB 5 SUCCESS: Artefact emitted at {artefact_path}")
    else:
        print("❌ WAJIB 5 FAILURE: Artefact missing or not linked.")
        print(result)

    # 2. Check Ledger
    try:
        with sqlite3.connect("/root/geox/asset_memory.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT well_id, vault_receipt_hash FROM well_ingestion_ledger ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row and row[1] == result.get("vault_receipt", {}).get("hash"):
                print(f"✅ WAJIB 1 SUCCESS: Ingestion anchored in Ledger. Well: {row[0]}")
            else:
                print("❌ WAJIB 1 FAILURE: DB Record mismatch or missing.")
    except Exception as e:
         print(f"❌ WAJIB 1 FAILURE: DB Error: {e}")

if __name__ == "__main__":
    test_wajib_forge()
