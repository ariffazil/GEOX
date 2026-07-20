"""
geox_crustal_domain_classify — Multi-cell crustal domain classifier
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBEI — Forged, Not Given

Stage 6 forge: Kinabalu Basin Phase I Deliverable 1 (Crustal Domain Map) substrate.

This module provides the multi-cell crustal-domain classifier that takes a set
of crust-anchor observations (Vp + crust thickness + heat flow + depth) across
a region and produces a contiguous crust-domain map.

Constitutional binding:
  F1  AMANAH    — Reversible: outputs are Pydantic models, no live mutation.
  F2  TRUTH     — Per-cell classifications are DER-grade; multi-cell maps are
                  INT-grade (interpretation). Provenance preserved.
  F4  CLARITY   — Inputs/outputs are Pydantic-strict. No extra fields.
  F7  HUMILITY  — Per-cell confidence hard-capped at 0.90.
  F8  LAW       — Domain naming must use canonical CrustZone enum.
  F9  ANTI-HANTU— No generative claims. Output is purely descriptive.
  F11 AUDIT     — Full audit_receipt in result.
  F13 SOVEREIGN — Domain BOUNDARY classification is sovereign; this tool
                  produces SUBSTRATE classifications only.

REFERENCE:
  Huang et al. (2021) — Tectonics — Seismic Imaging of an Intracrustal
  Deformation in the Northwestern Margin of the South China Sea
  (the Vp grammar that powers this tool).

USAGE:
  from geox_mcp.tools.crustal_domain_classify import (
      geox_crustal_domain_classify,
      CrustDomainRequest,
  )

  request = CrustDomainRequest(
      basin_name="Layang-Layang",
      cells=[
          CrustCellObservation(vp_km_s=5.5, depth_km=2.0, crust_thickness_km=22.0),
          CrustCellObservation(vp_km_s=5.9, depth_km=9.0, crust_thickness_km=10.0),
          ...
      ],
  )
  result = await geox_crustal_domain_classify(request)

STATUS:
  This module is forged as a forge_work preview. **Registry promotion
  (addition to CANONICAL_PUBLIC_TOOLS) requires 888_HOLD per GEOX AGENTS.md.
  The tool can be imported and used directly without registry promotion.**

888_HOLD PACKET:
  See forge_work/2026-06-22-888-hold-crustal-domain-classify.md
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from geox_core.schemas.crust_vp_grammar import (
    CrustClassification,
    CrustZone,
    vp_zone_classify,
)

logger = logging.getLogger("geox.crustal_domain")


# ═══════════════════════════════════════════════════════════════════════════════
# F4 CLARITY — Pydantic envelope schemas
# ═══════════════════════════════════════════════════════════════════════════════


class CrustCellObservation(BaseModel):
    """One crust-anchor observation at one (lat, lon, depth) cell.

    F2 TRUTH: this is OBS-grade data. Source must be declared.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        str_strip_whitespace=True,
    )

    # Spatial anchor (optional but recommended)
    lat: float | None = Field(default=None, ge=-90.0, le=90.0, description="Latitude (WGS84).")
    lon: float | None = Field(default=None, ge=-180.0, le=180.0, description="Longitude (WGS84).")
    # Vp at this cell
    vp_km_s: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="P-wave velocity at the cell (km/s).",
    )
    depth_km: float = Field(
        default=0.0,
        ge=0.0,
        le=50.0,
        description="Depth below sea level (km).",
    )
    # Optional crust-scale context
    crust_thickness_km: float | None = Field(
        default=None,
        ge=0.0,
        le=50.0,
        description="Local crust thickness (km). If None, classifier uses depth only.",
    )
    heat_flow_mw_m2: float | None = Field(
        default=None,
        ge=0.0,
        le=200.0,
        description="Surface heat flow (mW/m²). Used for serpentinization diagnostic.",
    )
    # Provenance
    source: str = Field(
        default="unknown",
        min_length=1,
        description="Source provenance: OBS, refraction, MCS stacking, etc.",
    )
    method: str = Field(
        default="unknown",
        min_length=1,
        description="Method: wide-angle, joint inversion, velocity-from-stacking.",
    )
    uncertainty_km_s: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="1σ uncertainty in Vp (km/s). Huang 2021 = ±0.3.",
    )
    cell_id: str | None = Field(
        default=None,
        description="Optional cell identifier for cross-reference.",
    )


class CrustDomainRequest(BaseModel):
    """A multi-cell crust-domain classification request.

    F4 CLARITY: at least one cell observation required.
    """

    model_config = ConfigDict(extra="forbid")

    basin_name: str = Field(
        ...,
        min_length=1,
        description="Target basin name (e.g. 'Layang-Layang').",
    )
    cells: list[CrustCellObservation] = Field(
        ...,
        min_length=1,
        description="List of cell observations across the region.",
    )
    include_diagnostics: bool = Field(
        default=False,
        description="If True, include full diagnostic_basis per cell.",
    )


class CrustDomainCellResult(BaseModel):
    """One cell's classification result."""

    model_config = ConfigDict(extra="forbid")

    cell_id: str | None = None
    lat: float | None = None
    lon: float | None = None
    depth_km: float
    vp_km_s: float
    crust_zone: CrustZone
    confidence: float = Field(..., ge=0.0, le=0.90)  # F7
    alternative_zones: list[CrustZone] = Field(default_factory=list)
    diagnostic_basis: list[str] = Field(default_factory=list)
    evidence_rank: str
    source: str


class CrustDomainMap(BaseModel):
    """Multi-cell crust-domain map result.

    F4 CLARITY: contains the full classification grid + audit trail.
    F11 AUDIT: includes provenance hash, timestamp, source_paper.
    """

    model_config = ConfigDict(extra="forbid")

    basin_name: str
    cell_count: int = Field(..., ge=1)
    cells: list[CrustDomainCellResult]
    zone_distribution: dict[str, int] = Field(
        ...,
        description="Count of cells per crust zone (for quick overview).",
    )
    # Audit trail
    observation_hash: str = Field(
        ...,
        description="SHA-256 of sorted cell inputs (F1 AMANAH).",
    )
    generated_at: str
    source_paper: str = Field(default="Huang et al. (2021) — Tectonics")
    sovereignty_note: str = Field(
        default=(
            "Domain BOUNDARIES are sovereign territory (F13). "
            "This map classifies each cell individually; "
            "region-level domain boundary inference requires 888_HOLD."
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helper — compute observation hash for F11 AUDIT
# ═══════════════════════════════════════════════════════════════════════════════


def _observation_hash(cells: list[CrustCellObservation]) -> str:
    """SHA-256 of sorted cell inputs. F1 AMANAH — content-addressed audit."""
    payload = repr(
        sorted(
            (
                c.cell_id or "",
                round(c.vp_km_s, 6),
                round(c.depth_km, 6),
                c.crust_thickness_km,
                c.heat_flow_mw_m2,
                c.source,
                c.method,
            )
            for c in cells
        )
    ).encode()
    return f"sha256:{hashlib.sha256(payload).hexdigest()[:16]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Core classification function
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_crustal_domain_classify(
    request: CrustDomainRequest,
) -> CrustDomainMap:
    """Classify each cell's crust domain from Vp observations.

    Pure async function (no side effects, no live mutation).
    Returns a CrustDomainMap with per-cell classifications, zone distribution,
    observation hash, and provenance.

    Constitutional note:
      - This tool classifies INDIVIDUAL CELLS.
      - It does NOT infer region-level domain BOUNDARIES (that's sovereign).
      - The user can post-process zone_distribution to draw boundaries manually,
        but those boundaries must be ratified by Arif (F13).

    F13 SOVEREIGN safety:
      - We deliberately do NOT collapse cells into "domains" automatically.
      - We provide the substrate (per-cell zones + distribution).
      - The team can then mark boundaries with sovereign authority.
    """
    cell_results: list[CrustDomainCellResult] = []
    zone_counts: dict[str, int] = {}

    for cell in request.cells:
        # F2 TRUTH — call the canonical Vp grammar
        classification: CrustClassification = vp_zone_classify(
            vp_km_s=cell.vp_km_s,
            crust_thickness_km=cell.crust_thickness_km,
            depth_km=cell.depth_km,
            heat_flow_mw_m2=cell.heat_flow_mw_m2,
        )

        # F4 CLARITY — build the result envelope
        result = CrustDomainCellResult(
            cell_id=cell.cell_id,
            lat=cell.lat,
            lon=cell.lon,
            depth_km=cell.depth_km,
            vp_km_s=cell.vp_km_s,
            crust_zone=classification.zone,
            confidence=classification.confidence,
            alternative_zones=classification.alternative_zones,
            diagnostic_basis=(classification.diagnostic_basis if request.include_diagnostics else []),
            evidence_rank=classification.evidence_rank,
            source=cell.source,
        )
        cell_results.append(result)

        # Distribution
        z = classification.zone.value
        zone_counts[z] = zone_counts.get(z, 0) + 1

    # F1 AMANAH — content-addressed audit
    obs_hash = _observation_hash(request.cells)

    return CrustDomainMap(
        basin_name=request.basin_name,
        cell_count=len(cell_results),
        cells=cell_results,
        zone_distribution=zone_counts,
        observation_hash=obs_hash,
        generated_at=datetime.now(UTC).isoformat(),
    )


__all__ = [
    "CrustCellObservation",
    "CrustDomainRequest",
    "CrustDomainCellResult",
    "CrustDomainMap",
    "geox_crustal_domain_classify",
]
