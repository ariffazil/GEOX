"""P0 regression tests — GEOX earth-evidence loop (2026-10-20).

Each test pins one failure reproduced live against https://geox.arif-fazil.com/mcp
(deployed_git_sha geox-778dcb58) on 2026-10-19T16:38–16:40Z:

  F1  geox_model(mode=physics_section) → OSError Errno 30 (read-only source tree).
      Fixed upstream in 0c62f150; tests here are regression guards only. Raw stderr
      (interpreter + source paths) is still returned at 2d6fde9 — fixed here.
  F1b client out_dir → os.makedirs AND (since 0c62f150) the renderer's output path:
      arbitrary file write from a readOnlyHint tool. Code-derived, NOT probed live.
  F2  tool-level failure stamped transport_status="ERROR" although transport succeeded.
  F3  invalid arguments (FastMCP ValidationError) classified INTERNAL_ERROR/-32001
      instead of SCHEMA_REJECTION/-32602.

Plus one deterministic known-answer gravity benchmark (Harmonica vs closed-form prism)
for the second vertical slice. No network in this file.
"""

from __future__ import annotations

import math
import os
import stat
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SECTION_SCRIPT = REPO / "geox" / "skills" / "subsurface" / "section" / "asas_malam_xs.py"


# ── F1 / F1b ─────────────────────────────────────────────────────────────────


@pytest.fixture
def readonly_section_tree(tmp_path, monkeypatch):
    """Copy the renderer into a dir made read-only, mimicking the deployed mount."""
    import shutil

    from geox_mcp.tools import model_physics as mp

    src = tmp_path / "src_ro" / "section"
    src.mkdir(parents=True)
    shutil.copy(SECTION_SCRIPT, src / SECTION_SCRIPT.name)
    (src / "output").mkdir()  # exists but unwritable, like production
    for p in (src / "output", src):
        p.chmod(stat.S_IRUSR | stat.S_IXUSR)
    art = tmp_path / "artifacts"
    monkeypatch.setattr(mp, "_SECTION_SCRIPT", src / SECTION_SCRIPT.name)
    monkeypatch.setattr(mp, "_SPINE_YAML", REPO / "okf" / "sabah-basin" / "kinabalu_event_spine.yaml")
    monkeypatch.setenv("GEOX_OUTPUT_DIR", str(art))
    yield src, art
    for p in (src, src / "output"):
        p.chmod(stat.S_IRWXU)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores chmod read-only; RO simulation invalid")
def test_f1_physics_section_renders_with_readonly_source(readonly_section_tree):
    from geox_mcp.tools.model_physics import render_physics_section

    src, art = readonly_section_tree
    r = render_physics_section(transect="sabah_nw_se", theme="dark")
    assert r["status"] in ("OK", "BLOCKED_CONFIDENTIALITY_GATE"), r.get("error")
    assert (art / "asas_malam_xs.svg").exists()
    assert not any((src / "output").iterdir()), "renderer must not write into source tree"


def test_f1_renderer_honours_env_out(tmp_path, monkeypatch):
    """Root-safe regression for upstream 0c62f150: output lands where GEOX_OUTPUT_DIR points."""
    import subprocess
    import sys

    out = tmp_path / "out"
    out.mkdir()
    proc = subprocess.run(
        [sys.executable, str(SECTION_SCRIPT), "dark"],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(SECTION_SCRIPT.parent),
        env={**os.environ, "GEOX_OUTPUT_DIR": str(out)},
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    assert (out / "asas_malam_xs.svg").exists()


def test_f1_error_does_not_leak_paths(tmp_path, monkeypatch):
    from geox_mcp.tools import model_physics as mp

    bad = tmp_path / "boom.py"
    bad.write_text(f"raise RuntimeError('boom at {tmp_path}/secret/path')\n")
    monkeypatch.setattr(mp, "_SECTION_SCRIPT", bad)
    monkeypatch.setenv("GEOX_OUTPUT_DIR", str(tmp_path / "art"))
    r = mp.render_physics_section()
    assert r["status"] == "ERROR"
    assert "Traceback" not in r["error"]
    assert "site-packages" not in r["error"] and ".venv" not in r["error"]


@pytest.mark.parametrize("kind", ["relative_traversal", "absolute_outside", "symlink_inside_root"])
def test_f1b_out_dir_confined_to_artifact_root(tmp_path, monkeypatch, kind):
    from geox_mcp.tools import model_physics as mp

    root = tmp_path / "art"
    outside = tmp_path / "outside_target"
    if kind == "relative_traversal":
        od = "../outside_target"
    elif kind == "symlink_inside_root":
        # Symlink placed INSIDE the root but pointing outside — .resolve() must follow it
        # and reject; a lexical-only check would be bypassed here.
        root.mkdir()
        (root / "innocent").symlink_to(outside, target_is_directory=True)
        od = "innocent"
    else:
        od = str(outside)
    monkeypatch.setattr(mp, "_SECTION_SCRIPT", SECTION_SCRIPT)
    monkeypatch.setenv("GEOX_OUTPUT_DIR", str(root))
    r = mp.render_physics_section(out_dir=od)
    assert r["status"] == "ERROR"
    assert r.get("error_class") == "SCHEMA_REJECTION"
    assert not outside.exists(), "renderer must not write outside the output root"
    if kind == "symlink_inside_root":
        assert list(root.iterdir()) == [root / "innocent"], "rejected request must create nothing"
    else:
        assert not root.exists(), "rejected request must create nothing"


# ── F2 ───────────────────────────────────────────────────────────────────────


def test_f2_tool_failure_is_execution_not_transport():
    from geox_mcp.geox_middleware import GeoxGovernanceMiddleware

    result = {"status": "ERROR", "error": "longitude must be in [-180, 180]", "isError": True}
    gov = {"artifact_id": "x", "session_id": "s", "actor_id": "a"}
    out = GeoxGovernanceMiddleware._inject_evidence_envelope(result, "geox_map", gov)
    env = out["_evidence_envelope"]["_envelope"]
    assert env["transport_status"] == "OK"
    assert env["execution_status"] == "FAILED"
    assert env["artifact_status"] == "REJECTED"


def test_f2_success_unchanged():
    from geox_mcp.geox_middleware import GeoxGovernanceMiddleware

    out = GeoxGovernanceMiddleware._inject_evidence_envelope(
        {"status": "OK"}, "geox_map", {"artifact_id": "x", "session_id": "s"}
    )
    env = out["_evidence_envelope"]["_envelope"]
    assert (env["transport_status"], env["execution_status"]) == ("OK", "COMPLETED")


# ── F3 ───────────────────────────────────────────────────────────────────────


def test_f3_fastmcp_validation_error_is_caught_as_schema_rejection():
    import ast

    import fastmcp.exceptions as fe

    from geox_mcp import geox_middleware as gm

    assert issubclass(fe.ValidationError, gm._FastMCPValidationError)
    # The schema branch (not the catch-all) must list the FastMCP class.
    tree = ast.parse(Path(gm.__file__).read_text())
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and isinstance(node.type, ast.Tuple):
            names = {getattr(e, "id", None) for e in node.type.elts}
            if {"ValueError", "_FastMCPValidationError"} <= names:
                body_src = ast.unparse(node)
                found = "SCHEMA_REJECTION" in body_src
    assert found


# ── Slice 2 prerequisite: known-answer gravity benchmark ─────────────────────

G = 6.6743e-11


def _prism_gz_mgal(xo, yo, zo, w, e, s, n, b, t, rho):
    """Closed-form vertical attraction of a right rectangular prism (Nagy et al. 2000).
    z positive up; returns downward attraction (positive for positive density) in mGal."""
    acc = 0.0
    for i, x in enumerate((w - xo, e - xo)):
        for j, y in enumerate((s - yo, n - yo)):
            for k, z in enumerate((b - zo, t - zo)):
                r = math.sqrt(x * x + y * y + z * z)
                acc += (-1) ** (i + j + k) * (x * math.log(y + r) + y * math.log(x + r) - z * math.atan(x * y / (z * r)))
    return abs(G * rho * acc * 1e5)


def test_prism_closed_form_matches_point_mass_far_field():
    m = 300.0 * 1000.0**3
    for x in (3000.0, 20000.0):
        pm = G * m * 1000.0 / (x * x + 1000.0**2) ** 1.5 * 1e5
        gz = _prism_gz_mgal(x, 0, 0, -500, 500, -500, 500, -1500, -500, 300.0)
        assert gz == pytest.approx(pm, rel=1e-2)


def test_harmonica_prism_known_answer():
    hm = pytest.importorskip("harmonica")
    import numpy as np

    prism = [-500.0, 500.0, -500.0, 500.0, -1500.0, -500.0]
    xs = np.array([-3000.0, -1500.0, 0.0, 1500.0, 3000.0])
    coords = (xs, np.zeros_like(xs), np.zeros_like(xs))
    gz = hm.prism_gravity(coords, prism, 300.0, field="g_z")
    ref = [_prism_gz_mgal(x, 0, 0, *prism, 300.0) for x in xs]
    # Documented tolerance: 1e-6 relative (same closed form, float64)
    assert np.allclose(np.abs(gz), ref, rtol=1e-6, atol=1e-9)
    assert abs(gz[2]) == pytest.approx(1.8882, abs=1e-3)  # on-axis value, mGal


def test_f3b_schema_cache_initialised():
    """SCHEMA_REJECTION branch reads self._tool_schemas; it must exist from construction."""
    from geox_mcp.geox_middleware import GeoxGovernanceMiddleware

    mw = GeoxGovernanceMiddleware(
        canonical_public_tools={"geox_map"}, canonical_internal_tools=set(), canonical_compat_tools=set()
    )
    assert mw._tool_schemas == {}
