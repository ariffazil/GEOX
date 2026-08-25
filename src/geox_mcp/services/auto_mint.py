"""
auto_mint — Gate-Pass → Claim Corpus Flywheel (v1)
══════════════════════════════════════════════════
Forged 2026-08-21 from LWM→LEM musyawarah convergence (333-AGI + ASI + F13 arc).

Doctrine:
    governed loop → corpus → better predictor → more decisions → bigger corpus.
    Every gate-passing tool output (local_verdict=QUALIFIED_CANDIDATE) becomes a
    DRAFT claim with provenance, epistemic label, and evidence receipt —
    automatically. No agent required to remember.

GUARDS (constitutional):
  - Mints DRAFT only. NEVER seals. Sealing stays with arifOS (voxel_state gate,
    ADR-008 well_constrained check). Local max = QUALIFIED_CANDIDATE.
  - Dedup by source_fingerprint: identical inputs never mint twice (F4: ΔS ≤ 0 —
    corpus accumulates decisions, not noise).
  - Kill switch: GEOX_AUTO_MINT=0 disables without code revert (F1 reversible).
  - Fail-open: any mint failure is logged and swallowed. The parent tool ALWAYS
    returns its own result. The flywheel must never break the work.

Wiring (3 lines, any gate-passing tool):
    from geox_mcp.services.auto_mint import mint_from_gate_pass
    mint = await mint_from_gate_pass("tool_name", result, session_id, actor_id)
    if mint: result["_auto_mint"] = mint

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger("geox.auto_mint")

AUTO_MINT_VERSION = "auto-mint:v1"
DEFAULT_DB_PATH = "/root/geox/earth_memory.db"

# Tools that emit gate-passing verdicts. Extending = append here + 3-line wire.
SUPPORTED_TOOLS = {
    "geox_contrast_metabolize": "trap",
    # future: "geox_petrophysics": "net_pay", "geox_prospect": "structure", ...
}


def _db_path() -> Path:
    return Path(os.environ.get("GEOX_EARTH_MEMORY_DB", DEFAULT_DB_PATH))


def _enabled() -> bool:
    return os.environ.get("GEOX_AUTO_MINT", "1") == "1"


def _fingerprint(tool_name: str, result: dict[str, Any]) -> str | None:
    """Content-addressable identity of a gate-pass result (stable, not timestamped)."""
    try:
        stage3 = result.get("stage3_classify") or {}
        hypotheses = stage3.get("hypotheses") or result.get("hypotheses") or []
        stage1 = result.get("stage1_isolate") or {}
        canon = {
            "tool": tool_name,
            "mode": result.get("mode"),
            "anomaly_count": stage1.get("anomaly_count"),
            "hypotheses": hypotheses,  # full hypothesis dicts — deterministic output
        }
        raw = json.dumps(canon, sort_keys=True, default=str, separators=(",", ":"))
        return "amf_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    except Exception:
        return None


def _already_minted(fingerprint: str, db_path: Path) -> str | None:
    """Return existing claim id if this fingerprint is already in the corpus."""
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT id FROM earth_memory WHERE payload LIKE ? LIMIT 1",
                (f'%"source_fingerprint": "{fingerprint}"%',),
            ).fetchone()
        return row[0] if row else None
    except sqlite3.Error:
        return None


def _extract_claim(result: dict[str, Any]) -> tuple[str, str] | None:
    """Extract (claim_text, note) from a gate-pass result. Returns None if nothing claimable."""
    stage3 = result.get("stage3_classify") or {}
    hypotheses = stage3.get("hypotheses") or []
    if not hypotheses:
        return None
    parts = []
    for i, h in enumerate(hypotheses[:3], 1):
        if isinstance(h, dict):
            text = h.get("hypothesis") or h.get("text") or h.get("description") or json.dumps(h, default=str)[:120]
            depth = h.get("depth_m") or h.get("top_m")
            tag = f" at ~{depth} m" if depth is not None else ""
        else:
            text, tag = str(h), ""
        parts.append(f"H{i}: {text}{tag}")
    claim_text = (
        "Auto-minted stratigraphic contrast hypotheses (normal-incidence profile): "
        + "; ".join(parts)
        + ". Pre-stack AVO and well ties required for promotion beyond QUALIFIED_CANDIDATE."
    )
    return claim_text, stage3.get("note", "")


async def mint_from_gate_pass(
    tool_name: str,
    result: dict[str, Any],
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any] | None:
    """Mint a DRAFT claim from a gate-passing tool result.

    Returns mint info dict on success, {"skipped": reason} on no-op, None when
    disabled. Never raises — fail-open by contract.
    """
    try:
        if not _enabled():
            return None
        if tool_name not in SUPPORTED_TOOLS:
            return {"skipped": f"tool {tool_name} not in auto-mint registry"}
        if not result.get("ok") or result.get("local_verdict") != "QUALIFIED_CANDIDATE":
            return {"skipped": "result is not a gate-passed QUALIFIED_CANDIDATE"}
        if result.get("mode") == "synthetic":
            # A fixture is not a decision. Sovereign corpus accumulates real
            # evidence only — synthetic runs must never launder into claims (F2).
            return {"skipped": "synthetic fixture — real evidence only"}

        fingerprint = _fingerprint(tool_name, result)
        if not fingerprint:
            return {"skipped": "fingerprint unavailable"}

        db_path = _db_path()
        existing = _already_minted(fingerprint, db_path)
        if existing:
            return {"skipped": "dedup", "existing_claim_id": existing, "fingerprint": fingerprint}

        extracted = _extract_claim(result)
        if not extracted:
            return {"skipped": "no claimable hypotheses in result"}
        claim_text, note = extracted

        claim_type = cast(Any, SUPPORTED_TOOLS[tool_name])
        evidence = result.get("_evidence_receipt") or {}
        evidence_ids = [f"{tool_name}:{evidence.get('sha256', 'no-receipt')}"]

        from geox_core.services.asset_memory import EarthMemoryStore
        from geox_mcp.tools.claims import _build_claim_envelope

        claim_id = f"clm_{hashlib.sha256(fingerprint.encode()).hexdigest()[:16]}"
        payload = _build_claim_envelope(
            claim_id=claim_id,
            claim_type=claim_type,
            claim_text=claim_text,
            truth_class="INTERPRETATION",  # stage3 epistemic label is INT — mirrors source
            uncertainty=None,  # honest: no fabricated envelope; attach later via attach_evidence
            evidence_ids=evidence_ids,
            alternatives=None,
            provenance=f"{AUTO_MINT_VERSION}:{tool_name}",
            authority="GEOX_AUTO_MINT",
            extra_metadata={
                "auto_mint": True,
                "source_tool": tool_name,
                "source_fingerprint": fingerprint,
                "source_note": note,
                "epistemic_label": "INT",
                "session_id": session_id,
                "actor_id": actor_id,
                "local_verdict_at_mint": "QUALIFIED_CANDIDATE",
            },
        )

        store = EarthMemoryStore(db_path=str(db_path))
        record_id = store.draft_claim(asset_id=claim_type, payload=payload)

        logger.info(f"auto-mint: {claim_id} ({fingerprint}) → earth_memory[{record_id}]")
        return {
            "minted": True,
            "claim_id": claim_id,
            "earth_memory_id": record_id,
            "fingerprint": fingerprint,
            "state": "DRAFT",  # arifOS seals — never this module
        }
    except Exception as exc:  # fail-open: flywheel never breaks the tool
        logger.warning(f"auto-mint failed (fail-open): {exc}")
        return None
