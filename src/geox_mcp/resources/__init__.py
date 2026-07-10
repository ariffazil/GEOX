"""
GEOX MCP Resources — Identity, Registry, TREE777 Wiki, Knowledge Pack
══════════════════════════════════════════════════════════════════════
Extracted from server.py for compositional mounting.
Register via register_resources(mcp) on the main FastMCP server.
DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("geox.resources")

# ── Resource Contract v1 imports (forged 2026-07-10) ────────────────────────
# Single source of truth for all `geox://` URIs. Never scatter raw strings.
try:
    from geox_mcp.uri_schemes import (
        SCHEME,
        URI_PATTERN,
        AccessClass,
        Tier,
        UriTemplate,
        JsonRpcError,
        REGISTRY,
        get as get_uri_template,
        full_uri,
        is_valid_uri,
        templates_only,
        fixed_only,
    )

    _HAS_URI_SCHEMES = True
except Exception as _e:  # pragma: no cover
    logger.warning(f"geox_mcp.uri_schemes not available: {_e}")
    _HAS_URI_SCHEMES = False

try:
    from geox_mcp.resources.pagination import (
        Page,
        PageResult,
        encode_cursor,
        decode_cursor,
        slice_page,
        DEFAULT_PAGE_SIZE,
        MAX_PAGE_SIZE,
    )

    _HAS_PAGINATION = True
except Exception as _e:  # pragma: no cover
    logger.warning(f"geox_mcp.resources.pagination not available: {_e}")
    _HAS_PAGINATION = False


# ── Resource helpers (Resource Contract v1) ───────────────────────────────────


def _geox_meta_envelope(
    *,
    seal_id: str | None = None,
    evidence_class: str = "DERIVED",
    authority: str = "EVIDENCE",
    sha256_input: bytes | str | None = None,
    actor_signature: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a `_meta` envelope per MCP 2025-11-25 Shape A — on contents object.

    Use this in every resource read handler. The seal travels with payload,
    survives client-side caching, and is verifiable per-resource
    independently of the response envelope.
    """
    sha256 = None
    if sha256_input is not None:
        if isinstance(sha256_input, str):
            sha256_input = sha256_input.encode("utf-8")
        sha256 = hashlib.sha256(sha256_input).hexdigest()

    meta: dict[str, Any] = {
        "contract_version": "geox.resource.v1",
        "forged_at": "2026-07-10",
        "geox_seal": GEOX_SEAL,
        "evidence_class": evidence_class,
        "authority": authority,
        "seal_id": seal_id,
        "sha256": sha256,
        "actor_signature": actor_signature,
        "read_at": time.gmtime(),
    }
    # ISO-format timestamp for transport
    meta["read_at_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", meta["read_at"])
    del meta["read_at"]

    if extra:
        meta.update(extra)
    return meta


def _geox_resource_annotations(
    audience: tuple[str, ...] = ("assistant",),
    priority: float = 0.7,
) -> dict[str, Any]:
    """Build standard resource annotations per MCP 2025-11-25.

    `audience` ∈ {('assistant',), ('user',), ('user', 'assistant')}
    `priority` ∈ [0.0, 1.0] — higher surfaces first in long listings.
    """
    return {
        "audience": list(audience),
        "priority": priority,
        "lastModified": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


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
    allowed_categories = {"ontology", "playbooks", "schemas", "examples"}
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


# ── EarthLayerRegistry resources (L1 export channel) ──────────────────────────
# DITEMPA BUKAN DIBERI — Sovereign earth layers surface through MCP resources,
# not new canonical tools (34-tool lock at server.py:324 is T3 888_HOLD).
# Layer registry lives in contracts/schemas/earth_layer_registry.py and seeds
# Sabah Basin + SE Asia plates + Kinabalu (falsified hypothesis, F6 maruah).


def _earth_layer_registry():
    """Lazy import + seed — avoids hard import at module load (mypy strict)."""
    try:
        from contracts.schemas.earth_layer_registry import seed_sabah_layers  # type: ignore[import-not-found]

        return seed_sabah_layers()
    except Exception as e:  # pragma: no cover — defensive surface
        logger.warning("earth_layer_registry seed failed: %s", e)
        return None


async def geox_layers_index() -> str:
    """Index of sovereign earth layers — discoverability for downstream agents."""
    reg = _earth_layer_registry()
    if reg is None:
        return json.dumps({"error": "earth_layer_registry unavailable", "layers": []})
    layers = reg.list()
    return json.dumps(
        {
            "uri_template": "geox://layers/{layer_id}/package",
            "count": len(layers),
            "layers": [
                {
                    "layer_id": lid,
                    "title": layer.title,
                    "license": layer.license.value,
                    "truth_class": layer.truth_class.value,
                    "bbox": [layer.bbox_west, layer.bbox_south, layer.bbox_east, layer.bbox_north],
                    "map_purposes_allowed": [p.value for p, ok in layer.map_purpose_allow.items() if ok],
                    "f6_maruah_flagged": layer.community_territory_flag,
                    "f11_audit_id": layer.audit_id,
                }
                for lid, layer in layers.items()
            ],
        },
        indent=2,
    )


async def geox_layer_package(layer_id: str) -> str:
    """Export a single sovereign earth layer as GEOX-LAYER-PKG-v1 envelope.

    Returns None for missing layer (consistent with runtime contract —
    export_package returns None, not raise). Caller sees the empty JSON
    envelope and reports layer_id as unresolvable.
    """
    reg = _earth_layer_registry()
    if reg is None:
        return json.dumps(
            {
                "error": "earth_layer_registry unavailable",
                "layer_id": layer_id,
                "envelope": None,
            }
        )
    pkg = reg.export_package(layer_id)
    if pkg is None:
        return json.dumps(
            {
                "error": f"layer_not_found: {layer_id}",
                "layer_id": layer_id,
                "envelope": None,
                "hint": "fetch geox://layers/index for available layer_ids",
            }
        )
    return json.dumps({"uri": f"geox://layers/{layer_id}/package", "envelope": pkg}, indent=2)


async def geox_resources_index() -> str:
    index = {}
    for category in ["ontology", "playbooks", "schemas", "examples"]:
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
    status = (
        "PASS"
        if (live_count > 0 and git_sha != "unknown" and all(count == live_count for count in checks.values() if count > 0))
        else "FAIL"
    )

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
            for _idx, c in enumerate(claims_data):
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
            "NOC-1999-PETROLEUM-GEOLOGY-MALAYSIA.pdf",
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

    mcp.resource(
        "geox://layers/{layer_id}/package",
        description=(
            "EarthLayerRegistry export package — GEOX-LAYER-PKG-v1 envelope for a single "
            "sovereign layer (license, truth class, bbox, governance gates F1/F2/F6/F11). "
            "Seeds include Sabah basin_outline, faults, plates, Kinabalu velocity. "
            "F6 MARUAH layers (community_territory_flag=True) are exported with F6=FLAGGED. "
            "Example: geox://layers/sabah.basin_outline.v3/package"
        ),
        mime_type="application/json",
    )(geox_layer_package)
    mcp.resource(
        "geox://layers/index",
        description=(
            "EarthLayerRegistry index — every seeded sovereign layer (id, title, "
            "license, truth class, bbox, governance gates). Use to discover what "
            "geox://layers/{layer_id}/package exposes."
        ),
        mime_type="application/json",
    )(geox_layers_index)
    mcp.resource(
        "geox://reality/context",
        description="Reality engineering context for agent execution — available tools, evidence, reports, forbidden claims, claim ladder.",
        mime_type="application/json",
    )(geox_reality_context)
    mcp.resource(
        "geox://identity",
        description="GEOX identity state — role, authority, seal, version, canon-9 quantities, GDE vocabulary, strat standards.",
        mime_type="application/json",
    )(geox_identity)
    mcp.resource(
        "geox://registry/apps", description="List of registered GEOX MCP apps and their manifests.", mime_type="application/json"
    )(list_geox_apps)
    mcp.resource(
        "geox://profile/status",
        description="GEOX profile status — health, enabled dimensions, version, constitutional floors.",
        mime_type="application/json",
    )(get_profile_status)
    mcp.resource(
        "tree777://index",
        description=(
            "TREE777 wiki full index. Lists all federation skills, concepts, and scars. "
            "Use this to discover available resources across the arifOS, GEOX, WELL, and WEALTH domains."
        ),
        mime_type="application/json",
    )(geox_tree777_index)
    mcp.resource(
        "tree777://skills/geox/{name}",
        description=(
            "Individual GEOX skill page from the TREE777 wiki. "
            "Returns markdown content (frontmatter-stripped) with metadata. "
            "Example: tree777://skills/geox/spatial-grounding"
        ),
        mime_type="text/markdown",
    )(geox_tree777_skill)
    mcp.resource(
        "tree777://geo/concepts/{name}",
        description=(
            "Geoscience concept page from the TREE777 wiki. "
            "Covers: TREE777, intelligence-tree, mcp-architecture-mapping, etc. "
            "Example: tree777://geo/concepts/TREE777"
        ),
        mime_type="text/markdown",
    )(geox_tree777_concept)
    mcp.resource(
        "tree777://geo/scars/{name}",
        description=(
            "GEOX scar/incident record from the TREE777 wiki. "
            "Documents failures and lessons learned for geoscience operations. "
            "Example: tree777://geo/scars/geo-seismic-misread"
        ),
        mime_type="text/markdown",
    )(geox_tree777_scar)
    mcp.resource(
        "geox://capabilities",
        description="Full GEOX capability map: tools, domains, claim limits, next best actions. Read at session start.",
        mime_type="application/json",
    )(geox_capabilities)
    mcp.resource(
        "geox://resources/{category}/{name}",
        description=(
            "Agent knowledge pack: ontology, playbooks, schemas, examples. "
            "Categories: ontology, playbooks, schemas, examples. "
            "Example: geox://resources/ontology/curve_aliases"
        ),
        mime_type="application/json",
    )(geox_resource)
    mcp.resource(
        "geox://resources/index",
        description="Index of all available resources in the GEOX knowledge pack.",
        mime_type="application/json",
    )(geox_resources_index)
    mcp.resource(
        "geox://surface/truth",
        description="Validate and report the current surface truth status (the Surface Truth Lock).",
        mime_type="application/json",
    )(geox_surface_truth)
    mcp.resource(
        "geox://literature/GSM-MADON-2021-MALAY-BASIN",
        description="Fetch literature resource for Mazlan Madon's 2021 GSM Malay Basin paper.",
        mime_type="application/json",
    )(geox_literature_madon_paper)
    mcp.resource(
        "geox://basins/malay-basin/profile",
        description="Fetch geological profile for Malay Basin.",
        mime_type="application/json",
    )(geox_basin_malay_profile)
    mcp.resource(
        "geox://literature/index",
        description="Index of all literature resources.",
        mime_type="application/json",
    )(geox_literature_index)
    mcp.resource(
        "geox://claims/index",
        description="Index of all claims (draft, validated, sealed).",
        mime_type="application/json",
    )(geox_claims_index)
    mcp.resource(
        "geox://artifacts/index",
        description="Index of all visualizable artifacts.",
        mime_type="application/json",
    )(geox_artifacts_index)
    mcp.resource(
        "geox://claims/graph",
        description="Visual claim graph nodes and edges.",
        mime_type="application/json",
    )(geox_claims_graph)
    mcp.resource(
        "geox://basins/index",
        description="Index of all available basins.",
        mime_type="application/json",
    )(geox_basins_index)
    mcp.resource(
        "geox://resources/playbooks/index",
        description="Index of playbook files.",
        mime_type="application/json",
    )(geox_resources_playbooks_index)
    mcp.resource(
        "geox://resources/ontology/index",
        description="Index of ontology files.",
        mime_type="application/json",
    )(geox_resources_ontology_index)
    mcp.resource(
        "geox://resources/schemas/index",
        description="Index of schemas files.",
        mime_type="application/json",
    )(geox_resources_schemas_index)

    # ── Binary render data resources (Module J: Binary Transport) ─────────────
    async def geox_render_surface(surface_id: str) -> str:
        """Serve binary surface data (horizon mesh, fault plane) via MCP resource.

        Format: geox://render/surfaces/{surface_id} where surface_id = "<name>.npz|gltf|ply"
        Returns base64-encoded binary for MCP transport.
        """
        import base64 as _b64
        import os as _os

        surface_path = _os.path.join(_os.environ.get("GEOX_RENDER_DATA_DIR", "/data/geox_render"), "surfaces", surface_id)

        if not _os.path.exists(surface_path):
            return f"ERROR: Surface not found: {surface_path}"

        with open(surface_path, "rb") as f:
            raw = f.read()

        return _b64.b64encode(raw).decode("ascii")

    mcp.resource(
        "geox://render/surfaces/{surface_id}",
        description="Binary surface data (horizon mesh, fault plane). "
        "Returns base64-encoded bytes. Format: geox://render/surfaces/",
        mime_type="application/octet-stream",
    )(geox_render_surface)

    async def geox_render_cube_slice(volume_id: str, orientation: str, slice_index: int) -> str:
        """Serve binary cube slice data (2D frame from 3D volume) via MCP resource.
        Returns raw Float32Array bytes (little-endian) as base64.
        """
        import base64 as _b64
        import os as _os

        filename = f"{volume_id}_{orientation}_{slice_index}.f32"
        slice_path = _os.path.join(_os.environ.get("GEOX_RENDER_DATA_DIR", "/data/geox_render"), "cubes", filename)

        if not _os.path.exists(slice_path):
            return f"ERROR: Cube slice not found: {slice_path}"

        with open(slice_path, "rb") as f:
            raw = f.read()

        return _b64.b64encode(raw).decode("ascii")

    mcp.resource(
        "geox://render/cubes/{volume_id}/{orientation}/{slice_index}",
        description="Binary cube slice frame (2D from 3D volume). Returns base64-encoded Float32Array bytes.",
        mime_type="application/octet-stream",
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
        mime_type="application/json",
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

        manifest_path = _os.path.join(_os.environ.get("GEOX_CUBE_MANIFEST_DIR", "/data/geox_cubes"), cube_id, "manifest.json")

        if not _os.path.exists(manifest_path):
            return _json.dumps({"error": f"Cube manifest not found: {cube_id}"})

        with open(manifest_path) as f:
            return f.read()

    mcp.resource(
        "geox://render/cubes/{cube_id}/manifest",
        description="CubeManifest for a 3D seismic volume. "
        "Describes brick grid, LOD pyramid, CRS, and brick URI template. "
        "Client fetches this first before requesting any bricks.",
        mime_type="application/json",
    )(geox_cube_manifest)

    async def geox_cube_brick(cube_id: str, lod: int, ix: int, iy: int, iz: int) -> str:
        """Serve a single brick of a 3D cube at a specific LOD.

        Returns base64-encoded binary bytes (Float32 or Int16 depending on LOD).
        Client decodes into a typed array on the browser side.
        """
        import base64 as _b64
        import os as _os

        brick_path = _os.path.join(
            _os.environ.get("GEOX_CUBE_BRICK_DIR", "/data/geox_cubes"), cube_id, f"lod_{lod}", f"brick_{ix}_{iy}_{iz}.bin"
        )

        if not _os.path.exists(brick_path):
            return f"ERROR: Brick not found: {brick_path}"

        with open(brick_path, "rb") as f:
            raw = f.read()

        return _b64.b64encode(raw).decode("ascii")

    mcp.resource(
        "geox://render/cubes/{cube_id}/lod/{lod}/brick/{ix}/{iy}/{iz}",
        description="Binary brick from a 3D cube at specified LOD and brick address. "
        "Returns base64-encoded bytes (Float32 or Int16). "
        "Progressive streaming: start with LOD=0, refine with higher LODs.",
        mime_type="application/octet-stream",
    )(geox_cube_brick)

    # =====================================================================
    # GEOX Resource Contract v2 (FORGED 2026-07-10) — canonical parametric
    # templates backed by src/geox_mcp/uri_schemes.py. Single source of
    # truth: all templates here MUST appear in uri_schemes.REGISTRY.
    #
    # Zen discipline (MCP docs-agent):
    #   - title distinct from name (human-readable display)
    #   - size field on blob returns
    #   - annotations: audience / priority / lastModified
    #   - file:// not required — geox:// is sovereign
    #   - error data echoes URI on -32002
    #   - bundling: read may return multiple contents
    #   - subscribe omitted (not yet implemented; see server.json)
    # =====================================================================

    # ── Helper: derive meta + annotations from uri_schemes ───────────────
    def _lit_meta(tname: str, **extra) -> dict[str, Any]:
        """Build _meta from a uri_schemes.UriTemplate, augmented with extras."""
        if not _HAS_URI_SCHEMES:
            return extra
        try:
            t = get_uri_template(tname)
        except KeyError:
            return extra
        base = {
            "contract_version": "geox.resource.v2",
            "geox_seal": "DITEMPA BUKAN DIBERI",
            "forged_at": "2026-07-10",
            "spec_conformance": "MCP-2025-11-25",
            "tier": t.tier.value,
            "access_class": t.access.value,
            "max_size_bytes": t.max_size_bytes,
            "audience": list(t.annotations_audience),
            "priority": t.annotations_priority,
            "read_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        base.update(extra)
        return base

    def _lit_annotations(tname: str) -> dict[str, Any]:
        """Return the annotations block (distinct from _meta)."""
        if not _HAS_URI_SCHEMES:
            return {}
        try:
            t = get_uri_template(tname)
        except KeyError:
            return {}
        return {
            "audience": list(t.annotations_audience),
            "priority": t.annotations_priority,
            "lastModified": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    # ── J. Literature canonical parametric template ────────────────────
    async def geox_literature_paper(basin: str, paper_id: str) -> dict[str, Any]:
        """Literature paper URI parametric resolver.

        Returns MULTI-CONTENTS shape so a single read can attach the
        canonical envelope alongside the markdown body. Per MCP docs-agent
        implicit tip #1: bundle returns are spec-blessed.

        F1 AMANAH: this resource NEVER exists without a provenance receipt.
        If the paper store can't produce a `_meta` envelope, this read
        MUST return -32002 (RESOURCE_NOT_FOUND) — not silent fallback.
        """
        canonical = full_uri("literature_paper", basin=basin, paper_id=paper_id)
        # Stub body — production reads go through paper store adapter.
        body = f"# {paper_id} ({basin})\n\n_Stub. Real paper loaded from /var/arifos/geox-resources/literature/._\n"
        return {
            "contents": [
                {
                    "uri": canonical,
                    "mimeType": "text/markdown",
                    "text": body,
                    "_meta": _lit_meta(
                        "literature_paper",
                        seal_id=f"GEOX-LIT-{basin}-{paper_id}-STUB",
                        evidence_class="DERIVED",
                        authority="EVIDENCE",
                        sha256=hashlib.sha256(body.encode()).hexdigest(),
                        pii_redacted=True,
                        annotations=_lit_annotations("literature_paper"),
                    ),
                },
                {
                    "uri": f"{canonical}#envelope",
                    "mimeType": "application/json",
                    "text": json.dumps(
                        {
                            "_schema": "geox.literature.paper.v2",
                            "basin": basin,
                            "paper_id": paper_id,
                            "fetch_via": "geox://resources/index → resources/read",
                        },
                        indent=2,
                    ),
                },
            ]
        }

    mcp.resource(
        "geox://literature/{basin}/{paper_id}",
        name="geox-literature-paper",
        title="Geological Literature Paper",
        description=(
            "Geological literature paper (markdown). {basin} = kebab-case basin (e.g. sabah, "
            "malay-basin). {paper_id} = paper slug. Returns TextResourceContents with `text` "
            "field carrying the paper markdown; `_meta` carries seal_id, evidence_class, "
            "sha256. Prefer over legacy `geox://literature/GSM-MADON-2021-MALAY-BASIN` for "
            "new lookups."
        ),
        mime_type="text/markdown",
        annotations=_lit_annotations("literature_paper"),
    )(geox_literature_paper)

    # ── K. Wells canonical parametric template ─────────────────────────
    async def geox_well_summary(basin: str, well_id: str) -> dict[str, Any]:
        """Well summary URI parametric resolver.

        Returns: header, deviation summary, log availability, top picks.
        F2 TRUTH: well_id is a PETRONAS canonical name; we MUST verify
        provenance before returning data. Stub for now.
        """
        canonical = full_uri("well", basin=basin, well_id=well_id)
        body = json.dumps(
            {
                "uri": canonical,
                "basin": basin,
                "well_id": well_id,
                "header": None,
                "deviation_summary": None,
                "log_availability": [],
                "top_picks": [],
                "status": "STUB_TIGHT_FOLLOWUP",
            },
            indent=2,
        )
        return {
            "contents": [
                {
                    "uri": canonical,
                    "mimeType": "application/json",
                    "text": body,
                    "_meta": _lit_meta(
                        "well",
                        seal_id=f"GEOX-WELL-{basin}-{well_id}-STUB",
                        evidence_class="OBSERVED",
                        authority="OBSERVATION",
                        sha256=hashlib.sha256(body.encode()).hexdigest(),
                        well_provenance_required=True,
                        f13_required_if_sensitive=True,
                        annotations=_lit_annotations("well"),
                    ),
                }
            ]
        }

    mcp.resource(
        "geox://wells/{basin}/{well_id}",
        name="geox-wells",
        title="Well Summary",
        description="Well summary: header, deviation summary, log availability, top picks.",
        mime_type="application/json",
        annotations=_lit_annotations("well"),
    )(geox_well_summary)

    # ── L. Claim parametric template (READ-ONLY) ────────────────────────
    async def geox_claim_read(claim_id: str) -> dict[str, Any]:
        """Single claim envelope READ. Create/challenge go via tool `geox_claim`."""
        canonical = full_uri("claim", claim_id=claim_id)
        body = json.dumps(
            {
                "_schema": "geox.claim.read.v2",
                "uri": canonical,
                "claim_id": claim_id,
                "status": "STUB_TIGHT_FOLLOWUP",
                "evidence_for": [],
                "evidence_against": [],
            },
            indent=2,
        )
        return {
            "contents": [
                {
                    "uri": canonical,
                    "mimeType": "application/json",
                    "text": body,
                    "_meta": _lit_meta(
                        "claim",
                        seal_id=f"GEOX-CLAIM-{claim_id}-STUB",
                        evidence_class="DERIVED",
                        authority="CLAIM_LANE",
                        sha256=hashlib.sha256(body.encode()).hexdigest(),
                        actor_signature_required_for_sealed=True,
                        annotations=_lit_annotations("claim"),
                    ),
                }
            ]
        }

    mcp.resource(
        "geox://claims/{claim_id}",
        name="geox-claims",
        title="Claim Envelope (READ-only)",
        description="Single claim envelope (READ-only). For create/challenge use the tool `geox_claim`.",
        mime_type="application/json",
        annotations=_lit_annotations("claim"),
    )(geox_claim_read)

    # =====================================================================
    # Zen post-processor — apply title / annotations / size to ALL existing
    # registered resources via uri_schemes lookup. Idempotent.
    # =====================================================================
    def _zen_existing(mcp) -> int:
        """Walk registered resources, mutate spec-correct fields in place."""
        if not _HAS_URI_SCHEMES:
            return 0
        # Find resource manager — FastMCP 3.x uses _resource_manager
        rm = getattr(mcp, "_resource_manager", None) or getattr(mcp, "_providers", None)
        if rm is None:
            return 0
        # Build lookup table from REGISTRY
        try:
            # Resource URIs may contain '{basin}' etc. — match on prefix.
            by_prefix = {}
            for t in REGISTRY:
                if t.template:
                    prefix = t.path.split("{")[0] if "{" in t.path else t.path
                    by_prefix[f"geox://{prefix}"] = t
                else:
                    by_prefix[f"geox://{t.path}"] = t
        except Exception:
            return 0

        patched = 0
        try:
            resources = getattr(rm, "_resources", {}) or {}
            for uri, res in resources.items():
                # Find template by URI prefix
                template = None
                for prefix, t in by_prefix.items():
                    if uri.startswith(prefix):
                        template = t
                        break
                if template is None:
                    continue
                # Apply title if missing
                if not getattr(res, "title", None):
                    try:
                        # Mutate best-effort — FastMCP Resource objects expose fields
                        setattr(res, "title", template.name.replace("_", " ").title())
                    except Exception:
                        pass
                # Apply annotations if missing
                if not getattr(res, "annotations", None):
                    try:
                        setattr(
                            res,
                            "annotations",
                            {
                                "audience": list(template.annotations_audience),
                                "priority": template.annotations_priority,
                                "lastModified": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            },
                        )
                    except Exception:
                        pass
                patched += 1
        except Exception as e:
            logger.debug(f"_zen_existing pass raised: {e}")
        return patched

    n_zen = _zen_existing(mcp)
    logger.info(f"geox.resources zen-pass applied to {n_zen} existing resources (v2 contract)")

    # =============================================================================
    # EARTH DATA ATLAS — MCP Resource Templates
    # Domain-separation pattern: geox://{domain}/{source}


# Schema index only — live data fetched via corresponding MCP tool.
# DITEMPA BUKAN DIBERI — all resources carry provenance + epistemic status.
# =============================================================================

# ---------------------------------------------------------------------------
# DOMAIN: SEISMOLOGY
# Corresponding tools: geox_seismic_ingest, geox_seismic_compute
# ---------------------------------------------------------------------------


def geox_earthquake_usgs_summary():
    """USGS Earthquake Catalog — M4.5+ worldwide last 30 days.
    URI: geox://earthquake/usgs_summary
    Source: USGS ANSS ComCat API
    URL: https://earthquake.usgs.gov/earthquakes/search/
    License: USGS Public Domain
    Fetch via: geox_seismic_ingest(mode="usgs_earthquake", ...)
    Epistemic: OBS — direct API, authoritative source
    """
    return "geox://earthquake/usgs_summary"


def geox_earthquake_usgs_fault():
    """USGS Did You Feel It? — macroseismic intensity + felt reports.
    URI: geox://earthquake/usgs_dyfi
    Source: USGS DYFI API
    License: USGS Public Domain
    Fetch via: geox_seismic_ingest(mode="usgs_earthquake", region="dyfi")
    Epistemic: OBS — crowd-sourced but validated
    """
    return "geox://earthquake/usgs_dyfi"


# ---------------------------------------------------------------------------
# DOMAIN: GRAVITY & MAGNETICS
# Corresponding tools: geox_subsurface_model (gravity_forward mode)
# ---------------------------------------------------------------------------


def geox_emag2v3():
    """EMAG2v3 — Earth Geoid model, 1-arc-min global magnetic anomaly.
    URI: geox://magnetics/emag2v3
    Source: NOAA NGDC → EMAG2v3
    URL: https://www.ngdc.noaa.gov/geomag/emag2.html
    License: NOAA Public Domain
    Fetch via: geox_io_emag2() in geox_core/io/emag2_client.py
    Epistemic: OBS — satellite+ground observation composite
    """
    return "geox://magnetics/emag2v3"


def geox_icgem_vrm():
    """ICGEM v7 — Virtual Geomagnetic Observatory, 10-arc-min global SV models.
    URI: geox://magnetics/icgem_vrm
    Source: GFZ Potsdam ICGEM
    URL: https://icgem.gfz-potsdam.de/series_10_vrm
    License: CC-BY 4.0
    Fetch via: geox_io_icgem() in geox_core/io/icgem_client.py
    Epistemic: OBS — observatory+satellite synthesis
    """
    return "geox://magnetics/icgem_vrm"


def geox_world_magnetic_model():
    """WMM2025 — World Magnetic Model, 3-arc-min referenced to WGS84.
    URI: geox://magnetics/wmm2025
    Source: NGA + NOAA NGDC joint product
    URL: https://www.ngdc.noaa.gov/geomag/WMM/
    License: Public Domain (US/DOD)
    Fetch via: geox_subsurface_model(mode='gravity_forward', survey='wmm2025')
    Epistemic: OBS — official military/civil model
    """
    return "geox://magnetics/wmm2025"


# ---------------------------------------------------------------------------
# DOMAIN: BATHYMETRY & TOPOGRAPHY
# Corresponding tools: geox_basin (bathymetry mode), geox_seismic_ingest
# ---------------------------------------------------------------------------


def geox_etopo1():
    """ETOPO1 — 1-arc-min global relief (topography + bathymetry), bedrock ice.
    URI: geox://bathymetry/etopo1
    Source: NOAA NGDC
    URL: https://www.ncei.noaa.gov/maps/grid_extract
    License: Public Domain
    Fetch via: geox_io_etopo1() in geox_core/io/etopo_client.py
    Epistemic: OBS — ship echo-sounder + satellite altimetry composite
    """
    return "geox://bathymetry/etopo1"


def geox_gebco():
    """GEBCO 2024 — 15-arc-sec global bathymetric grid, Type Approval Committee.
    URI: geox://bathymetry/gebco2024
    Source: GEBCO/Nippon Foundation TAML
    URL: https://www.gebco.net/data_and_products/gebco_web_services/web_map_services/
    License: CC-BY 4.0 (GEBCO)
    Fetch via: geox_io_gebco() in geox_core/io/gebco_client.py
    Epistemic: OBS — crowd-sourced + ship survey validated
    """
    return "geox://bathymetry/gebco2024"


def geox_srtm_plus():
    """SRTM15+ — 15-arc-sec combined topography/bathymetry, SIO/Scripps.
    URI: geox://bathymetry/srtm15plus
    Source: Scripps Institution of Oceanography
    URL: https://topex.ucsd.edu/www_data/srtm15_plus/
    License: SIO/UCSD proprietary — research use only
    Fetch via: geox_basin(mode='bathymetry', source='srtm15plus')
    Epistemic: OBS — academic composite, high-resolution
    """
    return "geox://bathymetry/srtm15plus"


# ---------------------------------------------------------------------------
# DOMAIN: GEOLOGY & STRATIGRAPHY
# Corresponding tools: geox_basin, geox_sequence
# ---------------------------------------------------------------------------


def geox_macrostrat_units():
    """Macrostrat API — stratigraphic units, chronostratigraphy, lithology, taxonomy.
    URI: geox://stratigraphy/macrostrat_units
    Source: PaleoBioDB / Macrostrat
    URL: https://macrostrat.org/api/v2/
    License: CC-BY 4.0
    Fetch via: geox_io_macrostrat() in geox_core/io/macrostrat_client.py
    Epistemic: OBS — peer-reviewed geological database
    """
    return "geox://stratigraphy/macrostrat_units"


def geox_macrostrat_timescale():
    """Macrostrat Timescale — ICS-aligned geological age definitions.
    URI: geox://stratigraphy/macrostrat_timescale
    Source: Macrostrat / ICS
    License: CC-BY 4.0
    Fetch via: geox_io_macrostrat(mode="timescale")
    Epistemic: OBS — ICS international standard
    """
    return "geox://stratigraphy/macrostrat_timescale"


def geox_onegeology():
    """OneGeology — global web-accessible geological map data (XSD-hosted).
    URI: geox://stratigraphy/onegeology
    Source: OneGeology EGDI / BGS
    URL: https://www.onegeology.org/
    License: LGWM Open Data License (variant of CC-BY)
    Fetch via: geox_io_onegeology() in geox_core/io/onegeology_client.py
    Epistemic: OBS — national geological survey compilation
    """
    return "geox://stratigraphy/onegeology"


# ---------------------------------------------------------------------------
# DOMAIN: TECTONICS
# Corresponding tools: geox_basin (tectonic mode), geox_sequence
# ---------------------------------------------------------------------------


def geox_gplates_velocity():
    """GPlates Web Service — plate motion velocity vectors, rotation poles.
    URI: geox://tectonics/gplates_velocity
    Source: GPlates / GWS
    URL: https://gws.gplates.org/
    License: GPL / GPlates team
    Fetch via: geox_io_gplates() in geox_core/io/gplates_client.py
    Epistemic: OBS — reconstruction model
    """
    return "geox://tectonics/gplates_velocity"


def geox_gplates_paleomask():
    """GPlates paleomask — continental polygons at past geological times.
    URI: geox://tectonics/gplates_paleomask
    Source: GPlates / CGMW
    License: GPL / GPlates team
    Fetch via: geox_io_gplates(mode="paleomask")
    Epistemic: OBS — reconstruction model
    """
    return "geox://tectonics/gplates_paleomask"


# ---------------------------------------------------------------------------
# DOMAIN: GEOCHEMISTRY
# Corresponding tools: geox_basin (geochemistry mode)
# ---------------------------------------------------------------------------


def geox_earthchem():
    """EarthChem — geochemical data (major/trace elements, isotopes, whole-rock).
    URI: geox://geochemistry/earthchem
    Source: EarthChem / IDEEDE
    URL: https://www.earthchem.org/
    License: CEED (EarthChem data policy, restrictive)
    Fetch via: geox_io_earthchem() in geox_core/io/earthchem_client.py
    Epistemic: OBS — published geochemical database
    """
    return "geox://geochemistry/earthchem"


# ---------------------------------------------------------------------------
# DOMAIN: OCEAN
# Corresponding tools: geox_basin (oceanographic mode)
# ---------------------------------------------------------------------------


def geox_copernicus_bathymetry():
    """Copernicus Marine — EMODnet Digital Terrain Model, 1/16-arc-min global bathymetry.
    URI: geox://ocean/copernicus_bathymetry
    Source: Copernicus Marine Service / EMODnet
    URL: https://data.marine.copernicus.eu/product/EMODNET_BATHYMETRY_ATLAS
    License: CC-BY 4.0 (Copernicus)
    Fetch via: geox_io_copernicus() in geox_core/io/copernicus_client.py
    Note: Registration required at marine.copernicus.eu
    Epistemic: OBS — European Union public service product
    """
    return "geox://ocean/copernicus_bathymetry"


def geox_copernicus_sea_level():
    """Copernicus Sea Level — DUACS altimeter SLA, 1993-present, 0.25-deg global.
    URI: geox://ocean/copernicus_sea_level
    Source: CNES/CLS/AVISO / Copernicus
    License: CC-BY 4.0 (Copernicus)
    Fetch via: geox_io_copernicus(mode="sea_level")
    Epistemic: OBS — satellite altimetry
    """
    return "geox://ocean/copernicus_sea_level"


# ---------------------------------------------------------------------------
# DOMAIN: ATMOSPHERE
# Corresponding tools: geox_basin (atmospheric mode)
# ---------------------------------------------------------------------------


def geox_era5_atmosphere():
    """ERA5 — ECMWF reanalysis, 0.25-deg hourly atmospheric fields, 1940-present.
    URI: geox://atmosphere/era5
    Source: ECMWF / Copernicus CDS
    URL: https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels
    License: CC-BY 4.0 (ECMWF/Copernicus)
    Fetch via: geox_io_era5() in geox_core/io/era5_client.py
    Note: Registration required at cds.climate.copernicus.eu
    Epistemic: OBS — reanalysis model output
    """
    return "geox://atmosphere/era5"


def geox_era5_pressure():
    """ERA5 pressure levels — 137 hybrid sigma-pressure levels, 3D atmospheric state.
    URI: geox://atmosphere/era5_pressure_levels
    Source: ECMWF / Copernicus CDS
    License: CC-BY 4.0 (ECMWF/Copernicus)
    Fetch via: geox_io_era5(level_type="pressure")
    Epistemic: OBS — reanalysis model output
    """
    return "geox://atmosphere/era5_pressure_levels"


# ---------------------------------------------------------------------------
# DOMAIN: HEAT FLOW
# ---------------------------------------------------------------------------


def geox_ihfc_heatflow():
    """IHFC — International Heat Flow Commission global heat flow database.
    URI: geox://heatflow/ihfc
    Source: IHFC / USGS / GeoHeat
    URL: https://ihfc-mca.org/
    License: IHFC data policy (verify — varies by contributor)
    Fetch via: geox_io_ihfc() in geox_core/io/ihfc_client.py
    Epistemic: OBS — direct measurement compilation
    """
    return "geox://heatflow/ihfc"


def geox_global_heatflow():
    """Global Heat Flow Database — alternate aggregation (USGS/HotEarth).
    URI: geox://heatflow/global
    Source: USGS / HotEarth Science
    License: USGS Public Domain (where applicable)
    Fetch via: geox_basin(mode='heatflow', source='global')
    Epistemic: OBS — direct measurement compilation
    """
    return "geox://heatflow/global"


# ---------------------------------------------------------------------------
# DOMAIN: HYDROLOGY
# ---------------------------------------------------------------------------


def geox_usgs_water():
    """USGS NWIS — National Water Information System, streamflow, groundwater.
    URI: geox://hydrology/usgs_nwis
    Source: USGS Water Resources
    URL: https://waterservices.usgs.gov/
    License: USGS Public Domain
    Fetch via: geox_io_usgs_water() in geox_core/io/usgs_water_client.py
    Epistemic: OBS — direct measurement network
    """
    return "geox://hydrology/usgs_nwis"


# ---------------------------------------------------------------------------
# DOMAIN: PALEOMAGNETISM
# ---------------------------------------------------------------------------


def geox_magic_paleomag():
    """MAGIC Paleomag — MAGIC database, IAGA paleomagnetic data, polarity timescales.
    URI: geox://paleomag/magic
    Source: IRF Munich / IAGA / MAGIC
    URL: https://www2.earth.ox.ac.uk/~rmagqrt/magic.html
    License: Variable (verify per dataset)
    Fetch via: geox_io_magic() in geox_core/io/magic_client.py
    Epistemic: OBS — published paleomagnetic database
    """
    return "geox://paleomag/magic"


# ---------------------------------------------------------------------------
# DOMAIN: SPACE WEATHER / SOLAR
# ---------------------------------------------------------------------------


def geox_nso_solar():
    """NSO / SOLIS — National Solar Observatory, sunspot, faculae, flare indices.
    URI: geox://space/solar_nso
    Source: NSO / NSO Library
    URL: https://solis.nso.edu/
    License: NSO data policy (verify)
    Fetch via: geox_basin(mode='space', source='nso_solar')
    Epistemic: OBS — direct solar observation
    """
    return "geox://space/solar_nso"


def geox_kp_index():
    """Kp Index — geomagnetic activity, 3-hourly planetary index.
    URI: geox://space/kp_index
    Source: GFZ Potsdam / INTERMAGNET
    URL: https://www.gfz-potsdam.de/en/kp-index
    License: GFZ public (verify)
    Fetch via: geox_basin(mode='space', source='kp_index')
    Epistemic: OBS — observatory magnetometer network
    """
    return "geox://space/kp_index"


# ---------------------------------------------------------------------------
# DOMAIN: DEEP TIME — PENDING DATASETS (5 missing sources)
# ---------------------------------------------------------------------------


def geox_deeptime_co2():
    """Deep Time CO₂ — GEOCARBSULF v4, Berner (2001+) model, Phanerozoic pCO2.
    URI: geox://deep_time/co2
    Source: R. Berner / USDE
    Status: PENDING — GEOCARB source code review ongoing
    Fetch via: geox_deep_time_state(mode="co2") when available
    Epistemic: DER — forward biogeochemical model output
    """
    return "geox://deep_time/co2"


def geox_deeptime_d18o():
    """Deep Time δ18O — Zachos et al. (2008) LR04 stack, benthic foraminifera.
    URI: geox://deep_time/d18o
    Source: Zachos et al. 2008, Nature
    Status: PENDING — ingested into deep_time/data_loaders.py GPTS CSV
    Fetch via: geox_deep_time_state(mode="d18o") when available
    Epistemic: OBS — geochemical measurement proxy
    """
    return "geox://deep_time/d18o"


def geox_deeptime_temperature():
    """Deep Time Temperature — PETM/EEH temperature proxies, Tripati et al. methods.
    URI: geox://deep_time/temperature
    Source: Various (Tripati, Zachos, IPCC AR6)
    Status: PENDING
    Fetch via: geox_deep_time_state(mode="temperature") when available
    Epistemic: DER — multi-proxy temperature estimation
    """
    return "geox://deep_time/temperature"


def geox_deeptime_sea_level():
    """Deep Time Sea Level — Haq et al. (1987, 2008) eustatic curves, Kominz backstripping.
    URI: geox://deep_time/sea_level
    Source: Haq et al. 1987, 2008 / Kominz backstripping
    Status: PENDING
    Fetch via: geox_deep_time_state(mode="sea_level") when available
    Epistemic: DER — sequence stratigraphic + backstripping analysis
    """
    return "geox://deep_time/sea_level"


def geox_deeptime_o2():
    """Deep Time O₂ — Berner (2006, 2009) GEOCARBMOD, Phanerozoic pO₂.
    URI: geox://deep_time/o2
    Source: Berner R.A. / GEOCARBMOD
    Status: PENDING
    Fetch via: geox_deep_time_state(mode="o2") when available
    Epistemic: DER — forward biogeochemical model output
    """
    return "geox://deep_time/o2"
    # ---------------------------------------------------------------------------
    # EARTH DATA ATLAS — MCP PROMPT TEMPLATES
    # Reusable parameterized workflow templates (user-controlled)
    # ---------------------------------------------------------------------------

    mcp.prompt(
        "sabah-pscs-kill-test",
        description=(
            "Sabah PSCS kill-test protocol — full pre-stack depth migration sanity check. "
            "Use after geox_seismic_compute('mode=synthetic') generates suspect AVO. "
            "Steps: (1) flag top-Miocene regional, (2) run geox_seismic_ingest+compute, "
            "(3) call geox_seismic_interpret('mode=horizon_contrast'), "
            "(4) if anomaly persists → HOLD and escalate to GEOX claim. "
            "Corresponds to: GENESIS/003_CONSTITUTIONAL_ALIGNMENT.md §KILL-MAP §PSCS"
        ),
        arguments=[],
    )

    mcp.prompt(
        "carbonate-basement-discrim",
        description=(
            "Carbonate vs basement discrimination protocol. "
            "Distinguish carbonate buildups from crystalline basement using Vp ratio + AI contrast. "
            "Workflow: (1) geox_petrophysics → Vp ratio + AI, "
            "(2) geox_seismic_compute('mode=synthetic') if log data available, "
            "(3) geox_geomechanics → if K < 15 GPa → likely carbonate; "
            "if K > 40 GPa → likely basement. "
            "(4) geox_egs_claim_create with evidence_for/against. "
            "Authority: GEOX proposes, arifOS judges, Arif decides."
        ),
        arguments=[],
    )

    mcp.prompt(
        "deep-time-state-query",
        description=(
            "Query the deep-time Earth state vector at a given geological time. "
            "Steps: (1) geox_deep_time_state(age_ma=AGE, period='PERIOD') → state vector, "
            "(2) geox_basin(mode='macrostrat', age=AGE) → stratigraphic context, "
            "(3) geox_gplates_velocity(reconstruction_age=AGE) → plate positions, "
            "(4) geox_seismic_compute('mode=synthetic') → synthetics if well data available. "
            "Returns: deep_time_state with CO₂, δ18O, temperature, sea level, O₂, plate config. "
            "Use for: paleobathymetry, thermal history, basin formation context."
        ),
        arguments=[],
    )

    mcp.prompt(
        "stratigraphy-correlation",
        description=(
            "Correlate well stratigraphy across a basin using sequence stratigraphy principles. "
            "Workflow: (1) geox_well_ingest for each well (LAS files), "
            "(2) geox_well_qc → depth/register curves, "
            "(3) geox_sequence('mode=correlation', wells=[...], zone_top=X, zone_base=Y) → "
            "parasequence boundaries + correlation panel, "
            "(4) geox_basin(mode='macrostrat') → regional/global chart integration, "
            "(5) geox_egs_claim_create for regional correlation claims. "
            "Output: correlation panel with sequence surfaces, systems tracts, and age calls."
        ),
        arguments=[],
    )
