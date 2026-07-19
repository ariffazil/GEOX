/**
 * GEOX MCP Bridge — Shared WebMCP client for geox.arif-fazil.com
 * Wires browser UI to GEOX MCP tools via HTTPS streamable-http transport.
 * DITEMPA BUKAN DIBERI
 */
const GEOX_MCP_BRIDGE = (() => {
  const MCP_URL = 'https://geox.arif-fazil.com/mcp/';
  const TIMEOUT_MS = 30000;

  let requestId = 1;
  const pending = new Map();

  async function callTool(toolName, args = {}) {
    const id = requestId++;
    const body = {
      jsonrpc: '2.0',
      id,
      method: 'tools/call',
      params: { name: toolName, arguments: args }
    };

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
      const res = await fetch(MCP_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
        body: JSON.stringify(body),
        signal: controller.signal
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${res.status}: ${errText}`);
      }

      // Streamable HTTP — read SSE
      const text = await res.text();
      const lines = text.split('\n').filter(l => l.startsWith('data: '));
      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.id === id) {
            if (data.error) throw new Error(data.error.message || JSON.stringify(data.error));
            // Extract text content from result
            const result = data.result;
            if (result && result.content) {
              const textContent = result.content
                .filter(c => c.type === 'text')
                .map(c => c.text)
                .join('\n');
              try { return JSON.parse(textContent); } catch { return textContent; }
            }
            return result;
          }
        } catch (e) {
          if (e.message?.startsWith('HTTP') || e.message?.includes('tool')) throw e;
        }
      }
      throw new Error('No valid response from MCP server');
    } finally {
      clearTimeout(timer);
    }
  }

  // High-level tool wrappers
  const tools = {
    // X1D Well Tie
    tiePreflight: (wellId, lasPath) =>
      callTool('geox_tie_preflight', { well_id: wellId, las_path: lasPath }),

    tieReceipt: (tieId, verdict) =>
      callTool('geox_tie_receipt', { tie_id: tieId, verdict }),

    waveletExtract: (wellId, timeWindowMs, frequencyBand) =>
      callTool('geox_wavelet_extract_least_squares', {
        well_id: wellId,
        time_window_ms: timeWindowMs,
        frequency_band: frequencyBand
      }),

    // X2D Seismic Cognition
    seismicCognition: (volumeRef, frameIndex, orientation) =>
      callTool('geox_seismic_cognition', { volume_ref: volumeRef, frame_index: frameIndex, orientation }),

    visualUnderstand: (imageData, mode) =>
      callTool('geox_visual_understand', { image_data: imageData, mode: mode || 'analyze' }),

    visualGenerateHypotheses: (imageData, constraints) =>
      callTool('geox_visual_generate_hypotheses', { image_data: imageData, constraints }),

    // X3D Subsurface
    subsurfaceModel: (mode, surveyType, params) =>
      callTool('geox_subsurface_model', { mode, survey_type: surveyType, ...params }),

    simulateAccommodation: (params) =>
      callTool('geox_simulate_accommodation', params),

    simulateSequences: (params) =>
      callTool('geox_simulate_sequences', params),

    // Basin
    basin: (name, mode) =>
      callTool('geox_basin', { name, mode: mode || 'profile' }),

    // Falsify
    falsify: (claimText, claimType) =>
      callTool('geox_falsify', { claim_text: claimText, claim_type: claimType || 'general' }),

    // Prospect
    prospect: (ref, mode) =>
      callTool('geox_prospect', { prospect_ref: ref, mode: mode || 'screen' }),

    // Petrophysics
    petrophysics: (params) =>
      callTool('geox_petrophysics', params),

    // Surface status
    surfaceStatus: () =>
      callTool('geox_surface_status', { mode: 'registry' }),

    // Generic call
    call: callTool
  };

  return {
    MCP_URL,
    callTool,
    tools,
    // Check connection
    async ping() {
      try {
        await callTool('geox_surface_status', { mode: 'registry' });
        return true;
      } catch { return false; }
    }
  };
})();

// Export to window for inline use
window.GEOX_MCP = GEOX_MCP_BRIDGE;
console.log('🔥 GEOX MCP Bridge loaded — DITEMPA BUKAN DIBERI');
