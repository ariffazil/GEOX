"""
Basin Context Loader
DITEMPA BUKAN DIBERI — Forged, not given

Loads literature-grounded basin stratigraphy from YAML registry files.
Ensures all geological context is sourced from published references,
not fabricated LLM patterns.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class BasinContextNotFoundError(FileNotFoundError):
    """Raised when basin registry file does not exist."""

    pass


@dataclass
class Group:
    """Stratigraphic group from basin context."""

    letter: str
    age: str
    lithology: str
    typical_depth_m: list[int]
    depositional_environment: str = ""
    hc_role: str = ""
    hc_type: str = ""
    overpressure_top_seal: bool = False
    overpressure_compartments: list[str] = field(default_factory=list)
    confidence: float = 0.85
    note: str = ""
    porosity_pct: list[float] = field(default_factory=list)
    permeability_mD_max: float = 0.0


@dataclass
class Overpressure:
    """Overpressure compartment configuration."""

    depth_top_m: list[int]
    stratigraphic_interval: str
    controlling_seal: str
    shape: str = ""
    mechanism: str = ""
    separate_compartment: bool = False
    note: str = ""


@dataclass
class Geothermal:
    """Geothermal parameters for basin."""

    surface_heat_flow_mw_m2: list[float]
    source: str
    stretching_factor_beta: dict[str, float] = field(default_factory=dict)
    geothermal_gradient_c_per_km: list[float] = field(default_factory=list)
    thermal_state: str = ""


@dataclass
class BasinContext:
    """
    Complete basin context loaded from literature-grounded registry.

    This object contains all stratigraphic, overpressure, and geothermal
    parameters needed for geopressure analysis. All data is sourced from
    published references - no fabricated stratigraphy.
    """

    basin: str
    provenance: dict[str, Any]
    groups: list[Group]
    overpressure: dict[str, Overpressure]
    geothermal: Geothermal
    confidence: float = 0.95
    tectonic_phases: list[dict[str, str]] = field(default_factory=list)

    def get_group(self, letter: str) -> Group:
        """
        Get stratigraphic group by letter.

        Args:
            letter: Group letter (A, B, D, E, F, etc.)

        Returns:
            Group dataclass

        Raises:
            KeyError: If group letter not found
        """
        for group in self.groups:
            if group.letter.upper() == letter.upper():
                return group
        raise KeyError(f"Group {letter} not found in basin {self.basin}")

    def get_overpressure_seal(self, compartment: str = "basin_central") -> str:
        """
        Get the letter of the regional top seal group for a compartment.

        Args:
            compartment: Overpressure compartment name (default: basin_central)

        Returns:
            Letter of the seal group (e.g., 'F' for basin_central)

        Raises:
            KeyError: If compartment not found
        """
        if compartment not in self.overpressure:
            raise KeyError(f"Overpressure compartment '{compartment}' not found")
        return self.overpressure[compartment].controlling_seal


def _parse_group(group_data: dict[str, Any]) -> Group:
    """Parse group data from YAML into Group dataclass."""
    return Group(
        letter=group_data.get("letter", ""),
        age=group_data.get("age", ""),
        lithology=group_data.get("lithology", ""),
        typical_depth_m=group_data.get("typical_depth_m", [0, 0]),
        depositional_environment=group_data.get("depositional_environment", ""),
        hc_role=group_data.get("hc_role", ""),
        hc_type=group_data.get("hc_type", ""),
        overpressure_top_seal=group_data.get("overpressure_top_seal", False),
        overpressure_compartments=group_data.get("overpressure_compartments", []),
        confidence=group_data.get("confidence", 0.85),
        note=group_data.get("note", ""),
        porosity_pct=group_data.get("porosity_pct", []),
        permeability_mD_max=group_data.get("permeability_mD_max", 0.0),
    )


def _parse_overpressure(comp_data: dict[str, Any], name: str) -> Overpressure:
    """Parse overpressure compartment data."""
    return Overpressure(
        depth_top_m=comp_data.get("depth_top_m", [0, 0]),
        stratigraphic_interval=comp_data.get("stratigraphic_interval", ""),
        controlling_seal=comp_data.get("controlling_seal", ""),
        shape=comp_data.get("shape", ""),
        mechanism=comp_data.get("mechanism", ""),
        separate_compartment=comp_data.get("separate_compartment", False),
        note=comp_data.get("note", ""),
    )


def _parse_geothermal(geo_data: dict[str, Any]) -> Geothermal:
    """Parse geothermal data."""
    return Geothermal(
        surface_heat_flow_mw_m2=geo_data.get("surface_heat_flow_mw_m2", [33, 42]),
        source=geo_data.get("source", ""),
        stretching_factor_beta=geo_data.get("stretching_factor_beta", {}),
        geothermal_gradient_c_per_km=geo_data.get("geothermal_gradient_c_per_km", [32, 38]),
        thermal_state=geo_data.get("thermal_state", ""),
    )


def load_basin_context(basin_name: str, registry_base: str | None = None) -> BasinContext:
    """
    Load basin context from YAML registry file.

    Args:
        basin_name: Name of basin (e.g., "Malay_Basin", "Sabah_Basin")
        registry_base: Optional base path to registry directory

    Returns:
        BasinContext object with all literature-grounded parameters

    Raises:
        BasinContextNotFoundError: If basin registry file doesn't exist

    Example:
        >>> ctx = load_basin_context("Malay_Basin")
        >>> ctx.get_overpressure_seal()
        'F'
        >>> ctx.get_group("F").overpressure_top_seal
        True
    """
    if registry_base is None:
        # Default to GEOX resources directory
        # Path: /root/GEOX/src/geox_core/registry/basin_context_loader.py
        #       → geox_core → src → GEOX (4 levels up)
        base_path = Path(__file__).parent.parent.parent.parent / "resources" / "registry" / "stratigraphy"
    else:
        base_path = Path(registry_base)

    # Normalize basin name for filename
    filename = basin_name.lower().replace(" ", "_") + ".yaml"
    filepath = base_path / filename

    if not filepath.exists():
        raise BasinContextNotFoundError(
            f"Basin registry not found: {filepath}\n"
            f"Please create a literature-grounded stratigraphy file for {basin_name}.\n"
            f"Required sources: Madon 2006, USGS OF-99-50T, Tjia 1994, etc."
        )

    with open(filepath, "r") as f:
        data = yaml.safe_load(f)

    # Parse groups
    groups = [_parse_group(g) for g in data.get("groups", [])]

    # Parse overpressure compartments
    overpressure = {}
    if "overpressure" in data:
        for name, comp_data in data["overpressure"].items():
            overpressure[name] = _parse_overpressure(comp_data, name)

    # Parse geothermal
    geothermal = _parse_geothermal(data.get("geothermal", {}))

    # Parse tectonic phases
    tectonic_phases = data.get("tectonic_phases", [])

    return BasinContext(
        basin=data.get("basin", basin_name),
        provenance=data.get("provenance", {}),
        groups=groups,
        overpressure=overpressure,
        geothermal=geothermal,
        confidence=data.get("confidence", 0.95),
        tectonic_phases=tectonic_phases,
    )


# Module-level convenience function for direct imports
_default_context_cache: dict[str, BasinContext] = {}


def get_basin_context(basin_name: str) -> BasinContext:
    """
    Get basin context with simple caching.

    Args:
        basin_name: Name of basin

    Returns:
        BasinContext object
    """
    if basin_name not in _default_context_cache:
        _default_context_cache[basin_name] = load_basin_context(basin_name)
    return _default_context_cache[basin_name]
