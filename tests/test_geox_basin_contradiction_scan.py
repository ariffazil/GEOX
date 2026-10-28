"""2026-10-28 — the contradiction scan must not be a stub.

Measured live 2026-10-28 on :8081: geox_basin(profile_mode='contradiction_scan')
on malay_basin returned `contradictions: []` while the SAME payload's
interpreted set contained CLM-MTJ-007 verbatim:

  "INTERNAL INCONSISTENCY in the GEOX MTJDA dossier: it states combined
   contracted capacity of about 700 mmscf/d across both blocks (2.2), and
   separately that Block A-18 alone processes approximately 790 mmscf/d at
   the riser (2.2 development). These two figures are not reconcilable..."

Two breaks fed that:
  1. the contradiction_scan branch hardcoded `contradictions_found: []` and
     never opened claims.json (the comment said "Add regional contradictions
     if any" — it did not);
  2. the result dict hardcoded `"contradictions": []`, so even a populated
     mode_data could never surface.

Contract after the fix:
  * every mode carries the basin's DECLARED contradictions (a claim that
    names its own inconsistency);
  * contradiction_scan states its scope and how many claims it scanned;
  * a RESOLVED contradiction is filed as RESOLVED, not as open;
  * the detector never infers — absence of a declared contradiction is not
    evidence that none exists, and the payload says so.
"""

from __future__ import annotations

import asyncio

from geox_mcp.tools.basin import _declared_contradictions, geox_basin_profile


def _profile(basin: str, mode: str = "contradiction_scan"):
    return asyncio.run(geox_basin_profile(basin_name=basin, mode=mode))


def _artifact(result):
    return result.get("primary_artifact") or {}


def test_malay_basin_surfaces_its_declared_contradiction():
    pa = _artifact(_profile("malay_basin"))
    found = pa.get("contradictions") or []
    assert found, "malay_basin declares CLM-MTJ-007 but the scan returned nothing"
    ids = [c["claim_id"] for c in found]
    assert "CLM-MTJ-007" in ids
    entry = next(c for c in found if c["claim_id"] == "CLM-MTJ-007")
    assert entry["status"] == "OPEN"
    assert entry["defect_class"] == "internal_capacity_inconsistency"
    assert "700 mmscf/d" in entry["claim"]
    assert "790 mmscf/d" in entry["claim"]


def test_scan_states_its_scope_and_claim_count():
    inter = _artifact(_profile("malay_basin")).get("interpreted") or {}
    assert inter.get("scan_status") == "COMPLETE"
    assert inter.get("scan_scope") == "DECLARED_IN_CLAIM_STORE"
    assert inter.get("claims_scanned", 0) > 0
    assert "does not" in (inter.get("scan_note") or "").lower()


def test_contradictions_are_visible_in_every_mode_not_only_the_scan():
    for mode in ("overview", "petroleum_system", "risk", "contradiction_scan"):
        pa = _artifact(_profile("malay_basin", mode))
        assert pa.get("contradictions"), f"mode={mode} dropped the declared contradiction"


def test_resolved_contradiction_is_filed_as_resolved():
    """kin_clm_6 says RESOLVED in its own text. It must not be filed as open."""
    found = _declared_contradictions(
        [
            {
                "claim_id": "kin_clm_6",
                "claim": "RESOLVED 2026-09-30 (was UNKNOWN): the header resolves a roster contradiction: Hyp-B correct.",
                "claim_type": "observed",
                "source": "internal WCR header",
                "confidence": "HIGH",
                "evidence_refs": [],
                "metadata": {},
            }
        ]
    )
    assert len(found) == 1
    assert found[0]["status"] == "RESOLVED"


def test_open_contradiction_is_not_closed_by_incidental_resolved_text():
    found = _declared_contradictions(
        [
            {
                "claim_id": "x1",
                "claim": "The dossier was resolved in 2019 but the depth contradiction is still open.",
                "metadata": {},
            }
        ]
    )
    assert found[0]["status"] == "OPEN"


def test_detector_does_not_invent_contradictions():
    found = _declared_contradictions(
        [
            {"claim_id": "ok1", "claim": "Group K is both a fluvial reservoir and a lacustrine source rock.", "metadata": {}},
            {"claim_id": "ok2", "claim": "Malay Basin is a failed rift.", "metadata": {}},
        ]
    )
    assert found == []


def test_forbidden_uses_travel_with_the_contradiction():
    """kin_clm_16 forbids a bare age in public artifacts. Losing that in the
    contradiction record would let the very thing it warns about ship."""
    found = _declared_contradictions(
        [
            {
                "claim_id": "kin_clm_16",
                "claim": "Granite age TENSION on record: external cites 7.85-7.22 Ma; internal holds it UNVERIFIED.",
                "forbidden_uses": ["bare_7.85_7.22_in_public_artifacts"],
                "metadata": {},
            }
        ]
    )
    assert found[0]["forbidden_uses"] == ["bare_7.85_7.22_in_public_artifacts"]
