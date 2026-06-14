/**
 * WellDesk Render Adapter — viewModel → DOM
 * ============================================
 * Consumes structuredContent.envelope.viewModel from the MCP bridge
 * and populates the WellDesk UI. Also renders governance state
 * (holds[], constraints{}) via the bridge's renderGovernance().
 *
 * Triggered by CustomEvent 'well-desk:viewmodel' emitted from MCPBridge.js.
 *
 * DITEMPA BUKAN DIBERI
 */
(function () {
  'use strict';

  /**
   * Render a well log curve into a target element.
   * This is a lightweight binding — the full TrackRenderer lives in src/tracks/
   */
  function renderCurve(targetId, depthArray, valueArray, label, color) {
    const target = document.getElementById(targetId);
    if (!target) return;

    // Simple text fallback; real rendering uses GEOPHYSICS/TrackRenderer
    if (depthArray && valueArray && depthArray.length > 0) {
      const min = Math.min(...valueArray);
      const max = Math.max(...valueArray);
      const range = max - min || 1;
      target.innerHTML = `<div style="font-size:10px;color:${color || '#4af'}">
        <b>${label}</b> ${valueArray.length} samples
        [${min.toFixed(1)}–${max.toFixed(1)}]
      </div>`;
    } else {
      target.innerHTML = `<div style="font-size:10px;color:#666">${label}: no data</div>`;
    }
  }

  /**
   * Render the complete viewModel into the WellDesk DOM.
   * viewModel = { wellId, curves, zones, physics9, ... }
   */
  function renderViewModel(viewModel) {
    if (!viewModel) return;

    const w = viewModel;

    // Well info
    const wellNameEl = document.getElementById('wellName');
    if (wellNameEl) wellNameEl.textContent = w.wellId || '—';

    const totalDepthEl = document.getElementById('totalDepth');
    if (totalDepthEl) totalDepthEl.textContent = w.totalDepth
      ? `${w.totalDepth.toLocaleString()} m` : (w.wellId ? '—' : '4,250 m');

    // Curves pane — each curve gets its own display
    const curves = w.curves || {};
    renderCurve('grTrack', curves.GR_depth, curves.GR, 'GR (API)', '#0f0');
    renderCurve('rhobTrack', curves.RHOB_depth, curves.RHOB, 'RHOB (g/cc)', '#f80');
    renderCurve('dtTrack', curves.DT_depth, curves.DT, 'DT (us/ft)', '#4af');
    renderCurve('resistivityTrack', curves.RES_depth, curves.RES, 'RT (ohm.m)', '#ff0');

    // Zones
    const zones = w.zones || [];
    const zonesEl = document.getElementById('zonesList');
    if (zonesEl) {
      if (zones.length === 0) {
        zonesEl.innerHTML = '<div class="wd-empty">No zones identified</div>';
      } else {
        zonesEl.innerHTML = zones.map(z => {
          const v = z.verdict || '—';
          const vClass = v === 'PAY' ? 'verdict-pay'
            : v === 'POSSIBLE' ? 'verdict-possible'
            : v === 'NON_PAY' ? 'verdict-nonpay'
            : 'verdict-unknown';
          return `<div class="wd-zone-row ${vClass}">
            <span class="wd-zone-depth">${z.top}–${z.bot} m</span>
            <span class="wd-zone-verdict">${v}</span>
          </div>`;
        }).join('');
      }
    }

    // Physics9 summary
    const p9 = w.physics9 || {};
    const p9El = document.getElementById('physics9Summary');
    if (p9El) {
      const items = [];
      if (p9.ai_kg_ms2 != null) items.push(`AI: ${p9.ai_kg_ms2} kg/m²s`);
      if (p9.vsh != null) items.push(`Vsh: ${(p9.vsh * 100).toFixed(0)}%`);
      if (p9.phi != null) items.push(`φ: ${(p9.phi * 100).toFixed(0)}%`);
      if (p9.sw != null) items.push(`Sw: ${(p9.sw * 100).toFixed(0)}%`);
      if (p9.phi_eff != null) items.push(`φ_eff: ${(p9.phi_eff * 100).toFixed(0)}%`);
      if (p9.sw_avg != null) items.push(`Sw_avg: ${p9.sw_avg.toFixed(2)}`);
      p9El.innerHTML = items.length
        ? items.map(t => `<span class="wd-param">${t}</span>`).join(' | ')
        : '<span class="wd-empty">No physics data</span>';
    }

    // Summary
    const summaryEl = document.getElementById('wellSummary');
    if (summaryEl && w.summary) {
      summaryEl.textContent = w.summary;
    }
  }

  /**
   * Listen for viewModel updates from the MCP bridge
   */
  window.addEventListener('well-desk:viewmodel', function onViewModel(event) {
    const detail = event.detail;
    if (detail?.viewModel) {
      renderViewModel(detail.viewModel);
    }
  });

  // Expose for manual calls
  window.WELLDESK_RENDER = { renderViewModel, renderCurve };

  console.log('[WellDeskRenderAdapter] ready');

})();
