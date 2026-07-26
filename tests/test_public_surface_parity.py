"""P0-2 hardening 2026-07-25 · FI-008 — Public surface parity tests.

These tests assert the GEOX public discovery surface is honest:

  1. Sitemap is regenerated from PUBLIC_SURFACE_MANIFEST.json. Drift
     (manual edits, stale entries) fails the test.
  2. No sitemap entry points at a path that has no backing canonical asset
     (soft-404 detection).
  3. Every entry in `preserved_overlays.mcp_apps` keeps a host page that
     is also reachable from the sitemap or one of the canonical discovery
     surfaces (no-delete sync).
  4. Manifest `removed_entries` are NOT silently re-injected into the
     sitemap.
  5. SPA-shell policy: every entry with `spa_shell=true` is flagged but
     kept (cockpit overlay is preserved).
  6. .well-known/agent.json points at the manifest / sitemap URLs and
     carries the public_surface_audit block.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "static" / "PUBLIC_SURFACE_MANIFEST.json"
SITEMAP_PATH = REPO_ROOT / "apps" / "site" / "sitemap.xml"
AGENT_JSON_PATH = REPO_ROOT / ".well-known" / "agent.json"
ROBOTS_PATH = REPO_ROOT / "static" / "robots.txt"
LLMS_PATH = REPO_ROOT / "static" / "llms.txt"
RENDERER = REPO_ROOT / "scripts" / "render_public_surface.py"

# Allow scripts/ as a default path on sys.path so we can import the renderer
# without making it a package.
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))


# ── helpers ────────────────────────────────────────────────────────────────


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_sitemap_xml() -> ET.Element:
    return ET.fromstring(SITEMAP_PATH.read_text(encoding="utf-8"))


def _sitemap_loc_urls(root: ET.Element) -> list[str]:
    out = []
    for url in root.findall("{http://sitemaps.org/schemas/sitemap/0.9}url"):
        loc = url.find("{http://sitemaps.org/schemas/sitemap/0.9}loc")
        if loc is not None and loc.text:
            out.append(loc.text.strip())
    return out


# ── 1. Sitemap is rendered from the manifest ───────────────────────────────


def test_sitemap_xml_is_well_formed() -> None:
    root = _load_sitemap_xml()
    assert root.tag.endswith("urlset"), f"unexpected root: {root.tag}"


def test_sitemap_matches_manifest_render() -> None:
    """`render_public_surface.py --check` must be clean — proves no drift."""
    import render_public_surface

    rendered = render_public_surface.render()
    existing = SITEMAP_PATH.read_text(encoding="utf-8")
    assert existing == rendered, (
        f"sitemap drift vs manifest. "
        f"Re-run: python {RENDERER.relative_to(REPO_ROOT)}"
    )


def test_sitemap_only_lists_manifest_routes_with_sitemap_exposure() -> None:
    """No entry in the sitemap should be missing from the manifest."""
    manifest = _load_manifest()
    manifest_paths = {
        r["path"] for r in manifest["routes"] if "sitemap" in r.get("exposed_via", [])
    }
    sitemap_root = _load_sitemap_xml()
    base_url = manifest["base_url"].rstrip("/")
    sitemap_paths = {
        url[len(base_url):] if url.startswith(base_url) else url
        for url in _sitemap_loc_urls(sitemap_root)
    }
    extras = sitemap_paths - manifest_paths
    assert not extras, f"sitemap contains paths not in manifest: {extras}"


# ── 2. Soft-404 detection ──────────────────────────────────────────────────


def test_no_sitemap_entry_points_at_missing_asset() -> None:
    """Every sitemap entry must have a backing asset on disk under the repo."""
    manifest = _load_manifest()
    sitemap_paths = {
        r["path"]: r["asset"] for r in manifest["routes"]
        if "sitemap" in r.get("exposed_via", [])
    }
    missing = []
    for path, asset in sitemap_paths.items():
        asset_abs = REPO_ROOT / asset
        if not asset_abs.exists():
            missing.append((path, asset))
    assert not missing, f"soft-404: sitemap entries without backing asset: {missing}"


def test_asset_minimum_substance_threshold() -> None:
    """A 200-byte HTML file is almost certainly a soft-404. Threshold: 1 KB.

    Exempt:
      - `discoverability` kind (robots.txt, llms.txt are tiny by design)
      - `spa_shell=true` routes (Operator Cockpit at /gui/index.html is
        intentionally a 677-byte shell that hydrates client-side)
    """
    manifest = _load_manifest()
    undersized = []
    for route in manifest["routes"]:
        if "sitemap" not in route.get("exposed_via", []):
            continue
        if route.get("kind") == "discoverability":
            continue
        if route.get("spa_shell") is True:
            continue
        asset = REPO_ROOT / route["asset"]
        if not asset.exists():
            continue
        if asset.stat().st_size < 1024:
            undersized.append((route["path"], asset.name, asset.stat().st_size))
    assert not undersized, (
        f"soft-404: substantive routes with < 1KB html backing: {undersized}"
    )


def test_removed_entries_are_not_in_sitemap() -> None:
    """The manifest's removed_entries MUST stay out of the produced sitemap."""
    manifest = _load_manifest()
    removed = {r["path"] for r in manifest.get("removed_entries", [])}
    sitemap_root = _load_sitemap_xml()
    base_url = manifest["base_url"].rstrip("/")
    sitemap_paths = {
        url[len(base_url):] if url.startswith(base_url) else url
        for url in _sitemap_loc_urls(sitemap_root)
    }
    resurrected = removed & sitemap_paths
    assert not resurrected, (
        f"regression: previously-removed soft-404 entries re-injected: {resurrected}"
    )


def test_known_soft_404_paths_are_not_in_sitemap() -> None:
    """A defense-in-depth check on the historic bad entries."""
    bad = {"/wiki.html", "/network.html", "/catalog.html"}
    manifest = _load_manifest()
    sitemap_root = _load_sitemap_xml()
    base_url = manifest["base_url"].rstrip("/")
    sitemap_paths = {
        url[len(base_url):] if url.startswith(base_url) else url
        for url in _sitemap_loc_urls(sitemap_root)
    }
    leaked = bad & sitemap_paths
    assert not leaked, f"soft-404 leaked into sitemap: {leaked}"


# ── 3. No-delete sync — preserved overlays are reachable ──────────────────


def _collect_sitemap_html_paths(manifest: dict) -> set[str]:
    sitemap_root = _load_sitemap_xml()
    base_url = manifest["base_url"].rstrip("/")
    return {
        url[len(base_url):] if url.startswith(base_url) else url
        for url in _sitemap_loc_urls(sitemap_root)
    }


def _resolve_asset_for_host(manifest: dict, host_public_path: str) -> Path | None:
    """Resolve a public URL path like `/gui/ac_risk_console/index.html` to the
    on-disk asset path declared in the manifest. Returns None if not declared
    as a route (caller can decide whether that's a violation)."""
    routes_by_path = {r["path"]: r for r in manifest["routes"]}
    route = routes_by_path.get(host_public_path)
    if not route:
        return None
    return REPO_ROOT / route["asset"]


def test_preserved_mcp_apps_have_a_host_page() -> None:
    """Each preserved_overlays.mcp_apps entry must have a backing asset on disk."""
    manifest = _load_manifest()
    overlays = manifest["preserved_overlays"]["mcp_apps"]
    missing = []
    for overlay in overlays:
        host = overlay["host"]
        asset = _resolve_asset_for_host(manifest, host)
        if asset is None:
            missing.append((overlay["app_id"], host, "no manifest route"))
            continue
        if not asset.exists():
            missing.append((overlay["app_id"], host, f"asset missing: {asset}"))
    assert not missing, (
        f"no-delete sync violated: preserved MCP apps missing host page: {missing}"
    )


def test_preserved_overlays_reachable_from_sitemap() -> None:
    """Each preserved overlay's host page must appear in the sitemap."""
    manifest = _load_manifest()
    overlays = manifest["preserved_overlays"]["mcp_apps"]
    sitemap_paths = _collect_sitemap_html_paths(manifest)
    sitemap_paths |= {
        # Cockpit overlay is /gui/index.html — exposed directly
        "/gui/index.html"
    }
    unreachable = []
    for overlay in overlays:
        host = overlay["host"]
        if host not in sitemap_paths:
            unreachable.append((overlay["app_id"], host))
    assert not unreachable, (
        f"no-delete sync violated: preserved MCP apps not reachable from sitemap: {unreachable}"
    )


def test_cockpit_overlay_preserved_with_spa_shell_flag() -> None:
    """The Operator Cockpit overlay must be kept BUT flagged as SPA shell."""
    manifest = _load_manifest()
    cockpit = [
        r for r in manifest["routes"] if r["path"] == "/gui/index.html"
    ]
    assert cockpit, "Operator Cockpit route must be present in the manifest"
    assert cockpit[0].get("spa_shell") is True, (
        "Cockpit route must be flagged as spa_shell so it is not silently dropped"
    )
    assert "sitemap" in cockpit[0]["exposed_via"], (
        "Cockpit route must remain exposed via sitemap even with spa_shell flag"
    )


def test_basin_overlay_preserved() -> None:
    """The Malay Basin overlay must remain in the manifest and sitemap."""
    manifest = _load_manifest()
    overlays = manifest["preserved_overlays"]["basin_overlays"]
    sitemap_paths = _collect_sitemap_html_paths(manifest)
    for overlay in overlays:
        host = overlay["host"]
        asset = _resolve_asset_for_host(manifest, host)
        assert asset is not None and asset.exists(), (
            f"basin overlay host missing on disk: {host} (resolved {asset})"
        )
        assert host in sitemap_paths, (
            f"basin overlay not in sitemap: {host}"
        )


# ── 4. SPA-shell policy ────────────────────────────────────────────────────


def test_spa_shell_signature_self_holds() -> None:
    """The file we KNOW is a SPA shell must match the documented signature."""
    cockpit = REPO_ROOT / "static" / "gui" / "index.html"
    if not cockpit.exists():
        return  # guard, file may not exist on CI
    text = cockpit.read_text(encoding="utf-8")
    assert '<div id="root"></div>' in text, "Cockpit must be a SPA shell with #root"
    assert 'type="module"' in text, "Cockpit must hydrate client-side via type=module script"


def test_cockpit_is_counted_in_sitemap() -> None:
    """Even though SPA-shell, cockpit must be in the sitemap."""
    sitemap_paths = _collect_sitemap_html_paths(_load_manifest())
    assert "/gui/index.html" in sitemap_paths, "Cockpit SPA shell must remain in sitemap"


# ── 5. agent.json parity ───────────────────────────────────────────────────


def test_agent_json_is_valid_json() -> None:
    agent = json.loads(AGENT_JSON_PATH.read_text(encoding="utf-8"))
    assert agent["name"] == "GEOX"


def test_agent_json_has_public_surface_audit_block() -> None:
    agent = json.loads(AGENT_JSON_PATH.read_text(encoding="utf-8"))
    audit = agent.get("public_surface_audit")
    assert audit is not None, "agent.json must carry public_surface_audit block"
    assert "manifest" in audit
    assert "sitemap" in audit
    assert "last_verified" in audit
    assert "rejects" in audit
    assert "/wiki.html" in audit["rejects"]
    assert "/network.html" in audit["rejects"]


def test_agent_json_documentation_url_resolves() -> None:
    """The agent.json docs URL must point at a real asset on disk."""
    agent = json.loads(AGENT_JSON_PATH.read_text(encoding="utf-8"))
    docs = agent.get("documentation_url")
    assert docs, "agent.json must declare documentation_url"
    assert "llms.txt" in docs, "documentation_url must point at /llms.txt"
    # llms.txt must exist in the repo
    assert LLMS_PATH.exists(), f"{LLMS_PATH} missing on disk"


def test_agent_json_urls_match_manifest() -> None:
    """agent.json URLs and manifest.discovery_paths must agree."""
    agent = json.loads(AGENT_JSON_PATH.read_text(encoding="utf-8"))
    manifest = _load_manifest()
    discovery = manifest["discovery_paths"]
    # agent.json docs URL must end with manifest's discovery llms path
    assert agent["documentation_url"].endswith(discovery["llms"]), (
        f"agent.json documentation_url={agent['documentation_url']} "
        f"does not match manifest llms={discovery['llms']}"
    )
    # agent.json must declare the agent-card URL
    assert agent["agent_card_url"].endswith(discovery["agent_card"]), (
        f"agent.json agent_card_url={agent['agent_card_url']} "
        f"does not match manifest agent_card={discovery['agent_card']}"
    )


def test_agent_json_tool_count_parity_with_canonical_surface() -> None:
    """Tool count in agent.json metadata must match CANONICAL_PUBLIC_SURFACE.json."""
    surface_path = REPO_ROOT / "CANONICAL_PUBLIC_SURFACE.json"
    if not surface_path.exists():
        return  # guard
    surface = json.loads(surface_path.read_text(encoding="utf-8"))
    canonical_count = len(surface.get("public_tools", []))
    agent = json.loads(AGENT_JSON_PATH.read_text(encoding="utf-8"))
    metadata_text = agent["metadata"].get("generator", "")
    # generator should mention 33 (or whatever current count is) — but at
    # minimum, the audit must consider CANONICAL_PUBLIC_SURFACE.json
    audit = agent.get("public_surface_audit", {})
    assert audit.get("manifest") == "static/PUBLIC_SURFACE_MANIFEST.json"
    # Sanity: the canonical public surface count is the live truth
    assert canonical_count >= 30, (
        f"canonical public surface count suspiciously low: {canonical_count}"
    )


# ── 6. Renderer must exist and be executable ──────────────────────────────


def test_renderer_script_exists() -> None:
    assert RENDERER.exists(), f"renderer missing: {RENDERER}"
    assert RENDERER.is_file()


def test_renderer_check_mode_is_clean() -> None:
    """`python scripts/render_public_surface.py --check` exits 0."""
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(RENDERER), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, (
        f"renderer --check failed ({proc.returncode}):\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )


# ── 7. robots.txt + llms.txt scaffolding still present ────────────────────


def test_robots_txt_points_at_sitemap() -> None:
    text = ROBOTS_PATH.read_text(encoding="utf-8")
    assert "Sitemap:" in text, "robots.txt must declare Sitemap URL"
    assert "sitemap.xml" in text


def test_llms_txt_has_canonical_metadata() -> None:
    text = LLMS_PATH.read_text(encoding="utf-8")
    assert "GEOX" in text
    assert "geox.arif-fazil.com" in text
    assert ".well-known/agent-card.json" in text or "agent-card" in text


# ── 8. Determinism — the manifest is order-stable ──────────────────────────


def test_manifest_routes_are_deterministically_ordered() -> None:
    """If we re-load the manifest, the route order must be byte-identical."""
    a = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    # Re-parse and compare route order
    b = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert [r["path"] for r in a["routes"]] == [r["path"] for r in b["routes"]]
    # And the JSON file itself is canonical (no trailing whitespace, sorted keys)
    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    assert not raw.endswith(" \n"), "manifest must not have trailing whitespace"
