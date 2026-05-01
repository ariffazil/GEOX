"""
GEOX MCP Server — THE NINEFOLD SUBSTRATE
DITEMPA BUKAN DIBERI | 888_JUDGE SEAL
"""
import logging
from fastmcp import FastMCP

# --- 1. X-1D Core (Material) ---
from geox.canonical.geox_lithos_tool import geox_lithos_tool
from geox.canonical.geox_pore_fluid_tools import geox_pore_tool, geox_fluid_tool

# --- 2. X-2D Geometry (Structure) ---
from geox.canonical.geox_geometry_tools import geox_strata_tool, geox_break_tool, geox_elastic_tool

# --- 3. X-3D State (Dynamics) ---
from geox.canonical.geox_kinetic_tool import geox_kinetic_tool
from geox.canonical.geox_state_tools import geox_stress_tool, geox_flow_tool

# --- Decision Layer (Convergence & Wealth) ---
from geox.canonical.geox_coupling_engine import geox_convergence_metabolic_loop
from geox.wealth.wealth_score_kernel import geox_to_wealth_score

# --- MCP Initialization ---
mcp = FastMCP("GEOX")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CANONICAL REGISTER (The Ninefold Substrate)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# X-1D: Material Substrates
mcp.tool()(geox_lithos_tool)
mcp.tool()(geox_pore_tool)
mcp.tool()(geox_fluid_tool)

# X-2D: Geometry Substrates
mcp.tool()(geox_strata_tool)
mcp.tool()(geox_break_tool)
mcp.tool()(geox_elastic_tool)

# X-3D: State Substrates
mcp.tool()(geox_kinetic_tool)
mcp.tool()(geox_stress_tool)
mcp.tool()(geox_flow_tool)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION REGISTER (Convergence & Wealth)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mcp.tool()(geox_convergence_metabolic_loop)
mcp.tool()(geox_to_wealth_score)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mcp.run()
