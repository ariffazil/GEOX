"""
GEOX Skill Resources — Live MCP resource surface for domain skills.
====================================================================
Scans src/geox_core/skills/ for markdown skill definitions and exposes
them as MCP resources under geox://skills/<domain>/<name>.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except Exception:
    yaml = None
    HAS_YAML = False

logger = logging.getLogger("geox.skills_resources")

SKILLS_ROOT = Path(__file__).resolve().parent.parent / "geox_core" / "skills"


def _parse_skill_md(path: Path) -> dict[str, Any] | None:
    """Parse a skill markdown file and return frontmatter + body metadata."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning(f"Cannot read skill file {path}: {exc}")
        return None

    if not text.startswith("---"):
        return None

    # Split frontmatter
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    frontmatter_text = parts[1].strip()
    body = parts[2].strip()

    if HAS_YAML:
        try:
            meta = yaml.safe_load(frontmatter_text) or {}
        except Exception as exc:
            logger.warning(f"YAML parse error in {path}: {exc}")
            return None
    else:
        # Fallback: basic key-value extraction
        meta = {}
        for line in frontmatter_text.splitlines():
            if ":" in line and not line.startswith("#"):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()

    if not meta.get("id"):
        return None

    # Derive URI from id or path
    skill_id = meta["id"]
    uri = f"geox://skills/{skill_id.replace('.', '/')}"

    return {
        "uri": uri,
        "name": meta.get("title", path.stem),
        "description": body.split("\n")[0].lstrip("# ").strip() if body else "",
        "mimeType": "text/markdown",
        "meta": meta,
        "path": str(path),
    }


def _collect_skills() -> list[dict[str, Any]]:
    """Walk SKILLS_ROOT and collect all valid skill definitions."""
    skills: list[dict[str, Any]] = []
    if not SKILLS_ROOT.exists():
        logger.warning(f"Skills root not found: {SKILLS_ROOT}")
        return skills

    for md_path in SKILLS_ROOT.rglob("*.md"):
        skill = _parse_skill_md(md_path)
        if skill:
            skills.append(skill)

    logger.info(f"Discovered {len(skills)} domain skills in {SKILLS_ROOT}")
    return skills


def register_geox_skills(mcp_server) -> None:
    """Register all geox_core skills as MCP resources on the given FastMCP server."""
    skills = _collect_skills()
    if not skills:
        logger.info("No skills to register.")
        return

    for skill in skills:
        uri = skill["uri"]
        name = skill["name"]
        meta = skill["meta"]

        # Build resource text: frontmatter summary + full markdown body
        def _make_resource(path=skill["path"], metadata=meta) -> str:
            try:
                return Path(path).read_text(encoding="utf-8")
            except Exception as exc:
                return f"# Skill Error\n\nFailed to load skill: {exc}"

        # FastMCP add_resource expects a callable that returns the resource content
        try:
            mcp_server.add_resource(
                uri=uri,
                name=name,
                description=skill.get("description", ""),
                mime_type="text/markdown",
                fn=_make_resource,
            )
            logger.info(f"Registered skill resource: {uri}")
        except Exception as exc:
            logger.warning(f"Failed to register skill resource {uri}: {exc}")

    logger.info(f"Skill resource surface: {len(skills)} domains registered.")
