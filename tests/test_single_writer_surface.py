"""Single-writer law for GEOX surfaces (2026-11-24).

Two generators produced `tools.json` in *different shapes* and silently fought each
other; a third (legacy `regenerate_surface.py`) wrote a duplicate *lean* canonical
surface that got published. This test pins one owner per artifact so duplicate
authority cannot come back quietly.

Owners:
  tools.json / .well-known/tools.json / .well-known/openapi.json / llms.txt
      -> scripts/generate_public_registry.py  (asserted by test_transport_manifest)
  src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json + contracts/tools.yaml
  + tools_sot.yaml + README badge
      -> scripts/generate_all_surfaces.py
  docroot publication
      -> scripts/publish_docroot.py (reads the SOT; no root mirror)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_tools_json_writer_is_retired_tombstone():
    mod = _load("_geox_gas", "scripts/generate_all_surfaces.py")
    with pytest.raises(RuntimeError, match="owned by scripts/generate_public_registry"):
        mod.regenerate_tools_json(dry_run=True)


def test_llms_txt_writer_is_retired_tombstone():
    mod = _load("_geox_gas2", "scripts/generate_all_surfaces.py")
    with pytest.raises(RuntimeError, match="owned by scripts/generate_public_registry"):
        mod.regenerate_llms_txt(dry_run=True)


def test_legacy_generator_fails_closed():
    import subprocess
    import sys

    r = subprocess.run(
        [sys.executable, "scripts/regenerate_surface.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0, "retired legacy generator must fail closed, not silently write"


def test_no_duplicate_root_canonical_surface():
    assert not (ROOT / "CANONICAL_PUBLIC_SURFACE.json").exists(), (
        "root CANONICAL_PUBLIC_SURFACE.json is a duplicate current-state source; "
        "the SOT lives at src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json"
    )


def test_publisher_reads_single_source():
    src = (ROOT / "scripts" / "publish_docroot.py").read_text(encoding="utf-8")
    assert "src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json" in src
    # The old hand-mirrored root name must no longer be a sync source.
    assert '"CANONICAL_PUBLIC_SURFACE.json": "CANONICAL_PUBLIC_SURFACE.json"' not in src
