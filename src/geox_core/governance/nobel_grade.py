"""
geox_core.governance.nobel_grade — 6-Layer AGI Earth Intelligence
═══════════════════════════════════════════════════════════════════════

Implements the sovereign specification for Nobel-grade AGI Earth
Intelligence ratified 2026-05-25 by Arif Fazil (F13 SOVEREIGN).

Layers:
  1. Physics First, AI Second
  2. Uncertainty Is First-Class Citizen
  3. Anti-Hallucination Hard Lock
  4. Decision Firewall (888_HOLD)
  5. Multi-Discipline Reasoning
  6. Memory Panjang + Trauma Industri

Any GEOX tool missing any layer is a TOY, not a tool.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# Layer 1 — Physics First, AI Second
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class PhysicsViolation:
    constraint: str
    message: str
    expected: str
    actual: str
    severity: Literal["fatal", "warning"] = "fatal"


@dataclass
class PhysicsGuardResult:
    passed: bool
    violations: List[PhysicsViolation]
    fatal: bool


class PhysicsGuard:
    """
    Hard locks that auto-FAIL any result violating subsurface physics.
    These run BEFORE any AI narrative is emitted.
    """

    LOCKS: List[dict[str, Any]] = [
        {
            "name": "shale_porosity_depth",
            "severity": "fatal",
            "check": lambda p: _check_shale_porosity_depth(p),
        },
        {
            "name": "mass_balance",
            "severity": "fatal",
            "check": lambda p: _check_mass_balance(p),
        },
        {
            "name": "darcy_sanity",
            "severity": "warning",
            "check": lambda p: _check_darcy_sanity(p),
        },
        {
            "name": "pressure_gradient",
            "severity": "fatal",
            "check": lambda p: _check_pressure_gradient(p),
        },
        {
            "name": "capillary_limit",
            "severity": "warning",
            "check": lambda p: _check_capillary_limit(p),
        },
    ]

    def check(self, payload: Dict[str, Any]) -> PhysicsGuardResult:
        violations: List[PhysicsViolation] = []
        fatal = False
        for lock in self.LOCKS:
            v = lock["check"](payload)
            if v is not None:
                v.severity = lock["severity"]
                violations.append(v)
                if lock["severity"] == "fatal":
                    fatal = True
        return PhysicsGuardResult(passed=len(violations) == 0, violations=violations, fatal=fatal)


def _check_shale_porosity_depth(p: Dict[str, Any]) -> Optional[PhysicsViolation]:
    porosity = _extract_float(p, "porosity", "porosity_fraction", "phi")
    depth = _extract_float(p, "depth_m", "depth", "tvdss")
    if porosity is not None and depth is not None and depth > 3000:
        lith = _extract_str(p, "lithology", "rock_type", "lith")
        if lith and "shale" in lith.lower() and porosity > 0.25:
            return PhysicsViolation(
                constraint="shale_porosity_depth",
                message=f"Shale porosity {porosity * 100:.1f}% at {depth:.0f} m violates compaction physics.",
                expected="shale porosity ≤ 25% below 3000 m",
                actual=f"{porosity * 100:.1f}% at {depth:.0f} m",
            )
    return None


def _check_mass_balance(p: Dict[str, Any]) -> Optional[PhysicsViolation]:
    influx = _extract_float(p, "water_influx", "aquifer_influx")
    production = _extract_float(p, "cumulative_production", "prod_total")
    expansion = _extract_float(p, "fluid_expansion", "expansion")
    if influx is not None and production is not None and expansion is not None:
        imbalance = abs(influx + expansion - production)
        relative = imbalance / production if production > 0 else 0
        if relative > 0.15:
            return PhysicsViolation(
                constraint="mass_balance",
                message=f"Material balance imbalance {relative * 100:.1f}% exceeds 15% tolerance.",
                expected="imbalance ≤ 15%",
                actual=f"{relative * 100:.1f}%",
            )
    return None


def _check_darcy_sanity(p: Dict[str, Any]) -> Optional[PhysicsViolation]:
    perm = _extract_float(p, "permeability_md", "perm", "k")
    rate = _extract_float(p, "flow_rate_bpd", "rate", "q")
    if perm is not None and rate is not None:
        if perm < 0.001 and rate > 1000:
            return PhysicsViolation(
                constraint="darcy_sanity",
                message=f"Flow rate {rate:.0f} bpd incompatible with permeability {perm:.3f} md.",
                expected="Darcy flow regime consistent with permeability",
                actual=f"perm={perm:.3f} md, rate={rate:.0f} bpd",
            )
    return None


def _check_pressure_gradient(p: Dict[str, Any]) -> Optional[PhysicsViolation]:
    pressure = _extract_float(p, "pressure_psi", "pressure")
    depth = _extract_float(p, "depth_m", "depth", "tvdss")
    if pressure is not None and depth is not None and depth > 0:
        gradient_psi_per_ft = pressure / (depth * 3.28084)
        if gradient_psi_per_ft > 1.0:
            return PhysicsViolation(
                constraint="pressure_gradient",
                message=f"Pressure gradient {gradient_psi_per_ft:.2f} psi/ft exceeds lithostatic limit.",
                expected="≤ 1.0 psi/ft (lithostatic)",
                actual=f"{gradient_psi_per_ft:.2f} psi/ft",
            )
    return None


def _check_capillary_limit(p: Dict[str, Any]) -> Optional[PhysicsViolation]:
    sw = _extract_float(p, "sw", "water_saturation")
    porosity = _extract_float(p, "porosity", "phi")
    if sw is not None and porosity is not None:
        if sw < 0.05 and porosity < 0.1:
            return PhysicsViolation(
                constraint="capillary_limit",
                message=f"Sw {sw * 100:.1f}% in low-porosity rock {porosity * 100:.1f}% may violate capillary retention.",
                expected="Sw ≥ irreducible saturation for given pore geometry",
                actual=f"Sw={sw * 100:.1f}%, φ={porosity * 100:.1f}%",
                severity="warning",
            )
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 2 — Uncertainty Is First-Class Citizen
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class RiskKiller:
    rank: int
    description: str
    probability: float
    mitigation: Optional[str] = None


@dataclass
class UncertaintyBand:
    p10: float
    p50: float
    p90: float
    unit: str
    dependencies: List[str] = field(default_factory=list)
    killers: List[RiskKiller] = field(default_factory=list)


def create_uncertainty_band(base: float, unit: str, killers: List[RiskKiller]) -> UncertaintyBand:
    spread = base * 0.4
    return UncertaintyBand(
        p10=round(base + spread, 2),
        p50=round(base, 2),
        p90=round(base - spread * 0.65, 2),
        unit=unit,
        dependencies=[k.description for k in killers],
        killers=sorted(killers, key=lambda k: k.rank),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 3 — Anti-Hallucination Hard Lock
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class EvidenceCitation:
    source_type: Literal["well", "seismic", "core", "report", "model", "analogue"]
    source_id: str
    observation: str
    confidence: float
    page_or_depth: Optional[str] = None


def audit_hallucination(claims: List[str], citations: List[EvidenceCitation]) -> Tuple[bool, List[str]]:
    ungrounded: List[str] = []
    for claim in claims:
        grounded = any(claim.lower() in c.observation.lower() or c.observation.lower() in claim.lower() for c in citations)
        if not grounded:
            ungrounded.append(claim)
    return len(ungrounded) == 0, ungrounded


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 4 — Decision Firewall (888_HOLD)
# ═══════════════════════════════════════════════════════════════════════════════

HighRiskDomain = Literal[
    "drilling", "reserves_booking", "barrier_integrity", "well_design", "abandonment", "production_alteration"
]

HIGH_RISK_KEYWORDS: Dict[str, HighRiskDomain] = {
    "drill": "drilling",
    "drilling": "drilling",
    "reserves": "reserves_booking",
    "booking": "reserves_booking",
    "barrier": "barrier_integrity",
    "integrity": "barrier_integrity",
    "well_design": "well_design",
    "casing": "well_design",
    "abandonment": "abandonment",
    "plug": "abandonment",
    "production": "production_alteration",
    "choke": "production_alteration",
}


@dataclass
class HoldManifest:
    domain: HighRiskDomain
    known: List[str] = field(default_factory=list)
    unknown: List[str] = field(default_factory=list)
    dangerous_assumptions: List[str] = field(default_factory=list)
    signatory_required: str = "Registered Petroleum Engineer / Chief Geoscientist"
    ai_recommendation: Literal["WITNESS_ONLY", "CONDITIONAL", "HOLD"] = "WITNESS_ONLY"


def is_high_risk_domain(query: str) -> Optional[HighRiskDomain]:
    key = query.lower().strip().replace(" ", "_")
    return HIGH_RISK_KEYWORDS.get(key)


def build_hold_manifest(
    domain: HighRiskDomain,
    known: List[str],
    unknown: List[str],
    dangerous_assumptions: List[str],
) -> HoldManifest:
    return HoldManifest(
        domain=domain,
        known=known,
        unknown=unknown,
        dangerous_assumptions=dangerous_assumptions,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 5 — Multi-Discipline Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

Discipline = Literal["geology", "geomechanics", "drilling", "reservoir", "geophysics", "petrophysics"]


@dataclass
class DisciplineOpinion:
    discipline: Discipline
    claim: str
    confidence: float
    risk_flag: Literal["green", "yellow", "red"] = "green"


@dataclass
class DisciplinePanel:
    opinions: List[DisciplineOpinion]
    synthesis: str
    dominant_risk: Optional[Discipline] = None


def run_discipline_panel(opinions: List[DisciplineOpinion]) -> DisciplinePanel:
    reds = [o for o in opinions if o.risk_flag == "red"]
    yellows = [o for o in opinions if o.risk_flag == "yellow"]
    dominant: Optional[Discipline] = None
    if reds:
        dominant = reds[0].discipline
    elif yellows:
        dominant = yellows[0].discipline

    if reds:
        synthesis = f"Geologically attractive BUT {' + '.join(r.discipline for r in reds)} flags critical risk."
    elif yellows:
        synthesis = f"Attractive with operational caution from {' + '.join(y.discipline for y in yellows)}."
    else:
        synthesis = "All disciplines green. Proceed with standard diligence."

    return DisciplinePanel(
        opinions=sorted(opinions, key=lambda o: o.confidence, reverse=True),
        synthesis=synthesis,
        dominant_risk=dominant,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 6 — Trauma Memory (Industry Catastrophes)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class TraumaCase:
    name: str
    year: int
    basin: Optional[str]
    failure_mode: str
    root_cause: str
    lessons: List[str]
    similarity_tags: List[str]


TRAUMA_REGISTRY: List[TraumaCase] = [
    TraumaCase(
        name="Macondo",
        year=2010,
        basin="Gulf of Mexico",
        failure_mode="Blowout → uncontrolled release",
        root_cause="Barrier failure + cement job inadequacy + missed negative pressure test",
        lessons=[
            "Never rely on single barrier",
            "Negative pressure test is go/no-go",
            "Cement bond log must be interpreted, not just run",
        ],
        similarity_tags=["deepwater", "hpht", "cement", "bop", "barrier"],
    ),
    TraumaCase(
        name="Montara",
        year=2009,
        basin="Timor Sea",
        failure_mode="Blowout during completion",
        root_cause="Cement barrier failure + inadequate well monitoring",
        lessons=[
            "Subsea BOP must be functional before displacement",
            "Real-time pressure monitoring is non-negotiable",
        ],
        similarity_tags=["platform", "cement", "completion", "bop"],
    ),
    TraumaCase(
        name="Piper Alpha",
        year=1988,
        basin="North Sea",
        failure_mode="Gas explosion → platform collapse",
        root_cause="Maintenance deferred + permit-to-work system breakdown",
        lessons=[
            "Never defer safety-critical maintenance",
            "Permit-to-work must be live, not paperwork",
            "Temporary refuge must remain intact",
        ],
        similarity_tags=["platform", "maintenance", "permit", "safety", "gas"],
    ),
]


def scan_trauma(scenario_tags: List[str]) -> List[TraumaCase]:
    return [t for t in TRAUMA_REGISTRY if any(tag in scenario_tags for tag in t.similarity_tags)]


def format_trauma_warning(cases: List[TraumaCase]) -> str:
    if not cases:
        return ""
    lines = [f"WARNING: Similar to {c.name} ({c.year}, {c.basin or 'unknown basin'}) — {c.failure_mode}." for c in cases]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _extract_float(obj: Dict[str, Any], *keys: str) -> Optional[float]:
    for k in keys:
        v = obj.get(k)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                continue
    return None


def _extract_str(obj: Dict[str, Any], *keys: str) -> Optional[str]:
    for k in keys:
        v = obj.get(k)
        if isinstance(v, str):
            return v
    return None
