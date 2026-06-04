"""
GEOX MCP Resources — Identity, Registry, TREE777 Wiki, Knowledge Pack
══════════════════════════════════════════════════════════════════════
Extracted from server.py for compositional mounting.
Register via register_resources(mcp) on the main FastMCP server.
DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("geox.resources")

# ── Constants injected at registration time ──────────────────────────────────
# These are set by register_resources() from the caller's context
GEOX_VERSION = "v2026.05.27"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"
GEOX_PROFILE = "full"

# Wiki root: /root/AAA/wiki (shared across all 4 federation servers)
TREE777_WIKI_ROOT = Path(os.environ.get("TREE777_WIKI_ROOT", "/root/AAA/wiki"))
TREE777_SKILLS_DIR = TREE777_WIKI_ROOT / "skills" / "geox"
TREE777_CONCEPTS_DIR = TREE777_WIKI_ROOT / "concepts"
TREE777_SCAR_DIR = TREE777_WIKI_ROOT / "scars"

RESOURCES_DIR = Path(os.getcwd()) / "resources"


# ── Identity helpers (forward-declared; injected by register_resources) ──────
_is_geox_func = None
_enforce_geox_func = None


def _geox_read_wiki_file(file_path: str | Path) -> str:
    """Read a wiki file, returning frontmatter-stripped content."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {path}"
    content = path.read_text()
    if content.startswith("---"):
        end = content.find("\n---\n", 4)
        if end != -1:
            content = content[end + 5 :]
    return content.strip()


def _geox_tree777_index() -> dict[str, Any]:
    """Build the TREE777 index for GEOX domain slice."""
    skills = []
    if TREE777_SKILLS_DIR.exists():
        for f in TREE777_SKILLS_DIR.glob("*.md"):
            skills.append({"name": f.stem, "uri": f"tree777://skills/geox/{f.stem}"})

    concepts = []
    if TREE777_CONCEPTS_DIR.exists():
        for f in TREE777_CONCEPTS_DIR.glob("*.md"):
            concepts.append({"name": f.stem, "uri": f"tree777://geo/concepts/{f.stem}"})

    scars = []
    if TREE777_SCAR_DIR.exists():
        for f in TREE777_SCAR_DIR.glob("*.md"):
            if "geox" in f.stem or "geo" in f.stem:
                scars.append({"name": f.stem, "uri": f"tree777://geo/scars/{f.stem}"})

    return {
        "domain": "geox",
        "skills": skills,
        "concepts": concepts,
        "scars": scars,
        "total": len(skills) + len(concepts) + len(scars),
    }


# ── Resource handlers (async functions, no decorators) ───────────────────────

async def geox_identity() -> dict:
    from geox_core.enums.statuses import CANON9_TOOL_MAP, GDE_VOCAB

    identity_state = {
        "identity": "GEOX",
        "role": "Earth Substrate Witness",
        "authority": "TERRAIN_WITNESS",
        "seal": GEOX_SEAL,
        "version": GEOX_VERSION,
        "profile": GEOX_PROFILE,
        "identity_pass": _is_geox_func() if _is_geox_func else True,
        "canon_9": {
            "quantities": ["rho", "Vp", "Vs", "rho_e", "chi", "k", "P", "T", "phi"],
            "tool_map": {k: v for k, v in sorted(CANON9_TOOL_MAP.items())},
            "description": "EARTH.CANON_9 — nine invariant subsurface quantities. Every tool declares which it touches.",
        },
        "gde_vocabulary": {
            "entries": len(GDE_VOCAB),
            "description": "Geological Depositional Environment vocabulary for paleoenvironment mapping.",
        },
        "strat_standards": {
            "supported": ["NN_zone", "NP_zone", "Stage_Sabah", "Cycle_Sarawak", "custom"],
            "description": "Stratigraphic reference schemes. NN_zone (GPTS2020) is the default anchor.",
        },
        "toac_version": "v1",
        "schema_version": "geox-output-v0.7",
    }
    if _enforce_geox_func:
        enforcement = _enforce_geox_func()
        if enforcement:
            identity_state["_enforcement"] = enforcement
    return identity_state


async def list_geox_apps() -> list[dict]:
    manifest_dir = "control_plane/fastmcp/manifests"
    apps = []
    if os.path.exists(manifest_dir):
        for filename in os.listdir(manifest_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(manifest_dir, filename)) as f:
                        apps.append(json.load(f))
                except Exception as e:
                    logger.error(f"Failed to load manifest {filename}: {e}")
    return apps


async def get_profile_status() -> str:
    return json.dumps(
        {
            "status": "healthy",
            "service": "geox-unified",
            "profile": GEOX_PROFILE,
            "enabled_dimensions": ["prospect", "well", "earth3d", "map", "cross"],
            "version": GEOX_VERSION,
            "seal": GEOX_SEAL,
            "constitutional_floors": "F1-F13 ACTIVE",
        }
    )


async def geox_tree777_index() -> str:
    return json.dumps(_geox_tree777_index(), indent=2)


async def geox_tree777_skill(name: str) -> str:
    file_path = TREE777_SKILLS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Skill not found: {name}", "uri": f"tree777://skills/geox/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://skills/geox/{name}", "content": content}, indent=2)


async def geox_tree777_concept(name: str) -> str:
    file_path = TREE777_CONCEPTS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Concept not found: {name}", "uri": f"tree777://geo/concepts/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://geo/concepts/{name}", "content": content}, indent=2)


async def geox_tree777_scar(name: str) -> str:
    file_path = TREE777_SCAR_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Scar not found: {name}", "uri": f"tree777://geo/scars/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://geo/scars/{name}", "content": content}, indent=2)


async def geox_capabilities() -> str:
    path = RESOURCES_DIR / "capabilities" / "geox_capabilities.json"
    if not path.exists():
        return json.dumps({"error": "Capabilities not found"})
    return path.read_text()


async def geox_resource(category: str, name: str) -> str:
    """Serve any file from the resources/ directory as an MCP resource."""
    allowed_categories = {"ontology", "playbooks", "schemas", "examples", "prompts"}
    if category not in allowed_categories:
        return json.dumps({"error": f"Invalid category: {category}"})

    file_path = RESOURCES_DIR / category / name
    try:
        file_path = file_path.resolve()
        resources_root = RESOURCES_DIR.resolve()
        if not str(file_path).startswith(str(resources_root)):
            return json.dumps({"error": "Invalid resource path"})
    except Exception:
        return json.dumps({"error": "Invalid resource path"})

    if not file_path.exists():
        for ext in [".yaml", ".yml", ".json", ".md", ".csv"]:
            alt = file_path.with_suffix(ext)
            if alt.exists():
                file_path = alt
                break

    if not file_path.exists():
        return json.dumps({"error": f"Resource not found: {category}/{name}"})

    try:
        content = file_path.read_text()
        return json.dumps(
            {
                "uri": f"geox://resources/{category}/{name}",
                "content": content,
                "format": file_path.suffix.lstrip("."),
            }
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to read resource: {e}"})


async def geox_resources_index() -> str:
    index = {}
    for category in ["ontology", "playbooks", "schemas", "examples", "prompts"]:
        cat_dir = RESOURCES_DIR / category
        if cat_dir.exists():
            files = [f.name for f in cat_dir.iterdir() if f.is_file()]
            index[category] = sorted(files)
    return json.dumps(index, indent=2)


# ── Registration ──────────────────────────────────────────────────────────────

def register_resources(mcp: Any, *, is_geox_func=None, enforce_geox_func=None) -> None:
    """Register all GEOX resources on the given FastMCP server."""
    global _is_geox_func, _enforce_geox_func
    _is_geox_func = is_geox_func
    _enforce_geox_func = enforce_geox_func

    mcp.resource("geox://identity")(geox_identity)
    mcp.resource("geox://registry/apps")(list_geox_apps)
    mcp.resource("geox://profile/status")(get_profile_status)
    mcp.resource(
        "tree777://index",
        description=(
            "TREE777 wiki full index. Lists all federation skills, concepts, and scars. "
            "Use this to discover available resources across the arifOS, GEOX, WELL, and WEALTH domains."
        ),
    )(geox_tree777_index)
    mcp.resource(
        "tree777://skills/geox/{name}",
        description=(
            "Individual GEOX skill page from the TREE777 wiki. "
            "Returns markdown content (frontmatter-stripped) with metadata. "
            "Example: tree777://skills/geox/spatial-grounding"
        ),
    )(geox_tree777_skill)
    mcp.resource(
        "tree777://geo/concepts/{name}",
        description=(
            "Geoscience concept page from the TREE777 wiki. "
            "Covers: TREE777, intelligence-tree, mcp-architecture-mapping, etc. "
            "Example: tree777://geo/concepts/TREE777"
        ),
    )(geox_tree777_concept)
    mcp.resource(
        "tree777://geo/scars/{name}",
        description=(
            "GEOX scar/incident record from the TREE777 wiki. "
            "Documents failures and lessons learned for geoscience operations. "
            "Example: tree777://geo/scars/geo-seismic-misread"
        ),
    )(geox_tree777_scar)
    mcp.resource(
        "geox://capabilities",
        description="Full GEOX capability map: tools, domains, claim limits, next best actions. Read at session start.",
    )(geox_capabilities)
    mcp.resource(
        "geox://resources/{category}/{name}",
        description=(
            "Agent knowledge pack: ontology, playbooks, schemas, examples. "
            "Categories: ontology, playbooks, schemas, examples. "
            "Example: geox://resources/ontology/curve_aliases"
        ),
    )(geox_resource)
    mcp.resource(
        "geox://resources/index",
        description="Index of all available resources in the GEOX knowledge pack.",
    )(geox_resources_index)
