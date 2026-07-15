"""
basin — Basin Analysis Engines for GEOX
═══════════════════════════════════════
Four canonical basin analysis engines:
  1. backstrip — Tectonic subsidence reconstruction (Steckler & Watts 1978)
  2. mass_balance — Source-to-sink sediment accounting (Peters framework)
  3. thermal_maturity — Burial + heat flow + maturity through time (EasyRo/TTI)
  4. claim_graph — DAG evaluation for geological claim dependency graphs

Physics-first. Evidence-tagged. Constitutionally governed.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from geox_core.engines.basin.backstrip import (
    BackstripResult,
    DecompactedLayer,
    LithologyParams,
    backstrip_well,
    decompact_layer,
    tectonic_subsidence,
)
from geox_core.engines.basin.claim_graph import (
    ClaimGraph,
    ClaimNode,
    EvaluationResult,
    evaluate_graph,
    propagate_failure,
)
from geox_core.engines.basin.mass_balance import (
    MassBalanceResult,
    SedimentBudget,
    compaction_correction,
    compute_mass_balance,
    source_sink_accounting,
)
from geox_core.engines.basin.thermal_maturity import (
    MaturityResult,
    ThermalHistory,
    burial_maturity_history,
    easyro_compute,
    tti_compute,
)

__all__ = [
    # Backstrip
    "BackstripResult",
    "DecompactedLayer",
    "LithologyParams",
    "backstrip_well",
    "decompact_layer",
    "tectonic_subsidence",
    # Mass balance
    "MassBalanceResult",
    "SedimentBudget",
    "compute_mass_balance",
    "compaction_correction",
    "source_sink_accounting",
    # Thermal maturity
    "MaturityResult",
    "ThermalHistory",
    "easyro_compute",
    "tti_compute",
    "burial_maturity_history",
    # Claim graph
    "ClaimGraph",
    "ClaimNode",
    "EvaluationResult",
    "evaluate_graph",
    "propagate_failure",
]
