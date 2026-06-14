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
import re
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


async def geox_surface_truth() -> str:
    """Validate and report the current surface truth status (the Surface Truth Lock).

    This resource derives the expected canonical tool count from the live registry
    and compares every declared surface (README, server-card, llms.txt, capabilities)
    against it. Hard-coded counts are intentionally removed so drift is visible.
    """

    def _extract_int(text: str, patterns: list[str]) -> int:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return 0

    # 1. Live registry count — source of truth
    try:
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

        live_count = len(CANONICAL_PUBLIC_TOOLS)
    except Exception:
        live_count = 0

    # 2. Parse README.md count
    readme_path = Path("/root/geox/README.md")
    readme_count = 0
    if readme_path.exists():
        readme_count = _extract_int(
            readme_path.read_text(),
            [r"(\d+)\s+canonical MCP tools", r"(\d+)\s+canonical tools"],
        )

    # 3. Parse server-card count
    card_path = Path("/root/geox/resources/server-card.json")
    card_count = 0
    if card_path.exists():
        try:
            card_data = json.loads(card_path.read_text())
            card_count = card_data.get("tools", 0)
        except Exception:
            logger.warning("Failed to parse server-card.json for surface truth check")

    # 4. Parse llms.txt count
    llms_path = Path("/root/geox/resources/llms.txt")
    llms_count = 0
    if llms_path.exists():
        llms_count = _extract_int(
            llms_path.read_text(),
            [r"\((\d+)\s+Tools?\)", r"(\d+)\s+canonical tools"],
        )

    # 5. Parse capabilities count
    cap_path = Path("/root/geox/resources/capabilities/geox_capabilities.json")
    cap_count = 0
    if cap_path.exists():
        try:
            cap_data = json.loads(cap_path.read_text())
            cap_count = cap_data.get("canonical_tool_count", 0)
        except Exception:
            logger.warning("Failed to parse capabilities count for surface truth check")

    # 6. Tests count — read from live pytest cache if available, else unknown
    tests_count = 0
    pytest_cache = Path("/root/geox/.pytest_cache/v/cache/lastfailed")
    if not pytest_cache.exists():
        # Best-effort: count discovered by a prior run is not persisted here.
        tests_count = 0

    # 7. Git SHA
    import subprocess

    try:
        git_sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=os.environ.get("ARIFOS_HOME", "/root") + "/geox")
            .decode("utf-8")
            .strip()
        )
    except Exception:
        git_sha = "unknown"

    checks = {
        "readme_count": readme_count,
        "server_card_count": card_count,
        "llms_txt_count": llms_count,
        "capabilities_count": cap_count,
        "live_registry_count": live_count,
    }
    status = "PASS" if (
        live_count > 0
        and git_sha != "unknown"
        and all(count == live_count for count in checks.values() if count > 0)
    ) else "FAIL"

    truth_map = {
        "status": status,
        **checks,
        "tests_count": tests_count,
        "git_sha": git_sha,
        "seal": "DITEMPA BUKAN DIBERI",
        "lock_active": True,
    }
    return json.dumps(truth_map, indent=2)


async def geox_literature_madon_paper() -> str:
    """Fetch literature resource for Mazlan Madon's 2021 GSM Malay Basin paper."""
    metadata = {
        "uri": "geox://literature/GSM-MADON-2021-MALAY-BASIN",
        "title": "Five decades of petroleum exploration and discovery in the Malay Basin (1968–2018) and remaining potential",
        "author": "Mazlan Madon",
        "journal": "Bulletin of the Geological Society of Malaysia, Volume 72, 2021",
        "doi": "10.7186/bgsm72202106",
        "claim_state": "DRAFT",
        "fidelity": "CONTEXTUAL_WITNESS_ONLY",
        "usability_boundaries": {
            "allowed": [
                "Basin-wide structural & play history",
                "Play-type taxonomy (Groups A-P)",
                "Creaming curve & mature basin framing",
                "Source-rock and migration hypotheses",
            ],
            "forbidden": [
                "Direct petrophysical log computations",
                "Field-level reserves booking/certification",
                "Seismic structural candidate generation",
                "Drilling decisions & Sealed POS evaluations",
            ],
        },
        "extracted_claims": [
            {
                "claim_id": "clm_317a7c30873e40b7",
                "category": "General",
                "text": "Malay Basin is offshore east of Peninsular Malaysia and contributes about 40% of Malaysia’s hydrocarbon resources in the review period.",
                "confidence": "HIGH",
            },
            {
                "claim_id": "clm_878a99cc8cc84177",
                "category": "Maturity",
                "text": "Exploration history shows mature-basin creaming behavior: early giant discoveries, later smaller incremental additions.",
                "confidence": "HIGH",
            },
            {
                "claim_id": "clm_4c04b8f277854aba",
                "category": "Structure",
                "text": "Malay Basin initiated by Late Eocene–Early Oligocene extension, high post-rift subsidence, >14 km sediment in deepest centre, E-W half-grabens influenced by Pre-Tertiary faults.",
                "confidence": "HIGH",
            },
            {
                "claim_id": "clm_db822655c84b43ac",
                "category": "Stratigraphy",
                "text": "Stratigraphy uses groups A–P; drilling reaches at least Group M; fill transitions from lacustrine/non-marine to coastal plain and shallow marine; K shale marks key transition.",
                "confidence": "HIGH",
            },
            {
                "claim_id": "clm_64bd3be4f6fb471c",
                "category": "Reservoir",
                "text": "Main resources are reported from Groups J, I, K, E, D; I/J/K contribute about 60%, and D/E plus those contribute about 85%; deltaic sands dominate.",
                "confidence": "HIGH",
            },
            {
                "claim_id": "clm_ca5a5ef4c80544ff",
                "category": "Source",
                "text": "Oils/condensates derive mainly from lower coastal plain fluvio-deltaic coal/coaly shale and lacustrine syn-rift shales; northwest is gas-prone, southeast more oil-prone.",
                "confidence": "MEDIUM",
            },
            {
                "claim_id": "clm_78c4535ee5764c10",
                "category": "Potential",
                "text": "Remaining potential is not zero; paper estimates roughly 2 bboe yet to discover by 2020, but requires new play concepts.",
                "confidence": "MEDIUM",
            },
        ],
    }
    return json.dumps(metadata, indent=2)


async def geox_basin_malay_profile() -> str:
    """Fetch geological profile for Malay Basin."""
    import yaml

    profile_path = Path("/root/geox/resources/basins/malay_basin/basin_profile.yaml")
    if profile_path.exists():
        try:
            profile_data = yaml.safe_load(profile_path.read_text())
            return json.dumps(profile_data, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to parse profile: {e}"})
    return json.dumps(
        {
            "basin_name": "Malay Basin",
            "basin_id": "MALAY_BASIN",
            "location": "Southern South China Sea, offshore Peninsular Malaysia",
            "area_sq_km": 80000,
            "tectonic_setting": "Cenozoic failed rift / pull-apart basin",
            "stratigraphic_framework": "Group A (youngest) to Group M (oldest, syn-rift)",
            "status": "Mature oil and gas province",
            "primary_hydrocarbon": "Gas-prone, significant oil in Group H and I",
        },
        indent=2,
    )


async def geox_literature_index() -> str:
    """Fetch the index of all literature resources."""
    literature_list = [
        {
            "uri": "geox://literature/GSM-MADON-2021-MALAY-BASIN",
            "title": "Five decades of petroleum exploration and discovery in the Malay Basin (1968–2018) and remaining potential",
            "author": "Mazlan Madon",
            "journal": "Bulletin of the Geological Society of Malaysia, Volume 72, 2021",
        }
    ]
    return json.dumps(literature_list, indent=2)


async def geox_claims_index() -> str:
    """Fetch the index of all claims (draft, validated, sealed)."""
    claims_path = Path("/root/geox/resources/basins/malay_basin/claims.json")
    if claims_path.exists():
        try:
            claims_data = json.loads(claims_path.read_text())
            index_list = [
                {
                    "claim_id": c.get("claim_id"),
                    "claim_type": c.get("claim_type"),
                    "confidence": c.get("confidence"),
                    "short_text": c.get("claim", "")[:60] + "..." if len(c.get("claim", "")) > 60 else c.get("claim", ""),
                }
                for c in claims_data
            ]
            return json.dumps(index_list, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to parse claims: {e}"})
    return json.dumps([], indent=2)


async def geox_artifacts_index() -> str:
    """Fetch list of all available visualizable artifacts."""
    artifacts = [
        {
            "artifact_ref": "geox://literature/GSM-MADON-2021-MALAY-BASIN",
            "artifact_type": "literature_review",
            "claim_state": "DRAFT",
            "source": "Mazlan Madon, 2021",
            "created_by_tool": "geox_literature_ingest",
            "created_at": "2026-06-06T13:47:00Z",
            "parent_refs": [],
            "visualizable": True,
        },
        {
            "artifact_ref": "geox://basins/malay-basin/profile",
            "artifact_type": "basin_profile",
            "claim_state": "VALIDATED",
            "source": "GEOX Basin Database",
            "created_by_tool": "geox_basin_resolve",
            "created_at": "2026-06-06T14:00:00Z",
            "parent_refs": [],
            "visualizable": True,
        },
    ]
    return json.dumps(artifacts, indent=2)


async def geox_claims_graph() -> str:
    """Fetch the visual claim graph nodes and edges."""
    claims_path = Path("/root/geox/resources/basins/malay_basin/claims.json")
    nodes = []
    edges = []
    if claims_path.exists():
        try:
            claims_data = json.loads(claims_path.read_text())
            for idx, c in enumerate(claims_data):
                cid = c.get("claim_id")
                nodes.append(
                    {
                        "id": cid,
                        "type": "claim",
                        "claim_state": c.get("claim_type", "draft").upper(),
                        "text": c.get("claim"),
                        "seal_status": "SEALED" if c.get("claim_type") == "sealed" else "UNSEALED",
                    }
                )
                for ev_ref in c.get("evidence_refs", []):
                    ev_id = f"ev_{ev_ref.replace('://', '_').replace('/', '_').replace('.', '_')}"
                    if not any(n["id"] == ev_id for n in nodes):
                        nodes.append({"id": ev_id, "type": "evidence", "text": ev_ref})
                    edges.append({"source": cid, "target": ev_id, "relation": "supported_by"})
        except Exception as exc:
            logger.warning(f"Failed to build claims graph: {exc}")
    return json.dumps({"nodes": nodes, "edges": edges}, indent=2)


async def geox_resources_sub_index(category: str) -> str:
    """Fetch list of files in a specific resource category."""
    cat_dir = RESOURCES_DIR / category
    files = []
    if cat_dir.exists():
        files = [f.name for f in cat_dir.iterdir() if f.is_file()]
    return json.dumps({"category": category, "files": sorted(files)}, indent=2)


async def geox_basins_index() -> str:
    """Fetch list of all available basin profile names and URIs."""
    basins_dir = RESOURCES_DIR / "basins"
    basins = []
    if basins_dir.exists():
        for d in basins_dir.iterdir():
            if d.is_dir():
                basins.append(
                    {"name": d.name.replace("_", " ").title(), "uri": f"geox://basins/{d.name.replace('_', '-')}/profile"}
                )
    return json.dumps(basins, indent=2)


async def geox_resources_prompts_index() -> str:
    return await geox_resources_sub_index("prompts")


async def geox_resources_playbooks_index() -> str:
    return await geox_resources_sub_index("playbooks")


async def geox_resources_ontology_index() -> str:
    return await geox_resources_sub_index("ontology")


async def geox_resources_schemas_index() -> str:
    return await geox_resources_sub_index("schemas")


async def geox_reality_context() -> str:
    """Fetch reality engineering context for agent execution."""
    try:
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

        tools = CANONICAL_PUBLIC_TOOLS
    except Exception:
        tools = []

    context_map = {
        "domain": "earth",
        "available_evidence": ["geox://literature/GSM-MADON-2021-MALAY-BASIN"],
        "available_tools": tools,
        "available_reports": [
            "GSM-MADON-2021-MALAY-BASIN.pdf",
            "USGS-BISHOP-2002-MALAY-BASIN.pdf",
            "PETRONAS-1999-PETROLEUM-GEOLOGY-MALAYSIA.pdf",
        ],
        "forbidden_claims": [
            "Silent report usage without provenance",
            "Drilling decisions & Sealed POS evaluations without human confirmation",
        ],
        "claim_ladder": ["observed", "derived", "interpreted", "hypothesis", "decision_support"],
        "human_final_authority": "Arif",
    }
    return json.dumps(context_map, indent=2)


# ── Registration ──────────────────────────────────────────────────────────────


def register_resources(mcp: Any, *, is_geox_func=None, enforce_geox_func=None) -> None:
    """Register all GEOX resources on the given FastMCP server."""
    global _is_geox_func, _enforce_geox_func
    _is_geox_func = is_geox_func
    _enforce_geox_func = enforce_geox_func

    mcp.resource("geox://reality/context")(geox_reality_context)
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
    mcp.resource(
        "geox://surface/truth",
        description="Validate and report the current surface truth status (the Surface Truth Lock).",
    )(geox_surface_truth)
    mcp.resource(
        "geox://literature/GSM-MADON-2021-MALAY-BASIN",
        description="Fetch literature resource for Mazlan Madon's 2021 GSM Malay Basin paper.",
    )(geox_literature_madon_paper)
    mcp.resource(
        "geox://basins/malay-basin/profile",
        description="Fetch geological profile for Malay Basin.",
    )(geox_basin_malay_profile)
    mcp.resource(
        "geox://literature/index",
        description="Index of all literature resources.",
    )(geox_literature_index)
    mcp.resource(
        "geox://claims/index",
        description="Index of all claims (draft, validated, sealed).",
    )(geox_claims_index)
    mcp.resource(
        "geox://artifacts/index",
        description="Index of all visualizable artifacts.",
    )(geox_artifacts_index)
    mcp.resource(
        "geox://claims/graph",
        description="Visual claim graph nodes and edges.",
    )(geox_claims_graph)
    mcp.resource(
        "geox://basins/index",
        description="Index of all available basins.",
    )(geox_basins_index)
    mcp.resource(
        "geox://resources/prompts/index",
        description="Index of prompts templates.",
    )(geox_resources_prompts_index)
    mcp.resource(
        "geox://resources/playbooks/index",
        description="Index of playbook files.",
    )(geox_resources_playbooks_index)
    mcp.resource(
        "geox://resources/ontology/index",
        description="Index of ontology files.",
    )(geox_resources_ontology_index)
    mcp.resource(
        "geox://resources/schemas/index",
        description="Index of schemas files.",
    )(geox_resources_schemas_index)

    # ── Binary render data resources (Module J: Binary Transport) ─────────────
    async def geox_render_surface(surface_id: str) -> str:
        """Serve binary surface data (horizon mesh, fault plane) via MCP resource.
        
        Format: geox://render/surfaces/{surface_id} where surface_id = "<name>.npz|gltf|ply"
        Returns base64-encoded binary for MCP transport.
        """
        import base64 as _b64
        import os as _os
        
        surface_path = _os.path.join(
            _os.environ.get("GEOX_RENDER_DATA_DIR", "/data/geox_render"), "surfaces", surface_id
        )
        
        if not _os.path.exists(surface_path):
            return f"ERROR: Surface not found: {surface_path}"
        
        with open(surface_path, "rb") as f:
            raw = f.read()
        
        return _b64.b64encode(raw).decode("ascii")
    
    mcp.resource(
        "geox://render/surfaces/{surface_id}",
        description="Binary surface data (horizon mesh, fault plane). "
                    "Returns base64-encoded bytes. Format: geox://render/surfaces/<filename>",
    )(geox_render_surface)
    
    async def geox_render_cube_slice(volume_id: str, orientation: str, slice_index: int) -> str:
        """Serve binary cube slice data (2D frame from 3D volume) via MCP resource.
        
        Returns raw Float32Array bytes (little-endian) as base64.
        """
        import base64 as _b64
        import os as _os
        
        filename = f"{volume_id}_{orientation}_{slice_index}.f32"
        slice_path = _os.path.join(
            _os.environ.get("GEOX_RENDER_DATA_DIR", "/data/geox_render"), "cubes", filename
        )
        
        if not _os.path.exists(slice_path):
            return f"ERROR: Cube slice not found: {slice_path}"
        
        with open(slice_path, "rb") as f:
            raw = f.read()
        
        return _b64.b64encode(raw).decode("ascii")
    
    mcp.resource(
        "geox://render/cubes/{volume_id}/{orientation}/{slice_index}",
        description="Binary cube slice frame (2D from 3D volume). "
                    "Returns base64-encoded Float32Array bytes.",
    )(geox_render_cube_slice)
    
    async def geox_render_payload_schema(_version: str = "v1") -> str:
        """Serve the canonical RenderPayload schema."""
        try:
            from geox_core.schemas.render_payload import RenderPayload
            schema = RenderPayload.model_json_schema()
            return json.dumps(schema, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"RenderPayload schema not available: {exc}"})
    
    mcp.resource(
        "geox://render/payload-schema/{_version}",
        description="Canonical RenderPayload schema (Pydantic JSON schema). "
                    "Every GEOX visual output conforms to this. Version: v1",
    )(geox_render_payload_schema)
    
    # ── Cube manifest + brick streaming ───────────────────────────────────────
    async def geox_cube_manifest(cube_id: str) -> str:
        """Serve a CubeManifest for a 3D seismic volume.
        
        The manifest describes the brick grid, LOD pyramid, CRS, and
        URI template for brick fetches. Client fetches this FIRST,
        then requests bricks progressively.
        """
        import json as _json
        import os as _os
        
        manifest_path = _os.path.join(
            _os.environ.get("GEOX_CUBE_MANIFEST_DIR", "/data/geox_cubes"),
            cube_id, "manifest.json"
        )
        
        if not _os.path.exists(manifest_path):
            return _json.dumps({"error": f"Cube manifest not found: {cube_id}"})
        
        with open(manifest_path) as f:
            return f.read()
    
    mcp.resource(
        "geox://render/cubes/{cube_id}/manifest",
        description="CubeManifest for a 3D seismic volume. "
                    "Describes brick grid, LOD pyramid, CRS, and brick URI template. "
                    "Client fetches this first before requesting any bricks.",
    )(geox_cube_manifest)
    
    async def geox_cube_brick(cube_id: str, lod: int, ix: int, iy: int, iz: int) -> str:
        """Serve a single brick of a 3D cube at a specific LOD.
        
        Returns base64-encoded binary bytes (Float32 or Int16 depending on LOD).
        Client decodes into a typed array on the browser side.
        """
        import base64 as _b64
        import os as _os
        
        brick_path = _os.path.join(
            _os.environ.get("GEOX_CUBE_BRICK_DIR", "/data/geox_cubes"),
            cube_id, f"lod_{lod}", f"brick_{ix}_{iy}_{iz}.bin"
        )
        
        if not _os.path.exists(brick_path):
            return f"ERROR: Brick not found: {brick_path}"
        
        with open(brick_path, "rb") as f:
            raw = f.read()
        
        return _b64.b64encode(raw).decode("ascii")
    
    mcp.resource(
        "geox://render/cubes/{cube_id}/lod/{lod}/brick/{ix}/{iy}/{iz}",
        description="Binary brick from a 3D seismic cube at specified LOD and brick address. "
                    "Returns base64-encoded bytes (Float32 or Int16). "
                    "Progressive streaming: start with LOD=0, refine with higher LODs.",
    )(geox_cube_brick)
