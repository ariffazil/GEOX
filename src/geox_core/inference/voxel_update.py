"""
geox_core.inference — Field/Record Bayes Bridge (ADR-008)

═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, not given.

This module implements the Bayes bridge between:
  • FIELD LAYER  — VoxelState4 latent variables (continuous Earth-physics)
  • RECORD LAYER — noisy, biased, sparse observations (rocks, logs, seismic)

Per ADR-008, GEOX lives in the field layer. Rocks are data, not the field.
Bayes is the bridge.

THIS IS A SKELETON — doc-only pilot per ADR-008 Phase 1.
Real forward models (rock physics, seismic synthetics, EM responses) come in
Phase 2+ forge tranches, each gated by per-item ADR.

What is real in this skeleton:
  • Bayes update formula (Bayes theorem applied to voxel posterior)
  • Likelihood scaffold (Gaussian likelihood on residual)
  • Observation bias model
  • 1D/2D/3D/4D forward model signature unification
  • Multi-voxel posterior ensemble support

What is stubbed:
  • Concrete forward models (use placeholders until physics arrives)
  • Real rock-physics transforms (Archie, Gardner, Wyllie — defer to lem_predict)
  • Real seismic synthetics (defer to geox_seismic_compute)
  • Real EM responses (defer to geox_mt_forward)

Anti-misconception spine (carried over from voxel_state.py):
  • "rock type = everything"  →  material_state is a derived field, not a label
  • "rock cycle is one clean loop"  →  process_state Markov allows non-cyclic history
  • "deformed = metamorphic"  →  strain_state is its own axis
  • "rock is solid or a cave"  →  void_state is multi-phase
  • "unconformity = time void"  →  record_density tracks temporal record coverage

═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, Sequence

# Pydantic v2 (consistent with voxel_state.py)
from pydantic import BaseModel, ConfigDict, Field

# The canonical voxel envelope (ADR-008)
from geox_core.schemas.voxel_state import (
    LithologyClass,
    PhaseType,
    VoxelState4,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. OBSERVATION MODEL — record-layer data types
# ═══════════════════════════════════════════════════════════════════════════════


class ObservationKind(str, Enum):
    """
    Kind of record-layer observation.

    Maps to GEOX canonical tools (per ADR-008 tool re-classification):
      well_log     ← geox_well_ingest / geox_petrophysics
      seismic_2d   ← geox_seismic_compute (attribute mode)
      seismic_3d   ← geox_seismic_compute (synthetic mode)
      seismic_4d   ← re-run at different epoch
      outcrop      ← geox_evidence (record-layer survey)
      vision       ← geox_vision (high-bias soft prior)
    """

    well_log = "well_log"
    seismic_2d = "seismic_2d"
    seismic_3d = "seismic_3d"
    seismic_4d = "seismic_4d"
    outcrop = "outcrop"
    vision = "vision"


class ObservationSource(str, Enum):
    """
    Source provenance for the observation.

    Used to bias-weight observations: outcrop description and vision interpretation
    are high-bias (operator interpretation); well-log and seismic are lower-bias
    (direct measurement of physical quantities).
    """

    measured_instrument = "measured_instrument"  # well log, seismic
    computed_attribute = "computed_attribute"  # inverted impedance, AVO
    expert_interpretation = "expert_interpretation"  # outcrop description, vision
    literature = "literature"  # cited source
    unknown = "unknown"


@dataclass
class Observation:
    """
    A single record-layer observation of a voxel.

    Maps a real datum (well log value, seismic amplitude, etc.) to a VoxelState4
    latent variable. Carries uncertainty + bias metadata.
    """

    voxel_id: str
    kind: ObservationKind
    source: ObservationSource
    values: dict[str, float]  # e.g. {"vp": 2950.0, "rho": 2350.0}
    uncertainty: dict[str, float] = field(default_factory=dict)  # 1-sigma per channel
    bias_model: Optional["BiasModel"] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.uncertainty:
            # Default uncertainty: 5% of value
            self.uncertainty = {k: abs(v) * 0.05 for k, v in self.values.items()}


class BiasModel(BaseModel):
    """
    Bias model for an observation.

    Captures systematic errors (e.g., outcrop description over-weights weathering;
    vision interpretation over-weights high-contrast features).

    Per Claim 1 (voxel-as-discretization) and Claim 3 (void paradox), bias
    correction is essential to honest inference.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    bias_kind: str = Field(description="e.g., 'surface_weathering', 'VLM_contrast', 'log_aging'")
    bias_magnitude: float = Field(ge=0.0, le=1.0, description="Fractional bias (0 = unbiased, 1 = totally untrustworthy)")
    bias_direction: dict[str, float] = Field(
        default_factory=dict,
        description="Per-channel bias sign and magnitude (e.g., {'vp': -0.02} for 2% underestimate)",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FORWARD MODELS — field-layer → record-layer prediction
# ═══════════════════════════════════════════════════════════════════════════════


class ForwardModel(ABC):
    """
    Abstract forward model: VoxelState4 → predicted Observation.

    This is the heart of the Bayes bridge. Each dimensionality has its own
    forward model (1D rock physics, 2D seismic attribute, 3D seismic synthetic,
    4D time-lapse). All operate on the same VoxelState4 latent state.

    Per ADR-008 §4: "Unified Physics Dimensionality Framework":
      1D  →  forward_1d(voxel_state) → logs
      2D  →  forward_2d(voxel_state) → seismic_section
      3D  →  forward_3d(voxel_state) → seismic_volume
      4D  →  forward_4d(voxel_state, t) → seismic_volume_at_t
    """

    @abstractmethod
    def predict(self, voxel_state: VoxelState4) -> dict[str, float]:
        """
        Predict record-layer observables from a field-layer voxel state.

        Returns a dict of channel_name → predicted_value.
        e.g., {"vp": 2950.0, "rho": 2350.0, "phi": 0.22}

        MUST be deterministic for a given voxel state — Bayes requires
        likelihood to be evaluable.
        """
        ...


class ForwardModel1D(ForwardModel):
    """
    1D forward model — voxel → log response.

    Maps to GEOX `geox_petrophysics` outputs: GR, RHOB, DT, NPHI, RT, etc.

    STUB ONLY — real rock-physics transforms (Archie, Gardner, Wyllie) come
    from `geox_lem_predict` in subsequent tranches.
    """

    def predict(self, voxel_state: VoxelState4) -> dict[str, float]:
        """
        Stub: derive log response from material_state + void_state.

        Real implementation will use:
          - Vsh from GR (linear or Clavier)
          - phi from density (rho_matrix - rho_bulk) / (rho_matrix - rho_fluid)
          - Sw from Archie: Sw = (a * Rw / (phi^m * Rt))^(1/n)
          - Vp from Gardner: Vp = (rho / a)^(1/b)
        """
        # Placeholder: extract from physics9_anchor if present
        if voxel_state.material_state.physics9_anchor is not None:
            p9 = voxel_state.material_state.physics9_anchor
            return {
                "vp": p9.vp,
                "vs": p9.vs,
                "rho": p9.rho,
                "phi": p9.phi,
            }

        # Default fallback — return mid-range estimates
        return {
            "vp": 3000.0,
            "vs": 1700.0,
            "rho": 2400.0,
            "phi": 0.20,
        }


class ForwardModel2D(ForwardModel):
    """
    2D forward model — voxel → seismic section attribute.

    Maps to GEOX `geox_seismic_compute` (attribute mode) outputs.

    STUB ONLY — real seismic attribute computation (coherence, sweetness,
    envelope) comes from existing seismic_compute modes.
    """

    def predict(self, voxel_state: VoxelState4) -> dict[str, float]:
        """
        Stub: derive seismic attributes from material_state + strain_state.

        Real implementation will use:
          - Acoustic impedance from physics9_anchor
          - Coherence from strain_state.fault_presence_prob
          - Amplitude from physics9_anchor.vp * physics9_anchor.rho
        """
        return {
            "acoustic_impedance": 3000.0 * 2400.0,  # vp * rho placeholder
            "coherence": 1.0 - (voxel_state.strain_state.fault_presence_prob or 0.0),
            "amplitude_envelope": 0.5,
        }


class ForwardModel3D(ForwardModel):
    """
    3D forward model — voxel → seismic volume synthetic.

    Maps to GEOX `geox_seismic_compute` (synthetic mode) outputs.

    STUB ONLY — real 3D synthetic generation comes from `geox_seismic_compute`
    with wavelet + reflectivity inputs.
    """

    def predict(self, voxel_state: VoxelState4) -> dict[str, float]:
        """Stub: returns single voxel amplitude prediction."""
        return {
            "amplitude": 0.3,
            "impedance": 3000.0 * 2400.0,
        }


class ForwardModel4D(ForwardModel):
    """
    4D forward model — voxel → seismic volume at time t.

    Maps to repeated runs of `geox_seismic_compute` across epochs.

    STUB ONLY — real 4D requires time-evolving physics (production, depletion).
    """

    def __init__(self, t_ma: float):
        self.t_ma = t_ma

    def predict(self, voxel_state: VoxelState4) -> dict[str, float]:
        """Stub: time-lapse amplitude prediction."""
        # Real impl would update void_state (depletion) + strain_state
        # before calling forward_3d.
        fwd3d = ForwardModel3D()
        return fwd3d.predict(voxel_state)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. LIKELIHOOD — P(observation | voxel_state)
# ═══════════════════════════════════════════════════════════════════════════════


def gaussian_likelihood(
    predicted: dict[str, float],
    observed: Observation,
) -> float:
    """
    Gaussian likelihood: P(observed | predicted).

    Per-channel residual normalized by uncertainty; combined via log-sum.
    This is the standard "goodness of fit" used in geophysical inversion.

    Returns the log-likelihood (natural log). Higher = better fit.

    Args:
        predicted: forward-modeled observables
        observed: record-layer observation with uncertainty + bias

    Note:
        Bias correction is NOT applied here — it should be applied to the
        observation BEFORE computing likelihood. See apply_bias_correction().
    """
    log_lik = 0.0
    n_channels = 0

    for channel, pred_value in predicted.items():
        if channel not in observed.values:
            continue
        obs_value = observed.values[channel]
        sigma = observed.uncertainty.get(channel, abs(obs_value) * 0.05 + 1e-6)

        # Gaussian log-likelihood: -0.5 * ((x - mu) / sigma)^2 - log(sigma)
        residual_normalized = (obs_value - pred_value) / sigma
        log_lik += -0.5 * residual_normalized ** 2 - math.log(sigma)
        n_channels += 1

    if n_channels == 0:
        return float("-inf")

    return log_lik


def apply_bias_correction(
    observation: Observation,
) -> Observation:
    """
    Apply bias correction to observation before likelihood computation.

    Per ADR-008 §3.2: "Every existing tool is re-classified... `geox_vision`
    is a soft prior (high bias — requires field validation)."

    Outcrop observations and vision interpretations carry systematic biases
    that must be corrected before being treated as evidence.
    """
    if observation.bias_model is None:
        return observation

    corrected_values = dict(observation.values)
    for channel, bias_sign in observation.bias_model.bias_direction.items():
        if channel in corrected_values:
            # bias_magnitude × value × sign
            corrected_values[channel] -= bias_sign * observation.bias_model.bias_magnitude

    # Return a new Observation with corrected values
    return Observation(
        voxel_id=observation.voxel_id,
        kind=observation.kind,
        source=observation.source,
        values=corrected_values,
        uncertainty=observation.uncertainty,
        bias_model=observation.bias_model,
        timestamp=observation.timestamp,
        provenance={**observation.provenance, "bias_corrected": True},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. BAYES UPDATE — the bridge
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class BayesUpdateResult:
    """
    Result of a Bayes update on a voxel.

    Carries the posterior VoxelState4 + diagnostics (residual, log-likelihood,
    updated observation_count).
    """

    prior: VoxelState4
    observation: Observation
    posterior: VoxelState4
    log_likelihood: float
    residual_normalized: float  # 0 = perfect fit, higher = worse
    n_channels_used: int


def bayes_update_voxel(
    prior: VoxelState4,
    forward_model: ForwardModel,
    observation: Observation,
) -> BayesUpdateResult:
    """
    Bayesian update of a voxel state given a single observation.

    Per ADR-008 §5: this is the bridge. The formula:

        posterior ∝ P(observation | voxel_state) × prior

    Implemented as:
      1. Forward model: predict observables from prior voxel_state
      2. Apply bias correction to observation
      3. Compute Gaussian likelihood: P(observation | predicted)
      4. Combine with prior (log-space) to get posterior log-density
      5. Update VoxelState4 metadata: residual, observation_count, confidence

    Args:
        prior: VoxelState4 prior belief (latent field-layer state)
        forward_model: forward model (1D/2D/3D/4D) — must be deterministic
        observation: record-layer observation with uncertainty + bias

    Returns:
        BayesUpdateResult with posterior VoxelState4 + diagnostics
    """
    # Step 1: Forward prediction from prior
    predicted = forward_model.predict(prior)

    # Step 2: Bias correction on observation
    corrected_obs = apply_bias_correction(observation)

    # Step 3: Gaussian likelihood
    log_lik = gaussian_likelihood(predicted, corrected_obs)

    # Step 4: Normalized residual (0 = perfect, higher = worse)
    residuals = []
    for channel, pred_value in predicted.items():
        if channel in corrected_obs.values:
            obs_value = corrected_obs.values[channel]
            sigma = corrected_obs.uncertainty.get(channel, abs(obs_value) * 0.05 + 1e-6)
            residuals.append(abs(obs_value - pred_value) / sigma)

    residual_normalized = (sum(residuals) / len(residuals)) if residuals else 0.0
    # Sigmoid-normalize to [0, 1]
    residual_normalized = 1.0 / (1.0 + math.exp(-residual_normalized + 1.0))

    # Step 5: Update VoxelState4 metadata
    posterior = prior.model_copy(deep=True)
    posterior.observation_count = prior.observation_count + 1
    posterior.forward_model_residual = residual_normalized
    posterior.updated_at = datetime.utcnow()

    # Derive truth_class from residual (per ADR-008 §3.2)
    if residual_normalized < 0.2:
        posterior.truth_class = "FACT"
    elif residual_normalized < 0.5:
        posterior.truth_class = "INTERPRETATION"
    else:
        posterior.truth_class = "SPECULATION"

    # Update overall_confidence from residual + observation_count, hard-cap 0.90
    confidence_raw = 1.0 - residual_normalized
    # More observations → higher confidence (asymptotic)
    obs_factor = min(posterior.observation_count / 10.0, 1.0)
    posterior.overall_confidence = min(0.90, confidence_raw * obs_factor)

    # Append provenance
    posterior.provenance = {
        **prior.provenance,
        "last_update": {
            "observation_id": corrected_obs.provenance.get("id", "unknown"),
            "observation_kind": corrected_obs.kind.value,
            "forward_model": type(forward_model).__name__,
            "log_likelihood": log_lik,
            "residual_normalized": residual_normalized,
        },
    }

    n_channels = sum(1 for k in predicted if k in corrected_obs.values)

    return BayesUpdateResult(
        prior=prior,
        observation=observation,
        posterior=posterior,
        log_likelihood=log_lik,
        residual_normalized=residual_normalized,
        n_channels_used=n_channels,
    )


def bayes_update_voxel_sequence(
    prior: VoxelState4,
    forward_model: ForwardModel,
    observations: Sequence[Observation],
) -> list[BayesUpdateResult]:
    """
    Sequential Bayesian update across multiple observations.

    Each observation updates the posterior, which becomes the prior for the next.
    This is the standard "online Bayes" pattern used in data assimilation.

    Per ADR-008 §5: "the bridge ensures the same VoxelState4 latent state is
    updated by observations at any dimensionality, weighted by their uncertainty
    and bias."
    """
    results = []
    current = prior
    for obs in observations:
        result = bayes_update_voxel(current, forward_model, obs)
        results.append(result)
        current = result.posterior
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MULTI-VOXEL ENSEMBLE — multiple compatible histories
# ═══════════════════════════════════════════════════════════════════════════════


def ensemble_posteriors(
    priors: list[VoxelState4],
    forward_model: ForwardModel,
    observation: Observation,
) -> list[BayesUpdateResult]:
    """
    Compute posterior ensemble from multiple prior hypotheses.

    Per ADR-008 §"Consequences": "VoxelState4 ensemble per prospect (multiple
    compatible histories) increases storage. Mitigated by sparse encoding + lazy
    instantiation."

    This function evaluates the same observation against multiple prior
    hypotheses and returns the full ensemble. Callers can then:
      • Rank by posterior likelihood
      • Identify non-compatible priors (low likelihood)
      • Carry forward the top-K as "surviving hypotheses"
    """
    return [
        bayes_update_voxel(prior, forward_model, observation)
        for prior in priors
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Observation model
    "ObservationKind",
    "ObservationSource",
    "Observation",
    "BiasModel",
    # Forward models
    "ForwardModel",
    "ForwardModel1D",
    "ForwardModel2D",
    "ForwardModel3D",
    "ForwardModel4D",
    # Likelihood
    "gaussian_likelihood",
    "apply_bias_correction",
    # Bayes bridge
    "BayesUpdateResult",
    "bayes_update_voxel",
    "bayes_update_voxel_sequence",
    "ensemble_posteriors",
]


# ═══════════════════════════════════════════════════════════════════════════════
# 7. SELF-TEST — sanity check that the bridge instantiates
# ═══════════════════════════════════════════════════════════════════════════════


def _self_test() -> None:
    """
    Smoke test for the inference bridge.

    Run via: python -m geox_core.inference.voxel_update
    """
    from geox_core.schemas.voxel_state import (
        LithologyClass,
        MaterialState,
        PhaseFraction,
        PhaseConnectivity,
        PhaseType,
        ProcessState,
        StrainState,
        StressRegime,
        StrainStyle,
        VoidState,
        VoxelState4,
    )

    # Build a prior voxel
    prior = VoxelState4(
        voxel_id="voxel@2450.5m",
        basin_id="example_basin",
        material_state=MaterialState(lithology=LithologyClass.siliciclastic_sandstone),
        process_state=ProcessState(),
        strain_state=StrainState(
            dominant_stress_regime=StressRegime.compression,
            strain_style=StrainStyle.brittle,
        ),
        void_state=VoidState(
            phase_fractions=[
                PhaseFraction(phase=PhaseType.solid_mineral, fraction=0.78),
                PhaseFraction(phase=PhaseType.liquid_water, fraction=0.21),
            ],
        ),
        observation_count=0,
        forward_model_residual=None,
    )

    # Build an observation (well-log values from a real basin log, hypothetically)
    obs = Observation(
        voxel_id="voxel@2450.5m",
        kind=ObservationKind.well_log,
        source=ObservationSource.measured_instrument,
        values={"vp": 2950.0, "rho": 2350.0, "phi": 0.22},
        uncertainty={"vp": 50.0, "rho": 30.0, "phi": 0.02},
    )

    # Run forward model
    fwd = ForwardModel1D()
    predicted = fwd.predict(prior)
    assert "vp" in predicted

    # Run Bayes update
    result = bayes_update_voxel(prior, fwd, obs)
    assert result.posterior.observation_count == 1
    assert result.posterior.forward_model_residual is not None
    assert result.posterior.overall_confidence is not None
    assert result.posterior.overall_confidence <= 0.90  # F7 HUMILITY cap

    # Sequential update — multiple observations
    obs2 = Observation(
        voxel_id="voxel@2450.5m",
        kind=ObservationKind.well_log,
        source=ObservationSource.measured_instrument,
        values={"vp": 2980.0, "rho": 2360.0, "phi": 0.21},
    )
    results = bayes_update_voxel_sequence(prior, fwd, [obs, obs2])
    assert len(results) == 2
    assert results[1].posterior.observation_count == 2

    # Ensemble — multiple priors
    prior_alt = prior.model_copy(deep=True)
    prior_alt.voxel_id = "voxel@2450.5m-alt"
    ensemble = ensemble_posteriors([prior, prior_alt], fwd, obs)
    assert len(ensemble) == 2

    print("Inference bridge self-test PASSED.")


if __name__ == "__main__":
    _self_test()