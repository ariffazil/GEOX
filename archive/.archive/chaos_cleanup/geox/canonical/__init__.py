"""
GEOX Canonical Substrate Tools — Stress, Flow, Pore, Fluid, Kinetic, Lithos, Convergence
═══════════════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Substrate layer: stress/flow/pore/fluid/kinetic/lithos/convergence

These modules register tools via @mcp.tool decorators. mcp is injected at import time.
"""

from __future__ import annotations

import logging
import sys
import importlib.util

logger = logging.getLogger("geox.canonical")

# Modules that define @mcp.tool-decorated substrate tools
_CANONICAL_MODULES = [
    "geox.canonical.geox_state_tools",       # stress, flow
    "geox.canonical.geox_pore_fluid_tools",  # pore, fluid
    "geox.canonical.geox_kinetic_tool",      # kinetic
    "geox.canonical.geox_lithos_tool",       # lithos
    "geox.canonical.geox_coupling_engine",   # convergence
    "geox.canonical.geox_geometry_tools",    # strata, break, elastic
]


def register_canonical_tools(mcp, profile: str = "full") -> None:
    """
    Register canonical substrate tools by injecting mcp into each module's
    namespace before execution, then importing. This preserves the existing
    @mcp.tool decorator pattern in each file without refactoring.
    """
    registered = 0
    for mod_name in _CANONICAL_MODULES:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is None:
                logger.warning(f"  canonical: {mod_name} not found — skipping")
                continue
            module = importlib.util.module_from_spec(spec)
            # Inject mcp so @mcp.tool decorators resolve during exec_module
            module.__dict__["mcp"] = mcp
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            registered += 1
            logger.info(f"  canonical: {mod_name.split('.')[-1]} OK")
        except Exception as e:
            logger.warning(f"  canonical: {mod_name} skipped ({e})")
    logger.info(f"Canonical substrate: {registered}/{len(_CANONICAL_MODULES)} modules registered")
