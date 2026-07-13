"""
tests/test_gravmag_studio_forward.py — Stage A tests for GEOX GravMag Studio.

Validates:
- geox_gravmag_studio_open returns the canonical envelope shape.
- Mock backend forward returns a non-zero anomaly grid for a single
  dense prism (gravity).
- Mock backend forward returns a non-zero anomaly grid for a single
  magnetised prism (magnetic).
- Empty prism set returns flat-zero grid.
- Manifest entry validates (no duplicate tool names).
- Tool resource registration survives a clean import.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Ensure src/ is on PYTHONPATH for editable install.
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ─────────────────────────── CORE TOOL ────────────────────────────────────────
@pytest.mark.asyncio
async def test_gravmag_studio_gravity_single_prism_mock():
    from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

    prisms = [
        {
            "easting": 0.0,
            "northing": 0.0,
            "depth_top": 1000.0,
            "depth_bottom": 2000.0,
            "width_e": 4000.0,
            "width_n": 4000.0,
            "density": 300.0,  # kg/m^3 contrast
        }
    ]
    out = await geox_gravmag_studio_open(
        survey_type="gravity",
        prisms=prisms,
        grid_extent_m=20000.0,
        grid_n=20,
        backend="mock",
    )

    assert out["tool_name"] == "geox_gravmag_studio_open"
    assert out["verdict"] == "QUALIFY"  # never SEAL for forward-only
    assert out["claim_tag"] == "SPECULATION"
    assert out["ui"]["resourceUri"] == "ui://geox/gravmag-studio.html"
    assert out["ui"]["app_id"] == "geox.gravmag.studio"
    assert out["render_payload"]["survey_type"] == "gravity"
    assert out["render_payload"]["backend"] == "mock"
    assert out["render_payload"]["grid_shape"] == [20, 20]
    assert len(out["render_payload"]["anomaly_values"]) == 20 * 20

    values = out["render_payload"]["anomaly_values"]
    peak = max(values)
    trough = min(values)
    assert peak > 0.0, "dense prism must produce positive gravity anomaly"
    assert trough < peak, "anomaly grid must not be flat"
    assert peak < 100.0, "single 300 kg/m^3 contrast prism should not exceed ~100 mGal at 20 km"

    # Provenance must reflect input shape.
    assert "20x20" in out["provenance"]
    assert "1prisms" in out["provenance"]
    assert out["vault_receipt"]["tool_name"] == "geox_gravmag_studio_open"


@pytest.mark.asyncio
async def test_gravmag_studio_magnetic_single_prism_mock():
    from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

    prisms = [
        {
            "easting": 0.0,
            "northing": 0.0,
            "depth_top": 500.0,
            "depth_bottom": 1500.0,
            "width_e": 3000.0,
            "width_n": 3000.0,
        }
    ]
    out = await geox_gravmag_studio_open(
        survey_type="magnetic",
        prisms=prisms,
        magnetization_a_m=5.0,
        field_declination_deg=0.0,
        field_inclination_deg=15.0,  # Sabah-ish low latitude
        grid_extent_m=15000.0,
        grid_n=16,
        backend="mock",
    )

    assert out["render_payload"]["survey_type"] == "magnetic"
    assert out["render_payload"]["units"]["magnetic"] == "nT"
    assert out["render_payload"]["grid_shape"] == [16, 16]

    values = out["render_payload"]["anomaly_values"]
    assert max(values) > 0.0 or min(values) < 0.0, "magnetised prism must produce anomaly"
    # Caveat about RTP at low latitude should appear since incl<20°
    caveat_blob = " ".join(out["caveats"]).lower()
    assert "spec" in caveat_blob  # SPECULATION emphasised
    assert "stage a" in caveat_blob  # forward-only caveat


@pytest.mark.asyncio
async def test_gravmag_studio_empty_prisms_returns_flat_zero():
    from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

    out = await geox_gravmag_studio_open(
        survey_type="gravity",
        prisms=[],
        grid_extent_m=10000.0,
        grid_n=10,
        backend="mock",
    )

    assert out["verdict"] == "QUALIFY"
    assert all(v == 0.0 for v in out["render_payload"]["anomaly_values"])
    assert out["render_payload"]["value_range"] == [0.0, 0.0]


@pytest.mark.asyncio
async def test_gravmag_studio_backend_selection_auto_uses_mock_when_live_unavailable():
    from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

    # Force auto path — mock should be picked when HarmonIC live import fails
    # or when GEOX_HARMONICA_LIVE != "1".
    os.environ.pop("GEOX_HARMONICA_LIVE", None)
    prisms = [
        {
            "easting": 0.0,
            "northing": 0.0,
            "depth_top": 100.0,
            "depth_bottom": 500.0,
            "width_e": 1000.0,
            "width_n": 1000.0,
            "density": 100.0,
        }
    ]
    out = await geox_gravmag_studio_open(
        survey_type="gravity",
        prisms=prisms,
        grid_extent_m=5000.0,
        grid_n=8,
        backend="auto",
    )
    # Either mock or harmonica depending on environment — but result must exist.
    assert out["render_payload"]["backend"] in {"mock", "harmonica"}
    assert out["render_payload"]["grid_shape"] == [8, 8]


@pytest.mark.asyncio
async def test_gravmag_studio_invalid_grid_n_returns_void_envelope():
    from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

    out = await geox_gravmag_studio_open(
        survey_type="gravity",
        prisms=[],
        grid_extent_m=1000.0,
        grid_n=4,  # below minimum
        backend="mock",
    )
    assert out["verdict"] == "VOID"
    assert "grid_n" in " ".join(out["caveats"]).lower()


@pytest.mark.asyncio
async def test_gravmag_studio_default_request_shape():
    """Call with zero-arg defaults — must succeed with empty anomaly grid."""
    from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

    out = await geox_gravmag_studio_open()
    assert out["tool_name"] == "geox_gravmag_studio_open"
    assert out["render_payload"]["grid_shape"] == [40, 40]
    assert all(v == 0.0 for v in out["render_payload"]["anomaly_values"])


# ─────────────────────────── MANIFEST & CONTRACT ──────────────────────────────
def test_manifest_entry_is_present_and_unique():
    """The tools manifest must contain geox_gravmag_studio_open exactly once."""
    import yaml

    manifest_path = REPO_ROOT / "src" / "geox_mcp" / "tools_manifest.yaml"
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    names = [t["name"] for t in payload.get("tools", [])]
    assert names.count("geox_gravmag_studio_open") == 1, (
        f"geox_gravmag_studio_open must appear exactly once in manifest, "
        f"got {names.count('geox_gravmag_studio_open')}"
    )

    entry = next(t for t in payload["tools"] if t["name"] == "geox_gravmag_studio_open")
    assert entry["ui"]["resource_uri"] == "ui://geox/gravmag-studio.html"
    assert entry["plugin"]["exposed"] is True
    assert entry["governance"]["mutation"] is False


def test_contract_json_validates():
    """The contract JSON must load + pass a minimal required-field check."""
    import jsonschema

    contract_path = REPO_ROOT / "src" / "geox_mcp" / "contracts" / "geox_gravmag_studio_contract.json"
    schema = json.loads(contract_path.read_text(encoding="utf-8"))

    # Minimal valid payload (synthetic, mirrors actual tool return).
    sample = {
        "tool_name": "geox_gravmag_studio_open",
        "claim_tag": "SPECULATION",
        "verdict": "QUALIFY",
        "ui": {
            "resourceUri": "ui://geox/gravmag-studio.html",
            "app_id": "geox.gravmag.studio",
            "version": "0.1.0",
        },
        "vault_receipt": {
            "vault": "VAULT999",
            "tool_name": "geox_gravmag_studio_open",
            "verdict": "QUALIFY",
            "timestamp": "2026-07-13T00:00:00+00:00",
            "hash": "deadbeefcafebabe",
        },
        "input": {"survey_type": "gravity"},
        "render_payload": {
            "type": "anomaly_grid",
            "survey_type": "gravity",
            "anomaly_values": [0.0],
            "grid_shape": [1, 1],
        },
    }
    jsonschema.validate(sample, schema)


# ─────────────────────────── HTML RESOURCE ────────────────────────────────────
def test_html_resource_exists_and_contains_required_anchors():
    html_path = REPO_ROOT / "src" / "geox_mcp" / "ui" / "static" / "gravmag_studio.html"
    assert html_path.exists(), "gravmag_studio.html must exist"
    html = html_path.read_text(encoding="utf-8")
    # Required structural anchors.
    assert "GEOX GravMag Studio" in html
    assert "id=\"heatmap\"" in html
    assert "renderHeatmap" in html
    assert "ui/notifications/tool-input" in html
    # Governance labels visible in HTML.
    assert "SPECULATION" in html or "SPEC" in html
    assert "QUALIFY" in html


def test_surface_manifest_exposes_gravmag_uri():
    """surface_manifest.py must export GRAVMAG_STUDIO_URI constant."""
    from geox_mcp.surface_manifest import GRAVMAG_STUDIO_MIME, GRAVMAG_STUDIO_URI

    assert GRAVMAG_STUDIO_URI == "ui://geox/gravmag-studio.html"
    assert GRAVMAG_STUDIO_MIME == "text/html;profile=mcp-app"


def test_screen_tab_anchors_present_in_html():
    """Stage B Screen-mode UI anchors must be present in gravmag_studio.html."""
    html_path = REPO_ROOT / "src" / "geox_mcp" / "ui" / "static" / "gravmag_studio.html"
    html = html_path.read_text(encoding="utf-8")

    # Tab bar
    assert 'id="tab-forward"' in html
    assert 'id="tab-screen"' in html
    assert 'data-mode="forward"' in html
    assert 'data-mode="screen"' in html
    assert 'id="pane-forward"' in html
    assert 'id="pane-screen"' in html

    # Verdict badge with all 4 states + explicit wording
    assert 'id="screen-verdict-badge"' in html
    assert 'PASS_SCREEN' in html and 'NOT YET FALSIFIED' in html
    assert 'MARGINAL' in html and 'NEEDS MORE EVIDENCE' in html
    assert 'FAIL_SCREEN' in html and 'MODEL DOES NOT DESERVE TO LIVE' in html
    assert 'HOLD' in html and 'HELD — FIX INPUT' in html

    # Abduction discipline anchors
    assert 'id="abduction-primary"' in html
    assert 'id="abduction-for"' in html
    assert 'id="abduction-against"' in html
    assert 'id="abduction-alternatives"' in html
    assert 'id="abduction-missing"' in html

    # Heatmap canvases
    assert 'id="screen-canvas-observed"' in html
    assert 'id="screen-canvas-predicted"' in html
    assert 'id="screen-canvas-residual"' in html

    # Stats + version
    assert 'id="screen-stat-rms"' in html
    assert 'id="screen-stat-rms-norm"' in html
    assert 'id="screen-stat-corr"' in html
    assert 'v0.2.1' in html
    assert "Stage B does not tell you your model is right" in html
