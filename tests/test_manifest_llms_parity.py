"""
Test 6: Manifest / llms.txt Parity
=====================================
Verifies that all manifest files agree on the canonical public surface.
This is a production-release blocker per the Blueprint 888 HOLD list.

Checks:
  - public_registry.json: canonical_tool_count == 13 and tools list matches CANONICAL_TOOLS
  - public_registry.json: epoch does not contain stale "11TOOLS" marker
  - llms.txt: lists exactly the 13 canonical tool names in its numbered section
  - README.md: does not claim a tool count that contradicts 13 (e.g. 28, 29)
  - smithery.yaml: tools section references only canonical names

Run: pytest tests/test_manifest_llms_parity.py -v
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")

from contracts.enums.statuses import CANONICAL_TOOLS

REPO_ROOT = Path(".")


# ── public_registry.json ──────────────────────────────────────────────────────

def test_public_registry_exists():
    assert (REPO_ROOT / "public_registry.json").exists(), "public_registry.json not found"


def test_public_registry_tool_count():
    registry = json.loads((REPO_ROOT / "public_registry.json").read_text())
    assert registry["canonical_tool_count"] == 13, (
        f"Registry canonical_tool_count={registry['canonical_tool_count']}, expected 13"
    )


def test_public_registry_tools_match_canonical():
    registry = json.loads((REPO_ROOT / "public_registry.json").read_text())
    registry_set = set(registry["tools"])
    canonical_set = set(CANONICAL_TOOLS)
    missing = canonical_set - registry_set
    extra = registry_set - canonical_set
    assert not missing, f"Tools in CANONICAL_TOOLS but not in registry: {missing}"
    assert not extra, f"Tools in registry but not in CANONICAL_TOOLS: {extra}"


def test_public_registry_epoch_not_stale():
    """Epoch must not contain '11TOOLS' — that was before the 13-tool consolidation."""
    registry = json.loads((REPO_ROOT / "public_registry.json").read_text())
    epoch = registry.get("epoch", "")
    assert "11TOOLS" not in epoch, (
        f"Stale epoch marker '11TOOLS' in public_registry.json: {epoch!r}. "
        "Update epoch to 'GEOX-13TOOLS-v0.4' or later."
    )


# ── llms.txt ──────────────────────────────────────────────────────────────────

def test_llms_txt_exists():
    assert (REPO_ROOT / "llms.txt").exists(), "llms.txt not found"


def _parse_llms_tool_names() -> list[str]:
    """Extract canonical tool names from the numbered list in llms.txt."""
    text = (REPO_ROOT / "llms.txt").read_text()
    return re.findall(r"\d+\.\s+\*?\*?(geox_[a-z0-9_]+)\*?\*?", text)


def test_llms_txt_lists_13_canonical_tools():
    tool_names = _parse_llms_tool_names()
    assert len(tool_names) == 13, (
        f"llms.txt lists {len(tool_names)} tools, expected 13: {tool_names}"
    )


def test_llms_txt_tools_match_canonical():
    llms_set = set(_parse_llms_tool_names())
    canonical_set = set(CANONICAL_TOOLS)
    missing = canonical_set - llms_set
    extra = llms_set - canonical_set
    assert not missing, f"Canonical tools missing from llms.txt: {missing}"
    assert not extra, f"Non-canonical tools in llms.txt numbered list: {extra}"


def test_llms_txt_no_dotted_names():
    """Dotted aliases like geox_well.compute_petrophysics must not appear as tool names in llms.txt.

    The tool list is in section 1 (up to the first ## header). References in later
    descriptive sections (e.g. Legacy Migration) are OK as explanatory text.
    """
    text = (REPO_ROOT / "llms.txt").read_text()
    section1 = text.split("## ")[0]
    dotted = re.findall(r"geox_[a-z][a-z0-9]*\.[a-z_][a-z0-9_]*", section1)
    assert not dotted, (
        f"Dotted alias names found in llms.txt section 1 tool list: {dotted}. "
        "Dotted names are not valid MCP tool names."
    )


# ── README.md ─────────────────────────────────────────────────────────────────

def test_readme_exists():
    assert (REPO_ROOT / "README.md").exists(), "README.md not found"


def test_readme_no_contradictory_tool_count():
    """README must not claim 28 or 29 tools — those are pre-consolidation numbers."""
    text = (REPO_ROOT / "README.md").read_text()
    # Disallow standalone 28 or 29 as a tool count claim
    bad_counts = re.findall(r"\b(28|29)\s+(?:canonical\s+)?tools?\b", text, re.IGNORECASE)
    assert not bad_counts, (
        f"README references obsolete tool count(s): {bad_counts}. "
        "Reconcile to 13 canonical tools."
    )


# ── smithery.yaml ─────────────────────────────────────────────────────────────

def test_smithery_yaml_exists():
    assert (REPO_ROOT / "smithery.yaml").exists(), "smithery.yaml not found"


def test_smithery_yaml_tools_are_canonical():
    """Any tool name in smithery.yaml must be a valid callable tool.

    This allows: canonical (13), aliases (LEGACY_ALIAS_MAP), and dimension tools.
    It blocks: truly fabricated/hallucinated names.
    """
    from compatibility.legacy_aliases import LEGACY_ALIAS_MAP

    text = (REPO_ROOT / "smithery.yaml").read_text()
    found = set(re.findall(r"geox_[a-z][a-z0-9_]*", text))
    full_names = {n for n in found if n.count("_") >= 1}

    # All known callable tools: canonical + aliases + dimension registries
    known_callable = (
        set(CANONICAL_TOOLS)
        | set(LEGACY_ALIAS_MAP.keys())
        | set(LEGACY_ALIAS_MAP.values())
    )

    unexpected = full_names - known_callable
    assert not unexpected, (
        f"smithery.yaml references unknown tool names: {unexpected}. "
        "These are not in CANONICAL_TOOLS or LEGACY_ALIAS_MAP."
    )


# ── cross-file consistency ────────────────────────────────────────────────────

def test_all_manifests_agree_on_13():
    """The count must be 13 in every manifest that declares it."""
    registry = json.loads((REPO_ROOT / "public_registry.json").read_text())
    assert registry["canonical_tool_count"] == 13
    assert len(set(_parse_llms_tool_names())) == 13
    assert len(set(CANONICAL_TOOLS)) == 13


if __name__ == "__main__":
    import pytest as _pytest
    _pytest.main([__file__, "-v"])
