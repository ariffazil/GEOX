import logging
from fastmcp import FastMCP

logger = logging.getLogger("geox.well")

def register_well_tools(mcp: FastMCP, profile: str = "full"):
    """
    WELL Registry: Borehole & Log Analysis tools.
    'What's in this borehole?'
    """
    
    try:
        from services.witness_engine.petrophysics import witness
    except ImportError:
        logger.error("Well services unavailable")
        return

    @mcp.tool(name="well_select_sw_model")
    async def well_select_sw_model(formation: str, temperature_c: float) -> dict:
        """Recommends a Water Saturation (Sw) model based on formation context."""
        return witness.select_sw_model(formation, temperature_c)

    # Alias
    @mcp.tool(name="geox_select_sw_model")
    async def alias_geox_select_sw_model(formation: str, temperature_c: float) -> dict:
        return await well_select_sw_model(formation, temperature_c)

    @mcp.tool(name="well_compute_petrophysics")
    async def well_compute_petrophysics(
        model: str, 
        rw: float, 
        rt: float, 
        phi: float, 
        a: float = 1.0, 
        m: float = 2.0, 
        n: float = 2.0
    ) -> dict:
        """Executes physics-9 grounded petrophysical calculations."""
        result = witness.compute_archie_sw(model, rw, rt, phi, a, m, n)
        return result.model_dump()

    # Alias
    @mcp.tool(name="geox_compute_petrophysics")
    async def alias_geox_compute_petrophysics(model, rw, rt, phi, a=1.0, m=2.0, n=2.0):
        return await well_compute_petrophysics(model, rw, rt, phi, a, m, n)

    @mcp.tool(name="well_petrophysical_check")
    async def well_petrophysical_check(well_id: str, phi: float, sw: float) -> dict:
        """Governance check (888_HOLD) for anomalous petrophysics."""
        return witness.hold_check(well_id, phi, sw)

    # Alias
    @mcp.tool(name="geox_petrophysical_hold_check")
    async def alias_geox_petrophysical_hold_check(well_id, phi, sw):
        return await well_petrophysical_check(well_id, phi, sw)
    
    # New Standardized Name from user request
    @mcp.tool(name="well_earth_signals")
    async def well_earth_signals(well_id: str) -> dict:
        """Fetch raw earth signals for a well."""
        return {"well_id": well_id, "signals": "Placeholder for earth signals logic"}

    @mcp.tool(name="geox_earth_signals")
    async def alias_geox_earth_signals(well_id):
        return await well_earth_signals(well_id)

    @mcp.tool(name="well_compute_stoiip")
    async def well_compute_stoiip(well_id: str) -> dict:
        """Compute Stock Tank Oil Initially In Place (STOIIP) for a well vicinity."""
        return {"well_id": well_id, "stoiip": 100.0, "unit": "MMbbl", "status": "Placeholder"}

    @mcp.tool(name="geox_compute_stoiip")
    async def alias_geox_compute_stoiip(well_id):
        return await well_compute_stoiip(well_id)
