"""
GEOX Tool Adapters — Host-specific transport wrappers.
DITEMPA BUKAN DIBERI
"""

# FastMCP adapter is the primary/default adapter
from .fastmcp_adapter import mcp, main

__all__ = ["mcp", "main"]
