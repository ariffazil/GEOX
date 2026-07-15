"""
geox_collision_zone — Two Oceanics Physics Engine
══════════════════════════════════════════════════
Implements collision zone physics from Arif's Sabah Eureka Ledger v1.0.

A collision zone is two lithospheric blocks with different subsidence physics:
  Domain A — loaded accretionary wedge (Kinabalu-type, 4.25x loading ratio)
  Domain B — thermally-decaying rifted margin (Dangerous Grounds-type)

The suture (e.g., Sabah Trough) is where Domain A's missing 60% mass goes.

Core metrics:
  accommodation_ratio = domain_a_accommodation / domain_b_accommodation
  loading_ratio = loading_subsidence_m / thermal_subsidence_m
  mass_deficit_pct = (predicted - observed) / predicted * 100
  bypass_fraction = mass_routed_to_suture / total_mass

Eureka signatures detected:
  EUREKA_1_TWO_OCEANICS — accommodation_ratio >= 2.5
  EUREKA_1_MFS_ASYMMETRY — MFS present in A, absent in B
  EUREKA_2_LOADING_PULSE — loading_ratio >= 3.0
  EUREKA_4_MASS_DEFICIT — mass_deficit >= 50%
  EUREKA_4_SUTURE_SINK — bypass_fraction >= 0.5
  EUREKA_11_PROSPECT_BIFURCATION — Domain A risk != Domain B risk

F2 TRUTH: All metrics DERIVED from physics simulation, not direct measurement.
F7 HUMILITY: Confidence capped at 0.90.
DITEMPA BUKAN DIBERI — Forged from Sabah Eureka Ledger 2026-07-10.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BlockParams:
    name: str
    initial_subsidence_km: float = 2.0
    loading_rate_m_myr: float = 50.0
    thermal_rate_mm_yr: float = 0.05
    sediment_supply_m_myr: float = 50.0
    initial_water_depth_m: float = 100.0
    has_mfs: bool = False
    source_rock_mature: bool = True
    domain_type: str = "accretionary"


@dataclass
class CollisionResult:
    accommodation_ratio: float = 0.0
    loading_ratio: float = 0.0
    mass_deficit_pct: float = 0.0
    bypass_fraction: float = 0.0
    total_accommodation_a_m: float = 0.0
    total_accommodation_b_m: float = 0.0
    loading_subsidence_m: float = 0.0
    thermal_subsidence_m: float = 0.0
    mfs_asymmetry: bool = False
    collision_signature: str = "UNKNOWN"
    prospect_domain_a: str = "UNEVALUATED"
    prospect_domain_b: str = "UNEVALUATED"
    eureka_flags: list[str] = field(default_factory=list)


def _accommodation(b: BlockParams, dur_ma: float) -> tuple[float, float, float]:
    """(total_m, loading_m, thermal_m)"""
    loading_m = b.loading_rate_m_myr * dur_ma * (1 + b.initial_subsidence_km / 5.0)
    thermal_m = b.thermal_rate_mm_yr * math.sqrt(dur_ma) * 1000.0
    total_m = b.initial_subsidence_km * 1000.0 + loading_m + thermal_m + b.initial_water_depth_m
    return total_m, loading_m, thermal_m


def _mass(b: BlockParams, dur_ma: float, bypass: float) -> tuple[float, float]:
    """(predicted, observed)"""
    pred = b.sediment_supply_m_myr * dur_ma
    obs = pred * (1.0 - bypass)
    return pred, obs


def _signature(ar: float, lr: float) -> str:
    if ar > 2.0 and lr > 2.0:
        return "LOADING_DOMINANT"
    if ar < 0.5:
        return "THERMAL_DOMINANT"
    return "BALANCED" if 0.5 <= ar <= 2.0 else "UNKNOWN"


def _bifurcate(r: CollisionResult, a: BlockParams, b: BlockParams) -> tuple[str, str]:
    da = "FAVORABLE" if (a.source_rock_mature and r.loading_ratio > 1.0) else "CAUTION" if a.source_rock_mature else "UNFAVORABLE"
    db = "FAVORABLE" if (b.source_rock_mature and r.loading_ratio > 2.0) else "CAUTION" if b.source_rock_mature else "UNFAVORABLE"
    return da, db


def _eurekas(r: CollisionResult) -> list[str]:
    f = []
    if r.accommodation_ratio >= 2.5:
        f.append("EUREKA_1_TWO_OCEANICS")
    if r.mfs_asymmetry:
        f.append("EUREKA_1_MFS_ASYMMETRY")
    if r.loading_ratio >= 3.0:
        f.append("EUREKA_2_LOADING_PULSE")
    if r.mass_deficit_pct >= 50:
        f.append("EUREKA_4_MASS_DEFICIT")
    if r.bypass_fraction >= 0.5:
        f.append("EUREKA_4_SUTURE_SINK")
    if r.prospect_domain_a != r.prospect_domain_b:
        f.append("EUREKA_11_PROSPECT_BIFURCATION")
    return f


def compute_collision(
    domain_a: dict[str, Any],
    domain_b: dict[str, Any],
    suture_name: str = "Suture",
    duration_ma: float = 15.0,
    bypass_fraction: float = 0.0,
) -> dict[str, Any]:
    """Compute Two Oceanics collision zone metrics."""
    a = BlockParams(
        name=domain_a.get("name", "Domain A"),
        initial_subsidence_km=domain_a.get("initial_subsidence_km", 4.0),
        loading_rate_m_myr=domain_a.get("loading_rate_m_myr", 400.0),
        thermal_rate_mm_yr=domain_a.get("thermal_rate_mm_yr", 0.05),
        sediment_supply_m_myr=domain_a.get("sediment_supply_m_myr", 100.0),
        initial_water_depth_m=domain_a.get("initial_water_depth_m", 500.0),
        has_mfs=domain_a.get("has_mfs", True),
        source_rock_mature=domain_a.get("source_rock_mature", True),
        domain_type="accretionary",
    )
    b = BlockParams(
        name=domain_b.get("name", "Domain B"),
        initial_subsidence_km=domain_b.get("initial_subsidence_km", 2.0),
        loading_rate_m_myr=domain_b.get("loading_rate_m_myr", 50.0),
        thermal_rate_mm_yr=domain_b.get("thermal_rate_mm_yr", 0.20),
        sediment_supply_m_myr=domain_b.get("sediment_supply_m_myr", 10.0),
        initial_water_depth_m=domain_b.get("initial_water_depth_m", 2000.0),
        has_mfs=domain_b.get("has_mfs", False),
        source_rock_mature=domain_b.get("source_rock_mature", False),
        domain_type="rifted",
    )

    acc_a, load_a, therm_a = _accommodation(a, duration_ma)
    acc_b, load_b, therm_b = _accommodation(b, duration_ma)

    pred_a, obs_a = _mass(a, duration_ma, bypass_fraction)
    pred_b, obs_b = _mass(b, duration_ma, 0.0)

    r = CollisionResult(
        accommodation_ratio=round(acc_a / acc_b, 2) if acc_b > 0 else float("inf"),
        loading_ratio=round(load_a / therm_b, 2) if therm_b > 0 else float("inf"),
        mass_deficit_pct=round(((pred_a + pred_b - obs_a - obs_b) / (pred_a + pred_b)) * 100, 1)
        if (pred_a + pred_b) > 0
        else 0.0,
        bypass_fraction=round(bypass_fraction, 3),
        total_accommodation_a_m=round(acc_a),
        total_accommodation_b_m=round(acc_b),
        loading_subsidence_m=round(load_a),
        thermal_subsidence_m=round(therm_b),
        mfs_asymmetry=a.has_mfs != b.has_mfs,
    )
    r.collision_signature = _signature(r.accommodation_ratio, r.loading_ratio)
    r.prospect_domain_a, r.prospect_domain_b = _bifurcate(r, a, b)
    r.eureka_flags = _eurekas(r)

    return {
        "verdict": "SEAL",
        "collision_zone": {
            "suture_name": suture_name,
            "duration_ma": duration_ma,
            "domain_a": {
                "name": a.name,
                "type": a.domain_type,
                "accommodation_m": r.total_accommodation_a_m,
                "loading_subsidence_m": r.loading_subsidence_m,
                "thermal_subsidence_m": round(therm_a),
            },
            "domain_b": {
                "name": b.name,
                "type": b.domain_type,
                "accommodation_m": r.total_accommodation_b_m,
                "thermal_subsidence_m": r.thermal_subsidence_m,
            },
        },
        "metrics": {
            "accommodation_ratio": r.accommodation_ratio,
            "loading_ratio": r.loading_ratio,
            "mass_deficit_pct": r.mass_deficit_pct,
            "bypass_fraction": r.bypass_fraction,
            "mfs_asymmetry": r.mfs_asymmetry,
            "collision_signature": r.collision_signature,
        },
        "prospect_bifurcation": {
            "domain_a_risk": r.prospect_domain_a,
            "domain_b_risk": r.prospect_domain_b,
        },
        "eureka_flags": r.eureka_flags,
        "margin_principle": {
            "statement": "Everything happens at the margins. The interior only records. Unconformities are made at margins.",
            "suture_note": f"The {suture_name} is not a bathymetric feature — it is the suture where Domain A's missing mass is deposited.",
        },
        "_meta": {
            "evidence_class": "DERIVED",
            "confidence_cap": 0.90,
            "physics": "McKenzie 1978 thermal + Airy loading isostasy",
            "governance": "EVIDENCE_ONLY — GEOX computes, arifOS judges, Arif decides.",
        },
    }


def compute_collision_chronology(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute collision duration from event sequence."""
    if not events:
        return {"verdict": "HOLD", "duration_ma": 0, "error": "No events"}
    ages = [e["age_ma"] for e in events if e.get("age_ma") is not None]
    if not ages:
        return {"verdict": "HOLD", "duration_ma": 0, "error": "No valid ages"}
    ages_s = sorted(ages, reverse=True)
    return {
        "verdict": "SEAL",
        "duration_ma": round(ages_s[0] - ages_s[-1], 1),
        "oldest_ma": ages_s[0],
        "youngest_ma": ages_s[-1],
        "n_events": len(events),
        "events": sorted(events, key=lambda e: e.get("age_ma", 0), reverse=True),
        "note": "The collision is not an event. It is a 15 Myr sequence, still finishing.",
        "_meta": {"evidence_class": "INTERPRETED", "confidence_cap": 0.85},
    }
