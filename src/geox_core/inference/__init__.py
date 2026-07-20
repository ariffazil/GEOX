"""
geox_core.inference — Field/Record Bayes Bridge (ADR-008)

═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Inference package: forward models + Bayes update rule for the
field/record bridge defined in ADR-008.

Public surface:
  • voxel_update — Bayes update rule + forward model scaffolds (1D/2D/3D/4D)
  • (future) process_state_graph — Markov propagation for process_state
  • (future) multi_voxel_inference — joint inference over voxel grids

Skeleton-only this cycle. Real physics deferred to subsequent forge tranches.
"""

from __future__ import annotations

from geox_core.inference.voxel_update import (
    BayesUpdateResult,
    BiasModel,
    ForwardModel,
    ForwardModel1D,
    ForwardModel2D,
    ForwardModel3D,
    ForwardModel4D,
    Observation,
    ObservationKind,
    ObservationSource,
    apply_bias_correction,
    bayes_update_voxel,
    bayes_update_voxel_sequence,
    ensemble_posteriors,
    gaussian_likelihood,
)

__all__ = [
    "BiasModel",
    "ForwardModel",
    "ForwardModel1D",
    "ForwardModel2D",
    "ForwardModel3D",
    "ForwardModel4D",
    "Observation",
    "ObservationKind",
    "ObservationSource",
    "apply_bias_correction",
    "bayes_update_voxel",
    "bayes_update_voxel_sequence",
    "ensemble_posteriors",
    "gaussian_likelihood",
    "BayesUpdateResult",
]
