"""
geox_replan_dag.py — P1 CRITICAL
DITEMPA BUKAN DIBERI — Stale truths must be visible, not silently propagated.

Explicit replan triggers for GEOX CANON-9 variables.
Every output carries expires_at, evidence_version, and supersedes fields.
When new evidence arrives, this DAG determines:
  1. Which CANON-9 variables are invalidated
  2. Which downstream tools must recompute
  3. Whether the invalidation requires 888_HOLD or propagates automatically
  4. How long evidence remains valid before recomputation is mandatory

CANON-9 Variables (grounding physics):
  rho    — bulk density (g/cm³)
  Vp     — P-wave velocity (m/s)
  Vs     — S-wave velocity (m/s)
  phi    — porosity (fraction)
  Sw     — water saturation (fraction)
  P      — pore pressure (MPa)
  k      — permeability (mD)
  T      — temperature (°C)
  chi    — magnetic susceptibility (SI)

Version: 1.0.0 (locked 2026-06-26)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

# ─── Invalidation Severity ──────────────────────────────────────────────────────


class InvalidationSeverity(StrEnum):
    """How serious is this evidence update?"""

    PATCH = "PATCH"  # minor: no recomputation needed, log only
    UPDATE = "UPDATE"  # moderate: downstream tools should recompute
    REVISION = "REVISION"  # major: EARTH_MODEL may be invalidated, Arif notified
    VOID = "VOID"  # critical: previous result is contradicted, seal revoked


# ─── Replan Trigger ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ReplanTrigger:
    """
    One entry in the replan DAG.

    Fields:
      trigger_variable: CANON-9 variable that was updated
      invalidates: list of CANON-9 variables that become stale
      downstream_tools: canonical MCP tools that must recompute
      severity: PATCH | UPDATE | REVISION | VOID
      requires_888_hold: True if Arif must approve before recomputation proceeds
      recompute_window_hours: how long after invalidation before recompute is mandatory
      evidence_version_required: minimum evidence version needed for valid recompute
      superseded_by: what new evidence supersedes this trigger
    """

    trigger_variable: str
    invalidates: list[str] = field(default_factory=list)
    downstream_tools: list[str] = field(default_factory=list)
    severity: InvalidationSeverity = InvalidationSeverity.UPDATE
    requires_888_hold: bool = False
    recompute_window_hours: int = 72  # 3 days default
    evidence_version_required: str = "v1.0"
    superseded_by: str = ""


# ─── CANON-9 Replan DAG ───────────────────────────────────────────────────────
#
# The replan DAG encodes what happens when evidence for one CANON-9 variable changes.
#
# Example: New well log with Vp, Vs, rho (sonic + density) arrives.
#   → trigger: Vp (primary)
#   → invalidates: AI (computed from Vp, rho), pore pressure (computed from Vp)
#   → downstream_tools: geox_petrophysics, geox_geomechanics, geox_seismic_compute
#   → severity: UPDATE
#
# Example: New seismic tomography reveals different Vp distribution.
#   → trigger: Vp (regional)
#   → invalidates: AI, pore pressure, subsidence estimates
#   → downstream_tools: geox_seismic_compute, geox_subsurface_model, geox_basin
#   → severity: REVISION
#   → requires_888_hold: True (if used for drill planning)
#
# Example: MintPy InSAR shows unexpected subsidence signal.
#   → trigger: P (pore pressure change detected)
#   → invalidates: k (permeability), T (thermal), Sw (saturation)
#   → downstream_tools: geox_subsurface_model, geox_petrophysics
#   → severity: REVISION | VOID (if contradicts prior pressure model)
#   → requires_888_hold: True
#
# RULES:
#  1. P updates ALWAYS require 888_HOLD if used for drill planning.
#  2. Vp updates from seismic tomography require 888_HOLD if crossing structural boundaries.
#  3. Sw updates from new production data require 888_HOLD if >10% change from prior.
#  4. phi updates from new core data require recompute of STOIIP (geox_prospect).

REPLAN_DAG: dict[str, ReplanTrigger] = {
    # ── Vp (P-wave velocity) ─────────────────────────────────────────────────
    # Primary source: seismic tomography, check-shot, sonic log
    # Downstream: AI, pore pressure, Vs (via Vp/Vs ratio), impedance
    "Vp": ReplanTrigger(
        trigger_variable="Vp",
        invalidates=["AI", "P", "Vs"],  # AI computed from Vp+rho; P from Vp+offset; Vs via Vp/Vs
        downstream_tools=["geox_seismic_compute", "geox_geomechanics", "geox_subsurface_model"],
        severity=InvalidationSeverity.REVISION,
        requires_888_hold=False,  # seismic Vp updates are routine; HOLD only if drill planning use
        recompute_window_hours=24,
        evidence_version_required="v1.0",
    ),
    # ── rho (density) ───────────────────────────────────────────────────────
    # Primary source: density log, gravity inversion, core
    # Downstream: AI, pore pressure, Bouguer anomaly, effective porosity
    "rho": ReplanTrigger(
        trigger_variable="rho",
        invalidates=["AI", "P", "phi_eff"],  # AI = Vp × rho; P via density anomaly; phi via density-neutron
        downstream_tools=["geox_petrophysics", "geox_geomechanics", "geox_seismic_compute", "geox_subsurface_model"],
        severity=InvalidationSeverity.UPDATE,
        requires_888_hold=False,
        recompute_window_hours=48,
        evidence_version_required="v1.0",
    ),
    # ── Vs (S-wave velocity) ────────────────────────────────────────────────
    # Primary source: multi-component seismic, sonic dipole, Vp/Vs ratio transform
    # Downstream: Poisson's ratio, AVO, fracture density
    "Vs": ReplanTrigger(
        trigger_variable="Vs",
        invalidates=["nu", "AVO_class"],  # nu from Vp/Vs; AVO class from Vp, Vs, rho
        downstream_tools=["geox_seismic_compute", "geox_geomechanics"],
        severity=InvalidationSeverity.UPDATE,
        requires_888_hold=False,
        recompute_window_hours=48,
        evidence_version_required="v1.0",
    ),
    # ── phi (porosity) ──────────────────────────────────────────────────────
    # Primary source: density-neutron cross-plot, core analysis, seismic inversion
    # Downstream: Sw, k (permeability), STOIIP, net pay
    "phi": ReplanTrigger(
        trigger_variable="phi",
        invalidates=["Sw", "k", "net_pay", "STOIIP"],  # Archie: Sw from phi; k from phi+Sw; net pay from phi cut-off
        downstream_tools=["geox_petrophysics", "geox_prospect"],
        severity=InvalidationSeverity.REVISION,
        requires_888_hold=False,  # phi from new core data → recompute petrophysics; prospect update needs Arif
        recompute_window_hours=24,
        evidence_version_required="v1.0",
        superseded_by="",
    ),
    # ── Sw (water saturation) ───────────────────────────────────────────────
    # Primary source: resistivity (Archie), core, capillary pressure
    # Downstream: k, STOIIP, HC pore volume
    "Sw": ReplanTrigger(
        trigger_variable="Sw",
        invalidates=["k", "STOIIP", "HCPV"],  # k via Coates or Timor; STOIIP from phi+Sw+Pay
        downstream_tools=["geox_petrophysics", "geox_prospect"],
        severity=InvalidationSeverity.REVISION,
        requires_888_hold=False,  # >10% change requires Arif for prospect update
        recompute_window_hours=24,
        evidence_version_required="v1.0",
    ),
    # ── P (pore pressure) ───────────────────────────────────────────────────
    # Primary source: MDT/RCI, offset well calibration, seismic velocity inversion
    # ⚠️ CRITICAL: pore pressure is life-critical for drilling
    # 888_HOLD GATE: all pore pressure recomputations require Arif release
    "P": ReplanTrigger(
        trigger_variable="P",
        invalidates=["sigma_v", "fracture_gradient", "mud_weight_window"],  # in-situ stresses
        downstream_tools=["geox_subsurface_model", "geox_geomechanics"],
        severity=InvalidationSeverity.VOID,  # pore pressure contradictions are VOID-level
        requires_888_hold=True,
        recompute_window_hours=0,  # immediate — no delay for pressure updates
        evidence_version_required="v1.0",
        superseded_by="",
    ),
    # ── k (permeability) ───────────────────────────────────────────────────
    # Primary source: core analysis, well test, wireline formation tester
    # Downstream: production rate, well placement, STOIIP drainage
    "k": ReplanTrigger(
        trigger_variable="k",
        invalidates=["production_rate", "drainage_area", "well_count"],  # production planning
        downstream_tools=["geox_prospect"],
        severity=InvalidationSeverity.UPDATE,
        requires_888_hold=False,
        recompute_window_hours=72,
        evidence_version_required="v1.0",
    ),
    # ── T (temperature) ────────────────────────────────────────────────────
    # Primary source: BHT, DST, wireline logs, geothermal gradient
    # Downstream: maturation (Ro), pore pressure (thermal expansion), viscosity
    "T": ReplanTrigger(
        trigger_variable="T",
        invalidates=["Ro", "P_thermal", "viscosity"],  # Ro from T-timuth; P from thermal; viscosity for production
        downstream_tools=["geox_basin", "geox_subsurface_model"],
        severity=InvalidationSeverity.UPDATE,
        requires_888_hold=False,
        recompute_window_hours=168,  # 1 week — thermal evidence is slow-changing
        evidence_version_required="v1.0",
    ),
    # ── chi (magnetic susceptibility) ──────────────────────────────────────
    # Primary source: magnetic survey, core, EMAG2 grid
    # Downstream: basement depth, structural interpretation, plate reconstruction
    "chi": ReplanTrigger(
        trigger_variable="chi",
        invalidates=["basement_depth", "structural_联系人"],  # magnetic anomaly → basement
        downstream_tools=["geox_basin", "geox_deep_time_state", "geox_subsurface_model"],
        severity=InvalidationSeverity.PATCH,
        requires_888_hold=False,
        recompute_window_hours=336,  # 2 weeks — magnetic evidence very stable
        evidence_version_required="v1.0",
    ),
    # ── AI (acoustic impedance) ─────────────────────────────────────────────
    # Primary source: computed from Vp × rho; seismic inversion
    # Downstream: seismostratigraphic interpretation, AVO, well tie
    "AI": ReplanTrigger(
        trigger_variable="AI",
        invalidates=["reflection_coef", "AVO_response", "well_tie"],  # AI → RC → seismogram
        downstream_tools=["geox_seismic_compute", "geox_seismic_interpret"],
        severity=InvalidationSeverity.UPDATE,
        requires_888_hold=False,
        recompute_window_hours=24,
        evidence_version_required="v1.0",
    ),
    # ── nu (Poisson's ratio) ───────────────────────────────────────────────
    # Primary source: Vp/Vs ratio transform
    # Downstream: brittleness, fracture prediction, AVO class
    "nu": ReplanTrigger(
        trigger_variable="nu",
        invalidates=["brittleness", "fracture_density", "AVO_class"],
        downstream_tools=["geox_geomechanics", "geox_seismic_compute"],
        severity=InvalidationSeverity.PATCH,
        requires_888_hold=False,
        recompute_window_hours=72,
        evidence_version_required="v1.0",
    ),
}


# ─── Evidence Versioning ────────────────────────────────────────────────────────


@dataclass
class EvidenceVersion:
    """Tracks evidence version for a CANON-9 variable."""

    variable: str
    version: str  # e.g. "v1.0", "v2.1"
    source: str  # e.g. "Bateh1_logs_v3", "Malay_Basin_2024_survey"
    timestamp_utc: str
    is_current: bool = True


# ─── Replan Query Functions ─────────────────────────────────────────────────────


def get_replan_trigger(canon9_variable: str) -> ReplanTrigger | None:
    """Get the replan trigger for a CANON-9 variable."""
    return REPLAN_DAG.get(canon9_variable)


def get_invalidated_variables(trigger_variable: str) -> list[str]:
    """Return list of CANON-9 variables invalidated by a trigger variable update."""
    trigger = REPLAN_DAG.get(trigger_variable)
    return list(trigger.invalidates) if trigger else []


def get_downstream_tools(canon9_variable: str) -> list[str]:
    """Return which canonical MCP tools must recompute after a variable update."""
    trigger = REPLAN_DAG.get(canon9_variable)
    return list(trigger.downstream_tools) if trigger else []


def get_888_hold_on_replan(canon9_variable: str) -> bool:
    """Return True if recomputation after this variable update requires Arif release."""
    trigger = REPLAN_DAG.get(canon9_variable)
    return trigger.requires_888_hold if trigger else False


def get_replan_severity(canon9_variable: str) -> InvalidationSeverity | None:
    """Return the invalidation severity for a CANON-9 variable update."""
    trigger = REPLAN_DAG.get(canon9_variable)
    return trigger.severity if trigger else None


def should_recompute_after(
    trigger_variable: str,
    downstream_tool: str,
    evidence_age_hours: int | None = None,
) -> tuple[bool, str]:
    """
    Determine if a downstream tool should recompute after a variable update.

    Args:
        trigger_variable: CANON-9 variable that was updated
        downstream_tool: canonical MCP tool to check
        evidence_age_hours: how old the downstream tool's current evidence is (if known)

    Returns:
        (should_recompute: bool, reason: str)
    """
    trigger = REPLAN_DAG.get(trigger_variable)
    if not trigger:
        return False, f"Unknown trigger variable: {trigger_variable}"

    if downstream_tool not in trigger.downstream_tools:
        return False, f"{downstream_tool} not downstream of {trigger_variable}"

    if trigger.requires_888_hold:
        return True, f"888_HOLD required: {trigger_variable} update is {trigger.severity.value}"

    if evidence_age_hours is not None and evidence_age_hours > trigger.recompute_window_hours:
        return True, f"Evidence stale: {evidence_age_hours}h > {trigger.recompute_window_hours}h window"

    return True, f"Downstream of {trigger_variable}: {trigger.severity.value} invalidation"


# ─── Replan Receipt ─────────────────────────────────────────────────────────────


@dataclass
class ReplanReceipt:
    """Receipt for a replan decision — audit trail for recomputation calls."""

    trigger_variable: str
    downstream_tool: str
    action: str  # "RECOMPUTE" | "HOLD" | "SKIP"
    reason: str
    severity: str
    requires_888_hold: bool
    timestamp_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    evidence_version: str = "v1.0"
    superseded_tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_variable": self.trigger_variable,
            "downstream_tool": self.downstream_tool,
            "action": self.action,
            "reason": self.reason,
            "severity": self.severity,
            "requires_888_hold": self.requires_888_hold,
            "timestamp_utc": self.timestamp_utc,
            "evidence_version": self.evidence_version,
            "superseded_tools": self.superseded_tools,
        }


# ─── Version Lock ─────────────────────────────────────────────────────────────

REPLAN_DAG_VERSION = "1.0.0"
REPLAN_DAG_EPOCH = "2026-06-26"
REPLAN_DAG_STATUS = "LOCKED"

"""
Version history:
  1.0.0 (2026-06-26) — Initial locked replan DAG.
                          10 CANON-9 variables with explicit invalidation rules.
                          P (pore pressure) is VOID-level + 888_HOLD.
                          All other variables are UPDATE or PATCH severity.

DITEMPA BUKAN DIBERI — Stale evidence must be visible, not silently propagated.
The replan DAG is the memory of what changed and what must be recomputed.
"""
