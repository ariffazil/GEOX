import os
import logging
import sys
from fastmcp import FastMCP

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Unified Dimension-Native Server (v2.0.0)
# DITEMPA BUKAN DIBERI: Dimension-First Ontology
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox.unified")

mcp = FastMCP(
    name="GEOX",
    on_duplicate="error",
# strict_input_validation=True
)

GEOX_VERSION = "2.0.0-DIMENSION-NATIVE"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"

# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE GATING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_PROFILE = os.getenv("GEOX_PROFILE", "full")

# Mapping of profile to enabled dimensions
DIMENSION_GATES = {
    "core": ["physics", "map"],
    "vps": ["prospect", "well", "earth3d", "map", "cross"],
    "full": ["prospect", "well", "section", "earth3d", "time4d", "physics", "map", "cross"]
}

ENABLED_DIMENSIONS = DIMENSION_GATES.get(GEOX_PROFILE, ["physics", "map"])

logger.info(f"Initializing GEOX Unified Server with profile: {GEOX_PROFILE}")
logger.info(f"Enabled Dimensions: {', '.join(ENABLED_DIMENSIONS)}")

# ═══════════════════════════════════════════════════════════════════════════════
# INTELLIGENCE LAYER: arifOS Thinking module
# ═══════════════════════════════════════════════════════════════════════════════

try:
    # Ensure arifosmcp is in path
    arifos_path = r"C:\ariffazil\arifOS"
    if arifos_path not in sys.path:
        sys.path.append(arifos_path)
    
    from arifosmcp.runtime.thinking import ThinkingSessionManager
    tsm = ThinkingSessionManager()
    HAS_THINKING = True
    logger.info("arifOS Thinking Module activated")
except Exception as e:
    logger.warning(f"arifOS Thinking Module disabled: {e}")
    HAS_THINKING = False

# ═══════════════════════════════════════════════════════════════════════════════
# DIMENSION REGISTRIES BOOTSTRAP
# ═══════════════════════════════════════════════════════════════════════════════

# Add current directory to path for registry imports
sys.path.append(os.getcwd())

def bootstrap_registries():
    # Registry to Import path mapping
    registry_map = {
        "prospect": "registries.prospect",
        "well": "registries.well",
        "section": "registries.section",
        "earth3d": "registries.earth3d",
        "time4d": "registries.time4d",
        "physics": "registries.physics",
        "map": "registries.map",
        "cross": "registries.cross"
    }

    for dim in ENABLED_DIMENSIONS:
        if dim in registry_map:
            module_name = registry_map[dim]
            try:
                # Dynamic import
                import importlib
                module = importlib.import_module(module_name)
                
                # Check for registration function
                func_name = f"register_{dim}_tools"
                if hasattr(module, func_name):
                    register_func = getattr(module, func_name)
                    register_func(mcp, profile=GEOX_PROFILE)
                    logger.info(f"Registered {dim.upper()} tools")
                else:
                    logger.warning(f"No registration function found for {dim}")
            except Exception as e:
                logger.error(f"Failed to bootstrap {dim} registry: {e}")

# Run Bootstrap
bootstrap_registries()

# ═══════════════════════════════════════════════════════════════════════════════
# CORE RESOURCES (Physics9 Sovereignty)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("physics9://materials_atlas")
async def get_geox_materials() -> str:
    """RATLAS Global Material Database for physics verification."""
    # Check current directory for the material file
    if os.path.exists("geox_atlas_99_materials.csv"):
        import pandas as pd
        return pd.read_csv("geox_atlas_99_materials.csv").to_string()
    return "Error: RATLAS csv missing."

# Interchangeable Alias (Legacy support)
@mcp.resource("canon9://materials_atlas")
async def get_geox_materials_legacy() -> str:
    return await get_geox_materials()

@mcp.resource("geox://reasoning/traces/{session_id}")
async def get_reasoning_trace_resource(session_id: str) -> str:
    """Provides a markdown view of a specific reasoning trace."""
    if not HAS_THINKING:
        return "Thinking module disabled."
    
    session = tsm.get_session(session_id)
    if not session:
        return f"Session {session_id} not found."
    
    return session.export_markdown()

@mcp.resource("geox://profile/status")
async def get_profile_status() -> dict:
    """Returns the current server profile and active dimensions."""
    return {
        "profile": GEOX_PROFILE,
        "enabled_dimensions": ENABLED_DIMENSIONS,
        "version": "2.0.0-UNIFIED"
    }

# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS: Sovereign Intelligence
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.prompt(name="SOVEREIGN_GEOX_SYSTEM_PROMPT")
def geox_system_prompt() -> str:
    return """
    You are GEOX, a sovereign subsurface governance coprocessor. 
    You are a Brutalist Geologist.
    
    RESPONSE CONTRACT (MANDATORY):
    Return your response as a structured report:
    - SUMMARY: [Max 2 sentences UI text]
    - STANCE: [CLAIM | PLAUSIBLE | HYPOTHESIS | UNKNOWN | HOLD]
    - BLOCKING: [true | false]
    - FLOOR_REPORT: [F2 Truth status, F7 Humility notes, F9 Anti-Hantu flags]
    - NEXT_TOOL: [Optional mcp.tool suggestion to clear blocks]
    
    GOVERNANCE RULES:
    1. If scene status is 'HOLD', you MUST set BLOCKING: true and STANCE: HOLD.
    2. Never invent numbers. Reference only provided context.
    3. State the dimension (PROSPECT/WELL/SECTION/EARTH3D/TIME4D/PHYSICS/MAP).
    """


def main() -> None:
    mcp.run()

# ═══════════════════════════════════════════════════════════════════════════════
# SERVER ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
