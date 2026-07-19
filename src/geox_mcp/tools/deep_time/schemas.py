"""deep_time/schemas.py — Pydantic models for the Earth State Vector.

F2 TRUTH: Each variable carries value, units, uncertainty, epistemic
status, source, and confidence. Empty values are explicit (null + NO_DATA
epistemic tag) — we never silently fabricate data.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ─── Epistemic categories (per GEOX claim grammar + arifOS doctrine) ─────────
#
# UNKNOWN is the F9 Anti-Hantu fabrication guard. It is distinct from NO_DATA:
#   NO_DATA   = the dataset has not been ingested yet; ingestion is possible.
#   UNKNOWN   = the parameter CANNOT be known at this age even in principle
#                (e.g. CO2 in the Hadean — no proxy exists; extrapolation
#                would be hallucination).
#
# A tool that emits UNKNOWN is honest. A tool that silently extrapolates to
# fill a gap violates F9.
#
# EpistemicLevel is a str-Enum so it serializes to JSON as the string value
# (not a quoted enum repr) and accepts string comparisons like
# `epistemic_level == "OBSERVED"` without coercion errors.
class EpistemicLevel(StrEnum):
    """Epistemic provenance of a deep_time variable — drives F7 confidence cap."""
    OBSERVED = "OBSERVED"             # directly measured (e.g. ice core δ18O)
    DERIVED = "DERIVED"               # formula-based from observed inputs
    INTERPRETED = "INTERPRETED"       # model output, calibrated
    PROCESS_HYPOTHESIS = "PROCESS_HYPOTHESIS"  # process-model prediction
    SPECULATION = "SPECULATION"       # analogy / statistics-based inference
    NO_DATA = "NO_DATA"               # dataset not yet ingested
    UNKNOWN = "UNKNOWN"               # cannot be known at this age (F9 guard)


EPISTEMIC_CONFIDENCE_CAP = {
    "OBSERVED": 0.90,
    "DERIVED": 0.90,
    "INTERPRETED": 0.85,
    "PROCESS_HYPOTHESIS": 0.75,
    "SPECULATION": 0.50,
    "NO_DATA": 0.10,
    "UNKNOWN": 0.05,  # explicitly low — we are telling the caller "we cannot know"
}


def cap_confidence(epistemic_level: str, raw_confidence: float) -> float:
    """Apply F7 HUMILITY cap based on epistemic level.

    Per GEOX F7, confidence is hard-capped per variable type:
      - OBSERVED:          cap = 0.90
      - DERIVED:           cap = 0.90 (formula-based, not fabricated)
      - INTERPRETED:       cap = 0.85
      - PROCESS_HYPOTHESIS: cap = 0.75
      - SPECULATION:       cap = 0.50
      - NO_DATA:           cap = 0.10
      - UNKNOWN:           cap = 0.05

    The F7 cap is the MAXIMUM confidence any variable may claim, regardless
    of what the raw confidence score is. If a data loader computes 0.99 for
    an OBSERVED measurement, this function reduces it to 0.90.

    This is distinct from the model-level F7 overall_confidence cap of 0.90
    for the whole envelope.
    """
    cap = EPISTEMIC_CONFIDENCE_CAP.get(epistemic_level, 0.10)
    return min(float(raw_confidence), cap)


# ─── Polarity states (5-state enum per F2 hardening) ─────────────────────────
# Replaces the previous binary normal/reversed. Critical for the Cretaceous
# Normal Superchron (CNS, ~83.6-120.6 Ma) and Kiaman Reversed Superchron
# (~262-318 Ma) where polarity is KNOWN but provides ZERO dating resolution.

class PolarityState(StrEnum):
    NORMAL = "normal"        # single normal chron
    REVERSED = "reversed"    # single reversed chron
    MIXED = "mixed"          # interval spans >=1 reversal
    SUPERCHRON = "superchron"  # CNS or Kiaman — polarity known, dating power NULL
    UNRESOLVED = "unresolved"  # pre-M29 (>157 Ma) — no calibrated GPTS


# ─── Reference-frame tagging for variables that need it ──────────────────────
# Sea level is the canonical case: "40 m above present" is meaningless
# without specifying the curve (Haq2014 vs Miller2005), the component
# (long-term eustasy vs short-term glacio-eustasy vs composite), and the
# datum (present-day MSL).

ReferenceFrame = Literal[
    "Haq2014_long_term",
    "Haq2014_composite",
    "Miller2005_backstrip",
    "Miller2005_composite",
    "Ray2019",
    "Kominz2008",
    "unknown_pending_ingestion",
]


# ─── Per-variable wrapper ─────────────────────────────────────────────────────

class EarthStateVariable(BaseModel):
    """A single Earth state variable with full epistemic envelope."""

    name: str
    value: float | int | str | None = None
    units: str | None = None
    uncertainty_p10: float | None = None
    uncertainty_p50: float | None = None
    uncertainty_p90: float | None = None
    uncertainty_method: str | None = None
    epistemic_level: EpistemicLevel = "NO_DATA"
    source_citation: str | None = None
    source_doi: str | None = None
    source_retrieval_date: str | None = None
    coverage_top_ma: float | None = None
    coverage_base_ma: float | None = None
    notes: str | None = None
    confidence: float = Field(default=0.10, ge=0.0, le=0.99)

    # ─── Reference-frame fields (for variables that need them) ───────────────
    # Used by sea_level, paleogeography, plate models. Optional for
    # variables where it's not meaningful (solar luminosity, day length).
    reference_curve: str | None = None      # e.g. "Haq2014", "Merdith2021"
    reference_component: str | None = None  # "long_term" | "short_term" | "composite"
    reference_datum: str | None = None      # "present_msl" | "modern_obliquity" etc.

    # ─── Interval-aggregation fields (for variables returned as distributions) ─
    # When the age_resolver returns a wide interval (>5 Myr), scalar variables
    # are expanded into distributions with these fields populated.
    interval_top_ma: float | None = None
    interval_base_ma: float | None = None
    n_proxy_points: int | None = None
    trend: str | None = None  # "rising" | "declining" | "stable" | "cyclic"
    value_min: float | None = None
    value_max: float | None = None
    warning: str | None = None


# ─── Aggregate Earth State Vector ─────────────────────────────────────────────

class EarthStateVector(BaseModel):
    """The full Earth State Vector for a resolved deep-time interval.

    Variables with NO_DATA carry explicit nulls and provenance pointing
    to the external dataset that needs to be ingested to fill them.
    Variables with UNKNOWN carry explicit nulls with a hard "cannot be
    known at this age" explanation (F9 fabrication guard).
    """

    # Time-resolved variables
    geomagnetic_polarity: EarthStateVariable | None = None
    atmospheric_co2_ppm: EarthStateVariable | None = None
    benthic_d18O_permil: EarthStateVariable | None = None       # OBSERVED measurement
    global_temperature_anomaly_c: EarthStateVariable | None = None  # INTERPRETED (depends on assumptions)
    eustatic_sea_level_m: EarthStateVariable | None = None
    atmospheric_o2_pal: EarthStateVariable | None = None

    # Spatial variables
    paleogeography_summary: EarthStateVariable | None = None
    supercontinent_state: EarthStateVariable | None = None
    ice_extent: EarthStateVariable | None = None

    # Astrophysical variables (always populated via formula)
    solar_luminosity_fraction: EarthStateVariable | None = None
    day_length_hours: EarthStateVariable | None = None
    orbital_eccentricity: EarthStateVariable | None = None
    orbital_obliquity_deg: EarthStateVariable | None = None

    # Biotic context
    biotic_realm: EarthStateVariable | None = None
    mass_extinction_events_in_window: list[EarthStateVariable] = Field(default_factory=list)

    # Provenance
    ics_chart_version: str = "v2024/12"
    ics_chart_hash: str | None = None
    n_variables_with_real_data: int = 0
    n_variables_pending_external_data: int = 0
    n_variables_unknown_at_age: int = 0
    overall_confidence: float = Field(default=0.10, ge=0.0, le=0.99)
    is_interval_query: bool = False
    interval_duration_myr: float | None = None
    notes: str | None = None


# ─── Governance footer (F11 AUDIT + F1/F13 SOVEREIGN) ────────────────────────

class GovernanceFooter(BaseModel):
    """Mandatory audit footer for every Earth State Vector.

    Carries verdict, lowest-confidence field, risk level, and a 999 seal
    pointer. The seal is computed by the caller from the envelope hash;
    here we carry the slot.

    For HIGH-risk downstream use (e.g. vector feeds a basin charge model),
    `human_review_required` flips to True and the tool caller should
    emit an 888_HOLD event before consuming the vector.
    """

    tool: str = "geox_deep_time_state"
    version: str = "v1.0"
    ics_version: str = "v2024/12"
    kernel: str = "arifOS"
    verdict: str = "PARTIAL"           # SEAL | PLAUSIBLE | PARTIAL | HOLD | VOID
    lowest_confidence_field: str | None = None
    lowest_confidence_value: float | None = None
    risk: str = "LOW"                 # LOW | MEDIUM | HIGH
    human_review_required: bool = False
    f9_fabrication_guard_active: bool = True
    seal: str | None = None           # populated by caller: VAULT999::DTC::<hash>::<ts>
    ics_chart_hash: str | None = None
    issued_at: str | None = None
    arifos_constitution_version: str = "v2026.05.05-SSCT"


# ─── Top-level envelope (the public return type) ──────────────────────────────

class EarthStateEnvelope(BaseModel):
    """Public MCP return envelope for geox_deep_time_state."""

    tool: str = "geox_deep_time_state"
    tool_class: str = "compute"
    execution_status: str = "SUCCESS"
    governance_status: str = "QUALIFY"
    artifact_status: str = "DRAFT"
    claim_tag: str = "PLAUSIBLE"
    claim_state: str = "INTERPRETED"
    uncertainty: str = "Moderate"
    humility_score: float = Field(default=0.5, ge=0.0, le=1.0)

    input_query: dict[str, Any] = Field(default_factory=dict)
    age_resolution: dict[str, Any] = Field(default_factory=dict)
    earth_state_vector: dict[str, Any] = Field(default_factory=dict)
    governance: dict[str, Any] = Field(default_factory=dict)  # GovernanceFooter serialised
    epistemic_summary: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    pending_external_datasets: list[dict[str, Any]] = Field(default_factory=list)
    unknown_at_age: list[dict[str, Any]] = Field(default_factory=list)
    audit_receipt: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None
