"""
GEOX Resource Registry — Persistent, URI-Addressable Artifact Store
═══════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

Persistent, queryable artifact registry replacing the ephemeral in-memory
_artifact_registry dict. Supports URI resolution, dependency tracking,
and lifecycle state management.

URI Schemes (Federation Contract §4):
  artifact://geox/{artifact_id}  — computed artifact
  claim://geox/{claim_id}        — sealed/qualified interpretation claim
  evidence://geox/{evidence_id}  — QC-verified evidence
  vault://receipt/{seal_id}      — VAULT999 sealed receipt
  las://well/{well_id}           — well log LAS file
  segy://survey/{survey}/{inline} — seismic volume brick
  geojson://block/{block_id}     — spatial boundary
  parquet://petrophysics/{run}    — petrophysical run

Storage: SQLite (same pattern as EarthMemoryStore)
Migration path: Postgres/Supabase when scale demands.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

logger = logging.getLogger("geox.resource_registry")

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

REGISTRY_DB_PATH = os.getenv("GEOX_RESOURCE_REGISTRY_DB", "/root/geox/resource_registry.db")

ResourceType = Literal[
    "seismic_volume", "well_log", "seismic_attribute", "structural_map",
    "stratigraphic_column", "petrophysics_run", "prospect_evaluation",
    "basin_profile", "literature_reference", "interpretation_claim",
    "evidence_bundle", "qc_report", "audit_receipt",
]

ResourceState = Literal[
    "RAW", "INGESTED", "QC_VERIFIED", "QC_VERIFIED_WITH_WARNINGS",
    "COMPUTED", "INTERPRETED", "DERIVED_CANDIDATE", "REVIEW_PENDING",
    "QUALIFIED", "SEALED", "VOID", "888_HOLD",
]

URI_SCHEME_MAP = {
    "artifact": "artifact://geox/{id}",
    "claim": "claim://geox/{id}",
    "evidence": "evidence://geox/{id}",
    "vault": "vault://receipt/{id}",
    "las": "las://well/{id}",
    "segy": "segy://survey/{id}",
    "geojson": "geojson://block/{id}",
    "parquet": "parquet://petrophysics/{id}",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════════════════════════════════

def _get_connection() -> sqlite3.Connection:
    """Get a connection to the resource registry database."""
    conn = sqlite3.connect(REGISTRY_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db() -> None:
    """Initialize the resource registry schema."""
    conn = _get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS resources (
            id              TEXT PRIMARY KEY,
            uri             TEXT UNIQUE NOT NULL,
            resource_type   TEXT NOT NULL,
            state           TEXT NOT NULL DEFAULT 'RAW',
            producer_tool   TEXT,
            well_id         TEXT,
            basin_id        TEXT,
            content_hash    TEXT,
            transform_hash  TEXT,
            physics_manifest_hash TEXT,
            claim_links     TEXT DEFAULT '[]',   -- JSON array of claim IDs
            input_refs      TEXT DEFAULT '[]',   -- JSON array of input resource IDs
            evidence_refs   TEXT DEFAULT '[]',   -- JSON array of evidence IDs
            metadata        TEXT DEFAULT '{}',   -- JSON blob for extra fields
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            sealed_at       TEXT,
            actor_id        TEXT,
            session_id      TEXT
        );

        CREATE TABLE IF NOT EXISTS resource_dependencies (
            resource_id     TEXT NOT NULL,
            depends_on_id   TEXT NOT NULL,
            dependency_type TEXT NOT NULL DEFAULT 'input',  -- input | evidence | claim
            PRIMARY KEY (resource_id, depends_on_id),
            FOREIGN KEY (resource_id) REFERENCES resources(id),
            FOREIGN KEY (depends_on_id) REFERENCES resources(id)
        );

        CREATE TABLE IF NOT EXISTS resource_contradictions (
            resource_id     TEXT NOT NULL,
            contradicted_by TEXT NOT NULL,
            reason          TEXT,
            created_at      TEXT NOT NULL,
            PRIMARY KEY (resource_id, contradicted_by),
            FOREIGN KEY (resource_id) REFERENCES resources(id),
            FOREIGN KEY (contradicted_by) REFERENCES resources(id)
        );

        CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(resource_type);
        CREATE INDEX IF NOT EXISTS idx_resources_state ON resources(state);
        CREATE INDEX IF NOT EXISTS idx_resources_well ON resources(well_id);
        CREATE INDEX IF NOT EXISTS idx_resources_basin ON resources(basin_id);
        CREATE INDEX IF NOT EXISTS idx_deps_resource ON resource_dependencies(resource_id);
        CREATE INDEX IF NOT EXISTS idx_deps_depends ON resource_dependencies(depends_on_id);
    """)
    conn.commit()
    conn.close()
    logger.info(f"Resource registry initialized at {REGISTRY_DB_PATH}")


# Initialize on module import
_init_db()


# ═══════════════════════════════════════════════════════════════════════════════
# URI Resolution
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_content_hash(data: dict[str, Any]) -> str:
    """SHA-256 hash of resource payload for immutability verification."""
    canonical = json.dumps(data, sort_keys=True, default=str, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_uri(scheme: str, resource_id: str) -> str:
    """Build a URI from a scheme and resource ID."""
    template = URI_SCHEME_MAP.get(scheme, "artifact://geox/{id}")
    return template.format(id=resource_id)


def parse_uri(uri: str) -> dict[str, str] | None:
    """Parse a resource URI into its components.

    Returns: {"scheme": str, "resource_id": str} or None if invalid.
    """
    try:
        parts = uri.split("://", 1)
        if len(parts) != 2:
            return None
        scheme = parts[0]
        path = parts[1]  # e.g., "geox/abc123" or "well/MB-001" or "receipt/seal-1"

        # Extract resource_id: last segment after final /
        resource_id = path.rsplit("/", 1)[-1]
        return {"scheme": scheme, "resource_id": resource_id, "full_path": path}
    except Exception:
        return None


def resolve_uri(uri: str) -> dict[str, Any] | None:
    """Resolve a URI to its full resource metadata.

    Returns: Full resource dict or None if not found.
    """
    parsed = parse_uri(uri)
    if not parsed:
        return None

    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM resources WHERE uri = ? OR id = ?",
        (uri, parsed["resource_id"]),
    ).fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Resource Registration
# ═══════════════════════════════════════════════════════════════════════════════

def register_resource(
    resource_type: ResourceType,
    *,
    resource_id: str | None = None,
    uri_scheme: str = "artifact",
    producer_tool: str = "unknown",
    well_id: str | None = None,
    basin_id: str | None = None,
    input_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    claim_links: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    actor_id: str | None = None,
    session_id: str | None = None,
    state: ResourceState = "RAW",
    physics_manifest_hash: str | None = None,
) -> dict[str, Any]:
    """Register a new resource in the persistent registry.

    Returns the full resource record including generated URI.
    """
    if resource_id is None:
        resource_id = f"res_{uuid.uuid4().hex[:16]}"

    uri = build_uri(uri_scheme, resource_id)
    now = _now_iso()

    # Compute content hash from metadata
    content_hash = _compute_content_hash(metadata or {})

    # Resolve physics manifest
    if physics_manifest_hash is None:
        try:
            from geox_core.physics.manifest import get_physics_manifest_hash
            physics_manifest_hash = get_physics_manifest_hash()
        except Exception:
            physics_manifest_hash = os.environ.get(
                "GEOX_PHYSICS_MANIFEST_HASH", "sha256:missing"
            )

    conn = _get_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO resources
               (id, uri, resource_type, state, producer_tool, well_id, basin_id,
                content_hash, transform_hash, physics_manifest_hash,
                claim_links, input_refs, evidence_refs, metadata,
                created_at, updated_at, actor_id, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                resource_id, uri, resource_type, state, producer_tool,
                well_id, basin_id, content_hash, content_hash, physics_manifest_hash,
                json.dumps(claim_links or []), json.dumps(input_refs or []),
                json.dumps(evidence_refs or []), json.dumps(metadata or {}),
                now, now, actor_id, session_id,
            ),
        )

        # Record dependencies
        for dep_id in (input_refs or []):
            conn.execute(
                "INSERT OR IGNORE INTO resource_dependencies (resource_id, depends_on_id, dependency_type) VALUES (?, ?, 'input')",
                (resource_id, dep_id),
            )
        for ev_id in (evidence_refs or []):
            conn.execute(
                "INSERT OR IGNORE INTO resource_dependencies (resource_id, depends_on_id, dependency_type) VALUES (?, ?, 'evidence')",
                (resource_id, ev_id),
            )
        for claim_id in (claim_links or []):
            conn.execute(
                "INSERT OR IGNORE INTO resource_dependencies (resource_id, depends_on_id, dependency_type) VALUES (?, ?, 'claim')",
                (resource_id, claim_id),
            )

        conn.commit()
        logger.info(f"Registered: {uri} [{resource_type}] → {state}")
    finally:
        conn.close()

    return {
        "resource_id": resource_id,
        "uri": uri,
        "resource_type": resource_type,
        "state": state,
        "producer_tool": producer_tool,
        "content_hash": content_hash,
        "physics_manifest_hash": physics_manifest_hash,
        "created_at": now,
    }


def update_resource_state(
    resource_id: str,
    new_state: ResourceState,
    *,
    metadata_updates: dict[str, Any] | None = None,
) -> bool:
    """Update a resource's lifecycle state."""
    conn = _get_connection()
    now = _now_iso()
    updates = {"state": new_state, "updated_at": now}

    if new_state == "SEALED":
        updates["sealed_at"] = now

    if metadata_updates:
        row = conn.execute("SELECT metadata FROM resources WHERE id = ?", (resource_id,)).fetchone()
        if row:
            existing = json.loads(row[0])
            existing.update(metadata_updates)
            updates["metadata"] = json.dumps(existing)

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [resource_id]
    conn.execute(f"UPDATE resources SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Resource Queries (Federation Contract §4 — Registry Questions)
# ═══════════════════════════════════════════════════════════════════════════════

def query_resources(
    *,
    resource_type: ResourceType | None = None,
    state: ResourceState | None = None,
    well_id: str | None = None,
    basin_id: str | None = None,
    producer_tool: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Query resources by filters. Answers: 'What exists? Where is it?'"""
    conn = _get_connection()
    query = "SELECT * FROM resources WHERE 1=1"
    params: list[Any] = []

    if resource_type:
        query += " AND resource_type = ?"
        params.append(resource_type)
    if state:
        query += " AND state = ?"
        params.append(state)
    if well_id:
        query += " AND well_id = ?"
        params.append(well_id)
    if basin_id:
        query += " AND basin_id = ?"
        params.append(basin_id)
    if producer_tool:
        query += " AND producer_tool = ?"
        params.append(producer_tool)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [_row_to_dict(r) for r in rows]


def get_resource_dependents(resource_id: str) -> list[dict[str, Any]]:
    """Get all resources that depend on this resource.
    Answers: 'Which claim depends on it? Can it be reused?'"""
    conn = _get_connection()
    rows = conn.execute(
        """SELECT r.*, d.dependency_type
           FROM resources r
           JOIN resource_dependencies d ON r.id = d.resource_id
           WHERE d.depends_on_id = ?
           ORDER BY r.created_at DESC""",
        (resource_id,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_resource_contradictions(resource_id: str) -> list[dict[str, Any]]:
    """Get contradictions against this resource.
    Answers: 'Has it been contradicted?'"""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM resource_contradictions WHERE resource_id = ?",
        (resource_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def is_resource_sealed(resource_id: str) -> bool:
    """Check if a resource is sealed.
    Answers: 'Is it sealed, qualified, held, or void?'"""
    conn = _get_connection()
    row = conn.execute(
        "SELECT state FROM resources WHERE id = ?",
        (resource_id,),
    ).fetchone()
    conn.close()
    return row is not None and row[0] == "SEALED"


def get_resource_producer(resource_id: str) -> dict[str, str] | None:
    """Get the producer tool and transform hash for a resource.
    Answers: 'Who produced it? What transformation touched it?'"""
    conn = _get_connection()
    row = conn.execute(
        "SELECT producer_tool, transform_hash, physics_manifest_hash FROM resources WHERE id = ?",
        (resource_id,),
    ).fetchone()
    conn.close()
    if row:
        return {
            "producer_tool": row[0],
            "transform_hash": row[1],
            "physics_manifest_hash": row[2],
        }
    return None


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a sqlite3.Row to a plain dict."""
    d = dict(row)
    # Deserialize JSON fields
    for field in ("claim_links", "input_refs", "evidence_refs", "metadata"):
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except json.JSONDecodeError:
                pass
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# In-Memory Bridge — transparently upgrade old _register_artifact calls
# ═══════════════════════════════════════════════════════════════════════════════

def bridge_register_artifact(
    artifact_id: str,
    **kwargs: Any,
) -> str:
    """Drop-in replacement for _register_artifact that persists to the registry.

    Call this instead of the in-memory _register_artifact in _artifact_helpers.py.
    """
    resource_type = kwargs.get("resource_type", "well_log")
    register_resource(
        resource_type=resource_type,
        resource_id=artifact_id,
        uri_scheme=kwargs.get("uri_scheme", "artifact"),
        producer_tool=kwargs.get("tool", "unknown"),
        well_id=kwargs.get("well_id"),
        basin_id=kwargs.get("basin_id"),
        input_refs=kwargs.get("input_refs", []),
        evidence_refs=kwargs.get("evidence_refs", []),
        state=kwargs.get("claim_state", "RAW"),
        actor_id=kwargs.get("actor_id"),
        session_id=kwargs.get("session_id"),
        metadata=kwargs,
    )

    # Also update the in-memory registry for backward compatibility
    try:
        from geox_mcp.tools._artifact_helpers import _register_artifact
        _register_artifact(artifact_id, **kwargs)
    except Exception:
        pass

    return artifact_id


# ═══════════════════════════════════════════════════════════════════════════════
# Registry Health & Stats
# ═══════════════════════════════════════════════════════════════════════════════

def registry_stats() -> dict[str, Any]:
    """Return registry health and statistics."""
    conn = _get_connection()
    total = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
    by_type_rows = conn.execute(
        "SELECT resource_type, COUNT(*) as cnt FROM resources GROUP BY resource_type ORDER BY cnt DESC"
    ).fetchall()
    by_state_rows = conn.execute(
        "SELECT state, COUNT(*) as cnt FROM resources GROUP BY state ORDER BY cnt DESC"
    ).fetchall()
    conn.close()

    return {
        "total_resources": total,
        "by_type": {r[0]: r[1] for r in by_type_rows},
        "by_state": {r[0]: r[1] for r in by_state_rows},
        "db_path": REGISTRY_DB_PATH,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Self-test
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Test registration
    result = register_resource(
        "well_log",
        resource_id="test-well-001",
        uri_scheme="las",
        producer_tool="geox_data_ingest_bundle",
        well_id="MB-001",
        state="INGESTED",
        metadata={"filename": "MB-001.las", "curves": ["GR", "DT", "RHOB"]},
    )
    print(f"✅ Registered: {result['uri']}")

    # Test URI resolution
    resolved = resolve_uri("las://well/test-well-001")
    print(f"✅ Resolved las://well/test-well-001: {resolved['resource_type']} [{resolved['state']}]")

    # Test URI parsing
    for uri in [
        "las://well/MB-001",
        "artifact://geox/abc123",
        "claim://geox/clm_test",
        "segy://survey/SABAH-3D/inline-1200",
        "vault://receipt/seal-2026-001",
    ]:
        parsed = parse_uri(uri)
        print(f"  URI: {uri} → {parsed}")

    # Test queries
    stats = registry_stats()
    print(f"✅ Registry stats: {stats['total_resources']} resources, {len(stats['by_type'])} types")

    # Clean up test data
    conn = _get_connection()
    conn.execute("DELETE FROM resources WHERE id = 'test-well-001'")
    conn.execute("DELETE FROM resource_dependencies WHERE resource_id = 'test-well-001'")
    conn.commit()
    conn.close()
    print("✅ Self-test complete")
