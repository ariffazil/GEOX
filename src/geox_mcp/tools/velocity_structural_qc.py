
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from geox_core.engines.seismic.velocity_structural_qc import VelocityStructuralEngine
from geox_core.schemas.velocity_mapping import VelocityFailureMode, VelocityQCGate
from geox_core.schemas.velocity_policy import VelocityACRiskPolicy


def register_velocity_tools(mcp: FastMCP):
    """
    Registers the Velocity-Driven Structural Mapping QC tools to the FastMCP server.
    """

    @mcp.tool(
        name="geox_velocity_structural_mapping_qc",
        description="""
        Evaluates a velocity cube for its validity as a structural mapping proxy.
        Enforces the 8 QC gates and identifies 6 critical failure modes.
        Returns a Binary Transport RenderPayload with a strict Epistemic Claim (EARTHMODEL).
        """
    )
    def geox_velocity_structural_mapping_qc(
        cube_id: str = Field(..., description="The ID of the velocity cube to evaluate"),
        source_model_version: str = Field(..., description="Version of the source model (e.g., FWI_v3)"),
        cleared_gates: list[VelocityQCGate] = Field(..., description="List of QC gates that have passed"),
        identified_failures: list[VelocityFailureMode] = Field(..., description="List of failure modes present in the volume"),
        evidence_for: str = Field(..., description="Geological/geophysical evidence supporting this velocity model"),
        evidence_against: str = Field(..., description="Contradicting evidence or unresolved artifacts"),
        uncertainty_band: str = Field("P10-P90 Not Calculated", description="Uncertainty spread across realizations"),
        proxy_id: str | None = Field(None, description="Unique proxy packet ID"),
        lineage: list[dict] | None = Field(None, description="List of VelocityLineageEvent dicts"),
        evidence_handles: list[str] | None = Field(None, description="URIs pointing to QC artifacts")
    ) -> dict:
        """
        Executes the VelocityStructuralEngine to compute AC Risk and 
        format the claim according to the GEOX Epistemic Ladder.
        """
        # In production, policy could be loaded from db based on region. Using default.
        engine = VelocityStructuralEngine(policy=VelocityACRiskPolicy())
        payload = engine.evaluate_velocity_cube(
            cube_id=cube_id,
            source_model_version=source_model_version,
            cleared_gates=cleared_gates,
            identified_failures=identified_failures,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            uncertainty_band=uncertainty_band,
            proxy_id=proxy_id,
            lineage=lineage,
            evidence_handles=evidence_handles
        )
        
        # Return as JSON dictionary for MCP transport
        # The frontend will use cube_manifest_uri to fetch the actual 3D bricks via binary transport
        return payload.model_dump()
