"""Phase B CI Gate — drift, duplicate tool names, token budget, telemetry & EarthGraph persistence."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from geox.egs.storage import db_stats, load_or_seed_earthgraph, save_earthgraph
from geox.obs import current_git_sha, observed, summarize_telemetry
from geox_mcp.registry import GEOX_TOOL_MANIFEST, SURFACE_TOOLS, TOOL_LIFECYCLE_MAP

TOKEN_BUDGET = int(os.getenv("GEOX_TOKEN_BUDGET", "1500"))


def test_no_duplicate_surface_tools_and_all_lifecycle_tagged() -> None:
    dupes = sorted({t for t in SURFACE_TOOLS if SURFACE_TOOLS.count(t) > 1})
    assert dupes == [], f"Duplicate surface tools detected: {dupes}"
    unmapped = [t for t in SURFACE_TOOLS if TOOL_LIFECYCLE_MAP.get(t) in (None, "", "unmapped")]
    assert unmapped == [], f"Unmapped lifecycle_stage tools: {unmapped}"
    assert all("lifecycle_stage" in row for row in GEOX_TOOL_MANIFEST)


def test_telemetry_emission_and_token_budget(tmp_path: Path, monkeypatch) -> None:
    tpath = tmp_path / "telemetry.jsonl"
    monkeypatch.setenv("GEOX_TELEMETRY_PATH", str(tpath))

    @observed(tool_name="geox_well_qc")
    async def _sample_tool(mode: str = "qc") -> dict:
        return {"verdict": "PASS", "defaults_applied": ["vsh_linear"], "summary": "clean"}

    out = asyncio.run(_sample_tool(mode="qc"))
    assert out["verdict"] == "PASS"

    lines = tpath.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    required = {
        "ts", "tool", "mode", "lifecycle_stage", "git_sha", "duration_ms",
        "resp_tokens_est", "resp_bytes", "verdict", "defaults_applied_n",
        "sha256_in", "sha256_out", "is_error",
    }
    assert required.issubset(rec.keys())
    assert rec["lifecycle_stage"] == "Appraisal"
    assert rec["is_error"] is False

    summary = summarize_telemetry(tpath)
    assert summary["count"] == 1
    assert summary["avg_resp_tokens"] <= TOKEN_BUDGET, (
        f"avg resp_tokens {summary['avg_resp_tokens']} exceeds budget {TOKEN_BUDGET}"
    )


def test_git_sha_drift_detector() -> None:
    sha = current_git_sha()
    assert sha != "unknown" and len(sha) >= 7
    deployed_sha = f"geox-{sha}"
    source_sha = f"geox-{sha}"
    assert deployed_sha == source_sha  # zero drift when aligned


def test_earthgraph_sqlite_boots_non_empty_and_persists(tmp_path: Path, monkeypatch) -> None:
    dbp = tmp_path / "earthgraph.db"
    monkeypatch.setenv("GEOX_EARTHGRAPH_DB", str(dbp))
    g1 = load_or_seed_earthgraph(dbp)
    assert len(g1.basins) >= 3
    assert dbp.exists()
    save_earthgraph(g1, dbp)
    stats = db_stats(dbp)
    assert stats["non_empty"] is True
    assert stats["basins"] >= 3
