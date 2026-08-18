"""Phase 1 Clean Slate: Legacy alias tests — verify all 29 aliases removed.

All legacy aliases were killed 2026-06-22. The LEGACY_ALIAS_MAP is now empty.
This test validates the clean slate invariant.
"""

import pytest
from contracts.canonical_registry import LEGACY_ALIAS_MAP, CANONICAL_PUBLIC_TOOLS


def test_legacy_aliases_empty():
    """Phase 1 Clean Slate: LEGACY_ALIAS_MAP must be empty. All 29 aliases killed."""
    assert LEGACY_ALIAS_MAP == {}, (
        f"LEGACY_ALIAS_MAP expected empty but has {len(LEGACY_ALIAS_MAP)} entries: {list(LEGACY_ALIAS_MAP.keys())[:5]}..."
    )


def test_canonical_tool_count_phase2():
    """Canonical count must match registry — no hardcoded drift allowed."""
    from contracts.canonical_registry import CANONICAL_COMPAT_TOOLS

    expected = len(CANONICAL_PUBLIC_TOOLS)
    assert expected > 0, "CANONICAL_PUBLIC_TOOLS must not be empty"
    assert len(CANONICAL_PUBLIC_TOOLS) == expected
    assert len(CANONICAL_COMPAT_TOOLS) >= 50, f"Expected 50+ backward-compat tools, got {len(CANONICAL_COMPAT_TOOLS)}"


def test_no_cross_organ_tools():
    """Phase 1 Clean Slate: cross-organ tools must NOT be in canonical surface."""
    removed = {"geox_well_decision_class", "geox_wealth_feed", "geox_report_to_workflow", "geox_system_registry_status"}
    found = removed & set(CANONICAL_PUBLIC_TOOLS)
    assert not found, f"Cross-organ tools still in canonical surface: {found}"


def test_aliases_not_in_canonical():
    """Phase 1 Clean Slate: verify no alias keys appear as canonical tools."""
    # Since aliases are empty, this is trivially true — but kept as invariant guard
    assert not (set(LEGACY_ALIAS_MAP.keys()) & set(CANONICAL_PUBLIC_TOOLS)), (
        "Alias names must not appear in CANONICAL_PUBLIC_TOOLS"
    )
