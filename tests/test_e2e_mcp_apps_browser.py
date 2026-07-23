"""
GEOX MCP Apps Browser E2E Test — Workspace (P0)
═══════════════════════════════════════════════
Proves: load → receive tool result → render → reject malicious payloads.

Uses HTTP server at localhost:18999 (started by conftest).
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

GEOX_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_HTML = GEOX_ROOT / "src" / "geox_mcp" / "ui" / "workspace_v1.html"

pytestmark = pytest.mark.e2e

# ═══════════════════════════════════════════════════════════════
# Server fixture
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def test_server(tmp_path_factory):
    """Start HTTP server to serve workspace HTML (needed for ES module imports)."""
    d = tmp_path_factory.mktemp("e2e_server")
    import shutil

    shutil.copy(str(WORKSPACE_HTML), str(d / "workspace.html"))

    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import threading

    class H(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(d), **kwargs)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 18999), H)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)
    yield "http://127.0.0.1:18999"
    server.shutdown()


@pytest.fixture(scope="module")
def browser_context(playwright):
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    yield ctx
    ctx.close()
    browser.close()


@pytest.fixture
def page(browser_context):
    p = browser_context.new_page()
    p.set_default_timeout(10000)
    yield p
    p.close()


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def tool_result(**overrides):
    base = {
        "structuredContent": {
            "workspace_id": "e2e-test-basin",
            "mode": "read_only",
            "initial_view": "overview",
            "artifacts": [
                {"ref": "ART-001", "label": "Seismic Section A", "kind": "seismic", "status": "QC_VERIFIED"},
                {"ref": "ART-002", "label": "Well MB-001 LAS", "kind": "well_log", "status": "INGESTED"},
                {"ref": "ART-003", "label": "Tectonic Map 2024", "kind": "map", "status": "PUBLISHED"},
            ],
            "governance": {"verdict": "OBSERVE_ONLY", "mutation_allowed": False},
        },
        "_meta": {"widgetState": {"panels": ["overview", "evidence"]}, "tool": "geox_workspace", "actor": "e2e"},
    }
    base.update(overrides)
    return base


def send_result(page, payload):
    """Inject tool result directly via exposed __workspace_adoptResult (E2E mode)."""
    page.evaluate(f"""
    const p = {json.dumps(payload)};
    if (window.__workspace_adoptResult) {{
        window.__workspace_adoptResult(p);
    }}
    """)


# ═══════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════


class TestWorkspaceRender:
    def test_initial_shell_loads(self, page, test_server):
        page.goto(f"{test_server}/workspace.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        assert page.locator(".hero h1").text_content() == "GEOX Workspace"

    def test_renders_artifacts(self, page, test_server):
        page.goto(f"{test_server}/workspace.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)  # Wait for SDK connect attempt

        send_result(page, tool_result())
        page.wait_for_timeout(800)

        artifacts = page.locator(".artifact")
        assert artifacts.count() == 3, f"Expected 3 artifacts, got {artifacts.count()}"

    def test_renders_workspace_id(self, page, test_server):
        page.goto(f"{test_server}/workspace.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        send_result(page, tool_result())
        page.wait_for_timeout(800)

        body = page.locator("#panel-body").text_content()
        assert "e2e-test-basin" in body, f"Missing workspace ID: {body}"


class TestWorkspaceClick:
    def test_tab_switching(self, page, test_server):
        page.goto(f"{test_server}/workspace.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        send_result(page, tool_result())
        page.wait_for_timeout(500)

        tabs = page.locator(".tab")
        if tabs.count() >= 2:
            texts = [tabs.nth(i).text_content() for i in range(tabs.count())]
            ev = next((i for i, t in enumerate(texts) if "evidence" in t.lower()), None)
            if ev is not None:
                tabs.nth(ev).click()
                page.wait_for_timeout(300)
                body = page.locator("#panel-body").text_content()
                assert "Evidence" in body or "OBSERVE_ONLY" in body

    def test_artifact_selection(self, page, test_server):
        page.goto(f"{test_server}/workspace.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        send_result(page, tool_result())
        page.wait_for_timeout(500)

        artifacts = page.locator(".artifact")
        if artifacts.count() > 0:
            artifacts.nth(0).click()
            page.wait_for_timeout(300)
            sel = page.locator("#selection").text_content()
            assert "ART-001" in sel or "Seismic" in sel


class TestWorkspaceSecurity:
    def test_xss_payload_rendered_as_text(self, page, test_server):
        page.goto(f"{test_server}/workspace.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        malicious = tool_result()
        malicious["structuredContent"]["artifacts"] = [
            {
                "ref": "XSS-001",
                "label": '<img src=x onerror="window.__XSS=true">',
                "kind": "malicious",
                "status": "DANGER",
            }
        ]

        send_result(page, malicious)
        page.wait_for_timeout(500)

        # XSS should NOT execute
        triggered = page.evaluate("window.__XSS")
        assert not triggered, "XSS payload EXECUTED!"

        # Artifact should still appear as element
        assert page.locator(".artifact").count() >= 1

    def test_empty_result_no_crash(self, page, test_server):
        page.goto(f"{test_server}/workspace.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        page.evaluate('window.postMessage({"structuredContent":{}}, "*")')
        page.wait_for_timeout(500)
        assert page.locator("#verdict").text_content()
