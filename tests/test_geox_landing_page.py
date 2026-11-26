"""Step 3 Landing Page Gate — verifies static/index.html hygiene, zero CDN, zero dead routes."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "static" / "index.html"
SERVER_PY = ROOT / "src" / "geox_mcp" / "server.py"

FORBIDDEN_STALE = [
    "33 tools",
    "33 MCP",
    "Sealed to VAULT999",
    "Judge Console",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "Port 8081",
]

FORBIDDEN_CORPORATE = [
    r"\bPekaka\b",
    r"\bBuluh\b",
    r"\bRotan\b",
    r"\bBunga\s+Lili\b",
    r"\bMaligan\b",
    r"\bBarton\b",
    r"\bSugut\b",
    r"\bSolisip\b",
    r"\bPETRONAS\b",
    r"\bOpenWorks\b",
    r"\bKL2\b",
    r"[UP]:\\",
]


def test_landing_page_has_zero_stale_claims_or_external_cdns() -> None:
    html = INDEX.read_text(encoding="utf-8")
    for bad in FORBIDDEN_STALE:
        assert bad not in html, f"Stale/forbidden string found in static/index.html: {bad}"
    assert not re.search(r"<(?:script|link)\b[^>]+https?://", html, flags=re.I)


def test_landing_page_has_zero_corporate_strings() -> None:
    html = INDEX.read_text(encoding="utf-8")
    for pat in FORBIDDEN_CORPORATE:
        assert not re.search(pat, html, flags=re.I), f"Corporate pattern found: {pat}"


def test_landing_page_internal_routes_are_declared() -> None:
    html = INDEX.read_text(encoding="utf-8")
    server_src = SERVER_PY.read_text(encoding="utf-8")
    verified_routes = {"/", "/health", "/tools", "/llms.txt", "/apps/well-forensic-desk/"}
    hrefs = re.findall(r'href="(/[^"#?]*)"', html)
    assert hrefs, "Expected internal links in static/index.html"
    for h in hrefs:
        assert h in verified_routes or f'"{h}"' in server_src or f"'{h}'" in server_src, (
            f"Unverified internal route in static/index.html: {h}"
        )
