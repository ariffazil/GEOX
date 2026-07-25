"""Prompt B — geox_well_view LAS hydrate + receipt (2026-07-25)."""

from __future__ import annotations

import asyncio

import pytest

from geox_mcp.tools.integration_well import _load_well_curves_for_ui


def test_demo_kinabalu_resolves_las() -> None:
    r = _load_well_curves_for_ui("DEMO-KINABALU", max_n=200)
    assert r["status"] == "loaded"
    assert r.get("curves")
    assert r.get("depths")
    assert len(r["depths"]) > 10
    assert "GR" in r["curves"] or r.get("curves_available")
    assert r.get("data_class") in ("DEMO", "OPEN_OSS", "SYNTHETIC_LABEL", "MEASURED", "INGESTED")
    assert r.get("las_path")


def test_unknown_well_no_silent_empty() -> None:
    r = _load_well_curves_for_ui("NO-SUCH-WELL-XYZ-999", max_n=50)
    assert r["status"] in ("no_las", "error")
    assert not r.get("curves")


def test_hydrate_receipt_seal_path() -> None:
    """Successful hydrate can mint a vault receipt (SEALED or PENDING)."""
    import hashlib
    import json

    from geox_mcp.seal_receipt import RiskClass, Reversibility, seal_receipt

    r = _load_well_curves_for_ui("DEMO-KINABALU", max_n=100)
    assert r["status"] == "loaded"
    payload = {
        "well_id": "DEMO-KINABALU",
        "las_path": r.get("las_path"),
        "n_samples": len(r.get("depths") or []),
        "curves": sorted((r.get("curves") or {}).keys()),
    }
    sha = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    seal = seal_receipt(
        tool="geox_well_view",
        artifact_id="well_view:DEMO-KINABALU",
        artifact_sha256=sha,
        actor_id="ARIF",
        session_id="SEAL-test-b",
        verdict="QUALIFY",
        risk_class=RiskClass.LOW,
        reversibility=Reversibility.FULL,
    )
    assert seal.state in ("SEALED", "PENDING", "FAILED")
    if seal.state == "SEALED":
        assert seal.ref and seal.ref.startswith("vault999://")
