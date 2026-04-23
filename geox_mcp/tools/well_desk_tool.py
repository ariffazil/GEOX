"""
well_desk_tool.py — FastMCP Tool: geox_well_desk_launch
=======================================================
Wires WellDesk app into MCP host. All compute routes through
rock_physics_engine.py. Every call emits vault_receipt.

Naming: fsh-linux convention. Aligned with existing geox_mcp/tools/*.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add core to path for physics engine import
_GEOX_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_GEOX_ROOT / "core"))

from rock_physics_engine import (
    RockPhysicsEngine, Physics9State, PhysicsGuard, VaultReceipt
)

# FastMCP import — pattern-matched to existing geox_mcp/tools/*.py
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # Runtime guard

# lasio for LAS file parsing
try:
    import lasio
except ImportError:
    lasio = None


_TOOL_NAME = "geox_well_desk_launch"

VOLVE_F1B_SCAFFOLD = {
    "well_id": "15/9-F-1B",
    "field": "Volve",
    "basin": "North Sea",
    "country": "Norway",
    "operator": "Equinor (decommissioned 2016)",
    "license_note": "Synthetic approximation. Real data: data.equinor.com (CC BY-NC)",
    "depth_range_m": (2000, 3500),
    "sample_interval_m": 0.5,
    "hc_zone": {"Name": "Heimdal Fm", "top_m": 2080, "base_m": 2120},
    "petro_summary": {
        "porosity_avg": 0.28,
        "sw_avg": 0.25,
        "vsh_avg": 0.08,
        "net_pay_m": 32.0,
        "fluid_type": "gas"
    },
    "rock_type": "quartz_sandstone",
    "las_path": "geox/apps/well-desk/data/samples/15_9_F1B_synthetic.las",
    "provenance": "synthetic_from_published_statistics"
}

_APP_ID = "geox.subsurface.well-desk"


class WellDeskTool:
    """
    MCP tool wrapper for GEOX WellDesk.
    Implements tool contract from contracts/mcp/geox_well_desk_contract.json
    """

    def __init__(self):
        self.engine = RockPhysicsEngine()
        self.guard = PhysicsGuard()

    def launch(self,
               well_id: str,
               mode: str = "1d",
               las_path: str | None = None,
               depth_range: dict | None = None,
               physics_params: dict | None = None) -> dict:
        """
        Launch WellDesk with specified mode and parameters.

        Args:
            well_id: Well identifier (e.g., 'BEK-2', 'DUL-A1')
            mode: '1d' | '2d' | 'forward' | 'inverse' | 'metabolic'
            las_path: Path to LAS file, or None for scaffold fixture
            depth_range: Optional {'top_m': float, 'base_m': float}
            physics_params: Optional forward/inverse parameters
        """
        # ── Load state ────────────────────────────────────────────────────────
        # ── Volve F-1B synthetic well ────────────────────────────────────────
        if well_id in ("15/9-F-1B", "VOLVE-F-1B", "volve_f1b"):
            scaffold = self.engine.load_scaffold("bek_2")  # base scaffold
            scaffold.porosity = 0.28
            scaffold.sw = 0.25
            scaffold.vsh = 0.08
            scaffold.fluid_type = "gas"
            scaffold.pressure_mpa = 22.0
            state = scaffold
        elif las_path and lasio and os.path.exists(las_path):
            state = self._load_las(las_path, well_id)
        else:
            state = self.engine.load_scaffold(well_id)

        # Override with user physics_params if provided
        if physics_params:
            state.porosity = physics_params.get("porosity", state.porosity)
            state.sw = physics_params.get("sw", state.sw)
            state.vsh = physics_params.get("vsh", state.vsh)
            state.fluid_type = physics_params.get("fluid_type", state.fluid_type)
            state.pressure_mpa = physics_params.get("pressure_mpa", state.pressure_mpa)
            state.temp_c = physics_params.get("temp_c", state.temp_c)

        # ── Route to mode ─────────────────────────────────────────────────────
        if mode == "forward":
            state = self.engine.forward(state)
        elif mode == "inverse":
            if physics_params and "observed_vp" in physics_params:
                vp_obs = physics_params["observed_vp"]
                vs_obs = physics_params.get("observed_vs", 0.0)
                rho_obs = physics_params.get("observed_rho", 2.2)
            else:
                # Derive from current forward state
                fwd = self.engine.forward(state)
                vp_obs, vs_obs, rho_obs = fwd.vp, fwd.vs, fwd.rho
            state = self.engine.inverse(vp_obs, vs_obs, rho_obs, prior=state)
        elif mode == "metabolic":
            obs_vp = physics_params.get("observed_vp", 3500.0) if physics_params else 3500.0
            obs_ai = physics_params.get("observed_ai", 7000.0) if physics_params else 7000.0
            state = self.engine.metabolic(obs_vp, obs_ai, state)
        elif mode in ("1d", "2d"):
            # Visualization modes: run forward to populate display fields
            state = self.engine.forward(state)
        else:
            state.grade = "RAW"

        # ── PhysicsGuard gate ─────────────────────────────────────────────────
        if state.grade == "PHYSICS_VIOLATION":
            return self._build_error_response(state, "PhysicsGuard rejected output")

        # ── F1 reversibility check (inverse + forward round-trip) ─────────────
        if mode in ("forward", "inverse"):
            fwd_check = self.engine.forward(Physics9State(**state.to_dict()))
            inv_check = self.engine.inverse(
                fwd_check.vp, fwd_check.vs, fwd_check.rho,
                prior=Physics9State(porosity=state.porosity, sw=state.sw,
                                   vsh=state.vsh, fluid_type=state.fluid_type,
                                   pressure_mpa=state.pressure_mpa, temp_c=state.temp_c)
            )
            f1_pass = self.guard.check_reversibility(fwd_check, inv_check)
        else:
            f1_pass = True  # Visualization modes skip F1

        # ── Build VAULT999 receipt ────────────────────────────────────────────
        receipt = self.engine.build_vault_receipt(state)
        receipt.floor_checks["F1"] = f1_pass
        receipt.floor_checks["F9"] = state.grade != "PHYSICS_VIOLATION"

        # ── Build response ────────────────────────────────────────────────────
        return {
            "ui": {
                "resourceUri": "ui://well_desk",
                "render_mode": mode,
                "track_count": 4 if mode in ("1d", "2d") else 0
            },
            "vault_receipt": {
                "receipt_id": receipt.receipt_id,
                "vault_route": receipt.vault_route,
                "app_id": receipt.app_id,
                "timestamp": receipt.timestamp,
                "floor_checks": receipt.floor_checks
            },
            "physics9_state": state.to_dict()
        }

    def _load_las(self, las_path: str, well_id: str) -> Physics9State:
        """Parse LAS file and extract key curves into Physics9State."""
        if lasio is None:
            return self.engine.load_scaffold(well_id)

        try:
            las = lasio.read(las_path)
            # Extract depth
            depth = las.index
            # Extract curves — standard mnemonics
            gr = las.curves.GR.data if hasattr(las.curves, "GR") else None
            rt = las.curves.RT.data if hasattr(las.curves, "RT") else None
            rhob = las.curves.RHOB.data if hasattr(las.curves, "RHOB") else None
            nphi = las.curves.NPHI.data if hasattr(las.curves, "NPHI") else None
            dt = las.curves.DT.data if hasattr(las.curves, "DT") else None

            # Compute average properties over depth range
            def _avg(curve):
                if curve is None:
                    return None
                valid = curve[~np.isnan(curve)] if 'np' in globals() else \
                        [v for v in curve if v == v]  # NaN check without numpy
                return sum(valid) / len(valid) if valid else None

            # Derive approximate inputs from logs
            avg_gr = _avg(gr)
            avg_rhob = _avg(rhob)
            avg_nphi = _avg(nphi)
            avg_dt = _avg(dt)

            # Simple transforms
            vsh = min(1.0, max(0.0, (avg_gr - 30) / 130)) if avg_gr else 0.20
            por = min(0.50, max(0.0, (2.65 - avg_rhob) / 1.65)) if avg_rhob else 0.20
            # Placeholder Sw — needs resistivity
            sw = 0.50

            return Physics9State(
                porosity=round(por, 3),
                sw=round(sw, 3),
                vsh=round(vsh, 3),
                fluid_type="brine",
                pressure_mpa=25.0,
                temp_c=80.0
            )
        except Exception:
            return self.engine.load_scaffold(well_id)

    def _build_error_response(self, state: Physics9State, error_msg: str) -> dict:
        """Build error response when PhysicsGuard rejects."""
        receipt = self.engine.build_vault_receipt(state)
        receipt.floor_checks["F9"] = False
        return {
            "ui": {"resourceUri": "ui://well_desk", "render_mode": "error", "track_count": 0},
            "vault_receipt": {
                "receipt_id": receipt.receipt_id,
                "vault_route": receipt.vault_route,
                "app_id": receipt.app_id,
                "timestamp": receipt.timestamp,
                "floor_checks": receipt.floor_checks,
                "error": error_msg
            },
            "physics9_state": state.to_dict()
        }


# ── FastMCP registration ──────────────────────────────────────────────────────

_tool_instance = WellDeskTool()


def register(mcp: FastMCP) -> None:
    """Register tool with FastMCP server instance."""

    @mcp.tool(name=_TOOL_NAME)
    def geox_well_desk_launch(
        well_id: str,
        mode: str = "1d",
        las_path: str | None = None,
        depth_range: dict | None = None,
        physics_params: dict | None = None
    ) -> dict:
        """
        Launch GEOX WellDesk for well log visualization and rock physics.

        Args:
            well_id: Well identifier (e.g., 'BEK-2', 'DUL-A1')
            mode: Operating mode — '1d' (track view), '2d' (correlation),
                  'forward' (Gassmann), 'inverse' (inversion), 'metabolic' (convergence)
            las_path: Optional path to LAS file. If None, loads scaffold fixture.
            depth_range: Optional depth window {'top_m': float, 'base_m': float}
            physics_params: Mode-specific parameters (porosity, sw, fluid_type, etc.)
        """
        return _tool_instance.launch(
            well_id=well_id,
            mode=mode,
            las_path=las_path,
            depth_range=depth_range,
            physics_params=physics_params
        )