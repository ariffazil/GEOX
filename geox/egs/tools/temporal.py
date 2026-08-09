"""
temporal.py — EGS Temporal Intelligence MCP Tools
===================================================
GEOX EGS: Time-series analysis for production decline,
reserve replacement, basin lifecycle, and exploration cadence tracking.

All functions are pure computation — no network, no mutable state.
Registered as public surface tools: geox_temporal_decline, geox_temporal_rrr,
geox_temporal_basin_lifecycle, geox_temporal_cadence.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger("geox.egs.tools.temporal")


# ═══════════════════════════════════════════════════════════════════════════════
# Production Decline
# ═══════════════════════════════════════════════════════════════════════════════


async def temporal_decline(
    production_data: list[dict[str, Any]],
    forecast_years: int = 5,
    threshold_bpd: float = 250000.0,
) -> dict[str, Any]:
    """Fit exponential decline curve to production history and forecast.

    Algorithm: exponential decline D = -ln(Q_end/Q_start) / dt,
    forecast Q(t) = Q_current * exp(-D * t).

    OBS — Pure computation from provided data.
    INT — Decline rate interpretation depends on data quality.
    """
    if not production_data or len(production_data) < 2:
        return {
            "success": False,
            "error": "Need at least 2 data points for decline fit",
            "recoverable": True,
        }

    # Sort by year
    sorted_data = sorted(production_data, key=lambda d: d.get("year", 0))
    years = [d["year"] for d in sorted_data]
    rates = [d["bpd"] for d in sorted_data]

    current_rate = rates[-1]
    dt = years[-1] - years[0]

    if dt <= 0:
        return {
            "success": False,
            "error": "Time span must be positive",
            "recoverable": True,
        }

    rate_ratio = rates[-1] / rates[0] if rates[0] > 0 else 1.0
    if rate_ratio <= 0:
        return {
            "success": False,
            "error": "Invalid rate ratio (negative or zero rates)",
            "recoverable": True,
        }

    # Exponential decline constant
    if rate_ratio >= 1.0:
        # No decline — growth or flat
        d_const = 0.0
        decline_rate_pct = 0.0
        trend = "growth" if rate_ratio > 1.01 else "stable"
    else:
        d_const = -math.log(rate_ratio) / dt
        decline_rate_pct = round((1.0 - math.exp(-d_const)) * 100.0, 2)
        trend = "decline"

    # Forecast — project forward
    forecast = []
    for i in range(1, forecast_years + 1):
        forecast_year = years[-1] + i
        forecast_bpd = current_rate * math.exp(-d_const * i)
        forecast.append({"year": forecast_year, "bpd": round(max(0.0, forecast_bpd), 1)})

    # Years until production drops below threshold
    years_to_threshold: float | None
    if d_const > 0 and current_rate > threshold_bpd > 0:
        years_to_threshold = round(-math.log(threshold_bpd / current_rate) / d_const, 1)
    elif current_rate <= threshold_bpd:
        years_to_threshold = 0.0
    elif d_const == 0 and current_rate >= threshold_bpd:
        years_to_threshold = float("inf")
    else:
        years_to_threshold = None

    return {
        "success": True,
        "results": {
            "current_rate_bpd": current_rate,
            "decline_rate_pct_annual": decline_rate_pct,
            "trend": trend,
            "forecast": forecast,
            "forecast_years": forecast_years,
            "threshold_bpd": threshold_bpd,
            "years_to_threshold": years_to_threshold,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Reserve Replacement Ratio
# ═══════════════════════════════════════════════════════════════════════════════


async def temporal_rrr(
    reserves_start: float,
    additions: float,
    production: float,
) -> dict[str, Any]:
    """Compute Reserve Replacement Ratio (RRR).

    RRR = additions / production.
    RRR >= 1.0 = replacing (adding at or above production rate).
    RRR < 1.0  = consuming (producing faster than adding).

    DER — Derived from provided reserves data.
    INT — Interpretation depends on reserves classification standard.
    """
    if production <= 0:
        return {
            "success": False,
            "error": "Production must be positive",
            "recoverable": True,
        }

    rrr = additions / production

    if rrr >= 1.0:
        interpretation = "replacing"
    elif rrr >= 0.5:
        interpretation = "partial_replacement"
    else:
        interpretation = "consuming"

    reserves_end = reserves_start + additions - production

    years_at_current_rate: float | None
    if production > 0 and reserves_end > 0:
        years_at_current_rate = round(reserves_end / production, 1)
    elif reserves_end <= 0 and production > 0:
        years_at_current_rate = 0.0
    else:
        years_at_current_rate = None

    return {
        "success": True,
        "results": {
            "rrr_ratio": round(rrr, 4),
            "interpretation": interpretation,
            "reserves_start_mmbbl": reserves_start,
            "additions_mmbbl": additions,
            "production_mmbbl": production,
            "reserves_end_mmbbl": round(reserves_end, 2),
            "years_at_current_rate": years_at_current_rate,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Basin Lifecycle
# ═══════════════════════════════════════════════════════════════════════════════


async def temporal_basin_lifecycle(
    basin_name: str,
    peak_production: float,
    current_production: float,
    discovery_year: int,
    peak_year: int,
) -> dict[str, Any]:
    """Classify basin lifecycle stage from production history versus peak.

    Stage thresholds:
        growth   — current > peak (still growing, peak not yet reached)
        plateau  — current > 90% of peak
        decline  — current < 60% of peak
        mature   — current between 60% and 90% of peak

    INT — Lifecycle classification is an interpretation based on thresholds.
    OBS — Pure computation from provided parameters.
    """
    if peak_production <= 0:
        return {
            "success": False,
            "error": "Peak production must be positive",
            "recoverable": True,
        }
    if current_production < 0:
        return {
            "success": False,
            "error": "Current production cannot be negative",
            "recoverable": True,
        }

    ratio = current_production / peak_production
    remaining_potential_pct = round(ratio * 100.0, 1)
    decline_rate_pct = round(max(0.0, (1.0 - ratio) * 100.0), 1)

    if ratio > 1.0:
        stage = "growth"
    elif ratio > 0.9:
        stage = "plateau"
    elif ratio < 0.6:
        stage = "decline"
    else:
        stage = "mature"

    # Basin time-to-peak from discovery
    basin_age_to_peak: int | None = None
    if discovery_year > 0 and peak_year > 0 and peak_year >= discovery_year:
        basin_age_to_peak = peak_year - discovery_year

    # Years since peak — estimated from discovery if peak_year known
    years_since_peak: int | None = None
    if basin_age_to_peak is not None:
        # Use an inferred current age (peak_year + basin_age_to_peak as proxy)
        # Without an explicit current_year we estimate conservatively
        pass  # no current_year provided; omit

    return {
        "success": True,
        "results": {
            "basin_name": basin_name,
            "stage": stage,
            "remaining_potential_pct": remaining_potential_pct,
            "decline_rate_pct": decline_rate_pct,
            "peak_production": peak_production,
            "current_production": current_production,
            "discovery_year": discovery_year,
            "peak_year": peak_year,
            "basin_age_to_peak_years": basin_age_to_peak,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Exploration Cadence
# ═══════════════════════════════════════════════════════════════════════════════


async def temporal_cadence(
    blocks_offered: int,
    blocks_awarded: int,
    years_span: int,
    average_cycle_time_years: float,
) -> dict[str, Any]:
    """Analyse exploration licensing cadence and pipeline impact.

    Award rate: percentage of offered blocks that were awarded.
    Pipeline lag: average cycle time from award to production impact.
    Production impact: estimated year when awarded blocks reach production.

    DER — Derived from cadence inputs.
    INT — Pipeline lag and impact are interpreted estimates.
    """
    if blocks_offered <= 0:
        return {
            "success": False,
            "error": "blocks_offered must be positive",
            "recoverable": True,
        }
    if years_span <= 0:
        return {
            "success": False,
            "error": "years_span must be positive",
            "recoverable": True,
        }

    award_rate_pct = round((blocks_awarded / blocks_offered) * 100.0, 1)

    # Average blocks awarded per year
    avg_blocks_per_year = round(blocks_awarded / years_span, 2)

    # Pipeline lag is the average cycle time
    pipeline_lag_years = average_cycle_time_years

    # Production impact: from end of span, add cycle time
    production_impact_year = round(years_span + average_cycle_time_years, 1)

    # Capacity gap assessment
    if average_cycle_time_years <= 2:
        capacity_gap = "tight — rapid turnaround, minimal pipeline slack"
    elif average_cycle_time_years <= 5:
        capacity_gap = "moderate — normal exploration-to-production timeline"
    elif average_cycle_time_years <= 8:
        capacity_gap = "extended — significant lag, may require accelerated development"
    else:
        capacity_gap = "critical — excessive cycle time, systemic bottleneck risk"

    return {
        "success": True,
        "results": {
            "award_rate_pct": award_rate_pct,
            "blocks_offered": blocks_offered,
            "blocks_awarded": blocks_awarded,
            "avg_blocks_per_year": avg_blocks_per_year,
            "pipeline_lag_years": pipeline_lag_years,
            "production_impact_year": production_impact_year,
            "years_span": years_span,
            "capacity_gap_assessment": capacity_gap,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Registry
# ═══════════════════════════════════════════════════════════════════════════════


EGS_TEMPORAL_TOOLS: dict[str, dict[str, Any]] = {
    "geox_temporal_decline": {
        "description": (
            "Fit exponential decline curve to production history and forecast "
            "future rates. Computes decline rate, trend, and years-to-threshold."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "production_data": {
                    "type": "array",
                    "description": "List of {year, bpd} data points",
                    "items": {
                        "type": "object",
                        "properties": {
                            "year": {"type": "integer"},
                            "bpd": {"type": "number"},
                        },
                        "required": ["year", "bpd"],
                    },
                },
                "forecast_years": {
                    "type": "integer",
                    "description": "Number of years to forecast (default 5)",
                },
                "threshold_bpd": {
                    "type": "number",
                    "description": "Production threshold for crossing estimate (default 250000)",
                },
            },
            "required": ["production_data"],
            "additionalProperties": False,
        },
        "handler": temporal_decline,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "geox_temporal_rrr": {
        "description": (
            "Compute Reserve Replacement Ratio (RRR). RRR >= 1.0 means replacing; "
            "< 1.0 means consuming. Includes end-reserves and years-at-current-rate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reserves_start": {
                    "type": "number",
                    "description": "Starting reserves (MMbbl)",
                },
                "additions": {
                    "type": "number",
                    "description": "Reserve additions during period (MMbbl)",
                },
                "production": {
                    "type": "number",
                    "description": "Production during period (MMbbl)",
                },
            },
            "required": ["reserves_start", "additions", "production"],
            "additionalProperties": False,
        },
        "handler": temporal_rrr,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "geox_temporal_basin_lifecycle": {
        "description": (
            "Classify basin lifecycle: growth, plateau, decline, or mature. Thresholds based on current vs peak production ratio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "basin_name": {"type": "string", "description": "Name of the basin"},
                "peak_production": {
                    "type": "number",
                    "description": "Peak production rate (bpd or equivalent)",
                },
                "current_production": {
                    "type": "number",
                    "description": "Current production rate",
                },
                "discovery_year": {
                    "type": "integer",
                    "description": "Year of first discovery",
                },
                "peak_year": {
                    "type": "integer",
                    "description": "Year of peak production",
                },
            },
            "required": [
                "basin_name",
                "peak_production",
                "current_production",
                "discovery_year",
                "peak_year",
            ],
            "additionalProperties": False,
        },
        "handler": temporal_basin_lifecycle,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "geox_temporal_cadence": {
        "description": (
            "Analyse exploration licensing cadence: award rate, pipeline lag, production impact year, and capacity gap."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "blocks_offered": {
                    "type": "integer",
                    "description": "Number of blocks offered in licensing round",
                },
                "blocks_awarded": {
                    "type": "integer",
                    "description": "Number of blocks awarded",
                },
                "years_span": {
                    "type": "integer",
                    "description": "Time span of the licensing programme (years)",
                },
                "average_cycle_time_years": {
                    "type": "number",
                    "description": "Average years from award to first production",
                },
            },
            "required": [
                "blocks_offered",
                "blocks_awarded",
                "years_span",
                "average_cycle_time_years",
            ],
            "additionalProperties": False,
        },
        "handler": temporal_cadence,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
}


def register_temporal_tools(mcp: FastMCP) -> None:
    """Register EGS temporal tools with the FastMCP server."""
    for tool_name, tool_def in EGS_TEMPORAL_TOOLS.items():
        mcp.tool(name=tool_name, description=tool_def["description"])(tool_def["handler"])
        logger.info(f"Registered EGS temporal tool: {tool_name}")
