# GEOX Contracts — Tool Definitions
# DITEMPA BUKAN DIBERI
#
# This module defines the canonical interfaces for all GEOX tools.
# Both FastMCP and VPS runtimes MUST use these definitions.

from typing import Any, Dict, List, Optional, Protocol, TypedDict, Callable
from pydantic import BaseModel, Field

from contracts.enums import (
    Dimension,
    Verdict,
    ProspectVerdict,
    ClaimTag,
    DimensionCode,
)


class ToolInput(BaseModel):
    """Base class for all tool inputs."""
    session_id: Optional[str] = Field(None, description="Session identifier for continuity")
    declared_intent: str = Field(..., description="Human-declared intent for this operation")
    
    class Config:
        extra = "allow"


class ToolOutput(BaseModel):
    """Base class for all tool outputs."""
    verdict: Verdict = Field(..., description="Constitutional verdict")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., description="Human-readable reasoning")
    
    class Config:
        extra = "allow"


class SeismicLineInput(ToolInput):
    """Input for seismic line loading."""
    line_id: str = Field(..., description="Seismic line identifier")
    format: str = Field("segy", description="File format (segy, segyd, etc.)")


class SeismicLineOutput(ToolOutput):
    """Output from seismic line loading."""
    line_data: Dict[str, Any] = Field(default_factory=dict)
    trace_count: int = Field(0)
    sample_rate_ms: float = Field(0.0)


class ProspectEvaluationInput(ToolInput):
    """Input for prospect evaluation."""
    prospect_id: str = Field(..., description="Prospect identifier")
    volumetrics: Dict[str, float] = Field(default_factory=dict)
    risk_factors: List[str] = Field(default_factory=list)


class ProspectEvaluationOutput(ToolOutput):
    """Output from prospect evaluation."""
    prospect_verdict: ProspectVerdict = Field(...)
    recoverable_mm Boe: float = Field(0.0)
    probability_of_success: float = Field(..., ge=0.0, le=1.0)


class PetrophysicsInput(ToolInput):
    """Input for petrophysics calculations."""
    well_id: str = Field(...)
    logs: Dict[str, List[float]] = Field(default_factory=dict)
    depth_range: Optional[tuple] = None


class PetrophysicsOutput(ToolOutput):
    """Output from petrophysics calculations."""
    porosity: List[float] = Field(default_factory=list)
    saturation: List[float] = Field(default_factory=list)
    permeability: List[float] = Field(default_factory=list)
    net_pay: float = Field(0.0)


# Tool registry type
tool_name = str
tool_implementation = Callable[..., ToolOutput]


class ToolRegistry:
    """Canonical tool registry."""
    
    def __init__(self):
        self._tools: Dict[tool_name, tool_implementation] = {}
    
    def register(self, name: str, func: tool_implementation):
        """Register a tool implementation."""
        self._tools[name] = func
    
    def get(self, name: str) -> Optional[tool_implementation]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self._tools.keys())
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools


# Global canonical registry
canonical_registry = ToolRegistry()


__all__ = [
    "ToolInput",
    "ToolOutput",
    "SeismicLineInput",
    "SeismicLineOutput", 
    "ProspectEvaluationInput",
    "ProspectEvaluationOutput",
    "PetrophysicsInput",
    "PetrophysicsOutput",
    "ToolRegistry",
    "canonical_registry",
]
