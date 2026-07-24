"""
GEOX Workspace Tool — H2 Persistent Session Context
═════════════════════════════════════════════════════
MCP tool for setting and viewing workspace context.
Every tool inherits workspace context automatically.

Modes:
  set      — Set geological context (basin, play, well)
  view     — View current workspace state
  history  — View tool call history
  evidence — View evidence stack
  reset    — Clear workspace context

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from geox_mcp.state.workspace import GeoxWorkspace, get_workspace

logger = logging.getLogger("geox.tools.workspace")

# Default session_id for MCP contexts that don't provide one
_DEFAULT_SESSION = "default"


async def geox_workspace(
    mode: Literal["set", "view", "history", "evidence", "reset", "relations"] = "view",
    basin: str | None = None,
    play: str | None = None,
    well_id: str | None = None,
    field: str | None = None,
    prospect_ref: str | None = None,
    session_id: str = _DEFAULT_SESSION,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Set or view the GEOX workspace context.

    The workspace persists geological context (basin, play, well) across
    all tool calls in a session. Set it once and every subsequent tool
    (Earth Volume, Prospect Studio, Basin Explorer) inherits the context.

    Args:
        mode: What to do — set context, view current state, see tool history,
              review evidence, reset everything, or see knowledge relations.
        basin: Basin name (e.g. 'Kinabalu', 'Malay', 'Sabah')
        play: Play name (e.g. 'Group H', 'K')
        well_id: Well identifier (e.g. 'Nuri-1', 'Malikai-1')
        field: Field name (e.g. 'Kikeh')
        prospect_ref: Prospect reference string
        session_id: Session identifier (default: 'default')
        actor_id: Calling actor (required by evidence-lane middleware; accepted for schema parity)
        trace_id: End-to-end trace id (accepted for schema parity; not stored as authority)
    """
    # actor_id / trace_id are governance envelope fields — accepted here so FastMCP
    # schema and P0_IDENTITY_PROPAGATION middleware agree (no dead-end HOLD).
    _ = actor_id, trace_id
    ws: GeoxWorkspace = get_workspace(session_id)

    if mode == "set":
        before = ws.get_context_banner()
        ws.set_basin_context(
            basin=basin or ws.basin or "",
            play=play if play is not None else ws.play,
            well_id=well_id if well_id is not None else ws.well_id,
        )
        if field:
            ws.field = field
        if prospect_ref:
            ws.prospect_ref = prospect_ref
        ws.touch()
        # H2 P1: Auto-save workspace to disk on every set
        # H3: Seed knowledge graph relations from basin context
        if basin:
            try:
                from geox_mcp.state.knowledge_graph import seed_relations

                kg_relations = seed_relations(basin=basin, play=play, well_id=well_id)
                if kg_relations:
                    ws.relations.update(kg_relations)
                    logger.info("H3 Knowledge graph seeded: %d relations for %s", len(kg_relations), basin)
            except Exception as e:
                logger.debug("H3 knowledge graph seed skipped: %s", e)

        from geox_mcp.state.workspace import get_workspace_store

        get_workspace_store().save(session_id, ws)
        after = ws.get_context_banner()
        logger.info("Workspace context updated: %s → %s", before, after)
        return {
            "mode": "set",
            "previous": before,
            "current": after,
            "workspace": ws.model_dump(),
        }

    elif mode == "view":
        return {
            "mode": "view",
            "context": ws.get_context_banner(),
            "workspace": ws.model_dump(),
        }

    elif mode == "history":
        return {
            "mode": "history",
            "tool_count": len(ws.tool_history),
            "recent_calls": ws.tool_history[-10:],
        }

    elif mode == "evidence":
        return {
            "mode": "evidence",
            "evidence_count": len(ws.evidence_stack),
            "evidence": ws.evidence_stack,
        }

    elif mode == "relations":
        return {
            "mode": "relations",
            "relations": ws.relations,
            "entity_count": len(ws.relations),
        }

    elif mode == "reset":
        from geox_mcp.state.workspace import get_workspace_store

        get_workspace_store().close(session_id)
        new_ws = get_workspace(session_id)
        return {
            "mode": "reset",
            "message": "Workspace context cleared. Fresh session started.",
            "workspace": new_ws.model_dump(),
        }

    return {"mode": mode, "error": f"Unknown mode: {mode}"}
