"""
GEOX Claims Domain Server — H5 Claim Engine
═══════════════════════════════════════════
Canonical claim lifecycle: create → challenge → evidence → seal.

Mounted by server.py with namespace=None (original names preserved).
DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from geox_mcp.tools._register import register_tools_on_server
from geox_mcp.tools.claims import (
    geox_claim_challenge,
    geox_claim_create,
    geox_claim_seal,
    geox_evidence_attach,
)

_CLAIMS_TOOLS: list[tuple[str, Any]] = [
    ("geox_claim_create", geox_claim_create),
    ("geox_claim_challenge", geox_claim_challenge),
    ("geox_evidence_attach", geox_evidence_attach),
    ("geox_claim_seal", geox_claim_seal),
]

_CLAIMS_ANNOTATIONS: dict[str, dict] = {
    "geox_claim_create": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_claim_challenge": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_evidence_attach": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_claim_seal": {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


def create_claims_server() -> FastMCP:
    server = FastMCP("geox-claims")
    register_tools_on_server(server, _CLAIMS_TOOLS, _CLAIMS_ANNOTATIONS)
    return server
