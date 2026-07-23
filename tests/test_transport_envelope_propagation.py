"""
🌊 GEOX Transport Envelope Propagation — empirical proof.

Per sovereign probe 2026-07-23: schema declares session_id/actor_id/trace_id/
source_sha256 (TransportAwareRequest), but does the HANDLER actually receive
them? Does the response carry them back in provenance?

This test pins the doctrine at the Python signature level — not just the
schema level — so audit claims are testable.
"""

from __future__ import annotations

import inspect

import pytest

from geox_mcp.domain.seismic_interpret.models import (
    StrictModel,
    TransportAwareRequest,
)
from geox_mcp.tools.seismic_interpret import geox_seismic_interpret


# ──────────────────────────────────────────────────────────────────────
# Point 1: schema layer — declared fields reach model_dump, unknown trip
# ──────────────────────────────────────────────────────────────────────


def test_strictmodel_uses_forbid_live():
    """Live state must be forbid (parallel-agent patch 07619e31)."""
    assert StrictModel.model_config.get("extra") == "forbid", (
        f"StrictModel.extra = {StrictModel.model_config.get('extra')!r}, expected 'forbid'"
    )


def test_transport_aware_declares_four_transport_fields():
    """TransportAwareRequest must declare session_id, actor_id, trace_id, source_sha256."""
    expected = {"session_id", "actor_id", "trace_id", "source_sha256"}
    actual = set(TransportAwareRequest.model_fields.keys())
    missing = expected - actual
    assert not missing, f"TransportAwareRequest missing: {missing}"


# ──────────────────────────────────────────────────────────────────────
# Point 2: handler signature — transport params are accepted, not rejected
# ──────────────────────────────────────────────────────────────────────


def test_handler_signature_accepts_transport_kwargs():
    """Handler must explicitly declare session_id/actor_id/trace_id/source_sha256.

    FastMCP rejects **kwargs, so each transport field must be a named
    parameter. If it's missing, MCP gateway will TypeError on any caller
    that passes transport metadata.
    """
    sig = inspect.signature(geox_seismic_interpret)
    params = set(sig.parameters.keys())
    expected = {"session_id", "actor_id", "trace_id", "source_sha256"}
    missing = expected - params
    assert not missing, f"handler signature missing transport params: {missing}"


# ──────────────────────────────────────────────────────────────────────
# Point 3: end-to-end — declared transport survives handler + reaches response
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_transport_reaches_response_provenance():
    """A caller passing transport kwargs must see them stamped into the response."""
    r = await geox_seismic_interpret(
        mode="interpret_section",
        image_path="/root/GEOX/data/atlas/cache/renders/8a5b232559341756.png",
        session_id="probe-sess-001",
        actor_id="arif-fazil",
        trace_id="trc-sov-1",
        source_sha256="sha256:abc123",
    )
    prov = r.get("provenance") or {}
    assert prov.get("session_id") == "probe-sess-001", f"session_id lost: {prov}"
    assert prov.get("actor_id") == "arif-fazil", f"actor_id lost: {prov}"
    assert prov.get("trace_id") == "trc-sov-1", f"trace_id lost: {prov}"
    assert prov.get("source_sha256") == "sha256:abc123", f"source_sha256 lost: {prov}"


@pytest.mark.asyncio
async def test_transport_omitted_does_not_clobber_existing_provenance():
    """If caller omits transport, we must not stamp None over existing provenance."""
    r = await geox_seismic_interpret(
        mode="interpret_section",
        image_path="/root/GEOX/data/atlas/cache/renders/8a5b232559341756.png",
    )
    prov = r.get("provenance") or {}
    # The R1 stage may set its own session_id via code_sha256; ours must
    # not have written a None that overwrote it.
    for k in ("session_id", "actor_id", "trace_id", "source_sha256"):
        if k in prov:
            assert prov[k] is not None, f"transport {k} stamped as None on omission"
