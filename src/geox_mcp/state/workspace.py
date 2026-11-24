"""
GEOX Workspace State — H2 Persistent Session Memory
====================================================
DITEMPA BUKAN DIBERI — Forged, Not Given.

Transforms GEOX from a tool collection into a persistent operating environment.
Every tool reads/writes the workspace so that "Kinabalu Basin" entered once
flows through Earth Volume, Prospect Studio, Evidence Console, and Risk Console
without re-entry.

Architecture:
  Workspace → JSON file store (per session) → auto-inject into tool params
  Upgrade path: filesystem → Supabase → VAULT999 sealed state

Session lifecycle:
  arif_init → workspace.load(session_id)
  tool_call → workspace.inject(params)
  tool_result → workspace.record(tool, result)
  session_end → workspace.persist()

H2-H8 alignment:
  H2 — Memory/State (this module)
  H3 — Knowledge Graph (workspace.relations)
  H5 — QQQ Runtime (workspace.hypotheses)
  H7 — AAA State (workspace federation sync)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.state.workspace")

# ── State store path ──────────────────────────────────────────────────────────
_STATE_DIR = Path(os.getenv("GEOX_STATE_DIR", "/root/GEOX/state"))
_STATE_DIR.mkdir(parents=True, exist_ok=True)


# ── Workspace Model ───────────────────────────────────────────────────────────


class GeoxWorkspace(BaseModel):
    """Persistent workspace state for a GEOX session.

    Every tool reads from and writes to this workspace. The workspace
    travels with the session so that context entered once (basin, play,
    well) flows through all subsequent tool calls.
    """

    # ── Geological Context ──────────────────────────────────────────────────
    basin: str | None = Field(default=None, description="Active basin (e.g. 'Kinabalu', 'Malay')")
    play: str | None = Field(default=None, description="Active play (e.g. 'Group H', 'K')")
    well_id: str | None = Field(default=None, description="Active well (e.g. 'Nuri-1')")
    field: str | None = Field(default=None, description="Active field (e.g. 'Kikeh')")
    prospect_ref: str | None = Field(default=None, description="Active prospect reference")
    depth_range: tuple[float, float] | None = Field(default=None, description="(top_m, base_m)")

    # ── Session Metadata ────────────────────────────────────────────────────
    session_id: str | None = Field(default=None, description="MCP session ID")
    actor_id: str = Field(default="arif-fazil", description="Actor identity — canonical sovereign ID, never default \"arif\"")
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    # ── Tool History ────────────────────────────────────────────────────────
    tool_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered list of tool calls: [{tool, params, result_summary, ts}]",
    )
    evidence_stack: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Evidence gathered: [{claim_id, type, label, source}]",
    )

    # ── Active Apps & Agents ────────────────────────────────────────────────
    active_apps: list[str] = Field(
        default_factory=list,
        description="Currently open MCP Apps (e.g. ['well_desk', 'basin_explorer'])",
    )
    agent_activity: dict[str, str] = Field(
        default_factory=dict,
        description="Agent status: {agent_id: status} (e.g. {'atlas': 'thinking'})",
    )

    # ── H3 Graph — Knowledge Relations ──────────────────────────────────────
    relations: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Entity relationships: {entity: [related_entities]}",
    )

    # ── H5 QQQ — Hypotheses ─────────────────────────────────────────────────
    hypotheses: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Active hypotheses: [{id, question, paths, evidence, verdict}]",
    )

    # ── Methods ─────────────────────────────────────────────────────────────

    def touch(self) -> None:
        """Update the last-modified timestamp."""
        self.updated_at = datetime.now(UTC).isoformat()

    def record_tool_call(self, tool_name: str, params: dict, result_summary: str) -> None:
        """Record a tool call in the history."""
        self.tool_history.append(
            {
                "tool": tool_name,
                "params": params,
                "result_summary": result_summary[:200],
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        # Keep last 50 calls
        if len(self.tool_history) > 50:
            self.tool_history = self.tool_history[-50:]
        self.touch()

    def add_evidence(self, claim_id: str, evidence_type: str, label: str, source: str) -> None:
        """Add evidence to the stack."""
        self.evidence_stack.append(
            {
                "claim_id": claim_id,
                "type": evidence_type,
                "label": label,  # OBS/DER/INT/SPEC
                "source": source,
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        self.touch()

    def set_basin_context(self, basin: str, play: str | None = None, well_id: str | None = None) -> None:
        """Set geological context — propagates to all subsequent tools."""
        self.basin = basin
        if play:
            self.play = play
        if well_id:
            self.well_id = well_id
        self.touch()

    def inject_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Auto-inject workspace context into tool parameters.

        If a tool param is None/empty and the workspace has a value,
        fill it in. Explicitly passed params always win.
        """
        ctx_map = {
            "basin_name": self.basin,
            "basin": self.basin,
            "well_id": self.well_id,
            "well_ref": self.well_id,
            "prospect_ref": self.prospect_ref,
        }
        for key, ws_value in ctx_map.items():
            if key in params and ws_value and not params.get(key):
                params[key] = ws_value
                logger.debug("Workspace auto-injected %s=%s", key, ws_value)
        return params

    def get_context_banner(self) -> str:
        """Human-readable context banner for UI display."""
        parts = []
        if self.basin:
            parts.append(f"Basin: {self.basin}")
        if self.play:
            parts.append(f"Play: {self.play}")
        if self.well_id:
            parts.append(f"Well: {self.well_id}")
        if self.field:
            parts.append(f"Field: {self.field}")
        return " · ".join(parts) if parts else "No context set"


# ── Workspace Store ──────────────────────────────────────────────────────────


class WorkspaceStore:
    """JSON file-backed workspace persistence.

    Stores one workspace per session_id as {session_id}.json in GEOX_STATE_DIR.
    Upgrade path: Supabase for multi-node, VAULT999 for sealed audit.
    """

    def __init__(self, state_dir: Path | None = None):
        self._dir = state_dir or _STATE_DIR
        self._cache: dict[str, GeoxWorkspace] = {}

    def _path(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.json"

    def load(self, session_id: str) -> GeoxWorkspace:
        """Load or create workspace for a session."""
        if session_id in self._cache:
            return self._cache[session_id]

        path = self._path(session_id)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                ws = GeoxWorkspace(**data)
                ws.session_id = session_id
                logger.info("Workspace loaded: %s (%s)", session_id, ws.get_context_banner())
            except Exception as exc:
                logger.warning("Workspace load failed for %s, creating fresh: %s", session_id, exc)
                ws = GeoxWorkspace(session_id=session_id)
        else:
            ws = GeoxWorkspace(session_id=session_id)
            logger.info("Workspace created: %s", session_id)

        self._cache[session_id] = ws
        return ws

    def save(self, session_id: str, workspace: GeoxWorkspace | None = None) -> None:
        """Persist workspace to disk."""
        ws = workspace or self._cache.get(session_id)
        if ws is None:
            return
        ws.touch()
        path = self._path(session_id)
        path.write_text(ws.model_dump_json(indent=2), encoding="utf-8")
        logger.debug("Workspace saved: %s", session_id)

    def close(self, session_id: str) -> None:
        """Save and evict from cache."""
        self.save(session_id)
        self._cache.pop(session_id, None)
        logger.info("Workspace closed: %s", session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all saved workspace sessions."""
        sessions = []
        for path in sorted(self._dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                sessions.append(
                    {
                        "session_id": path.stem,
                        "basin": data.get("basin"),
                        "play": data.get("play"),
                        "well_id": data.get("well_id"),
                        "tool_count": len(data.get("tool_history", [])),
                        "updated_at": data.get("updated_at"),
                    }
                )
            except Exception:
                pass
        return sessions


# ── Singleton ─────────────────────────────────────────────────────────────────

_store: WorkspaceStore | None = None


def get_workspace_store() -> WorkspaceStore:
    """Get or create the singleton workspace store."""
    global _store
    if _store is None:
        _store = WorkspaceStore()
    return _store


def get_workspace(session_id: str) -> GeoxWorkspace:
    """Convenience: load workspace for a session."""
    return get_workspace_store().load(session_id)
