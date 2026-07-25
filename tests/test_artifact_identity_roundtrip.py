"""P0-3 hardening 2026-07-25 · FI-008 — Artifact identity roundtrip.

The audit identified that ingest returned ``well_las:<WELL>`` while QC's
identity gate rejected the same reference. The contract must round-trip:
the artifact_ref that ingest produces must be consumable by QC, and
both must refer to the same logical artifact.

These tests assert:

  1. ``_artifact_identity.make_artifact_id`` emits canonical refs that
     ``parse_artifact_ref`` consumes correctly.
  2. ``_normalize_artifact_ref_for_ingestor`` (in qc.py) strips the legacy
     ``well_las:`` prefix so LASIngestor's identity gate no longer rejects
     it.
  3. The audit's exact failing case — ingest returns
     ``well_las:GEOX-AUDIT-01``, QC receives that string — now produces
     a clean asset_id (``GEOX-AUDIT-01``) that matches the LAS WELL
     header.
  4. ``storage_keys_for`` enumerates all candidate store keys for a ref
     so callers can do defensive lookup during the legacy→canonical
     migration.
  5. Round-trip helpers produce equivalent canonical_ids regardless of
     whether the input is canonical, legacy-prefix, or bare.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib

import pytest

from geox_mcp.tools._artifact_identity import (
    artifact_refs_equal,
    canonicalize_well_ref,
    make_artifact_id,
    parse_artifact_ref,
    sha256_for_bytes,
    sha256_for_file,
    storage_keys_for,
)


# ── 1. make + parse roundtrip ──────────────────────────────────────────────


def test_make_then_parse_canonical() -> None:
    ref = make_artifact_id(
        kind="well_las",
        canonical_id="AUDIT-0001",
        sha256="a" * 64,
    )
    parsed = parse_artifact_ref(ref)
    assert parsed is not None
    assert parsed["format"] == "canonical"
    assert parsed["kind"] == "well_las"
    assert parsed["canonical_id"] == "AUDIT-0001"
    assert parsed["sha256"] == "a" * 64
    assert parsed["version"] is None


def test_make_strips_sha256_prefix() -> None:
    """``sha256:abc...`` input is normalized to bare hex in the output."""
    ref = make_artifact_id("well_las", "X", "sha256:" + "b" * 64)
    assert "sha256-" in ref
    assert "sha256:sha256-" not in ref  # no double prefix


def test_make_with_version() -> None:
    ref = make_artifact_id("well_las", "X", "c" * 64, version=3)
    assert ref.endswith("@v3")
    parsed = parse_artifact_ref(ref)
    assert parsed is not None
    assert parsed["version"] == 3


def test_make_validates_kind() -> None:
    with pytest.raises(ValueError):
        make_artifact_id("Invalid-Kind", "X", "a" * 64)


def test_make_validates_sha256_length() -> None:
    with pytest.raises(ValueError):
        make_artifact_id("well_las", "X", "too_short")


def test_make_validates_version() -> None:
    with pytest.raises(ValueError):
        make_artifact_id("well_las", "X", "a" * 64, version=0)
    with pytest.raises(ValueError):
        make_artifact_id("well_las", "X", "a" * 64, version=-1)


# ── 2. parse legacy forms ──────────────────────────────────────────────────


def test_parse_well_las_prefix() -> None:
    p = parse_artifact_ref("well_las:GEOX-AUDIT-01")
    assert p is not None
    assert p["format"] == "legacy_prefix"
    assert p["kind"] == "well_las"
    assert p["canonical_id"] == "well:GEOX-AUDIT-01"
    assert p["display_name"] == "GEOX-AUDIT-01"
    assert p["sha256"] is None


def test_parse_WELL_uppercase_prefix() -> None:
    p = parse_artifact_ref("WELL:AUDIT-WELL")
    assert p is not None
    assert p["format"] == "legacy_prefix"
    assert p["kind"] == "well"  # lowercased
    assert p["display_name"] == "AUDIT-WELL"


def test_parse_bare_name() -> None:
    """Bare names default to well_las kind for back-compat."""
    p = parse_artifact_ref("AUDIT-WELL")
    assert p is not None
    assert p["format"] == "bare"
    assert p["kind"] == "well_las"
    assert p["canonical_id"] == "well:AUDIT-WELL"


def test_parse_empty_returns_none() -> None:
    assert parse_artifact_ref("") is None
    assert parse_artifact_ref("   ") is None
    assert parse_artifact_ref(None) is None  # type: ignore[arg-type]


# ── 3. canonicalize_well_ref ───────────────────────────────────────────────


def test_canonicalize_prefers_uwi() -> None:
    """UWI wins over WELL when both present (industry standard)."""
    assert canonicalize_well_ref("GEOX-AUDIT-01", "AUDIT-0001") == "AUDIT-0001"


def test_canonicalize_falls_back_to_well() -> None:
    assert canonicalize_well_ref("GEOX-AUDIT-01", None) == "well:GEOX-AUDIT-01"
    assert canonicalize_well_ref("GEOX-AUDIT-01", "") == "well:GEOX-AUDIT-01"


def test_canonicalize_empty_when_both_missing() -> None:
    assert canonicalize_well_ref(None, None) == ""
    assert canonicalize_well_ref("", "") == ""


# ── 4. SHA-256 helpers ─────────────────────────────────────────────────────


def test_sha256_for_bytes_known_value() -> None:
    assert sha256_for_bytes(b"hello") == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_sha256_for_file(tmp_path) -> None:
    p = tmp_path / "blob.bin"
    p.write_bytes(b"hello")
    expected = hashlib.sha256(b"hello").hexdigest()
    assert sha256_for_file(str(p)) == expected


def test_sha256_for_file_missing(tmp_path) -> None:
    """Missing file → empty string (graceful)."""
    assert sha256_for_file(str(tmp_path / "nonexistent.bin")) == ""


# ── 5. THE AUDIT'S EXACT FAILING CASE ─────────────────────────────────────


def test_audit_failing_case_normalizes_correctly() -> None:
    """Reproduces the audit's exact scenario:

    ingest → artifact_ref = "well_las:GEOX-AUDIT-01"
    QC(artifact_ref="well_las:GEOX-AUDIT-01")
    → "Identity Mismatch: Requested 'well_las:GEOX-AUDIT-01' but found
       UWI='AUDIT-0001' WELL='GEOX-AUDIT-01'"

    The fix: _normalize_artifact_ref_for_ingestor strips the prefix
    before the ingestor compares to LAS headers.
    """
    from geox_mcp.tools.qc import _normalize_artifact_ref_for_ingestor

    # The audit's exact artifact_ref string:
    audit_ref = "well_las:GEOX-AUDIT-01"
    normalized = _normalize_artifact_ref_for_ingestor(audit_ref)
    # Now this matches the LAS WELL header (which is "GEOX-AUDIT-01"),
    # NOT the prefixed ref, so LASIngestor's identity gate passes.
    assert normalized == "GEOX-AUDIT-01"


def test_canonical_ref_normalizes_to_uwi() -> None:
    """When the canonical ref carries a UWI, normalize to the UWI."""
    from geox_mcp.tools.qc import _normalize_artifact_ref_for_ingestor

    ref = make_artifact_id("well_las", "AUDIT-0001", "a" * 64)
    normalized = _normalize_artifact_ref_for_ingestor(ref)
    assert normalized == "AUDIT-0001"


# ── 6. artifact_refs_equal ─────────────────────────────────────────────────


def test_refs_equal_when_same_canonical() -> None:
    a = make_artifact_id("well_las", "X", "a" * 64)
    b = make_artifact_id("well_las", "X", "a" * 64)
    assert artifact_refs_equal(a, b)


def test_refs_equal_when_legacy_normalizes() -> None:
    """Legacy ref normalizes to the same canonical_id → equal."""
    ref1 = make_artifact_id("well_las", "well:AUDIT-WELL", "a" * 64)
    ref2 = "well_las:AUDIT-WELL"
    # canonical_id "well:AUDIT-WELL" matches "well:AUDIT-WELL" from the legacy parse
    assert artifact_refs_equal(ref1, ref2)


def test_refs_unequal_when_canonical_id_differs() -> None:
    ref1 = "well_las:GEOX-AUDIT-01"
    ref2 = "well_las:AUDIT-0001"
    # canonical_id differs: "well:GEOX-AUDIT-01" vs "well:AUDIT-0001"
    assert not artifact_refs_equal(ref1, ref2)


# ── 7. storage_keys_for ─────────────────────────────────────────────────────


def test_storage_keys_for_legacy() -> None:
    keys = storage_keys_for("well_las:GEOX-AUDIT-01")
    assert keys[0] == "well_las:GEOX-AUDIT-01"
    # No canonical form (legacy lacks sha256)
    assert all(not k.startswith("artifact://") for k in keys)


def test_storage_keys_for_canonical() -> None:
    ref = make_artifact_id("well_las", "AUDIT-0001", "a" * 64)
    keys = storage_keys_for(ref)
    assert ref in keys
    # The canonical form is first since the raw input is the canonical.
    assert keys[0] == ref


# ── 8. Round-trip preserves canonical_id ──────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected_canonical_id",
    [
        ("well_las:GEOX-AUDIT-01", "well:GEOX-AUDIT-01"),
        ("WELL:GEOX-AUDIT-01", "well:GEOX-AUDIT-01"),
        ("GEOX-AUDIT-01", "well:GEOX-AUDIT-01"),
        (
            make_artifact_id("well_las", "AUDIT-0001", "a" * 64),
            "AUDIT-0001",
        ),
    ],
)
def test_roundtrip_canonical_id(raw: str, expected_canonical_id: str) -> None:
    parsed = parse_artifact_ref(raw)
    assert parsed is not None
    assert parsed["canonical_id"] == expected_canonical_id
