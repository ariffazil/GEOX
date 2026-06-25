"""
geox_replan_dag.py — Replan Trigger Logic per CANON-9 Variable
DITEMPA BUKAN DIBERI — Earth state is never final.

Purpose:
  When new evidence arrives (new well, InSAR anomaly, seismic interpretation),
  this module determines:
    1. Which CANON-9 variables are affected
    2. Which downstream tools must be re-evaluated
    3. Whether propagation is automatic, advisory, or requires 888_HOLD

Rule: propagation=hold means the replan output cannot be used by autonomous
  agents. Arif must release. This is the only hard gate.

KISS: This is a lookup table, not a graph library.
  If the DAG grows complex, it gets refactored. Not now.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── CANON-9 Variables ────────────────────────────────────────────────────────

class Canon9Variable(str, Enum):
    Vp = "Vp"      # P-wave velocity — seismic, impedance
    Vs = "Vs"      # S-wave velocity — rock stiffness
    rho = "rho"   # Bulk density — gravity, overburden
    phi = "phi"   # Porosity — storage capacity
    Sw = "Sw"     # Water saturation — moveable HC
    P = "P"       # Pore pressure — kick risk, compaction
    k = "k"       # Permeability — flow capacity
    T = "T"       # Temperature — maturity, diagenesis
    chi = "chi"   # Magnetic susceptibility — anomaly


# ─── Propagation Levels ────────────────────────────────────────────────────────

class Propagation(str, Enum):
    """
    What happens when a variable is updated.

    auto:      Replan downstream tools automatically. Safe for autonomous use.
    advisory:  Replan and surface to Arif. No block — Arif can override.
    hold:      Replan and require Arif explicit release. BLOCKED for autonomous agents.
    """
    AUTO = "auto"          # low risk — autonomous propagation OK
    ADVISORY = "advisory"  # medium risk — surface to Arif, no block
    HOLD = "hold"          # high risk — 888_HOLD gate, Arif release required


# ─── Replan Trigger ───────────────────────────────────────────────────────────

class ReplanTrigger(BaseModel):
    """
    One trigger event: something changed, here is what it affects
    and how far the replan propagates.
    """
    trigger_name: str = Field(
        description="Canonical name of the trigger event. E.g. new_well_data, insar_subsidence_anomaly."
    )
    source_tool: str = Field(
        description="The GEOX tool that produced the new evidence. E.g. geox_well_ingest."
    )
    affected_variables: list[Canon9Variable] = Field(
        description="Which CANON-9 variables are updated by this trigger."
    )
    propagation: Propagation = Field(
        description="How far the replan propagates through the DAG."
    )
    reason: str = Field(
        description="Why this propagation level. Short sentence."
    )


# ─── Replan Entry ─────────────────────────────────────────────────────────────

class ReplanEntry(BaseModel):
    """
    One row in the replan DAG: trigger → affected variables → propagation.
    """
    trigger_name: str
    source_tool: str
    affected_variables: list[Canon9Variable]
    propagation: Propagation
    reason: str


# ─── The DAG (flat lookup table) ─────────────────────────────────────────────
#
# Format: trigger_name → ReplanEntry
#
# To add a new trigger: append a ReplanEntry to REPLAN_TABLE.
# To change propagation: edit the Propagation value.
# That is all.

REPLAN_TABLE: dict[str, ReplanEntry] = {}


def _register(
    trigger_name: str,
    source_tool: str,
    affected_variables: list[Canon9Variable],
    propagation: Propagation,
    reason: str,
) -> None:
    REPLAN_TABLE[trigger_name] = ReplanEntry(
        trigger_name=trigger_name,
        source_tool=source_tool,
        affected_variables=affected_variables,
        propagation=propagation,
        reason=reason,
    )


# ── Well Domain ───────────────────────────────────────────────────────────────

_register(
    trigger_name="new_well_log",
    source_tool="geox_well_ingest",
    affected_variables=[Canon9Variable.Vp, Canon9Variable.rho, Canon9Variable.Vs],
    propagation=Propagation.AUTO,
    reason="New log data updates local velocity/density. Well-level only.",
)

_register(
    trigger_name="new_petrophysics",
    source_tool="geox_petrophysics",
    affected_variables=[Canon9Variable.phi, Canon9Variable.Sw, Canon9Variable.k],
    propagation=Propagation.AUTO,
    reason="Vsh/porosity/Sw from a single well. Local interpretation — does not affect basin model.",
)

_register(
    trigger_name="new_sequence_interpretation",
    source_tool="geox_sequence",
    affected_variables=[],
    propagation=Propagation.ADVISORY,
    reason="Stratigraphic correlation changes may affect sand distribution model. Surface to Arif.",
)

# ── Seismic Domain ─────────────────────────────────────────────────────────────

_register(
    trigger_name="new_well_tie",
    source_tool="geox_seismic_compute",
    affected_variables=[Canon9Variable.Vp, Canon9Variable.rho],
    propagation=Propagation.AUTO,
    reason="New well tie updates Vp calibration at one location. Local.",
)

_register(
    trigger_name="new_horizon_interpretation",
    source_tool="geox_seismic_interpret",
    affected_variables=[],
    propagation=Propagation.ADVISORY,
    reason="Horizon changes may affect structural map. Surface to Arif.",
)

_register(
    trigger_name="new_seismic_inversion",
    source_tool="geox_seismic_compute",
    affected_variables=[Canon9Variable.Vp, Canon9Variable.Vs, Canon9Variable.rho],
    propagation=Propagation.HOLD,
    reason="Full-stack elastic inversion changes AI and Vp/Vs ratio across the volume. Structural maps may shift. Arif release required.",
)

# ── Geomechanics + Pressure ───────────────────────────────────────────────────

_register(
    trigger_name="insar_subsidence_anomaly",
    source_tool="geox_geomechanics",
    affected_variables=[Canon9Variable.P],
    propagation=Propagation.HOLD,
    reason="InSAR surface subsidence is a proxy for pore pressure change. Could indicate compaction or leakage. 888_HOLD.",
)

_register(
    trigger_name="new_pressure_test",
    source_tool="geox_petrophysics",
    affected_variables=[Canon9Variable.P],
    propagation=Propagation.HOLD,
    reason="Actual pressure measurement — directly affects drilling window and reserve estimates. Arif release required.",
)

_register(
    trigger_name="new_stress_measurement",
    source_tool="geox_geomechanics",
    affected_variables=[],
    propagation=Propagation.ADVISORY,
    reason="Stress orientation may affect wellbore stability and fracture interpretation. Surface to Arif.",
)

# ── Basin Domain ───────────────────────────────────────────────────────────────

_register(
    trigger_name="new_maturity_data",
    source_tool="geox_basin",
    affected_variables=[Canon9Variable.T],
    propagation=Propagation.HOLD,
    reason="New maturity (Ro, Tmax) changes charge timing and volume. Prospect risking may shift. Arif release required.",
)

_register(
    trigger_name="new_bathymetry",
    source_tool="geox_basin",
    affected_variables=[],
    propagation=Propagation.AUTO,
    reason="Seafloor depth update — accommodation space changes. Does not directly affect HC system.",
)

_register(
    trigger_name="new_heatflow",
    source_tool="geox_basin",
    affected_variables=[Canon9Variable.T],
    propagation=Propagation.ADVISORY,
    reason="Heatflow changes thermal history. May shift maturity. Surface to Arif.",
)

# ── Plate Tectonics ────────────────────────────────────────────────────────────

_register(
    trigger_name="new_paleo_reconstruction",
    source_tool="geox_deep_time_state",
    affected_variables=[],
    propagation=Propagation.ADVISORY,
    reason="New paleo-position changes paleolatitude and paleoclimate context. Surface to Arif.",
)

# ── Subsurface Model ──────────────────────────────────────────────────────────

_register(
    trigger_name="new_3d_structure",
    source_tool="geox_subsurface_model",
    affected_variables=[],
    propagation=Propagation.HOLD,
    reason="Structural framework changes (new fault, different depth) may affect trap volume. Arif release required.",
)

_register(
    trigger_name="new_gravity_data",
    source_tool="geox_subsurface_model",
    affected_variables=[Canon9Variable.rho],
    propagation=Propagation.ADVISORY,
    reason="New gravity data constrains density model. Density changes may affect depth conversion. Surface to Arif.",
)

_register(
    trigger_name="new_magnetic_data",
    source_tool="geox_deep_time_state",
    affected_variables=[Canon9Variable.chi],
    propagation=Propagation.AUTO,
    reason="Magnetic anomaly update — local crustal interpretation. Low blast radius.",
)

# ── Prospect ─────────────────────────────────────────────────────────────────

_register(
    trigger_name="any_canon9_update",
    source_tool="*",
    affected_variables=list(Canon9Variable),
    propagation=Propagation.HOLD,
    reason="Any update touching prospect inputs (POS, EVOI, risking) always routes to Arif. Prospect-level decisions are sovereign.",
)


# ─── Query API ────────────────────────────────────────────────────────────────

def get_replan(
    trigger_name: str,
    *,
    source_tool: Optional[str] = None,
) -> ReplanEntry | None:
    """
    Look up replan propagation for a trigger.

    Args:
        trigger_name: The canonical trigger event name.
        source_tool: Optional — if provided, also validate the source tool matches.

    Returns:
        ReplanEntry if trigger exists, None otherwise.
    """
    entry = REPLAN_TABLE.get(trigger_name)
    if entry is None:
        return None
    if source_tool is not None and entry.source_tool not in (source_tool, "*"):
        return None
    return entry


def requires_hold(trigger_name: str, source_tool: Optional[str] = None) -> bool:
    """True if this trigger requires Arif release before autonomous use."""
    entry = get_replan(trigger_name, source_tool=source_tool)
    return entry is not None and entry.propagation == Propagation.HOLD


def get_downstream_variables(
    trigger_name: str,
    source_tool: Optional[str] = None,
) -> list[Canon9Variable]:
    """Return the list of CANON-9 variables affected by this trigger."""
    entry = get_replan(trigger_name, source_tool=source_tool)
    return list(entry.affected_variables) if entry else []
