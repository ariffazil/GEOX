/**
 * VaultReceipt.js — VAULT999 Receipt Builder (Client-Side)
 * =========================================================
 * Builds local receipts that mirror VAULT999 schema.
 * Full receipts are sealed server-side; this module handles UI display.
 */

class VaultReceipt {
  constructor() {
    this.receipts = [];  // Local receipt history
  }

  /**
   * Build receipt from physics9_state
   */
  build(physics9State, floorChecks = {}) {
    const receipt = {
      receipt_id: this._generateId(),
      vault_route: "999_VAULT",
      app_id: "geox.subsurface.well-desk",
      timestamp: new Date().toISOString(),
      physics9_state: physics9State,
      floor_checks: {
        F1: floorChecks.F1 ?? false,
        F2: floorChecks.F2 ?? false,
        F4: floorChecks.F4 ?? false,
        F7: floorChecks.F7 ?? false,
        F9: floorChecks.F9 ?? false,
        F11: floorChecks.F11 ?? false,
        F13: floorChecks.F13 ?? false
      }
    };

    this.receipts.push(receipt);
    return receipt;
  }

  /**
   * Format receipt for display
   */
  format(receipt) {
    const { receipt_id, timestamp, physics9_state, floor_checks } = receipt;
    const state = physics9_state || {};
    const grade = state.grade || "RAW";

    const gradeColor = {
      AAA: "#0f0",
      AA: "#8f0",
      A: "#ff0",
      RAW: "#888",
      PHYSICS_VIOLATION: "#f00"
    }[grade] || "#888";

    let html = `
      <div class="vault-receipt" style="border:1px solid ${gradeColor};padding:8px;margin:4px 0;background:rgba(0,255,0,0.05);font-family:monospace;font-size:11px;">
        <div style="display:flex;justify-content:space-between;">
          <span style="color:#aaa;">${receipt_id}</span>
          <span style="color:${gradeColor};font-weight:bold;">${grade}</span>
        </div>
        <div style="color:#666;margin-top:4px;">${timestamp}</div>
    `;

    if (state.forward_result || (state.vp && state.vs)) {
      html += `<div style="margin-top:6px;color:#ccc;">`;
      html += `Vp=${state.vp || state.forward_result?.vp} `;
      html += `Vs=${state.vs || state.forward_result?.vs} `;
      html += `rho=${state.rho || state.forward_result?.rho}</div>`;
    }

    if (state.inverse_result || state.est_porosity) {
      html += `<div style="margin-top:4px;color:#ccc;">`;
      html += `est_phi=${state.est_porosity || state.inverse_result?.est_porosity} `;
      html += `est_Sw=${state.est_sw || state.inverse_result?.est_sw} `;
      html += `fluid=${state.est_fluid || state.inverse_result?.est_fluid}</div>`;
    }

    // Floor check indicators
    html += `<div style="margin-top:6px;display:flex;gap:6px;">`;
    for (const [floor, passed] of Object.entries(floor_checks)) {
      const color = passed ? "#0f0" : "#f00";
      html += `<span style="color:${color};font-size:9px;">${floor}:${passed ? "OK" : "FAIL"}</span>`;
    }
    html += `</div></div>`;

    return html;
  }

  /**
   * Render receipt panel into DOM element
   */
  renderPanel(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `<div style="color:#888;font-size:10px;margin-bottom:8px;">VAULT999 RECEIPTS (${this.receipts.length})</div>`;

    // Show last 10 receipts (newest first)
    const recent = [...this.receipts].reverse().slice(0, 10);
    for (const receipt of recent) {
      container.innerHTML += this.format(receipt);
    }
  }

  /**
   * Export all receipts as JSON
   */
  export() {
    return JSON.stringify(this.receipts, null, 2);
  }

  _generateId() {
    return `vlt-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  }
}
