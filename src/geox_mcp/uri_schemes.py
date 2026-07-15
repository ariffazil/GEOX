"""
GEOX MCP URI Scheme Registry — Single Source of Truth
═══════════════════════════════════════════════════
Binds all `geox://...` resource URIs to template paths, MIME types,
access classes, and F1-F13 floors. Importing this module replaces
scattered URI string literals across the GEOX MCP server.

Authoritative reference: `/root/GEOX/forge_work/2026-07-10/RESOURCE-CONTRACT-v1.md`
Spec: MCP 2025-11-25 (per GEOX /.well-known/mcp/server.json protocol_version)

DITEMPA BUKAN DIBERI — URIs are forged, not given.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── 1. Scheme root ────────────────────────────────────────────────────────────
SCHEME = "geox"
URI_PATTERN = re.compile(r"^geox://[A-Za-z0-9._/\-{}]+$")


# ── 2. Access classes (F13 SOVEREIGN) ─────────────────────────────────────────
class AccessClass(str, Enum):
    """F13-gated access tiers. Order is sensitivity-ascending."""

    PUBLIC = "PUBLIC"  # anyone can read
    READ_OPEN = "READ_OPEN"  # any registered agent
    DOMAIN_ONLY = "DOMAIN_ONLY"  # arifOS federation only
    SOVEREIGN = "SOVEREIGN"  # F13 actor_signature required


# ── 3. Resource tier (what kind of transport) ─────────────────────────────────
class Tier(str, Enum):
    """Transport tier — drives `read` return shape per MCP 2025-11-25."""

    TEXT_INLINE = "TEXT_INLINE"  # TextResourceContents{ text }
    BLOB_INLINE = "BLOB_INLINE"  # BlobResourceContents{ blob: base64 } (small)
    URI_EXTERNAL = "URI_EXTERNAL"  # { uri: "https://..." } (large binary)


# ── 4. The registry entry ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class UriTemplate:
    """Canonical declaration of a single URI pattern (or fixed URI).

    `path` follows the `geox://` scheme. Templates use `{name}` braces
    for parametric segments. Fixed URIs declare no braces.
    """

    name: str  # logical key (used by code)
    path: str  # full URI or template (without scheme prefix)
    description: str
    mime_type: str
    tier: Tier = Tier.TEXT_INLINE
    access: AccessClass = AccessClass.READ_OPEN
    annotations_audience: tuple[str, ...] = ("assistant",)
    annotations_priority: float = 0.7
    max_size_bytes: int | None = None  # for blob tier — fail if bigger
    template: bool = False  # True iff path contains '{...}'
    floors_active: tuple[str, ...] = ("F1", "F2", "F11")
    # extension metadata written into _meta on read
    meta_default: dict[str, Any] = field(default_factory=dict)


# ── 5. The registry — ordered by domain ───────────────────────────────────────
#   When adding a new URI here, EVERY consumer (resources/__init__.py,
#   tools, tests, docs) imports the constant. Never scatter a raw string.
REGISTRY: tuple[UriTemplate, ...] = (
    # ── A. Federation identity & surface ─────────────────────────────────────
    UriTemplate(
        name="identity",
        path="identity",
        description="GEOX identity state — role, authority, seal, version, canon-9 quantities, GDE vocabulary, strat standards.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("user", "assistant"),
        annotations_priority=0.95,
    ),
    UriTemplate(
        name="profile_status",
        path="profile/status",
        description="GEOX profile status — health, enabled dimensions, version, constitutional floors.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("user",),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="capabilities",
        path="capabilities",
        description="Full GEOX capability map: tools, domains, claim limits, next best actions. Read at session start.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.9,
    ),
    UriTemplate(
        name="surface_truth",
        path="surface/truth",
        description="Validate and report the current surface truth status (the Surface Truth Lock).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    UriTemplate(
        name="reality_context",
        path="reality/context",
        description="Reality engineering context for agent execution — available tools, evidence, reports, forbidden claims, claim ladder.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.8,
    ),
    # ── B. Literature (papers, citable artifacts) ────────────────────────────
    UriTemplate(
        name="literature_paper",
        path="literature/{basin}/{paper_id}",
        description="Canonical literature paper URI. {basin} = kebab-case basin name (e.g. sabah, malay-basin). {paper_id} = paper slug. Returns markdown-extracted text + provenance _meta.",
        mime_type="text/markdown",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.85,
    ),
    UriTemplate(
        name="literature_paper_pdf",
        path="literature/{basin}/{paper_id}/pdf",
        description="Raw PDF of a literature paper. Returns base64 blob — small files only (<2 MB). For larger volumes use URI_EXTERNAL.",
        mime_type="application/pdf",
        tier=Tier.BLOB_INLINE,
        max_size_bytes=2_000_000,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="literature_index",
        path="literature/index",
        description="Cursor-paginated index of all registered literature resources.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    UriTemplate(
        name="literature_madon_paper_legacy",
        path="literature/GSM-MADON-2021-MALAY-BASIN",
        description="[LEGACY FIXED URI] Mazlan Madon's 2021 GSM Malay Basin paper. Kept for backward compat — prefer literature_paper template for new lookups.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    # ── C. Wells ──────────────────────────────────────────────────────────────
    UriTemplate(
        name="well",
        path="wells/{basin}/{well_id}",
        description="Canonical well summary — header, deviation summary, log availability, top picks. {basin}/{well_id} = verbatim PETRONAS naming.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.85,
    ),
    UriTemplate(
        name="well_logs",
        path="wells/{basin}/{well_id}/logs",
        description="LAS-format logs for a well (text). For binary log normalization use well_tops.",
        mime_type="text/plain",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    UriTemplate(
        name="well_tops",
        path="wells/{basin}/{well_id}/tops",
        description="Formation tops (markers) for a well — JSON list with depth, MD/TVD, source citation.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    # ── D. Seismic & 3D render (binary, often large) ─────────────────────────
    UriTemplate(
        name="seismic_volume_meta",
        path="seismic/{basin}/{volume_id}",
        description="Seismic volume metadata (geometry, samples, CRS, brick grid). Returns JSON manifest; never inline the binary.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    UriTemplate(
        name="cube_manifest",
        path="render/cubes/{cube_id}/manifest",
        description="CubeManifest for a 3D seismic volume. Brick grid, LOD pyramid, CRS.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    UriTemplate(
        name="cube_brick",
        path="render/cubes/{cube_id}/lod/{lod}/brick/{ix}/{iy}/{iz}",
        description="Binary brick from a 3D cube. Returns base64 bytes (Float32 / Int16). Progressive streaming: LOD 0 → refine.",
        mime_type="application/octet-stream",
        tier=Tier.BLOB_INLINE,
        max_size_bytes=8_000_000,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    UriTemplate(
        name="render_surface",
        path="render/surfaces/{surface_id}",
        description="Binary surface data (horizon mesh, fault plane). surface_id = '<name>.npz|gltf|ply'.",
        mime_type="application/octet-stream",
        tier=Tier.BLOB_INLINE,
        max_size_bytes=16_000_000,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    UriTemplate(
        name="render_cube_slice",
        path="render/cubes/{volume_id}/{orientation}/{slice_index}",
        description="Binary cube slice frame. Raw Float32Array bytes, base64-encoded.",
        mime_type="application/octet-stream",
        tier=Tier.BLOB_INLINE,
        max_size_bytes=16_000_000,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    UriTemplate(
        name="render_payload_schema",
        path="render/payload-schema/{_version}",
        description="Canonical RenderPayload Pydantic schema (versioned).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.6,
    ),
    # ── E. Earth layers & claims graph ───────────────────────────────────────
    UriTemplate(
        name="layers_index",
        path="layers/index",
        description="EarthLayerRegistry index — every seeded sovereign layer (id, title, license, truth class).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    UriTemplate(
        name="layer_package",
        path="layers/{layer_id}/package",
        description="Single-layer export package — envelope (license, truth class, bbox, F1/F2/F6/F11 gates).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    UriTemplate(
        name="claims_index",
        path="claims/index",
        description="Cursor-paginated index of all claims (draft, validated, sealed, challenged).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        annotations_audience=("assistant",),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="claims_graph",
        path="claims/graph",
        description="Visual claim graph: nodes + edges with epistemic + authority labels.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        annotations_audience=("assistant",),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="claim",
        path="claims/{claim_id}",
        description="Single claim envelope (GET). For create/challenge use tool `geox_claim` (MUTATE).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    # ── F. Earth data atlas (external dataset caches — NOTE: live data via TOOL) ──
    #     These resources expose schema/citation metadata only. Live queries
    #     MUST go through the corresponding MCP tool (e.g. geox_basin for
    #     Macrostrat, geox_earthquake_catalog for USGS). Per MCP docs-agent
    #     doctrine (2025-06-18, ratified 2026-07-10): external live APIs
    #     are Tools, NOT Resources.
    UriTemplate(
        name="atlas_macrostrat_units_meta",
        path="stratigraphy/macrostrat_units",
        description="[SCHEMA INDEX] Macrostrat units endpoint metadata. Live data via tool `geox_basin(mode='macrostrat_units')`. Cached snapshot resource — does not fetch live.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.4,
    ),
    UriTemplate(
        name="atlas_macrostrat_timescale_meta",
        path="stratigraphy/macrostrat_timescale",
        description="[SCHEMA INDEX] Macrostrat Timescale (ICS-aligned ages) metadata. Live data via tool `geox_basin(mode='macrostrat_timescale')`.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.4,
    ),
    # ── G. Basins ────────────────────────────────────────────────────────────
    UriTemplate(
        name="basins_index",
        path="basins/index",
        description="Index of all available basins (sabah, malay-basin, sarawak, etc.).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.7,
    ),
    UriTemplate(
        name="basin_profile",
        path="basins/{basin}/profile",
        description="Geological profile for a basin (template). {basin} = kebab-case basin name.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.8,
    ),
    UriTemplate(
        name="basin_malay_legacy",
        path="basins/malay-basin/profile",
        description="[LEGACY FIXED URI] Malay Basin profile. Use basin_profile template for new lookups.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    # ── H. Internal knowledge packs (ontology, playbooks, schemas, examples) ──
    UriTemplate(
        name="resources_pack",
        path="resources/{category}/{name}",
        description="Agent knowledge pack. Categories: ontology, playbooks, schemas, examples. {name} is filename without ext.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    UriTemplate(
        name="resources_index",
        path="resources/index",
        description="Cursor-paginated index of all knowledge-pack resources.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="resources_playbooks_index",
        path="resources/playbooks/index",
        description="Index of playbook files (operational patterns).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    UriTemplate(
        name="resources_ontology_index",
        path="resources/ontology/index",
        description="Index of ontology files (canonical vocab).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    UriTemplate(
        name="resources_schemas_index",
        path="resources/schemas/index",
        description="Index of schema files (Pydantic + JSON).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    UriTemplate(
        name="artifacts_index",
        path="artifacts/index",
        description="Index of all visualizable artifacts (panels, sections, maps).",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.DOMAIN_ONLY,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
    # ── I. TREE777 wiki cross-organ surface (shared under /root/AAA/wiki) ─────
    UriTemplate(
        name="tree777_index",
        path="tree777://index",
        description="TREE777 wiki full index. Federation skills, concepts, scars across organs.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("user", "assistant"),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="tree777_skill",
        path="tree777://skills/geox/{name}",
        description="GEOX skill page markdown (frontmatter-stripped).",
        mime_type="text/markdown",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="tree777_concept",
        path="tree777://geo/concepts/{name}",
        description="Geoscience concept page markdown.",
        mime_type="text/markdown",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="tree777_scar",
        path="tree777://geo/scars/{name}",
        description="GEOX scar/incident record (failures and lessons learned).",
        mime_type="text/markdown",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        template=True,
        annotations_audience=("assistant",),
        annotations_priority=0.6,
    ),
    UriTemplate(
        name="registry_apps",
        path="registry/apps",
        description="List of registered GEOX MCP apps and manifests.",
        mime_type="application/json",
        tier=Tier.TEXT_INLINE,
        access=AccessClass.PUBLIC,
        annotations_audience=("assistant",),
        annotations_priority=0.5,
    ),
)


# ── 6. Lookup helpers ────────────────────────────────────────────────────────
_BY_NAME: dict[str, UriTemplate] = {t.name: t for t in REGISTRY}


def get(name: str) -> UriTemplate:
    """Resolve a UriTemplate by logical name. F2: unknown → raise, never default."""
    if name not in _BY_NAME:
        raise KeyError(f"URI template '{name}' not in registry. Known: {sorted(_BY_NAME)[:5]}... ({len(_BY_NAME)} total)")
    return _BY_NAME[name]


def full_uri(template_name: str, **params: str) -> str:
    """Build a fully-resolved URI from a template name + params.

    Raises if any required `{key}` remains unresolved. F2: no silent placeholders.

    Example:
        full_uri("literature_paper", basin="sabah", paper_id="madon-2021")
        # → 'geox://literature/sabah/madon-2021'
    """
    tmpl = get(template_name)
    if not tmpl.template:
        return f"{SCHEME}://{tmpl.path}"
    path = tmpl.path
    for key, val in params.items():
        path = path.replace(f"{{{key}}}", str(val))
    if re.search(r"\{[^}]+\}", path):
        missing = re.findall(r"\{([^}]+)\}", path)
        raise ValueError(f"URI template '{template_name}' unresolved keys: {missing}. Passed params: {sorted(params)}")
    out = f"{SCHEME}://{path}"
    if not URI_PATTERN.match(out):
        raise ValueError(f"Composed URI '{out}' does not match scheme pattern")
    return out


def is_valid_uri(uri: str) -> bool:
    """Loose validation — URI matches the `geox://` RFC pattern."""
    return bool(URI_PATTERN.match(uri))


def templates_only() -> tuple[UriTemplate, ...]:
    """Return only the parametric (templated) entries — used for `resources/templates/list`."""
    return tuple(t for t in REGISTRY if t.template)


def fixed_only() -> tuple[UriTemplate, ...]:
    """Return only the fixed (non-templated) entries."""
    return tuple(t for t in REGISTRY if not t.template)


# ── 7. JSON-RPC error codes (per MCP spec 2025-11-25) ────────────────────────
class JsonRpcError:
    RESOURCE_NOT_FOUND = -32002  # URI not in registry or params unresolved
    FORBIDDEN = -32003  # F13 gate denied (operator-private / SOVEREIGN tier)
    URI_INVALID = -32602  # malformed URI
    METHOD_NOT_FOUND = -32601  # subscribe not declared
    INTERNAL_ERROR = -32603  # backend failure


# ── 8. Public re-exports ──────────────────────────────────────────────────────
__all__ = [
    "SCHEME",
    "URI_PATTERN",
    "AccessClass",
    "Tier",
    "UriTemplate",
    "JsonRpcError",
    "REGISTRY",
    "get",
    "full_uri",
    "is_valid_uri",
    "templates_only",
    "fixed_only",
]
