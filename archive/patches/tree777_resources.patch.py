# ═══════════════════════════════════════════════════════════════════════════════
# TREE777 WIKI RESOURCES (Federation Canonical Knowledge Tree)
# ═══════════════════════════════════════════════════════════════════════════════
# Exposes GEOX-domain slice of the canonical TREE777 wiki as MCP Resources.
#
# URI scheme:
#   tree777://skills/geox/{name}   — GEOX skill pages
#   tree777://geo/concepts/{name}  — Geoscience concept pages
#   tree777://geo/scars/{name}     — GEOX scar/incident records
#
# Wiki root: /root/AAA/wiki (shared across all 4 federation servers)
# Rule: Resources grow. Tools stay bounded. Judgment remains Arif.
# DITEMPA BUKAN DIBERI — Intelligence is forged, not given.

TREE777_WIKI_ROOT = Path(os.environ.get("TREE777_WIKI_ROOT", "/root/AAA/wiki"))
TREE777_SKILLS_DIR = TREE777_WIKI_ROOT / "skills" / "geox"
TREE777_CONCEPTS_DIR = TREE777_WIKI_ROOT / "concepts"
TREE777_SCAR_DIR = TREE777_WIKI_ROOT / "scars"


def _geox_read_wiki_file(file_path: str | Path) -> str:
    """Read a wiki file, returning frontmatter-stripped content."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {path}"
    content = path.read_text()
    # Strip YAML frontmatter
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
            # GEOX-domain concepts: spatial-grounding, petrophysics, etc.
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


@mcp.resource(
    "tree777://index",
    description=(
        "TREE777 wiki full index. Lists all federation skills, concepts, and scars. "
        "Use this to discover available resources across the arifOS, GEOX, WELL, and WEALTH domains."
    ),
)
async def geox_tree777_index() -> str:
    return json.dumps(_geox_tree777_index(), indent=2)


@mcp.resource(
    "tree777://skills/geox/{name}",
    description=(
        "Individual GEOX skill page from the TREE777 wiki. "
        "Returns markdown content (frontmatter-stripped) with metadata. "
        "Example: tree777://skills/geox/spatial-grounding"
    ),
)
async def geox_tree777_skill(name: str) -> str:
    file_path = TREE777_SKILLS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Skill not found: {name}", "uri": f"tree777://skills/geox/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://skills/geox/{name}", "content": content}, indent=2)


@mcp.resource(
    "tree777://geo/concepts/{name}",
    description=(
        "Geoscience concept page from the TREE777 wiki. "
        "Covers: TREE777, intelligence-tree, mcp-architecture-mapping, etc. "
        "Example: tree777://geo/concepts/TREE777"
    ),
)
async def geox_tree777_concept(name: str) -> str:
    file_path = TREE777_CONCEPTS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Concept not found: {name}", "uri": f"tree777://geo/concepts/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://geo/concepts/{name}", "content": content}, indent=2)


@mcp.resource(
    "tree777://geo/scars/{name}",
    description=(
        "GEOX scar/incident record from the TREE777 wiki. "
        "Documents failures and lessons learned for geoscience operations. "
        "Example: tree777://geo/scars/geo-seismic-misread"
    ),
)
async def geox_tree777_scar(name: str) -> str:
    file_path = TREE777_SCAR_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Scar not found: {name}", "uri": f"tree777://geo/scars/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://geo/scars/{name}", "content": content}, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY MCP HANDLER (for backward compatibility with existing POST /mcp callers)
# ═══════════════════════════════════════════════════════════════════════════════
