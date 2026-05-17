"""
GEOX Skill Resources — Expose geox_core/skills as live MCP resources and prompts.
================================================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Walks src/geox_core/skills/ recursively, parses YAML frontmatter from every
.md file, and registers eligible skills as:

  - MCP resources  (surface.mcp_resource == true)  → geox://skills/{domain}/{name}
  - MCP prompts    (surface.mcp_prompt   == true)  → named prompt
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

logger = logging.getLogger("geox.unified")

_SKILLS_DIR = Path(__file__).parent.parent / "geox_core" / "skills"


def _parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str]:
    """Extract YAML frontmatter and markdown body from file content."""
    if not content.startswith("---"):
        return None, content

    end = content.find("\n---\n", 4)
    if end == -1:
        return None, content

    raw_yaml = content[4:end]
    body = content[end + 5 :]

    if yaml is None:
        logger.warning("PyYAML not available; cannot parse frontmatter")
        return None, content

    try:
        data = yaml.safe_load(raw_yaml)
    except Exception as exc:
        logger.debug("YAML parse error: %s", exc)
        return None, content

    return data if isinstance(data, dict) else None, body


def _resource_payload(frontmatter: dict[str, Any], body: str) -> str:
    """Serialize metadata + markdown body for an MCP resource response."""
    return json.dumps(
        {
            "metadata": frontmatter,
            "body": body.strip(),
        },
        indent=2,
        default=str,
    )


def _build_resource_handler(frontmatter: dict[str, Any], body: str) -> Any:
    """Return a parameter-less async function suitable for mcp.resource()."""

    async def _handler() -> str:
        return _resource_payload(frontmatter, body)

    return _handler


def _build_prompt_handler(body: str) -> Any:
    """Return a parameter-less async function suitable for mcp.prompt()."""

    async def _handler() -> str:
        return body.strip()

    return _handler


def register_skill_resources(mcp: Any) -> None:
    """Discover skill markdown files and register them as MCP resources and prompts."""
    if not _SKILLS_DIR.exists():
        logger.warning("Skills directory not found: %s", _SKILLS_DIR)
        return

    resource_count = 0
    prompt_count = 0

    for md_path in _SKILLS_DIR.rglob("*.md"):
        if not md_path.is_file():
            continue

        rel_parts = md_path.parent.relative_to(_SKILLS_DIR).parts
        domain = rel_parts[0] if rel_parts else "general"
        skill_name = md_path.stem

        try:
            raw = md_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to read %s: %s", md_path, exc)
            continue

        frontmatter, body = _parse_frontmatter(raw)
        if frontmatter is None:
            continue

        surface = frontmatter.get("surface") or {}

        # ── MCP resource ───────────────────────────────────────────────────────
        if surface.get("mcp_resource"):
            uri = f"geox://skills/{domain}/{skill_name}"
            description = frontmatter.get("title") or f"GEOX skill: {skill_name}"
            handler = _build_resource_handler(frontmatter, body)
            mcp.resource(uri, description=description)(handler)
            resource_count += 1

        # ── MCP prompt ─────────────────────────────────────────────────────────
        if surface.get("mcp_prompt"):
            prompt_name = f"skill_{domain}_{skill_name}".replace("-", "_")
            prompt_description = frontmatter.get("title") or f"GEOX skill prompt: {skill_name}"
            handler = _build_prompt_handler(body)
            mcp.prompt(name=prompt_name, description=prompt_description)(handler)
            prompt_count += 1

    logger.info(
        "Skill surface registered: %s resources, %s prompts from %s",
        resource_count,
        prompt_count,
        _SKILLS_DIR,
    )
