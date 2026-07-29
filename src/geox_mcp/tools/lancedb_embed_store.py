"""geox_lancedb_embed_store — LanceDB Embedded Vector Store.

Serverless vector DB for earth embeddings (AlphaEarth 64-dim, Clay 768-dim, custom).
PQ compression + refine_factor for recall.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("geox.canonical.lancedb_embed_store")

LANCEDB_DIR = Path(os.environ.get("GEOX_LANCEDB_DIR", "/opt/geox/data/lancedb"))
LANCEDB_DIR.mkdir(parents=True, exist_ok=True)


async def geox_lancedb_embed_store(
    mode: str = "search",
    table_name: str = "geo_embeddings",
    embeddings: list[float] | list[list[float]] | str | None = None,
    metadata: list[dict] | str | None = None,
    k: int = 10,
    refine_factor: int | None = None,
    filter_expr: str | None = None,
    h3_cell: str | None = None,
    h3_radius: int = 1,
    create_if_missing: bool = True,
    drop_table: bool = False,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """LanceDB embedded vector store for earth embeddings.

    Modes:
        search       — KNN vector similarity search.
        store        — Insert/append embeddings with metadata.
        spatial      — Search by H3 cell + radius (cross-reference).
        hybrid       — Combined vector + H3 spatial search.
        info         — Get table info (row count, dimension).
        list_tables  — List all stored tables.
        delete_rows  — Delete rows by filter expression.

    Args:
        mode: Operation mode.
        table_name: LanceDB table name (default: 'geo_embeddings').
        embeddings: Single embedding vector or list of vectors.
        metadata: List of {h3_cell, source, label, ...} dicts (store mode).
        k: Number of nearest neighbors for search.
        refine_factor: PQ refinement multiplier (default: auto).
        filter_expr: SQL-like filter (e.g., "source = 'Clay'").
        h3_cell: H3 cell index for spatial search.
        h3_radius: H3 k-ring radius for spatial filter.
        create_if_missing: Auto-create table if absent.
        drop_table: Delete and recreate the table (store mode).
        session_id, actor_id, trace_id: Federation audit.

    Returns:
        dict with search results or operation confirmation.
    """
    _ = (session_id, actor_id, trace_id)

    # Parse stringified inputs
    if isinstance(embeddings, str):
        embeddings = json.loads(embeddings)
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    try:
        import lancedb
    except ImportError:
        return {"ok": False, "error": "lancedb not installed", "epistemic": "TOOL_UNAVAILABLE"}

    try:
        db = lancedb.connect(str(LANCEDB_DIR))

        # ── Mode: list_tables ───────────────────────────────────────────
        if mode == "list_tables":
            tables = db.table_names()
            return {"ok": True, "tables": tables, "count": len(tables)}

        # ── Mode: info ─────────────────────────────────────────────────
        if mode == "info":
            try:
                tbl = db.open_table(table_name)
                return {
                    "ok": True,
                    "table_name": table_name,
                    "rows": tbl.count_rows(),
                    "schema": str(tbl.schema),
                }
            except Exception:
                return {"ok": False, "error": f"Table '{table_name}' not found"}

        # ── Mode: store ─────────────────────────────────────────────────
        if mode == "store":
            if drop_table:
                try:
                    db.drop_table(table_name)
                except Exception:
                    pass

            vecs = embeddings if isinstance(embeddings, list) else [embeddings]
            metas = metadata or [{}] * len(vecs)

            if len(vecs) != len(metas):
                return {"ok": False, "error": "embeddings and metadata lengths must match"}

            # Ensure all metadata entries are non-empty dicts
            metas = [m if isinstance(m, dict) and m else {"id": i} for i, m in enumerate(metas)]

            # Determine embedding dimension
            dim = len(vecs[0]) if isinstance(vecs[0], list) else len(vecs)

            data = []
            for i, (vec, meta) in enumerate(zip(vecs, metas)):
                row = {"vector": vec, **meta}
                if "id" not in row:
                    row["id"] = i
                data.append(row)

            # Try to create or open table
            try:
                tbl = db.open_table(table_name)
            except Exception:
                if create_if_missing:
                    import pyarrow as pa

                    schema = pa.schema(
                        [
                            ("vector", pa.list_(pa.float32(), dim)),
                            ("id", pa.int64()),
                            ("h3_cell", pa.string()),
                            ("source", pa.string()),
                            ("label", pa.string()),
                        ]
                    )
                    tbl = db.create_table(table_name, data, schema=schema, mode="create")
                else:
                    return {"ok": False, "error": f"Table '{table_name}' not found"}

            tbl.add(data)
            return {
                "ok": True,
                "table_name": table_name,
                "rows_added": len(data),
                "total_rows": tbl.count_rows(),
                "dimension": dim,
            }

        # ── Mode: search (vector similarity) ─────────────────────────────
        if mode == "search":
            if not embeddings:
                return {"ok": False, "error": "embeddings vector required for search"}

            query_vec = embeddings if isinstance(embeddings[0], (int, float)) else embeddings[0]

            try:
                tbl = db.open_table(table_name)
            except Exception:
                return {"ok": False, "error": f"Table '{table_name}' not found"}

            search = tbl.search(query_vec).limit(k)
            if refine_factor:
                search = search.refine_factor(refine_factor)
            if filter_expr:
                search = search.where(filter_expr)

            # H3 spatial filtering (post-query)
            results = search.to_list()
            if h3_cell:
                import h3

                try:
                    cells_in_radius = set(h3.grid_disk(h3_cell, h3_radius))
                    results = [r for r in results if r.get("h3_cell", "") in cells_in_radius]
                except Exception:
                    pass
                results = results[:k]

            return {
                "ok": True,
                "results": results,
                "k": k,
                "dim": len(query_vec),
                "n_returned": len(results),
            }

        # ── Mode: spatial ───────────────────────────────────────────────
        if mode == "spatial":
            if not h3_cell:
                return {"ok": False, "error": "h3_cell required for spatial search"}

            try:
                tbl = db.open_table(table_name)
            except Exception:
                return {"ok": False, "error": f"Table '{table_name}' not found"}

            import h3

            cells_in_radius = set(h3.grid_disk(h3_cell, h3_radius))

            all_rows = tbl.to_pandas()
            matching = all_rows[all_rows["h3_cell"].isin(cells_in_radius)]
            results = matching.head(k).to_dict(orient="records") if len(matching) > 0 else []

            return {
                "ok": True,
                "h3_center": h3_cell,
                "h3_radius": h3_radius,
                "results": results,
                "n_returned": len(results),
            }

        # ── Mode: hybrid ─────────────────────────────────────────────────
        if mode == "hybrid":
            if not embeddings or not h3_cell:
                return {"ok": False, "error": "embeddings and h3_cell required for hybrid"}

            query_vec = embeddings if isinstance(embeddings[0], (int, float)) else embeddings[0]

            try:
                tbl = db.open_table(table_name)
            except Exception:
                return {"ok": False, "error": f"Table '{table_name}' not found"}

            import h3

            cells_in_radius = set(h3.grid_disk(h3_cell, h3_radius))

            # Vector search
            search = tbl.search(query_vec).limit(k * 3)
            if refine_factor:
                search = search.refine_factor(refine_factor)
            results = search.to_list()

            # Spatial filter
            results = [r for r in results if r.get("h3_cell", "") in cells_in_radius][:k]

            return {
                "ok": True,
                "results": results,
                "k": k,
                "h3_center": h3_cell,
                "h3_radius": h3_radius,
                "n_returned": len(results),
            }

        # ── Mode: delete_rows ────────────────────────────────────────────
        if mode == "delete_rows":
            if not filter_expr:
                return {"ok": False, "error": "filter_expr required for delete"}

            try:
                tbl = db.open_table(table_name)
            except Exception:
                return {"ok": False, "error": f"Table '{table_name}' not found"}

            before = tbl.count_rows()
            tbl.delete(filter_expr)
            after = tbl.count_rows()

            return {
                "ok": True,
                "table_name": table_name,
                "deleted": before - after,
                "remaining": after,
            }

        return {
            "ok": False,
            "error": f"Unknown mode: {mode}",
            "valid_modes": [
                "search",
                "store",
                "spatial",
                "hybrid",
                "info",
                "list_tables",
                "delete_rows",
            ],
        }

    except Exception as e:
        logger.exception("LanceDB operation failed")
        return {"ok": False, "error": str(e)}
