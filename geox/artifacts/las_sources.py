"""Materialize LAS sources that arrive through existing MCP arguments."""

from __future__ import annotations

import base64
import hashlib
import os
import urllib.request
from pathlib import Path


MAX_INLINE_LAS_BYTES = int(os.environ.get("GEOX_MAX_INLINE_LAS_BYTES", str(25 * 1024 * 1024)))
WELL_DATA_DIR = Path(os.environ.get("GEOX_WELL_DATA_DIR", "/data/wells"))


class LASSourceError(ValueError):
    """Raised when a LAS source cannot be materialized on the GEOX server."""


def materialize_las_source(source: str, *, artifact_id: str | None = None) -> str:
    """Return a server-visible LAS path for local, URL, data URI, or base64 input."""
    if not source:
        raise LASSourceError("LAS source is empty")

    if source.startswith("data:"):
        return _write_inline_payload(_decode_data_uri(source), artifact_id=artifact_id)

    if source.startswith("base64:"):
        return _write_inline_payload(
            _decode_base64(source.removeprefix("base64:")),
            artifact_id=artifact_id,
        )

    if source.startswith(("http://", "https://")):
        # Red Team Fix: Basic SSRF protection
        from urllib.parse import urlparse
        import socket
        
        parsed = urlparse(source)
        hostname = parsed.hostname
        if not hostname:
            raise LASSourceError("Invalid URL: no hostname")
        
        # FIND-LIVE-002 FIX: Comprehensive SSRF blocklist
        # Block all private, loopback, and metadata IP ranges
        hostname_lower = hostname.lower()
        if hostname_lower in ("localhost", "127.0.0.1", "::1"):
            raise LASSourceError(f"Access to {hostname} is blocked (loopback)")

        # Check for IPv4 private ranges (10/8, 172.16/12, 192.168/16)
        if hostname_lower.startswith(("10.", "192.168.", "172.")):
            if hostname_lower.startswith("172."):
                try:
                    second_octet = int(hostname_lower.split(".")[1])
                    if 16 <= second_octet <= 31:
                        raise LASSourceError(f"Access to {hostname} is blocked (private IP range 172.16/12)")
                except (IndexError, ValueError):
                    pass
            else:
                raise LASSourceError(f"Access to {hostname} is blocked (private IP range)")

        # Block169.254.0.0/16 (AWS metadata, link-local)
        if hostname_lower.startswith(("169.254.", "0.")):
            raise LASSourceError(f"Access to {hostname} is blocked (link-local/metadata range)")

        # Block IPv6 link-local and unique local
        if ":" in hostname and not hostname_lower.startswith(("2a0", "2001:db8")):
            raise LASSourceError(f"Access to {hostname} is blocked (IPv6 internal range)")

        # Block URLs with credentials (credential injection)
        if parsed.port or "@" in source:
            raise LASSourceError(f"URL with port or credentials not allowed")
            
        suffix = Path(source.split("?", 1)[0]).suffix or ".las"
        target = _target_path(artifact_id, suffix=suffix)
        try:
            urllib.request.urlretrieve(source, target)
        except Exception as exc:
            raise LASSourceError(f"Could not fetch LAS URL: {exc}") from exc
        return str(target)

    local_path = source
    # Red Team Fix: Block absolute paths to prevent arbitrary file read
    if os.path.isabs(local_path):
        # We only allow absolute paths if they are under /data or /app/fixtures
        resolved = Path(local_path).resolve()
        is_safe = False
        for safe_root in [Path("/data"), Path("/app/fixtures")]:
            if resolved == safe_root or resolved.is_relative_to(safe_root):
                is_safe = True
                break
        if not is_safe:
            raise LASSourceError(f"Absolute path {local_path} is not under an allowed directory (/data or /app/fixtures)")
    else:
        # Relative paths are checked against /app/fixtures then /data
        fixture_path = f"/app/fixtures/{os.path.basename(local_path)}"
        if os.path.exists(fixture_path):
            local_path = fixture_path
        elif os.path.exists(f"/data/{local_path}"):
            local_path = f"/data/{local_path}"
        else:
            raise FileNotFoundError(f"LAS file not found: {local_path}")

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"LAS file not found: {local_path}")
    return local_path


def _decode_data_uri(source: str) -> bytes:
    header, sep, payload = source.partition(",")
    if not sep:
        raise LASSourceError("Invalid data URI: missing comma separator")
    if ";base64" not in header.lower():
        raise LASSourceError("Only base64 data URIs are supported for LAS payloads")
    return _decode_base64(payload)


def _decode_base64(payload: str) -> bytes:
    try:
        decoded = base64.b64decode(payload.strip(), validate=True)
    except Exception as exc:
        raise LASSourceError(f"Invalid base64 LAS payload: {exc}") from exc
    if not decoded:
        raise LASSourceError("Decoded LAS payload is empty")
    if len(decoded) > MAX_INLINE_LAS_BYTES:
        raise LASSourceError(
            f"Decoded LAS payload exceeds {MAX_INLINE_LAS_BYTES} byte limit"
        )
    return decoded


def _write_inline_payload(payload: bytes, *, artifact_id: str | None = None) -> str:
    WELL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = _target_path(artifact_id, payload=payload)
    target.write_bytes(payload)
    return str(target)


def _target_path(
    artifact_id: str | None = None,
    *,
    suffix: str = ".las",
    payload: bytes | None = None,
) -> Path:
    safe_id = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in (artifact_id or ""))
    if not safe_id:
        digest = hashlib.sha256(payload or os.urandom(16)).hexdigest()[:16]
        safe_id = f"inline_las_{digest}"
    if not suffix.lower().endswith(".las"):
        suffix = ".las"
    return WELL_DATA_DIR / f"{safe_id}{suffix}"
