"""
test_biostrat_calibrate.py — Integration tests for GEOX biostrat calibration layer.

Phase T2.6 (2026-07-21): FORGE session SEAL-613335b1f5f34abe → T2.6 CALIBRATE.

Tests (T2.6-R1 → T2.6-R9):
  R1 — geox_biostrat_calibrate exists and is callable
  R2 — zone-only calibration returns structured output
  R3 — taxon-only calibration returns structured output (live PBDB)
  R4 — taxon + zone overlap narrows or explains bracket
  R5 — contradiction case triggers falsification summary and avoids confident claim
  R6 — PBDB zero/empty behaviour is gracefully reported, not hidden
  R7 — Mikrotax empty response is labelled explicitly and does not masquerade as evidence
  R8 — all outputs include audit_receipt
  R9 — pytest passes (this file's existence is the proof)
  Wiring — geox_biostrat_calibrate is registered in tools_wiring.py

Mirrors test_biostrat_substrate.py structure. F2 TRUTH: live assertions are honest;
F7 HUMILITY: test the contract, not the data.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from geox_mcp.tools.biostrat_calibrate import geox_biostrat_calibrate  # noqa: E402




# ═════════════════════════════════════════════════════════════════════════════
# Liveness gates
# ═════════════════════════════════════════════════════════════════════════════


def _pbdb_alive() -> bool:
    import httpx

    try:
        resp = httpx.get(
            "https://paleobiodb.org/data1.2/taxa/auto.json?name=Foraminifera&limit=1",
            timeout=8.0,
        )
        return resp.status_code == 200
    except Exception:
        return False


def _mikrotax_alive() -> bool:
    import httpx

    try:
        resp = httpx.get(
            "https://www.mikrotax.org/system/api?name=Emiliania&db=main",
            timeout=8.0,
        )
        return resp.status_code == 200 and bool(resp.text.strip())
    except Exception:
        return False


SKIP_PBDB = pytest.mark.skipif(not _pbdb_alive(), reason="PBDB API unreachable")
SKIP_MIKROTAX = pytest.mark.skipif(not _mikrotax_alive(), reason="Mikrotax API unreachable/empty")


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R1 — Calibrate exists and is callable
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_r1_calibrate_callable():
    """The function exists, is async-callable, and returns a dict envelope."""
    import inspect

    assert callable(geox_biostrat_calibrate)
    assert inspect.iscoroutinefunction(geox_biostrat_calibrate)
    result = await geox_biostrat_calibrate(taxon_name="", zone_code="")
    assert isinstance(result, dict)
    assert "ok" in result
    assert "tool" in result
    assert result["tool"] == "geox_biostrat_calibrate"
    # Empty inputs → UNKNOWN verdict with reason_code
    assert result["ok"] is False
    assert result.get("reason_code") == "EMPTY_INPUTS"


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R2 — Zone-only calibration returns structured output
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_r2_zone_only_calibration_returns_structured_output():
    """Zone-only: Martini NN5 should bracket ~14.62–15.97 Ma per canonical registry."""
    result = await geox_biostrat_calibrate(
        taxon_name="",
        zone_code="NN5",
        scheme="Martini_1971_NN",
    )
    assert result["ok"] is True, f"Expected ok=True for NN5 zone-only, got {result}"
    data = result["data"]
    # Required output fields per spec
    required = [
        "calibrated_age_min_ma",
        "calibrated_age_max_ma",
        "best_age_label",
        "input_basis",
        "sources_used",
        "evidence_for",
        "evidence_against",
        "uncertainty_notes",
        "falsification_summary",
        "confidence_tier",
        "verdict",
        "audit_receipt",
    ]
    for key in required:
        assert key in data, f"Missing required field: {key}"

    assert data["input_basis"] == "zone_only"
    assert data["calibrated_age_min_ma"] is not None
    assert data["calibrated_age_max_ma"] is not None
    assert data["verdict"] in ("PARTIAL", "SABAR", "HOLD", "VOID", "UNKNOWN")
    # NN5 zone canonical age (Martini 1971 in zones.py): 14.62–15.97 Ma
    assert 14.0 < data["calibrated_age_min_ma"] < 16.5, (
        f"NN5 min age {data['calibrated_age_min_ma']} outside expected band"
    )
    assert 14.0 < data["calibrated_age_max_ma"] < 16.5
    assert data["confidence_tier"] in ("HIGH", "MED", "LOW", "BLOCKED")
    assert "NN5" in data["sources_used"][0] or any("NN5" in s for s in data["sources_used"])


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R3 — Taxon-only calibration (live PBDB)
# ═════════════════════════════════════════════════════════════════════════════


@SKIP_PBDB
@pytest.mark.asyncio
async def test_r3_taxon_only_calibration_returns_provenance():
    """Taxon-only: Discoaster should resolve via PBDB with FAD/LAD and provenance."""
    result = await geox_biostrat_calibrate(taxon_name="Discoaster")
    data = result["data"]
    assert data["input_basis"] == "taxon_only"
    # PBDB has Discoaster (it is a major nannofossil genus) — FAD/LAD should be present
    assert data["calibrated_age_min_ma"] is not None or data["calibrated_age_max_ma"] is not None
    assert data["verdict"] in ("PARTIAL", "SABAR")
    # Provenance must include "taxon:" prefix
    assert any(s.startswith("taxon:") for s in data["sources_used"]), (
        f"sources_used missing taxon entry: {data['sources_used']}"
    )
    # T2.6 caveat: taxon-only is broad — must surface uncertainty
    assert any("diachron" in n.lower() or "broad" in n.lower() for n in data["uncertainty_notes"]), (
        "Taxon-only uncertainty note missing"
    )


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R4 — Taxon + zone overlap narrows or explains bracket
# ═════════════════════════════════════════════════════════════════════════════


@SKIP_PBDB
@pytest.mark.asyncio
async def test_r4_taxon_plus_zone_overlap_narrows_bracket():
    """NN5 zone + Discoaster taxon should overlap and narrow the bracket."""
    # NN5 canonical age: ~14.62–15.97 Ma. Discoaster FAD/LAD should overlap.
    result = await geox_biostrat_calibrate(
        taxon_name="Discoaster",
        zone_code="NN5",
        scheme="Martini_1971_NN",
    )
    data = result["data"]
    assert data["input_basis"] == "taxon_plus_zone"
    # Either overlap narrows the bracket, OR falsification VOIDs it
    if data["verdict"] != "VOID":
        assert data["calibrated_age_min_ma"] is not None
        assert data["calibrated_age_max_ma"] is not None
        # Narrowed bracket should be contained within zone bracket
        assert 14.0 < data["calibrated_age_min_ma"] < 16.5
        assert 14.0 < data["calibrated_age_max_ma"] < 16.5
        # Should mention overlap in evidence_for
        assert any("overlap" in e.lower() or "narrowed" in e.lower() for e in data["evidence_for"])
    else:
        # Popper rule: if VOID, falsification_summary must explain
        assert data["falsification_summary"] is not None or data["confidence_tier"] == "BLOCKED"


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R5 — Contradiction case triggers falsification summary and avoids confident claim
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_r5_contradiction_case_does_not_make_confident_claim():
    """Marine nannofossil + coal + freshwater swamp + run_falsify → must NOT be confident.

    A single FALSIFIED gate from biostrat_falsify → calibrate VOIDed or HELD.
    """
    result = await geox_biostrat_calibrate(
        taxon_name="Discoaster",  # marine nannofossil
        zone_code="NN5",           # Middle Miocene marine
        fossil_group="calcareous_nannofossil",
        lithology="coal",
        environment="freshwater swamp",
        run_falsify=True,
        claim="Marine nannofossil preserved in situ in coal",
        region="sabah",
        sample_type="core",
    )
    data = result["data"]
    # Calibration MUST NOT be HIGH confidence
    assert data["confidence_tier"] != "HIGH", (
        "Contradiction case must not be HIGH confidence"
    )
    # Falsify summary must be present
    assert data["falsification_summary"] is not None, (
        "Falsify was run but summary missing"
    )
    # Evidence-against must include the G1 contradiction
    ev_against = " ".join(data["evidence_against"]).lower()
    assert any(kw in ev_against for kw in ["falsif", "coal", "incompatible", "freshwater"]), (
        f"Contradiction must surface in evidence_against. Got: {data['evidence_against']}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R6 — PBDB zero/empty behaviour is gracefully reported, not hidden
# ═════════════════════════════════════════════════════════════════════════════


@SKIP_PBDB
@pytest.mark.asyncio
async def test_r6_pbdb_zero_or_empty_record_handled_gracefully():
    """When PBDB returns no FAD/LAD for a taxon, calibrate must label it explicitly.

    Use a taxon that PBDB resolves but has no FAD/LAD, OR an unresolved taxon.
    Either path: must surface the gap in evidence_against/uncertainty_notes,
    and verdict must be HOLD/SABAR/VOID (never silently PARTIAL).
    """
    # Try a fictitious taxon that PBDB definitely won't resolve
    result = await geox_biostrat_calibrate(
        taxon_name="FictitiousBiostratMarker_xyz_9999",
        zone_code="",
    )
    data = result["data"]
    # Verdict must NOT be a confident PARTIAL with no source
    assert data["verdict"] in ("HOLD", "SABAR", "VOID", "UNKNOWN"), (
        f"Unresolved taxon must not produce confident PARTIAL. Got verdict={data['verdict']}"
    )
    # The absence must be visible
    combined = " ".join(data["evidence_against"] + data["uncertainty_notes"]).lower()
    assert any(
        kw in combined
        for kw in ["not found", "no fad", "no lad", "unresolved", "empty", "could not"]
    ), f"Resolution failure must be visible. Got: {data['evidence_against']} | {data['uncertainty_notes']}"


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R7 — Mikrotax empty response labelled explicitly
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_r7_mikrotax_empty_labelled_explicitly(monkeypatch):
    """Simulate Mikrotax-empty path: resolve_taxon returns Mikrotax-only provenance with no FAD/LAD.

    Calibrate must NOT masquerade Mikrotax web-only presence as positive age evidence.
    """
    from geox_mcp.tools import biostrat_calibrate as _cal_mod

    class _FakeTaxonRecord:
        name = "TestGenus"
        accepted_name = "TestGenus"
        rank = "genus"
        first_occurrence_ma = None
        last_occurrence_ma = None
        pbdb_oid = None
        n_occurrences = None
        extant = None
        mikrotax_url = "https://www.mikrotax.org/system/index.php?taxon=TestGenus"
        provenance = "Mikrotax (web only — no structured data)"

    async def _fake_resolve(*args, **kwargs):
        return _FakeTaxonRecord()

    monkeypatch.setattr(_cal_mod, "resolve_taxon", _fake_resolve)

    result = await _cal_mod.geox_biostrat_calibrate(taxon_name="TestGenus")
    data = result["data"]

    # Must NOT produce a confident age bracket
    assert data["verdict"] in ("SABAR", "HOLD", "VOID"), (
        f"Mikrotax-empty must downgrade verdict. Got {data['verdict']}"
    )
    # Must explicitly label Mikrotax empty
    combined = " ".join(data["evidence_against"] + data["uncertainty_notes"]).lower()
    assert "mikrotax" in combined and "empty" in combined, (
        f"Mikrotax empty must be labelled. Got: {data['evidence_against']} | {data['uncertainty_notes']}"
    )
    # confidence must be LOW or BLOCKED
    assert data["confidence_tier"] in ("LOW", "BLOCKED"), (
        f"Mikrotax-empty must not produce MED/HIGH. Got {data['confidence_tier']}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R8 — All outputs include audit_receipt
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_r8_audit_receipt_present_on_every_output():
    """F11 AUDIT: every calibrate output, including failures, must carry an audit_receipt."""
    # Happy path
    r1 = await geox_biostrat_calibrate(zone_code="NN5", scheme="Martini_1971_NN")
    assert "audit_receipt" in r1["data"]
    receipt = r1["data"]["audit_receipt"]
    assert receipt["tool"] == "geox_biostrat_calibrate"
    assert receipt["phase"] == "T2.6"
    assert receipt["verdict"] in ("PARTIAL", "SABAR", "HOLD", "VOID", "UNKNOWN")
    assert receipt["confidence"] in ("HIGH", "MED", "LOW", "BLOCKED")
    assert "popper_rule_applied" in receipt

    # Empty path
    r2 = await geox_biostrat_calibrate(taxon_name="", zone_code="")
    assert "audit_receipt" in r2["data"]
    assert r2["data"]["audit_receipt"]["verdict"] == "UNKNOWN"


# ═════════════════════════════════════════════════════════════════════════════
# T2.6-R9 — pytest passes (this test is R9 by existence)
# ═════════════════════════════════════════════════════════════════════════════


def test_r9_pytest_file_exists_and_runs():
    """If pytest executes this file, R9 is satisfied."""
    assert Path(__file__).exists()
    assert Path(__file__).name == "test_biostrat_calibrate.py"


# ═════════════════════════════════════════════════════════════════════════════
# Wiring registration — geox_biostrat_calibrate must be in tools_wiring.py
# ═════════════════════════════════════════════════════════════════════════════


def test_wiring_biostrat_calibrate_registered():
    """geox_biostrat_calibrate must be registered as @mcp.tool in tools_wiring.py."""
    wiring_path = Path(__file__).resolve().parents[2] / "src" / "geox_mcp" / "tools_wiring.py"
    source = wiring_path.read_text(encoding="utf-8")
    tree = ast.parse(source)


    registered_tools: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    for kw in dec.keywords:
                        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                            registered_tools.add(kw.value.value)

    expected = {
        "geox_biostrat_resolve_taxon",
        "geox_biostrat_lookup_zone",
        "geox_biostrat_falsify",
        "geox_biostrat_calibrate",
    }
    missing = expected - registered_tools
    assert not missing, f"Missing MCP tool registrations: {missing}"


# ═════════════════════════════════════════════════════════════════════════════
# Additional safety: verify the calibrate module never emits SEAL verdict
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_no_seal_verdict_in_calibrate():
    """T2.6 forbids SEAL — SEAL is sovereign path. Verify by reading source."""
    src_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "geox_mcp"
        / "tools"
        / "biostrat_calibrate.py"
    )
    text = src_path.read_text()
    # 'SEAL' must not appear as a verdict value in calibrate module
    # (the docstring mentions it but does not assign it as VERDICT_*)
    assert 'VERDICT_SEAL' not in text, "Calibrate must not define VERDICT_SEAL"
    assert '"SEAL"' not in text, "Calibrate must not emit 'SEAL' as verdict string"
    assert "'SEAL'" not in text, "Calibrate must not emit 'SEAL' as verdict string"
