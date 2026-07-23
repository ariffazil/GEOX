"""Deterministic seismic physics gates domain.

Canonical receipt helper. Gate implementations live in
`geox_mcp.tools.structure_gates` (product path) and re-export here.

DITEMPA BUKAN DIBERI.
"""

from geox_mcp.domain.seismic_physics.receipts import GateStatus, make_gate_receipt, receipt_hash

__all__ = ["GateStatus", "make_gate_receipt", "receipt_hash"]
