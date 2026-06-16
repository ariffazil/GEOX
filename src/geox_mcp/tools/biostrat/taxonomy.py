"""
biostrat/taxonomy.py — PBDB + Mikrotax + GNR API clients for taxonomic resolution.

DITEMPA BUKAN DIBERI — Forged, Not Given.

Provides:
- PBDBClient: query PBDB v1.2 for taxa, occurrences, intervals
- MikrotaxClient: query Nannotax3 API for taxon data
- resolve_taxon(): unified taxonomic resolution (PBDB → Mikrotax fallback)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .schemas import BiostratEnvelope, TaxonRecord

logger = logging.getLogger(__name__)

# ── PBDB Client ──────────────────────────────────────────────────────────────

PBDB_BASE = "https://paleobiodb.org/data1.2"
PBDB_NANNOFOSSIL_CLASS = "Coccolithophyceae"


class PBDBClient:
    """Async client for the Paleobiology Database (PBDB) REST API.

    No authentication required. Read-only. JSON output.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        client = await self._get_client()
        url = f"{PBDB_BASE}/{path}"
        resp = await client.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # ── Taxa ──────────────────────────────────────────────────────────────

    async def taxa_autocomplete(
        self, name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Autocomplete a taxon name.

        Args:
            name: Partial taxon name (e.g. "Emiliania")
            limit: Max results

        Returns:
            List of matching taxa with oid, name, rank, n_occurrences
        """
        data = await self._get("taxa/auto.json", {"name": name, "limit": limit})
        return data.get("records", [])  # type: ignore[no-any-return]

    async def taxa_list(
        self,
        base_name: str,
        rank: str | None = None,
        show: str = "attr,app",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List taxa under a parent taxon.

        Args:
            base_name: Parent taxon name (e.g. "Coccolithophyceae")
            rank: Filter by rank (e.g. "genus", "species")
            show: Fields to show
            limit: Max results

        Returns:
            List of taxon records with attributes and appearance data
        """
        params: dict[str, Any] = {
            "base_name": base_name,
            "show": show,
            "limit": limit,
        }
        if rank:
            params["rank"] = rank
        data = await self._get("taxa/list.json", params)
        return data.get("records", [])  # type: ignore[no-any-return]

    async def taxa_get(self, taxon_name: str) -> TaxonRecord | None:
        """Get detailed info for a specific taxon.

        Args:
            taxon_name: Full taxon name (e.g. "Emiliania huxleyi")

        Returns:
            TaxonRecord or None if not found
        """
        data = await self._get("taxa/list.json", {
            "base_name": taxon_name,
            "show": "attr,app,ecospace",
            "limit": 5,
        })
        records = data.get("records", [])
        if not records:
            return None

        # Find the best match (exact name match preferred)
        rec = None
        for r in records:
            if r.get("nam", "").lower() == taxon_name.lower():
                rec = r
                break
        if rec is None:
            rec = records[0]

        return TaxonRecord(
            name=rec.get("nam", taxon_name),
            accepted_name=rec.get("nam", taxon_name),
            rank=_pbdb_rank(rec.get("rnk", "")),
            parent=rec.get("par", None),
            pbdb_oid=rec.get("oid", None),
            first_occurrence_ma=rec.get("fea"),
            last_occurrence_ma=rec.get("lea"),
            n_occurrences=rec.get("noc"),
            extant=rec.get("ext") == "1",
            provenance="PBDB",
        )

    # ── Occurrences ───────────────────────────────────────────────────────

    async def occs_list(
        self,
        base_name: str,
        show: str = "loc,attr",
        limit: int = 50,
        interval: str | None = None,
        cc: str | None = None,
    ) -> list[dict[str, Any]]:
        """List fossil occurrences.

        Args:
            base_name: Taxon name
            show: Fields to show
            limit: Max results
            interval: Geologic time interval filter (e.g. "Miocene")
            cc: Country code filter (e.g. "MY")

        Returns:
            List of occurrence records
        """
        params: dict[str, Any] = {
            "base_name": base_name,
            "show": show,
            "limit": limit,
        }
        if interval:
            params["interval"] = interval
        if cc:
            params["cc"] = cc
        data = await self._get("occs/list.json", params)
        return data.get("records", [])  # type: ignore[no-any-return]

    # ── Intervals (Geologic Time) ─────────────────────────────────────────

    async def intervals_list(
        self, scale: int = 1, limit: int = 200
    ) -> list[dict[str, Any]]:
        """List geochronologic intervals.

        Args:
            scale: Timescale ID (1=international ages, 5=calcareous nannoplankton zones,
                   24=planktic foram primary biozones)
            limit: Max results

        Returns:
            List of interval records with name, type, age range
        """
        params: dict[str, Any] = {"scale": scale, "limit": limit}
        data = await self._get("intervals/list.json", params)
        return data.get("records", [])  # type: ignore[no-any-return]

    async def get_nannoplankton_zones(self) -> list[dict[str, Any]]:
        """Get all calcareous nannoplankton zones from PBDB (scale=5).

        Returns:
            List of zone records with name, age range, OID
        """
        return await self.intervals_list(scale=5, limit=200)

    async def get_foram_zones(self) -> list[dict[str, Any]]:
        """Get planktic foram primary biozones from PBDB (scale=24).

        Returns:
            List of zone records
        """
        return await self.intervals_list(scale=24, limit=100)

    async def get_ics_intervals(self) -> list[dict[str, Any]]:
        """Get ICS international ages from PBDB (scale=1).

        Returns:
            List of interval records (eons → ages)
        """
        return await self.intervals_list(scale=1, limit=200)

    # ── Collections ───────────────────────────────────────────────────────

    async def colls_list(
        self,
        base_name: str,
        show: str = "loc,strat",
        limit: int = 50,
        interval: str | None = None,
        cc: str | None = None,
    ) -> list[dict[str, Any]]:
        """List fossil collections matching a taxon.

        Args:
            base_name: Taxon name
            show: Fields to show
            limit: Max results
            interval: Time interval filter
            cc: Country code filter

        Returns:
            List of collection records
        """
        params: dict[str, Any] = {
            "base_name": base_name,
            "show": show,
            "limit": limit,
        }
        if interval:
            params["interval"] = interval
        if cc:
            params["cc"] = cc
        data = await self._get("colls/list.json", params)
        return data.get("records", [])  # type: ignore[no-any-return]


# ── Mikrotax Client ──────────────────────────────────────────────────────────

MIKROTAX_API = "https://www.mikrotax.org/system/api"


class MikrotaxClient:
    """Async client for the Nannotax3 (Mikrotax) REST API.

    Note: API may return empty responses (status checked 2026-06-16).
    Use as secondary source after PBDB.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_taxon(
        self,
        name: str | None = None,
        taxon_id: int | None = None,
        db: str = "main",
    ) -> dict[str, Any] | None:
        """Look up a taxon in Nannotax3.

        Args:
            name: Taxon name (e.g. "Emiliania huxleyi")
            taxon_id: Numeric Mikrotax ID
            db: "main" (working taxonomy) or "cat" (Farinacci catalog)

        Returns:
            Taxon data dict or None if not found / API down
        """
        params: dict[str, Any] = {"db": db}
        if name:
            params["name"] = name
        elif taxon_id:
            params["id"] = taxon_id
        else:
            return None

        try:
            client = await self._get_client()
            resp = await client.get(MIKROTAX_API, params=params)
            if resp.status_code != 200 or not resp.text.strip():
                return None
            # API returns HTML, not JSON — parse minimally
            return {"raw_html": resp.text, "status": "ok"}
        except Exception as e:
            logger.warning(f"Mikrotax API error: {e}")
            return None

    @staticmethod
    def build_url(name: str | None = None, taxon_id: int | None = None) -> str:
        """Build a Nannotax3 web URL for manual lookup.

        Args:
            name: Taxon name
            taxon_id: Numeric ID

        Returns:
            URL string for browser lookup
        """
        if taxon_id:
            return f"https://www.mikrotax.org/system/index.php?id={taxon_id}"
        if name:
            return f"https://www.mikrotax.org/system/index.php?taxon={name.replace(' ', '_')}&module=ntax_cenozoic"
        return "https://www.mikrotax.org/Nannotax3/"


# ── Unified Resolver ─────────────────────────────────────────────────────────

async def resolve_taxon(
    taxon_name: str,
    pbdb: PBDBClient | None = None,
    mikrotax: MikrotaxClient | None = None,
) -> TaxonRecord | None:
    """Resolve a taxon name to a canonical TaxonRecord.

    Strategy:
    1. Try PBDB first (reliable, structured JSON, has age data)
    2. Fallback to Mikrotax (has images, but API may be down)
    3. Build TaxonRecord from best available source

    Args:
        taxon_name: Name to resolve
        pbdb: PBDB client instance (created if None)
        mikrotax: Mikrotax client instance (created if None)

    Returns:
        TaxonRecord or None
    """
    _pbdb = pbdb or PBDBClient()
    _mikrotax = mikrotax or MikrotaxClient()

    try:
        # Try PBDB
        record = await _pbdb.taxa_get(taxon_name)
        if record and record.first_occurrence_ma is not None:
            # Enrich with Mikrotax URL
            record.mikrotax_url = MikrotaxClient.build_url(name=taxon_name)
            return record

        # Fallback: try PBDB autocomplete for fuzzy match
        auto = await _pbdb.taxa_autocomplete(taxon_name, limit=5)
        if auto:
            best = auto[0]
            oid = best.get("oid", "")
            # Fetch full record
            full = await _pbdb.taxa_list(
                base_name=best.get("nam", taxon_name),
                show="attr,app",
                limit=1,
            )
            if full:
                rec = full[0]
                return TaxonRecord(
                    name=rec.get("nam", taxon_name),
                    accepted_name=rec.get("nam", taxon_name),
                    rank=_pbdb_rank(rec.get("rnk", "")),
                    pbdb_oid=rec.get("oid"),
                    first_occurrence_ma=rec.get("fea"),
                    last_occurrence_ma=rec.get("lea"),
                    n_occurrences=rec.get("noc"),
                    extant=rec.get("ext") == "1",
                    mikrotax_url=MikrotaxClient.build_url(name=taxon_name),
                    provenance="PBDB (autocomplete)",
                )

        # Last resort: Mikrotax
        mt = await _mikrotax.get_taxon(name=taxon_name)
        if mt and mt.get("status") == "ok":
            return TaxonRecord(
                name=taxon_name,
                accepted_name=taxon_name,
                mikrotax_url=MikrotaxClient.build_url(name=taxon_name),
                provenance="Mikrotax (web only — no structured data)",
            )

        return None
    finally:
        if pbdb is None:
            await _pbdb.close()
        if mikrotax is None:
            await _mikrotax.close()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _pbdb_rank(rnk: Any) -> str:
    """Convert PBDB numeric rank to string."""
    rank_map = {
        5: "genus", 6: "species", 3: "family", 4: "subfamily",
        9: "class", 10: "order", 7: "subgenus", 8: "subspecies",
    }
    if isinstance(rnk, int):
        return rank_map.get(rnk, str(rnk))
    return str(rnk) if rnk else "unknown"
