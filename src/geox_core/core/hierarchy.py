from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ObjectType(Enum):
    SEGMENT = "SEGMENT"
    PROSPECT = "PROSPECT"
    PORTFOLIO = "PORTFOLIO"

@dataclass
class GeologicalRisk:
    """Geological Chance of Success (GCOS) components."""
    source: float = 1.0
    reservoir: float = 1.0
    trap: float = 1.0
    seal: float = 1.0
    
    @property
    def gcos(self) -> float:
        return self.source * self.reservoir * self.trap * self.seal

@dataclass
class Segment:
    """
    WAJIB #2: The fundamental unit of subsurface truth.
    A Prospect consists of one or more Segments.
    """
    id: str
    name: str
    risk: GeologicalRisk = field(default_factory=GeologicalRisk)
    volumetrics: Dict[str, Any] = field(default_factory=dict)
    parent_prospect_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "gcos": round(self.risk.gcos, 4),
            "risk_components": {
                "source": self.risk.source,
                "reservoir": self.risk.reservoir,
                "trap": self.risk.trap,
                "seal": self.risk.seal
            },
            "volumetrics": self.volumetrics
        }

@dataclass
class Prospect:
    """
    A collection of Segments with explicit dependency logic.
    """
    id: str
    name: str
    segments: List[Segment] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    
    # SUNNAH: Structural Uncertainty (Segment Multiplier)
    # e.g., if we aren't sure if 1, 2, or 3 segments are actually sealing.
    segment_multiplier_dist: Optional[Dict[str, float]] = None # e.g., {"min": 1, "ml": 2, "max": 3}
    
    def add_segment(self, segment: Segment):
        segment.parent_prospect_id = self.id
        self.segments.append(segment)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "segment_count": len(self.segments),
            "segment_multiplier_dist": self.segment_multiplier_dist,
            "segments": [s.to_dict() for s in self.segments],
            "dependencies": self.dependencies
        }
