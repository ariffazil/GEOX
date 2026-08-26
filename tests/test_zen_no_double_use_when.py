"""
test_zen_no_double_use_when.py — Regression guard for Zen §6 trigger pattern.

Audit 2026-08-26 found 10 tools emitting "Use when: Use when you need ..."
in MCP tools/list — the docstring parser emitted the trigger twice. This
test enforces one trigger phrase per tool description.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from geox_mcp.tools_manifest import CANONICAL_TOOLS  # noqa: E402


def _all_tool_descriptions() -> list[tuple[str, str]]:
    """Return [(tool_name, description)] for every canonical public tool."""
    out = []
    for name, canonical in CANONICAL_TOOLS.items():
        desc = canonical.description or ""
        out.append((name, desc))
    return out


def test_no_double_use_when_in_descriptions() -> None:
    """No tool description should contain 'Use when' twice (or more)."""
    offenders = []
    for name, desc in _all_tool_descriptions():
        count = desc.lower().count("use when")
        if count > 1:
            offenders.append((name, count, desc[:80]))
    assert not offenders, (
        "Zen §6 violation: tools with duplicated 'Use when' trigger:\n"
        + "\n".join(f"  - {n} ({c}x): {d!r}" for n, c, d in offenders)
    )


def test_canonical_tools_not_empty() -> None:
    """Sanity: CANONICAL_TOOLS must be populated; otherwise the test above is a no-op."""
    assert len(CANONICAL_TOOLS) > 0, (
        "CANONICAL_TOOLS is empty — re-import after server-side registry drift"
    )
