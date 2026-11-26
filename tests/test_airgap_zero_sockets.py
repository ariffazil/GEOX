"""Phase E --airgap --stdio test: prove zero outbound sockets during GEOX execution."""
from __future__ import annotations

import socket
import pytest

from geox.airgap import AirgapViolationError, airgap_context, is_airgap_enabled
from geox.forensics.well_pda import geox_well_pda


def test_airgap_blocks_outbound_sockets_and_runs_well_pda_offline() -> None:
    with airgap_context():
        assert is_airgap_enabled() is True
        # Attempting any outbound socket must fail closed
        with pytest.raises(AirgapViolationError):
            socket.create_connection(("1.1.1.1", 443), timeout=1)
        # Running GEOX well pre-flight auditor succeeds with zero network calls
        res = geox_well_pda(mode="all", payload=None)
        assert res["verdict"] == "READY"
    assert is_airgap_enabled() is False
