"""
GEOX Skills Registry MCP Server
================================
Lightweight MCP server exposing the GEOX skills registry as resources.
Phase 1: static read-only surface — list_skills, get_skill_metadata.
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    from mcp.server import Server
    mcp = Server("geox-registry")
except Exception:
    mcp = object()  # fallback if mcp library not installed

_REGISTRY_PATH = Path(__file__).parent.parent / "registry" / "registry.json"
_registry: dict | None = None


def _load_registry() -> dict:
    global _registry
    if _registry is None:
        with open(_REGISTRY_PATH) as f:
            _registry = json.load(f)
    return _registry


def list_skills(domain: str | None = None) -> dict:
    """Return all skills, optionally filtered by domain."""
    registry = _load_registry()
    skills = registry["skills"]
    if domain:
        skills = [s for s in skills if s.get("domain") == domain]
    return {
        "count": len(skills),
        "total_skills": registry["total_skills"],
        "total_domains": registry["total_domains"],
        "skills": skills,
    }


def get_skill_metadata(skill_id: str) -> dict:
    """Return metadata for a single skill by ID."""
    registry = _load_registry()
    for skill in registry["skills"]:
        if skill.get("id") == skill_id:
            return {"found": True, "skill": skill}
    return {"found": False, "skill_id": skill_id}
