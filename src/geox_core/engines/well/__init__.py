"""geox_core.engines.well — wellbore computational engines.

Engines here are kernels (pure compute). MCP-facing wrappers live in
geox_mcp.tools. This separation: kernels are testable offline; tools
are wiring.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

__all__ = ["desurvey_core"]
