"""
GEOX → WEALTH Adapter
WELD-002: Bridges GEOX ResourceNode to WEALTH score_kernel input
DITEMPA BUKAN DIBERI

Constitutional contract:
  - EpistemicTag is PRESERVED, never upgraded.
  - ESTIMATE stays ESTIMATE. PLAUSIBLE stays PLAUSIBLE.
  - Upgrading a tag at this boundary is an F2 violation.
  - Governance-blocked nodes cannot enter WEALTH pipeline.
"""

from typing import TypedDict
import sys
from pathlib import Path

# Attempt to locate arifos_types from the arifOS workspace if present
_arifos_types_path = Path("/root/arifOS/packages/arifos-types/py")
if _arifos_types_path.exists():
    sys.path.insert(0, str(_arifos_types_path))

try:
    from arifos_types import (
        ResourceNode,
        EpistemicTag,
        TelemetryPayload,
        Verdict,
    )
    TYPES_AVAILABLE = True
except ImportError:
    TYPES_AVAILABLE = False
    ResourceNode = None
    EpistemicTag = None
    TelemetryPayload = None
    Verdict = None


class WealthInput(TypedDict):
    base_rate: float
    d_s: float
    peace2: float
    maruah_score: float
    epistemic_source: str
    wealth_signals: dict
    extractive_signals: dict
    task_definition: str
    irreversible: bool


class AdmissibilityError(Exception):
    """Raised when a governance-blocked node attempts to cross into WEALTH."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(
            f"Node {node_id} is governance-blocked. "
            "Cannot pass to WEALTH score_kernel."
        )


def geox_to_wealth(node: "ResourceNode", telemetry: "TelemetryPayload", verdict: "Verdict") -> WealthInput:
    """
    GEOX geox_prospect_evaluate → WEALTH score_kernel adapter.

    Args:
        node: ResourceNode from GEOX geology pipeline
        telemetry: TelemetryPayload from GEOX session
        verdict: Verdict from arifos_judge_prospect

    Returns:
        WealthInput dictionary for WEALTH score_kernel

    Raises:
        AdmissibilityError: If node.governance.admissibility_status == "blocked"

    Constitutional rules enforced:
        F2: epistemic_source is passed through, NEVER upgraded
        F1: irreversibile=False for read-only scoring calls
        F13: blocked nodes cannot enter WEALTH pipeline
    """
    if not TYPES_AVAILABLE:
        raise ImportError(
            "arifos_types not installed. "
            "Install via: pip install arifos-types "
            "Or add as git dependency: pip install git+https://github.com/ariffazil/arifOS.git"
        )

    if node.governance.admissibility_status == "blocked":
        raise AdmissibilityError(node.id)

    mod_penalty = len(node.governance.required_modifications or []) * 0.05
    maruah = max(0.0, 1.0 - (node.governance.sigma_policy or 0.0) - mod_penalty)

    epistemic_source = getattr(node.geology, "epistemic_geo", None)
    if epistemic_source is None:
        epistemic_source = EpistemicTag.UNKNOWN

    return WealthInput(
        base_rate=node.economics.discount_rate,
        d_s=telemetry.dS,
        peace2=telemetry.peace2,
        maruah_score=round(maruah, 4),
        epistemic_source=epistemic_source.value,
        wealth_signals={
            "npv_usd": node.economics.npv_usd,
            "irr": node.economics.irr,
            "breakeven": node.economics.breakeven_usd_per_unit,
            "sigma_geo": node.geology.risk_geo,
            "sigma_market": node.economics.sigma_market,
            "sigma_policy": node.governance.sigma_policy,
        },
        extractive_signals={
            "admissibility": node.governance.admissibility_status,
            "penalty_inf": node.governance.penalty_infinite,
            "carbon_cost": node.governance.carbon_cost_usd_per_tco2e,
            "delay_risk": node.governance.delay_risk,
        },
        task_definition=f"score_resource_node:{node.id}",
        irreversible=False,
    )