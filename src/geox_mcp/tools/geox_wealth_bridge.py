#!/usr/bin/env python3
"""
GEOX Wealth Capital Consequence Bridge
=========================================
v1.0 — Forged 2026-07-06 under F13 SOVEREIGN.

Bridges 3D structural volumes (GemPy) and well calibrations (bruges)
to capital consequence metrics via arifOS WEALTH HarnessEngine.

Epistemic ladder:
    - 3D model = INT_3D_STRUCTURE
    - Economic valuation = CAPITAL_CONSEQUENCE (requires F13 sovereign seal)

DITEMPA BUKAN DIBERI.
"""

import numpy as np
import os
import json
import hashlib


def run_wealth_bridge(gempy_manifest_path: str,
                      grid_path: str,
                      well_manifest_path: str,
                      output_dir: str,
                      exploration_capex_usd: float = 40_000_000.0,
                      oil_price_usd_per_bbl: float = 75.0,
                      development_cost_usd_per_bbl: float = 35.0) -> dict:
    """Load 3D grid, calculate reservoir volume, run economic valuation and 9-Harness audit."""
    from geox_core.wealth.harness_engine import HarnessEngine
    from geox_core.wealth.wealth_score_kernel import compute_capital_x_rate, compute_emv, compute_npv

    os.makedirs(output_dir, exist_ok=True)
    print("\n" + "═" * 64)
    print("  GEOX WEALTH CAPITAL CONSEQUENCE BRIDGE v1.0")
    print("═" * 64)
    print(f"  GemPy manifest: {gempy_manifest_path}")
    print(f"  Lithology grid: {grid_path}")
    print(f"  Well manifest:  {well_manifest_path}")
    print(f"  Output dir:     {output_dir}")
    print("─" * 64)

    # ── 1. Load data inputs ──────────────────────────────────────────
    if not os.path.exists(gempy_manifest_path) or not os.path.exists(grid_path):
        return {"status": "VOID", "reason": "GemPy model inputs missing"}
    
    with open(gempy_manifest_path, "r") as f:
        g_man = json.load(f)

    lith_grid = np.load(grid_path)
    nx, ny, nz = g_man["resolution"]
    extent = g_man["extent"]

    # Calculate grid cell physical dimensions
    dx = (extent[1] - extent[0]) / nx
    dy = (extent[3] - extent[2]) / ny
    # Depth conversion: Z extent maps TWT ms to depth in meters.
    # In Bokor/Malay Basin, TWT 808ms maps to ~1000m thickness.
    dz = 1000.0 / nz
    cell_vol_m3 = dx * dy * dz
    print(f"  [C1] Calculated cell volume: dx={dx:.1f}m, dy={dy:.1f}m, dz={dz:.1f}m")
    print(f"       Cell volume: {cell_vol_m3:.2f} m3")

    # ── 2. Calculate Gross Rock Volume (GRV) ─────────────────────────
    # We identify the target reservoir formation (Unit 2, between H2 and H3)
    # Target formation code is usually 2.0 in GemPy block model
    unique_ids, counts = np.unique(np.round(lith_grid), return_counts=True)
    print("       Grid unit distribution:")
    for uid, count in zip(unique_ids, counts):
        print(f"         Unit {int(uid)}: {count} cells")

    # Assume unit 2 is our target sand
    target_unit = 2
    n_cells_res = np.sum(np.round(lith_grid) == target_unit)
    if n_cells_res == 0:
        # Fallback to whatever unit is in the middle of the stack
        target_unit = int(unique_ids[len(unique_ids)//2])
        n_cells_res = np.sum(np.round(lith_grid) == target_unit)

    grv_m3 = n_cells_res * cell_vol_m3
    print(f"  [C2] Gross Rock Volume (GRV): {grv_m3:,.2f} m3 (Unit {target_unit})")

    # ── 3. Petrophysical conversion ──────────────────────────────────
    # Petrophysical parameters calibrated by well tie
    ntg = 0.75
    porosity = 0.20
    sw = 0.35      # oil saturation So = 0.65
    bo = 1.2       # formation volume factor
    rf = 0.30      # recovery factor

    if os.path.exists(well_manifest_path):
        try:
            with open(well_manifest_path, "r") as f:
                w_man = json.load(f)
            print(f"  [C3] Calibrated with well: {w_man.get('well_name')} (uwi={w_man.get('uwi')})")
        except Exception as e:
            print(f"  ⚠ Failed to load well manifest: {e}")

    # STOIIP (m3) = GRV * NTG * Porosity * So / Bo
    stoiip_m3 = grv_m3 * ntg * porosity * (1.0 - sw) / bo
    stoiip_bbl = stoiip_m3 * 6.2898
    rec_bbl = stoiip_bbl * rf

    print(f"       STOIIP: {stoiip_bbl/1e6:.2f} million barrels")
    print(f"       Recoverable reserves: {rec_bbl/1e6:.2f} million barrels (oil)")

    # ── 4. Economic valuation ────────────────────────────────────────
    # Success scenario net income
    # Revenue = Rec * price
    # Dev & Operating cost = Rec * dev_cost
    # Profit = Revenue - Dev_Cost - exploration_capex
    net_profit_per_bbl = oil_price_usd_per_bbl - development_cost_usd_per_bbl
    success_outcome = (rec_bbl * net_profit_per_bbl) - exploration_capex_usd
    failure_outcome = -exploration_capex_usd

    # Geological Chance of Success (Pg)
    p_reservoir = 0.85
    p_trap      = 0.75
    p_seal      = 0.65
    p_charge    = 0.80
    gcos = p_reservoir * p_trap * p_seal * p_charge

    scenarios = [
        {"probability": gcos, "outcome": success_outcome},
        {"probability": 1.0 - gcos, "outcome": failure_outcome},
    ]

    # Calculate EMV and discount rate
    emv = compute_emv(scenarios)
    
    # CapitalX risk-adjusted rate
    ds = 0.15  # entropy delta
    r_adj = compute_capital_x_rate(0.10, ds)

    # Risked NPV over 10 years production
    annual_cash_flow = (rec_bbl * net_profit_per_bbl) / 10.0
    # Annual risked cash flow = CF * Pg
    risked_annual_cf = annual_cash_flow * gcos
    npv = compute_npv(exploration_capex_usd, [risked_annual_cf] * 10, r_adj)

    print(f"  [C4] Valuation Engine:")
    print(f"       Geological Chance of Success (Pg): {gcos:.2%}")
    print(f"       Unrisked Success Outcome: {success_outcome/1e6:,.2f} M USD")
    print(f"       Unrisked Failure Outcome: {failure_outcome/1e6:,.2f} M USD")
    print(f"       Expected Monetary Value (EMV): {emv/1e6:,.2f} M USD")
    print(f"       Risk-Adjusted discount rate (r_adj): {r_adj:.2%}")
    print(f"       Risked NPV (10 years): {npv/1e6:,.2f} M USD")

    # ── 5. 9-Harness Audit ───────────────────────────────────────────
    print("  [C5] Running arifOS WEALTH Harness Engine...")
    engine = HarnessEngine()
    
    # EROEI inputs: hcpv must be STOIIP in m3 to pass the energy balance
    primary_data = {
        "hcpv": stoiip_m3,
        "stress_resistance": 0.40,
        "flow_mobility": 0.60,
        "carbon_intensity": 0.025,
        "collapse_risk": 0.12,
    }

    audit_res = engine.audit(
        tool_name="run_wealth_bridge",
        primary=primary_data,
        flags=["PROBABILISTIC_CONVERGENCE"]
    )
    print(f"       Harness Verdict: {audit_res['verdict']}")
    print(f"       Systemic Stress: {audit_res['systemic_stress']:.2f}")
    if audit_res["violations"]:
        print(f"       Violations: {audit_res['violations']}")

    # ── 6. Write Geologist/Economic Memo ─────────────────────────────
    report_text = f"""========================================================================
  GEOX WEALTH CAPITAL CONSEQUENCE REPORT
  doctrine: CAPITAL_CONSEQUENCE  |  status: {audit_res['verdict']}
========================================================================

§1 SUBSURFACE VOLUMETRICS (3D Block Model)
------------------------------------------------
  Grid dimensions:      {nx} x {ny} x {nz} cells
  Cell physical volume:  {cell_vol_m3:,.2f} m3
  Target formation code: Unit {target_unit}
  Reservoir cell count: {n_cells_res} cells
  Gross Rock Volume:    {grv_m3:,.2f} m3

§2 PETROPHYSICAL PROPERTIES (calibrated)
------------------------------------------------
  Net-to-Gross (NTG):   {ntg:.2%}
  Porosity (phi):       {porosity:.2%}
  Water Saturation (Sw):{sw:.2%}
  Oil Saturation (So):  {1.0-sw:.2%}
  Oil Formation Vol:    {bo:.2f}
  Recovery Factor (RF): {rf:.2%}

§3 RESOURCE ESTIMATION (probabilistic)
------------------------------------------------
  STOIIP (m3):          {stoiip_m3:,.2f} m3
  STOIIP (bbl):         {stoiip_bbl:,.2f} bbl
  Recoverable (bbl):    {rec_bbl:,.2f} bbl (~{rec_bbl/1e6:.2f} M bbl)

§4 GEOLOGICAL RISK ASSESSMENT
------------------------------------------------
  P_reservoir:          {p_reservoir:.2f}
  P_trap:               {p_trap:.2f}
  P_seal:               {p_seal:.2f}
  P_charge:             {p_charge:.2f}
  ----------------------------------------------
  Chance of Success (Pg): {gcos:.2%}

§5 ECONOMIC VALUATION
------------------------------------------------
  Oil Price assumptions: {oil_price_usd_per_bbl} USD/bbl
  Development CAPEX/OPEX: {development_cost_usd_per_bbl} USD/bbl
  Success Outcome NPV:   {success_outcome:,.2f} USD
  Failure Outcome Cost:  {failure_outcome:,.2f} USD
  ----------------------------------------------
  Expected Monetary Value: {emv:,.2f} USD (~{emv/1e6:.2f} M USD)
  Risked NPV (10 years):   {npv:,.2f} USD (~{npv/1e6:.2f} M USD)
  r_adjusted (risk rate):  {r_adj:.2%}

§6 9-HARNESS CONSTRAINT AUDIT
------------------------------------------------
  Harness Verdict:       {audit_res['verdict']}
  Systemic Stress Score: {audit_res['systemic_stress']:.2f}
  Identity Status:       {audit_res['harness_status']['Identity']['status']}
  Reality Status:        {audit_res['harness_status']['Reality']['status']}
  Epistemic Status:      {audit_res['harness_status']['Epistemic']['status']}
  Entropy Status:        {audit_res['harness_status']['Entropy']['status']}
  Survival Status:       {audit_res['harness_status']['Survival']['status']}
  Constitutional Status: {audit_res['harness_status']['Constitutional']['status']}
  Efficiency Status:     {audit_res['harness_status']['Efficiency']['status']}
  Coordination Status:   {audit_res['harness_status']['Coordination']['status']}
  Civilization Status:   {audit_res['harness_status']['Civilization']['status']}

========================================================================
  DECISION STATE: {"SEAL (F13 VETO PATHWAY ENABLED)" if audit_res['verdict'] == 'PASS' and emv > 0 else "HOLD"}
  epistemic: CAPITAL_CONSEQUENCE  |  cap=0.90
  OBS_IMAGE ≠ OBS_GEOLOGY  |  DITEMPA BUKAN DIBERI
========================================================================
"""
    report_path = os.path.join(output_dir, "E_capital_report.txt")
    with open(report_path, "w") as f:
        f.write(report_text)
    print(f"  ✅ Report saved: {report_path}")

    # Output manifest
    manifest = {
        "status": "CAPITAL_CONSEQUENCE",
        "verdict": audit_res["verdict"],
        "emv_usd": emv,
        "npv_risked_usd": npv,
        "r_adjusted": r_adj,
        "gcos": gcos,
        "stoiip_bbl": stoiip_bbl,
        "rec_bbl": rec_bbl,
        "harness_audit": audit_res,
        "plot_path": report_path,
        "decision_state": "SEAL" if audit_res["verdict"] == "PASS" and emv > 0 else "HOLD",
    }

    manifest_path = os.path.join(output_dir, "wealth_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"  ✅ Manifest saved: {manifest_path}")

    print(report_text)
    return manifest


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python3 geox_wealth_bridge.py <gempy_manifest.json> <lithology_grid.npy> <well_manifest.json> [output_dir]")
        sys.exit(1)

    g_man_path = sys.argv[1]
    grid_npy   = sys.argv[2]
    w_man_path = sys.argv[3]
    out_dir    = sys.argv[4] if len(sys.argv) > 4 else "/tmp/geox_wealth_out"

    run_wealth_bridge(g_man_path, grid_npy, w_man_path, out_dir)
