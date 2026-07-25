"""Multi-well correlation DEMO_A + DEMO_B via artifact spine."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_section_correlation_auto_tops_demo_ab() -> None:
    from geox_mcp.tools.sequence_unified import geox_sequence

    out = await geox_sequence(
        workflow="section_correlation",
        well_refs=["DEMO_WELL_A", "DEMO_WELL_B"],
        mode="correlation",
        # section_ref omitted — should default
    )
    assert out.get("execution_status") in ("SUCCESS", "COMPLETED")
    pa = out.get("primary_artifact") or {}
    assert pa.get("n_wells_ok", 0) >= 2
    assert len(pa.get("markers") or []) >= 4  # 3 markers × 2 wells (at least)
    assert pa.get("correlation_panel")
    assert pa.get("tops_auto_derived") is True
    # both wells resolved via spine
    resolved = pa.get("wells_resolved") or []
    assert sum(1 for w in resolved if w.get("ok")) >= 2


@pytest.mark.asyncio
async def test_section_correlation_explicit_tops() -> None:
    from geox_mcp.tools.sequence_unified import geox_sequence

    tops = {
        "BOKOR-1": {"Top_Sand": 1500.0, "Base_Sand": 1800.0},
        "BOKOR-2": {"Top_Sand": 1520.0, "Base_Sand": 1820.0},
    }
    # DEMO wells resolve to BOKOR names in LAS headers — use DEMO ids as tops keys too
    tops_demo = {
        "DEMO_WELL_A": {"Top_Sand": 1500.0, "Base_Sand": 1800.0},
        "DEMO_WELL_B": {"Top_Sand": 1520.0, "Base_Sand": 1820.0},
    }
    out = await geox_sequence(
        workflow="section_correlation",
        section_ref="section:sabah-demo",
        well_refs=["DEMO_WELL_A", "DEMO_WELL_B"],
        mode="correlation",
        tops=tops_demo,
    )
    assert out.get("execution_status") in ("SUCCESS", "COMPLETED")
    pa = out.get("primary_artifact") or {}
    assert pa.get("tops_auto_derived") is False
    markers = pa.get("markers") or []
    assert any(m.get("marker") == "Top_Sand" for m in markers)
    assert any(m.get("tie_type") == "observed" for m in markers)


@pytest.mark.asyncio
async def test_gr_motif_two_wells() -> None:
    from geox_mcp.tools.sequence_unified import geox_sequence

    out = await geox_sequence(
        workflow="section_correlation",
        well_refs=["DEMO_WELL_A", "DEMO_WELL_B"],
        mode="gr_motif",
        section_ref="section:motif-demo",
    )
    assert out.get("execution_status") in ("SUCCESS", "COMPLETED")
    pa = out.get("primary_artifact") or {}
    assert pa.get("wells_processed", 0) >= 1
    motifs = pa.get("motifs_by_well") or {}
    assert len(motifs) >= 1
