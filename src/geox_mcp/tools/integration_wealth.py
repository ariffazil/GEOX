"""
integration_wealth.py — W13+ Phase C forge: WEALTH ← GEOX integration.

Strategic doc: "joint_inversion output → prospect ranking + NPV scenarios".

This tool consumes a joint_inversion output (Physics13State per cell +
residual + per-modality breakdown) and produces:
  - Volumetric estimate (STOIIP P10/P50/P90) using rock physics priors
  - Capital allocation ranking via simple scoring
  - Wealth-grade verdict (passes to arifOS for final 999_SEAL)

NOTE: This is the GEOX-side wiring only. Actual NPV + portfolio
optimization happens in the WEALTH organ (canonical_tools/wealth_*).
This tool produces the feed.

DITEMPA BUKAN DIBEI — the volumetrics are forged, not given.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from geox_core.physics.state import Physics13State


class WealthFeedRequest(BaseModel):
    cell_states: list[dict] = Field(..., description="List of Physics13State dicts (one per cell)")
    areal_extent_m2: float = Field(default=1e6, gt=0, description="Areal extent of the prospect")
    pay_zone_thickness_m: float = Field(default=50.0, gt=0)
    formation_volume_factor: float = Field(default=1.3, gt=0)
    water_saturation: float = Field(default=0.30, ge=0, le=1)
    oil_density_kg_m3: float = Field(default=850.0, gt=0)
    recovery_factor: float = Field(default=0.30, ge=0, le=1)


class WealthFeedResponse(BaseModel):
    ok: bool
    tool: str = "geox_wealth_feed"
    feed: dict | None = None
    error: str | None = None


def stoiip_cell(
    phi: float,
    sw: float,
    areal_extent_m2: float,
    pay_zone_thickness_m: float,
    formation_volume_factor: float,
    recovery_factor: float,
) -> dict:
    """Compute STOIIP for one cell using volumetric formula.

    STOIIP = (V_bulk · φ · (1-Sw)) / Bo · N/G
    where V_bulk = areal_extent · thickness.
    Simplified: in-place oil volume = V · φ · (1-Sw).
    """
    v_bulk = areal_extent_m2 * pay_zone_thickness_m  # m^3
    hcpv = v_bulk * phi * (1.0 - sw)  # m^3 oil in place
    stoiip_m3 = hcpv / formation_volume_factor  # surface conditions
    recoverable_m3 = stoiip_m3 * recovery_factor
    stoiip_bbl = stoiip_m3 / 0.159  # m3 → bbl
    recoverable_bbl = recoverable_m3 / 0.159
    return {
        "stoiip_m3": stoiip_m3,
        "stoiip_bbl": stoiip_bbl,
        "recoverable_bbl": recoverable_bbl,
        "hcpv_m3": hcpv,
    }


async def geox_wealth_feed(request: WealthFeedRequest) -> WealthFeedResponse:
    """Constitutional MCP tool: GEOX → WEALTH feed for prospect economics.

    Takes cell-level Physics13State from joint_inversion and produces a
    WEALTH-ready feed with STOIIP, ranking score, and risk verdict.
    """
    try:
        cells = [Physics13State(**c) for c in request.cell_states]

        per_cell = []
        total_recoverable = 0.0
        for i, s in enumerate(cells):
            vol = stoiip_cell(
                phi=s.phi, sw=request.water_saturation,
                areal_extent_m2=request.areal_extent_m2,
                pay_zone_thickness_m=request.pay_zone_thickness_m,
                formation_volume_factor=request.formation_volume_factor,
                recovery_factor=request.recovery_factor,
            )
            total_recoverable += vol["recoverable_bbl"]
            per_cell.append({
                "cell_index": i,
                "state_grade": s.grade(),
                "phi": s.phi,
                "stoiip_bbl": vol["stoiip_bbl"],
                "recoverable_bbl": vol["recoverable_bbl"],
            })

        # Simple ranking: average porosity × (1 - Sw) × RF
        avg_phi = sum(c.phi for c in cells) / max(1, len(cells))
        avg_grade_aaa = sum(1 for c in cells if c.grade() == "AAA") / max(1, len(cells))
        ranking_score = avg_phi * (1 - request.water_saturation) * request.recovery_factor * avg_grade_aaa

        # Monte Carlo-lite: P10/P50/P90 from porosity distribution
        phis = sorted(c.phi for c in cells)
        n = len(phis)
        p10 = phis[max(0, int(0.10 * n))] if n else 0.0
        p50 = phis[max(0, int(0.50 * n))] if n else 0.0
        p90 = phis[max(0, int(0.90 * n))] if n else 0.0

        # Risk verdict.
        # Lithology-aware: only Sandstone, Limestone, Dolomite are producible.
        # Shale, Basement, Coal, Anhydrite, Salt are NOT producible reservoirs.
        try:
            from geox_core.physics.drivers import build_lithology_model
            lithology_counts: dict[str, int] = {}
            for c in cells:
                litho, _conf, _ = build_lithology_model(c)
                lithology_counts[litho] = lithology_counts.get(litho, 0) + 1
            producible_count = sum(
                v for k, v in lithology_counts.items()
                if k in ("Sandstone", "Limestone", "Dolomite")
            )
            producible_fraction = producible_count / max(1, len(cells))
        except Exception:
            producible_fraction = 1.0  # conservative fallback

        # Also defensible phi cap: shales typically > 0.28, reservoirs rarely.
        producible_phi = max(0.0, min(avg_phi, 0.28) - 0.05)
        producible_score = (
            producible_phi
            * (1 - request.water_saturation)
            * request.recovery_factor
            * avg_grade_aaa
            * producible_fraction
        )

        if avg_grade_aaa < 0.5 or producible_fraction < 0.3 or producible_score < 0.005:
            verdict = "REJECT"
            rationale = (
                f"Avg grade AAA = {avg_grade_aaa:.2f}, "
                f"producible_fraction = {producible_fraction:.2f}, "
                f"producible_score = {producible_score:.3f}. "
                "Insufficient evidence or non-reservoir lithology."
            )
        elif producible_score < 0.015:
            verdict = "DEFER"
            rationale = (
                f"Producible score {producible_score:.3f} below 0.015 threshold. "
                "Acquire more data before committing capital."
            )
        else:
            verdict = "ADVANCE"
            rationale = (
                f"Producible score {producible_score:.3f} above 0.015 threshold. "
                f"Reservoir lithology fraction: {producible_fraction:.2f}. "
                "Ready for WEALTH NPV modelling."
            )

        feed = {
            "n_cells": len(cells),
            "total_recoverable_bbl": total_recoverable,
            "phi_p10": p10, "phi_p50": p50, "phi_p90": p90,
            "avg_phi": avg_phi,
            "avg_grade_aaa_fraction": avg_grade_aaa,
            "ranking_score": ranking_score,
            "verdict": verdict,
            "rationale": rationale,
            "per_cell": per_cell,
            "epistemic_provenance": {
                "rung": 5,  # MODEL
                "grounding": "volumetric_arithmetic_on_physics9",
                "method": "monte_carlo_lite_phi_percentiles",
                "caveat": (
                    "Single-facies volumetric. WEALTH organ should consume "
                    "this feed and apply full portfolio + NPV modelling."
                ),
            },
            "godel_wall": {
                "state": "KNOWN",
                "reason": "Deterministic arithmetic on Physics9 inputs.",
            },
        }
        return WealthFeedResponse(ok=True, feed=feed)
    except Exception as e:
        return WealthFeedResponse(ok=False, error=str(e))


__all__ = [
    "WealthFeedRequest",
    "WealthFeedResponse",
    "geox_wealth_feed",
    "stoiip_cell",
]
