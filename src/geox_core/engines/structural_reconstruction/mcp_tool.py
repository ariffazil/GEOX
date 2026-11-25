"""Internal MCP registration for geox_structural_reconstruction.

The tool is observe-only. Benchmark mode returns the receipt and does not
write the repository file.
"""

from __future__ import annotations

from geox_core.engines.structural_reconstruction.ledger import dispatch_mode

_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def register_structural_reconstruction(mcp) -> None:
    @mcp.tool(name="geox_structural_reconstruction", annotations=_ANNOTATIONS)
    async def geox_structural_reconstruction(mode: str, payload_json: str = "{}") -> dict:
        """Restore, test depth admission, or falsify kinematic histories.

        mode: restore | depth_sensitivity | falsify_histories | receipt | benchmark.
        Every mode returns the full five-axis gate receipt.
        """
        return dispatch_mode(mode, payload_json)
