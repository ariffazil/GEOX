"""Phase D Verification Gate — 8-defect SYNTH-DW-01 suite + clean control + SEP-1865 bundle."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import fastmcp

from geox.forensics.well_audit import run_well_forensic_audit
from geox_mcp.apps_well_forensic import APP_DIST_HTML, APP_MIME, APP_URI, register_well_forensic_app
from tests.fixtures.generate_synthetic_las_pack import generate_clean_control, generate_synth_dw_01

ALL_8_FAULTS = {
    "KB_DATUM_SHIFT",
    "UNIT_FACTOR_32808",
    "POROSITY_X100_MISMATCH",
    "SONIC_UNIT_HEADER_LIE",
    "SENTINEL_STUB_BLINDSPOT",
    "IDENTITY_TDR_FORMAT_DRIFT",
    "ROCK_PHYSICS_TRAP",
    "STRAT_AGE_INVERSION",
}


def test_synth_dw_01_detects_all_8_faults_zero_false_negatives(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GEOX_EARTHGRAPH_DB", str(tmp_path / "eg.db"))
    monkeypatch.setenv("GEOX_TELEMETRY_PATH", str(tmp_path / "telemetry.jsonl"))
    pack = generate_synth_dw_01(tmp_path / "synth_dw_01", seed=42)

    res = run_well_forensic_audit(pack, mode="forensic_audit")
    assert res["verdict"] == "QUARANTINE"
    found = set(res["structuredContent"]["data"]["fault_codes"])
    assert found == ALL_8_FAULTS, f"Missing faults: {ALL_8_FAULTS - found}"

    # Verify quantified evidence for key defects
    faults = res["structuredContent"]["data"]["faults"]
    assert abs(faults["KB_DATUM_SHIFT"]["lag_m"] - 30.0) <= 0.5
    assert faults["KB_DATUM_SHIFT"]["pearson_r"] >= 0.95
    assert faults["UNIT_FACTOR_32808"]["median"] > 6.0
    assert faults["POROSITY_X100_MISMATCH"]["median"] > 15.0
    assert faults["SONIC_UNIT_HEADER_LIE"]["header_unit"] == "US/M"
    assert len(faults["SENTINEL_STUB_BLINDSPOT"]["stub_files"]) == 3
    assert faults["IDENTITY_TDR_FORMAT_DRIFT"]["checkshot_flag_zero"] == 1
    assert faults["ROCK_PHYSICS_TRAP"]["nphi_nmr_sep_vv"] >= 0.18
    assert len(faults["ROCK_PHYSICS_TRAP"]["hypotheses"]) >= 3
    assert faults["STRAT_AGE_INVERSION"]["verdict"] == "HOLD"

    # Verify telemetry emitted and EarthGraph SQLite updated
    assert (tmp_path / "telemetry.jsonl").exists()
    assert (tmp_path / "eg.db").exists()


def test_clean_control_las_passes_with_zero_quarantine_flags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GEOX_EARTHGRAPH_DB", str(tmp_path / "eg_clean.db"))
    monkeypatch.setenv("GEOX_TELEMETRY_PATH", str(tmp_path / "tel_clean.jsonl"))
    clean = generate_clean_control(tmp_path / "synth_clean_01", seed=42)

    res = run_well_forensic_audit(clean, mode="forensic_audit")
    assert res["verdict"] == "PASS"
    assert res["structuredContent"]["data"]["quarantine_count"] == 0
    assert res["structuredContent"]["data"]["fault_codes"] == []


def test_mcp_app_metadata_resource_mime_size_and_zero_cdn() -> None:
    assert APP_DIST_HTML.exists(), f"Missing built Vite singlefile bundle: {APP_DIST_HTML}"
    raw = APP_DIST_HTML.read_bytes()
    assert len(raw) < 500 * 1024, f"Bundle too large: {len(raw)} bytes (>= 500 KiB)"
    html = raw.decode("utf-8")
    assert not re.search(r"<(?:script|link)\b[^>]+https?://", html, flags=re.I), "External CDN script/link found!"

    mcp = fastmcp.FastMCP("phase-d-probe")
    register_well_forensic_app(mcp)

    async def _probe():
        tools = await mcp.list_tools()
        resources = await mcp.list_resources()
        return tools, resources

    tools, resources = asyncio.run(_probe())
    pda = next(t for t in tools if t.name == "geox_well_pda")
    assert pda.meta and pda.meta.get("ui", {}).get("resourceUri") == APP_URI
    res_obj = next(r for r in resources if str(r.uri) == APP_URI)
    assert res_obj.mime_type == APP_MIME
