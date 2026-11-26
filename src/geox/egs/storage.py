"""SQLite persistence for GEOX EarthGraph & Claims (~/.geox/earthgraph.db)."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from geox.egs.models.claims import ClaimEnvelope
from geox.egs.models.entities import Basin, EarthGraph

_SCHEMA = """
CREATE TABLE IF NOT EXISTS earthgraph_state (
    key TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def earthgraph_db_path() -> Path:
    return Path(os.getenv("GEOX_EARTHGRAPH_DB") or (Path.home() / ".geox" / "earthgraph.db"))


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    p = db_path or earthgraph_db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.executescript(_SCHEMA)
    return conn


def _seed_graph() -> EarthGraph:
    """Seed public-domain reference basins so EarthGraph never boots empty."""
    g = EarthGraph()
    for bid, name, btype, setting, bbox, age, desc in [
        (
            "basin-nw-sabah",
            "NW Sabah Basin",
            "foreland_passive_margin",
            "compressional_gravity",
            (113.0, 5.2, 119.4, 8.3),
            (45.0, 0.0),
            "Public reference basin for T-KIN-XS-833 (Dangerous Grounds to Sulu Sea).",
        ),
        (
            "basin-north-sea-volve",
            "North Sea — Volve Benchmark",
            "rift",
            "extensional",
            (1.8, 58.3, 2.0, 58.6),
            (200.0, 0.0),
            "Equinor Volve public subsurface benchmark (open licence).",
        ),
        (
            "basin-dutch-f3",
            "Dutch North Sea — F3 Block",
            "rift_postrift",
            "extensional",
            (4.6, 54.7, 5.0, 55.0),
            (66.0, 0.0),
            "dGB/NLOG F3 Netherlands public 3D SEG-Y benchmark (CC-BY-SA).",
        ),
    ]:
        g.basins[bid] = Basin(
            id=bid,
            name=name,
            basin_type=btype,
            tectonic_setting=setting,
            bounding_box=bbox,
            age_range_ma=age,
            description=desc,
            tags=["public", "seed"],
        )
    return g


def save_earthgraph(graph: EarthGraph, db_path: Path | None = None) -> None:
    now = datetime.now(UTC).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO earthgraph_state (key, payload_json, updated_at) VALUES (?, ?, ?)",
            ("graph", graph.model_dump_json(), now),
        )


def save_claims(claims: dict[str, ClaimEnvelope], db_path: Path | None = None) -> None:
    now = datetime.now(UTC).isoformat()
    with _connect(db_path) as conn:
        for cid, env in claims.items():
            conn.execute(
                "INSERT OR REPLACE INTO claims (claim_id, payload_json, updated_at) VALUES (?, ?, ?)",
                (cid, env.model_dump_json(), now),
            )


def load_or_seed_earthgraph(db_path: Path | None = None) -> EarthGraph:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT payload_json FROM earthgraph_state WHERE key = 'graph'").fetchone()
    if row:
        try:
            g = EarthGraph.model_validate_json(row[0])
            if g.basins or g.wells or g.horizons or g.surveys:
                return g
        except Exception:
            pass
    seeded = _seed_graph()
    save_earthgraph(seeded, db_path=db_path)
    return seeded


def load_claims(db_path: Path | None = None) -> dict[str, ClaimEnvelope]:
    out: dict[str, ClaimEnvelope] = {}
    with _connect(db_path) as conn:
        for cid, payload in conn.execute("SELECT claim_id, payload_json FROM claims").fetchall():
            try:
                out[cid] = ClaimEnvelope.model_validate_json(payload)
            except Exception:
                continue
    return out


def db_stats(db_path: Path | None = None) -> dict[str, Any]:
    p = db_path or earthgraph_db_path()
    g = load_or_seed_earthgraph(p)
    c = load_claims(p)
    return {
        "db_path": str(p),
        "exists": p.exists(),
        "basins": len(g.basins),
        "wells": len(g.wells),
        "claims": len(c),
        "non_empty": bool(g.basins or g.wells or g.horizons or c),
    }
