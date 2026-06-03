"""
MCP wrapper for LAS ingestion.
"""

from __future__ import annotations

from geox_core.core.governed_output import classify_claim_tag, make_vault_receipt
from geox_core.services.las_ingestor import LASIngestor, ConstitutionalRefusal
from geox_core.core.truth_ledger import TruthLedger
from geox_core.core.artefact_emission import ArtefactEmitter


def geox_ingest_las_tool(path: str, asset_id: str | None = None, chunk_size: int = 200) -> dict:
    try:
        result_obj = LASIngestor().ingest(path=path, asset_id=asset_id, chunk_size=chunk_size)
        manifest = result_obj.to_dict()
        manifest["claim_tag"] = classify_claim_tag(
            0.8 if manifest["qcfail_count"] == 0 else 0.55, hold_enforced=manifest["qcfail_count"] > 0
        )

        manifest["vault_receipt"] = make_vault_receipt(
            "geox_ingest_las", manifest, verdict="HOLD" if manifest["qcfail_count"] > 0 else "SEAL"
        )

        # WAJIB #1 & #5: Truth anchoring and Artefact Emission (Final Boundary)
        try:
            artefact_path = ArtefactEmitter().emit_well_ingestion_report(manifest)
            manifest["vault_receipt"]["artefact_path"] = artefact_path
            TruthLedger().anchor_ingestion(manifest)
        except Exception as e:
            manifest["limitations"].append(f"Artefact/Ledger Failure: {str(e)}")

        return manifest
    except ConstitutionalRefusal as ref:
        return {
            "status": "888_HOLD",
            "verdict": "VOID",
            "reason": f"CONSTITUTIONAL REFUSAL: {ref.reason}",
            "evidence": ref.evidence,
            "claim_tag": "UNKNOWN",
            "hold_enforced": True,
            "suitability": "void",
            "qc_prerequisite_met": False,
            "vault_receipt": make_vault_receipt("geox_ingest_las", {"refusal": str(ref)}, verdict="VOID"),
        }
    except Exception as exc:
        return {"status": "ERROR", "reason": str(exc), "claim_tag": "UNKNOWN", "hold_enforced": True}
