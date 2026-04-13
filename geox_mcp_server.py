"""
Backward-compatible GEOX MCP entrypoint.

Canonical public server: geox_unified_mcp_server.py
"""

from __future__ import annotations

import fastmcp

from geox_unified_mcp_server import *  # noqa: F401,F403
from geox_unified_mcp_server import __all__ as _UNIFIED_ALL

IS_FASTMCP_3 = tuple(int(part) for part in fastmcp.__version__.split(".")[:2]) >= (3, 0)

__all__ = [
    *_UNIFIED_ALL,
    "IS_FASTMCP_3",
]


if __name__ == "__main__":
    main()
