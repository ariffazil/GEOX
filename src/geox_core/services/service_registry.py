"""
geox_core/services/service_registry.py — P1 CRITICAL
DITEMPA BUKAN DIBERI — Internal plumbing is private, not public.

Maps every internal adapter to:
  1. Which library/package provides the computation
  2. Which canonical MCP tool(s) it backs
  3. Its ACRisk profile
  4. Whether it requires calibration (888_HOLD gate)

This is the INTERNAL registry. It NEVER crosses the membrane.
External agents see ONLY tools_manifest.py (domain-verb IDs).

MEMBRANE ENFORCEMENT:
  - Adapter names are INTERNAL_ONLY
  - Library names are INTERNAL_ONLY
  - Public contract is tools_manifest.py::DOMAIN_VERB_TOOLS
  - One-way mapping: internal → external is explicit, never auto-discovered

Version: 1.0.0 (locked 2026-06-26)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ─── Adapter Risk Profile ───────────────────────────────────────────────────────

class AdapterStatus:
    """Adapter lifecycle status."""
    EXPERIMENTAL = "EXPERIMENTAL"   # not yet validated; do not trust
    STABLE = "STABLE"               # validated; proceed with normal use
    DEPRECATED = "DEPRECATED"       # will be removed; migrate to replacement
    CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED"  # needs offset well or reference data


@dataclass(frozen=True)
class AdapterEntry:
    """
    One internal adapter in the service registry.

    Fields:
      adapter_name: Python module path, e.g. "geox_core.engines.geophysics.bruges_adapter"
      library_name: The underlying library, e.g. "bruges", "harmonica", "devito"
      library_version: Minimum required version string
      canonical_tools: Which canonical MCP tool(s) this adapter contributes to
      status: EXPERIMENTAL | STABLE | DEPRECATED | CALIBRATION_REQUIRED
      acrisk: QUALIFY | ADVISORY | HOLD | BLOCK
      requires_888_hold: True if Arif must release before autonomous use
      calibration_notes: What calibration data is needed (if CALIBRATION_REQUIRED)
      replaces: Adapter this replaces (if DEPRECATED)
      replaced_by: Adapter that replaces this (if DEPRECATED)
    """
    adapter_name: str
    library_name: str
    library_version: str
    canonical_tools: list[str]
    status: str
    acrisk: str
    requires_888_hold: bool = False
    calibration_notes: str = ""
    replaces: str = ""
    replaced_by: str = ""


# ─── Service Registry ──────────────────────────────────────────────────────────

SERVICE_REGISTRY: dict[str, AdapterEntry] = {

    # ══════════════════════════════════════════════════════════════════════════════
    # PETROPHYSICS — bruges_adapter
    # ══════════════════════════════════════════════════════════════════════════════

    "bruges_adapter": AdapterEntry(
        adapter_name="geox_core.engines.petrophysics.bruges_adapter",
        library_name="bruges",
        library_version=">=0.4.0",
        canonical_tools=["geox_petrophysics", "geox_geomechanics", "geox_seismic_compute"],
        status=AdapterStatus.STABLE,
        acrisk="QUALIFY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    # ══════════════════════════════════════════════════════════════════════════════
    # SEISMIC — devito_adapter, pylops_adapter, pygeopressure_adapter
    # ══════════════════════════════════════════════════════════════════════════════

    "devito_adapter": AdapterEntry(
        adapter_name="geox_core.engines.seismic.devito_adapter",
        library_name="devito",
        library_version=">=4.0",
        canonical_tools=["geox_seismic_compute"],
        status=AdapterStatus.STABLE,
        acrisk="QUALIFY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    "pylops_adapter": AdapterEntry(
        adapter_name="geox_core.engines.seismic.pylops_adapter",
        library_name="pylops",
        library_version=">=2.0",
        canonical_tools=["geox_seismic_compute", "geox_seismic_interpret"],
        status=AdapterStatus.STABLE,
        acrisk="QUALIFY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    "pygeopressure_adapter": AdapterEntry(
        adapter_name="geox_core.engines.seismic.pygeopressure_adapter",
        library_name="pygeopressure",
        library_version=">=0.4.0",
        canonical_tools=["geox_subsurface_model"],
        status=AdapterStatus.CALIBRATION_REQUIRED,
        acrisk="HOLD",
        requires_888_hold=True,
        calibration_notes=(
            "⚠️ 888_HOLD GATE: Eaton/Bowers pore pressure requires calibration against "
            "offset wells (MDT/RCI or repeat formation tester data). "
            "Do NOT use for drill planning without Arif release. "
            "Required: at least 2 offset wells with measured pore pressures in same basin."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════════════
    # GEOPHYSICS — harmonica_adapter, simpeg_adapter, pygimli_adapter, igrf_adapter
    # ══════════════════════════════════════════════════════════════════════════════

    "harmonica_adapter": AdapterEntry(
        adapter_name="geox_core.engines.geophysics.harmonica_adapter",
        library_name="harmonica",
        library_version=">=0.4.0",
        canonical_tools=["geox_subsurface_model", "geox_basin"],
        status=AdapterStatus.STABLE,
        acrisk="QUALIFY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    "simpeg_adapter": AdapterEntry(
        adapter_name="geox_core.engines.geophysics.simpeg_adapter",
        library_name="simpeg",
        library_version=">=0.6.0",
        canonical_tools=["geox_subsurface_model"],
        status=AdapterStatus.CALIBRATION_REQUIRED,
        acrisk="HOLD",
        requires_888_hold=True,
        calibration_notes=(
            "⚠️ 888_HOLD GATE on MT→pore pressure path: SimPEG MT 1D inversion "
            "produces resistivity models that can be converted to pore pressure via "
            "Archie-equivalent transforms — but these transforms are uncalibrated "
            "for frontier basins. Requires Arif release before MT results are used "
            "in drill planning or pore pressure prediction."
        ),
    ),

    "pygimli_adapter": AdapterEntry(
        adapter_name="geox_core.engines.geophysics.pygimli_adapter",
        library_name="pygimli",
        library_version=">=1.4",
        canonical_tools=["geox_subsurface_model"],
        status=AdapterStatus.STABLE,
        acrisk="QUALIFY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    "igrf_adapter": AdapterEntry(
        adapter_name="geox_core.engines.geophysics.igrf_adapter",
        library_name="ppigrf",
        library_version=">=2024.0",
        canonical_tools=["geox_basin", "geox_subsurface_model"],
        status=AdapterStatus.STABLE,
        acrisk="QUALIFY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    # ══════════════════════════════════════════════════════════════════════════════
    # GEOSPATIAL — gplately_adapter, gplates_ws_adapter, gempy_adapter, loopstructural_adapter
    # ══════════════════════════════════════════════════════════════════════════════

    "gplately_adapter": AdapterEntry(
        adapter_name="geox_core.engines.geospatial.gplately_adapter",
        library_name="gplately",
        library_version=">=2.0.0",
        canonical_tools=["geox_basin", "geox_deep_time_state"],
        status=AdapterStatus.STABLE,
        acrisk="QUALIFY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    "gplates_ws_adapter": AdapterEntry(
        adapter_name="geox_core.engines.geospatial.gplates_ws_adapter",
        library_name="gwspy",
        library_version=">=2.0.0",
        canonical_tools=["geox_basin", "geox_deep_time_state"],
        status=AdapterStatus.EXPERIMENTAL,
        acrisk="ADVISORY",
        requires_888_hold=False,
        calibration_notes=(
            "REST fallback when pyGPlates unavailable. "
            "Rate-limited to ~100 req/min on gws.gplates.org. "
            "Use for single-point reconstruction only."
        ),
    ),

    "gempy_adapter": AdapterEntry(
        adapter_name="geox_core.engines.geospatial.gempy_adapter",
        library_name="gempy",
        library_version=">=2.0",
        canonical_tools=["geox_subsurface_model", "geox_basin"],
        status=AdapterStatus.STABLE,
        acrisk="ADVISORY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    "loopstructural_adapter": AdapterEntry(
        adapter_name="geox_core.engines.geospatial.loopstructural_adapter",
        library_name="loopstructural",
        library_version=">=1.0",
        canonical_tools=["geox_subsurface_model"],
        status=AdapterStatus.EXPERIMENTAL,
        acrisk="ADVISORY",
        requires_888_hold=False,
        calibration_notes="",
    ),

    # ══════════════════════════════════════════════════════════════════════════════
    # HYDROGEOLOGY — flopy_adapter
    # ══════════════════════════════════════════════════════════════════════════════

    "flopy_adapter": AdapterEntry(
        adapter_name="geox_core.engines.hydrogeology.flopy_adapter",
        library_name="flopy",
        library_version=">=3.0",
        canonical_tools=["geox_subsurface_model"],
        status=AdapterStatus.STABLE,
        acrisk="QUALIFY",
        requires_888_hold=False,
        calibration_notes="",
    ),
}


# ─── Lookup Helpers ─────────────────────────────────────────────────────────────

def get_adapter_entry(adapter_name: str) -> AdapterEntry | None:
    """Look up an adapter by name."""
    return SERVICE_REGISTRY.get(adapter_name)


def get_adapter_library_version(adapter_name: str) -> str:
    """Get the required library version for an adapter."""
    entry = SERVICE_REGISTRY.get(adapter_name)
    return entry.library_version if entry else ""


def get_adapters_for_tool(mcp_tool_name: str) -> list[AdapterEntry]:
    """Return all adapters that contribute to a canonical MCP tool."""
    return [
        entry for entry in SERVICE_REGISTRY.values()
        if mcp_tool_name in entry.canonical_tools
    ]


def get_888_hold_adapters() -> list[str]:
    """Return all adapter names that require Arif release."""
    return [
        name for name, entry in SERVICE_REGISTRY.items()
        if entry.requires_888_hold
    ]


def get_calibration_required_adapters() -> list[str]:
    """Return all adapter names that need calibration data."""
    return [
        name for name, entry in SERVICE_REGISTRY.items()
        if entry.status == AdapterStatus.CALIBRATION_REQUIRED
    ]


def get_unstable_adapters() -> list[str]:
    """Return adapter names that are EXPERIMENTAL or DEPRECATED."""
    return [
        name for name, entry in SERVICE_REGISTRY.items()
        if entry.status in (AdapterStatus.EXPERIMENTAL, AdapterStatus.DEPRECATED)
    ]


def check_adapter_conflicts(new_adapter: str, old_adapter: str) -> bool:
    """
    Check if new_adapter replaces old_adapter (no overlap in canonical tools).

    Returns True if replacement is clean (no shared canonical tools).
    Returns False if there is an overlap — investigate before replacing.
    """
    new_entry = SERVICE_REGISTRY.get(new_adapter)
    old_entry = SERVICE_REGISTRY.get(old_adapter)
    if not new_entry or not old_entry:
        return True
    return len(set(new_entry.canonical_tools) & set(old_entry.canonical_tools)) == 0


# ─── Version Lock ─────────────────────────────────────────────────────────────

SERVICE_REGISTRY_VERSION = "1.0.0"
SERVICE_REGISTRY_EPOCH = "2026-06-26"
SERVICE_REGISTRY_STATUS = "LOCKED"

"""
Version history:
  1.0.0 (2026-06-26) — Initial locked registry.
                          14 adapters across 6 domains.
                          888_HOLD gates on pygeopressure and SimPEG MT paths.

DITEMPA BUKAN DIBERI — Internal adapters are private plumbing.
The membrane is enforced by tools_manifest.py (external) and this
registry (internal). Never expose adapter names to external agents.
"""
