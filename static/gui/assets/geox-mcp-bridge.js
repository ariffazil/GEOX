/**
 * GEOX MCP Bridge — browser-side transport boundary.
 *
 * Inside /gui/: forwards requests to the authenticated parent cockpit.
 * Inside an MCP host: uses the host postMessage bridge.
 * Standalone preview: disabled until configure({ sessionToken }) succeeds.
 *
 * No component talks to /mcp/ directly. DITEMPA BUKAN DIBERI.
 */
const GEOX_MCP_BRIDGE = (() => {
  const MCP_URL = '/mcp/';
  const TIMEOUT_MS = 30_000;
  const PROTOCOL_VERSION = '2025-11-25';
  const PUBLIC_TOOLS = new Set([
    'geox_basin', 'geox_basin_backstrip', 'geox_claim',
    'geox_claim_graph_evaluate', 'geox_contradiction_scan',
    'geox_deep_time_state', 'geox_evidence', 'geox_falsify',
    'geox_geomechanics', 'geox_gravmag_studio', 'geox_lem_predict',
    'geox_petrophysics', 'geox_prospect', 'geox_sediment_mass_balance',
    'geox_seismic_compute', 'geox_seismic_ingest',
    'geox_seismic_interpret', 'geox_sequence', 'geox_subsurface_model',
    'geox_surface_status', 'geox_thermal_maturity_history',
    'geox_to_wealth_bridge', 'geox_well_desk', 'geox_well_ingest',
  ]);

  let requestId = 1;
  let sessionToken = '';
  let mcpSessionId = '';
  let actorId = 'ARIF';
  let initialized = false;

  function isEmbedded() {
    try { return window.parent !== window; } catch { return true; }
  }

  function decodeToken(token) {
    try {
      const payload = token.split('.')[1]
        .replace(/-/g, '+')
        .replace(/_/g, '/');
      const parsed = JSON.parse(atob(payload));
      return { actorId: parsed.actor || 'ARIF', sessionId: parsed.sid || '' };
    } catch {
      return { actorId: 'ARIF', sessionId: '' };
    }
  }

  function canonicalize(toolName, args = {}) {
    switch (toolName) {
      case 'geox_tie_preflight':
        return ['geox_seismic_compute', { ...args, mode: 'tie_preflight' }];
      case 'geox_tie_receipt':
        return ['geox_seismic_compute', {
          mode: 'tie_receipt',
          well_id: args.well_id || String(args.tie_id || '').split('_')[1] || '',
          decision_permission: args.verdict === 'SEAL' ? 'HOLD' : (args.verdict || 'HOLD'),
          decision_reason: 'Operator cockpit evidence receipt; constitutional seal not implied',
        }];
      case 'geox_wavelet_extract_least_squares':
        return ['geox_seismic_compute', { ...args, mode: 'wavelet_extract' }];
      case 'geox_seismic_cognition':
        return ['geox_seismic_interpret', {
          mode: 'rsi_pipeline',
          volume_ref: args.volume_ref,
          frame_index: args.frame_index || 0,
          orientation: args.orientation || 'inline',
        }];
      case 'geox_visual_understand':
        return ['geox_seismic_interpret', {
          mode: 'vision', image_data: args.image_data, action: args.mode || 'analyze',
        }];
      case 'geox_visual_generate_hypotheses':
        return ['geox_seismic_interpret', {
          mode: 'vision', image_data: args.image_data, action: 'generate_hypotheses',
        }];
      case 'geox_simulate_accommodation':
        return ['geox_basin', {
          mode: 'rift', basin_name: args.basin_name || 'Malay Basin',
          rift_mode: 'full', beta: args.beta || 1.8,
          time_since_rift_ma: args.time_since_rift_ma || 30,
        }];
      case 'geox_simulate_sequences':
        return ['geox_basin', {
          mode: 'rift', basin_name: args.basin_name || 'Malay Basin',
          rift_mode: 'sequence', beta: args.beta || 1.8,
          time_since_rift_ma: args.time_since_rift_ma || 30,
        }];
      default:
        if (!PUBLIC_TOOLS.has(toolName)) {
          throw new Error(`Tool is not on the callable GEOX public surface: ${toolName}`);
        }
        return [toolName, args];
    }
  }

  function parseEnvelope(text, id) {
    const chunks = text.split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trim())
      .filter(Boolean);
    const candidates = chunks.length ? chunks : [text];
    for (const candidate of candidates) {
      try {
        const data = JSON.parse(candidate);
        if (id == null || data.id === id || data.error) return data;
      } catch { /* continue */ }
    }
    throw new Error('MCP response was not valid JSON or SSE JSON');
  }

  async function postMcp(body) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
      };
      if (mcpSessionId) headers['Mcp-Session-Id'] = mcpSessionId;
      const response = await fetch(MCP_URL, {
        method: 'POST', headers, body: JSON.stringify(body), signal: controller.signal,
      });
      const nextSession = response.headers.get('mcp-session-id');
      if (nextSession) mcpSessionId = nextSession;
      const text = await response.text();
      if (!response.ok) throw new Error(`MCP HTTP ${response.status}: ${text}`);
      return parseEnvelope(text, body.id);
    } finally {
      clearTimeout(timer);
    }
  }

  async function initializeDirect() {
    if (initialized) return;
    const id = requestId++;
    const envelope = await postMcp({
      jsonrpc: '2.0', id, method: 'initialize',
      params: {
        protocolVersion: PROTOCOL_VERSION,
        capabilities: {},
        clientInfo: { name: 'geox-operator-cockpit', version: '2026.07.19' },
      },
    });
    if (envelope.error) throw new Error(envelope.error.message || 'MCP initialize failed');
    await postMcp({ jsonrpc: '2.0', method: 'notifications/initialized' });
    initialized = true;
  }

  function hostCall(toolName, args) {
    return new Promise((resolve, reject) => {
      const id = `geox-ui-${Date.now()}-${requestId++}`;
      const timer = setTimeout(() => {
        window.removeEventListener('message', onMessage);
        reject(new Error(`Host tool call timed out: ${toolName}`));
      }, TIMEOUT_MS);
      function onMessage(event) {
        const data = event.data;
        if (!data || data.id !== id) return;
        if (data.method !== 'tool.response' && data.jsonrpc !== '2.0') return;
        clearTimeout(timer);
        window.removeEventListener('message', onMessage);
        const error = data.error || data.params?.error;
        if (error) reject(new Error(error.message || String(error)));
        else resolve(data.result ?? data.params?.result);
      }
      window.addEventListener('message', onMessage);
      window.parent.postMessage({
        jsonrpc: '2.0', id, method: 'tool.request',
        params: { tool: toolName, arguments: args },
      }, '*');
    });
  }

  async function callTool(toolName, args = {}) {
    if (isEmbedded()) return hostCall(toolName, args);
    if (!sessionToken) throw new Error('AUTH_REQUIRED: open this preview through /gui/ or configure a valid SCT');
    await initializeDirect();
    const [name, canonicalArgs] = canonicalize(toolName, args);
    const id = requestId++;
    const envelope = await postMcp({
      jsonrpc: '2.0', id, method: 'tools/call',
      params: {
        name,
        arguments: {
          ...canonicalArgs,
          session_token: sessionToken,
          actor_id: canonicalArgs.actor_id || actorId,
          session_id: canonicalArgs.session_id || decodeToken(sessionToken).sessionId,
        },
      },
    });
    if (envelope.error) throw new Error(envelope.error.message || JSON.stringify(envelope.error));
    const content = envelope.result?.content || [];
    const text = content.filter((item) => item.type === 'text').map((item) => item.text).join('\n');
    if (!text) return envelope.result;
    try { return JSON.parse(text); } catch { return text; }
  }

  const tools = {
    tiePreflight: (wellId, lasPath) => callTool('geox_tie_preflight', { well_id: wellId, las_path: lasPath }),
    tieReceipt: (tieId, verdict) => callTool('geox_tie_receipt', { tie_id: tieId, verdict }),
    waveletExtract: (wellId, timeWindowMs, frequencyBand) => callTool('geox_wavelet_extract_least_squares', {
      well_id: wellId, wavelet_length_ms: timeWindowMs, frequency_band: frequencyBand,
    }),
    seismicCognition: (volumeRef, frameIndex, orientation) => callTool('geox_seismic_cognition', { volume_ref: volumeRef, frame_index: frameIndex, orientation }),
    visualUnderstand: (imageData, mode) => callTool('geox_visual_understand', { image_data: imageData, mode }),
    visualGenerateHypotheses: (imageData, constraints) => callTool('geox_visual_generate_hypotheses', { image_data: imageData, constraints }),
    subsurfaceModel: (mode, surveyType, params) => callTool('geox_subsurface_model', { mode, survey_type: surveyType, ...params }),
    simulateAccommodation: (params) => callTool('geox_simulate_accommodation', params),
    simulateSequences: (params) => callTool('geox_simulate_sequences', params),
    basin: (name, mode) => callTool('geox_basin', { name, basin_name: name, mode: mode || 'profile' }),
    falsify: (claimText, claimType) => callTool('geox_falsify', { claim_text: claimText, claim_type: claimType || 'general' }),
    prospect: (ref, mode) => callTool('geox_prospect', { prospect_ref: ref, mode: mode || 'screen' }),
    petrophysics: (params) => callTool('geox_petrophysics', params),
    surfaceStatus: () => callTool('geox_surface_status', { mode: 'registry' }),
    call: callTool,
  };

  return {
    MCP_URL, callTool, tools, canonicalize,
    configure(config = {}) {
      sessionToken = String(config.sessionToken || '');
      const decoded = decodeToken(sessionToken);
      actorId = String(config.actorId || decoded.actorId || 'ARIF');
      initialized = false;
      mcpSessionId = '';
    },
    async ping() {
      if (isEmbedded()) return true;
      if (!sessionToken) return false;
      await tools.surfaceStatus();
      return true;
    },
  };
})();

window.GEOX_MCP = GEOX_MCP_BRIDGE;
