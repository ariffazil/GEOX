"""
_artifact_identity — P0-3 canonical artifact reference scheme (Phase C).

Forged 2026-07-25 · FI-008 (kimi-code).

The audit identified that the ingest→QC contract breaks because ingest
returns ``well_las:<WELL>`` (display-name based) while QC expects the
artifact_ref to round-trip through a UWI-or-WELL parser. The downstream
chain therefore fails on the simplest production case:

    ingest     → artifact_ref = "well_las:GEOX-AUDIT-01"
    QC(artifact_ref=...)
                → Identity Mismatch: UWI='AUDIT-0001' vs WELL='GEOX-AUDIT-01'

DOCTRINE
========

Every artifact has exactly ONE canonical reference:

    artifact://geox/<kind>/<canonical_id>/sha256-<hex>[@v<n>]

where:
  - kind          : "well_las" | "well_qc" | "seismic_segy" | "well_log" ...
  - canonical_id  : UWI when present, else ``well:<WELL>``
  - sha256        : 64-char hex digest of the artifact bytes
  - version       : optional positive integer for revised artifacts

WELL, filename, and legacy aliases (``well_las:<name>``, ``WELL:<name>``)
remain as metadata — never as primary keys.

The functions in this module are PURE (no I/O, no module-level state).
They are the single source of truth for parsing and emitting canonical
artifact references. Every ingest/QC/downstream tool SHOULD consume
``parse_artifact_ref`` and emit ``make_artifact_id``.

REVERSIBILITY
=============

All ingest/QC/downstream tools retain their legacy accept/emit paths.
The canonical helpers are additive — they enhance, never replace.
To revert: stop calling ``make_artifact_id`` / ``parse_artifact_ref``;
remove the helpers file; everything still works the old way.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import unquote, urlparse

# ── Canonical scheme ───────────────────────────────────────────────────────

ARTIFACT_SCHEME = "artifact"

# Pattern: artifact://geox/<kind>/<canonical_id>/sha256-<64hex>[@v<n>]
# canonical_id may contain ``:`` (for ``well:<WELL>`` or ``uwi:<UWI>``)
# and any URL-safe characters except ``/`` and ``@``.
# We capture the trailing ``@v<n>`` separately.
_CANONICAL_RE = re.compile(
    r"^artifact://geox/(?P<kind>[a-z][a-z0-9_]+)/(?P<canonical_id>[^/@]+)/sha256-(?P<sha256>[0-9a-f]{64})(?:@v(?P<version>\d+))?$"
)

# Legacy patterns:
#   well_las:<name>
#   WELL:<name>
#   <name>  (bare, treated as WELL display name)
_LEGACY_PREFIX_RE = re.compile(r"^(?:well_las|well_qc|well_log|WELL):(.+)$")


# ── Constructors ───────────────────────────────────────────────────────────


def make_artifact_id(
    kind: str,
    canonical_id: str,
    sha256: str,
    version: int | None = None,
) -> str:
    """Build the canonical artifact:// reference.

    Args:
        kind: e.g. ``"well_las"`` — short taxonomy token (alnum + ``_``).
        canonical_id: UWI or ``well:<WELL>`` or other stable identifier.
            The function does NOT validate the format beyond encoding.
        sha256: 64-char hex digest of the artifact bytes (without the
            ``sha256:`` prefix).
        version: optional positive integer for revised artifacts.

    Returns:
        The canonical reference string, e.g.
        ``artifact://geox/well/AUDIT-0001/sha256-69558c...``

    Raises:
        ValueError: when inputs violate the contract.
    """
    if not kind or not re.match(r"^[a-z][a-z0-9_]+$", kind):
        raise ValueError(f"invalid kind: {kind!r} (must match ^[a-z][a-z0-9_]+$)")
    if not canonical_id:
        raise ValueError("canonical_id is required")
    clean_sha = sha256.removeprefix("sha256:")
    if not re.match(r"^[0-9a-f]{64}$", clean_sha):
        raise ValueError(
            f"invalid sha256: {sha256!r} (expected 64 hex chars)"
        )
    if version is not None and (not isinstance(version, int) or version < 1):
        raise ValueError(f"invalid version: {version!r} (must be int >= 1)")

    ref = f"{ARTIFACT_SCHEME}://geox/{kind}/{canonical_id}/sha256-{clean_sha}"
    if version is not None:
        ref += f"@v{version}"
    return ref


def canonicalize_well_ref(well_name: str | None, uwi: str | None) -> str:
    """Compute the canonical_id segment for a well.

    Preference: UWI when present (industry-standard unique identifier),
    else ``well:<WELL>`` (display name with explicit namespace prefix).
    Returns an empty string when both are absent.
    """
    if uwi:
        clean = uwi.strip()
        if clean:
            return clean
    if well_name:
        clean = well_name.strip()
        if clean:
            return f"well:{clean}"
    return ""


def sha256_for_bytes(data: bytes) -> str:
    """Compute the lowercase hex SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def sha256_for_file(path: str) -> str:
    """Stream-compute the SHA-256 of a file. Empty string on read error."""
    sha = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                sha.update(chunk)
    except OSError:
        return ""
    return sha.hexdigest()


# ── Parser ────────────────────────────────────────────────────────────────


def parse_artifact_ref(ref: str) -> dict[str, Any] | None:
    """Parse any artifact reference into a normalized dict.

    Accepts:
      - Canonical: ``artifact://geox/<kind>/<id>/sha256-<hex>[@v<n>]``
      - Legacy:    ``well_las:<name>``, ``WELL:<name>``, ``well_qc:<name>``
      - Bare:      ``<name>``  (treated as a WELL display name)

    Returns a dict with at minimum ``raw``, ``kind``, ``canonical_id``,
    ``sha256`` (may be None), ``version`` (may be None), and ``format``
    ("canonical" | "legacy_prefix" | "bare").

    Returns None only when the input is empty/whitespace.
    """
    if not ref or not isinstance(ref, str):
        return None
    ref = ref.strip()
    if not ref:
        return None

    # Canonical
    m = _CANONICAL_RE.match(ref)
    if m:
        return {
            "raw": ref,
            "format": "canonical",
            "kind": m.group("kind"),
            "canonical_id": unquote(m.group("canonical_id")),
            "sha256": m.group("sha256"),
            "version": int(m.group("version")) if m.group("version") else None,
        }

    # Legacy prefix: well_las:NAME, WELL:NAME, etc.
    m = _LEGACY_PREFIX_RE.match(ref)
    if m:
        name = m.group(1).strip()
        kind = ref.split(":", 1)[0].lower()
        return {
            "raw": ref,
            "format": "legacy_prefix",
            "kind": kind,
            "canonical_id": f"well:{name}" if name else "",
            "display_name": name,
            "sha256": None,
            "version": None,
        }

    # Bare: treat as WELL display name (best-effort back-compat).
    bare = ref.strip()
    if bare:
        return {
            "raw": ref,
            "format": "bare",
            "kind": "well_las",  # assume well_las by default for bare refs
            "canonical_id": f"well:{bare}",
            "display_name": bare,
            "sha256": None,
            "version": None,
        }
    return None


def artifact_refs_equal(a: str, b: str) -> bool:
    """Return True iff two refs refer to the same artifact.

    Compares the canonical (kind, canonical_id, sha256) triple. Legacy
    refs are normalized to their canonical form before comparison, so
    ``well_las:GEOX-AUDIT-01`` equals ``artifact://geox/well_las/well:GEOX-AUDIT-01/sha256-<any>``
    only when the canonical_id segment matches and both lack a hash;
    otherwise the canonical form's sha256 wins.
    """
    pa = parse_artifact_ref(a)
    pb = parse_artifact_ref(b)
    if pa is None or pb is None:
        return False
    if pa["kind"] != pb["kind"]:
        return False
    if pa["canonical_id"] != pb["canonical_id"]:
        return False
    if pa["sha256"] and pb["sha256"] and pa["sha256"] != pb["sha256"]:
        return False
    return True


# ── Storage key resolution ────────────────────────────────────────────────


def storage_keys_for(ref: str) -> list[str]:
    """Return the in-memory artifact-store keys to try for ``ref``.

    The artifact store uses an in-memory dict keyed by the legacy
    ``well_las:<name>`` form (and possibly other legacy forms). Given any
    artifact_ref, return ALL candidate keys so the caller can do a
    defensive lookup until the store migrates to canonical keys.

    Always returns at least one element. The order is "most likely first".
    """
    parsed = parse_artifact_ref(ref)
    if parsed is None:
        return []

    keys: list[str] = []

    # 1. The raw input — fastest path when caller passes the same form
    #    the store uses.
    keys.append(parsed["raw"])

    # 2. If the parsed ref has a display_name, emit the legacy prefix.
    display = parsed.get("display_name")
    if not display and parsed["canonical_id"].startswith("well:"):
        display = parsed["canonical_id"][len("well:") :]
    if display:
        kind = parsed.get("kind", "well_las")
        keys.append(f"{kind}:{display}")

    # 3. The canonical form itself.
    if parsed["format"] != "canonical" and parsed.get("sha256"):
        keys.append(
            make_artifact_id(
                kind=parsed["kind"],
                canonical_id=parsed["canonical_id"],
                sha256=parsed["sha256"],
                version=parsed.get("version"),
            )
        )

    # Dedupe while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out
