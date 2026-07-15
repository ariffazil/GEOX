"""
biostrat/schemas.py — Pydantic v2 models for biostratigraphic intelligence.

DITEMPA BUKAN DIBERI — Forged, Not Given.

These schemas govern all biostrat data flowing through GEOX:
- Biozone: zone definitions (NN21, NP25, N17, etc.)
- BioEvent: FO/LD observations from wells
- TaxonRecord: resolved taxonomy from PBDB/Mikrotax
- BiostratRecord: normalised internal well biostrat data
- AgeModelPoint: marker for age-depth interpolation
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# ── Zone Schemes ──────────────────────────────────────────────────────────────

ZONE_SCHEMES = Literal[
    "Martini_1971_NN",      # Neogene nannofossil (NN1–NN21)
    "Martini_1971_NP",      # Paleogene nannofossil (NP1–NP25)
    "Sissingh_1977_CC",     # Cretaceous nannofossil (CC1–CC26)
    "Bukry_1973_CN",        # Neogene low-lat coccolith (CN1–CN15)
    "Okada_Bukry_1980_CP",  # Paleogene low-lat coccolith (CP1–CP19)
    "Agnini_2014_CNP",      # Paleocene nannofossil
    "Agnini_2014_CNE",      # Eocene nannofossil
    "Agnini_2014_CNO",      # Oligocene nannofossil
    "Blow_1969_N",          # Neogene planktonic foram (N1–N23)
    "Blow_1969_P",          # Paleogene planktonic foram (P1–P22)
    "Wade_2011",            # Updated Cenozoic planktonic foram
    "Lunt_2016_LBF",        # Larger benthic foram (SE Asia)
    "Morley_1991_PALYNO",   # SE Asia palynology
    "SSB_1995",             # Malaysian palynology (old)
    "SSB_2013",             # Malaysian palynology (new)
    "ICS_GLOBAL",           # ICS chronostratigraphic stages
    "CUSTOM",               # User-defined
]

FOSSIL_GROUPS = Literal[
    "calcareous_nannofossil",
    "planktonic_foram",
    "benthic_foram",
    "larger_benthic_foram",
    "palynology",
    "dinoflagellate",
    "radiolaria",
    "diatom",
    "conodont",
    "ostracod",
]


# ── Biozone Definition ───────────────────────────────────────────────────────

class Biozone(BaseModel):
    """A biostratigraphic zone definition from published literature.

    Represents a single zone (e.g., NN21, NP25, N17) with its age range,
    defining events, and bibliographic reference.
    """
    zone_id: str = Field(..., description="Zone code, e.g. 'NN21', 'NP25', 'N17'")
    scheme: ZONE_SCHEMES = Field(..., description="Zonation scheme name")
    fossil_group: FOSSIL_GROUPS = Field(..., description="Fossil group")
    age_top_ma: float = Field(..., description="Top (youngest) age in Ma")
    age_base_ma: float = Field(..., description="Base (oldest) age in Ma")
    epoch: str = Field(default="", description="ICS epoch/stage name")
    marker_taxon_top: str | None = Field(default=None, description="LO-defining taxon")
    marker_taxon_base: str | None = Field(default=None, description="FO-defining taxon")
    reference: str = Field(default="", description="Bibliographic reference")
    pbdb_int_id: str | None = Field(default=None, description="PBDB interval OID")
    macrostrat_int_id: int | None = Field(default=None, description="Macrostrat interval ID")
    notes: str = Field(default="")

    @field_validator("age_base_ma")
    @classmethod
    def base_older_than_top(cls, v: float, info: Any) -> float:
        top = info.data.get("age_top_ma", 0)
        if v < top:
            raise ValueError(f"age_base_ma ({v}) must be >= age_top_ma ({top})")
        return v


# ── Biostratigraphic Event ───────────────────────────────────────────────────

class BioEvent(BaseModel):
    """A single biostratigraphic observation from a well sample.

    Represents a First Occurrence (FO) or Last Occurrence (LO) of a taxon
    at a specific depth in a well.
    """
    well_id: str = Field(..., description="Well identifier")
    taxon: str = Field(..., description="Taxon name, e.g. 'Emiliania huxleyi'")
    event_type: Literal["FO", "LO", "FAD", "LAD", "present", "absent"] = Field(
        ..., description="Type of biostratigraphic event"
    )
    depth_m: float = Field(..., description="Measured depth in metres")
    depth_datum: Literal["KB", "MSL", "DF", "RT"] = Field(
        default="KB", description="Depth reference datum"
    )
    zone: str | None = Field(default=None, description="Assigned zone, e.g. 'NN21'")
    zone_scheme: ZONE_SCHEMES | None = Field(default=None, description="Zone scheme")
    fossil_group: FOSSIL_GROUPS | None = Field(default=None)
    age_ma: float | None = Field(default=None, description="Calculated age in Ma")
    age_uncertainty_ma: float | None = Field(
        default=None, description="Age uncertainty (±Ma)"
    )
    confidence: Literal["definite", "probable", "questionable"] = Field(
        default="probable", description="Pick confidence"
    )
    reworked: bool = Field(default=False, description="Reworking flag")
    caving: bool = Field(default=False, description="Caving contamination flag")
    preservation: Literal["good", "moderate", "poor", "barren"] = Field(
        default="moderate"
    )
    abundance: Literal["rare", "few", "common", "abundant", "dominant"] = Field(
        default="common"
    )
    analyst: str | None = Field(default=None)
    analysis_date: str | None = Field(default=None)
    vendor: str | None = Field(default=None, description="Lab/vendor name")
    source_report: str | None = Field(default=None, description="Source report/file")
    pbdb_occ_id: str | None = Field(default=None)
    notes: str = Field(default="")
    provenance: str = Field(default="GEOX Biostrat Engine")


# ── Taxon Record (from PBDB/Mikrotax) ────────────────────────────────────────

class TaxonRecord(BaseModel):
    """Resolved taxonomic record from external database.

    Synthesised from PBDB taxonomy API and/or Mikrotax.
    """
    name: str = Field(..., description="Taxon name")
    accepted_name: str = Field(..., description="Accepted/valid name (after synonym resolution)")
    rank: Literal["class", "order", "family", "genus", "species", "subspecies"] = Field(
        default="species"
    )
    parent: str | None = Field(default=None, description="Parent taxon name")
    fossil_group: FOSSIL_GROUPS | None = Field(default=None)
    pbdb_oid: str | None = Field(default=None, description="PBDB taxon OID, e.g. 'txn:421517'")
    first_occurrence_ma: float | None = Field(
        default=None, description="FAD age (oldest occurrence)"
    )
    last_occurrence_ma: float | None = Field(
        default=None, description="LAD age (youngest occurrence)"
    )
    n_occurrences: int | None = Field(default=None, description="PBDB occurrence count")
    extant: bool | None = Field(default=None)
    synonyms: list[str] = Field(default_factory=list)
    mikrotax_url: str | None = Field(default=None)
    pbdb_url: str | None = Field(default=None)
    reference: str = Field(default="")
    provenance: str = Field(default="PBDB/Mikrotax")


# ── Internal Well Biostrat Record ────────────────────────────────────────────

class BiostratRecord(BaseModel):
    """Normalised internal biostrat data for a single well.

    This is the canonical format for ingested enterprise biostrat data
    (from NOC reports, vendor deliverables, etc.).
    """
    well_id: str = Field(..., description="Canonical well identifier")
    field_name: str | None = Field(default=None)
    basin: str | None = Field(default=None, description="Basin name")
    operator: str | None = Field(default=None)
    fossil_group: FOSSIL_GROUPS = Field(...)
    zone: str = Field(..., description="Zone code")
    zone_scheme: ZONE_SCHEMES = Field(...)
    depth_top_m: float | None = Field(default=None, description="Top depth (mMD)")
    depth_base_m: float | None = Field(default=None, description="Base depth (mMD)")
    age_ma: float | None = Field(default=None, description="Derived age (Ma)")
    age_top_ma: float | None = Field(default=None)
    age_base_ma: float | None = Field(default=None)
    confidence: Literal["definite", "probable", "questionable"] = Field(
        default="probable"
    )
    reworked: bool = Field(default=False)
    preservation: Literal["good", "moderate", "poor", "barren"] = Field(
        default="moderate"
    )
    events: list[BioEvent] = Field(default_factory=list, description="Individual FO/LO events")
    eod: str | None = Field(default=None, description="Depositional environment")
    source_report: str | None = Field(default=None)
    source_file: str | None = Field(default=None)
    import_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: str = Field(default="")
    provenance: str = Field(default="GEOX Internal Biostrat DB")


# ── Age Model Point ──────────────────────────────────────────────────────────

class AgeModelPoint(BaseModel):
    """A marker point for age-depth modelling.

    Can come from biostrat zones, seismic ties, DST ages, or other sources.
    """
    depth_m: float = Field(..., description="Measured depth (mMD)")
    age_ma: float = Field(..., description="Age in Ma")
    source_type: Literal[
        "biostrat_zone", "biostrat_event", "seismic_tie",
        "dst_age", "radiometric", "magnetostrat", "other"
    ] = Field(default="biostrat_zone")
    confidence: Literal["definite", "probable", "questionable"] = Field(
        default="probable"
    )
    zone: str | None = Field(default=None)
    taxon: str | None = Field(default=None)
    reference: str = Field(default="")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Interpolation weight")


# ── Biostrat QC Result ───────────────────────────────────────────────────────

class BiostratQC(BaseModel):
    """Quality control result for a biostrat pick or well."""
    well_id: str
    zone: str
    depth_m: float
    qc_flags: list[str] = Field(default_factory=list)
    reworking_risk: Literal["low", "medium", "high"] = Field(default="low")
    caving_risk: Literal["low", "medium", "high"] = Field(default="low")
    range_violation: bool = Field(default=False, description="Zone out of expected depth range")
    age_inversion: bool = Field(default=False, description="Younger zone below older zone")
    missing_marker: bool = Field(default=False, description="Expected marker taxon absent")
    confidence_adjusted: Literal["definite", "probable", "questionable"] = Field(
        default="probable"
    )
    notes: str = Field(default="")


# ── Correlation Result ───────────────────────────────────────────────────────

class WellPick(BaseModel):
    """A zone pick in a well for correlation."""
    well_id: str
    zone: str
    scheme: ZONE_SCHEMES
    depth_m: float
    age_ma: float
    fossil_group: FOSSIL_GROUPS
    confidence: Literal["definite", "probable", "questionable"] = "probable"


class CorrelationResult(BaseModel):
    """Result of cross-well biostrat correlation."""
    wells: list[str] = Field(..., description="Well IDs included")
    scheme: ZONE_SCHEMES
    composite_zones: list[dict[str, Any]] = Field(
        default_factory=list, description="Composite standard zone picks"
    )
    diachroneity_flags: list[dict[str, Any]] = Field(
        default_factory=list, description="Zones with diachronous behaviour"
    )
    correlation_matrix: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Well-pair correlation confidence"
    )
    notes: str = Field(default="")


# ── MCP Tool Envelope ────────────────────────────────────────────────────────

class BiostratEnvelope(BaseModel):
    """Standard MCP output envelope for biostrat tools."""
    status: Literal["ok", "partial", "error"]
    tool: str
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    epistemic_label: Literal["OBS", "DER", "INT", "SPEC"] = Field(default="DER")
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provenance: str = Field(default="GEOX Biostrat Engine")
