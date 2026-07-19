"""
publisher.py — emits IntelligenceAtom for every GEOX tool call.

Per docs/FEDERATION_INTELLIGENCE_FLOW.md, every GEOX tool call produces
an IntelligenceAtom that flows on NATS to arifOS Ω + AAA + A-FORGE + WEALTH + WELL.

This module wraps the existing tool result envelope (`get_standard_envelope()`)
and publishes an atom via `event_bus.get_bus()`. Failures are non-blocking —
if NATS is down, the tool call still succeeds; we just don't emit.

DITEMPA BUKAN DIBEI — every tool is a publisher.

SOT-MANIFEST
owner: FORGE (000Ω) under F13 directive
last_verified: 2026-06-22
confidence: high
scope: /root/geox/src/geox_mcp/events/publisher.py
"""

from __future__ import annotations

import os

from geox_core.governance.event_bus import (
    IntelligenceAtom,
    get_bus,
)

# Global toggle — disable quantum flow publication if env says so.
# (Useful for testing or when NATS is intentionally down.)
QUANTUM_FLOW_ENABLED = os.environ.get("GEOX_QUANTUM_FLOW", "1") != "0"


def build_atom_from_tool_result(
    *,
    tool_name: str,
    tool_version: str,
    result: dict,
    pai_receipt: dict | None = None,
    rung: int = 0,
    godel_state: str = "UNKNOWN",
) -> IntelligenceAtom:
    """Build an IntelligenceAtom from a tool's standard envelope result.

    Caller is expected to pass the full tool output envelope. We extract
    PAI Receipt if present, otherwise build a minimal one.
    """
    # Try to extract PAI receipt from the result envelope.
    embedded_pai = result.get("pai_receipt") if isinstance(result, dict) else None
    embedded_rung = result.get("epistemic_provenance", {}).get("rung", 0) if isinstance(result, dict) else 0
    embedded_godel = result.get("godel_wall", {}).get("state", "UNKNOWN") if isinstance(result, dict) else "UNKNOWN"

    return IntelligenceAtom(
        tool_name=tool_name,
        tool_version=tool_version,
        result=result,
        pai_receipt=pai_receipt or embedded_pai or {
            "actor_id": "geox",
            "actor_role": "earth_witness",
            "human_root": None,
            "intent": f"tool_call:{tool_name}",
            "scope": "evidence_only",
        },
        epistemic_ladder_rung=rung or embedded_rung,
        godel_wall_state=godel_state if godel_state != "UNKNOWN" else embedded_godel,
        emitted_by_organ="geox",
    )


async def publish_tool_atom(
    *,
    tool_name: str,
    tool_version: str,
    result: dict,
    pai_receipt: dict | None = None,
    rung: int = 0,
    godel_state: str = "UNKNOWN",
) -> bool:
    """Build + publish an IntelligenceAtom for a GEOX tool call.

    Returns True on successful publish, False on NATS unavailable or error.
    Never raises — quantum flow publication is non-blocking.
    """
    if not QUANTUM_FLOW_ENABLED:
        return False

    atom = build_atom_from_tool_result(
        tool_name=tool_name,
        tool_version=tool_version,
        result=result,
        pai_receipt=pai_receipt,
        rung=rung,
        godel_state=godel_state,
    )
    try:
        bus = get_bus()
        return await bus.publish_atom(atom)
    except Exception:  # noqa: BLE001
        # Graceful degradation — tool call must not fail because of publish.
        return False


def publish_tool_atom_sync(
    *,
    tool_name: str,
    tool_version: str,
    result: dict,
    pai_receipt: dict | None = None,
    rung: int = 0,
    godel_state: str = "UNKNOWN",
) -> bool:
    """Synchronous wrapper for non-async contexts (e.g. legacy tool code).

    Spawns an event loop task to publish. Non-blocking on caller.
    """
    if not QUANTUM_FLOW_ENABLED:
        return False
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.create_task(
            publish_tool_atom(
                tool_name=tool_name,
                tool_version=tool_version,
                result=result,
                pai_receipt=pai_receipt,
                rung=rung,
                godel_state=godel_state,
            )
        ) is not None
    except Exception:  # noqa: BLE001
        return False


__all__ = [
    "publish_tool_atom",
    "publish_tool_atom_sync",
    "build_atom_from_tool_result",
    "QUANTUM_FLOW_ENABLED",
]