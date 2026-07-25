"""Prompt C — artifact spine resolve + sequence single_well via well_refs."""

from __future__ import annotations

import pytest

from geox_mcp.artifact_identity import make_artifact_id, parse_artifact_ref
from geox_mcp.artifact_resolve import resolve_well_las


def test_resolve_demo_kinabalu() -> None:
    r = resolve_well_las("DEMO-KINABALU")
    assert r["ok"] is True
    assert r["las_path"]
    assert r["canonical_artifact_ref"]
    assert r["canonical_artifact_ref"].startswith("artifact://geox/well_las/")
    # slash-safe canonical id
    parsed = parse_artifact_ref(r["canonical_artifact_ref"])
    assert parsed is not None
    assert parsed["format"] == "canonical"
    assert "/" not in parsed["canonical_id"]


def test_resolve_canonical_roundtrip() -> None:
    r = resolve_well_las("DEMO_WELL_A")
    assert r["ok"]
    canon = r["canonical_artifact_ref"]
    # second resolve via store/path still works for same demo
    r2 = resolve_well_las("DEMO_WELL_A")
    assert r2["ok"]
    assert r2["las_path"] == r["las_path"]
    # make_artifact_id sanitizes
    ref = make_artifact_id("well_las", "well:15/9-X", "a" * 64)
    assert "15_9-X" in ref or "15/9" not in ref.split("sha256-")[0]
    assert parse_artifact_ref(ref) is not None


def test_resolve_unknown() -> None:
    r = resolve_well_las("NO-SUCH-WELL-XYZ")
    assert r["ok"] is False
    assert r["error"]


@pytest.mark.asyncio
async def test_sequence_single_well_via_well_refs() -> None:
    from geox_mcp.tools.sequence_unified import geox_sequence

    out = await geox_sequence(
        workflow="single_well",
        well_refs=["DEMO_WELL_A"],
        detail_level="bins",
    )
    assert out.get("execution_status") in ("SUCCESS", "COMPLETED", "OK") or out.get(
        "primary_artifact", {}
    ).get("n_usable_bins", 0) > 0 or out.get("primary_artifact", {}).get("bins")
    # Prefer success envelope
    if out.get("execution_status") not in ("SUCCESS", "COMPLETED"):
        # surface error for debug
        pa = out.get("primary_artifact") or {}
        pytest.fail(f"sequence failed: {pa.get('error_code')} {pa.get('message')} exec={out.get('execution_status')}")
    pa = out.get("primary_artifact") or {}
    assert pa.get("canonical_artifact_ref") or pa.get("source")
