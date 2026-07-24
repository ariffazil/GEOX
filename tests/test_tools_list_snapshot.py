"""
test_tools_list_snapshot.py — Drift detector for the per-release tools/list snapshot.

The docs/canonical_public_tools.json snapshot is the contract between the
live MCP surface and the prose (README, governance docs, federation manifests).
This test fails CI if the snapshot drifts from the live registry.

F2 TRUTH: drift is the entire class of "52 vs 31" prose-error we just spent
a session fixing. The snapshot is the seal; the live registry is the truth;
mismatch = someone added/removed/deregistered a tool without regenerating.

Regenerate via:
    python scripts/generate_canonical_surface.py

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS  # noqa: E402

SNAPSHOT_PATH = REPO_ROOT / "docs" / "canonical_public_tools.json"


def _load_snapshot() -> dict:
    assert SNAPSHOT_PATH.exists(), (
        f"Snapshot missing at {SNAPSHOT_PATH}. "
        f"Regenerate via: python scripts/generate_canonical_surface.py"
    )
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


class TestToolsListSnapshot:
    """Drift detection between live registry and per-release snapshot."""

    def test_snapshot_file_exists(self):
        """The snapshot file must exist in docs/."""
        assert SNAPSHOT_PATH.exists(), (
            f"Snapshot missing at {SNAPSHOT_PATH}. "
            f"Regenerate via: python scripts/generate_canonical_surface.py"
        )

    def test_snapshot_schema_is_v1(self):
        """Snapshot must carry the v1 schema marker for forward compat."""
        snapshot = _load_snapshot()
        assert snapshot.get("schema") == "geox.canonical_public_surface.v1"

    def test_snapshot_count_matches_live_registry(self):
        """public_count in snapshot must equal len(CANONICAL_PUBLIC_TOOLS)."""
        snapshot = _load_snapshot()
        assert snapshot["public_count"] == len(CANONICAL_PUBLIC_TOOLS), (
            f"public_count drift: snapshot={snapshot['public_count']}, "
            f"live={len(CANONICAL_PUBLIC_TOOLS)}. "
            f"Regenerate snapshot: python scripts/generate_canonical_surface.py"
        )

    def test_snapshot_tools_match_live_registry(self):
        """public_tools list must equal CANONICAL_PUBLIC_TOOLS (same order)."""
        snapshot = _load_snapshot()
        assert snapshot["public_tools"] == list(CANONICAL_PUBLIC_TOOLS), (
            f"public_tools drifted. "
            f"Added: {set(snapshot['public_tools']) - set(CANONICAL_PUBLIC_TOOLS)}. "
            f"Removed: {set(CANONICAL_PUBLIC_TOOLS) - set(snapshot['public_tools'])}. "
            f"Regenerate: python scripts/generate_canonical_surface.py"
        )

    def test_snapshot_has_generated_at_timestamp(self):
        """Snapshot must carry a generated_at timestamp for audit trail."""
        snapshot = _load_snapshot()
        assert "generated_at" in snapshot
        assert snapshot["generated_at"]  # non-empty

    def test_snapshot_references_tools_manifest_source(self):
        """Snapshot must declare its source as tools_manifest.yaml."""
        snapshot = _load_snapshot()
        assert snapshot.get("source") == "tools_manifest.yaml"

    def test_snapshot_has_count_must_equal_tools_list_rule(self):
        """Snapshot must carry the rule that ties it to tools/list."""
        snapshot = _load_snapshot()
        assert "rule" in snapshot
        assert "tools/list" in snapshot["rule"]
        assert "MUST" in snapshot["rule"] or "must" in snapshot["rule"].lower()


class TestNoProseHardcodesCount:
    """The '52 vs 31' drift class: README and docs must not hardcode counts.

    Skips historical changelog entries (date-labelled rows are auditable
    evidence of what was true at that date) — only flags the HEAD of the
    README or current capability sections.
    """

    @pytest.mark.parametrize(
        "doc_path",
        [
            REPO_ROOT / "README.md",
            REPO_ROOT / "docs" / "index.md",
        ],
    )
    def test_no_hardcoded_tool_count_in_prose(self, doc_path):
        """If a doc path exists, it must not hardcode a count in capability prose."""
        if not doc_path.exists():
            pytest.skip(f"{doc_path.name} not present")
        text = doc_path.read_text(encoding="utf-8", errors="replace")
        import re
        bad_patterns = re.findall(r"\b\d{2,}\s+tools\b", text, re.IGNORECASE)
        for pattern in bad_patterns:
            idx = text.find(pattern)
            context_window = text[max(0, idx - 80):idx + 80]
            # Skip if surrounded by historical evidence markers:
            # - date-labelled row: "| 2026-" or "| 2025-"
            # - audit/registered/changelog/release-history vocabulary
            historical_markers = (
                "| 2026-", "| 2025-", "registered", "audit", "changelog",
                "release history", "P0 — MCP Restore", "v2026.07.19",
            )
            if any(marker in context_window for marker in historical_markers):
                continue
            # Allow references that explicitly point to the snapshot
            if "canonical_public_tools.json" in context_window or "snapshot" in context_window.lower():
                continue
            # Current capability prose must NOT hardcode a count
            pytest.fail(
                f"{doc_path.name}: hardcoded count '{pattern}' in capability prose "
                f"— defer to docs/canonical_public_tools.json snapshot.\n"
                f"Context: ...{context_window}..."
            )
