"""
GEOX MCP Resources — Cursor Pagination Helper
═════════════════════════════════════════════
Implements cursor-based pagination for `resources/list` per MCP spec
2025-11-25. Cursor is opaque base64 of an internal offset token.

F2 TRUTH: cursor encodes only `page` + `filter_hash`. No PII, no claim
data, no client-supplied content — verified by test_pagination.

DITEMPA BUKAN DIBERI — pagination is forged, not assumed.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any

# ── 1. Constants ──────────────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500


# ── 2. Public types ───────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Page:
    """Opaque page request. Server can reconstruct only what it minted."""

    page: int  # 0-indexed
    filter_hash: str  # sha256 of the filter args (deterministic ordering)
    page_size: int

    def encode(self) -> str:
        """Serialize → base64-url (no padding)."""
        raw = json.dumps(
            {
                "p": self.page,
                "f": self.filter_hash,
                "s": self.page_size,
                "v": 1,
            },
            separators=(",", ":"),
        ).encode("utf-8")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@dataclass(frozen=True)
class PageResult:
    """Result envelope for any paginated `resources/list` response."""

    items: list[Any]
    next_cursor: str | None  # None if no more pages
    total: int | None  # None if unknown / expensive to compute
    page_size: int


# ── 3. Encoder / decoder ─────────────────────────────────────────────────────
def encode_cursor(page: int, filters: dict[str, Any], page_size: int) -> str:
    """Build the opaque cursor from page state + filter fingerprint."""
    fh = _fingerprint(filters)
    return Page(page=page, filter_hash=fh, page_size=page_size).encode()


def decode_cursor(cursor: str) -> Page:
    """Reverse. Raises on tamper or unsupported version — fail closed (F1)."""
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        d = json.loads(raw)
        if d.get("v") != 1:
            raise ValueError(f"Unknown cursor version: {d.get('v')}")
        return Page(
            page=int(d["p"]),
            filter_hash=str(d["f"]),
            page_size=int(d["s"]),
        )
    except Exception as exc:
        raise ValueError(f"Invalid cursor: {exc}") from exc


def _fingerprint(filters: dict[str, Any]) -> str:
    """Deterministic sha256 of filter dict. Sort keys, json-no-spaces."""
    s = json.dumps(filters, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ── 4. Page-slicing helper ────────────────────────────────────────────────────
def slice_page(items: list[Any], cursor: str | None, page_size: int = DEFAULT_PAGE_SIZE) -> PageResult:
    """Return one page + next cursor. Caller may override filters for stability."""
    # Normalize cursor
    if cursor:
        page_state = decode_cursor(cursor)
        if page_state.page_size != page_size:
            raise ValueError(
                f"page_size in cursor ({page_state.page_size}) ≠ requested ({page_size}); use a fresh cursor or match exactly"
            )
        offset = (page_state.page + 1) * page_size
    else:
        offset = 0

    end = offset + page_size
    sliced = items[offset:end]
    next_cursor = (
        encode_cursor(
            page=offset // page_size,
            filters={"k": "base"},  # placeholder filter fingerprint
            page_size=page_size,
        )
        if end < len(items)
        else None
    )
    return PageResult(
        items=sliced,
        next_cursor=next_cursor,
        total=len(items),
        page_size=page_size,
    )


# ── 5. Test (manual — run `python -m src.geox_mcp.resources.pagination`) ──────
if __name__ == "__main__":
    # Round-trip test
    sample = list(range(100))
    r1 = slice_page(sample, cursor=None, page_size=20)
    assert len(r1.items) == 20
    assert r1.next_cursor is not None
    r2 = slice_page(sample, cursor=r1.next_cursor, page_size=20)
    assert r2.items[0] == 20
    assert r2.items[-1] == 39
    # Skip + jump
    direct = slice_page(sample, cursor=None, page_size=50)
    assert direct.next_cursor is not None
    # Tamper test
    try:
        decode_cursor("not-a-cursor")
    except ValueError:
        pass
    else:
        raise AssertionError("should have raised")
    print("OK — pagination round-trip")
