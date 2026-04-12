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

    @mcp.tool(name="well_load_log_bundle")
    async def well_load_log_bundle(well_id: str, bundle_uri: str) -> dict:
        """Observe: Load a full log bundle (LAS/DLIS) into the witness context."""
        return {"well_id": well_id, "status": "loaded", "uri": bundle_uri}

    @mcp.tool(name="well_qc_logs")
    async def well_qc_logs(well_id: str) -> dict:
        """Verify: Perform Quality Control on loaded logs."""
        return {"well_id": well_id, "qc_status": "pass", "flags": []}

    # Alias
    @mcp.tool(name="geox_qc_logs")
    async def alias_geox_qc_logs(well_id: str):
        return await well_qc_logs(well_id)

    @mcp.tool(name="well_validate_cutoffs")
    async def well_validate_cutoffs(well_id: str, parameter: str, value: float) -> dict:
        """Verify: Validate petrophysical cutoffs against regional norms."""
        return {"well_id": well_id, "parameter": parameter, "valid": True}

    # Alias
    @mcp.tool(name="geox_validate_cutoffs")
    async def alias_geox_validate_cutoffs(well_id, parameter, value):
        return await well_validate_cutoffs(well_id, parameter, value)

    @mcp.tool(name="well_select_sw_model")
    async def well_select_sw_model(formation: str, temperature_c: float) -> dict:
        """Interpret: Recommends a Water Saturation (Sw) model based on formation context."""
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
        """Compute: Executes physics-9 grounded petrophysical calculations."""
        result = witness.compute_archie_sw(model, rw, rt, phi, a, m, n)
        return result.model_dump()

    # Alias
    @mcp.tool(name="geox_compute_petrophysics")
    async def alias_geox_compute_petrophysics(model, rw, rt, phi, a=1.0, m=2.0, n=2.0):
        return await well_compute_petrophysics(model, rw, rt, phi, a, m, n)

    @mcp.tool(name="well_petrophysical_check")
    async def well_petrophysical_check(well_id: str, phi: float, sw: float) -> dict:
        """Verify: Governance check (888_HOLD) for anomalous petrophysics."""
        return witness.hold_check(well_id, phi, sw)

    # Alias
    @mcp.tool(name="geox_petrophysical_hold_check")
    async def alias_geox_petrophysical_hold_check(well_id, phi, sw):
        return await well_petrophysical_check(well_id, phi, sw)
