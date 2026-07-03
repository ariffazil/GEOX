"""
backstrip_decompaction.py — P2 Backstripping + Decompaction
=============================================================
Backstripping: removing sediment load from total subsidence to isolate
tectonic (driving) subsidence (Steckler & Watts 1978, Allen & Allen 2005).
Decompaction: restoring compacted sediment thickness to original depositional
thickness using Athy's porosity–depth law (Athy 1930).

P0 (GPlates live mode) and P1 (McKenzie rift kinematics) provide:
  beta → initial_subsidence + thermal_subsidence → total_subsidence_km.
P2 feeds on P1's total_subsidence_km to isolate the tectonic component.

DITEMPA BUKAN DIBERI — Forged, Not Given.

Forged: 2026-07-03 — P2 Backstripping + Decompaction (atomic with P0 + P1)
"""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════
# Constants (Athy 1930, Sclater & Christie 1980, Allen & Allen 2005)
# ═══════════════════════════════════════════════════════════════════════════

RHO_MANTLE_KGM3: float = 3300.0  # ρm — asthenosphere density (kg/m³)
RHO_WATER_KGM3: float = 1000.0  # ρw — seawater density (kg/m³)
RHO_SEDIMENT_KGM3: float = 2400.0  # ρs — bulk sediment grain density (kg/m³)
GRAVITY_MS2: float = 9.81  # g — gravitational acceleration (m/s²)

# Athy porosity-depth constants per lithology
# φ(z) = φ₀ · exp(−c · z)  where z is depth in km, c in /km
GEOS_POROSITY_DEPTH: dict[str, dict[str, float]] = {
    "sandstone": {"phi0": 0.49, "c_per_km": 0.27},
    "shale": {"phi0": 0.63, "c_per_km": 0.51},
    "limestone": {"phi0": 0.70, "c_per_km": 0.55},
    "siltstone": {"phi0": 0.56, "c_per_km": 0.39},
    "dolomite": {"phi0": 0.50, "c_per_km": 0.40},
    "conglomerate": {"phi0": 0.40, "c_per_km": 0.20},
    "generic": {"phi0": 0.60, "c_per_km": 0.50},  # fallback
}


def _lithology_params(lithology: str) -> tuple[float, float]:
    """Resolve φ₀ and c from lithology name with generic fallback."""
    entry = GEOS_POROSITY_DEPTH.get(lithology.lower(), GEOS_POROSITY_DEPTH["generic"])
    return entry["phi0"], entry["c_per_km"]


# ═══════════════════════════════════════════════════════════════════════════
# Pydantic I/O schemas — MCP transport compatible
# ═══════════════════════════════════════════════════════════════════════════


class BackstripRequest(BaseModel):
    """Input for a single backstrip + decompaction step."""

    present_thickness_m: float = Field(
        ...,
        ge=1.0,
        le=20000.0,
        description="Present-day compacted layer thickness (m)",
    )
    present_base_depth_m: float = Field(
        ...,
        ge=0.0,
        le=30000.0,
        description="Present-day depth to base of layer (m)",
    )
    lithology: str = Field(
        default="generic",
        description="Lithology key: sandstone, shale, limestone, siltstone, dolomite, conglomerate, generic",
    )
    phi0: float | None = Field(
        default=None,
        ge=0.1,
        le=0.8,
        description="Override surface porosity φ₀. None → resolved from lithology.",
    )
    c_per_km: float | None = Field(
        default=None,
        ge=0.1,
        le=1.5,
        description="Override compaction coefficient c (/km). None → resolved from lithology.",
    )
    rho_sediment_kgm3: float = Field(
        default=RHO_SEDIMENT_KGM3,
        ge=2000.0,
        le=3000.0,
        description="Sediment grain density (kg/m³)",
    )


class DecompactionResult(BaseModel):
    """Output of a single-layer decompaction.

    Every field carries epistemic labels. F2 TRUTH + F7 HUMILITY enforced.
    """

    present_thickness_m: float = Field(...)
    original_thickness_m: float = Field(
        ...,
        description="T₀ — thickness at deposition (decompacted)",
    )
    solid_grain_thickness_m: float = Field(
        ...,
        description="T_solid — irreducible solid fraction of the layer",
    )
    present_avg_porosity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="φ̄ — depth-averaged porosity at present burial depth",
    )
    surface_porosity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="φ₀ — porosity at deposition surface",
    )
    compaction_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="T_present / T_original — how compacted the layer is",
    )
    confidence: float = Field(
        default=0.80,
        ge=0.0,
        le=0.90,
        description="Confidence capped at 0.90 (F7 HUMILITY)",
    )
    epistemic_label: str = Field(default="DER")
    assumptions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)


class SubsidenceStep(BaseModel):
    """One step in the tectonic subsidence history."""

    step: int = Field(..., ge=0)
    layer_name: str = Field(default="")
    decompacted_thickness_m: float = Field(...)
    tectonic_subsidence_km: float = Field(...)
    sediment_load_correction_km: float = Field(
        ...,
        description="ΔS — subsidence attributable to sediment weight alone",
    )
    water_depth_m: float = Field(default=0.0)
    cumulative_sediment_km: float = Field(
        ...,
        description="Total decompacted sediment thickness deposited so far",
    )


class SubsidenceHistory(BaseModel):
    """Tectonic subsidence curve — from backstripping.

    Agentic contract:
      - alternative_models always populated (no single hypothesis without contest)
      - evidence_gaps lists what other agents should fetch next
      - confidence decreases with fewer constraints
    """

    steps: list[SubsidenceStep] = Field(default_factory=list)
    total_decompacted_sediment_km: float = Field(default=0.0)
    total_tectonic_subsidence_km: float = Field(default=0.0)
    water_depth_m: float = Field(default=0.0)
    confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=0.90,
        description="Confidence capped at 0.90 (F7 HUMILITY)",
    )
    epistemic_label: str = Field(default="DER")
    alternative_models: list[str] = Field(
        default_factory=lambda: [
            "flexural_isostasy",
            "compaction_dis-equilibrium",
            "chemical_compaction",
        ],
    )
    evidence_gaps: list[str] = Field(
        default_factory=lambda: [
            "paleobathymetry_data",
            "biostratigraphic_age_control",
            "vitrinite_reflectance",
            "formation_pressure_data",
        ],
    )
    note: str = Field(default="")


# ═══════════════════════════════════════════════════════════════════════════
# Pure Functions — no I/O, no side effects
# ═══════════════════════════════════════════════════════════════════════════


def porosity_at_depth(z_km: float, phi0: float, c_per_km: float) -> float:
    """Porosity at depth z via Athy's law (Athy 1930).

    φ(z) = φ₀ · exp(−c · z)

    z_km : depth in kilometres
    phi0  : surface porosity (depositional)
    c_per_km : compaction coefficient (/km)

    F2 TRUTH: empirical correlation, not a physical law.
    Valid for mechanical compaction regime (<3–4 km depth).
    Chemical compaction (quartz cementation) dominates beyond ~3 km.

    Returns porosity as fraction [0, 1].
    """
    if z_km < 0:
        raise ValueError(f"Depth must be ≥ 0, got {z_km}")
    return phi0 * math.exp(-c_per_km * z_km)


def average_porosity(z_top_km: float, z_base_km: float, phi0: float, c_per_km: float) -> float:
    """Depth-averaged porosity over [z_top, z_base].

    φ̄ = (1 / Δz) ∫_{z_top}^{z_base} φ₀ · exp(−c · z) dz
       = (φ₀ / (c · Δz)) · (exp(−c · z_top) − exp(−c · z_base))

    Where Δz = z_base − z_top.

    Returns mean porosity as fraction [0, 1].
    """
    if z_base_km <= z_top_km:
        raise ValueError(f"z_base ({z_base_km}) must be > z_top ({z_top_km})")
    dz = z_base_km - z_top_km
    integral = (phi0 / (c_per_km * dz)) * (math.exp(-c_per_km * z_top_km) - math.exp(-c_per_km * z_base_km))
    return max(0.0, min(1.0, integral))


def decompact_thickness(
    present_thickness_m: float,
    present_base_depth_m: float,
    phi0: float = 0.60,
    c_per_km: float = 0.50,
) -> float:
    """Restore compacted layer to original depositional thickness.

    Physics (Athy 1930, Sclater & Christie 1980):
      Solid grain volume is conserved during compaction.
      T_solid = T_present · (1 − φ̄_present)
      T₀       = T_solid / (1 − φ₀)

    Where φ̄_present is the depth-averaged porosity of the layer at its
    present burial depth, and φ₀ is the surface porosity at deposition.

    present_thickness_m : present compacted thickness (metres)
    present_base_depth_m : depth to base of layer (metres)
    phi0 : surface porosity at deposition
    c_per_km : compaction coefficient (/km)

    F2 TRUTH: Athy's law is an empirical fit. Real compaction depends on
    grain size, sorting, clay content, overpressure, and chemical diagenesis.
    F7 HUMILITY: decompacted thickness error ±15–25% for deep (>3 km) layers.

    Returns original (decompacted) thickness in metres.
    """
    if present_thickness_m <= 0:
        raise ValueError(f"present_thickness_m must be > 0, got {present_thickness_m}")
    if present_base_depth_m < 0:
        raise ValueError(f"present_base_depth_m must be ≥ 0, got {present_base_depth_m}")

    z_top_km = (present_base_depth_m - present_thickness_m) / 1000.0
    z_base_km = present_base_depth_m / 1000.0

    if z_top_km < 0:
        z_top_km = 0.0

    phi_avg = average_porosity(z_top_km, z_base_km, phi0, c_per_km)
    solid_grains_m = present_thickness_m * (1.0 - phi_avg)
    original_thickness_m = solid_grains_m / (1.0 - phi0)

    return original_thickness_m


def backstrip_sediment_load(
    total_subsidence_km: float,
    sediment_thickness_km: float,
    rho_sediment_kgm3: float = RHO_SEDIMENT_KGM3,
    rho_mantle_kgm3: float = RHO_MANTLE_KGM3,
    rho_water_kgm3: float = RHO_WATER_KGM3,
) -> float:
    """Remove sediment loading from total subsidence (Airy isostasy).

    When sediment fills a water-filled basin, the denser sediment drives
    additional isostatic subsidence beyond what tectonic forces alone
    would produce. This function isolates the tectonic component.

    ΔS_sediment = T_sed · (ρs − ρw) / (ρm − ρw)          … isostatic correction
    S_tectonic  = S_total − ΔS_sediment                   … tectonic residual

    Steckler & Watts (1978), Allen & Allen (2005, eq. 9.17).

    total_subsidence_km   : total subsidence including sediment load (km)
    sediment_thickness_km : thickness of the sediment column (km)
    rho_sediment_kgm3     : bulk sediment grain density (kg/m³)
    rho_mantle_kgm3       : mantle density (kg/m³)
    rho_water_kgm3        : water density (kg/m³)

    F2 TRUTH: Airy is local (no flexural rigidity). For wide basins
    (>200 km), flexural effects reduce the correction by 10–30%.
    This is a first-order approximation.

    Returns tectonic subsidence in km.
    """
    if total_subsidence_km < 0:
        raise ValueError(f"total_subsidence_km must be ≥ 0, got {total_subsidence_km}")
    if sediment_thickness_km < 0:
        raise ValueError(f"sediment_thickness_km must be ≥ 0, got {sediment_thickness_km}")

    density_ratio = (rho_sediment_kgm3 - rho_water_kgm3) / (rho_mantle_kgm3 - rho_water_kgm3)
    sediment_load_correction_km = sediment_thickness_km * density_ratio
    tectonic_km = total_subsidence_km - sediment_load_correction_km

    return max(0.0, tectonic_km)


def decompact_result(
    present_thickness_m: float,
    present_base_depth_m: float,
    lithology: str = "generic",
    phi0: float | None = None,
    c_per_km: float | None = None,
) -> DecompactionResult:
    """Full decompaction result with provenance and gaps.

    F2 TRUTH: all numbers are DER (derived from Athy's law).
    F7 HUMILITY: confidence capped at 0.90.
    """
    resolved_phi0, resolved_c = _lithology_params(lithology)
    if phi0 is not None:
        resolved_phi0 = phi0
    if c_per_km is not None:
        resolved_c = c_per_km

    z_top_km = max(0.0, (present_base_depth_m - present_thickness_m) / 1000.0)
    z_base_km = present_base_depth_m / 1000.0

    phi_avg = average_porosity(z_top_km, z_base_km, resolved_phi0, resolved_c)
    solid_grains_m = present_thickness_m * (1.0 - phi_avg)
    original_m = solid_grains_m / (1.0 - resolved_phi0)
    compaction_ratio = present_thickness_m / original_m if original_m > 0 else 1.0

    # Confidence: decreases with depth (mechanical → chemical compaction transition)
    if z_base_km < 1.0:
        conf = 0.88
    elif z_base_km < 2.0:
        conf = 0.82
    elif z_base_km < 3.0:
        conf = 0.76
    else:
        conf = 0.68  # chemical compaction / overpressure possible

    gaps = ["overpressure_data", "velocity‑porosity_transform", "core_porosity_measurements"]
    if z_base_km > 2.5:
        gaps.append("quartz_cementation_history")

    return DecompactionResult(
        present_thickness_m=round(present_thickness_m, 1),
        original_thickness_m=round(original_m, 1),
        solid_grain_thickness_m=round(solid_grains_m, 1),
        present_avg_porosity=round(phi_avg, 4),
        surface_porosity=round(resolved_phi0, 4),
        compaction_ratio=round(compaction_ratio, 4),
        confidence=conf,
        epistemic_label="DER",
        assumptions=[
            f"Athy exponential φ(z) = {resolved_phi0}·exp(−{resolved_c}·z)",
            "no overpressure (hydrostatic pore pressure)",
            "mechanical compaction only (no chemical diagenesis)",
        ],
        evidence_gaps=gaps,
    )


def compute_subsidence_history(
    stratigraphic_column: list[dict[str, Any]],
    water_depth_m: float = 0.0,
    rho_sediment_kgm3: float = RHO_SEDIMENT_KGM3,
    rho_mantle_kgm3: float = RHO_MANTLE_KGM3,
    rho_water_kgm3: float = RHO_WATER_KGM3,
) -> SubsidenceHistory:
    """Compute tectonic subsidence curve via sequential backstripping.

    Procedure (Allen & Allen 2005, ch. 9):
      1. Sort layers from deepest (oldest) to shallowest (youngest).
      2. At each step, decompact all layers to restore their thicknesses
         to what they were at the time that layer was at the surface.
      3. Compute the sediment-load correction for the cumulative sediment
         column deposited up to that step.
      4. Record tectonic subsidence at each time step.

    stratigraphic_column : list of per-layer dicts with keys:
        present_thickness_m  : float  — present compacted thickness
        present_base_depth_m : float  — depth to base of layer
        lithology            : str    — sandstone|shale|limestone|siltstone|...
        name                 : str    — optional label
        phi0                 : float  — optional surface porosity override
        c_per_km             : float  — optional compaction coefficient override
    water_depth_m : paleo-water depth (assumed constant for simplicity)
    rho_sediment_kgm3 : sediment grain density
    rho_mantle_kgm3   : mantle density
    rho_water_kgm3    : water density

    F2 TRUTH: assumes constant water depth, uniform lithospheric properties,
    and Athy mechanical compaction only. Real basins require time-varying
    paleobathymetry, flexural isostasy, and chemical compaction corrections.
    F7 HUMILITY: confidence decreases with number of decompaction steps
    (errors compound).

    Returns SubsidenceHistory with tectonic subsidence curve.
    """
    if not stratigraphic_column:
        raise ValueError("stratigraphic_column must be non-empty")

    # Sort deepest-first (oldest at bottom)
    sorted_col = sorted(stratigraphic_column, key=lambda layer: layer["present_base_depth_m"], reverse=True)
    n_layers = len(sorted_col)

    steps: list[SubsidenceStep] = []
    decompacted_columns: list[dict[str, Any]] = []  # decompacted state at each step

    for i in range(n_layers):
        layer = sorted_col[i]
        present_thickness = layer["present_thickness_m"]
        present_base = layer["present_base_depth_m"]
        lith = layer.get("lithology", "generic")
        name = layer.get("name", f"L{i + 1}")
        phi0_override = layer.get("phi0")
        c_override = layer.get("c_per_km")

        resolved_phi0, resolved_c = _lithology_params(lith)
        if phi0_override is not None:
            resolved_phi0 = phi0_override
        if c_override is not None:
            resolved_c = c_override

        # Decompact this layer: its top was at the surface when deposited
        orig_thickness = decompact_thickness(
            present_thickness_m=present_thickness,
            present_base_depth_m=present_base,
            phi0=resolved_phi0,
            c_per_km=resolved_c,
        )

        # Decompact overlying (younger) layers: after this layer is deposited,
        # the layers above it were at shallower depths. For each already-deposited
        # layer, we must decompact it relative to the cumulative sediment above it.
        # Simplification: at step i, cumulative decompacted thickness above this
        # layer is the sum of decompacted thicknesses of layers i+1..n.
        cumulative_decompacted_km = (
            sum(
                decompact_thickness(
                    present_thickness_m=sorted_col[k]["present_thickness_m"],
                    present_base_depth_m=sorted_col[k]["present_base_depth_m"],
                    phi0=_lithology_params(sorted_col[k].get("lithology", "generic"))[0],
                    c_per_km=_lithology_params(sorted_col[k].get("lithology", "generic"))[1],
                )
                for k in range(i + 1, n_layers)
            )
            / 1000.0
        )

        # Total decompacted sediment column at this step (this layer + all above)
        total_sediment_km = cumulative_decompacted_km + orig_thickness / 1000.0

        # Sediment-load correction
        density_ratio = (rho_sediment_kgm3 - rho_water_kgm3) / (rho_mantle_kgm3 - rho_water_kgm3)
        sediment_load_correction_km = total_sediment_km * density_ratio

        # Total subsidence = water depth + accumulated decompacted sediment column
        # The tectonic subsidence is the basement depth with water loading only
        water_depth_km = water_depth_m / 1000.0
        total_subsidence_km = water_depth_km + total_sediment_km

        # Tectonic subsidence = total − sediment-load correction
        tectonic_km = total_subsidence_km - sediment_load_correction_km

        steps.append(
            SubsidenceStep(
                step=i,
                layer_name=name,
                decompacted_thickness_m=round(orig_thickness, 1),
                tectonic_subsidence_km=round(max(0.0, tectonic_km), 4),
                sediment_load_correction_km=round(sediment_load_correction_km, 4),
                water_depth_m=water_depth_m,
                cumulative_sediment_km=round(total_sediment_km, 4),
            )
        )

        decompacted_columns.append(
            {
                "name": name,
                "present_thickness_m": present_thickness,
                "original_thickness_m": round(orig_thickness, 1),
                "lithology": lith,
            }
        )

    final_total_sediment_km = steps[-1].cumulative_sediment_km if steps else 0.0
    final_tectonic_km = steps[-1].tectonic_subsidence_km if steps else 0.0

    # Confidence calibration
    conf = 0.80  # base: Athy + Airy
    if n_layers > 4:
        conf = max(0.60, conf - 0.05 * (n_layers - 4))  # error compounding
    if water_depth_m > 0:
        conf = min(0.85, conf + 0.05)  # water-depth constraint present

    return SubsidenceHistory(
        steps=steps,
        total_decompacted_sediment_km=round(final_total_sediment_km, 4),
        total_tectonic_subsidence_km=round(final_tectonic_km, 4),
        water_depth_m=water_depth_m,
        confidence=conf,
        epistemic_label="DER",
        alternative_models=[
            "flexural_isostasy",
            "compaction_dis-equilibrium",
            "chemical_compaction",
        ],
        evidence_gaps=[
            "paleobathymetry_data",
            "biostratigraphic_age_control",
            "vitrinite_reflectance",
            "formation_pressure_data",
        ],
        note=(
            f"Backstripping across {n_layers} layers. "
            f"Total decompacted sediment: {final_total_sediment_km:.2f} km. "
            f"Tectonic subsidence: {final_tectonic_km:.3f} km. "
            f"Airy isostasy, Athy compaction. "
            f"Calibrate with flexural model + paleobathymetry for higher confidence."
        ),
    )


__all__ = [
    "BackstripRequest",
    "DecompactionResult",
    "SubsidenceStep",
    "SubsidenceHistory",
    "porosity_at_depth",
    "average_porosity",
    "decompact_thickness",
    "backstrip_sediment_load",
    "decompact_result",
    "compute_subsidence_history",
    "GEOS_POROSITY_DEPTH",
    "RHO_MANTLE_KGM3",
    "RHO_WATER_KGM3",
    "RHO_SEDIMENT_KGM3",
]
