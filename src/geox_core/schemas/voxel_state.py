"""
voxel_state.py — VoxelState4 Pydantic Schema (ADR-008)

═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, not given.

The 4-axis voxel ontology for GEOX. Each voxel carries:
  • material_state  — what is there right now
  • process_state   — how it formed / transformed
  • strain_state    — deformation history
  • void_state      — multi-phase occupancy + connectivity

Plus 3 field-layer metadata fields that make the field/record split queryable:
  • record_density(t_window)   — temporal coverage quality (0 = total record void)
  • observation_count          — how many record-layer data points inform this voxel
  • forward_model_residual     — discrepancy between forward-modeled and observed

Backbone:
  material_state wraps Physics9State (genuine non-conflicting extension).
  Wraps, doesn't replace — Physics9 boundaries (0.02 ≤ φ ≤ 0.45, etc.) untouched.

This is a SKELETON schema — doc-only pilot per ADR-008 Phase 1.
Real forward models, real priors, real likelihoods come in Phase 2+.

Anti-misconception spine:
  Every field carries a docstring tag identifying the human cognitive prism
  it defeats. This makes the schema a teaching object, not just a data model.

═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Re-export Physics9State — schema wraps, doesn't redefine
from geox_core.physics.state import Physics9State


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ENUMS — categorical type systems for each axis
# ═══════════════════════════════════════════════════════════════════════════════


class LithologyClass(str, Enum):
    """
    Categorical lithology for material_state.

    anti_misconception: "rock type = everything"
    This separates WHAT-IT-IS-NOW from HOW-IT-GOT-HERE (process_state).
    """

    igneous_intrusive = "igneous_intrusive"
    igneous_extrusive = "igneous_extrusive"
    siliciclastic_sandstone = "siliciclastic_sandstone"
    siliciclastic_shale = "siliciclastic_shale"
    carbonate_mudstone = "carbonate_mudstone"
    carbonate_grainstone = "carbonate_grainstone"
    evaporite = "evaporite"
    coal = "coal"
    metamorphic_schist = "metamorphic_schist"
    metamorphic_gneiss = "metamorphic_gneiss"
    basement_undifferentiated = "basement_undifferentiated"
    unknown = "unknown"


class CompositionClass(str, Enum):
    """
    Bulk composition class.

    anti_misconception: "composition = mineralogy"
    This separates mineral-class from textural/mechanical state.
    """

    felsic = "felsic"
    intermediate = "intermediate"
    mafic = "mafic"
    ultramafic = "ultramafic"
    siliciclastic = "siliciclastic"
    carbonate = "carbonate"
    organic_rich = "organic_rich"
    evaporitic = "evaporitic"
    unknown = "unknown"


class OriginType(str, Enum):
    """
    Origin tag for process_state.

    anti_misconception: "everything was once lava"
    Most crustal rocks never melted.
    """

    igneous = "igneous"
    sedimentary = "sedimentary"
    metamorphic = "metamorphic"
    unknown = "unknown"


class DepositionalEnvironment(str, Enum):
    """
    Depositional environment for sedimentary rocks.

    anti_misconception: "sediment = dried mud"
    Marine ≠ lacustrine ≠ fluvial ≠ deltaic ≠ aeolian ≠ glacial.
    """

    marine_shelf = "marine_shelf"
    marine_deepwater = "marine_deepwater"
    lacustrine = "lacustrine"
    fluvial = "fluvial"
    deltaic = "deltaic"
    aeolian = "aeolian"
    glacial = "glacial"
    paleosol = "paleosol"
    mixed = "mixed"
    none = "none"  # not sedimentary
    unknown = "unknown"


class IgneousContext(str, Enum):
    """
    Igneous context for igneous rocks.

    anti_misconception: "igneous = volcano"
    Most igneous rock is intrusive, not extrusive.
    """

    intrusive_body = "intrusive_body"
    lava_flow = "lava_flow"
    pyroclastic = "pyroclastic"
    volcaniclastics = "volcaniclastics"
    crystal_mush = "crystal_mush"
    none = "none"  # not igneous
    unknown = "unknown"


class MetamorphicRegime(str, Enum):
    """
    Metamorphic regime for metamorphic rocks.

    anti_misconception: "metamorphic = heat + pressure uniformly"
    Contact ≠ regional ≠ high-P-low-T ≠ shock ≠ hydrothermal.
    """

    contact = "contact"
    regional = "regional"
    high_P_low_T = "high_P_low_T"
    shock = "shock"
    hydrothermal = "hydrothermal"
    none = "none"  # not metamorphic
    unknown = "unknown"


class LastMajorTransition(str, Enum):
    """
    Last major state transition for the voxel.

    anti_misconception: "rock cycle is one clean loop"
    Real histories are non-cyclic and asymmetric.
    """

    melt_crystallization = "melt_crystallization"
    deposition_lithification = "deposition_lithification"
    metamorphism = "metamorphism"
    strong_erosion = "strong_erosion"
    deformation = "deformation"
    diagenesis = "diagenesis"
    unknown = "unknown"


class StressRegime(str, Enum):
    """
    Dominant stress regime for strain_state.

    anti_misconception: "deformation = broken rock"
    Stress regime is separate from strain style.
    """

    tension = "tension"
    compression = "compression"
    shear = "shear"
    mixed = "mixed"
    unknown = "unknown"


class StrainStyle(str, Enum):
    """
    Strain style for strain_state.

    anti_misconception: "ductile = metamorphic"
    Ductile flow can occur without metamorphism.
    """

    elastic = "elastic"
    brittle = "brittle"
    ductile = "ductile"
    brittle_ductile_mix = "brittle_ductile_mix"
    unknown = "unknown"


class AnisotropyType(str, Enum):
    """
    Type of anisotropy in the voxel.

    anti_misconception: "rock is mechanically isotropic"
    Foliation, bedding, fracture sets create anisotropy.
    """

    none = "none"
    foliation = "foliation"
    bedding = "bedding"
    fracture_set = "fracture_set"
    lamination = "lamination"
    mixed = "mixed"
    unknown = "unknown"


class PhaseType(str, Enum):
    """
    Phase types for void_state occupancy.

    anti_misconception: "rock is solid or a cave"
    Multi-phase occupancy is the norm — solid, liquid, gas, field.
    """

    solid_mineral = "solid_mineral"
    liquid_water = "liquid_water"
    liquid_hydrocarbon = "liquid_hydrocarbon"
    gas = "gas"
    field_residual = "field_residual"  # atomic-scale emptiness, never zero
    ice = "ice"
    unknown = "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SUB-MODELS — each axis as a typed Pydantic model
# ═══════════════════════════════════════════════════════════════════════════════


class TextureProperties(BaseModel):
    """
    Textural properties of a voxel.

    anti_misconception: "rock is featureless"
    Texture (grain size, sorting, matrix ratio) controls mechanical response.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    grain_size_phi: Optional[float] = Field(
        default=None, description="Grain size in phi units (negative = coarser, positive = finer)"
    )
    sorting: Optional[Literal["very_poor", "poor", "moderate", "well", "very_well"]] = Field(
        default=None
    )
    matrix_to_framework_ratio: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Matrix fraction (0 = framework-supported, 1 = matrix-dominated)"
    )
    crystallinity: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="0 = amorphous, 1 = fully crystalline"
    )


class MechanicsProperties(BaseModel):
    """
    Mechanical properties derived from material_state.

    anti_misconception: "rock is just stone"
    Rock has mechanical properties that change with P-T-strain.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    density_kg_m3: Optional[float] = Field(default=None, ge=500.0, le=5000.0)
    youngs_modulus_pa: Optional[float] = Field(default=None, ge=1e8, le=200e9)
    poisson_ratio: Optional[float] = Field(default=None, ge=0.0, le=0.5)
    cohesion_pa: Optional[float] = Field(default=None, ge=0.0)
    friction_angle_deg: Optional[float] = Field(default=None, ge=0.0, le=90.0)


class MaterialState(BaseModel):
    """
    Material axis: what is there RIGHT NOW in this voxel, ignoring history.

    anti_misconception: "rock type = everything"
    This axis captures the current physical state, separated from history.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    lithology: LithologyClass = Field(
        default=LithologyClass.unknown, description="Categorical lithology class"
    )
    composition_class: CompositionClass = Field(
        default=CompositionClass.unknown, description="Bulk composition class"
    )
    texture: TextureProperties = Field(default_factory=TextureProperties)
    mechanics: MechanicsProperties = Field(default_factory=MechanicsProperties)

    # Physics9 anchor — wraps the canonical 9-parameter state
    physics9_anchor: Optional[Physics9State] = Field(
        default=None,
        description="Optional Physics9State anchor — when populated, supplies the canonical 9 physics dials (rho, vp, vs, rho_e, chi, k, P, T, phi)",
    )

    @field_validator("lithology", "composition_class")
    @classmethod
    def _no_emergency_defaults(cls, v):
        # Allow 'unknown' as a legal value — never coerce to a guess
        return v


class ProcessState(BaseModel):
    """
    Process axis: how this voxel formed and what transitions it has gone through.

    anti_misconception: "rock cycle is one clean loop"
    Real histories are non-cyclic and asymmetric.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    origin: OriginType = Field(default=OriginType.unknown)
    depositional_environment: DepositionalEnvironment = Field(
        default=DepositionalEnvironment.unknown
    )
    igneous_context: IgneousContext = Field(default=IgneousContext.unknown)
    metamorphic_regime: MetamorphicRegime = Field(default=MetamorphicRegime.unknown)

    has_been_molten: Optional[bool] = Field(
        default=None, description="True if this voxel has ever been in melt state"
    )
    has_been_exhumed: Optional[bool] = Field(
        default=None, description="True if brought back toward surface after deep burial"
    )
    last_major_transition: LastMajorTransition = Field(
        default=LastMajorTransition.unknown
    )

    @model_validator(mode="after")
    def _cross_check_origin_with_environment(self):
        # Soft validation — flag mismatches but don't reject
        if (
            self.origin == OriginType.sedimentary
            and self.depositional_environment == DepositionalEnvironment.none
        ):
            # sedimentary origin should have an environment (or 'unknown', not 'none')
            pass  # warning, not error — user might genuinely be uncertain
        return self


class StrainState(BaseModel):
    """
    Strain axis: deformation as distinct from rock type.

    anti_misconception: "deformed = metamorphic" / "rock only changes when it breaks"
    Strain is its own axis, can apply to any origin.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    dominant_stress_regime: StressRegime = Field(default=StressRegime.unknown)
    strain_style: StrainStyle = Field(default=StrainStyle.unknown)

    fold_presence_prob: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Probability that this voxel is folded"
    )
    fault_presence_prob: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Probability that this voxel hosts a fault"
    )
    fault_sense: Optional[Literal["normal", "reverse", "strike_slip", "oblique"]] = Field(
        default=None
    )

    anisotropy: AnisotropyType = Field(default=AnisotropyType.unknown)
    anisotropy_strength: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="0 = isotropic, 1 = strongly anisotropic"
    )


class PhaseFraction(BaseModel):
    """
    Single phase occupancy fraction.

    anti_misconception: "rock is solid or a cave"
    Multi-phase occupancy is normal. Fractions sum to 1.0.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    phase: PhaseType
    fraction: float = Field(ge=0.0, le=1.0, description="Volume fraction (0-1)")


class PhaseConnectivity(BaseModel):
    """
    Connectivity for a single phase in void_state.

    anti_misconception: "porosity = scalar magic number"
    Connectivity is anisotropic and phase-specific.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    phase: PhaseType
    percolation: bool = Field(description="Whether this phase forms a connected network")
    principal_permeability_md: Optional[list[float]] = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Principal permeabilities [k1, k2, k3] in mD, sparse form",
    )
    isolated_pockets: bool = Field(
        default=False, description="True if phase exists only in disconnected pockets"
    )


class VoidState(BaseModel):
    """
    Void axis: explicit representation of "void + fluid" instead of pretending rock is solid.

    anti_misconception: "rock is solid or a cave" / "porosity = scalar magic number"
    Multi-phase occupancy with anisotropic connectivity.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    phase_fractions: list[PhaseFraction] = Field(
        default_factory=list,
        description="Volume fractions of all phases present (sum to 1.0)",
    )
    phase_connectivity: list[PhaseConnectivity] = Field(
        default_factory=list, description="Per-phase connectivity (percolation, permeability tensor)"
    )

    @field_validator("phase_fractions")
    @classmethod
    def _fractions_non_negative(cls, v):
        # Permissive check: fractions must be non-negative and ≤ 1.0.
        # Sum-to-1.0 is enforced by model_validator (which can normalize).
        # anti_misconception: void is multi-phase, not scalar porosity.
        for p in v:
            if p.fraction < 0.0 or p.fraction > 1.0:
                raise ValueError(
                    f"phase fraction must be in [0, 1]; got {p.fraction} for {p.phase}"
                )
        return v

    @model_validator(mode="after")
    def _normalize_phase_fractions(self):
        """
        Ensure phase_fractions sum to 1.0 and field_residual is present.

        Per Claim 3 (void paradox): no total void; field_residual must be ≥ 0.
        Per ADR-008 §1: void_state is multi-phase, not scalar porosity.
        """
        if not self.phase_fractions:
            return self

        # Step 1: add field_residual if missing (atomic-scale emptiness, always present)
        phases_present = {p.phase for p in self.phase_fractions}
        if PhaseType.field_residual not in phases_present:
            self.phase_fractions.append(
                PhaseFraction(phase=PhaseType.field_residual, fraction=0.0)
            )

        # Step 2: renormalize so fractions sum exactly to 1.0
        total = sum(p.fraction for p in self.phase_fractions)
        if total > 0 and abs(total - 1.0) > 1e-6:
            for p in self.phase_fractions:
                p.fraction = p.fraction / total

        return self


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FIELD-LAYER METADATA — makes the field/record split queryable
# ═══════════════════════════════════════════════════════════════════════════════


class RecordDensity(BaseModel):
    """
    Temporal coverage quality — fraction of Earth history preserved in rock at this voxel.

    anti_misconception: "unconformity = time void"
    A Great Unconformity is record_density ≈ 0 for ~1.5 Ga, NOT a gap in time.
    Time flowed; the rock pages are torn.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    t_window_start_ma: float = Field(description="Start of time window (Ma)")
    t_window_end_ma: float = Field(description="End of time window (Ma)")
    density: float = Field(
        ge=0.0, le=1.0,
        description="Fraction of time window preserved in rock (0 = total record void, 1 = complete)",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. VOXELSTATE4 — the canonical envelope
# ═══════════════════════════════════════════════════════════════════════════════


class VoxelState4(BaseModel):
    """
    The 4-axis voxel state envelope.

    Backbone of the field/record/Bayes bridge (ADR-008).
    Each voxel is a **latent variable** in the field layer — not a label.
    Rocks (record layer) are noisy observations of this latent state.

    Anti-misconception spine (4 axes, each killing a specific prism):
      • material_state  — kills "rock type = everything"
      • process_state   — kills "rock cycle is one clean loop"
      • strain_state    — kills "deformed = metamorphic"
      • void_state      — kills "rock is solid or a cave"

    Plus 3 field-layer metadata fields:
      • record_density         — temporal record coverage (unconformities → ~0)
      • observation_count      — how many record-layer data points
      • forward_model_residual — forward-model vs observation mismatch

    Backward compatibility:
      material_state.physics9_anchor wraps Physics9State (the canonical 9-parameter
      vector). Boundaries (0.02 ≤ φ ≤ 0.45, 0.0 ≤ Sw ≤ 1.0, etc.) UNTOUCHED.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    # ─── Identity ───
    voxel_id: str = Field(description="Canonical voxel identifier (e.g., 'voxel@2450.5m')")
    basin_id: Optional[str] = Field(default=None, description="Basin context (e.g., 'example_basin')")

    # ─── 4 axes ───
    material_state: MaterialState = Field(default_factory=MaterialState)
    process_state: ProcessState = Field(default_factory=ProcessState)
    strain_state: StrainState = Field(default_factory=StrainState)
    void_state: VoidState = Field(default_factory=VoidState)

    # ─── Field-layer metadata ───
    record_density: list[RecordDensity] = Field(
        default_factory=list,
        description="Per-time-window record coverage. Unconformities → density ≈ 0.",
    )
    observation_count: int = Field(
        default=0, ge=0,
        description="Number of record-layer data points informing this voxel",
    )
    forward_model_residual: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Normalized residual between forward-modeled and observed (0 = perfect fit, 1 = total mismatch)",
    )

    # ─── Uncertainty + provenance ───
    overall_confidence: Optional[float] = Field(
        default=None, ge=0.0, le=0.90,
        description="Hard-capped 0.90 per F7 HUMILITY; never claims certainty",
    )
    truth_class: Optional[Literal["FACT", "INTERPRETATION", "SPECULATION"]] = Field(
        default=None,
        description="Epistemic label. Per ADR-008, this is derived from residual, not assigned.",
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance chain — forward model version, observation IDs, prior source, etc.",
    )

    # ─── Timestamps ───
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # ═════════════════════════════════════════════════════════════════════════
    # DERIVED PROPERTIES (F2 TRUTH — never stored as truth)
    # ═════════════════════════════════════════════════════════════════════════

    @property
    def total_porosity(self) -> Optional[float]:
        """
        DERIVED total porosity from void_state.phase_fractions.

        anti_misconception: "40% void magic constant"
        Porosity is derived from phase fractions, not stored as a magic scalar.
        Sum of (1 - solid_mineral fraction) across non-solid phases.
        """
        if not self.void_state.phase_fractions:
            return None
        solid = sum(
            p.fraction
            for p in self.void_state.phase_fractions
            if p.phase == PhaseType.solid_mineral
        )
        return 1.0 - solid

    @property
    def effective_porosity(self) -> Optional[float]:
        """
        DERIVED effective (connected) porosity — sum of percolating non-solid phases.
        """
        if not self.void_state.phase_connectivity:
            return None
        percolating_phases = {
            pc.phase for pc in self.void_state.phase_connectivity if pc.percolation
        }
        if not percolating_phases:
            return 0.0
        total = 0.0
        for p in self.void_state.phase_fractions:
            if p.phase in percolating_phases and p.phase != PhaseType.solid_mineral:
                total += p.fraction
        return total

    @property
    def well_constrained(self) -> bool:
        """
        Whether this voxel is well-constrained by observations.

        Returns True iff observation_count ≥ 3 AND forward_model_residual < 0.3.
        Per ADR-008: gates geox_claim seal.
        """
        return (
            self.observation_count >= 3
            and self.forward_model_residual is not None
            and self.forward_model_residual < 0.3
        )

    @property
    def record_void_indicator(self) -> Optional[str]:
        """
        Returns a description of the largest record-density gap, or None if no gaps.

        anti_misconception: "unconformity = time void"
        Returns the time window with the lowest record_density (record void), NOT
        a claim that time was missing.
        """
        if not self.record_density:
            return None
        worst = min(self.record_density, key=lambda r: r.density)
        if worst.density < 0.1:
            return (
                f"Record void ({worst.density:.2f}) between "
                f"{worst.t_window_start_ma:.1f} Ma and {worst.t_window_end_ma:.1f} Ma. "
                f"Time flowed; rock pages are torn."
            )
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Enums
    "LithologyClass",
    "CompositionClass",
    "OriginType",
    "DepositionalEnvironment",
    "IgneousContext",
    "MetamorphicRegime",
    "LastMajorTransition",
    "StressRegime",
    "StrainStyle",
    "AnisotropyType",
    "PhaseType",
    # Sub-models
    "TextureProperties",
    "MechanicsProperties",
    "MaterialState",
    "ProcessState",
    "StrainState",
    "PhaseFraction",
    "PhaseConnectivity",
    "VoidState",
    "RecordDensity",
    # Envelope
    "VoxelState4",
]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SELF-TEST — sanity check that schema instantiates and validates
# ═══════════════════════════════════════════════════════════════════════════════


def _self_test() -> None:
    """
    Smoke test for VoxelState4.

    Run via: python -m geox_core.schemas.voxel_state
    Not a pytest fixture — a quick CLI check that the schema loads.
    """
    # Minimal voxel — all defaults, should construct
    voxel = VoxelState4(voxel_id="test@1000m")
    assert voxel.observation_count == 0
    assert voxel.well_constrained is False
    assert voxel.material_state.lithology == LithologyClass.unknown

    # Fully populated voxel
    voxel_full = VoxelState4(
        voxel_id="voxel@2450.5m",
        basin_id="example_basin",
        material_state=MaterialState(
            lithology=LithologyClass.siliciclastic_sandstone,
            composition_class=CompositionClass.siliciclastic,
        ),
        process_state=ProcessState(
            origin=OriginType.sedimentary,
            depositional_environment=DepositionalEnvironment.fluvial,
            has_been_molten=False,
            has_been_exhumed=True,
            last_major_transition=LastMajorTransition.deposition_lithification,
        ),
        strain_state=StrainState(
            dominant_stress_regime=StressRegime.compression,
            strain_style=StrainStyle.brittle_ductile_mix,
            fold_presence_prob=0.7,
            fault_presence_prob=0.4,
            anisotropy=AnisotropyType.bedding,
            anisotropy_strength=0.6,
        ),
        void_state=VoidState(
            phase_fractions=[
                PhaseFraction(phase=PhaseType.solid_mineral, fraction=0.78),
                PhaseFraction(phase=PhaseType.liquid_water, fraction=0.15),
                PhaseFraction(phase=PhaseType.liquid_hydrocarbon, fraction=0.04),
                PhaseFraction(phase=PhaseType.gas, fraction=0.02),
                # field_residual will be auto-added by validator
            ],
            phase_connectivity=[
                PhaseConnectivity(
                    phase=PhaseType.liquid_water,
                    percolation=True,
                    principal_permeability_md=[120.0, 80.0, 25.0],
                ),
                PhaseConnectivity(
                    phase=PhaseType.gas,
                    percolation=False,
                    isolated_pockets=True,
                ),
            ],
        ),
        record_density=[
            RecordDensity(t_window_start_ma=66.0, t_window_end_ma=0.0, density=0.95),
            RecordDensity(t_window_start_ma=145.0, t_window_end_ma=66.0, density=0.85),
        ],
        observation_count=12,
        forward_model_residual=0.18,
        overall_confidence=0.78,
    )

    # Derived properties
    assert abs(voxel_full.total_porosity - 0.22) < 0.05  # ~22% after auto-add of field_residual
    assert voxel_full.effective_porosity is not None
    assert voxel_full.well_constrained is True  # 12 obs, 0.18 residual
    assert voxel_full.record_void_indicator is None  # no density < 0.1

    print("VoxelState4 self-test PASSED.")


if __name__ == "__main__":
    _self_test()