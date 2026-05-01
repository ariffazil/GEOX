"""
tests/test_geox_well_hardening.py — GEOX MCP Well-Log Hardening Suite
═══════════════════════════════════════════════════════════════════════

8 regression tests (A–H) covering:
  A. Local LAS ingest succeeds and registers artifact
  B. URL LAS fetch (mocked) ingest succeeds
  C. Missing file returns FILE_NOT_FOUND error
  D. Bad URL returns URL_FETCH_FAILED error
  E. geox_data_qc_bundle fails closed for unregistered artifact_ref (Bug 3 regression)
  F. geox_data_qc_bundle passes for registered artifact_ref (positive path)
  G. geox_subsurface_generate_candidates fails closed for unregistered refs (Bug 4 regression)
  H. geox_well_correlation_panel returns ERROR when all LAS paths are invalid (Bug 2 regression)

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure repo root is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Path to LAS smoke test fixture
SMOKE_LAS = str(Path(__file__).parent / "fixtures" / "geox_smoke_test.las")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _reset_registry():
    """Clear the in-memory artifact registry between tests."""
    from contracts.tools.unified_13 import _artifact_registry, _well_curves_registry, _artifact_store
    _artifact_registry.clear()
    _well_curves_registry.clear()
    _artifact_store.clear()


def _run(coro):
    """Run a coroutine synchronously (test helper)."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ─── Test A: Local LAS ingest succeeds ───────────────────────────────────────

def test_A_local_las_ingest_succeeds(tmp_path):
    """A: geox_data_ingest_bundle with a valid local LAS file must succeed
    and register the artifact in the in-memory store."""
    _reset_registry()

    # Wire up a minimal FastMCP so register_unified_tools can register tools
    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools, _artifact_exists

    mcp = FastMCP(name="test_geox")
    register_unified_tools(mcp)

    # Grab the registered tool and call it
    async def run():
        return await mcp.call_tool("geox_data_ingest_bundle", {
            "source_uri": SMOKE_LAS,
            "source_type": "well",
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text) if hasattr(result.content[0], "text") else result

    # Engine may return a nested dict in content[0].text
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    # Accept both direct dict and nested wrapper
    status = data.get("status") or data.get("execution_status", "")
    assert status != "ERROR", f"Expected success, got ERROR: {data}"
    # Artifact must be registered
    derived_id = Path(SMOKE_LAS).stem
    assert _artifact_exists(derived_id), f"Expected '{derived_id}' in registry after ingest"


# ─── Test B: URL LAS fetch (mocked) succeeds ─────────────────────────────────

def test_B_url_las_fetch_mocked_succeeds(tmp_path):
    """B: geox_data_ingest_bundle with HTTPS URL must download to tmp, ingest,
    and register. Uses monkeypatched urllib.request.urlretrieve."""
    _reset_registry()

    import shutil
    import urllib.request

    def fake_retrieve(url, dest):
        shutil.copyfile(SMOKE_LAS, dest)

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools, _artifact_exists

    mcp = FastMCP(name="test_geox_url")
    register_unified_tools(mcp)

    with patch("urllib.request.urlretrieve", side_effect=fake_retrieve):
        async def run():
            return await mcp.call_tool("geox_data_ingest_bundle", {
                "source_uri": "https://example.com/fake.las",
                "source_type": "well",
                "well_id": "FAKE_WELL_URL",
            })

        result = _run(run())

    import json
    data = json.loads(result.content[0].text) if hasattr(result.content[0], "text") else result
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    status = data.get("status") or data.get("execution_status", "")
    assert status != "ERROR", f"Expected success from URL ingest, got ERROR: {data}"
    assert _artifact_exists("FAKE_WELL_URL"), "Artifact 'FAKE_WELL_URL' should be registered after URL ingest"


# ─── Test C: Missing file returns FILE_NOT_FOUND ─────────────────────────────

def test_C_missing_file_returns_file_not_found():
    """C: geox_data_ingest_bundle with a nonexistent path must return
    error_code=FILE_NOT_FOUND (no computation allowed without evidence)."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_missing")
    register_unified_tools(mcp)

    async def run():
        return await mcp.call_tool("geox_data_ingest_bundle", {
            "source_uri": "/nonexistent/path/does_not_exist.las",
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text) if hasattr(result.content[0], "text") else result
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    assert data.get("error_code") == "FILE_NOT_FOUND", (
        f"Expected FILE_NOT_FOUND, got: {data}"
    )
    status = data.get("status") or data.get("execution_status", "")
    assert status == "ERROR", f"Expected status ERROR for missing file, got: {status}"


# ─── Test D: Bad URL returns URL_FETCH_FAILED ────────────────────────────────

def test_D_bad_url_returns_url_fetch_failed():
    """D: geox_data_ingest_bundle with an inaccessible HTTPS URL must return
    error_code=URL_FETCH_FAILED."""
    _reset_registry()

    import urllib.error

    def fake_bad_retrieve(url, dest):
        raise urllib.error.URLError("Connection refused (mocked)")

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_badurl")
    register_unified_tools(mcp)

    with patch("urllib.request.urlretrieve", side_effect=fake_bad_retrieve):
        async def run():
            return await mcp.call_tool("geox_data_ingest_bundle", {
                "source_uri": "https://bad.host.invalid/data.las",
            })

        result = _run(run())

    import json
    data = json.loads(result.content[0].text) if hasattr(result.content[0], "text") else result
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    assert data.get("error_code") == "URL_FETCH_FAILED", (
        f"Expected URL_FETCH_FAILED, got: {data}"
    )


# ─── Test E: QC fails closed for unregistered artifact_ref (Bug 3) ───────────

def test_E_qc_fails_closed_for_unregistered_ref():
    """E (Bug 3 regression): geox_data_qc_bundle with an artifact_ref that was
    never ingested must return ERROR/ARTIFACT_NOT_FOUND.
    This tests the fail-closed rule: no fake ref can pass QC."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_qc_e")
    register_unified_tools(mcp)

    async def run():
        return await mcp.call_tool("geox_data_qc_bundle", {
            "artifact_ref": "WELL_THAT_WAS_NEVER_INGESTED",
            "artifact_type": "well_log",
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text) if hasattr(result.content[0], "text") else result
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    assert data.get("error_code") == "ARTIFACT_NOT_FOUND", (
        f"BUG3 REGRESSION: unregistered ref should fail closed, got: {data}"
    )
    exec_status = data.get("execution_status") or data.get("status", "")
    assert exec_status == "ERROR", (
        f"BUG3 REGRESSION: expected ERROR status, got: {exec_status}"
    )
    assert data.get("claim_state") == "NO_VALID_EVIDENCE", (
        f"Expected NO_VALID_EVIDENCE, got: {data.get('claim_state')}"
    )


# ─── Test F: QC passes for registered artifact_ref (positive path) ───────────

def test_F_qc_passes_for_registered_ref():
    """F (positive path): geox_data_qc_bundle must succeed when artifact_ref
    has been previously registered via ingest."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools, _register_artifact

    mcp = FastMCP(name="test_geox_qc_f")
    register_unified_tools(mcp)

    # Directly register an artifact as if it had been ingested
    _register_artifact("PRELOADED_WELL", curves=["GR", "RT", "RHOB"])

    async def run():
        return await mcp.call_tool("geox_data_qc_bundle", {
            "artifact_ref": "PRELOADED_WELL",
            "artifact_type": "well_log",
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text) if hasattr(result.content[0], "text") else result
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    # Must NOT return ARTIFACT_NOT_FOUND
    assert data.get("error_code") != "ARTIFACT_NOT_FOUND", (
        f"Registered artifact should not return ARTIFACT_NOT_FOUND: {data}"
    )
    exec_status = data.get("execution_status") or data.get("status", "")
    assert exec_status != "ERROR", (
        f"Registered artifact QC should succeed, got ERROR: {data}"
    )


# ─── Test G: Candidates fail closed for unregistered refs (Bug 4) ────────────

def test_G_candidates_fail_closed_for_unregistered_refs():
    """G (Bug 4 regression): geox_subsurface_generate_candidates must return
    EVIDENCE_REF_NOT_FOUND when evidence_refs contain unregistered artifact IDs.
    Any unregistered ref must block computation."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_candidates_g")
    register_unified_tools(mcp)

    async def run():
        return await mcp.call_tool("geox_subsurface_generate_candidates", {
            "target_class": "petrophysics",
            "evidence_refs": ["UNREGISTERED_WELL_A", "UNREGISTERED_WELL_B"],
            "realizations": 3,
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text) if hasattr(result.content[0], "text") else result
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    assert data.get("error_code") == "EVIDENCE_REF_NOT_FOUND", (
        f"BUG4 REGRESSION: unregistered evidence_refs should fail closed, got: {data}"
    )
    exec_status = data.get("execution_status") or data.get("status", "")
    assert exec_status == "ERROR", (
        f"BUG4 REGRESSION: expected ERROR, got: {exec_status}"
    )
    assert data.get("claim_state") == "NO_VALID_EVIDENCE", (
        f"Expected NO_VALID_EVIDENCE, got: {data.get('claim_state')}"
    )


# ─── Test H: Correlation panel returns ERROR for all invalid paths (Bug 2) ───

def test_H_correlation_panel_errors_for_all_invalid_paths(tmp_path):
    """H (Bug 2 regression): geox_well_correlation_panel must return ok=False /
    error_code=NO_WELLS_LOADED when every LAS path is invalid.
    A panel with zero wells loaded must never be returned as ok=True."""
    _reset_registry()

    from geox.ingest.plotting import render_correlation_panel

    result = render_correlation_panel(
        las_paths=[
            "/completely/fake/path/well_A.las",
            "/completely/fake/path/well_B.las",
        ],
        output_dir=str(tmp_path),
    )

    assert result.ok is False, (
        f"BUG2 REGRESSION: panel with no wells loaded must have ok=False, got ok={result.ok}"
    )
    assert result.error_code == "NO_WELLS_LOADED", (
        f"BUG2 REGRESSION: expected error_code=NO_WELLS_LOADED, got: {result.error_code}"
    )
    assert result.wells_loaded == 0, (
        f"Expected wells_loaded=0, got: {result.wells_loaded}"
    )

    # Also verify the MCP wrapper propagates the error correctly
    from contracts.tools.well_correlation import _error_response
    err = _error_response("NO_WELLS_LOADED", "test", ["/fake/a.las"])
    assert err["ok"] is False
    assert err["error_code"] == "NO_WELLS_LOADED"
    assert err["wells_loaded"] == 0
    assert err["claim_state"] == "NO_VALID_EVIDENCE"


# ─── Test I: Petrophysics computation succeeds (Positive Path) ──────────────

def test_I_petrophysics_computation_succeeds():
    """I: geox_subsurface_generate_candidates with target_class=petrophysics
    should perform actual calculations if artifact is registered."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools, _register_artifact

    mcp = FastMCP(name="test_geox_petro")
    register_unified_tools(mcp)

    # Register the smoke test LAS
    _register_artifact("SMOKE_WELL", curves=["GR", "RT", "RHOB", "NPHI"], las_path=SMOKE_LAS)

    async def run():
        return await mcp.call_tool("geox_subsurface_generate_candidates", {
            "target_class": "petrophysics",
            "evidence_refs": ["SMOKE_WELL"],
            "vsh_method": "linear",
            "sw_model": "archie",
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text) if hasattr(result.content[0], "text") else result
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    # This should fail if there are import errors or if target_class=petrophysics isn't wired yet.
    assert data.get("execution_status") == "SUCCESS", f"Expected SUCCESS, got: {data}"
    assert "p50" in data or "sw_mean" in data, f"Expected Sw results in output, got: {data}"


def test_J_ingest_qc_candidate_preserve_artifact_ref():
    """Real evidence must flow ingest -> QC -> candidate generation with one artifact_ref."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_artifact_flow")
    register_unified_tools(mcp)

    async def run():
        ingest = await mcp.call_tool("geox_data_ingest_bundle", {
            "source_uri": SMOKE_LAS,
            "source_type": "well",
            "well_id": "FLOW_WELL",
        })
        import json
        ingest_data = json.loads(ingest.content[0].text)
        if isinstance(ingest_data, dict) and "data" in ingest_data:
            ingest_data = ingest_data["data"]

        artifact_ref = ingest_data.get("artifact_ref")
        qc = await mcp.call_tool("geox_data_qc_bundle", {
            "artifact_ref": artifact_ref,
            "artifact_type": "well_log",
        })
        cand = await mcp.call_tool("geox_subsurface_generate_candidates", {
            "target_class": "petrophysics",
            "evidence_refs": [artifact_ref],
            "realizations": 3,
        })
        return ingest_data, json.loads(qc.content[0].text), json.loads(cand.content[0].text)

    ingest_data, qc_data, cand_data = _run(run())
    if isinstance(qc_data, dict) and "data" in qc_data:
        qc_data = qc_data["data"]
    if isinstance(cand_data, dict) and "data" in cand_data:
        cand_data = cand_data["data"]

    assert ingest_data.get("artifact_ref") == "FLOW_WELL"
    assert qc_data.get("artifact_ref") == "FLOW_WELL"
    assert qc_data.get("error_code") != "ARTIFACT_NOT_FOUND", qc_data
    assert cand_data.get("error_code") != "EVIDENCE_REF_NOT_FOUND", cand_data
    assert cand_data.get("artifact_ref") == "FLOW_WELL"


def test_J2_candidate_holds_when_latest_qc_failed():
    """Candidate generation must not return plain SUCCESS after failed latest QC."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import (
        _get_artifact,
        _record_latest_qc,
        _register_artifact,
        register_unified_tools,
    )

    _register_artifact("QC_FAIL_WELL", curves=["GR", "RT"], las_path=SMOKE_LAS)
    _record_latest_qc(
        "QC_FAIL_WELL",
        {
            "qc_overall": "FAIL",
            "qc_passed": False,
            "flags": ["CURVE_FAIL_STATE", "SUITABILITY_VOID"],
            "limitations": ["3 curve(s) in FAIL state"],
            "claim_state": "RAW_OBSERVATION",
        },
    )

    mcp = FastMCP(name="test_geox_qc_candidate_gate")
    register_unified_tools(mcp)

    async def run():
        return await mcp.call_tool("geox_subsurface_generate_candidates", {
            "target_class": "petrophysics",
            "evidence_refs": ["QC_FAIL_WELL"],
            "realizations": 3,
        })

    result = _run(run())
    data = json.loads(result.content[0].text)
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    entry = _get_artifact("QC_FAIL_WELL")
    assert entry["latest_qc"]["qc_passed"] is False
    assert data.get("execution_status") == "HOLD", data
    assert data.get("error_code") == "QC_FAILED_HUMAN_REVIEW_REQUIRED", data
    assert data.get("claim_state") == "HUMAN_REVIEW_REQUIRED", data
    assert data.get("requires_human_review") is True
    assert data.get("artifact_ref") == "QC_FAIL_WELL"


def test_J3_file_upload_import_makes_las_server_visible():
    """Base64 LAS upload should write /data-visible evidence and register artifact_ref."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    payload = base64.b64encode(Path(SMOKE_LAS).read_bytes()).decode("ascii")
    mcp = FastMCP(name="test_geox_file_upload_import")
    register_unified_tools(mcp)

    async def run():
        imported = await mcp.call_tool("geox_file_upload_import", {
            "filename": "UPLOAD_SMOKE.las",
            "content_base64": payload,
            "target_dir": "/data/geox_las_pytest",
            "well_id": "UPLOAD_SMOKE",
            "overwrite": True,
        })
        import_data = json.loads(imported.content[0].text)

        inventory = await mcp.call_tool("geox_las_curve_inventory", {
            "las_path": import_data["stored_path"],
            "well_id": "UPLOAD_SMOKE",
        })
        return import_data, json.loads(inventory.content[0].text)

    import_data, inventory_data = _run(run())
    if isinstance(import_data, dict) and "data" in import_data:
        import_data = import_data["data"]
    if isinstance(inventory_data, dict) and "data" in inventory_data:
        inventory_data = inventory_data["data"]

    assert import_data["status"] == "OK", import_data
    assert import_data["artifact_ref"] == "well_las:UPLOAD_SMOKE"
    assert Path(import_data["stored_path"]).exists()
    assert inventory_data["ok"] is True, inventory_data
    assert inventory_data["well_id"] == "UPLOAD_SMOKE"


def test_K_correlation_panel_accepts_output_png(tmp_path):
    """The advertised output_png argument must be callable and create that file."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_output_png")
    register_unified_tools(mcp)
    output_png = tmp_path / "requested_panel.png"

    async def run():
        return await mcp.call_tool("geox_well_correlation_panel", {
            "las_paths": [SMOKE_LAS],
            "well_names": ["Smoke-01"],
            "tracks": ["GR", "RT"],
            "normalize": True,
            "output_png": str(output_png),
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text)
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    assert data.get("ok") is True, data
    assert data.get("artifact", {}).get("png_path") == str(output_png)
    assert output_png.exists(), f"Expected requested output_png to exist: {output_png}"


def test_L_tool_schema_matches_correlation_callable():
    """Registry discovery must expose output_png exactly once for the callable tool."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_schema")
    register_unified_tools(mcp)

    async def run():
        return await mcp.list_tools()

    tools = _run(run())
    panel_tools = [tool for tool in tools if tool.name == "geox_well_correlation_panel"]
    assert len(panel_tools) == 1, f"Expected one panel tool registration, got {len(panel_tools)}"
    schema_props = panel_tools[0].parameters.get("properties", {})
    assert "output_png" in schema_props, panel_tools[0].parameters


def test_M_correlation_panel_outputs_svg_pdf_json_audit(tmp_path):
    """Plotting layer should generate and validate deterministic companion artifacts."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_plot_artifacts")
    register_unified_tools(mcp)
    output_png = tmp_path / "governed_panel.png"

    async def run():
        return await mcp.call_tool("geox_well_correlation_panel", {
            "las_paths": [SMOKE_LAS],
            "well_names": ["Smoke-01"],
            "tracks": ["GR", "RT"],
            "output_png": str(output_png),
            "output_formats": ["png", "svg", "pdf", "csv_summary", "json_audit"],
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text)
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    artifact = data.get("artifact", {})
    assert data.get("ok") is True, data
    assert artifact.get("png_path") == str(output_png)
    assert artifact.get("svg_path") == str(output_png.with_suffix(".svg"))
    assert artifact.get("pdf_path") == str(output_png.with_suffix(".pdf"))
    assert artifact.get("json_audit_path") == str(output_png.with_suffix(".json"))
    for key in ("png_path", "svg_path", "pdf_path", "csv_summary_path", "json_audit_path"):
        assert data.get("artifact_validation", {}).get(key, {}).get("status") == "VALID"
    assert data.get("telemetry", {}).get("artifact_status") == "VALID"


def test_N_plotspec_rejects_arbitrary_code_field(tmp_path):
    """Declarative PlotSpec must reject executable/script fields."""
    _reset_registry()

    from fastmcp import FastMCP
    from contracts.tools.unified_13 import register_unified_tools

    mcp = FastMCP(name="test_geox_plotspec_reject")
    register_unified_tools(mcp)

    async def run():
        return await mcp.call_tool("geox_well_correlation_panel", {
            "las_paths": [SMOKE_LAS],
            "output_png": str(tmp_path / "blocked.png"),
            "plot_spec": {
                "plot_type": "well_correlation_panel",
                "las_paths": [SMOKE_LAS],
                "tracks": [{"name": "GR", "curves": ["GR"]}],
                "python_code": "import os; os.system('whoami')",
            },
        })

    result = _run(run())
    import json
    data = json.loads(result.content[0].text)
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    assert data.get("ok") is False
    assert data.get("error_code") == "PLOTSPEC_REJECTED"
    assert "Executable PlotSpec field rejected" in data.get("error_message", "")
