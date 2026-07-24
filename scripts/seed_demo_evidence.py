#!/usr/bin/env python3
"""Seed demo LAS into GEOX artifact registry for generate/verify demos (Batch E).

Does NOT invent geology — only registers on-disk DEMO fixtures with QC=pass
so geox_petrophysics(mode=generate) can resolve evidence_refs.

Usage:
  PYTHONPATH=src python3 scripts/seed_demo_evidence.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geox_mcp.tools.kernel._registry import (  # noqa: E402
    _get_artifact,
    _persist_artifact_registry,
    _record_latest_qc,
    _register_artifact,
    _artifact_store,
)


def main() -> int:
    reg_path = ROOT / "resources" / "demo_wells.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    seeded = []
    for w in reg.get("wells") or []:
        wid = w["well_id"]
        las = ROOT / w["las_path"]
        if not las.is_file():
            print(f"SKIP {wid}: missing {las}")
            continue
        # Register under canonical id + demo: alias used as evidence_ref
        for ref in {wid, f"demo:{wid}"}:
            _register_artifact(
                ref,
                curves=["GR", "RT", "RHOB", "NPHI", "DT"],
                las_path=str(las),
                claim_state="RAW_OBSERVATION",
                diagnostics={
                    "data_class": w.get("data_class"),
                    "geography": w.get("geography"),
                    "seed": "seed_demo_evidence.py",
                    "seal_status": "NOT_SEALED",
                },
                source_uri=str(las),
                artifact_type="well_log",
            )
            _record_latest_qc(
                ref,
                {
                    "qc_passed": True,
                    "qc_overall": "PASS",
                    "flags": [],
                    "limitations": ["DEMO seed QC — not a field seal"],
                    "claim_state": "RAW_OBSERVATION",
                },
            )
            entry = _get_artifact(ref)
            if entry is not None:
                entry["data_class"] = w.get("data_class")
                _artifact_store[ref] = entry
        seeded.append(wid)
        print(f"SEED {wid} → {las}")

    _persist_artifact_registry()
    print(
        f"Done. Seeded {len(seeded)} wells. "
        f"Registry keys sample: {list(_artifact_store.keys())[:8]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
