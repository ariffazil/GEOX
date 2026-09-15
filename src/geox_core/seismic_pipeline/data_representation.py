"""Data representation classification for seismic data provenance.

Distinguishes native trace data (suitable for quantitative analysis)
from display-derived proxy evidence (image-only, pixel-transformed).

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DataRepresentation(str, Enum):
    NATIVE_TRACE = "NATIVE_TRACE"
    DISPLAY_DERIVED_PROXY = "DISPLAY_DERIVED_PROXY"


class AmplitudeIntegrity(str, Enum):
    PRESERVED = "PRESERVED"
    CONDITIONAL = "CONDITIONAL"
    UNKNOWN = "UNKNOWN"
    DISPLAY_TRANSFORMED = "DISPLAY_TRANSFORMED"


class PhaseIntegrity(str, Enum):
    KNOWN = "KNOWN"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"
    DISPLAY_TRANSFORMED = "DISPLAY_TRANSFORMED"


@dataclass
class SeismicDataClassification:
    """Immutable classification of seismic data provenance."""
    data_representation: DataRepresentation
    amplitude_integrity: AmplitudeIntegrity = AmplitudeIntegrity.UNKNOWN
    phase_integrity: PhaseIntegrity = PhaseIntegrity.UNKNOWN
    source_hash: Optional[str] = None
    source_uri: Optional[str] = None

    @property
    def permitted_uses(self) -> list[str]:
        base = ["visual_interpretation", "event_tracking", "structural_pick_assist"]
        if self.data_representation == DataRepresentation.NATIVE_TRACE:
            return base + [
                "quantitative_amplitude_analysis",
                "avo_classification",
                "native_trace_well_tie",
                "seismic_inversion",
                "attribute_computation",
            ]
        return base

    @property
    def prohibited_uses(self) -> list[str]:
        if self.data_representation == DataRepresentation.DISPLAY_DERIVED_PROXY:
            return [
                "quantitative_amplitude_analysis",
                "avo_classification",
                "native_trace_well_tie_acceptance",
                "seismic_inversion",
            ]
        return []

    @property
    def quality_coverage_cap(self) -> float:
        """Maximum quality score this representation can contribute to coverage."""
        if self.data_representation == DataRepresentation.DISPLAY_DERIVED_PROXY:
            return 0.25
        return 1.0
