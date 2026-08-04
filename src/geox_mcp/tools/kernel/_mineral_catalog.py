"""
_mineral_catalog.py — GEOX Mineral Physics Catalogue (Chemistry9 X1)
════════════════════════════════════════════════════════════════════════

DITEMPA BUKAN DIBERI — The rock's chemistry is forged, not given.

12 minerals spanning clastic, carbonate, evaporite, and heavy/accessory families.
Each mineral carries formula, grain density, elastic moduli, log responses,
and clay-specific cation exchange capacity (CEC).

References:
  - Mavko, G., Mukerji, T., Dvorkin, J. (2009) The Rock Physics Handbook.
  - Ellis, D.V. & Singer, J.M. (2007) Well Logging for Earth Scientists.
  - Crain's Petrophysical Handbook (crainpetrophysical.com).
  - Thomas, E.C. & Stieber, S.J. (1975) Distribution of shale types.
  - Waxman, M.H. & Smits, L.J.M. (1968) Electrical conductivities.
"""

from __future__ import annotations

from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# MINERAL CATALOGUE — 12 Minerals
# ═══════════════════════════════════════════════════════════════════════════════
# Each mineral entry:
#   formula          — chemical formula
#   rho_gcc          — grain density (g/cm³)
#   vp_ms            — P-wave velocity (m/s)
#   vs_ms            — S-wave velocity (m/s)
#   pef_barns_e      — photoelectric factor (barns/electron)
#   gr_api           — natural gamma ray response (API units)
#   neutron_phi_nphi — apparent neutron porosity in limestone matrix (v/v)
#   k_gpa            — bulk modulus (GPa)
#   mu_gpa           — shear modulus (GPa)
#   cec_meq_100g     — cation exchange capacity (meq/100g, clay only)
#   chemical_family  — clastic / carbonate / evaporite / heavy / organic

MINERAL_CATALOG: dict[str, dict[str, Any]] = {
    # ── Clastic Family ──────────────────────────────────────────────────────
    "quartz": {
        "formula": "SiO₂",
        "rho_gcc": 2.65,
        "vp_ms": 6050,
        "vs_ms": 4090,
        "pef_barns_e": 1.81,
        "gr_api": 5,
        "neutron_phi_nphi": -0.02,
        "k_gpa": 37.0,
        "mu_gpa": 44.0,
        "cec_meq_100g": 0,
        "chemical_family": "clastic",
        "notes": "Stable framework grain. The reservoir king. Chemically inert at surface conditions.",
    },
    "feldspar": {
        "formula": "KAlSi₃O₈ (orthoclase) / NaAlSi₃O₈ (albite)",
        "rho_gcc": 2.56,
        "vp_ms": 5800,
        "vs_ms": 3300,
        "pef_barns_e": 2.86,
        "gr_api": 200,
        "neutron_phi_nphi": -0.01,
        "k_gpa": 37.5,
        "mu_gpa": 15.0,
        "cec_meq_100g": 0,
        "chemical_family": "clastic",
        "notes": "K-feldspar dominant. Radioactive — GR anomaly. Weathers to kaolinite.",
    },
    "illite": {
        "formula": "K₀.₇Al₂(Al₀.₇Si₃.₃)O₁₀(OH)₂",
        "rho_gcc": 2.77,
        "vp_ms": 4300,
        "vs_ms": 2500,
        "pef_barns_e": 3.45,
        "gr_api": 250,
        "neutron_phi_nphi": 0.30,
        "k_gpa": 25.0,
        "mu_gpa": 10.0,
        "cec_meq_100g": 25,
        "chemical_family": "clastic",
        "notes": "Common burial clay. Conductive. High CEC. mica-derived. K-bearing → radioactive.",
    },
    "smectite": {
        "formula": "(Na,Ca)₀.₃(Al,Mg)₂Si₄O₁₀(OH)₂·nH₂O",
        "rho_gcc": 2.12,
        "vp_ms": 2500,
        "vs_ms": 1200,
        "pef_barns_e": 2.04,
        "gr_api": 150,
        "neutron_phi_nphi": 0.44,
        "k_gpa": 7.0,
        "mu_gpa": 2.0,
        "cec_meq_100g": 100,
        "chemical_family": "clastic",
        "notes": "Swelling clay. Very high CEC. Bound water ⪅ 40%. Kills permeability on contact with fresh water.",
    },
    "kaolinite": {
        "formula": "Al₂Si₂O₅(OH)₄",
        "rho_gcc": 2.64,
        "vp_ms": 3400,
        "vs_ms": 1800,
        "pef_barns_e": 1.83,
        "gr_api": 100,
        "neutron_phi_nphi": 0.37,
        "k_gpa": 12.0,
        "mu_gpa": 5.0,
        "cec_meq_100g": 8,
        "chemical_family": "clastic",
        "notes": "Pore-throat blocking clay. Low CEC. Weathering product of feldspar. Migrates, doesn't swell.",
    },
    "chlorite": {
        "formula": "(Mg,Fe)₅Al(AlSi₃)O₁₀(OH)₈",
        "rho_gcc": 2.88,
        "vp_ms": 5000,
        "vs_ms": 3000,
        "pef_barns_e": 6.30,
        "gr_api": 50,
        "neutron_phi_nphi": 0.52,
        "k_gpa": 30.0,
        "mu_gpa": 15.0,
        "cec_meq_100g": 15,
        "chemical_family": "clastic",
        "notes": "Iron-rich clay. High density. Grain-coating → can preserve porosity. Very high PE.",
    },
    # ── Carbonate Family ─────────────────────────────────────────────────────
    "calcite": {
        "formula": "CaCO₃",
        "rho_gcc": 2.71,
        "vp_ms": 6400,
        "vs_ms": 3400,
        "pef_barns_e": 5.08,
        "gr_api": 8,
        "neutron_phi_nphi": 0.00,
        "k_gpa": 77.0,
        "mu_gpa": 32.0,
        "cec_meq_100g": 0,
        "chemical_family": "carbonate",
        "notes": "Primary carbonate. NPHI=0 in limestone matrix. Chemically reactive — dissolves, recrystallises.",
    },
    "dolomite": {
        "formula": "CaMg(CO₃)₂",
        "rho_gcc": 2.87,
        "vp_ms": 7000,
        "vs_ms": 3800,
        "pef_barns_e": 3.14,
        "gr_api": 10,
        "neutron_phi_nphi": 0.01,
        "k_gpa": 95.0,
        "mu_gpa": 45.0,
        "cec_meq_100g": 0,
        "chemical_family": "carbonate",
        "notes": "Replacement of calcite by Mg-rich fluids. Higher density, velocity. Porosity-preserving.",
    },
    "ankerite": {
        "formula": "Ca(Fe,Mg,Mn)(CO₃)₂",
        "rho_gcc": 2.97,
        "vp_ms": 6800,
        "vs_ms": 3600,
        "pef_barns_e": 9.32,
        "gr_api": 15,
        "neutron_phi_nphi": 0.02,
        "k_gpa": 85.0,
        "mu_gpa": 40.0,
        "cec_meq_100g": 0,
        "chemical_family": "carbonate",
        "notes": "Iron-rich dolomite. Very high PE (Fe). Late-diagenetic cement in deep burial.",
    },
    # ── Heavy / Accessory Family ──────────────────────────────────────────────
    "pyrite": {
        "formula": "FeS₂",
        "rho_gcc": 5.00,
        "vp_ms": 8000,
        "vs_ms": 5000,
        "pef_barns_e": 16.97,
        "gr_api": 0,
        "neutron_phi_nphi": -0.03,
        "k_gpa": 147.0,
        "mu_gpa": 132.0,
        "cec_meq_100g": 0,
        "chemical_family": "heavy",
        "notes": "Very high density and PE. 1% pyrite → +0.02 g/cc in bulk density. Anoxic indicator.",
    },
    "siderite": {
        "formula": "FeCO₃",
        "rho_gcc": 3.96,
        "vp_ms": 6200,
        "vs_ms": 3300,
        "pef_barns_e": 14.69,
        "gr_api": 20,
        "neutron_phi_nphi": 0.12,
        "k_gpa": 124.0,
        "mu_gpa": 51.0,
        "cec_meq_100g": 0,
        "chemical_family": "heavy",
        "notes": "Iron carbonate. High density. Freshwater diagenesis indicator. Concretionary.",
    },
    # ── Organic Family ────────────────────────────────────────────────────────
    "organic_matter": {
        "formula": "CH₂O (simplified kerogen)",
        "rho_gcc": 1.30,
        "vp_ms": 2200,
        "vs_ms": 1000,
        "pef_barns_e": 0.20,
        "gr_api": 250,
        "neutron_phi_nphi": 0.65,
        "k_gpa": 4.0,
        "mu_gpa": 1.5,
        "cec_meq_100g": 0,
        "chemical_family": "organic",
        "notes": "Kerogen/organic matter. Very low density, very high GR, very high neutron. Source rock indicator.",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLAY DISCRIMINATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

CLAY_MINERALS = {"illite", "smectite", "kaolinite", "chlorite"}

# GR endpoints per clay type (pure clay, no silt)
CLAY_GR_RESPONSE: dict[str, float] = {
    "illite": 250.0,
    "smectite": 150.0,
    "kaolinite": 100.0,
    "chlorite": 50.0,
}

# Density of pure clay (no bound water)
CLAY_DRY_DENSITY: dict[str, float] = {
    "illite": 2.77,
    "smectite": 2.12,
    "kaolinite": 2.64,
    "chlorite": 2.88,
}

# Typical GR_cl (clean sand GR) and GR_sh (pure shale GR) per basin
# From petrophysics_assumptions.yaml + regional calibration
GR_ENDPOINT_DEFAULTS: dict[str, dict[str, float]] = {
    "sabah": {"gr_clean": 20, "gr_shale": 150},
    "malay": {"gr_clean": 15, "gr_shale": 140},
    "generic": {"gr_clean": 15, "gr_shale": 150},
}


# ═══════════════════════════════════════════════════════════════════════════════
# MINERAL CATALOGUE QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def get_mineral(name: str) -> dict[str, Any] | None:
    """Look up a mineral by name. Case-insensitive. Returns None if not found."""
    key = name.lower().strip()
    # Handle common aliases
    aliases = {
        "k-feldspar": "feldspar",
        "orthoclase": "feldspar",
        "albite": "feldspar",
        "organic": "organic_matter",
        "kerogen": "organic_matter",
        "toc": "organic_matter",
    }
    key = aliases.get(key, key)
    return MINERAL_CATALOG.get(key)


def get_mineral_property(name: str, prop: str) -> float | None:
    """Get a single property value for a mineral."""
    mineral = get_mineral(name)
    if mineral is None:
        return None
    return mineral.get(prop)


def list_minerals_by_family(family: str) -> list[str]:
    """Get all minerals in a chemical family."""
    return [name for name, data in MINERAL_CATALOG.items() if data.get("chemical_family") == family]


def get_all_clay_minerals() -> list[str]:
    """Get all clay mineral names."""
    return list(CLAY_MINERALS)


def compute_matrix_density(mineral_fractions: dict[str, float]) -> float:
    """Compute weighted-average matrix density from mineral volume fractions.

    Args:
        mineral_fractions: {mineral_name: volume_fraction} — must sum to (1 - phi)

    Returns:
        Weighted matrix density in g/cm³
    """
    total_vol = 0.0
    weighted_rho = 0.0
    for name, frac in mineral_fractions.items():
        mineral = get_mineral(name)
        if mineral and frac > 0:
            rho = mineral.get("rho_gcc", 2.65)
            weighted_rho += frac * rho
            total_vol += frac

    if total_vol < 0.001:
        return 2.65  # default quartz
    return weighted_rho / total_vol


def compute_matrix_elastic(
    mineral_fractions: dict[str, float],
) -> dict[str, float]:
    """Compute Hill-average matrix elastic moduli (Voigt-Reuss-Hill).

    Returns {k_matrix_gpa, mu_matrix_gpa, vp_matrix_ms, vs_matrix_ms}
    """
    k_v = 0.0  # Voigt (upper bound — strain uniform)
    k_r_inv = 0.0  # Reuss inverse (lower bound — stress uniform)
    mu_v = 0.0
    mu_r_inv = 0.0
    total_vol = 0.0

    for name, frac in mineral_fractions.items():
        mineral = get_mineral(name)
        if mineral and frac > 0:
            k = mineral.get("k_gpa", 37.0)
            mu = mineral.get("mu_gpa", 44.0)
            _rho = mineral.get("rho_gcc", 2.65)

            k_v += frac * k
            k_r_inv += frac / max(k, 1e-6)
            mu_v += frac * mu
            mu_r_inv += frac / max(mu, 1e-6)
            total_vol += frac

    if total_vol < 0.001:
        return {"k_matrix_gpa": 37.0, "mu_matrix_gpa": 44.0, "vp_matrix_ms": 6050, "vs_matrix_ms": 4090}

    k_v /= total_vol
    k_r = total_vol / max(k_r_inv, 1e-6)
    mu_v /= total_vol
    mu_r = total_vol / max(mu_r_inv, 1e-6)

    # Voigt-Reuss-Hill average
    k_hill = 0.5 * (k_v + k_r)
    mu_hill = 0.5 * (mu_v + mu_r)

    # Matrix density for Vp/Vs
    rho_matrix = compute_matrix_density(mineral_fractions) * 1000.0  # kg/m³
    vp = ((k_hill * 1e9 + 4.0 / 3.0 * mu_hill * 1e9) / max(rho_matrix, 1.0)) ** 0.5
    vs = (mu_hill * 1e9 / max(rho_matrix, 1.0)) ** 0.5

    return {
        "k_matrix_gpa": round(k_hill, 1),
        "mu_matrix_gpa": round(mu_hill, 1),
        "vp_matrix_ms": round(vp, 0),
        "vs_matrix_ms": round(vs, 0),
    }


def compute_brittleness_index(mineral_fractions: dict[str, float]) -> float:
    """Compute brittleness index from mineralogy (Jarvie et al. 2007 / Rickman et al. 2008).

    BI = (quartz + calcite + dolomite) / (quartz + calcite + dolomite + clay + organic)

    Returns 0 (fully ductile) to 1 (fully brittle).
    """
    brittle = (
        mineral_fractions.get("quartz", 0.0)
        + mineral_fractions.get("calcite", 0.0)
        + mineral_fractions.get("dolomite", 0.0)
        + mineral_fractions.get("feldspar", 0.0)
    )
    ductile = brittle + mineral_fractions.get("clay", 0.0) + mineral_fractions.get("organic_matter", 0.0)

    if ductile < 0.001:
        return 0.5
    return round(brittle / ductile, 4)
