"""
earth_state_vector.py — Petrophysical EarthStateVector (P0 gap fill)

A shared context object for cross-tool petrophysical state.
Every GEOX tool that produces subsurface properties writes to this.
Every tool that consumes subsurface properties reads from this.

The bridge between geox_petrophysics → geox_basin_backstrip →
geox_thermal_maturity → geox_prospect.

Fields are optional — tools populate what they can, consumers
check availability before reading. This is the "causal connectivity"
that the 30 July audit correctly identified as missing.

DITEMPA BUKAN DIBERI — 2026-07-31
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PetrophysicalEarthStateVector:
    """Shared petrophysical context across GEOX tools.

    Populated progressively through the geological reasoning chain:
    petrophysics → burial → thermal → charge → prospect.

    All fields optional — tools write what they produce, consumers
    check for None before reading.
    """

    # ── Identity ──────────────────────────────────────────────────────────
    well_id: str | None = None
    basin: str | None = None
    zone_name: str | None = None
    depth_top_m: float | None = None
    depth_base_m: float | None = None

    # ── Mineralogy (from geox_petrophysics multi_mineral_zone) ────────────
    mineral_volumes: dict[str, float] = field(default_factory=dict)
    dominant_mineral: str | None = None
    clay_type: str | None = None
    cec_meq_100g: float | None = None
    matrix_density_gcc: float | None = None
    matrix_vp_ms: float | None = None
    matrix_vs_ms: float | None = None

    # ── Porosity & Saturation (from geox_petrophysics) ────────────────────
    porosity: float | None = None
    sw: float | None = None
    permeability_md: float | None = None
    sw_model: str | None = None

    # ── Pressure & Temperature ────────────────────────────────────────────
    pore_pressure_mpa: float | None = None
    temperature_c: float | None = None
    geothermal_gradient_c_km: float | None = None
    overburden_stress_mpa: float | None = None
    effective_stress_mpa: float | None = None

    # ── Burial History (from geox_basin_backstrip) ────────────────────────
    max_burial_depth_m: float | None = None
    subsidence_rate_mm_yr: float | None = None
    tectonic_subsidence_m: float | None = None

    # ── Thermal Maturity (from geox_thermal_maturity_history) ─────────────
    vitrinite_reflectance_ro: float | None = None
    tmax_c: float | None = None
    tti: float | None = None
    maturity_zone: str | None = None  # immature / oil / wet_gas / dry_gas / overmature

    # ── Geomechanics ──────────────────────────────────────────────────────
    youngs_modulus_gpa: float | None = None
    poisson_ratio: float | None = None
    brittleness_index: float | None = None
    fracture_pressure_mpa: float | None = None

    # ── Rock Physics ──────────────────────────────────────────────────────
    vp_ms: float | None = None
    vs_ms: float | None = None
    acoustic_impedance: float | None = None
    vp_vs_ratio: float | None = None

    # ── Epistemic ─────────────────────────────────────────────────────────
    provenance: dict[str, str] = field(default_factory=dict)  # field → tool that produced it
    confidence: dict[str, str] = field(default_factory=dict)   # field → HIGH/MEDIUM/LOW
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict, stripping None values."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None and (not isinstance(value, (dict, list)) or value):
                result[key] = value
        # Always include non-empty provenance/confidence/warnings
        if self.provenance:
            result["provenance"] = self.provenance
        if self.confidence:
            result["confidence"] = self.confidence
        if self.warnings:
            result["warnings"] = self.warnings
        return result

    def completeness(self) -> float:
        """Fraction of key fields populated. 1.0 = fully characterised."""
        key_fields = [
            "porosity", "sw", "matrix_density_gcc", "dominant_mineral",
            "pore_pressure_mpa", "temperature_c", "max_burial_depth_m",
            "vitrinite_reflectance_ro", "brittleness_index",
        ]
        populated = sum(1 for f in key_fields if getattr(self, f, None) is not None)
        return populated / len(key_fields)

    def grade(self) -> str:
        """AAA-quality grade based on completeness."""
        c = self.completeness()
        if c >= 0.80: return "AAA"
        if c >= 0.50: return "AA"
        if c >= 0.30: return "A"
        return "RAW"


# ── Builder ──────────────────────────────────────────────────────────────────

def build_earth_state_vector_from_mineral_zone(
    zone_result: dict[str, Any],
    well_id: str | None = None,
    basin: str | None = None,
) -> PetrophysicalEarthStateVector:
    """Populate an EarthStateVector from a multi_mineral_zone result."""
    esv = PetrophysicalEarthStateVector(
        well_id=well_id or zone_result.get("well"),
        basin=basin or zone_result.get("zone"),
        depth_top_m=zone_result.get("depth_top_m"),
        depth_base_m=zone_result.get("depth_base_m"),
        porosity=zone_result.get("phie"),
        matrix_density_gcc=zone_result.get("matrix_density_gcc"),
        dominant_mineral=_dominant_mineral_from_stats(zone_result.get("mineralogy", {})),
        clay_type=zone_result.get("dominant_clay_type"),
        cec_meq_100g=zone_result.get("avg_cec_meq_100g"),
        sw_model=zone_result.get("sw_model"),
        provenance={"mineralogy": "geox_petrophysics.multi_mineral_zone"},
        confidence={"mineralogy": zone_result.get("solver_confidence", "MEDIUM")},
        warnings=zone_result.get("warnings", []),
    )
    return esv


def _dominant_mineral_from_stats(mineralogy: dict) -> str | None:
    """Extract dominant mineral from P50 stats."""
    best = None
    best_p50 = 0.0
    for name, stats in mineralogy.items():
        p50 = stats.get("p50", 0) if isinstance(stats, dict) else 0
        if p50 > best_p50:
            best_p50 = p50
            best = name
    return best
